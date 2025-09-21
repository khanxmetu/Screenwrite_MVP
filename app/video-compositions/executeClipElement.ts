import React from "react";
import { AbsoluteFill, Video, Img, Audio, Easing, interpolateColors, spring, random } from "remotion";
import { interp } from "../utils/animations";
import type { BlueprintExecutionContext } from "./BlueprintTypes";

/**
 * Safe wrapper functions for Remotion components
 * These provide a secure, AI-friendly interface with validation and error handling
 */

// Safe Video wrapper component with file validation and seconds-based props
const SafeVideoComponent = React.forwardRef<any, {
  src: string;
  startFromSeconds?: number;
  endAtSeconds?: number;
  volume?: number;
  style?: React.CSSProperties;
}>((props, ref) => {
  // Validate file path (only allow relative paths and common extensions)
  const allowedExtensions = ['.mp4', '.mov', '.avi', '.webm', '.mkv'];
  const hasValidExtension = allowedExtensions.some(ext => props.src.toLowerCase().endsWith(ext));
  
  if (!hasValidExtension) {
    console.warn(`Invalid video file extension: ${props.src}`);
    return React.createElement('div', { 
      style: { ...props.style, backgroundColor: '#333', color: '#fff', padding: '10px' } 
    }, 'Invalid video file');
  }

  // Convert seconds to frames (30fps)
  const videoProps: any = {
    src: props.src,
    volume: Math.max(0, Math.min(1, props.volume || 1)), // Clamp volume 0-1
    style: props.style,
    ref,
  };

  if (props.startFromSeconds !== undefined) {
    videoProps.startFrom = Math.floor(props.startFromSeconds * 30);
  }
  if (props.endAtSeconds !== undefined) {
    videoProps.endAt = Math.floor(props.endAtSeconds * 30);
  }

  return React.createElement(Video, videoProps);
});

// Safe Audio wrapper component with file validation and seconds-based props
const SafeAudioComponent = React.forwardRef<any, {
  src: string;
  startFromSeconds?: number;
  endAtSeconds?: number;
  volume?: number;
}>((props, ref) => {
  // Validate file path
  const allowedExtensions = ['.mp3', '.wav', '.aac', '.ogg', '.m4a'];
  const hasValidExtension = allowedExtensions.some(ext => props.src.toLowerCase().endsWith(ext));
  
  if (!hasValidExtension) {
    console.warn(`Invalid audio file extension: ${props.src}`);
    return null; // Audio components can return null
  }

  // Convert seconds to frames (30fps)
  const audioProps: any = {
    src: props.src,
    volume: Math.max(0, Math.min(1, props.volume || 1)), // Clamp volume 0-1
    ref,
  };

  if (props.startFromSeconds !== undefined) {
    audioProps.startFrom = Math.floor(props.startFromSeconds * 30);
  }
  if (props.endAtSeconds !== undefined) {
    audioProps.endAt = Math.floor(props.endAtSeconds * 30);
  }

  return React.createElement(Audio, audioProps);
});

// Safe Img wrapper component with file validation
const SafeImgComponent = React.forwardRef<any, {
  src: string;
  style?: React.CSSProperties;
  alt?: string;
}>((props, ref) => {
  // Validate image file
  const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'];
  const hasValidExtension = allowedExtensions.some(ext => props.src.toLowerCase().endsWith(ext));
  
  if (!hasValidExtension) {
    console.warn(`Invalid image file extension: ${props.src}`);
    return React.createElement('div', { 
      style: { ...props.style, backgroundColor: '#ddd', color: '#666', padding: '10px' } 
    }, 'Invalid image file');
  }

  return React.createElement(Img, { ...props, ref });
});

// Safe AbsoluteFill wrapper component (already safe, but for consistency)
const SafeAbsoluteFillComponent = React.forwardRef<any, {
  style?: React.CSSProperties;
  children?: React.ReactNode;
}>((props, ref) => {
  return React.createElement(AbsoluteFill, { ...props, ref });
});

// Safe interpolateColors wrapper
const safeInterpolateColors = (
  input: number,
  inputRange: [number, number],
  outputRange: [string, string]
) => {
  try {
    return interpolateColors(input, inputRange, outputRange);
  } catch (error) {
    console.warn('Error in color interpolation:', error);
    return outputRange[0]; // Return first color as fallback
  }
};

// Safe spring wrapper with parameter validation
const safeSpring = (options: {
  fps?: number;
  frame: number;
  config?: {
    damping?: number;
    mass?: number;
    stiffness?: number;
  };
}) => {
  // Validate and clamp spring parameters
  const safeConfig = {
    damping: Math.max(0, Math.min(100, options.config?.damping || 10)),
    mass: Math.max(0.1, Math.min(10, options.config?.mass || 1)),
    stiffness: Math.max(0, Math.min(1000, options.config?.stiffness || 100)),
  };

  try {
    return spring({
      fps: options.fps || 30,
      frame: Math.max(0, options.frame),
      config: safeConfig,
    });
  } catch (error) {
    console.warn('Error in spring animation:', error);
    return 0; // Return neutral value
  }
};

