import React from "react";
import * as Remotion from "remotion";
import { fade } from "@remotion/transitions";
import { interp } from "../utils/animations";
import type { CompositionBlueprint } from "./BlueprintTypes";

// Destructure commonly used components for convenience
const { 
  AbsoluteFill, 
  Sequence, 
  Img, 
  Video, 
  Audio,
  Freeze,
  TransitionSeries,
} = Remotion;

// REUSABLE EXECUTOR FOR CLIP ELEMENTS
const executeClipElement = (elementString: string): React.ReactElement => {
  try {
    // This function takes the element string from the blueprint,
    // executes it in a safe sandbox, and returns a renderable React element.
    const executeCode = new Function(
      'React',
      'AbsoluteFill',
      'interp',
      'Img',
      'Video',
      'Audio',
      // We expect the string to be a valid React.createElement call.
      // Adding "return" makes it a valid function body.
      `return ${elementString}` 
    );

    return executeCode(
      React,
      AbsoluteFill,
      interp,
      Img,
      Video,
      Audio
    );
  } catch (error) {
    console.error("Error executing clip element:", error);
    // If a single clip's code is invalid, we render an error message
    // in its place without crashing the entire video.
    return (
      <AbsoluteFill style={{ backgroundColor: 'red', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'white', fontSize: '20px', padding: '20px', fontFamily: 'sans-serif' }}>
          Error in clip: {error instanceof Error ? error.message : "Unknown error"}
        </p>
      </AbsoluteFill>
    );
  }
};

export interface BlueprintCompositionProps {
  blueprint: CompositionBlueprint;
  fps: number;
}

export function BlueprintComposition({ blueprint, fps }: BlueprintCompositionProps) {
  // If no blueprint, show a placeholder.
  if (!blueprint || blueprint.length === 0) {
    return (
      <AbsoluteFill style={{ backgroundColor: '#000000', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: 'white', fontSize: '24px', fontFamily: 'sans-serif' }}>
          No blueprint to display
        </div>
      </AbsoluteFill>
    );
  }

  // This is the new rendering engine.
  return (
    <AbsoluteFill>
      {blueprint.map((track, trackIndex) => {
        // The track's index in the array determines its Z-order.
        const zIndex = trackIndex;

        // --- TRANSITION LOGIC ---
        // First, we analyze the track to see if it's a valid sequential track
        // that can be rendered with TransitionSeries.
        let isSequential = true;
        if (track.clips.length === 0) {
          isSequential = false;
        } else {
          for (let i = 0; i < track.clips.length - 1; i++) {
            const currentClip = track.clips[i];
            const nextClip = track.clips[i + 1];
            // A track is sequential if each clip starts exactly when the last one ended,
            // and it has a transition flag.
            if (currentClip.endTimeInSeconds !== nextClip.startTimeInSeconds || !currentClip.transitionToNext) {
              isSequential = false;
              break;
            }
          }
        }
        
        // If it's a sequential track, we use the powerful TransitionSeries component.
        if (isSequential) {
          return (
            <div key={`track-${trackIndex}`} style={{ zIndex, position: 'absolute', width: '100%', height: '100%' }}>
              <TransitionSeries>
                {track.clips.map((clip, clipIndex) => {
                  // Here we perform the critical duration math to handle the transition overlap.
                  const contentDurationS = clip.endTimeInSeconds - clip.startTimeInSeconds;
                  const transitionDurationS = clip.transitionToNext?.durationInSeconds || 0;
                  const sequenceDurationS = contentDurationS + transitionDurationS;

                  const elements = [];
                  elements.push(
                    <TransitionSeries.Sequence
                      key={clip.id}
                      durationInFrames={Math.round(sequenceDurationS * fps)}
                    >
                      <Freeze frame={Math.round(contentDurationS * fps)}>
                        {executeClipElement(clip.element)}
                      </Freeze>
                    </TransitionSeries.Sequence>
                  );

                  if (clip.transitionToNext && clipIndex < track.clips.length - 1) {
                    elements.push(
                      <TransitionSeries.Transition
                        key={`${clip.id}-transition`}
                        durationInFrames={Math.round(transitionDurationS * fps)}
                        presentation={fade()} // Currently supports fade, can be expanded.
                      />
                    );
                  }
                  return elements;
                })}
              </TransitionSeries>
            </div>
          );
        }
        
        // --- STANDARD OVERLAY LOGIC ---
        // If the track is not sequential, we render each clip as an independent overlay.
        return track.clips.map((clip) => {
          const durationInSeconds = clip.endTimeInSeconds - clip.startTimeInSeconds;
          if (durationInSeconds <= 0) return null;

          return (
            <Sequence
              key={clip.id}
              from={Math.round(clip.startTimeInSeconds * fps)}
              durationInFrames={Math.round(durationInSeconds * fps)}
              style={{ zIndex }}
            >
              {executeClipElement(clip.element)}
            </Sequence>
          );
        });
      })}
    </AbsoluteFill>
  );
}

// Legacy exports for backward compatibility
export const renderTransitionSeries = () => null;
export const renderSequence = () => null;
