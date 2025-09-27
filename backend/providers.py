import os
import time
import uuid
import base64
import io
from typing import Any
from google import genai
from google.genai import types
import anthropic


class AIProvider:
    """Abstract interface for AI content generation"""
    
    def generate_content(self, system_instruction: str, user_prompt: str) -> str:
        """Generate content using the AI provider"""
        raise NotImplementedError


class GeminiProvider(AIProvider):
    """Google Gemini API provider with structured output"""
    
    def __init__(self, api_client: Any = None):
        if api_client is None:
            # Create our own client if none provided
            import os
            from google import genai
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required")
            self.api_client = genai.Client(api_key=api_key)
        else:
            self.api_client = api_client
    
    def generate_content(self, system_instruction: str, user_prompt: str) -> str:
        # Define the schema using Gemini's Schema format directly
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "clips": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "startTimeInSeconds": {"type": "number"},
                                "endTimeInSeconds": {"type": "number"},
                                "element": {"type": "string"},
                                "transitionFromPrevious": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"},
                                        "durationInSeconds": {"type": "number"},
                                        "direction": {"type": "string"}
                                    },
                                    "required": ["type", "durationInSeconds"]
                                },
                                "transitionToNext": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"},
                                        "durationInSeconds": {"type": "number"},
                                        "direction": {"type": "string"}
                                    },
                                    "required": ["type", "durationInSeconds"]
                                }
                            },
                            "required": ["id", "startTimeInSeconds", "endTimeInSeconds", "element"]
                        }
                    }
                },
                "required": ["clips"]
            }
        }
        
        response = self.api_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config={
                "system_instruction": system_instruction,
                "temperature": 0.3,
                "response_mime_type": "application/json",
                "response_schema": schema
            }
        )
        return response.text.strip()


class VertexAIProvider(AIProvider):
    """Google Vertex AI fine-tuned model provider"""
    
    def __init__(self):
        # Set environment variables for Vertex AI
        os.environ['GOOGLE_CLOUD_PROJECT'] = "24816576653"
        os.environ['GOOGLE_CLOUD_LOCATION'] = "europe-west1"
        os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = "True"
        
        self.client = genai.Client()
        self.endpoint_name = "projects/24816576653/locations/europe-west1/endpoints/6998941266608128000"
    
    def generate_content(self, system_instruction: str, user_prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.endpoint_name,
            contents=user_prompt,
            config={
                "system_instruction": system_instruction,
                "temperature": 0.0,
            }
        )
        return response.text.strip()


class ClaudeProvider(AIProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self):
        claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not claude_api_key:
            raise Exception("ANTHROPIC_API_KEY environment variable is required when USE_CLAUDE is enabled")
        
        self.client = anthropic.Anthropic(api_key=claude_api_key)
    
    def generate_content(self, system_instruction: str, user_prompt: str) -> str:
        response = self.client.messages.create(
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
        return response.content[0].text.strip()


def get_ai_provider(gemini_api: Any = None, use_vertex_ai: bool = False) -> AIProvider:
    """Factory function to get the appropriate AI provider based on configuration"""
    use_claude = os.getenv('USE_CLAUDE', '').lower() in ['true', '1', 'yes']
    
    if use_claude:
        return ClaudeProvider()
    elif use_vertex_ai:
        return VertexAIProvider()
    else:
        if gemini_api is None:
            raise ValueError("gemini_api is required when not using Claude or Vertex AI")
        return GeminiProvider(gemini_api)


def create_ai_provider(provider_type: str = None) -> AIProvider:
    """Create AI provider based on environment configuration or specified type"""
    use_claude = os.getenv('USE_CLAUDE', '').lower() in ['true', '1', 'yes']
    use_vertex_ai = os.getenv('USE_VERTEX_AI', '').lower() in ['true', '1', 'yes']
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    # Override with specific type if provided
    if provider_type == 'claude':
        return ClaudeProvider()
    elif provider_type == 'vertex':
        return VertexAIProvider()
    elif provider_type == 'gemini':
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        from google import genai
        gemini_api = genai.Client(api_key=gemini_api_key)
        return GeminiProvider(gemini_api)
    
    # Auto-detect based on environment
    if use_claude:
        return ClaudeProvider()
    elif use_vertex_ai:
        return VertexAIProvider()
    else:
        # Default to Gemini if API key is available
        if not gemini_api_key:
            raise ValueError("No AI provider configured - missing API keys")
        from google import genai
        gemini_api = genai.Client(api_key=gemini_api_key)
        return GeminiProvider(gemini_api)


class ContentGenerationProvider:
    """Google Gemini Content Generation Provider for video and image generation"""
    
    def __init__(self, api_client: Any = None):
        if api_client is None:
            # Create our own client if none provided
            import os
            from google import genai
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required")
            self.api_client = genai.Client(api_key=api_key)
        else:
            self.api_client = api_client
    
    async def generate_video(
        self, 
        prompt: str, 
        negative_prompt: str = None, 
        aspect_ratio: str = "16:9", 
        resolution: str = "720p",
        reference_image = None
    ):
        """Generate video using Veo 3 model"""
        try:
            import io
            
            # Choose model based on requirements
            model = "veo-3.0-fast-generate-001"  # Use fast model for better performance
            
            # Build generation config - only negative_prompt goes in config
            config = None
            if negative_prompt:
                config = types.GenerateVideosConfig(negative_prompt=negative_prompt)
            
            # Format reference image for Google API if provided
            formatted_image = None
            if reference_image:
                try:
                    # Convert PIL Image to bytes
                    img_buffer = io.BytesIO()
                    reference_image.save(img_buffer, format='PNG')
                    img_bytes = img_buffer.getvalue()
                    
                    # Create image object with the bytes directly (based on debug output attributes)
                    formatted_image = types.Image(
                        image_bytes=img_bytes,
                        mime_type="image/png"
                    )
                    print(f"✅ Successfully formatted reference image for Veo")
                except Exception as img_error:
                    print(f"⚠️ Could not format reference image: {img_error}")
                    formatted_image = None
            
            # Start video generation (async operation) - aspect_ratio and resolution are direct parameters
            operation = self.api_client.models.generate_videos(
                model=model,
                prompt=prompt,
                image=formatted_image,  # Properly formatted image for image-to-video
                config=config
            )
            
            return operation
            
        except Exception as e:
            print(f"❌ Video generation failed: {str(e)}")
            raise e
    
    async def generate_image(self, prompt: str, reference_images: list = None):
        """Generate image using Imagen 4.0 Fast model"""
        try:
            # Configure image generation with 16:9 aspect ratio and allow all person generation
            config = types.GenerateImagesConfig(
                number_of_images=1,  # Generate single image for efficiency  
                aspect_ratio="16:9"  # Standard screen aspect ratio
            )            # For image generation, use the dedicated generate_images method with Imagen 4.0 Fast
            response = self.api_client.models.generate_images(
                model="imagen-4.0-fast-generate-001",
                prompt=prompt,
                config=config
            )
            
            return response
            
        except Exception as e:
            print(f"❌ Image generation failed: {str(e)}")
            raise e
    
    async def check_video_status(self, operation):
        """Check status of video generation operation"""
        try:
            # Refresh operation status
            updated_operation = self.api_client.operations.get(operation)
            return updated_operation
            
        except Exception as e:
            print(f"❌ Status check failed: {str(e)}")
            raise e
