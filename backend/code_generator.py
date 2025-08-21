import os
import subprocess
import tempfile
import json
import time
import re
import shutil
from typing import Tuple, List, Dict, Any, Optional
from google import genai
from google.genai import types

# Global validation template directory
VALIDATION_TEMPLATE_DIR = None


def setup_validation_template():
    """Create the master validation environment once."""
    global VALIDATION_TEMPLATE_DIR
    
    if VALIDATION_TEMPLATE_DIR and os.path.exists(VALIDATION_TEMPLATE_DIR):
        return VALIDATION_TEMPLATE_DIR
    
    print("🔧 Setting up validation template (one-time setup)...")
    
    # Create template directory
    template_dir = os.path.join("/tmp", "remotion-validation-template")
    os.makedirs(template_dir, exist_ok=True)
    
    # Create package.json - match production dependencies exactly
    package_json = {
        "name": "remotion-validation-template",
        "version": "1.0.0",
        "type": "module",
        "dependencies": {
            "remotion": "4.0.329",
            "@remotion/player": "4.0.329",
            "@remotion/transitions": "4.0.329",
            "react": "^19.1.1",
            "react-dom": "^19.1.1",
            "typescript": "^5.0.0",
            "@types/react": "^18.0.0"
        }
    }
    
    with open(os.path.join(template_dir, "package.json"), "w") as f:
        json.dump(package_json, f, indent=2)
    
    # Create tsconfig.json
    tsconfig = {
        "compilerOptions": {
            "target": "ES2020",
            "lib": ["DOM", "DOM.Iterable", "ES6"],
            "allowJs": True,
            "skipLibCheck": True,
            "esModuleInterop": True,
            "allowSyntheticDefaultImports": True,
            "strict": True,
            "forceConsistentCasingInFileNames": True,
            "module": "ESNext",
            "moduleResolution": "node",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "jsx": "react-jsx"
        },
        "include": ["*.ts", "*.tsx"]
    }
    
    with open(os.path.join(template_dir, "tsconfig.json"), "w") as f:
        json.dump(tsconfig, f, indent=2)
    
    # Create placeholder composition file - match execution environment imports
    placeholder_composition = """
import React from 'react';
import { 
    AbsoluteFill, 
    useCurrentFrame, 
    interpolate, 
    Sequence, 
    Img, 
    Video, 
    Audio, 
    spring, 
    useVideoConfig,
    useCurrentScale 
} from 'remotion';
import { Player, type PlayerRef } from '@remotion/player';
import { fade } from '@remotion/transitions/fade';
import { iris } from '@remotion/transitions/iris';
import { wipe } from '@remotion/transitions/wipe';
import { flip } from '@remotion/transitions/flip';
import { slide } from '@remotion/transitions/slide';

export const TestComposition = () => {
  return <AbsoluteFill />;
};
"""
    
    with open(os.path.join(template_dir, "Composition.tsx"), "w") as f:
        f.write(placeholder_composition)
    
    # Install dependencies (this happens only once!)
    print("📦 Installing dependencies in template...")
    install_result = subprocess.run(
        ['npm', 'install', '--silent'],
        cwd=template_dir,
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if install_result.returncode != 0:
        raise Exception(f"Failed to install template dependencies: {install_result.stderr}")
    
    VALIDATION_TEMPLATE_DIR = template_dir
    print(f"✅ Template created at: {template_dir}")
    return template_dir


def validate_by_remotion_compilation(code: str) -> Tuple[bool, str]:
    """
    Fast validation by copying pre-built environment and updating code.
    Returns (is_valid, error_message)
    """
    try:
        print("Validating code with copy-based Remotion compilation...")
        
        # Ensure template exists
        template_dir = setup_validation_template()
        
        # Create temporary validation directory by copying template
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy the entire template (including node_modules) with symlinks preserved
            shutil.copytree(template_dir, temp_dir, dirs_exist_ok=True, symlinks=True)
            
            # Update the composition file with new code - match execution environment imports exactly
            composition_content = f"""
import React from 'react';
import {{ 
    AbsoluteFill, 
    useCurrentFrame, 
    interpolate, 
    Sequence, 
    Img, 
    Video, 
    Audio, 
    spring, 
    useVideoConfig,
    useCurrentScale 
}} from 'remotion';
import {{ Player, type PlayerRef }} from '@remotion/player';
import {{ fade }} from '@remotion/transitions/fade';
import {{ iris }} from '@remotion/transitions/iris';
import {{ wipe }} from '@remotion/transitions/wipe';
import {{ flip }} from '@remotion/transitions/flip';
import {{ slide }} from '@remotion/transitions/slide';

export const TestComposition = () => {{
{code}
}};
"""
            
            composition_file_path = os.path.join(temp_dir, "Composition.tsx")
            with open(composition_file_path, "w") as f:
                f.write(composition_content)
            
            print(f"Created composition file: {composition_file_path}")
            print(f"Composition content preview: {composition_content[:300]}...")
            
            # Run TypeScript compilation
            compile_result = subprocess.run(
                ['npx', 'tsc', '--noEmit'],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if compile_result.returncode == 0:
                print("Copy-based validation passed!")
                return True, ""
            else:
                # Capture both stderr and stdout for error details
                error_msg = compile_result.stderr.strip()
                stdout_msg = compile_result.stdout.strip()
                
                # Combine both for more complete error info
                full_error = ""
                if error_msg:
                    full_error += f"STDERR: {error_msg}"
                if stdout_msg:
                    if full_error:
                        full_error += f"\nSTDOUT: {stdout_msg}"
                    else:
                        full_error = f"STDOUT: {stdout_msg}"
                
                # If still empty, provide a generic message
                if not full_error:
                    full_error = f"TypeScript compilation failed with exit code {compile_result.returncode}"
                
                print(f"Copy-based validation failed: {full_error}")
                
                # Return the raw TypeScript error - it's more useful than our interpretations
                return False, full_error
                    
    except subprocess.TimeoutExpired:
        return False, "Compilation timeout - code may be too complex"
    except FileNotFoundError as e:
        raise Exception(f"TypeScript/npm not found. Please install Node.js and npm for validation to work: {str(e)}")
    except Exception as e:
        print(f"Copy-based validation exception: {str(e)}")
        return False, f"Validation error: {str(e)}"


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


def build_edit_prompt(request: Dict[str, Any]) -> str:
    """Build prompt for first attempt - has everything needed to modify composition"""
    
    # Get media assets
    media_library = request.get('media_library', [])
    media_section = ""
    if media_library and len(media_library) > 0:
        media_section = "\nAVAILABLE MEDIA ASSETS:\n"
        for media in media_library:
            name = media.get('name', 'unnamed')
            media_type = media.get('mediaType', 'unknown')
            duration = media.get('durationInSeconds', 0)
            
            if media_type == 'video':
                media_section += f"- {name}: Video ({duration}s)\n"
            elif media_type == 'image':
                media_section += f"- {name}: Image\n"
            elif media_type == 'audio':
                media_section += f"- {name}: Audio ({duration}s)\n"
        media_section += "Use exact URLs in Video/Img/Audio components.\n"
    else:
        media_section = "\nNo media assets available. Create compositions using text, shapes, and animations.\n"
    
    return f"""You are a world-class Remotion developer. Update the composition based on user requests.

⚠️ **CRITICAL**: Only change/add what the user specifically asks for. Keep EVERYTHING else UNCHANGED.
            
⚠️ **CRITICAL**: All Sequence components use children: in the props object for Remotion 4.0.329+!

⚠️ **CRITICAL** REMOTION RULES:
1. interpolate() inputRange MUST be strictly monotonically increasing (each value must be larger than the previous one)
2. interpolate() outputRange MUST contain ONLY NUMBERS - never strings, booleans, or other types
3. CSS properties in React must be camelCase (backgroundColor, fontSize, fontWeight)
4. spring() config uses 'damping' not 'dampening'

CORRECT interpolate examples:
- interpolate(frame, [0, 30, 60], [0, 1, 0])  ✅ inputRange: 0 < 30 < 60 (strictly increasing)
- interpolate(frame, [10, 20, 50], [0, 100, 0])  ✅ inputRange: 10 < 20 < 50 (strictly increasing)
- interpolate(frame, [0, 30], [0, 1])  ✅ Numbers only in outputRange
- interpolate(frame, [0, 30], ['hidden', 'visible'])  ❌ WRONG - strings not allowed in outputRange
- interpolate(frame, [30, 20, 60], [0, 1, 0])  ❌ WRONG - inputRange not increasing (30 > 20)

CSS POSITIONING SYSTEM:
Screen coordinates: (0,0) is TOP-LEFT corner. Y-axis goes DOWN (top: 100px = 100px DOWN from top).

POSITIONING PATTERNS - Use these exact patterns:
CENTER ELEMENT:
style: {{
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 'desired-width',
  height: 'desired-height'
}}

FILL WITH PADDING:
style: {{
  position: 'absolute',
  top: '40px',
  left: '40px',
  right: '40px',
  bottom: '40px'
}}

FORBIDDEN:
❌ Never use objectFit for positioning (objectFit only controls scaling)
❌ Never use margin for positioning with position: 'absolute'

RESPONSE FORMAT - You must respond with EXACTLY this structure:
DURATION: [number in seconds based on composition content and timing]
CODE:
[raw JavaScript code - no markdown blocks]

# Complete Remotion Composition Template

## EXAMPLE RESPONSE:
DURATION: 8
CODE:

const frame = useCurrentFrame();
const {{ width, height, fps }} = useVideoConfig();

// Basic interpolation animation
const textOpacity = interpolate(
  frame,
  [0, 30, 180, 210],
  [0, 1, 1, 0]
);

const textScale = interpolate(
  frame,
  [0, 40],
  [0.5, 1]
);

// Spring animation
const logoScale = spring({{
  frame: frame - 60,
  fps: fps,
  config: {{ damping: 10, stiffness: 100 }}
}});

// Movement animation
const slideX = interpolate(
  frame,
  [90, 150],
  [-200, 0]
);

return React.createElement(AbsoluteFill, {{}},
  // Video clip 1: Play from 5-15 seconds of source video
  React.createElement(Sequence, {{
    from: 0,
    durationInFrames: 90,
    children: React.createElement(Video, {{
      src: 'https://example.com/video1.mp4',
      startFrom: 150, // Start from frame 150 (5 seconds at 30fps)
      endAt: 450,     // End at frame 450 (15 seconds at 30fps)
      style: {{
        width: '100%',
        height: '100%',
        objectFit: 'cover'
      }}
    }})
  }}),

  // Video clip 2: Different section of same or different video
  React.createElement(Sequence, {{
    from: 90,
    durationInFrames: 60,
    children: React.createElement(Video, {{
      src: 'https://example.com/video2.mp4',
      startFrom: 300, // Start from frame 300 (10 seconds at 30fps)
      endAt: 600,     // End at frame 600 (20 seconds at 30fps)
      style: {{
        width: '100%',
        height: '100%',
        objectFit: 'cover'
      }}
    }})
  }}),

  // Background video for remaining duration
  React.createElement(Sequence, {{
    from: 150,
    durationInFrames: 90,
    children: React.createElement(Video, {{
      src: 'https://example.com/background.mp3',
      style: {{
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        opacity: 0.5
      }}
    }})
  }}),

  // Background audio
  React.createElement(Audio, {{
    src: 'https://example.com/audio.mp3'
  }}),

  // Main text element with animations
  React.createElement(Sequence, {{
    from: 0,
    durationInFrames: 210,
    children: React.createElement(AbsoluteFill, {{
      style: {{
        justifyContent: 'center',
        alignItems: 'center'
      }}
    }},
      React.createElement('h1', {{
        style: {{
          color: 'white',
          fontSize: 80,
          textAlign: 'center',
          fontFamily: 'Arial, sans-serif',
          fontWeight: 'bold',
          opacity: textOpacity,
          transform: `scale(${{textScale}})`,
          textShadow: '2px 2px 4px rgba(0, 0, 0, 0.8)'
        }}
      }}, 'Main Title')
    )
  }}),

  // Logo with spring animation
  React.createElement(Sequence, {{
    from: 60,
    durationInFrames: 180,
    children: React.createElement('div', {{
      style: {{
        position: 'absolute',
        top: 100,
        left: '50%',
        transform: `translateX(-50%) scale(${{logoScale}})`
      }}
    }},
      React.createElement(Img, {{
        src: 'https://example.com/logo.png',
        style: {{
          width: 120,
          height: 120,
          objectFit: 'contain'
        }}
      }})
    )
  }}),

  // Sliding subtitle
  React.createElement(Sequence, {{
    from: 90,
    durationInFrames: 150,
    children: React.createElement('h2', {{
      style: {{
        position: 'absolute',
        bottom: 150,
        left: '50%',
        transform: `translateX(-50%) translateX(${{slideX}}px)`,
        color: 'yellow',
        fontSize: 36,
        textAlign: 'center',
        fontFamily: 'Arial, sans-serif'
      }}
    }}, 'Subtitle Text')
  }})
);

**CRITICAL**: DO NOT include any import statements in your code. All necessary imports (React, useCurrentFrame, useVideoConfig, spring, interpolate, AbsoluteFill, etc.) are already provided. Start your code directly with variable declarations and function calls.

---

CURRENT COMPOSITION CODE:
{request.get('current_generated_code', '')}

USER REQUEST: {request.get('user_request', '')}
{media_section}"""


def build_retry_prompt(failed_code: str, error_message: str) -> str:
    """Build prompt for retry attempts - just fix the error"""
    
    return f"""Fix the validation error in this code:

BROKEN CODE:
{failed_code}

ERROR MESSAGE:
{error_message}

Return the corrected code in this format:
DURATION: [seconds]
CODE:
[fixed code]"""


async def generate_composition_with_validation(
    request: Dict[str, Any], 
    gemini_api: Any,
    use_vertex_ai: bool = False,
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Generate a composition with compilation validation and retry logic.
    """
    last_error = None
    last_failed_code = None  # Track the code that failed validation
    
    for attempt in range(max_retries + 1):
        try:
            print(f"Generation attempt {attempt + 1}/{max_retries + 1}")
            
            # Build the appropriate prompt based on attempt type
            if attempt > 0:
                # Retry attempt - just fix the error
                prompt = build_retry_prompt(last_failed_code, last_error)
            else:
                # First attempt - full edit prompt
                prompt = build_edit_prompt(request)

            # Generate code with AI
            if use_vertex_ai:
                response = gemini_api.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7
                    )
                )
            else:
                response = gemini_api.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={
                        "temperature": 0.7,
                    },
                )
            
            # Parse the AI response to extract duration and code
            raw_response = response.text.strip()
            print(f"Raw AI response (first 200 chars): {raw_response[:200]}...")
            
            # Extract duration and code from structured response
            duration, generated_code = parse_ai_response(raw_response)
            
            # Debug: Log the extracted components
            print(f"Extracted duration: {duration} seconds")
            print(f"Generated code (first 200 chars): {generated_code[:200]}...")
            
            # Validate by TypeScript compilation with Remotion types
            is_valid, validation_error = validate_by_remotion_compilation(generated_code)
            
            if is_valid:
                print(f"Code validation passed on attempt {attempt + 1}")
                
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
                    f.write(f"// Attempt: {attempt + 1}/{max_retries + 1}\n")
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
            else:
                # Validation failed, prepare for retry
                last_error = validation_error
                last_failed_code = generated_code  # Capture the code that failed
                
                # DEBUG: Log exactly what error will be sent to AI
                print(f"🔍 DEBUG - Attempt {attempt + 1} failed validation")
                print(f"🔍 DEBUG - Error being captured for AI: {repr(validation_error)}")
                print(f"🔍 DEBUG - Error length: {len(validation_error)} characters")
                print(f"🔍 DEBUG - Error preview: {validation_error[:500]}...")
                
                print(f"Attempt {attempt + 1} failed validation: {validation_error}")
                
                if attempt == max_retries:
                    # Final attempt failed - don't change anything, keep previous composition
                    print(f"⚠️ All validation attempts failed, keeping previous composition")
                    return {
                        "composition_code": "",
                        "content_data": [],
                        "explanation": f"Failed to generate valid composition after {max_retries + 1} attempts. Last error: {validation_error}",
                        "duration": 0,  # Duration 0 signals no change
                        "success": False,
                        "error_message": validation_error
                    }
                    
        except Exception as e:
            print(f"Error in generation attempt {attempt + 1}: {str(e)}")
            last_error = str(e)
            
            if attempt == max_retries:
                print(f"⚠️ Error in all generation attempts, keeping previous composition")
                return {
                    "composition_code": "",
                    "content_data": [],
                    "explanation": f"Error generating composition: {str(e)}",
                    "duration": 0,  # Duration 0 signals no change
                    "success": False,
                    "error_message": str(e)
                }
    
    # Should never reach here, but just in case
    return {
        "composition_code": "",
        "content_data": [],
        "explanation": "Failed to generate composition",
        "duration": 5.0,  # Minimal fallback duration
        "success": False,
        "error_message": "Unknown error in composition generation"
    }
