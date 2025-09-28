#!/usr/bin/env python3
"""
Enhanced AI Analysis Debugging Test
FOCUS: Test the enhanced AI analysis debugging to identify exactly what the AI is returning 
for marine certificate classification and why it's not classifying legitimate marine certificates correctly.

SPECIFIC TEST FOCUS:
1. Test Multi-Upload with Debug Logs
2. Analyze AI Response Structure
3. Debug Category Classification Logic
4. Identify Root Cause
5. Verify Marine Certificate Keywords
"""

import requests
import json
import os
import sys
import tempfile
import base64
from datetime import datetime
import traceback

# Configuration
BACKEND_URL = 'https://marinetrack-1.preview.emergentagent.com/api'
print(f"Using backend URL: {BACKEND_URL}")

class EnhancedDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_ship_id = None
        
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
    
    def get_test_ship(self):
        """Get a test ship for certificate upload"""
        try:
            self.log("🚢 Getting test ship for certificate upload...")
            
            endpoint = f"{BACKEND_URL}/ships"
            response = requests.get(endpoint, headers=self.get_headers(), timeout=30)
            
            if response.status_code == 200:
                ships = response.json()
                if ships and len(ships) > 0:
                    # Use the first available ship
                    test_ship = ships[0]
                    self.test_ship_id = test_ship.get('id')
                    ship_name = test_ship.get('name', 'Unknown')
                    
                    self.log(f"✅ Using test ship: {ship_name}")
                    self.log(f"   Ship ID: {self.test_ship_id}")
                    return True
                else:
                    self.log("❌ No ships available for testing")
                    return False
            else:
                self.log(f"❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting test ship: {str(e)}", "ERROR")
            return False
    
    def create_marine_certificate_file(self):
        """Create a legitimate marine certificate file for testing"""
        try:
            # Create a comprehensive marine certificate that should definitely be classified as "certificates"
            marine_cert_content = """
CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE
(SOLAS Convention)

Certificate No: CSSC-2024-001
IMO Number: 9415313
Ship Name: SUNSHINE 01
Flag State: PANAMA
Port of Registry: PANAMA CITY
Classification Society: PANAMA MARITIME DOCUMENTATION SERVICES (PMDS)

CERTIFICATE VALIDITY:
Issue Date: 15/01/2024
Valid Until: 15/01/2029
Place of Issue: Panama City, Panama

SURVEY INFORMATION:
Last Annual Survey: 10/03/2024
Next Annual Survey Due: 10/03/2025
Last Intermediate Survey: 15/07/2023
Next Intermediate Survey Due: 15/07/2025
Last Special Survey: 15/01/2024
Next Special Survey Due: 15/01/2029

INSPECTIONS OF THE OUTSIDE OF THE SHIP'S BOTTOM:
Last Bottom Inspection: 15/01/2024
Next Bottom Inspection Due: 15/01/2027

COMPLIANCE STATUS:
✓ SOLAS Chapter II-1 (Construction - Structure, subdivision and stability)
✓ SOLAS Chapter II-2 (Construction - Fire protection, fire detection and fire extinction)
✓ SOLAS Chapter III (Life-saving appliances and arrangements)
✓ SOLAS Chapter IV (Radiocommunications)
✓ SOLAS Chapter V (Safety of navigation)

MARITIME KEYWORDS FOR AI DETECTION:
- SOLAS (Safety of Life at Sea)
- MARPOL (Marine Pollution Prevention)
- Certificate
- Maritime
- Safety
- Construction
- Survey
- IMO (International Maritime Organization)
- Classification Society
- Marine Certificate
- Ship Certificate
- Statutory Certificate

This certificate is issued under the authority of the Government of Panama
in accordance with the provisions of the International Convention for the
Safety of Life at Sea (SOLAS), 1974, as amended.

Authorized by: Panama Maritime Authority
Issued by: Panama Maritime Documentation Services
Digital Signature: [DIGITAL_SIGNATURE_HASH]
"""
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, 
                                                  prefix='CARGO_SHIP_SAFETY_CONSTRUCTION_CERTIFICATE_')
            temp_file.write(marine_cert_content)
            temp_file.close()
            
            self.log(f"✅ Created marine certificate file: {temp_file.name}")
            self.log("   Contains: SOLAS, MARPOL, Certificate, Maritime, Safety, Construction, Survey, IMO")
            
            return temp_file.name
            
        except Exception as e:
            self.log(f"❌ Error creating marine certificate file: {str(e)}", "ERROR")
            return None
    
    def test_multi_upload_with_enhanced_debugging(self):
        """Test POST /api/certificates/multi-upload with enhanced debugging logs"""
        try:
            self.log("🔍 TESTING MULTI-UPLOAD WITH ENHANCED DEBUGGING")
            self.log("=" * 70)
            
            if not self.test_ship_id:
                self.log("❌ No test ship available")
                return False
            
            # Create marine certificate file
            cert_file_path = self.create_marine_certificate_file()
            if not cert_file_path:
                return False
            
            try:
                # Test multi-upload endpoint
                endpoint = f"{BACKEND_URL}/certificates/multi-upload"
                params = {"ship_id": self.test_ship_id}
                
                self.log(f"   POST {endpoint}")
                self.log(f"   Ship ID: {self.test_ship_id}")
                self.log("   Uploading legitimate marine certificate...")
                
                # Read file and upload
                with open(cert_file_path, 'rb') as f:
                    files = {
                        'files': (os.path.basename(cert_file_path), f, 'text/plain')
                    }
                    
                    response = requests.post(
                        endpoint,
                        params=params,
                        files=files,
                        headers=self.get_headers(),
                        timeout=180  # Extended timeout for AI analysis
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    self.log("✅ Multi-upload request completed")
                    
                    # Detailed response analysis
                    self.analyze_enhanced_debugging_response(response_data)
                    
                    return True
                else:
                    self.log(f"❌ Multi-upload failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"   Error response: {json.dumps(error_data, indent=2)}")
                    except:
                        self.log(f"   Error text: {response.text[:1000]}")
                    return False
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(cert_file_path)
                    self.log("   Cleaned up temporary certificate file")
                except:
                    pass
                    
        except Exception as e:
            self.log(f"❌ Multi-upload test error: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def analyze_enhanced_debugging_response(self, response_data):
        """Analyze the multi-upload response with enhanced debugging focus"""
        try:
            self.log("🔍 ENHANCED DEBUGGING ANALYSIS")
            self.log("=" * 50)
            
            # Log complete response structure
            self.log("📊 COMPLETE API RESPONSE:")
            self.log(json.dumps(response_data, indent=2))
            
            # Check results array
            results = response_data.get('results', [])
            if not results:
                self.log("❌ No results in response - this is unexpected")
                return
            
            self.log(f"\n📋 ANALYZING {len(results)} RESULT(S):")
            
            for i, result in enumerate(results):
                self.log(f"\n🔍 RESULT {i+1} DETAILED ANALYSIS:")
                self.log("-" * 40)
                
                filename = result.get('filename', 'Unknown')
                success = result.get('success', False)
                message = result.get('message', 'No message')
                
                self.log(f"   Filename: {filename}")
                self.log(f"   Success: {success}")
                self.log(f"   Message: {message}")
                
                # Focus on AI analysis result
                analysis_result = result.get('analysis_result')
                if analysis_result:
                    self.log("\n🤖 AI ANALYSIS RESULT FOUND:")
                    self.analyze_ai_response_structure(analysis_result)
                else:
                    self.log("\n❌ NO AI ANALYSIS RESULT - This is the problem!")
                    self.log("   The AI analysis is not returning any data")
                
                # Check for specific error patterns
                if not success:
                    self.identify_classification_failure_cause(message, analysis_result)
                    
        except Exception as e:
            self.log(f"❌ Response analysis error: {str(e)}", "ERROR")
    
    def analyze_ai_response_structure(self, analysis_result):
        """Analyze the AI analysis result structure in detail"""
        try:
            self.log("🤖 AI RESPONSE STRUCTURE ANALYSIS:")
            self.log("-" * 35)
            
            # Check data type
            result_type = type(analysis_result).__name__
            self.log(f"   Data Type: {result_type}")
            
            if isinstance(analysis_result, dict):
                # Analyze dictionary keys
                keys = list(analysis_result.keys())
                self.log(f"   Keys Found: {keys}")
                
                # CRITICAL: Check category field
                category = analysis_result.get('category')
                self.log(f"\n🎯 CATEGORY ANALYSIS:")
                self.log(f"   Raw Category Value: '{category}'")
                self.log(f"   Category Type: {type(category).__name__}")
                
                # Check category classification logic
                if category == 'certificates':
                    self.log("   ✅ Category matches expected 'certificates'")
                elif category is None:
                    self.log("   ❌ Category is None - AI didn't classify")
                    self.log("   🔍 ROOT CAUSE: AI analysis returned no category")
                elif category == '':
                    self.log("   ❌ Category is empty string")
                    self.log("   🔍 ROOT CAUSE: AI returned empty category")
                else:
                    self.log(f"   ❌ Category is '{category}' - not 'certificates'")
                    self.log(f"   🔍 ROOT CAUSE: AI classified as wrong category")
                
                # Check other important fields
                cert_name = analysis_result.get('cert_name')
                cert_type = analysis_result.get('cert_type')
                confidence = analysis_result.get('confidence')
                
                self.log(f"\n📋 OTHER AI FIELDS:")
                self.log(f"   Certificate Name: '{cert_name}'")
                self.log(f"   Certificate Type: '{cert_type}'")
                self.log(f"   Confidence: {confidence}")
                
                # Check for marine keywords detection
                self.check_marine_keywords_detection(analysis_result)
                
                # Log all fields for complete debugging
                self.log(f"\n📊 ALL AI ANALYSIS FIELDS:")
                for key, value in analysis_result.items():
                    value_type = type(value).__name__
                    if isinstance(value, str) and len(value) > 100:
                        display_value = value[:100] + "..."
                    else:
                        display_value = value
                    self.log(f"      {key}: '{display_value}' ({value_type})")
                    
            elif isinstance(analysis_result, str):
                self.log(f"   String Content: '{analysis_result[:200]}...'")
                
                # Check if it's JSON string
                if 'category' in analysis_result.lower():
                    try:
                        parsed = json.loads(analysis_result)
                        self.log("   ✅ Parsed as JSON - analyzing...")
                        self.analyze_ai_response_structure(parsed)
                    except:
                        self.log("   ❌ Failed to parse as JSON")
                        
            else:
                self.log(f"   Unexpected Type: {result_type}")
                self.log(f"   Content: {str(analysis_result)[:200]}")
                
        except Exception as e:
            self.log(f"❌ AI response structure analysis error: {str(e)}", "ERROR")
    
    def check_marine_keywords_detection(self, analysis_result):
        """Check if marine certificate keywords were detected by AI"""
        try:
            self.log(f"\n🔍 MARINE KEYWORDS DETECTION CHECK:")
            
            # Expected marine keywords
            marine_keywords = [
                'solas', 'marpol', 'certificate', 'maritime', 'safety', 
                'construction', 'survey', 'imo', 'cargo ship', 'panama'
            ]
            
            # Check all text fields for keywords
            text_fields = [
                analysis_result.get('cert_name', ''),
                analysis_result.get('cert_type', ''),
                analysis_result.get('issued_by', ''),
                analysis_result.get('text_content', ''),
                str(analysis_result.get('category', ''))
            ]
            
            detected_keywords = []
            for field in text_fields:
                if field:
                    field_lower = str(field).lower()
                    for keyword in marine_keywords:
                        if keyword in field_lower and keyword not in detected_keywords:
                            detected_keywords.append(keyword)
            
            if detected_keywords:
                self.log(f"   ✅ Marine keywords detected: {detected_keywords}")
                self.log("   🔍 AI should have classified as 'certificates'")
            else:
                self.log("   ❌ No marine keywords detected")
                self.log("   🔍 This could explain classification failure")
                
        except Exception as e:
            self.log(f"❌ Keywords detection check error: {str(e)}", "ERROR")
    
    def identify_classification_failure_cause(self, message, analysis_result):
        """Identify the specific cause of classification failure"""
        try:
            self.log(f"\n🔍 CLASSIFICATION FAILURE ROOT CAUSE ANALYSIS:")
            self.log("-" * 45)
            
            if "Not a marine certificate" in message:
                self.log("   🎯 FAILURE TYPE: 'Not a marine certificate'")
                self.log("   🔍 CAUSE: category != 'certificates' in classification logic")
                
                if analysis_result:
                    category = analysis_result.get('category')
                    self.log(f"   🔍 AI returned category: '{category}'")
                    self.log("   🔍 Expected category: 'certificates'")
                    
                    if category != 'certificates':
                        self.log("   ❌ ROOT CAUSE CONFIRMED: AI classification error")
                        self.log("   💡 FIX NEEDED: Improve AI prompt or add fallback logic")
                else:
                    self.log("   ❌ ROOT CAUSE: No AI analysis result at all")
                    self.log("   💡 FIX NEEDED: Fix AI analysis pipeline")
                    
            elif "Unknown error" in message:
                self.log("   🎯 FAILURE TYPE: 'Unknown error'")
                self.log("   🔍 CAUSE: Exception during processing")
                self.log("   💡 FIX NEEDED: Check backend logs for specific error")
                
            elif "Processing error" in message:
                self.log("   🎯 FAILURE TYPE: 'Processing error'")
                self.log("   🔍 CAUSE: File processing or upload error")
                self.log("   💡 FIX NEEDED: Check file processing pipeline")
                
            else:
                self.log(f"   🎯 FAILURE TYPE: Other - '{message}'")
                self.log("   🔍 CAUSE: Unidentified error")
                
        except Exception as e:
            self.log(f"❌ Failure cause analysis error: {str(e)}", "ERROR")
    
    def run_enhanced_debug_test(self):
        """Main test function for enhanced debugging"""
        self.log("🔍 ENHANCED AI ANALYSIS DEBUGGING TEST STARTED")
        self.log("=" * 80)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed")
                return False
            
            # Step 2: Get Test Ship
            self.log("\n🚢 STEP 2: GET TEST SHIP")
            self.log("=" * 50)
            if not self.get_test_ship():
                self.log("❌ Could not get test ship")
                return False
            
            # Step 3: Test Multi-Upload with Enhanced Debugging
            self.log("\n🔍 STEP 3: MULTI-UPLOAD WITH ENHANCED DEBUGGING")
            self.log("=" * 50)
            success = self.test_multi_upload_with_enhanced_debugging()
            
            # Step 4: Final Analysis
            self.log("\n📊 STEP 4: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis(success)
            
            return success
            
        except Exception as e:
            self.log(f"❌ Critical error: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
    
    def provide_final_analysis(self, test_success):
        """Provide final analysis and recommendations"""
        try:
            self.log("🔍 ENHANCED DEBUGGING FINAL ANALYSIS")
            self.log("=" * 60)
            
            if test_success:
                self.log("✅ Enhanced debugging test completed successfully")
                self.log("   The detailed AI response analysis above shows:")
                self.log("   - Exact AI response structure and category values")
                self.log("   - Whether category == 'certificates' comparison is working")
                self.log("   - Marine certificate keywords detection status")
                self.log("   - Root cause of any classification failures")
            else:
                self.log("❌ Enhanced debugging test failed")
                self.log("   This indicates a fundamental issue with:")
                self.log("   - Multi-upload endpoint accessibility")
                self.log("   - AI analysis pipeline")
                self.log("   - Certificate processing workflow")
            
            self.log("\n🎯 KEY FINDINGS FROM ENHANCED DEBUGGING:")
            self.log("   1. AI response structure and data types")
            self.log("   2. Category field value and comparison logic")
            self.log("   3. Marine keywords detection by AI")
            self.log("   4. Specific failure points in classification")
            
            self.log("\n💡 NEXT STEPS:")
            self.log("   1. Review the detailed AI response logs above")
            self.log("   2. Identify the exact category value being returned")
            self.log("   3. Fix the classification logic based on findings")
            self.log("   4. Test with additional marine certificate samples")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False


def main():
    """Main function"""
    print("🔍 ENHANCED AI ANALYSIS DEBUGGING TEST")
    print("=" * 80)
    
    try:
        tester = EnhancedDebugTester()
        success = tester.run_enhanced_debug_test()
        
        if success:
            print("\n✅ ENHANCED DEBUGGING TEST COMPLETED")
        else:
            print("\n❌ ENHANCED DEBUGGING TEST FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    sys.exit(0)

if __name__ == "__main__":
    main()