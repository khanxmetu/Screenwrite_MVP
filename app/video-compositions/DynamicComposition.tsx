import React, { useState, useEffect } from "react";
import * as Remotion from "remotion";
import { Player, type PlayerRef } from "@remotion/player";
import * as Transitions from "@remotion/transitions";
import { fixCode, type CodeFixRequest } from "../utils/api";

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
  backgroundColor?: string;
  fps?: number;
  onCodeFixed?: (fixedCode: string) => void; // Callback to update the parent with fixed code
}

// Dynamic composition that executes AI-generated TSX code
export function DynamicComposition({
  tsxCode,
  backgroundColor = "#000000",
  onCodeFixed,
}: DynamicCompositionProps) {
  const frame = useCurrentFrame();
  const [isFixingError, setIsFixingError] = useState(false);
  const [currentCode, setCurrentCode] = useState(tsxCode);
  const [fixAttempts, setFixAttempts] = useState(0);
  const maxFixAttempts = 2; // Limit retry attempts

  // Update current code when tsxCode prop changes
  useEffect(() => {
    setCurrentCode(tsxCode);
    setFixAttempts(0); // Reset attempts when new code arrives
  }, [tsxCode]);

  // Function to attempt automatic error correction
  const attemptErrorFix = async (error: Error, brokenCode: string) => {
    if (fixAttempts >= maxFixAttempts || isFixingError) {
      console.log('Max fix attempts reached or already fixing, showing error');
      return null;
    }

    setIsFixingError(true);
    setFixAttempts(prev => prev + 1);

    try {
      console.log('🔧 Attempting automatic error correction...');
      
      const fixRequest: CodeFixRequest = {
        broken_code: brokenCode,
        error_message: error.message,
        error_stack: error.stack || '',
        user_request: 'Auto-fix broken composition code', // Generic request since we don't have original context
        media_library: [] // Could be passed from parent if needed
      };

      const fixResponse = await fixCode(fixRequest);

      if (fixResponse.success && fixResponse.corrected_code !== brokenCode) {
        console.log('✅ Code fixed successfully, applying correction...');
        setCurrentCode(fixResponse.corrected_code);
        
        // Notify parent component of the fix
        if (onCodeFixed) {
          onCodeFixed(fixResponse.corrected_code);
        }
        
        return fixResponse.corrected_code;
      } else {
        console.log('❌ Error correction failed or no changes made');
        return null;
      }
    } catch (fixError) {
      console.error('Error during automatic correction:', fixError);
      return null;
    } finally {
      setIsFixingError(false);
    }
  };

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
            <p>AI Composition Mode</p>
            <p style={{ fontSize: "16px", opacity: 0.7, marginTop: "10px" }}>
              Describe what you want to see and AI will generate Remotion code
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
      
      // Destructure everything from Remotion
      const {
        AbsoluteFill,
        interpolate,
        Sequence,
        Img,
        Video,
        Audio,
        spring,
        Easing,
        // Add more as needed
      } = Remotion;
      
      // Destructure transitions
      const { fade, iris, wipe, flip, slide } = Transitions;
      
      // Safe interpolate wrapper that sorts inputRange and removes duplicates
      const safeInterpolate = (frame, inputRange, outputRange, options = {}) => {
        // Create paired array of [input, output] to maintain correspondence
        const paired = inputRange.map((input, index) => ({
          input: input,
          output: outputRange[index] !== undefined ? outputRange[index] : outputRange[outputRange.length - 1]
        }));
        
        // Remove duplicates based on input values
        const uniquePaired = [];
        const seenInputs = new Set();
        
        for (const pair of paired) {
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
      
      // Create helper functions that use the passed values
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

    // If we're currently fixing an error, show loading state
    if (isFixingError) {
      return (
        <AbsoluteFill style={{ backgroundColor: "#1a1a1a" }}>
          <div
            style={{
              width: "100%",
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#4CAF50",
              fontSize: "18px",
              fontFamily: "Arial, sans-serif",
              textAlign: "center",
              padding: "40px",
            }}
          >
            <div>
              <p>🔧 Fixing code automatically...</p>
              <p style={{ fontSize: "14px", opacity: 0.8, marginTop: "10px" }}>
                AI is correcting the error, please wait
              </p>
            </div>
          </div>
        </AbsoluteFill>
      );
    }

    // Attempt automatic error correction
    if (error instanceof Error && fixAttempts < maxFixAttempts) {
      attemptErrorFix(error, currentCode);
      
      // Show loading state while fixing
      return (
        <AbsoluteFill style={{ backgroundColor: "#1a1a1a" }}>
          <div
            style={{
              width: "100%",
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#4CAF50",
              fontSize: "18px",
              fontFamily: "Arial, sans-serif",
              textAlign: "center",
              padding: "40px",
            }}
          >
            <div>
              <p>🔧 Fixing code automatically...</p>
              <p style={{ fontSize: "14px", opacity: 0.8, marginTop: "10px" }}>
                Attempt {fixAttempts + 1} of {maxFixAttempts}
              </p>
            </div>
          </div>
        </AbsoluteFill>
      );
    }

    // Show error if auto-fix failed or max attempts reached
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
            {fixAttempts >= maxFixAttempts && (
              <p style={{ fontSize: "12px", opacity: 0.6, marginTop: "10px" }}>
                Auto-fix attempts exhausted
              </p>
            )}
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
  compositionWidth,
  compositionHeight,
  backgroundColor = "#000000",
  playerRef,
  durationInFrames = 300, // Default 10 seconds at 30fps
  onCodeFixed,
}: DynamicVideoPlayerProps) {
  console.log("DynamicVideoPlayer - TSX Code length:", tsxCode?.length || 0);

  return (
    <Player
      ref={playerRef}
      component={DynamicComposition}
      inputProps={{
        tsxCode,
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
