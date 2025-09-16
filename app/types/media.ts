// MediaBinItem type definition compatible with existing code
export interface MediaBinItem {
  id: string;
  mediaType: "video" | "image" | "audio" | "text" | "element";
  mediaUrlLocal: string | null;
  mediaUrlRemote: string | null;
  media_width: number;
  media_height: number;
  name: string;
  durationInSeconds: number;
  
  // Upload tracking properties
  uploadProgress: number | null;
  isUploading: boolean;
  
  // Gemini file reference for analysis
  gemini_file_id: string | null;
  
  // Optional blueprint-specific properties
  element?: string;
  text: TextProperties | null;
  left_transition_id: string | null;
  right_transition_id: string | null;
}

export interface TextProperties {
  textContent: string;
  fontSize: number;
  fontFamily: string;
  color: string;
  textAlign: "left" | "center" | "right";
  fontWeight: "normal" | "bold";
}
