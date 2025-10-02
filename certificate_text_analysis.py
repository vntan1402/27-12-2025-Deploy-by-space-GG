#!/usr/bin/env python3
"""
MINH ANH 09 - Certificate Text Analysis
FOCUS: Analyze the full text content of PM242308 certificate to understand AI parsing failure
"""

import requests
import json
import os
import sys
import re
from datetime import datetime

# Configuration
try:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=')[1].strip() + '/api'
                break
    print(f"Using backend URL: {BACKEND_URL}")
except:
    BACKEND_URL = 'https://vesseldocs.preview.emergentagent.com/api'

def authenticate():
    """Authenticate and get token"""
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

def get_certificate_full_text():
    """Get the full text content of PM242308 certificate"""
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get MINH ANH 09 ship
    ships_response = requests.get(f"{BACKEND_URL}/ships", headers=headers, timeout=30)
    if ships_response.status_code != 200:
        print("❌ Failed to get ships")
        return None
    
    ships = ships_response.json()
    minh_anh_ship = None
    for ship in ships:
        if 'MINH ANH' in ship.get('name', '').upper() and '09' in ship.get('name', ''):
            minh_anh_ship = ship
            break
    
    if not minh_anh_ship:
        print("❌ MINH ANH 09 ship not found")
        return None
    
    ship_id = minh_anh_ship.get('id')
    
    # Get certificates
    certs_response = requests.get(f"{BACKEND_URL}/ships/{ship_id}/certificates", headers=headers, timeout=30)
    if certs_response.status_code != 200:
        print("❌ Failed to get certificates")
        return None
    
    certificates = certs_response.json()
    pm242308_cert = None
    for cert in certificates:
        if cert.get('cert_no', '').upper() == 'PM242308':
            pm242308_cert = cert
            break
    
    if not pm242308_cert:
        print("❌ PM242308 certificate not found")
        return None
    
    return pm242308_cert.get('text_content', '')

