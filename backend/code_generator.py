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

# BLUEPRINT COMPOSITION SYSTEM INSTRUCTION MODULE
BLUEPRINT_COMPOSITION_INSTRUCTION = """
You are an expert at creating video compositions using our CompositionBlueprint system - a JSON-based approach for multi-track video editing with executable JavaScript clip elements.

SYSTEM OVERVIEW:
Your job is to generate CompositionBlueprint JSON that defines tracks with clips containing executable JavaScript code elements.

OUR WRAPPER SYSTEM - AVAILABLE COMPONENTS (PRE-IMPORTED):
- React (for createElement)
- AbsoluteFill (Remotion container - fills entire viewport)
- Video (Remotion video player) 
- Img (Remotion image display)
- Audio (Remotion audio player)
- interp(startTime, endTime, fromValue, toValue, easing?) - Animation interpolation helper
- require() - Mock require for 'remotion' module access

BLUEPRINT STRUCTURE:
```json
[
  {
    "clips": [
      {
        "id": "unique-clip-id",
        "startTimeInSeconds": 0,
        "endTimeInSeconds": 3,
        "element": "return React.createElement('div', { style: { color: 'white' } }, 'Hello');",
        "transitionToNext": {
          "type": "fade",
          "durationInSeconds": 0.5
        }
      }
    ]
  }
]
```

DETAILED WRAPPER SYNTAX:

### 1. EXECUTION CONTEXT
All clip 'element' code is executed as a function body with these available:
- React: Full React library
- AbsoluteFill: Remotion's viewport container
- Video, Img, Audio: Remotion media components
- interp: Animation helper function  
- inSeconds: Time conversion helper
- require: Mock require function

### 2. REMOTION COMPONENTS SYNTAX

**Note:** Video and Audio components use custom seconds-based props (startFromSeconds, endAtSeconds) that are automatically converted to frames internally. This makes timing more intuitive than working with frame numbers.

**Video Component:**
- Displays video files with optional trimming
- Props: src (string), startFromSeconds (number, seconds), endAtSeconds (number, seconds), volume (0-1)
- Example: Video({ src: "/video.mp4", startFromSeconds: 1.0, endAtSeconds: 5.0, volume: 0.8 })
- Use for: Video clips, background footage, imported media

#### Img Component:
```javascript
React.createElement(Img, {
  src: 'EXACT_URL_FROM_MEDIA_LIBRARY',
  style: {
    width: '100%',
    height: '100%',
    objectFit: 'contain',   // 'cover', 'contain', 'fill'
    backgroundColor: '#ffffff'
  }
})
```

**Audio Component:**
- Plays audio files with optional trimming
- Props: src (string), startFromSeconds (number, seconds), endAtSeconds (number, seconds), volume (0-1)
- Example: Audio({ src: "/audio.mp3", startFromSeconds: 0, endAtSeconds: 10.5, volume: 0.6 })
- Use for: Background music, sound effects, voiceovers

#### AbsoluteFill Container:
```javascript
React.createElement(AbsoluteFill, {
  style: { 
    backgroundColor: '#000000',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  }
}, [child1, child2])
```

### 3. ANIMATION SYSTEM - interp() FUNCTION

The interp() function is our custom animation wrapper that simplifies Remotion's interpolate function by using time in seconds instead of frames.

#### Syntax:
```javascript
interp(startTime, endTime, fromValue, toValue, easing?)
```

#### Parameters:
- startTime: When animation starts (seconds) - e.g., 0, 1.5, 2.3
- endTime: When animation ends (seconds) - e.g., 2, 3.5, 5.0  
- fromValue: Starting numeric value - e.g., 0, 100, -50
- toValue: Ending numeric value - e.g., 1, 200, 0
- easing: Animation curve (optional, default 'out')
  - 'linear': Constant speed throughout
  - 'in': Slow start, fast end
  - 'out': Fast start, slow end (most natural, default)
  - 'inOut': Slow start and end, fast middle

#### How interp() Works:
- Automatically converts seconds to frames using the composition's FPS (30fps)
- Uses Remotion's useCurrentFrame() to get the current playback position
- Applies the specified easing function
- Clamps values outside the animation range (no overshoot)
- Returns the interpolated value for the current frame

#### Timing Examples:
```javascript
// Animation from 0s to 2s
interp(0, 2, 0, 100)        // Returns 0 at 0s, 50 at 1s, 100 at 2s

// Animation from 1.5s to 3.5s  
interp(1.5, 3.5, 50, 150)   // Returns 50 at 1.5s, 100 at 2.5s, 150 at 3.5s

// Short 0.5s animation
interp(2, 2.5, 0, 1)        // Quick fade from 2s to 2.5s
```

#### Animation Examples:
```javascript
// Opacity fade in (0 to 1 over 2 seconds)
opacity: interp(0, 2, 0, 1)

// Opacity fade out (1 to 0 over 1.5 seconds starting at 3s)
opacity: interp(3, 4.5, 1, 0)

// Scale animation (small to large)
transform: `scale(${interp(0.5, 1.5, 0.8, 1.2)})`

// Scale with easing
transform: `scale(${interp(0, 1, 0.5, 1, 'inOut')})`

// Position movement (left to right)
transform: `translateX(${interp(1, 3, -100, 100)}px)`

// Vertical movement (top to bottom)
transform: `translateY(${interp(1.2, 2.8, -50, 50)}px)`

// Rotation (0 to 360 degrees)
transform: `rotate(${interp(0, 4, 0, 360)}deg)`

// Size changes
width: `${interp(1, 3, 50, 300)}px`
height: `${interp(1.2, 3.2, 20, 150)}px`

// Border radius animation
borderRadius: `${interp(2, 4, 0, 50)}px`

// Font size changes
fontSize: `${interp(0, 1, 12, 48)}px`

// Color component transitions (RGB values)
backgroundColor: `rgb(${interp(0, 2, 255, 0)}, ${interp(0, 2, 0, 255)}, 100)`

// Opacity with RGB
color: `rgba(255, 255, 255, ${interp(1, 2, 0, 1)})`
```

#### Easing Comparison:
```javascript
// Linear - constant speed (robotic)
opacity: interp(0, 2, 0, 1, 'linear')

// In - slow start, fast end (dramatic entrance)
transform: `scale(${interp(0, 1, 0.5, 1, 'in')})`

// Out - fast start, slow end (natural, default)
opacity: interp(0, 1, 0, 1, 'out')

// InOut - slow start and end (elegant)
transform: `translateY(${interp(0, 2, -50, 0, 'inOut')}px)`
```

### 4. MULTI-ELEMENT COMPOSITIONS

#### Container with Multiple Children:
```javascript
return React.createElement('div', { 
  style: { 
    width: '100%', 
    height: '100%', 
    position: 'relative' 
  } 
}, [
  React.createElement(Video, { 
    key: 'background',
    src: 'video_url_here',
    style: { width: '100%', height: '100%', objectFit: 'cover' }
  }),
  React.createElement('div', { 
    key: 'overlay',
    style: { 
      position: 'absolute', 
      bottom: '20px', 
      left: '20px',
      padding: '12px 16px',
      backgroundColor: 'rgba(0,0,0,0.7)',
      color: 'white',
      fontSize: '24px',
      borderRadius: '8px'
    } 
  }, 'Video Title')
]);
```

### 5. STYLING SYSTEM

#### Supported CSS Properties:
- Layout: width, height, position, top, left, right, bottom
- Flexbox: display, alignItems, justifyContent, flexDirection
- Typography: fontSize, color, fontFamily, fontWeight, textAlign
- Background: backgroundColor, backgroundImage, backgroundSize
- Border: border, borderRadius, borderWidth, borderColor
- Transform: transform (scale, translate, rotate, skew)
- Animation: opacity, transition
- Spacing: margin, padding (and variants like marginTop, paddingLeft)
- Object Fit: objectFit for media elements

#### CSS Values:
- Pixels: '24px', '100px'
- Percentages: '100%', '50%'  
- Colors: '#ffffff', 'rgba(255,255,255,0.8)', 'red'
- Keywords: 'center', 'flex', 'absolute', 'cover'

### 7. MULTI-TRACK CONCEPTS:
- Track 0: Main content layer (videos, images, primary content)
- Track 1+: Overlay layers (titles, effects, secondary content, audio)
- Clips can overlap across tracks for layered compositions
- Use precise startTimeInSeconds/endTimeInSeconds for timing
- Higher track numbers render on top of lower tracks

### 8. TRANSITIONS (between clips on same track):
Available types: "fade", "slide", "wipe", "flip", "clockWipe", "iris"
Directions: "from-left", "from-right", "from-top", "from-bottom"
```json
"transitionToNext": {
  "type": "fade",
  "durationInSeconds": 1.0
}
```
### 9. CRITICAL EXECUTION RULES:
- Each 'element' string is executed as: new Function('React', 'AbsoluteFill', 'interp', 'inSeconds', 'require', ELEMENT_CODE)
- Must RETURN a React element using React.createElement()
- NO import statements - all components pre-imported
- Use exact URLs from media library - never use relative paths
- All animations use interp() with time in seconds
- Use 'key' prop for multiple children in arrays
- Style objects use camelCase CSS properties
"""

