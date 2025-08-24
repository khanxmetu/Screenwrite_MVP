import React, { useState, useEffect } from "react";
import * as Remotion from "remotion";
import { Player, type PlayerRef } from "@remotion/player";
import * as Transitions from "@remotion/transitions";
import { getSampleCode } from "~/utils/sampleCodeLoader";

// Destructure commonly used components for convenience
const { 
  AbsoluteFill, 
  useCurrentFrame, 
  interpolate, 
  Sequence, 
  Img, 
  Video, 
  Audio, 
  spring, 
  useVideoConfig,
  useCurrentScale,
  Easing
} = Remotion;

export interface DynamicCompositionProps {
  tsxCode: string;
  useSampleCode?: boolean; // When true, load from test file
  backgroundColor?: string;
  fps?: number;
}

// Dynamic composition that executes AI-generated TSX code
export function DynamicComposition({
  tsxCode,
  useSampleCode = false,
  backgroundColor = "#000000",
}: DynamicCompositionProps) {
  const frame = useCurrentFrame();
  const [currentCode, setCurrentCode] = useState(tsxCode);
  const [sampleCode, setSampleCode] = useState<string>('');

  // Load sample code from test file when needed
  useEffect(() => {
    if (useSampleCode && !sampleCode) {
      try {
        const loadedCode = getSampleCode();
        console.log('📁 Loaded sample code from file system');
        setSampleCode(loadedCode);
      } catch (error) {
        console.error('❌ Failed to load sample code:', error);
        // Fallback to embedded simple code
        setSampleCode(`
const frame = currentFrameValue;
const { width, height, fps } = videoConfigValue;

const opacity = interpolate(frame, [0, 30, 270, 300], [0, 1, 1, 0]);
const scale = interpolate(frame, [0, 60, 240, 300], [0.5, 1.2, 1.2, 0.5]);
const rotation = interpolate(frame, [0, 300], [0, 360]);

return React.createElement(AbsoluteFill, {
  style: {
    backgroundColor: '#2563eb',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    opacity: opacity
  }
}, React.createElement('div', {
  style: {
    transform: 'scale(' + scale + ') rotate(' + rotation + 'deg)',
    color: 'white',
    fontSize: '48px',
    fontWeight: 'bold',
    textAlign: 'center',
    padding: '20px',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    border: '2px solid rgba(255, 255, 255, 0.3)'
  }
}, 'Sample Mode Active'));
        `);
      }
    }
  }, [useSampleCode, sampleCode]);

  // Update current code when tsxCode prop changes or sample mode changes
  useEffect(() => {
    if (useSampleCode && sampleCode) {
      setCurrentCode(sampleCode);
    } else {
      setCurrentCode(tsxCode);
    }
  }, [tsxCode, useSampleCode, sampleCode]);

  // If no TSX code, show placeholder
  if (!currentCode) {
    return (
      <AbsoluteFill style={{ backgroundColor }}>
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "white",
            fontSize: "24px",
            fontFamily: "Arial, sans-serif",
          }}
        >
          <div style={{ textAlign: "center" }}>
            <p>{useSampleCode ? "🧪 Sample Mode" : "🤖 AI Composition Mode"}</p>
            <p style={{ fontSize: "16px", opacity: 0.7, marginTop: "10px" }}>
              {useSampleCode 
                ? "Loading structured animation patterns..." 
                : "Describe what you want to see and AI will generate Remotion code"
              }
            </p>
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  // Execute the AI-generated TSX code
  try {
    console.log('Executing AI-generated code directly:', currentCode.slice(0, 200) + '...');

    // Call hooks at component level (Rules of Hooks)
    const frame = useCurrentFrame();
    const videoConfig = useVideoConfig();
    const currentScale = useCurrentScale();

    // Apply safeInterpolate wrapper to prevent monotonic errors
    const safeCode = currentCode.replace(/\binterpolate\b/g, 'safeInterpolate');
    
    // Log if we're applying safe interpolation
    if (safeCode !== currentCode) {
      console.log('🛡️ Applied safeInterpolate wrapper to prevent monotonic errors');
    }

    // Debug: Log the code being executed
    console.log('🔍 Code to execute (first 500 chars):', safeCode.substring(0, 500));
    console.log('🔍 Code contains "<":', safeCode.includes('<'));
    
    if (safeCode.includes('<')) {
      console.error('❌ Found "<" character in code at positions:', 
        [...safeCode.matchAll(/</g)].map(match => match.index)
      );
    }

    // Create a function that evaluates the JavaScript code that returns JSX
    const executeCode = new Function(
      'React',
      'Remotion', // Pass entire Remotion namespace
      'Transitions', // Pass entire Transitions namespace
      'currentFrameValue', // Renamed to avoid conflicts
      'videoConfigValue', // Renamed to avoid conflicts
      'currentScaleValue', // Renamed to avoid conflicts
      'Player',
      `
      // Available components and functions
      const { createElement } = React;
      
      // Destructure components and utilities from Remotion - avoid duplicates
      const {
        AbsoluteFill,
        interpolate,
        spring,
        Sequence,
        Img,
        Video,
        Audio,
        Easing,
        // Animation utilities
        continueRender,
        delayRender,
        // Composition utilities
        Composition,
        Folder,
        Still,
        // Audio utilities
        getAudioData,
        getAudioDurationInSeconds,
        // Video utilities
        getVideoMetadata,
        // Math utilities
        random,
        // Layout utilities
        Loop,
        Series
      } = Remotion;
      
      // Destructure transitions
      const { fade, iris, wipe, flip, slide } = Transitions;
      
      // Safe interpolate wrapper that handles duplicates, sorting, and NaN values
      const safeInterpolate = (frame, inputRange, outputRange, options = {}) => {
        // Create paired array of [input, output] to maintain correspondence
        const paired = inputRange.map((input, index) => ({
          input: input,
          output: outputRange[index] !== undefined ? outputRange[index] : outputRange[outputRange.length - 1]
        }));
        
        // Filter out NaN and invalid values
        const validPaired = paired.filter(pair => 
          !isNaN(pair.input) && isFinite(pair.input) && 
          !isNaN(pair.output) && isFinite(pair.output)
        );
        
        // Log when we filter invalid values
        if (validPaired.length !== paired.length) {
          console.log('🛡️ safeInterpolate: Filtered out NaN/invalid values:', 
            paired.filter(pair => isNaN(pair.input) || !isFinite(pair.input) || isNaN(pair.output) || !isFinite(pair.output))
          );
        }
        
        // If no valid values, return a safe default
        if (validPaired.length === 0) {
          console.warn('🛡️ safeInterpolate: No valid values, returning 0');
          return 0;
        }
        
        // Remove duplicates based on input values
        const uniquePaired = [];
        const seenInputs = new Set();
        
        for (const pair of validPaired) {
          if (!seenInputs.has(pair.input)) {
            seenInputs.add(pair.input);
            uniquePaired.push(pair);
          }
        }
        
        // Sort by input values
        uniquePaired.sort((a, b) => a.input - b.input);
        
        // If we only have one unique value, create a minimal valid range
        if (uniquePaired.length === 1) {
          const singleValue = uniquePaired[0];
          return interpolate(
            frame,
            [singleValue.input, singleValue.input + 1],
            [singleValue.output, singleValue.output],
            options
          );
        }
        
        // Extract sorted arrays
        const safeInputRange = uniquePaired.map(pair => pair.input);
        const safeOutputRange = uniquePaired.map(pair => pair.output);
        
        return interpolate(frame, safeInputRange, safeOutputRange, options);
      };
      
      // Create helper functions that use the passed values (avoiding hook duplication)
      const useCurrentFrame = () => currentFrameValue;
      const useVideoConfig = () => videoConfigValue;
      const useCurrentScale = () => currentScaleValue;
      
      // Execute the AI-generated code with safe interpolation
      ${safeCode}
      `
    );

    const generatedJSX = executeCode(
      React,
      Remotion, // Pass entire namespace
      Transitions, // Pass entire namespace
      frame, // Pass the actual frame value
      videoConfig, // Pass the config object
      currentScale, // Pass the scale value
      Player
    );

    return generatedJSX;
  } catch (error) {
    console.error("Error executing AI-generated code:", error);

    // Show simple error message
    return (
      <AbsoluteFill style={{ backgroundColor: "#1a1a1a" }}>
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#ff6b6b",
            fontSize: "18px",
            fontFamily: "Arial, sans-serif",
            textAlign: "center",
            padding: "40px",
          }}
        >
          <div>
            <p>⚠️ Error in AI-generated code</p>
            <p style={{ fontSize: "14px", opacity: 0.8, marginTop: "10px" }}>
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
            <p style={{ fontSize: "12px", opacity: 0.6, marginTop: "20px" }}>
              Try rephrasing your request or ask for something simpler
            </p>
          </div>
        </div>
      </AbsoluteFill>
    );
  }
}

