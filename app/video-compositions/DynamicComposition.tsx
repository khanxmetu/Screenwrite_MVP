import React, { useState, useEffect } from "react";
import * as Remotion from "remotion";
import { Player, type PlayerRef } from "@remotion/player";
import { Animated } from "remotion-animated";
import { Move, Scale, Rotate, Fade, Ease } from "remotion-animated";

// Destructure commonly used components for convenience
const { 
  AbsoluteFill, 
  useCurrentFrame, 
  interpolate, 
  Sequence, 
  Img, 
  Video, 
  Audio, 
  spring, 
  useVideoConfig,
  useCurrentScale,
  Easing
} = Remotion;

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

  // If no TSX code, show placeholder
  if (!tsxCode) {
    return (
      <div style={{ backgroundColor, width: "100%", height: "100%" }}>
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
          No content to display
        </div>
      </div>
    );
  }

  // SIMPLIFIED EXECUTION - Only execute the generated code with minimal setup
  try {
    console.log("Executing AI-generated code directly:", tsxCode.slice(0, 100) + "...");

    // Use the imported components directly
    const AnimatedFade = Fade;
    
    // Helper function to convert seconds to frames
    const inSeconds = (seconds: number): number => {
      return Math.round(seconds * 30); // 30 FPS
    };

    // Essential Positioning Helpers - Return CSS style objects
    
    // Screen Anchors (9 fundamental positions)
    const TopLeft = (margin = 0) => ({
      position: 'absolute' as const,
      top: margin,
      left: margin
    });

    const TopCenter = (margin = 0) => ({
      position: 'absolute' as const,
      top: margin,
      left: '50%',
      transform: 'translateX(-50%)'
    });

    const TopRight = (margin = 0) => ({
      position: 'absolute' as const,
      top: margin,
      right: margin
    });

    const CenterLeft = (margin = 0) => ({
      position: 'absolute' as const,
      top: '50%',
      left: margin,
      transform: 'translateY(-50%)'
    });

    const CenterScreen = () => ({
      position: 'absolute' as const,
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)'
    });

    const CenterRight = (margin = 0) => ({
      position: 'absolute' as const,
      top: '50%',
      right: margin,
      transform: 'translateY(-50%)'
    });

    const BottomLeft = (margin = 0) => ({
      position: 'absolute' as const,
      bottom: margin,
      left: margin
    });

    const BottomCenter = (margin = 0) => ({
      position: 'absolute' as const,
      bottom: margin,
      left: '50%',
      transform: 'translateX(-50%)'
    });

    const BottomRight = (margin = 0) => ({
      position: 'absolute' as const,
      bottom: margin,
      right: margin
    });

    // Relative Positioning (simplified for now - conceptual)
    const Above = (elementId: string, spacing = 20) => ({
      position: 'absolute' as const,
      bottom: `calc(var(--${elementId}-top) + ${spacing}px)`,
      left: `var(--${elementId}-left)`
    });

    const Below = (elementId: string, spacing = 20) => ({
      position: 'absolute' as const,
      top: `calc(var(--${elementId}-bottom) + ${spacing}px)`,
      left: `var(--${elementId}-left)`
    });

    const LeftOf = (elementId: string, spacing = 20) => ({
      position: 'absolute' as const,
      top: `var(--${elementId}-top)`,
      right: `calc(var(--${elementId}-left) + ${spacing}px)`
    });

    const RightOf = (elementId: string, spacing = 20) => ({
      position: 'absolute' as const,
      top: `var(--${elementId}-top)`,
      left: `calc(var(--${elementId}-right) + ${spacing}px)`
    });

    const CenterOn = (elementId: string) => ({
      position: 'absolute' as const,
      top: `var(--${elementId}-center-y)`,
      left: `var(--${elementId}-center-x)`,
      transform: 'translate(-50%, -50%)'
    });

    // Simple execution - just the generated code
    const executeCode = new Function(
      'React',
      'Animated', 
      'Move', 
      'Scale', 
      'Rotate', 
      'AnimatedFade',
      'inSeconds',
      'Ease',
      'TopLeft',
      'TopCenter', 
      'TopRight',
      'CenterLeft',
      'CenterScreen',
      'CenterRight',
      'BottomLeft',
      'BottomCenter',
      'BottomRight',
      'Above',
      'Below',
      'LeftOf',
      'RightOf',
      'CenterOn',
      tsxCode
    );

    const generatedJSX = executeCode(
      React,
      Animated,
      Move,
      Scale,
      Rotate,
      AnimatedFade,
      inSeconds,
      Ease,
      TopLeft,
      TopCenter,
      TopRight,
      CenterLeft,
      CenterScreen,
      CenterRight,
      BottomLeft,
      BottomCenter,
      BottomRight,
      Above,
      Below,
      LeftOf,
      RightOf,
      CenterOn
    );

    return generatedJSX;
  } catch (error) {
    console.error("Error executing AI-generated code:", error);

    return (
      <div style={{ backgroundColor: "#1a1a1a", width: "100%", height: "100%" }}>
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
          </div>
        </div>
      </div>
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
