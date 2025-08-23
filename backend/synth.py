
"""
Synth - Simplified Request Enhancement Engine

Two simple functions to enhance user requests:
1. enhance_without_media() - Basic textual enhancement
2. enhance_with_media() - Enhancement with media content analysis
"""

import json
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types


# Common system instruction shared by both enhancement functions
COMMON_SYSTEM_INSTRUCTION = """You are a request disambiguation engine. Your job is to create ONE comprehensive enhanced request that maximizes the likelihood of successful Remotion generation and accomplishment of the user's intent.

⚠️ CRITICAL: Never output clarifying questions. Fill missing details with reasonable assumptions. Always provide executable instructions for the code generator. Your response goes to another AI, not a human.

⚠️ CRITICAL MEDIA FILE NAMING: When referencing media files in your enhanced request, you MUST use the exact file names from the user's context or media library. DO NOT use generic names like "myVideo.mp4" or "video.mp4". Use the actual file names that are available in the composition or conversation context.

REQUIREMENTS for the enhanced request:
- Unequivocally states what the user wants to achieve
- Includes exact parameters (timing in seconds/frames, positions in pixels/percentages)
- References specific media assets by their EXACT NAMES from the available context (never use generic placeholders)
- Is actionable and executable by the downstream Remotion generator
- Eliminates ambiguity that could cause generation failure
- Maximizes probability of accomplishing the user's actual intent

Return ONLY the enhanced request - no explanations, no questions."""


async def synthesize_request(
    user_request: str,
    conversation_history: Optional[List[Dict[str, Any]]],
    current_composition: Optional[str],
    relevant_media_files: List[str],
    media_library: Optional[List[Dict[str, Any]]],
    preview_settings: Dict[str, Any],
    gemini_api: Any
) -> str:
    """
    Enhanced Synth: Route to appropriate enhancement function based on media availability
    """
    
    print(f"🧠 Synth: Processing request with {len(relevant_media_files)} relevant media files")
    
    if not relevant_media_files:
        # No media analysis needed - use basic enhancement
        return await enhance_without_media(
            user_request, conversation_history, current_composition, 
            preview_settings, gemini_api
        )
    else:
        # Media analysis needed - use enhanced enhancement
        return await enhance_with_media(
            user_request, conversation_history, current_composition,
            relevant_media_files, media_library, gemini_api
        )


async def enhance_without_media(
    user_request: str,
    conversation_history: Optional[List[Dict[str, Any]]],
    current_composition: Optional[str],
    preview_settings: Dict[str, Any],
    gemini_api: Any
) -> str:
    """Simple enhancement without media analysis - resolve textual ambiguities only"""
    
    print("🧠 Synth: Enhancing without media analysis")
    
    # Build simple context
    context_parts = [f"User request: {user_request}"]
    
    if conversation_history:
        recent = conversation_history[-4:]  # Last 2 exchanges
        context_parts.append("Recent conversation:")
        for msg in recent:
            # Handle ConversationMessage Pydantic model
            if hasattr(msg, 'user_request') and hasattr(msg, 'ai_response'):
                context_parts.append(f"user: {msg.user_request}")
                context_parts.append(f"assistant: {msg.ai_response}")
            else:
                # Fallback for dict format
                role = msg.get('role', 'unknown') if hasattr(msg, 'get') else getattr(msg, 'role', 'unknown')
                content = msg.get('content', '') if hasattr(msg, 'get') else getattr(msg, 'content', '')
                context_parts.append(f"{role}: {content}")
    
    if current_composition:
        context_parts.append(f"Current composition exists (duration context available)")
    
    context_text = "\n".join(context_parts)

    # Use common system instruction
    system_instruction = COMMON_SYSTEM_INSTRUCTION

    # User prompt with context
    prompt = f"""USER REQUEST: "{user_request}"

CONTEXT:
- Current Composition Code: {current_composition or "No current composition"}
- Conversation History: {context_text}"""

    try:
        response = gemini_api.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            system_instruction=system_instruction,
            config=types.GenerateContentConfig(temperature=0.3)
        )
        
        if response and response.text:
            enhanced = response.text.strip()
            print(f"✅ Synth: Enhanced without media: '{enhanced[:100]}...'\n")
            return enhanced
        else:
            return f"Apply the following change: {user_request}"
            
    except Exception as e:
        print(f"❌ Synth: Enhancement failed: {e}")
        return f"Apply the following change: {user_request}"


