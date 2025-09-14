import React from "react";
import { BlueprintComposition } from "./BlueprintComposition";
import type { CompositionBlueprint } from "./BlueprintTypes";

// Comprehensive Test Blueprint - Testing ALL available transition types
export function AllTransitionsTestBlueprintComposition() {
  const allTransitionsBlueprint: CompositionBlueprint = [
    // Track 1: All transition types showcase
    {
      clips: [
        // 1. Fade transition (0s-3s) - Video
        {
          id: "video-fade-test",
          startTimeInSeconds: 0,
          endTimeInSeconds: 3,
          element: `
            const { Video } = require('remotion');
            return React.createElement('div', {
              style: {
                width: '100%',
                height: '100%',
                position: 'relative'
              }
            }, [
              React.createElement(Video, {
                key: 'video',
                src: '/screenrecording.mp4',
                style: {
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover'
                },
                muted: true
              }),
              React.createElement('div', {
                key: 'overlay',
                style: {
                  position: 'absolute',
                  bottom: '20px',
                  left: '20px',
                  padding: '8px 16px',
                  backgroundColor: 'rgba(0,0,0,0.7)',
                  color: 'white',
                  fontSize: '24px',
                  fontFamily: 'Arial, sans-serif',
                  fontWeight: 'bold',
                  borderRadius: '4px'
                }
              }, 'FADE TRANSITION')
            ]);
          `,
          transitionToNext: {
            type: 'fade',
            durationInSeconds: 1
          }
        },

        // 2. Slide transition (3s-6s) - Image
        {
          id: "image-slide-test",
          startTimeInSeconds: 3,
          endTimeInSeconds: 6,
          element: `
            return React.createElement('div', {
              style: {
                width: '100%',
                height: '100%',
                position: 'relative'
              }
            }, [
              React.createElement('img', {
                key: 'image',
                src: '/screenshot-app.png',
                style: {
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover'
                }
              }),
              React.createElement('div', {
                key: 'overlay',
                style: {
                  position: 'absolute',
                  bottom: '20px',
                  left: '20px',
                  padding: '8px 16px',
                  backgroundColor: 'rgba(0,0,0,0.7)',
                  color: 'white',
                  fontSize: '24px',
                  fontFamily: 'Arial, sans-serif',
                  fontWeight: 'bold',
                  borderRadius: '4px'
                }
              }, 'SLIDE FROM RIGHT')
            ]);
          `,
          transitionToNext: {
            type: 'slide',
            direction: 'from-right',
            durationInSeconds: 1
          }
        },

        // 3. Wipe transition (6s-9s) - Video
        {
          id: "video-wipe-test",
          startTimeInSeconds: 6,
          endTimeInSeconds: 9,
          element: `
            const { Video } = require('remotion');
            return React.createElement('div', {
              style: {
                width: '100%',
                height: '100%',
                position: 'relative'
              }
            }, [
              React.createElement(Video, {
                key: 'video',
                src: '/screenrecording.mp4',
                style: {
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover'
                },
                muted: true
              }),
              React.createElement('div', {
                key: 'overlay',
                style: {
                  position: 'absolute',
                  bottom: '20px',
                  left: '20px',
                  padding: '8px 16px',
                  backgroundColor: 'rgba(0,0,0,0.7)',
                  color: 'white',
                  fontSize: '24px',
                  fontFamily: 'Arial, sans-serif',
                  fontWeight: 'bold',
                  borderRadius: '4px'
                }
              }, 'WIPE FROM TOP')
            ]);
          `,
          transitionToNext: {
            type: 'wipe',
            direction: 'from-top',
            durationInSeconds: 1
          }
        },

        // 4. Flip transition (9s-12s) - Image
        {
          id: "image-flip-test",
          startTimeInSeconds: 9,
          endTimeInSeconds: 12,
          element: `
            return React.createElement('div', {
              style: {
                width: '100%',
                height: '100%',
                position: 'relative'
              }
            }, [
              React.createElement('img', {
                key: 'image',
                src: '/favicon.png',
                style: {
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                  backgroundColor: '#2c3e50'
                }
              }),
              React.createElement('div', {
                key: 'overlay',
                style: {
                  position: 'absolute',
                  bottom: '20px',
                  left: '20px',
                  padding: '8px 16px',
                  backgroundColor: 'rgba(0,0,0,0.7)',
                  color: 'white',
                  fontSize: '24px',
                  fontFamily: 'Arial, sans-serif',
                  fontWeight: 'bold',
                  borderRadius: '4px'
                }
              }, 'FLIP FROM LEFT')
            ]);
          `,
          transitionToNext: {
            type: 'flip',
            direction: 'from-left',
            perspective: 1500,
            durationInSeconds: 1
          }
        },

        // 5. Clock Wipe transition (12s-15s) - Video
        {
          id: "video-clockwipe-test",
          startTimeInSeconds: 12,
          endTimeInSeconds: 15,
          element: `
            const { Video } = require('remotion');
            return React.createElement('div', {
              style: {
                width: '100%',
                height: '100%',
                position: 'relative'
              }
            }, [
              React.createElement(Video, {
                key: 'video',
                src: '/screenrecording.mp4',
                style: {
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover'
                },
                muted: true
              }),
              React.createElement('div', {
                key: 'overlay',
                style: {
                  position: 'absolute',
                  bottom: '20px',
                  left: '20px',
                  padding: '8px 16px',
                  backgroundColor: 'rgba(0,0,0,0.7)',
                  color: 'white',
                  fontSize: '24px',
                  fontFamily: 'Arial, sans-serif',
                  fontWeight: 'bold',
                  borderRadius: '4px'
                }
              }, 'CLOCK WIPE')
            ]);
          `,
          transitionToNext: {
            type: 'clockWipe',
            durationInSeconds: 1
          }
        },

        // 6. Iris transition (15s-18s) - Image
        {
          id: "image-iris-test",
          startTimeInSeconds: 15,
          endTimeInSeconds: 18,
          element: `
            return React.createElement('div', {
              style: {
                width: '100%',
                height: '100%',
                position: 'relative'
              }
            }, [
              React.createElement('img', {
                key: 'image',
                src: '/screenshot-app.png',
                style: {
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover'
                }
              }),
              React.createElement('div', {
                key: 'overlay',
                style: {
                  position: 'absolute',
                  bottom: '20px',
                  left: '20px',
                  padding: '8px 16px',
                  backgroundColor: 'rgba(0,0,0,0.7)',
                  color: 'white',
                  fontSize: '24px',
                  fontFamily: 'Arial, sans-serif',
                  fontWeight: 'bold',
                  borderRadius: '4px'
                }
              }, 'IRIS TRANSITION')
            ]);
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
  // Track 1: All transition types showcase with media
  {
    clips: [
      // 1. Fade transition (0s-3s) - Video
      {
        id: "video-fade-test",
        startTimeInSeconds: 0,
        endTimeInSeconds: 3,
        element: `
          const { Video } = require('remotion');
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              position: 'relative'
            }
          }, [
            React.createElement(Video, {
              key: 'video',
              src: '/screenrecording.mp4',
              style: {
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              },
              muted: true
            }),
            React.createElement('div', {
              key: 'overlay',
              style: {
                position: 'absolute',
                bottom: '20px',
                left: '20px',
                padding: '8px 16px',
                backgroundColor: 'rgba(0,0,0,0.7)',
                color: 'white',
                fontSize: '24px',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'bold',
                borderRadius: '4px'
              }
            }, 'FADE TRANSITION')
          ]);
        `,
        transitionToNext: {
          type: 'fade',
          durationInSeconds: 1
        }
      },

      // 2. Slide transition (3s-6s) - Image
      {
        id: "image-slide-test",
        startTimeInSeconds: 3,
        endTimeInSeconds: 6,
        element: `
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              position: 'relative'
            }
          }, [
            React.createElement('img', {
              key: 'image',
              src: '/screenshot-app.png',
              style: {
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              }
            }),
            React.createElement('div', {
              key: 'overlay',
              style: {
                position: 'absolute',
                bottom: '20px',
                left: '20px',
                padding: '8px 16px',
                backgroundColor: 'rgba(0,0,0,0.7)',
                color: 'white',
                fontSize: '24px',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'bold',
                borderRadius: '4px'
              }
            }, 'SLIDE FROM RIGHT')
          ]);
        `,
        transitionToNext: {
          type: 'slide',
          direction: 'from-right',
          durationInSeconds: 1
        }
      },

      // 3. Wipe transition (6s-9s) - Video
      {
        id: "video-wipe-test",
        startTimeInSeconds: 6,
        endTimeInSeconds: 9,
        element: `
          const { Video } = require('remotion');
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              position: 'relative'
            }
          }, [
            React.createElement(Video, {
              key: 'video',
              src: '/screenrecording.mp4',
              style: {
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              },
              muted: true
            }),
            React.createElement('div', {
              key: 'overlay',
              style: {
                position: 'absolute',
                bottom: '20px',
                left: '20px',
                padding: '8px 16px',
                backgroundColor: 'rgba(0,0,0,0.7)',
                color: 'white',
                fontSize: '24px',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'bold',
                borderRadius: '4px'
              }
            }, 'WIPE FROM TOP')
          ]);
        `,
        transitionToNext: {
          type: 'wipe',
          direction: 'from-top',
          durationInSeconds: 1
        }
      },

      // 4. Flip transition (9s-12s) - Image
      {
        id: "image-flip-test",
        startTimeInSeconds: 9,
        endTimeInSeconds: 12,
        element: `
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              position: 'relative'
            }
          }, [
            React.createElement('img', {
              key: 'image',
              src: '/favicon.png',
              style: {
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                backgroundColor: '#2c3e50'
              }
            }),
            React.createElement('div', {
              key: 'overlay',
              style: {
                position: 'absolute',
                bottom: '20px',
                left: '20px',
                padding: '8px 16px',
                backgroundColor: 'rgba(0,0,0,0.7)',
                color: 'white',
                fontSize: '24px',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'bold',
                borderRadius: '4px'
              }
            }, 'FLIP FROM LEFT')
          ]);
        `,
        transitionToNext: {
          type: 'flip',
          direction: 'from-left',
          perspective: 1500,
          durationInSeconds: 1
        }
      },

      // 5. Clock Wipe transition (12s-15s) - Video
      {
        id: "video-clockwipe-test",
        startTimeInSeconds: 12,
        endTimeInSeconds: 15,
        element: `
          const { Video } = require('remotion');
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              position: 'relative'
            }
          }, [
            React.createElement(Video, {
              key: 'video',
              src: '/screenrecording.mp4',
              style: {
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              },
              muted: true
            }),
            React.createElement('div', {
              key: 'overlay',
              style: {
                position: 'absolute',
                bottom: '20px',
                left: '20px',
                padding: '8px 16px',
                backgroundColor: 'rgba(0,0,0,0.7)',
                color: 'white',
                fontSize: '24px',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'bold',
                borderRadius: '4px'
              }
            }, 'CLOCK WIPE')
          ]);
        `,
        transitionToNext: {
          type: 'clockWipe',
          durationInSeconds: 1
        }
      },

      // 6. Iris transition (15s-18s) - Image
      {
        id: "image-iris-test",
        startTimeInSeconds: 15,
        endTimeInSeconds: 18,
        element: `
          return React.createElement('div', {
            style: {
              width: '100%',
              height: '100%',
              position: 'relative'
            }
          }, [
            React.createElement('img', {
              key: 'image',
              src: '/screenshot-app.png',
              style: {
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              }
            }),
            React.createElement('div', {
              key: 'overlay',
              style: {
                position: 'absolute',
                bottom: '20px',
                left: '20px',
                padding: '8px 16px',
                backgroundColor: 'rgba(0,0,0,0.7)',
                color: 'white',
                fontSize: '24px',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'bold',
                borderRadius: '4px'
              }
            }, 'IRIS TRANSITION')
          ]);
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