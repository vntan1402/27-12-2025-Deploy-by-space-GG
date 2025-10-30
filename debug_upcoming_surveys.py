#!/usr/bin/env python3
"""
Debug script to understand why the certificate is not appearing in upcoming surveys
"""

import requests
import json
from datetime import datetime, date, timedelta

# Backend URL
BACKEND_URL = "https://cert-tracker-8.preview.emergentagent.com/api"

def debug_certificate_filtering():
    """Debug the certificate filtering logic"""
    
    # Login first
    session = requests.Session()
    login_response = session.post(f"{BACKEND_URL}/auth/login", json={
        "username": "admin1",
        "password": "123456"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get the specific certificate
    target_cert_id = "51d1c55a-81d4-4e68-9dd2-9fef7d8bf895"
    ship_id = "bc444bc3-aea9-4491-b199-8098efcc16d2"
    
    print(f"🔍 Debugging certificate: {target_cert_id}")
    print(f"🚢 Ship ID: {ship_id}")
    
    # Get certificate details
    certs_response = session.get(f"{BACKEND_URL}/ships/{ship_id}/certificates", headers=headers)
    if certs_response.status_code != 200:
        print(f"❌ Failed to get certificates: {certs_response.status_code}")
        return
    
    certificates = certs_response.json()
    target_cert = None
    
    for cert in certificates:
        if cert.get('id') == target_cert_id:
            target_cert = cert
            break
    
    if not target_cert:
        print(f"❌ Certificate not found in ship certificates")
        return
    
    print(f"✅ Found certificate:")
    print(f"   📄 Name: {target_cert.get('cert_name')}")
    print(f"   📅 Next Survey: {target_cert.get('next_survey')}")
    print(f"   🔄 Survey Type: {target_cert.get('next_survey_type')}")
    print(f"   📋 Issue Date: {target_cert.get('issue_date')}")
    print(f"   📋 Valid Date: {target_cert.get('valid_date')}")
    
    # Simulate the backend logic
    print(f"\n🧮 Simulating backend filtering logic:")
    
    # Current date (simulating server date)
    current_date = date(2025, 10, 30)
    print(f"📅 Current Date: {current_date}")
    
    # Parse next survey date
    next_survey_str = target_cert.get('next_survey')
    next_survey_type = target_cert.get('next_survey_type') or ''
    cert_name = (target_cert.get('cert_name') or '').upper()
    
    print(f"🔍 Next Survey String: '{next_survey_str}'")
    print(f"🔍 Next Survey Type: '{next_survey_type}'")
    print(f"🔍 Certificate Name (upper): '{cert_name}'")
    
    if not next_survey_str:
        print(f"❌ No next_survey date - certificate would be skipped")
        return
    
    # Parse the date
    try:
        if isinstance(next_survey_str, str):
            if 'T' in next_survey_str:
                next_survey_date = datetime.fromisoformat(next_survey_str.replace('Z', '')).date()
            else:
                if ' ' in next_survey_str:
                    next_survey_date = datetime.strptime(next_survey_str.split(' ')[0], '%Y-%m-%d').date()
                else:
                    next_survey_date = datetime.strptime(next_survey_str, '%Y-%m-%d').date()
        else:
            next_survey_date = next_survey_str.date() if hasattr(next_survey_str, 'date') else next_survey_str
        
        print(f"✅ Parsed next survey date: {next_survey_date}")
        
    except Exception as e:
        print(f"❌ Error parsing next survey date: {e}")
        return
    
    # Determine window based on certificate type
    print(f"\n🪟 Determining survey window:")
    
    # Check certificate type logic
    is_condition_cert = 'Condition Certificate Expiry' in next_survey_type
    is_initial_smc_issc_mlc = ('Initial' in next_survey_type and 
                               any(cert_type in cert_name for cert_type in ['SAFETY MANAGEMENT', 'SHIP SECURITY', 'MARITIME LABOUR', 'SMC', 'ISSC', 'MLC']))
    is_special_survey = 'Special Survey' in next_survey_type
    
    print(f"🔍 Is Condition Certificate: {is_condition_cert}")
    print(f"🔍 Is Initial SMC/ISSC/MLC: {is_initial_smc_issc_mlc}")
    print(f"🔍 Is Special Survey: {is_special_survey}")
    
    if is_condition_cert:
        print(f"📋 Certificate type: Condition Certificate")
        # Would need issue_date and valid_date
        issue_date_str = target_cert.get('issue_date')
        valid_date_str = target_cert.get('valid_date')
        print(f"   Issue Date: {issue_date_str}")
        print(f"   Valid Date: {valid_date_str}")
        
        if not issue_date_str or not valid_date_str:
            print(f"❌ Missing required dates for condition certificate")
            return
            
    elif is_initial_smc_issc_mlc:
        print(f"📋 Certificate type: Initial SMC/ISSC/MLC")
        # Would use valid_date - 3 months to valid_date
        valid_date_str = target_cert.get('valid_date')
        print(f"   Valid Date: {valid_date_str}")
        
        if not valid_date_str:
            print(f"❌ Missing valid date for initial certificate")
            return
            
    elif is_special_survey:
        print(f"📋 Certificate type: Special Survey")
        # Would use next_survey - 90 days to next_survey
        window_open = next_survey_date - timedelta(days=90)
        window_close = next_survey_date
        
    else:
        print(f"📋 Certificate type: Other surveys (±3M)")
        # Standard ±90 days window
        window_open = next_survey_date - timedelta(days=90)
        window_close = next_survey_date + timedelta(days=90)
    
    print(f"🪟 Window Open: {window_open}")
    print(f"🪟 Window Close: {window_close}")
    
    # Check if current date is within window
    is_within_window = window_open <= current_date <= window_close
    print(f"🎯 Current date within window: {is_within_window}")
    
    if is_within_window:
        print(f"✅ Certificate SHOULD appear in upcoming surveys")
        
        # Calculate additional fields
        days_until_survey = (next_survey_date - current_date).days
        print(f"📊 Days until survey: {days_until_survey}")
        
    else:
        print(f"❌ Certificate should NOT appear (outside window)")
        print(f"   Current: {current_date}")
        print(f"   Window: {window_open} to {window_close}")
    
    # Now test the actual endpoint
    print(f"\n📡 Testing actual upcoming surveys endpoint:")
    response = session.get(f"{BACKEND_URL}/certificates/upcoming-surveys", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        upcoming_surveys = data.get("upcoming_surveys", [])
        
        found_in_response = False
        for survey in upcoming_surveys:
            if survey.get('certificate_id') == target_cert_id:
                found_in_response = True
                print(f"✅ Certificate found in response!")
                print(f"   Response data: {json.dumps(survey, indent=4, default=str)}")
                break
        
        if not found_in_response:
            print(f"❌ Certificate NOT found in upcoming surveys response")
            print(f"📊 Total surveys in response: {len(upcoming_surveys)}")
            
            if upcoming_surveys:
                print(f"📋 Other certificates in response:")
                for survey in upcoming_surveys[:3]:  # Show first 3
                    print(f"   - {survey.get('certificate_id')} - {survey.get('cert_name')}")
    else:
        print(f"❌ Endpoint failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    debug_certificate_filtering()