async def enhance_with_media(
    user_request: str,
    conversation_history: Optional[List[Dict[str, Any]]],
    current_composition: Optional[str],
    relevant_media_files: List[str],
    media_library: Optional[List[Dict[str, Any]]],
    gemini_api: Any
) -> str:
    """Enhanced enhancement with media content analysis"""
    
    print(f"🧠 Synth: Enhancing with {len(relevant_media_files)} media files")
    
    # Build context with media info
    context_parts = [f"User request: {user_request}"]
    
    if conversation_history:
        recent = conversation_history[-4:]
        context_parts.append("Recent conversation:")
        for msg in recent:
            # Handle ConversationMessage Pydantic model
            if hasattr(msg, 'user_request') and hasattr(msg, 'ai_response'):
                context_parts.append(f"user: {msg.user_request}")
                context_parts.append(f"assistant: {msg.ai_response}")
            else:
                # Fallback for dict format
                role = msg.get('role', 'unknown') if hasattr(msg, 'get') else getattr(msg, 'role', 'unknown')
                content = msg.get('content', '') if hasattr(msg, 'get') else getattr(msg, 'content', '')
                context_parts.append(f"{role}: {content}")
    
    # Extract composition duration for timing calculations
    duration = 0.0
    if current_composition:
        import re
        duration_patterns = [
            r'DURATION:\s*(\d+(?:\.\d+)?)',
            r'AI-determined Duration:\s*(\d+(?:\.\d+)?)\s*seconds'
        ]
        for pattern in duration_patterns:
            match = re.search(pattern, current_composition)
            if match:
                duration = float(match.group(1))
                break
        context_parts.append(f"Current composition duration: {duration} seconds")
    
    # Add media file info
    context_parts.append("Relevant media files:")
    for media_name in relevant_media_files:
        if media_library:
            media_item = next((m for m in media_library if m.get('name') == media_name), None)
            if media_item:
                media_type = media_item.get('mediaType', 'unknown')
                media_duration = media_item.get('durationInSeconds', 0)
                if media_type == 'video' and media_duration:
                    context_parts.append(f"- {media_name}: {media_type} ({media_duration}s)")
                else:
                    context_parts.append(f"- {media_name}: {media_type}")
    
    context_text = "\n".join(context_parts)
    
    # System instruction with role, requirements and examples
    system_instruction = COMMON_SYSTEM_INSTRUCTION + """

CRITICAL: VIDEO-TO-COMPOSITION TIMING CONVERSION
Follow these exact reasoning patterns when analyzing video content and converting timing to composition coordinates.

⚠️ REASONING INSTRUCTION: Use the step-by-step Q&A format shown below. Break down each problem systematically, check video segment ranges, and calculate precise timing offsets. This is exactly how you should reason through timing conversions.
Follow these exact reasoning patterns when analyzing video content and converting timing to composition coordinates.

⚠️ REASONING INSTRUCTION: Use the step-by-step Q&A format shown below. Break down each problem systematically, check video segment ranges, and calculate precise timing offsets. This is exactly how you should reason through timing conversions.

Use these Q&A reasoning patterns with real generated compositions:

EXAMPLE 1 - Reordered Video Segments (Real Generated Code):
```
// Generated at: 2025-08-21 23:40:20
// User Request: Analyze the video to identify when the bird appears and add text...

const videoSrc = 'blob:http://localhost:5173/2ffc470e-70f9-429b-b095-734b7aeccc73';
const videoTotalDurationSeconds = 172.332063;
const videoSegment1StartSeconds = 30;
const videoSegment1EndSeconds = videoTotalDurationSeconds;
const videoSegment2StartSeconds = 0;
const videoSegment2EndSeconds = 30;

const segment1DurationFrames = (videoSegment1EndSeconds - videoSegment1StartSeconds) * fps;
const segment2DurationFrames = (videoSegment2EndSeconds - videoSegment2StartSeconds) * fps;

React.createElement(Sequence, {{
  from: 0,
  durationInFrames: segment1DurationFrames,
  children: React.createElement(Video, {{
    startFrom: videoSegment1StartSeconds * fps,  // 30s
    endAt: videoSegment1EndSeconds * fps,        // 172.332063s
  }})
}}),
React.createElement(Sequence, {{
  from: segment1DurationFrames,
  durationInFrames: segment2DurationFrames,
  children: React.createElement(Video, {{
    startFrom: videoSegment2StartSeconds * fps,  // 0s
    endAt: videoSegment2EndSeconds * fps,        // 30s
  }})
}})
```
Q: The user wants me to add text when a bird appears. I found the bird at 25s in the original video. This composition reorders the video - when should the text appear?
A: Step 1: Identify bird timing in original video → 25s
Step 2: Check which segment contains 25s:
   - Segment 1: videoSegment1StartSeconds (30s) to videoSegment1EndSeconds (172.332063s) → doesn't contain 25s
   - Segment 2: videoSegment2StartSeconds (0s) to videoSegment2EndSeconds (30s) → 25s falls here ✓
Step 3: Calculate offset within segment 2 → 25s - videoSegment2StartSeconds = 25s - 0s = 25s
Step 4: Find segment 2's composition start → from: segment1DurationFrames
Step 5: Convert to frames → segment1DurationFrames + (25s * fps)
Step 6: Set birdTextFromFrame = segment1DurationFrames + (25 - videoSegment2StartSeconds) * fps
Answer: Text should appear at birdTextFromFrame = segment1DurationFrames + (25 * fps) frames in composition.

EXAMPLE 2 - Simple Video with Text Overlays (Real Generated Code):
```
// Generated at: 2025-08-21 22:46:27
// User Request: Add text when an eagle appears in the nature video...
// AI-determined Duration: 20.04 seconds

const videoDurationInFrames = Math.ceil(20.04 * fps);

React.createElement(Sequence, {{
  from: 0,
  durationInFrames: videoDurationInFrames,
  children: React.createElement(Video, {{
    src: 'blob:http://localhost:5173/a2a9ff8f-faf7-4102-972f-d9ad42da7316',
    startFrom: 0,  // Video plays from 0s
    endAt: 20.04 * fps  // to 20.04s
  }})
}}),

// Text 1: 'Black Screen'
React.createElement(Sequence, {{
  from: 0,
  durationInFrames: 1 * fps,
  children: React.createElement('div', {{
    style: {{ position: 'absolute', top: '80%', left: '50%' }}
  }}, 'Black Screen')
}}),

// Text 2: 'Sunlit Purple Flowers'  
React.createElement(Sequence, {{
  from: 1 * fps,
  durationInFrames: (9 - 1) * fps,
  children: React.createElement('div', {{
    style: {{ position: 'absolute', top: '80%', left: '50%' }}
  }}, 'Sunlit Purple Flowers')
}})
```
Q: The user wants me to add text when an eagle appears. I found the eagle at 15s in the original video. The video plays normally from 0s. Where should I position the text to avoid existing overlays?
A: Step 1: Identify eagle timing in original video → 15s
Step 2: Check video segment range → Simple video from 0s to 20.04s, so 15s is included ✓  
Step 3: Calculate composition timing → 15s occurs at 15s in composition (no offset)
Step 4: Check existing text positions at 15s:
   - At 15s: "Sunlit Purple Flowers" text is active (from 1s to 9s) → No, it's inactive
   - No active text overlays at 15s
Step 5: Choose safe positioning → Can use standard positions
Step 6: Set eagleTextFromFrame = 15 * fps
Answer: Text should appear at eagleTextFromFrame = 15 * fps, positioned at top: '20%' to avoid future text conflicts.

EXAMPLE 3 - Animation with Frame Calculations (Real Generated Code):
```
// Generated at: 2025-08-21 13:03:36
// User Request: Add dramatic text when car crash happens at 2.5s...
// AI-determined Duration: 4.333333333333333 seconds

const frame = useCurrentFrame();
const {{ fps }} = useVideoConfig();

const videoDurationInFrames = Math.ceil(4.333333333333333 * fps);

React.createElement(Sequence, {{
  from: 0,
  durationInFrames: videoDurationInFrames,
  children: React.createElement(Video, {{
    src: 'blob:http://localhost:5173/crash-video',
    startFrom: 0,  // Video plays from 0s
    endAt: 4.333333333333333 * fps  // to 4.33s
  }})
}}),

const crashWarningFromFrame = 2.0 * fps;  // 0.5s before crash at 2.5s
const crashWarningDurationFrames = 1.0 * fps;

React.createElement(Sequence, {{
  from: crashWarningFromFrame,
  durationInFrames: crashWarningDurationFrames,
  children: (() => {{
    const localFrame = frame - crashWarningFromFrame;
    const textOpacity = interpolate(localFrame, [0, 10], [0, 1]);
    return React.createElement('div', {{
      style: {{ opacity: textOpacity }}
    }}, 'WARNING: CRASH!');
  }})()
}})
```
Q: The user wants me to add text when a car crash happens. I found the crash at 2.5s in the original video. The video plays normally. How should I time the text to appear just before the crash for dramatic effect?
A: Step 1: Identify crash timing in original video → 2.5s
Step 2: Convert to frames → 2.5s * fps = 75 frames (assuming 30fps)
Step 3: Calculate dramatic timing → Appear 0.5s before crash = 2.0s = 60 frames
Step 4: Set text duration → Show for 1s through the crash = 30 frames duration
Step 5: Set crashWarningFromFrame = (2.0 * fps) and crashWarningDurationFrames = (1.0 * fps)
Step 6: Add fade-in animation → interpolate(localFrame, [0, 10], [0, 1]) for first 10 frames
Answer: Use crashWarningFromFrame = 60 frames, crashWarningDurationFrames = 30 frames, with fade-in over first 10 frames.

EXAMPLE 4 - Content Not Included Analysis:
```
// Generated composition with limited video segment
const videoSegment1StartSeconds = 50;
const videoSegment1EndSeconds = 150;

React.createElement(Sequence, {{
  from: 0,
  durationInFrames: (150 - 50) * fps,
  children: React.createElement(Video, {{
    startFrom: 50 * fps,  // Only plays 50s-150s of original video
    endAt: 150 * fps
  }})
}})
```
Q: The user wants me to add text when a sunset appears. I found sunset at 180s in the original video. The composition has videoSegment1StartSeconds = 50s and videoSegment1EndSeconds = 150s. Can I add the sunset text?
A: Step 1: Identify sunset timing in original video → 180s
Step 2: Check video segment range → 50s to 150s in original video
Step 3: Check if sunset is included → 180s > 150s (sunset occurs AFTER segment ends)
Step 4: Determine availability → Sunset timing not included in composition
Answer: Cannot add sunset text - the sunset at 180s occurs after this composition's video segment which ends at 150s.

EXAMPLE 5 - Position Analysis with Existing Elements:
```
// Composition with multiple existing text overlays
React.createElement(Sequence, {{
  from: 0,
  children: React.createElement('div', {{
    style: {{ position: 'absolute', top: '80%', left: '25%' }}
  }}, 'Existing Text 1')
}}),
React.createElement(Sequence, {{
  from: 30,
  children: React.createElement('div', {{
    style: {{ position: 'absolute', top: '80%', left: '75%' }}
  }}, 'Existing Text 2')
}})
```
Q: The user wants me to position text where it won't interfere with existing elements. I analyzed the composition and found multiple text overlays at 80% top. Where should I place new text?
A: Step 1: Analyze existing text positions → Multiple elements at top: '80%'
Step 2: Identify safe zones → Top area (0%-60%), bottom area (90%-100%), side areas
Step 3: Check for visual conflicts → Avoid crowded 80% area
Step 4: Select optimal position → top: '20%' for clear separation from existing 80% elements  
Step 5: Consider content behind → Ensure good contrast with video content
Answer: Position new text at top: '20%', left: '50%' with transform: 'translateX(-50%)' for center alignment, avoiding the crowded 80% area.

⚠️ CRITICAL: Your output must be clearly actionable for a Remotion LLM code generator:
- Use precise technical specifications (hex colors, exact coordinates, frame numbers)
- Provide concrete measurements and timing values
- Include all necessary parameters for immediate Remotion component implementation
- Ensure the request can be executed without further clarification or analysis

ENHANCED OUTPUT EXAMPLE:
Input: "add text when the sunset looks beautiful"
Output: "Add text overlay with content 'Golden Hour Magic', fontSize 56px, fontFamily 'Inter', color #FFFFFF, backgroundColor rgba(255,140,66,0.8), positioned at 50% left, 15% top, appearing from frame 1080 to frame 1380 (36.0s to 46.0s in composition) when the sunset reaches peak orange saturation #FF8C42 in the sky"

Return ONLY the enhanced request as a single, comprehensive instruction."""

    # User prompt with specific request and context
    prompt = f"""USER REQUEST: "{user_request}"

CONTEXT:
- Current Composition Code: {current_composition or "No current composition"}
- Conversation History: {context_text}
- Relevant Media Files: {len(relevant_media_files)} files for analysis"""

    try:
        # Prepare content for Gemini (text + media files)
        content_parts = [prompt]
        
        # Add media files with Gemini file IDs
        if media_library:
            for media_name in relevant_media_files:
                media_item = next((m for m in media_library if m.get('name') == media_name), None)
                if media_item and media_item.get('gemini_file_id'):
                    try:
                        gemini_file = gemini_api.files.get(name=media_item['gemini_file_id'])
                        content_parts.append(gemini_file)
                        print(f"🧠 Synth: Added {media_name} for analysis")
                    except Exception as e:
                        print(f"⚠️ Synth: Failed to load {media_name}: {e}")
        
        response = gemini_api.models.generate_content(
            model="gemini-2.5-flash",
            contents=content_parts,
            system_instruction=system_instruction,
            config=types.GenerateContentConfig(temperature=0.4)
        )
        
        if response and response.text:
            enhanced = response.text.strip()
            print(f"✅ Synth: Enhanced with media: '{enhanced[:100]}...'\n")
            return enhanced
        else:
            return f"Apply the following change: {user_request} (using relevant media files)"
            
    except Exception as e:
        print(f"❌ Synth: Media enhancement failed: {e}")
        return f"Apply the following change: {user_request} (using relevant media files)"
