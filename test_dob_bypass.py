#!/usr/bin/env python3
"""Test DOB validation bypass"""
import requests

BACKEND_URL = 'https://crewcert-manager.preview.emergentagent.com/api'
PDF_URL = 'https://customer-assets.emergentagent.com/job_shipmatrix/artifacts/fwad1ybv_2.%20CO%20DUC%20-%20PNM%20COC%20DOB.pdf'

print("🧪 TEST: DOB Validation BYPASS")
print("=" * 70)

# Authenticate
login_response = requests.post(
    f"{BACKEND_URL}/auth/login",
    json={"username": "admin1", "password": "123456", "remember_me": False}
)
token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Get ship and crew
ships_response = requests.get(f"{BACKEND_URL}/ships", headers=headers)
ship = next(s for s in ships_response.json() if s.get("name") == "BROTHER 36")

crew_response = requests.get(f"{BACKEND_URL}/crew?ship_name=BROTHER 36", headers=headers)
crew = next(c for c in crew_response.json() 
            if "TRAN VAN DUC" in c.get("full_name", "").upper() or "TRẦN VĂN ĐỨC" in c.get("full_name", ""))

print(f"✅ Found crew: {crew.get('full_name')}")
print(f"   Crew DOB: {crew.get('date_of_birth')}")

# Download PDF
pdf_content = requests.get(PDF_URL).content

# Test with bypass_dob_validation=true
print("\n📝 Uploading with bypass_dob_validation=true...")
files = {"cert_file": ("co_duc_coc.pdf", pdf_content, "application/pdf")}
data = {
    "ship_id": ship.get("id"),
    "crew_id": crew.get("id"),
    "bypass_validation": "true",  # Also bypass holder name validation
    "bypass_dob_validation": "true"  # Bypass DOB validation
}

response = requests.post(
    f"{BACKEND_URL}/crew-certificates/analyze-file",
    files=files,
    data=data,
    headers=headers,
    timeout=120
)

print(f"\n📊 Response Status: {response.status_code}")
print("=" * 70)

if response.status_code == 200:
    result = response.json()
    print("✅ SUCCESS - Bypass worked!")
    print(f"   AI extracted DOB would have been validated but was bypassed")
    print(f"   Certificate analyzed: {result.get('analysis', {}).get('cert_name')}")
else:
    print(f"❌ FAILED - Expected 200 but got {response.status_code}")
    print(f"   Response: {response.text[:200]}")

print("=" * 70)
