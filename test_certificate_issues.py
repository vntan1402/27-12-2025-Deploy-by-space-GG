#!/usr/bin/env python3
"""
Test the specific certificate analysis issues reported by the user
"""

import requests
import json
import tempfile
import os

# Configuration
BACKEND_URL = 'https://vesseldocs.preview.emergentagent.com/api'

def authenticate():
    """Authenticate with admin1/123456"""
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None

def download_sunshine_certificate():
    """Download the SUNSHINE 01 certificate"""
    pdf_url = "https://customer-assets.emergentagent.com/job_8713f098-d577-491f-ae01-3c714b8055af/artifacts/h9jbvh37_SUNSHINE%2001%20-%20CSSC%20-%20PM25385.pdf"
    
    try:
        response = requests.get(pdf_url, timeout=60)
        if response.status_code == 200:
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.write(response.content)
            temp_file.close()
            print(f"✅ Downloaded SUNSHINE 01 certificate ({len(response.content)} bytes)")
            return temp_file.name
        else:
            print(f"❌ Failed to download certificate: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Download error: {e}")
        return None

def test_certificate_analysis(token, pdf_path):
    """Test the certificate analysis endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        with open(pdf_path, 'rb') as file:
            files = {'file': ('SUNSHINE_01_CSSC.pdf', file, 'application/pdf')}
            
            response = requests.post(
                f"{BACKEND_URL}/analyze-ship-certificate",
                files=files,
                headers=headers,
                timeout=120
            )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n=== CERTIFICATE ANALYSIS RESULTS ===")
            print(json.dumps(data, indent=2))
            
            # Check specific issues
            print("\n=== ISSUE ANALYSIS ===")
            
            # Issue 1: Last Docking format
            last_docking = data.get('last_docking')
            last_docking_2 = data.get('last_docking_2')
            
            print(f"Last Docking 1: {last_docking}")
            print(f"Last Docking 2: {last_docking_2}")
            
            if last_docking:
                if any(day in str(last_docking) for day in ['30', '31']):
                    print("❌ ISSUE 1: Last Docking has artificial days added")
                else:
                    print("✅ ISSUE 1: Last Docking format looks correct")
            
            # Issue 2: Auto-calculation
            next_docking = data.get('next_docking')
            special_survey_from = data.get('special_survey_from_date')
            
            print(f"Next Docking: {next_docking}")
            print(f"Special Survey From Date: {special_survey_from}")
            
            if next_docking and next_docking != "dd/mm/yyyy" and next_docking.strip():
                print("✅ ISSUE 2a: Next Docking auto-calculation working")
            else:
                print("❌ ISSUE 2a: Next Docking not auto-calculated")
            
            if special_survey_from and special_survey_from != "dd/mm/yyyy" and special_survey_from.strip():
                print("✅ ISSUE 2b: Special Survey From Date auto-calculation working")
            else:
                print("❌ ISSUE 2b: Special Survey From Date not auto-calculated")
            
            return True
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Error: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    print("🎯 TESTING CERTIFICATE ANALYSIS ISSUES")
    print("=" * 50)
    
    # Step 1: Authenticate
    print("1. Authenticating...")
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    print("✅ Authentication successful")
    
    # Step 2: Download certificate
    print("\n2. Downloading SUNSHINE 01 certificate...")
    pdf_path = download_sunshine_certificate()
    if not pdf_path:
        print("❌ Certificate download failed")
        return
    
    try:
        # Step 3: Test analysis
        print("\n3. Testing certificate analysis...")
        success = test_certificate_analysis(token, pdf_path)
        
        if success:
            print("\n✅ Certificate analysis test completed")
        else:
            print("\n❌ Certificate analysis test failed")
    
    finally:
        # Cleanup
        try:
            os.unlink(pdf_path)
        except:
            pass

if __name__ == "__main__":
    main()