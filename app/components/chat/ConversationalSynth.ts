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
import {
  AI_PERSONA,
  CONVERSATIONAL_SYNTH_SYSTEM,
  STYLING_GUIDELINES,
  VIDEO_EDITOR_CAPABILITIES,
  PROBE_GUIDELINES,
  CHAT_GUIDELINES,
  EDIT_GUIDELINES,
  IMAGE_GENERATION_GUIDELINES,
  VIDEO_GENERATION_GUIDELINES,
  PLANNING_GUIDELINES,
  SLEEP_GUIDELINES
} from "./PromptComponents";

// Gemini API configuration
const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY;
const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent";

export interface ConversationMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

export interface SynthResponse {
  type: 'chat' | 'edit' | 'probe' | 'generate' | 'sleep';
  content: string;
  referencedFiles?: string[]; // @-mentioned files
  fileName?: string; // For probe responses
  question?: string; // For probe responses
  prompt?: string; // For generate responses - content generation prompt
  suggestedName?: string; // For generate responses - AI-chosen filename
  content_type?: 'image' | 'video'; // For generate responses - type of content to generate
}

export interface SynthContext {
  messages: ConversationMessage[];
  currentComposition?: any; // Blueprint composition
  mediaLibrary: MediaBinItem[];
  compositionDuration?: number;
}

export class ConversationalSynth {
  constructor(apiKey?: string) {
    // API key is now handled globally in the file
    // This constructor is kept for compatibility
  }

  /**
   * Main entry point - analyze conversation and return appropriate response
   */
  async processMessage(
    context: SynthContext
  ): Promise<SynthResponse> {
    console.log("🧠 ConversationalSynth: Processing conversation with", context.messages.length, "messages");

    // Get the last user message from conversation context for @filename detection
    const lastUserMessage = context.messages.filter(msg => msg.isUser).pop();
    const messageForFileDetection = lastUserMessage ? lastUserMessage.content : "";

    // Detect @filename mentions
    const referencedFiles = this.detectReferencedFiles(messageForFileDetection, context.mediaLibrary);
    console.log("📁 Referenced files:", referencedFiles);

    // Build context for the AI
    const contextText = this.buildContextText(context, true);
    const conversationHistory = this.buildConversationHistory(context);

    // Create comprehensive prompt for structured response
    let prompt = `CONTEXT:
${contextText}

BLUEPRINT UNDERSTANDING:
- The "Current Timeline Blueprint JSON" shows the exact structure of what's currently on the timeline
- Each track contains clips with startTime, endTime, and element (React code)
- Use this to understand existing content, timing, and make informed edit suggestions
- When proposing edits, reference specific clips by their IDs or timing

${conversationHistory}

Your job is to generate the next appropriate response based on the conversation up to now.`;

    try {
      const fullSystemPrompt = `${AI_PERSONA}

${CONVERSATIONAL_SYNTH_SYSTEM}

${VIDEO_EDITOR_CAPABILITIES}

${STYLING_GUIDELINES}

${PROBE_GUIDELINES}

${CHAT_GUIDELINES}

${EDIT_GUIDELINES}

${IMAGE_GENERATION_GUIDELINES}

${VIDEO_GENERATION_GUIDELINES}

${PLANNING_GUIDELINES}

${SLEEP_GUIDELINES}`;
      
      // Log the exact context before sending to AI
      console.log("🚀 SYNTH PROMPT LOG:", {
        contextText: contextText,
        conversationHistory: conversationHistory
      });

      // LOG THE COMPLETE PROMPT TO FILE using existing fileLogger system
      try {
        const { apiUrl } = await import('~/utils/api');
        
        // Create a dedicated prompt log entry using the same system
        const promptLogEntry = {
          timestamp: new Date().toISOString(),
          step: 'FULL_PROMPT_TO_AI',
          data: {
            messagesInContext: context.messages.length,
            fullSystemPrompt: fullSystemPrompt,
            fullPrompt: prompt,
            conversationBreakdown: context.messages.map((msg, idx) => ({
              index: idx,
              type: msg.isUser ? 'User' : 'Assistant',
              content: msg.content
            }))
          }
        };

        const response = await fetch(apiUrl('/chat/log', true), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: `prompt_${Date.now()}`,
            log_entry: promptLogEntry
          })
        });

