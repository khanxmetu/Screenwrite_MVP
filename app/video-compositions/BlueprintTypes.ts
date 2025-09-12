// Blueprint-based composition system interfaces
// Updated to match proper Remotion TransitionSeries implementation

// Available transition types from Remotion
export type TransitionType = 
  | 'fade'
  | 'slide'
  | 'wipe' 
  | 'flip'
  | 'clockWipe'
  | 'iris';

// Direction options for slide and flip transitions
export type SlideFlipDirection = 'from-left' | 'from-right' | 'from-top' | 'from-bottom';

// Direction options for wipe transitions (includes diagonals)
export type WipeDirection = 
  | 'from-left'
  | 'from-right' 
  | 'from-top'
  | 'from-bottom'
  | 'from-top-left'
  | 'from-top-right'
  | 'from-bottom-left'
  | 'from-bottom-right';

// Union of all possible directions
export type TransitionDirection = SlideFlipDirection | WipeDirection;

export interface TransitionConfig {
  type: TransitionType;
  durationInSeconds: number;
  direction?: TransitionDirection; // For slide, wipe, flip transitions
  perspective?: number; // For flip transitions (default: 1000)
}

export interface Clip {
  id: string;
  startTimeInSeconds: number;
  endTimeInSeconds: number;
  element: string; // The string of code to be executed for the visual content
  transitionToNext?: TransitionConfig;
  transitionFromPrevious?: TransitionConfig;
}

export interface Track {
  clips: Clip[];
}

export type CompositionBlueprint = Track[];

// Helper types for rendering modes
export type RenderingMode = 'blueprint' | 'string';

export interface BlueprintExecutionContext {
  // Helper functions available to clip code
  interp: (startTime: number, endTime: number, fromValue: number, toValue: number, easing?: 'linear' | 'in' | 'out' | 'inOut') => number;
  inSeconds: (seconds: number) => number;
  // Add more helper functions as needed
}
