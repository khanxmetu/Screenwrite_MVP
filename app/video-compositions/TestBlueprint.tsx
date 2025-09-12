import React from "react";
import { BlueprintComposition } from "./BlueprintComposition";
import type { CompositionBlueprint } from "./BlueprintTypes";

// Test blueprint composition demonstrating the new blueprint system
export function TestBlueprintComposition() {
  const testBlueprint: CompositionBlueprint = {
    backgroundColor: "#1a1a2e",
    fps: 30,
    tracks: [
      // Text animation track
      {
        id: "text-track",
        clips: [
          {
            id: "intro-text",
            startTime: 0,
            duration: 3,
            code: `
              return React.createElement('div', {
                style: {
                  position: 'absolute',
                  top: '30%',
                  left: '50%',
                  transform: 'translateX(-50%) translateY(' + interp(0, 1.5, -30, 0) + 'px)',
                  opacity: interp(0, 1, 0, 1),
                  fontSize: '42px',
                  color: '#FFD93D',
                  fontWeight: 'bold',
                  textAlign: 'center',
                  fontFamily: 'Arial, sans-serif',
                  textShadow: '0 0 20px rgba(255,217,61,0.3)'
                }
              }, 'Blueprint Testing');
            `,
            transition: {
              type: 'slide',
              duration: 0.8
            }
          },
          {
            id: "description-text",
            startTime: 1.5,
            duration: 4,
            code: `
              return React.createElement('div', {
                style: {
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translateX(-50%) scale(' + interp(1.5, 2.5, 0.8, 1) + ')',
                  opacity: interp(1.5, 2, 0, 1),
                  fontSize: '24px',
                  color: '#67E8F9',
                  textAlign: 'center',
                  fontFamily: 'Arial, sans-serif',
                  maxWidth: '600px',
                  lineHeight: '1.4'
                }
              }, 'Multi-track composition with smooth transitions');
            `,
            transition: {
              type: 'scale',
              duration: 0.5
            }
          }
        ]
      },
      
      // Background effects track
      {
        id: "bg-effects-track",
        clips: [
          {
            id: "animated-background",
            startTime: 0,
            duration: 5.5,
            code: `
              return React.createElement('div', {
                style: {
                  position: 'absolute',
                  top: '0',
                  left: '0',
                  width: '100%',
                  height: '100%',
                  background: 'radial-gradient(circle at ' + interp(0, 5.5, 30, 70) + '% ' + interp(0, 5.5, 40, 60) + '%, rgba(168,85,247,0.2) 0%, rgba(15,15,35,0.9) 70%)',
                  zIndex: -1
                }
              });
            `
          }
        ]
      },

      // Feature highlights track
      {
        id: "features-highlight-track", 
        clips: [
          {
            id: "feature-item-1",
            startTime: 3,
            duration: 2.5,
            code: `
              return React.createElement('div', {
                style: {
                  position: 'absolute',
                  top: '70%',
                  left: interp(3, 4, -20, 20) + '%',
                  opacity: interp(3, 3.5, 0, 1),
                  fontSize: '18px',
                  color: '#FFFFFF',
                  fontFamily: 'Arial, sans-serif',
                  padding: '10px 16px',
                  backgroundColor: 'rgba(255,217,61,0.15)',
                  borderRadius: '8px',
                  border: '1px solid rgba(255,217,61,0.3)',
                  backdropFilter: 'blur(10px)'
                }
              }, '🎯 Precise timing control');
            `,
            transition: {
              type: 'slide',
              duration: 0.6
            }
          },
          
          {
            id: "feature-item-2",
            startTime: 4,
            duration: 1.5,
            code: `
              return React.createElement('div', {
                style: {
                  position: 'absolute',
                  top: '70%',
                  right: interp(4, 5, -30, 20) + '%',
                  opacity: interp(4, 4.5, 0, 1),
                  fontSize: '18px',
                  color: '#FFFFFF',
                  fontFamily: 'Arial, sans-serif',
                  padding: '10px 16px',
                  backgroundColor: 'rgba(103,232,249,0.15)',
                  borderRadius: '8px', 
                  border: '1px solid rgba(103,232,249,0.3)',
                  backdropFilter: 'blur(10px)'
                }
              }, '✨ Beautiful transitions');
            `,
            transition: {
              type: 'slide',
              duration: 0.6
            }
          }
        ]
      }
    ]
  };

  return <BlueprintComposition blueprint={testBlueprint} />;
}

