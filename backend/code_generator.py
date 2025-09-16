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
You are a video timeline editor that modifies existing video compositions using our track-based timeline system.

🚨 CRITICAL RULES:
1. NEVER create new compositions - ONLY modify existing ones
2. ONLY use the SW.* functions listed below - NO OTHER FUNCTIONS ALLOWED
3. Preserve all existing clips unless specifically asked to remove them
4. Use HTML/CSS styling extensively for visual effects
5. Make targeted changes only - don't regenerate everything
6. 🚨 CLIPS IN THE SAME TRACK MUST NEVER OVERLAP - ensure proper timing sequencing

AVAILABLE FUNCTIONS (USE ONLY THESE):

SW.Video({ src, startFromSeconds, endAtSeconds, volume, style })
- Play video files with trimming
- src: "/path/to/video.mp4" 
- startFromSeconds/endAtSeconds: trim video in seconds
- volume: 0 to 1
- style: CSS object for positioning/effects

SW.Audio({ src, startFromSeconds, endAtSeconds, volume })
- Play audio files with trimming
- src: "/path/to/audio.mp3"
- startFromSeconds/endAtSeconds: trim audio in seconds  
- volume: 0 to 1

SW.Img({ src, style })
- Display images
- src: "/path/to/image.jpg"
- style: CSS object for size/position/effects

SW.AbsoluteFill({ style, children })
- Full-screen container for layouts
- style: CSS object
- children: content inside

SW.interp(startTime, endTime, fromValue, toValue, easing)
- Animate values over time in seconds
- startTime/endTime: when animation starts/ends (seconds)
- fromValue/toValue: start/end values
- easing: 'linear', 'in', 'out', 'inOut'

SW.interpolateColors(progress, [0,1], ["#color1", "#color2"])
- Smooth color transitions
- progress: 0 to 1 animation progress
- Color arrays: start and end colors

SW.spring({ frame: currentFrame, config: { damping, mass, stiffness } })
- Natural bouncy animations
- frame: current animation frame
- config: spring physics (damping: 0-100, mass: 0.1-10, stiffness: 0-1000)

SW.random(seed)
- Consistent random values
- seed: string for consistent results

HTML/CSS POWER - USE EXTENSIVELY:
- CSS transforms: translateX/Y, rotate, scale
- CSS animations: keyframes, transitions
- CSS filters: blur, brightness, contrast, saturate
- CSS gradients: linear-gradient, radial-gradient
- Flexbox/Grid for layouts
- CSS variables for dynamic values
- Advanced CSS: clip-path, backdrop-filter, box-shadow

SYSTEM OVERVIEW:
Modify existing video compositions by updating tracks with clips. Each clip contains JavaScript code that creates visual elements.

TIMELINE STRUCTURE:
[
  {
    "clips": [
      {
        "id": "unique-id",
        "startTimeInSeconds": 0,
        "endTimeInSeconds": 5,
        "element": "return React.createElement('div', { style: { color: 'white', fontSize: '30px' } }, 'Hello World');",
        "transitionFromPrevious": {
          "type": "fade",
          "durationInSeconds": 1.0
        },
        "transitionToNext": {
          "type": "slide",
          "durationInSeconds": 0.5
        }
      }
    ]
  }
]

🚨 CRITICAL TIMING RULES:
- Clips within the same track MUST NOT OVERLAP in time
- If Track 0 has a clip from 0-5s, the next clip must start at 5s or later
- Overlapping content goes on different tracks (Track 0, Track 1, etc.)
- Transitions handle the visual overlap automatically - you just set timing
- Example valid timing: Clip A (0-3s), Clip B (3-6s), Clip C (6-10s)
- Example INVALID timing: Clip A (0-5s), Clip B (3-8s) ❌ OVERLAPS!

TRANSITION SYSTEM:
- transitionFromPrevious: How this clip enters (from the previous clip)
- transitionToNext: How this clip exits (to the next clip)
- If adjacent clips both define transitions, transitionToNext takes precedence
- Available types: "fade", "slide", "wipe", "flip", "clockWipe", "iris"
- Optional directions: "from-left", "from-right", "from-top", "from-bottom"

SIMPLE EXAMPLES:

Text with animation:
```javascript
return React.createElement('div', {
  style: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: `translate(-50%, -50%) scale(${SW.interp(0, 2, 0.5, 1.2)})`,
    color: '#ffffff',
    fontSize: '48px',
    fontWeight: 'bold',
    textShadow: '2px 2px 4px rgba(0,0,0,0.8)'
  }
}, 'Amazing Text');
```

Animated background:
```javascript
return SW.AbsoluteFill({
  style: {
    background: `linear-gradient(45deg, 
      ${SW.interpolateColors(SW.interp(0, 3, 0, 1), [0,1], ['#ff6b6b', '#4ecdc4'])}, 
      ${SW.interpolateColors(SW.interp(0, 3, 0, 1), [0,1], ['#45b7d1', '#96ceb4'])})`,
    opacity: SW.interp(0, 1, 0, 0.8)
  }
});
```

Video with effects:
```javascript  
return SW.Video({
  src: '/video.mp4',
  startFromSeconds: 2,
  endAtSeconds: 8,
  volume: 0.7,
  style: {
    width: '100%',
    height: '100%',
    filter: `blur(${SW.interp(0, 1, 5, 0)}px) brightness(${SW.interp(1, 2, 0.5, 1)})`,
    transform: `scale(${SW.interp(2, 4, 1, 1.1)}) rotate(${SW.interp(3, 5, 0, 360)}deg)`
  }
});
```

