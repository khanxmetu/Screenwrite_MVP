import { interpolate, useCurrentFrame, useVideoConfig, Easing } from 'remotion';

type EasingType = 'in' | 'out' | 'inOut' | 'linear';

/**
 * Simple interpolation wrapper for animations
 * Works with sequence-relative timing - no context adjustments needed
 * 
 * @param startTime - When to start the animation (in seconds, relative to sequence start)
 * @param endTime - When to end the animation (in seconds, relative to sequence start) 
 * @param fromValue - Starting value
 * @param toValue - Ending value
 * @param easing - Easing type: 'linear', 'in', 'out', 'inOut' (default: 'out')
 * @returns Interpolated value for current frame
 */
export function interp(
  startTime: number,
  endTime: number, 
  fromValue: number,
  toValue: number,
  easing: EasingType = 'out'
): number {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Convert seconds to frames (sequence-relative)
  const startFrame = startTime * fps;
  const endFrame = endTime * fps;
  
  let easingFunction;
  switch (easing) {
    case 'linear':
      easingFunction = undefined; // Linear is default
      break;
    case 'in':
      easingFunction = Easing.ease;
      break;
    case 'inOut':
      easingFunction = Easing.bezier(0.42, 0, 0.58, 1);
      break;
    default: // 'out'
      easingFunction = Easing.out(Easing.quad);
      break;
  }
  
  return interpolate(
    frame,
    [startFrame, endFrame],
    [fromValue, toValue],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: easingFunction,
    }
  );
}