// Advanced blueprint data for testing with video, images, and complex transitions
export const sampleBlueprint: CompositionBlueprint = {
  backgroundColor: "#0f0f23",
  fps: 30,
  tracks: [
    // Background video track
    {
      id: "background-video-track",
      clips: [
        {
          id: "bg-video",
          startTime: 0,
          duration: 8,
          code: `
            const { Video } = require('remotion');
            return React.createElement(Video, {
              src: '/screenrecording.mp4',
              style: {
                position: 'absolute',
                top: '0',
                left: '0',
                width: '100%',
                height: '100%',
                opacity: interp(0, 1, 0, 0.3),
                filter: 'blur(' + interp(0, 2, 5, 0) + 'px) brightness(' + interp(1, 3, 0.5, 1) + ')',
                objectFit: 'cover',
                zIndex: -2
              },
              volume: 0
            });
          `,
          transition: {
            type: 'fade',
            duration: 1.0
          }
        }
      ]
    },
    
    // Animated background overlay
    {
      id: "background-overlay-track",
      clips: [
        {
          id: "animated-bg",
          startTime: 0,
          duration: 8,
          code: `
            return React.createElement('div', {
              style: {
                position: 'absolute',
                top: '0',
                left: '0',
                width: '100%',
                height: '100%',
                background: 'radial-gradient(circle at ' + interp(0, 8, 20, 80) + '% ' + interp(0, 8, 30, 70) + '%, rgba(255,217,61,0.1) 0%, rgba(103,232,249,0.05) 50%, rgba(15,15,35,0.8) 100%)',
                zIndex: -1
              }
            });
          `
        }
      ]
    },

    // Title sequence with complex animations
    {
      id: "title-track",
      clips: [
        {
          id: "main-title",
          startTime: 0.5,
          duration: 3,
          code: `
            return React.createElement('div', {
              style: {
                position: 'absolute',
                top: '20%',
                left: '50%',
                transform: 'translateX(-50%) translateY(' + interp(0, 1.5, -50, 0) + 'px) scale(' + interp(0, 1, 0.8, 1) + ') rotate(' + interp(0.5, 2, -5, 0) + 'deg)',
                opacity: interp(0, 1, 0, 1),
                fontSize: '56px',
                color: '#FFD93D',
                fontWeight: 'bold',
                textAlign: 'center',
                fontFamily: 'Arial, sans-serif',
                textShadow: '0 0 20px rgba(255,217,61,0.5)',
                zIndex: 10
              }
            }, 'SCREENWRITE');
          `
        },
        
        {
          id: "subtitle-animated",
          startTime: 2,
          duration: 4,
          code: `
            return React.createElement('div', {
              style: {
                position: 'absolute',
                top: '35%',
                left: '50%',
                transform: 'translateX(-50%) scale(' + interp(0, 0.8, 0.7, 1) + ')',
                opacity: interp(0, 0.5, 0, 1),
                fontSize: '28px',
                color: '#67E8F9',
                textAlign: 'center',
                fontFamily: 'Arial, sans-serif',
                fontWeight: '300',
                letterSpacing: '2px',
                zIndex: 9
              }
            }, 'Blueprint Architecture Demo');
          `
        }
      ]
    },

    // Feature showcase track
    {
      id: "features-track",
      clips: [
        {
          id: "feature-1",
          startTime: 3.5,
          duration: 2,
          code: `
            return React.createElement('div', {
              style: {
                position: 'absolute',
                top: '55%',
                left: interp(0, 1, -20, 15) + '%',
                opacity: interp(0, 0.5, 0, 1),
                fontSize: '20px',
                color: '#FFFFFF',
                fontFamily: 'Arial, sans-serif',
                padding: '12px 20px',
                backgroundColor: 'rgba(255,217,61,0.1)',
                borderLeft: '4px solid #FFD93D',
                borderRadius: '4px',
                backdropFilter: 'blur(10px)',
                zIndex: 8
              }
            }, '✨ Multi-track composition');
          `
        },
        
        {
          id: "feature-2", 
          startTime: 4.5,
          duration: 2,
          code: `
            return React.createElement('div', {
              style: {
                position: 'absolute',
                top: '65%',
                left: interp(0, 1, 120, 15) + '%',
                opacity: interp(0, 0.5, 0, 1),
                fontSize: '20px',
                color: '#FFFFFF',
                fontFamily: 'Arial, sans-serif',
                padding: '12px 20px',
                backgroundColor: 'rgba(103,232,249,0.1)',
                borderLeft: '4px solid #67E8F9',
                borderRadius: '4px',
                backdropFilter: 'blur(10px)',
                zIndex: 8
              }
            }, '🎬 Smooth transitions');
          `
        },
        
        {
          id: "feature-3",
          startTime: 5.5,
          duration: 2.5,
          code: `
            return React.createElement('div', {
              style: {
                position: 'absolute',
                top: '75%',
                left: interp(0, 1, -20, 15) + '%',
                opacity: interp(0, 0.5, 0, 1),
                fontSize: '20px',
                color: '#FFFFFF',
                fontFamily: 'Arial, sans-serif',
                padding: '12px 20px',
                backgroundColor: 'rgba(168,85,247,0.1)',
                borderLeft: '4px solid #A855F7',
                borderRadius: '4px',
                backdropFilter: 'blur(10px)',
                zIndex: 8
              }
            }, '⚡ Real-time preview');
          `
        }
      ]
    },

    // Logo/Image track
    {
      id: "logo-track",
      clips: [
        {
          id: "app-screenshot",
          startTime: 6,
          duration: 2,
          code: `
            const { Img } = require('remotion');
            return React.createElement('div', {
              style: {
                position: 'absolute',
                top: '50%',
                right: interp(0, 1, -300, 50) + 'px',
                transform: 'translateY(-50%) scale(' + interp(0, 0.8, 0.6, 0.8) + ') rotate(' + interp(0.2, 1.2, 5, 0) + 'deg)',
                opacity: interp(0, 0.5, 0, 0.9),
                borderRadius: '12px',
                border: '2px solid rgba(255,217,61,0.3)',
                boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
                overflow: 'hidden',
                zIndex: 5
              }
            }, React.createElement(Img, {
              src: '/screenshot-app.png',
              style: {
                width: '200px',
                height: '140px',
                objectFit: 'cover'
              }
            }));
          `,
          transition: {
            type: 'slide',
            duration: 0.6
          }
        }
      ]
    },

    // Particle effects track
    {
      id: "particles-track",
      clips: [
        {
          id: "floating-particles",
          startTime: 1,
          duration: 7,
          code: `
            return React.createElement('div', {
              style: {
                position: 'absolute',
                top: '0',
                left: '0',
                width: '100%',
                height: '100%',
                zIndex: 1
              }
            }, 
            // Create multiple floating particles
            Array.from({length: 8}).map((_, i) => 
              React.createElement('div', {
                key: i,
                style: {
                  position: 'absolute',
                  left: (10 + i * 12) + '%',
                  top: interp(0, 7, 20 + i * 10, 80 - i * 8) + '%',
                  width: '4px',
                  height: '4px',
                  borderRadius: '50%',
                  backgroundColor: i % 3 === 0 ? '#FFD93D' : i % 3 === 1 ? '#67E8F9' : '#A855F7',
                  opacity: interp(i * 0.2, 7, 0.3, 0.8),
                  boxShadow: '0 0 10px currentColor'
                }
              })
            ));
          `
        }
      ]
    },

    // Call to action track
    {
      id: "cta-track",
      clips: [
        {
          id: "final-message",
          startTime: 6.5,
          duration: 1.5,
          code: `
            return React.createElement('div', {
              style: {
                position: 'absolute',
                bottom: '15%',
                left: '50%',
                transform: 'translateX(-50%) scale(' + interp(0, 0.7, 0.9, 1) + ')',
                opacity: interp(0, 0.5, 0, 1),
                fontSize: '24px',
                color: '#FFFFFF',
                textAlign: 'center',
                fontFamily: 'Arial, sans-serif',
                fontWeight: '500',
                padding: '16px 32px',
                background: 'linear-gradient(135deg, rgba(255,217,61,0.2) 0%, rgba(103,232,249,0.2) 100%)',
                borderRadius: '50px',
                border: '1px solid rgba(255,255,255,0.1)',
                backdropFilter: 'blur(20px)',
                zIndex: 12
              }
            }, 'Experience the Future of Video Creation');
          `
        }
      ]
    }
  ]
};
