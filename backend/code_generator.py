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

# Could any hell be more horrible than now and here?

# ANIMATION SYSTEM INSTRUCTION MODULE
ANIMATION_INSTRUCTION = """**OUR CUSTOM ANIMATION API - USE THESE EXACTLY:**

**GLOBAL TIMING HELPER FUNCTION:**
- inSeconds(seconds): Converts seconds to frames (MANDATORY for ALL timing values across ALL components)
  - Example: inSeconds(2.5) = 75 frames at 30fps
  - Example: inSeconds(1) = 30 frames at 30fps
  - This is a GLOBAL utility - use it everywhere timing is needed
  - NEVER use raw frame numbers anywhere in the code

**ANIMATED COMPONENT:**
- Animated: Main animation container with these props:
  - animations: Array of animation objects (required)
  - style?: React.CSSProperties for CSS styling
  - children: React.ReactNode content to animate

**ANIMATION HELPER FUNCTIONS:**
- Move: Position animations
  - x?: number (pixels to move right, positive = right, negative = left)
  - y?: number (pixels to move down, positive = down, negative = up)
  - start: number (frame to start animation, required - USE inSeconds())
  - duration?: number (animation length in frames, defaults to inSeconds(1))

- Scale: Size animations
  - by: number (scale factor, required - 1 = same size, 2 = double, 0.5 = half)
  - start: number (frame to start animation, required - USE inSeconds())
  - duration?: number (animation length in frames, defaults to inSeconds(1))

- Rotate: Rotation animations
  - degrees: number (rotation in degrees, required - 360 = full rotation)
  - start: number (frame to start animation, required - USE inSeconds())
  - duration?: number (animation length in frames, defaults to inSeconds(1))

- AnimatedFade: Opacity animations
  - to: number (target opacity 0-1, required - 0 = invisible, 1 = fully visible)
  - start: number (frame to start animation, required - USE inSeconds())
  - duration?: number (animation length in frames, defaults to inSeconds(1))

**ANIMATION EASING - MAKE YOUR ANIMATIONS FEEL NATURAL:**

**SPRING ANIMATIONS (DEFAULT & RECOMMENDED):**
- Spring physics provide the most natural-looking animations
- Default behavior: smooth, realistic motion with slight overshoot
- Customize spring behavior with these options:
  - mass: number (heavier = slower, lighter = faster)
  - damping: number (higher = less bouncy, lower = more bouncy)
  - stiffness: number (higher = faster, lower = slower)
  - overshootClamping: boolean (true = no overshoot, false = natural bounce)

**SPRING EXAMPLES:**
```javascript
// Default spring (recommended for most cases)
Move({ x: 200, start: inSeconds(0) })

// Custom bouncy spring
Move({ x: 200, start: inSeconds(0), mass: 1, damping: 10, stiffness: 100 })

// Smooth, no-overshoot spring
Scale({ by: 1.5, start: inSeconds(1), damping: 20, overshootClamping: true })
```

**CLASSIC EASING FUNCTIONS:**
Use these for specific animation feels:

- **Linear**: Constant speed (robotic, use sparingly)
  - Ease.Linear

- **Quadratic**: Gentle acceleration/deceleration (subtle, elegant)
  - Ease.QuadraticIn (slow start, fast end)
  - Ease.QuadraticOut (fast start, slow end) 
  - Ease.QuadraticInOut (smooth both ends)

- **Cubic**: Moderate curves (good for UI transitions)
  - Ease.CubicIn, Ease.CubicOut, Ease.CubicInOut

- **Quartic**: Strong curves (dramatic, fluid motion)
  - Ease.QuarticIn, Ease.QuarticOut, Ease.QuarticInOut

- **Bounce**: Playful bouncing effect
  - Ease.BounceIn, Ease.BounceOut, Ease.BounceInOut

- **Circular**: Sharp acceleration based on circle geometry
  - Ease.CircularIn, Ease.CircularOut, Ease.CircularInOut

**EASING EXAMPLES:**
```javascript
// Smooth slide-in with cubic easing
Move({ x: 200, start: inSeconds(0), ease: Ease.CubicOut })

// Bouncy scale animation
Scale({ by: 1.5, start: inSeconds(1), ease: Ease.BounceOut })

// Custom bezier curve
Rotate({ degrees: 180, start: inSeconds(2), ease: Ease.Bezier(0.33, 1, 0.68, 1) })
```

**EASING BEST PRACTICES:**
- Use spring animations for most cases (they feel natural)
- QuadraticOut/CubicOut for UI elements appearing
- QuadraticIn/CubicIn for UI elements disappearing  
- BounceOut for playful, attention-grabbing effects
- Linear only for mechanical/robotic movements
- Avoid overly complex easing that distracts from content

**CORRECT ANIMATION SYNTAX (ALWAYS USE inSeconds):**
```javascript
React.createElement(Animated, {
  animations: [
    // Spring animations (default, most natural)
    Move({ x: 200, y: -50, start: inSeconds(0), duration: inSeconds(1) }),
    Scale({ by: 1.5, start: inSeconds(0.5), duration: inSeconds(1.5) }),
    
    // Custom easing for specific effects
    AnimatedFade({ to: 0.8, start: inSeconds(2), duration: inSeconds(1), ease: Ease.CubicOut }),
    Rotate({ degrees: 180, start: inSeconds(3), duration: inSeconds(2), ease: Ease.BounceOut })
  ],
  style: {
    position: 'absolute',
    backgroundColor: '#FF6B6B',
    color: 'white',
    fontSize: '24px',
    padding: '20px',
    borderRadius: '8px'
  }
}, 'Your content here')
```

**ANIMATION BEHAVIOR:**
- All animations start from default values (position 0,0, scale 1, opacity 1, rotation 0)
- Animations interpolate smoothly from start to target values
- Multiple animations on same element combine (e.g., move + scale + fade)
- start: When animation begins (required for each animation - USE inSeconds())
- duration: Length of animation (optional, defaults to inSeconds(1) = 1 second)

**TIMING EXAMPLES (ALWAYS use inSeconds helper):**
- start: inSeconds(0), duration: inSeconds(1) = animate from 0 to 1 second
- start: inSeconds(1), duration: inSeconds(0.5) = animate from 1s to 1.5s
- start: inSeconds(2) = animate from 2 seconds for default duration (1 second)
- start: inSeconds(2.5) = start at 2.5 seconds
- start: inSeconds(0.25) = start at quarter second

**MANDATORY RULES:**
- EVERY animated element MUST use Animated wrapper
- Use React.createElement syntax only (no JSX)
- Animation helpers (Move, Scale, Rotate, AnimatedFade) are pre-imported
- start parameter is REQUIRED for all animations
- GLOBAL REQUIREMENT: ALWAYS use inSeconds() for ALL timing values across ALL components
- Video components: src, startFrom, endAt - use inSeconds()
- Audio components: src, startFrom, endAt - use inSeconds() 
- Animated components: start, duration - use inSeconds()
- ANY timing value anywhere in code - use inSeconds()
- NEVER use raw frame numbers in any component or context
- Focus on smooth, professional motion design

**COMMON PATTERNS (using inSeconds + smart easing):**
- Entrance (smooth appear): AnimatedFade({ to: 1, start: inSeconds(0), ease: Ease.CubicOut }) with initial opacity 0 in style
- Exit (gentle disappear): AnimatedFade({ to: 0, start: inSeconds(3), ease: Ease.CubicIn })
- Slide in (from left): Move({ x: -100, start: inSeconds(0), ease: Ease.QuadraticOut }) (comes from left)
- Bounce scale up: Scale({ by: 1.2, start: inSeconds(1), ease: Ease.BounceOut })
- Smooth rotation: Rotate({ degrees: 360, start: inSeconds(2) }) (spring default)
- Attention-grabbing bounce: Scale({ by: 1.1, start: inSeconds(0), ease: Ease.BounceOut })
- UI element slide: Move({ y: 50, start: inSeconds(0), ease: Ease.CubicOut })
- Playful wiggle: Rotate({ degrees: 15, start: inSeconds(1), ease: Ease.BounceInOut })

**ESSENTIAL POSITIONING HELPERS - PROFESSIONAL LAYOUTS:**

**SCREEN ANCHORS (9 fundamental positions):**
These helpers return CSS style objects for clean, semantic positioning:

- TopLeft(margin) - Top-left corner with optional margin
- TopCenter(margin) - Top center with optional margin  
- TopRight(margin) - Top-right corner with optional margin
- CenterLeft(margin) - Middle left edge with optional margin
- CenterScreen() - Perfect center of screen
- CenterRight(margin) - Middle right edge with optional margin
- BottomLeft(margin) - Bottom-left corner with optional margin
- BottomCenter(margin) - Bottom center with optional margin
- BottomRight(margin) - Bottom-right corner with optional margin

**RELATIVE POSITIONING (element relationships):**
Position elements relative to other elements (conceptual):

- Above(elementId, spacing) - Position above another element
- Below(elementId, spacing) - Position below another element  
- LeftOf(elementId, spacing) - Position to the left of element
- RightOf(elementId, spacing) - Position to the right of element
- CenterOn(elementId) - Center exactly on another element

**POSITIONING EXAMPLES (SEMANTIC vs MANUAL):**
```javascript
// ✅ CLEAN: Semantic positioning with helpers
React.createElement(Animated, {
  animations: [Move({ x: 0, y: 0, start: inSeconds(0) })],
  style: {
    ...TopCenter(40),        // Semantic: top center, 40px margin
    fontSize: '32px',
    fontWeight: 'bold'
  }
}, 'Professional Title')

// ✅ CLEAN: Bottom watermark
React.createElement(Animated, {
  animations: [AnimatedFade({ to: 1, start: inSeconds(0) })],
  style: {
    ...BottomRight(20),      // Semantic: bottom-right, 20px margin
    fontSize: '12px',
    opacity: 0.7
  }
}, '© 2025 Company')

// ✅ CLEAN: Perfect center with fade
React.createElement(Animated, {
  animations: [
    AnimatedFade({ to: 1, start: inSeconds(0.5), ease: Ease.CubicOut })
  ],
  style: {
    ...CenterScreen(),       // Semantic: perfect center
    fontSize: '48px',
    opacity: 0
  }
}, 'Main Message')

// ❌ AVOID: Manual pixel calculations
React.createElement(Animated, {
  style: {
    position: 'absolute',
    top: '40px',             // Manual positioning
    left: '50%',            // Manual calculation
    transform: 'translateX(-50%)'  // Manual transform
  }
}, 'Title')
```

**POSITIONING BEST PRACTICES:**
- Use spread operator (...TopCenter(20)) to merge with other styles
- Helpers handle position, transform, and centering automatically
- No manual pixel calculations needed
- Semantic naming makes code self-documenting
- Consistent spacing with margin parameters
- Professional layouts with minimal code"""

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
            duration = 10
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
        estimated_duration = 10
        print(f"📊 Using estimated fallback duration: {estimated_duration} seconds")
        return estimated_duration, response_text.strip()


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
    
    # Build modular system instruction
    main_instruction = """You are an animation specialist focused EXCLUSIVELY on creating smooth, visually appealing animations using our custom Animated component system.

**ANIMATION-FIRST APPROACH**
Your ONLY job is to create beautiful animations using the Animated component with clean HTML/CSS styling."""

    execution_instruction = """

**CRITICAL EXECUTION REQUIREMENTS:**
• Code is executed as a function body - must start with return statement
• Animated, Move, Scale, Rotate, AnimatedFade are pre-imported and ready to use
• React.createElement is available for creating elements
• NO import statements - everything needed is already available"""

    response_format = """

RESPONSE FORMAT - You must respond with EXACTLY this structure:
DURATION: [number in seconds based on composition content and timing]
CODE:
[raw JavaScript code - no markdown blocks]"""

    # Concatenate all instruction modules
    system_instruction = main_instruction + "\n\n" + ANIMATION_INSTRUCTION + execution_instruction + response_format

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
    import os
    import time
    
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
                model="claude-sonnet-4-20250514",
                #model="claude-3-5-haiku-20241022",
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
            # Use Vertex AI fine-tuned model with thinking budget
            from google import genai
            from google.genai.types import GenerateContentConfig, ThinkingConfig
            
            # Set environment variables for Vertex AI
            os.environ['GOOGLE_CLOUD_PROJECT'] = "24816576653"
            os.environ['GOOGLE_CLOUD_LOCATION'] = "europe-west1"
            os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = "True"
            
            client = genai.Client()
            
            # Use the endpoint ID for your deployed fine-tuned model
            # fine-tuned flash with 40 epochs
            #ENDPOINT_NAME = "projects/24816576653/locations/europe-west1/endpoints/3373543566574878720"

            # fine-tuned pro with 40 epochs
            ENDPOINT_NAME = "projects/24816576653/locations/europe-west1/endpoints/6998941266608128000"

            # fine-tuned pro with 80 epochs
            # ENDPOINT_NAME = "projects/24816576653/locations/europe-west1/endpoints/2477327240728150016"
            
            response = client.models.generate_content(
                model=ENDPOINT_NAME,
                contents=user_prompt,
                config=GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.0,
#                    thinking_config=ThinkingConfig(
#                        thinking_budget=1200
#                    ),
                )
            )
            raw_response = response.text.strip()
        else:
            # Use standard Gemini API with thinking budget
            response = gemini_api.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3
                )
            )
            raw_response = response.text.strip()
        print(f"Raw AI response (first 200 chars): {raw_response[:200]}...")
        
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
