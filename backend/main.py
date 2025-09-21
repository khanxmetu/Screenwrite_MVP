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
    current_composition: Optional[List[Dict[str, Any]]] = None  # Current composition blueprint for incremental editing
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


class VideoAnalysisRequest(BaseModel):
    gemini_file_id: str
    question: str


class VideoAnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[str] = None
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
                
                # Wait for file to be ready for analysis (max 30 seconds)
                import time
                max_wait_time = 30
                wait_interval = 2
                elapsed_time = 0
                
                while elapsed_time < max_wait_time:
                    try:
                        file_status = gemini_api.files.get(name=uploaded_file.name)
                        if hasattr(file_status, 'state') and file_status.state == 'ACTIVE':
                            print(f"✅ File is ACTIVE and ready for analysis: {uploaded_file.name}")
                            break
                        else:
                            print(f"⏳ File not ready yet, state: {getattr(file_status, 'state', 'UNKNOWN')}, waiting...")
                            time.sleep(wait_interval)
                            elapsed_time += wait_interval
                    except Exception as e:
                        print(f"⚠️ Error checking file state: {e}, continuing...")
                        time.sleep(wait_interval)
                        elapsed_time += wait_interval
                
                if elapsed_time >= max_wait_time:
                    print(f"⚠️ File upload completed but may not be fully ready for analysis yet: {uploaded_file.name}")
            
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
    """Generate a new Remotion composition blueprint using AI."""
    
    print(f"🎬 Main: Processing request: '{request.user_request}'")
    print(f"📝 Main: Current composition has {len(request.current_composition or [])} tracks")
    
    # AI Blueprint Generation (NEW SYSTEM)
    print(f"🚀 AI: Generating CompositionBlueprint with updated system")
    
    # Convert to dict format expected by code generator
    request_dict = {
        "user_request": request.user_request,
        "preview_settings": request.preview_settings,
        "media_library": request.media_library,
        "current_composition": request.current_composition,
        "conversation_history": request.conversation_history
    }
    
    # Call the blueprint generation module (LLM-agnostic)
    result = await generate_composition_with_validation(request_dict)
    
    print(f"✅ Main: Blueprint generation completed - Success: {result['success']}")
    
    # Convert result back to the response model
    return CompositionResponse(
        composition_code=result["composition_code"],  # This is now CompositionBlueprint JSON
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


@app.post("/analyze-video")
async def analyze_video(request: VideoAnalysisRequest) -> VideoAnalysisResponse:
    """Analyze a video file using Gemini Files API reference."""
    
    try:
        print(f"🎬 Video Analysis: Analyzing file {request.gemini_file_id}")
        print(f"🔍 Question: {request.question}")
        
        if USE_VERTEX_AI:
            # For Vertex AI, the gemini_file_id is actually a Cloud Storage URI
            # Use a simpler approach - pass the file URI directly in contents
            response = gemini_api.models.generate_content(
                model="gemini-2.5-flash",
                contents=[request.gemini_file_id, request.question],
                config=types.GenerateContentConfig(temperature=0.1)
            )
        else:
            # For regular Gemini API, use the file reference directly
            # The gemini_file_id is the file URI from Files API (e.g., "files/abc123")
            # We need to get the file object from the file ID
            file_obj = gemini_api.files.get(name=request.gemini_file_id)
            
            # Check if file is ready for analysis
            if hasattr(file_obj, 'state') and file_obj.state != 'ACTIVE':
                raise Exception(f"Video file is not ready for analysis yet (state: {file_obj.state}). Please wait a moment and try again.")
            
            response = gemini_api.models.generate_content(
                model="gemini-2.5-flash", 
                contents=[file_obj, request.question],
                config=types.GenerateContentConfig(temperature=0.1)
            )
        
        analysis_result = response.text
        print(f"✅ Video Analysis: Success - {len(analysis_result)} characters")
        
        return VideoAnalysisResponse(
            success=True,
            analysis=analysis_result
        )
        
    except Exception as e:
        print(f"❌ Video Analysis: Failed - {str(e)}")
        
        # Provide user-friendly error messages
        error_msg = str(e)
        if "API key" in error_msg.lower():
            user_error = "AI service authentication failed. Please check server configuration."
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            user_error = "Network connection error. Please check your internet connection and try again."
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            user_error = "AI service quota exceeded. Please try again later."
        elif "not found" in error_msg.lower():
            user_error = "Video file not found. Please try uploading the video again."
        elif "failed_precondition" in error_msg.lower() or "not in an active state" in error_msg.lower():
            user_error = "Video is still being processed by the AI service. Please wait a moment and try again."
        elif "not ready for analysis yet" in error_msg.lower():
            user_error = "Video is still being processed. Please wait a moment and try again."
        else:
            user_error = f"Video analysis failed: {error_msg}"
        
        return VideoAnalysisResponse(
            success=False,
            error_message=user_error
        )


class ChatLogRequest(BaseModel):
    session_id: str
    log_entry: Dict[str, Any]

@app.post("/chat/log")
async def save_chat_log(request: ChatLogRequest):
    """Save chat workflow log entries to files"""
    try:
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)
        
        log_file = os.path.join(logs_dir, f"chat_workflow_{request.session_id}.json")
        
        # Read existing log or create new one
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = {
                "session_id": request.session_id,
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "entries": []
            }
        
        # Append new entry
        log_data["entries"].append(request.log_entry)
        log_data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        log_data["total_entries"] = len(log_data["entries"])
        
        # Save updated log
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return {"success": True, "log_file": log_file, "entry_count": len(log_data["entries"])}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save chat log: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
