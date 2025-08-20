import React from "react";
import { 
  AbsoluteFill, 
  useCurrentFrame, 
  interpolate, 
  Sequence, 
  Img, 
  Video, 
  Audio, 
  spring, 
  useVideoConfig,
  useCurrentScale 
} from "remotion";
import { Player, type PlayerRef } from "@remotion/player";
import { fade } from "@remotion/transitions/fade";
import { iris } from "@remotion/transitions/iris";
import { wipe } from "@remotion/transitions/wipe";
import { flip } from "@remotion/transitions/flip";
import { slide } from "@remotion/transitions/slide";

export interface DynamicCompositionProps {
  tsxCode: string;
  backgroundColor?: string;
  fps?: number;
}

// Dynamic composition that executes AI-generated TSX code
export function DynamicComposition({
  tsxCode,
  backgroundColor = "#000000",
}: DynamicCompositionProps) {
  const frame = useCurrentFrame();

  // If no TSX code, show placeholder
  if (!tsxCode) {
    return (
      <AbsoluteFill style={{ backgroundColor }}>
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "white",
            fontSize: "24px",
            fontFamily: "Arial, sans-serif",
          }}
        >
          <div style={{ textAlign: "center" }}>
            <p>AI Composition Mode</p>
            <p style={{ fontSize: "16px", opacity: 0.7, marginTop: "10px" }}>
              Describe what you want to see and AI will generate Remotion code
            </p>
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  // Execute the AI-generated TSX code
  try {
    console.log('Executing AI-generated code directly:', tsxCode.slice(0, 200) + '...');

    // Call hooks at component level (Rules of Hooks)
    const frame = useCurrentFrame();
    const videoConfig = useVideoConfig();
    const currentScale = useCurrentScale();

    // Create a function that evaluates the JavaScript code that returns JSX
    const executeCode = new Function(
      'React',
      'AbsoluteFill', 
      'currentFrameValue', // Renamed to avoid conflicts
      'interpolate', 
      'Sequence',
      'Img',
      'Video',
      'Audio',
      'spring',
      'videoConfigValue', // Renamed to avoid conflicts
      'currentScaleValue', // Renamed to avoid conflicts
      'Player',
      'fade',
      'iris',
      'wipe',
      'flip',
      'slide',
      `
      // Available components and functions
      const { createElement } = React;
      
      // Create helper functions that use the passed values
      const useCurrentFrame = () => currentFrameValue;
      const useVideoConfig = () => videoConfigValue;
      const useCurrentScale = () => currentScaleValue;
      
      // Execute the AI-generated code directly
      ${tsxCode}
      `
    );

    const generatedJSX = executeCode(
      React,
      AbsoluteFill,
      frame, // Pass the actual frame value
      interpolate,
      Sequence,
      Img,
      Video,
      Audio,
      spring,
      videoConfig, // Pass the config object
      currentScale, // Pass the scale value
      Player,
      fade,
      iris,
      wipe,
      flip,
      slide
    );

    return generatedJSX;
  } catch (error) {
    console.error("Error executing AI-generated code:", error);
    return (
      <AbsoluteFill style={{ backgroundColor: "#1a1a1a" }}>
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#ff6b6b",
            fontSize: "18px",
            fontFamily: "Arial, sans-serif",
            textAlign: "center",
            padding: "40px",
          }}
        >
          <div>
            <p>⚠️ Error in AI-generated code</p>
            <p style={{ fontSize: "14px", opacity: 0.8, marginTop: "10px" }}>
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
            <p style={{ fontSize: "12px", opacity: 0.6, marginTop: "20px" }}>
              Try rephrasing your request or ask for something simpler
            </p>
          </div>
        </div>
      </AbsoluteFill>
    );
  }
}

// Props for the dynamic video player
export interface DynamicVideoPlayerProps {
  tsxCode: string;
  compositionWidth: number;
  compositionHeight: number;
  backgroundColor?: string;
  playerRef?: React.Ref<PlayerRef>;
  durationInFrames?: number;
}

// The dynamic video player component
export function DynamicVideoPlayer({
  tsxCode,
  compositionWidth,
  compositionHeight,
  backgroundColor = "#000000",
  playerRef,
  durationInFrames = 300, // Default 10 seconds at 30fps
}: DynamicVideoPlayerProps) {
  console.log("DynamicVideoPlayer - TSX Code length:", tsxCode?.length || 0);

  return (
    <Player
      ref={playerRef}
      component={DynamicComposition}
      inputProps={{
        tsxCode,
        backgroundColor,
      }}
      durationInFrames={durationInFrames}
      compositionWidth={compositionWidth}
      compositionHeight={compositionHeight}
      fps={30}
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
        zIndex: 1,
      }}
      acknowledgeRemotionLicense
    />
  );
}
