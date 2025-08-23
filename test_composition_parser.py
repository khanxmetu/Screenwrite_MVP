#!/usr/bin/env python3
"""
Test script for composition state extraction function
"""

import sys
import os

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from analyzer import extract_composition_state

# Test cases
test_cases = [
    {
        "name": "Empty composition",
        "tsx_code": None,
        "expected_duration": 0.0
    },
    {
        "name": "Real Generated Code - Video Reordering with Text",
        "tsx_code": """
// Generated at: 2025-08-21 23:40:20
// User Request: Analyze the video 'Shore - Cinematic Nature Video (Sony FX3) - Jack McCann (720p, h264).mp4' to identify the exact start time (in seconds) of the sunset scene. Once the sunset scene is detected, add a text element with the content 'Sunset' to the composition. This text should be centered horizontally and vertically on the screen, have a white color, and a font size of 100px. The text should appear for a duration of 5 seconds, starting precisely at the beginning of the identified sunset scene.
// AI-determined Duration: 172.332063 seconds
// Attempt: 1/3
// ======================================


const frame = useCurrentFrame();
const { fps } = useVideoConfig();

const videoSrc = 'blob:http://localhost:5173/2ffc470e-70f9-429b-b095-734b7aeccc73';
const videoTotalDurationSeconds = 172.332063;
const videoSegment1StartSeconds = 30;
const videoSegment1EndSeconds = videoTotalDurationSeconds;
const videoSegment2StartSeconds = 0;
const videoSegment2EndSeconds = 30;

const segment1DurationFrames = (videoSegment1EndSeconds - videoSegment1StartSeconds) * fps;
const segment2DurationFrames = (videoSegment2EndSeconds - videoSegment2StartSeconds) * fps;

// Sunset scene details
const sunsetSceneOriginalStartSeconds = 148; // Identified sunset scene start in original video
const sunsetTextDurationSeconds = 5;

// Calculate the frame where the sunset scene starts within the composition's timeline.
// The first sequence starts at frame 0 and plays video from 30s onwards.
// So, an original video time of 148s corresponds to (148 - 30) seconds into the first sequence.
const sunsetTextFromFrame = (sunsetSceneOriginalStartSeconds - videoSegment1StartSeconds) * fps;
const sunsetTextDurationFrames = sunsetTextDurationSeconds * fps;

return React.createElement(AbsoluteFill, {},
  // First video segment: 30 seconds to end
  React.createElement(Sequence, {
    from: 0,
    durationInFrames: segment1DurationFrames,
    children: React.createElement(Video, {
      src: videoSrc,
      startFrom: videoSegment1StartSeconds * fps,
      endAt: videoSegment1EndSeconds * fps,
      style: {
        width: '100%',
        height: '100%',
        objectFit: 'cover'
      }
    })
  }),

  // Second video segment: 0 seconds to 30 seconds (plays after the first segment)
  React.createElement(Sequence, {
    from: segment1DurationFrames,
    durationInFrames: segment2DurationFrames,
    children: React.createElement(Video, {
      src: videoSrc,
      startFrom: videoSegment2StartSeconds * fps,
      endAt: videoSegment2EndSeconds * fps,
      style: {
        width: '100%',
        height: '100%',
        objectFit: 'cover'
      }
    })
  }),

  // Sunset text overlay
  React.createElement(Sequence, {
    from: sunsetTextFromFrame,
    durationInFrames: sunsetTextDurationFrames,
    children: React.createElement(AbsoluteFill, {
      style: {
        justifyContent: 'center',
        alignItems: 'center'
      }
    },
      React.createElement('h1', {
        style: {
          color: 'white',
          fontSize: 100,
          textAlign: 'center'
        }
      }, 'Sunset')
    )
  })
);
        """,
        "expected_duration": 172.332063
    },
    {
        "name": "Simple video composition",
        "tsx_code": """
        // DURATION: 15.5
        
        return (
          <AbsoluteFill style={{ backgroundColor: "#000000" }}>
            <Sequence from={0} durationInFrames={450}>
              <Video src="http://localhost:8000/media/video1.mp4" />
            </Sequence>
            <Sequence from={300} durationInFrames={150}>
              <Audio src="http://localhost:8000/media/audio1.mp3" />
            </Sequence>
          </AbsoluteFill>
        );
        """,
        "expected_duration": 15.5
    }
]

def test_composition_parser():
    print("🧪 Testing TSX Video Element Filtering Function\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 50)
        
        # Extract composition state
        result = extract_composition_state(test_case['tsx_code'])
        
        # Print results
        print(f"📊 Results:")
        print(f"  Duration: {result['total_duration']}s (expected: {test_case['expected_duration']}s)")
        print(f"  Video elements found: {result['video_count']}")
        
        # Show filtered TSX
        if result['filtered_tsx']:
            print(f"  Filtered TSX (video elements only):")
            print("  " + "="*40)
            for line in result['filtered_tsx'].split('\n'):
                print(f"  {line}")
            print("  " + "="*40)
        else:
            print(f"  No video elements found - filtered TSX is empty")
        
        # Validation
        duration_match = result['total_duration'] == test_case['expected_duration']
        print(f"  ✅ Duration correct: {duration_match}")
        
        print()

if __name__ == "__main__":
    test_composition_parser()
