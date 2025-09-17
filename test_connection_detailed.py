#!/usr/bin/env python3
"""
Detailed Test Connection Functionality Test
Testing the "Test Connection" functionality specifically for the review request.
"""

import requests
import json
import sys

def test_apps_script_detailed():
    """Test the Apps Script URL with various payloads"""
    apps_script_url = "https://script.google.com/macros/s/AKfycbzgEVRtLEGylJem_1826xgwdf_XYzQfv7IYiPlvZggq-6Yw4fKW3NZ-QG3yE-T-OlnF/exec"
    test_folder_id = "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
    
    print("🔍 DETAILED APPS SCRIPT CONNECTION TESTING")
    print("=" * 60)
    print(f"URL: {apps_script_url}")
    print(f"Test Folder ID: {test_folder_id}")
    print()
    
    # Test 1: Basic test_connection
    print("Test 1: Basic test_connection")
    try:
        payload = {
            "action": "test_connection",
            "folder_id": test_folder_id
        }
        
        response = requests.post(apps_script_url, json=payload, timeout=30)
        print(f"  Status Code: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('content-type', 'Unknown')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=4)}")
                
                if data.get('success'):
                    print("  ✅ Test connection PASSED")
                else:
                    print("  ❌ Test connection FAILED")
                    print(f"  Error: {data.get('error', 'Unknown error')}")
            except json.JSONDecodeError:
                print(f"  ❌ Non-JSON response: {response.text[:200]}")
        else:
            print(f"  ❌ HTTP Error: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"  ❌ Request failed: {str(e)}")
    
    print()
    
    # Test 2: Test with invalid folder ID
    print("Test 2: Test with invalid folder ID")
    try:
        payload = {
            "action": "test_connection",
            "folder_id": "invalid_folder_id_12345"
        }
        
        response = requests.post(apps_script_url, json=payload, timeout=30)
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=4)}")
                
                if not data.get('success'):
                    print("  ✅ Correctly rejected invalid folder ID")
                else:
                    print("  ⚠️ Unexpectedly accepted invalid folder ID")
            except json.JSONDecodeError:
                print(f"  ❌ Non-JSON response: {response.text[:200]}")
        else:
            print(f"  Status: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Request failed: {str(e)}")
    
    print()
    
    # Test 3: Test with no action
    print("Test 3: Test with no action parameter")
    try:
        payload = {
            "folder_id": test_folder_id
        }
        
        response = requests.post(apps_script_url, json=payload, timeout=30)
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=4)}")
            except json.JSONDecodeError:
                print(f"  ❌ Non-JSON response: {response.text[:200]}")
        else:
            print(f"  Status: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Request failed: {str(e)}")
    
    print()
    
    # Test 4: Test GET request (should fail)
    print("Test 4: Test GET request (should fail or redirect)")
    try:
        response = requests.get(apps_script_url, timeout=30)
        print(f"  Status Code: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('content-type', 'Unknown')}")
        
        if 'text/html' in response.headers.get('content-type', ''):
            print("  ✅ Correctly returned HTML (likely redirect or error page)")
        elif response.status_code == 405:
            print("  ✅ Correctly rejected GET request (Method Not Allowed)")
        else:
            print(f"  Response preview: {response.text[:200]}")
            
    except Exception as e:
        print(f"  ❌ Request failed: {str(e)}")

def main():
    test_apps_script_detailed()
    return 0

if __name__ == "__main__":
    sys.exit(main())