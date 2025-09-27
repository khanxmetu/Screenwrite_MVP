# Pexels Stock Video Fetch Implementation Plan

## 🎯 Overview
Add stock video fetching from Pexels with automatic quality evaluation and fallback to custom generation.

## � API Details (From Official Documentation)

### Video Search Endpoint
```
GET https://api.pexels.com/videos/search
```

**Headers**:
```
Authorization: YOUR_API_KEY
```

**Parameters**:
- `query` (string, required): Search query (e.g., "Ocean", "Tigers", "People")
- `orientation` (string, optional): "landscape", "portrait", or "square"  
- `size` (string, optional): "large" (4K), "medium" (Full HD), or "small" (HD)
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Results per page (default: 15, max: 80)
- `locale` (string, optional): Search locale

**Response Structure**:
```json
{
  "page": 1,
  "per_page": 15,
  "total_results": 20475,
  "url": "https://www.pexels.com/videos/",
  "videos": [
    {
      "id": 1448735,
      "width": 4096,
      "height": 2160,
      "url": "https://www.pexels.com/video/video-of-forest-1448735/",
      "image": "https://images.pexels.com/videos/1448735/free-video-1448735.jpg",
      "duration": 32,
      "user": {
        "id": 574687,
        "name": "Ruvim Miksanskiy",
        "url": "https://www.pexels.com/@digitech"
      },
      "video_files": [
        {
          "id": 58649,
          "quality": "sd", // or "hd" or "hls"
          "file_type": "video/mp4",
          "width": 640,
          "height": 338,
          "fps": 24.0,
          "link": "https://player.vimeo.com/external/291648067.sd.mp4?s=..."
        }
        // Multiple quality options available
      ],
      "video_pictures": [
        {
          "id": 133236,
          "picture": "https://static-videos.pexels.com/videos/1448735/pictures/preview-0.jpg",
          "nr": 0
        }
        // Multiple preview images
      ]
    }
  ]
}
```

**Rate Limits**:
- Free: 200 requests/hour, 20,000 requests/month
- Headers returned: `X-Ratelimit-Limit`, `X-Ratelimit-Remaining`, `X-Ratelimit-Reset`

## �📋 Phase 1: Backend Endpoint Foundation

### 1.1 Pexels API Setup
- [ ] Get Pexels API key from https://www.pexels.com/api/
- [ ] Add `PEXELS_API_KEY` to `.env` file
- [ ] Install requests library if not already available

### 1.2 Backend Endpoint Creation (`/fetch-stock-video`)
**File**: `backend/main.py`

**Request Schema**:
```python
class FetchStockVideoRequest(BaseModel):
    query: str = Field(description="Search query for stock video")
    per_page: Optional[int] = Field(description="Number of results", default=5)
    orientation: Optional[Literal["landscape", "portrait", "square"]] = Field(default="landscape")
    size: Optional[Literal["large", "medium", "small"]] = Field(default="medium")
```

**Response Schema**:
```python
class StockVideoResult(BaseModel):
    id: int
    pexels_url: str
    download_url: str
    preview_image: str
    duration: int
    width: int 
    height: int
    file_type: str
    quality: str
    photographer: str
    photographer_url: str

class FetchStockVideoResponse(BaseModel):
    success: bool
    query: str
    results: List[StockVideoResult]
    total_results: int
    auto_evaluation: Dict[str, Any]
    recommendation: Literal["proceed", "fallback"]
    selected_video: Optional[StockVideoResult] = None
    error_message: Optional[str] = None
```

### 1.3 Pexels API Integration
**Core Functions**:
```python
async def search_pexels_videos(query: str, per_page: int = 5, orientation: str = "landscape", size: str = "medium"):
    """Search Pexels for videos using their API"""
    headers = {"Authorization": os.getenv("PEXELS_API_KEY")}
    params = {
        "query": query,
        "per_page": per_page,
        "orientation": orientation,
        "size": size
    }
    
    response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
    return response.json()

def select_best_video_file(video_files: List[Dict]) -> Dict:
    """Select the best quality video file from available options"""
    # Priority: HD mp4 > SD mp4 > others
    hd_mp4 = [f for f in video_files if f["quality"] == "hd" and f["file_type"] == "video/mp4"]
    if hd_mp4:
        # Prefer 1920x1080 or 1280x720
        preferred = [f for f in hd_mp4 if f["width"] in [1920, 1280]]
        return preferred[0] if preferred else hd_mp4[0]
    
    sd_mp4 = [f for f in video_files if f["quality"] == "sd" and f["file_type"] == "video/mp4"]
    return sd_mp4[0] if sd_mp4 else video_files[0]

def evaluate_stock_results(results: List[Dict], query: str) -> Dict:
    """Evaluate quality of stock video search results"""
    if not results:
        return {
            "score": 0,
            "reason": "No results found",
            "recommendation": "fallback"
        }
    
    top_video = results[0]
    score = 0
    reasons = []
    
    # Duration check (25 points)
    if top_video["duration"] >= 5:
        score += 25
        reasons.append("Good duration")
    elif top_video["duration"] >= 3:
        score += 15
        reasons.append("Acceptable duration")
    else:
        reasons.append("Too short")
    
    # Resolution check (35 points)
    if top_video["width"] >= 1920 and top_video["height"] >= 1080:
        score += 35
        reasons.append("Full HD quality")
    elif top_video["width"] >= 1280 and top_video["height"] >= 720:
        score += 25
        reasons.append("HD quality")
    else:
        score += 10
        reasons.append("Lower quality")
        
    # Video files availability (20 points)
    best_file = select_best_video_file(top_video["video_files"])
    if best_file["file_type"] == "video/mp4":
        score += 20
        reasons.append("MP4 format available")
    
    # Basic keyword relevance (20 points) 
    query_words = set(query.lower().split())
    # This is basic - could be enhanced with AI relevance scoring
    score += 20  # Assume decent relevance since Pexels search is good
    
    return {
        "score": score,
        "max_score": 100,
        "reasons": reasons,
        "recommendation": "proceed" if score >= 60 else "fallback"
    }

async def download_video_file(video_url: str, filename: str) -> str:
    """Download video file from Pexels/Vimeo URL"""
    response = requests.get(video_url, stream=True)
    response.raise_for_status()
    
    filepath = os.path.join("out", filename)
    os.makedirs("out", exist_ok=True)
    
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return filepath
```

