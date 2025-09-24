#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
Focus: Test improved Marine Certificate classification with PMDS certificate
Review Request: Test certificate analysis endpoint with PMDS certificate and verify classification improvements
"""

import requests
import json
import os
import sys
from datetime import datetime
import time

# Configuration - Use external URL for testing
BACKEND_URL = "https://shipai-system.preview.emergentagent.com/api"

class CertificateClassificationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        self.pmds_certificate_url = "https://customer-assets.emergentagent.com/job_shipai-system/artifacts/m1vpd5z1_SUNSHINE%2001%20-%20CICA-%20PM251277.pdf"
        self.classification_improvements_tested = {
            'conditional_certificate_type': False,
            'pmds_document_classification': False,
            'enhanced_detection_rules': False,
            'certificate_information_extraction': False,
            'on_behalf_of_detection': False
        }
        
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
            
            response = requests.post(endpoint, json=login_data, timeout=10)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                self.log(f"   Full Name: {self.current_user.get('full_name')}")
                
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
    
    def download_pmds_certificate(self):
        """Download the PMDS certificate for testing"""
        try:
            self.log("📥 Downloading PMDS certificate for testing...")
            self.log(f"   URL: {self.pmds_certificate_url}")
            
            response = requests.get(self.pmds_certificate_url, timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                # Save the file temporarily
                temp_file_path = "/tmp/pmds_certificate.pdf"
                with open(temp_file_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = len(response.content)
                self.log(f"   ✅ Certificate downloaded successfully")
                self.log(f"   File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                self.log(f"   Saved to: {temp_file_path}")
                
                self.test_results['pmds_certificate_path'] = temp_file_path
                self.test_results['pmds_certificate_size'] = file_size
                return True
            else:
                self.log(f"   ❌ Failed to download certificate: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Certificate download error: {str(e)}", "ERROR")
            return False
    
    def get_available_ships(self):
        """Get available ships for testing"""
        try:
            self.log("🚢 Getting available ships for certificate testing...")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   ✅ Found {len(ships)} ships")
                
                # Look for SUNSHINE ships specifically
                sunshine_ships = [ship for ship in ships if 'SUNSHINE' in ship.get('name', '').upper()]
                if sunshine_ships:
                    selected_ship = sunshine_ships[0]
                    self.log(f"   ✅ Selected SUNSHINE ship: {selected_ship.get('name')} (ID: {selected_ship.get('id')})")
                    self.test_results['selected_ship'] = selected_ship
                    return selected_ship
                elif ships:
                    selected_ship = ships[0]
                    self.log(f"   ✅ Selected first available ship: {selected_ship.get('name')} (ID: {selected_ship.get('id')})")
                    self.test_results['selected_ship'] = selected_ship
                    return selected_ship
                else:
                    self.log("   ❌ No ships available for testing")
                    return None
            else:
                self.log(f"   ❌ Failed to get ships: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Get ships error: {str(e)}", "ERROR")
            return None
    
    def test_certificate_analysis_endpoint(self, ship_id):
        """Test the certificate analysis endpoint with PMDS certificate"""
        try:
            self.log("🔍 Testing certificate classification endpoint with PMDS certificate...")
            
            cert_file_path = self.test_results.get('pmds_certificate_path')
            if not cert_file_path or not os.path.exists(cert_file_path):
                self.log("   ❌ PMDS certificate file not available")
                return False
            
            # Test the certificates/multi-upload endpoint which does classification
            endpoint = f"{BACKEND_URL}/certificates/multi-upload"
            self.log(f"   POST {endpoint}")
            
            # Prepare multipart form data
            with open(cert_file_path, 'rb') as f:
                files = {'files': ('pmds_certificate.pdf', f, 'application/pdf')}
                data = {'ship_id': ship_id}
                
                self.log("   📤 Uploading PMDS certificate for classification analysis...")
                start_time = time.time()
                
                response = requests.post(
                    endpoint, 
                    files=files, 
                    data=data,
                    headers=self.get_headers(), 
                    timeout=120
                )
                
                end_time = time.time()
                
            self.log(f"   Response status: {response.status_code}")
            self.log(f"   Analysis time: {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                analysis_result = response.json()
                self.log("   ✅ Certificate classification completed successfully")
                self.log(f"   Classification result: {json.dumps(analysis_result, indent=6)}")
                
                self.test_results['analysis_result'] = analysis_result
                
                # Extract the actual analysis from the first result
                results = analysis_result.get('results', [])
                if results:
                    first_result = results[0]
                    actual_analysis = first_result.get('analysis', {})
                    self.test_results['certificate_analysis'] = actual_analysis
                    
                    # Verify the classification improvements
                    self.verify_classification_improvements(first_result, actual_analysis)
                else:
                    self.log("   ⚠️ No results found in classification response")
                
                return True
            else:
                self.log(f"   ❌ Certificate classification failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Certificate classification error: {str(e)}", "ERROR")
            return False
    
    def verify_classification_improvements(self, result_item, analysis_result):
        """Verify the 3 main classification improvements"""
        try:
            self.log("🔍 Verifying classification improvements...")
            
            # 1. Check if certificate is classified as "certificates" category (not rejected)
            status = result_item.get('status', '')
            is_marine = result_item.get('is_marine', False)
            category = analysis_result.get('category', '').lower()
            
            if status == 'success' and is_marine and category == 'certificates':
                self.log("   ✅ IMPROVEMENT 1: Certificate correctly classified as 'certificates' category")
                self.classification_improvements_tested['pmds_document_classification'] = True
                self.classification_improvements_tested['enhanced_detection_rules'] = True
            elif status == 'skipped' and not is_marine:
                self.log(f"   ❌ IMPROVEMENT 1: Certificate was rejected as non-marine (status: {status}, category: {category})")
            else:
                self.log(f"   ⚠️ IMPROVEMENT 1: Unclear classification result (status: {status}, is_marine: {is_marine}, category: {category})")
            
            # 2. Check for PMDS detection in issued_by or other fields
            issued_by = analysis_result.get('issued_by', '').upper()
            cert_name = analysis_result.get('cert_name', '').upper()
            
            if 'PMDS' in issued_by or 'PANAMA MARITIME DOCUMENTATION' in issued_by:
                self.log("   ✅ IMPROVEMENT 2: PMDS organization properly detected in issued_by field")
                self.classification_improvements_tested['pmds_document_classification'] = True
            else:
                self.log(f"   ⚠️ IMPROVEMENT 2: PMDS not explicitly detected in issued_by: '{issued_by}'")
            
            # 3. Check for "on behalf of" detection
            if 'ON BEHALF' in issued_by or 'BEHALF' in issued_by:
                self.log("   ✅ IMPROVEMENT 3: 'On behalf of' detection working")
                self.classification_improvements_tested['on_behalf_of_detection'] = True
            else:
                self.log(f"   ℹ️ IMPROVEMENT 3: 'On behalf of' not detected in issued_by field")
            
            # 4. Check certificate information extraction
            extracted_fields = {
                'cert_name': analysis_result.get('cert_name'),
                'cert_no': analysis_result.get('cert_no'),
                'issue_date': analysis_result.get('issue_date'),
                'valid_date': analysis_result.get('valid_date'),
                'issued_by': analysis_result.get('issued_by'),
                'ship_name': analysis_result.get('ship_name')
            }
            
            extracted_count = sum(1 for v in extracted_fields.values() if v and str(v).strip() and str(v).strip().lower() != 'null')
            total_fields = len(extracted_fields)
            
            self.log(f"   📊 Certificate information extraction: {extracted_count}/{total_fields} fields extracted")
            
            for field, value in extracted_fields.items():
                if value and str(value).strip() and str(value).strip().lower() != 'null':
                    self.log(f"      ✅ {field}: {value}")
                else:
                    self.log(f"      ❌ {field}: Not extracted")
            
            if extracted_count >= 3:  # At least 3 fields extracted
                self.log("   ✅ IMPROVEMENT 4: Certificate information extraction working well")
                self.classification_improvements_tested['certificate_information_extraction'] = True
            else:
                self.log("   ❌ IMPROVEMENT 4: Certificate information extraction needs improvement")
            
            # 5. Check enhanced detection rules (successful classification as marine certificate)
            if status == 'success' and is_marine:
                self.log("   ✅ IMPROVEMENT 5: Enhanced detection rules prevent misclassification")
                self.classification_improvements_tested['enhanced_detection_rules'] = True
            else:
                self.log("   ❌ IMPROVEMENT 5: Certificate may have been misclassified or rejected")
                
        except Exception as e:
            self.log(f"❌ Classification verification error: {str(e)}", "ERROR")
    
    def test_conditional_certificate_type(self):
        """Test if 'Conditional' certificate type is available"""
        try:
            self.log("🔍 Testing if 'Conditional' certificate type is available...")
            
            # This would typically be tested through the frontend, but we can check
            # if the backend accepts 'Conditional' as a cert_type
            ship = self.test_results.get('selected_ship')
            if not ship:
                self.log("   ❌ No ship available for conditional certificate test")
                return False
            
            # Try to create a test certificate with 'Conditional' type
            test_cert_data = {
                "ship_id": ship.get('id'),
                "cert_name": "Test Conditional Certificate",
                "cert_type": "Conditional",
                "cert_no": "TEST_COND_001",
                "issue_date": "2024-01-01T00:00:00Z",
                "valid_date": "2025-01-01T00:00:00Z",
                "issued_by": "Test Authority",
                "category": "certificates"
            }
            
            endpoint = f"{BACKEND_URL}/certificates"
            self.log(f"   POST {endpoint}")
            self.log("   Testing 'Conditional' certificate type acceptance...")
            
            response = requests.post(
                endpoint, 
                json=test_cert_data,
                headers=self.get_headers(), 
                timeout=30
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                cert_response = response.json()
                cert_type = cert_response.get('cert_type')
                
                if cert_type == 'Conditional':
                    self.log("   ✅ IMPROVEMENT: 'Conditional' certificate type is accepted and working")
                    self.classification_improvements_tested['conditional_certificate_type'] = True
                    
                    # Clean up - delete the test certificate
                    cert_id = cert_response.get('id')
                    if cert_id:
                        delete_endpoint = f"{BACKEND_URL}/certificates/{cert_id}"
                        requests.delete(delete_endpoint, headers=self.get_headers(), timeout=30)
                        self.log("   🗑️ Test certificate cleaned up")
                    
                    return True
                else:
                    self.log(f"   ⚠️ Certificate created but type returned as '{cert_type}' instead of 'Conditional'")
            else:
                self.log(f"   ❌ Failed to create conditional certificate: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
            
            return False
                
        except Exception as e:
            self.log(f"❌ Conditional certificate type test error: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_certificate_classification_test(self):
        """Main test function for certificate classification improvements"""
        self.log("🎯 STARTING CERTIFICATE CLASSIFICATION TESTING SESSION")
        self.log("🔍 Focus: Test improved Marine Certificate classification with PMDS certificate")
        self.log("📋 Review Request: Verify 3 classification improvements")
        self.log("=" * 100)
        
        # Step 1: Authenticate
        self.log("\n🔐 STEP 1: AUTHENTICATION")
        self.log("=" * 50)
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        # Step 2: Download PMDS certificate
        self.log("\n📥 STEP 2: DOWNLOAD PMDS CERTIFICATE")
        self.log("=" * 50)
        if not self.download_pmds_certificate():
            self.log("❌ Certificate download failed - cannot proceed with testing")
            return False
        
        # Step 3: Get available ships
        self.log("\n🚢 STEP 3: GET AVAILABLE SHIPS")
        self.log("=" * 50)
        ship = self.get_available_ships()
        if not ship:
            self.log("❌ No ships available - cannot proceed with certificate testing")
            return False
        
        # Step 4: Test certificate analysis endpoint
        self.log("\n🔍 STEP 4: CERTIFICATE ANALYSIS TESTING")
        self.log("=" * 50)
        analysis_success = self.test_certificate_analysis_endpoint(ship.get('id'))
        
        # Step 5: Test conditional certificate type
        self.log("\n📝 STEP 5: CONDITIONAL CERTIFICATE TYPE TESTING")
        self.log("=" * 50)
        self.test_conditional_certificate_type()
        
        # Step 6: Final analysis
        self.log("\n📊 STEP 6: FINAL ANALYSIS")
        self.log("=" * 50)
        self.provide_final_analysis()
        
        return analysis_success
    
    def provide_final_analysis(self):
        """Provide final analysis of the certificate classification testing"""
        try:
            self.log("🎯 CERTIFICATE CLASSIFICATION IMPROVEMENTS - TESTING RESULTS")
            self.log("=" * 70)
            
            # Check which improvements were detected
            detected_improvements = []
            missing_improvements = []
            
            for improvement, detected in self.classification_improvements_tested.items():
                if detected:
                    detected_improvements.append(improvement)
                else:
                    missing_improvements.append(improvement)
            
            self.log(f"✅ CLASSIFICATION IMPROVEMENTS WORKING ({len(detected_improvements)}/5):")
            for improvement in detected_improvements:
                self.log(f"   ✅ {improvement.replace('_', ' ').title()}")
            
            if missing_improvements:
                self.log(f"\n❌ CLASSIFICATION IMPROVEMENTS NOT DETECTED ({len(missing_improvements)}/5):")
                for improvement in missing_improvements:
                    self.log(f"   ❌ {improvement.replace('_', ' ').title()}")
            
            # Overall assessment
            success_rate = len(detected_improvements) / len(self.classification_improvements_tested) * 100
            self.log(f"\n📊 CLASSIFICATION IMPROVEMENTS SUCCESS RATE: {success_rate:.1f}%")
            
            if success_rate >= 80:
                self.log("🎉 EXCELLENT: Most classification improvements are working correctly")
            elif success_rate >= 60:
                self.log("✅ GOOD: Majority of classification improvements are working")
            elif success_rate >= 40:
                self.log("⚠️ MODERATE: Some classification improvements are working")
            else:
                self.log("❌ POOR: Few classification improvements detected")
            
            # Analysis results
            if self.test_results.get('analysis_result'):
                self.log("\n🔍 CERTIFICATE ANALYSIS RESULTS:")
                analysis = self.test_results['analysis_result']
                
                self.log(f"   Category: {analysis.get('category', 'Not classified')}")
                self.log(f"   Certificate Name: {analysis.get('cert_name', 'Not extracted')}")
                self.log(f"   Certificate Number: {analysis.get('cert_no', 'Not extracted')}")
                self.log(f"   Issue Date: {analysis.get('issue_date', 'Not extracted')}")
                self.log(f"   Valid Date: {analysis.get('valid_date', 'Not extracted')}")
                self.log(f"   Issued By: {analysis.get('issued_by', 'Not extracted')}")
                self.log(f"   Ship Name: {analysis.get('ship_name', 'Not extracted')}")
                
                # Check for specific PMDS indicators
                issued_by = analysis.get('issued_by', '').upper()
                if 'PMDS' in issued_by or 'PANAMA MARITIME DOCUMENTATION' in issued_by:
                    self.log("   ✅ PMDS organization detected in analysis")
                else:
                    self.log("   ⚠️ PMDS organization not explicitly detected")
                
                if 'BEHALF' in issued_by:
                    self.log("   ✅ 'On behalf of' pattern detected")
                else:
                    self.log("   ℹ️ 'On behalf of' pattern not detected")
            else:
                self.log("\n🔍 CERTIFICATE ANALYSIS RESULTS:")
                self.log("   ❌ No analysis results available")
            
            # Ship information
            if self.test_results.get('selected_ship'):
                ship = self.test_results['selected_ship']
                self.log(f"\n🚢 TESTED WITH SHIP:")
                self.log(f"   Ship Name: {ship.get('name')}")
                self.log(f"   Ship ID: {ship.get('id')}")
                self.log(f"   Company: {ship.get('company')}")
            
            # Certificate file information
            if self.test_results.get('pmds_certificate_size'):
                size_mb = self.test_results['pmds_certificate_size'] / 1024 / 1024
                self.log(f"\n📄 PMDS CERTIFICATE FILE:")
                self.log(f"   File Size: {size_mb:.2f} MB")
                self.log(f"   Source: {self.pmds_certificate_url}")
                
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    print("🎯 Ship Management System - Certificate Classification Testing")
    print("🔍 Focus: Test improved Marine Certificate classification with PMDS certificate")
    print("📋 Review Request: Verify 3 classification improvements")
    print("=" * 100)
    
    tester = CertificateClassificationTester()
    success = tester.run_comprehensive_certificate_classification_test()
    
    print("=" * 100)
    print("🔍 CERTIFICATE CLASSIFICATION TESTING RESULTS:")
    print("=" * 60)
    
    # Print classification improvements summary
    detected_improvements = [f for f, detected in tester.classification_improvements_tested.items() if detected]
    missing_improvements = [f for f, detected in tester.classification_improvements_tested.items() if not detected]
    
    print(f"✅ CLASSIFICATION IMPROVEMENTS WORKING ({len(detected_improvements)}/5):")
    for improvement in detected_improvements:
        print(f"   ✅ {improvement.replace('_', ' ').title()}")
    
    if missing_improvements:
        print(f"\n❌ CLASSIFICATION IMPROVEMENTS NOT DETECTED ({len(missing_improvements)}/5):")
        for improvement in missing_improvements:
            print(f"   ❌ {improvement.replace('_', ' ').title()}")
    
    # Print analysis results
    if tester.test_results.get('analysis_result'):
        print(f"\n🔍 CERTIFICATE ANALYSIS: ✅ SUCCESS")
        analysis = tester.test_results['analysis_result']
        print(f"   Category: {analysis.get('category', 'Not classified')}")
        print(f"   Certificate Name: {analysis.get('cert_name', 'Not extracted')}")
        print(f"   Certificate Number: {analysis.get('cert_no', 'Not extracted')}")
        print(f"   Issued By: {analysis.get('issued_by', 'Not extracted')}")
    else:
        print(f"\n🔍 CERTIFICATE ANALYSIS: ❌ FAILED")
    
    # Print ship information
    if tester.test_results.get('selected_ship'):
        ship = tester.test_results['selected_ship']
        print(f"\n🚢 TESTED WITH SHIP: {ship.get('name')} (ID: {ship.get('id')})")
    
    # Calculate success rate
    success_rate = len(detected_improvements) / len(tester.classification_improvements_tested) * 100
    print(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")
    
    print("=" * 100)
    if success:
        print("🎉 Certificate classification testing completed successfully!")
        print("✅ All testing steps executed - detailed analysis available above")
    else:
        print("❌ Certificate classification testing completed with issues!")
        print("🔍 Check detailed logs above for specific issues")
    
    if len(detected_improvements) >= 3:
        print("\n💡 NEXT STEPS FOR MAIN AGENT:")
        print("   ✅ Classification improvements are working well")
        print("   1. Review the specific improvements detected above")
        print("   2. Consider the testing successful for detected improvements")
        print("   3. Investigate any missing improvements if needed")
    else:
        print("\n💡 NEXT STEPS FOR MAIN AGENT:")
        print("   ⚠️ Few classification improvements detected")
        print("   1. Review backend implementation for classification improvements")
        print("   2. Check if PMDS detection is properly implemented")
        print("   3. Verify 'Conditional' certificate type support")
        print("   4. Test enhanced detection rules manually")
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()