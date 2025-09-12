// Test generated code using the new animation syntax
const generatedAnimationCode = `
import React from "react";
import { AbsoluteFill } from "remotion";
import { Animated, Move, Scale, Fade, Rotate } from "./SimpleAnimated";

export function GeneratedTestComposition() {
  return (
    <AbsoluteFill style={{ backgroundColor: "#0f0f0f" }}>
      {/* Title with entrance animation */}
      <Animated
        animations={[
          Move({ y: -50, start: 0, duration: 30 }),
          Fade({ from: 0, to: 1, start: 0, duration: 30 }),
          Scale({ from: 0.8, to: 1, start: 15, duration: 15 })
        ]}
        style={{
          position: "absolute",
          top: "25%",
          left: "50%",
          transform: "translateX(-50%)",
          color: "#FFD93D",
          fontSize: "48px",
          fontWeight: "bold",
          textAlign: "center",
        }}
      >
        Welcome to Screenwrite
      </Animated>

      {/* Subtitle with delayed entrance */}
      <Animated
        animations={[
          Fade({ from: 0, to: 1, start: 60, duration: 45 }),
          Move({ x: -30, start: 60, duration: 45 })
        ]}
        style={{
          position: "absolute",
          top: "40%",
          left: "50%",
          transform: "translateX(-50%)",
          color: "#6BCF7F",
          fontSize: "24px",
          textAlign: "center",
        }}
      >
        AI-Powered Video Creation
      </Animated>

      {/* Rotating logo */}
      <Animated
        animations={[
          Rotate({ degrees: 360, start: 120, duration: 120 }),
          Scale({ from: 1, to: 1.2, start: 180, duration: 60 })
        ]}
        style={{
          position: "absolute",
          bottom: "30%",
          left: "50%",
          transform: "translateX(-50%)",
          width: "80px",
          height: "80px",
          backgroundColor: "#4ECDC4",
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "white",
          fontSize: "36px",
          fontWeight: "bold",
        }}
      >
        ✨
      </Animated>

      {/* Exit animation */}
      <Animated
        animations={[
          Fade({ from: 1, to: 0, start: 270, duration: 30 }),
          Scale({ to: 0.5, start: 270, duration: 30 })
        ]}
        style={{
          position: "absolute",
          bottom: "10%",
          right: "10%",
          color: "#FF6B6B",
          fontSize: "18px",
        }}
      >
        Made with ❤️
      </Animated>
    </AbsoluteFill>
  );
}
`;

console.log("Generated animation code demonstrates:");
console.log("✅ Move animations with x/y coordinates");
console.log("✅ Scale animations with from/to values");
console.log("✅ Fade animations with opacity control");
console.log("✅ Rotate animations with degree rotation");
console.log("✅ Combined animations on single elements");
console.log("✅ Timing control with start/duration");
console.log("✅ Declarative, readable syntax");