# POSITIONING AND STYLING INSTRUCTION MODULE
POSITIONING_STYLING_INSTRUCTION = """
"""

def parse_blueprint_response(response_text: str) -> Tuple[float, str]:
    """
    Parse AI response to extract duration and CompositionBlueprint JSON.
    Expected format:
    DURATION: 12
    BLUEPRINT:
    [JSON array]
    
    Returns (duration, blueprint_json)
    """
    try:
        print(f"Parsing blueprint response. Full response:\n{response_text}")
        
        lines = response_text.strip().split('\n')
        duration = None
        blueprint_json = ""
        
        # Look for DURATION line
        duration_found = False
        blueprint_started = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            print(f"Processing line {i}: '{line_stripped}'")
            
            # Parse duration
            if line_stripped.upper().startswith('DURATION:') and not duration_found:
                try:
                    duration_str = line_stripped[9:].strip()
                    print(f"Attempting to parse duration from: '{duration_str}'")
                    duration = float(duration_str)
                    duration_found = True
                    print(f"✅ Successfully extracted duration: {duration} seconds")
                except ValueError as e:
                    print(f"❌ Failed to parse duration from: '{line_stripped}', error: {e}")
                continue
            
            # Start collecting blueprint JSON after BLUEPRINT: line
            if line_stripped.upper() == 'BLUEPRINT:' and not blueprint_started:
                print(f"Found BLUEPRINT: marker at line {i}")
                blueprint_started = True
                # Collect all remaining lines as JSON
                json_lines = lines[i+1:]
                blueprint_json = '\n'.join(json_lines)
                print(f"Extracted {len(json_lines)} lines of JSON")
                break
        
        # Fallback: if no structured format found, treat entire response as JSON
        if not blueprint_started:
            print("⚠️ No structured format found, treating entire response as blueprint JSON")
            blueprint_json = response_text.strip()
            
        # If no duration found, estimate from blueprint
        if duration is None:
            print("⚠️ No duration found, using default of 10 seconds")
            duration = 10.0
        else:
            print(f"🎯 Using AI-determined duration: {duration} seconds")
            
        # Ensure we have some JSON
        if not blueprint_json.strip():
            raise ValueError("No blueprint JSON found in AI response")
            
        # Try to parse JSON to validate it's valid
        try:
            import json
            parsed = json.loads(blueprint_json)
            print(f"✅ Valid JSON blueprint with {len(parsed)} tracks")
        except json.JSONDecodeError as e:
            print(f"⚠️ Blueprint JSON validation failed: {e}")
            # Don't fail here - let frontend handle validation
            
        print(f"✅ Final parsed result - Duration: {duration}s, Blueprint length: {len(blueprint_json)} chars")
        return duration, blueprint_json
        
    except Exception as e:
        print(f"❌ Error parsing blueprint response: {e}")
        # Return fallback values
        fallback_duration = 10.0
        fallback_blueprint = '[]'  # Empty blueprint
        print(f"📊 Using fallback - Duration: {fallback_duration}s, Empty blueprint")
        return fallback_duration, fallback_blueprint



