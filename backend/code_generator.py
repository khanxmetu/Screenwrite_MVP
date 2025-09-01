import os
import json
import time
import re
from typing import Tuple, List, Dict, Any, Optional
from google import genai
from google.genai import types
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
import anthropic


def create_simplified_system_instruction(original_system_instruction: str) -> str:
    """
    Create a simplified system instruction ONLY for fine-tuning by removing the bloated template
    but keeping the essential rules and API reference.
    """
    simplified = """You are a world-class Remotion developer. Update the composition based on user requests.

🎯 **CURATED API REFERENCE** - Use ONLY these verified components:

**CORE ANIMATION:**
• AbsoluteFill: Main container component for layouts
• Sequence: Timeline control with {from: number, durationInFrames: number, children: ReactNode}
• useCurrentFrame(): Returns current frame number (call at component level)
• useVideoConfig(): Returns {width, height, fps, durationInFrames}
• interpolate(frame, inputRange, outputRange, options?): Animate numeric values
• spring({frame, fps, config}): Physics-based animations with {damping: number, stiffness: number}

**MEDIA COMPONENTS:**
• Video: {src: string, trimBefore?: number, trimAfter?: number, volume?: number, playbackRate?: number, muted?: boolean, style?: object}
• Audio: {src: string, trimBefore?: number, trimAfter?: number, volume?: number, playbackRate?: number, muted?: boolean}
• Img: {src: string, style?: object, placeholder?: string}

**EXECUTION CONTEXT:**
- Code executes in React.createElement environment with Function() constructor
- Use React.createElement syntax, not JSX
- Use 'div' elements for text (no Text component in Remotion)

⚠️ **CRITICAL**: Only change/add what the user specifically asks for. Keep EVERYTHING else UNCHANGED.

**CRITICAL**: DO NOT include any import statements in your code. All necessary imports (React, useCurrentFrame, useVideoConfig, spring, interpolate, AbsoluteFill, etc.) are already provided. Start your code directly with variable declarations and function calls.

**CRITICAL**: DO NOT define 'frame' variable - it is already available in the execution environment. Never include `const frame = useCurrentFrame();` in your generated code. Just use it!

RESPONSE FORMAT - You must respond with EXACTLY this structure:
DURATION: [number in seconds based on composition content and timing]
CODE:
[raw JavaScript code - no markdown blocks]"""
    
    return simplified


def log_conversation_for_fine_tuning(system_instruction: str, user_prompt: str, ai_response: str, dataset_file: str = "fine_tuning_dataset.jsonl"):
    """
    Log conversation in Gemini fine-tuning format (JSONL) for dataset creation.
    Each line is a complete conversation with system instruction and user/model exchange.
    Uses a simplified system instruction without the bloated template.
    """
    try:
        # Use simplified system instruction for fine-tuning (removes bloated examples)
        simplified_system_instruction = create_simplified_system_instruction(system_instruction)
        
        # Create the conversation entry in Gemini fine-tuning format
        conversation_entry = {
            "systemInstruction": {
                "role": "system",
                "parts": [
                    {
                        "text": simplified_system_instruction
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": user_prompt
                        }
                    ]
                },
                {
                    "role": "model",
                    "parts": [
                        {
                            "text": ai_response
                        }
                    ]
                }
            ]
        }
        
        # Ensure fine-tuning directory exists
        dataset_path = os.path.join("logs", "fine-tuning", dataset_file)
        os.makedirs(os.path.join("logs", "fine-tuning"), exist_ok=True)
        
        # Append to JSONL file (each line is a complete JSON object)
        with open(dataset_path, "a", encoding="utf-8") as f:
            # Add timestamp at the beginning of the line for reference
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] ")
            json.dump(conversation_entry, f, ensure_ascii=False)
            f.write("\n")  # JSONL format: one JSON object per line
        
        # Count total lines for feedback
        line_count = 0
        if os.path.exists(dataset_path):
            with open(dataset_path, "r", encoding="utf-8") as f:
                line_count = sum(1 for line in f if line.strip())
        
        print(f"💾 Fine-tuning conversation logged to: {dataset_path} (total entries: {line_count})")
        
    except Exception as e:
        print(f"❌ Error logging fine-tuning conversation: {e}")


def manage_fine_tuning_dataset(action: str = "list", entry_index: Optional[int] = None, dataset_file: str = "fine_tuning_dataset.jsonl"):
    """
    Helper function to manage the fine-tuning dataset (JSONL format).
    Actions: 'list' (show all entries), 'remove' (remove by line number), 'clear' (remove all)
    """
    try:
        dataset_path = os.path.join("logs", "fine-tuning", dataset_file)
        
        if not os.path.exists(dataset_path):
            print(f"📂 No dataset file found at: {dataset_path}")
            return
        
        # Read all lines from JSONL file
        entries = []
        with open(dataset_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f):
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        entries.append((line_num + 1, entry))
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Skipping invalid JSON on line {line_num + 1}: {e}")
        
        if action == "list":
            print(f"📊 Fine-tuning dataset has {len(entries)} entries:")
            for i, (line_num, entry) in enumerate(entries):
                user_text = entry["contents"][0]["parts"][0]["text"][:100]
                print(f"  {i}: (line {line_num}) {user_text}...")
                
        elif action == "remove" and entry_index is not None:
            if 0 <= entry_index < len(entries):
                # Remove entry by recreating file without that line
                removed_entry = entries[entry_index][1]
                user_text = removed_entry["contents"][0]["parts"][0]["text"][:100]
                print(f"🗑️ Removing entry {entry_index}: {user_text}...")
                
                # Write all entries except the removed one
                with open(dataset_path, "w", encoding="utf-8") as f:
                    for i, (_, entry) in enumerate(entries):
                        if i != entry_index:
                            json.dump(entry, f, ensure_ascii=False)
                            f.write("\n")
                
                print(f"💾 Dataset updated. Remaining entries: {len(entries) - 1}")
            else:
                print(f"❌ Invalid index {entry_index}. Dataset has {len(entries)} entries.")
                
        elif action == "clear":
            with open(dataset_path, "w", encoding="utf-8") as f:
                pass  # Empty file
            print(f"🧹 Cleared all entries from dataset.")
            
        else:
            print(f"❌ Unknown action: {action}. Use 'list', 'remove', or 'clear'.")
            
    except Exception as e:
        print(f"❌ Error managing dataset: {e}")


