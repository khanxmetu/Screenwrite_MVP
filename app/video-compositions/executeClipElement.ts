import React from "react";
import { AbsoluteFill, Video, Img, Audio } from "remotion";
import { interp } from "../utils/animations";
import type { BlueprintExecutionContext } from "./BlueprintTypes";

/**
 * Safely execute a clip's TSX code with proper error handling
 * This is the core execution engine for blueprint-based clips
 */
export function executeClipElement(
  clipCode: string,
  context: BlueprintExecutionContext
): React.ReactElement {
  try {
    console.log("Executing clip code:", clipCode.slice(0, 100) + "...");

    // Mock require function for common Remotion components
    const mockRequire = (moduleName: string) => {
      if (moduleName === 'remotion') {
        return { Video, Img, Audio, AbsoluteFill };
      }
      return {};
    };

    // Create execution function with clip code and make Remotion components available
    const executeCode = new Function(
      'React',
      'AbsoluteFill', 
      'interp',
      'inSeconds',
      'require', // Add require function for dynamic imports in clips
      clipCode
    );

    // Execute with context
    const result = executeCode(
      React,
      AbsoluteFill,
      context.interp,
      context.inSeconds,
      mockRequire
    );

    // Validate result is a React element
    if (!React.isValidElement(result)) {
      throw new Error("Clip code must return a valid React element");
    }

    return result;
  } catch (error) {
    console.error("Error executing clip code:", error);
    
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
 */
export function calculateBlueprintDuration(tracks: import('./BlueprintTypes').Track[]): number {
  let maxDuration = 0;

  for (const track of tracks) {
    for (const clip of track.clips) {
      const clipEnd = clip.startTime + clip.duration;
      if (clipEnd > maxDuration) {
        maxDuration = clipEnd;
      }
    }
  }

  // Convert seconds to frames (30 FPS)
  return Math.ceil(maxDuration * 30);
}
