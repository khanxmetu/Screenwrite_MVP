import type { CompositionBlueprint } from './BlueprintTypes';

/**
 * Empty composition blueprint with one track and no clips
 * This serves as the starting point for AI generation
 */
export const emptyCompositionBlueprint: CompositionBlueprint = [
  {
    clips: [] // Empty track ready for AI to add clips
  }
];
