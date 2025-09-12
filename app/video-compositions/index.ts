// Blueprint architecture exports
// Main entry point for the new blueprint-based composition system

export type {
  CompositionBlueprint,
  Track,
  Clip,
  TransitionSeries,
  Sequence,
  RenderingMode,
  BlueprintExecutionContext
} from './BlueprintTypes';

export {
  BlueprintComposition,
  renderTransitionSeries,
  renderSequence
} from './BlueprintComposition';

export {
  executeClipElement,
  calculateBlueprintDuration
} from './executeClipElement';

export {
  TestBlueprintComposition,
  sampleBlueprint
} from './TestBlueprint';

// Enhanced DynamicComposition with blueprint support
export {
  DynamicComposition,
  DynamicVideoPlayer
} from './DynamicComposition';

export type {
  DynamicCompositionProps,
  DynamicVideoPlayerProps
} from './DynamicComposition';
