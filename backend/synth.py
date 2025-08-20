"""
Synth - AI Request Enhancement Engine

Takes ambiguous user requests and transforms them into crystal-clear, 
unambiguous instructions by analyzing all available context.
"""

import json
from typing import Dict, Any, List, Tuple, Optional
from google import genai
from google.genai import types


class SynthResult:
    """Result from the Synth engine"""
    def __init__(
        self, 
        enhanced_request: str, 
        needs_analysis: bool, 
        media_for_analysis: List[str] = None,
        confidence_score: float = 0.0,
        context_used: List[str] = None
    ):
        self.enhanced_request = enhanced_request
        self.needs_analysis = needs_analysis
        self.media_for_analysis = media_for_analysis or []
        self.confidence_score = confidence_score
        self.context_used = context_used or []


async def synthesize_request(
    user_request: str,
    conversation_history: Optional[List[Dict[str, Any]]],
    current_composition: Optional[str],
    preview_frame: Optional[str],
    media_library: Optional[List[Dict[str, Any]]],
    preview_settings: Dict[str, Any],
    gemini_api: Any
) -> SynthResult:
    """
    Main Synth function: Transform vague user request into unambiguous instructions
    
    Args:
        user_request: Raw user input (often vague)
        conversation_history: Previous interactions for context
        current_composition: Current TSX composition code
        preview_frame: Base64 encoded screenshot of current frame
        media_library: Available media assets
        preview_settings: Current preview configuration
        gemini_api: Gemini AI client
        
    Returns:
        SynthResult with enhanced request and routing decision
    """
    
    print(f"🧠 Synth: Processing request: '{user_request}'")
    
    # Build comprehensive context
    context = _build_synthesis_context(
        user_request=user_request,
        conversation_history=conversation_history,
        current_composition=current_composition,
        preview_frame=preview_frame,
        media_library=media_library,
        preview_settings=preview_settings
    )
    
    # Generate enhanced request using AI
    enhanced_request, ai_needs_analysis, ai_media_files = _ai_enhance_request(context, gemini_api)
    
    # Determine if media analysis is needed (use AI decision or fallback logic)
    needs_analysis, media_for_analysis = _determine_analysis_needs(
        enhanced_request, 
        user_request, 
        media_library,
        preview_frame,
        ai_decision=ai_needs_analysis,
        ai_media_files=ai_media_files
    )
    
    # Calculate confidence and track context usage
    confidence_score = _calculate_confidence(context, enhanced_request)
    context_used = _identify_context_used(context)
    
    result = SynthResult(
        enhanced_request=enhanced_request,
        needs_analysis=needs_analysis,
        media_for_analysis=media_for_analysis,
        confidence_score=confidence_score,
        context_used=context_used
    )
    
    print(f"✅ Synth: Enhanced request: '{enhanced_request[:100]}...'")
    print(f"📊 Synth: Needs analysis: {needs_analysis}, Media count: {len(media_for_analysis)}")
    
    return result


def _build_synthesis_context(
    user_request: str,
    conversation_history: Optional[List[Dict[str, Any]]],
    current_composition: Optional[str],
    preview_frame: Optional[str],
    media_library: Optional[List[Dict[str, Any]]],
    preview_settings: Dict[str, Any]
) -> Dict[str, Any]:
    """Build comprehensive context for synthesis"""
    
    context = {
        "user_request": user_request,
        "preview_settings": preview_settings
    }
    
    # Add conversation history context
    if conversation_history:
        context["conversation_history"] = conversation_history  # Give raw history to LLM
    else:
        context["conversation_history"] = "No previous conversation"
    
    # Add current composition context
    if current_composition:
        context["current_composition_code"] = current_composition  # Give raw code to LLM
    else:
        context["current_composition_code"] = "No current composition"
    
    # Add visual context from frame
    if preview_frame:
        context["has_visual_context"] = True
        # For now, just note that we have visual context
        # Later this will be enhanced with actual frame analysis
    
    # Add media context
    if media_library:
        context["media_summary"] = _summarize_media_library(media_library)
        context["available_assets"] = _categorize_media_assets(media_library)
    
    return context


def _summarize_media_library(media_library: List[Dict[str, Any]]) -> str:
    """Create summary of available media"""
    if not media_library:
        return "No media available"
    
    counts = {"video": 0, "image": 0, "audio": 0, "text": 0}
    
    for media in media_library:
        media_type = media.get('mediaType', 'unknown')
        if media_type in counts:
            counts[media_type] += 1
    
    summary_parts = []
    for media_type, count in counts.items():
        if count > 0:
            summary_parts.append(f"{count} {media_type}{'s' if count > 1 else ''}")
    
    return f"Available: {', '.join(summary_parts)}"


