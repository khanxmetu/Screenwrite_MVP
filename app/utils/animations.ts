import { interpolate, useCurrentFrame, useVideoConfig, Easing } from 'remotion';

type EasingType = 'in' | 'out' | 'inOut' | 'linear';

/**
 * Enhanced interpolation wrapper for animations
 * Supports both simple two-point interpolation and multi-keyframe animations
 * 
 * Simple syntax:
 * @param startTime - When to start the animation (in seconds, relative to sequence start)
 * @param endTime - When to end the animation (in seconds, relative to sequence start) 
 * @param fromValue - Starting value
 * @param toValue - Ending value
 * @param easing - Easing type: 'linear', 'in', 'out', 'inOut' (default: 'out')
 * 
 * Keyframe syntax:
 * @param timePoints - Array of time points in seconds [t1, t2, t3, ...]
 * @param values - Array of corresponding values [v1, v2, v3, ...]
 * @param easing - Easing type (optional, third parameter)
 * 
 * @returns Interpolated value for current frame
 */
export function interp(
  startTimeOrTimePoints: number | number[],
  endTimeOrValues: number | number[], 
  fromValueOrEasing?: number | EasingType,
  toValue?: number,
  easing: EasingType = 'out'
): number {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Handle keyframe syntax: interp([0, 2, 3, 4], [0, 1, 1, 0], 'linear')
  if (Array.isArray(startTimeOrTimePoints)) {
    const timePoints = startTimeOrTimePoints;
    const values = endTimeOrValues as number[];
    const easingType = (fromValueOrEasing as EasingType) || 'out';
    
    if (!Array.isArray(values) || timePoints.length !== values.length) {
      throw new Error('Time points and values arrays must have the same length');
    }
    
    // Convert time points to frames
    const framePoints = timePoints.map(t => t * fps);
    
    let easingFunction = getEasingFunction(easingType);
    
    return interpolate(
      frame,
      framePoints,
      values,
      {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
        easing: easingFunction,
      }
    );
  }
  
  // Handle simple syntax: interp(0, 2, 0, 1, 'linear')
  const startTime = startTimeOrTimePoints as number;
  const endTime = endTimeOrValues as number;
  const fromValue = fromValueOrEasing as number;
  const finalEasing = easing;
  
  // Convert seconds to frames (sequence-relative)
  const startFrame = startTime * fps;
  const endFrame = endTime * fps;
  
  let easingFunction = getEasingFunction(finalEasing);
  
  return interpolate(
    frame,
    [startFrame, endFrame],
    [fromValue, toValue!],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: easingFunction,
    }
  );
}

function getEasingFunction(easingType: EasingType) {
  switch (easingType) {
    case 'linear':
      return undefined; // Linear is default
    case 'in':
      return Easing.ease;
    case 'inOut':
      return Easing.bezier(0.42, 0, 0.58, 1);
    default: // 'out'
      return Easing.out(Easing.quad);
  }
}
