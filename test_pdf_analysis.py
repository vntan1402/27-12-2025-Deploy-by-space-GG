#!/usr/bin/env python3
"""
Test PDF Analysis Endpoint with Emergent LLM
"""

import requests
import sys
import json
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class PDFAnalysisTester:
    def __init__(self, base_url="https://shipmanage.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None

    def create_test_pdf(self):
        """Create a simple test PDF with ship information"""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add ship certificate content
        p.drawString(100, 750, "SHIP CERTIFICATE")
        p.drawString(100, 720, "Ship Name: MV TEST VESSEL")
        p.drawString(100, 690, "IMO Number: 1234567")
        p.drawString(100, 660, "Flag: Panama")
        p.drawString(100, 630, "Gross Tonnage: 50000")
        p.drawString(100, 600, "Built Year: 2020")
        p.drawString(100, 570, "Ship Owner: Test Maritime Company")
        p.drawString(100, 540, "Class Society: DNV GL")
        
        p.save()
        buffer.seek(0)
        return buffer

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

    def test_pdf_analysis(self):
        """Test PDF analysis endpoint"""
        print(f"\n📄 Testing PDF Analysis with Emergent LLM")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        # Create test PDF
        try:
            pdf_buffer = self.create_test_pdf()
            print("✅ Test PDF created successfully")
        except Exception as e:
            print(f"❌ Failed to create test PDF: {e}")
            return False
        
        # Prepare file upload
        files = {
            'file': ('test_certificate.pdf', pdf_buffer, 'application/pdf')
        }
        
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        
        print("🔍 Sending PDF to analysis endpoint...")
        
        try:
            response = requests.post(
                f"{self.api_url}/analyze-ship-certificate",
                files=files,
                headers=headers,
                timeout=60  # Longer timeout for AI processing
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ PDF Analysis successful!")
                print("   Analysis Results:")
                
                analysis = result.get('analysis', {})
                for field, value in analysis.items():
                    print(f"     {field}: {value}")
                
                return True
            else:
                print(f"❌ PDF Analysis failed")
                try:
                    error = response.json()
                    print(f"   Error: {error}")
                except:
                    print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False

    def test_ai_config_with_emergent(self):
        """Test if we can configure the system to use Emergent LLM through AI config"""
        print(f"\n⚙️ Testing AI Config with Emergent LLM")
        
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
                
                # Verify the config was saved
                get_response = requests.get(
                    f"{self.api_url}/ai-config",
                    headers=headers,
                    timeout=30
                )
                
                if get_response.status_code == 200:
                    config = get_response.json()
                    print("   Current AI Config:")
                    for key, value in config.items():
                        if key == 'api_key':
                            masked_key = value[:8] + "..." + value[-4:] if value and len(value) > 12 else "***"
                            print(f"     {key}: {masked_key}")
                        else:
                            print(f"     {key}: {value}")
                
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

def main():
    """Main test execution"""
    print("🤖 PDF Analysis with Emergent LLM Testing")
    print("=" * 50)
    
    tester = PDFAnalysisTester()
    
    # Test authentication
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Test AI config with Emergent
    config_success = tester.test_ai_config_with_emergent()
    
    # Test PDF analysis
    analysis_success = tester.test_pdf_analysis()
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"AI Config Test: {'✅ PASSED' if config_success else '❌ FAILED'}")
    print(f"PDF Analysis Test: {'✅ PASSED' if analysis_success else '❌ FAILED'}")
    
    if config_success and analysis_success:
        print("\n🎉 All tests passed! Emergent LLM is working correctly.")
        print("💡 The system can use Emergent LLM through the AI config instead of hardcoded keys.")
        return 0
    else:
        print("\n⚠️ Some tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())