/**
 * ConversationalSynth - Frontend conversational AI for chat and video editing
 * 
 * This handles:
 * 1. AI-powered intent detection (CHAT vs EDIT)
 * 2. @filename detection and media validation  
 * 3. Conversation history management
 * 4. Edit confirmation workflow before sending to backend
 */

import type { MediaBinItem } from "../timeline/types";

// Gemini API configuration
const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY;
const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent";

// System instruction for the conversational synth
const CONVERSATIONAL_SYNTH_SYSTEM = `You are a friendly creative director helping users with video editing. Respond with structured JSON containing a "type" and "content" field.

**RESPONSE TYPES:**
- type: "chat" - For questions, conversations, confirmations, and general help
- type: "edit" - For direct video editing instructions to send to the backend editor

**CHAT TYPE RESPONSES:**
Use type "chat" for:
- Answering questions about composition, media files, capabilities
- Asking for confirmation on edit plans: "I'll [describe plan]. Does this sound good? Say 'yes' to proceed."
- General conversation and help
- Plan modifications and clarifications

**EDIT TYPE RESPONSES:**
Use type "edit" ONLY when user has confirmed a plan. Generate structured editing instructions like:
"First, [specific action with timing], then [specific action with positioning], and finally [specific action with effects]."

**CRITICAL RULES:**
- ONLY reference media files that exist in the provided media library
- Use exact filenames from the media list
- Be precise with timing, colors, and positioning  
- For edit type: NO conversational language, just direct editing instructions
- For chat type: Be conversational and helpful
- Never output code or technical syntax

**@FILENAME DETECTION:**
- Detect @filename mentions in user requests
- Validate against available media files`;

export interface ConversationMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

export interface SynthResponse {
  type: 'chat' | 'edit';
  content: string;
  referencedFiles?: string[]; // @-mentioned files
}

export interface SynthContext {
  messages: ConversationMessage[];
  currentComposition?: any; // Blueprint composition
  mediaLibrary: MediaBinItem[];
  compositionDuration?: number;
}

export class ConversationalSynth {
  private pendingPlan: string | null = null;
  private pendingPlanContext: string | null = null;

  constructor(apiKey?: string) {
    // API key is now handled globally in the file
    // This constructor is kept for compatibility
  }

  /**
   * Main entry point - analyze user message and return appropriate response
   */
  async processMessage(
    userMessage: string,
    context: SynthContext
  ): Promise<SynthResponse> {
    console.log("🧠 ConversationalSynth: Processing message:", userMessage);

    // Detect @filename mentions
    const referencedFiles = this.detectReferencedFiles(userMessage, context.mediaLibrary);
    console.log("📁 Referenced files:", referencedFiles);

    // Build context for the AI
    const contextText = this.buildContextText(context, true);

    // Create comprehensive prompt for structured response
    let prompt = `USER MESSAGE: "${userMessage}"

CONTEXT:
${contextText}

PENDING PLAN STATUS: ${this.pendingPlan ? 'User has a pending edit plan awaiting confirmation' : 'No pending plan'}

BLUEPRINT UNDERSTANDING:
- The "Current Timeline Blueprint JSON" shows the exact structure of what's currently on the timeline
- Each track contains clips with startTime, endTime, and element (React code)
- Use this to understand existing content, timing, and make informed edit suggestions
- When proposing edits, reference specific clips by their IDs or timing

INSTRUCTIONS:
- If user is asking questions or having general conversation: respond with type "chat"
- If user wants to edit their video BUT no pending plan exists: respond with type "chat" and ask for confirmation of your plan
- If user confirms a pending plan (says "yes", "go ahead", etc.): respond with type "edit" with direct editing instructions
- If user wants to modify a pending plan: respond with type "chat" with updated plan and ask for confirmation again

Be helpful, conversational for chat responses, and precise with editing instructions for edit responses.
When discussing the timeline, reference specific clips and timing from the blueprint JSON.`;

    try {
      const structuredResponse = await this.callGeminiAPIStructured(CONVERSATIONAL_SYNTH_SYSTEM, prompt);
      
      // Handle the structured response
      if (structuredResponse.type === 'edit') {
        // Clear any pending plan since we're executing
        this.pendingPlan = null;
        this.pendingPlanContext = null;
        console.log("🎬 Generated edit instructions:", structuredResponse.content);
      } else if (structuredResponse.type === 'chat') {
        // Check if this is setting up a new plan
        if (structuredResponse.content.toLowerCase().includes('does this') || 
            structuredResponse.content.toLowerCase().includes('sound good') ||
            structuredResponse.content.toLowerCase().includes('say \'yes\'')) {
          // Store pending plan
          this.pendingPlan = userMessage;
          this.pendingPlanContext = userMessage;
          console.log("📋 Created pending plan for approval");
        }
      }
      
      return {
        type: structuredResponse.type,
        content: structuredResponse.content,
        referencedFiles
      };

    } catch (error) {
      console.error("❌ Structured response failed:", error);
      return {
        type: 'chat',
        content: "I'm having trouble processing your message right now. Could you try again?",
        referencedFiles
      };
    }
  }

