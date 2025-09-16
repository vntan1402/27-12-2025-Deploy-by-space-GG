#!/usr/bin/env python3
"""
AI Configuration Testing Script
Tests the AI configuration system and available providers as requested in the review.
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone

class AIConfigTester:
    def __init__(self, base_url="https://ship-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_info = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self, username="admin", password="admin123"):
        """Test login and get token"""
        print(f"\n🔐 Testing Authentication with {username}/{password}")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_info = response.get('user', {})
            print(f"✅ Login successful, token obtained")
            print(f"   User: {self.user_info.get('full_name')} ({self.user_info.get('role')})")
            print(f"   Company: {self.user_info.get('company', 'N/A')}")
            return True
        return False

    def test_ai_config_get(self):
        """Test GET /api/ai-config endpoint"""
        print(f"\n🤖 Testing AI Configuration - GET")
        success, config = self.run_test(
            "Get AI Configuration",
            "GET",
            "ai-config",
            200
        )
        
        if success:
            print(f"   Current AI Config:")
            if config:
                for key, value in config.items():
                    if key == 'api_key':
                        # Mask API key for security
                        masked_key = value[:8] + "..." + value[-4:] if value and len(value) > 12 else "***"
                        print(f"     {key}: {masked_key}")
                    else:
                        print(f"     {key}: {value}")
            else:
                print(f"     No AI configuration found")
            return config
        return None

    def test_ai_providers_available(self):
        """Test what AI providers are available in the system"""
        print(f"\n🔍 Testing Available AI Providers")
        
        # Check environment variables for API keys
        print(f"   Checking Environment Variables:")
        
        # Check for OpenAI
        openai_key = os.environ.get('OPENAI_API_KEY')
        print(f"     OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Not set'}")
        if openai_key:
            print(f"       Key preview: {openai_key[:8]}...{openai_key[-4:] if len(openai_key) > 12 else '***'}")
        
        # Check for Anthropic
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
        print(f"     ANTHROPIC_API_KEY: {'✅ Set' if anthropic_key else '❌ Not set'}")
        if anthropic_key:
            print(f"       Key preview: {anthropic_key[:8]}...{anthropic_key[-4:] if len(anthropic_key) > 12 else '***'}")
        
        # Check for Google
        google_key = os.environ.get('GOOGLE_API_KEY')
        print(f"     GOOGLE_API_KEY: {'✅ Set' if google_key else '❌ Not set'}")
        if google_key:
            print(f"       Key preview: {google_key[:8]}...{google_key[-4:] if len(google_key) > 12 else '***'}")
        
        # Check for Emergent LLM
        emergent_key = os.environ.get('EMERGENT_LLM_KEY')
        print(f"     EMERGENT_LLM_KEY: {'✅ Set' if emergent_key else '❌ Not set'}")
        if emergent_key:
            print(f"       Key preview: {emergent_key[:8]}...{emergent_key[-4:] if len(emergent_key) > 12 else '***'}")
        
        # Test if there's an endpoint for available providers
        success, providers = self.run_test(
            "Get Available AI Providers",
            "GET",
            "ai-providers",
            200
        )
        
        if success:
            print(f"   Available Providers from API:")
            if providers:
                for provider in providers:
                    print(f"     - {provider}")
            else:
                print(f"     No providers returned from API")
        else:
            print(f"   No ai-providers endpoint available")
        
        return {
            'openai': bool(openai_key),
            'anthropic': bool(anthropic_key),
            'google': bool(google_key),
            'emergent': bool(emergent_key)
        }

    def test_ai_config_structure(self):
        """Test AI config structure and available options"""
        print(f"\n📋 Testing AI Configuration Structure")
        
        # Test different provider configurations
        test_configs = [
            {
                "name": "OpenAI GPT-4",
                "config": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "api_key": "test-key-openai"
                }
            },
            {
                "name": "Anthropic Claude",
                "config": {
                    "provider": "anthropic", 
                    "model": "claude-3-sonnet",
                    "api_key": "test-key-anthropic"
                }
            },
            {
                "name": "Google Gemini",
                "config": {
                    "provider": "google",
                    "model": "gemini-pro",
                    "api_key": "test-key-google"
                }
            }
        ]
        
        results = []
        for test_config in test_configs:
            print(f"\n   Testing {test_config['name']} Configuration:")
            success, response = self.run_test(
                f"Set AI Config - {test_config['name']}",
                "POST",
                "ai-config",
                200,
                data=test_config['config']
            )
            
            if success:
                print(f"     ✅ Configuration accepted")
                # Verify the configuration was saved
                success_get, saved_config = self.run_test(
                    f"Verify AI Config - {test_config['name']}",
                    "GET",
                    "ai-config",
                    200
                )
                if success_get:
                    print(f"     ✅ Configuration saved and retrieved")
                    print(f"       Provider: {saved_config.get('provider', 'N/A')}")
                    print(f"       Model: {saved_config.get('model', 'N/A')}")
                results.append(True)
            else:
                print(f"     ❌ Configuration rejected")
                results.append(False)
        
        return results

    def test_ai_config_permissions(self):
        """Test AI config permissions (should be Super Admin only)"""
        print(f"\n🔒 Testing AI Configuration Permissions")
        
        current_role = self.user_info.get('role', 'unknown')
        print(f"   Current user role: {current_role}")
        
        if current_role == 'super_admin':
            print(f"   ✅ Super Admin should have access to AI config")
            expected_status = 200
        else:
            print(f"   ⚠️ Non-Super Admin should be denied access")
            expected_status = 403
        
        # Test GET permissions
        success, config = self.run_test(
            "Test AI Config GET Permissions",
            "GET",
            "ai-config",
            expected_status
        )
        
        # Test POST permissions
        test_config = {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "test-permission-key"
        }
        
        success_post, response = self.run_test(
            "Test AI Config POST Permissions",
            "POST",
            "ai-config",
            expected_status,
            data=test_config
        )
        
        return success and success_post

    def test_current_ai_system(self):
        """Test the current AI system being used"""
        print(f"\n🔬 Testing Current AI System Usage")
        
        # Check if there's a PDF analysis endpoint (mentioned in review)
        success, response = self.run_test(
            "Test PDF Analysis Endpoint",
            "GET",
            "analyze-ship-certificate",
            405  # Method not allowed for GET, but endpoint should exist
        )
        
        if not success:
            # Try with different status codes
            success, response = self.run_test(
                "Test PDF Analysis Endpoint (404 check)",
                "GET",
                "analyze-ship-certificate",
                404
            )
        
        # Check for AI analysis endpoints
        ai_endpoints = [
            "ai/analyze",
            "ai/search", 
            "analyze-document-with-ai",
            "analyze-ship-certificate"
        ]
        
        working_endpoints = []
        for endpoint in ai_endpoints:
            success, response = self.run_test(
                f"Check AI Endpoint - {endpoint}",
                "GET",
                endpoint,
                [200, 405, 422]  # Accept multiple status codes
            )
            if success:
                working_endpoints.append(endpoint)
        
        print(f"   Working AI endpoints: {working_endpoints}")
        return working_endpoints

    def run_comprehensive_test(self):
        """Run comprehensive AI configuration testing"""
        print("🤖 AI Configuration System Testing")
        print("=" * 60)
        
        # Test 1: Login as admin/admin123
        if not self.test_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Test 2: Check what AI config exists in database
        current_config = self.test_ai_config_get()
        
        # Test 3: Check what AI providers are available
        available_providers = self.test_ai_providers_available()
        
        # Test 4: Test AI config structure and options
        structure_results = self.test_ai_config_structure()
        
        # Test 5: Test permissions
        permission_result = self.test_ai_config_permissions()
        
        # Test 6: Test current AI system
        current_system = self.test_current_ai_system()
        
        # Print comprehensive summary
        print("\n" + "=" * 60)
        print("📊 AI CONFIGURATION TEST SUMMARY")
        print("=" * 60)
        
        print(f"\n1. AUTHENTICATION:")
        print(f"   ✅ Login successful as {self.user_info.get('username')} ({self.user_info.get('role')})")
        
        print(f"\n2. CURRENT AI CONFIGURATION:")
        if current_config:
            print(f"   ✅ AI config exists in database")
            for key, value in current_config.items():
                if key == 'api_key':
                    masked_key = value[:8] + "..." + value[-4:] if value and len(value) > 12 else "***"
                    print(f"     {key}: {masked_key}")
                else:
                    print(f"     {key}: {value}")
        else:
            print(f"   ⚠️ No AI configuration found in database")
        
        print(f"\n3. AVAILABLE AI PROVIDERS:")
        for provider, available in available_providers.items():
            status = "✅ Available" if available else "❌ Not configured"
            print(f"   {provider.upper()}: {status}")
        
        print(f"\n4. AI CONFIG STRUCTURE TESTS:")
        structure_passed = sum(structure_results)
        structure_total = len(structure_results)
        print(f"   Configuration tests: {structure_passed}/{structure_total} passed")
        
        print(f"\n5. PERMISSION TESTING:")
        print(f"   Permission check: {'✅ Passed' if permission_result else '❌ Failed'}")
        
        print(f"\n6. CURRENT AI SYSTEM:")
        if current_system:
            print(f"   Working AI endpoints found: {len(current_system)}")
            for endpoint in current_system:
                print(f"     - {endpoint}")
        else:
            print(f"   ⚠️ No working AI endpoints found")
        
        print(f"\nOVERALL API TESTS: {self.tests_passed}/{self.tests_run}")
        
        # Determine if we need to switch from Emergent LLM
        emergent_in_use = current_config and current_config.get('provider') == 'emergent'
        system_has_other_keys = any([available_providers.get('openai'), 
                                   available_providers.get('anthropic'), 
                                   available_providers.get('google')])
        
        print(f"\n🔄 RECOMMENDATION FOR SWITCHING FROM EMERGENT LLM:")
        if emergent_in_use:
            print(f"   Current system is using Emergent LLM")
        else:
            print(f"   Current system is not using Emergent LLM")
        
        if system_has_other_keys:
            print(f"   ✅ System has other AI provider keys configured")
            print(f"   💡 Can switch to system AI config instead of hardcoded Emergent LLM")
        else:
            print(f"   ⚠️ No other AI provider keys found in system")
            print(f"   💡 Need to configure AI provider keys before switching")
        
        return True

def main():
    """Main test execution"""
    tester = AIConfigTester()
    
    try:
        success = tester.run_comprehensive_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())