#!/usr/bin/env python3
"""
Test Certificate Duplicate Detection Workflow
"""
import requests
import json
import sys
import os

# Add backend to path
sys.path.append('/app/backend')

# Test backend URL
backend_url = 'http://localhost:8001'

def test_duplicate_detection():
    """Test the duplicate detection workflow"""
    
    # Login
    login_data = {
        "username": "admin1",
        "password": "123456"
    }
    
    session = requests.Session()
    
    print("🔐 Logging in...")
    login_response = session.post(f"{backend_url}/api/auth/login", json=login_data)
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        token = login_result.get('access_token')
        session.headers.update({'Authorization': f'Bearer {token}'})
        print("✅ Login successful")
        
        # Get ships and certificates to understand duplicate logic
        print("\n🚢 Getting ships...")
        ships_response = session.get(f"{backend_url}/api/ships")
        
        if ships_response.status_code == 200:
            ships = ships_response.json()
            if ships:
                test_ship = ships[0]
                ship_id = test_ship['id']
                ship_name = test_ship.get('name', 'Unknown')
                
                print(f"Testing with ship: {ship_name} (ID: {ship_id})")
                
                # Get certificates for this ship
                certs_response = session.get(f"{backend_url}/api/ships/{ship_id}/certificates")
                
                if certs_response.status_code == 200:
                    certificates = certs_response.json()
                    print(f"\n📋 Found {len(certificates)} certificates for {ship_name}:")
                    
                    for i, cert in enumerate(certificates[:5]):  # Show first 5
                        print(f"   {i+1}. {cert.get('cert_name', 'Unknown')}")
                        print(f"      Certificate No: {cert.get('cert_no', 'N/A')}")
                        print(f"      Certificate Type: {cert.get('cert_type', 'Unknown')}")
                        print(f"      Issue Date: {cert.get('issue_date', 'N/A')}")
                        print()
                    
                    # Test duplicate detection API endpoint
                    if certificates:
                        print("🔍 Testing duplicate detection logic...")
                        
                        # Create a test analysis result that would match existing certificate
                        sample_cert = certificates[0]
                        test_analysis = {
                            "ship_id": ship_id,
                            "analysis_result": {
                                "cert_name": sample_cert.get('cert_name'),
                                "cert_no": sample_cert.get('cert_no'),
                                "cert_type": sample_cert.get('cert_type'),
                                "issue_date": sample_cert.get('issue_date'),
                                "valid_date": sample_cert.get('valid_date'),
                                "category": "certificates"
                            }
                        }
                        
                        # Test the duplicate check API
                        duplicate_response = session.post(
                            f"{backend_url}/api/certificates/check-duplicates",
                            json=test_analysis
                        )
                        
                        if duplicate_response.status_code == 200:
                            duplicate_result = duplicate_response.json()
                            print("✅ Duplicate check API working")
                            print(f"   Duplicates found: {len(duplicate_result.get('duplicates', []))}")
                            print(f"   Has issues: {duplicate_result.get('has_issues', False)}")
                            
                            if duplicate_result.get('duplicates'):
                                for dup in duplicate_result['duplicates']:
                                    print(f"      - Duplicate: {dup['certificate'].get('cert_name')} (Similarity: {dup['similarity']}%)")
                        else:
                            print(f"❌ Duplicate check API failed: {duplicate_response.status_code}")
                        
                        # Explain the duplicate detection criteria
                        print(f"\n📚 DUPLICATE DETECTION CRITERIA:")
                        print(f"   1. Certificate Number (cert_no) must match exactly (case insensitive)")
                        print(f"   2. Certificate Name (cert_name) must match exactly (case insensitive)")
                        print(f"   3. Both fields must be present and non-empty")
                        print(f"   4. Similarity = 100% only if BOTH fields match exactly")
                        print(f"   5. Duplicate threshold = 100% (exact match required)")
                        
                        print(f"\n🔄 WORKFLOW PROCESS:")
                        print(f"   1. User uploads certificate file")
                        print(f"   2. AI extracts cert_name and cert_no from file")
                        print(f"   3. System searches existing certificates for same ship")
                        print(f"   4. Compares cert_name and cert_no (case insensitive)")
                        print(f"   5. If 100% match found → status = 'duplicate'")
                        print(f"   6. Frontend shows 'Already exists' message")
                        print(f"   7. Certificate is not created in database")
                
                else:
                    print(f"❌ Failed to get certificates: {certs_response.status_code}")
            else:
                print("❌ No ships found")
        else:
            print(f"❌ Failed to get ships: {ships_response.status_code}")
    else:
        print(f"❌ Login failed: {login_response.text}")

if __name__ == "__main__":
    test_duplicate_detection()