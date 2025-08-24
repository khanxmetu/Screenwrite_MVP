// Structured test code - imported as module
export const structuredTestCode = `// Test Code - Structured Animation Patterns
// Generated at: 2025-08-24 14:45:00
// User Request: Testing structured animation patterns with proper timing
// AI-determined Duration: 12.0 seconds
// No backend validation - errors handled by frontend
// ======================================

const frame = currentFrameValue;
const { width, height, fps } = videoConfigValue;

// TIMING CONSTANTS - Standard durations for consistency
const FADE_DURATION = 20;          // Standard fade in/out
const QUICK_TRANSITION = 10;       // Fast transitions
const CROSS_FADE_OVERLAP = 15;     // Overlap between sequences
const SPRING_DELAY = 30;           // Delay before spring animations

// CONTAINER CONSTANTS - Prevent size jumping
const TITLE_CONTAINER_HEIGHT = 120;
const SUBTITLE_CONTAINER_HEIGHT = 80;
const SAFE_ZONE_PADDING = 60;     // Safe area padding
const CARD_PADDING = 40;          // Internal card padding

// Z-INDEX LAYERS - Visual hierarchy
const Z_BACKGROUND = 1;
const Z_CONTENT = 2;
const Z_OVERLAY = 3;
const Z_UI = 4;

// SPRING CONFIG - Consistent easing
const STANDARD_SPRING = { damping: 12, stiffness: 80 };
const GENTLE_SPRING = { damping: 15, stiffness: 60 };
const BOUNCY_SPRING = { damping: 8, stiffness: 100 };

// === BACKGROUND VIDEO SEQUENCES WITH CROSS-FADES ===

// Video clip 1 with fade in - strictly increasing: [0, 20, 75, 90]
const clip1Opacity = interpolate(
  frame,
  [0, FADE_DURATION, 75, 90],
  [0, 1, 1, 0]
);

// Video clip 2 with cross-fade from clip 1 - strictly increasing: [75, 90, 165, 180]
const clip2Opacity = interpolate(
  frame,
  [75, 90, 165, 180],
  [0, 1, 1, 0]
);

// Background video for remaining duration with fade in - strictly increasing: [165, 180]
const backgroundOpacity = interpolate(
  frame,
  [165, 180],
  [0, 0.6]
);

// === CONTAINER-BASED TEXT ANIMATIONS ===

// Title animation with fixed container - no size jumping - strictly increasing: [30, 50]
const titleOpacity = interpolate(
  frame,
  [SPRING_DELAY, SPRING_DELAY + FADE_DURATION],
  [0, 1]
);

const titleScale = spring({
  frame: frame - SPRING_DELAY,
  fps: fps,
  config: STANDARD_SPRING
});

// Typing effect with stable container - strictly increasing: [60, 120]
const typingProgress = interpolate(
  frame,
  [60, 120],
  [0, 1],
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
);

// Subtitle slide-in with proper timing - strictly increasing: [90, 110]
const subtitleY = interpolate(
  frame,
  [90, 110],
  [40, 0]
);

const subtitleOpacity = interpolate(
  frame,
  [90, 110],
  [0, 1]
);

// === CARD/CONTAINER SLIDE ANIMATION ===
// Card slide animation - strictly increasing: [150, 190]
const cardX = interpolate(
  frame,
  [150, 190],
  [-400, 0]
);

const cardOpacity = interpolate(
  frame,
  [150, 170],
  [0, 1]
);

// === LOGO SCALING WITH PROPER TIMING ===
const logoScale = spring({
  frame: frame - 180,
  fps: fps,
  config: GENTLE_SPRING
});

const logoOpacity = interpolate(
  frame,
  [180, 200],
  [0, 1]
);

return React.createElement(AbsoluteFill, {},

  // === BACKGROUND LAYER (Z-INDEX 1) ===
  
  // Simulated video backgrounds with colored divs since video URLs are examples
  React.createElement(Sequence, {
    from: 0,
    durationInFrames: 90,
    children: React.createElement('div', {
      style: {
        width: '100%',
        height: '100%',
        backgroundColor: '#FF6B6B',
        opacity: clip1Opacity,
        zIndex: Z_BACKGROUND,
        position: 'absolute'
      }
    })
  }),

  React.createElement(Sequence, {
    from: 90,
    durationInFrames: 90,
    children: React.createElement('div', {
      style: {
        width: '100%',
        height: '100%',
        backgroundColor: '#4ECDC4',
        opacity: clip2Opacity,
        zIndex: Z_BACKGROUND,
        position: 'absolute'
      }
    })
  }),

  React.createElement(Sequence, {
    from: 180,
    durationInFrames: 180,
    children: React.createElement('div', {
      style: {
        width: '100%',
        height: '100%',
        backgroundColor: '#45B7D1',
        opacity: backgroundOpacity,
        zIndex: Z_BACKGROUND,
        position: 'absolute'
      }
    })
  }),

  // === CONTENT LAYER (Z-INDEX 2) ===

  // === POSITIONING EXAMPLES - Core Patterns ===

  // PATTERN 1: CENTER ELEMENT - Perfect centering for titles/logos
  React.createElement(Sequence, {
    from: 0,
    durationInFrames: 60,
    children: React.createElement('div', {
      style: {
        // STANDARD CENTER PATTERN - Use this for perfect centering
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '300px',
        height: '100px',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        border: '2px solid rgba(255, 255, 255, 0.3)',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '18px',
        color: '#FFFFFF',
        zIndex: Z_CONTENT
      }
    }, 'Perfect Center')
  }),

  // PATTERN 2: FILL WITH PADDING - Responsive containers
  React.createElement(Sequence, {
    from: 20,
    durationInFrames: 60,
    children: React.createElement('div', {
      style: {
        // FILL WITH PADDING PATTERN - Responsive to screen size
        position: 'absolute',
        top: '60px',
        left: '60px',
        right: '60px',
        bottom: '60px',
        backgroundColor: 'rgba(0, 0, 0, 0.1)',
        border: '2px solid rgba(255, 255, 255, 0.2)',
        borderRadius: '12px',
        padding: '20px',
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'flex-end',
        fontSize: '16px',
        color: '#FFFFFF',
        zIndex: Z_CONTENT
      }
    }, 'Fill Container')
  }),

  // PATTERN 3: SAFE ZONE POSITIONING - Professional layouts
  React.createElement(Sequence, {
    from: 10,
    durationInFrames: 60,
    children: React.createElement('div', {
      style: {
        // SAFE ZONE PATTERN - Consistent margins from edges
        position: 'absolute',
        top: SAFE_ZONE_PADDING + 'px',    // 60px from top
        left: SAFE_ZONE_PADDING + 'px',   // 60px from left
        width: '200px',
        height: '80px',
        backgroundColor: 'rgba(76, 205, 196, 0.8)',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '16px',
        color: '#FFFFFF',
        zIndex: Z_CONTENT
      }
    }, 'Safe Zone')
  }),

  // Main title with fixed container - prevents size jumping
  React.createElement(Sequence, {
    from: SPRING_DELAY,
    durationInFrames: 150,
    children: React.createElement('div', {
      style: {
        position: 'absolute',
        top: '30%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '80%',
        height: TITLE_CONTAINER_HEIGHT + 'px', // Fixed height prevents jumping
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: Z_CONTENT
      }
    }, React.createElement('div', {
      style: {
        fontSize: '72px',
        fontWeight: 'bold',
        color: '#FFFFFF',
        textAlign: 'center',
        textShadow: '2px 2px 4px rgba(0,0,0,0.5)',
        opacity: titleOpacity,
        transform: 'scale(' + Math.max(0.1, titleScale) + ')', // Prevent scale(0) artifacts
        lineHeight: '1.1'
      }
    }, 'Professional Title'))
  }),

  // Typing effect with stable container
  React.createElement(Sequence, {
    from: 60,
    durationInFrames: 120,
    children: React.createElement('div', {
      style: {
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '70%',
        height: SUBTITLE_CONTAINER_HEIGHT + 'px', // Fixed container height
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        borderRadius: '12px',
        padding: CARD_PADDING + 'px',
        zIndex: Z_CONTENT
      }
    }, React.createElement('div', {
      style: {
        fontSize: '32px',
        color: '#FFFFFF',
        textAlign: 'center',
        fontWeight: '500',
        width: '100%' // Takes full container width
      }
    }, 'Dynamic Content Here'.substring(0, Math.floor(typingProgress * 'Dynamic Content Here'.length))))
  }),

  // Subtitle with smooth slide-in
  React.createElement(Sequence, {
    from: 90,
    durationInFrames: 180,
    children: React.createElement('div', {
      style: {
        position: 'absolute',
        top: '70%',
        left: '50%',
        transform: 'translate(-50%, calc(-50% + ' + subtitleY + 'px))',
        width: '60%',
        textAlign: 'center',
        fontSize: '28px',
        color: '#FFFFFF',
        opacity: subtitleOpacity,
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        padding: (CARD_PADDING / 2) + 'px ' + CARD_PADDING + 'px',
        borderRadius: '8px',
        zIndex: Z_CONTENT
      }
    }, 'Supporting Information')
  }),

  // === OVERLAY LAYER (Z-INDEX 3) ===

  // Sliding card container with proper positioning
  React.createElement(Sequence, {
    from: 150,
    durationInFrames: 120,
    children: React.createElement('div', {
      style: {
        position: 'absolute',
        top: SAFE_ZONE_PADDING + 'px',
        left: SAFE_ZONE_PADDING + 'px',
        right: SAFE_ZONE_PADDING + 'px',
        bottom: SAFE_ZONE_PADDING + 'px',
        pointerEvents: 'none',
        zIndex: Z_OVERLAY
      }
    }, React.createElement('div', {
      style: {
        position: 'absolute',
        bottom: '0',
        right: '0',
        width: '400px',
        height: '200px',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '16px',
        padding: CARD_PADDING + 'px',
        transform: 'translateX(' + cardX + 'px)',
        opacity: cardOpacity,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center'
      }
    }, 
      React.createElement('div', {
        style: {
          fontSize: '24px',
          fontWeight: 'bold',
          color: '#333333',
          marginBottom: '12px'
        }
      }, 'Key Information'),
      React.createElement('div', {
        style: {
          fontSize: '18px',
          color: '#666666',
          lineHeight: '1.4'
        }
      }, 'Supporting details with proper spacing and hierarchy')
    ))
  }),

  // === UI LAYER (Z-INDEX 4) ===

  // Logo with spring animation - top-right safe zone
  React.createElement(Sequence, {
    from: 180,
    durationInFrames: 180,
    children: React.createElement('div', {
      style: {
        position: 'absolute',
        top: (SAFE_ZONE_PADDING / 2) + 'px',
        right: (SAFE_ZONE_PADDING / 2) + 'px',
        width: '120px',
        height: '120px',
        backgroundColor: '#FF6B6B',
        borderRadius: '50%',
        transform: 'scale(' + Math.max(0.1, logoScale) + ')',
        opacity: logoOpacity,
        zIndex: Z_UI,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)'
      }
    }, React.createElement('div', {
      style: {
        color: '#FFFFFF',
        fontSize: '24px',
        fontWeight: 'bold'
      }
    }, 'LOGO'))
  }),

  // Progress indicator with smooth animation
  React.createElement(Sequence, {
    from: 0,
    durationInFrames: 360,
    children: React.createElement('div', {
      style: {
        position: 'absolute',
        bottom: (SAFE_ZONE_PADDING / 3) + 'px',
        left: SAFE_ZONE_PADDING + 'px',
        right: SAFE_ZONE_PADDING + 'px',
        height: '4px',
        backgroundColor: 'rgba(255, 255, 255, 0.3)',
        borderRadius: '2px',
        zIndex: Z_UI
      }
    }, React.createElement('div', {
      style: {
        width: ((frame / 360) * 100) + '%',
        height: '100%',
        backgroundColor: '#4ECDC4',
        borderRadius: '2px',
        transition: 'width 0.1s ease'
      }
    }))
  })
);`;
