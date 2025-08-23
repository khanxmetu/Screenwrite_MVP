#!/usr/bin/env python3
"""
Debug TSX Video Element Detection
"""

import re

# Sample from the real generated code
real_code = """
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
  })
);
"""

def debug_video_detection():
    print("🔍 Debugging Video Element Detection\n")
    
    # Test different patterns
    patterns = [
        r'React\.createElement\(Video,.*?\)',
        r'React\.createElement\(Sequence,.*?React\.createElement\(Video,.*?\).*?\)',
        r'React\.createElement\(Sequence,\s*{[^}]*},\s*React\.createElement\(Video,.*?\)\s*\)',
    ]
    
    for i, pattern in enumerate(patterns, 1):
        print(f"🔍 Pattern {i}: {pattern}")
        matches = list(re.finditer(pattern, real_code, re.DOTALL))
        print(f"   Found {len(matches)} matches:")
        
        for j, match in enumerate(matches, 1):
            print(f"   Match {j}: {match.group(0)[:100]}...")
        print()

if __name__ == "__main__":
    debug_video_detection()
