#!/usr/bin/env python3
"""
Simple Apps Script Test - Direct call to Company Apps Script
"""

import requests
import json
import base64
import time

# From the backend logs, we know:
COMPANY_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzzpvHsThfQPjlz7kgr6Uontm-b0y-4AyishYmxPDIB72yxbBK29Zbv9oGiV3BHte2u/exec"
PARENT_FOLDER_ID = "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG"
PASSPORT_FILE = "/app/3_2O_THUONG_PP.pdf"

def test_company_apps_script():
    """Test Company Apps Script directly"""
    print("🧪 Testing Company Apps Script directly")
    print("=" * 60)
    
    try:
        # Read passport file
        with open(PASSPORT_FILE, 'rb') as f:
            file_content = f.read()
        
        print(f"📄 File size: {len(file_content):,} bytes")
        
        # Prepare payload exactly as dual_apps_script_manager does
        payload = {
            'action': 'upload_file_with_folder_creation',
            'parent_folder_id': PARENT_FOLDER_ID,
            'ship_name': 'BROTHER 36',
            'category': 'Crew Records',
            'filename': '3_2O_THUONG_PP.pdf',
            'file_content': base64.b64encode(file_content).decode('utf-8'),
            'content_type': 'application/pdf'
        }
        
        print(f"📤 Calling Company Apps Script...")
        print(f"   URL: {COMPANY_APPS_SCRIPT_URL}")
        print(f"   Action: {payload['action']}")
        print(f"   Parent Folder ID: {payload['parent_folder_id']}")
        print(f"   Ship Name: {payload['ship_name']}")
        print(f"   Category: {payload['category']}")
        print(f"   Filename: {payload['filename']}")
        print(f"   Content Type: {payload['content_type']}")
        print(f"   Base64 content length: {len(payload['file_content']):,} chars")
        
        # Make the call
        start_time = time.time()
        response = requests.post(
            COMPANY_APPS_SCRIPT_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        print(f"⏱️ Apps Script response time: {processing_time:.1f} seconds")
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Apps Script responded successfully")
                print(f"📋 Response data:")
                
                # Pretty print the response
                print(json.dumps(result, indent=2))
                
                # Check for success indicators
                success = result.get('success', False)
                message = result.get('message', '')
                error = result.get('error', '')
                file_id = result.get('file_id', '')
                
                print(f"\n🎯 Key indicators:")
                print(f"   Success: {success}")
                print(f"   Message: {message}")
                print(f"   Error: {error}")
                print(f"   File ID: {file_id}")
                
                if success and file_id:
                    print("✅ File upload appears successful")
                    return True
                else:
                    print("❌ File upload failed or incomplete")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response: {e}")
                print(f"   Raw response: {response.text[:1000]}...")
                return False
        else:
            print(f"❌ Apps Script HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Apps Script: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test execution"""
    print("🔍 Simple Apps Script Test for Passport Upload")
    print("📄 Testing with REAL passport file: 3. 2O THUONG - PP.pdf")
    print("🎯 Focus: Direct Company Apps Script call")
    print("=" * 80)
    
    success = test_company_apps_script()
    
    print("=" * 80)
    if success:
        print("✅ APPS SCRIPT TEST COMPLETED SUCCESSFULLY")
    else:
        print("❌ APPS SCRIPT TEST FAILED")
    
    return success

if __name__ == "__main__":
    main()