def parse_ai_response(response_text: str) -> Tuple[float, str]:
    """
    Parse AI response to extract duration and code.
    Expected format:
    DURATION: 12
    CODE:
    [JavaScript code]
    
    Returns (duration, code)
    """
    try:
        print(f"Parsing AI response. Full response:\n{response_text}")
        
        lines = response_text.strip().split('\n')
        duration = None  # No default, force explicit parsing
        code = ""
        
        # Look for DURATION line
        duration_found = False
        code_started = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            print(f"Processing line {i}: '{line}'")
            
            # Parse duration - be more flexible with format
            if line.upper().startswith('DURATION:') and not duration_found:
                try:
                    duration_str = line[9:].strip()  # Remove 'DURATION:' prefix
                    print(f"Attempting to parse duration from: '{duration_str}'")
                    duration = float(duration_str)
                    duration_found = True
                    print(f"✅ Successfully extracted AI duration: {duration} seconds")
                except ValueError as e:
                    print(f"❌ Failed to parse duration from: '{line}', error: {e}")
                continue
            
            # Start collecting code after CODE: line
            if line.upper() == 'CODE:' and not code_started:
                print(f"Found CODE: marker at line {i}")
                code_started = True
                # Collect all remaining lines as code
                code_lines = lines[i+1:]
                code = '\n'.join(code_lines)
                print(f"Extracted {len(code_lines)} lines of code")
                break
        
        # Fallback: if no structured format found, treat entire response as code
        if not code_started:
            print("⚠️ No structured format found, treating entire response as code")
            code = response_text.strip()
            
        # If no duration found, estimate from code as fallback
        if duration is None:
            print("⚠️ No AI duration found, estimating from code analysis...")
            duration = estimate_duration_from_code(code)
            print(f"📊 Estimated duration: {duration} seconds")
        else:
            print(f"🎯 Using AI-determined duration: {duration} seconds")
            
        # Ensure we have some code
        if not code.strip():
            raise ValueError("No code found in AI response")
            
        print(f"✅ Final parsed result - Duration: {duration}s, Code length: {len(code)} chars")
        return duration, code
        
    except Exception as e:
        print(f"❌ Error parsing AI response: {e}")
        # Return fallback values with estimation
        estimated_duration = estimate_duration_from_code(response_text)
        print(f"📊 Using estimated fallback duration: {estimated_duration} seconds")
        return estimated_duration, response_text.strip()


def estimate_duration_from_code(code: str) -> float:
    """
    Estimate duration by analyzing the code for frame numbers and timing.
    Assumes 30 FPS and calculates based on the highest frame usage.
    """
    try:
        import re
        
        print(f"🔍 Analyzing code for duration calculation...")
        
        max_frame = 0
        fps = 30  # Assume 30 FPS
        
        # Find all numeric values that could be frame numbers
        # Look for interpolate calls: interpolate(frame, [start, end, ...], ...)
        interpolate_patterns = [
            r'interpolate\s*\([^,]+,\s*\[([^\]]+)\]',  # Basic interpolate pattern
            r'interpolate\s*\(\s*frame\s*,\s*\[([^\]]+)\]',  # More specific
        ]
        
        for pattern in interpolate_patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            for match in matches:
                try:
                    # Extract frame numbers from the array
                    frame_str = match.replace(' ', '')
                    # Handle various formats: "0,30,60" or "0, 30, 60" etc.
                    frames = []
                    for part in frame_str.split(','):
                        part = part.strip()
                        # Handle expressions like "fps * 15" or "startFrame + 30"
                        if any(op in part for op in ['*', '+', '-', '/']):
                            # Try to extract numbers from expressions
                            numbers = re.findall(r'\d+(?:\.\d+)?', part)
                            for num_str in numbers:
                                try:
                                    frames.append(float(num_str))
                                except:
                                    continue
                        else:
                            try:
                                frames.append(float(part))
                            except:
                                continue
                    
                    if frames:
                        frame_max = max(frames)
                        max_frame = max(max_frame, frame_max)
                        print(f"📊 Found interpolate frames: {frames}, max: {frame_max}")
                except Exception as e:
                    print(f"⚠️ Error parsing frame range '{match}': {e}")
                    continue
        
        # Look for spring delays: frame - delay_value
        spring_delays = re.findall(r'frame\s*-\s*(\d+(?:\.\d+)?)', code, re.IGNORECASE)
        for delay_str in spring_delays:
            try:
                delay = float(delay_str)
                # Spring animations typically need 2-3 seconds to complete
                estimated_spring_end = delay + (fps * 2.5)  # 2.5 seconds for spring completion
                max_frame = max(max_frame, estimated_spring_end)
                print(f"📊 Found spring delay: {delay}, estimated end frame: {estimated_spring_end}")
            except:
                continue
        
        # Look for explicit fps calculations: fps * seconds
        fps_multiplications = re.findall(r'fps\s*\*\s*(\d+(?:\.\d+)?)', code, re.IGNORECASE)
        for mult_str in fps_multiplications:
            try:
                seconds = float(mult_str)
                estimated_frame = fps * seconds
                max_frame = max(max_frame, estimated_frame)
                print(f"📊 Found fps multiplication: fps * {seconds} = {estimated_frame} frames")
            except:
                continue
        
        # Look for direct frame numbers in code (common in timing calculations)
        direct_frames = re.findall(r'(?:frame|startFrame|endFrame)\s*[=+\-]\s*(\d+(?:\.\d+)?)', code, re.IGNORECASE)
        for frame_str in direct_frames:
            try:
                frame_num = float(frame_str)
                max_frame = max(max_frame, frame_num)
                print(f"📊 Found direct frame reference: {frame_num}")
            except:
                continue
        
        # Look for large numeric constants that might be frame numbers
        large_numbers = re.findall(r'\b(\d{2,4}(?:\.\d+)?)\b', code)
        for num_str in large_numbers:
            try:
                num = float(num_str)
                # Only consider numbers that could reasonably be frame numbers (30-3600 for 1-120 seconds)
                if 30 <= num <= 3600:
                    max_frame = max(max_frame, num)
                    print(f"📊 Found potential frame number: {num}")
            except:
                continue
        
        if max_frame > 0:
            # Calculate duration and add buffer
            calculated_duration = (max_frame / fps) + 1.0  # Add 1 second buffer
            print(f"🎯 Duration calculation: max_frame={max_frame}, fps={fps}, duration={calculated_duration}s")
            return round(calculated_duration, 1)  # Round to 1 decimal place
        else:
            # Fallback based on code complexity
            code_length = len(code)
            if code_length < 500:
                duration = 5.0
            elif code_length < 1500:
                duration = 8.0
            elif code_length < 3000:
                duration = 12.0
            else:
                duration = 15.0
            
            print(f"📊 No frame analysis possible, using code-length-based estimation: {duration}s (code length: {code_length})")
            return duration
                
    except Exception as e:
        print(f"❌ Error in duration estimation: {e}")
        return 8.0  # Conservative fallback


