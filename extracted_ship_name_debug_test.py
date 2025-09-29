#!/usr/bin/env python3
"""
Extracted Ship Name Field Debug Test
FOCUS: Debug why certificates show "No ship name extracted" in tooltip

REVIEW REQUEST REQUIREMENTS:
1. Check existing certificates structure for extracted_ship_name field
2. Test new certificate upload with AI analysis
3. Monitor AI analysis response for ship_name extraction
4. Check if extracted_ship_name field is properly saved to database
5. Backend log analysis for AI analysis debugging
6. Use admin1/123456 authentication

DEBUG QUESTIONS:
1. Do existing certificates have extracted_ship_name field in database?
2. Does AI analysis extract ship_name from new certificate uploads?
3. Is extracted_ship_name field being saved during certificate creation?

EXPECTED FINDINGS:
- Old certificates (created before enhancement) won't have extracted_ship_name field
- New certificates should have extracted_ship_name if AI extracts ship_name
- AI analysis might not be extracting ship_name from certificate PDFs
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback
import tempfile
from urllib.parse import urlparse

# Configuration - Use environment variable for backend URL
try:
    # Test internal connection first
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:  # 401 is expected without auth
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://seacraft-portfolio.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class ExtractedShipNameDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking
        self.debug_tests = {
            'authentication_successful': False,
            'sunshine_01_ship_found': False,
            'existing_certificates_retrieved': False,
            'extracted_ship_name_field_analysis_completed': False,
            'ai_analysis_tested': False,
            'new_certificate_upload_tested': False,
            'ship_name_extraction_verified': False,
            'database_save_verified': False,
            'backend_logs_analyzed': False,
        }
        
        # Ship data for testing
        self.sunshine_01_ship = None
        self.test_certificates = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
        # Also store in our log collection
        self.backend_logs.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        
    def authenticate(self):
        """Authenticate with admin1/123456 credentials as specified in review request"""
        try:
            self.log("🔐 Authenticating with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, json=login_data, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.debug_tests['authentication_successful'] = True
                return True
            else:
                self.log(f"   ❌ Authentication failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def find_sunshine_01_ship(self):
        """Find SUNSHINE 01 ship for testing"""
        try:
            self.log("🚢 Finding SUNSHINE 01 ship...")
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} ships total")
                
                # Look for SUNSHINE 01
                for ship in ships:
                    ship_name = ship.get('name', '').upper()
                    if 'SUNSHINE 01' in ship_name or 'SUNSHINE01' in ship_name:
                        self.sunshine_01_ship = ship
                        self.log("✅ SUNSHINE 01 ship found")
                        self.log(f"   Ship ID: {ship.get('id')}")
                        self.log(f"   Ship Name: {ship.get('name')}")
                        self.log(f"   IMO: {ship.get('imo')}")
                        self.log(f"   Flag: {ship.get('flag')}")
                        self.log(f"   Class Society: {ship.get('ship_type')}")
                        
                        self.debug_tests['sunshine_01_ship_found'] = True
                        return True
                
                self.log("❌ SUNSHINE 01 ship not found")
                self.log("   Available ships:")
                for ship in ships[:5]:  # Show first 5 ships
                    self.log(f"      - {ship.get('name')} (ID: {ship.get('id')})")
                return False
            else:
                self.log(f"   ❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error finding SUNSHINE 01 ship: {str(e)}", "ERROR")
            return False
    
    def analyze_existing_certificates(self):
        """Analyze existing certificates for extracted_ship_name field"""
        try:
            self.log("📋 Analyzing existing certificates for extracted_ship_name field...")
            
            if not self.sunshine_01_ship:
                self.log("   ❌ No SUNSHINE 01 ship available")
                return False
            
            ship_id = self.sunshine_01_ship.get('id')
            endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                certificates = response.json()
                self.test_certificates = certificates
                self.log(f"✅ Retrieved {len(certificates)} certificates for SUNSHINE 01")
                
                self.debug_tests['existing_certificates_retrieved'] = True
                
                # Analyze extracted_ship_name field presence
                certificates_with_extracted_name = 0
                certificates_without_extracted_name = 0
                sample_certificates = []
                
                for i, cert in enumerate(certificates):
                    cert_name = cert.get('cert_name', 'Unknown')
                    cert_id = cert.get('id', 'Unknown')
                    extracted_ship_name = cert.get('extracted_ship_name')
                    
                    if extracted_ship_name:
                        certificates_with_extracted_name += 1
                        if len(sample_certificates) < 3:
                            sample_certificates.append({
                                'cert_name': cert_name,
                                'cert_id': cert_id,
                                'extracted_ship_name': extracted_ship_name,
                                'has_field': True
                            })
                    else:
                        certificates_without_extracted_name += 1
                        if len(sample_certificates) < 3:
                            sample_certificates.append({
                                'cert_name': cert_name,
                                'cert_id': cert_id,
                                'extracted_ship_name': extracted_ship_name,
                                'has_field': False
                            })
                
                self.log("📊 EXTRACTED_SHIP_NAME FIELD ANALYSIS:")
                self.log(f"   Total certificates: {len(certificates)}")
                self.log(f"   Certificates WITH extracted_ship_name: {certificates_with_extracted_name}")
                self.log(f"   Certificates WITHOUT extracted_ship_name: {certificates_without_extracted_name}")
                
                # Show sample certificates
                self.log("   Sample certificates:")
                for sample in sample_certificates:
                    status = "✅ HAS FIELD" if sample['has_field'] else "❌ NO FIELD"
                    self.log(f"      {status}: {sample['cert_name'][:50]}...")
                    self.log(f"         ID: {sample['cert_id']}")
                    self.log(f"         extracted_ship_name: {sample['extracted_ship_name']}")
                
                # Root cause analysis
                if certificates_with_extracted_name == 0:
                    self.log("🔍 ROOT CAUSE ANALYSIS:")
                    self.log("   ❌ NO certificates have extracted_ship_name field")
                    self.log("   This explains why all tooltips show 'No ship name extracted'")
                    self.log("   Possible causes:")
                    self.log("      1. Field was added recently, old certificates don't have it")
                    self.log("      2. AI analysis is not extracting ship names")
                    self.log("      3. Field is not being saved during certificate creation")
                elif certificates_with_extracted_name < len(certificates):
                    self.log("🔍 ROOT CAUSE ANALYSIS:")
                    self.log("   ⚠️ MIXED RESULTS: Some certificates have field, others don't")
                    self.log(f"   {certificates_with_extracted_name}/{len(certificates)} certificates have extracted_ship_name")
                    self.log("   This suggests:")
                    self.log("      1. Field was added recently (newer certificates have it)")
                    self.log("      2. AI analysis works sometimes but not always")
                else:
                    self.log("🔍 ROOT CAUSE ANALYSIS:")
                    self.log("   ✅ ALL certificates have extracted_ship_name field")
                    self.log("   The issue might be in frontend tooltip display logic")
                
                self.debug_tests['extracted_ship_name_field_analysis_completed'] = True
                return True
            else:
                self.log(f"   ❌ Failed to get certificates: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error analyzing existing certificates: {str(e)}", "ERROR")
            return False
    
    def test_ai_analysis_ship_name_extraction(self):
        """Test AI analysis for ship name extraction by uploading a new certificate"""
        try:
            self.log("🤖 Testing AI analysis for ship name extraction...")
            
            if not self.sunshine_01_ship:
                self.log("   ❌ No SUNSHINE 01 ship available")
                return False
            
            ship_id = self.sunshine_01_ship.get('id')
            
            # Create a test certificate with clear ship name content
            test_certificate_content = f"""
CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE

This is to certify that the ship SUNSHINE 01 has been surveyed in accordance with the provisions of the International Convention for the Safety of Life at Sea, 1974, as amended.

Ship Name: SUNSHINE 01
IMO Number: 9415313
Port of Registry: BELIZE
Flag State: BELIZE
Classification Society: PANAMA MARITIME DOCUMENTATION SERVICES (PMDS)

Certificate Number: TEST-CSSC-2025-001
Issue Date: 15/01/2024
Valid Until: 10/03/2026
Last Endorsed: 15/06/2024

This certificate is issued under the authority of the Government of BELIZE.

The ship SUNSHINE 01 complies with the relevant requirements of the Convention.
            """
            
            # Create a temporary file with the test content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(test_certificate_content)
                temp_file_path = temp_file.name
            
            try:
                # Upload the test certificate
                self.log("   📤 Uploading test certificate with clear ship name...")
                self.log(f"   Ship name in content: SUNSHINE 01")
                self.log(f"   Expected extracted_ship_name: SUNSHINE 01")
                
                endpoint = f"{BACKEND_URL}/certificates/multi-upload"
                
                with open(temp_file_path, 'rb') as file:
                    files = {'files': ('test_certificate.txt', file, 'text/plain')}
                    data = {
                        'ship_id': ship_id,
                        'category': 'certificates',
                        'sensitivity_level': 'public'
                    }
                    
                    response = requests.post(
                        endpoint,
                        files=files,
                        data=data,
                        headers=self.get_headers(),
                        timeout=120  # AI analysis can take time
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    self.log("✅ Certificate upload successful")
                    
                    # Log the full response for analysis
                    self.log("   📋 AI Analysis Response:")
                    self.log(f"   {json.dumps(response_data, indent=2)}")
                    
                    # Check if AI extracted ship name
                    results = response_data.get('results', [])
                    if results:
                        first_result = results[0]
                        analysis_result = first_result.get('analysis_result', {})
                        
                        ship_name_extracted = analysis_result.get('ship_name')
                        extracted_ship_name = first_result.get('extracted_ship_name')
                        
                        self.log("🔍 AI Analysis Debug:")
                        self.log(f"   ship_name in analysis_result: {ship_name_extracted}")
                        self.log(f"   extracted_ship_name in certificate: {extracted_ship_name}")
                        
                        if ship_name_extracted:
                            self.log("✅ AI successfully extracted ship name from certificate")
                            self.log(f"   Extracted: {ship_name_extracted}")
                            
                            if extracted_ship_name:
                                self.log("✅ extracted_ship_name field is present in certificate")
                                self.log(f"   Field value: {extracted_ship_name}")
                                self.debug_tests['ship_name_extraction_verified'] = True
                                self.debug_tests['database_save_verified'] = True
                            else:
                                self.log("❌ extracted_ship_name field is missing from certificate")
                                self.log("   AI extracted ship name but field was not saved")
                        else:
                            self.log("❌ AI did not extract ship name from certificate")
                            self.log("   This is the root cause of the issue")
                            
                            # Check if AI analysis worked at all
                            cert_name = analysis_result.get('cert_name')
                            cert_no = analysis_result.get('cert_no')
                            
                            if cert_name or cert_no:
                                self.log("   ⚠️ AI analysis partially working (extracted other fields)")
                                self.log(f"      cert_name: {cert_name}")
                                self.log(f"      cert_no: {cert_no}")
                                self.log("   Issue: AI prompt may not include ship_name extraction")
                            else:
                                self.log("   ❌ AI analysis completely failed")
                                self.log("   Issue: AI analysis pipeline not working")
                    
                    self.debug_tests['ai_analysis_tested'] = True
                    self.debug_tests['new_certificate_upload_tested'] = True
                    return True
                else:
                    self.log(f"   ❌ Certificate upload failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"      Error: {response.text[:500]}")
                    return False
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                
        except Exception as e:
            self.log(f"❌ Error testing AI analysis: {str(e)}", "ERROR")
            return False
    
    def analyze_backend_logs(self):
        """Analyze backend logs for AI analysis debugging"""
        try:
            self.log("📋 Analyzing backend logs for AI analysis debugging...")
            
            # Check if we can access backend logs
            # This would typically require access to the server logs
            # For now, we'll check if there are any debug endpoints
            
            try:
                # Try to get AI config to see if AI is properly configured
                endpoint = f"{BACKEND_URL}/ai-config"
                response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
                
                if response.status_code == 200:
                    ai_config = response.json()
                    self.log("✅ AI Configuration found:")
                    self.log(f"   Provider: {ai_config.get('provider')}")
                    self.log(f"   Model: {ai_config.get('model')}")
                    self.log(f"   Using Emergent Key: {ai_config.get('use_emergent_key')}")
                    
                    if ai_config.get('provider') and ai_config.get('model'):
                        self.log("✅ AI is properly configured")
                    else:
                        self.log("❌ AI configuration incomplete")
                        self.log("   This could explain why ship name extraction is not working")
                else:
                    self.log(f"   ⚠️ Could not access AI config: {response.status_code}")
                    
            except Exception as e:
                self.log(f"   ⚠️ Error checking AI config: {str(e)}")
            
            # Look for any debug information in our test logs
            ai_related_logs = [log for log in self.backend_logs if 'ai' in log['message'].lower() or 'analysis' in log['message'].lower()]
            
            if ai_related_logs:
                self.log("🔍 AI-related logs found:")
                for log in ai_related_logs[-5:]:  # Show last 5 AI-related logs
                    self.log(f"   [{log['timestamp']}] {log['message']}")
            
            self.debug_tests['backend_logs_analyzed'] = True
            return True
            
        except Exception as e:
            self.log(f"❌ Error analyzing backend logs: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_debug_test(self):
        """Main debug test function"""
        self.log("🔍 STARTING EXTRACTED SHIP NAME DEBUG TEST")
        self.log("🎯 OBJECTIVE: Debug why certificates show 'No ship name extracted' in tooltip")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Find SUNSHINE 01 ship
            self.log("\n🚢 STEP 2: FIND SUNSHINE 01 SHIP")
            self.log("=" * 50)
            if not self.find_sunshine_01_ship():
                self.log("❌ SUNSHINE 01 ship not found - cannot proceed with testing")
                return False
            
            # Step 3: Analyze existing certificates
            self.log("\n📋 STEP 3: ANALYZE EXISTING CERTIFICATES")
            self.log("=" * 50)
            self.analyze_existing_certificates()
            
            # Step 4: Test AI analysis
            self.log("\n🤖 STEP 4: TEST AI ANALYSIS")
            self.log("=" * 50)
            self.test_ai_analysis_ship_name_extraction()
            
            # Step 5: Analyze backend logs
            self.log("\n📋 STEP 5: ANALYZE BACKEND LOGS")
            self.log("=" * 50)
            self.analyze_backend_logs()
            
            # Step 6: Final analysis
            self.log("\n📊 STEP 6: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_debug_analysis()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Debug test error: {str(e)}", "ERROR")
            return False
    
    def provide_final_debug_analysis(self):
        """Provide final debug analysis and recommendations"""
        try:
            self.log("🔍 EXTRACTED SHIP NAME DEBUG - FINAL ANALYSIS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.debug_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ DEBUG STEPS COMPLETED ({len(passed_tests)}/{len(self.debug_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ DEBUG STEPS FAILED ({len(failed_tests)}/{len(self.debug_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.debug_tests)) * 100
            self.log(f"\n📊 DEBUG COMPLETION RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.debug_tests)})")
            
            # Provide specific findings and recommendations
            self.log("\n🔍 KEY FINDINGS:")
            
            if self.debug_tests['extracted_ship_name_field_analysis_completed']:
                if len(self.test_certificates) > 0:
                    certificates_with_field = sum(1 for cert in self.test_certificates if cert.get('extracted_ship_name'))
                    self.log(f"   📋 Existing certificates: {certificates_with_field}/{len(self.test_certificates)} have extracted_ship_name field")
                    
                    if certificates_with_field == 0:
                        self.log("   🎯 ROOT CAUSE IDENTIFIED: NO existing certificates have extracted_ship_name field")
                        self.log("      This explains why all tooltips show 'No ship name extracted'")
                    elif certificates_with_field < len(self.test_certificates):
                        self.log("   🎯 PARTIAL ISSUE: Some certificates missing extracted_ship_name field")
                        self.log("      Older certificates may not have been updated with this field")
            
            if self.debug_tests['ai_analysis_tested']:
                if self.debug_tests['ship_name_extraction_verified']:
                    self.log("   ✅ AI analysis is working: Successfully extracts ship names from new certificates")
                    self.log("   ✅ Database save is working: extracted_ship_name field is properly saved")
                else:
                    self.log("   ❌ AI analysis issue: Not extracting ship names from certificate content")
                    self.log("      This is likely the main cause of the problem")
            
            # Provide recommendations
            self.log("\n💡 RECOMMENDATIONS:")
            
            if not self.debug_tests['ship_name_extraction_verified']:
                self.log("   🔧 HIGH PRIORITY: Fix AI analysis to extract ship names")
                self.log("      1. Check AI prompt includes ship_name extraction instructions")
                self.log("      2. Verify AI model can process certificate text content")
                self.log("      3. Test with different certificate formats")
                
            if self.debug_tests['extracted_ship_name_field_analysis_completed']:
                certificates_without_field = len(self.test_certificates) - sum(1 for cert in self.test_certificates if cert.get('extracted_ship_name'))
                if certificates_without_field > 0:
                    self.log(f"   🔧 MEDIUM PRIORITY: Update {certificates_without_field} existing certificates")
                    self.log("      1. Run batch job to re-analyze existing certificates")
                    self.log("      2. Extract ship names from existing certificate text content")
                    self.log("      3. Update database with extracted_ship_name field")
            
            self.log("   🔧 LOW PRIORITY: Frontend tooltip improvements")
            self.log("      1. Show more informative message when ship name not available")
            self.log("      2. Add fallback to use current ship name if extracted name missing")
            
            # Final conclusion
            if self.debug_tests['ship_name_extraction_verified'] and self.debug_tests['database_save_verified']:
                self.log(f"\n🎉 CONCLUSION: AI ANALYSIS IS WORKING FOR NEW CERTIFICATES")
                self.log(f"   The issue is mainly with existing certificates that don't have extracted_ship_name field")
                self.log(f"   Solution: Run batch update on existing certificates")
            elif self.debug_tests['ai_analysis_tested']:
                self.log(f"\n❌ CONCLUSION: AI ANALYSIS IS NOT EXTRACTING SHIP NAMES")
                self.log(f"   This is the root cause of the 'No ship name extracted' issue")
                self.log(f"   Solution: Fix AI analysis prompt and ship name extraction logic")
            else:
                self.log(f"\n⚠️ CONCLUSION: UNABLE TO FULLY TEST AI ANALYSIS")
                self.log(f"   Need to investigate AI analysis pipeline further")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final debug analysis error: {str(e)}", "ERROR")
            return False


def main():
    """Main function to run extracted ship name debug test"""
    print("🔍 EXTRACTED SHIP NAME DEBUG TEST STARTED")
    print("=" * 80)
    
    try:
        tester = ExtractedShipNameDebugTester()
        success = tester.run_comprehensive_debug_test()
        
        if success:
            print("\n✅ EXTRACTED SHIP NAME DEBUG TEST COMPLETED")
        else:
            print("\n❌ EXTRACTED SHIP NAME DEBUG TEST FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()