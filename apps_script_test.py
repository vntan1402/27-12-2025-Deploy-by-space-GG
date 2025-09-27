#!/usr/bin/env python3
"""
Apps Script Direct Test - Test the Google Apps Script URL directly
to understand if it's a timeout issue or a 404 configuration issue
"""

import requests
import json
import time
from datetime import datetime

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{level}] {message}")

def test_apps_script_direct():
    """Test the Apps Script URL directly with different payloads"""
    
    apps_script_url = "https://script.google.com/macros/s/AKfycbxVm_mf2ghDgpY78FdLVcjMxdVa_LB94abysbRzoycod8pvTWgKdLrOvkcp16WVWW0/exec"
    
    log_message("🔧 TESTING APPS SCRIPT URL DIRECTLY")
    log_message(f"   URL: {apps_script_url}")
    log_message("=" * 80)
    
    # Test 1: Simple test_connection
    log_message("🧪 Test 1: Simple test_connection")
    test_payload = {
        "action": "test_connection",
        "folder_id": "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG"
    }
    
    try:
        log_message(f"   Payload: {json.dumps(test_payload, indent=3)}")
        start_time = time.time()
        response = requests.post(apps_script_url, json=test_payload, timeout=60)
        end_time = time.time()
        
        log_message(f"   Response time: {end_time - start_time:.2f} seconds")
        log_message(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                log_message("   ✅ Apps Script responded successfully")
                log_message(f"   Response: {json.dumps(result, indent=6)}")
            except:
                log_message("   ✅ Apps Script responded but not JSON")
                log_message(f"   Response: {response.text[:500]}")
        else:
            log_message(f"   ❌ Apps Script failed: {response.status_code}")
            log_message(f"   Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        log_message("   ❌ TIMEOUT ERROR - Apps Script took too long to respond")
    except Exception as e:
        log_message(f"   ❌ ERROR: {str(e)}")
    
    # Test 2: Create folder structure (the actual failing call)
    log_message("\n🧪 Test 2: Create complete ship structure (the failing call)")
    create_payload = {
        "action": "create_complete_ship_structure",
        "parent_folder_id": "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG",
        "ship_name": "APPS_SCRIPT_TEST_SHIP",
        "company_id": "78fdb82e-bc68-4618-b277-3f69e8840f1e",
        "backend_api_url": "https://marinetrack-1.preview.emergentagent.com"
    }
    
    try:
        log_message(f"   Payload: {json.dumps(create_payload, indent=3)}")
        start_time = time.time()
        response = requests.post(apps_script_url, json=create_payload, timeout=60)
        end_time = time.time()
        
        log_message(f"   Response time: {end_time - start_time:.2f} seconds")
        log_message(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                log_message("   ✅ Folder creation successful")
                log_message(f"   Response: {json.dumps(result, indent=6)}")
            except:
                log_message("   ✅ Apps Script responded but not JSON")
                log_message(f"   Response: {response.text[:500]}")
        else:
            log_message(f"   ❌ Folder creation failed: {response.status_code}")
            log_message(f"   Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        log_message("   ❌ TIMEOUT ERROR - Apps Script took too long to respond")
        log_message("   🎯 THIS IS THE ROOT CAUSE OF THE ISSUE!")
    except Exception as e:
        log_message(f"   ❌ ERROR: {str(e)}")
    
    # Test 3: Check if Apps Script makes callbacks to backend
    log_message("\n🧪 Test 3: Check for potential callback issues")
    log_message("   💡 The Apps Script might be trying to call back to the backend")
    log_message("   💡 If the backend API URL is not accessible from Apps Script, it could cause timeouts")
    log_message("   💡 Backend API URL being sent: https://marinetrack-1.preview.emergentagent.com")
    
    # Test if the backend URL is accessible
    try:
        log_message("   🔍 Testing if backend URL is accessible...")
        backend_test = requests.get("https://marinetrack-1.preview.emergentagent.com/api/sidebar-structure", timeout=10)
        log_message(f"   Backend accessibility: {backend_test.status_code}")
        if backend_test.status_code == 200:
            log_message("   ✅ Backend URL is accessible from external requests")
        else:
            log_message("   ⚠️ Backend URL returned non-200 status")
    except Exception as e:
        log_message(f"   ❌ Backend URL not accessible: {str(e)}")
        log_message("   🎯 THIS COULD BE WHY APPS SCRIPT TIMES OUT!")

def main():
    """Main test execution"""
    log_message("🔧 APPS SCRIPT DIRECT TEST")
    log_message("🎯 Focus: Test Google Apps Script URL directly to identify timeout vs 404 issues")
    log_message("📋 Goal: Understand if the issue is Apps Script timeout or missing backend endpoints")
    log_message("=" * 100)
    
    test_apps_script_direct()
    
    log_message("\n🎯 ANALYSIS SUMMARY")
    log_message("=" * 50)
    log_message("Based on the backend logs, the issue is:")
    log_message("1. ✅ AMCSC company Google Drive configuration EXISTS")
    log_message("2. ✅ Apps Script URL is valid and configured")
    log_message("3. ✅ Ship creation succeeds in database")
    log_message("4. ❌ Apps Script calls TIMEOUT after 30 seconds")
    log_message("5. ⚠️ Ship creation continues despite Google Drive failure")
    log_message("")
    log_message("🔍 ROOT CAUSE ANALYSIS:")
    log_message("- The error 'Failed to create ship folder: 404: Company Google Drive not configured' is NOT occurring")
    log_message("- Instead, we have timeout errors: 'HTTPSConnectionPool(host='script.google.com', port=443): Read timed out'")
    log_message("- The Apps Script is taking longer than 30 seconds to respond")
    log_message("- This could be due to:")
    log_message("  a) Apps Script performance issues")
    log_message("  b) Apps Script trying to callback to backend and failing")
    log_message("  c) Google Drive API rate limiting")
    log_message("  d) Network connectivity issues")
    log_message("")
    log_message("💡 RECOMMENDATION:")
    log_message("- The user's reported error may be intermittent or from a different scenario")
    log_message("- Current issue is timeout, not 404 configuration error")
    log_message("- Need to investigate Apps Script performance and callback mechanisms")

if __name__ == "__main__":
    main()