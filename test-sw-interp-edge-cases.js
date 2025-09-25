#!/usr/bin/env node

/**
 * Test script to check SW.interp edge cases
 * Testing what happens with duplicate/decreasing timestamps
 */

// Mock Remotion's interpolate function to understand behavior
function mockInterpolate(input, inputRange, outputRange, options = {}) {
    console.log(`interpolate(${input}, [${inputRange.join(', ')}], [${outputRange.join(', ')}])`);
    
    // Check for edge cases
    if (inputRange.length !== outputRange.length) {
        throw new Error('Input and output ranges must have same length');
    }
    
    if (inputRange.length < 2) {
        throw new Error('Input range must have at least 2 values');
    }
    
    // Check for duplicate values in input range
    for (let i = 1; i < inputRange.length; i++) {
        if (inputRange[i] === inputRange[i-1]) {
            console.warn(`⚠️  Duplicate timestamp at index ${i}: ${inputRange[i]}`);
            // What should happen? Return the first value? Average? Error?
        }
        
        if (inputRange[i] < inputRange[i-1]) {
            console.warn(`⚠️  Decreasing timestamp at index ${i}: ${inputRange[i-1]} -> ${inputRange[i]}`);
            // What should happen? Error? Sort automatically?
        }
    }
    
    // Simple linear interpolation for testing
    if (input <= inputRange[0]) return outputRange[0];
    if (input >= inputRange[inputRange.length - 1]) return outputRange[outputRange.length - 1];
    
    for (let i = 1; i < inputRange.length; i++) {
        if (input <= inputRange[i]) {
            const t = (input - inputRange[i-1]) / (inputRange[i] - inputRange[i-1]);
            return outputRange[i-1] + t * (outputRange[i] - outputRange[i-1]);
        }
    }
    
    return outputRange[outputRange.length - 1];
}

console.log("🧪 Testing SW.interp edge cases\n");

// Test 1: Normal case
console.log("1. Normal case:");
try {
    const result1 = mockInterpolate(15, [0, 30, 60], [0, 1, 0]);
    console.log(`✅ Result: ${result1}\n`);
} catch (error) {
    console.log(`❌ Error: ${error.message}\n`);
}

// Test 2: Duplicate timestamps
console.log("2. Duplicate timestamps:");
try {
    const result2 = mockInterpolate(30, [0, 30, 30, 60], [0, 1, 1, 0]);
    console.log(`✅ Result: ${result2}\n`);
} catch (error) {
    console.log(`❌ Error: ${error.message}\n`);
}

// Test 3: Decreasing timestamps  
console.log("3. Decreasing timestamps:");
try {
    const result3 = mockInterpolate(15, [0, 30, 20, 60], [0, 1, 0.5, 0]);
    console.log(`✅ Result: ${result3}\n`);
} catch (error) {
    console.log(`❌ Error: ${error.message}\n`);
}

// Test 4: All same timestamps
console.log("4. All same timestamps:");
try {
    const result4 = mockInterpolate(30, [30, 30, 30], [0, 1, 0]);
    console.log(`✅ Result: ${result4}\n`);
} catch (error) {
    console.log(`❌ Error: ${error.message}\n`);
}

// Test 5: Single duplicate at start
console.log("5. Single duplicate at start:");
try {
    const result5 = mockInterpolate(15, [0, 0, 30], [0, 0.5, 1]);
    console.log(`✅ Result: ${result5}\n`);
} catch (error) {
    console.log(`❌ Error: ${error.message}\n`);
}

console.log("📝 Summary:");
console.log("- SW.interp relies on Remotion's interpolate function");
console.log("- Need to test actual Remotion behavior with these edge cases");
console.log("- Consider adding validation in SW.interp wrapper");
