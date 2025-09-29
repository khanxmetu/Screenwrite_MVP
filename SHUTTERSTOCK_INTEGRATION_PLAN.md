# Shutterstock Integration - Technical Implementation Plan

## Overview

Implementation of AI-driven automatic stock content acquisition with intelligent content comparison and user selection. Users request stock content, AI fetches multiple options, analyzes differences, and presents informed choices.

## Architecture Components

### 1. Enhanced Synth Response Pipeline

**Current Response Types:**
- `chat` - Conversational responses
- `edit` - Blueprint modifications  
- `probe` - Follow-up questions

**New Response Type:**
- `fetch` - Stock content acquisition with auto-analysis

### 2. Fetch Workflow Pipeline

```
User Request → Synth Classify → Fetch → Download → Preprocess → Auto-Probe → User Choice → Continue
```

**Detailed Flow:**
1. **Request Analysis**: Synth determines if user wants stock content
2. **Search & Download**: Fetch 2-3 best matching options from Shutterstock
3. **Video Preprocessing**: Apply existing re-encoding pipeline to downloaded videos
4. **Auto-Probe Generation**: AI analyzes differences and presents comparison
5. **User Selection**: User chooses preferred option based on AI analysis
6. **Integration**: Continue with selected content in composition

## Technical Implementation

### Phase 1: Core Infrastructure

#### 1.1 Shutterstock API Integration

**New Backend Module: `shutterstock_client.py`**
```python
class ShutterstockClient:
    def __init__(self, client_id: str, client_secret: str)
    def authenticate(self) -> str  # OAuth token
    def search_videos(query: str, per_page: int = 3) -> List[VideoResult]
    def search_images(query: str, per_page: int = 3) -> List[ImageResult]
    def download_asset(asset_id: str, license_type: str) -> DownloadResult
    def get_asset_metadata(asset_id: str) -> AssetMetadata
```

**API Endpoints Required:**
- `POST /api/v2/oauth/access_token` - Authentication
- `GET /api/v1/videos/search` - Video search
- `GET /api/v1/images/search` - Image search  
- `POST /api/v1/videos/licenses` - License video
- `POST /api/v1/images/licenses` - License image
- `GET /api/v1/videos/{id}/download` - Download video
- `GET /api/v1/images/{id}/download` - Download image

#### 1.2 Enhanced Synth Response Types

**File: `backend/schema.py`**
```python
class FetchResponse(BaseModel):
    response_type: Literal["fetch"]
    content_type: Literal["video", "image", "audio"]
    search_query: str
    auto_probe_question: str
    fetched_assets: List[FetchedAsset]

class FetchedAsset(BaseModel):
    asset_id: str
    title: str
    description: str
    url: str
    thumbnail_url: str
    metadata: Dict[str, Any]
    local_path: Optional[str] = None
    processed_path: Optional[str] = None
```

**File: `backend/main.py` - New Endpoint**
```python
@app.post("/fetch-stock-content")
async def fetch_stock_content(request: FetchRequest):
    # 1. Search Shutterstock
    # 2. Download assets
    # 3. Preprocess videos
    # 4. Generate auto-probe question
    # 5. Return FetchResponse
```

#### 1.3 Video Preprocessing Integration

**Extend existing `reencodeVideoForAccurateTrimming` function:**

**File: `app/videorender/videorender.ts`**
```typescript
// New endpoint for processing downloaded stock videos
app.post('/process-stock-video', upload.single('video'), async (req, res) => {
  // Apply same preprocessing pipeline as user uploads:
  // - Re-encode with I-frames every 30 frames
  // - H.264 + AAC codecs
  // - +faststart optimization
  // - Generate web-accessible URL
});
```

### Phase 2: Frontend Integration

#### 2.1 Fetch Response Handling

