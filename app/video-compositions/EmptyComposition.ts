import type { CompositionBlueprint } from './BlueprintTypes';

/**
 * Empty composition blueprint with multiple empty tracks ready for content
 * This serves as the starting point for AI generation and manual editing
 * Now supports dynamic track count based on content needs
 */
export const emptyCompositionBlueprint: CompositionBlueprint = [];

/**
 * Ensure composition has minimum required tracks
 * Automatically expands to accommodate content without losing existing data
 */
export function ensureMinimumTracks(blueprint: CompositionBlueprint, minTracks: number = 4): CompositionBlueprint {
  const result = [...blueprint];
  
  // Add empty tracks if we don't have enough
  while (result.length < minTracks) {
    result.push({ clips: [] });
  }
  
  return result;
}
