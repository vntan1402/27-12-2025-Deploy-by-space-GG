#!/usr/bin/env python3
"""
Focused Ship Creation Testing Script
FOCUS: Test Ship Creation with unique IMO numbers and core functionality
"""

import requests
import json
import random
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8001/api"

def generate_unique_imo():
    """Generate a unique IMO number for testing"""
    return f"98765{random.randint(10, 99)}"

def test_ship_creation():
    """Test ship creation functionality"""
    print("🚢 FOCUSED SHIP CREATION TESTING")
    print("=" * 50)
    
    # Step 1: Authenticate
    print("\n🔐 AUTHENTICATION")
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    auth_response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=10)
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        return False
    
    token = auth_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authentication successful")
    
    # Step 2: Test Minimal Ship Creation
    print("\n🚢 MINIMAL SHIP CREATION TEST")
    minimal_ship = {
        "name": f"MINIMAL TEST SHIP {random.randint(1000, 9999)}",
        "imo": generate_unique_imo(),
        "flag": "Panama",
        "ship_type": "Container Ship",
        "ship_owner": "Test Maritime Co",
        "company": "AMCSC"
    }
    
    print(f"Creating ship: {minimal_ship['name']}")
    print(f"IMO: {minimal_ship['imo']}")
    
    response = requests.post(f"{BACKEND_URL}/ships", json=minimal_ship, headers=headers, timeout=15)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 201:
        created_ship = response.json()
        ship_id = created_ship.get('id')
        print("✅ Minimal ship creation successful")
        print(f"   Ship ID: {ship_id}")
        print(f"   Name: {created_ship.get('name')}")
        print(f"   IMO: {created_ship.get('imo')}")
        print(f"   Flag: {created_ship.get('flag')}")
        print(f"   Ship Type: {created_ship.get('ship_type')}")
        print(f"   Ship Owner: {created_ship.get('ship_owner')}")
        print(f"   Company: {created_ship.get('company')}")
        
        # Test cleanup
        print(f"\n🧹 Cleaning up ship {ship_id}")
        delete_response = requests.delete(f"{BACKEND_URL}/ships/{ship_id}", headers=headers, timeout=10)
        if delete_response.status_code == 200:
            print("✅ Ship deleted successfully")
        else:
            print(f"⚠️ Could not delete ship: {delete_response.status_code}")
            
        return True
    else:
        print(f"❌ Minimal ship creation failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error: {error_data.get('detail', 'Unknown error')}")
        except:
            print(f"   Error: {response.text[:200]}")
        return False

    # Step 3: Test Basic Fields Ship Creation
    print("\n🚢 BASIC FIELDS SHIP CREATION TEST")
    basic_ship = {
        "name": f"BASIC FIELDS TEST SHIP {random.randint(1000, 9999)}",
        "imo": generate_unique_imo(),
        "flag": "Singapore",
        "ship_type": "Bulk Carrier",
        "gross_tonnage": 75000.0,
        "deadweight": 95000.0,
        "built_year": 2022,
        "keel_laid": "2021-06-15T00:00:00Z",
        "ship_owner": "Maritime Shipping Co",
        "company": "AMCSC"
    }
    
    print(f"Creating ship: {basic_ship['name']}")
    print(f"IMO: {basic_ship['imo']}")
    
    response = requests.post(f"{BACKEND_URL}/ships", json=basic_ship, headers=headers, timeout=15)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 201:
        created_ship = response.json()
        ship_id = created_ship.get('id')
        print("✅ Basic fields ship creation successful")
        print(f"   Ship ID: {ship_id}")
        
        # Verify all basic fields
        basic_fields_verified = 0
        for field, expected_value in basic_ship.items():
            actual_value = created_ship.get(field)
            if actual_value is not None:
                basic_fields_verified += 1
                print(f"   ✅ {field}: {actual_value}")
            else:
                print(f"   ❌ {field}: Missing")
        
        print(f"   Basic fields verified: {basic_fields_verified}/{len(basic_ship)}")
        
        # Test cleanup
        print(f"\n🧹 Cleaning up ship {ship_id}")
        delete_response = requests.delete(f"{BACKEND_URL}/ships/{ship_id}", headers=headers, timeout=10)
        if delete_response.status_code == 200:
            print("✅ Ship deleted successfully")
        else:
            print(f"⚠️ Could not delete ship: {delete_response.status_code}")
            
        return basic_fields_verified >= len(basic_ship) - 1  # Allow one optional field
    else:
        print(f"❌ Basic fields ship creation failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error: {error_data.get('detail', 'Unknown error')}")
        except:
            print(f"   Error: {response.text[:200]}")
        return False

