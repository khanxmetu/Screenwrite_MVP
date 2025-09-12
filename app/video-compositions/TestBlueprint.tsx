import React from "react";
import { BlueprintComposition } from "./BlueprintComposition";
import type { CompositionBlueprint } from "./BlueprintTypes";

// Media Testing Blueprint Component - Testing intelligent track system
export function TestBlueprintComposition() {
  const intelligentTrackBlueprint: CompositionBlueprint = [
    // Track 1: Mixed scenarios - adjacent clips with transitions + individual clips + gaps
    {
      clips: [
        // Group 1: Adjacent clips with transitions (0s-9.5s with 1.8s total transitions = 9.5s)
        {
          id: "video-1",
          startTimeInSeconds: 0,
          endTimeInSeconds: 3,
          element: `
            const { Video } = require('remotion');
            return React.createElement(Video, {
              src: '/screenrecording.mp4',
              startFrom: 0,
              endAt: 90,
              style: {
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              },
              volume: 0
            });
          `,
          transitionToNext: {
            type: 'fade',
            durationInSeconds: 1
          }
        },
        {
          id: "image-1",
          startTimeInSeconds: 3, // Adjacent: starts where video-1 ends
          endTimeInSeconds: 5.5, // 2.5s duration
          element: `
            const { Img } = require('remotion');
            return React.createElement(Img, {
              src: '/screenshot-app.png',
              style: {
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                backgroundColor: '#ffffff'
              }
            });
          `,
          transitionToNext: {
            type: 'fade',
            durationInSeconds: 0.8
          }
        },
        {
          id: "video-2",
          startTimeInSeconds: 5.5, // Adjacent: starts where image-1 ends
          endTimeInSeconds: 9.5, // 4s duration
          element: `
            const { Video } = require('remotion');
            return React.createElement(Video, {
              src: '/screenrecording.mp4',
              startFrom: 120,
              endAt: 240,
              style: {
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              },
              volume: 0
            });
          `
          // No transition - ends the group
        },
        
        // Gap here (9.5s to 12s = 2.5s gap)
        
        // Individual clip after gap
        {
          id: "standalone-text",
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
                backgroundColor: '#2a2a2a',
                color: '#00ff00',
                fontSize: '24px',
                fontFamily: 'monospace'
              }
            }, 'Standalone clip after gap');
          `
        }
      ]
    },
    
    // Track 2: Overlaid on top (different timing)
    {
      clips: [
        {
          id: "overlay-badge",
          startTimeInSeconds: 1,
          endTimeInSeconds: 8,
          element: `
            return React.createElement('div', {
              style: {
                position: 'absolute',
                top: '20px',
                right: '20px',
                padding: '8px 16px',
                backgroundColor: 'rgba(255,0,0,0.8)',
                color: 'white',
                fontSize: '14px',
                borderRadius: '4px',
                fontFamily: 'Arial, sans-serif'
              }
            }, 'Track 2 Overlay');
          `
        }
      ]
    }
  ];

  console.log("Intelligent Track Blueprint:", intelligentTrackBlueprint);
  return <BlueprintComposition blueprint={intelligentTrackBlueprint} />;
}

// Export the complex blueprint for use in other components
export const complexTestBlueprint: CompositionBlueprint = [
  // Track 1: Mixed scenarios - adjacent clips with transitions + individual clips + gaps
  {
    clips: [
      // Group 1: Adjacent clips with transitions (0s-9.5s with 1.8s total transitions = 9.5s)
      {
        id: "video-1",
        startTimeInSeconds: 0,
        endTimeInSeconds: 3,
        element: `
          const { Video } = require('remotion');
          return React.createElement(Video, {
            src: '/screenrecording.mp4',
            startFrom: 0,
            endAt: 90,
            style: {
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            },
            volume: 0
          });
        `,
        transitionToNext: {
          type: 'fade',
          durationInSeconds: 1
        }
      },
      {
        id: "image-1",
        startTimeInSeconds: 3, // Adjacent: starts where video-1 ends
        endTimeInSeconds: 5.5, // 2.5s duration
        element: `
          const { Img } = require('remotion');
          return React.createElement(Img, {
            src: '/screenshot-app.png',
            style: {
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              backgroundColor: '#ffffff'
            }
          });
        `,
        transitionToNext: {
          type: 'fade',
          durationInSeconds: 0.8
        }
      },
      {
        id: "video-2",
        startTimeInSeconds: 5.5, // Adjacent: starts where image-1 ends
        endTimeInSeconds: 9.5, // 4s duration
        element: `
          const { Video } = require('remotion');
          return React.createElement(Video, {
            src: '/screenrecording.mp4',
            startFrom: 120,
            endAt: 240,
            style: {
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            },
            volume: 0
          });
        `
        // No transition - ends the group
      },
      
      // Gap here (9.5s to 12s = 2.5s gap)
      
      // Individual clip after gap
      {
        id: "standalone-text",
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
              backgroundColor: '#2a2a2a',
              color: '#00ff00',
              fontSize: '24px',
              fontFamily: 'monospace'
            }
          }, 'Standalone clip after gap');
        `
      }
    ]
  },
  
  // Track 2: Overlaid on top (different timing)
  {
    clips: [
      {
        id: "overlay-badge",
        startTimeInSeconds: 1,
        endTimeInSeconds: 8,
        element: `
          return React.createElement('div', {
            style: {
              position: 'absolute',
              top: '20px',
              right: '20px',
              padding: '8px 16px',
              backgroundColor: 'rgba(255,0,0,0.8)',
              color: 'white',
              fontSize: '14px',
              borderRadius: '4px',
              fontFamily: 'Arial, sans-serif'
            }
          }, 'Track 2 Overlay');
        `
      }
    ]
  }
];

// Simple blueprint for compatibility - single track with basic media
export const sampleBlueprint: CompositionBlueprint = [
  {
    clips: [
      {
        id: "simple-video",
        startTimeInSeconds: 0,
        endTimeInSeconds: 5,
        element: `
          const { Video } = require('remotion');
          return React.createElement(Video, {
            src: '/screenrecording.mp4',
            startFrom: 30,
            endAt: 180,
            style: {
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            },
            volume: 0.3
          });
        `
      }
    ]
  }
];
