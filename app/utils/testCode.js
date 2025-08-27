// Simple test code for Remotion - paste your code here
// This file is imported as a module to avoid TypeScript parsing issues

const testCode = `
const frame = currentFrameValue;
const { width, height, fps } = videoConfigValue;

const opacity = interpolate(frame, [0, 30, 270, 300], [0, 1, 1, 0]);
const scale = interpolate(frame, [0, 60, 240, 300], [0.5, 1.2, 1.2, 0.5]);
const rotation = interpolate(frame, [0, 300], [0, 360]);

return React.createElement(AbsoluteFill, {
  style: {
    backgroundColor: '#2563eb',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    opacity: opacity
  }
}, React.createElement('div', {
  style: {
    transform: 'scale(' + scale + ') rotate(' + rotation + 'deg)',
    color: 'white',
    fontSize: '48px',
    fontWeight: 'bold',
    textAlign: 'center',
    padding: '20px',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    border: '2px solid rgba(255, 255, 255, 0.3)'
  }
}, 'Sample Mode Active'));
`;

export default testCode;