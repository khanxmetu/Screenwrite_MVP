// Blueprint architecture exports - Clean minimal setup
// Main entry point for the blueprint-based composition system

// Core Blueprint Types and Interfaces
export type {
  CompositionBlueprint,
  Track,
  Clip,
  TransitionSeries,
  Sequence,
  RenderingMode,
  BlueprintExecutionContext
} from './BlueprintTypes';

// Blueprint Composition System
export {
  BlueprintComposition,
  renderTransitionSeries,
  renderSequence
} from './BlueprintComposition';

// Execution Engine
export {
  executeClipElement,
  calculateBlueprintDuration
} from './executeClipElement';

// Enhanced Dynamic Composition (supports both string and blueprint modes)
export {
  DynamicComposition,
  DynamicVideoPlayer
} from './DynamicComposition';

export type {
  DynamicCompositionProps,
  DynamicVideoPlayerProps
} from './DynamicComposition';

// Test Data and Examples
export {
  TestBlueprintComposition,
  sampleBlueprint
} from './TestBlueprint';

// Standalone Preview System (existing)
export {
  StandalonePreviewComposition,
  StandaloneVideoPlayer
} from './StandalonePreview';

export type {
  PreviewContent,
  PreviewCompositionProps,
  StandaloneVideoPlayerProps
} from './StandalonePreview';

// Timeline Video Player (existing)
export {
  TimelineComposition,
  VideoPlayer
} from './VideoPlayer';

export type {
  VideoPlayerProps
} from './VideoPlayer';