def build_blueprint_prompt(request: Dict[str, Any]) -> tuple[str, str]:
    """Build system instruction and user prompt for blueprint generation"""
    
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
        media_section = "\nNo media assets available. Create compositions using text, shapes, and animations only.\n"
    
    # Get current composition for incremental editing
    current_composition = request.get('current_composition', [])
    composition_context = ""
    if current_composition and len(current_composition) > 0:
        composition_context = f"\nCURRENT COMPOSITION:\n"
        composition_context += f"- {len(current_composition)} tracks\n"
        clip_count = sum(len(track.get('clips', [])) for track in current_composition)
        composition_context += f"- {clip_count} total clips\n"
        if clip_count > 0:
            composition_context += f"- Modify, extend, or replace the existing composition based on user request\n"
        composition_context += f"\nExisting composition structure: {str(current_composition)[:200]}...\n"
    
    # Build modular system instruction
    main_instruction = """You are a video composition specialist focused on creating CompositionBlueprint JSON structures for multi-track video editing.

**BLUEPRINT-FIRST APPROACH**
Your job is to generate or modify CompositionBlueprint JSON arrays that define video compositions with tracks containing executable JavaScript clip elements."""

    execution_instruction = """

**CRITICAL EXECUTION REQUIREMENTS:**
• Generate valid CompositionBlueprint JSON (array of tracks with clips)
• Each clip has executable JavaScript 'element' code that returns React elements
• NO import statements needed - React, Video, Img, Audio, AbsoluteFill, interp are pre-available
• Use EXACT media URLs from the provided media library"""

    response_format = """

RESPONSE FORMAT - You must respond with EXACTLY this structure:
DURATION: [total composition duration in seconds]
BLUEPRINT:
[valid CompositionBlueprint JSON array]"""

    # Build complete system instruction
    system_instruction = main_instruction + "\n\n" + BLUEPRINT_COMPOSITION_INSTRUCTION + execution_instruction + response_format

    # User prompt with specific context
    user_prompt = f"""USER REQUEST: {request.get('user_request', '')}
{composition_context}
{media_section}"""

    return system_instruction, user_prompt



