"""
Analyzer - Media-Driven Request Enhancement Engine

Enhances user requests by examining actual media content to extract specific details.
Works alongside Synth to transform vague requests into ultra-precise instructions
for the code generator by analyzing visual and audio content in media files.
"""

import re
from typing import Dict, Any, List, Optional


def extract_composition_state(tsx_code: Optional[str]) -> Dict[str, Any]:
    """
    Extract and filter composition to keep only video elements with their timing
    
    Returns:
    - total_duration: Duration from comments
    - filtered_tsx: TSX code with only video elements (preserves timing/positioning)
    - video_count: Number of video elements found
    """
    if not tsx_code:
        return {
            "total_duration": 0.0,
            "filtered_tsx": "",
            "video_count": 0
        }
    
    composition_state = {
        "total_duration": 0.0,
        "filtered_tsx": "",
        "video_count": 0
    }
    
    try:
        # Extract total duration from comments
        duration_patterns = [
            r'DURATION:\s*(\d+(?:\.\d+)?)',
            r'AI-determined Duration:\s*(\d+(?:\.\d+)?)\s*seconds'
        ]
        
        for pattern in duration_patterns:
            duration_match = re.search(pattern, tsx_code)
            if duration_match:
                composition_state["total_duration"] = float(duration_match.group(1))
                break
        
        # Find sequences that contain Video elements by using a different approach
        # Split the code into individual React.createElement blocks and filter for Video ones
        
        video_sequences = []
        
        # Look for React.createElement(Sequence blocks that contain Video
        sequence_starts = []
        for match in re.finditer(r'React\.createElement\(Sequence,', tsx_code):
            sequence_starts.append(match.start())
        
        for start_pos in sequence_starts:
            # Find the matching closing parenthesis for this Sequence
            paren_count = 0
            pos = start_pos
            sequence_start = start_pos
            
            while pos < len(tsx_code):
                char = tsx_code[pos]
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        # Found the complete sequence
                        sequence_text = tsx_code[sequence_start:pos + 1]
                        
                        # Check if this sequence contains a Video element
                        if 'React.createElement(Video,' in sequence_text:
                            video_sequences.append(sequence_text)
                            composition_state["video_count"] += 1
                        break
                pos += 1
        
        # Build the filtered TSX with only video elements
        if video_sequences:
            # Extract the header/setup part (imports, constants, etc.)
            header_parts = []
            
            # Get duration calculation if present
            duration_calc_match = re.search(r'const videoDurationInFrames.*?;', tsx_code)
            if duration_calc_match:
                header_parts.append(duration_calc_match.group(0))
            
            # Get fps reference if present
            fps_match = re.search(r'const \{ fps \}.*?;', tsx_code)
            if fps_match:
                header_parts.append(fps_match.group(0))
                
            # Get frame reference if present
            frame_match = re.search(r'const frame.*?;', tsx_code)
            if frame_match:
                header_parts.append(frame_match.group(0))
            
            # Build the filtered composition
            filtered_parts = []
            if header_parts:
                filtered_parts.extend(header_parts)
                filtered_parts.append("")  # Empty line
            
            filtered_parts.append("return React.createElement(AbsoluteFill, {},")
            
            # Add each video sequence with proper indentation
            for i, video_seq in enumerate(video_sequences):
                if i > 0:
                    filtered_parts.append(",")
                filtered_parts.append(f"  {video_seq}")
            
            filtered_parts.append(");")
            
            composition_state["filtered_tsx"] = "\n".join(filtered_parts)
        
    except Exception as e:
        print(f"⚠️ Failed to filter composition: {e}")
    
    return composition_state


class AnalysisResult:
    """Result from the Analyzer enhancement engine"""
    def __init__(
        self, 
        enhanced_request: str,
        media_analysis: Dict[str, Any] = None,
        visual_context: Dict[str, Any] = None
    ):
        self.enhanced_request = enhanced_request
        self.media_analysis = media_analysis or {}
        self.visual_context = visual_context or {}


