#!/usr/bin/env python3
"""
AI Response Debug Test - Deep dive into AI response parsing
"""

import requests
import sys
import json
import os
import tempfile
from datetime import datetime, timezone
import time

class AIResponseDebugTester:
    def __init__(self, base_url="https://ship-manager-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        
        # Test PDF URL from the review request
        self.test_pdf_url = "https://customer-assets.emergentagent.com/job_vessel-docs-1/artifacts/xs4c3jhi_BROTHER%2036%20-EIAPP-PM242757.pdf"
        self.expected_ship_name = "BROTHER 36"

    def authenticate(self):
        """Authenticate and get token"""
        response = requests.post(
            f"{self.api_url}/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            print(f"✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False

    def download_pdf(self):
        """Download the test PDF"""
        response = requests.get(self.test_pdf_url, timeout=30)
        
        if response.status_code == 200:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(response.content)
            temp_file.close()
            print(f"✅ PDF downloaded: {len(response.content)} bytes")
            return temp_file.name
        else:
            print(f"❌ PDF download failed: {response.status_code}")
            return None

    def test_ai_analysis_with_debug(self, pdf_path):
        """Test AI analysis with detailed debugging"""
        print(f"\n🔍 Testing AI Analysis with Debug Info")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        with open(pdf_path, 'rb') as pdf_file:
            files = {'file': ('BROTHER_36_EIAPP.pdf', pdf_file, 'application/pdf')}
            
            # Make the request
            response = requests.post(
                f"{self.api_url}/analyze-ship-certificate",
                files=files,
                headers=headers,
                timeout=120
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"\n📋 Full API Response:")
                    print(json.dumps(data, indent=2, default=str))
                    
                    # Check the analysis field specifically
                    analysis = data.get('analysis', {})
                    ship_name = analysis.get('ship_name')
                    
                    print(f"\n🔍 Analysis Details:")
                    print(f"Ship Name: {repr(ship_name)} (type: {type(ship_name)})")
                    print(f"IMO Number: {repr(analysis.get('imo_number'))}")
                    print(f"Flag: {repr(analysis.get('flag'))}")
                    print(f"Built Year: {repr(analysis.get('built_year'))}")
                    
                    # Check if ship name is correct
                    if ship_name == self.expected_ship_name:
                        print(f"✅ Ship name correctly extracted: '{ship_name}'")
                        return True
                    elif ship_name is None:
                        print(f"❌ Ship name is None - AI parsing issue")
                        return False
                    else:
                        print(f"❌ Ship name incorrect: expected '{self.expected_ship_name}', got '{ship_name}'")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    print(f"Raw response: {response.text}")
                    return False
            else:
                print(f"❌ API request failed")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Raw error response: {response.text}")
                return False

    def check_backend_logs_for_ai_response(self):
        """Check backend logs to see the actual AI response"""
        print(f"\n📋 Checking Backend Logs for AI Response")
        
        try:
            import subprocess
            
            # Get recent logs that contain AI response
            result = subprocess.run(
                ['grep', '-A', '10', '-B', '5', 'AI Response content', '/var/log/supervisor/backend.out.log'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                print(f"   AI Response from logs:")
                print(result.stdout)
                return True
            else:
                print(f"   No AI response found in logs")
                
                # Try to get general backend logs
                result2 = subprocess.run(
                    ['tail', '-n', '30', '/var/log/supervisor/backend.out.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result2.returncode == 0:
                    print(f"   Recent backend logs:")
                    print(result2.stdout)
                
                return False
                
        except Exception as e:
            print(f"   Error reading logs: {str(e)}")
            return False

    def run_debug_test(self):
        """Run the complete debug test"""
        print("🔍 AI Response Debug Test")
        print("=" * 50)
        
        # Step 1: Authentication
        if not self.authenticate():
            return False
        
        # Step 2: Download PDF
        pdf_path = self.download_pdf()
        if not pdf_path:
            return False
        
        try:
            # Step 3: Test AI analysis with debug
            success = self.test_ai_analysis_with_debug(pdf_path)
            
            # Step 4: Check backend logs
            self.check_backend_logs_for_ai_response()
            
            return success
            
        finally:
            # Clean up
            try:
                os.unlink(pdf_path)
                print(f"   Cleaned up: {pdf_path}")
            except:
                pass

def main():
    """Main execution"""
    tester = AIResponseDebugTester()
    
    success = tester.run_debug_test()
    
    if success:
        print("\n🎉 AI response debug completed - ship name extraction working!")
        return 0
    else:
        print("\n⚠️ AI response debug found issues with ship name extraction")
        return 1

if __name__ == "__main__":
    sys.exit(main())