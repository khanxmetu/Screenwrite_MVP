import os
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
    """Google Gemini API provider"""
    
    def __init__(self, api_client: Any):
        self.api_client = api_client
    
    def generate_content(self, system_instruction: str, user_prompt: str) -> str:
        response = self.api_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3
            )
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
    
    # Override with specific type if provided
    if provider_type == 'claude':
        return ClaudeProvider()
    elif provider_type == 'vertex':
        return VertexAIProvider()
    elif provider_type == 'gemini':
        # For direct gemini, we need to handle the API client differently
        # This will be handled in the calling code with fallback logic
        raise ImportError("Direct Gemini provider requires API client - use fallback logic")
    
    # Auto-detect based on environment
    if use_claude:
        return ClaudeProvider()
    elif use_vertex_ai:
        return VertexAIProvider()
    else:
        # Default case - will trigger fallback logic in calling code
        raise ImportError("Default provider requires API client - use fallback logic")
