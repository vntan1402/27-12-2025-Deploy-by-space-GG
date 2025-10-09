#!/usr/bin/env python3
"""
Test Google Drive Folder Structure
Check what folders exist and test folder creation
"""

import requests
import json
import time

# From the backend logs, we know:
COMPANY_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzzpvHsThfQPjlz7kgr6Uontm-b0y-4AyishYmxPDIB72yxbBK29Zbv9oGiV3BHte2u/exec"
PARENT_FOLDER_ID = "1mqi-BCcUXc_wN9QAUqnwik3KWTKZjelG"

def test_apps_script_info():
    """Get Apps Script service information"""
    print("🔍 Testing Apps Script service information...")
    
    try:
        # Test basic connectivity
        payload = {
            'action': 'get_service_info'
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
                print("✅ Apps Script service info:")
                print(json.dumps(result, indent=2))
                return True
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_folder_structure():
    """Test folder structure for BROTHER 36"""
    print("\n🗂️ Testing folder structure for BROTHER 36...")
    
    try:
        # Test getting folder structure
        payload = {
            'action': 'get_ship_folder_structure',
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
                print("✅ Folder structure response:")
                print(json.dumps(result, indent=2))
                return True
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_create_crew_records_folder():
    """Test creating Crew Records folder"""
    print("\n📁 Testing creation of Crew Records folder...")
    
    try:
        # Test creating the folder
        payload = {
            'action': 'create_folder_structure',
            'parent_folder_id': PARENT_FOLDER_ID,
            'ship_name': 'BROTHER 36',
            'category': 'Crew Records'
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
                print("✅ Folder creation response:")
                print(json.dumps(result, indent=2))
                return True
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_available_actions():
    """Test what actions are available"""
    print("\n🎯 Testing available actions...")
    
    actions_to_test = [
        'get_service_info',
        'list_supported_actions',
        'get_ship_folder_structure',
        'create_folder_structure',
        'upload_file_with_folder_creation',
        'list_ship_folders'
    ]
    
    for action in actions_to_test:
        try:
            payload = {'action': action}
            
            response = requests.post(
                COMPANY_APPS_SCRIPT_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"✅ {action}: {result.get('message', 'Success')}")
                except:
                    print(f"✅ {action}: Response received")
            else:
                print(f"❌ {action}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {action}: {e}")

def main():
    """Main test execution"""
    print("🔍 Google Drive Folder Structure Test")
    print("🎯 Focus: Understanding why 'Crew Records' folder not found")
    print("=" * 80)
    
    # Test 1: Service info
    test_apps_script_info()
    
    # Test 2: Available actions
    test_available_actions()
    
    # Test 3: Folder structure
    test_folder_structure()
    
    # Test 4: Create folder
    test_create_crew_records_folder()
    
    print("=" * 80)
    print("✅ FOLDER STRUCTURE TEST COMPLETED")

if __name__ == "__main__":
    main()