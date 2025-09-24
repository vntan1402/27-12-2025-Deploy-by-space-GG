#!/usr/bin/env python3
"""
Enhanced Ship Creation Test - Focus on Google Drive Folder Creation Error
Review Request: Test ship creation with enhanced logging to capture the exact 
"Failed to create ship folder: 404: Company Google Drive not configured" error.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://shipai-system.preview.emergentagent.com/api"

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{level}] {message}")

def authenticate():
    """Authenticate with admin1/123456 (AMCSC company user)"""
    try:
        log_message("🔐 Authenticating with admin1/123456 (AMCSC company user)...")
        
        login_data = {
            "username": "admin1",
            "password": "123456",
            "remember_me": False
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=30)
        log_message(f"   Authentication response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user = data.get("user", {})
            
            log_message("✅ Authentication successful")
            log_message(f"   User: {user.get('username')} ({user.get('role')})")
            log_message(f"   Company: {user.get('company')}")
            
            return token, user
        else:
            log_message(f"❌ Authentication failed: {response.status_code}")
            try:
                error_data = response.json()
                log_message(f"   Error: {error_data.get('detail')}")
            except:
                log_message(f"   Error: {response.text[:200]}")
            return None, None
            
    except Exception as e:
        log_message(f"❌ Authentication error: {str(e)}", "ERROR")
        return None, None

def get_company_info(token):
    """Get AMCSC company information and Google Drive config"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        log_message("🏢 Getting company information...")
        response = requests.get(f"{BACKEND_URL}/companies", headers=headers, timeout=30)
        log_message(f"   Companies response: {response.status_code}")
        
        if response.status_code == 200:
            companies = response.json()
            log_message(f"   Found {len(companies)} companies")
            
            # Find AMCSC company
            amcsc_company = None
            for company in companies:
                company_names = [
                    company.get('name', ''),
                    company.get('name_en', ''),
                    company.get('name_vn', '')
                ]
                if 'AMCSC' in str(company_names).upper():
                    amcsc_company = company
                    break
            
            if amcsc_company:
                company_id = amcsc_company.get('id')
                log_message(f"   ✅ Found AMCSC company (ID: {company_id})")
                
                # Check Google Drive configuration
                log_message("   🔧 Checking Google Drive configuration...")
                config_response = requests.get(f"{BACKEND_URL}/companies/{company_id}/gdrive/config", headers=headers, timeout=30)
                log_message(f"   Google Drive config response: {config_response.status_code}")
                
                if config_response.status_code == 200:
                    config_data = config_response.json()
                    log_message("   ✅ Google Drive configuration found")
                    log_message(f"   Config: {json.dumps(config_data, indent=6)}")
                    return company_id, config_data
                else:
                    log_message(f"   ❌ Google Drive config not found: {config_response.status_code}")
                    try:
                        error_data = config_response.json()
                        log_message(f"   Error: {error_data.get('detail')}")
                    except:
                        log_message(f"   Error: {config_response.text[:200]}")
                    return company_id, None
            else:
                log_message("   ❌ AMCSC company not found")
                return None, None
        else:
            log_message(f"   ❌ Failed to get companies: {response.status_code}")
            return None, None
            
    except Exception as e:
        log_message(f"❌ Company info error: {str(e)}", "ERROR")
        return None, None