  /**
   * Detect @filename patterns in user message
   */
  private detectReferencedFiles(message: string, mediaLibrary: MediaBinItem[]): string[] {
    const referencedFiles: string[] = [];
    
    // Pattern 1: @"quoted filename with spaces.ext"
    const quotedPattern = /@"([^"]+)"/g;
    let quotedMatch: RegExpExecArray | null;
    while ((quotedMatch = quotedPattern.exec(message)) !== null) {
      referencedFiles.push(quotedMatch[1]);
    }
    
    // Remove quoted sections to avoid double-matching
    const textWithoutQuotes = message.replace(quotedPattern, '');
    
    // Pattern 2: @filename.ext (common extensions)
    const extensionPattern = /@([^\s@"]+(?:\s+[^\s@"]+)*\.(?:mp4|mov|avi|mkv|webm|jpg|jpeg|png|gif|webp|mp3|wav|flac|aac|m4a))/gi;
    let extensionMatch: RegExpExecArray | null;
    while ((extensionMatch = extensionPattern.exec(textWithoutQuotes)) !== null) {
      referencedFiles.push(extensionMatch[1]);
    }
    
    // Pattern 3: @filename (no extension)
    const simplePattern = /@([^\s@"]+)/g;
    let simpleMatch: RegExpExecArray | null;
    while ((simpleMatch = simplePattern.exec(textWithoutQuotes)) !== null) {
      const filename = simpleMatch[1];
      if (!referencedFiles.includes(filename) && 
          !referencedFiles.some(file => file.includes(filename))) {
        referencedFiles.push(filename);
      }
    }
    
    // Validate against media library
    const availableFiles = mediaLibrary.map(item => item.name);
    return referencedFiles.filter(file => availableFiles.includes(file));
  }



  /**
   * Build context text for AI prompts
   */
  private buildContextText(context: SynthContext, isEdit: boolean): string {
    const parts: string[] = [];
    
    // Recent conversation (last 4 messages)
    if (context.messages.length > 0) {
      const recent = context.messages.slice(-4);
      parts.push("Recent conversation:");
      recent.forEach(msg => {
        parts.push(`${msg.isUser ? 'User' : 'Assistant'}: ${msg.content}`);
      });
    }
    
    // Current composition info - full blueprint JSON
    console.log("🔍 ConversationalSynth: currentComposition =", context.currentComposition);
    
    if (context.currentComposition) {
      const tracks = Array.isArray(context.currentComposition) ? context.currentComposition : [];
      const totalClips = tracks.reduce((sum, track) => sum + (track.clips?.length || 0), 0);
      
      console.log("📊 Composition analysis:", { tracks: tracks.length, totalClips });
      
      if (totalClips > 0) {
        parts.push(`Current composition: ${context.compositionDuration || 'unknown'} seconds`);
        parts.push("\nCurrent Timeline Blueprint JSON:");
        parts.push("```json");
        parts.push(JSON.stringify(context.currentComposition, null, 2));
        parts.push("```");
        parts.push(`\nComposition Summary: ${tracks.length} tracks, ${totalClips} total clips`);
      } else {
        parts.push("Timeline exists but is currently empty (no clips)");
      }
    } else {
      parts.push("No current composition - timeline is empty");
    }
    
    // Media library
    if (context.mediaLibrary.length > 0) {
      parts.push("\nAvailable media files:");
      context.mediaLibrary.forEach(item => {
        let fileInfo = `- ${item.name} (${item.mediaType}`;
        if (item.durationInSeconds) fileInfo += `, ${item.durationInSeconds}s`;
        if (item.media_width && item.media_height) {
          fileInfo += `, ${item.media_width}x${item.media_height}`;
        }
        fileInfo += ")";
        parts.push(fileInfo);
      });
    } else {
      parts.push("\nNo media files available");
    }
    
    return parts.join("\n");
  }

  /**
   * Call Gemini API with structured response
   */
  private async callGeminiAPIStructured(
    systemInstruction: string, 
    prompt: string
  ): Promise<{ type: 'chat' | 'edit'; content: string }> {
    if (!GEMINI_API_KEY) {
      throw new Error("GEMINI_API_KEY not found. Please set VITE_GEMINI_API_KEY in your environment.");
    }

    const responseSchema = {
      type: "OBJECT",
      properties: {
        "type": {
          "type": "STRING",
          "enum": ["chat", "edit"]
        },
        "content": {
          "type": "STRING"
        }
      },
      required: ["type", "content"]
    };

    try {
      const response = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [
            {
              parts: [
                {
                  text: `${systemInstruction}\n\n${prompt}`
                }
              ]
            }
          ],
          generationConfig: {
            response_mime_type: "application/json",
            response_schema: responseSchema
          },
          safetySettings: [
            {
              category: "HARM_CATEGORY_HARASSMENT",
              threshold: "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
              category: "HARM_CATEGORY_HATE_SPEECH", 
              threshold: "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
              category: "HARM_CATEGORY_SEXUALLY_EXPLICIT",
              threshold: "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
              category: "HARM_CATEGORY_DANGEROUS_CONTENT",
              threshold: "BLOCK_MEDIUM_AND_ABOVE"
            }
          ]
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Gemini API error: ${response.status} - ${errorData.error?.message || 'Unknown error'}`);
      }

      const data = await response.json();
      
      if (!data.candidates || !data.candidates[0] || !data.candidates[0].content) {
        throw new Error('Invalid response format from Gemini API');
      }

      const responseText = data.candidates[0].content.parts[0].text;
      
      try {
        const parsedResponse = JSON.parse(responseText);
        
        if (!parsedResponse.type || !parsedResponse.content || !["chat", "edit"].includes(parsedResponse.type)) {
          throw new Error('Invalid structured response from Gemini API');
        }

        return {
          type: parsedResponse.type,
          content: parsedResponse.content
        };
      } catch (e) {
        // If parsing fails, it might be a plain text response
        console.warn("Failed to parse JSON, treating as chat response:", responseText);
        return {
          type: 'chat',
          content: responseText
        };
      }

    } catch (error) {
      console.error('Gemini API call failed:', error);
      
      // Provide fallback response
      return {
        type: 'chat',
        content: "I'm sorry, I'm having trouble processing your request right now. Could you try again?"
      };
    }
  }

  /**
   * Clear any pending plans
   */
  clearPendingPlan(): void {
    this.pendingPlan = null;
    this.pendingPlanContext = null;
  }

  /**
   * Check if there's a pending plan awaiting approval
   */
  hasPendingPlan(): boolean {
    return this.pendingPlan !== null;
  }
}