def analyze_certificate_text(text_content):
    """Analyze certificate text for docking-related information"""
    if not text_content:
        print("❌ No text content to analyze")
        return
    
    print("📋 CERTIFICATE TEXT ANALYSIS")
    print("=" * 50)
    print(f"Total text length: {len(text_content)} characters")
    print()
    
    # Show full text
    print("📄 FULL CERTIFICATE TEXT:")
    print("-" * 50)
    print(text_content)
    print("-" * 50)
    print()
    
    # Look for docking-related keywords
    docking_keywords = [
        'dry dock', 'docking', 'bottom inspection', 'hull inspection', 
        'construction survey', 'survey date', 'inspection date',
        'dock', 'drydock', 'bottom', 'hull', 'survey', 'inspection',
        'date', 'issued', 'valid', 'expire', 'endorse'
    ]
    
    print("🔍 KEYWORD ANALYSIS:")
    print("-" * 30)
    text_lower = text_content.lower()
    found_keywords = []
    for keyword in docking_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
            # Find context around keyword
            start_pos = text_lower.find(keyword)
            context_start = max(0, start_pos - 50)
            context_end = min(len(text_content), start_pos + len(keyword) + 50)
            context = text_content[context_start:context_end].replace('\n', ' ')
            print(f"✅ Found '{keyword}': ...{context}...")
    
    if not found_keywords:
        print("❌ No docking-related keywords found")
    else:
        print(f"✅ Found {len(found_keywords)} docking-related keywords: {found_keywords}")
    
    print()
    
    # Look for date patterns
    print("📅 DATE PATTERN ANALYSIS:")
    print("-" * 30)
    
    date_patterns = [
        r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}',  # DD/MM/YYYY or similar
        r'\d{1,2}\s+\w{3,9}\s+\d{4}',  # DD Month YYYY
        r'\w{3,9}\s+\d{1,2},?\s+\d{4}',  # Month DD, YYYY
        r'\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}',  # YYYY/MM/DD
    ]
    
    all_dates = []
    for pattern in date_patterns:
        matches = re.finditer(pattern, text_content, re.IGNORECASE)
        for match in matches:
            date_str = match.group(0)
            start_pos = match.start()
            context_start = max(0, start_pos - 30)
            context_end = min(len(text_content), start_pos + len(date_str) + 30)
            context = text_content[context_start:context_end].replace('\n', ' ')
            all_dates.append((date_str, context))
            print(f"📅 Found date '{date_str}': ...{context}...")
    
    if not all_dates:
        print("❌ No date patterns found")
    else:
        print(f"✅ Found {len(all_dates)} date patterns")
    
    print()
    
    # Look for specific CSSC sections
    print("📋 CSSC SECTION ANALYSIS:")
    print("-" * 30)
    
    cssc_sections = [
        'construction', 'equipment', 'radio', 'survey', 'inspection',
        'endorsement', 'annual', 'intermediate', 'special', 'renewal'
    ]
    
    for section in cssc_sections:
        if section in text_lower:
            # Find the section and surrounding text
            start_pos = text_lower.find(section)
            context_start = max(0, start_pos - 100)
            context_end = min(len(text_content), start_pos + len(section) + 100)
            context = text_content[context_start:context_end].replace('\n', ' ')
            print(f"📋 Found '{section}' section: ...{context}...")
    
    print()
    
    # Analyze why AI might fail
    print("🤖 AI PARSING FAILURE ANALYSIS:")
    print("-" * 40)
    
    # Check if this is a standard CSSC format
    if 'CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE' in text_content:
        print("✅ Standard CSSC certificate format detected")
    else:
        print("⚠️ Non-standard certificate format")
    
    # Check for typical docking information sections
    docking_indicators = [
        'dry dock', 'docking survey', 'bottom inspection', 
        'hull survey', 'construction survey date'
    ]
    
    has_docking_info = any(indicator in text_lower for indicator in docking_indicators)
    if has_docking_info:
        print("✅ Certificate contains docking-related information")
    else:
        print("❌ Certificate does NOT contain obvious docking information")
        print("   This explains why AI cannot extract docking dates")
    
    # Check certificate type
    if 'full term' in text_lower:
        print("✅ Full Term certificate - should have docking history")
    elif 'interim' in text_lower:
        print("⚠️ Interim certificate - may not have complete docking history")
    else:
        print("⚠️ Certificate type unclear")
    
    print()
    
    # Final recommendation
    print("💡 RECOMMENDATIONS:")
    print("-" * 20)
    
    if not has_docking_info:
        print("1. ❌ ROOT CAUSE: This CSSC certificate does NOT contain docking dates")
        print("   - CSSC certificates typically don't include dry docking history")
        print("   - They focus on construction and safety equipment compliance")
        print("   - Docking dates are usually found in:")
        print("     • Dry Docking Survey Reports")
        print("     • Classification Society Survey Reports") 
        print("     • Port State Control Inspection Reports")
        print("     • Ship's logbooks or maintenance records")
        print()
        print("2. 🔧 SOLUTION: Look for different certificate types:")
        print("   - Upload Dry Docking Survey certificates")
        print("   - Upload Classification Society survey reports")
        print("   - Check if ship has other certificates with docking history")
        print()
        print("3. 🤖 AI ENHANCEMENT: Update AI prompt to:")
        print("   - Recognize that CSSC certificates don't contain docking dates")
        print("   - Provide clear feedback about certificate type limitations")
        print("   - Suggest alternative certificate types for docking information")
    else:
        print("1. 🔧 AI PROMPT NEEDS IMPROVEMENT:")
        print("   - Certificate contains docking info but AI cannot extract it")
        print("   - Review and enhance docking date extraction patterns")
        print("   - Test with this specific certificate format")

def main():
    print("🔍 MINH ANH 09 - CERTIFICATE TEXT ANALYSIS")
    print("=" * 60)
    
    text_content = get_certificate_full_text()
    if text_content:
        analyze_certificate_text(text_content)
    else:
        print("❌ Failed to retrieve certificate text content")

if __name__ == "__main__":
    main()