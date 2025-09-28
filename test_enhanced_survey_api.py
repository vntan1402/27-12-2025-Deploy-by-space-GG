#!/usr/bin/env python3
"""
Test the enhanced survey logic API endpoints
"""
import asyncio
import sys
import os
import json
import requests
from datetime import datetime

# Add backend to path
sys.path.append('/app/backend')

async def test_enhanced_survey_api():
    """Test the enhanced survey logic API endpoints"""
    
    # Get the backend URL from environment
    backend_url = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    
    # Test credentials (from test data)
    login_data = {
        "email": "admin1@example.com",
        "password": "123456"
    }
    
    session = requests.Session()
    
    try:
        print("🔐 Logging in...")
        login_response = session.post(f"{backend_url}/api/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
            return
            
        login_result = login_response.json()
        token = login_result.get('access_token')
        
        if not token:
            print("❌ No access token received")
            return
        
        print("✅ Login successful")
        
        # Set authorization header
        session.headers.update({'Authorization': f'Bearer {token}'})
        
        # Test 1: Get survey type analysis
        print("\n📊 Testing survey type analysis endpoint...")
        analysis_response = session.get(f"{backend_url}/api/certificates/survey-type-analysis")
        
        if analysis_response.status_code == 200:
            analysis_result = analysis_response.json()
            print("✅ Survey type analysis successful")
            
            stats = analysis_result.get('improvement_statistics', {})
            print(f"   Total certificates: {stats.get('total_certificates', 0)}")
            print(f"   Potential improvements: {stats.get('potential_improvements', 0)}")
            print(f"   Improvement rate: {stats.get('improvement_rate', '0.0%')}")
            print(f"   Unknown survey types: {stats.get('unknown_survey_types', 0)}")
            
            # Show some improvement examples
            improvements = analysis_result.get('analysis', {}).get('potential_improvements', [])
            if improvements:
                print(f"\n   📋 Sample improvements:")
                for improvement in improvements[:3]:
                    print(f"      - {improvement['cert_name']}")
                    print(f"        Ship: {improvement['ship_name']}")
                    print(f"        {improvement['current']} → {improvement['enhanced']}")
                    print(f"        Reasoning: {improvement['reasoning']}")
                    print()
        else:
            print(f"❌ Survey type analysis failed: {analysis_response.status_code} - {analysis_response.text}")
            return
        
        # Test 2: Update all survey types with enhanced logic
        print("\n🔄 Testing enhanced survey type update...")
        update_response = session.post(f"{backend_url}/api/certificates/update-survey-types-enhanced")
        
        if update_response.status_code == 200:
            update_result = update_response.json()
            print("✅ Enhanced survey type update successful")
            print(f"   Updated certificates: {update_result.get('updated_count', 0)}")
            print(f"   Total certificates: {update_result.get('total_certificates', 0)}")
            print(f"   Improvement rate: {update_result.get('improvement_rate', '0.0%')}")
            
            # Show some update examples
            results = update_result.get('results', [])
            if results:
                print(f"\n   📋 Sample updates:")
                for result in results[:3]:
                    print(f"      - {result['cert_name']}")
                    print(f"        Ship: {result['ship_name']}")
                    print(f"        {result['old_survey_type']} → {result['new_survey_type']}")
                    print(f"        Reasoning: {result['reasoning']}")
                    print()
        else:
            print(f"❌ Enhanced survey type update failed: {update_response.status_code} - {update_response.text}")
            return
        
        # Test 3: Test individual certificate enhanced survey type determination
        print("\n🔍 Testing individual certificate enhanced survey type...")
        
        # First, get a certificate ID
        certs_response = session.get(f"{backend_url}/api/certificates")
        if certs_response.status_code == 200:
            certificates = certs_response.json()
            if certificates:
                test_cert_id = certificates[0]['id']
                test_cert_name = certificates[0].get('cert_name', 'Unknown')
                
                print(f"   Testing with certificate: {test_cert_name} (ID: {test_cert_id})")
                
                individual_response = session.post(f"{backend_url}/api/certificates/{test_cert_id}/determine-survey-type-enhanced")
                
                if individual_response.status_code == 200:
                    individual_result = individual_response.json()
                    print("✅ Individual certificate enhanced survey type successful")
                    print(f"   Certificate: {individual_result.get('certificate_name', 'Unknown')}")
                    print(f"   Ship: {individual_result.get('ship_name', 'Unknown')}")
                    print(f"   Previous: {individual_result.get('previous_survey_type', 'Unknown')}")
                    print(f"   Enhanced: {individual_result.get('enhanced_survey_type', 'Unknown')}")
                    print(f"   Changed: {individual_result.get('changed', False)}")
                    print(f"   Reasoning: {individual_result.get('reasoning', 'No reasoning provided')}")
                else:
                    print(f"❌ Individual certificate test failed: {individual_response.status_code} - {individual_response.text}")
            else:
                print("❌ No certificates found to test with")
        else:
            print(f"❌ Failed to get certificates: {certs_response.status_code}")
        
        print("\n🎉 Enhanced Survey Logic API Testing Complete!")
        
    except Exception as e:
        print(f"❌ Error testing enhanced survey API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set backend URL environment variable
    os.environ['REACT_APP_BACKEND_URL'] = 'http://localhost:8001'
    
    asyncio.run(test_enhanced_survey_api())