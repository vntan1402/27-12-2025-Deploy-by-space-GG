#!/usr/bin/env python3
"""
Backend Testing Script for Ship Management System
Focus: Login Functionality Debugging - Authentication System Testing
"""

import requests
import json
import os
import sys
from datetime import datetime
import tempfile
import subprocess
import time
import jwt
import base64

# Configuration - Use production URL from frontend .env
BACKEND_URL = "https://shipment-ai-1.preview.emergentagent.com/api"

class ShipsVisibilityTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_info = None
        self.user_company = None
        self.all_ships = []
        self.company_ships = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_ships_visibility_issue(self):
        """Main test function for ships visibility debugging"""
        self.log("🚢 Starting Ships Visibility Issue Testing - Debug getUserCompanyShips() Filter")
        self.log("=" * 80)
        
        # Step 1: Authentication with admin1/123456
        auth_result = self.test_authentication()
        if not auth_result:
            self.log("❌ Authentication failed - cannot proceed with testing")
            return False
        
        # Step 2: Get User Profile Data
        profile_result = self.get_user_profile_data()
        if not profile_result:
            self.log("❌ Failed to get user profile data")
            return False
        
        # Step 3: Get All Ships Data
        ships_result = self.get_all_ships_data()
        if not ships_result:
            self.log("❌ Failed to get ships data")
            return False
        
        # Step 4: Analyze Company Values
        company_analysis_result = self.analyze_company_values()
        
        # Step 5: Check Ship Structure
        structure_result = self.check_ship_structure()
        
        # Step 6: Test getUserCompanyShips Filter Logic
        filter_result = self.test_filter_logic()
        
        # Step 7: Identify Root Cause
        root_cause_result = self.identify_root_cause()
        
        # Step 8: Summary
        self.log("=" * 80)
        self.log("📋 SHIPS VISIBILITY ISSUE TEST SUMMARY")
        self.log("=" * 80)
        
        self.log(f"{'✅' if auth_result else '❌'} Authentication: {'SUCCESS' if auth_result else 'FAILED'}")
        self.log(f"{'✅' if profile_result else '❌'} User Profile Data: {'SUCCESS' if profile_result else 'FAILED'}")
        self.log(f"{'✅' if ships_result else '❌'} Ships Data Retrieval: {'SUCCESS' if ships_result else 'FAILED'}")
        self.log(f"{'✅' if company_analysis_result else '❌'} Company Values Analysis: {'SUCCESS' if company_analysis_result else 'FAILED'}")
        self.log(f"{'✅' if structure_result else '❌'} Ship Structure Check: {'SUCCESS' if structure_result else 'FAILED'}")
        self.log(f"{'✅' if filter_result else '❌'} Filter Logic Test: {'SUCCESS' if filter_result else 'FAILED'}")
        self.log(f"{'✅' if root_cause_result else '❌'} Root Cause Identification: {'SUCCESS' if root_cause_result else 'FAILED'}")
        
        overall_success = all([auth_result, profile_result, ships_result, company_analysis_result, structure_result])
        
        if overall_success:
            self.log("🎉 SHIPS VISIBILITY ISSUE: FULLY ANALYZED")
        else:
            self.log("❌ SHIPS VISIBILITY ISSUE: ANALYSIS INCOMPLETE")
            self.log("🔍 Root cause analysis completed - check detailed logs above")
        
        return overall_success
    
    def test_authentication(self):
        """Test authentication with admin1/123456"""
        try:
            self.log("🔐 Step 1: Testing Authentication with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            response = requests.post(endpoint, json=login_data, timeout=30)
            
            self.log(f"   Login response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_info = data.get("user")
                
                if self.auth_token and self.user_info:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    
                    self.log(f"   ✅ Authentication successful")
                    self.log(f"      User: {self.user_info.get('username')} ({self.user_info.get('role')})")
                    self.log(f"      Full Name: {self.user_info.get('full_name')}")
                    self.log(f"      Company: {self.user_info.get('company', 'N/A')}")
                    
                    return True
                else:
                    self.log("   ❌ Authentication failed - missing token or user data")
                    return False
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                
                self.log(f"   ❌ Authentication failed - HTTP {response.status_code}")
                self.log(f"      Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_user_profile_data(self):
        """Get current user profile data to check company assignment"""
        try:
            self.log("👤 Step 2: Getting User Profile Data...")
            
            # Try to get user profile from /api/user/profile or similar endpoint
            # Since we have user info from login, let's use that and also try to get more details
            
            self.log("   📊 User data from login response:")
            self.log(f"      Username: {self.user_info.get('username')}")
            self.log(f"      Role: {self.user_info.get('role')}")
            self.log(f"      Full Name: {self.user_info.get('full_name')}")
            self.log(f"      Company: {self.user_info.get('company')}")
            self.log(f"      Department: {self.user_info.get('department')}")
            self.log(f"      Ship: {self.user_info.get('ship')}")
            self.log(f"      User ID: {self.user_info.get('id')}")
            
            # Store user company for comparison
            self.user_company = self.user_info.get('company')
            
            if not self.user_company:
                self.log("   ⚠️ WARNING: User has no company assigned!")
                self.log("      This could be the root cause of ships visibility issue")
                return True  # Continue analysis even if no company
            
            self.log(f"   ✅ User company identified: '{self.user_company}'")
            self.log(f"      Company type: {type(self.user_company)}")
            self.log(f"      Company length: {len(self.user_company) if self.user_company else 0}")
            self.log(f"      Company repr: {repr(self.user_company)}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ User profile data error: {str(e)}", "ERROR")
            return False
    
    def get_all_ships_data(self):
        """Get all ships data and analyze company field values"""
        try:
            self.log("🚢 Step 3: Getting All Ships Data...")
            
            endpoint = f"{BACKEND_URL}/ships"
            response = self.session.get(endpoint, timeout=30)
            
            self.log(f"   Ships API response status: {response.status_code}")
            
            if response.status_code == 200:
                self.all_ships = response.json()
                self.log(f"   ✅ Retrieved {len(self.all_ships)} ships")
                
                # Analyze each ship's company field
                self.log("   📊 Ships company field analysis:")
                
                for i, ship in enumerate(self.all_ships):
                    ship_name = ship.get('name', 'Unknown')
                    ship_company = ship.get('company', 'N/A')
                    ship_id = ship.get('id', 'N/A')
                    
                    self.log(f"      Ship {i+1}: {ship_name}")
                    self.log(f"         ID: {ship_id}")
                    self.log(f"         Company: '{ship_company}'")
                    self.log(f"         Company type: {type(ship_company)}")
                    self.log(f"         Company length: {len(ship_company) if ship_company else 0}")
                    self.log(f"         Company repr: {repr(ship_company)}")
                    
                    # Check for SUNSHINE ships specifically
                    if "SUNSHINE" in ship_name.upper():
                        self.log(f"         🌟 SUNSHINE SHIP FOUND!")
                        self.log(f"         🌟 Company value: '{ship_company}'")
                
                # Look for unique company values
                unique_companies = set()
                for ship in self.all_ships:
                    company = ship.get('company')
                    if company:
                        unique_companies.add(company)
                
                self.log(f"   📈 Unique company values found: {len(unique_companies)}")
                for company in sorted(unique_companies):
                    self.log(f"      - '{company}' (type: {type(company)}, len: {len(company)})")
                
                return True
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                
                self.log(f"   ❌ Ships API failed - HTTP {response.status_code}")
                self.log(f"      Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ships data retrieval error: {str(e)}", "ERROR")
            return False
    
    def analyze_company_values(self):
        """Compare user company with ship company values"""
        try:
            self.log("🔍 Step 4: Analyzing Company Values for Matching...")
            
            if not self.user_company:
                self.log("   ⚠️ User has no company - cannot perform comparison")
                return True
            
            if not self.all_ships:
                self.log("   ❌ No ships data available for comparison")
                return False
            
            self.log(f"   🎯 Target user company: '{self.user_company}'")
            
            # Find exact matches
            exact_matches = []
            case_insensitive_matches = []
            trimmed_matches = []
            no_matches = []
            
            for ship in self.all_ships:
                ship_name = ship.get('name', 'Unknown')
                ship_company = ship.get('company', '')
                
                if ship_company == self.user_company:
                    exact_matches.append((ship_name, ship_company))
                elif ship_company.lower() == self.user_company.lower():
                    case_insensitive_matches.append((ship_name, ship_company))
                elif ship_company.strip() == self.user_company.strip():
                    trimmed_matches.append((ship_name, ship_company))
                else:
                    no_matches.append((ship_name, ship_company))
            
            self.log(f"   📊 Company matching analysis:")
            self.log(f"      ✅ Exact matches: {len(exact_matches)}")
            for ship_name, ship_company in exact_matches:
                self.log(f"         - {ship_name}: '{ship_company}'")
            
            self.log(f"      🔤 Case-insensitive matches: {len(case_insensitive_matches)}")
            for ship_name, ship_company in case_insensitive_matches:
                self.log(f"         - {ship_name}: '{ship_company}' vs '{self.user_company}'")
            
            self.log(f"      ✂️ Trimmed matches: {len(trimmed_matches)}")
            for ship_name, ship_company in trimmed_matches:
                self.log(f"         - {ship_name}: '{ship_company}' vs '{self.user_company}'")
            
            self.log(f"      ❌ No matches: {len(no_matches)}")
            for ship_name, ship_company in no_matches[:5]:  # Show first 5
                self.log(f"         - {ship_name}: '{ship_company}' vs '{self.user_company}'")
            
            # Store company ships for filter testing
            self.company_ships = exact_matches
            
            # Check for SUNSHINE ships specifically
            sunshine_ships = [ship for ship in self.all_ships if "SUNSHINE" in ship.get('name', '').upper()]
            if sunshine_ships:
                self.log(f"   🌟 SUNSHINE ships analysis:")
                for ship in sunshine_ships:
                    ship_name = ship.get('name')
                    ship_company = ship.get('company', '')
                    match_status = "✅ MATCH" if ship_company == self.user_company else "❌ NO MATCH"
                    self.log(f"      - {ship_name}: '{ship_company}' {match_status}")
                    
                    if ship_company != self.user_company:
                        self.log(f"        🔍 Difference analysis:")
                        self.log(f"           User: '{self.user_company}' (len: {len(self.user_company)})")
                        self.log(f"           Ship: '{ship_company}' (len: {len(ship_company)})")
                        self.log(f"           Equal: {ship_company == self.user_company}")
                        self.log(f"           Case equal: {ship_company.lower() == self.user_company.lower()}")
                        self.log(f"           Trimmed equal: {ship_company.strip() == self.user_company.strip()}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Company values analysis error: {str(e)}", "ERROR")
            return False
    
    def check_ship_structure(self):
        """Check ship data structure and fields"""
        try:
            self.log("🏗️ Step 5: Checking Ship Data Structure...")
            
            if not self.all_ships:
                self.log("   ❌ No ships data available")
                return False
            
            # Analyze first ship structure
            if self.all_ships:
                sample_ship = self.all_ships[0]
                self.log(f"   📋 Sample ship structure (Ship: {sample_ship.get('name', 'Unknown')}):")
                
                for key, value in sample_ship.items():
                    self.log(f"      {key}: {repr(value)} (type: {type(value).__name__})")
                
                # Check for company vs company_id field
                has_company = 'company' in sample_ship
                has_company_id = 'company_id' in sample_ship
                
                self.log(f"   🔍 Company field analysis:")
                self.log(f"      'company' field present: {'✅' if has_company else '❌'}")
                self.log(f"      'company_id' field present: {'✅' if has_company_id else '❌'}")
                
                if has_company:
                    self.log(f"      'company' value: '{sample_ship.get('company')}'")
                if has_company_id:
                    self.log(f"      'company_id' value: '{sample_ship.get('company_id')}'")
                
                # Check all ships for consistency
                company_field_consistency = True
                for ship in self.all_ships:
                    if 'company' not in ship:
                        company_field_consistency = False
                        self.log(f"      ⚠️ Ship '{ship.get('name')}' missing 'company' field")
                
                self.log(f"   📊 Field consistency: {'✅ All ships have company field' if company_field_consistency else '❌ Some ships missing company field'}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Ship structure check error: {str(e)}", "ERROR")
            return False
    
    def test_filter_logic(self):
        """Test the getUserCompanyShips() filter logic"""
        try:
            self.log("⚙️ Step 6: Testing getUserCompanyShips() Filter Logic...")
            
            if not self.user_company:
                self.log("   ⚠️ User has no company - filter would return empty array")
                return True
            
            if not self.all_ships:
                self.log("   ❌ No ships data available for filter testing")
                return False
            
            # Simulate the filter logic: ships.filter(ship => ship.company === user.company)
            self.log(f"   🔧 Simulating: ships.filter(ship => ship.company === '{self.user_company}')")
            
            filtered_ships = []
            for ship in self.all_ships:
                ship_company = ship.get('company', '')
                if ship_company == self.user_company:
                    filtered_ships.append(ship)
            
            self.log(f"   📊 Filter results:")
            self.log(f"      Total ships: {len(self.all_ships)}")
            self.log(f"      Filtered ships: {len(filtered_ships)}")
            self.log(f"      Filter success rate: {len(filtered_ships)/len(self.all_ships)*100:.1f}%")
            
            if filtered_ships:
                self.log(f"   ✅ Ships that match user company:")
                for ship in filtered_ships:
                    self.log(f"      - {ship.get('name')}: '{ship.get('company')}'")
            else:
                self.log(f"   ❌ NO SHIPS MATCH USER COMPANY!")
                self.log(f"      This explains why getUserCompanyShips() returns empty array")
                
                # Show what ships would match with different comparison methods
                self.log(f"   🔍 Alternative matching methods:")
                
                # Case insensitive
                case_insensitive_matches = [
                    ship for ship in self.all_ships 
                    if ship.get('company', '').lower() == self.user_company.lower()
                ]
                self.log(f"      Case-insensitive matches: {len(case_insensitive_matches)}")
                
                # Trimmed
                trimmed_matches = [
                    ship for ship in self.all_ships 
                    if ship.get('company', '').strip() == self.user_company.strip()
                ]
                self.log(f"      Trimmed matches: {len(trimmed_matches)}")
                
                # Contains
                contains_matches = [
                    ship for ship in self.all_ships 
                    if self.user_company.upper() in ship.get('company', '').upper()
                ]
                self.log(f"      Contains matches: {len(contains_matches)}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Filter logic test error: {str(e)}", "ERROR")
            return False
    
    def identify_root_cause(self):
        """Identify the root cause of the ships visibility issue"""
        try:
            self.log("🎯 Step 7: Identifying Root Cause...")
            
            # Analyze all the data we've collected
            root_causes = []
            
            # Check 1: User has no company
            if not self.user_company:
                root_causes.append("User has no company assigned - filter will always return empty")
            
            # Check 2: No ships match user company exactly
            if self.user_company and self.all_ships:
                exact_matches = [
                    ship for ship in self.all_ships 
                    if ship.get('company', '') == self.user_company
                ]
                if not exact_matches:
                    root_causes.append(f"No ships have company field exactly matching '{self.user_company}'")
            
            # Check 3: Case sensitivity issues
            if self.user_company and self.all_ships:
                case_matches = [
                    ship for ship in self.all_ships 
                    if ship.get('company', '').lower() == self.user_company.lower()
                ]
                exact_matches = [
                    ship for ship in self.all_ships 
                    if ship.get('company', '') == self.user_company
                ]
                if case_matches and not exact_matches:
                    root_causes.append("Case sensitivity issue - ships exist but with different case")
            
            # Check 4: Whitespace issues
            if self.user_company and self.all_ships:
                trimmed_matches = [
                    ship for ship in self.all_ships 
                    if ship.get('company', '').strip() == self.user_company.strip()
                ]
                exact_matches = [
                    ship for ship in self.all_ships 
                    if ship.get('company', '') == self.user_company
                ]
                if trimmed_matches and not exact_matches:
                    root_causes.append("Whitespace issue - ships exist but with extra spaces")
            
            # Check 5: Field name issues
            ships_missing_company = [
                ship for ship in self.all_ships 
                if 'company' not in ship or not ship.get('company')
            ]
            if ships_missing_company:
                root_causes.append(f"{len(ships_missing_company)} ships missing or have empty 'company' field")
            
            # Report findings
            self.log("   🔍 ROOT CAUSE ANALYSIS RESULTS:")
            
            if root_causes:
                self.log(f"   ❌ {len(root_causes)} potential root cause(s) identified:")
                for i, cause in enumerate(root_causes, 1):
                    self.log(f"      {i}. {cause}")
            else:
                self.log("   ✅ No obvious root causes found - ships visibility should be working")
            
            # Provide specific recommendations
            self.log("   💡 RECOMMENDATIONS:")
            
            if not self.user_company:
                self.log("      1. Assign a company to admin1 user")
                self.log("      2. Update user profile with correct company name")
            
            if self.user_company and self.all_ships:
                # Find the most likely company match
                all_companies = [ship.get('company', '') for ship in self.all_ships if ship.get('company')]
                unique_companies = list(set(all_companies))
                
                self.log(f"      1. Available company values in ships:")
                for company in sorted(unique_companies):
                    self.log(f"         - '{company}'")
                
                self.log(f"      2. User company should match one of these exactly")
                self.log(f"      3. Current user company: '{self.user_company}'")
                
                # Find closest match
                closest_match = None
                for company in unique_companies:
                    if company.lower() == self.user_company.lower():
                        closest_match = company
                        break
                
                if closest_match and closest_match != self.user_company:
                    self.log(f"      4. SUGGESTED FIX: Change user company from '{self.user_company}' to '{closest_match}'")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Root cause identification error: {str(e)}", "ERROR")
            return False

def main():
    """Main test execution"""
    print("🚢 Ship Management System - Ships Visibility Issue Testing")
    print("🔍 Debug: getUserCompanyShips() filter returning empty array")
    print("=" * 80)
    
    tester = ShipsVisibilityTester()
    success = tester.test_ships_visibility_issue()
    
    print("=" * 80)
    if success:
        print("🎉 Ships visibility issue analysis completed successfully!")
        print("✅ Root cause analysis completed - check detailed logs above")
        sys.exit(0)
    else:
        print("❌ Ships visibility issue analysis completed with issues!")
        print("🔍 Some analysis steps failed - check detailed logs above")
        print("💡 Focus on the failed steps to identify the exact issue")
        sys.exit(1)

if __name__ == "__main__":
    main()