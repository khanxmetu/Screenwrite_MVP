import os
import subprocess
import tempfile
import json
import time
import re
import shutil
import uuid
import requests
import asyncio
import httpx
from PIL import Image
from io import BytesIO

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Import code generation functionality
from code_generator import generate_composition_with_validation
import code_generator  # Keep for other functions like parse_ai_response

from schema import (
    TextProperties, BaseScrubber, 
    GenerateContentRequest, GenerateContentResponse, GeneratedAsset,
    CheckGenerationStatusRequest, CheckGenerationStatusResponse,
    FetchStockVideoRequest, FetchStockVideoResponse, StockVideoResult
)
from providers import ContentGenerationProvider

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

# Ensure output directory exists before mounting static files
os.makedirs("out", exist_ok=True)

# Mount static file serving for generated media
app.mount("/media", StaticFiles(directory="out"), name="media")


# Pexels API Helper Functions
async def search_pexels_videos(query: str):
    """Search Pexels for landscape videos using their API"""
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Pexels API key not configured")
    
    # Remove quotes if present (from .env file)
    api_key = api_key.strip('"\'')
    
    headers = {"Authorization": api_key}  # Pexels expects just the API key, not "Bearer"
    params = {
        "query": query,
        "per_page": 3,  # Get top 3 results
        "orientation": "landscape"  # Enforce landscape only
    }
    
    try:
        print(f"🔍 Pexels API call: {query} (key: {api_key[:8]}...)")
        response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=30)
        print(f"📡 Response status: {response.status_code}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Pexels API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pexels API request failed: {str(e)}")


def select_best_video_file(video_files: List[Dict]) -> Dict:
    """Select the best quality video file from available options"""
    if not video_files:
        return None
    
    # Priority: HD mp4 > SD mp4 > others
    hd_mp4 = [f for f in video_files if f.get("quality") == "hd" and f.get("file_type") == "video/mp4"]
    if hd_mp4:
        # Prefer standard resolutions (1920x1080, 1280x720)
        preferred = [f for f in hd_mp4 if f.get("width") in [1920, 1280]]
        return preferred[0] if preferred else hd_mp4[0]
    
    # Fallback to SD mp4
    sd_mp4 = [f for f in video_files if f.get("quality") == "sd" and f.get("file_type") == "video/mp4"]
    return sd_mp4[0] if sd_mp4 else video_files[0]


def select_lowest_quality_video_file(video_files: List[Dict]) -> Dict:
    """Select the lowest quality video file for fast Gemini uploads"""
    if not video_files:
        return None
    
    # Priority for Gemini: Smallest file size (lowest quality, smallest resolution)
    mp4_files = [f for f in video_files if f.get("file_type") == "video/mp4"]
    if not mp4_files:
        return video_files[0] if video_files else None
    
    # Sort by quality (sd before hd) and resolution (smaller first)
    def quality_score(file):
        # Lower score = prefer for Gemini upload
        quality = file.get("quality", "sd")
        width = file.get("width", 0)
        
        quality_score = 0 if quality == "sd" else 1  # Prefer SD over HD
        resolution_score = width / 1000  # Lower resolution preferred
        
        return quality_score + resolution_score
    
    # Return the file with the lowest quality score
    return min(mp4_files, key=quality_score)


