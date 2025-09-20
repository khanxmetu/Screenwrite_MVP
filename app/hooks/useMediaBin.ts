import { useState, useCallback } from "react"
import axios from "axios"
import { type MediaBinItem } from "~/components/timeline/types"
import { generateUUID } from "~/utils/uuid"
import { apiUrl } from "~/utils/api"

// Delete media file from server
export const deleteMediaFile = async (filename: string): Promise<{ success: boolean; message?: string; error?: string }> => {
  try {
    const response = await fetch(apiUrl(`/media/${encodeURIComponent(filename)}`), {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to delete file');
    }

    return await response.json();
  } catch (error) {
    console.error('Delete API error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
};

// Clone/copy media file on server
export const cloneMediaFile = async (filename: string, originalName: string, suffix: string): Promise<{ success: boolean; filename?: string; originalName?: string; url?: string; fullUrl?: string; size?: number; error?: string }> => {
  try {
    const response = await fetch(apiUrl('/clone-media'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filename,
        originalName,
        suffix
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to clone file');
    }

    return await response.json();
  } catch (error) {
    console.error('Clone API error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
};


// Helper function to get media metadata
const getMediaMetadata = (file: File, mediaType: "video" | "image" | "audio"): Promise<{
  durationInSeconds?: number;
  width: number;
  height: number;
}> => {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);

    if (mediaType === "video") {
      const video = document.createElement("video");
      video.preload = "metadata";

      video.onloadedmetadata = () => {
        const width = video.videoWidth;
        const height = video.videoHeight;
        const durationInSeconds = video.duration;

        URL.revokeObjectURL(url);
        resolve({
          durationInSeconds: isFinite(durationInSeconds) ? durationInSeconds : undefined,
          width,
          height
        });
      };

      video.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error("Failed to load video metadata"));
      };

      video.src = url;
    } else if (mediaType === "image") {
      const img = new Image();

      img.onload = () => {
        const width = img.naturalWidth;
        const height = img.naturalHeight;

        URL.revokeObjectURL(url);
        resolve({
          durationInSeconds: undefined, // Images don't have duration
          width,
          height
        });
      };

      img.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error("Failed to load image metadata"));
      };

      img.src = url;
    } else if (mediaType === "audio") {
      const audio = document.createElement("audio");
      audio.preload = "metadata";

      audio.onloadedmetadata = () => {
        const durationInSeconds = audio.duration;

        URL.revokeObjectURL(url);
        resolve({
          durationInSeconds: isFinite(durationInSeconds) ? durationInSeconds : undefined,
          width: 0, // Audio files don't have visual dimensions
          height: 0
        });
      };

      audio.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error("Failed to load audio metadata"));
      };

      audio.src = url;
    }
  });
};

