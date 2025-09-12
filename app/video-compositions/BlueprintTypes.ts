// Blueprint-based composition system interfaces
// Based on the user's architectural design for structured video composition

export interface CompositionBlueprint {
  tracks: Track[];
  backgroundColor?: string;
  fps?: number;
}

export interface Track {
  id: string;
  clips: Clip[];
  // Track-level properties can be added here (volume, opacity, etc.)
}

export interface Clip {
  id: string;
  startTime: number; // in seconds
  duration: number;  // in seconds
  code: string;      // TSX code to execute for this clip
  type?: 'sequential' | 'overlay'; // Default: 'overlay'
  transition?: {
    type: 'fade' | 'slide' | 'scale' | 'none';
    duration: number; // in seconds
  };
}

// For sequential rendering (one clip after another with transitions)
export interface TransitionSeries {
  clips: Clip[];
  defaultTransition?: {
    type: 'fade' | 'slide' | 'scale' | 'none';
    duration: number;
  };
}

// For overlay rendering (clips stacked on top of each other)
export interface Sequence {
  clips: Clip[];
}

// Helper types for rendering modes
export type RenderingMode = 'blueprint' | 'string';

export interface BlueprintExecutionContext {
  // Helper functions available to clip code
  interp: (startTime: number, endTime: number, fromValue: number, toValue: number, easing?: 'linear' | 'in' | 'out' | 'inOut') => number;
  inSeconds: (seconds: number) => number;
  // Add more helper functions as needed
}