def create_test_ship(token):
    """Create a test ship to trigger Google Drive folder creation"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Generate unique ship data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ship_data = {
            "name": f"TEST_SHIP_{timestamp}",
            "imo": f"TEST{timestamp[-6:]}",
            "company": "AMCSC",
            "flag": "Panama",
            "ship_type": "General Cargo",
            "gross_tonnage": 5000,
            "deadweight": 8000,
            "built_year": 2020,
            "ship_owner": "Test Owner"
        }
        
        log_message("🚢 Creating test ship to trigger Google Drive folder creation...")
        log_message(f"   Ship data: {json.dumps(ship_data, indent=3)}")
        
        # Mark the start of ship creation
        log_message("🎬 === SHIP CREATION STARTING - MONITORING FOR GOOGLE DRIVE ERRORS ===")
        
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/ships", json=ship_data, headers=headers, timeout=120)
        end_time = time.time()
        
        log_message("🎬 === SHIP CREATION COMPLETED ===")
        log_message(f"   Response status: {response.status_code}")
        log_message(f"   Response time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            ship_response = response.json()
            log_message("   ✅ Ship creation successful")
            log_message(f"   Ship ID: {ship_response.get('id')}")
            log_message(f"   Ship Name: {ship_response.get('name')}")
            return ship_response
            
        elif response.status_code == 400:
            log_message("   ❌ Ship creation failed with 400 Bad Request")
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', 'Unknown error')
                log_message(f"   Error: {error_detail}")
                
                # Check for our target error
                if "Failed to create ship folder" in str(error_detail) and "404" in str(error_detail):
                    log_message("   🎯 FOUND TARGET ERROR: 'Failed to create ship folder: 404: Company Google Drive not configured'")
                    return {"error": error_detail, "target_error_found": True}
                    
            except Exception as parse_error:
                error_detail = response.text[:500]
                log_message(f"   Error (raw): {error_detail}")
                
                if "Failed to create ship folder" in error_detail and "404" in error_detail:
                    log_message("   🎯 FOUND TARGET ERROR: 'Failed to create ship folder: 404: Company Google Drive not configured'")
                    return {"error": error_detail, "target_error_found": True}
            
            return {"error": error_detail, "status_code": response.status_code}
            
        else:
            log_message(f"   ❌ Ship creation failed with status {response.status_code}")
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', 'Unknown error')
            except:
                error_detail = response.text[:500]
            
            log_message(f"   Error: {error_detail}")
            return {"error": error_detail, "status_code": response.status_code}
            
    except Exception as e:
        log_message(f"❌ Ship creation error: {str(e)}", "ERROR")
        return {"error": str(e)}

def test_direct_folder_creation(token, company_id):
    """Test direct Google Drive folder creation endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        log_message("🔧 Testing direct Google Drive folder creation endpoint...")
        
        folder_data = {
            "ship_name": "DIRECT_TEST_SHIP",
            "ship_id": "direct-test-id"
        }
        
        endpoint = f"{BACKEND_URL}/companies/{company_id}/gdrive/create-ship-folder"
        log_message(f"   POST {endpoint}")
        log_message(f"   Data: {json.dumps(folder_data, indent=3)}")
        
        response = requests.post(endpoint, json=folder_data, headers=headers, timeout=60)
        log_message(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            log_message("   ✅ Direct folder creation successful")
            log_message(f"   Result: {json.dumps(result, indent=6)}")
            return result
        else:
            log_message(f"   ❌ Direct folder creation failed: {response.status_code}")
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', 'Unknown')
                log_message(f"   Error: {error_detail}")
                
                if "404" in str(error_detail) and "Company Google Drive not configured" in str(error_detail):
                    log_message("   🎯 FOUND TARGET ERROR in direct folder creation!")
                    return {"error": error_detail, "target_error_found": True}
                    
            except:
                error_detail = response.text[:300]
                log_message(f"   Error (raw): {error_detail}")
                
                if "404" in error_detail and "Company Google Drive not configured" in error_detail:
                    log_message("   🎯 FOUND TARGET ERROR in direct folder creation!")
                    return {"error": error_detail, "target_error_found": True}
            
            return {"error": error_detail, "status_code": response.status_code}
            
    except Exception as e:
        log_message(f"❌ Direct folder creation error: {str(e)}", "ERROR")
        return {"error": str(e)}

def main():
    """Main test execution"""
    log_message("🚢 SHIP CREATION TEST - GOOGLE DRIVE FOLDER CREATION ERROR DEBUG")
    log_message("🎯 Focus: Capture exact 'Failed to create ship folder: 404: Company Google Drive not configured' error")
    log_message("📋 Review Request: Monitor backend logs and identify exact failing API call")
    log_message("=" * 100)
    
    # Step 1: Authenticate
    token, user = authenticate()
    if not token:
        log_message("❌ Authentication failed - cannot proceed")
        return
    
    # Step 2: Get company information
    company_id, gdrive_config = get_company_info(token)
    if not company_id:
        log_message("❌ Company information not found - cannot proceed")
        return
    
    # Step 3: Create test ship
    log_message("\n🚢 STEP 1: CREATE TEST SHIP")
    log_message("=" * 50)
    ship_result = create_test_ship(token)
    
    # Step 4: Test direct folder creation if ship creation was successful
    if company_id and not ship_result.get("target_error_found"):
        log_message("\n🔧 STEP 2: TEST DIRECT FOLDER CREATION")
        log_message("=" * 50)
        folder_result = test_direct_folder_creation(token, company_id)
    
    # Step 5: Final analysis
    log_message("\n🎯 FINAL ANALYSIS")
    log_message("=" * 50)
    
    if ship_result.get("target_error_found"):
        log_message("✅ TARGET ERROR SUCCESSFULLY CAPTURED:")
        log_message("   'Failed to create ship folder: 404: Company Google Drive not configured'")
        log_message(f"   Error detail: {ship_result.get('error')}")
    elif ship_result.get("error"):
        log_message("❌ Ship creation failed with different error:")
        log_message(f"   Error: {ship_result.get('error')}")
        log_message(f"   Status: {ship_result.get('status_code', 'Unknown')}")
    else:
        log_message("✅ Ship creation was successful")
        log_message("   No Google Drive folder creation errors detected")
    
    if gdrive_config:
        log_message("\n📋 Google Drive Configuration Status:")
        log_message("   ✅ Configuration exists")
        log_message(f"   Apps Script URL: {gdrive_config.get('config', {}).get('web_app_url', 'Not found')}")
        log_message(f"   Folder ID: {gdrive_config.get('config', {}).get('folder_id', 'Not found')}")
    else:
        log_message("\n📋 Google Drive Configuration Status:")
        log_message("   ❌ No configuration found")
    
    log_message("=" * 100)
    log_message("🎉 Ship creation test completed!")
    log_message("✅ All test steps executed - check logs above for detailed analysis")

if __name__ == "__main__":
    main()