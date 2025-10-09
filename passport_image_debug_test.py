#!/usr/bin/env python3
"""
PASSPORT DATE OF BIRTH DEBUG TEST - WITH PROPER IMAGE FILE

This test creates a proper image-based passport file to test the Document AI integration
and debug the date_of_birth field issue.
"""

import requests
import json
import os
import sys
import tempfile
import base64
from datetime import datetime
import traceback
from PIL import Image, ImageDraw, ImageFont
import io

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://crewdocs-ai.preview.emergentagent.com') + '/api'
print(f"Using backend URL: {BACKEND_URL}")

class PassportImageDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
    def authenticate(self):
        """Authenticate with admin1/123456 credentials"""
        try:
            self.log("🔐 Authenticating with admin1/123456...")
            
            login_data = {
                "username": "admin1",
                "password": "123456",
                "remember_me": False
            }
            
            endpoint = f"{BACKEND_URL}/auth/login"
            response = requests.post(endpoint, json=login_data, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User: {self.current_user.get('username')}")
                self.log(f"   Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def create_passport_image(self):
        """Create a simple passport-like image with text"""
        try:
            self.log("🖼️ Creating passport image...")
            
            # Create a white image
            width, height = 800, 1200
            image = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(image)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw passport header
            draw.text((50, 50), "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", fill='black', font=font_medium)
            draw.text((50, 80), "SOCIALIST REPUBLIC OF VIETNAM", fill='black', font=font_small)
            draw.text((50, 120), "HỘ CHIẾU / PASSPORT", fill='black', font=font_large)
            
            # Draw passport information
            y_pos = 200
            passport_data = [
                ("Họ và tên / Surname and given names:", "VŨ NGỌC TÂN"),
                ("Ngày sinh / Date of birth:", "14/02/1983"),
                ("Nơi sinh / Place of birth:", "HẢI PHÒNG"),
                ("Giới tính / Sex:", "M / Nam"),
                ("Quốc tịch / Nationality:", "VIỆT NAM / VIETNAMESE"),
                ("Số hộ chiếu / Passport No.:", "C1571189"),
                ("Ngày cấp / Date of issue:", "15/03/2020"),
                ("Ngày hết hạn / Date of expiry:", "14/03/2030"),
                ("Nơi cấp / Place of issue:", "HÀ NỘI")
            ]
            
            for label, value in passport_data:
                draw.text((50, y_pos), label, fill='black', font=font_small)
                draw.text((50, y_pos + 25), value, fill='black', font=font_medium)
                y_pos += 70
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            image.save(temp_file.name, 'PNG')
            temp_file.close()
            
            self.log(f"✅ Passport image created: {temp_file.name}")
            self.log("📋 Image contains:")
            self.log("   Full Name: VŨ NGỌC TÂN")
            self.log("   Date of Birth: 14/02/1983")
            self.log("   Place of Birth: HẢI PHÒNG")
            self.log("   Sex: M")
            self.log("   Passport Number: C1571189")
            
            return temp_file.name
            
        except Exception as e:
            self.log(f"❌ Error creating passport image: {str(e)}", "ERROR")
            return None
    
    def analyze_passport_with_image(self, image_path):
        """Make API call with proper image file"""
        try:
            self.log("🔍 Making API call with passport image...")
            
            endpoint = f"{BACKEND_URL}/crew/analyze-passport"
            self.log(f"   POST {endpoint}")
            
            # Prepare multipart form data with image
            with open(image_path, 'rb') as f:
                files = {
                    'passport_file': ('test_passport.png', f, 'image/png')
                }
                
                data = {
                    'ship_name': 'BROTHER 36'
                }
                
                self.log("   Request data:")
                self.log(f"     ship_name: {data['ship_name']}")
                self.log(f"     passport_file: test_passport.png (image/png)")
                
                response = requests.post(
                    endpoint, 
                    files=files, 
                    data=data,
                    headers=self.get_headers(), 
                    timeout=120
                )
                
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.log("✅ Passport analysis API call successful")
                
                try:
                    response_data = response.json()
                    self.log("📊 CRITICAL: API Response Analysis")
                    self.log("=" * 60)
                    
                    # Print the EXACT response JSON
                    self.log("🔍 EXACT API RESPONSE JSON:")
                    self.log(json.dumps(response_data, indent=2, ensure_ascii=False))
                    
                    # Check the analysis section specifically
                    analysis = response_data.get('analysis', {})
                    if analysis:
                        self.log("\n🔍 ANALYSIS SECTION FIELD-BY-FIELD:")
                        
                        fields_to_check = [
                            'full_name', 'sex', 'date_of_birth', 'place_of_birth', 
                            'passport_number', 'nationality', 'issue_date', 'expiry_date'
                        ]
                        
                        for field in fields_to_check:
                            value = analysis.get(field, 'FIELD_NOT_PRESENT')
                            if value == 'FIELD_NOT_PRESENT':
                                self.log(f"   ❌ {field}: FIELD NOT PRESENT IN ANALYSIS")
                            elif value == "" or value is None:
                                self.log(f"   ❌ {field}: EMPTY/NULL ('{value}')")
                            else:
                                self.log(f"   ✅ {field}: '{value}' (type: {type(value).__name__})")
                        
                        # CRITICAL: Focus on date_of_birth field
                        self.log("\n🎯 CRITICAL FOCUS: date_of_birth field")
                        self.log("=" * 40)
                        
                        date_of_birth = analysis.get('date_of_birth')
                        if 'date_of_birth' not in analysis:
                            self.log("❌ CRITICAL ISSUE: 'date_of_birth' field is NOT PRESENT in analysis")
                        elif date_of_birth == "" or date_of_birth is None:
                            self.log(f"❌ CRITICAL ISSUE: 'date_of_birth' field is EMPTY/NULL: '{date_of_birth}'")
                        else:
                            self.log(f"✅ 'date_of_birth' field is PRESENT and has value: '{date_of_birth}'")
                            self.log(f"   Type: {type(date_of_birth).__name__}")
                            self.log(f"   Length: {len(str(date_of_birth))}")
                            self.log(f"   Format check: {'DD/MM/YYYY' if '/' in str(date_of_birth) else 'Other format'}")
                        
                        # Check confidence score
                        confidence = analysis.get('confidence_score', 0)
                        self.log(f"\n📊 AI Confidence Score: {confidence}")
                        
                        return response_data
                    else:
                        self.log("❌ No 'analysis' section found in response")
                        return response_data
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON response: {str(e)}")
                    self.log(f"Raw response: {response.text[:500]}")
                    return None
                    
            else:
                self.log(f"❌ Passport analysis API call failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error making passport analysis API call: {str(e)}", "ERROR")
            traceback.print_exc()
            return None
    
    def run_image_debug_test(self):
        """Run debug test with proper image file"""
        try:
            self.log("🚀 STARTING PASSPORT IMAGE DEBUG TEST")
            self.log("=" * 80)
            self.log("OBJECTIVE: Test with proper image file to debug date_of_birth issue")
            self.log("=" * 80)
            
            # Step 1: Authentication
            if not self.authenticate():
                self.log("❌ CRITICAL: Authentication failed - cannot proceed")
                return False
            
            # Step 2: Create passport image
            image_path = self.create_passport_image()
            if not image_path:
                self.log("❌ CRITICAL: Failed to create passport image")
                return False
            
            # Step 3: Make API call with image
            api_response = self.analyze_passport_with_image(image_path)
            if not api_response:
                self.log("❌ CRITICAL: Passport analysis API call failed")
                return False
            
            # Cleanup
            try:
                os.unlink(image_path)
                self.log("✅ Cleaned up test image file")
            except:
                pass
            
            self.log("\n" + "=" * 80)
            self.log("✅ PASSPORT IMAGE DEBUG TEST COMPLETED")
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR in debug test: {str(e)}", "ERROR")
            traceback.print_exc()
            return False

def main():
    """Main function to run the passport image debug test"""
    tester = PassportImageDebugTester()
    
    try:
        # Run debug test
        success = tester.run_image_debug_test()
        
        # Return appropriate exit code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.log("\n❌ Test interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()