export const useMediaBin = (handleDeleteScrubbersByMediaBinId: (mediaBinId: string) => void) => {
  const [mediaBinItems, setMediaBinItems] = useState<MediaBinItem[]>([])
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    item: MediaBinItem;
  } | null>(null)

  const handleAddMediaToBin = useCallback(async (file: File) => {
    const id = generateUUID();
    const name = file.name;
    let mediaType: "video" | "image" | "audio";
    if (file.type.startsWith("video/")) mediaType = "video";
    else if (file.type.startsWith("image/")) mediaType = "image";
    else if (file.type.startsWith("audio/")) mediaType = "audio";
    else {
      alert("Unsupported file type. Please select a video or image.");
      return;
    }

    console.log("Adding to bin:", name, mediaType);

    try {
      const mediaUrlLocal = URL.createObjectURL(file);

      console.log(`Parsing ${mediaType} file for metadata...`);
      const metadata = await getMediaMetadata(file, mediaType);
      console.log("Media metadata:", metadata);

      // Add item to media bin immediately with upload progress tracking
      const newItem: MediaBinItem = {
        id,
        name,
        mediaType,
        mediaUrlLocal,
        mediaUrlRemote: null, // Will be set after successful upload
        durationInSeconds: metadata.durationInSeconds ?? 0,
        media_width: metadata.width,
        media_height: metadata.height,
        text: null,
        isUploading: true,
        uploadProgress: 0,
        left_transition_id: null,
        right_transition_id: null,
        gemini_file_id: null, // Will be set after Gemini upload
      };
      setMediaBinItems(prev => [...prev, newItem]);

      const formData = new FormData();
      formData.append('media', file);

      console.log("Uploading file to server...");
      const uploadResponse = await axios.post(apiUrl('/upload'), formData, {
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            console.log(`Upload progress: ${percentCompleted}%`);

            // Update upload progress in the media bin
            setMediaBinItems(prev =>
              prev.map(item =>
                item.id === id
                  ? { ...item, uploadProgress: percentCompleted }
                  : item
              )
            );
          }
        }
      });

      const uploadResult = uploadResponse.data;
      console.log("Upload successful:", uploadResult);

      // Upload to Gemini Files API for analysis (required for media analysis)
      console.log("Uploading to Gemini for analysis...");
      const geminiFormData = new FormData();
      geminiFormData.append('file', file);
      
      let geminiFileId: string;
      try {
        const geminiResponse = await axios.post(apiUrl('/upload-to-gemini', true), geminiFormData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        if (!geminiResponse.data.success) {
          throw new Error(`Server connection error: ${geminiResponse.data.error_message || 'Failed to connect to AI analysis service'}`);
        }
        
        geminiFileId = geminiResponse.data.gemini_file_id;
        console.log("Gemini upload successful:", geminiFileId);
      } catch (geminiError) {
        if (geminiError instanceof Error && geminiError.message.includes("Server connection error")) {
          throw geminiError; // Re-throw our custom error
        }
        // Handle axios/network errors
        if (axios.isAxiosError(geminiError)) {
          if (geminiError.code === 'ECONNREFUSED' || geminiError.message.includes('ECONNREFUSED')) {
            throw new Error('Server connection error: AI analysis service is not available. Please contact support.');
          } else if (geminiError.response?.status === 500) {
            throw new Error('Server connection error: AI analysis service encountered an internal error. Please try again later.');
          } else if (geminiError.response?.status === 404) {
            throw new Error('Server connection error: AI analysis service endpoint not found. Please contact support.');
          }
        }
        throw new Error(`Server connection error: Unable to connect to AI analysis service. Please try again later.`);
      }

      // Update item with successful upload result and remove progress tracking
      setMediaBinItems(prev =>
        prev.map(item =>
          item.id === id
            ? {
              ...item,
              mediaUrlRemote: apiUrl(uploadResult.url),
              isUploading: false,
              uploadProgress: null,
              gemini_file_id: geminiFileId
            }
            : item
        )
      );

    } catch (error) {
      console.error("Error adding media to bin:", error);
      
      // Provide user-friendly error messages
      let errorMessage: string;
      if (error instanceof Error) {
        if (error.message.includes("Server connection error")) {
          errorMessage = error.message; // Use the specific server error message
        } else if (error.message.includes("Network Error") || error.message.includes("ERR_NETWORK")) {
          errorMessage = "Network connection error. Please check your internet connection and try again.";
        } else if (error.message.includes("timeout")) {
          errorMessage = "Upload timeout. Please try again with a smaller file or check your connection.";
        } else {
          errorMessage = `Upload failed: ${error.message}`;
        }
      } else {
        errorMessage = "Upload failed due to an unknown error. Please try again.";
      }

      // Remove the failed item from media bin
      setMediaBinItems(prev => prev.filter(item => item.id !== id));

      throw new Error(errorMessage);
    }
  }, []);

  const handleAddTextToBin = useCallback((
    textContent: string,
    fontSize: number,
    fontFamily: string,
    color: string,
    textAlign: "left" | "center" | "right",
    fontWeight: "normal" | "bold"
  ) => {
    const newItem: MediaBinItem = {
      id: generateUUID(),
      name: textContent,
      mediaType: "text",
      media_width: 0,
      media_height: 0,
      text: {
        textContent,
        fontSize,
        fontFamily,
        color,
        textAlign,
        fontWeight,
      },
      mediaUrlLocal: null,
      mediaUrlRemote: null,
      durationInSeconds: 0,
      isUploading: false,
      uploadProgress: null,
      left_transition_id: null,
      right_transition_id: null,
      gemini_file_id: null, // Text items don't need Gemini upload
    };
    setMediaBinItems(prev => [...prev, newItem]);
  }, []);

  const handleDeleteMedia = useCallback(async (item: MediaBinItem) => {
    try {
      if (item.mediaType === "text") {
        setMediaBinItems(prev => prev.filter(binItem => binItem.id !== item.id));

        // Also remove any scrubbers from the timeline that use this media
        if (handleDeleteScrubbersByMediaBinId) {
          handleDeleteScrubbersByMediaBinId(item.id);
        }
        return;
      }

      // Extract filename from mediaUrlRemote URL
      if (!item.mediaUrlRemote) {
        console.error('No remote URL found for media item');
        return;
      }

      // Parse the URL and extract filename from the path
      const url = new URL(item.mediaUrlRemote);
      const pathSegments = url.pathname.split('/');
      const encodedFilename = pathSegments[pathSegments.length - 1]; // Get the last segment after /media/

      if (!encodedFilename) {
        console.error('Could not extract filename from URL:', item.mediaUrlRemote);
        return;
      }

      // Decode the filename
      const filename = decodeURIComponent(encodedFilename);
      console.log('Extracted filename:', filename);

      const result = await deleteMediaFile(filename);
      if (result.success) {
        console.log(`Media deleted: ${item.name}`);
        // Remove from media bin state
        setMediaBinItems(prev => prev.filter(binItem => binItem.id !== item.id));
        // Also remove any scrubbers from the timeline that use this media
        if (handleDeleteScrubbersByMediaBinId) {
          handleDeleteScrubbersByMediaBinId(item.id);
        }
      } else {
        console.error('Failed to delete media:', result.error);
      }
    } catch (error) {
      console.error('Error deleting media:', error);
    }
  }, [handleDeleteScrubbersByMediaBinId]);

  const handleSplitAudio = useCallback(async (videoItem: MediaBinItem) => {
    if (videoItem.mediaType !== 'video') {
      throw new Error('Can only split audio from video files');
    }

    try {
      // Extract filename from mediaUrlRemote URL
      if (!videoItem.mediaUrlRemote) {
        throw new Error('No remote URL found for video item');
      }

      // Parse the URL and extract filename from the path
      const url = new URL(videoItem.mediaUrlRemote);
      const pathSegments = url.pathname.split('/');
      const encodedFilename = pathSegments[pathSegments.length - 1];

      if (!encodedFilename) {
        throw new Error('Could not extract filename from URL');
      }

      // Clone the file on the server
      const cloneResult = await cloneMediaFile(encodedFilename, videoItem.name, '(Audio)');

      if (!cloneResult.success) {
        throw new Error(cloneResult.error || 'Failed to clone media file');
      }

      // Create a new audio media item with the cloned file info
      const audioItem: MediaBinItem = {
        id: generateUUID(),
        name: `${videoItem.name} (Audio)`,
        mediaType: "audio",
        mediaUrlLocal: videoItem.mediaUrlLocal, // Reuse the original video's blob URL
        mediaUrlRemote: apiUrl(cloneResult.url!), // Use the new cloned file URL
        durationInSeconds: videoItem.durationInSeconds,
        media_width: 0, // Audio doesn't have visual dimensions
        media_height: 0,
        text: null,
        isUploading: false,
        uploadProgress: null,
        left_transition_id: null,
        right_transition_id: null,
        gemini_file_id: null, // TODO: Audio could also be uploaded to Gemini for analysis
      };

      // Add the audio item to the media bin
      setMediaBinItems(prev => [...prev, audioItem]);
      setContextMenu(null); // Close context menu after action

      console.log(`Audio split successful: ${videoItem.name} -> ${audioItem.name}`);
    } catch (error) {
      console.error('Error splitting audio:', error);
      throw error;
    }
  }, []);

  // Handle right-click to show context menu
  const handleContextMenu = useCallback((e: React.MouseEvent, item: MediaBinItem) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      item,
    });
  }, []);

  // Handle context menu actions
  const handleDeleteFromContext = useCallback(async () => {
    if (!contextMenu) return;
    await handleDeleteMedia(contextMenu.item);
    setContextMenu(null);
  }, [contextMenu, handleDeleteMedia]);

  const handleSplitAudioFromContext = useCallback(async () => {
    if (!contextMenu) return;
    await handleSplitAudio(contextMenu.item);
  }, [contextMenu, handleSplitAudio]);

  // Close context menu when clicking outside
  const handleCloseContextMenu = useCallback(() => {
    setContextMenu(null);
  }, []);

  return {
    mediaBinItems,
    handleAddMediaToBin,
    handleAddTextToBin,
    handleDeleteMedia,
    handleSplitAudio,
    contextMenu,
    handleContextMenu,
    handleDeleteFromContext,
    handleSplitAudioFromContext,
    handleCloseContextMenu,
  }
} 