import os
import json
import time
import re
from typing import Tuple, List, Dict, Any, Optional
from google import genai
from google.genai import types


def create_simplified_system_instruction(original_system_instruction: str) -> str:
    """
    Create a simplified system instruction for fine-tuning by removing the bloated template
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

⚠️ **CRITICAL RULES:**

1. **interpolate() OUTPUT TYPES:**
   ✅ CORRECT: interpolate(frame, [0, 100], [0, 1, 0.5]) // Numbers only
   ❌ WRONG: interpolate(frame, [0, 100], ['hidden', 'visible']) // No strings
   → For strings: Use conditionals instead: opacity > 0.5 ? 'block' : 'none'

2. **EASING SYNTAX:**
   ✅ CORRECT: {easing: Easing.inOut(Easing.quad)}
   ❌ WRONG: {easing: 'ease-in-out'}

3. **CSS PROPERTIES:**
   ✅ CORRECT: backgroundColor, fontSize, fontWeight, borderRadius
   ❌ WRONG: background-color, font-size, font-weight, border-radius

4. **SPRING CONFIG:**
   ✅ CORRECT: {damping: 12, stiffness: 80}
   ❌ WRONG: {dampening: 12, stiffness: 80}

5. **SEQUENCE CHILDREN:**
   ✅ CORRECT: React.createElement(Sequence, {from: 0, durationInFrames: 60, children: content})

6. **DOM LAYERING:** Elements rendered LATER appear ON TOP. Place overlays AFTER background elements.

⚠️ **CRITICAL**: Only change/add what the user specifically asks for. Keep EVERYTHING else UNCHANGED.

**CRITICAL**: DO NOT include any import statements in your code. All necessary imports (React, useCurrentFrame, useVideoConfig, spring, interpolate, AbsoluteFill, etc.) are already provided. Start your code directly with variable declarations and function calls.

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
        
        # Ensure logs directory exists
        dataset_path = os.path.join("logs", dataset_file)
        os.makedirs("logs", exist_ok=True)
        
        # Append to JSONL file (each line is a complete JSON object)
        with open(dataset_path, "a", encoding="utf-8") as f:
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
        dataset_path = os.path.join("logs", dataset_file)
        
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

**MEDIA COMPONENTS:**
• Video: {src: string, trimBefore?: number, trimAfter?: number, volume?: number, playbackRate?: number, muted?: boolean, style?: object}
• Audio: {src: string, trimBefore?: number, trimAfter?: number, volume?: number, playbackRate?: number, muted?: boolean}
• Img: {src: string, style?: object, placeholder?: string}

⚠️ CRITICAL MEDIA RULE: When using Video/Audio/Img components, ALWAYS use the exact URL from the AVAILABLE MEDIA ASSETS section above. 
NEVER use just the filename - always use the full URL provided in the "URL:" field.

EXAMPLE CORRECT USAGE:
- If media shows "video.mp4 - URL: https://example.com/video.mp4", use src: "https://example.com/video.mp4"
- NOT src: "video.mp4"

**TRANSITION EFFECTS (from @remotion/transitions):**
• fade(): Simple opacity transition
• slide({direction}): direction = "from-left" | "from-right" | "from-top" | "from-bottom"
• wipe(): Slide overlay transition
• flip(): 3D rotation transition
• iris(): Circular reveal transition
• clockWipe(): Circular wipe transition

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

1. **interpolate() OUTPUT TYPES:**
   ✅ CORRECT: interpolate(frame, [0, 100], [0, 1, 0.5]) // Numbers only
   ❌ WRONG: interpolate(frame, [0, 100], ['hidden', 'visible']) // No strings
   ❌ WRONG: interpolate(frame, [0, 100], [true, false]) // No booleans
   → For strings: Use conditionals instead: opacity > 0.5 ? 'block' : 'none'

2. **EASING SYNTAX:**
   ✅ CORRECT: {easing: Easing.inOut(Easing.quad)}
   ❌ WRONG: {easing: 'ease-in-out'}

3. **CSS PROPERTIES:**
   ✅ CORRECT: backgroundColor, fontSize, fontWeight, borderRadius
   ❌ WRONG: background-color, font-size, font-weight, border-radius

4. **SPRING CONFIG:**
   ✅ CORRECT: {damping: 12, stiffness: 80}
   ❌ WRONG: {dampening: 12, stiffness: 80}

5. **SEQUENCE CHILDREN:**
   ✅ CORRECT: React.createElement(Sequence, {from: 0, durationInFrames: 60, children: content})

6. **DOM LAYERING:** Elements rendered LATER appear ON TOP. Place overlays AFTER background elements.

7. **NAMING CONVENTIONS:**
   ✅ CORRECT naming patterns to follow:
   - Constants: UPPER_SNAKE_CASE (SCENE_START, FADE_DURATION, TEXT_COLOR)
   - Variables: camelCase (textElement, backgroundDiv, fadeOpacity)
   - Functions: camelCase (createText, animateElement, renderScene)
   - Use full descriptive names, NO abbreviations
   ❌ WRONG: Mixing conventions, inconsistent patterns, or abbreviations
   - Don't mix camelCase and snake_case for similar items
   - Don't abbreviate (use textElement not txtElem, backgroundColor not bgColor)
   - Stick to one convention per type throughout the entire code

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
- [ ] All constants use UPPER_SNAKE_CASE, variables use camelCase
- [ ] NO abbreviations used anywhere (full descriptive names only)
- [ ] Naming conventions are consistent throughout the code
- [ ] No string/boolean outputs in interpolate() calls
- [ ] Proper React.createElement syntax used
- [ ] No import statements included

RESPONSE FORMAT - You must respond with EXACTLY this structure:
DURATION: [number in seconds based on composition content and timing]
CODE:
[raw JavaScript code - no markdown blocks]

# Complete Remotion Composition Template

## EXAMPLE RESPONSE:
DURATION: 12
CODE:

const frame = useCurrentFrame();
const {{ width, height, fps }} = useVideoConfig();

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
const STANDARD_SPRING = {{ damping: 12, stiffness: 80 }};
const GENTLE_SPRING = {{ damping: 15, stiffness: 60 }};
const BOUNCY_SPRING = {{ damping: 8, stiffness: 100 }};

// === BACKGROUND VIDEO SEQUENCES WITH CROSS-FADES ===

// Video clip 1 with fade in - strictly increasing: [0, 20, 75, 90]
const clip1Opacity = interpolate(
  frame,
  [0, FADE_DURATION, 75, 90],
  [0, 1, 1, 0]
);

// Video clip 2 with cross-fade from clip 1 - strictly increasing: [75, 90, 165, 180]
const clip2Opacity = interpolate(
  frame,
  [75, 90, 165, 180],
  [0, 1, 1, 0]
);

// Background video for remaining duration with fade in - strictly increasing: [165, 180]
const backgroundOpacity = interpolate(
  frame,
  [165, 180],
  [0, 0.6]
);

// === CONTAINER-BASED TEXT ANIMATIONS ===

// Title animation with fixed container - no size jumping - strictly increasing: [30, 50]
const titleOpacity = interpolate(
  frame,
  [SPRING_DELAY, SPRING_DELAY + FADE_DURATION],
  [0, 1]
);

const titleScale = spring({{
  frame: frame - SPRING_DELAY,
  fps: fps,
  config: STANDARD_SPRING
}});

// Typing effect with stable container - strictly increasing: [60, 120]
const typingProgress = interpolate(
  frame,
  [60, 120],
  [0, 1],
  {{ extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }}
);

// Subtitle slide-in with proper timing - strictly increasing: [90, 110]
const subtitleY = interpolate(
  frame,
  [90, 110],
  [40, 0],
  {{ easing: Easing.inOut(Easing.quad) }}  // CORRECT EASING SYNTAX
);

const subtitleOpacity = interpolate(
  frame,
  [90, 110],
  [0, 1],
  {{ easing: Easing.ease }}  // CORRECT EASING SYNTAX
);

// === CARD/CONTAINER SLIDE ANIMATION ===
// Card slide animation with smooth easing - strictly increasing: [150, 190]
const cardX = interpolate(
  frame,
  [150, 190],
  [-400, 0],
  {{ easing: Easing.out(Easing.cubic) }}  // CORRECT EASING SYNTAX
);

const cardOpacity = interpolate(
  frame,
  [150, 170],
  [0, 1],
  {{ easing: Easing.bezier(0.4, 0.0, 0.2, 1) }}  // CORRECT BEZIER EASING
);

// === LOGO SCALING WITH PROPER TIMING ===
const logoScale = spring({{
  frame: frame - 180,
  fps: fps,
  config: GENTLE_SPRING
}});

const logoOpacity = interpolate(
  frame,
  [180, 200],
  [0, 1],
  {{ easing: Easing.in(Easing.sine) }}  // CORRECT EASING SYNTAX
);

return React.createElement(AbsoluteFill, {{}},

  // === BACKGROUND LAYER (Z-INDEX 1) ===
  
  // Video clip 1: Trimmed section (5-8 seconds of source)
  React.createElement(Sequence, {{
    from: 0,
    durationInFrames: 90,
    children: React.createElement(Video, {{
      src: 'https://example.com/video1.mp4',
      trimBefore: 150,  // Start at 5 seconds (30fps) - MODERN PROP
      trimAfter: 390,   // End at 13 seconds (30fps) - MODERN PROP
      style: {{
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        opacity: clip1Opacity,
        zIndex: Z_BACKGROUND
      }}
    }})
  }}),

  // Video clip 2: Different section with cross-fade
  React.createElement(Sequence, {{
    from: 90,
    durationInFrames: 90,
    children: React.createElement(Video, {{
      src: 'https://example.com/video2.mp4',
      trimBefore: 300,  // Start at 10 seconds - MODERN PROP
      trimAfter: 600,   // End at 20 seconds - MODERN PROP
      style: {{
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        opacity: clip2Opacity,
        zIndex: Z_BACKGROUND
      }}
    }})
  }}),

  // Background video with reduced opacity
  React.createElement(Sequence, {{
    from: 180,
    durationInFrames: 180,
    children: React.createElement(Video, {{
      src: 'https://example.com/background.mp4',
      style: {{
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        opacity: backgroundOpacity,
        zIndex: Z_BACKGROUND
      }}
    }})
  }}),

  // Background audio
  React.createElement(Audio, {{
    src: 'https://example.com/audio.mp3',
    trimBefore: 0,   // MODERN PROP - start from beginning
    trimAfter: 360   // MODERN PROP - end at 12 seconds
  }}),

  // === CONTENT LAYER (Z-INDEX 2) ===

  // === POSITIONING EXAMPLES - Core Patterns ===

  // PATTERN 1: CENTER ELEMENT - Perfect centering with fade transition
  React.createElement(Sequence, {{
    from: 0,
    durationInFrames: 60,
    children: (() => {{
      const centerOpacity = interpolate(frame, [0, 15, 45, 60], [0, 1, 1, 0]);
      const centerScale = interpolate(frame, [0, 20], [0.8, 1]);
      
      return React.createElement('div', {{
        style: {{
          // STANDARD CENTER PATTERN - Use this for perfect centering
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: `translate(-50%, -50%) scale(${{centerScale}})`,
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
        }}
      }}, 'Perfect Center');
    }})()
  }}),

  // PATTERN 2: FILL WITH PADDING - Responsive containers with slide-in
  React.createElement(Sequence, {{
    from: 20,
    durationInFrames: 60,
    children: (() => {{
      const fillOpacity = interpolate(frame, [20, 35, 65, 80], [0, 1, 1, 0]);
      const fillY = interpolate(frame, [20, 40], [20, 0]);
      
      return React.createElement('div', {{
        style: {{
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
          transform: `translateY(${{fillY}}px)`,
          zIndex: Z_CONTENT
        }}
      }}, 'Fill Container');
    }})()
  }}),

  // PATTERN 3: SAFE ZONE POSITIONING - All corner and edge placements
  React.createElement(Sequence, {{
    from: 10,
    durationInFrames: 80,
    children: (() => {{
      const safeOpacity = interpolate(frame, [10, 25, 75, 90], [0, 1, 1, 0]);
      const safeScale = interpolate(frame, [10, 30], [0.9, 1]);
      
      return React.createElement('div', {{
        style: {{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          opacity: safeOpacity,
          transform: `scale(${{safeScale}})`,
          zIndex: Z_CONTENT
        }}
      }},
        // TOP-LEFT: Brand/Logo placement
        React.createElement('div', {{
          style: {{
            position: 'absolute',
            top: `${{SAFE_ZONE_PADDING / 2}}px`,      // 30px from top
            left: `${{SAFE_ZONE_PADDING / 2}}px`,     // 30px from left
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
          }}
        }}, 'TOP-LEFT'),

        // TOP-RIGHT: Status/Info placement
        React.createElement('div', {{
          style: {{
            position: 'absolute',
            top: `${{SAFE_ZONE_PADDING / 2}}px`,      // 30px from top
            right: `${{SAFE_ZONE_PADDING / 2}}px`,    // 30px from right
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
          }}
        }}, 'TOP-RIGHT'),

        // BOTTOM-LEFT: Secondary info placement
        React.createElement('div', {{
          style: {{
            position: 'absolute',
            bottom: `${{SAFE_ZONE_PADDING / 2}}px`,   // 30px from bottom
            left: `${{SAFE_ZONE_PADDING / 2}}px`,     // 30px from left
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
          }}
        }}, 'BOTTOM-LEFT'),

        // BOTTOM-RIGHT: CTA/Action placement
        React.createElement('div', {{
          style: {{
            position: 'absolute',
            bottom: `${{SAFE_ZONE_PADDING / 2}}px`,   // 30px from bottom
            right: `${{SAFE_ZONE_PADDING / 2}}px`,    // 30px from right
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
          }}
        }}, 'BOTTOM-RIGHT'),

        // TOP-CENTER: Title/Header placement
        React.createElement('div', {{
          style: {{
            position: 'absolute',
            top: `${{SAFE_ZONE_PADDING / 2}}px`,      // 30px from top
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
          }}
        }}, 'TOP-CENTER'),

        // BOTTOM-CENTER: Progress/Status placement
        React.createElement('div', {{
          style: {{
            position: 'absolute',
            bottom: `${{SAFE_ZONE_PADDING / 2}}px`,   // 30px from bottom
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
          }}
        }}, 'BOTTOM-CENTER'),

        // LEFT-CENTER: Navigation placement
        React.createElement('div', {{
          style: {{
            position: 'absolute',
            left: `${{SAFE_ZONE_PADDING / 2}}px`,     // 30px from left
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
          }}
        }}, 'LEFT-CENTER'),

        // RIGHT-CENTER: Sidebar placement
        React.createElement('div', {{
          style: {{
            position: 'absolute',
            right: `${{SAFE_ZONE_PADDING / 2}}px`,    // 30px from right
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
          }}
        }}, 'RIGHT-CENTER')
      );
    }})()
  }}),

  // Main title with fixed container - prevents size jumping
  React.createElement(Sequence, {{
    from: SPRING_DELAY,
    durationInFrames: 150,
    children: React.createElement('div', {{
      style: {{
        position: 'absolute',
        top: '30%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '80%',
        height: `${{TITLE_CONTAINER_HEIGHT}}px`, // Fixed height prevents jumping
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: Z_CONTENT
      }}
    }}, React.createElement('div', {{
      style: {{
        fontSize: '72px',
        fontWeight: 'bold',
        color: '#FFFFFF',
        textAlign: 'center',
        textShadow: '2px 2px 4px rgba(0,0,0,0.5)',
        opacity: titleOpacity,
        transform: `scale(${{Math.max(0.1, titleScale)}})`, // Prevent scale(0) artifacts
        lineHeight: '1.1'
      }}
    }}, 'Professional Title'))
  }}),

  // Typing effect with stable container
  React.createElement(Sequence, {{
    from: 60,
    durationInFrames: 120,
    children: React.createElement('div', {{
      style: {{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '70%',
        height: `${{SUBTITLE_CONTAINER_HEIGHT}}px`, // Fixed container height
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        borderRadius: '12px',
        padding: `${{CARD_PADDING}}px`,
        zIndex: Z_CONTENT
      }}
    }}, React.createElement('div', {{
      style: {{
        fontSize: '32px',
        color: '#FFFFFF',
        textAlign: 'center',
        fontWeight: '500',
        width: '100%' // Takes full container width
      }}
    }}, 'Dynamic Content Here'.substring(0, Math.floor(typingProgress * 'Dynamic Content Here'.length))))
  }}),

  // Subtitle with smooth slide-in
  React.createElement(Sequence, {{
    from: 90,
    durationInFrames: 180,
    children: React.createElement('div', {{
      style: {{
        position: 'absolute',
        top: '70%',
        left: '50%',
        transform: `translate(-50%, calc(-50% + ${{subtitleY}}px))`,
        width: '60%',
        textAlign: 'center',
        fontSize: '28px',
        color: '#FFFFFF',
        opacity: subtitleOpacity,
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        padding: `${{CARD_PADDING / 2}}px ${{CARD_PADDING}}px`,
        borderRadius: '8px',
        zIndex: Z_CONTENT
      }}
    }}, 'Supporting Information')
  }}),

  // === OVERLAY LAYER (Z-INDEX 3) ===

  // Sliding card container with proper positioning
  React.createElement(Sequence, {{
    from: 150,
    durationInFrames: 120,
    children: React.createElement('div', {{
      style: {{
        position: 'absolute',
        top: `${{SAFE_ZONE_PADDING}}px`,
        left: `${{SAFE_ZONE_PADDING}}px`,
        right: `${{SAFE_ZONE_PADDING}}px`,
        bottom: `${{SAFE_ZONE_PADDING}}px`,
        pointerEvents: 'none',
        zIndex: Z_OVERLAY
      }}
    }}, React.createElement('div', {{
      style: {{
        position: 'absolute',
        bottom: '0',
        right: '0',
        width: '400px',
        height: '200px',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '16px',
        padding: `${{CARD_PADDING}}px`,
        transform: `translateX(${{cardX}}px)`,
        opacity: cardOpacity,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center'
      }}
    }}, 
      React.createElement('div', {{
        style: {{
          fontSize: '24px',
          fontWeight: 'bold',
          color: '#333333',
          marginBottom: '12px'
        }}
      }}, 'Key Information'),
      React.createElement('div', {{
        style: {{
          fontSize: '18px',
          color: '#666666',
          lineHeight: '1.4'
        }}
      }}, 'Supporting details with proper spacing and hierarchy')
    ))
  }}),

  // === UI LAYER (Z-INDEX 4) ===

  // Logo with spring animation - top-right safe zone
  React.createElement(Sequence, {{
    from: 180,
    durationInFrames: 180,
    children: React.createElement('div', {{
      style: {{
        position: 'absolute',
        top: `${{SAFE_ZONE_PADDING / 2}}px`,
        right: `${{SAFE_ZONE_PADDING / 2}}px`,
        width: '120px',
        height: '120px',
        backgroundColor: '#FF6B6B',
        borderRadius: '50%',
        transform: `scale(${{Math.max(0.1, logoScale)}})`,
        opacity: logoOpacity,
        zIndex: Z_UI,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)'
      }}
    }}, React.createElement('div', {{
      style: {{
        color: '#FFFFFF',
        fontSize: '24px',
        fontWeight: 'bold'
      }}
    }}, 'LOGO'))
  }}),

  // Progress indicator with smooth animation
  React.createElement(Sequence, {{
    from: 0,
    durationInFrames: 360,
    children: React.createElement('div', {{
      style: {{
        position: 'absolute',
        bottom: `${{SAFE_ZONE_PADDING / 3}}px`,
        left: `${{SAFE_ZONE_PADDING}}px`,
        right: `${{SAFE_ZONE_PADDING}}px`,
        height: '4px',
        backgroundColor: 'rgba(255, 255, 255, 0.3)',
        borderRadius: '2px',
        zIndex: Z_UI
      }}
    }}, React.createElement('div', {{
      style: {{
        width: `${{(frame / 360) * 100}}%`,
        height: '100%',
        backgroundColor: '#4ECDC4',
        borderRadius: '2px',
        transition: 'width 0.1s ease'
      }}
    }}))
  }})
);

**CRITICAL**: DO NOT include any import statements in your code. All necessary imports (React, useCurrentFrame, useVideoConfig, spring, interpolate, AbsoluteFill, etc.) are already provided. Start your code directly with variable declarations and function calls."""

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

        # Generate code with AI
        if use_vertex_ai:
            response = gemini_api.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3
                )
            )
        else:
            response = gemini_api.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3
                )
            )
        
        # Parse the AI response to extract duration and code
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
