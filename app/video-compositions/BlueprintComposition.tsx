import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, Freeze } from "remotion";
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { flip } from "@remotion/transitions/flip";
import { clockWipe } from "@remotion/transitions/clock-wipe";
import { iris } from "@remotion/transitions/iris";
import { interp } from "../utils/animations";
import type { 
  CompositionBlueprint, 
  Track, 
  Clip,
  BlueprintExecutionContext 
} from "./BlueprintTypes";
import { executeClipElement } from "./executeClipElement";

export interface BlueprintCompositionProps {
  blueprint: CompositionBlueprint;
}

/**
 * Main blueprint composition renderer using proper Remotion TransitionSeries
 * Implements the freeze technique for intuitive duration calculation
 */
export function BlueprintComposition({ blueprint }: BlueprintCompositionProps) {
  const { fps } = useVideoConfig();

  // Create execution context with helper functions
  const executionContext: BlueprintExecutionContext = {
    interp: interp,
    inSeconds: (seconds: number): number => Math.round(seconds * fps),
  };

  console.log("BlueprintComposition rendering with", blueprint.length, "tracks");

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      {blueprint.map((track, trackIndex) => (
        <TrackRenderer
          key={trackIndex}
          track={track}
          executionContext={executionContext}
        />
      ))}
    </AbsoluteFill>
  );
}

/**
 * Intelligent track renderer that respects startTime/endTime while detecting adjacent clips for transitions
 * - Non-adjacent clips: rendered with Sequence at their exact timing
 * - Adjacent clips with transitions: grouped into TransitionSeries with freeze technique
 */
function TrackRenderer({ 
  track, 
  executionContext 
}: { 
  track: Track; 
  executionContext: BlueprintExecutionContext;
}) {
  const { fps } = useVideoConfig();
  
  // Group clips into segments: either individual clips or transition groups
  const segments = groupClipsIntoSegments(track.clips);
  
  return (
    <AbsoluteFill>
      {segments.map((segment, segmentIndex) => (
        <SegmentRenderer
          key={`segment-${segmentIndex}`}
          segment={segment}
          executionContext={executionContext}
          fps={fps}
        />
      ))}
    </AbsoluteFill>
  );
}

/**
 * Groups clips into segments based on adjacency and transitions
 * Now handles orphaned transitions (transitionToNext/transitionFromPrevious without adjacent clips)
 */
function groupClipsIntoSegments(clips: Clip[]): ClipSegment[] {
  const segments: ClipSegment[] = [];
  let i = 0;
  
  while (i < clips.length) {
    const currentClip = clips[i];
    
    // Check for any transitions (including orphaned ones)
    const hasOrphanedTransitionTo = currentClip.transitionToNext && (
      i >= clips.length - 1 || 
      Math.abs(currentClip.endTimeInSeconds - clips[i + 1].startTimeInSeconds) > 0.001
    );
    
    const hasOrphanedTransitionFrom = currentClip.transitionFromPrevious && (
      i === 0 || 
      Math.abs(clips[i - 1].endTimeInSeconds - currentClip.startTimeInSeconds) > 0.001
    );
    
    // Check if this clip starts a regular adjacent transition group
    if (currentClip.transitionToNext && i < clips.length - 1) {
      const nextClip = clips[i + 1];
      // Check if clips are adjacent (current end time == next start time)
      if (Math.abs(currentClip.endTimeInSeconds - nextClip.startTimeInSeconds) < 0.001) {
        // Start building a transition group
        const transitionGroup: Clip[] = [currentClip];
        let j = i + 1;
        
        // Add subsequent adjacent clips with transitions
        while (j < clips.length) {
          const clip = clips[j];
          const prevClip = clips[j - 1];
          
          // Check adjacency
          if (Math.abs(prevClip.endTimeInSeconds - clip.startTimeInSeconds) < 0.001) {
            transitionGroup.push(clip);
            // If this clip doesn't have a transition to next, or it's the last clip, stop
            if (!clip.transitionToNext || j === clips.length - 1) {
              break;
            }
            j++;
          } else {
            break;
          }
        }
        
        segments.push({
          type: 'transition-group',
          clips: transitionGroup,
          startTime: currentClip.startTimeInSeconds,
          hasOrphanedStart: false,
          hasOrphanedEnd: false
        });
        
        i = j + 1;
      } else {
        // Adjacent transition failed, check for orphaned transitions
        if (hasOrphanedTransitionTo || hasOrphanedTransitionFrom) {
          // This clip has orphaned transitions, needs TransitionSeries with empty divs
          segments.push({
            type: 'transition-group',
            clips: [currentClip],
            startTime: hasOrphanedTransitionFrom ? 
              currentClip.startTimeInSeconds - currentClip.transitionFromPrevious!.durationInSeconds :
              currentClip.startTimeInSeconds,
            hasOrphanedStart: !!hasOrphanedTransitionFrom,
            hasOrphanedEnd: !!hasOrphanedTransitionTo
          });
        } else {
          // No transitions, individual clip
          segments.push({
            type: 'individual',
            clips: [currentClip],
            startTime: currentClip.startTimeInSeconds,
            hasOrphanedStart: false,
            hasOrphanedEnd: false
          });
        }
        i++;
      }
    } else if (hasOrphanedTransitionTo || hasOrphanedTransitionFrom) {
      // This clip has orphaned transitions but no adjacent clips
      segments.push({
        type: 'transition-group',
        clips: [currentClip],
        startTime: hasOrphanedTransitionFrom ? 
          currentClip.startTimeInSeconds - currentClip.transitionFromPrevious!.durationInSeconds :
          currentClip.startTimeInSeconds,
        hasOrphanedStart: !!hasOrphanedTransitionFrom,
        hasOrphanedEnd: !!hasOrphanedTransitionTo
      });
      i++;
    } else {
      // Individual clip (no transition)
      segments.push({
        type: 'individual',
        clips: [currentClip],
        startTime: currentClip.startTimeInSeconds,
        hasOrphanedStart: false,
        hasOrphanedEnd: false
      });
      i++;
    }
  }
  
  return segments;
}

