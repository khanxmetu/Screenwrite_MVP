import os
import subprocess
import tempfile
import json
import time
import re
import shutil
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Import code generation functionality
import code_generator
from code_generator import generate_composition_with_validation
from synth import synthesize_request

load_dotenv()

# Get API key (used for both regular and Vertex AI fallback)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Check if we should use Vertex AI
USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "false").lower() == "true"

# Use Vertex AI if flag is set
if USE_VERTEX_AI:
    # For Vertex AI fine-tuned models, we'll initialize in code_generator.py
    # Keep a dummy client here for compatibility
    gemini_api = genai.Client(api_key=GEMINI_API_KEY)  # Fallback client
    # Cloud Storage will be imported when needed
    storage_bucket_name = f"{os.getenv('VERTEX_PROJECT_ID', '24816576653')}-screenwrite-uploads"
    print(f"🔥 Using Vertex AI Fine-tuned Model - Project: {os.getenv('VERTEX_PROJECT_ID', '24816576653')}, Location: {os.getenv('VERTEX_LOCATION', 'europe-west1')}")
else:
    # Use regular Gemini API
    gemini_api = genai.Client(api_key=GEMINI_API_KEY)
    storage_bucket_name = None
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


class CodeFixRequest(BaseModel):
    broken_code: str  # The code that failed to execute
    error_message: str  # The exact error from frontend
    error_stack: Optional[str] = None  # Full error stack if available
    media_library: Optional[List[Dict[str, Any]]] = []  # Available media files


class CodeFixResponse(BaseModel):
    corrected_code: str  # Fixed code
    explanation: str  # What was fixed
    duration: float  # Updated duration
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
    """Upload a file to Gemini Files API or Cloud Storage for later analysis."""
    
    try:
        print(f"📤 Gemini Upload: Uploading {file.filename} ({file.content_type})")
        
        # Read file content
        file_content = await file.read()
        
        if USE_VERTEX_AI:
            # Vertex AI: Upload to Cloud Storage
            try:
                # Import and initialize Cloud Storage client when needed
                from google.cloud import storage
                storage_client = storage.Client(project=os.getenv("VERTEX_PROJECT_ID"))
                
                # Create bucket if it doesn't exist
                bucket = storage_client.bucket(storage_bucket_name)
                try:
                    bucket.reload()
                except Exception:
                    # Bucket doesn't exist, create it
                    bucket = storage_client.create_bucket(storage_bucket_name, location=os.getenv("VERTEX_LOCATION", "europe-west1"))
                    print(f"📦 Created storage bucket: {storage_bucket_name}")
                
                # Generate unique filename
                file_id = str(uuid.uuid4())
                file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
                blob_name = f"uploads/{file_id}{file_extension}"
                
                # Upload to Cloud Storage
                blob = bucket.blob(blob_name)
                blob.upload_from_string(file_content, content_type=file.content_type)
                
                # Generate Cloud Storage URI
                gs_uri = f"gs://{storage_bucket_name}/{blob_name}"
                
                print(f"✅ Vertex AI Upload: Success - Cloud Storage URI: {gs_uri}")
                
                return GeminiUploadResponse(
                    success=True,
                    gemini_file_id=gs_uri,  # Return Cloud Storage URI instead of file ID
                    file_name=file.filename,
                    mime_type=file.content_type
                )
                
            except Exception as e:
                print(f"❌ Cloud Storage Upload Failed: {str(e)}")
                raise e
                
        else:
            # Standard Gemini API: Use Files API
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
                tmp_file.write(file_content)
                tmp_file.flush()
                
                # Upload to Gemini Files API
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
        elif "only supported in the Gemini Developer client" in error_msg:
            user_error = "File upload configuration error. Please contact support."
        else:
            user_error = "AI analysis service is temporarily unavailable. Please try again later."
        
        return GeminiUploadResponse(
            success=False,
            error_message=user_error
        )


@app.post("/ai/generate-composition")
async def generate_composition(request: CompositionRequest) -> CompositionResponse:
    """Generate a new Remotion composition using @ syntax for media file selection."""
    
    print(f"🎬 Main: Processing request: '{request.user_request}'")
    
    # Step 1: Enhanced Synth - Transform request with @ syntax-based media analysis
    enhanced_request = await synthesize_request(
        user_request=request.user_request,
        conversation_history=request.conversation_history,
        current_composition=request.current_generated_code,
        media_library=request.media_library,
        preview_settings=request.preview_settings,
        gemini_api=gemini_api,
        use_vertex_ai=USE_VERTEX_AI
    )
    
    print(f"🧠 Main: Enhanced Synth completed - Final request: '{enhanced_request[:150]}...'")
    
    # Step 2: Generate composition using enhanced request
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
        USE_VERTEX_AI
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


@app.post("/ai/fix-code")
async def fix_code(request: CodeFixRequest) -> CodeFixResponse:
    """Fix broken AI-generated code based on real runtime errors from the frontend."""
    
    print(f"🔧 Fix: Processing error correction")
    print(f"🔧 Fix: Error message: {request.error_message}")
    
    try:
        # System instruction for code fixing
        system_instruction = """You are a world-class Remotion developer and code fixing specialist. Your job is to fix broken React/TypeScript code that failed during execution.

⚠️ **CRITICAL**: Only fix the specific error - do not redesign, rewrite, or improve the code. Make the minimal possible change to resolve the error.


**CRITICAL: EXECUTION CONTEXT:**
- Code executes in React.createElement environment with Function() constructor
- Use React.createElement syntax, not JSX
- Use 'div' elements for text (no Text component in Remotion)

RESPONSE FORMAT - You must respond with EXACTLY this structure:
DURATION: [number in seconds based on composition content and timing]
CODE:
[raw JavaScript code using React.createElement - no markdown blocks, no import statements]

Fix ONLY the error and return the corrected code that will execute properly."""

        # User prompt with just the error and broken code
        user_prompt = f"""Fix this broken code:

ERROR MESSAGE:
{request.error_message}

BROKEN CODE:
{request.broken_code}

Fix the error and return the corrected code."""

        # Create thinking config for code fixes
        thinking_config = types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=2000  # Default thinking budget for fixes
        )

        # Use the same AI call pattern as other endpoints
        response = gemini_api.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,  # Low temperature for precise fixes
                max_output_tokens=4000,
                thinking_config=thinking_config
            ),
            contents=user_prompt
        )
        
        duration, corrected_code = code_generator.parse_ai_response(response.text)
        
        print(f"✅ Fix: Generated corrected code (duration: {duration}s)")
        
        return CodeFixResponse(
            corrected_code=corrected_code,
            explanation=f"Fixed error: {request.error_message[:100]}...",
            duration=duration,
            success=True
        )
        
    except Exception as e:
        print(f"❌ Fix: Error correction failed - {str(e)}")
        
        return CodeFixResponse(
            corrected_code=request.broken_code,  # Return original as fallback
            explanation=f"Error correction failed: {str(e)}",
            duration=10.0,
            success=False,
            error_message=str(e)
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