        if (!response.ok) {
          console.error('Failed to save prompt log:', await response.text());
        } else {
          console.log('✅ Prompt logged to file successfully');
        }
      } catch (logError) {
        console.error('❌ Failed to log prompt to file:', logError);
      }

      const structuredResponse = await this.callGeminiAPIStructured(fullSystemPrompt, prompt);
      
      // Handle the structured response
      if (structuredResponse.type === 'edit') {
        console.log("🎬 Generated edit instructions:", structuredResponse.content);
      } else if (structuredResponse.type === 'chat') {
        console.log("💬 Generated chat response:", structuredResponse.content);
      }
      
      return {
        type: structuredResponse.type,
        content: structuredResponse.content,
        referencedFiles,
        fileName: structuredResponse.fileName,
        question: structuredResponse.question,
        prompt: structuredResponse.prompt,
        suggestedName: structuredResponse.suggestedName,
        content_type: structuredResponse.content_type
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
   * Build conversation history text - just read messages in chronological order
   */
  private buildConversationHistory(context: SynthContext): string {
    if (context.messages.length === 0) {
      return "";
    }
    
    // Take the most recent 8 messages in chronological order
    const recent = context.messages.slice(-8);
    const conversationParts: string[] = [];
    
    conversationParts.push("=== CONVERSATION UP TO NOW (LAST 8 MESSAGES) ===");
    conversationParts.push("This is the complete conversation history truncated to the most recent messages:");
    conversationParts.push("");
    
    recent.forEach(msg => {
      conversationParts.push(`${msg.isUser ? 'User' : 'Assistant'}: ${msg.content}`);
    });
    
    conversationParts.push("");
    conversationParts.push("=== END OF CONVERSATION ===");
    
    return conversationParts.join("\n");
  }

  /**
   * Call Gemini API with structured response
   */
  private async callGeminiAPIStructured(
    systemInstruction: string, 
    prompt: string
  ): Promise<{ type: 'chat' | 'edit' | 'probe' | 'generate'; content: string; fileName?: string; question?: string; prompt?: string; suggestedName?: string; content_type?: 'image' | 'video' }> {
    if (!GEMINI_API_KEY) {
      throw new Error("GEMINI_API_KEY not found. Please set VITE_GEMINI_API_KEY in your environment.");
    }

    const responseSchema = {
      type: "OBJECT",
      properties: {
        "type": {
          "type": "STRING",
          "enum": ["chat", "edit", "probe", "generate", "sleep"]
        },
        "fileName": {
          "type": "STRING"
        },
        "question": {
          "type": "STRING"
        },
        "prompt": {
          "type": "STRING"
        },
        "suggestedName": {
          "type": "STRING"
        },
        "content_type": {
          "type": "STRING",
          "enum": ["image", "video"]
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
        
        if (!parsedResponse.type || !parsedResponse.content || !["chat", "edit", "probe", "generate", "sleep"].includes(parsedResponse.type)) {
          throw new Error('Invalid structured response from Gemini API');
        }

        return {
          type: parsedResponse.type,
          content: parsedResponse.content,
          fileName: parsedResponse.fileName,
          question: parsedResponse.question,
          prompt: parsedResponse.prompt,
          suggestedName: parsedResponse.suggestedName,
          content_type: parsedResponse.content_type
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
   * Stream chat responses for better UX (only for type: 'chat' responses)
   */
  async streamChatResponse(
    context: SynthContext,
    onChunk: (text: string) => void
  ): Promise<void> {
    console.log("🌊 ConversationalSynth: Streaming chat response");
    
    // Build context for the AI
    const contextText = this.buildContextText(context, false);
    const conversationHistory = this.buildConversationHistory(context);
    
    // Create chat-only prompt (no structured JSON needed for streaming)
    const prompt = `${AI_PERSONA}

Respond naturally in a conversational manner. For streaming responses, only provide chat-type responses - no structured editing instructions or probing requests.

Be helpful, creative, and engaging. If the user wants to make edits, create a detailed plan and ask for confirmation before proceeding.

CONTEXT:
${contextText}

${conversationHistory}`;

    if (!GEMINI_API_KEY) {
      throw new Error("GEMINI_API_KEY not found. Please set VITE_GEMINI_API_KEY in your environment.");
    }

    try {
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:streamGenerateContent?key=${GEMINI_API_KEY}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            contents: [
              {
                parts: [{ text: prompt }]
              }
            ],
            generationConfig: {
              temperature: 0.7,
              topK: 40,
              topP: 0.95,
              maxOutputTokens: 2048,
            },
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Gemini API error: ${response.status} - ${errorData.error?.message || response.statusText}`);
      }

      if (!response.body) {
        throw new Error("Response body is null");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let braceCount = 0;
      let currentObject = '';
      let insideObject = false;
      
      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          
          // Process character by character to find complete JSON objects
          let i = 0;
          while (i < buffer.length) {
            const char = buffer[i];
            
            if (char === '{') {
              if (!insideObject) {
                insideObject = true;
                currentObject = '';
              }
              braceCount++;
              currentObject += char;
            } else if (char === '}' && insideObject) {
              braceCount--;
              currentObject += char;
              
              // When braces are balanced, we have a complete JSON object
              if (braceCount === 0) {
                try {
                  const data = JSON.parse(currentObject);
                  
                  if (data.candidates && data.candidates[0] && data.candidates[0].content) {
                    const text = data.candidates[0].content.parts[0]?.text || '';
                    if (text) {
                      console.log("🌊 Streaming chunk:", text);
                      onChunk(text);
                    }
                  }
                } catch (parseError) {
                  console.warn("Failed to parse JSON object:", currentObject, parseError);
                }
                
                // Reset for next object
                insideObject = false;
                currentObject = '';
              }
            } else if (insideObject) {
              currentObject += char;
            }
            
            i++;
          }
          
          // Clear the processed buffer
          buffer = '';
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error("💥 Gemini streaming API error:", error);
      throw error;
    }
  }
}
