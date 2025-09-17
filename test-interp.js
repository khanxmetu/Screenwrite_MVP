// Test script to verify context-aware interp function
// This will help us debug the timing issue

const testBlueprint = [
  {
    "clips": [
      {
        "id": "test-clip",
        "startTimeInSeconds": 3,
        "endTimeInSeconds": 6,
        "element": "return React.createElement('div', { style: { opacity: SW.interp(3, 4, 0, 1) } }, 'Test');"
      }
    ]
  }
];

console.log("Testing context-aware interp implementation...");

// Test case: Clip starts at 3s, interp should be SW.interp(3, 4, 0, 1)
// With individual sequence: sequenceStartTime = 3
// Expected: interp(3, 4, 0, 1, 'out', 3) 
// Should normalize to: interp(0, 1, 0, 1) in local sequence time

console.log("Expected behavior:");
console.log("- Clip starts at 3s (90 frames at 30fps)");
console.log("- SW.interp(3, 4, 0, 1) should animate from frame 0-30 in local sequence");
console.log("- sequenceStartTime should be 3");

// The issue is likely that sequenceStartTime isn't being passed correctly
// or the timing calculation is wrong
