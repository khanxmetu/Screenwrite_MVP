
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
COMMON_SYSTEM_INSTRUCTION = """You are a creative director helping to clarify user requests for video compositions. Speak naturally and create clear plans like a real director would.

🚫 CRITICAL: NEVER EVER output code, technical syntax, or programming language. Only natural human language.
🚫 NO JavaScript, React, CSS properties, or any code syntax
🚫 NO curly braces {}, parentheses for functions, or technical specifications

You can suggest:
- Specific timing (like "starts at 5 seconds" or "fades in over 2 seconds")
- Positioning (like "center of screen", "top left corner", "50% from left")
- Transitions (fade in/out, slide from left/right/top/bottom, wipe across, flip, iris open/close)
- Animations (move, scale, rotate, fade, bounce, spring effects)
- Media files (use exact filenames when available)
- Text styling (large/small, bold, colors, shadows)
- Exact colors (like "white", "red", "#FF0000", "rgba(255,0,0,0.5)")
- Audio control (volume levels, muting, speed changes)
- Video effects (slow motion, fast forward, trimming clips)

EXAMPLES:

User: "Add text saying hello"
You: "Add the word 'Hello' in large white text at the top center of the screen. Have it fade in smoothly over about a second."

User: "Add my logo" 
You: "Place the logo in the top right corner, medium size so it's visible but not dominating. Give it a subtle drop shadow."

User: "Add shore video"
You: "Add shore.mp4 as the main background filling the entire screen. Have it fade in at the beginning."

Always use exact filenames from the available media when mentioned. Create clear, natural plans that describe what viewers will see and when."""


