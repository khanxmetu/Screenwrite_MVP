
"""
Synth - Simplified Request Enhancement Engine

Two simple functions to enhance user requests:
1. enhance_without_media() - Basic textual enhancement
2. enhance_with_media() - Enhancement with media content analysis
"""

import json
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types


# Common system instruction shared by both enhancement functions
COMMON_SYSTEM_INSTRUCTION = """You are a video editing request enhancement engine. Your job is to create enhanced request(s) that clearly describe WHAT the user wants to achieve, not HOW to implement it technically.

⚠️ CRITICAL: Never output clarifying questions. Fill missing details with reasonable assumptions. Focus on creative and editorial intent, not code implementation. Your response goes to a code generator that handles technical details.

⚠️ CRITICAL MEDIA FILE NAMING: When referencing media files in your enhanced request, you MUST use the exact file names from the user's context or media library. DO NOT use generic names like "myVideo.mp4" or "video.mp4". Use the actual file names that are available.

REQUIREMENTS for the enhanced request(s):
- Clearly describe the desired visual/audio outcome in plain language
- Specify exact media files by their EXACT NAMES from the available context
- Include timing information (when things should happen in seconds)
- Include visual specifications (colors, positions, sizes, animations)
- Focus on creative intent, not technical implementation
- Avoid code-specific terms (components, props, functions, etc.)
- Use video editing terminology instead of programming terminology

EXAMPLES OF GOOD VS BAD REQUESTS:
❌ BAD: "Add a Video component with src prop set to staticFile('video.mp4')"
✅ GOOD: "Add the shore.mp4 video to the composition starting at 0 seconds"

❌ BAD: "Create a div element with absolute positioning at top: 20%"
✅ GOOD: "Add text 'Hello World' positioned at the top center of the screen"

If the user request involves multiple distinct tasks, provide separate enhanced requests. If it's a single cohesive task, provide one enhanced request.

Return ONLY the enhanced request(s) - no explanations, no questions."""


async def synthesize_request(
    user_request: str,
    conversation_history: Optional[List[Dict[str, Any]]],
    current_composition: Optional[str],
    relevant_media_files: List[str],
    media_library: Optional[List[Dict[str, Any]]],
    preview_settings: Dict[str, Any],
    gemini_api: Any
) -> str:
    """
    Enhanced Synth: Route to appropriate enhancement function based on media availability
    """
    
    print(f"🧠 Synth: Processing request with {len(relevant_media_files)} relevant media files")
    
    if not relevant_media_files:
        # No media analysis needed - use basic enhancement
        return await enhance_without_media(
            user_request, conversation_history, current_composition, 
            media_library, preview_settings, gemini_api
        )
    else:
        # Media analysis needed - use enhanced enhancement
        return await enhance_with_media(
            user_request, conversation_history, current_composition,
            relevant_media_files, media_library, gemini_api
        )


async def enhance_without_media(
    user_request: str,
    conversation_history: Optional[List[Dict[str, Any]]],
    current_composition: Optional[str],
    media_library: Optional[List[Dict[str, Any]]],
    preview_settings: Dict[str, Any],
    gemini_api: Any
) -> str:
    """Simple enhancement without media analysis - resolve textual ambiguities only"""
    
    print("🧠 Synth: Enhancing without media analysis")
    
    # Build simple context
    context_parts = [f"User request: {user_request}"]
    
    if conversation_history:
        recent = conversation_history[-4:]  # Last 2 exchanges
        context_parts.append("Recent conversation:")
        for msg in recent:
            # Handle ConversationMessage Pydantic model
            if hasattr(msg, 'user_request') and hasattr(msg, 'ai_response'):
                context_parts.append(f"user: {msg.user_request}")
                context_parts.append(f"assistant: {msg.ai_response}")
            else:
                # Fallback for dict format
                role = msg.get('role', 'unknown') if hasattr(msg, 'get') else getattr(msg, 'role', 'unknown')
                content = msg.get('content', '') if hasattr(msg, 'get') else getattr(msg, 'content', '')
                context_parts.append(f"{role}: {content}")
    
    if current_composition:
        context_parts.append(f"Current composition exists (duration context available)")
    
    # Add available media files for filename reference
    if media_library:
        context_parts.append("Available media files:")
        for media_item in media_library:
            media_name = media_item.get('name', 'unknown')
            media_type = media_item.get('mediaType', 'unknown')
            context_parts.append(f"- {media_name} ({media_type})")
    
    context_text = "\n".join(context_parts)

    # Use common system instruction
    system_instruction = COMMON_SYSTEM_INSTRUCTION

    # User prompt with context
    prompt = f"""USER REQUEST: "{user_request}"

CONTEXT:
- Current Composition Code: {current_composition or "No current composition"}
- Conversation History: {context_text}"""

    try:
        response = gemini_api.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3
            )
        )
        
        if response and response.text:
            enhanced = response.text.strip()
            print(f"✅ Synth: Enhanced without media: '{enhanced[:100]}...'\n")
            return enhanced
        else:
            return f"Apply the following change: {user_request}"
            
    except Exception as e:
        print(f"❌ Synth: Enhancement failed: {e}")
        return f"Apply the following change: {user_request}"


