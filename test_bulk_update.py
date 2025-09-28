#!/usr/bin/env python3
"""
Test bulk update of survey types with enhanced logic
"""
import requests
import json

backend_url = 'http://localhost:8001'

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
    
    # Test bulk update with enhanced logic
    print("\n🔄 Testing bulk update with enhanced survey logic...")
    
    bulk_response = session.post(f"{backend_url}/api/certificates/update-survey-types-enhanced")
    print(f"Bulk update status: {bulk_response.status_code}")
    
    if bulk_response.status_code == 200:
        result = bulk_response.json()
        print("✅ Bulk update successful!")
        print(f"Updated certificates: {result.get('updated_count', 0)}")
        print(f"Total certificates: {result.get('total_certificates', 0)}")
        print(f"Improvement rate: {result.get('improvement_rate', '0.0%')}")
        
        # Show some results
        results = result.get('results', [])
        if results:
            print(f"\n📋 Updated certificates:")
            for update_result in results[:5]:  # Show first 5
                print(f"   - {update_result['cert_name']}")
                print(f"     Ship: {update_result['ship_name']}")
                print(f"     {update_result['old_survey_type']} → {update_result['new_survey_type']}")
                print(f"     Reasoning: {update_result['reasoning']}")
                print()
        else:
            print("   No certificates were updated (all already have optimal survey types)")
    else:
        print(f"❌ Bulk update failed: {bulk_response.text}")
        
    # Test survey analysis
    print("\n📊 Testing survey type analysis...")
    analysis_response = session.get(f"{backend_url}/api/certificates/survey-type-analysis")
    print(f"Analysis status: {analysis_response.status_code}")
    
    if analysis_response.status_code == 200:
        analysis_result = analysis_response.json()
        print("✅ Analysis successful!")
        
        stats = analysis_result.get('improvement_statistics', {})
        print(f"Total certificates: {stats.get('total_certificates', 0)}")
        print(f"Potential improvements: {stats.get('potential_improvements', 0)}")
        print(f"Improvement rate: {stats.get('improvement_rate', '0.0%')}")
        print(f"Unknown survey types: {stats.get('unknown_survey_types', 0)}")
        
        # Show certificate categories
        analysis = analysis_result.get('analysis', {})
        cert_categories = analysis.get('certificate_categories', {})
        
        if cert_categories:
            print(f"\n📋 Certificate categories:")
            for category, info in cert_categories.items():
                print(f"   {category}: {info['count']} certificates")
                survey_types = info.get('survey_types', {})
                for survey_type, count in survey_types.items():
                    print(f"      - {survey_type}: {count}")
    else:
        print(f"❌ Analysis failed: {analysis_response.text}")
        
else:
    print(f"❌ Login failed: {login_response.text}")