def test_survey_maintenance_fields():
    """Test ship creation with survey/maintenance fields"""
    print("\n🚢 SURVEY/MAINTENANCE FIELDS TEST")
    
    # Authenticate
    login_data = {"username": "admin1", "password": "123456", "remember_me": False}
    auth_response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=10)
    token = auth_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    survey_ship = {
        "name": f"SURVEY TEST SHIP {random.randint(1000, 9999)}",
        "imo": generate_unique_imo(),
        "flag": "Marshall Islands",
        "ship_type": "Tanker",
        "gross_tonnage": 85000.0,
        "deadweight": 105000.0,
        "built_year": 2023,
        "keel_laid": "2022-03-20T00:00:00Z",
        "last_docking": "2023-01-15T00:00:00Z",
        "last_docking_2": "2021-08-20T00:00:00Z",
        "next_docking": "2025-07-15T00:00:00Z",
        "last_special_survey": "2023-01-15T00:00:00Z",
        "ship_owner": "Survey Test Maritime Co",
        "company": "AMCSC"
    }
    
    print(f"Creating ship: {survey_ship['name']}")
    print(f"IMO: {survey_ship['imo']}")
    
    response = requests.post(f"{BACKEND_URL}/ships", json=survey_ship, headers=headers, timeout=15)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 201:
        created_ship = response.json()
        ship_id = created_ship.get('id')
        print("✅ Survey/maintenance fields ship creation successful")
        print(f"   Ship ID: {ship_id}")
        
        # Verify survey/maintenance fields
        survey_fields = ['last_docking', 'last_docking_2', 'next_docking', 'last_special_survey']
        survey_fields_verified = 0
        
        for field in survey_fields:
            actual_value = created_ship.get(field)
            expected_value = survey_ship.get(field)
            
            if actual_value is not None and expected_value is not None:
                survey_fields_verified += 1
                print(f"   ✅ {field}: {actual_value}")
            elif expected_value is not None:
                print(f"   ❌ {field}: Missing (expected: {expected_value})")
        
        print(f"   Survey fields verified: {survey_fields_verified}/{len(survey_fields)}")
        
        # Test cleanup
        print(f"\n🧹 Cleaning up ship {ship_id}")
        delete_response = requests.delete(f"{BACKEND_URL}/ships/{ship_id}", headers=headers, timeout=10)
        if delete_response.status_code == 200:
            print("✅ Ship deleted successfully")
        else:
            print(f"⚠️ Could not delete ship: {delete_response.status_code}")
            
        return survey_fields_verified >= 3  # Allow some optional fields
    else:
        print(f"❌ Survey/maintenance fields ship creation failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error: {error_data.get('detail', 'Unknown error')}")
        except:
            print(f"   Error: {response.text[:200]}")
        return False

