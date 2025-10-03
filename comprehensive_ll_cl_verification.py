#!/usr/bin/env python3
"""
Comprehensive LL and CL Certificate Verification
Final verification that all LL and CL certificates have proper abbreviations
"""

import requests
import json
import os

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
    else:
        raise Exception("Internal URL not working")
except:
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vesseldocs.preview.emergentagent.com') + '/api'

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

def get_headers(token):
    """Get authentication headers"""
    return {"Authorization": f"Bearer {token}"}

def comprehensive_verification():
    """Comprehensive verification of all LL and CL certificates"""
    print("🔍 COMPREHENSIVE LL AND CL CERTIFICATE VERIFICATION")
    print("=" * 70)
    
    # Authenticate
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Get all ships
    ships_response = requests.get(f"{BACKEND_URL}/ships", headers=get_headers(token), timeout=30)
    if ships_response.status_code != 200:
        print("❌ Failed to get ships")
        return
    
    ships = ships_response.json()
    print(f"📊 Found {len(ships)} ships to check")
    
    # Track all LL and CL certificates
    all_ll_certificates = []
    all_cl_certificates = []
    ll_missing_abbreviation = []
    cl_missing_abbreviation = []
    
    ll_keywords = ['LOAD LINE', 'INTERNATIONAL LOAD LINE']
    cl_keywords = ['CLASSIFICATION', 'CLASS CERTIFICATE']
    
    # Check each ship
    for ship in ships:
        ship_id = ship.get('id')
        ship_name = ship.get('name', 'Unknown')
        
        print(f"\n🚢 Checking ship: {ship_name}")
        
        # Get certificates for this ship
        certs_response = requests.get(f"{BACKEND_URL}/ships/{ship_id}/certificates", 
                                    headers=get_headers(token), timeout=30)
        
        if certs_response.status_code == 200:
            certificates = certs_response.json()
            print(f"   📋 Found {len(certificates)} certificates")
            
            ship_ll_count = 0
            ship_cl_count = 0
            
            for cert in certificates:
                cert_name = cert.get('cert_name', '').upper()
                cert_id = cert.get('id')
                cert_abbreviation = cert.get('cert_abbreviation')
                
                # Check for LL certificates
                if any(keyword in cert_name for keyword in ll_keywords):
                    cert_info = {
                        'id': cert_id,
                        'ship_id': ship_id,
                        'ship_name': ship_name,
                        'cert_name': cert.get('cert_name'),
                        'cert_abbreviation': cert_abbreviation,
                        'cert_type': cert.get('cert_type'),
                        'google_drive_file_id': cert.get('google_drive_file_id')
                    }
                    all_ll_certificates.append(cert_info)
                    ship_ll_count += 1
                    
                    print(f"      LL: {cert.get('cert_name')}")
                    print(f"          Abbreviation: {cert_abbreviation}")
                    
                    if not cert_abbreviation or cert_abbreviation.strip() == '':
                        ll_missing_abbreviation.append(cert_info)
                        print(f"          ❌ Missing abbreviation!")
                    elif cert_abbreviation != 'LL':
                        ll_missing_abbreviation.append(cert_info)
                        print(f"          ⚠️ Wrong abbreviation: {cert_abbreviation} (should be LL)")
                    else:
                        print(f"          ✅ Correct abbreviation: LL")
                
                # Check for CL certificates
                elif any(keyword in cert_name for keyword in cl_keywords):
                    cert_info = {
                        'id': cert_id,
                        'ship_id': ship_id,
                        'ship_name': ship_name,
                        'cert_name': cert.get('cert_name'),
                        'cert_abbreviation': cert_abbreviation,
                        'cert_type': cert.get('cert_type'),
                        'google_drive_file_id': cert.get('google_drive_file_id')
                    }
                    all_cl_certificates.append(cert_info)
                    ship_cl_count += 1
                    
                    print(f"      CL: {cert.get('cert_name')}")
                    print(f"          Abbreviation: {cert_abbreviation}")
                    
                    if not cert_abbreviation or cert_abbreviation.strip() == '':
                        cl_missing_abbreviation.append(cert_info)
                        print(f"          ❌ Missing abbreviation!")
                    elif cert_abbreviation != 'CL':
                        cl_missing_abbreviation.append(cert_info)
                        print(f"          ⚠️ Wrong abbreviation: {cert_abbreviation} (should be CL)")
                    else:
                        print(f"          ✅ Correct abbreviation: CL")
            
            if ship_ll_count > 0 or ship_cl_count > 0:
                print(f"   📊 Ship summary: {ship_ll_count} LL, {ship_cl_count} CL certificates")
        else:
            print(f"   ❌ Failed to get certificates: {certs_response.status_code}")
    
    # Overall summary
    print(f"\n📊 COMPREHENSIVE VERIFICATION RESULTS:")
    print(f"=" * 50)
    print(f"Total LL certificates found: {len(all_ll_certificates)}")
    print(f"Total CL certificates found: {len(all_cl_certificates)}")
    print(f"LL certificates with missing/wrong abbreviation: {len(ll_missing_abbreviation)}")
    print(f"CL certificates with missing/wrong abbreviation: {len(cl_missing_abbreviation)}")
    
    # Test auto-rename functionality with a sample of certificates
    print(f"\n🔄 TESTING AUTO-RENAME FUNCTIONALITY:")
    print(f"=" * 40)
    
    # Test a few certificates with Google Drive files
    test_certificates = []
    
    # Add LL certificates with Google Drive files
    for cert in all_ll_certificates:
        if cert.get('google_drive_file_id') and len(test_certificates) < 2:
            test_certificates.append(cert)
    
    # Add CL certificates with Google Drive files
    for cert in all_cl_certificates:
        if cert.get('google_drive_file_id') and len(test_certificates) < 4:
            test_certificates.append(cert)
    
    abbreviation_usage_count = 0
    full_name_usage_count = 0
    
    for cert in test_certificates:
        print(f"\n🔍 Testing auto-rename: {cert['cert_name']} ({cert['ship_name']})")
        
        endpoint = f"{BACKEND_URL}/certificates/{cert['id']}/auto-rename-file"
        response = requests.post(endpoint, headers=get_headers(token), timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            naming_convention = result.get('naming_convention', {})
            cert_identifier = naming_convention.get('cert_identifier', '')
            
            print(f"   ✅ Auto-rename successful")
            print(f"   📁 cert_identifier: {cert_identifier}")
            
            # Determine expected abbreviation
            cert_name_upper = cert['cert_name'].upper()
            if any(keyword in cert_name_upper for keyword in ll_keywords):
                expected_abbrev = 'LL'
            elif any(keyword in cert_name_upper for keyword in cl_keywords):
                expected_abbrev = 'CL'
            else:
                expected_abbrev = 'UNKNOWN'
            
            if cert_identifier == expected_abbrev:
                print(f"   ✅ SUCCESS: Using abbreviation '{expected_abbrev}'")
                abbreviation_usage_count += 1
            else:
                print(f"   ❌ ISSUE: Using '{cert_identifier}' instead of '{expected_abbrev}'")
                full_name_usage_count += 1
        else:
            print(f"   ❌ Auto-rename failed: {response.status_code}")
    
    # Final conclusion
    print(f"\n🎯 FINAL VERIFICATION RESULTS:")
    print(f"=" * 40)
    
    total_certificates = len(all_ll_certificates) + len(all_cl_certificates)
    total_missing = len(ll_missing_abbreviation) + len(cl_missing_abbreviation)
    
    print(f"Total LL and CL certificates: {total_certificates}")
    print(f"Certificates with missing/wrong abbreviations: {total_missing}")
    print(f"Certificates with correct abbreviations: {total_certificates - total_missing}")
    
    if total_missing == 0:
        print(f"✅ SUCCESS: All LL and CL certificates have proper abbreviations!")
    else:
        print(f"❌ ISSUE: {total_missing} certificates still need abbreviation fixes")
    
    print(f"\nAuto-rename functionality test:")
    print(f"   Certificates using abbreviations: {abbreviation_usage_count}")
    print(f"   Certificates using full names: {full_name_usage_count}")
    
    if abbreviation_usage_count > 0 and full_name_usage_count == 0:
        print(f"   ✅ SUCCESS: Auto-rename is using abbreviations correctly!")
    elif abbreviation_usage_count > full_name_usage_count:
        print(f"   ⚠️ PARTIAL: Most certificates use abbreviations, some still use full names")
    else:
        print(f"   ❌ ISSUE: Auto-rename is not consistently using abbreviations")
    
    # Overall conclusion
    if total_missing == 0 and abbreviation_usage_count > 0:
        print(f"\n🎉 COMPREHENSIVE FIX SUCCESSFUL!")
        print(f"   ✅ All LL certificates have cert_abbreviation = 'LL'")
        print(f"   ✅ All CL certificates have cert_abbreviation = 'CL'")
        print(f"   ✅ Auto Rename File uses abbreviations instead of full names")
        return True
    else:
        print(f"\n⚠️ FIX PARTIALLY SUCCESSFUL - Some issues remain")
        return False

if __name__ == "__main__":
    comprehensive_verification()