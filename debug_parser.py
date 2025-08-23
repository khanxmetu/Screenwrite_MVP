#!/usr/bin/env python3
"""
Debug script to understand sequence detection
"""

import sys
import os
import re

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Test code from the real generated composition
real_code = """
// Generated at: 2025-08-21 22:46:27
// AI-determined Duration: 20.04 seconds

const frame = useCurrentFrame();
const { fps } = useVideoConfig();

const videoDurationInFrames = Math.ceil(20.04 * fps); // Ensure full video plays
const fadeInDurationFrames = 15; // Duration for fade-in animation

return React.createElement(AbsoluteFill, {},
  // Video 'Shore_first_20_seconds.mp4'
  React.createElement(Sequence, {
    from: 0,
    durationInFrames: videoDurationInFrames,
    children: React.createElement(Video, {
      src: 'blob:http://localhost:5173/a2a9ff8f-faf7-4102-972f-d9ad42da7316',
      style: {
        width: '100%',
        height: '100%',
        objectFit: 'cover'
      }
    })
  }),

  // Text 1: 'Black Screen' (Existing)
  React.createElement(Sequence, {
    from: 0,
    durationInFrames: 1 * fps,
    children: (() => {
      return React.createElement('div', {
        style: { color: '#FFFFFF' }
      }, 'Black Screen');
    })()
  }),

  // Text 2: 'Sunlit Purple Flowers' (Existing)
  React.createElement(Sequence, {
    from: 1 * fps,
    durationInFrames: (9 - 1) * fps,
    children: (() => {
      return React.createElement('div', {
        style: { color: '#FFFFFF' }
      }, 'Sunlit Purple Flowers');
    })()
  })
);
"""

def debug_sequence_detection():
    print("🔍 Debugging Sequence Detection\n")
    
    # The sequence patterns from the analyzer
    sequence_patterns = [
        r'<Sequence[^>]*from={(\d+(?:\.\d+)?)}[^>]*durationInFrames={(\d+(?:\.\d+)?)}',
        r'React\.createElement\(Sequence,\s*{\s*from:\s*(\d+(?:\.\d+)?)[^}]*durationInFrames:\s*([^,}]+)'
    ]
    
    print("📋 Expected Sequences:")
    print("1. Video sequence: from=0, duration=videoDurationInFrames")
    print("2. Text 1: from=0, duration=1*fps") 
    print("3. Text 2: from=1*fps, duration=(9-1)*fps")
    print()
    
    for i, pattern in enumerate(sequence_patterns, 1):
        print(f"🔍 Pattern {i}: {pattern}")
        matches = list(re.finditer(pattern, real_code))
        print(f"   Found {len(matches)} matches:")
        
        for j, match in enumerate(matches, 1):
            print(f"   Match {j}:")
            print(f"     Full match: {match.group(0)[:100]}...")
            print(f"     Group 1 (from): {match.group(1)}")
            print(f"     Group 2 (duration): {match.group(2)}")
        print()

if __name__ == "__main__":
    debug_sequence_detection()
