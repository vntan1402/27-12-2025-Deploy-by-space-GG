#!/usr/bin/env python3
"""
Simple AI Configuration Testing Script
Tests the AI configuration system without PDF creation
"""

import requests
import sys
import json

class SimpleAITester:
    def __init__(self, base_url="https://ship-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None

    def test_login(self, username="admin", password="admin123"):
        """Test login and get token"""
        print(f"🔐 Testing Authentication with {username}/{password}")
        
        response = requests.post(
            f"{self.api_url}/auth/login",
            json={"username": username, "password": password},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            user_info = data.get('user', {})
            print(f"✅ Login successful")
            print(f"   User: {user_info.get('full_name')} ({user_info.get('role')})")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False

    def test_current_ai_config(self):
        """Test current AI configuration"""
        print(f"\n⚙️ Testing Current AI Configuration")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{self.api_url}/ai-config",
                headers=headers,
                timeout=30
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                config = response.json()
                print("✅ Current AI Configuration:")
                for key, value in config.items():
                    if key == 'api_key':
                        masked_key = value[:8] + "..." + value[-4:] if value and len(value) > 12 else "***"
                        print(f"     {key}: {masked_key}")
                    else:
                        print(f"     {key}: {value}")
                return config
            else:
                print(f"❌ Failed to get AI config")
                try:
                    error = response.json()
                    print(f"   Error: {error}")
                except:
                    print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None

    def test_set_emergent_config(self):
        """Test setting Emergent LLM configuration"""
        print(f"\n🔧 Testing Set Emergent LLM Configuration")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Test setting Emergent LLM config
        emergent_config = {
            "provider": "emergent",
            "model": "gemini-2.0-flash",
            "api_key": "sk-emergent-eEe35Fb1b449940199"
        }
        
        print("🔍 Setting Emergent LLM configuration...")
        
        try:
            response = requests.post(
                f"{self.api_url}/ai-config",
                json=emergent_config,
                headers=headers,
                timeout=30
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Emergent LLM config set successfully!")
                return True
            else:
                print(f"❌ Failed to set Emergent LLM config")
                try:
                    error = response.json()
                    print(f"   Error: {error}")
                except:
                    print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False

    def test_other_providers(self):
        """Test setting other AI provider configurations"""
        print(f"\n🔄 Testing Other AI Provider Configurations")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        providers = [
            {
                "name": "OpenAI",
                "config": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "api_key": "test-openai-key"
                }
            },
            {
                "name": "Anthropic",
                "config": {
                    "provider": "anthropic",
                    "model": "claude-3-sonnet",
                    "api_key": "test-anthropic-key"
                }
            },
            {
                "name": "Google",
                "config": {
                    "provider": "google",
                    "model": "gemini-pro",
                    "api_key": "test-google-key"
                }
            }
        ]
        
        results = []
        for provider in providers:
            print(f"\n   Testing {provider['name']} Configuration:")
            
            try:
                response = requests.post(
                    f"{self.api_url}/ai-config",
                    json=provider['config'],
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    print(f"     ✅ {provider['name']} config accepted")
                    results.append(True)
                else:
                    print(f"     ❌ {provider['name']} config rejected")
                    results.append(False)
                    
            except Exception as e:
                print(f"     ❌ {provider['name']} test failed: {e}")
                results.append(False)
        
        return results

    def test_pdf_analysis_endpoint_availability(self):
        """Test if PDF analysis endpoint is available"""
        print(f"\n📄 Testing PDF Analysis Endpoint Availability")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        
        # Test with GET (should return 405 Method Not Allowed)
        try:
            response = requests.get(
                f"{self.api_url}/analyze-ship-certificate",
                headers=headers,
                timeout=30
            )
            
            print(f"   GET Response Status: {response.status_code}")
            
            if response.status_code == 405:
                print("✅ PDF Analysis endpoint exists (Method Not Allowed for GET is expected)")
                return True
            elif response.status_code == 404:
                print("❌ PDF Analysis endpoint not found")
                return False
            else:
                print(f"⚠️ Unexpected response: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False

def main():
    """Main test execution"""
    print("🤖 Simple AI Configuration Testing")
    print("=" * 50)
    
    tester = SimpleAITester()
    
    # Test authentication
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Test current AI config
    current_config = tester.test_current_ai_config()
    
    # Test setting Emergent LLM config
    emergent_success = tester.test_set_emergent_config()
    
    # Test other providers
    other_providers_results = tester.test_other_providers()
    
    # Test PDF analysis endpoint availability
    pdf_endpoint_available = tester.test_pdf_analysis_endpoint_availability()
    
    # Print comprehensive results
    print("\n" + "=" * 50)
    print("📊 AI CONFIGURATION TEST RESULTS")
    print("=" * 50)
    
    print(f"\n1. CURRENT AI CONFIG:")
    if current_config:
        print(f"   ✅ AI config exists in database")
        print(f"   Provider: {current_config.get('provider', 'N/A')}")
        print(f"   Model: {current_config.get('model', 'N/A')}")
    else:
        print(f"   ⚠️ No AI configuration found")
    
    print(f"\n2. EMERGENT LLM CONFIG:")
    print(f"   {'✅ PASSED' if emergent_success else '❌ FAILED'}")
    
    print(f"\n3. OTHER PROVIDERS:")
    provider_names = ["OpenAI", "Anthropic", "Google"]
    for i, result in enumerate(other_providers_results):
        print(f"   {provider_names[i]}: {'✅ PASSED' if result else '❌ FAILED'}")
    
    print(f"\n4. PDF ANALYSIS ENDPOINT:")
    print(f"   {'✅ AVAILABLE' if pdf_endpoint_available else '❌ NOT AVAILABLE'}")
    
    # Summary and recommendations
    print(f"\n🔄 RECOMMENDATIONS:")
    
    if current_config and current_config.get('provider') == 'emergent':
        print(f"   ✅ System is already configured to use Emergent LLM")
    elif emergent_success:
        print(f"   ✅ System can be configured to use Emergent LLM")
        print(f"   💡 Switch analyze_document_with_ai function to use system AI config")
    else:
        print(f"   ⚠️ Emergent LLM configuration failed")
    
    if any(other_providers_results):
        print(f"   ✅ System supports multiple AI providers")
        print(f"   💡 Can switch from hardcoded Emergent LLM to configurable system")
    
    if pdf_endpoint_available:
        print(f"   ✅ PDF analysis functionality is available")
        print(f"   💡 Currently uses hardcoded EMERGENT_LLM_KEY")
        print(f"   💡 Should be modified to use system AI config instead")
    
    total_tests = 1 + len(other_providers_results) + 1 + 1  # emergent + others + pdf + current
    passed_tests = sum([emergent_success] + other_providers_results + [pdf_endpoint_available, bool(current_config)])
    
    print(f"\nOVERALL: {passed_tests}/{total_tests} tests passed")
    
    return 0 if passed_tests >= total_tests - 1 else 1  # Allow 1 failure

if __name__ == "__main__":
    sys.exit(main())