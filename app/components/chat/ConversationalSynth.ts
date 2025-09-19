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
- type: "probe" - To analyze media files before making decisions (images: probe liberally, videos: only when necessary)

**CHAT TYPE RESPONSES:**
Use type "chat" for:
- Answering questions about composition, media files, capabilities
- Creating detailed edit plans with specific invented details: "I'll [complete detailed plan with timing, positioning, effects]. Does this sound good? Say 'yes' to proceed."
- General conversation and help
- Plan modifications when user objects to details

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
`;

export interface ConversationMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

export interface SynthResponse {
  type: 'chat' | 'edit' | 'probe';
  content: string;
  referencedFiles?: string[]; // @-mentioned files
  fileName?: string; // For probe responses
  question?: string; // For probe responses
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
- If user wants to edit their video BUT no pending plan exists: respond with type "chat" and CREATE A COMPLETE DETAILED PLAN
  * Invent specific timing values, positions, colors, transitions, and effects as needed
  * Make creative decisions to fill in missing details 
  * Present the full plan confidently and ask for approval
  * Don't ask many questions - be decisive and creative
- If user confirms a pending plan (says "yes", "go ahead", etc.): respond with type "edit" with direct editing instructions
- If user objects to plan details: respond with type "chat" with revised plan addressing their concerns

Be proactive and creative when making plans. Invent reasonable details rather than asking questions.
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

  // CSS styling guidelines for visually exciting results
  private readonly STYLING_GUIDELINES = `
CSS STYLING CAPABILITIES - USE CSS TO ITS FULLEST:

Typography Excellence:
- Rich font combinations with proper hierarchy (headings, body, captions)
- Letter-spacing, line-height, and text-transform for polished look
- Text shadows, outlines, and gradient text effects
- Custom font weights and styles for visual impact

Color & Visual Impact:
- Linear and radial gradients instead of flat colors
- RGBA/HSLA for sophisticated transparency effects
- Color harmony with complementary and analogous schemes
- High contrast combinations for readability and drama

Advanced Visual Effects:
- Box-shadows for depth and dimension (multiple layers)
- Border-radius for modern rounded aesthetics
- Backdrop-filter for glass morphism effects
- Clip-path for custom geometric shapes and reveals
- CSS filters: blur, brightness, contrast, hue-rotate, saturate

Layout & Positioning:
- Flexbox and CSS Grid for sophisticated layouts
- Absolute positioning for precise control
- Transform combinations: rotate + scale + translate
- 3D transforms with perspective for dynamic effects

Modern Aesthetics:
- Smooth CSS animations and transitions
- Gradient overlays on backgrounds and images
- Subtle animations for micro-interactions
- Glass morphism, neumorphism, and contemporary design trends
- Always prioritize visual polish and professional appearance

MANDATE: Create visually stunning, modern designs - never settle for plain styling!
`;

  // Media analysis guidelines for probe decisions
  private readonly PROBE_GUIDELINES = `
MEDIA ANALYSIS GUIDELINES:

When to Probe:
- Images (jpg, png, gif, webp): PROBE LIBERALLY - very cheap and fast
  * Always probe for color schemes, composition, subject placement
  * Probe for text detection, dominant elements, visual style
  * Use probing to make smart positioning and styling decisions

- Videos (mp4, mov, avi, webm): PROBE ONLY WHEN NECESSARY - more expensive
  * Probe for crucial decisions like text placement over main subjects
  * Probe when color scheme is critical for overlay design
  * Avoid probing for simple tasks like basic transitions or timing
  * Consider file duration - shorter videos are cheaper to analyze

- Audio files: Minimal probing - focus on metadata (duration, format)

Smart Probing Strategy:
- For images: Default to probing for better results
- For short videos (<30s): Probe when content-aware decisions needed
- For long videos (>30s): Only probe if absolutely critical
- Always explain why you're probing in the question
`;

  // Video editor capabilities and rules
  private readonly VIDEO_EDITOR_CAPABILITIES = `
VIDEO EDITOR CAPABILITIES AND RULES:

Available Features:
- Timeline tracks with collision detection (elements cannot overlap on same track)
- Video/audio clips with trimming capabilities  
- CSS elements with styling options
- Transitions between clips with full Remotion transition support
- Animations using SW.interp for position, scale, opacity, rotation
- Media bin for asset management

Available Transition Types:
- "fade": Opacity crossfade/dissolve transitions (fade-in, fade-out, crossfade)
- "slide": Directional slide transitions (from-left, from-right, from-top, from-bottom)
- "wipe": Directional wipe/reveal transitions (from-left, from-right, from-top, from-bottom, diagonals)
- "flip": 3D rotation transitions with perspective (from-left, from-right, from-top, from-bottom)
- "clockWipe": Circular wipe transition like clock hands
- "iris": Circular expand/contract reveal transition

How to Use Transitions:
- Transitions connect adjacent clips on the same track
- Place clips next to each other (no gap/overlap needed) - the transition system handles timing
- If no adjacent clip exists, transitions still work to/from nothing

Timing Rules:
- All timing values are in seconds
- Track collision: if elements overlap on same track, suggest different tracks or timing adjustments

Animation Capabilities:
- Position animations: move elements across the screen over time
- Scale animations: grow/shrink elements smoothly
- Opacity animations: fade elements in/out over duration
- Rotation animations: spin/rotate elements
- Color animations: change colors gradually over time
- Supports both simple animations (start→end) and complex keyframe sequences
- Timing can be precise to the second for smooth motion

Best Practices:
- Suggest specific timing values (e.g., "start at 5.2 seconds, duration 3.8 seconds")
- Propose smooth transitions between scenes
- Consider visual flow and pacing in suggestions
`;

  /**
   * Call Gemini API with structured response
   */
  private async callGeminiAPIStructured(
    systemInstruction: string, 
    prompt: string
  ): Promise<{ type: 'chat' | 'edit' | 'probe'; content: string; fileName?: string; question?: string }> {
    if (!GEMINI_API_KEY) {
      throw new Error("GEMINI_API_KEY not found. Please set VITE_GEMINI_API_KEY in your environment.");
    }

    const responseSchema = {
      type: "OBJECT",
      properties: {
        "type": {
          "type": "STRING",
          "enum": ["chat", "edit", "probe"]
        },
        "fileName": {
          "type": "STRING"
        },
        "question": {
          "type": "STRING"
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
                  text: `${systemInstruction}\n\n${prompt}\n\n${this.VIDEO_EDITOR_CAPABILITIES}\n\n${this.STYLING_GUIDELINES}\n\n${this.PROBE_GUIDELINES}`
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
        
        if (!parsedResponse.type || !parsedResponse.content || !["chat", "edit", "probe"].includes(parsedResponse.type)) {
          throw new Error('Invalid structured response from Gemini API');
        }

        return {
          type: parsedResponse.type,
          content: parsedResponse.content,
          fileName: parsedResponse.fileName,
          question: parsedResponse.question
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
