import React, { useState, useEffect } from "react";
import * as Remotion from "remotion";
import { Player, type PlayerRef } from "@remotion/player";
import { interp } from "../utils/animations";
import { BlueprintComposition } from "./BlueprintComposition";
import { calculateBlueprintDuration } from "./executeClipElement";
import type { CompositionBlueprint } from "./BlueprintTypes";

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
  blueprint?: CompositionBlueprint;
  backgroundColor?: string;
  fps?: number;
}

// Dynamic composition that renders blueprint-based compositions only
export function DynamicComposition({
  blueprint,
  backgroundColor = "#000000",
}: DynamicCompositionProps) {

  // Blueprint-based rendering
  if (blueprint) {
    console.log("Rendering blueprint composition with", blueprint.length, "tracks");
    return (
      <BlueprintComposition 
        blueprint={blueprint} 
      />
    );
  }

  // No content placeholder
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

// Props for the dynamic video player
export interface DynamicVideoPlayerProps {
  blueprint?: CompositionBlueprint;
  compositionWidth: number;
  compositionHeight: number;
  backgroundColor?: string;
  playerRef?: React.Ref<PlayerRef>;
  durationInFrames?: number;
}

// The dynamic video player component
export function DynamicVideoPlayer({
  blueprint,
  compositionWidth,
  compositionHeight,
  backgroundColor = "#000000",
  playerRef,
  durationInFrames,
}: DynamicVideoPlayerProps) {
  console.log("DynamicVideoPlayer - Blueprint tracks:", blueprint?.length || 0);

  // Calculate duration based on blueprint
  const calculatedDuration = React.useMemo(() => {
    if (blueprint) {
      return calculateBlueprintDuration(blueprint);
    }
    return durationInFrames || 300; // Default 10 seconds at 30fps
  }, [blueprint, durationInFrames]);

  return (
    <Player
      ref={playerRef}
      component={DynamicComposition}
      inputProps={{
        blueprint,
        backgroundColor,
      }}
      durationInFrames={Math.max(calculatedDuration, 1)} // Ensure minimum 1 frame
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