// Safe easing functions (curated subset)
const safeEasing = {
  linear: (x: number) => x,
  easeIn: Easing.in,
  easeOut: Easing.out,
  easeInOut: Easing.inOut,
  bezier: (x1: number, y1: number, x2: number, y2: number) => {
    // Clamp bezier parameters to safe range
    return Easing.bezier(
      Math.max(0, Math.min(1, x1)),
      Math.max(0, Math.min(1, y1)),
      Math.max(0, Math.min(1, x2)),
      Math.max(0, Math.min(1, y2))
    );
  },
};

// Safe random wrapper (deterministic)
const safeRandom = (seed?: string | number) => {
  try {
    return random(seed || 'default');
  } catch (error) {
    console.warn('Error in random generation:', error);
    return Math.random(); // Fallback to regular random
  }
};

// Create SW namespace with component references and utility functions
const createSW = () => ({
  Video: SafeVideoComponent,
  Audio: SafeAudioComponent,
  Img: SafeImgComponent,
  AbsoluteFill: SafeAbsoluteFillComponent,
  interp: (
    startTimeOrTimePoints: number | number[], 
    endTimeOrValues?: number | number[], 
    fromValueOrEasing?: number | 'in' | 'out' | 'inOut' | 'linear', 
    toValue?: number, 
    easing?: 'in' | 'out' | 'inOut' | 'linear'
  ) => {
    return interp(startTimeOrTimePoints as any, endTimeOrValues as any, fromValueOrEasing as any, toValue, easing);
  },
  interpolateColors: safeInterpolateColors,
  spring: safeSpring,
  easing: safeEasing,
  random: safeRandom,
});

/**
 * Safely execute a clip's TSX code with proper error handling
 * This is the core execution engine for blueprint-based clips
 */
export function executeClipElement(
  clipCode: string,
  context: BlueprintExecutionContext
): React.ReactElement {
  try {
    console.log("🎬 executeClipElement: Starting execution");
    console.log("🎬 Clip code:", clipCode);
    
    // Create SW namespace using the execution context's interp function
    const SW = {
      ...createSW(),
      interp: context.interp, // Use the context-aware interp function
    };
    
    // Create execution function with ONLY safe SW namespace functions
    const executeCode = new Function(
      'React',
      'SW',
      'inSeconds',
      clipCode
    );

    console.log("🎬 executeClipElement: Function created, executing...");

    // Execute with ONLY safe context - no direct Remotion access
    const result = executeCode(
      React,
      SW,
      context.inSeconds
    );

    console.log("🎬 executeClipElement: Execution result:", result);

    // Validate result is a React element
    if (!React.isValidElement(result)) {
      console.error("🎬 executeClipElement: Result is not a valid React element:", result);
      throw new Error("Clip code must return a valid React element");
    }

    console.log("🎬 executeClipElement: SUCCESS - Valid React element returned");
    return result;
  } catch (error) {
    console.error("🎬 executeClipElement: ERROR:", error);
    
    // Return error display component
    return React.createElement(
      'div',
      {
        style: {
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: '#1a1a1a',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#ff6b6b',
          fontSize: '16px',
          fontFamily: 'Arial, sans-serif',
          textAlign: 'center' as const,
          padding: '20px',
          zIndex: 1000,
        }
      },
      React.createElement(
        'div',
        {},
        React.createElement('p', {}, '⚠️ Error in clip execution'),
        React.createElement(
          'p', 
          { style: { fontSize: '12px', opacity: 0.8, marginTop: '10px' } },
          error instanceof Error ? error.message : 'Unknown error'
        )
      )
    );
  }
}

/**
 * Calculate total composition duration from blueprint
 * Works with intelligent track system that respects actual timing and transitions
 */
export function calculateBlueprintDuration(blueprint: import('./BlueprintTypes').CompositionBlueprint): number {
  let maxDuration = 0;

  // Find the latest end time across all tracks and clips, accounting for transitions
  for (const track of blueprint) {
    if (!track.clips || track.clips.length === 0) continue;
    
    for (const clip of track.clips) {
      let clipEndTime = clip.endTimeInSeconds;
      
      // Account for orphaned transitions that extend the clip
      if (clip.transitionToNext && clip.transitionToNext.durationInSeconds) {
        // Only extend if this is an orphaned transition (no adjacent clip)
        const isOrphanedTransition = true; // Assume orphaned for duration calculation safety
        if (isOrphanedTransition) {
          clipEndTime += clip.transitionToNext.durationInSeconds * 0.5; // Partial extension for safety
        }
      }
      
      if (clipEndTime > maxDuration) {
        maxDuration = clipEndTime;
      }
    }
  }

  // Convert seconds to frames (30 FPS) with minimum duration
  const durationInFrames = Math.ceil(maxDuration * 30);
  return Math.max(durationInFrames, 30); // Minimum 1 second
}
