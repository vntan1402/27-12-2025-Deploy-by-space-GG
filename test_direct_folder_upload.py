#!/usr/bin/env python3
"""
Test Direct Folder Upload
Try uploading directly to the known Crew Records folder ID
"""

import requests
import json
import base64
import time

# From the folder structure test, we know:
COMPANY_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzzpvHsThfQPjlz7kgr6Uontm-b0y-4AyishYmxPDIB72yxbBK29Zbv9oGiV3BHte2u/exec"
PARENT_FOLDER_ID = "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG"
SHIP_FOLDER_ID = "1WT4oA_lVPWADBJ7hRqT5LujVmTKoxnXx"
CREW_RECORDS_FOLDER_ID = "1AwvA3zzHKkbAxNst8-B1FYNsUflurnif"

def test_upload_variations():
    """Test different upload parameter variations"""
    print("🧪 Testing different upload parameter variations...")
    
    # Read passport file
    with open("/app/3_2O_THUONG_PP.pdf", 'rb') as f:
        file_content = f.read()
    
    base64_content = base64.b64encode(file_content).decode('utf-8')
    
    # Test variations
    test_cases = [
        {
            "name": "Original parameters",
            "payload": {
                'action': 'upload_file_with_folder_creation',
                'parent_folder_id': PARENT_FOLDER_ID,
                'ship_name': 'BROTHER 36',
                'category': 'Crew Records',
                'filename': '3_2O_THUONG_PP.pdf',
                'file_content': base64_content,
                'content_type': 'application/pdf'
            }
        },
        {
            "name": "Direct folder ID",
            "payload": {
                'action': 'upload_file_with_folder_creation',
                'parent_folder_id': CREW_RECORDS_FOLDER_ID,  # Direct to Crew Records folder
                'ship_name': 'BROTHER 36',
                'category': '',  # Empty category
                'filename': '3_2O_THUONG_PP.pdf',
                'file_content': base64_content,
                'content_type': 'application/pdf'
            }
        },
        {
            "name": "Case variations",
            "payload": {
                'action': 'upload_file_with_folder_creation',
                'parent_folder_id': PARENT_FOLDER_ID,
                'ship_name': 'BROTHER 36',
                'category': 'crew records',  # lowercase
                'filename': '3_2O_THUONG_PP.pdf',
                'file_content': base64_content,
                'content_type': 'application/pdf'
            }
        },
        {
            "name": "Alternative category name",
            "payload": {
                'action': 'upload_file_with_folder_creation',
                'parent_folder_id': PARENT_FOLDER_ID,
                'ship_name': 'BROTHER 36',
                'category': 'Crewlist',  # Alternative name
                'filename': '3_2O_THUONG_PP.pdf',
                'file_content': base64_content,
                'content_type': 'application/pdf'
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        
        try:
            response = requests.post(
                COMPANY_APPS_SCRIPT_URL,
                json=test_case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            print(f"   📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    success = result.get('success', False)
                    message = result.get('message', '')
                    file_id = result.get('file_id', '')
                    
                    if success:
                        print(f"   ✅ SUCCESS: {message}")
                        print(f"   📁 File ID: {file_id}")
                        return True  # Found working solution
                    else:
                        print(f"   ❌ FAILED: {message}")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON: {response.text[:200]}...")
            else:
                print(f"   ❌ HTTP error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return False

def test_apps_script_debug():
    """Test Apps Script with debug information"""
    print("\n🔍 Testing Apps Script with debug information...")
    
    try:
        payload = {
            'action': 'upload_file_with_folder_creation',
            'parent_folder_id': PARENT_FOLDER_ID,
            'ship_name': 'BROTHER 36',
            'category': 'Crew Records',
            'filename': 'debug_test.txt',
            'file_content': base64.b64encode(b'Debug test content').decode('utf-8'),
            'content_type': 'text/plain',
            'debug': True  # Request debug information
        }
        
        response = requests.post(
            COMPANY_APPS_SCRIPT_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("🔍 Debug response:")
                print(json.dumps(result, indent=2))
                return result
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON: {response.text}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main test execution"""
    print("🔍 Direct Folder Upload Test")
    print("🎯 Focus: Bypassing 'Category folder not found' issue")
    print("=" * 80)
    print(f"Known folder IDs:")
    print(f"  Parent: {PARENT_FOLDER_ID}")
    print(f"  Ship (BROTHER 36): {SHIP_FOLDER_ID}")
    print(f"  Crew Records: {CREW_RECORDS_FOLDER_ID}")
    print("=" * 80)
    
    # Test different upload variations
    success = test_upload_variations()
    
    # Test with debug information
    test_apps_script_debug()
    
    print("=" * 80)
    if success:
        print("✅ FOUND WORKING UPLOAD METHOD")
    else:
        print("❌ ALL UPLOAD METHODS FAILED - Apps Script bug confirmed")

if __name__ == "__main__":
    main()