async def enhance_with_media(
    user_request: str,
    conversation_history: Optional[List[Dict[str, Any]]],
    current_composition: Optional[str],
    relevant_media_files: List[str],
    media_library: Optional[List[Dict[str, Any]]],
    gemini_api: Any
) -> str:
    """Enhanced enhancement with media content analysis"""
    
    print(f"🧠 Synth: Enhancing with {len(relevant_media_files)} media files")
    
    # Build context with media info
    context_parts = [f"User request: {user_request}"]
    
    if conversation_history:
        recent = conversation_history[-4:]
        context_parts.append("Recent conversation:")
        for msg in recent:
            # Handle ConversationMessage Pydantic model
            if hasattr(msg, 'user_request') and hasattr(msg, 'ai_response'):
                context_parts.append(f"user: {msg.user_request}")
                context_parts.append(f"assistant: {msg.ai_response}")
            else:
                # Fallback for dict format
                role = msg.get('role', 'unknown') if hasattr(msg, 'get') else getattr(msg, 'role', 'unknown')
                content = msg.get('content', '') if hasattr(msg, 'get') else getattr(msg, 'content', '')
                context_parts.append(f"{role}: {content}")
    
    # Extract composition duration for timing calculations
    duration = 0.0
    if current_composition:
        import re
        duration_patterns = [
            r'DURATION:\s*(\d+(?:\.\d+)?)',
            r'AI-determined Duration:\s*(\d+(?:\.\d+)?)\s*seconds'
        ]
        for pattern in duration_patterns:
            match = re.search(pattern, current_composition)
            if match:
                duration = float(match.group(1))
                break
        context_parts.append(f"Current composition duration: {duration} seconds")
    
    # Add media file info
    context_parts.append("Relevant media files:")
    for media_name in relevant_media_files:
        if media_library:
            media_item = next((m for m in media_library if m.get('name') == media_name), None)
            if media_item:
                media_type = media_item.get('mediaType', 'unknown')
                media_duration = media_item.get('durationInSeconds', 0)
                if media_type == 'video' and media_duration:
                    context_parts.append(f"- {media_name}: {media_type} ({media_duration}s)")
                else:
                    context_parts.append(f"- {media_name}: {media_type}")
    
    context_text = "\n".join(context_parts)
    
    # System instruction with role, requirements and examples
    system_instruction = COMMON_SYSTEM_INSTRUCTION + """

CRITICAL: SOURCE MEDIA TIMING REFERENCE
When analyzing video content and referencing specific moments, always specify timestamps as they appear in the SOURCE MEDIA FILE with clear file identification.

⚠️ TIMING INSTRUCTION: Reference video moments using their original timestamps from the source media file. Always clearly specify which media file the timestamp refers to. The code generator will handle composition timing conversion.

⚠️ KEY PATTERNS FOR VIDEO REFERENCES:
- Timing: "at X seconds in source media file 'filename.ext'"
- Position: "positioned [relative to video frame content/areas]" 
- Properties: Reference visual elements in source video rather than absolute coordinates

⚠️ CRITICAL: Your output must be clearly actionable for a Remotion code generator:
- Reference source media timing: "at X seconds in source media file 'filename.ext'"
- Reference video frame positions: "positioned relative to [video content/object]"
- Use descriptive positioning relative to video content rather than absolute coordinates
- Include visual styling specifications (colors, fonts, animations)
- Provide concrete content and timing values
- Ensure the request can be executed without requiring video analysis

Return ONLY the enhanced request as a single, comprehensive instruction."""

    # User prompt with specific request and context
    prompt = f"""USER REQUEST: "{user_request}"

CONTEXT:
- Current Composition Code: {current_composition or "No current composition"}
- Conversation History: {context_text}
- Relevant Media Files: {len(relevant_media_files)} files for analysis"""

    try:
        # Prepare content for Gemini (text + media files)
        content_parts = [prompt]
        
        # Add media files with Gemini file IDs
        if media_library:
            for media_name in relevant_media_files:
                media_item = next((m for m in media_library if m.get('name') == media_name), None)
                if media_item and media_item.get('gemini_file_id'):
                    try:
                        gemini_file = gemini_api.files.get(name=media_item['gemini_file_id'])
                        content_parts.append(gemini_file)
                        print(f"🧠 Synth: Added {media_name} for analysis")
                    except Exception as e:
                        print(f"⚠️ Synth: Failed to load {media_name}: {e}")
        
        response = gemini_api.models.generate_content(
            model="gemini-2.5-flash",
            contents=content_parts,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.4
            )
        )
        
        if response and response.text:
            enhanced = response.text.strip()
            print(f"✅ Synth: Enhanced with media: '{enhanced}...'\n")
            return enhanced
        else:
            return f"Apply the following change: {user_request} (using relevant media files)"
            
    except Exception as e:
        print(f"❌ Synth: Media enhancement failed: {e}")
        return f"Apply the following change: {user_request} (using relevant media files)"
