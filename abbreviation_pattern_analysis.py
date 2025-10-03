#!/usr/bin/env python3
"""
Abbreviation Pattern Analysis - Check patterns in certificate abbreviation data
"""

import requests
import json
import os
from datetime import datetime

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

def analyze_abbreviation_patterns():
    """Analyze patterns in certificate abbreviation data"""
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = get_headers(token)
    
    # Get MINH ANH 09 ship ID
    ships_response = requests.get(f"{BACKEND_URL}/ships", headers=headers, timeout=30)
    if ships_response.status_code != 200:
        print("❌ Failed to get ships")
        return
    
    ships = ships_response.json()
    minh_anh_ship = None
    for ship in ships:
        if 'MINH ANH' in ship.get('name', '').upper() and '09' in ship.get('name', ''):
            minh_anh_ship = ship
            break
    
    if not minh_anh_ship:
        print("❌ MINH ANH 09 ship not found")
        return
    
    ship_id = minh_anh_ship.get('id')
    print(f"🚢 Analyzing certificates for MINH ANH 09 (ID: {ship_id})")
    
    # Get all certificates for MINH ANH 09
    certs_response = requests.get(f"{BACKEND_URL}/certificates", headers=headers, params={"ship_id": ship_id}, timeout=30)
    if certs_response.status_code != 200:
        print("❌ Failed to get certificates")
        return
    
    certificates = certs_response.json()
    print(f"📋 Found {len(certificates)} certificates")
    
    # Analyze patterns
    ll_certs = []
    cl_certs = []
    
    for cert in certificates:
        cert_name = cert.get('cert_name', '').upper()
        cert_abbreviation = cert.get('cert_abbreviation', '')
        created_at = cert.get('created_at', '')
        cert_type = cert.get('cert_type', '')
        
        if 'LOAD LINE' in cert_name:
            ll_certs.append({
                'id': cert.get('id'),
                'name': cert.get('cert_name'),
                'abbreviation': cert_abbreviation,
                'created_at': created_at,
                'cert_type': cert_type,
                'has_abbreviation': bool(cert_abbreviation and cert_abbreviation.strip())
            })
        elif 'CLASSIFICATION' in cert_name:
            cl_certs.append({
                'id': cert.get('id'),
                'name': cert.get('cert_name'),
                'abbreviation': cert_abbreviation,
                'created_at': created_at,
                'cert_type': cert_type,
                'has_abbreviation': bool(cert_abbreviation and cert_abbreviation.strip())
            })
    
    print(f"\n📋 LL CERTIFICATE PATTERN ANALYSIS:")
    print(f"   Total LL certificates: {len(ll_certs)}")
    
    ll_with_abbrev = [cert for cert in ll_certs if cert['has_abbreviation']]
    ll_without_abbrev = [cert for cert in ll_certs if not cert['has_abbreviation']]
    
    print(f"   With abbreviation: {len(ll_with_abbrev)}")
    print(f"   Without abbreviation: {len(ll_without_abbrev)}")
    
    if ll_with_abbrev:
        print(f"\n   ✅ LL certificates WITH abbreviation:")
        for cert in ll_with_abbrev:
            print(f"      ID: {cert['id'][:8]}... | Type: {cert['cert_type']} | Abbrev: '{cert['abbreviation']}' | Created: {cert['created_at'][:10]}")
    
    if ll_without_abbrev:
        print(f"\n   ❌ LL certificates WITHOUT abbreviation:")
        for cert in ll_without_abbrev:
            print(f"      ID: {cert['id'][:8]}... | Type: {cert['cert_type']} | Abbrev: '{cert['abbreviation']}' | Created: {cert['created_at'][:10]}")
    
    print(f"\n📋 CL CERTIFICATE PATTERN ANALYSIS:")
    print(f"   Total CL certificates: {len(cl_certs)}")
    
    cl_with_abbrev = [cert for cert in cl_certs if cert['has_abbreviation']]
    cl_without_abbrev = [cert for cert in cl_certs if not cert['has_abbreviation']]
    
    print(f"   With abbreviation: {len(cl_with_abbrev)}")
    print(f"   Without abbreviation: {len(cl_without_abbrev)}")
    
    if cl_with_abbrev:
        print(f"\n   ✅ CL certificates WITH abbreviation:")
        for cert in cl_with_abbrev:
            print(f"      ID: {cert['id'][:8]}... | Type: {cert['cert_type']} | Abbrev: '{cert['abbreviation']}' | Created: {cert['created_at'][:10]}")
    
    if cl_without_abbrev:
        print(f"\n   ❌ CL certificates WITHOUT abbreviation:")
        for cert in cl_without_abbrev:
            print(f"      ID: {cert['id'][:8]}... | Type: {cert['cert_type']} | Abbrev: '{cert['abbreviation']}' | Created: {cert['created_at'][:10]}")
    
    # Pattern analysis
    print(f"\n🔍 PATTERN ANALYSIS:")
    
    # Check if there's a pattern by certificate type
    ll_full_term_with_abbrev = [cert for cert in ll_with_abbrev if cert['cert_type'] == 'Full Term']
    ll_interim_with_abbrev = [cert for cert in ll_with_abbrev if cert['cert_type'] == 'Interim']
    ll_full_term_without_abbrev = [cert for cert in ll_without_abbrev if cert['cert_type'] == 'Full Term']
    ll_interim_without_abbrev = [cert for cert in ll_without_abbrev if cert['cert_type'] == 'Interim']
    
    print(f"   LL Full Term with abbreviation: {len(ll_full_term_with_abbrev)}")
    print(f"   LL Full Term without abbreviation: {len(ll_full_term_without_abbrev)}")
    print(f"   LL Interim with abbreviation: {len(ll_interim_with_abbrev)}")
    print(f"   LL Interim without abbreviation: {len(ll_interim_without_abbrev)}")
    
    cl_full_term_with_abbrev = [cert for cert in cl_with_abbrev if cert['cert_type'] == 'Full Term']
    cl_interim_with_abbrev = [cert for cert in cl_with_abbrev if cert['cert_type'] == 'Interim']
    cl_full_term_without_abbrev = [cert for cert in cl_without_abbrev if cert['cert_type'] == 'Full Term']
    cl_interim_without_abbrev = [cert for cert in cl_without_abbrev if cert['cert_type'] == 'Interim']
    
    print(f"   CL Full Term with abbreviation: {len(cl_full_term_with_abbrev)}")
    print(f"   CL Full Term without abbreviation: {len(cl_full_term_without_abbrev)}")
    print(f"   CL Interim with abbreviation: {len(cl_interim_with_abbrev)}")
    print(f"   CL Interim without abbreviation: {len(cl_interim_without_abbrev)}")
    
    # Check creation date patterns
    if ll_with_abbrev and ll_without_abbrev:
        with_dates = [cert['created_at'] for cert in ll_with_abbrev if cert['created_at']]
        without_dates = [cert['created_at'] for cert in ll_without_abbrev if cert['created_at']]
        
        if with_dates and without_dates:
            latest_with = max(with_dates)
            latest_without = max(without_dates)
            print(f"   Latest LL cert WITH abbreviation: {latest_with[:10]}")
            print(f"   Latest LL cert WITHOUT abbreviation: {latest_without[:10]}")

if __name__ == "__main__":
    analyze_abbreviation_patterns()