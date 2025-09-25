"""
Media Checker - Lightweight Media Relevance Detector

Single responsibility: Determine which media files are relevant to a user request.
Fast, focused, and reliable - the foundation of our new architecture.
"""

import json
from typing import Dict, Any, List
from google import genai
from google.genai import types


async def check_media_relevance(
    user_request: str,
    current_composition: str,
    media_library: List[Dict[str, Any]],
    gemini_api: Any
) -> List[str]:
    """
    Determine which media files are relevant to the user request.
    
    This is a lightweight, fast check that only identifies which media files
    need to be sent to the Synth for detailed analysis and enhancement.
    
    Args:
        user_request: The raw user request
        current_composition: Current TSX composition code to resolve references
        media_library: Available media assets with metadata
        gemini_api: Gemini AI client
        
    Returns:
        List of media file names that are relevant to the request
    """
    
    print(f"📋 Media Checker: Analyzing relevance for {len(media_library)} media files")
    
    if not media_library:
        print("📋 Media Checker: No media library provided")
        return []
    
    # Build media file list for prompt
    media_list = []
    for media in media_library:
        name = media.get('name', 'unnamed')
        media_type = media.get('mediaType', 'unknown')
        duration = media.get('durationInSeconds', 0) if media_type == 'video' else None
        
        if duration:
            media_list.append(f"- {name}: {media_type} ({duration}s)")
        else:
            media_list.append(f"- {name}: {media_type}")
    
    # Build composition context
    comp_context = "No current composition"
    if current_composition:
        comp_context = f"Current composition:\n{current_composition}"

    # System instruction for role definition
    system_instruction = """You are a media content analysis detector for a video editing system.

CONTEXT: The user has a video composition (React/Remotion code) with available media files. They've made a request that will be forwarded to the code generator LLM. Your ONLY job is to figure out which specific media files the code generator should analyze to fulfill the user's request. You are NOT generating code or making changes - just selecting which files are necessary.

YOUR ONLY TASK: Determine which files need analysis. Nothing else.

- Content analysis needed: "when dog appears", "colors in sunset", "where person is", "empty space in video"
- No content analysis: "make longer", "add text", "move element", "resize video"

Use the composition to resolve references like "first clip", "main video", then determine if those specific files need content examination.

Return JSON with exact file names that need content examination, or empty array if none.

{"files_needing_analysis": ["filename.mp4"], "reasoning": "Brief explanation"}"""

    # User prompt with context  
    prompt = f"""USER REQUEST: "{user_request}"

CURRENT COMPOSITION:
{comp_context}

AVAILABLE MEDIA FILES:
{chr(10).join(media_list)}"""

    # Define structured output schema
    response_schema = {
        "type": "object",
        "properties": {
            "files_needing_analysis": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of media file names that need content analysis"
            },
            "reasoning": {
                "type": "string",
                "description": "Brief explanation of why these files were selected"
            }
        },
        "required": ["files_needing_analysis", "reasoning"]
    }
    
    try:
        print("📋 Media Checker: Calling Gemini for content analysis needs detection")
        
        # Call Gemini with structured output
        response = gemini_api.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,  # Low temperature for consistent relevance detection
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )
        
        if response and response.text:
            try:
                result = json.loads(response.text.strip())
                files_needing_analysis = result.get("files_needing_analysis", [])
                reasoning = result.get("reasoning", "No reasoning provided")
                
                print(f"📋 Media Checker: Found {len(files_needing_analysis)} files needing content analysis")
                print(f"📋 Media Checker: Reasoning: {reasoning}")
                
                # Validate that returned files exist in media library
                valid_files = []
                available_names = [media.get('name', '') for media in media_library]
                
                for file_name in files_needing_analysis:
                    if file_name in available_names:
                        valid_files.append(file_name)
                    else:
                        print(f"⚠️ Media Checker: File '{file_name}' not found in media library")
                
                return valid_files
                
            except json.JSONDecodeError as e:
                print(f"❌ Media Checker: Failed to parse JSON response: {e}")
                print(f"Raw response: {response.text}")
                # Smart fallback - only return files if directly referenced
                fallback_files = []
                request_lower = user_request.lower()
                
                # Check for direct file name mentions
                for media in media_library:
                    media_name = media.get('name', '').lower()
                    if media_name and media_name in request_lower:
                        fallback_files.append(media.get('name', ''))
                
                # Check for content analysis keywords + media type references
                content_analysis_keywords = ['appears', 'shows', 'color', 'mood', 'style', 'scene']
                media_type_references = ['video', 'image', 'photo', 'clip']
                
                has_content_keyword = any(keyword in request_lower for keyword in content_analysis_keywords)
                has_media_reference = any(ref in request_lower for ref in media_type_references)
                
                # Only include files if both content analysis AND media reference detected
                if has_content_keyword and has_media_reference and not fallback_files:
                    # Try to match based on context/description
                    for media in media_library:
                        if media.get('mediaType') in ['video', 'image']:
                            fallback_files.append(media.get('name', ''))
                            break  # Just take first relevant file, not all
                return [f for f in fallback_files if f]
        else:
            print("❌ Media Checker: No response from Gemini")
            # Smart fallback - only return files if directly referenced
            fallback_files = []
            request_lower = user_request.lower()
            
            # Check for direct file name mentions
            for media in media_library:
                media_name = media.get('name', '').lower()
                if media_name and media_name in request_lower:
                    fallback_files.append(media.get('name', ''))
            
            # If no direct file mentions, return empty (be conservative)
            return [f for f in fallback_files if f]
            
    except Exception as e:
        print(f"❌ Media Checker: Error during relevance check: {e}")
        # Smart fallback - only return files if directly referenced
        fallback_files = []
        request_lower = user_request.lower()
        
        # Check for direct file name mentions
        for media in media_library:
            media_name = media.get('name', '').lower()
            if media_name and media_name in request_lower:
                fallback_files.append(media.get('name', ''))
        
        # If no direct file mentions, return empty (be conservative)
        return [f for f in fallback_files if f]
