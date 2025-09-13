#!/usr/bin/env python3
"""
Missing Endpoints Detection Test
Identifies which endpoints are missing from the MongoDB backend implementation
"""

import requests
import sys
import json

class MissingEndpointsDetector:
    def __init__(self, base_url="https://ship-management.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.missing_endpoints = []
        self.working_endpoints = []

    def authenticate(self):
        """Get authentication token"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                print(f"✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def test_endpoint(self, method, endpoint, description):
        """Test if an endpoint exists"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json={}, headers=headers, timeout=10)
            
            if response.status_code == 404:
                self.missing_endpoints.append({
                    'method': method,
                    'endpoint': endpoint,
                    'description': description,
                    'url': url
                })
                print(f"❌ MISSING: {method} {endpoint} - {description}")
                return False
            else:
                self.working_endpoints.append({
                    'method': method,
                    'endpoint': endpoint,
                    'description': description,
                    'status': response.status_code
                })
                print(f"✅ EXISTS: {method} {endpoint} - {description} (Status: {response.status_code})")
                return True
                
        except Exception as e:
            print(f"⚠️ ERROR: {method} {endpoint} - {e}")
            return False

    def detect_missing_endpoints(self):
        """Detect all missing endpoints based on frontend requirements"""
        print("🔍 Detecting Missing Endpoints")
        print("=" * 50)
        
        if not self.authenticate():
            return False
        
        # Test all expected endpoints based on frontend functionality
        endpoints_to_test = [
            # Authentication endpoints
            ('POST', 'auth/login', 'User login'),
            ('POST', 'auth/register', 'User registration'),
            
            # User management
            ('GET', 'users', 'Get all users'),
            ('POST', 'users', 'Create user'),
            ('PUT', 'users/test-id', 'Update user'),
            ('DELETE', 'users/test-id', 'Delete user'),
            
            # Company management
            ('GET', 'companies', 'Get all companies'),
            ('POST', 'companies', 'Create company'),
            ('PUT', 'companies/test-id', 'Update company'),
            ('DELETE', 'companies/test-id', 'Delete company'),
            
            # Ship management
            ('GET', 'ships', 'Get all ships'),
            ('POST', 'ships', 'Create ship'),
            ('PUT', 'ships/test-id', 'Update ship'),
            ('DELETE', 'ships/test-id', 'Delete ship'),
            
            # Certificate management
            ('GET', 'certificates', 'Get all certificates'),
            ('POST', 'certificates', 'Create certificate'),
            ('PUT', 'certificates/test-id', 'Update certificate'),
            ('DELETE', 'certificates/test-id', 'Delete certificate'),
            
            # AI Configuration
            ('GET', 'ai-config', 'Get AI configuration'),
            ('POST', 'ai-config', 'Update AI configuration'),
            
            # Usage tracking
            ('GET', 'usage-stats', 'Get usage statistics'),
            ('GET', 'usage-tracking', 'Get usage tracking data'),
            
            # Google Drive
            ('GET', 'gdrive/config', 'Get Google Drive config'),
            ('GET', 'gdrive/status', 'Get Google Drive status'),
            ('POST', 'gdrive/configure', 'Configure Google Drive'),
            ('POST', 'gdrive/test', 'Test Google Drive connection'),
            
            # Settings
            ('GET', 'settings', 'Get system settings'),
            ('POST', 'settings', 'Update system settings'),
            
            # AI Features
            ('POST', 'ai/analyze', 'AI document analysis'),
            ('GET', 'ai/search', 'AI smart search'),
        ]
        
        print(f"\nTesting {len(endpoints_to_test)} endpoints...\n")
        
        for method, endpoint, description in endpoints_to_test:
            self.test_endpoint(method, endpoint, description)
        
        return True

    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "=" * 60)
        print("📊 MISSING ENDPOINTS DETECTION REPORT")
        print("=" * 60)
        
        print(f"\n✅ WORKING ENDPOINTS: {len(self.working_endpoints)}")
        for endpoint in self.working_endpoints:
            print(f"   {endpoint['method']} {endpoint['endpoint']} (Status: {endpoint['status']})")
        
        print(f"\n❌ MISSING ENDPOINTS: {len(self.missing_endpoints)}")
        for endpoint in self.missing_endpoints:
            print(f"   {endpoint['method']} {endpoint['endpoint']} - {endpoint['description']}")
        
        if self.missing_endpoints:
            print(f"\n🚨 CRITICAL FINDINGS:")
            print(f"   - {len(self.missing_endpoints)} endpoints are missing from the backend")
            print(f"   - This explains why frontend shows 'no content' in various sections")
            print(f"   - Frontend is making requests to non-existent endpoints")
            
            # Categorize missing endpoints
            missing_categories = {}
            for endpoint in self.missing_endpoints:
                category = endpoint['endpoint'].split('/')[0]
                if category not in missing_categories:
                    missing_categories[category] = []
                missing_categories[category].append(endpoint)
            
            print(f"\n📋 MISSING ENDPOINTS BY CATEGORY:")
            for category, endpoints in missing_categories.items():
                print(f"   {category.upper()}: {len(endpoints)} missing")
                for ep in endpoints:
                    print(f"     - {ep['method']} {ep['endpoint']}")
        else:
            print(f"\n🎉 All expected endpoints are available!")
        
        return len(self.missing_endpoints) == 0

def main():
    detector = MissingEndpointsDetector()
    detector.detect_missing_endpoints()
    success = detector.generate_report()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())