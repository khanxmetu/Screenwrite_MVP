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
  const { fps, width, height } = useVideoConfig();
  const videoConfig = { width, height };

  // Create base execution context with helper functions
  const createExecutionContext = (clipStartTime: number): BlueprintExecutionContext => ({
    interp: (
      startTimeOrTimePoints: number | number[], 
      endTimeOrValues?: number | number[], 
      fromValueOrEasing?: number | 'in' | 'out' | 'inOut' | 'linear', 
      toValue?: number, 
      easing?: 'in' | 'out' | 'inOut' | 'linear'
    ) => {
      // Handle keyframe syntax: interp([0, 2, 3, 4], [0, 1, 1, 0], 'linear')
      if (Array.isArray(startTimeOrTimePoints)) {
        const globalTimePoints = startTimeOrTimePoints;
        const values = endTimeOrValues as number[];
        const easingType = fromValueOrEasing as 'in' | 'out' | 'inOut' | 'linear';
        
        // Convert global timing to clip-relative timing
        const localTimePoints = globalTimePoints.map(t => t - clipStartTime);
        
        return interp(localTimePoints, values, easingType);
      }
      
      // Handle simple syntax: interp(0, 2, 0, 1, 'linear')
      const globalStartTime = startTimeOrTimePoints as number;
      const globalEndTime = endTimeOrValues as number;
      const fromValue = fromValueOrEasing as number;
      
      // Convert global timing to clip-relative timing
      const localStartTime = globalStartTime - clipStartTime;
      const localEndTime = globalEndTime - clipStartTime;
      
      return interp(localStartTime, localEndTime, fromValue, toValue!, easing as 'in' | 'out' | 'inOut' | 'linear');
    },
    inSeconds: (seconds: number): number => Math.round(seconds * fps),
    sequenceStartTime: clipStartTime,
  });

  // Ensure we have valid tracks array
  const validBlueprint = Array.isArray(blueprint) ? blueprint : [];

  console.log("🎬 BlueprintComposition: Rendering", validBlueprint.length, "tracks");
  validBlueprint.forEach((track, i) => {
    console.log(`🎬 Track ${i}:`, track.clips?.length || 0, "clips");
    track.clips?.forEach(clip => {
      console.log(`🎬   - ${clip.id}: ${clip.startTimeInSeconds}s-${clip.endTimeInSeconds}s`);
    });
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      {validBlueprint.map((track, trackIndex) => (
        <TrackRenderer
          key={`track-${trackIndex}-${track.clips.length}`}
          track={track}
          createExecutionContext={createExecutionContext}
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
  createExecutionContext 
}: { 
  track: Track; 
  createExecutionContext: (clipStartTime: number) => BlueprintExecutionContext;
}) {
  const { fps, width, height } = useVideoConfig();
  const videoConfig = { width, height };
  
  // Ensure track has clips array
  const clips = track.clips || [];
  
  // Group clips into segments: either individual clips or transition groups
  const segments = groupClipsIntoSegments(clips);
  
  return (
    <AbsoluteFill>
      {segments.map((segment, segmentIndex) => (
        <SegmentRenderer
          key={`segment-${segmentIndex}-${segment.clips.map(c => c.id).join('-')}`}
          segment={segment}
          createExecutionContext={createExecutionContext}
          fps={fps}
          videoConfig={videoConfig}
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
  
  console.log(`🎬 groupClipsIntoSegments: Processing ${clips.length} clips`);
  
  while (i < clips.length) {
    const currentClip = clips[i];
    console.log(`🎬 Processing clip ${i}: ${currentClip.id} (${currentClip.startTimeInSeconds}s-${currentClip.endTimeInSeconds}s)`);
    console.log(`🎬 - Has transitionToNext: ${!!currentClip.transitionToNext}`);
    console.log(`🎬 - Has transitionFromPrevious: ${!!currentClip.transitionFromPrevious}`);
    
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
      const timeDiff = Math.abs(currentClip.endTimeInSeconds - nextClip.startTimeInSeconds);
      console.log(`🎬 Adjacency check: Current clip ends at ${currentClip.endTimeInSeconds}s, next clip starts at ${nextClip.startTimeInSeconds}s, diff: ${timeDiff}`);
      // Check if clips are adjacent (current end time == next start time)
      if (timeDiff < 0.001) {
        console.log(`🎬 ✅ Clips are adjacent! Creating transition group...`);
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
        console.log(`🎬 ❌ Clips not adjacent (diff: ${timeDiff}), checking for orphaned transitions...`);
        // Adjacent transition failed, check for orphaned transitions
        if (hasOrphanedTransitionTo || hasOrphanedTransitionFrom) {
          // This clip has orphaned transitions, needs TransitionSeries with empty divs
          console.log(`🎬 Creating orphaned transition segment for ${currentClip.id}`);
          // For orphaned transitions, timing should be WITHIN clip boundaries, not outside
          segments.push({
            type: 'transition-group',
            clips: [currentClip],
            startTime: currentClip.startTimeInSeconds, // Keep within clip timing boundaries
            hasOrphanedStart: !!hasOrphanedTransitionFrom,
            hasOrphanedEnd: !!hasOrphanedTransitionTo
          });
        } else {
          // No transitions, individual clip
          console.log(`🎬 Creating individual segment for ${currentClip.id}`);
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
        startTime: currentClip.startTimeInSeconds, // Keep within clip timing boundaries for orphaned transitions
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
  
  console.log(`🎬 Final segments created: ${segments.length} segments`);
  segments.forEach((segment, index) => {
    console.log(`🎬 Segment ${index}: type=${segment.type}, clips=[${segment.clips.map(c => c.id).join(', ')}], startTime=${segment.startTime}s`);
  });
  
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
  createExecutionContext,
  fps,
  videoConfig
}: {
  segment: ClipSegment;
  createExecutionContext: (clipStartTime: number) => BlueprintExecutionContext;
  fps: number;
  videoConfig: { width: number; height: number };
}) {
  const startFrame = Math.round(segment.startTime * fps);
  
  // Only log once per segment, not every frame
  if (startFrame === 0) {
    console.log(`🎬 SegmentRenderer: Processing segment type="${segment.type}" with ${segment.clips.length} clips: [${segment.clips.map(c => c.id).join(', ')}]`);
  }
  
  if (segment.type === 'individual') {
    // Render single clip at its specified time
    const clip = segment.clips[0];
    const durationInFrames = Math.round(
      (clip.endTimeInSeconds - clip.startTimeInSeconds) * fps
    );
    
    console.log(`🎬 SegmentRenderer (Individual Clip): Clip ID=${clip.id}, StartTime=${clip.startTimeInSeconds}s, EndTime=${clip.endTimeInSeconds}s, FromFrame=${startFrame}, DurationFrames=${durationInFrames}`);

    // Create execution context for individual clips
    const executionContext = createExecutionContext(clip.startTimeInSeconds);

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
    
    // Process clips (regular adjacent logic or single orphaned clip)
    if (segment.clips.length === 1 && (segment.hasOrphanedStart || segment.hasOrphanedEnd)) {
      if (startFrame === 0) {
        console.log(`🎬 SegmentRenderer: Taking ORPHANED transition path for single clip`);
      }
      // Single clip with orphaned transitions - use TransitionSeries with empty divs
      const clip = segment.clips[0];
      const clipDurationFrames = Math.round((clip.endTimeInSeconds - clip.startTimeInSeconds) * fps);
      
      // Calculate transition durations
      const transitionFromDuration = segment.hasOrphanedStart && clip.transitionFromPrevious
        ? Math.round(clip.transitionFromPrevious.durationInSeconds * fps)
        : 0;
      const transitionToDuration = segment.hasOrphanedEnd && clip.transitionToNext
        ? Math.round(clip.transitionToNext.durationInSeconds * fps)
        : 0;
      
      // Total duration includes ALL parts: transition from + clip + transition to
      totalDurationFrames = transitionFromDuration + clipDurationFrames + transitionToDuration;
      
      // Add empty div for transition from (if needed)
      if (segment.hasOrphanedStart && clip.transitionFromPrevious) {
        sequences.push(
          <TransitionSeries.Sequence 
            durationInFrames={transitionFromDuration}
          >
            <div style={{ width: '100%', height: '100%' }} />
          </TransitionSeries.Sequence>
        );
        
        sequences.push(
          <TransitionSeries.Transition
            presentation={getTransitionPresentation(clip.transitionFromPrevious, videoConfig)}
            timing={linearTiming({ durationInFrames: transitionFromDuration })}
          />
        );
      }
      
      // Add the main clip content
      const clipSequenceDuration = clipDurationFrames + transitionToDuration;
      // Create execution context for TransitionSeries clips
      const executionContext = createExecutionContext(clip.startTimeInSeconds);
      sequences.push(
        <TransitionSeries.Sequence 
          durationInFrames={clipSequenceDuration}
        >
          <ClipContentWithFreeze 
            clip={clip} 
            executionContext={executionContext} 
            freezeAfterFrames={clipDurationFrames}
            totalSequenceDuration={clipSequenceDuration}
          />
        </TransitionSeries.Sequence>
      );
      
      // Add transition to empty div (if needed)
      if (segment.hasOrphanedEnd && clip.transitionToNext) {
        sequences.push(
          <TransitionSeries.Transition
            presentation={getTransitionPresentation(clip.transitionToNext, videoConfig)}
            timing={linearTiming({ durationInFrames: transitionToDuration })}
          />
        );
        
        sequences.push(
          <TransitionSeries.Sequence 
            durationInFrames={transitionToDuration}
          >
            <div style={{ width: '100%', height: '100%' }} />
          </TransitionSeries.Sequence>
        );
      }
    } else {
      if (startFrame === 0) {
        console.log(`🎬 SegmentRenderer: Taking CROSS-TRANSITION path for ${segment.clips.length} clips`);
      }
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
        // Create execution context for TransitionSeries clips
        const executionContext = createExecutionContext(clip.startTimeInSeconds);
        sequences.push(
          <TransitionSeries.Sequence 
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
          const presentation = getTransitionPresentation(clip.transitionToNext!, videoConfig);
          if (startFrame === 0) {
            console.log(`🎬 Adding TransitionSeries.Transition after clip ${clip.id}, duration: ${transitionDuration} frames, presentation:`, presentation);
          }
          sequences.push(
            <TransitionSeries.Transition
              presentation={presentation}
              timing={linearTiming({ durationInFrames: transitionDuration })}
            />
          );
        }
      });
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
  transitionConfig: import('./BlueprintTypes').TransitionConfig,
  videoConfig: { width: number; height: number }
): any {
  const { width, height } = videoConfig;
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
  
  console.log(`🎬 ClipContent: Executed clip ${clip.id}, returned element:`, clipElement);

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
  
  // Simplest approach: extend the video duration from the start to avoid any jumps
  if (clip.element.includes('Video')) {
    const endAtMatch = clip.element.match(/endAtSeconds:\s*([0-9.]+)/);
    
    if (endAtMatch) {
      const originalEndTime = parseFloat(endAtMatch[1]);
      const fps = 30; // Assuming 30fps - should match your project settings
      const originalEndFrame = originalEndTime * fps;
      
      // If we need to extend beyond the original video duration, just repeat the last frame
      if (totalSequenceDuration > freezeAfterFrames) {
        const extensionFrames = totalSequenceDuration - freezeAfterFrames;
        const extensionSeconds = extensionFrames / fps;
        const newEndTime = originalEndTime + extensionSeconds;
        
        const extendedElement = clip.element.replace(
          /endAtSeconds:\s*[0-9.]+/,
          `endAtSeconds: ${newEndTime}`
        );
        
        console.log(`🎬 ClipContentWithFreeze: Extending ${clip.id} from ${originalEndTime}s to ${newEndTime}s (extension: ${extensionSeconds}s)`);
        return executeClipElement(extendedElement, executionContext);
      }
    }
  }
  
  // Normal rendering for non-video or no extension needed
  return executeClipElement(clip.element, executionContext);
}