// Props for the dynamic video player
export interface DynamicVideoPlayerProps {
  tsxCode: string;
  useSampleCode?: boolean; // When true, load from test file instead of tsxCode
  compositionWidth: number;
  compositionHeight: number;
  backgroundColor?: string;
  playerRef?: React.Ref<PlayerRef>;
  durationInFrames?: number;
  onCodeFixed?: (fixedCode: string) => void; // Callback for when code is automatically fixed
}

// The dynamic video player component
export function DynamicVideoPlayer({
  tsxCode,
  useSampleCode = false,
  compositionWidth,
  compositionHeight,
  backgroundColor = "#000000",
  playerRef,
  durationInFrames = 300, // Default 10 seconds at 30fps
  onCodeFixed,
}: DynamicVideoPlayerProps) {
  console.log("DynamicVideoPlayer - TSX Code length:", tsxCode?.length || 0);
  console.log("DynamicVideoPlayer - Use Sample Code:", useSampleCode);

  return (
    <Player
      ref={playerRef}
      component={DynamicComposition}
      inputProps={{
        tsxCode,
        useSampleCode,
        backgroundColor,
        onCodeFixed,
      }}
      durationInFrames={durationInFrames}
      compositionWidth={compositionWidth}
      compositionHeight={compositionHeight}
      fps={30}
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
        zIndex: 1,
      }}
      acknowledgeRemotionLicense
    />
  );
}