**File: `app/components/chat/ChatInterface.tsx`**
```typescript
interface FetchResponseProps {
  response: FetchResponse;
  onAssetSelect: (asset: FetchedAsset) => void;
  onCancel: () => void;
}

const FetchResponseComponent = ({ response, onAssetSelect, onCancel }) => {
  return (
    <div className="fetch-response">
      <div className="ai-analysis">
        <h3>AI Analysis</h3>
        <p>{response.auto_probe_question}</p>
      </div>
      
      <div className="asset-grid">
        {response.fetched_assets.map(asset => (
          <AssetPreviewCard 
            key={asset.asset_id}
            asset={asset}
            onSelect={() => onAssetSelect(asset)}
          />
        ))}
      </div>
      
      <div className="actions">
        <button onClick={onCancel}>Cancel</button>
        <button onClick={() => /* search different terms */}>Try Different Search</button>
      </div>
    </div>
  );
};
```

#### 2.2 Asset Preview Components

**File: `app/components/chat/AssetPreviewCard.tsx`**
```typescript
const AssetPreviewCard = ({ asset, onSelect }) => {
  return (
    <div className="asset-card" onClick={onSelect}>
      <div className="preview">
        {asset.content_type === 'video' ? (
          <video src={asset.url} muted loop autoPlay />
        ) : (
          <img src={asset.url} alt={asset.title} />
        )}
      </div>
      
      <div className="metadata">
        <h4>{asset.title}</h4>
        <p>{asset.description}</p>
        <div className="tags">
          {asset.metadata.keywords?.slice(0, 3).map(tag => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      </div>
    </div>
  );
};
```

### Phase 3: Auto-Probe Intelligence

#### 3.1 Content-Specific Analysis Questions

**File: `backend/auto_probe_generator.py`**
```python
class AutoProbeGenerator:
    @staticmethod
    def generate_comparison_question(content_type: str, assets: List[FetchedAsset]) -> str:
        if content_type == "video":
            return f"How do these {len(assets)} videos differ in style, pacing, visual quality, and mood? Which would work best for different types of projects?"
            
        elif content_type == "image":
            return f"How do these {len(assets)} images differ in composition, lighting, style, and emotional tone? What are the strengths of each for different use cases?"
            
        elif content_type == "audio":
            return f"How do these {len(assets)} audio tracks differ in genre, tempo, energy level, and production style? Which would suit different video moods?"
```

#### 3.2 Intelligent Asset Selection

**Context-Aware Analysis:**
- **Style Detection**: Modern vs vintage, professional vs casual
- **Technical Quality**: Resolution, frame rate, audio quality
- **Mood Analysis**: Energetic vs calm, bright vs moody
- **Use Case Matching**: Corporate, social media, cinematic, etc.

### Phase 4: Media Library Integration

#### 4.1 Seamless Asset Integration

**File: `app/hooks/useMediaBin.ts`**
```typescript
const useMediaBin = () => {
  const addStockAsset = async (asset: FetchedAsset) => {
    // 1. Add to media library with metadata
    // 2. Generate thumbnail if needed  
    // 3. Update media bin state
    // 4. Trigger re-render of media grid
    
    const mediaItem = {
      id: asset.asset_id,
      name: asset.title,
      mediaType: asset.content_type,
      mediaUrlLocal: asset.processed_path, // Preprocessed local URL
      mediaUrlRemote: asset.url,           // Original Shutterstock URL
      durationInSeconds: asset.metadata.duration,
      media_width: asset.metadata.width,
      media_height: asset.metadata.height,
      source: 'shutterstock',
      license_info: asset.metadata.license
    };
    
    setMediaLibrary(prev => [...prev, mediaItem]);
  };
};
```

## Required File Changes

### Backend Files

1. **`backend/requirements.txt`**
   - Add: `requests`, `python-dotenv`

2. **`backend/.env`** (new)
   ```
   SHUTTERSTOCK_CLIENT_ID=your_client_id
   SHUTTERSTOCK_CLIENT_SECRET=your_client_secret
   ```

3. **`backend/shutterstock_client.py`** (new)
   - Complete Shutterstock API client implementation

4. **`backend/schema.py`**
   - Add `FetchResponse`, `FetchedAsset` models
   - Extend `SynthResponse` union type

5. **`backend/main.py`**
   - Add `/fetch-stock-content` endpoint
   - Add stock content processing logic