def _categorize_media_assets(media_library: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Categorize media assets by type"""
    categories = {"videos": [], "images": [], "audio": [], "text": []}
    
    for media in media_library:
        media_type = media.get('mediaType', 'unknown')
        name = media.get('name', 'unnamed')
        
        if media_type == 'video':
            categories["videos"].append(name)
        elif media_type == 'image':
            categories["images"].append(name)
        elif media_type == 'audio':
            categories["audio"].append(name)
        elif media_type == 'text':
            categories["text"].append(name)
    
    return categories


def _ai_enhance_request(context: Dict[str, Any], gemini_api: Any) -> Tuple[str, bool, List[str]]:
    """Use AI to enhance the vague request into specific instructions"""
    
    # Define the response schema for structured output
    response_schema = {
        "type": "object",
        "properties": {
            "enhanced_request": {
                "type": "string",
                "description": "One comprehensive, executable request that maximizes Remotion generation success and user intent accomplishment"
            },
            "needs_analysis": {
                "type": "boolean",
                "description": "Whether media content analysis is required to fulfill the request"
            },
            "media_files_to_analyze": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of specific media file names that need analysis"
            }
        },
        "required": ["enhanced_request", "needs_analysis", "media_files_to_analyze"]
    }
    
    # Build the synthesis prompt
    prompt = _build_synthesis_prompt(context)
    
    try:
        print(f"🧠 Synth: About to call Gemini API with model: gemini-2.5-flash")
        print(f"🧠 Synth: Prompt length: {len(prompt)} characters")
        print(f"🧠 Synth: Using structured output with schema")
        
        # Call Gemini with structured output
        response = gemini_api.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )
        
        print(f"🧠 Synth: Received response object: {type(response)}")
        print(f"🧠 Synth: Response is None: {response is None}")
        
        # Check if response is valid
        if response is None:
            print("❌ Synth: Received None response from Gemini API")
            return _fallback_enhancement(context), False, []
            
        if not hasattr(response, 'text') or response.text is None:
            print(f"❌ Synth: Response has no text attribute or text is None. Response attributes: {dir(response)}")
            return _fallback_enhancement(context), False, []
        
        print(f"🧠 Synth: Response text length: {len(response.text)}")
        print(f"🧠 Synth: Response text preview: {response.text[:200]}...")
        
        # Parse the structured JSON response
        try:
            result = json.loads(response.text.strip())
            enhanced_request = result.get("enhanced_request", "")
            needs_analysis = result.get("needs_analysis", False)
            media_files_to_analyze = result.get("media_files_to_analyze", [])
            return enhanced_request, needs_analysis, media_files_to_analyze
        except json.JSONDecodeError as json_error:
            print(f"❌ Synth: Failed to parse structured JSON response: {json_error}")
            print(f"❌ Synth: Raw response text: {response.text}")
            return _fallback_enhancement(context), False, []
        
    except Exception as e:
        print(f"❌ Synth AI enhancement failed: {e}")
        # Fallback: return original request with basic enhancement
        return _fallback_enhancement(context), False, []


def _build_synthesis_prompt(context: Dict[str, Any]) -> str:
    """Build the AI prompt for request synthesis"""
    
    user_request = context.get("user_request", "")
    
    prompt = f"""You are a request disambiguation engine. Your job is to create ONE comprehensive enhanced request that maximizes the likelihood of successful Remotion generation and accomplishment of the user's intent.

USER REQUEST: "{user_request}"

CONTEXT:
- Preview Settings: {context.get('preview_settings', {})}
- Current Composition Code: {context.get('current_composition_code', 'None')}
- Available Media: {context.get('media_summary', 'None')}
- Conversation History: {context.get('conversation_history', 'None')}
- Available Media Assets: {context.get('available_assets', {})}

YOUR PROCESS to create the enhanced request:
1. UNDERSTAND USER INTENT: Determine what the user actually wants by analyzing their vague language, conversation history, and current composition state
2. TECHNICAL SPECIFICATION: Translate that intent into specific Remotion parameters (timing, positioning, assets, animations, styling)
3. EXECUTABLE FORMULATION: Structure the request so the Remotion LLM can execute it without confusion or failure

REQUIREMENTS for the enhanced request:
- Unequivocally states what the user wants to achieve
- Includes exact parameters (timing in seconds/frames, positions in pixels/percentages)
- References specific media assets by name
- Is actionable and executable by the downstream Remotion generator
- Eliminates ambiguity that could cause generation failure
- Maximizes probability of accomplishing the user's actual intent

ANALYSIS DECISION: Determine if understanding the user's intent requires content analysis of available media files:
- Does the request involve understanding video content, extracting colors/styles, scene analysis, or content matching?
- Does the user reference visual elements that need to be analyzed ("match the style", "extract colors", "based on what you see")?
- If analysis is needed, specify which exact media files from the available assets require analysis

OUTPUT: Return ONLY a JSON object with these exact fields:
{{
    "enhanced_request": "one comprehensive, executable request that maximizes Remotion generation success and user intent accomplishment",
    "needs_analysis": true/false,
    "media_files_to_analyze": ["specific-file-1.mp4", "specific-file-2.jpg"] or []
}}"""

    return prompt


def _fallback_enhancement(context: Dict[str, Any]) -> str:
    """Fallback enhancement when AI fails"""
    user_request = context.get("user_request", "")
    
    # Basic enhancement based on context
    enhanced = f"Apply the following change: {user_request}"
    
    # Add context if available
    if context.get("current_composition_code") and context.get("current_composition_code") != "No current composition":
        enhanced += f" to the existing composition"
    
    if context.get("media_summary"):
        enhanced += f" using available media: {context['media_summary']}"
    
    return enhanced


def _determine_analysis_needs(
    enhanced_request: str, 
    original_request: str, 
    media_library: Optional[List[Dict[str, Any]]],
    preview_frame: Optional[str],
    ai_decision: bool = False,
    ai_media_files: List[str] = None
) -> Tuple[bool, List[str]]:
    """Determine if media analysis is needed and which media to analyze"""
    
    # Start with AI decision and media file list if provided
    needs_analysis = ai_decision
    media_for_analysis = ai_media_files or []
    
    # If AI didn't decide analysis is needed, check fallback triggers
    if not needs_analysis:
        analysis_triggers = [
            "analyze", "extract", "match style", "similar to", "based on content",
            "identify", "detect", "recognize", "understand the video",
            "what's in the", "scene analysis", "color palette", "visual style"
        ]
        
        combined_text = f"{original_request} {enhanced_request}".lower()
        
        # Check if any analysis triggers are present
        for trigger in analysis_triggers:
            if trigger in combined_text:
                needs_analysis = True
                break
        
        # Check if frame analysis is needed
        if preview_frame and any(word in combined_text for word in ["frame", "current", "what i see", "visible"]):
            needs_analysis = True
        
        # If analysis is needed but AI didn't specify files, include all analyzable media
        if needs_analysis and not media_for_analysis and media_library:
            for media in media_library:
                if media.get('mediaType') in ['video', 'image']:
                    media_name = media.get('name', '')
                    if media_name:
                        media_for_analysis.append(media_name)
    
    return needs_analysis, media_for_analysis


def _calculate_confidence(context: Dict[str, Any], enhanced_request: str) -> float:
    """Calculate confidence score for the synthesis"""
    confidence = 0.5  # Base confidence
    
    # Increase confidence based on available context
    if context.get("conversation_history") and context.get("conversation_history") != "No previous conversation":
        confidence += 0.2
    
    if context.get("current_composition_code") and context.get("current_composition_code") != "No current composition":
        confidence += 0.2
    
    if context.get("media_summary") != "No media available":
        confidence += 0.1
    
    # Decrease confidence for very vague requests
    vague_indicators = ["better", "good", "nice", "fix", "improve"]
    user_request = context.get("user_request", "").lower()
    
    for indicator in vague_indicators:
        if indicator in user_request and len(user_request.split()) < 5:
            confidence -= 0.1
    
    return max(0.0, min(1.0, confidence))


def _identify_context_used(context: Dict[str, Any]) -> List[str]:
    """Identify which context sources were used"""
    used = []
    
    if context.get("conversation_history") and context.get("conversation_history") != "No previous conversation":
        used.append("conversation_history")
    
    if context.get("current_composition_code") and context.get("current_composition_code") != "No current composition":
        used.append("current_composition")
    
    if context.get("media_summary") != "No media available":
        used.append("media_library")
    
    if context.get("has_visual_context"):
        used.append("preview_frame")
    
    return used
