#!/usr/bin/env python3
"""
Detailed Google Drive Configuration Analysis

This test will examine the exact response structure from GET /api/gdrive/config
to understand why the frontend might show "Not Configured" despite backend working.
"""

import requests
import json
import sys
from datetime import datetime

class DetailedConfigAnalyzer:
    def __init__(self, base_url="https://shipwise-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def authenticate(self):
        """Authenticate as admin"""
        self.log("🔐 Authenticating as admin/admin123")
        
        response = requests.post(
            f"{self.api_url}/auth/login",
            json={"username": "admin", "password": "admin123"},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            self.log("✅ Authentication successful")
            return True
        else:
            self.log(f"❌ Authentication failed: {response.status_code}")
            return False

    def analyze_config_response(self):
        """Analyze the GET /api/gdrive/config response in detail"""
        self.log("🔍 Analyzing GET /api/gdrive/config response structure")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        
        response = requests.get(
            f"{self.api_url}/gdrive/config",
            headers=headers,
            timeout=30
        )
        
        self.log(f"Response Status: {response.status_code}")
        self.log(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                self.log("✅ Response is valid JSON")
                
                # Detailed analysis of response structure
                self.log("📋 DETAILED RESPONSE ANALYSIS:")
                self.log(f"Raw JSON: {json.dumps(data, indent=2)}")
                
                self.log("\n🔍 FIELD-BY-FIELD ANALYSIS:")
                for key, value in data.items():
                    value_type = type(value).__name__
                    self.log(f"   {key}: {repr(value)} (type: {value_type})")
                
                # Check for specific fields that frontend might expect
                expected_fields = [
                    'configured', 'auth_method', 'folder_id', 'apps_script_url',
                    'web_app_url', 'service_account_email', 'service_account_json'
                ]
                
                self.log("\n🎯 EXPECTED FIELDS CHECK:")
                for field in expected_fields:
                    if field in data:
                        value = data[field]
                        if isinstance(value, bool):
                            status = "✅ PRESENT (boolean)" if value else "⚠️ PRESENT (false)"
                        elif isinstance(value, str) and value:
                            status = "✅ PRESENT (non-empty string)"
                        elif isinstance(value, str) and not value:
                            status = "⚠️ PRESENT (empty string)"
                        elif value is None:
                            status = "⚠️ PRESENT (null)"
                        else:
                            status = f"✅ PRESENT ({type(value).__name__})"
                        self.log(f"   {field}: {status}")
                    else:
                        self.log(f"   {field}: ❌ MISSING")
                
                # Check for potential frontend issues
                self.log("\n🚨 POTENTIAL FRONTEND ISSUES:")
                
                # Issue 1: apps_script_url is boolean instead of string
                if 'apps_script_url' in data and isinstance(data['apps_script_url'], bool):
                    self.log("   ⚠️ ISSUE: apps_script_url is boolean (True) instead of actual URL string")
                    self.log("      Frontend might expect the actual URL string, not just True/False")
                
                # Issue 2: Check if configured field is properly set
                if 'configured' in data:
                    if data['configured'] is True:
                        self.log("   ✅ configured field is True")
                    else:
                        self.log("   ❌ ISSUE: configured field is not True")
                else:
                    self.log("   ❌ ISSUE: configured field is missing")
                
                # Issue 3: Check auth_method
                if 'auth_method' in data:
                    if data['auth_method'] == 'apps_script':
                        self.log("   ✅ auth_method is 'apps_script'")
                    else:
                        self.log(f"   ⚠️ auth_method is '{data['auth_method']}' (not 'apps_script')")
                else:
                    self.log("   ❌ ISSUE: auth_method field is missing")
                
                return True, data
                
            except json.JSONDecodeError:
                self.log("❌ Response is not valid JSON")
                self.log(f"Raw response: {response.text}")
                return False, None
        else:
            self.log(f"❌ Request failed with status {response.status_code}")
            self.log(f"Response: {response.text}")
            return False, None

    def compare_with_status_endpoint(self):
        """Compare config response with status response"""
        self.log("🔄 Comparing GET /api/gdrive/config with GET /api/gdrive/status")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        
        # Get config
        config_response = requests.get(f"{self.api_url}/gdrive/config", headers=headers, timeout=30)
        status_response = requests.get(f"{self.api_url}/gdrive/status", headers=headers, timeout=30)
        
        if config_response.status_code == 200 and status_response.status_code == 200:
            config_data = config_response.json()
            status_data = status_response.json()
            
            self.log("📊 ENDPOINT COMPARISON:")
            self.log(f"Config endpoint: {json.dumps(config_data, indent=2)}")
            self.log(f"Status endpoint: {json.dumps(status_data, indent=2)}")
            
            # Check consistency
            config_configured = config_data.get('configured', False)
            status_connected = status_data.get('status') == 'connected'
            
            self.log("\n🔍 CONSISTENCY CHECK:")
            self.log(f"   Config says configured: {config_configured}")
            self.log(f"   Status says connected: {status_connected}")
            
            if config_configured and status_connected:
                self.log("   ✅ Both endpoints agree: system is configured")
            elif config_configured and not status_connected:
                self.log("   ⚠️ INCONSISTENCY: Config says configured but status not connected")
            elif not config_configured and status_connected:
                self.log("   ⚠️ INCONSISTENCY: Status says connected but config not configured")
            else:
                self.log("   ❌ Both endpoints agree: system is NOT configured")
            
            return True
        else:
            self.log("❌ Failed to get responses from both endpoints")
            return False

    def test_frontend_expectations(self):
        """Test what the frontend might be expecting"""
        self.log("🎯 Testing Frontend Expectations")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        
        response = requests.get(f"{self.api_url}/gdrive/config", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            self.log("🔍 FRONTEND EXPECTATION ANALYSIS:")
            
            # Common frontend patterns for checking if configured
            patterns = [
                ("data.configured === true", data.get('configured') is True),
                ("data.configured && data.folder_id", data.get('configured') and data.get('folder_id')),
                ("data.configured && data.apps_script_url", data.get('configured') and data.get('apps_script_url')),
                ("data.auth_method === 'apps_script'", data.get('auth_method') == 'apps_script'),
                ("data.folder_id && data.apps_script_url", data.get('folder_id') and data.get('apps_script_url')),
                ("typeof data.apps_script_url === 'string'", isinstance(data.get('apps_script_url'), str)),
            ]
            
            for pattern, result in patterns:
                status = "✅ PASS" if result else "❌ FAIL"
                self.log(f"   {pattern}: {status}")
            
            # The key issue might be here
            if isinstance(data.get('apps_script_url'), bool):
                self.log("\n🚨 CRITICAL FINDING:")
                self.log("   The apps_script_url field is boolean (True) instead of the actual URL string")
                self.log("   Frontend might be checking: if (config.apps_script_url && typeof config.apps_script_url === 'string')")
                self.log("   This would fail because True is not a string")
                
            return True
        else:
            self.log("❌ Failed to get config response")
            return False

    def run_analysis(self):
        """Run the complete analysis"""
        self.log("🔍 DETAILED GOOGLE DRIVE CONFIGURATION ANALYSIS")
        self.log("=" * 80)
        
        if not self.authenticate():
            return False
        
        # Step 1: Analyze config response
        success, config_data = self.analyze_config_response()
        if not success:
            return False
        
        # Step 2: Compare with status endpoint
        self.compare_with_status_endpoint()
        
        # Step 3: Test frontend expectations
        self.test_frontend_expectations()
        
        # Final conclusion
        self.log("=" * 80)
        self.log("🎯 FINAL CONCLUSION")
        self.log("=" * 80)
        
        if config_data and isinstance(config_data.get('apps_script_url'), bool):
            self.log("❌ ROOT CAUSE IDENTIFIED:")
            self.log("   The GET /api/gdrive/config endpoint returns apps_script_url as boolean (True)")
            self.log("   instead of the actual Apps Script URL string.")
            self.log("   Frontend likely expects the actual URL string to display configuration status.")
            self.log("")
            self.log("🔧 RECOMMENDED FIX:")
            self.log("   Modify the backend GET /api/gdrive/config endpoint to return the actual")
            self.log("   Apps Script URL string instead of just True/False.")
            return False
        else:
            self.log("✅ No obvious issues found in the configuration response structure.")
            self.log("   The issue might be in the frontend logic or timing.")
            return True

def main():
    analyzer = DetailedConfigAnalyzer()
    success = analyzer.run_analysis()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())