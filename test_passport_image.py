#!/usr/bin/env python3
"""
Test passport analysis with proper image file format
"""

import requests
import json
import os
import sys
from datetime import datetime
import tempfile
import base64

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://crewdocs-ai.preview.emergentagent.com') + '/api'

def create_test_passport_image():
    """Create a simple test image file that Document AI can process"""
    # Create a simple HTML file that can be converted to PDF
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Passport</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .passport { border: 2px solid black; padding: 20px; width: 400px; }
            .field { margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="passport">
            <h2>PASSPORT</h2>
            <h3>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</h3>
            
            <div class="field">Surname: NGUYEN</div>
            <div class="field">Given Names: VAN MINH</div>
            <div class="field">Passport No: C1571189</div>
            <div class="field">Date of Birth: February 14, 1983 (14/02/1983)</div>
            <div class="field">Sex: M</div>
            <div class="field">Place of Birth: Ho Chi Minh City, Vietnam</div>
            <div class="field">Nationality: VIETNAMESE</div>
            <div class="field">Date of Issue: March 15, 2020 (15/03/2020)</div>
            <div class="field">Date of Expiry: March 14, 2030 (14/03/2030)</div>
        </div>
    </body>
    </html>
    """
    
    # Save as HTML file (which Document AI can process)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
        temp_file.write(html_content)
        return temp_file.name

def authenticate():
    """Authenticate with admin1/123456 credentials"""
    try:
        login_data = {
            "username": "admin1",
            "password": "123456",
            "remember_me": False
        }
        
        endpoint = f"{BACKEND_URL}/auth/login"
        response = requests.post(endpoint, json=login_data, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"Authentication failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return None

def test_passport_with_image():
    """Test passport analysis with proper image file"""
    try:
        print("🔐 Authenticating...")
        auth_token = authenticate()
        if not auth_token:
            print("❌ Authentication failed")
            return False
        
        print("✅ Authentication successful")
        
        # Create test passport image
        print("📄 Creating test passport file...")
        test_file_path = create_test_passport_image()
        
        try:
            # Test passport analysis endpoint
            endpoint = f"{BACKEND_URL}/crew/analyze-passport"
            print(f"📡 POST {endpoint}")
            
            # Prepare multipart form data with HTML file
            files = {
                'passport_file': ('test_passport.html', open(test_file_path, 'rb'), 'text/html')
            }
            data = {
                'ship_name': 'BROTHER 36'
            }
            
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            response = requests.post(
                endpoint, 
                files=files, 
                data=data, 
                headers=headers, 
                timeout=60
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Passport analysis endpoint working")
                
                try:
                    response_data = response.json()
                    print(f"Response: {json.dumps(response_data, indent=2)}")
                    
                    if response_data.get('success'):
                        analysis = response_data.get('analysis', {})
                        
                        print("\n📋 EXTRACTED DATE FIELDS:")
                        date_fields = ['date_of_birth', 'issue_date', 'expiry_date']
                        
                        for field in date_fields:
                            date_value = analysis.get(field, '')
                            print(f"   {field}: '{date_value}'")
                            
                            # Check if date is in clean DD/MM/YYYY format
                            if date_value and '/' in date_value and len(date_value.split('/')) == 3:
                                print(f"      ✅ Clean DD/MM/YYYY format detected")
                            elif date_value and ('February' in date_value or 'March' in date_value):
                                print(f"      ❌ Verbose date format detected - standardization may be needed")
                            elif not date_value:
                                print(f"      ⚠️ Empty date field")
                        
                        return True
                    else:
                        print(f"❌ Analysis failed: {response_data.get('error', 'Unknown error')}")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON response: {str(e)}")
                    return False
                    
            else:
                print(f"❌ Request failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"Error: {response.text[:200]}")
                return False
                
        finally:
            # Clean up temporary file
            try:
                files['passport_file'][1].close()
                os.unlink(test_file_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Error testing passport with image: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 TESTING PASSPORT ANALYSIS WITH PROPER FILE FORMAT")
    print("=" * 60)
    
    success = test_passport_with_image()
    
    if success:
        print("\n✅ TEST COMPLETED SUCCESSFULLY")
    else:
        print("\n❌ TEST FAILED")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()