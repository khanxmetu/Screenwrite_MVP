import React from "react";
import { AbsoluteFill } from "remotion";
import { Animated, Move, Scale, Fade, Rotate } from "./SimpleAnimated";

// Test composition to demonstrate the animation system
export function TestAnimationComposition() {
  return (
    <AbsoluteFill style={{ backgroundColor: "#1a1a1a" }}>
      {/* Moving text */}
      <Animated
        animations={[
          Move({ x: 200, start: 0, duration: 60 }),
          Scale({ by: 1.2, start: 30, duration: 30 })
        ]}
        style={{
          position: "absolute",
          top: "20%",
          left: "10%",
          color: "white",
          fontSize: "24px",
          fontWeight: "bold",
        }}
      >
        Moving Text
      </Animated>

      {/* Fading text */}
      <Animated
        animations={[
          Fade({ to: 0.3, start: 60, duration: 30 }),
          Rotate({ degrees: 45, start: 90, duration: 30 })
        ]}
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          color: "#4ECDC4",
          fontSize: "32px",
          fontWeight: "bold",
        }}
      >
        Rotating & Fading
      </Animated>

      {/* Scaling box */}
      <Animated
        animations={[
          Scale({ by: 2, start: 120, duration: 60 }),
          Move({ x: -100, y: 50, start: 150, duration: 30 })
        ]}
        style={{
          position: "absolute",
          bottom: "20%",
          right: "20%",
          width: "100px",
          height: "100px",
          backgroundColor: "#FF6B6B",
          borderRadius: "8px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "white",
          fontWeight: "bold",
        }}
      >
        Box
      </Animated>
    </AbsoluteFill>
  );
}