async def generate_composition_with_validation(
    request: Dict[str, Any], 
    gemini_api: Any,
    use_vertex_ai: bool = False,
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Generate a CompositionBlueprint JSON without backend validation - let frontend handle errors.
    """
    import os
    import time
    
    try:
        print(f"Blueprint generation attempt (no validation)")
        
        # Build the blueprint prompt
        system_instruction, user_prompt = build_blueprint_prompt(request)

        # Check if Claude should be used
        use_claude = os.getenv('USE_CLAUDE', '').lower() in ['true', '1', 'yes']
        
        if use_claude:
            # Use Claude for blueprint generation
            claude_api_key = os.getenv('ANTHROPIC_API_KEY')
            if not claude_api_key:
                raise Exception("ANTHROPIC_API_KEY environment variable is required when USE_CLAUDE is enabled")
            
            client = anthropic.Anthropic(api_key=claude_api_key)
            
            response = client.messages.create(
                max_tokens=8192,
                model="claude-sonnet-4-20250514",
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
            # Use Vertex AI fine-tuned model
            from google import genai
            # Note: genai.types import may fail in some environments, using direct access instead
            
            # Set environment variables for Vertex AI
            os.environ['GOOGLE_CLOUD_PROJECT'] = "24816576653"
            os.environ['GOOGLE_CLOUD_LOCATION'] = "europe-west1"
            os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = "True"
            
            client = genai.Client()
            
            # Use the endpoint ID for your deployed fine-tuned model
            ENDPOINT_NAME = "projects/24816576653/locations/europe-west1/endpoints/6998941266608128000"
            
            response = client.models.generate_content(
                model=ENDPOINT_NAME,
                contents=user_prompt,
                config={
                    "system_instruction": system_instruction,
                    "temperature": 0.0,
                }
            )
            raw_response = response.text.strip()
        else:
            # Use standard Gemini API
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
        
        # Extract duration and blueprint JSON from structured response
        duration, blueprint_json = parse_blueprint_response(raw_response)
        
        # Debug: Log the extracted components
        print(f"Extracted duration: {duration} seconds")
        print(f"Generated blueprint JSON (first 200 chars): {blueprint_json[:200]}...")
        
        # Log the successful generated blueprint
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_filename = f"generated_blueprint_{timestamp}.json"
        log_path = os.path.join("logs", log_filename)
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Save the generated blueprint to file
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"// Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"// User Request: {request.get('user_request', '')}\n")
            f.write(f"// AI-determined Duration: {duration} seconds\n")
            f.write(f"// CompositionBlueprint JSON\n")
            f.write("// ======================================\n\n")
            f.write(blueprint_json)
        
        print(f"Generated blueprint saved to: {log_path}")
        
        # Return successful response with blueprint JSON
        return {
            "composition_code": blueprint_json,  # Frontend expects this field name
            "content_data": [],
            "explanation": f"Generated CompositionBlueprint for: {request.get('user_request', '')}",
            "duration": duration,
            "success": True
        }
            
    except Exception as e:
        print(f"Error in blueprint generation: {str(e)}")
        return {
            "composition_code": "[]",  # Empty blueprint fallback
            "content_data": [],
            "explanation": f"Error generating blueprint: {str(e)}",
            "duration": 5.0,  # Minimal fallback duration
            "success": False,
            "error_message": str(e)
        }
