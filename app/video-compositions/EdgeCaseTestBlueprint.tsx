import React from "react";
import { BlueprintComposition } from "./BlueprintComposition";
import type { CompositionBlueprint } from "./BlueprintTypes";

// Edge Case Testing Blueprint - Testing NON-CROSSFADE transition scenarios
export function EdgeCaseTestBlueprintComposition() {
  const edgeCaseBlueprint: CompositionBlueprint = [
    // Track 1: Non-crossfade edge case scenarios
    {
      clips: [
      // Case 1: Clip with orphaned transitionToNext - should fade to transparent
      {
        id: "fade-to-transparent",
        startTimeInSeconds: 0,
        endTimeInSeconds: 4,
        element: `
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#ff6b6b',
              color: 'white',
              fontSize: '24px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'bold'
            }
          }, 'FADE TO TRANSPARENT');
        `,
        transitionToNext: {
          type: 'fade',
          durationInSeconds: 2  // Should fade out to transparent over 2 seconds
        }
      },        // Gap here (4s to 8s = 4s gap of black)

      // Case 2: Clip with orphaned transitionFromPrevious - should fade from transparent
      {
        id: "fade-from-transparent",  
        startTimeInSeconds: 8,
        endTimeInSeconds: 12,
        element: `
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#4ecdc4',
              color: 'white', 
              fontSize: '24px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'bold'
            }
          }, 'FADE FROM TRANSPARENT');
        `,
        transitionFromPrevious: {
          type: 'fade',
          durationInSeconds: 1.5  // Should fade in from transparent over 1.5 seconds
        }
      },        // Gap here (12s to 16s = 4s gap of black)

      // Case 3: Both orphaned transitions - fade in AND fade out
      {
        id: "double-orphaned",
        startTimeInSeconds: 16, 
        endTimeInSeconds: 20,
        element: `
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#9b59b6',
              color: 'white',
              fontSize: '24px', 
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'bold'
            }
          }, 'BOTH FADE IN & OUT');
        `,
        transitionFromPrevious: {
          type: 'fade',
          durationInSeconds: 1  // Fade in from transparent
        },
        transitionToNext: {
          type: 'fade',
          durationInSeconds: 1.5  // Fade out to transparent
        }
      },        // Large gap (20s to 24s = 4s gap)

        // Case 4: Final clip - transition at very end of composition 
        {
          id: "final-transition",
          startTimeInSeconds: 24,
          endTimeInSeconds: 28, 
          element: `
            return React.createElement('div', {
              style: {
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#e74c3c',
                color: 'white',
                fontSize: '24px',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'bold'
              }
            }, 'FINAL CLIP WITH TRANSITION');
          `,
          transitionToNext: {
            type: 'fade', 
            durationInSeconds: 3  // Transition past end of composition!
          }
        }
      ]
    },

    // Track 2: Overlay to show timing
    {
      clips: [
        {
          id: "timing-overlay",
          startTimeInSeconds: 0,
          endTimeInSeconds: 23,
          element: `
            const frame = 0; // This will be handled by the execution context
            const currentTime = frame / 30; // Assuming 30 FPS
            
            return React.createElement('div', {
              style: {
                position: 'absolute',
                top: '10px',
                left: '10px',
                padding: '8px 12px',
                backgroundColor: 'rgba(0,0,0,0.7)',
                color: '#00ff00',
                fontSize: '16px',
                fontFamily: 'monospace',
                borderRadius: '4px',
                border: '1px solid #00ff00'
              }
            }, 'Time: ' + currentTime.toFixed(1) + 's');
          `
        }
      ]
    }
  ];

  console.log("Edge Case Test Blueprint:", edgeCaseBlueprint);
  return <BlueprintComposition blueprint={edgeCaseBlueprint} />;
}

// Export the edge case blueprint for use in other components
export const edgeCaseTestBlueprint: CompositionBlueprint = [
  // Track 1: Non-crossfade edge case scenarios
  {
    clips: [
      // Case 1: Clip with orphaned transitionToNext - should fade to transparent
      {
        id: "fade-to-transparent",
        startTimeInSeconds: 0,
        endTimeInSeconds: 4,
        element: `
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#ff6b6b',
              color: 'white',
              fontSize: '24px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'bold'
            }
          }, 'FADE TO TRANSPARENT');
        `,
        transitionToNext: {
          type: 'fade',
          durationInSeconds: 2  // Should fade out to transparent over 2 seconds
        }
      },

      // Gap here (4s to 8s = 4s gap of black)

      // Case 2: Clip with orphaned transitionFromPrevious - should fade from transparent
      {
        id: "fade-from-transparent",  
        startTimeInSeconds: 8,
        endTimeInSeconds: 12,
        element: `
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#4ecdc4',
              color: 'white', 
              fontSize: '24px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'bold'
            }
          }, 'FADE FROM TRANSPARENT');
        `,
        transitionFromPrevious: {
          type: 'fade',
          durationInSeconds: 1.5  // Should fade in from transparent over 1.5 seconds
        }
      },

      // Gap here (12s to 16s = 4s gap of black)

      // Case 3: Both orphaned transitions - fade in AND fade out
      {
        id: "double-orphaned",
        startTimeInSeconds: 16, 
        endTimeInSeconds: 20,
        element: `
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#9b59b6',
              color: 'white',
              fontSize: '24px', 
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'bold'
            }
          }, 'BOTH FADE IN & OUT');
        `,
        transitionFromPrevious: {
          type: 'fade',
          durationInSeconds: 1  // Fade in from transparent
        },
        transitionToNext: {
          type: 'fade',
          durationInSeconds: 1.5  // Fade out to transparent
        }
      },

      // Large gap (20s to 24s = 4s gap)

      // Case 4: Final clip - transition at very end of composition 
      {
        id: "final-transition",
        startTimeInSeconds: 24,
        endTimeInSeconds: 28, 
        element: `
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#e74c3c',
              color: 'white',
              fontSize: '24px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'bold'
            }
          }, 'FINAL CLIP WITH TRANSITION');
        `,
        transitionToNext: {
          type: 'fade', 
          durationInSeconds: 3  // Transition past end of composition!
        }
      }
    ]
  },

  // Track 2: Background pattern to see transparency effects
  {
    clips: [
      {
        id: "timing-overlay",
        startTimeInSeconds: 0,
        endTimeInSeconds: 32,
        element: `
          return React.createElement('div', {
            style: {
              position: 'absolute',
              top: '10px',
              left: '10px',
              padding: '8px 12px',
              backgroundColor: 'rgba(0,0,0,0.8)',
              color: '#00ff00',
              fontSize: '16px',
              fontFamily: 'monospace',
              borderRadius: '4px',
              border: '1px solid #00ff00'
            }
          }, 'FADE TO/FROM TRANSPARENT TEST');
        `
      }
    ]
  }
];
