import os
import subprocess
import tempfile
import json
import time
import re
import shutil

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Import code generation functionality
from code_generator import generate_composition_with_validation

load_dotenv()

# Get API key (used for both regular and Vertex AI fallback)
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# Check if we should use Vertex AI
USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "false").lower() == "true"
GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() == "true"

# Use Vertex AI if either flag is set
if USE_VERTEX_AI or GOOGLE_GENAI_USE_VERTEXAI:
    # Initialize Vertex AI client
    gemini_api = genai.Client(
        vertexai=True,
        project=os.getenv("VERTEX_PROJECT_ID"),
        location=os.getenv("VERTEX_LOCATION", "europe-west1")
    )
    print(f"🔥 Using Vertex AI - Project: {os.getenv('VERTEX_PROJECT_ID')}, Location: {os.getenv('VERTEX_LOCATION', 'europe-west1')}")
else:
    # Use regular Gemini API
    gemini_api = genai.Client(api_key=GEMINI_API_KEY)
    print("🔥 Using regular Gemini API")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    message: str  # the full user message


class ConversationMessage(BaseModel):
    user_request: str  # What the user asked for
    ai_response: str  # What the AI generated (explanation)
    generated_code: str  # The code that was generated
    timestamp: str  # When this interaction happened


class CompositionRequest(BaseModel):
    user_request: str  # User's description of what they want
    preview_settings: Dict[str, Any]  # Current preview settings (width, height, etc.)
    media_library: Optional[List[Dict[str, Any]]] = []  # Available media files in library
    current_generated_code: Optional[str] = None  # Current AI-generated TSX code for context
    conversation_history: Optional[List[ConversationMessage]] = []  # Past requests and responses for context


class GeneratedComposition(BaseModel):
    tsx_code: str  # Raw Remotion TSX composition code
    explanation: str
    duration: float
    success: bool


class CompositionResponse(BaseModel):
    composition_code: str  # Generated Remotion composition TSX code
    content_data: List[Dict[str, Any]]  # For backwards compatibility (empty)
    explanation: str  # Human-readable explanation of what was generated
    duration: float  # Duration in seconds
    success: bool
    error_message: Optional[str] = None


@app.post("/ai/generate-composition")
async def generate_composition(request: CompositionRequest) -> CompositionResponse:
    """Generate a new Remotion composition based on user request and current context with validation."""
    # Convert request to dict for the code generator module
    request_dict = {
        "user_request": request.user_request,
        "preview_settings": request.preview_settings,
        "media_library": request.media_library,
        "current_generated_code": request.current_generated_code,
        "conversation_history": request.conversation_history
    }
    
    # Call the code generation module with the appropriate parameters
    result = await generate_composition_with_validation(
        request_dict, 
        gemini_api,
        USE_VERTEX_AI or GOOGLE_GENAI_USE_VERTEXAI
    )
    
    # Convert result back to the response model
    return CompositionResponse(
        composition_code=result["composition_code"],
        content_data=result["content_data"],
        explanation=result["explanation"],
        duration=result["duration"],
        success=result["success"],
        error_message=result.get("error_message")
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
