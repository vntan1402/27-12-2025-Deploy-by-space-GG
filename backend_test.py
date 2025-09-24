#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
Focus: Testing Updated Sidebar Structure Endpoint
"""

import requests
import json
import os
import sys
from datetime import datetime
import tempfile
import subprocess
import time
import base64

# Configuration - Use production URL from frontend .env
BACKEND_URL = "https://shipment-ai-1.preview.emergentagent.com/api"

class SidebarStructureTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_credentials = [
            {"username": "admin1", "password": "123456", "description": "Primary admin account"},
            {"username": "admin", "password": "admin123", "description": "Demo admin account"}
        ]
        self.auth_token = None
        self.test_results = {}
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def authenticate(self):
        """Authenticate with the backend to get access token"""
        try:
            self.log("🔐 Authenticating with backend...")
            
            for cred in self.test_credentials:
                username = cred["username"]
                password = cred["password"]
                
                login_data = {
                    "username": username,
                    "password": password,
                    "remember_me": False
                }
                
                endpoint = f"{BACKEND_URL}/auth/login"
                self.log(f"   Attempting login to: {endpoint}")
                response = requests.post(endpoint, json=login_data, timeout=60)
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    user_data = data.get("user", {})
                    
                    self.log(f"✅ Authentication successful with {username}")
                    self.log(f"   User Role: {user_data.get('role')}")
                    self.log(f"   Company: {user_data.get('company')}")
                    return True
                else:
                    self.log(f"❌ Authentication failed with {username} - Status: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"   Error: {response.text[:200]}")
                    
            self.log("❌ Authentication failed with all credentials")
            return False
            
        except requests.exceptions.RequestException as req_error:
            self.log(f"❌ Network error during authentication: {str(req_error)}", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def test_sidebar_structure_endpoint(self):
        """Main test function for sidebar structure endpoint"""
        self.log("📋 Starting Sidebar Structure Endpoint Testing")
        self.log("🎯 Focus: Testing updated /api/sidebar-structure endpoint")
        self.log("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            return False
        
        # Step 2: Test Sidebar Structure API
        api_result = self.test_sidebar_structure_api()
        
        # Step 3: Verify Structure Content
        content_result = self.verify_structure_content()
        
        # Step 4: Test Structure Format
        format_result = self.test_structure_format()
        
        # Step 5: Verify Specific Changes
        changes_result = self.verify_specific_changes()
        
        # Step 6: Test Authentication Requirements
        auth_result = self.test_authentication_requirements()
        
        # Step 7: Summary
        self.log("=" * 80)
        self.log("📋 SIDEBAR STRUCTURE ENDPOINT TESTING SUMMARY")
        self.log("=" * 80)
        
        self.log(f"{'✅' if api_result else '❌'} Sidebar Structure API: {'SUCCESS' if api_result else 'FAILED'}")
        self.log(f"{'✅' if content_result else '❌'} Structure Content Verification: {'SUCCESS' if content_result else 'FAILED'}")
        self.log(f"{'✅' if format_result else '❌'} Structure Format Testing: {'SUCCESS' if format_result else 'FAILED'}")
        self.log(f"{'✅' if changes_result else '❌'} Specific Changes Verification: {'SUCCESS' if changes_result else 'FAILED'}")
        self.log(f"{'✅' if auth_result else '❌'} Authentication Requirements: {'SUCCESS' if auth_result else 'FAILED'}")
        
        overall_success = all([api_result, content_result, format_result, changes_result, auth_result])
        
        if overall_success:
            self.log("🎉 SIDEBAR STRUCTURE ENDPOINT TESTING: COMPLETED SUCCESSFULLY")
        else:
            self.log("❌ SIDEBAR STRUCTURE ENDPOINT TESTING: ISSUES DETECTED")
            self.log("🔍 Check detailed logs above for specific issues")
        
        return overall_success
    
    def test_sidebar_structure_api(self):
        """Test GET /api/sidebar-structure endpoint"""
        try:
            self.log("📋 Step 1: Testing Sidebar Structure API...")
            
            endpoint = f"{BACKEND_URL}/sidebar-structure"
            self.log(f"   Testing endpoint: {endpoint}")
            
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   GET /api/sidebar-structure - Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.log("   ✅ API endpoint accessible and returns JSON")
                    
                    # Store response for further analysis
                    self.test_results['sidebar_response'] = data
                    
                    # Basic structure validation
                    if 'success' in data and data['success']:
                        self.log("   ✅ Response indicates success")
                    else:
                        self.log("   ❌ Response does not indicate success")
                        return False
                    
                    if 'structure' in data:
                        self.log("   ✅ Response contains 'structure' field")
                        structure = data['structure']
                        self.log(f"   📊 Structure contains {len(structure)} main categories")
                    else:
                        self.log("   ❌ Response missing 'structure' field")
                        return False
                    
                    if 'metadata' in data:
                        self.log("   ✅ Response contains 'metadata' field")
                        metadata = data['metadata']
                        self.log(f"   📈 Metadata: {json.dumps(metadata, indent=2)}")
                    else:
                        self.log("   ❌ Response missing 'metadata' field")
                        return False
                    
                    return True
                    
                except json.JSONDecodeError:
                    self.log("   ❌ Response is not valid JSON")
                    self.log(f"   Raw response: {response.text[:500]}")
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                except:
                    error_detail = response.text[:200]
                
                self.log(f"   ❌ API endpoint failed - HTTP {response.status_code}")
                self.log(f"      Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log(f"❌ Sidebar structure API testing error: {str(e)}", "ERROR")
            return False
    
    def verify_structure_content(self):
        """Verify the structure content matches expected categories"""
        try:
            self.log("📁 Step 2: Verifying Structure Content...")
            
            sidebar_response = self.test_results.get('sidebar_response')
            if not sidebar_response:
                self.log("   ❌ No sidebar response available for content verification")
                return False
            
            structure = sidebar_response.get('structure', {})
            
            # Expected structure based on review request
            expected_structure = {
                "Document Portfolio": ["Certificates", "Class Survey Report", "Test Report", "Drawings & Manuals", "Other Documents"],
                "Crew Records": ["Crew List", "Crew Certificates", "Medical Records"],
                "ISM Records": ["ISM Certificate", "Safety Procedures", "Audit Reports"],
                "ISPS Records": ["ISPS Certificate", "Security Plan", "Security Assessments"],
                "MLC Records": ["MLC Certificate", "Labor Conditions", "Accommodation Reports"],
                "Supplies": ["Inventory", "Purchase Orders", "Spare Parts"]
            }
            
            self.log("   🔍 Verifying expected categories and subcategories...")
            
            # Check main categories
            missing_categories = []
            extra_categories = []
            
            for expected_cat in expected_structure.keys():
                if expected_cat not in structure:
                    missing_categories.append(expected_cat)
                else:
                    self.log(f"   ✅ Category '{expected_cat}' found")
            
            for actual_cat in structure.keys():
                if actual_cat not in expected_structure:
                    extra_categories.append(actual_cat)
            
            if missing_categories:
                self.log(f"   ❌ Missing categories: {missing_categories}")
                return False
            
            if extra_categories:
                self.log(f"   ⚠️ Extra categories found: {extra_categories}")
            
            # Check subcategories for each main category
            subcategory_issues = []
            
            for category, expected_subcats in expected_structure.items():
                if category in structure:
                    actual_subcats = structure[category]
                    
                    self.log(f"   🔍 Checking subcategories for '{category}':")
                    self.log(f"      Expected: {expected_subcats}")
                    self.log(f"      Actual: {actual_subcats}")
                    
                    # Check if all expected subcategories are present
                    missing_subcats = [sub for sub in expected_subcats if sub not in actual_subcats]
                    extra_subcats = [sub for sub in actual_subcats if sub not in expected_subcats]
                    
                    if missing_subcats:
                        self.log(f"      ❌ Missing subcategories: {missing_subcats}")
                        subcategory_issues.append(f"{category}: missing {missing_subcats}")
                    
                    if extra_subcats:
                        self.log(f"      ⚠️ Extra subcategories: {extra_subcats}")
                    
                    if not missing_subcats and not extra_subcats:
                        self.log(f"      ✅ All subcategories match for '{category}'")
            
            if subcategory_issues:
                self.log(f"   ❌ Subcategory issues found: {subcategory_issues}")
                return False
            
            self.log("   ✅ All structure content verification passed")
            return True
                
        except Exception as e:
            self.log(f"❌ Structure content verification error: {str(e)}", "ERROR")
            return False
    
    def test_structure_format(self):
        """Test the JSON response format"""
        try:
            self.log("📋 Step 3: Testing Structure Format...")
            
            sidebar_response = self.test_results.get('sidebar_response')
            if not sidebar_response:
                self.log("   ❌ No sidebar response available for format testing")
                return False
            
            # Check required top-level fields
            required_fields = ['success', 'structure', 'metadata']
            
            for field in required_fields:
                if field in sidebar_response:
                    self.log(f"   ✅ Required field '{field}' present")
                else:
                    self.log(f"   ❌ Required field '{field}' missing")
                    return False
            
            # Check success flag
            success_flag = sidebar_response.get('success')
            if success_flag is True:
                self.log("   ✅ Success flag is boolean True")
            else:
                self.log(f"   ❌ Success flag is not boolean True: {success_flag}")
                return False
            
            # Check structure format
            structure = sidebar_response.get('structure')
            if isinstance(structure, dict):
                self.log("   ✅ Structure is a dictionary")
                
                # Check that each category has a list of subcategories
                for category, subcategories in structure.items():
                    if isinstance(subcategories, list):
                        self.log(f"   ✅ Category '{category}' has list of subcategories ({len(subcategories)} items)")
                    else:
                        self.log(f"   ❌ Category '{category}' does not have list of subcategories")
                        return False
            else:
                self.log(f"   ❌ Structure is not a dictionary: {type(structure)}")
                return False
            
            # Check metadata format
            metadata = sidebar_response.get('metadata')
            if isinstance(metadata, dict):
                self.log("   ✅ Metadata is a dictionary")
                
                # Check expected metadata fields
                expected_metadata_fields = ['total_categories', 'total_subcategories', 'structure_version']
                
                for field in expected_metadata_fields:
                    if field in metadata:
                        value = metadata[field]
                        self.log(f"   ✅ Metadata field '{field}': {value}")
                    else:
                        self.log(f"   ❌ Metadata field '{field}' missing")
                        return False
                
                # Verify counts
                actual_categories = len(structure)
                actual_subcategories = sum(len(subcats) for subcats in structure.values())
                
                if metadata.get('total_categories') == actual_categories:
                    self.log(f"   ✅ Total categories count correct: {actual_categories}")
                else:
                    self.log(f"   ❌ Total categories count mismatch: expected {actual_categories}, got {metadata.get('total_categories')}")
                    return False
                
                if metadata.get('total_subcategories') == actual_subcategories:
                    self.log(f"   ✅ Total subcategories count correct: {actual_subcategories}")
                else:
                    self.log(f"   ❌ Total subcategories count mismatch: expected {actual_subcategories}, got {metadata.get('total_subcategories')}")
                    return False
                
            else:
                self.log(f"   ❌ Metadata is not a dictionary: {type(metadata)}")
                return False
            
            self.log("   ✅ All structure format tests passed")
            return True
                
        except Exception as e:
            self.log(f"❌ Structure format testing error: {str(e)}", "ERROR")
            return False
    
    def verify_specific_changes(self):
        """Verify specific changes mentioned in review request"""
        try:
            self.log("🔄 Step 4: Verifying Specific Changes...")
            
            sidebar_response = self.test_results.get('sidebar_response')
            if not sidebar_response:
                self.log("   ❌ No sidebar response available for changes verification")
                return False
            
            structure = sidebar_response.get('structure', {})
            
            # Check specific changes mentioned in review request:
            # 1. "Inspection Records" → "Class Survey Report"
            # 2. "Survey Reports" → "Test Report"
            
            self.log("   🔍 Checking specific naming changes...")
            
            # Check Document Portfolio subcategories
            document_portfolio = structure.get("Document Portfolio", [])
            
            # Verify "Class Survey Report" is present (changed from "Inspection Records")
            if "Class Survey Report" in document_portfolio:
                self.log("   ✅ 'Class Survey Report' found in Document Portfolio")
            else:
                self.log("   ❌ 'Class Survey Report' not found in Document Portfolio")
                self.log(f"      Available subcategories: {document_portfolio}")
                return False
            
            # Verify "Test Report" is present (changed from "Survey Reports")
            if "Test Report" in document_portfolio:
                self.log("   ✅ 'Test Report' found in Document Portfolio")
            else:
                self.log("   ❌ 'Test Report' not found in Document Portfolio")
                self.log(f"      Available subcategories: {document_portfolio}")
                return False
            
            # Verify old names are NOT present
            if "Inspection Records" not in document_portfolio:
                self.log("   ✅ Old name 'Inspection Records' correctly removed")
            else:
                self.log("   ❌ Old name 'Inspection Records' still present")
                return False
            
            if "Survey Reports" not in document_portfolio:
                self.log("   ✅ Old name 'Survey Reports' correctly removed")
            else:
                self.log("   ❌ Old name 'Survey Reports' still present")
                return False
            
            # Verify other expected subcategories in Document Portfolio
            expected_document_portfolio = ["Certificates", "Class Survey Report", "Test Report", "Drawings & Manuals", "Other Documents"]
            
            if set(document_portfolio) == set(expected_document_portfolio):
                self.log("   ✅ Document Portfolio subcategories exactly match expected structure")
            else:
                self.log("   ❌ Document Portfolio subcategories do not match expected structure")
                self.log(f"      Expected: {expected_document_portfolio}")
                self.log(f"      Actual: {document_portfolio}")
                return False
            
            self.log("   ✅ All specific changes verification passed")
            return True
                
        except Exception as e:
            self.log(f"❌ Specific changes verification error: {str(e)}", "ERROR")
            return False
    
    def test_authentication_requirements(self):
        """Test authentication requirements for the endpoint"""
        try:
            self.log("🔐 Step 5: Testing Authentication Requirements...")
            
            endpoint = f"{BACKEND_URL}/sidebar-structure"
            
            # Test without authentication
            self.log("   🧪 Testing endpoint without authentication...")
            response_no_auth = requests.get(endpoint, timeout=30)
            self.log(f"   GET /api/sidebar-structure (no auth) - Status: {response_no_auth.status_code}")
            
            if response_no_auth.status_code == 401:
                self.log("   ✅ Endpoint properly requires authentication (401 Unauthorized)")
            elif response_no_auth.status_code == 200:
                self.log("   ℹ️ Endpoint accessible without authentication (public endpoint)")
                # This might be intentional for Google Apps Script integration
            else:
                self.log(f"   ⚠️ Unexpected response without authentication: {response_no_auth.status_code}")
            
            # Test with authentication (we already tested this in step 1)
            self.log("   🧪 Testing endpoint with authentication...")
            response_with_auth = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            self.log(f"   GET /api/sidebar-structure (with auth) - Status: {response_with_auth.status_code}")
            
            if response_with_auth.status_code == 200:
                self.log("   ✅ Endpoint accessible with authentication")
            else:
                self.log(f"   ❌ Endpoint not accessible with authentication: {response_with_auth.status_code}")
                return False
            
            # Test with invalid authentication
            self.log("   🧪 Testing endpoint with invalid authentication...")
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            response_invalid_auth = requests.get(endpoint, headers=invalid_headers, timeout=30)
            self.log(f"   GET /api/sidebar-structure (invalid auth) - Status: {response_invalid_auth.status_code}")
            
            if response_invalid_auth.status_code == 401:
                self.log("   ✅ Endpoint properly rejects invalid authentication")
            elif response_invalid_auth.status_code == 200:
                self.log("   ℹ️ Endpoint accessible with invalid authentication (public endpoint)")
            else:
                self.log(f"   ⚠️ Unexpected response with invalid authentication: {response_invalid_auth.status_code}")
            
            self.log("   ✅ Authentication requirements testing completed")
            return True
                
        except Exception as e:
            self.log(f"❌ Authentication requirements testing error: {str(e)}", "ERROR")
            return False

def main():
    """Main test execution"""
    print("📋 Ship Management System - Sidebar Structure Endpoint Testing")
    print("🎯 Focus: Testing updated /api/sidebar-structure endpoint")
    print("=" * 80)
    
    tester = SidebarStructureTester()
    success = tester.test_sidebar_structure_endpoint()
    
    print("=" * 80)
    if success:
        print("🎉 Sidebar structure endpoint testing completed successfully!")
        print("✅ All test steps passed - endpoint working correctly")
        
        # Print key findings summary
        print("\n🔑 KEY FINDINGS SUMMARY:")
        print("=" * 50)
        
        if 'sidebar_response' in tester.test_results:
            response = tester.test_results['sidebar_response']
            structure = response.get('structure', {})
            metadata = response.get('metadata', {})
            
            print(f"📊 Total Categories: {len(structure)}")
            print(f"📈 Total Subcategories: {sum(len(subcats) for subcats in structure.values())}")
            print(f"🏷️ Structure Version: {metadata.get('structure_version', 'N/A')}")
            
            print("\n📁 STRUCTURE OVERVIEW:")
            for category, subcategories in structure.items():
                print(f"   {category}: {len(subcategories)} subcategories")
                for subcat in subcategories:
                    print(f"      - {subcat}")
            
            print("\n✅ VERIFIED CHANGES:")
            print("   - 'Inspection Records' → 'Class Survey Report' ✅")
            print("   - 'Survey Reports' → 'Test Report' ✅")
        
        print("\n💡 ENDPOINT STATUS:")
        print("✅ GET /api/sidebar-structure endpoint working correctly")
        print("✅ Returns proper JSON structure for Google Apps Script")
        print("✅ Structure matches frontend requirements")
        print("✅ Metadata includes correct counts and version info")
        
        sys.exit(0)
    else:
        print("❌ Sidebar structure endpoint testing completed with issues!")
        print("🔍 Some test steps failed - check detailed logs above")
        sys.exit(1)

if __name__ == "__main__":
    main()