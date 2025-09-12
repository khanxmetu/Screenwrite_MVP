import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { interp } from "../utils/animations";
import type { 
  CompositionBlueprint, 
  Track, 
  Clip,
  TransitionSeries,
  BlueprintExecutionContext 
} from "./BlueprintTypes";
import { executeClipElement } from "./executeClipElement";

export interface BlueprintCompositionProps {
  blueprint: CompositionBlueprint;
}

/**
 * Main blueprint composition renderer
 * This component renders a structured blueprint-based composition
 */
export function BlueprintComposition({ blueprint }: BlueprintCompositionProps) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Create execution context with helper functions
  const executionContext: BlueprintExecutionContext = {
    interp: interp,
    inSeconds: (seconds: number): number => Math.round(seconds * fps),
  };

  console.log("BlueprintComposition rendering at frame:", frame, "with", blueprint.tracks.length, "tracks");

  return (
    <AbsoluteFill style={{ backgroundColor: blueprint.backgroundColor || "#000000" }}>
      {blueprint.tracks.map((track) => (
        <TrackRenderer
          key={track.id}
          track={track}
          executionContext={executionContext}
        />
      ))}
    </AbsoluteFill>
  );
}

/**
 * Renders a single track with all its clips
 */
function TrackRenderer({ 
  track, 
  executionContext 
}: { 
  track: Track; 
  executionContext: BlueprintExecutionContext;
}) {
  return (
    <AbsoluteFill>
      {track.clips.map((clip) => (
        <ClipRenderer
          key={clip.id}
          clip={clip}
          executionContext={executionContext}
        />
      ))}
    </AbsoluteFill>
  );
}

/**
 * Renders a single clip with proper timing and transitions
 */
function ClipRenderer({ 
  clip, 
  executionContext 
}: { 
  clip: Clip; 
  executionContext: BlueprintExecutionContext;
}) {
  const { fps } = useVideoConfig();
  
  // Convert seconds to frames
  const startFrame = Math.round(clip.startTime * fps);
  const durationInFrames = Math.round(clip.duration * fps);

  console.log(`Rendering clip ${clip.id}: start=${startFrame}f, duration=${durationInFrames}f`);

  return (
    <Sequence
      from={startFrame}
      durationInFrames={durationInFrames}
      layout="none"
    >
      <ClipContent 
        clip={clip} 
        executionContext={executionContext} 
      />
    </Sequence>
  );
}

/**
 * Renders the actual content of a clip with transitions
 */
function ClipContent({ 
  clip, 
  executionContext 
}: { 
  clip: Clip; 
  executionContext: BlueprintExecutionContext;
}) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Execute the clip's TSX code
  const clipElement = executeClipElement(clip.code, executionContext);
  
  // Apply transitions if specified
  if (clip.transition && clip.transition.type !== 'none') {
    return (
      <TransitionWrapper
        clip={clip}
        frame={frame}
        fps={fps}
      >
        {clipElement}
      </TransitionWrapper>
    );
  }

  return clipElement;
}

/**
 * Applies transition effects to clip content
 */
function TransitionWrapper({
  clip,
  frame,
  fps,
  children
}: {
  clip: Clip;
  frame: number;
  fps: number;
  children: React.ReactElement;
}) {
  if (!clip.transition || clip.transition.type === 'none') {
    return children;
  }

  const transitionFrames = Math.round(clip.transition.duration * fps);
  const clipDurationFrames = Math.round(clip.duration * fps);
  
  let style: React.CSSProperties = {};

  switch (clip.transition.type) {
    case 'fade':
      // Fade in at start, fade out at end
      if (frame < transitionFrames) {
        // Fade in
        const opacity = interp(0, transitionFrames, 0, 1);
        style.opacity = opacity;
      } else if (frame > clipDurationFrames - transitionFrames) {
        // Fade out
        const opacity = interp(clipDurationFrames - transitionFrames, clipDurationFrames, 1, 0);
        style.opacity = opacity;
      }
      break;
      
    case 'slide':
      // Slide in from left
      if (frame < transitionFrames) {
        const translateX = interp(0, transitionFrames, -100, 0);
        style.transform = `translateX(${translateX}%)`;
      }
      break;
      
    case 'scale':
      // Scale in from small
      if (frame < transitionFrames) {
        const scale = interp(0, transitionFrames, 0.8, 1);
        style.transform = `scale(${scale})`;
      }
      break;
  }

  return (
    <div style={{ ...style, width: '100%', height: '100%' }}>
      {children}
    </div>
  );
}

/**
 * Renders clips in sequential mode (TransitionSeries)
 * Each clip plays after the previous one ends
 */
export function renderTransitionSeries(
  series: TransitionSeries,
  executionContext: BlueprintExecutionContext
): React.ReactElement {
  let currentStartTime = 0;
  
  return (
    <AbsoluteFill>
      {series.clips.map((clip, index) => {
        const clipStartTime = currentStartTime;
        const clipWithTransition = {
          ...clip,
          startTime: clipStartTime,
          transition: clip.transition || series.defaultTransition
        };
        
        // Update start time for next clip
        currentStartTime += clip.duration;
        
        return (
          <ClipRenderer
            key={clip.id}
            clip={clipWithTransition}
            executionContext={executionContext}
          />
        );
      })}
    </AbsoluteFill>
  );
}

/**
 * Renders clips in overlay mode (Sequence)
 * All clips play simultaneously, stacked on top of each other
 */
export function renderSequence(
  sequence: import('./BlueprintTypes').Sequence,
  executionContext: BlueprintExecutionContext
): React.ReactElement {
  return (
    <AbsoluteFill>
      {sequence.clips.map((clip) => (
        <ClipRenderer
          key={clip.id}
          clip={clip}
          executionContext={executionContext}
        />
      ))}
    </AbsoluteFill>
  );
}
