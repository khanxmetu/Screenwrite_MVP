import React from "react";
import { AbsoluteFill } from "remotion";
import { interp } from "../utils/animations";

// Test composition to demonstrate the simple interp animation system
export function TestAnimationComposition() {
  return (
    <AbsoluteFill style={{ backgroundColor: "#1a1a1a" }}>
      {/* Fading text using interp */}
      <div
        style={{
          position: "absolute",
          top: "20%",
          left: "10%",
          opacity: interp(0, 2, 0, 1), // Fade in from 0s to 2s
          fontSize: "32px",
          color: "white",
          fontFamily: "Arial, sans-serif",
        }}
      >
        Fading Text (interp for opacity)
      </div>

      {/* Scaling text using interp */}
      <div
        style={{
          position: "absolute",
          top: "40%",
          left: "20%",
          transform: `scale(${interp(1, 3, 0.5, 1.5)})`, // Scale from 0.5 to 1.5 between 1s and 3s
          color: "yellow",
          fontSize: "28px",
          fontFamily: "Arial, sans-serif",
        }}
      >
        Scaling Text (interp for scale)
      </div>

      {/* Moving and rotating text using interp */}
      <div
        style={{
          position: "absolute",
          top: "60%",
          left: "30%",
          transform: `translateX(${interp(2, 4, -100, 100)}px) translateY(${interp(2.5, 4.5, 0, -50)}px) rotate(${interp(3, 5, 0, 360)}deg)`,
          color: "cyan",
          fontSize: "24px",
          fontFamily: "Arial, sans-serif",
        }}
      >
        Moving & Rotating (interp for transform)
      </div>

      {/* Animated rectangle using interp for dimensions */}
      <div
        style={{
          position: "absolute",
          top: "80%",
          left: "40%",
          width: `${interp(4, 6, 50, 300)}px`,
          height: `${interp(4.2, 6.2, 10, 60)}px`,
          backgroundColor: "white",
          borderRadius: `${interp(5, 7, 0, 30)}px`,
        }}
      />
    </AbsoluteFill>
  );
}
