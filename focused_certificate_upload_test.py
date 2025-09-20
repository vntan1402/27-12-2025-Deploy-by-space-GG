#!/usr/bin/env python3
"""
Focused Certificate Upload Functionality Test
==============================================

Testing the specific issues reported in the review request:
1. Classification results are not displayed after upload
2. Files are not uploaded to Company Google Drive 
3. New records are not created in Certificate list

This test focuses on the actual endpoints that exist and tests the complete workflow.
"""

import requests
import json
import io
import time
from datetime import datetime, timezone

def test_certificate_upload_workflow():
    """Test the complete certificate upload workflow"""
    
    base_url = "https://certmaster-ship.preview.emergentagent.com/api"
    
    print("🚢 FOCUSED CERTIFICATE UPLOAD FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Step 1: Authentication
    print("\n🔐 Step 1: Authentication")
    login_data = {"username": "admin", "password": "admin123"}
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data['access_token']
            user_info = auth_data['user']
            print(f"✅ Login successful: {user_info['full_name']} ({user_info['role']})")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Step 2: Get prerequisite data
    print("\n📋 Step 2: Get prerequisite data")
    
    # Get ships
    try:
        response = requests.get(f"{base_url}/ships", headers=headers, timeout=10)
        if response.status_code == 200:
            ships = response.json()
            if ships:
                test_ship = ships[0]
                ship_id = test_ship['id']
                print(f"✅ Found {len(ships)} ships, using: {test_ship['name']}")
            else:
                print("❌ No ships found")
                return False
        else:
            print(f"❌ Failed to get ships: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ships error: {e}")
        return False
    
    # Get initial certificate count
    try:
        response = requests.get(f"{base_url}/certificates", headers=headers, timeout=10)
        if response.status_code == 200:
            initial_certificates = response.json()
            initial_count = len(initial_certificates)
            print(f"✅ Initial certificate count: {initial_count}")
        else:
            print(f"❌ Failed to get certificates: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Certificates error: {e}")
        return False
    
    # Step 3: Test AI Configuration
    print("\n🤖 Step 3: Test AI Configuration")
    try:
        response = requests.get(f"{base_url}/ai-config", headers=headers, timeout=10)
        if response.status_code == 200:
            ai_config = response.json()
            print(f"✅ AI configured: Provider={ai_config.get('provider')}, Model={ai_config.get('model')}")
        else:
            print(f"⚠️ AI config issue: {response.status_code}")
    except Exception as e:
        print(f"⚠️ AI config error: {e}")
    
    # Step 4: Test Google Drive Configuration
    print("\n☁️ Step 4: Test Google Drive Configuration")
    try:
        response = requests.get(f"{base_url}/gdrive/config", headers=headers, timeout=10)
        if response.status_code == 200:
            gdrive_config = response.json()
            print(f"✅ Google Drive configured: {gdrive_config.get('configured', False)}")
        else:
            print(f"⚠️ Google Drive config issue: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Google Drive config error: {e}")
    
    # Step 5: Test Multi-file Upload with AI Processing
    print("\n📁 Step 5: Test Multi-file Upload with AI Processing")
    
    # Create realistic test certificate content
    cert_content = """
INTERNATIONAL AIR POLLUTION PREVENTION CERTIFICATE

Ship Name: BROTHER 36
IMO Number: IMO9876543
Certificate Number: IAPP2024TEST
Issue Date: 2024-01-15
Valid Until: 2028-01-15

Issued by: Panama Maritime Documentation Services Inc
On behalf of: Panama Maritime Authority

This certificate is issued under the provisions of the International Convention
for the Prevention of Pollution from Ships, 1973, as modified by the Protocol
of 1978 relating thereto (MARPOL 73/78).

Classification Society: DNV GL
Flag State: Panama
Certificate Type: Full Term

Survey Information:
- Certificate Type: STATUTORY
- Survey Type: Renewal
- Issuance Date: 2024-01-15
- Expiration Date: 2028-01-15

This certificate is valid for international voyages.
    """.strip().encode('utf-8')
    
    # Prepare file for upload
    files = [('files', ('test_certificate.pdf', io.BytesIO(cert_content), 'application/pdf'))]
    
    try:
        # Remove Content-Type header to let requests handle multipart properly
        upload_headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(
            f"{base_url}/certificates/upload-multi-files", 
            files=files, 
            headers=upload_headers, 
            timeout=30
        )
        
        print(f"Upload response status: {response.status_code}")
        
        if response.status_code == 200:
            upload_result = response.json()
            print(f"✅ Upload successful")
            
            # Analyze results for the three reported issues
            if 'results' in upload_result and upload_result['results']:
                result = upload_result['results'][0]
                filename = result.get('filename', 'unknown')
                status = result.get('status', 'unknown')
                
                print(f"\n📊 Analysis of uploaded file: {filename}")
                print(f"   Status: {status}")
                
                # Issue 1: Classification results display
                analysis = result.get('analysis', {})
                if analysis:
                    print(f"   ✅ ISSUE 1 - Classification results ARE displayed:")
                    print(f"      Category: {analysis.get('category', 'Unknown')}")
                    print(f"      Ship Name: {analysis.get('ship_name', 'Unknown')}")
                    print(f"      Cert Name: {analysis.get('cert_name', 'Unknown')}")
                    print(f"      Cert Type: {analysis.get('cert_type', 'Unknown')}")
                    print(f"      Issue Date: {analysis.get('issue_date', 'Unknown')}")
                    print(f"      Valid Date: {analysis.get('valid_date', 'Unknown')}")
                    print(f"      Issued By: {analysis.get('issued_by', 'Unknown')}")
                    classification_working = True
                else:
                    print(f"   ❌ ISSUE 1 - Classification results NOT displayed")
                    classification_working = False
                
                # Issue 2: Google Drive upload
                upload_info = result.get('upload', {})
                if upload_info:
                    gdrive_success = upload_info.get('success', False)
                    if gdrive_success:
                        print(f"   ✅ ISSUE 2 - Files ARE uploaded to Google Drive:")
                        print(f"      File ID: {upload_info.get('file_id', 'Unknown')}")
                        print(f"      Folder Path: {upload_info.get('folder_path', 'Unknown')}")
                    else:
                        print(f"   ❌ ISSUE 2 - Files NOT uploaded to Google Drive:")
                        print(f"      Error: {upload_info.get('error', 'Unknown error')}")
                    gdrive_working = gdrive_success
                else:
                    print(f"   ❌ ISSUE 2 - No Google Drive upload information")
                    gdrive_working = False
                
                # Issue 3: Certificate record creation
                cert_result = result.get('certificate', {})
                if cert_result and cert_result.get('success', False):
                    print(f"   ✅ ISSUE 3 - Certificate records ARE created:")
                    print(f"      Certificate ID: {cert_result.get('id', 'Unknown')}")
                    print(f"      Certificate Name: {cert_result.get('cert_name', 'Unknown')}")
                    records_working = True
                else:
                    print(f"   ❌ ISSUE 3 - Certificate records NOT created:")
                    if cert_result:
                        print(f"      Error: {cert_result.get('error', 'Unknown error')}")
                    records_working = False
                
            else:
                print("❌ No upload results found")
                classification_working = gdrive_working = records_working = False
                
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            classification_working = gdrive_working = records_working = False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        classification_working = gdrive_working = records_working = False
    
    # Step 6: Verify certificate list updated
    print("\n📋 Step 6: Verify certificate list updated")
    try:
        response = requests.get(f"{base_url}/certificates", headers=headers, timeout=10)
        if response.status_code == 200:
            final_certificates = response.json()
            final_count = len(final_certificates)
            print(f"✅ Final certificate count: {final_count}")
            
            if final_count > initial_count:
                print(f"   ✅ Certificate list updated: {initial_count} → {final_count}")
                list_updated = True
            else:
                print(f"   ❌ Certificate list NOT updated: {initial_count} → {final_count}")
                list_updated = False
        else:
            print(f"❌ Failed to get final certificates: {response.status_code}")
            list_updated = False
    except Exception as e:
        print(f"❌ Final certificates error: {e}")
        list_updated = False
    
    # Step 7: Test ship-specific certificate retrieval
    print("\n🚢 Step 7: Test ship-specific certificate retrieval")
    try:
        response = requests.get(f"{base_url}/ships/{ship_id}/certificates", headers=headers, timeout=10)
        if response.status_code == 200:
            ship_certificates = response.json()
            print(f"✅ Ship certificates: {len(ship_certificates)} found")
        else:
            print(f"❌ Failed to get ship certificates: {response.status_code}")
    except Exception as e:
        print(f"❌ Ship certificates error: {e}")
    
    # Final Summary
    print("\n" + "=" * 60)
    print("🎯 FINAL ANALYSIS OF REPORTED ISSUES")
    print("=" * 60)
    
    issues = [
        ("1. Classification results display", classification_working),
        ("2. Google Drive file upload", gdrive_working),
        ("3. Certificate record creation", records_working),
        ("4. Certificate list updated", list_updated)
    ]
    
    working_count = sum(1 for _, working in issues if working)
    total_issues = len(issues)
    
    for issue, working in issues:
        status = "✅ WORKING" if working else "❌ NOT WORKING"
        print(f"{issue:35} {status}")
    
    print(f"\nOverall Status: {working_count}/{total_issues} issues resolved")
    
    if working_count == total_issues:
        print("🎉 ALL ISSUES RESOLVED - Certificate upload workflow is working correctly!")
        return True
    elif working_count >= total_issues * 0.75:
        print("⚠️ MOSTLY WORKING - Some minor issues remain")
        return True
    else:
        print("❌ SIGNIFICANT ISSUES - Certificate upload workflow needs attention")
        return False

if __name__ == "__main__":
    import sys
    success = test_certificate_upload_workflow()
    sys.exit(0 if success else 1)