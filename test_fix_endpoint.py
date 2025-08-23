#!/usr/bin/env python3
"""
Test script for the /ai/fix-code endpoint
"""

import requests
import json

# Test data - broken code with a common error
test_data = {
    "broken_code": """return (
    <AbsoluteFill style={{ backgroundColor: 'blue' }}>
        <div style={{ 
            fontSize: 60, 
            color: 'white',
            textAlign: 'center',
            marginTop: useCurrentFrame() * 2
        }}>
            Hello World at frame {useCurrentFrame()}
        </div>
    </AbsoluteFill>
);""",
    "error_message": "ReferenceError: useCurrentFrame is not defined",
    "error_stack": "ReferenceError: useCurrentFrame is not defined\n    at TestComposition\n    at renderWithHooks",
    "user_request": "Create a simple hello world animation",
    "media_library": []
}

def test_fix_code_endpoint():
    """Test the /ai/fix-code endpoint"""
    
    endpoint_url = "http://127.0.0.1:8001/ai/fix-code"
    
    print("🧪 Testing /ai/fix-code endpoint...")
    print(f"📡 Sending request to: {endpoint_url}")
    print(f"💥 Error to fix: {test_data['error_message']}")
    print(f"🔧 Broken code preview: {test_data['broken_code'][:100]}...")
    
    try:
        # Send POST request
        response = requests.post(
            endpoint_url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Success!")
            print(f"🔧 Fixed code length: {len(result.get('corrected_code', ''))} characters")
            print(f"📝 Explanation: {result.get('explanation', 'N/A')}")
            print(f"⏱️ Duration: {result.get('duration', 'N/A')} seconds")
            print(f"✔️ Success flag: {result.get('success', False)}")
            
            if result.get('success'):
                print(f"\n🎯 CORRECTED CODE:")
                print("=" * 50)
                print(result.get('corrected_code', 'No code returned'))
                print("=" * 50)
            else:
                print(f"❌ Fix failed: {result.get('error_message', 'Unknown error')}")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the backend server running on port 8001?")
        print("💡 Start it with: cd backend && python main.py")
        
    except requests.exceptions.Timeout:
        print("❌ Timeout: The request took longer than 30 seconds")
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_fix_code_endpoint()
