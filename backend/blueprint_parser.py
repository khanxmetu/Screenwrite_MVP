import json
from typing import Tuple


def parse_structured_blueprint_response(response_text: str) -> Tuple[float, str]:
    """
    Parse structured JSON response directly from Gemini API.
    Returns (calculated_duration, blueprint_json)
    """
    try:
        print(f"Parsing structured blueprint response. JSON: {response_text[:200]}...")
        
        # Validate and parse JSON
        blueprint_data = json.loads(response_text)
        
        # Calculate duration from blueprint structure
        max_end_time = 0.0
        for track in blueprint_data:
            if 'clips' in track:
                for clip in track['clips']:
                    end_time = clip.get('endTimeInSeconds', 0)
                    max_end_time = max(max_end_time, end_time)
        
        duration = max_end_time if max_end_time > 0 else 5.0
        
        print(f"✅ Calculated duration from blueprint: {duration}s")
        print(f"✅ Valid structured blueprint with {len(blueprint_data)} tracks")
        
        return duration, response_text
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return 5.0, "[]"
    except Exception as e:
        print(f"❌ Error parsing structured response: {e}")
        return 5.0, "[]"


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