async def upload_url_to_gemini_directly(url: str, filename: str, client: httpx.AsyncClient = None) -> str:
    """
    Stream video directly from Pexels URL to Gemini without local storage.
    Optimized for fast Gemini uploads using lowest quality files.
    Returns gemini_file_id
    """
    try:
        print(f"📤 Direct streaming to Gemini: {url}")
        
        if client:
            # Use shared client for connection reuse
            async with client.stream('GET', url, follow_redirects=True) as response:
                response.raise_for_status()
                
                # Stream directly to memory for Gemini upload
                gemini_buffer = BytesIO()
                
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    gemini_buffer.write(chunk)
                
                # Upload to Gemini from memory buffer
                gemini_buffer.seek(0)
                gemini_file_id = await upload_file_content_to_gemini(gemini_buffer.getvalue(), filename)
                
                print(f"✅ Direct Gemini upload completed: {filename} -> {gemini_file_id}")
                return gemini_file_id
        else:
            # Fallback to individual client
            timeout = httpx.Timeout(60.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream('GET', url, follow_redirects=True) as response:
                    response.raise_for_status()
                    
                    # Stream directly to memory for Gemini upload
                    gemini_buffer = BytesIO()
                    
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        gemini_buffer.write(chunk)
                    
                    # Upload to Gemini from memory buffer
                    gemini_buffer.seek(0)
                    gemini_file_id = await upload_file_content_to_gemini(gemini_buffer.getvalue(), filename)
                    
                    print(f"✅ Direct Gemini upload completed: {filename} -> {gemini_file_id}")
                    return gemini_file_id
                
    except Exception as e:
        print(f"❌ Direct Gemini upload failed for {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload directly to Gemini: {str(e)}")


async def download_video_file(url: str, filename: str, client: httpx.AsyncClient = None) -> str:
    """Download video file from Pexels/Vimeo URL"""
    try:
        filepath = os.path.join("out", filename)
        os.makedirs("out", exist_ok=True)
        
        if client:
            # Use shared client for connection reuse
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
        else:
            # Fallback to individual client  
            timeout = httpx.Timeout(60.0)  # 60 second timeout for large files
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
        
        return filepath
    except Exception as e:
        print(f"❌ Download failed for {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download video: {str(e)}")


async def download_and_upload_to_gemini_simultaneously(url: str, filename: str) -> tuple[str, str]:
    """
    Download video from URL and upload to Gemini simultaneously for optimal performance.
    Returns (local_filepath, gemini_file_id)
    """
    try:
        filepath = os.path.join("out", filename)
        os.makedirs("out", exist_ok=True)
        
        print(f"📥 Downloading and uploading to Gemini: {url}")
        
        timeout = httpx.Timeout(60.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream('GET', url, follow_redirects=True) as response:
                response.raise_for_status()
                
                # Prepare both destinations
                local_file = open(filepath, 'wb')
                gemini_buffer = BytesIO()
                
                # Stream to both local disk and memory simultaneously
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    local_file.write(chunk)      # → Local disk
                    gemini_buffer.write(chunk)   # → Memory for Gemini
                
                local_file.close()
                
                # Upload to Gemini from memory buffer
                gemini_buffer.seek(0)
                gemini_file_id = await upload_file_content_to_gemini(gemini_buffer.getvalue(), filename)
                
                print(f"✅ Download and Gemini upload completed: {filename} -> {gemini_file_id}")
                return filepath, gemini_file_id
                
    except Exception as e:
        print(f"❌ Download/upload failed for {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download/upload video: {str(e)}")


async def upload_file_content_to_gemini(file_content: bytes, filename: str) -> str:
    """Upload file content to Gemini Files API and return file ID"""
    try:
        if USE_VERTEX_AI:
            # Vertex AI: Upload to Cloud Storage
            from google.cloud import storage
            storage_client = storage.Client(project=os.getenv("VERTEX_PROJECT_ID"))
            
            bucket = storage_client.bucket(storage_bucket_name)
            try:
                bucket.reload()
            except Exception:
                bucket = storage_client.create_bucket(storage_bucket_name, location=os.getenv("VERTEX_LOCATION", "europe-west1"))
                
            # Generate unique blob name
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(filename)[1] if filename else ""
            blob_name = f"stock_videos/{file_id}{file_extension}"
            
            # Upload to Cloud Storage
            blob = bucket.blob(blob_name)
            blob.upload_from_string(file_content, content_type="video/mp4")
            
            gs_uri = f"gs://{storage_bucket_name}/{blob_name}"
            return gs_uri
            
        else:
            # Standard Gemini API: Use Files API
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp_file:
                tmp_file.write(file_content)
                tmp_file.flush()
                
                # Upload to Gemini Files API
                uploaded_file = gemini_api.files.upload(file=tmp_file.name)
                
                # Clean up temporary file
                os.unlink(tmp_file.name)
                
                # Wait for file to be ready
                import time
                max_wait_time = 30
                wait_interval = 2
                elapsed_time = 0
                
                while elapsed_time < max_wait_time:
                    try:
                        file_status = gemini_api.files.get(name=uploaded_file.name)
                        if hasattr(file_status, 'state') and file_status.state == 'ACTIVE':
                            break
                        else:
                            time.sleep(wait_interval)
                            elapsed_time += wait_interval
                    except Exception as e:
                        time.sleep(wait_interval)
                        elapsed_time += wait_interval
                
                return uploaded_file.name
                
    except Exception as e:
        print(f"❌ Gemini upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload to Gemini: {str(e)}")


async def upload_file_content_to_gemini(file_content: bytes, filename: str) -> str:
    """Upload file content to Gemini Files API and return file ID"""
    try:
        if USE_VERTEX_AI:
            # Vertex AI: Upload to Cloud Storage
            from google.cloud import storage
            storage_client = storage.Client(project=os.getenv("VERTEX_PROJECT_ID"))
            
            bucket = storage_client.bucket(storage_bucket_name)
            try:
                bucket.reload()
            except Exception:
                bucket = storage_client.create_bucket(storage_bucket_name, location=os.getenv("VERTEX_LOCATION", "europe-west1"))
                
            # Generate unique blob name
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(filename)[1] if filename else ""
            blob_name = f"stock_videos/{file_id}{file_extension}"
            
            # Upload to Cloud Storage
            blob = bucket.blob(blob_name)
            blob.upload_from_string(file_content, content_type="video/mp4")
            
            gs_uri = f"gs://{storage_bucket_name}/{blob_name}"
            return gs_uri
            
        else:
            # Standard Gemini API: Use Files API
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp_file:
                tmp_file.write(file_content)
                tmp_file.flush()
                
                # Upload to Gemini Files API
                uploaded_file = gemini_api.files.upload(file=tmp_file.name)
                
                # Clean up temporary file
                os.unlink(tmp_file.name)
                
                # Wait for file to be ready
                import time
                max_wait_time = 30
                wait_interval = 2
                elapsed_time = 0
                
                while elapsed_time < max_wait_time:
                    try:
                        file_status = gemini_api.files.get(name=uploaded_file.name)
                        if hasattr(file_status, 'state') and file_status.state == 'ACTIVE':
                            break
                        else:
                            time.sleep(wait_interval)
                            elapsed_time += wait_interval
                    except Exception as e:
                        time.sleep(wait_interval)
                        elapsed_time += wait_interval
                
                return uploaded_file.name
                
    except Exception as e:
        print(f"❌ Gemini upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload to Gemini: {str(e)}")


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


# Initialize content generation provider
content_generator = ContentGenerationProvider()

# Store active generation operations
active_operations = {}


@app.post("/generate-content", response_model=GenerateContentResponse)
async def generate_content(request: GenerateContentRequest):
    """Generate video or image content using Gemini AI"""
    try:
        print(f"🎨 Generating {request.content_type} with prompt: '{request.prompt[:100]}...'")
        
        if request.content_type == "video":
            # Handle reference image if provided
            reference_image = None
            if request.reference_image:
                try:
                    # Decode base64 image
                    import base64
                    image_data = base64.b64decode(request.reference_image)
                    reference_image = Image.open(BytesIO(image_data))
                except Exception as e:
                    print(f"⚠️ Failed to process reference image: {e}")
            
            # Start video generation (async)
            operation = await content_generator.generate_video(
                prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                aspect_ratio=request.aspect_ratio,
                resolution=request.resolution,
                reference_image=reference_image
            )
            
            # Poll internally until video generation is complete
            import time
            print("Video generation started, polling for completion...")
            while not operation.done:
                print("⏳ Video still generating, waiting 5 seconds...")
                time.sleep(5)
                operation = await content_generator.check_video_status(operation)
            
            print("Video generation completed!")
            
            # Process completed video (same logic as check_generation_status)
            try:
                # Download the generated video
                generated_video = operation.response.generated_videos[0]
                
                # Create unique filename
                asset_id = str(uuid.uuid4())
                file_name = f"generated_video_{asset_id}.mp4"
                file_path = os.path.join("out", file_name)
                
                # Ensure output directory exists
                os.makedirs("out", exist_ok=True)
                
                # Download the generated video.
                content_generator.api_client.files.download(file=generated_video.video)
                generated_video.video.save(file_path)
                
                # Get file size (video dimensions would need separate analysis)
                file_size = os.path.getsize(file_path)
                
                # Create asset response
                generated_asset = GeneratedAsset(
                    asset_id=asset_id,
                    content_type="video",
                    file_path=file_path,
                    file_url=f"/media/{file_name}",
                    prompt=request.prompt,
                    duration_seconds=8.0,  # Veo generates 8-second videos
                    width=1280 if request.resolution == "720p" else 1920,
                    height=720 if request.resolution == "720p" else 1080,
                    file_size=file_size
                )
                
                return GenerateContentResponse(
                    success=True,
                    generated_asset=generated_asset,
                    status="completed"
                )
                
            except Exception as e:
                print(f"❌ Failed to download generated video: {e}")
                return GenerateContentResponse(
                    success=False,
                    status="failed",
                    error_message=f"Failed to download video: {str(e)}"
                )
            
        elif request.content_type == "image":
            # Handle reference images if provided
            reference_images = []
            if request.reference_image:
                try:
                    import base64
                    image_data = base64.b64decode(request.reference_image)
                    reference_image = Image.open(BytesIO(image_data))
                    reference_images.append(reference_image)
                except Exception as e:
                    print(f"⚠️ Failed to process reference image: {e}")
            
            # Generate image (synchronous)
            response = await content_generator.generate_image(
                prompt=request.prompt,
                reference_images=reference_images
            )
            
            # Save generated image
            asset_id = str(uuid.uuid4())
            file_name = f"generated_image_{asset_id}.png"
            file_path = os.path.join("out", file_name)
            
            # Ensure output directory exists
            os.makedirs("out", exist_ok=True)
            
            # Extract and save image from Imagen response
            if response.generated_images and len(response.generated_images) > 0:
                print(f"🎯 Found {len(response.generated_images)} generated images")
                generated_image = response.generated_images[0]
                
                # Get the PIL Image object from the Google GenAI Image object
                pil_image = generated_image.image._pil_image
                print(f"📸 PIL image size: {pil_image.size}")
                
                # Save the PIL Image object to file
                print(f"💾 Saving to: {file_path}")
                pil_image.save(file_path)
                print(f"✅ File saved successfully")
                
                # Get dimensions from the image
                width, height = pil_image.size
                file_size = os.path.getsize(file_path)
                print(f"📏 Image dimensions: {width}x{height}, file size: {file_size} bytes")
                
                # Create asset response
                generated_asset = GeneratedAsset(
                    asset_id=asset_id,
                    content_type="image",
                    file_path=file_path,
                    file_url=f"/media/{file_name}",
                    prompt=request.prompt,
                    width=width,
                    height=height,
                    file_size=file_size
                )
                
                return GenerateContentResponse(
                    success=True,
                    generated_asset=generated_asset,
                    status="completed"
                )
            
            raise HTTPException(status_code=500, detail="No image generated in response")
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported content type: {request.content_type}")
            
    except Exception as e:
        print(f"❌ Content generation failed: {str(e)}")
        return GenerateContentResponse(
            success=False,
            status="failed",
            error_message=str(e)
        )


@app.post("/check-generation-status", response_model=CheckGenerationStatusResponse)
async def check_generation_status(request: CheckGenerationStatusRequest):
    """Check status of video generation operation"""
    try:
        operation_id = request.operation_id
        
        if operation_id not in active_operations:
            raise HTTPException(status_code=404, detail="Operation not found")
        
        operation_data = active_operations[operation_id]
        operation = operation_data['operation']
        stored_prompt = operation_data['prompt']
        stored_resolution = operation_data['resolution']
        
        # Check current status
        updated_operation = await content_generator.check_video_status(operation)
        
        if updated_operation.done:
            # Generation completed
            try:
                # Download the generated video
                generated_video = updated_operation.response.generated_videos[0]
                
                # Create unique filename
                asset_id = str(uuid.uuid4())
                file_name = f"generated_video_{asset_id}.mp4"
                file_path = os.path.join("out", file_name)
                
                # Ensure output directory exists
                os.makedirs("out", exist_ok=True)
                
                # Download the generated video.
                content_generator.api_client.files.download(file=generated_video.video)
                generated_video.video.save(file_path)
                
                # Get file size (video dimensions would need separate analysis)
                file_size = os.path.getsize(file_path)
                
                # Create asset response
                generated_asset = GeneratedAsset(
                    asset_id=asset_id,
                    content_type="video",
                    file_path=file_path,
                    file_url=f"/media/{file_name}",
                    prompt=stored_prompt,  # Use stored prompt
                    duration_seconds=8.0,  # Veo generates 8-second videos
                    width=1280 if stored_resolution == "720p" else 1920,  # Use stored resolution
                    height=720 if stored_resolution == "720p" else 1080,
                    file_size=file_size
                )
                
                # Clean up operation
                del active_operations[operation_id]
                
                return CheckGenerationStatusResponse(
                    success=True,
                    status="completed",
                    generated_asset=generated_asset
                )
                
            except Exception as e:
                print(f"❌ Failed to download generated video: {e}")
                del active_operations[operation_id]
                return CheckGenerationStatusResponse(
                    success=False,
                    status="failed",
                    error_message=f"Failed to download video: {str(e)}"
                )
        else:
            # Still processing
            return CheckGenerationStatusResponse(
                success=True,
                status="processing"
            )
            
    except Exception as e:
        print(f"❌ Status check failed: {str(e)}")
        return CheckGenerationStatusResponse(
            success=False,
            status="failed", 
            error_message=str(e)
        )


@app.post("/fetch-stock-video", response_model=FetchStockVideoResponse)
async def fetch_stock_video(request: FetchStockVideoRequest):
    """
    Optimized dual-quality stock video fetch endpoint with shared HTTP client:
    1. Search Pexels for top 3 landscape videos
    2. Download HIGH quality for frontend timeline use
    3. Stream LOW quality directly to Gemini for fast AI analysis
    4. Use single HTTP client for all operations (connection reuse)
    5. Return videos with both local URLs and gemini_file_id ready for analysis
    """
    print(f"Fetching stock videos for query: {request.query}")
    
    try:
        # Step 1: Search Pexels for landscape videos
        search_results = await search_pexels_videos(request.query)
        videos_data = search_results.get("videos", [])
        
        if not videos_data:
            raise HTTPException(status_code=404, detail="No videos found for query")
        
        print(f"Found {len(videos_data)} videos from Pexels")
        
        # Step 2: Create shared HTTP client for all operations
        timeout = httpx.Timeout(60.0)
        async with httpx.AsyncClient(timeout=timeout) as shared_client:
            
            # Step 3: Process all 3 videos in parallel with shared client
            async def process_video(video, index):
                """Process a single video with dual quality: HD for frontend, low quality for Gemini"""
                video_files = video.get("video_files", [])
                
                # Select HIGH quality for frontend/local download
                best_file = select_best_video_file(video_files)
                # Select LOW quality for fast Gemini upload
                gemini_file = select_lowest_quality_video_file(video_files)
                
                if not best_file or not gemini_file:
                    raise Exception("No suitable video files found")
                
                # Generate filename
                asset_id = str(uuid.uuid4())
                file_name = f"stock_video_{asset_id}.mp4"
                gemini_file_name = f"gemini_{file_name}"
                
                print(f"📥 Processing video {index+1}/3:")
                print(f"  Frontend: {best_file['quality']} {best_file.get('width')}x{best_file.get('height')} - {best_file['link']}")
                print(f"  Gemini: {gemini_file['quality']} {gemini_file.get('width')}x{gemini_file.get('height')} - {gemini_file['link']}")
                
                # Run both downloads in parallel using shared client
                download_task = asyncio.create_task(
                    download_video_file(best_file["link"], file_name, client=shared_client)
                )
                gemini_task = asyncio.create_task(
                    upload_url_to_gemini_directly(gemini_file["link"], gemini_file_name, client=shared_client)
                )
                
                # Wait for both to complete
                filepath, gemini_file_id = await asyncio.gather(download_task, gemini_task)
                
                # Create stock result with both local URL and Gemini file ID
                stock_result = StockVideoResult(
                    id=video["id"],
                    pexels_url=video.get("url", ""),
                    download_url=f"/media/{file_name}",
                    preview_image=video.get("image", ""),
                    duration=video.get("duration", 0),
                    width=best_file.get("width", video.get("width", 0)),  # Use best file dimensions
                    height=best_file.get("height", video.get("height", 0)),
                    file_type=best_file.get("file_type", "video/mp4"),
                    quality=best_file.get("quality", "sd"),  # Use best file quality
                    photographer=video.get("user", {}).get("name", "Unknown"),
                    photographer_url=video.get("user", {}).get("url", ""),
                    gemini_file_id=gemini_file_id  # ✅ Fast low-quality upload!
                )
                
                print(f"✅ Completed video {index+1}/3: {file_name} (Frontend: {best_file['quality']}) + Gemini: {gemini_file_id}")
                return stock_result
            
            # Process all 3 videos in parallel with shared client
            tasks = [
                asyncio.create_task(process_video(video, i)) 
                for i, video in enumerate(videos_data[:3])
            ]
            
            # Wait for all videos to complete (with error handling)
            stock_results = []
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(completed_results):
                if isinstance(result, Exception):
                    print(f"❌ Failed to process video {i+1}/3: {result}")
                    continue  # Skip failed videos, don't add to results
                else:
                    stock_results.append(result)
            
            if not stock_results:
                raise HTTPException(status_code=500, detail="Failed to process any videos")
            
            print(f"🎉 Successfully processed {len(stock_results)}/{len(videos_data[:3])} videos with shared HTTP client")
            
            return FetchStockVideoResponse(
                success=True,
                query=request.query,
                videos=stock_results,
                total_results=len(videos_data)
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Stock video fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock videos: {str(e)}")


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

    # Run with extended timeout to handle long video generation (up to 10 minutes)
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8001,
        timeout_keep_alive=600,  # 10 minutes for long video generation
        timeout_graceful_shutdown=30
    )
