#!/usr/bin/env python3
"""
Google Drive Folder Structure API Testing
FOCUS: Test the Google Drive folder structure API endpoints to verify "Class & Flag Cert" usage

REVIEW REQUEST REQUIREMENTS:
1. Authentication: Login with admin1/123456 credentials
2. Sidebar Structure API: Test GET /api/sidebar-structure endpoint to verify it returns "Class & Flag Cert"
3. Structure Validation: Verify the returned structure has:
   - "Class & Flag Cert" as first category (not "Document Portfolio")
   - Correct subfolders: ["Certificates", "Class Survey Report", "Test Report", "Drawings & Manuals", "Other Documents"]
   - All other categories remain unchanged
4. API Response Format: Verify response includes success, structure, and metadata

EXPECTED RESULTS:
- GET /api/sidebar-structure should return "Class & Flag Cert" in structure
- When ship folders are created, they will use the new naming convention
- This fixes the mismatch between UI sidebar and Google Drive folder names
- Backward compatibility maintained
"""

import requests
import json
import os
import sys
from datetime import datetime
import traceback

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
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://shipdata-hub.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class GoogleDriveFolderStructureTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking for Google Drive folder structure verification
        self.structure_tests = {
            # Authentication and setup
            'authentication_successful': False,
            'user_role_verified': False,
            
            # Sidebar Structure API tests
            'sidebar_structure_endpoint_accessible': False,
            'sidebar_structure_response_valid': False,
            'response_format_correct': False,
            
            # Structure Content Verification
            'class_flag_cert_category_present': False,
            'class_flag_cert_is_first_category': False,
            'class_flag_cert_subfolders_correct': False,
            'document_portfolio_not_present': False,
            
            # Subfolder Verification
            'certificates_subfolder_present': False,
            'class_survey_report_subfolder_present': False,
            'test_report_subfolder_present': False,
            'drawings_manuals_subfolder_present': False,
            'other_documents_subfolder_present': False,
            
            # Other Categories Verification
            'crew_records_category_present': False,
            'ism_records_category_present': False,
            'isps_records_category_present': False,
            'mlc_records_category_present': False,
            'supplies_category_present': False,
            
            # Response Metadata Verification
            'success_field_true': False,
            'structure_field_present': False,
            'metadata_field_present': False,
            'total_categories_correct': False,
            'total_subcategories_correct': False,
            'structure_version_present': False,
            'last_updated_present': False,
            'source_field_correct': False,
        }
        
        # Store test results for analysis
        self.sidebar_structure_response = {}
        self.expected_structure = {
            "Class & Flag Cert": [
                "Certificates",
                "Class Survey Report", 
                "Test Report",
                "Drawings & Manuals",
                "Other Documents"
            ]
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
                
                self.structure_tests['authentication_successful'] = True
                
                # Verify user role
                user_role = self.current_user.get('role')
                if user_role == 'ADMIN':
                    self.structure_tests['user_role_verified'] = True
                    self.log("✅ User role verified as ADMIN")
                else:
                    self.log(f"⚠️ User role is {user_role}, expected ADMIN")
                
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
    
    def test_sidebar_structure_endpoint(self):
        """Test the sidebar structure endpoint accessibility and response"""
        try:
            self.log("📁 Testing sidebar structure endpoint...")
            
            endpoint = f"{BACKEND_URL}/sidebar-structure"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.structure_tests['sidebar_structure_endpoint_accessible'] = True
                self.log("✅ Sidebar structure endpoint is accessible")
                
                try:
                    response_data = response.json()
                    self.sidebar_structure_response = response_data
                    self.structure_tests['sidebar_structure_response_valid'] = True
                    self.log("✅ Response is valid JSON")
                    
                    # Log response structure for analysis
                    self.log(f"   Response keys: {list(response_data.keys())}")
                    
                    return True
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                self.log(f"❌ Sidebar structure endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing sidebar structure endpoint: {str(e)}", "ERROR")
            return False
    
    def verify_response_format(self):
        """Verify the sidebar structure response has the correct format"""
        try:
            self.log("🔍 Verifying response format...")
            
            if not self.sidebar_structure_response:
                self.log("❌ No response data to verify")
                return False
            
            response = self.sidebar_structure_response
            
            # Check for expected top-level keys
            expected_keys = ['success', 'message', 'structure', 'metadata']
            missing_keys = []
            
            for key in expected_keys:
                if key not in response:
                    missing_keys.append(key)
                else:
                    self.log(f"   ✅ Found key: {key}")
            
            if missing_keys:
                self.log(f"   ❌ Missing keys: {missing_keys}")
                return False
            
            self.structure_tests['response_format_correct'] = True
            self.log("✅ Response format is correct")
            
            # Verify success field
            success = response.get('success')
            if success is True:
                self.structure_tests['success_field_true'] = True
                self.log("   ✅ Success field is True")
            else:
                self.log(f"   ❌ Success field is {success}, expected True")
            
            # Verify structure field
            structure = response.get('structure')
            if structure and isinstance(structure, dict):
                self.structure_tests['structure_field_present'] = True
                self.log("   ✅ Structure field is present and is a dictionary")
            else:
                self.log(f"   ❌ Structure field is invalid: {type(structure)}")
            
            # Verify metadata field
            metadata = response.get('metadata')
            if metadata and isinstance(metadata, dict):
                self.structure_tests['metadata_field_present'] = True
                self.log("   ✅ Metadata field is present and is a dictionary")
                
                # Check metadata contents
                expected_metadata_keys = ['total_categories', 'total_subcategories', 'structure_version', 'last_updated', 'source']
                for meta_key in expected_metadata_keys:
                    if meta_key in metadata:
                        self.log(f"      ✅ Found metadata.{meta_key}: {metadata[meta_key]}")
                        
                        if meta_key == 'structure_version':
                            self.structure_tests['structure_version_present'] = True
                        elif meta_key == 'last_updated':
                            self.structure_tests['last_updated_present'] = True
                        elif meta_key == 'source' and metadata[meta_key] == 'homepage_sidebar_current':
                            self.structure_tests['source_field_correct'] = True
                    else:
                        self.log(f"      ❌ Missing metadata.{meta_key}")
            else:
                self.log(f"   ❌ Metadata field is invalid: {type(metadata)}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Error verifying response format: {str(e)}", "ERROR")
            return False
    
    def verify_class_flag_cert_structure(self):
        """Verify that 'Class & Flag Cert' is present and has correct structure"""
        try:
            self.log("🏷️ Verifying 'Class & Flag Cert' structure...")
            
            if not self.sidebar_structure_response:
                self.log("❌ No response data to verify")
                return False
            
            structure = self.sidebar_structure_response.get('structure', {})
            
            # Check if 'Class & Flag Cert' category is present
            if 'Class & Flag Cert' in structure:
                self.structure_tests['class_flag_cert_category_present'] = True
                self.log("✅ 'Class & Flag Cert' category is present")
                
                # Check if it's the first category
                structure_keys = list(structure.keys())
                if structure_keys[0] == 'Class & Flag Cert':
                    self.structure_tests['class_flag_cert_is_first_category'] = True
                    self.log("✅ 'Class & Flag Cert' is the first category")
                else:
                    self.log(f"❌ 'Class & Flag Cert' is not first. First category is: {structure_keys[0]}")
                
                # Verify subfolders
                class_flag_subfolders = structure['Class & Flag Cert']
                expected_subfolders = [
                    "Certificates",
                    "Class Survey Report", 
                    "Test Report",
                    "Drawings & Manuals",
                    "Other Documents"
                ]
                
                self.log(f"   Found subfolders: {class_flag_subfolders}")
                self.log(f"   Expected subfolders: {expected_subfolders}")
                
                if class_flag_subfolders == expected_subfolders:
                    self.structure_tests['class_flag_cert_subfolders_correct'] = True
                    self.log("✅ 'Class & Flag Cert' subfolders are correct")
                    
                    # Check individual subfolders
                    if "Certificates" in class_flag_subfolders:
                        self.structure_tests['certificates_subfolder_present'] = True
                    if "Class Survey Report" in class_flag_subfolders:
                        self.structure_tests['class_survey_report_subfolder_present'] = True
                    if "Test Report" in class_flag_subfolders:
                        self.structure_tests['test_report_subfolder_present'] = True
                    if "Drawings & Manuals" in class_flag_subfolders:
                        self.structure_tests['drawings_manuals_subfolder_present'] = True
                    if "Other Documents" in class_flag_subfolders:
                        self.structure_tests['other_documents_subfolder_present'] = True
                        
                else:
                    self.log("❌ 'Class & Flag Cert' subfolders are incorrect")
                    missing = set(expected_subfolders) - set(class_flag_subfolders)
                    extra = set(class_flag_subfolders) - set(expected_subfolders)
                    if missing:
                        self.log(f"   Missing subfolders: {list(missing)}")
                    if extra:
                        self.log(f"   Extra subfolders: {list(extra)}")
                
            else:
                self.log("❌ 'Class & Flag Cert' category is NOT present")
                self.log(f"   Available categories: {list(structure.keys())}")
            
            # Verify that 'Document Portfolio' is NOT present (old naming)
            if 'Document Portfolio' not in structure:
                self.structure_tests['document_portfolio_not_present'] = True
                self.log("✅ 'Document Portfolio' is NOT present (correct - old naming removed)")
            else:
                self.log("❌ 'Document Portfolio' is still present (should be replaced by 'Class & Flag Cert')")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Error verifying Class & Flag Cert structure: {str(e)}", "ERROR")
            return False
    
    def verify_other_categories(self):
        """Verify that all other categories remain unchanged"""
        try:
            self.log("📂 Verifying other categories remain unchanged...")
            
            if not self.sidebar_structure_response:
                self.log("❌ No response data to verify")
                return False
            
            structure = self.sidebar_structure_response.get('structure', {})
            
            # Expected other categories
            expected_categories = {
                'Crew Records': ['Crew List', 'Crew Certificates', 'Medical Records'],
                'ISM Records': ['ISM Certificate', 'Safety Procedures', 'Audit Reports'],
                'ISPS Records': ['ISPS Certificate', 'Security Plan', 'Security Assessments'],
                'MLC Records': ['MLC Certificate', 'Labor Conditions', 'Accommodation Reports'],
                'Supplies': ['Inventory', 'Purchase Orders', 'Spare Parts']
            }
            
            for category, expected_subfolders in expected_categories.items():
                if category in structure:
                    actual_subfolders = structure[category]
                    self.log(f"   ✅ Found category: {category}")
                    
                    if actual_subfolders == expected_subfolders:
                        self.log(f"      ✅ Subfolders correct: {actual_subfolders}")
                        
                        # Set specific test flags
                        if category == 'Crew Records':
                            self.structure_tests['crew_records_category_present'] = True
                        elif category == 'ISM Records':
                            self.structure_tests['ism_records_category_present'] = True
                        elif category == 'ISPS Records':
                            self.structure_tests['isps_records_category_present'] = True
                        elif category == 'MLC Records':
                            self.structure_tests['mlc_records_category_present'] = True
                        elif category == 'Supplies':
                            self.structure_tests['supplies_category_present'] = True
                            
                    else:
                        self.log(f"      ❌ Subfolders incorrect for {category}")
                        self.log(f"         Expected: {expected_subfolders}")
                        self.log(f"         Actual: {actual_subfolders}")
                else:
                    self.log(f"   ❌ Missing category: {category}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Error verifying other categories: {str(e)}", "ERROR")
            return False
    
    def verify_metadata_accuracy(self):
        """Verify that metadata fields contain accurate information"""
        try:
            self.log("📊 Verifying metadata accuracy...")
            
            if not self.sidebar_structure_response:
                self.log("❌ No response data to verify")
                return False
            
            structure = self.sidebar_structure_response.get('structure', {})
            metadata = self.sidebar_structure_response.get('metadata', {})
            
            # Calculate actual values
            actual_total_categories = len(structure)
            actual_total_subcategories = sum(len(subcats) for subcats in structure.values())
            
            # Verify total_categories
            reported_total_categories = metadata.get('total_categories')
            if reported_total_categories == actual_total_categories:
                self.structure_tests['total_categories_correct'] = True
                self.log(f"   ✅ Total categories correct: {actual_total_categories}")
            else:
                self.log(f"   ❌ Total categories mismatch: reported {reported_total_categories}, actual {actual_total_categories}")
            
            # Verify total_subcategories
            reported_total_subcategories = metadata.get('total_subcategories')
            if reported_total_subcategories == actual_total_subcategories:
                self.structure_tests['total_subcategories_correct'] = True
                self.log(f"   ✅ Total subcategories correct: {actual_total_subcategories}")
            else:
                self.log(f"   ❌ Total subcategories mismatch: reported {reported_total_subcategories}, actual {actual_total_subcategories}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Error verifying metadata accuracy: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_structure_test(self):
        """Run comprehensive test of the Google Drive folder structure API"""
        try:
            self.log("🚀 STARTING COMPREHENSIVE GOOGLE DRIVE FOLDER STRUCTURE TEST")
            self.log("=" * 80)
            
            # Step 1: Authentication
            self.log("STEP 1: Authentication")
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Test sidebar structure endpoint
            self.log("\nSTEP 2: Testing sidebar structure endpoint")
            if not self.test_sidebar_structure_endpoint():
                self.log("❌ CRITICAL: Sidebar structure endpoint failed")
                return False
            
            # Step 3: Verify response format
            self.log("\nSTEP 3: Verifying response format")
            if not self.verify_response_format():
                self.log("❌ CRITICAL: Response format verification failed")
                return False
            
            # Step 4: Verify Class & Flag Cert structure
            self.log("\nSTEP 4: Verifying 'Class & Flag Cert' structure")
            if not self.verify_class_flag_cert_structure():
                self.log("❌ Class & Flag Cert structure verification failed")
                return False
            
            # Step 5: Verify other categories
            self.log("\nSTEP 5: Verifying other categories remain unchanged")
            if not self.verify_other_categories():
                self.log("❌ Other categories verification failed")
                return False
            
            # Step 6: Verify metadata accuracy
            self.log("\nSTEP 6: Verifying metadata accuracy")
            if not self.verify_metadata_accuracy():
                self.log("❌ Metadata accuracy verification failed")
                return False
            
            self.log("\n" + "=" * 80)
            self.log("✅ COMPREHENSIVE GOOGLE DRIVE FOLDER STRUCTURE TEST COMPLETED SUCCESSFULLY")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in comprehensive test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def print_test_summary(self):
        """Print comprehensive summary of test results"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 GOOGLE DRIVE FOLDER STRUCTURE TEST SUMMARY")
            self.log("=" * 80)
            
            # Count passed tests
            total_tests = len(self.structure_tests)
            passed_tests = sum(1 for result in self.structure_tests.values() if result)
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
            self.log("")
            
            # Authentication Results
            self.log("🔐 AUTHENTICATION:")
            auth_tests = [
                ('authentication_successful', 'Login with admin1/123456 successful'),
                ('user_role_verified', 'User role verified as ADMIN'),
            ]
            
            for test_key, description in auth_tests:
                status = "✅ PASS" if self.structure_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # API Endpoint Results
            self.log("\n🌐 API ENDPOINT:")
            api_tests = [
                ('sidebar_structure_endpoint_accessible', 'GET /api/sidebar-structure endpoint accessible'),
                ('sidebar_structure_response_valid', 'Response is valid JSON'),
                ('response_format_correct', 'Response format is correct'),
            ]
            
            for test_key, description in api_tests:
                status = "✅ PASS" if self.structure_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Structure Content Results
            self.log("\n📁 STRUCTURE CONTENT:")
            structure_tests = [
                ('class_flag_cert_category_present', '"Class & Flag Cert" category present'),
                ('class_flag_cert_is_first_category', '"Class & Flag Cert" is first category'),
                ('class_flag_cert_subfolders_correct', '"Class & Flag Cert" subfolders correct'),
                ('document_portfolio_not_present', '"Document Portfolio" not present (old naming removed)'),
            ]
            
            for test_key, description in structure_tests:
                status = "✅ PASS" if self.structure_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Subfolder Verification Results
            self.log("\n📂 SUBFOLDER VERIFICATION:")
            subfolder_tests = [
                ('certificates_subfolder_present', '"Certificates" subfolder present'),
                ('class_survey_report_subfolder_present', '"Class Survey Report" subfolder present'),
                ('test_report_subfolder_present', '"Test Report" subfolder present'),
                ('drawings_manuals_subfolder_present', '"Drawings & Manuals" subfolder present'),
                ('other_documents_subfolder_present', '"Other Documents" subfolder present'),
            ]
            
            for test_key, description in subfolder_tests:
                status = "✅ PASS" if self.structure_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Other Categories Results
            self.log("\n🗂️ OTHER CATEGORIES:")
            category_tests = [
                ('crew_records_category_present', 'Crew Records category unchanged'),
                ('ism_records_category_present', 'ISM Records category unchanged'),
                ('isps_records_category_present', 'ISPS Records category unchanged'),
                ('mlc_records_category_present', 'MLC Records category unchanged'),
                ('supplies_category_present', 'Supplies category unchanged'),
            ]
            
            for test_key, description in category_tests:
                status = "✅ PASS" if self.structure_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Response Format Results
            self.log("\n📋 RESPONSE FORMAT:")
            format_tests = [
                ('success_field_true', 'Success field is true'),
                ('structure_field_present', 'Structure field present'),
                ('metadata_field_present', 'Metadata field present'),
                ('total_categories_correct', 'Total categories count correct'),
                ('total_subcategories_correct', 'Total subcategories count correct'),
                ('structure_version_present', 'Structure version present'),
                ('last_updated_present', 'Last updated timestamp present'),
                ('source_field_correct', 'Source field correct'),
            ]
            
            for test_key, description in format_tests:
                status = "✅ PASS" if self.structure_tests.get(test_key, False) else "❌ FAIL"
                self.log(f"   {status} - {description}")
            
            # Overall Assessment
            self.log("\n🎯 OVERALL ASSESSMENT:")
            
            critical_tests = [
                'class_flag_cert_category_present',
                'class_flag_cert_is_first_category', 
                'class_flag_cert_subfolders_correct',
                'document_portfolio_not_present'
            ]
            
            critical_passed = sum(1 for test_key in critical_tests if self.structure_tests.get(test_key, False))
            
            if critical_passed == len(critical_tests):
                self.log("   ✅ GOOGLE DRIVE FOLDER STRUCTURE UPDATE SUCCESSFUL")
                self.log("   ✅ 'Class & Flag Cert' is now used instead of 'Document Portfolio'")
                self.log("   ✅ Correct subfolders are present")
                self.log("   ✅ Google Apps Script will receive correct structure")
                self.log("   ✅ Mismatch between UI sidebar and Google Drive folder names FIXED")
            else:
                self.log("   ❌ GOOGLE DRIVE FOLDER STRUCTURE UPDATE INCOMPLETE")
                self.log(f"   ❌ Only {critical_passed}/{len(critical_tests)} critical tests passed")
                self.log("   ❌ Further investigation needed")
            
            self.log("=" * 80)
            
        except Exception as e:
            self.log(f"❌ Error printing test summary: {str(e)}", "ERROR")

def main():
    """Main test execution"""
    print("🚀 Starting Google Drive Folder Structure API Testing...")
    
    tester = GoogleDriveFolderStructureTester()
    
    try:
        # Run comprehensive test
        success = tester.run_comprehensive_structure_test()
        
        # Print detailed summary
        tester.print_test_summary()
        
        if success:
            print("\n✅ All tests completed successfully!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Critical error during testing: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)