6. **`backend/auto_probe_generator.py`** (new)
   - Content-specific analysis question generation

### Frontend Files

7. **`app/videorender/videorender.ts`**
   - Add `/process-stock-video` endpoint
   - Extend preprocessing pipeline for stock videos

8. **`app/components/chat/ChatInterface.tsx`**
   - Add fetch response handling
   - Integrate asset selection workflow

9. **`app/components/chat/FetchResponseComponent.tsx`** (new)
   - Complete fetch response UI implementation

10. **`app/components/chat/AssetPreviewCard.tsx`** (new)
    - Asset preview and selection UI

11. **`app/hooks/useMediaBin.ts`**
    - Add stock asset integration methods

12. **`app/utils/api.ts`**
    - Add fetch content API methods

## Video Preprocessing Requirements

### Critical Processing Pipeline

**All downloaded Shutterstock videos MUST be preprocessed using existing pipeline:**

1. **Re-encoding with I-frames every 30 frames**
   - Ensures accurate trimming in timeline
   - Uses `ffmpeg` with `-g 30 -keyint_min 30 -sc_threshold 0`

2. **Codec Standardization**
   - Video: H.264 (`libx264`)
   - Audio: AAC
   - Container: MP4

3. **Web Optimization**
   - Add `+faststart` for progressive download
   - Optimize file structure for streaming

**Implementation:**
- Extend existing `reencodeVideoForAccurateTrimming` function
- Apply to all downloaded stock videos before adding to media library
- Store both original and processed versions (processed for timeline use)

## Error Handling & Edge Cases

### 1. API Failures
- Shutterstock API rate limiting
- Authentication token expiration
- Network connectivity issues
- Invalid search queries

### 2. Download Failures
- Large file timeouts
- Insufficient disk space
- Corrupted downloads
- Unsupported formats

### 3. Preprocessing Failures
- FFmpeg errors
- Codec compatibility issues
- Audio track problems
- File permission issues

### 4. User Experience
- No search results found
- User cancels selection
- Duplicate asset downloads
- License quota exceeded

## Testing Strategy

### 1. Unit Tests
- Shutterstock API client methods
- Auto-probe question generation
- Asset metadata extraction
- Video preprocessing pipeline

### 2. Integration Tests  
- Complete fetch workflow
- Asset selection and integration
- Media library updates
- Error handling scenarios

### 3. User Acceptance Tests
- Search accuracy and relevance
- Asset preview functionality
- Selection and integration flow
- Performance with large assets

## Performance Considerations

### 1. Download Optimization
- Parallel asset downloads
- Progress indicators for large files
- Background processing
- Thumbnail generation

### 2. Storage Management
- Automatic cleanup of unused downloads
- Disk space monitoring
- Asset caching strategy
- Preprocessed file management

### 3. UI Responsiveness
- Lazy loading of previews
- Skeleton loading states
- Progressive enhancement
- Mobile-responsive design

## Security & Licensing

### 1. API Security
- Secure credential storage
- Token refresh handling
- Rate limit compliance
- HTTPS-only communication

### 2. License Compliance
- Track licensed asset usage
- Store license metadata
- Prevent unauthorized redistribution
- License quota monitoring

### 3. Data Privacy
- Secure temporary file handling
- User search history privacy
- Asset metadata scrubbing
- GDPR compliance considerations

## Future Enhancements

### 1. Advanced Search
- Natural language search queries
- Visual similarity search
- AI-powered content matching
- Search history and favorites

### 2. Batch Operations
- Multiple asset downloads
- Bulk preprocessing
- Collection-based organization
- Project-specific asset libraries

### 3. Integration Expansions  
- Additional stock providers (Getty, Adobe Stock)
- AI-generated content integration
- Custom asset libraries
- Collaborative sharing features

## Deployment Checklist

- [ ] Shutterstock API credentials configured
- [ ] FFmpeg installation verified
- [ ] Disk space allocation for downloads
- [ ] CORS configuration for asset serving
- [ ] Rate limiting implementation
- [ ] Error monitoring setup
- [ ] Performance metrics tracking
- [ ] User feedback collection system