type ClipSegment = {
  type: 'individual' | 'transition-group';
  clips: Clip[];
  startTime: number;
  hasOrphanedStart: boolean;
  hasOrphanedEnd: boolean;
};

/**
 * Renders a segment (either individual clip or transition group)
 */
function SegmentRenderer({
  segment,
  executionContext,
  fps
}: {
  segment: ClipSegment;
  executionContext: BlueprintExecutionContext;
  fps: number;
}) {
  const startFrame = Math.round(segment.startTime * fps);
  
  if (segment.type === 'individual') {
    // Render single clip at its specified time
    const clip = segment.clips[0];
    const durationInFrames = Math.round(
      (clip.endTimeInSeconds - clip.startTimeInSeconds) * fps
    );
    
    return (
      <Sequence
        from={startFrame}
        durationInFrames={durationInFrames}
        layout="none"
      >
        <ClipContent clip={clip} executionContext={executionContext} />
      </Sequence>
    );
  } else {
    // Render transition group using TransitionSeries with support for orphaned transitions
    const sequences: React.ReactElement[] = [];
    let totalDurationFrames = 0;
    
    // Handle orphaned fade-in at the start
    if (segment.hasOrphanedStart && segment.clips[0].transitionFromPrevious) {
      const transitionDuration = Math.round(segment.clips[0].transitionFromPrevious.durationInSeconds * fps);
      totalDurationFrames += transitionDuration;
      
      // Add empty div sequence
      sequences.push(
        <TransitionSeries.Sequence
          key="orphaned-start-empty"
          durationInFrames={transitionDuration}
        >
          <AbsoluteFill style={{ backgroundColor: '#000000' }} />
        </TransitionSeries.Sequence>
      );
      
      // Add transition
      sequences.push(
        <TransitionSeries.Transition
          key="orphaned-start-transition"
          presentation={getTransitionPresentation({ type: 'fade', durationInSeconds: 0 })}
          timing={linearTiming({ durationInFrames: transitionDuration })}
        />
      );
    }
    
    // Process clips (regular adjacent logic or single orphaned clip)
    if (segment.clips.length === 1 && (segment.hasOrphanedStart || segment.hasOrphanedEnd)) {
      // Single clip with orphaned transitions
      const clip = segment.clips[0];
      const clipDurationFrames = Math.round((clip.endTimeInSeconds - clip.startTimeInSeconds) * fps);
      
      let clipSequenceDurationFrames = clipDurationFrames;
      if (segment.hasOrphanedEnd && clip.transitionToNext) {
        clipSequenceDurationFrames += Math.round(clip.transitionToNext.durationInSeconds * fps);
      }
      
      totalDurationFrames += clipSequenceDurationFrames;
      
      sequences.push(
        <TransitionSeries.Sequence 
          key={`seq-${clip.id}`}
          durationInFrames={clipSequenceDurationFrames}
        >
          <ClipContentWithFreeze 
            clip={clip} 
            executionContext={executionContext} 
            freezeAfterFrames={clipDurationFrames}
            totalSequenceDuration={clipSequenceDurationFrames}
          />
        </TransitionSeries.Sequence>
      );
    } else {
      // Regular adjacent clips logic (existing code)
      totalDurationFrames += calculateTransitionGroupDuration(segment.clips, fps);
      
      segment.clips.forEach((clip, index) => {
        const clipDurationFrames = Math.round(
          (clip.endTimeInSeconds - clip.startTimeInSeconds) * fps
        );
        
        // Apply freeze technique: extend clip duration by transition duration
        const hasTransitionToNext = clip.transitionToNext && index < segment.clips.length - 1;
        const transitionDuration = hasTransitionToNext 
          ? Math.round(clip.transitionToNext!.durationInSeconds * fps)
          : 0;
        
        const sequenceDurationFrames = clipDurationFrames + transitionDuration;
        
        // Add the sequence with proper freeze technique
        console.log(`Setting up TransitionSeries.Sequence for ${clip.id}: duration=${sequenceDurationFrames}, freezeAfter=${clipDurationFrames}`);
        
        sequences.push(
          <TransitionSeries.Sequence 
            key={`seq-${clip.id}`}
            durationInFrames={sequenceDurationFrames}
          >
            <ClipContentWithFreeze 
              clip={clip} 
              executionContext={executionContext} 
              freezeAfterFrames={clipDurationFrames}
              totalSequenceDuration={sequenceDurationFrames}
            />
          </TransitionSeries.Sequence>
        );
        
        // Add transition if this clip has one and it's not the last clip
        if (hasTransitionToNext) {
          sequences.push(
            <TransitionSeries.Transition
              key={`trans-${clip.id}`}
              presentation={getTransitionPresentation(clip.transitionToNext!)}
              timing={linearTiming({ durationInFrames: transitionDuration })}
            />
          );
        }
      });
    }
    
    // Handle orphaned fade-out at the end
    if (segment.hasOrphanedEnd && segment.clips[segment.clips.length - 1].transitionToNext) {
      const transitionDuration = Math.round(segment.clips[segment.clips.length - 1].transitionToNext!.durationInSeconds * fps);
      totalDurationFrames += transitionDuration;
      
      // Add transition
      sequences.push(
        <TransitionSeries.Transition
          key="orphaned-end-transition"
          presentation={getTransitionPresentation({ type: 'fade', durationInSeconds: 0 })}
          timing={linearTiming({ durationInFrames: transitionDuration })}
        />
      );
      
      // Add empty div sequence
      sequences.push(
        <TransitionSeries.Sequence
          key="orphaned-end-empty"
          durationInFrames={transitionDuration}
        >
          <AbsoluteFill style={{ backgroundColor: '#000000' }} />
        </TransitionSeries.Sequence>
      );
    }
    
    return (
      <Sequence
        from={startFrame}
        durationInFrames={totalDurationFrames}
        layout="none"
      >
        <TransitionSeries>
          {sequences}
        </TransitionSeries>
      </Sequence>
    );
  }
}

