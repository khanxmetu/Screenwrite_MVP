import type { CompositionBlueprint } from "../../video-compositions/BlueprintTypes";
import type { TimelineRow, TimelineAction, TimelineEffect } from "@xzdarcy/react-timeline-editor";

/**
 * Converts a CompositionBlueprint to TimelineState for read-only visualization
 * Maps Blueprint clips to timeline scrubbers and transitions
 */
export function blueprintToTimelineState(blueprint: CompositionBlueprint): TimelineState {
  console.log("🎬 Converting blueprint to timeline state:", blueprint);
  
  // Process each track in the blueprint
  blueprint.forEach((track, trackIndex) => {
    console.log(`🎵 Processing track ${trackIndex} with ${track.clips.length} clips:`, track.clips);
    const scrubbers: ScrubberState[] = [];
    const transitions: Transition[] = [];

    track.clips.forEach((clip, clipIndex) => {
      console.log(`  🎥 Processing clip ${clipIndex}:`, clip);
      
      // Create scrubber for this clip
      const scrubber: ScrubberState = {
        // Base scrubber properties
        id: clip.id,
        mediaType: "element", // Our clips are React elements
        mediaUrlLocal: null,
        mediaUrlRemote: null,
        media_width: 1920, // Default composition dimensions
        media_height: 1080,
        element: clip.element, // Our React element code
        text: null,
        left_transition_id: null,
        right_transition_id: null,

        // Media bin properties
        name: `Clip ${clipIndex + 1}`,
        durationInSeconds: clip.endTimeInSeconds - clip.startTimeInSeconds,
        uploadProgress: null,
        isUploading: false,
        gemini_file_id: null,

        // Timeline position properties
        left: clip.startTimeInSeconds * PIXELS_PER_SECOND,
        y: trackIndex,
        width: (clip.endTimeInSeconds - clip.startTimeInSeconds) * PIXELS_PER_SECOND,
        sourceMediaBinId: clip.id,

        // Player properties (default values for read-only)
        left_player: 0,
        top_player: 0,
        width_player: 1920,
        height_player: 1080,
        is_dragging: false,

        // Trim properties
        trimBefore: null,
        trimAfter: null,
      };

      // Handle transitions
      if (clip.transitionToNext) {
        const transitionId = `transition-${clip.id}-to-next`;
        const transition: Transition = {
          id: transitionId,
          presentation: mapTransitionType(clip.transitionToNext.type),
          timing: "linear", // Default to linear for now
          durationInFrames: Math.round(clip.transitionToNext.durationInSeconds * FPS),
          leftScrubberId: clip.id,
          rightScrubberId: null, // Will be set when processing next clip
        };

        // Set the right transition ID on current scrubber
        scrubber.right_transition_id = transitionId;
        transitions.push(transition);
      }

      if (clip.transitionFromPrevious) {
        const transitionId = `transition-prev-to-${clip.id}`;
        // Set the left transition ID on current scrubber
        scrubber.left_transition_id = transitionId;
      }

      scrubbers.push(scrubber);
      console.log(`  ✅ Created scrubber:`, scrubber);
    });

    console.log(`🎵 Track ${trackIndex} final: ${scrubbers.length} scrubbers, ${transitions.length} transitions`);

    // Connect transition right scrubber IDs
    transitions.forEach((transition) => {
      if (transition.leftScrubberId) {
        const leftScrubberIndex = scrubbers.findIndex(s => s.id === transition.leftScrubberId);
        if (leftScrubberIndex >= 0 && leftScrubberIndex < scrubbers.length - 1) {
          transition.rightScrubberId = scrubbers[leftScrubberIndex + 1].id;
        }
      }
    });

    return {
      id: `track-${trackIndex}`,
      scrubbers,
      transitions,
    };
  });

  console.log("🎬 Final timeline state:", { tracks });
  return { tracks };
}

/**
 * Maps our Blueprint transition types to Kimu's timeline transition types
 */
function mapTransitionType(blueprintType: string): "fade" | "wipe" | "clockWipe" | "slide" | "flip" | "iris" {
  const typeMap: Record<string, "fade" | "wipe" | "clockWipe" | "slide" | "flip" | "iris"> = {
    fade: "fade",
    slide: "slide", 
    wipe: "wipe",
    flip: "flip",
    clockWipe: "clockWipe",
    iris: "iris",
  };
  
  return typeMap[blueprintType] || "fade"; // Default to fade if unknown
}

/**
 * Calculates the total duration of a blueprint in seconds
 */
export function calculateBlueprintDurationInSeconds(blueprint: CompositionBlueprint): number {
  let maxEndTime = 0;

  blueprint.forEach(track => {
    track.clips.forEach(clip => {
      if (clip.endTimeInSeconds > maxEndTime) {
        maxEndTime = clip.endTimeInSeconds;
      }
    });
  });

  return maxEndTime;
}

/**
 * Gets timeline width in pixels based on blueprint duration
 */
export function getTimelineWidthFromBlueprint(blueprint: CompositionBlueprint): number {
  const durationInSeconds = calculateBlueprintDurationInSeconds(blueprint);
  return Math.max(durationInSeconds * PIXELS_PER_SECOND, 1000); // Minimum 1000px width
}
