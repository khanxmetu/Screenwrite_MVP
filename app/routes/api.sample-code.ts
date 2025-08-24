import { type LoaderFunction } from "react-router";
import { readFileSync } from "fs";
import { join } from "path";

export const loader: LoaderFunction = async () => {
  try {
    // Read the simple test code file first
    const testCodePath = join(process.cwd(), "backend", "logs", "test_code_simple.js");
    const testCode = readFileSync(testCodePath, "utf-8");
    
    return new Response(testCode, {
      headers: {
        "Content-Type": "text/plain",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (error) {
    console.error("Failed to load sample code:", error);
    
    // Return fallback sample code
    const fallbackCode = `
const frame = currentFrameValue;
const opacity = interpolate(frame, [0, 30, 270, 300], [0, 1, 1, 0]);

return React.createElement(AbsoluteFill, {
  style: { 
    backgroundColor: '#4A90E2', 
    display: 'flex', 
    alignItems: 'center', 
    justifyContent: 'center',
    opacity: opacity
  }
}, React.createElement('div', {
  style: { 
    color: 'white', 
    fontSize: '48px', 
    fontWeight: 'bold',
    textAlign: 'center',
    padding: '20px'
  }
}, 'Sample Mode Active'));
    `;
    
    return new Response(fallbackCode, {
      headers: {
        "Content-Type": "text/plain",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
};