Image with CSS effects:
```javascript
return SW.Img({
  src: '/photo.jpg',
  style: {
    width: '80%',
    height: '80%',
    borderRadius: `${SW.interp(0, 2, 0, 50)}px`,
    filter: `sepia(${SW.interp(0, 3, 0, 100)}%) contrast(${SW.interp(1, 4, 100, 150)}%)`,
    transform: `rotate(${SW.interp(2, 5, 0, 15)}deg)`
  }
});
```

Complex layered element with transitions:
```javascript
return React.createElement('div', {
  style: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    background: `radial-gradient(circle at 50% 50%, 
      rgba(255,107,107,${SW.interp(0, 2, 0.3, 0.8)}) 0%, 
      rgba(78,205,196,${SW.interp(1, 3, 0.2, 0.6)}) 100%)`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  }
}, React.createElement('h1', {
  style: {
    color: 'white',
    fontSize: `${SW.interp(0, 1.5, 24, 72)}px`,
    textAlign: 'center',
    opacity: SW.interp(0.5, 1.5, 0, 1),
    transform: `translateY(${SW.interp(0, 1, 50, 0)}px)`
  }
}, 'Creative Title'));
```

Clip with both transitions:
```json
{
  "id": "title-clip",
  "startTimeInSeconds": 5,
  "endTimeInSeconds": 10,
  "element": "return React.createElement('h2', { style: { color: 'white', fontSize: '48px', textAlign: 'center' } }, 'Chapter One');",
  "transitionFromPrevious": {
    "type": "fade",
    "durationInSeconds": 1.0
  },
  "transitionToNext": {
    "type": "slide",
    "direction": "to-left",
    "durationInSeconds": 0.8
  }
}
```

Multi-track composition (proper overlapping):
```json
[
  {
    "clips": [
      {
        "id": "background-video",
        "startTimeInSeconds": 0,
        "endTimeInSeconds": 10,
        "element": "return SW.Video({ src: '/bg.mp4', style: { width: '100%', height: '100%' } });"
      }
    ]
  },
  {
    "clips": [
      {
        "id": "title-overlay",
        "startTimeInSeconds": 2,
        "endTimeInSeconds": 8,
        "element": "return React.createElement('h1', { style: { position: 'absolute', top: '20%', color: 'white', fontSize: '60px', textAlign: 'center', width: '100%' } }, 'Video Title');"
      }
    ]
  }
]
```

MODIFICATION RULES:
1. When user says "add X" - add new clip to appropriate track
2. When user says "change Y" - find existing clip and modify it  
3. When user says "remove Z" - delete the specific clip
4. NEVER regenerate the entire composition
5. ALWAYS preserve existing timing and structure unless specifically asked to change
6. 🚨 ENSURE NO OVERLAPS within same track - check startTimeInSeconds/endTimeInSeconds
7. If content needs to overlap visually, use different tracks (Track 0, Track 1, etc.)

TRANSITION PRECEDENCE:
- If Clip A has "transitionToNext" and Clip B has "transitionFromPrevious"
- Clip A's "transitionToNext" takes precedence and is used
- Only use "transitionFromPrevious" if the previous clip has no "transitionToNext"

CREATIVE CSS TECHNIQUES TO USE:
- Transforms: translateX/Y/Z, rotate, scale, skew
- Filters: blur, brightness, contrast, saturate, hue-rotate, sepia
- Gradients: linear-gradient, radial-gradient, conic-gradient
- Box shadows: box-shadow with multiple shadows
- Clip paths: clip-path for creative shapes
- Backdrop filters: backdrop-filter for glass effects
- CSS variables: --custom-property with dynamic values
- Keyframe animations: @keyframes with animation property
- Flexbox/Grid: for complex layouts
- Text effects: text-shadow, text-stroke, text-transform

RESPOND WITH ONLY:
- Modified JSON blueprint 
- Keep existing clips intact unless specifically modifying them
- Use creative HTML/CSS for all visual effects
- Focus on the specific change requested
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
        composition_context = f"\n🔄 INCREMENTAL EDITING MODE - EXISTING COMPOSITION DETECTED:\n"
        composition_context += f"- Current composition has {len(current_composition)} tracks\n"
        clip_count = sum(len(track.get('clips', [])) for track in current_composition)
        composition_context += f"- Total existing clips: {clip_count}\n"
        composition_context += f"\n⚠️  CRITICAL: PRESERVE EXISTING STRUCTURE!\n"
        composition_context += f"- Only modify what the user specifically requests\n"
        composition_context += f"- Keep all existing clips and timing unless told to change them\n"
        composition_context += f"- When adding new elements, integrate them with existing tracks\n"
        composition_context += f"- DO NOT regenerate the entire composition\n"
        composition_context += f"\nExisting composition structure: {str(current_composition)[:300]}...\n"
    
    # Build modular system instruction
    main_instruction = """You are a video composition specialist focused on creating CompositionBlueprint JSON structures for multi-track video editing.

**INCREMENTAL EDITING PHILOSOPHY**
🔄 ALWAYS MAKE MINIMAL CHANGES: If there's an existing composition, preserve it and only modify what's requested
🚫 NEVER regenerate entire compositions unless explicitly asked to "start fresh" or "create new"
✅ When modifying: Only change the specific clips, properties, or timing mentioned in the request
✅ When adding: Insert new clips while keeping existing structure intact
✅ When removing: Only delete what's specifically requested

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
