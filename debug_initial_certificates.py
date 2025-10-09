#!/usr/bin/env python3
"""
Debug script to test Initial certificate detection logic
"""
import requests
import json
from datetime import datetime, timedelta

# Configuration
BACKEND_URL = "https://mariner-scan.preview.emergentagent.com/api"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlNDNkOWNmNS0yMTZhLTRjZjAtOGM2My00MjE4YzY5YjJkOTAiLCJ1c2VybmFtZSI6ImFkbWluMSIsInJvbGUiOiJhZG1pbiIsImNvbXBhbnkiOiJBTUNTQyIsImZ1bGxfbmFtZSI6IkFkbWluIFVzZXIgMSIsImV4cCI6MTc1OTY1NzgzMX0.dZ0_Z32CRKegkdTQKc7U_IbhCKf6sP-PZhF0nq9B-fY"

def get_headers():
    return {"Authorization": f"Bearer {TOKEN}"}

def test_certificate_matching():
    """Test the certificate matching logic"""
    print("🔍 Testing Initial Certificate Detection Logic")
    print("=" * 60)
    
    # Get certificates for SUNSHINE 01 ship
    ship_id = "26e7cc88-1999-4496-8d76-a2f46c07da3a"
    
    response = requests.get(f"{BACKEND_URL}/ships/{ship_id}/certificates", headers=get_headers())
    if response.status_code != 200:
        print(f"❌ Failed to get certificates: {response.status_code}")
        return
    
    certificates = response.json()
    print(f"📋 Found {len(certificates)} total certificates")
    
    # Filter for Initial SMC/ISSC/MLC certificates
    initial_certificates = []
    current_date = datetime.now().date()
    
    print(f"📅 Current date: {current_date}")
    print("\n🔍 Checking each certificate:")
    
    for cert in certificates:
        cert_name = cert.get('cert_name', '')
        next_survey_type = cert.get('next_survey_type', '')
        valid_date_str = cert.get('valid_date', '')
        cert_no = cert.get('cert_no', '')
        
        print(f"\n📜 Certificate: {cert_no}")
        print(f"   Name: {cert_name}")
        print(f"   Survey Type: {next_survey_type}")
        print(f"   Valid Date: {valid_date_str}")
        
        # Test the matching condition
        is_initial = 'Initial' in (next_survey_type or '')
        is_smc_issc_mlc = any(cert_type in (cert_name or '') for cert_type in ['SAFETY MANAGEMENT', 'SHIP SECURITY', 'MARITIME LABOUR', 'SMC', 'ISSC', 'MLC'])
        
        print(f"   Is Initial: {is_initial}")
        print(f"   Is SMC/ISSC/MLC: {is_smc_issc_mlc}")
        
        if is_initial and is_smc_issc_mlc:
            print("   ✅ MATCHES Initial SMC/ISSC/MLC criteria")
            
            # Test window calculation
            if valid_date_str:
                try:
                    # Parse valid date (same logic as backend)
                    if isinstance(valid_date_str, str):
                        if 'T' in valid_date_str:
                            valid_date = datetime.fromisoformat(valid_date_str.replace('Z', '')).date()
                        else:
                            if ' ' in valid_date_str:
                                valid_date = datetime.strptime(valid_date_str.split(' ')[0], '%Y-%m-%d').date()
                            else:
                                valid_date = datetime.strptime(valid_date_str, '%Y-%m-%d').date()
                    else:
                        valid_date = valid_date_str.date() if hasattr(valid_date_str, 'date') else valid_date_str
                    
                    # Calculate window (same logic as backend)
                    window_open = valid_date - timedelta(days=90)  # 3 months before valid date
                    window_close = valid_date
                    
                    print(f"   📅 Valid Date: {valid_date}")
                    print(f"   📅 Window Open: {window_open}")
                    print(f"   📅 Window Close: {window_close}")
                    
                    # Test if current date is within window
                    is_within_window = window_open <= current_date <= window_close
                    print(f"   📅 Is within window: {is_within_window}")
                    
                    if is_within_window:
                        print("   ✅ SHOULD APPEAR in upcoming surveys")
                        initial_certificates.append(cert)
                    else:
                        print("   ❌ NOT within window - will not appear")
                        days_to_open = (window_open - current_date).days
                        days_to_close = (window_close - current_date).days
                        print(f"      Days to window open: {days_to_open}")
                        print(f"      Days to window close: {days_to_close}")
                        
                except Exception as e:
                    print(f"   ❌ Error parsing date: {e}")
            else:
                print("   ❌ No valid date - will not appear")
        else:
            print("   ⚠️ Does not match Initial SMC/ISSC/MLC criteria")
    
    print(f"\n📊 Summary:")
    print(f"   Total certificates: {len(certificates)}")
    print(f"   Initial SMC/ISSC/MLC certificates within window: {len(initial_certificates)}")
    
    # Test the actual API
    print(f"\n🌐 Testing actual upcoming surveys API:")
    response = requests.get(f"{BACKEND_URL}/certificates/upcoming-surveys", headers=get_headers())
    if response.status_code == 200:
        data = response.json()
        actual_count = len(data.get('upcoming_surveys', []))
        print(f"   API returned: {actual_count} upcoming surveys")
        
        if actual_count != len(initial_certificates):
            print(f"   ❌ MISMATCH: Expected {len(initial_certificates)}, got {actual_count}")
        else:
            print(f"   ✅ MATCH: Both show {actual_count} upcoming surveys")
    else:
        print(f"   ❌ API failed: {response.status_code}")

if __name__ == "__main__":
    test_certificate_matching()