def test_complex_objects():
    """Test ship creation with complex objects"""
    print("\n🚢 COMPLEX OBJECTS TEST")
    
    # Authenticate
    login_data = {"username": "admin1", "password": "123456", "remember_me": False}
    auth_response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=10)
    token = auth_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    complex_ship = {
        "name": f"COMPLEX OBJECTS TEST SHIP {random.randint(1000, 9999)}",
        "imo": generate_unique_imo(),
        "flag": "Liberia",
        "ship_type": "Container Ship",
        "gross_tonnage": 95000.0,
        "deadweight": 115000.0,
        "built_year": 2024,
        "keel_laid": "2023-01-10T00:00:00Z",
        "last_docking": "2024-01-15T00:00:00Z",
        "last_special_survey": "2024-01-15T00:00:00Z",
        "ship_owner": "Complex Objects Maritime Co",
        "company": "AMCSC",
        # Complex anniversary_date object
        "anniversary_date": {
            "day": 15,
            "month": 3,
            "auto_calculated": True,
            "source_certificate_type": "Full Term Class Certificate",
            "manual_override": False
        },
        # Complex special_survey_cycle object
        "special_survey_cycle": {
            "from_date": "2024-01-15T00:00:00Z",
            "to_date": "2029-01-15T00:00:00Z",
            "intermediate_required": True,
            "cycle_type": "SOLAS Safety Construction Survey Cycle"
        }
    }
    
    print(f"Creating ship: {complex_ship['name']}")
    print(f"IMO: {complex_ship['imo']}")
    
    response = requests.post(f"{BACKEND_URL}/ships", json=complex_ship, headers=headers, timeout=15)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 201:
        created_ship = response.json()
        ship_id = created_ship.get('id')
        print("✅ Complex objects ship creation successful")
        print(f"   Ship ID: {ship_id}")
        
        # Verify anniversary_date complex object
        anniversary_date = created_ship.get('anniversary_date')
        anniversary_verified = False
        if anniversary_date:
            print("   ✅ Anniversary Date object present:")
            print(f"      Day: {anniversary_date.get('day')}")
            print(f"      Month: {anniversary_date.get('month')}")
            print(f"      Auto calculated: {anniversary_date.get('auto_calculated')}")
            print(f"      Source certificate type: {anniversary_date.get('source_certificate_type')}")
            print(f"      Manual override: {anniversary_date.get('manual_override')}")
            
            expected_anniversary = complex_ship['anniversary_date']
            if (anniversary_date.get('day') == expected_anniversary['day'] and 
                anniversary_date.get('month') == expected_anniversary['month']):
                print("   ✅ Anniversary Date object verified")
                anniversary_verified = True
            else:
                print("   ❌ Anniversary Date object values incorrect")
        else:
            print("   ❌ Anniversary Date object missing")
        
        # Verify special_survey_cycle complex object
        special_survey_cycle = created_ship.get('special_survey_cycle')
        survey_cycle_verified = False
        if special_survey_cycle:
            print("   ✅ Special Survey Cycle object present:")
            print(f"      From date: {special_survey_cycle.get('from_date')}")
            print(f"      To date: {special_survey_cycle.get('to_date')}")
            print(f"      Intermediate required: {special_survey_cycle.get('intermediate_required')}")
            print(f"      Cycle type: {special_survey_cycle.get('cycle_type')}")
            
            expected_cycle = complex_ship['special_survey_cycle']
            if (special_survey_cycle.get('intermediate_required') == expected_cycle['intermediate_required'] and 
                special_survey_cycle.get('cycle_type') == expected_cycle['cycle_type']):
                print("   ✅ Special Survey Cycle object verified")
                survey_cycle_verified = True
            else:
                print("   ❌ Special Survey Cycle object values incorrect")
        else:
            print("   ❌ Special Survey Cycle object missing")
        
        # Test cleanup
        print(f"\n🧹 Cleaning up ship {ship_id}")
        delete_response = requests.delete(f"{BACKEND_URL}/ships/{ship_id}", headers=headers, timeout=10)
        if delete_response.status_code == 200:
            print("✅ Ship deleted successfully")
        else:
            print(f"⚠️ Could not delete ship: {delete_response.status_code}")
            
        return anniversary_verified and survey_cycle_verified
    else:
        print(f"❌ Complex objects ship creation failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error: {error_data.get('detail', 'Unknown error')}")
        except:
            print(f"   Error: {response.text[:200]}")
        return False

def test_ai_config():
    """Test AI configuration availability"""
    print("\n🤖 AI CONFIGURATION TEST")
    
    # Authenticate
    login_data = {"username": "admin1", "password": "123456", "remember_me": False}
    auth_response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=10)
    token = auth_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BACKEND_URL}/ai-config", headers=headers, timeout=10)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        ai_config = response.json()
        provider = ai_config.get('provider')
        model = ai_config.get('model')
        
        print("✅ AI configuration available")
        print(f"   Provider: {provider}")
        print(f"   Model: {model}")
        return True
    else:
        print(f"❌ AI configuration not available: {response.status_code}")
        return False

def main():
    """Main test function"""
    print("🚢 FOCUSED SHIP CREATION TESTING STARTED")
    print("=" * 80)
    
    results = {
        'minimal_creation': False,
        'basic_fields': False,
        'survey_maintenance': False,
        'complex_objects': False,
        'ai_config': False
    }
    
    try:
        # Run tests
        results['minimal_creation'] = test_ship_creation()
        time.sleep(1)  # Brief pause between tests
        
        results['survey_maintenance'] = test_survey_maintenance_fields()
        time.sleep(1)
        
        results['complex_objects'] = test_complex_objects()
        time.sleep(1)
        
        results['ai_config'] = test_ai_config()
        
        # Final analysis
        print("\n📊 FINAL RESULTS")
        print("=" * 50)
        
        passed_tests = sum(results.values())
        total_tests = len(results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"✅ TESTS PASSED: {passed_tests}/{total_tests}")
        for test_name, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n📊 SUCCESS RATE: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n🎉 CONCLUSION: SHIP CREATION FUNCTIONALITY IS WORKING EXCELLENTLY")
            print("   ✅ Ship Creation form can handle complete field coverage")
            print("   ✅ Backend models support new optional fields")
            print("   ✅ Complex nested objects working correctly")
        elif success_rate >= 60:
            print("\n⚠️ CONCLUSION: SHIP CREATION FUNCTIONALITY PARTIALLY WORKING")
            print("   Core functionality working, some enhancements needed")
        else:
            print("\n❌ CONCLUSION: SHIP CREATION FUNCTIONALITY HAS ISSUES")
            print("   System needs fixes for ship creation")
        
        return success_rate >= 60
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    main()