/**
 * Calculate total duration for a transition group (intuitive timing)
 */
function calculateTransitionGroupDuration(clips: Clip[], fps: number): number {
  if (clips.length === 0) return 0;
  
  const startTime = clips[0].startTimeInSeconds;
  const endTime = clips[clips.length - 1].endTimeInSeconds;
  return Math.round((endTime - startTime) * fps);
}

/**
 * Helper function to get Remotion presentation from transition configuration
 */
function getTransitionPresentation(
  transitionConfig: import('./BlueprintTypes').TransitionConfig
): any {
  const { width, height } = useVideoConfig();
  const { type, direction, perspective } = transitionConfig;
  
  switch (type) {
    case 'fade':
      return fade({
        shouldFadeOutExitingScene: true // Enable proper cross-fade
      });
      
    case 'slide':
      return slide({
        direction: (direction as any) || 'from-left'
      });
      
    case 'wipe':
      return wipe({
        direction: (direction as any) || 'from-left'
      });
      
    case 'flip':
      return flip({
        direction: (direction as any) || 'from-left',
        perspective: perspective || 1000
      });
      
    case 'clockWipe':
      return clockWipe({
        width,
        height
      });
      
    case 'iris':
      return iris({
        width,
        height
      });
      
    default:
      return fade({
        shouldFadeOutExitingScene: true
      });
  }
}



/**
 * Renders the actual content of a clip using executeClipElement
 * This is used within TransitionSeries.Sequence components
 */
function ClipContent({ 
  clip, 
  executionContext 
}: { 
  clip: Clip; 
  executionContext: BlueprintExecutionContext;
}) {
  // Execute the clip's element string as TSX
  const clipElement = executeClipElement(clip.element, executionContext);
  
  return clipElement;
}

/**
 * Renders clip content with proper freeze technique for TransitionSeries
 * When freezeAfterFrames is reached, video content freezes at last frame
 */
function ClipContentWithFreeze({ 
  clip, 
  executionContext,
  freezeAfterFrames,
  totalSequenceDuration
}: { 
  clip: Clip; 
  executionContext: BlueprintExecutionContext;
  freezeAfterFrames: number;
  totalSequenceDuration: number;
}) {
  const frame = useCurrentFrame();
  
  console.log(`ClipContentWithFreeze - Clip: ${clip.id}, Frame: ${frame}, FreezeAfter: ${freezeAfterFrames}`);
  
  // Simplest approach: extend the video duration from the start to avoid any jumps
  if (clip.element.includes('Video')) {
    const endAtMatch = clip.element.match(/endAt:\s*(\d+)/);
    
    if (endAtMatch) {
      const originalEndFrame = parseInt(endAtMatch[1]);
      
      // If we need to extend beyond the original video duration, just repeat the last frame
      if (totalSequenceDuration > freezeAfterFrames) {
        const extendedElement = clip.element.replace(
          /endAt:\s*\d+/,
          `endAt: ${originalEndFrame + (totalSequenceDuration - freezeAfterFrames)}`
        );
        
        console.log(`Pre-extended video to cover full sequence duration: ${totalSequenceDuration} frames`);
        return executeClipElement(extendedElement, executionContext);
      }
    }
  }
  
  // Normal rendering for non-video or no extension needed
  return executeClipElement(clip.element, executionContext);
}


