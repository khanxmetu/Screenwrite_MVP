import os
import subprocess
import tempfile
import json
import time
import re
import shutil

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Import code generation functionality
from code_generator import generate_composition_with_validation
from synth import synthesize_request
from media_checker import check_media_relevance

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
    preview_frame: Optional[str] = None  # Base64 encoded screenshot of current frame


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


class GeminiUploadResponse(BaseModel):
    success: bool
    gemini_file_id: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    error_message: Optional[str] = None


@app.post("/upload-to-gemini")
async def upload_to_gemini(file: UploadFile = File(...)) -> GeminiUploadResponse:
    """Upload a file to Gemini Files API for later analysis."""
    
    try:
        print(f"📤 Gemini Upload: Uploading {file.filename} ({file.content_type})")
        
        # Read file content
        file_content = await file.read()
        
        # Create temporary file for Gemini upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
            tmp_file.write(file_content)
            tmp_file.flush()
            
            # Upload to Gemini Files API with correct method signature
            uploaded_file = gemini_api.files.upload(file=tmp_file.name)
            
            # Clean up temporary file
            os.unlink(tmp_file.name)
        
        print(f"✅ Gemini Upload: Success - File ID: {uploaded_file.name}")
        
        return GeminiUploadResponse(
            success=True,
            gemini_file_id=uploaded_file.name,
            file_name=file.filename,
            mime_type=file.content_type
        )
        
    except Exception as e:
        print(f"❌ Gemini Upload: Failed - {str(e)}")
        
        # Provide user-friendly error messages
        error_msg = str(e)
        if "API key" in error_msg.lower():
            user_error = "AI service authentication failed. Please check server configuration."
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            user_error = "Network connection error. Please check your internet connection and try again."
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            user_error = "AI service quota exceeded. Please try again later."
        else:
            user_error = "AI analysis service is temporarily unavailable. Please try again later."
        
        return GeminiUploadResponse(
            success=False,
            error_message=user_error
        )


@app.post("/ai/generate-composition")
async def generate_composition(request: CompositionRequest) -> CompositionResponse:
    """Generate a new Remotion composition using the new streamlined Synth-MediaChecker-Generator architecture."""
    
    print(f"🎬 Main: Processing request: '{request.user_request}'")
    
    # Step 1: Media Checker - Determine which media files are relevant
    relevant_media_files = await check_media_relevance(
        user_request=request.user_request,
        current_composition=request.current_generated_code,
        media_library=request.media_library or [],
        gemini_api=gemini_api
    )
    
    print(f"📋 Main: Media Checker found {len(relevant_media_files)} relevant files")
    
    # Step 2: Enhanced Synth - Transform request with media analysis capabilities
    enhanced_request = await synthesize_request(
        user_request=request.user_request,
        conversation_history=request.conversation_history,
        current_composition=request.current_generated_code,
        relevant_media_files=relevant_media_files,
        media_library=request.media_library,
        preview_settings=request.preview_settings,
        gemini_api=gemini_api
    )
    
    print(f"🧠 Main: Enhanced Synth completed - Final request: '{enhanced_request[:150]}...'")
    
    # Step 3: Generate composition using enhanced request
    print(f"⚙️ Main: Generating composition with enhanced request")
    
    # Convert to dict format expected by code generator
    enhanced_request_dict = {
        "user_request": enhanced_request,  # Use enhanced request instead of original
        "preview_settings": request.preview_settings,
        "media_library": request.media_library,
        "current_generated_code": request.current_generated_code,
        "conversation_history": request.conversation_history
    }
    
    # Call the existing code generation module
    result = await generate_composition_with_validation(
        enhanced_request_dict, 
        gemini_api,
        USE_VERTEX_AI or GOOGLE_GENAI_USE_VERTEXAI
    )
    
    print(f"✅ Main: Generation completed - Success: {result['success']}")
    
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
