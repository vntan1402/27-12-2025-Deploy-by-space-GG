#!/usr/bin/env python3
"""
Test Real Google Drive Folder Structure
Using the actual supported actions from Apps Script v3.8
"""

import requests
import json
import time

# From the backend logs, we know:
COMPANY_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzzpvHsThfQPjlz7kgr6Uontm-b0y-4AyishYmxPDIB72yxbBK29Zbv9oGiV3BHte2u/exec"
PARENT_FOLDER_ID = "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG"

def test_get_folder_structure():
    """Test get_folder_structure action"""
    print("🗂️ Testing get_folder_structure...")
    
    try:
        payload = {
            'action': 'get_folder_structure',
            'parent_folder_id': PARENT_FOLDER_ID,
            'ship_name': 'BROTHER 36'
        }
        
        response = requests.post(
            COMPANY_APPS_SCRIPT_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Folder structure:")
                print(json.dumps(result, indent=2))
                return result
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_check_ship_folder_exists():
    """Test check_ship_folder_exists action"""
    print("\n🔍 Testing check_ship_folder_exists...")
    
    try:
        payload = {
            'action': 'check_ship_folder_exists',
            'parent_folder_id': PARENT_FOLDER_ID,
            'ship_name': 'BROTHER 36'
        }
        
        response = requests.post(
            COMPANY_APPS_SCRIPT_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Ship folder check:")
                print(json.dumps(result, indent=2))
                return result
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_create_complete_ship_structure():
    """Test create_complete_ship_structure action"""
    print("\n🏗️ Testing create_complete_ship_structure...")
    
    try:
        payload = {
            'action': 'create_complete_ship_structure',
            'parent_folder_id': PARENT_FOLDER_ID,
            'ship_name': 'BROTHER 36'
        }
        
        response = requests.post(
            COMPANY_APPS_SCRIPT_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # Longer timeout for folder creation
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Ship structure creation:")
                print(json.dumps(result, indent=2))
                return result
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_upload_with_proper_structure():
    """Test upload after ensuring folder structure exists"""
    print("\n📤 Testing upload with proper folder structure...")
    
    try:
        # Read passport file
        with open("/app/3_2O_THUONG_PP.pdf", 'rb') as f:
            file_content = f.read()
        
        import base64
        
        payload = {
            'action': 'upload_file_with_folder_creation',
            'parent_folder_id': PARENT_FOLDER_ID,
            'ship_name': 'BROTHER 36',
            'category': 'Crew Records',
            'filename': '3_2O_THUONG_PP.pdf',
            'file_content': base64.b64encode(file_content).decode('utf-8'),
            'content_type': 'application/pdf'
        }
        
        response = requests.post(
            COMPANY_APPS_SCRIPT_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Upload result:")
                print(json.dumps(result, indent=2))
                return result
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main test execution"""
    print("🔍 Real Google Drive Folder Structure Test")
    print("🎯 Focus: Understanding and fixing 'Crew Records' folder issue")
    print("=" * 80)
    
    # Step 1: Check if ship folder exists
    ship_check = test_check_ship_folder_exists()
    
    # Step 2: Get current folder structure
    folder_structure = test_get_folder_structure()
    
    # Step 3: Create complete ship structure if needed
    if ship_check and not ship_check.get('success', False):
        print("\n🏗️ Ship folder doesn't exist, creating complete structure...")
        create_result = test_create_complete_ship_structure()
        
        # Step 4: Check structure again after creation
        if create_result and create_result.get('success', False):
            print("\n🔍 Checking folder structure after creation...")
            folder_structure = test_get_folder_structure()
    
    # Step 5: Try upload now
    upload_result = test_upload_with_proper_structure()
    
    print("=" * 80)
    if upload_result and upload_result.get('success', False):
        print("✅ UPLOAD TEST COMPLETED SUCCESSFULLY")
    else:
        print("❌ UPLOAD TEST FAILED - Need to investigate further")

if __name__ == "__main__":
    main()