import React from "react";
import { AbsoluteFill, Img, Video, Audio, Sequence, useCurrentFrame, interpolate } from "remotion";
import { Player, type PlayerRef } from "@remotion/player";

// Types for the standalone preview
export interface PreviewContent {
  id: string;
  type: "video" | "image" | "audio" | "text" | "empty";
  src?: string;
  text?: {
    content: string;
    fontSize: number;
    color: string;
    fontFamily: string;
    textAlign: "left" | "center" | "right";
    fontWeight: "normal" | "bold";
  };
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  duration?: number; // in seconds
  trimStart?: number; // in frames
  trimEnd?: number; // in frames;
}

export interface PreviewCompositionProps {
  content: PreviewContent[];
  backgroundColor?: string;
  fps?: number;
}

// The standalone preview composition
export function StandalonePreviewComposition({
  content,
  backgroundColor = "#000000",
}: PreviewCompositionProps) {
  return (
    <AbsoluteFill style={{ backgroundColor }}>
      {content.map((item, index) => {
        const durationInFrames = item.duration ? Math.round(item.duration * 30) : 90; // 30 FPS
        const startFrame = index * 30; // Stagger start times
        
        return (
          <Sequence
            key={item.id}
            from={startFrame}
            durationInFrames={durationInFrames}
            layout="none"
          >
            <AnimatedContent item={item} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
}

// Animated content component
function AnimatedContent({ item }: { item: PreviewContent }) {
  const frame = useCurrentFrame();
  const durationInFrames = item.duration ? Math.round(item.duration * 30) : 90;
  
  // Animation for sliding text
  let animatedX = item.position.x;
  let animatedY = item.position.y;
  let opacity = 1;
  let scale = 1;

  if (item.id === "sample-text-3") {
    // Slide in animation from left
    animatedX = interpolate(
      frame,
      [0, 60], // First 2 seconds
      [-500, 500], // From off-screen to center
      { extrapolateRight: "clamp" }
    );
  }

  if (item.id === "sample-text-4") {
    // Bounce scale animation
    scale = interpolate(
      frame,
      [0, 15, 30, 45, 60],
      [0.5, 1.2, 0.9, 1.1, 1.0],
      { extrapolateRight: "clamp" }
    );
  }

  // Fade in animation for all elements
  opacity = interpolate(
    frame,
    [0, 15], // Fade in over 0.5 seconds
    [0, 1],
    { extrapolateRight: "clamp" }
  );

  // Fade out animation at the end
  if (frame > durationInFrames - 30) {
    opacity = interpolate(
      frame,
      [durationInFrames - 30, durationInFrames],
      [1, 0],
      { extrapolateRight: "clamp" }
    );
  }

  return (
    <AbsoluteFill
      style={{
        left: animatedX,
        top: animatedY,
        width: item.position.width,
        height: item.position.height,
        opacity,
        transform: `scale(${scale})`,
      }}
    >
      {renderContent(item)}
    </AbsoluteFill>
  );
}

// Helper function to render different content types
function renderContent(item: PreviewContent): React.ReactNode {
  switch (item.type) {
    case "video":
      return (
        <Video
          src={item.src!}
          trimBefore={item.trimStart}
          trimAfter={item.trimEnd}
        />
      );
    
    case "image":
      return <Img src={item.src!} />;
    
    case "audio":
      return (
        <Audio
          src={item.src!}
          trimBefore={item.trimStart}
          trimAfter={item.trimEnd}
        />
      );
    
    case "text":
      return (
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            textAlign: item.text?.textAlign || "center",
            textShadow: "2px 2px 4px rgba(0,0,0,0.8)", // Add text shadow for better visibility
          }}
        >
          <p
            style={{
              fontSize: item.text?.fontSize || 48,
              color: item.text?.color || "white",
              fontFamily: item.text?.fontFamily || "Arial, sans-serif",
              fontWeight: item.text?.fontWeight || "normal",
              margin: 0,
              padding: "20px",
              textShadow: "2px 2px 4px rgba(0,0,0,0.8)",
            }}
          >
            {item.text?.content || ""}
          </p>
        </div>
      );
    
    case "empty":
    default:
      return <div style={{ backgroundColor: "transparent" }} />;
  }
}

// Props for the standalone video player
export interface StandaloneVideoPlayerProps {
  content: PreviewContent[];
  compositionWidth: number;
  compositionHeight: number;
  backgroundColor?: string;
  playerRef?: React.Ref<PlayerRef>;
  durationInFrames?: number;
}

// The standalone video player component
export function StandaloneVideoPlayer({
  content,
  compositionWidth,
  compositionHeight,
  backgroundColor = "#000000",
  playerRef,
  durationInFrames = 300,
}: StandaloneVideoPlayerProps) {
  console.log("StandaloneVideoPlayer - Content length:", content.length, "Content:", content);

  // If no content, show placeholder
  if (content.length === 0) {
    return (
      <div
        style={{
          width: "100%",
          height: "100%",
          backgroundColor: backgroundColor,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "white",
          fontSize: "24px",
          fontFamily: "Arial, sans-serif",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <p>Standalone Preview Mode</p>
          <p style={{ fontSize: "16px", opacity: 0.7, marginTop: "10px" }}>
            Click "Load Sample" to see animated content
          </p>
        </div>
      </div>
    );
  }

  // Calculate total duration based on content with staggered timing
  const calculatedDuration = content.reduce((max, item, index) => {
    const itemDuration = (item.duration || 3) + (index * 1); // Stagger by 1 second each
    return Math.max(max, itemDuration);
  }, 10); // Minimum 10 seconds to see all animations

  const finalDurationInFrames = durationInFrames || Math.round(calculatedDuration * 30); // 30 FPS

  console.log("Standalone player - Total duration:", calculatedDuration, "seconds, frames:", finalDurationInFrames);

  return (
    <Player
      ref={playerRef}
      component={StandalonePreviewComposition}
      inputProps={{
        content,
        backgroundColor,
      }}
      durationInFrames={finalDurationInFrames}
      compositionWidth={compositionWidth}
      compositionHeight={compositionHeight}
      fps={30}
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
        zIndex: 1,
      }}
      // Enable built-in controls with scrubber/seek bar
      controls={true}
      // Show volume controls alongside play/pause and scrubber
      showVolumeControls={true}
      // Allow fullscreen functionality
      allowFullscreen={true}
      // Enable click-to-play/pause
      clickToPlay={true}
      // Show controls briefly when player loads, then auto-hide
      initiallyShowControls={true}
      // Enable space key for play/pause
      spaceKeyToPlayOrPause={true}
      acknowledgeRemotionLicense
    />
  );
}
