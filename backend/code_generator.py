import os
import json
import time
from typing import Tuple, List, Dict, Any, Optional

from providers import create_ai_provider
from prompts import build_blueprint_prompt
from blueprint_parser import parse_blueprint_response

# Could any hell be more horrible than now and here?

# REFACTORED MODULAR ARCHITECTURE
# ================================
# This module has been refactored from 595 lines to 180 lines (70% reduction)
# 
# Modular Components:
# - prompts.py: System instructions and prompt building logic (383 lines)  
# - providers.py: AI provider abstraction (Gemini/Claude/Vertex) (95 lines)
# - blueprint_parser.py: Response parsing utilities (86 lines)
# - code_generator.py: Main generation orchestration (180 lines)
#
# All functionality preserved while improving maintainability and organization



async def generate_composition_with_validation(
    request: Dict[str, Any], 
    gemini_api: Any,
    use_vertex_ai: bool = False,
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Generate a CompositionBlueprint JSON using modular AI providers.
    """
    try:
        print(f"Blueprint generation attempt (no validation)")
        
        # Build the blueprint prompt using modular function
        system_instruction, user_prompt = build_blueprint_prompt(request)

        # Create appropriate AI provider
        provider = create_ai_provider()
        
        # Generate using the provider (sync call within async function)
        raw_response = provider.generate_content(system_instruction, user_prompt)
        
        print(f"✅ Generated {len(raw_response)} characters from {provider.__class__.__name__}")
        
        # Parse the response using modular function
        duration, blueprint_json = parse_blueprint_response(raw_response)
        
        # Return in format expected by main.py
        return {
            "composition_code": blueprint_json,  # Frontend expects this field name
            "content_data": [],
            "explanation": f"Generated CompositionBlueprint for: {request.get('user_request', '')}",
            "duration": duration,
            "success": True
        }
        
    except Exception as e:
        print(f"❌ Error in blueprint generation: {e}")
        return {
            "composition_code": "[]",  # Empty blueprint fallback
            "content_data": [],
            "explanation": f"Error generating blueprint: {str(e)}",
            "duration": 10.0,
            "success": False,
            "error_message": str(e)
        }


# Legacy function - keeping same signature for compatibility  
def generate_composition_legacy(
    request: Dict[str, Any], 
    gemini_api: Any,
    use_vertex_ai: bool = False,
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Legacy synchronous wrapper - maintains old AI provider logic temporarily.
    """
    
    try:
        print(f"Legacy blueprint generation")
        
        # Build the blueprint prompt using modular function
        system_instruction, user_prompt = build_blueprint_prompt(request)

        # Check if Claude should be used
        use_claude = os.getenv('USE_CLAUDE', '').lower() in ['true', '1', 'yes']
        
        # Determine provider type
        if use_claude:
            provider_type = 'claude'
        elif use_vertex_ai:
            provider_type = 'vertex'
        else:
            provider_type = 'gemini'
        
        # Use provider factory (fallback to direct imports for legacy support)
        try:
            provider = create_ai_provider(provider_type)
            raw_response = provider.generate_content(system_instruction, user_prompt)
        except ImportError:
            # Fallback to direct provider usage for import errors
            if use_claude:
                import anthropic
                claude_api_key = os.getenv('ANTHROPIC_API_KEY')
                client = anthropic.Anthropic(api_key=claude_api_key)
                response = client.messages.create(
                    max_tokens=8192,
                    model="claude-sonnet-4-20250514", 
                    temperature=0.3,
                    system=system_instruction,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                raw_response = response.content[0].text.strip()
            elif use_vertex_ai:
                from google import genai
                os.environ['GOOGLE_CLOUD_PROJECT'] = "24816576653"
                os.environ['GOOGLE_CLOUD_LOCATION'] = "europe-west1" 
                os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = "True"
                client = genai.Client()
                ENDPOINT_NAME = "projects/24816576653/locations/europe-west1/endpoints/6998941266608128000"
                response = client.models.generate_content(
                    model=ENDPOINT_NAME,
                    contents=user_prompt,
                    config={"system_instruction": system_instruction, "temperature": 0.0}
                )
                raw_response = response.text.strip()
            else:
                from google import genai
                from google.genai import types
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
