// Blueprint-based composition system interfaces
// Updated to match proper Remotion TransitionSeries implementation

export interface Clip {
  id: string;
  startTimeInSeconds: number;
  endTimeInSeconds: number;
  element: string; // The string of code to be executed for the visual content
  transitionToNext?: {
    type: 'fade'; // For now, we'll just support fade
    durationInSeconds: number;
  };
  transitionFromPrevious?: {
    type: 'fade'; // For now, we'll just support fade
    durationInSeconds: number;
  };
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