def build_edit_prompt(request: Dict[str, Any]) -> tuple[str, str]:
    """Build system instruction and user prompt for first attempt"""
    
    # Get media assets
    media_library = request.get('media_library', [])
    media_section = ""
    if media_library and len(media_library) > 0:
        media_section = "\nAVAILABLE MEDIA ASSETS:\n"
        for media in media_library:
            name = media.get('name', 'unnamed')
            media_type = media.get('mediaType', 'unknown')
            duration = media.get('durationInSeconds', 0)
            media_width = media.get('media_width', 0)
            media_height = media.get('media_height', 0)
            media_url_local = media.get('mediaUrlLocal', '')
            media_url_remote = media.get('mediaUrlRemote', '')
            
            # Determine which URL to use (prefer remote static URL, fallback to local blob URL)
            actual_url = media_url_remote if media_url_remote else media_url_local
            
            # Build comprehensive media description with metadata
            if media_type == 'video':
                media_info = f"- {name}: Video"
                if media_width and media_height:
                    media_info += f" ({media_width}x{media_height})"
                if duration:
                    media_info += f" ({duration}s)"
                media_info += f" - URL: {actual_url}\n"
                media_section += media_info
            elif media_type == 'image':
                media_info = f"- {name}: Image"
                if media_width and media_height:
                    media_info += f" ({media_width}x{media_height})"
                media_info += f" - URL: {actual_url}\n"
                media_section += media_info
            elif media_type == 'audio':
                media_info = f"- {name}: Audio"
                if duration:
                    media_info += f" ({duration}s)"
                media_info += f" - URL: {actual_url}\n"
                media_section += media_info
        media_section += "\n⚠️ CRITICAL: Use the EXACT URLs provided above in Video/Img/Audio src props. Never use filenames like 'video.mp4' - always use the full URL.\n"
        media_section += "⚠️ EXAMPLE: src: 'https://example.com/file.mp4' NOT src: 'filename.mp4'\n"
    else:
        media_section = "\nNo media assets available. Create compositions using text, shapes, and animations.\n"
    
    # System instruction with role and rules
    system_instruction = """You are a world-class Remotion developer. Update the composition based on user requests.

🎯 **CURATED API REFERENCE** - Use ONLY these verified components:

**CORE ANIMATION:**
• AbsoluteFill: Main container component for layouts
• Sequence: Timeline control with {{from: number, durationInFrames: number, children: ReactNode}}
• useCurrentFrame(): Returns current frame number (call at component level)
• useVideoConfig(): Returns {width, height, fps, durationInFrames}
• interpolate(frame, inputRange, outputRange, options?): Animate numeric values
• spring({frame, fps, config}): Physics-based animations with {damping: number, stiffness: number}

🚨 **CRITICAL TIMING RULE: GLOBAL vs SEQUENCE-RELATIVE FRAMES**

**⚠️ MOST COMMON BUG: Using sequence-relative timing in interpolate()**

The `frame` variable in `interpolate()` is ALWAYS the GLOBAL frame number, NOT relative to the Sequence start!

**❌ WRONG (sequence-relative timing):**
```javascript
React.createElement(Sequence, {{
  from: timeToFrames(5.5),  // Sequence starts at 5.5s globally
  durationInFrames: timeToFrames(3)
}}, (() => {{
  // WRONG: Using sequence-relative timing [0, 0.5, 2.5, 3]
  const opacity = interpolate(frame, [0, timeToFrames(0.5), timeToFrames(2.5), timeToFrames(3)], [0, 1, 1, 0]);
  // This will animate at wrong times because frame is GLOBAL!
```

**✅ CORRECT (global timing):**
```javascript
React.createElement(Sequence, {{
  from: timeToFrames(5.5),  // Sequence starts at 5.5s globally
  durationInFrames: timeToFrames(3)
}}, (() => {{
  // CORRECT: Using global timing [5.5, 6, 8, 8.5]
  const opacity = interpolate(frame, [timeToFrames(5.5), timeToFrames(6), timeToFrames(8), timeToFrames(8.5)], [0, 1, 1, 0]);
  // This animates from 5.5s-6s (fade in) and 8s-8.5s (fade out) GLOBALLY
```

**🎯 TIMING CALCULATION FORMULA:**
1. When should text appear globally? → Use that exact time in interpolate()
2. Text at 10s globally → `timeToFrames(10)` in interpolate array
3. NEVER use `[0, timeToFrames(0.5), ...]` unless Sequence starts at 0s!

**MEDIA COMPONENTS:**
• Video: {src: string, trimBefore?: number, trimAfter?: number, volume?: number, playbackRate?: number, muted?: boolean, style?: object}
• Audio: {src: string, trimBefore?: number, trimAfter?: number, volume?: number, playbackRate?: number, muted?: boolean}
• Img: {src: string, style?: object, placeholder?: string}

⚠️ CRITICAL TRIMMING RULE: trimBefore and trimAfter use FRAMES, not seconds!
→ Always use timeToFrames(): timeToFrames(155) converts 155 seconds to frames

🚨 **CRITICAL TRIM CALCULATION - MUST GET THIS RIGHT:**

**Understanding trimBefore and trimAfter:**
- `trimBefore`: Start time in source video (in frames)
- `trimAfter`: End time in source video (in frames)  
- These define which portion of the source video to play

**✅ CORRECT CALCULATION:**
**🎯 SIMPLE FORMULA - ALWAYS USE THIS:**
```javascript
// To play from 14s to 16.6s in source video (2.6s duration):
const startSeconds = 14; // Where to start in source video
const playSeconds = 2.6; // How long to play

const trimBefore = timeToFrames(startSeconds);
const trimAfter = timeToFrames(startSeconds + playSeconds);

// VALIDATION: trimAfter must ALWAYS be > trimBefore
if (trimAfter <= trimBefore) {
  throw new Error("trimAfter must be greater than trimBefore");
}
```

⚠️ CRITICAL MEDIA RULE: When using Video/Audio/Img components, ALWAYS use the exact URL from the AVAILABLE MEDIA ASSETS section above. 
NEVER use just the filename - always use the full URL provided in the "URL:" field.

EXAMPLE CORRECT USAGE:
- If media shows "video.mp4 - URL: https://example.com/video.mp4", use src: "https://example.com/video.mp4"
- NOT src: "video.mp4"

**TRANSITION EFFECTS (from @remotion/transitions):**

🚨 **USE TransitionSeries FOR ALL MEDIA TRANSITIONS - NOT manual interpolation**

**🚨 CRITICAL OVERLAP TIMING RULE (FROM REMOTION DOCS):**
**TransitionSeries.Sequence durations = intended clip durations (USE FULL DURATIONS)**
- Each sequence uses its full intended durationInFrames
- Transitions create overlaps that REDUCE total timeline duration  
- Formula: Total = Seq1Duration + Seq2Duration - TransitionDuration

**OVERLAP EXAMPLE (VERIFIED WITH REMOTION DOCS):**
Synth: "Beach 7s, 0.5s crossfade, Forest 5s" 
```javascript
React.createElement(TransitionSeries.Sequence, {durationInFrames: timeToFrames(7)}, // Full 7s
  React.createElement(Video, {...})),
React.createElement(TransitionSeries.Transition, {
  timing: linearTiming({durationInFrames: timeToFrames(0.5)}), // 0.5s transition
  presentation: fade()
}),
React.createElement(TransitionSeries.Sequence, {durationInFrames: timeToFrames(5)}, // Full 5s
  React.createElement(Video, {...}))
```
**Result:** Total composition = 11.5s (7+5-0.5), sequences overlap during transition automatically!

**TransitionSeries Components:**
• TransitionSeries: Container for sequences with transitions between them
• TransitionSeries.Sequence: Individual scenes with durationInFrames
• TransitionSeries.Transition: Transitions between sequences with timing and presentation

**🚨 CRITICAL: EMPTY SEQUENCE PREVENTION**
**NEVER create empty TransitionSeries.Sequence components!**
```javascript
// ❌ WRONG - Empty sequence (causes runtime error):
React.createElement(TransitionSeries.Sequence, {durationInFrames: timeToFrames(3)})

// ✅ CORRECT - Sequence with content (duration = actual content duration):
React.createElement(TransitionSeries.Sequence, {durationInFrames: timeToFrames(6)},
  React.createElement(Video, {
    src: "...",
    trimBefore: timeToFrames(10),
    trimAfter: timeToFrames(16)  // 6 seconds of content
  }))
```
**RULE:** Every TransitionSeries.Sequence MUST contain child elements AND durationInFrames should match the actual content duration (NOT content + transition duration)

**🚨 CRITICAL: FADE ENDINGS**
**For fade endings, you MUST include a final sequence after the transition!**
```javascript
// ❌ WRONG - Ends with transition (causes hard cut):
React.createElement(TransitionSeries.Sequence, {...video...}),
React.createElement(TransitionSeries.Transition, {presentation: fade()})  // Hard cut!

// ✅ CORRECT - Fade to final sequence:
React.createElement(TransitionSeries.Sequence, {...video...}),
React.createElement(TransitionSeries.Transition, {
  timing: linearTiming({durationInFrames: timeToFrames(1)}),
  presentation: fade()
}),
React.createElement(TransitionSeries.Sequence, {
  durationInFrames: timeToFrames(2)  // Final sequence duration
}, React.createElement('div', {style: {backgroundColor: '#000000', width: '100%', height: '100%'}}))
```
**RULE:** Transitions need a target sequence to fade INTO. For fade endings, create a final sequence with appropriate content.


**Transition Functions Available:**
• fade(): Simple opacity transition between scenes
• slide(): Slide transition with direction: {direction: "from-left" | "from-right" | "from-top" | "from-bottom"}
• wipe(): Slide over transition (wipe effect)
• flip(): 3D rotation transition
• iris(): Circular reveal transition

**Timing Functions Available:**
• linearTiming({durationInFrames: number, easing?: Easing}): Linear timing with optional easing
• springTiming({config?: {damping: number, stiffness: number}, durationInFrames?: number}): Spring-based timing

🚨 **CRITICAL TRANSITION RULES:**
✅ REQUIRED: TransitionSeries.Transition with presentation: fade() for ALL Video/Audio fade effects
✅ REQUIRED: TransitionSeries.Transition with presentation: slide() for ALL Video/Audio slide effects
✅ REQUIRED: Use linearTiming() or springTiming() for transition duration

**CORRECT TransitionSeries USAGE PATTERNS:**

**Pattern 1: Single Video with Fade-in (Entry Animation):**
```javascript
React.createElement(TransitionSeries, {},
  React.createElement(TransitionSeries.Transition, {
    timing: linearTiming({durationInFrames: timeToFrames(1.5)}),
    presentation: fade()
  }),
  React.createElement(TransitionSeries.Sequence, {durationInFrames: timeToFrames(5)},
    React.createElement(Video, {
      src: 'https://example.com/video.mp4',
      trimBefore: timeToFrames(10),
      trimAfter: timeToFrames(15)
    })
  )
)
```

**Pattern 2: Single Video with Fade-out (Exit Animation):**
```javascript
React.createElement(TransitionSeries, {},
  React.createElement(TransitionSeries.Sequence, {durationInFrames: timeToFrames(5)},
    React.createElement(Video, {
      src: 'https://example.com/video.mp4',
      trimBefore: timeToFrames(10),
      trimAfter: timeToFrames(15)
    })
  ),
  React.createElement(TransitionSeries.Transition, {
    timing: linearTiming({durationInFrames: timeToFrames(1.5)}),
    presentation: fade()
  })
)
```

**Pattern 3: Multiple Videos with Transitions Between:**
```javascript
React.createElement(TransitionSeries, {},
  React.createElement(TransitionSeries.Sequence, {durationInFrames: timeToFrames(3)},
    React.createElement(Video, {src: 'https://example.com/video1.mp4'})),
  React.createElement(TransitionSeries.Transition, {
    timing: linearTiming({durationInFrames: timeToFrames(1)}),
    presentation: fade()
  }),
  React.createElement(TransitionSeries.Sequence, {durationInFrames: timeToFrames(3)},
    React.createElement(Video, {src: 'https://example.com/video2.mp4'})),
  React.createElement(TransitionSeries.Transition, {
    timing: springTiming({config: {damping: 200}}),
    presentation: slide({direction: "from-right"})
  }),
  React.createElement(TransitionSeries.Sequence, {durationInFrames: timeToFrames(3)},
    React.createElement(Video, {src: 'https://example.com/video3.mp4'}))
)
```

**Pattern 4: Advanced Timing Examples:**
```javascript
// Linear timing with easing
linearTiming({
  durationInFrames: timeToFrames(2),
  easing: Easing.inOut(Easing.ease)
})

// Spring timing with custom config
springTiming({
  config: {damping: 200, stiffness: 100},
  durationInFrames: timeToFrames(1.5),
  durationRestThreshold: 0.001 // Recommended for smooth transitions
})
```

**EASING FUNCTIONS** - Use EXACT syntax:
✅ CORRECT: easing: Easing.linear, easing: Easing.ease, easing: Easing.quad, easing: Easing.cubic
✅ CORRECT: easing: Easing.sin, easing: Easing.circle, easing: Easing.exp, easing: Easing.bounce
✅ CORRECT: easing: Easing.in(Easing.quad), easing: Easing.out(Easing.quad), easing: Easing.inOut(Easing.quad)
✅ CORRECT: easing: Easing.bezier(0.4, 0.0, 0.2, 1)
❌ WRONG: easing: 'ease-in-out', easing: 'easeInOut', easing: 'linear'

**EXECUTION CONTEXT:**
- Code executes in React.createElement environment with Function() constructor
- Use React.createElement syntax, not JSX
- Use 'div' elements for text (no Text component in Remotion)
⚠️ **CRITICAL RULES:**

1. **🚨 FRAME USAGE IN SEQUENCES - Use 'frame' variable directly:**
   ✅ CORRECT: Use frame variable directly (it's pre-defined in execution environment)
   ```javascript
   React.createElement(Sequence, {}, (() => {
     const opacity = interpolate(frame, [0, 30], [0, 1]);
     return React.createElement('div', {style: {opacity}}, 'Text');
   })())
   ```
   ❌ FORBIDDEN: Never call useCurrentFrame() inside Sequence children (breaks Rules of Hooks)
   ```javascript
   React.createElement(Sequence, {}, (() => {
     const currentFrame = useCurrentFrame(); // ❌ FATAL ERROR
   })())
   ```
   → ALWAYS use the pre-defined 'frame' variable directly

3. **interpolate() OUTPUT TYPES:**
   ✅ CORRECT: interpolate(frame, [0, 100], [0, 1, 0.5]) // Numbers only
   ❌ WRONG: interpolate(frame, [0, 100], ['hidden', 'visible']) // No strings
   ❌ WRONG: interpolate(frame, [0, 100], [true, false]) // No booleans
   → For strings: Use conditionals instead: opacity > 0.5 ? 'block' : 'none'

4. **EASING SYNTAX:**
   ✅ CORRECT: {easing: Easing.inOut(Easing.quad)}
   ❌ WRONG: {easing: 'ease-in-out'}

5. **CSS PROPERTIES:**
   ✅ CORRECT: backgroundColor, fontSize, fontWeight, borderRadius
   ❌ WRONG: background-color, font-size, font-weight, border-radius

6. **SPRING CONFIG:**
   ✅ CORRECT: {damping: 12, stiffness: 80}
   ❌ WRONG: {dampening: 12, stiffness: 80}

7. **SEQUENCE CHILDREN:**
   ✅ CORRECT: React.createElement(Sequence, {from: 0, durationInFrames: 60, children: content})

8. **DOM LAYERING:** Elements rendered LATER appear ON TOP. Place overlays AFTER background elements.
   ⚠️ **TEXT OVER VIDEO CRITICAL:** Text elements MUST include `zIndex` to ensure visibility over video content.
   ✅ CORRECT: style: { position: 'absolute', zIndex: 10, color: 'white', ... }
   ❌ WRONG: style: { position: 'absolute', color: 'white', ... } // Missing zIndex - text may be hidden behind video

📐 **POSITIONING FUNDAMENTALS - MASTER THESE PATTERNS:**

**🎯 CENTER EVERYTHING (Most Common Need):**
```javascript
// Perfect center (horizontal + vertical)
style: {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  textAlign: 'center' // Only for text centering within element
}
```

**🎯 SPECIFIC POSITIONING PATTERNS:**
```javascript
// Top-left corner
style: { position: 'absolute', top: 0, left: 0 }

// Top-right corner  
style: { position: 'absolute', top: 0, right: 0 }

// Bottom-left corner
style: { position: 'absolute', bottom: 0, left: 0 }

// Bottom-right corner
style: { position: 'absolute', bottom: 0, right: 0 }

// Center horizontally, specific vertical position
style: { 
  position: 'absolute', 
  left: '50%', 
  transform: 'translateX(-50%)',
  top: '20px' // or bottom: '20px'
}

// Center vertically, specific horizontal position  
style: { 
  position: 'absolute', 
  top: '50%', 
  transform: 'translateY(-50%)',
  left: '20px' // or right: '20px'
}
```

**🚨 CRITICAL POSITIONING RULES:**

1. **ALWAYS use position: 'absolute'** for precise placement
2. **NEVER rely on textAlign: 'center' alone** - it only centers text within its container
3. **Use transform: 'translate(-50%, -50%)' for true centering** - this centers the element itself
4. **Combine positioning methods:** 
   - `left: '50%'` moves element's left edge to center
   - `transform: 'translateX(-50%)'` moves element back by half its width
   - Result: element is perfectly centered

**❌ POSITIONING MISTAKES TO AVOID:**
```javascript
// WRONG - Won't center the element, only text inside it
style: { textAlign: 'center' }

// WRONG - Element's left edge will be at center, not element center  
style: { position: 'absolute', left: '50%' }

// WRONG - Missing position absolute
style: { top: '50%', left: '50%' }
```

**✅ CORRECT POSITIONING EXAMPLES:**
```javascript
// Title centered on screen
style: { 
  position: 'absolute', 
  top: '50%', 
  left: '50%', 
  transform: 'translate(-50%, -50%)',
  fontSize: '48px',
  color: '#FFFFFF',
  textAlign: 'center'
}

// Subtitle below center
style: { 
  position: 'absolute', 
  top: '60%', 
  left: '50%', 
  transform: 'translateX(-50%)',
  fontSize: '24px'
}

// Corner overlay text
style: { 
  position: 'absolute', 
  bottom: '20px', 
  left: '20px',
  fontSize: '18px'
}
```


⚠️ **COMMON MISTAKES TO AVOID:**
❌ display: interpolate(frame, [0, 60], ['none', 'block']) 
✅ display: interpolate(frame, [0, 60], [0, 1]) > 0.5 ? 'block' : 'none'

❌ backgroundColor: interpolate(frame, [0, 60], ['red', 'blue'])
✅ backgroundColor: frame < 30 ? '#ff0000' : '#0000ff'

❌ transform: interpolate(frame, [0, 60], ['scale(0)', 'scale(1)'])
✅ transform: `scale(${interpolate(frame, [0, 60], [0, 1])})`

⚠️ **CRITICAL**: Only change/add what the user specifically asks for. Keep EVERYTHING else UNCHANGED.

⚠️ **PRE-SUBMISSION CHECKLIST:**
Before submitting your code, verify:
- [ ] 🚨 Code MUST start with `return` statement - function must return JSX
- [ ] 🚨 NO useCurrentFrame() calls inside Sequence children - USE 'frame' variable directly
- [ ] 🚨 NO frame variable definition - it's already available in execution environment
- [ ] 🚨 NO manual interpolation for fade/slide/wipe on Video/Audio - USE TransitionSeries.Transition ALWAYS
- [ ] 🚨 NO style: { opacity: interpolate(...) } on Video/Audio components
- [ ] No import statements included
- [ ] NO timeToFrames() function definition - it's already provided
- [ ] All constants use UPPER_SNAKE_CASE, variables use camelCase
- [ ] NO abbreviations used anywhere (full descriptive names only)
- [ ] Naming conventions are consistent throughout the code
- [ ] No string/boolean outputs in interpolate() calls
- [ ] Proper React.createElement syntax used

RESPONSE FORMAT - You must respond with EXACTLY this structure:
DURATION: [number in seconds based on composition content and timing]
CODE:
[raw JavaScript code - no markdown blocks]

🚨 **CRITICAL**: Your generated code MUST start with a `return` statement. The code is executed inside a function, so it must return the JSX element.

✅ CORRECT: `return React.createElement(AbsoluteFill, {}, ...)`
❌ WRONG: `React.createElement(AbsoluteFill, {}, ...)` (missing return)

# Complete Remotion Composition Template

## EXAMPLE RESPONSE:
DURATION: 12
CODE:

return React.createElement(AbsoluteFill, {
  style: { backgroundColor: '#000000' }
},
  // Your composition content here
  React.createElement('div', {
    style: {
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      color: 'white',
      fontSize: '48px'
    }
  }, 'Sample Content')
);

const { width, height, fps } = useVideoConfig();

// 🚨 CRITICAL: In Sequence children, use the 'frame' variable directly - it's already available
// ✅ CORRECT: Use frame variable directly in Sequences
// React.createElement(Sequence, {}, (() => {
//   const opacity = interpolate(frame, [0, 30], [0, 1]);
//   return React.createElement('div', {style: {opacity}}, 'Text');
// })())
//
// ❌ WRONG: Never call useCurrentFrame() inside Sequence children
// React.createElement(Sequence, {}, (() => {
//   const currentFrame = useCurrentFrame(); // ❌ FORBIDDEN - breaks Rules of Hooks
// })())
//
// ❌ WRONG: Never define frame variable - it's already available
// const frame = useCurrentFrame(); // ❌ FORBIDDEN - already defined

// TIMING CONSTANTS - Standard durations for consistency
const FADE_DURATION = 20;          // Standard fade in/out
const QUICK_TRANSITION = 10;       // Fast transitions
const CROSS_FADE_OVERLAP = 15;     // Overlap between sequences
const SPRING_DELAY = 30;           // Delay before spring animations

// CONTAINER CONSTANTS - Prevent size jumping
const TITLE_CONTAINER_HEIGHT = 120;
const SUBTITLE_CONTAINER_HEIGHT = 80;
const SAFE_ZONE_PADDING = 60;     // Safe area padding
const CARD_PADDING = 40;          // Internal card padding

// Z-INDEX LAYERS - Visual hierarchy
const Z_BACKGROUND = 1;
const Z_CONTENT = 2;
const Z_OVERLAY = 3;
const Z_UI = 4;

// SPRING CONFIG - Consistent easing
const STANDARD_SPRING = { damping: 12, stiffness: 80 };
const GENTLE_SPRING = { damping: 15, stiffness: 60 };
const BOUNCY_SPRING = { damping: 8, stiffness: 100 };

// FRAME CALCULATION HELPERS - Pre-defined functions
// timeToFrames(timeInSeconds) is already available - do not redefine

// === BACKGROUND LAYER WITH TRANSITIONS ===

// Use TransitionSeries for video sequences with proper transitions
React.createElement(TransitionSeries, {},
  // First video sequence
  React.createElement(TransitionSeries.Sequence, {
    durationInFrames: timeToFrames(3)
  }, React.createElement(Video, {
    src: 'https://example.com/video1.mp4',
    trimBefore: timeToFrames(5),   // Start at 5 seconds using timeToFrames
    trimAfter: timeToFrames(13),   // End at 13 seconds using timeToFrames
    style: {
      width: '100%',
      height: '100%',
      objectFit: 'cover'
    }
  })),
  
  // Transition between sequences
  React.createElement(TransitionSeries.Transition, {
    timing: linearTiming({durationInFrames: FADE_DURATION}),
    presentation: fade()
  }),
  
  // Second video sequence
  React.createElement(TransitionSeries.Sequence, {
    durationInFrames: timeToFrames(3)
  }, React.createElement(Video, {
    src: 'https://example.com/video2.mp4',
    trimBefore: timeToFrames(10),  // Start at 10 seconds using timeToFrames
    trimAfter: timeToFrames(20),   // End at 20 seconds using timeToFrames
    style: {
      width: '100%',
      height: '100%',
      objectFit: 'cover'
    }
  })),
  
  // Another transition
  React.createElement(TransitionSeries.Transition, {
    timing: linearTiming({durationInFrames: FADE_DURATION}),
    presentation: slide({direction: "from-left"})
  }),
  
  // Third video sequence  
  React.createElement(TransitionSeries.Sequence, {
    durationInFrames: timeToFrames(4)
  }, React.createElement(Video, {
    src: 'https://example.com/background.mp4',
    style: {
      width: '100%',
      height: '100%', 
      objectFit: 'cover',
      opacity: 0.6 // Reduced opacity for background
    }
  }))
),

// Background audio
React.createElement(Audio, {
  src: 'https://example.com/audio.mp3',
  trimBefore: 0,   // MODERN PROP - start from beginning
  trimAfter: timeToFrames(12)   // MODERN PROP - end at 12 seconds
}),

// === CONTENT LAYER (Z-INDEX 2) ===

// === POSITIONING EXAMPLES - Core Patterns ===

// PATTERN 1: CENTER ELEMENT - Perfect centering with fade transition
React.createElement(Sequence, {
  from: 0,
  durationInFrames: timeToFrames(2),
  children: (() => {
    const centerOpacity = interpolate(frame, [0, 15, timeToFrames(1.5), timeToFrames(2)], [0, 1, 1, 0]);
    const centerScale = interpolate(frame, [0, 20], [0.8, 1]);
    
    return React.createElement('div', {
      style: {
        // STANDARD CENTER PATTERN - Use this for perfect centering
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: `translate(-50%, -50%) scale(${centerScale})`,
        width: '300px',
        height: '100px',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        border: '2px solid rgba(255, 255, 255, 0.3)',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '18px',
        color: '#FFFFFF',
        opacity: centerOpacity,
        zIndex: Z_CONTENT
      }
    }, 'Perfect Center');
  })()
}),

// PATTERN 2: FILL WITH PADDING - Responsive containers with slide-in
React.createElement(Sequence, {
  from: timeToFrames(0.67),
  durationInFrames: timeToFrames(2),
  children: (() => {
    const fillOpacity = interpolate(frame, [timeToFrames(0.67), timeToFrames(1.17), timeToFrames(2.17), timeToFrames(2.67)], [0, 1, 1, 0]);
    const fillY = interpolate(frame, [timeToFrames(0.67), timeToFrames(1.33)], [20, 0]);
    
    return React.createElement('div', {
      style: {
        // FILL WITH PADDING PATTERN - Responsive to screen size
        position: 'absolute',
        top: '60px',
        left: '60px',
        right: '60px',
        bottom: '60px',
        backgroundColor: 'rgba(0, 0, 0, 0.1)',
        border: '2px solid rgba(255, 255, 255, 0.2)',
        borderRadius: '12px',
        padding: '20px',
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'flex-end',
        fontSize: '16px',
        color: '#FFFFFF',
        opacity: fillOpacity,
        transform: `translateY(${fillY}px)`,
        zIndex: Z_CONTENT
      }
    }, 'Fill Container');
  })()
}),

// PATTERN 3: SAFE ZONE POSITIONING - All corner and edge placements
React.createElement(Sequence, {
  from: timeToFrames(0.33),
  durationInFrames: timeToFrames(2.67),
  children: (() => {
    const safeOpacity = interpolate(frame, [timeToFrames(0.33), timeToFrames(0.83), timeToFrames(2.5), timeToFrames(3)], [0, 1, 1, 0]);
    const safeScale = interpolate(frame, [timeToFrames(0.33), timeToFrames(1)], [0.9, 1]);
    
    return React.createElement('div', {
      style: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        opacity: safeOpacity,
        transform: `scale(${safeScale})`,
        zIndex: Z_CONTENT
      }
    },
      // TOP-LEFT: Brand/Logo placement
      React.createElement('div', {
        style: {
          position: 'absolute',
          top: `${SAFE_ZONE_PADDING / 2}px`,      // 30px from top
          left: `${SAFE_ZONE_PADDING / 2}px`,     // 30px from left
          width: '120px',
          height: '40px',
          backgroundColor: 'rgba(76, 205, 196, 0.9)',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          color: '#FFFFFF',
          fontWeight: 'bold'
        }
      }, 'TOP-LEFT'),

      // TOP-RIGHT: Status/Info placement
      React.createElement('div', {
        style: {
          position: 'absolute',
          top: `${SAFE_ZONE_PADDING / 2}px`,      // 30px from top
          right: `${SAFE_ZONE_PADDING / 2}px`,    // 30px from right
          width: '120px',
          height: '40px',
          backgroundColor: 'rgba(255, 107, 107, 0.9)',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          color: '#FFFFFF',
          fontWeight: 'bold'
        }
      }, 'TOP-RIGHT'),

      // BOTTOM-LEFT: Secondary info placement
      React.createElement('div', {
        style: {
          position: 'absolute',
          bottom: `${SAFE_ZONE_PADDING / 2}px`,   // 30px from bottom
          left: `${SAFE_ZONE_PADDING / 2}px`,     // 30px from left
          width: '120px',
          height: '40px',
          backgroundColor: 'rgba(255, 195, 0, 0.9)',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          color: '#FFFFFF',
          fontWeight: 'bold'
        }
      }, 'BOTTOM-LEFT'),

      // BOTTOM-RIGHT: CTA/Action placement
      React.createElement('div', {
        style: {
          position: 'absolute',
          bottom: `${SAFE_ZONE_PADDING / 2}px`,   // 30px from bottom
          right: `${SAFE_ZONE_PADDING / 2}px`,    // 30px from right
          width: '120px',
          height: '40px',
          backgroundColor: 'rgba(138, 43, 226, 0.9)',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          color: '#FFFFFF',
          fontWeight: 'bold'
        }
      }, 'BOTTOM-RIGHT'),

      // TOP-CENTER: Title/Header placement
      React.createElement('div', {
        style: {
          position: 'absolute',
          top: `${SAFE_ZONE_PADDING / 2}px`,      // 30px from top
          left: '50%',
          transform: 'translateX(-50%)',
          width: '200px',
          height: '40px',
          backgroundColor: 'rgba(0, 123, 255, 0.9)',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          color: '#FFFFFF',
          fontWeight: 'bold'
        }
      }, 'TOP-CENTER'),

      // BOTTOM-CENTER: Progress/Status placement
      React.createElement('div', {
        style: {
          position: 'absolute',
          bottom: `${SAFE_ZONE_PADDING / 2}px`,   // 30px from bottom
          left: '50%',
          transform: 'translateX(-50%)',
          width: '200px',
          height: '40px',
          backgroundColor: 'rgba(40, 167, 69, 0.9)',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          color: '#FFFFFF',
          fontWeight: 'bold'
        }
      }, 'BOTTOM-CENTER'),

      // LEFT-CENTER: Navigation placement
      React.createElement('div', {
        style: {
          position: 'absolute',
          left: `${SAFE_ZONE_PADDING / 2}px`,     // 30px from left
          top: '50%',
          transform: 'translateY(-50%)',
          width: '80px',
          height: '100px',
          backgroundColor: 'rgba(108, 117, 125, 0.9)',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '10px',
          color: '#FFFFFF',
          fontWeight: 'bold',
          writingMode: 'vertical-rl'
        }
      }, 'LEFT-CENTER'),

      // RIGHT-CENTER: Sidebar placement
      React.createElement('div', {
        style: {
          position: 'absolute',
          right: `${SAFE_ZONE_PADDING / 2}px`,    // 30px from right
          top: '50%',
          transform: 'translateY(-50%)',
          width: '80px',
          height: '100px',
          backgroundColor: 'rgba(220, 53, 69, 0.9)',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '10px',
          color: '#FFFFFF',
          fontWeight: 'bold',
          writingMode: 'vertical-rl'
        }
      }, 'RIGHT-CENTER')
    );
  })()
}),

// === CONTENT LAYER ANIMATIONS ===
// For individual element animations, use interpolate() for complex effects

// Slide-in animation example using interpolate()
React.createElement(Sequence, {
  from: timeToFrames(1),
  durationInFrames: timeToFrames(2),
  children: (() => {
    const slideX = interpolate(
      frame, 
      [timeToFrames(1), timeToFrames(1.5)], 
      [width, 0], 
      {easing: Easing.out(Easing.quad)}
    );
    const slideOpacity = interpolate(
      frame,
      [timeToFrames(1), timeToFrames(1.3)],
      [0, 1]
    );
    
    return React.createElement('div', {
      style: {
        position: 'absolute',
        top: '20%',
        left: '50%',
        transform: `translateX(calc(-50% + ${slideX}px))`,
        width: '300px',
        height: '80px',
        backgroundColor: 'rgba(255, 123, 0, 0.9)',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '18px',
        color: '#FFFFFF',
        fontWeight: 'bold',
        opacity: slideOpacity,
        zIndex: Z_CONTENT
      }
    }, 'Slide Animation');
  })()
}),

// Scale animation example using spring()
React.createElement(Sequence, {
  from: timeToFrames(3.5),
  durationInFrames: timeToFrames(1.5),
  children: (() => {
    const scaleValue = spring({
      frame: frame - timeToFrames(3.5),
      fps: fps,
      config: BOUNCY_SPRING
    });
    const fadeOpacity = interpolate(
      frame,
      [timeToFrames(3.5), timeToFrames(3.8)],
      [0, 1]
    );
    
    return React.createElement('div', {
      style: {
        position: 'absolute',
        top: '80%',
        left: '50%',
        transform: `translate(-50%, -50%) scale(${Math.max(0.1, scaleValue)})`,
        width: '400px',
        height: '60px',
        backgroundColor: 'rgba(138, 43, 226, 0.9)',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '16px',
        color: '#FFFFFF',
        fontWeight: 'bold',
        opacity: fadeOpacity,
        zIndex: Z_CONTENT
      }
    }, 'Scale Animation');
  })()
}),

// Main title with fixed container - prevents size jumping
React.createElement(Sequence, {
  from: SPRING_DELAY,
  durationInFrames: timeToFrames(5),
  children: React.createElement('div', {
    style: {
      position: 'absolute',
      top: '30%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      width: '80%',
      height: `${TITLE_CONTAINER_HEIGHT}px`, // Fixed height prevents jumping
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: Z_CONTENT
    }
  }, React.createElement('div', {
    style: {
      fontSize: '72px',
      fontWeight: 'bold',
      color: '#FFFFFF',
      textAlign: 'center',
      textShadow: '2px 2px 4px rgba(0,0,0,0.5)',
      opacity: interpolate(frame, [SPRING_DELAY, SPRING_DELAY + FADE_DURATION], [0, 1]),
      transform: `scale(${Math.max(0.1, spring({
        frame: frame - SPRING_DELAY,
        fps: fps,
        config: STANDARD_SPRING
      }))})`, // Prevent scale(0) artifacts
      lineHeight: '1.1'
    }
  }, 'Professional Title'))
}),

// Typing effect with stable container
React.createElement(Sequence, {
  from: timeToFrames(2),
  durationInFrames: timeToFrames(4),
  children: (() => {
    const typingProgress = interpolate(
      frame,
      [timeToFrames(2), timeToFrames(4)],
      [0, 1],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    );
    
    return React.createElement('div', {
      style: {
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '70%',
        height: `${SUBTITLE_CONTAINER_HEIGHT}px`, // Fixed container height
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        borderRadius: '12px',
        padding: `${CARD_PADDING}px`,
        zIndex: Z_CONTENT
      }
    }, React.createElement('div', {
      style: {
        fontSize: '32px',
        color: '#FFFFFF',
        textAlign: 'center',
        fontWeight: '500',
        width: '100%' // Takes full container width
      }
    }, 'Dynamic Content Here'.substring(0, Math.floor(typingProgress * 'Dynamic Content Here'.length))));
  })()
}),

// Subtitle with smooth slide-in
React.createElement(Sequence, {
  from: timeToFrames(3),
  durationInFrames: timeToFrames(6),
  children: (() => {
    const subtitleY = interpolate(
      frame,
      [timeToFrames(3), timeToFrames(3.67)],
      [40, 0],
      { easing: Easing.inOut(Easing.quad) }  // CORRECT EASING SYNTAX
    );

    const subtitleOpacity = interpolate(
      frame,
      [timeToFrames(3), timeToFrames(3.67)],
      [0, 1],
      { easing: Easing.ease }  // CORRECT EASING SYNTAX
    );
    
    return React.createElement('div', {
      style: {
        position: 'absolute',
        top: '70%',
        left: '50%',
        transform: `translate(-50%, calc(-50% + ${subtitleY}px))`,
        width: '60%',
        textAlign: 'center',
        fontSize: '28px',
        color: '#FFFFFF',
        opacity: subtitleOpacity,
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        padding: `${CARD_PADDING / 2}px ${CARD_PADDING}px`,
        borderRadius: '8px',
        zIndex: Z_CONTENT
      }
    }, 'Supporting Information');
  })()
}),

// === OVERLAY LAYER (Z-INDEX 3) ===

// Sliding card container with proper positioning
React.createElement(Sequence, {
  from: timeToFrames(5),
  durationInFrames: timeToFrames(4),
  children: (() => {
    const cardX = interpolate(
      frame,
      [timeToFrames(5), timeToFrames(6.33)],
      [-400, 0],
      { easing: Easing.out(Easing.cubic) }  // CORRECT EASING SYNTAX
    );

    const cardOpacity = interpolate(
      frame,
      [timeToFrames(5), timeToFrames(5.67)],
      [0, 1],
      { easing: Easing.bezier(0.4, 0.0, 0.2, 1) }  // CORRECT BEZIER EASING
    );
    
    return React.createElement('div', {
      style: {
        position: 'absolute',
        top: `${SAFE_ZONE_PADDING}px`,
        left: `${SAFE_ZONE_PADDING}px`,
        right: `${SAFE_ZONE_PADDING}px`,
        bottom: `${SAFE_ZONE_PADDING}px`,
        pointerEvents: 'none',
        zIndex: Z_OVERLAY
      }
    }, React.createElement('div', {
      style: {
        position: 'absolute',
        bottom: '0',
        right: '0',
        width: '400px',
        height: '200px',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '16px',
        padding: `${CARD_PADDING}px`,
        transform: `translateX(${cardX}px)`,
        opacity: cardOpacity,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center'
      }
    }, 
      React.createElement('div', {
        style: {
          fontSize: '24px',
          fontWeight: 'bold',
          color: '#333333',
          marginBottom: '12px'
        }
      }, 'Key Information'),
      React.createElement('div', {
        style: {
          fontSize: '18px',
          color: '#666666',
          lineHeight: '1.4'
        }
      }, 'Supporting details with proper spacing and hierarchy')
    ));
  })()
}),

// === UI LAYER (Z-INDEX 4) ===

// Logo with spring animation - top-right safe zone
React.createElement(Sequence, {
  from: timeToFrames(6),
  durationInFrames: timeToFrames(6),
  children: (() => {
    const logoScale = spring({
      frame: frame - timeToFrames(6),
      fps: fps,
      config: GENTLE_SPRING
    });

    const logoOpacity = interpolate(
      frame,
      [timeToFrames(6), timeToFrames(6.67)],
      [0, 1],
      { easing: Easing.in(Easing.sine) }  // CORRECT EASING SYNTAX
    );
    
    return React.createElement('div', {
      style: {
        position: 'absolute',
        top: `${SAFE_ZONE_PADDING / 2}px`,
        right: `${SAFE_ZONE_PADDING / 2}px`,
        width: '120px',
        height: '120px',
        backgroundColor: '#FF6B6B',
        borderRadius: '50%',
        transform: `scale(${Math.max(0.1, logoScale)})`,
        opacity: logoOpacity,
        zIndex: Z_UI,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)'
      }
    }, React.createElement('div', {
      style: {
        color: '#FFFFFF',
        fontSize: '24px',
        fontWeight: 'bold'
      }
    }, 'LOGO'));
  })()
}),

// Progress indicator with smooth animation
React.createElement(Sequence, {
  from: 0,
  durationInFrames: timeToFrames(12),
  children: React.createElement('div', {
    style: {
      position: 'absolute',
      bottom: `${SAFE_ZONE_PADDING / 3}px`,
      left: `${SAFE_ZONE_PADDING}px`,
      right: `${SAFE_ZONE_PADDING}px`,
      height: '4px',
      backgroundColor: 'rgba(255, 255, 255, 0.3)',
      borderRadius: '2px',
      zIndex: Z_UI
    }
  }, React.createElement('div', {
    style: {
      width: `${(frame / timeToFrames(12)) * 100}%`,
      height: '100%',
      backgroundColor: '#4ECDC4',
      borderRadius: '2px',
      transition: 'width 0.1s ease'
    }
  }))
})

);

**CRITICAL**: DO NOT include any import statements in your code. All necessary imports (React, useCurrentFrame, useVideoConfig, spring, interpolate, AbsoluteFill, fade, slide, wipe, TransitionSeries, etc.) are already provided. Start your code directly with variable declarations and function calls."""

    # User prompt with specific context
    user_prompt = f"""CURRENT COMPOSITION CODE:
{request.get('current_generated_code', '')}

USER REQUEST: {request.get('user_request', '')}
{media_section}"""

    return system_instruction, user_prompt



