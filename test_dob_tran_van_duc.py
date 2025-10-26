#!/usr/bin/env python3
"""
Test DOB validation với file PDF thực tế cho TRAN VAN DUC
"""
import requests
import json

# Configuration
BACKEND_URL = 'https://vessel-docs-sys.preview.emergentagent.com/api'
PDF_URL = 'https://customer-assets.emergentagent.com/job_shipmatrix/artifacts/fwad1ybv_2.%20CO%20DUC%20-%20PNM%20COC%20DOB.pdf'

print("=" * 70)
print("🧪 TEST: Add Crew Certificate với DOB Validation")
print("=" * 70)

# Step 1: Authenticate
print("\n📝 Step 1: Authentication...")
login_response = requests.post(
    f"{BACKEND_URL}/auth/login",
    json={"username": "admin1", "password": "123456", "remember_me": False}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.text}")
    exit(1)

token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print("✅ Authenticated successfully")

# Step 2: Get BROTHER 36 ship
print("\n📝 Step 2: Finding BROTHER 36 ship...")
ships_response = requests.get(f"{BACKEND_URL}/ships", headers=headers)
ship = None
for s in ships_response.json():
    if s.get("name") == "BROTHER 36":
        ship = s
        break

if not ship:
    print("❌ Ship BROTHER 36 not found")
    exit(1)

print(f"✅ Found ship: {ship.get('name')} (ID: {ship.get('id')})")

# Step 3: Find crew member TRAN VAN DUC
print("\n📝 Step 3: Finding crew TRAN VAN DUC...")
crew_response = requests.get(
    f"{BACKEND_URL}/crew?ship_name=BROTHER 36",
    headers=headers
)

crew = None
for c in crew_response.json():
    name = c.get("full_name", "").upper()
    if "TRAN VAN DUC" in name or "TRẦN VĂN ĐỨC" in name:
        crew = c
        break

if not crew:
    print("❌ Crew TRAN VAN DUC not found on BROTHER 36")
    print("Available crew:")
    for c in crew_response.json()[:5]:
        print(f"  - {c.get('full_name')}")
    exit(1)

print(f"✅ Found crew: {crew.get('full_name')}")
print(f"   Crew ID: {crew.get('id')}")
print(f"   Date of Birth: {crew.get('date_of_birth', 'NOT SET')}")

# Step 4: Download PDF file
print("\n📝 Step 4: Downloading PDF certificate...")
pdf_response = requests.get(PDF_URL)
if pdf_response.status_code != 200:
    print(f"❌ Failed to download PDF: {pdf_response.status_code}")
    exit(1)

pdf_content = pdf_response.content
print(f"✅ Downloaded PDF: {len(pdf_content)} bytes")

# Step 5: Upload certificate for analysis
print("\n📝 Step 5: Uploading certificate for analysis...")
print(f"   Ship ID: {ship.get('id')}")
print(f"   Crew ID: {crew.get('id')}")

files = {"cert_file": ("co_duc_coc.pdf", pdf_content, "application/pdf")}
data = {
    "ship_id": ship.get("id"),
    "crew_id": crew.get("id")
}

analyze_response = requests.post(
    f"{BACKEND_URL}/crew-certificates/analyze-file",
    files=files,
    data=data,
    headers=headers,
    timeout=120
)

print(f"\n📊 Response Status: {analyze_response.status_code}")
print("=" * 70)

if analyze_response.status_code == 200:
    result = analyze_response.json()
    print("✅ SUCCESS - Certificate analyzed successfully")
    print(f"\n📋 Analysis Result:")
    print(f"   Crew Name: {result.get('crew_name')}")
    print(f"   Passport: {result.get('passport')}")
    print(f"   Rank: {result.get('rank')}")
    print(f"   Date of Birth (returned): {result.get('date_of_birth')}")
    
    analysis = result.get('analysis', {})
    print(f"\n🔍 Certificate Fields:")
    print(f"   Cert Name: {analysis.get('cert_name')}")
    print(f"   Cert No: {analysis.get('cert_no')}")
    print(f"   Holder Name: {analysis.get('holder_name')}")
    print(f"   Issued By: {analysis.get('issued_by')}")
    print(f"   Issued Date: {analysis.get('issued_date')}")
    print(f"   Expiry Date: {analysis.get('expiry_date')}")
    
    print("\n✅ NO DOB MISMATCH - Validation passed or skipped")
    
elif analyze_response.status_code == 400:
    error_data = analyze_response.json().get("detail", {})
    error_code = error_data.get("error")
    
    print(f"⚠️ VALIDATION ERROR: {error_code}")
    print(f"\n📋 Error Details:")
    print(f"   Message: {error_data.get('message')}")
    
    if error_code == "DATE_OF_BIRTH_MISMATCH":
        print(f"\n🎂 Date of Birth Comparison:")
        print(f"   AI Extracted DOB: {error_data.get('ai_extracted_dob')}")
        print(f"   Crew DOB (Database): {error_data.get('crew_dob')}")
        print(f"   Crew Name: {error_data.get('crew_name')}")
        print("\n✅ DOB VALIDATION IS WORKING!")
        print("   Modal should appear in frontend with these values")
        
    elif error_code == "CERTIFICATE_HOLDER_MISMATCH":
        print(f"\n👤 Holder Name Comparison:")
        print(f"   Certificate Holder: {error_data.get('holder_name')}")
        print(f"   Selected Crew: {error_data.get('crew_name')}")
        print(f"   Crew Name (EN): {error_data.get('crew_name_en')}")
        print("\n⚠️ Holder name validation failed first")
        print("   (DOB validation runs AFTER holder name validation)")
    else:
        print(f"\n❌ Other error: {error_data}")
        
else:
    print(f"❌ Unexpected status: {analyze_response.status_code}")
    print(f"Response: {analyze_response.text[:500]}")

print("\n" + "=" * 70)
