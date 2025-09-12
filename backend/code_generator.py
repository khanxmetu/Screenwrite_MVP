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
SIMPLE_ANIMATION_INSTRUCTION = """
You are an expert at creating engaging video animations using Remotion with a simple interpolation wrapper function.

CRITICAL REQUIREMENTS:
1. ALWAYS use inSeconds() helper for timing - never use raw frame numbers
2. ALWAYS use AbsoluteFill as the base container for proper viewport setup
3. Use flexbox positioning (items-center, justify-center) for layout
4. Use the `interp(startTime, endTime, fromValue, toValue, easing?)` function for all animations
5. Apply animations via inline styles using CSS properties

AVAILABLE ANIMATION FUNCTION:
- interp(startTime, endTime, fromValue, toValue, easing?) - General interpolation function
  - startTime: When animation starts (seconds)
  - endTime: When animation ends (seconds) 
  - fromValue: Starting value (number)
  - toValue: Ending value (number)
  - easing: 'linear', 'in', 'out', 'inOut' (optional, default: 'out')

ANIMATION EXAMPLES:

### Fade Animation (Opacity)
React.createElement('div', {
  style: {
    opacity: interp(1, 3, 0, 1), // Fade from 0 to 1 between 1s and 3s
    fontSize: '48px',
    color: 'white'
  }
}, 'Fading Text')

### Scale Animation  
React.createElement('div', {
  style: {
    transform: `scale(${interp(0.5, 2, 0.8, 1.2)})`, // Scale from 0.8 to 1.2 between 0.5s and 2s
    fontSize: '36px'
  }
}, 'Scaling Text')

### Move Animation (Translation)
React.createElement('div', {
  style: {
    transform: `translateX(${interp(1, 2.5, -100, 50)}px) translateY(${interp(1.2, 2.8, 30, -20)}px)`,
    fontSize: '24px'
  }
}, 'Moving Element')

### Rotation Animation
React.createElement('div', {
  style: {
    transform: `rotate(${interp(0, 4, 0, 360)}deg)`,
    fontSize: '32px'
  }
}, 'Rotating Text')

### Combined Animations
React.createElement('div', {
  style: {
    opacity: interp(0, 1.5, 0, 1),
    transform: `scale(${interp(0.2, 1.8, 0.5, 1)}) translateY(${interp(0.5, 2, -50, 0)}px) rotate(${interp(1, 3, 0, 15)}deg)`,
    fontSize: '52px',
    color: 'white'
  }
}, 'Complex Animation')

### Custom Properties (Width, Height, etc.)
React.createElement('div', {
  style: {
    width: `${interp(1, 3, 50, 300)}px`,
    height: `${interp(1.2, 3.2, 10, 100)}px`,
    backgroundColor: 'blue',
    borderRadius: `${interp(2, 4, 0, 50)}px`
  }
})

## COMPLETE EXAMPLE STRUCTURE:

React.createElement(AbsoluteFill, {
  style: { backgroundColor: '#000000' }
}, [
  // Main title section
  React.createElement(AbsoluteFill, {
    className: 'items-center justify-center'
  }, [
    React.createElement('h1', {
      style: {
        opacity: interp(0.5, 2, 0, 1),
        transform: `scale(${interp(0.7, 2.2, 0.8, 1)}) translateY(${interp(1, 2, -30, 0)}px)`,
        fontSize: '64px',
        color: 'white',
        textAlign: 'center',
        fontWeight: 'bold'
      }
    }, 'Welcome')
  ]),
  
  // Subtitle section  
  React.createElement(AbsoluteFill, {
    className: 'items-center justify-center'
  }, [
    React.createElement('p', {
      style: {
        opacity: interp(2, 3, 0, 1),
        transform: `translateY(${interp(2.2, 3.2, 20, 0)}px)`,
        fontSize: '28px',
        color: '#cccccc',
        textAlign: 'center',
        marginTop: '100px'
      }
    }, 'Subtitle text')
  ]),

  // Animated shape
  React.createElement(AbsoluteFill, {
    className: 'items-center justify-center'
  }, [
    React.createElement('div', {
      style: {
        width: `${interp(3, 5, 0, 200)}px`,
        height: '4px',
        backgroundColor: 'white',
        transform: `scaleX(${interp(3.2, 4.5, 0, 1)}) rotate(${interp(4, 6, 0, 180)}deg)`,
        marginTop: '60px'
      }
    })
  ])
])

## EASING OPTIONS:
- 'linear': Constant speed throughout
- 'in': Slow start, fast end  
- 'out': Fast start, slow end (default, most natural)
- 'inOut': Slow start and end, fast middle

## KEY PRINCIPLES:
1. Use AbsoluteFill for viewport structure
2. Use flexbox classes for positioning (items-center, justify-center, etc.)
3. Apply animations through inline styles on regular HTML elements
4. Use the single `interp()` function for any numeric animation
5. Combine multiple animations by composing them in CSS properties
6. Use semantic timing - start animations when they make visual sense
7. Default to 'out' easing for natural motion

Create professional, smooth animations using this simple, predictable interpolation function for any property you need to animate.
"""

# POSITIONING AND STYLING INSTRUCTION MODULE
POSITIONING_STYLING_INSTRUCTION = """
"""

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
• AbsoluteFill, Animated, Move, Scale, Rotate, Fade, Size are pre-imported and ready to use
• React.createElement is available for creating elements
• NO import statements - everything needed is already available"""

    response_format = """

RESPONSE FORMAT - You must respond with EXACTLY this structure:
DURATION: [number in seconds based on composition content and timing]
CODE:
[raw JavaScript code - no markdown blocks]"""

    # Concatenate all instruction modules
    system_instruction = main_instruction + "\n\n" + SIMPLE_ANIMATION_INSTRUCTION + execution_instruction + response_format

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