async def synthesize_request(
    user_request: str,
    conversation_history: Optional[List[Dict[str, Any]]],
    current_composition: Optional[str],
    media_library: Optional[List[Dict[str, Any]]],
    preview_settings: Dict[str, Any],
    gemini_api: Any
) -> str:
    """
    Enhanced Synth: Route to appropriate enhancement function based on @ syntax detection
    """
    
    # Detect @filename patterns in user request (handles spaces and extensions)
    import re
    # Pattern handles: @filename.ext, @"filename with spaces.ext", @filename (no extension)
    at_mentioned_files = []
    
    # Pattern 1: @"quoted filename with spaces.ext" (remove quotes from result)
    quoted_pattern = r'@"([^"]+)"'
    quoted_matches = re.findall(quoted_pattern, user_request)
    at_mentioned_files.extend(quoted_matches)
    
    # Remove quoted sections from text to avoid double-matching
    text_without_quotes = re.sub(quoted_pattern, '', user_request)
    
    # Pattern 2: @filename.ext (with common extensions, allowing spaces until punctuation/whitespace)
    extension_pattern = r'@([^\s@"]+(?:\s+[^\s@"]+)*\.(?:mp4|mov|avi|mkv|webm|jpg|jpeg|png|gif|webp|mp3|wav|flac|aac|m4a))'
    extension_matches = re.findall(extension_pattern, text_without_quotes, re.IGNORECASE)
    at_mentioned_files.extend(extension_matches)
    
    # Pattern 3: @filename (no extension, stops at whitespace/punctuation)
    simple_pattern = r'@([^\s@"]+)'
    simple_matches = re.findall(simple_pattern, text_without_quotes)
    # Only add if not already captured by extension pattern
    for match in simple_matches:
        if match not in at_mentioned_files and not any(match in ext_match for ext_match in extension_matches):
            at_mentioned_files.append(match)
    
    # Remove duplicates while preserving order
    at_mentioned_files = list(dict.fromkeys(at_mentioned_files))
    
    # Validate that @-mentioned files exist in media library
    valid_files = []
    invalid_files = []
    
    if media_library:
        available_files = [media.get('name', '') for media in media_library]
        for mentioned_file in at_mentioned_files:
            if mentioned_file in available_files:
                valid_files.append(mentioned_file)
            else:
                invalid_files.append(mentioned_file)
    else:
        # No media library provided - all mentions are invalid
        invalid_files = at_mentioned_files.copy()
    
    # Log validation results
    if invalid_files:
        print(f"⚠️ Synth: Invalid @-mentioned files (not found): {invalid_files}")
        if media_library:
            available_names = [media.get('name', 'unnamed') for media in media_library]
            print(f"📁 Synth: Available files: {available_names}")
    
    print(f"🧠 Synth: Processing request with {len(valid_files)} valid @-mentioned files: {valid_files}")
    
    if not valid_files:
        # No valid @filename mentions - use basic enhancement
        return await enhance_without_media(
            user_request, conversation_history, current_composition, 
            media_library, preview_settings, gemini_api
        )
    else:
        # Valid @filename mentions found - use enhanced enhancement with media analysis
        return await enhance_with_media(
            user_request, conversation_history, current_composition,
            valid_files, media_library, gemini_api
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
        context_parts.append("⚠️ CRITICAL MEDIA RULE: ONLY reference media files that are explicitly listed below. If no media files are available, create compositions using text, shapes, animations, and visual effects only.")
        context_parts.append("⚠️ CRITICAL MEDIA FILE NAMING: Always use exact file names from this list. Never use generic names like 'video.mp4' or 'image.jpg'.")
        for media_item in media_library:
            media_name = media_item.get('name', 'unknown')
            media_type = media_item.get('mediaType', 'unknown')
            media_duration = media_item.get('durationInSeconds', 0)
            media_width = media_item.get('media_width', 0)
            media_height = media_item.get('media_height', 0)
            
            # Build comprehensive media description with metadata
            media_info = f"- {media_name} ({media_type}"
            
            # Add resolution for video/image
            if media_type in ['video', 'image'] and media_width and media_height:
                media_info += f", {media_width}x{media_height}"
            
            # Add duration for video/audio
            if media_type in ['video', 'audio'] and media_duration:
                media_info += f", {media_duration}s"
            
            media_info += ")"
            context_parts.append(media_info)
    
    context_text = "\n".join(context_parts)

    # Use common system instruction
    system_instruction = COMMON_SYSTEM_INSTRUCTION

    # User prompt with context
    prompt = f"""USER REQUEST: "{user_request}"

ANALYSIS CONTEXT (for understanding current state only - DO NOT copy or reference in output):
{context_text}

⚠️ CRITICAL: Analyze the context for understanding, but output ONLY natural language creative direction. Never include code or technical syntax in your response."""

    try:
        response = gemini_api.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=1.0
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
    context_parts.append("⚠️ CRITICAL MEDIA RULE: ONLY reference media files that are explicitly listed below. Use exact file names from this list.")
    context_parts.append("⚠️ CRITICAL MEDIA FILE NAMING: Always use exact file names from this list. Never use generic names like 'video.mp4' or 'image.jpg'.")
    found_files = []
    missing_files = []
    
    for media_name in relevant_media_files:
        if media_library:
            media_item = next((m for m in media_library if m.get('name') == media_name), None)
            if media_item:
                found_files.append(media_name)
                media_type = media_item.get('mediaType', 'unknown')
                media_duration = media_item.get('durationInSeconds', 0)
                media_width = media_item.get('media_width', 0)
                media_height = media_item.get('media_height', 0)
                
                # Build comprehensive media description with metadata
                media_info = f"- {media_name}: {media_type}"
                
                # Add resolution for video/image
                if media_type in ['video', 'image'] and media_width and media_height:
                    media_info += f" ({media_width}x{media_height})"
                
                # Add duration for video/audio
                if media_type in ['video', 'audio'] and media_duration:
                    media_info += f" - {media_duration}s duration"
                
                context_parts.append(media_info)
            else:
                missing_files.append(media_name)
    
    if missing_files:
        print(f"⚠️ Synth: Media files not found in library: {missing_files}")
        context_parts.append(f"Note: Files not found in media library: {missing_files}")
    context_text = "\n".join(context_parts)
    
    # System instruction with role, requirements and examples
    system_instruction = COMMON_SYSTEM_INSTRUCTION + """

CRITICAL: SOURCE MEDIA TIMING REFERENCE
When analyzing video content and referencing specific moments, always specify timestamps as they appear in the SOURCE MEDIA FILE with clear file identification.

⚠️ TIMING INSTRUCTION: Reference video moments using their original timestamps from the source media file. Always clearly specify which media file the timestamp refers to. The code generator will handle composition timing conversion.

⚠️ KEY PATTERNS FOR VIDEO REFERENCE:
- Timing: "at X seconds in source media file 'filename.ext'"

⚠️ FOCUS ON CREATIVE INTENT: Do not output technical implementation or code. Focus purely on creative direction and visual specifications.

⚠️ CRITICAL OUTPUT RULE: NEVER include JavaScript code, React.createElement statements, or any programming syntax in your response. Output ONLY natural language creative direction.

⚠️ FORBIDDEN OUTPUT PATTERNS:
- React.createElement(...) 
- const frame = useCurrentFrame();
- Any JavaScript syntax
- Code blocks or technical implementation

✅ CORRECT OUTPUT PATTERN: Natural language creative specifications only.

Return ONLY the creative execution plan - no code, no explanations, no questions."""

    # User prompt with specific request and context
    prompt = f"""USER REQUEST: "{user_request}"

ANALYSIS CONTEXT (for understanding current state only - DO NOT copy or reference in output):
- Current Composition: {current_composition or "No current composition"}
- Conversation History: {context_text}
- Relevant Media Files: {len(relevant_media_files)} files for analysis

⚠️ CRITICAL: Analyze the context for understanding, but output ONLY natural language creative direction. Never include code or technical syntax in your response."""

    try:
        # Prepare content for Gemini (text + media files)
        content_parts = [prompt]
        
        # Add media files with Gemini file IDs
        if media_library:
            for media_name in relevant_media_files:
                media_item = next((m for m in media_library if m.get('name') == media_name), None)
                if media_item and media_item.get('gemini_file_id'):
                    try:
                        # Retry mechanism for files not yet ACTIVE
                        max_retries = 10
                        retry_delay = 2  # seconds
                        
                        for attempt in range(max_retries):
                            gemini_file = gemini_api.files.get(name=media_item['gemini_file_id'])
                            
                            if gemini_file.state.name == 'ACTIVE':
                                content_parts.append(gemini_file)
                                print(f"🧠 Synth: Added {media_name} for analysis (ready after {attempt + 1} attempts)")
                                break
                            elif gemini_file.state.name == 'FAILED':
                                print(f"❌ Synth: {media_name} failed to process, skipping")
                                break
                            else:
                                print(f"⏳ Synth: {media_name} not ready (state: {gemini_file.state.name}), retrying in {retry_delay}s... ({attempt + 1}/{max_retries})")
                                if attempt < max_retries - 1:  # Don't sleep on last attempt
                                    import asyncio
                                    await asyncio.sleep(retry_delay)
                        else:
                            # All retries exhausted
                            print(f"⚠️ Synth: {media_name} not ready after {max_retries} attempts, proceeding without analysis")
                            
                    except Exception as e:
                        print(f"⚠️ Synth: Failed to load {media_name}: {e}")
        
        response = gemini_api.models.generate_content(
            model="gemini-2.5-flash",
            contents=content_parts,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=1.0
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