## 📋 Phase 2: Frontend Integration

### 2.1 ConversationalSynth Updates
**File**: `app/components/chat/ConversationalSynth.ts`

**Add new content_type**:
```typescript
enum ContentType {
  IMAGE_GENERATION = "image",
  VIDEO_GENERATION = "video", 
  STOCK_VIDEO_FETCH = "stock_video"  // NEW
}
```

**Detection Logic**:
```typescript
// Keywords that indicate stock search vs generation
const STOCK_FETCH_KEYWORDS = [
  "find", "search", "get", "fetch", "look for", 
  "stock video", "stock footage", "existing video"
];

const GENERATION_KEYWORDS = [
  "create", "generate", "make", "produce", "build"
];
```

### 2.2 ChatBox Integration
**File**: `app/components/chat/ChatBox.tsx`

**New handler**: `handleStockVideoFetch()`
```typescript
const handleStockVideoFetch = async (query: string): Promise<Message[]> => {
  // 1. Call /fetch-stock-video endpoint
  // 2. Check auto_evaluation.recommendation
  // 3a. If "proceed" → Download best result → Add to media bin → type: "chat"
  // 3b. If "fallback" → Return sleep message asking about custom generation
}
```

## 📋 Phase 3: Workflow Implementation

### 3.1 Success Path (Auto-Continue)
1. User: "Find me a video of ocean waves"
2. AI detects: `content_type: "stock_video"`
3. Backend searches Pexels → finds good results
4. Auto-evaluation: `recommendation: "proceed"`
5. Download best video → Add to media bin
6. Response: `type: "chat"` with success message

### 3.2 Fallback Path (User Decision)
1. User: "Find me a video of purple unicorns dancing"
2. Backend searches Pexels → poor/no results
3. Auto-evaluation: `recommendation: "fallback"`
4. Response: `type: "sleep"` with message: "No suitable stock found. Generate custom video instead?"
5. User can approve → triggers video generation workflow

## 📋 Phase 4: Media Integration

### 4.1 Stock Video MediaBinItem
```typescript
const stockVideoItem: MediaBinItem = {
  id: generateUUID(),
  name: `Stock: ${searchQuery}`,
  mediaType: "video",
  mediaUrlLocal: null,
  mediaUrlRemote: downloadedVideoUrl,
  media_width: result.width,
  media_height: result.height, 
  durationInSeconds: result.duration,
  // ... other standard fields
  // Pexels attribution data:
  photographer: result.photographer,
  photographer_url: result.photographer_url,
  source: "pexels"
}
```

### 4.2 Attribution Handling
- Store photographer info in MediaBinItem
- Display attribution in media bin UI
- Include in exported projects per Pexels requirements

## 🔧 Testing Strategy

### Backend Testing
```bash
# Test endpoint directly
curl -X POST "http://localhost:8001/fetch-stock-video" \
  -H "Content-Type: application/json" \
  -d '{"query": "ocean waves", "per_page": 3}'
```

### Integration Testing
1. Test with queries that should have good results
2. Test with queries that should trigger fallback
3. Test error handling (API down, no API key, etc.)
4. Test video download and file serving

## 📚 API Documentation References
- Pexels API: https://www.pexels.com/api/documentation/
- Videos endpoint: `GET https://api.pexels.com/videos/search`
- Rate limits: 200 requests/hour for free tier
- Attribution requirements: https://www.pexels.com/license/

## 🚀 Implementation Order
1. **Phase 1.1-1.2**: Create backend endpoint skeleton
2. **Phase 1.3**: Integrate Pexels API 
3. **Test**: Verify endpoint works with curl
4. **Phase 1.4**: Add auto-evaluation logic
5. **Test**: Verify evaluation works for different queries
6. **Phase 2**: Frontend integration
7. **Phase 3**: Full workflow testing
8. **Phase 4**: Polish and attribution

## 💡 Future Enhancements
- Support for Pexels photo search
- Multiple stock providers (Unsplash, Pixabay)
- User preference for stock vs generation
- Batch download of multiple videos
- Advanced relevance scoring with AI