async def analyze_content(
    enhanced_request: str,
    media_for_analysis: List[str],
    media_library: List[Dict[str, Any]],
    preview_frame: Optional[str],
    current_composition: Optional[str],
    gemini_api: Any
) -> AnalysisResult:
    """
    Enhance user request by analyzing media content and extracting specific details
    
    Similar to Synth, this function takes a request and makes it more actionable 
    for the code generator by examining actual media content to replace vague 
    references with precise specifications.
    
    Args:
        enhanced_request: The request enhanced by Synth
        media_for_analysis: List of media file names to analyze  
        media_library: Full media library with metadata
        preview_frame: Base64 encoded screenshot for visual analysis
        current_composition: Current TSX composition code for timing context
        gemini_api: Gemini AI client
        
    Returns:
        AnalysisResult with media-enhanced request and analysis context
    """
    
    print(f"🔍 Analyzer: Processing {len(media_for_analysis)} media files")
    
    # Extract basic composition info without filtering
    total_duration = 0.0
    if current_composition:
        # Extract duration from comments
        duration_patterns = [
            r'DURATION:\s*(\d+(?:\.\d+)?)',
            r'AI-determined Duration:\s*(\d+(?:\.\d+)?)\s*seconds'
        ]
        
        for pattern in duration_patterns:
            duration_match = re.search(pattern, current_composition)
            if duration_match:
                total_duration = float(duration_match.group(1))
                break
    
    print(f"📐 Composition duration: {total_duration}s")
    
    if not media_for_analysis:
        # No media to analyze, return as-is
        return AnalysisResult(
            enhanced_request=enhanced_request,
            media_analysis={"status": "no_media_to_analyze"},
            visual_context={"status": "no_media_to_analyze"}
        )
    
    # Find Gemini file IDs for the media files to analyze
    gemini_file_refs = []
    for media_name in media_for_analysis:
        # Find the media item in the library
        media_item = next((item for item in media_library if item.get('name') == media_name), None)
        if media_item and media_item.get('gemini_file_id'):
            gemini_file_refs.append({
                'name': media_name,
                'gemini_file_id': media_item['gemini_file_id']
            })
            print(f"📁 Found Gemini file ID for {media_name}: {media_item['gemini_file_id']}")
        else:
            print(f"⚠️ No Gemini file ID found for {media_name}")
    
    if not gemini_file_refs:
        print("❌ No Gemini file references found for analysis")
        return AnalysisResult(
            enhanced_request=enhanced_request,
            media_analysis={"status": "no_gemini_files"},
            visual_context={"status": "no_gemini_files"}
        )
    
    try:
        # Build analysis prompt with composition context
        analysis_prompt = f"""You are a content-based request enhancement engine. Your ONLY job is to resolve ambiguities that require understanding what's actually happening inside the media content.

⚠️ CRITICAL: Your output goes directly to a code generator. You only handle requests that depend on visual/audio content analysis.

USER REQUEST: "{enhanced_request}"

COMPOSITION CONTEXT:
- Total composition duration: {total_duration} seconds  
- Current composition code:
{current_composition or "No composition provided"}

CONTENT-BASED ENHANCEMENT OBJECTIVE:
Examine the media files and resolve content-dependent references in the user request. Replace content-based ambiguities with specific details extracted from the media.

EXAMPLES OF WHAT YOU HANDLE:
- "when the chimpanzee appears" → "at 23.4 seconds when the chimpanzee is visible"
- "match the dominant color" → "use color #3A7BD4 (the dominant blue from the sky)"
- "complement the mood" → "use warm orange tones (#FF8C42) to complement the sunset atmosphere"
- "where the text is readable" → "position at top-left to avoid the bright water area"
- "don't cover the person" → "position at bottom-right since person is centered in frame"
- "place it where there's space" → "position at 25% from left, 80% from top in the dark forest area"
- "avoid the action" → "position at top-center since the car chase happens in bottom half"
- "where it won't interfere" → "position at 15%, 20% to avoid the bird flying across center"

CRITICAL: VIDEO-TO-COMPOSITION TIMING CONVERSION
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

OUTPUT FORMAT: Return the enhanced request with content-based ambiguities resolved using specific details from the media analysis, with all timing converted to composition seconds.

⚠️ CRITICAL: Your output must be clearly actionable for a Remotion LLM code generator:
- Use precise technical specifications (hex colors, exact coordinates, frame numbers)
- Provide concrete measurements and timing values
- Include all necessary parameters for immediate Remotion component implementation
- Ensure the request can be executed without further clarification or analysis

ENHANCED OUTPUT EXAMPLE:
Input: "add text when the sunset looks beautiful"
Output: "Add text overlay with content 'Golden Hour Magic', fontSize 56px, fontFamily 'Inter', color #FFFFFF, backgroundColor rgba(255,140,66,0.8), positioned at 50% left, 15% top, appearing from frame 1080 to frame 1380 (36.0s to 46.0s in composition) when the sunset reaches peak orange saturation #FF8C42 in the sky"

Return ONLY the enhanced request as a single, comprehensive instruction."""

        # Call Gemini for analysis
        response = gemini_api.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                *[gemini_api.files.get(name=file_ref['gemini_file_id']) for file_ref in gemini_file_refs],
                analysis_prompt
            ]
        )
        
        enhanced_final_request = response.text.strip()
        
        print(f"✅ Analyzer: Enhanced request: '{enhanced_final_request[:100]}...'")
        
        return AnalysisResult(
            enhanced_request=enhanced_final_request,
            media_analysis={
                "analyzed_files": [ref['name'] for ref in gemini_file_refs],
                "gemini_files_used": [ref['gemini_file_id'] for ref in gemini_file_refs],
                "composition_duration": total_duration,
                "status": "analyzed"
            },
            visual_context={
                "files_processed": len(gemini_file_refs),
                "composition_context_used": True,
                "composition_duration": total_duration,
                "status": "completed"
            }
        )
        
    except Exception as e:
        print(f"❌ Analyzer: Failed to analyze media - {str(e)}")
        
        # Return original request if analysis fails
        return AnalysisResult(
            enhanced_request=enhanced_request,
            media_analysis={"status": "analysis_failed", "error": str(e)},
            visual_context={"status": "analysis_failed", "error": str(e)}
        )
