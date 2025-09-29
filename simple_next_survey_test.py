#!/usr/bin/env python3
"""
Simple Next Survey Calculation Test
Testing the POST /api/ships/{ship_id}/update-next-survey endpoint with existing ships
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = 'https://certflow-2.preview.emergentagent.com/api'

def authenticate():
    """Authenticate with admin1/123456"""
    try:
        login_data = {
            "username": "admin1",
            "password": "123456",
            "remember_me": False
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user = data.get("user", {})
            print(f"✅ Authentication successful - User: {user.get('username')} ({user.get('role')})")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return None

def get_headers(token):
    """Get authentication headers"""
    return {"Authorization": f"Bearer {token}"}

def test_next_survey_calculation(token):
    """Test Next Survey calculation with existing ships"""
    try:
        print("\n🎯 TESTING NEXT SURVEY CALCULATION API")
        print("=" * 60)
        
        # Get list of ships
        response = requests.get(f"{BACKEND_URL}/ships", headers=get_headers(token), timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Failed to get ships: {response.status_code}")
            return False
        
        ships = response.json()
        print(f"📋 Found {len(ships)} ships")
        
        # Test with ships that have anniversary_date and special_survey_cycle
        test_results = []
        
        for ship in ships:
            ship_id = ship.get('id')
            ship_name = ship.get('name')
            anniversary_date = ship.get('anniversary_date')
            special_survey_cycle = ship.get('special_survey_cycle')
            
            print(f"\n🚢 Testing ship: {ship_name} (ID: {ship_id})")
            
            # Show ship survey data
            if anniversary_date:
                day = anniversary_date.get('day')
                month = anniversary_date.get('month')
                print(f"   Anniversary Date: {day}/{month}")
            else:
                print("   Anniversary Date: Not set")
            
            if special_survey_cycle:
                from_date = special_survey_cycle.get('from_date', '')[:10]  # Just date part
                to_date = special_survey_cycle.get('to_date', '')[:10]
                cycle_type = special_survey_cycle.get('cycle_type')
                print(f"   Special Survey Cycle: {from_date} to {to_date} ({cycle_type})")
            else:
                print("   Special Survey Cycle: Not set")
            
            # Get certificates for this ship
            cert_response = requests.get(f"{BACKEND_URL}/certificates?ship_id={ship_id}", 
                                       headers=get_headers(token), timeout=30)
            
            if cert_response.status_code == 200:
                certificates = cert_response.json()
                print(f"   Certificates: {len(certificates)} found")
                
                if len(certificates) > 0:
                    # Test the Next Survey calculation API
                    print(f"   🎯 Testing POST /api/ships/{ship_id}/update-next-survey")
                    
                    survey_response = requests.post(
                        f"{BACKEND_URL}/ships/{ship_id}/update-next-survey",
                        headers=get_headers(token),
                        timeout=60
                    )
                    
                    print(f"   Response Status: {survey_response.status_code}")
                    
                    if survey_response.status_code == 200:
                        survey_data = survey_response.json()
                        
                        if survey_data.get('success'):
                            print("   ✅ Next Survey calculation successful")
                            
                            updated_count = survey_data.get('updated_count', 0)
                            total_certificates = survey_data.get('total_certificates', 0)
                            results = survey_data.get('results', [])
                            
                            print(f"   📊 Updated {updated_count}/{total_certificates} certificates")
                            
                            # Analyze results for IMO compliance
                            compliance_results = analyze_imo_compliance(results, anniversary_date, special_survey_cycle)
                            test_results.append({
                                'ship_name': ship_name,
                                'ship_id': ship_id,
                                'success': True,
                                'updated_count': updated_count,
                                'total_certificates': total_certificates,
                                'compliance': compliance_results,
                                'results': results[:3]  # Show first 3 results
                            })
                            
                            # Show detailed results
                            for i, result in enumerate(results[:3]):  # Show first 3
                                cert_name = result.get('cert_name', 'Unknown')
                                cert_type = result.get('cert_type', 'Unknown')
                                new_next_survey = result.get('new_next_survey')
                                new_next_survey_type = result.get('new_next_survey_type')
                                reasoning = result.get('reasoning', '')
                                
                                print(f"   📋 Certificate {i+1}: {cert_name} ({cert_type})")
                                print(f"      Next Survey: {new_next_survey}")
                                print(f"      Next Survey Type: {new_next_survey_type}")
                                print(f"      Reasoning: {reasoning}")
                        else:
                            print(f"   ❌ Next Survey calculation failed: {survey_data.get('message')}")
                            test_results.append({
                                'ship_name': ship_name,
                                'ship_id': ship_id,
                                'success': False,
                                'error': survey_data.get('message')
                            })
                    else:
                        print(f"   ❌ API call failed: {survey_response.status_code}")
                        try:
                            error_data = survey_response.json()
                            print(f"      Error: {error_data.get('detail', 'Unknown error')}")
                        except:
                            print(f"      Error: {survey_response.text[:200]}")
                        
                        test_results.append({
                            'ship_name': ship_name,
                            'ship_id': ship_id,
                            'success': False,
                            'error': f"HTTP {survey_response.status_code}"
                        })
                else:
                    print("   ⚠️ No certificates found - skipping")
            else:
                print(f"   ❌ Failed to get certificates: {cert_response.status_code}")
        
        # Final analysis
        print("\n📊 FINAL ANALYSIS")
        print("=" * 60)
        
        successful_tests = [r for r in test_results if r.get('success')]
        failed_tests = [r for r in test_results if not r.get('success')]
        
        print(f"✅ Successful tests: {len(successful_tests)}")
        print(f"❌ Failed tests: {len(failed_tests)}")
        
        if successful_tests:
            print("\n🎯 IMO COMPLIANCE ANALYSIS:")
            
            total_compliance_checks = 0
            passed_compliance_checks = 0
            
            for test in successful_tests:
                compliance = test.get('compliance', {})
                ship_name = test.get('ship_name')
                
                print(f"\n🚢 {ship_name}:")
                for check_name, passed in compliance.items():
                    status = "✅" if passed else "❌"
                    print(f"   {status} {check_name.replace('_', ' ').title()}")
                    total_compliance_checks += 1
                    if passed:
                        passed_compliance_checks += 1
            
            compliance_rate = (passed_compliance_checks / total_compliance_checks * 100) if total_compliance_checks > 0 else 0
            print(f"\n📊 Overall IMO Compliance Rate: {compliance_rate:.1f}% ({passed_compliance_checks}/{total_compliance_checks})")
            
            if compliance_rate >= 80:
                print("🎉 EXCELLENT: Next Survey calculation logic is working well and follows IMO regulations")
            elif compliance_rate >= 60:
                print("⚠️ GOOD: Next Survey calculation is mostly working but some improvements needed")
            else:
                print("❌ NEEDS WORK: Next Survey calculation has significant compliance issues")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   🚢 {test.get('ship_name')}: {test.get('error')}")
        
        return len(successful_tests) > 0
        
    except Exception as e:
        print(f"❌ Testing error: {str(e)}")
        return False

def analyze_imo_compliance(results, anniversary_date, special_survey_cycle):
    """Analyze results for IMO compliance"""
    compliance = {
        'date_format_correct': False,
        'window_applied': False,
        'anniversary_date_used': False,
        'five_year_cycle_identified': False,
        'annual_survey_types': False,
        'intermediate_survey_logic': False,
        'condition_cert_logic': False
    }
    
    try:
        for result in results:
            cert_type = result.get('cert_type', '').upper()
            new_next_survey = result.get('new_next_survey', '')
            new_next_survey_type = result.get('new_next_survey_type', '')
            reasoning = result.get('reasoning', '').lower()
            
            # Check date format (dd/MM/yyyy)
            import re
            if re.search(r'\d{2}/\d{2}/\d{4}', str(new_next_survey)):
                compliance['date_format_correct'] = True
            
            # Check ±3M window
            if '±3M' in str(new_next_survey) or '±' in str(new_next_survey):
                compliance['window_applied'] = True
            
            # Check anniversary date usage
            if anniversary_date and 'anniversary' in reasoning:
                compliance['anniversary_date_used'] = True
            
            # Check 5-year cycle
            if '5-year' in reasoning or 'cycle' in reasoning:
                compliance['five_year_cycle_identified'] = True
            
            # Check annual survey types
            if 'annual survey' in str(new_next_survey_type).lower():
                compliance['annual_survey_types'] = True
            
            # Check intermediate survey logic
            if 'intermediate' in str(new_next_survey_type).lower():
                compliance['intermediate_survey_logic'] = True
            
            # Check condition certificate logic
            if 'condition' in cert_type and 'condition certificate expiry' in str(new_next_survey_type).lower():
                compliance['condition_cert_logic'] = True
        
    except Exception as e:
        print(f"⚠️ Compliance analysis error: {str(e)}")
    
    return compliance

def main():
    """Main function"""
    print("🎯 NEXT SURVEY CALCULATION TESTING")
    print("Testing POST /api/ships/{ship_id}/update-next-survey")
    print("Authentication: admin1/123456")
    print("=" * 80)
    
    try:
        # Authenticate
        token = authenticate()
        if not token:
            print("❌ Authentication failed - cannot proceed")
            return False
        
        # Test Next Survey calculation
        success = test_next_survey_calculation(token)
        
        if success:
            print("\n✅ NEXT SURVEY CALCULATION TESTING COMPLETED")
        else:
            print("\n❌ NEXT SURVEY CALCULATION TESTING FAILED")
        
        return success
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)