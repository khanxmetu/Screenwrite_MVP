"""
Analyzer - Media Content Analysis Engine

Performs content analysis on media files when needed.
Currently placeholder - will be enhanced with actual analysis capabilities.
"""

from typing import Dict, Any, List, Optional


class AnalysisResult:
    """Result from the Analyzer engine"""
    def __init__(
        self, 
        enhanced_request: str,
        media_analysis: Dict[str, Any] = None,
        visual_context: Dict[str, Any] = None
    ):
        self.enhanced_request = enhanced_request
        self.media_analysis = media_analysis or {}
        self.visual_context = visual_context or {}


async def analyze_content(
    enhanced_request: str,
    media_for_analysis: List[str],
    media_library: List[Dict[str, Any]],
    preview_frame: Optional[str],
    gemini_api: Any
) -> AnalysisResult:
    """
    Analyze media content and enhance request with analysis context
    
    Args:
        enhanced_request: The request enhanced by Synth
        media_for_analysis: List of media file names to analyze
        media_library: Full media library with metadata
        preview_frame: Base64 encoded screenshot for visual analysis
        gemini_api: Gemini AI client
        
    Returns:
        AnalysisResult with further enhanced request and analysis data
    """
    
    print(f"🔍 Analyzer: Processing {len(media_for_analysis)} media files")
    
    if not media_for_analysis:
        # No media to analyze, return as-is
        return AnalysisResult(
            enhanced_request=enhanced_request,
            media_analysis={"status": "no_media_to_analyze"},
            visual_context={"status": "no_media_to_analyze"}
        )
    
    # Find Gemini file IDs for the media files to analyze
    gemini_file_refs = []
    for media_name in media_for_analysis:
        # Find the media item in the library
        media_item = next((item for item in media_library if item.get('name') == media_name), None)
        if media_item and media_item.get('gemini_file_id'):
            gemini_file_refs.append({
                'name': media_name,
                'gemini_file_id': media_item['gemini_file_id']
            })
            print(f"📁 Found Gemini file ID for {media_name}: {media_item['gemini_file_id']}")
        else:
            print(f"⚠️ No Gemini file ID found for {media_name}")
    
    if not gemini_file_refs:
        print("❌ No Gemini file references found for analysis")
        return AnalysisResult(
            enhanced_request=enhanced_request,
            media_analysis={"status": "no_gemini_files"},
            visual_context={"status": "no_gemini_files"}
        )
    
    try:
        # Build analysis prompt
        analysis_prompt = f"""Analyze the provided media files and enhance this user request with specific details:

USER REQUEST: "{enhanced_request}"

Your task:
1. Look at the media files and extract specific visual details (colors, positions, styles, timing)
2. Enhance the user request by replacing vague references with exact specifications
3. Provide specific numbers, coordinates, colors (hex codes), timestamps, and measurements
4. Make the request ultra-specific so a code generator can execute it precisely

Focus on:
- Exact colors (hex codes) instead of "red", "blue"
- Specific positions (pixel coordinates) instead of "center", "left" 
- Precise timing (timestamps) instead of "when", "during"
- Exact sizes and measurements instead of "large", "small"
- Specific font/style details if text is involved

Return ONLY the enhanced request as a single, comprehensive instruction."""

        # Call Gemini for analysis
        response = gemini_api.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                *[gemini_api.files.get(name=file_ref['gemini_file_id']) for file_ref in gemini_file_refs],
                analysis_prompt
            ]
        )
        
        enhanced_final_request = response.text.strip()
        
        print(f"✅ Analyzer: Enhanced request: '{enhanced_final_request[:100]}...'")
        
        return AnalysisResult(
            enhanced_request=enhanced_final_request,
            media_analysis={
                "analyzed_files": [ref['name'] for ref in gemini_file_refs],
                "gemini_files_used": [ref['gemini_file_id'] for ref in gemini_file_refs],
                "status": "analyzed"
            },
            visual_context={
                "files_processed": len(gemini_file_refs),
                "status": "completed"
            }
        )
        
    except Exception as e:
        print(f"❌ Analyzer: Failed to analyze media - {str(e)}")
        
        # Return original request if analysis fails
        return AnalysisResult(
            enhanced_request=enhanced_request,
            media_analysis={"status": "analysis_failed", "error": str(e)},
            visual_context={"status": "analysis_failed", "error": str(e)}
        )
