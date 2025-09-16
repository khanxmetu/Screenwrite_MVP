// Simple types for the application

export interface MediaBinItem {
  id: string;
  name: string;
  type: 'image' | 'video' | 'audio' | 'text';
  mediaType: 'image' | 'video' | 'audio' | 'text';
  src?: string;
  durationInSeconds?: number;
  isUploading?: boolean;
  uploadProgress?: number | null;
  mediaUrlLocal?: string;
  mediaUrlRemote?: string;
  gemini_file_id?: string;
  // Additional properties from old timeline types
  media_width?: number;
  media_height?: number;
  text?: string;
  left_transition_id?: string;
  right_transition_id?: string;
}

// Timeline related types
export const FPS = 60;
export const PIXELS_PER_SECOND = 100;

// Legacy timeline types (will be replaced with custom implementation)
export interface TimelineDataItem {
  id: string;
  type: 'media' | 'text' | 'transition';
  name: string;
  durationInFrames: number;
  startTimeInFrames: number;
  mediaBinItemId?: string;
  transitionType?: string;
  element?: React.ReactElement;
  scrubbers?: any[]; // Temporary placeholder
}

export interface TrackState {
  id: string;
  items: TimelineDataItem[];
  scrubbers?: any[]; // Temporary placeholder
}

export interface ScrubberState {
  id: string;
  position: number; // in frames
  duration: number; // in frames
  isPlaying: boolean;
  media_width?: number;
  media_height?: number;
  endTime?: number;
}

export interface TimelineState {
  tracks: TrackState[];
  scrubbers: ScrubberState[];
  currentTime: number; // in frames
  totalDuration: number; // in frames
  zoomLevel: number;
}
