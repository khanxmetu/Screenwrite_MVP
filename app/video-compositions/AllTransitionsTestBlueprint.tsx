import React from "react";
import { BlueprintComposition } from "./BlueprintComposition";
import type { CompositionBlueprint } from "./BlueprintTypes";

// Comprehensive Test Blueprint - Testing ALL available transition types
export function AllTransitionsTestBlueprintComposition() {
  const allTransitionsBlueprint: CompositionBlueprint = [
    // Track 1: All transition types showcase
    {
      clips: [
        // 1. Fade transition (0s-3s)
        {
          id: "fade-test",
          startTimeInSeconds: 0,
          endTimeInSeconds: 3,
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
                fontSize: '32px',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'bold'
              }
            }, 'FADE TRANSITION');
          `,
          transitionToNext: {
            type: 'fade',
            durationInSeconds: 1
          }
        },

        // 2. Slide transition (3s-6s)
        {
          id: "slide-test",
          startTimeInSeconds: 3,
          endTimeInSeconds: 6,
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
                fontSize: '32px',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'bold'
              }
            }, 'SLIDE FROM RIGHT');
          `,
          transitionToNext: {
            type: 'slide',
            direction: 'from-right',
            durationInSeconds: 1
          }
        },

        // 3. Wipe transition (6s-9s)
        {
          id: "wipe-test",
          startTimeInSeconds: 6,
          endTimeInSeconds: 9,
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
                fontSize: '32px',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'bold'
              }
            }, 'WIPE FROM TOP');
          `,
          transitionToNext: {
            type: 'wipe',
            direction: 'from-top',
            durationInSeconds: 1
          }
        },

        // 4. Flip transition (9s-12s)
        {
          id: "flip-test",
          startTimeInSeconds: 9,
          endTimeInSeconds: 12,
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
                fontSize: '32px',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'bold'
              }
            }, 'FLIP FROM LEFT');
          `,
          transitionToNext: {
            type: 'flip',
            direction: 'from-left',
            perspective: 1500,
            durationInSeconds: 1
          }
        },

        // 5. Clock Wipe transition (12s-15s)
        {
          id: "clockwipe-test",
          startTimeInSeconds: 12,
          endTimeInSeconds: 15,
          element: `
            return React.createElement('div', {
              style: {
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#f39c12',
                color: 'white',
                fontSize: '32px',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'bold'
              }
            }, 'CLOCK WIPE');
          `,
          transitionToNext: {
            type: 'clockWipe',
            durationInSeconds: 1
          }
        },

        // 6. Iris transition (15s-18s)
        {
          id: "iris-test",
          startTimeInSeconds: 15,
          endTimeInSeconds: 18,
          element: `
            return React.createElement('div', {
              style: {
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#2ecc71',
                color: 'white',
                fontSize: '32px',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'bold'
              }
            }, 'IRIS TRANSITION');
          `
        }
      ]
    },

    // Track 2: Info overlay
    {
      clips: [
        {
          id: "info-overlay",
          startTimeInSeconds: 0,
          endTimeInSeconds: 18,
          element: `
            return React.createElement('div', {
              style: {
                position: 'absolute',
                top: '20px',
                right: '20px',
                padding: '12px 16px',
                backgroundColor: 'rgba(0,0,0,0.8)',
                color: '#ffffff',
                fontSize: '18px',
                fontFamily: 'monospace',
                borderRadius: '8px',
                border: '2px solid #ffffff'
              }
            }, 'ALL TRANSITIONS DEMO');
          `
        }
      ]
    }
  ];

  console.log("All Transitions Test Blueprint:", allTransitionsBlueprint);
  return <BlueprintComposition blueprint={allTransitionsBlueprint} />;
}

// Export the all transitions blueprint for use in other components
export const allTransitionsTestBlueprint: CompositionBlueprint = [
  // Track 1: All transition types showcase
  {
    clips: [
      // 1. Fade transition (0s-3s)
      {
        id: "fade-test",
        startTimeInSeconds: 0,
        endTimeInSeconds: 3,
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
              fontSize: '32px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'bold'
            }
          }, 'FADE TRANSITION');
        `,
        transitionToNext: {
          type: 'fade',
          durationInSeconds: 1
        }
      },

      // 2. Slide transition (3s-6s)
      {
        id: "slide-test",
        startTimeInSeconds: 3,
        endTimeInSeconds: 6,
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
              fontSize: '32px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'bold'
            }
          }, 'SLIDE FROM RIGHT');
        `,
        transitionToNext: {
          type: 'slide',
          direction: 'from-right',
          durationInSeconds: 1
        }
      },

      // 3. Wipe transition (6s-9s)
      {
        id: "wipe-test",
        startTimeInSeconds: 6,
        endTimeInSeconds: 9,
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
              fontSize: '32px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'bold'
            }
          }, 'WIPE FROM TOP');
        `,
        transitionToNext: {
          type: 'wipe',
          direction: 'from-top',
          durationInSeconds: 1
        }
      },

      // 4. Flip transition (9s-12s)
      {
        id: "flip-test",
        startTimeInSeconds: 9,
        endTimeInSeconds: 12,
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
              fontSize: '32px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'bold'
            }
          }, 'FLIP FROM LEFT');
        `,
        transitionToNext: {
          type: 'flip',
          direction: 'from-left',
          perspective: 1500,
          durationInSeconds: 1
        }
      },

      // 5. Clock Wipe transition (12s-15s)
      {
        id: "clockwipe-test",
        startTimeInSeconds: 12,
        endTimeInSeconds: 15,
        element: `
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#f39c12',
              color: 'white',
              fontSize: '32px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'bold'
            }
          }, 'CLOCK WIPE');
        `,
        transitionToNext: {
          type: 'clockWipe',
          durationInSeconds: 1
        }
      },

      // 6. Iris transition (15s-18s)
      {
        id: "iris-test",
        startTimeInSeconds: 15,
        endTimeInSeconds: 18,
        element: `
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#2ecc71',
              color: 'white',
              fontSize: '32px',
              fontFamily: 'Arial, sans-serif',
              fontWeight: 'bold'
            }
          }, 'IRIS TRANSITION');
        `
      }
    ]
  },

  // Track 2: Info overlay
  {
    clips: [
      {
        id: "info-overlay",
        startTimeInSeconds: 0,
        endTimeInSeconds: 18,
        element: `
          return React.createElement('div', {
            style: {
              position: 'absolute',
              top: '20px',
              right: '20px',
              padding: '12px 16px',
              backgroundColor: 'rgba(0,0,0,0.8)',
              color: '#ffffff',
              fontSize: '18px',
              fontFamily: 'monospace',
              borderRadius: '8px',
              border: '2px solid #ffffff'
            }
          }, 'ALL TRANSITIONS DEMO');
        `
      }
    ]
  }
];
