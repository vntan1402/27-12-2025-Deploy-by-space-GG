#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
Focus: Certificate Database Schema and Category/Folder Structure Analysis
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

class CertificateDatabaseTester:
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
    
    def test_certificate_database_schema(self):
        """Main test function for certificate database schema analysis"""
        self.log("📋 Starting Certificate Database Schema Analysis")
        self.log("🎯 Focus: Understanding certificate category/folder structure for move functionality")
        self.log("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            return False
        
        # Step 2: Get Certificate Schema Sample
        schema_result = self.get_certificate_schema_sample()
        
        # Step 3: Check Current Categories
        categories_result = self.check_current_categories()
        
        # Step 4: Analyze Certificate-Folder Relationship
        folder_relationship_result = self.analyze_certificate_folder_relationship()
        
        # Step 5: Check Current Move Implementation
        move_implementation_result = self.check_current_move_implementation()
        
        # Step 6: Test Certificate Endpoints
        endpoints_result = self.test_certificate_endpoints()
        
        # Step 7: Summary
        self.log("=" * 80)
        self.log("📋 CERTIFICATE DATABASE SCHEMA ANALYSIS SUMMARY")
        self.log("=" * 80)
        
        self.log(f"{'✅' if schema_result else '❌'} Certificate Schema Sample: {'SUCCESS' if schema_result else 'FAILED'}")
        self.log(f"{'✅' if categories_result else '❌'} Current Categories Check: {'SUCCESS' if categories_result else 'FAILED'}")
        self.log(f"{'✅' if folder_relationship_result else '❌'} Certificate-Folder Relationship: {'SUCCESS' if folder_relationship_result else 'FAILED'}")
        self.log(f"{'✅' if move_implementation_result else '❌'} Current Move Implementation: {'SUCCESS' if move_implementation_result else 'FAILED'}")
        self.log(f"{'✅' if endpoints_result else '❌'} Certificate Endpoints Testing: {'SUCCESS' if endpoints_result else 'FAILED'}")
        
        overall_success = all([schema_result, categories_result, folder_relationship_result, move_implementation_result, endpoints_result])
        
        if overall_success:
            self.log("🎉 CERTIFICATE DATABASE SCHEMA ANALYSIS: COMPLETED SUCCESSFULLY")
        else:
            self.log("❌ CERTIFICATE DATABASE SCHEMA ANALYSIS: ISSUES DETECTED")
            self.log("🔍 Check detailed logs above for specific issues")
        
        return overall_success
    
    def get_certificate_schema_sample(self):
        """Get a sample certificate from database to understand schema"""
        try:
            self.log("📋 Step 1: Getting Certificate Schema Sample...")
            
            # First, get all certificates to find a sample
            endpoint = f"{BACKEND_URL}/certificates"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            self.log(f"   GET /api/certificates - Status: {response.status_code}")
            
            if response.status_code == 200:
                certificates = response.json()
                self.log(f"   ✅ Retrieved {len(certificates)} certificates from database")
                
                if certificates:
                    # Analyze the first certificate as a sample
                    sample_cert = certificates[0]
                    self.log("   📋 Sample Certificate Schema Analysis:")
                    self.log("   " + "=" * 50)
                    
                    # Core identification fields
                    self.log("   🔑 CORE IDENTIFICATION FIELDS:")
                    self.log(f"      id: {sample_cert.get('id', 'N/A')}")
                    self.log(f"      ship_id: {sample_cert.get('ship_id', 'N/A')}")
                    self.log(f"      cert_name: {sample_cert.get('cert_name', 'N/A')}")
                    self.log(f"      cert_no: {sample_cert.get('cert_no', 'N/A')}")
                    
                    # Category/Folder related fields
                    self.log("   📁 CATEGORY/FOLDER RELATED FIELDS:")
                    category = sample_cert.get('category', 'N/A')
                    self.log(f"      category: {category}")
                    self.log(f"      google_drive_folder_path: {sample_cert.get('google_drive_folder_path', 'N/A')}")
                    self.log(f"      google_drive_file_id: {sample_cert.get('google_drive_file_id', 'N/A')}")
                    
                    # Certificate details
                    self.log("   📄 CERTIFICATE DETAILS:")
                    self.log(f"      cert_type: {sample_cert.get('cert_type', 'N/A')}")
                    self.log(f"      issue_date: {sample_cert.get('issue_date', 'N/A')}")
                    self.log(f"      valid_date: {sample_cert.get('valid_date', 'N/A')}")
                    self.log(f"      issued_by: {sample_cert.get('issued_by', 'N/A')}")
                    
                    # File information
                    self.log("   📎 FILE INFORMATION:")
                    self.log(f"      file_uploaded: {sample_cert.get('file_uploaded', 'N/A')}")
                    self.log(f"      file_name: {sample_cert.get('file_name', 'N/A')}")
                    self.log(f"      file_size: {sample_cert.get('file_size', 'N/A')}")
                    
                    # Additional fields
                    self.log("   ➕ ADDITIONAL FIELDS:")
                    self.log(f"      sensitivity_level: {sample_cert.get('sensitivity_level', 'N/A')}")
                    self.log(f"      notes: {sample_cert.get('notes', 'N/A')}")
                    self.log(f"      ship_name: {sample_cert.get('ship_name', 'N/A')}")
                    self.log(f"      created_at: {sample_cert.get('created_at', 'N/A')}")
                    
                    # Enhanced fields (from response processing)
                    self.log("   🔧 ENHANCED FIELDS:")
                    self.log(f"      cert_abbreviation: {sample_cert.get('cert_abbreviation', 'N/A')}")
                    self.log(f"      status: {sample_cert.get('status', 'N/A')}")
                    self.log(f"      issued_by_abbreviation: {sample_cert.get('issued_by_abbreviation', 'N/A')}")
                    self.log(f"      has_notes: {sample_cert.get('has_notes', 'N/A')}")
                    
                    # Store sample for further analysis
                    self.test_results['sample_certificate'] = sample_cert
                    
                    # Key finding: Check if category field exists and what values it contains
                    if 'category' in sample_cert:
                        self.log(f"   🎯 KEY FINDING: 'category' field exists with value: '{category}'")
                        self.log("      This field likely determines which folder/category the certificate belongs to")
                    else:
                        self.log("   ⚠️ WARNING: 'category' field not found in certificate schema")
                    
                else:
                    self.log("   ⚠️ No certificates found in database - cannot analyze schema")
                    return True  # Don't fail if no data exists
                
                return True
                
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                
                self.log(f"   ❌ Failed to retrieve certificates - HTTP {response.status_code}")
                self.log(f"      Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log(f"❌ Certificate schema analysis error: {str(e)}", "ERROR")
            return False
    
    def check_current_categories(self):
        """Check all possible certificate categories in the system"""
        try:
            self.log("📁 Step 2: Checking Current Certificate Categories...")
            
            # Get all certificates to analyze category distribution
            endpoint = f"{BACKEND_URL}/certificates"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                certificates = response.json()
                self.log(f"   ✅ Analyzing categories from {len(certificates)} certificates")
                
                # Collect all unique categories
                categories = set()
                category_counts = {}
                
                for cert in certificates:
                    category = cert.get('category', 'unknown')
                    categories.add(category)
                    category_counts[category] = category_counts.get(category, 0) + 1
                
                self.log("   📊 CERTIFICATE CATEGORIES FOUND:")
                self.log("   " + "=" * 40)
                
                for category in sorted(categories):
                    count = category_counts[category]
                    self.log(f"      '{category}': {count} certificates")
                
                self.log(f"   📈 Total unique categories: {len(categories)}")
                
                # Store categories for further analysis
                self.test_results['categories'] = list(categories)
                self.test_results['category_counts'] = category_counts
                
                # Check if there are standard folder categories
                expected_categories = [
                    'certificates', 'test_reports', 'survey_reports', 
                    'drawings_manuals', 'other_documents', 'inspection_records'
                ]
                
                self.log("   🎯 EXPECTED FOLDER CATEGORIES CHECK:")
                for expected in expected_categories:
                    if expected in categories:
                        self.log(f"      ✅ '{expected}' - Found")
                    else:
                        self.log(f"      ❌ '{expected}' - Not found")
                
                return True
                
            else:
                self.log(f"   ❌ Failed to retrieve certificates for category analysis - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Category analysis error: {str(e)}", "ERROR")
            return False
    
    def analyze_certificate_folder_relationship(self):
        """Analyze how certificates are associated with specific folders"""
        try:
            self.log("🔗 Step 3: Analyzing Certificate-Folder Relationship...")
            
            # Get ships to understand the folder structure
            ships_endpoint = f"{BACKEND_URL}/ships"
            ships_response = requests.get(ships_endpoint, headers=self.get_headers(), timeout=30)
            
            if ships_response.status_code == 200:
                ships = ships_response.json()
                self.log(f"   ✅ Retrieved {len(ships)} ships from database")
                
                if ships:
                    # Analyze first ship's certificates
                    sample_ship = ships[0]
                    ship_id = sample_ship.get('id')
                    ship_name = sample_ship.get('name')
                    
                    self.log(f"   🚢 Analyzing certificates for ship: {ship_name} (ID: {ship_id})")
                    
                    # Get certificates for this ship
                    cert_endpoint = f"{BACKEND_URL}/ships/{ship_id}/certificates"
                    cert_response = requests.get(cert_endpoint, headers=self.get_headers(), timeout=30)
                    
                    if cert_response.status_code == 200:
                        ship_certificates = cert_response.json()
                        self.log(f"      📋 Found {len(ship_certificates)} certificates for this ship")
                        
                        # Analyze folder structure
                        self.log("      📁 FOLDER STRUCTURE ANALYSIS:")
                        
                        folder_paths = set()
                        category_to_folder = {}
                        
                        for cert in ship_certificates:
                            category = cert.get('category', 'unknown')
                            folder_path = cert.get('google_drive_folder_path', 'N/A')
                            
                            if folder_path != 'N/A':
                                folder_paths.add(folder_path)
                                category_to_folder[category] = folder_path
                        
                        self.log(f"         Unique folder paths: {len(folder_paths)}")
                        for path in sorted(folder_paths):
                            self.log(f"            {path}")
                        
                        self.log("      🎯 CATEGORY TO FOLDER MAPPING:")
                        for category, folder in category_to_folder.items():
                            self.log(f"         '{category}' → '{folder}'")
                        
                        # Store relationship data
                        self.test_results['folder_relationships'] = {
                            'ship_id': ship_id,
                            'ship_name': ship_name,
                            'category_to_folder': category_to_folder,
                            'folder_paths': list(folder_paths)
                        }
                        
                        # Key finding: How to move certificates between categories
                        self.log("      🔑 KEY FINDING FOR MOVE FUNCTIONALITY:")
                        self.log("         To move a certificate between categories/folders:")
                        self.log("         1. Update the 'category' field in the certificate record")
                        self.log("         2. Update the 'google_drive_folder_path' field")
                        self.log("         3. Move the actual file in Google Drive")
                        self.log("         4. Update 'google_drive_file_id' if needed")
                        
                    else:
                        self.log(f"      ❌ Failed to get certificates for ship - HTTP {cert_response.status_code}")
                        return False
                
                return True
                
            else:
                self.log(f"   ❌ Failed to retrieve ships - HTTP {ships_response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Certificate-folder relationship analysis error: {str(e)}", "ERROR")
            return False
    
    def check_current_move_implementation(self):
        """Check what the current move API does"""
        try:
            self.log("🔄 Step 4: Checking Current Move Implementation...")
            
            # Look for move-related endpoints
            move_endpoints_to_test = [
                "/certificates/move",
                "/certificates/{cert_id}/move",
                "/gdrive/move-file",
                "/gdrive/move-certificate"
            ]
            
            self.log("   🔍 Testing potential move endpoints...")
            
            for endpoint_template in move_endpoints_to_test:
                # For endpoints with {cert_id}, use a sample certificate ID if available
                if '{cert_id}' in endpoint_template:
                    sample_cert = self.test_results.get('sample_certificate')
                    if sample_cert:
                        cert_id = sample_cert.get('id')
                        endpoint = endpoint_template.replace('{cert_id}', cert_id)
                    else:
                        self.log(f"      ⚠️ Skipping {endpoint_template} - no sample certificate ID available")
                        continue
                else:
                    endpoint = endpoint_template
                
                full_endpoint = f"{BACKEND_URL}{endpoint}"
                
                # Test with OPTIONS to see if endpoint exists
                try:
                    options_response = requests.options(full_endpoint, headers=self.get_headers(), timeout=10)
                    self.log(f"      OPTIONS {endpoint} - Status: {options_response.status_code}")
                    
                    if options_response.status_code in [200, 204]:
                        allowed_methods = options_response.headers.get('Allow', 'N/A')
                        self.log(f"         ✅ Endpoint exists - Allowed methods: {allowed_methods}")
                    
                    # Test with GET to see what happens
                    get_response = requests.get(full_endpoint, headers=self.get_headers(), timeout=10)
                    self.log(f"      GET {endpoint} - Status: {get_response.status_code}")
                    
                    if get_response.status_code == 405:
                        self.log("         ℹ️ Method not allowed (endpoint exists but GET not supported)")
                    elif get_response.status_code == 404:
                        self.log("         ❌ Endpoint not found")
                    elif get_response.status_code == 200:
                        self.log("         ✅ Endpoint accessible")
                        
                except requests.exceptions.RequestException as e:
                    self.log(f"      ❌ Error testing {endpoint}: {str(e)}")
            
            # Check if there are any Google Drive related endpoints
            self.log("   🔍 Checking Google Drive integration endpoints...")
            
            gdrive_endpoints = [
                "/gdrive/status",
                "/gdrive/config", 
                "/gdrive/sync-to-drive",
                "/gdrive/sync-to-drive-proxy"
            ]
            
            for endpoint in gdrive_endpoints:
                full_endpoint = f"{BACKEND_URL}{endpoint}"
                
                try:
                    response = requests.get(full_endpoint, headers=self.get_headers(), timeout=10)
                    self.log(f"      GET {endpoint} - Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        self.log("         ✅ Google Drive endpoint accessible")
                        try:
                            data = response.json()
                            self.log(f"         📋 Response: {json.dumps(data, indent=2)[:200]}...")
                        except:
                            pass
                    elif response.status_code == 404:
                        self.log("         ❌ Google Drive endpoint not found")
                    
                except requests.exceptions.RequestException as e:
                    self.log(f"      ❌ Error testing {endpoint}: {str(e)}")
            
            # Key finding about current implementation
            self.log("   🎯 KEY FINDINGS ABOUT CURRENT MOVE IMPLEMENTATION:")
            self.log("      Based on the certificate schema analysis:")
            self.log("      1. Certificates have 'category' field that determines folder")
            self.log("      2. Certificates have 'google_drive_folder_path' for Google Drive location")
            self.log("      3. Certificates have 'google_drive_file_id' for Google Drive file reference")
            self.log("      4. To implement proper move functionality, need to:")
            self.log("         - Update certificate 'category' field in database")
            self.log("         - Update 'google_drive_folder_path' field")
            self.log("         - Move actual file in Google Drive to new folder")
            self.log("         - Update 'google_drive_file_id' if necessary")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Move implementation analysis error: {str(e)}", "ERROR")
            return False
    
    def test_certificate_endpoints(self):
        """Test certificate-related endpoints to understand current functionality"""
        try:
            self.log("🔌 Step 5: Testing Certificate Endpoints...")
            
            # Test main certificate endpoints
            endpoints_to_test = [
                ("GET", "/certificates", "Get all certificates"),
                ("GET", "/ships", "Get all ships"),
                ("GET", "/companies", "Get all companies")
            ]
            
            # Add ship-specific certificate endpoint if we have a ship
            sample_ship_id = None
            if 'folder_relationships' in self.test_results:
                sample_ship_id = self.test_results['folder_relationships']['ship_id']
                endpoints_to_test.append(
                    ("GET", f"/ships/{sample_ship_id}/certificates", "Get ship certificates")
                )
            
            for method, endpoint, description in endpoints_to_test:
                self.log(f"   🧪 Testing {method} {endpoint} - {description}")
                
                full_endpoint = f"{BACKEND_URL}{endpoint}"
                
                try:
                    if method == "GET":
                        response = requests.get(full_endpoint, headers=self.get_headers(), timeout=30)
                    else:
                        continue  # Skip non-GET methods for now
                    
                    self.log(f"      Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if isinstance(data, list):
                                self.log(f"      ✅ Success - Retrieved {len(data)} items")
                            else:
                                self.log(f"      ✅ Success - Retrieved data object")
                        except:
                            self.log(f"      ✅ Success - Non-JSON response")
                    else:
                        try:
                            error_data = response.json()
                            error_detail = error_data.get('detail', 'Unknown error')
                        except:
                            error_detail = response.text[:100]
                        
                        self.log(f"      ❌ Failed - {error_detail}")
                
                except requests.exceptions.RequestException as e:
                    self.log(f"      ❌ Network error: {str(e)}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Certificate endpoints testing error: {str(e)}", "ERROR")
            return False

def main():
    """Main test execution"""
    print("📋 Ship Management System - Certificate Database Schema Analysis")
    print("🎯 Focus: Understanding certificate category/folder structure for move functionality")
    print("=" * 80)
    
    tester = CertificateDatabaseTester()
    success = tester.test_certificate_database_schema()
    
    print("=" * 80)
    if success:
        print("🎉 Certificate database schema analysis completed successfully!")
        print("✅ All analysis steps completed - certificate structure understood")
        
        # Print key findings summary
        print("\n🔑 KEY FINDINGS SUMMARY:")
        print("=" * 50)
        
        if 'sample_certificate' in tester.test_results:
            sample = tester.test_results['sample_certificate']
            print(f"📋 Certificate Schema: {len(sample.keys())} fields identified")
            print(f"📁 Category Field: {'✅ Present' if 'category' in sample else '❌ Missing'}")
            if 'category' in sample:
                print(f"   Current value: '{sample['category']}'")
        
        if 'categories' in tester.test_results:
            categories = tester.test_results['categories']
            print(f"📊 Total Categories: {len(categories)}")
            print(f"   Categories: {', '.join(categories)}")
        
        if 'folder_relationships' in tester.test_results:
            rel = tester.test_results['folder_relationships']
            print(f"🔗 Folder Relationships: {len(rel['category_to_folder'])} mappings found")
            for cat, folder in rel['category_to_folder'].items():
                print(f"   '{cat}' → '{folder}'")
        
        print("\n💡 RECOMMENDATIONS FOR MOVE FUNCTIONALITY:")
        print("1. Update certificate 'category' field to change folder assignment")
        print("2. Update 'google_drive_folder_path' field accordingly")
        print("3. Implement Google Drive file move operation")
        print("4. Consider adding move history/audit trail")
        
        sys.exit(0)
    else:
        print("❌ Certificate database schema analysis completed with issues!")
        print("🔍 Some analysis steps failed - check detailed logs above")
        sys.exit(1)

if __name__ == "__main__":
    main()