async def generate_composition_with_validation(
    request: Dict[str, Any], 
    gemini_api: Any,
    use_vertex_ai: bool = False,
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Generate a composition without backend validation - let frontend handle errors.
    """
    try:
        print(f"Generation attempt (no validation)")
        
        # Build the edit prompt
        system_instruction, user_prompt = build_edit_prompt(request)

        # Check if Claude should be used
        use_claude = os.getenv('USE_CLAUDE', '').lower() in ['true', '1', 'yes']
        
        if use_claude:
            # Use Claude for code generation
            claude_api_key = os.getenv('ANTHROPIC_API_KEY')
            if not claude_api_key:
                raise Exception("ANTHROPIC_API_KEY environment variable is required when USE_CLAUDE is enabled")
            
            client = anthropic.Anthropic(api_key=claude_api_key)
            
            response = client.messages.create(
                max_tokens=8192,
                #model="claude-sonnet-4-20250514",
                model="claude-3-5-haiku-20241022",
                temperature=0.3,
                system=system_instruction,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )
            raw_response = response.content[0].text.strip()
            
        elif use_vertex_ai:
            # Use Vertex AI fine-tuned model with endpoint ID
            # Initialize Vertex AI with your project and region
            PROJECT_ID = "24816576653"
            REGION = "europe-west1"
            vertexai.init(project=PROJECT_ID, location=REGION)

            # Use the endpoint ID for your deployed fine-tuned model
            # fine-tuned flash with 40 epochs
            #ENDPOINT_NAME = "projects/24816576653/locations/europe-west1/endpoints/3373543566574878720"

            # fine-tuned pro with 40 epochs
            ENDPOINT_NAME = "projects/24816576653/locations/europe-west1/endpoints/6998941266608128000"

            # fine-tuned pro with 80 epochs
            # ENDPOINT_NAME = "projects/24816576653/locations/europe-west1/endpoints/2477327240728150016"
            
            # Create the fine-tuned model instance with system instruction
            model = GenerativeModel(
                model_name=ENDPOINT_NAME,
                system_instruction=system_instruction
            )
            
            # Generate content with fine-tuned model
            config = GenerationConfig(
                temperature=0.0
            )

            response = model.generate_content(
                contents=[user_prompt],
                generation_config=config
            )
            raw_response = response.text.strip()
        else:
            # Use standard Gemini API
            response = gemini_api.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                )
            )
            raw_response = response.text.strip()
        print(f"Raw AI response (first 200 chars): {raw_response[:200]}...")
        
        # Log conversation for fine-tuning dataset
        log_conversation_for_fine_tuning(system_instruction, user_prompt, raw_response)
        
        # Extract duration and code from structured response
        duration, generated_code = parse_ai_response(raw_response)
        
        # Debug: Log the extracted components
        print(f"Extracted duration: {duration} seconds")
        print(f"Generated code (first 200 chars): {generated_code[:200]}...")
        
        # Log the successful generated code
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_filename = f"generated_code_{timestamp}.js"
        log_path = os.path.join("logs", log_filename)
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Save the generated code to file
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"// Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"// User Request: {request.get('user_request', '')}\n")
            f.write(f"// AI-determined Duration: {duration} seconds\n")
            f.write(f"// No backend validation - errors handled by frontend\n")
            f.write("// ======================================\n\n")
            f.write(generated_code)
        
        print(f"Generated code saved to: {log_path}")
        
        # Return successful response with AI-determined duration
        return {
            "composition_code": generated_code,
            "content_data": [],
            "explanation": f"Generated composition for: {request.get('user_request', '')}",
            "duration": duration,
            "success": True
        }
            
    except Exception as e:
        print(f"Error in generation: {str(e)}")
        return {
            "composition_code": "",
            "content_data": [],
            "explanation": f"Error generating composition: {str(e)}",
            "duration": 5.0,  # Minimal fallback duration
            "success": False,
            "error_message": str(e)
        }
