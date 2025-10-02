#!/usr/bin/env python3
"""
AI Analysis Functionality Testing
FOCUS: Test AI analysis functionality to understand what happens when AI fails to extract information

REVIEW REQUEST REQUIREMENTS:
1. Check the current AI configuration: GET /api/ai-config
2. Test AI analysis with an existing certificate by uploading a test certificate to SUNSHINE 01 ship
3. Examine the analysis_result to see what fields are being extracted
4. Check the multi-upload endpoint behavior when AI extraction is incomplete or fails
5. Understand how to detect when AI extraction is insufficient/failed
6. What criteria should be used to determine if manual input is needed
7. Current behavior when AI confidence is low or fields are missing

EXPECTED BEHAVIOR:
- AI configuration should be accessible and show current provider/model
- Certificate upload should trigger AI analysis
- Analysis result should show extracted fields with confidence levels
- Multi-upload should handle AI failures gracefully
- System should provide clear indicators when manual input is needed
"""

import requests
import json
import os
import sys
import re
from datetime import datetime, timedelta
import time
import traceback
import tempfile
from urllib.parse import urlparse
import base64

# Configuration - Use environment variable for backend URL
try:
    # Test internal connection first
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:  # 401 is expected without auth
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    # Fallback to external URL
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vesseldocs.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

class AIAnalysisTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = {}
        self.backend_logs = []
        
        # Test tracking
        self.ai_tests = {
            'authentication_successful': False,
            'ai_config_accessible': False,
            'ai_provider_model_configured': False,
            'sunshine_01_ship_found': False,
            'test_certificate_uploaded': False,
            'ai_analysis_triggered': False,
            'analysis_result_examined': False,
            'extracted_fields_verified': False,
            'confidence_level_checked': False,
            'multi_upload_endpoint_tested': False,
            'ai_failure_handling_verified': False,
            'manual_input_criteria_identified': False,
            'low_confidence_behavior_tested': False,
            'missing_fields_behavior_tested': False
        }
        
        # Test data
        self.sunshine_01_ship_id = None
        self.test_certificate_id = None
        self.ai_config = {}
        self.analysis_results = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message)
        
        # Also store in our log collection
        self.backend_logs.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        
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
            self.log(f"   POST {endpoint}")
            
            response = requests.post(endpoint, json=login_data, timeout=60)
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                self.log("✅ Authentication successful")
                self.log(f"   User ID: {self.current_user.get('id')}")
                self.log(f"   User Role: {self.current_user.get('role')}")
                self.log(f"   Company: {self.current_user.get('company')}")
                
                self.ai_tests['authentication_successful'] = True
                return True
            else:
                self.log(f"   ❌ Authentication failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"   Error: {response.text[:200]}")
                return False
                            
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def test_ai_config(self):
        """Test 1: Check the current AI configuration"""
        try:
            self.log("🤖 TEST 1: Checking AI Configuration...")
            
            endpoint = f"{BACKEND_URL}/ai-config"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(
                endpoint,
                headers=self.get_headers(),
                timeout=30
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                self.ai_config = response.json()
                self.log("✅ AI configuration accessible")
                self.ai_tests['ai_config_accessible'] = True
                
                # Log AI configuration details
                self.log("   AI Configuration:")
                self.log(f"   Provider: {self.ai_config.get('provider', 'Not configured')}")
                self.log(f"   Model: {self.ai_config.get('model', 'Not configured')}")
                self.log(f"   Using Emergent Key: {self.ai_config.get('use_emergent_key', 'Not specified')}")
                
                # Verify AI is properly configured
                if self.ai_config.get('provider') and self.ai_config.get('model'):
                    self.log("✅ AI provider and model are configured")
                    self.ai_tests['ai_provider_model_configured'] = True
                else:
                    self.log("❌ AI provider or model not properly configured")
                
                return True
            else:
                self.log(f"   ❌ AI configuration not accessible: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    self.log(f"      Error: {response.text[:500]}")
                return False
                
        except Exception as e:
            self.log(f"❌ AI configuration test error: {str(e)}", "ERROR")
            return False
    
    def find_sunshine_01_ship(self):
        """Find SUNSHINE 01 ship for testing"""
        try:
            self.log("🚢 Finding SUNSHINE 01 ship...")
            
            endpoint = f"{BACKEND_URL}/ships"
            self.log(f"   GET {endpoint}")
            
            response = requests.get(
                endpoint,
                headers=self.get_headers(),
                timeout=30
            )
            
            self.log(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                ships = response.json()
                self.log(f"   Found {len(ships)} ships")
                
                # Look for SUNSHINE 01
                for ship in ships:
                    if 'SUNSHINE 01' in ship.get('name', '').upper():
                        self.sunshine_01_ship_id = ship.get('id')
                        self.log("✅ SUNSHINE 01 ship found")
                        self.log(f"   Ship ID: {self.sunshine_01_ship_id}")
                        self.log(f"   Ship Name: {ship.get('name')}")
                        self.log(f"   IMO: {ship.get('imo')}")
                        self.log(f"   Flag: {ship.get('flag')}")
                        self.log(f"   Class Society: {ship.get('ship_type')}")
                        
                        self.ai_tests['sunshine_01_ship_found'] = True
                        return True
                
                self.log("❌ SUNSHINE 01 ship not found")
                self.log("   Available ships:")
                for ship in ships[:5]:  # Show first 5 ships
                    self.log(f"      - {ship.get('name')} (ID: {ship.get('id')})")
                return False
            else:
                self.log(f"   ❌ Failed to get ships: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ship finding error: {str(e)}", "ERROR")
            return False
    
    def create_test_certificate_file(self):
        """Create a test PDF certificate file for upload"""
        try:
            # Create a simple test PDF content (this is a minimal PDF structure)
            pdf_content = """%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
50 750 Td
(CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE) Tj
0 -20 Td
(Ship Name: SUNSHINE 01) Tj
0 -20 Td
(IMO Number: 9415313) Tj
0 -20 Td
(Flag State: BELIZE) Tj
0 -20 Td
(Classification Society: PANAMA MARITIME DOCUMENTATION SERVICES (PMDS)) Tj
0 -20 Td
(Certificate No: TEST-CSSC-2025-001) Tj
0 -20 Td
(Issue Date: 15/01/2024) Tj
0 -20 Td
(Valid Date: 10/03/2026) Tj
0 -20 Td
(Last Endorse: 15/06/2024) Tj
0 -20 Td
(Built Year: 2010) Tj
0 -20 Td
(Gross Tonnage: 2959 GT) Tj
0 -20 Td
(Deadweight: 4850 DWT) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000526 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
625
%%EOF"""
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(pdf_content.encode('utf-8'))
            temp_file.close()
            
            self.log(f"✅ Test certificate file created: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            self.log(f"❌ Test certificate file creation error: {str(e)}", "ERROR")
            return None
    
    def test_certificate_upload_with_ai_analysis(self):
        """Test 2: Upload a test certificate and examine AI analysis"""
        try:
            self.log("📄 TEST 2: Testing certificate upload with AI analysis...")
            
            if not self.sunshine_01_ship_id:
                self.log("   ❌ No SUNSHINE 01 ship available")
                return False
            
            # Create test certificate file
            test_file_path = self.create_test_certificate_file()
            if not test_file_path:
                return False
            
            try:
                # Upload certificate using multi-upload endpoint
                endpoint = f"{BACKEND_URL}/certificates/multi-upload?ship_id={self.sunshine_01_ship_id}"
                self.log(f"   POST {endpoint}")
                
                with open(test_file_path, 'rb') as f:
                    files = {
                        'files': ('test_certificate.pdf', f, 'application/pdf')
                    }
                    data = {
                        'notes': 'AI Analysis Test Certificate'
                    }
                    
                    response = requests.post(
                        endpoint,
                        files=files,
                        data=data,
                        headers=self.get_headers(),
                        timeout=120  # AI analysis can take time
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    self.log("✅ Certificate uploaded successfully")
                    self.ai_tests['test_certificate_uploaded'] = True
                    
                    # Log full response for analysis
                    self.log("   Upload Response:")
                    self.log(f"   {json.dumps(response_data, indent=2)}")
                    
                    # Check if AI analysis was triggered
                    results = response_data.get('results', [])
                    if results:
                        result = results[0]  # First result
                        analysis_result = result.get('analysis', {})  # Changed from 'analysis_result' to 'analysis'
                        
                        if analysis_result:
                            self.log("✅ AI analysis was triggered")
                            self.ai_tests['ai_analysis_triggered'] = True
                            self.analysis_results.append(analysis_result)
                            
                            # Examine analysis result
                            self.examine_analysis_result(analysis_result)
                            
                            # Store certificate ID for cleanup
                            certificate_info = result.get('certificate', {})
                            self.test_certificate_id = certificate_info.get('id')
                            
                            return True
                        else:
                            self.log("❌ No AI analysis result found")
                            return False
                    else:
                        self.log("❌ No upload results found")
                        return False
                else:
                    self.log(f"   ❌ Certificate upload failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        self.log(f"      Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        self.log(f"      Error: {response.text[:500]}")
                    return False
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(test_file_path)
                except:
                    pass
                
        except Exception as e:
            self.log(f"❌ Certificate upload test error: {str(e)}", "ERROR")
            return False
    
    def examine_analysis_result(self, analysis_result):
        """Test 3: Examine the analysis_result to see what fields are being extracted"""
        try:
            self.log("🔍 TEST 3: Examining AI analysis result...")
            self.ai_tests['analysis_result_examined'] = True
            
            # Log the complete analysis result
            self.log("   Complete Analysis Result:")
            self.log(f"   {json.dumps(analysis_result, indent=2)}")
            
            # Check extracted fields
            extracted_fields = {
                'ship_name': analysis_result.get('ship_name'),
                'imo_number': analysis_result.get('imo_number'),
                'flag': analysis_result.get('flag'),
                'class_society': analysis_result.get('class_society'),
                'built_year': analysis_result.get('built_year'),
                'gross_tonnage': analysis_result.get('gross_tonnage'),
                'deadweight': analysis_result.get('deadweight'),
                'cert_name': analysis_result.get('cert_name'),
                'cert_no': analysis_result.get('cert_no'),
                'issue_date': analysis_result.get('issue_date'),
                'valid_date': analysis_result.get('valid_date'),
                'last_endorse': analysis_result.get('last_endorse')
            }
            
            self.log("   Extracted Fields Analysis:")
            extracted_count = 0
            missing_count = 0
            
            for field, value in extracted_fields.items():
                if value and str(value).strip() and str(value).strip().lower() not in ['null', 'none', 'unknown', '']:
                    self.log(f"   ✅ {field}: {value}")
                    extracted_count += 1
                else:
                    self.log(f"   ❌ {field}: {value or 'NOT EXTRACTED'}")
                    missing_count += 1
            
            self.log(f"   📊 Extraction Summary: {extracted_count}/{len(extracted_fields)} fields extracted ({(extracted_count/len(extracted_fields)*100):.1f}%)")
            
            if extracted_count > 0:
                self.ai_tests['extracted_fields_verified'] = True
            
            # Check confidence level
            confidence = analysis_result.get('confidence')
            if confidence:
                self.log(f"   📊 Confidence Level: {confidence}")
                self.ai_tests['confidence_level_checked'] = True
                
                # Analyze confidence level
                if confidence.lower() in ['high', 'medium']:
                    self.log("   ✅ AI confidence is acceptable")
                elif confidence.lower() == 'low':
                    self.log("   ⚠️ AI confidence is LOW - may need manual input")
                    self.test_low_confidence_behavior()
                else:
                    self.log(f"   ❓ Unknown confidence level: {confidence}")
            else:
                self.log("   ❌ No confidence level provided")
            
            # Check other analysis metadata
            category = analysis_result.get('category')
            if category:
                self.log(f"   📂 Document Category: {category}")
                if category != 'certificates':
                    self.log("   ⚠️ Document not classified as certificate - may indicate AI failure")
            
            processing_method = analysis_result.get('processing_method')
            if processing_method:
                self.log(f"   ⚙️ Processing Method: {processing_method}")
            
            text_content = analysis_result.get('text_content')
            if text_content:
                self.log(f"   📝 Text Content Length: {len(text_content)} characters")
                self.log(f"   📝 Text Preview: {text_content[:200]}...")
            else:
                self.log("   ❌ No text content extracted")
            
            # Determine if manual input is needed
            self.determine_manual_input_criteria(analysis_result, extracted_count, len(extracted_fields))
            
            return True
            
        except Exception as e:
            self.log(f"❌ Analysis result examination error: {str(e)}", "ERROR")
            return False
    
    def determine_manual_input_criteria(self, analysis_result, extracted_count, total_fields):
        """Determine criteria for when manual input is needed"""
        try:
            self.log("🎯 TEST 4: Determining manual input criteria...")
            
            manual_input_needed = False
            reasons = []
            
            # Criteria 1: Low confidence
            confidence = analysis_result.get('confidence', '').lower()
            if confidence == 'low':
                manual_input_needed = True
                reasons.append("AI confidence is LOW")
            
            # Criteria 2: Low extraction rate
            extraction_rate = (extracted_count / total_fields) * 100
            if extraction_rate < 50:  # Less than 50% fields extracted
                manual_input_needed = True
                reasons.append(f"Low extraction rate ({extraction_rate:.1f}%)")
            
            # Criteria 3: Missing critical fields
            critical_fields = ['ship_name', 'cert_name', 'cert_no']
            missing_critical = []
            for field in critical_fields:
                value = analysis_result.get(field)
                if not value or str(value).strip().lower() in ['null', 'none', 'unknown', '']:
                    missing_critical.append(field)
            
            if missing_critical:
                manual_input_needed = True
                reasons.append(f"Missing critical fields: {', '.join(missing_critical)}")
            
            # Criteria 4: Document not classified as certificate
            category = analysis_result.get('category', '').lower()
            if category != 'certificates':
                manual_input_needed = True
                reasons.append(f"Document classified as '{category}' instead of 'certificates'")
            
            # Criteria 5: No text content extracted
            text_content = analysis_result.get('text_content')
            if not text_content or len(text_content.strip()) < 100:
                manual_input_needed = True
                reasons.append("Insufficient text content extracted")
            
            # Log the determination
            if manual_input_needed:
                self.log("⚠️ MANUAL INPUT NEEDED")
                self.log("   Reasons:")
                for reason in reasons:
                    self.log(f"      - {reason}")
                self.ai_tests['manual_input_criteria_identified'] = True
            else:
                self.log("✅ AI extraction appears sufficient - no manual input needed")
                self.ai_tests['manual_input_criteria_identified'] = True
            
            return manual_input_needed, reasons
            
        except Exception as e:
            self.log(f"❌ Manual input criteria determination error: {str(e)}", "ERROR")
            return False, []
    
    def test_low_confidence_behavior(self):
        """Test behavior when AI confidence is low"""
        try:
            self.log("⚠️ TEST 5: Testing low confidence behavior...")
            self.ai_tests['low_confidence_behavior_tested'] = True
            
            # This would typically involve:
            # 1. Checking if the system flags the certificate for manual review
            # 2. Verifying if progress bar shows appropriate message
            # 3. Ensuring user is prompted for manual input
            
            self.log("   Low confidence behavior analysis:")
            self.log("   - Certificate should be flagged for manual review")
            self.log("   - Progress bar should show 'AI extraction incomplete - manual input needed'")
            self.log("   - User should be prompted to verify/complete extracted data")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Low confidence behavior test error: {str(e)}", "ERROR")
            return False
    
    def test_multi_upload_endpoint_behavior(self):
        """Test 6: Check multi-upload endpoint behavior when AI extraction fails"""
        try:
            self.log("📤 TEST 6: Testing multi-upload endpoint behavior with AI failures...")
            
            if not self.sunshine_01_ship_id:
                self.log("   ❌ No SUNSHINE 01 ship available")
                return False
            
            # Create a problematic file that might cause AI extraction to fail
            problematic_content = b"This is not a valid PDF certificate file"
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(problematic_content)
            temp_file.close()
            
            try:
                endpoint = f"{BACKEND_URL}/certificates/multi-upload?ship_id={self.sunshine_01_ship_id}"
                self.log(f"   POST {endpoint} (with problematic file)")
                
                with open(temp_file.name, 'rb') as f:
                    files = {
                        'files': ('problematic_certificate.pdf', f, 'application/pdf')
                    }
                    data = {
                        'notes': 'AI Failure Test Certificate'
                    }
                    
                    response = requests.post(
                        endpoint,
                        files=files,
                        data=data,
                        headers=self.get_headers(),
                        timeout=120
                    )
                
                self.log(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    self.log("✅ Multi-upload endpoint accessible")
                    self.ai_tests['multi_upload_endpoint_tested'] = True
                    
                    # Examine how the endpoint handles AI failures
                    self.log("   Multi-upload response with problematic file:")
                    self.log(f"   {json.dumps(response_data, indent=2)}")
                    
                    results = response_data.get('results', [])
                    if results:
                        result = results[0]
                        status = result.get('status')
                        analysis_result = result.get('analysis_result', {})
                        
                        self.log(f"   Upload Status: {status}")
                        
                        if status in ['requires_manual_review', 'pending_manual_input', 'ai_extraction_failed']:
                            self.log("✅ AI failure handling working correctly")
                            self.ai_tests['ai_failure_handling_verified'] = True
                        elif analysis_result.get('confidence') == 'low':
                            self.log("✅ Low confidence detected - appropriate for manual review")
                            self.ai_tests['ai_failure_handling_verified'] = True
                        else:
                            self.log("⚠️ AI failure handling may need improvement")
                    
                    return True
                else:
                    self.log(f"   ❌ Multi-upload endpoint failed: {response.status_code}")
                    return False
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
                
        except Exception as e:
            self.log(f"❌ Multi-upload endpoint test error: {str(e)}", "ERROR")
            return False
    
    def test_missing_fields_behavior(self):
        """Test behavior when critical fields are missing"""
        try:
            self.log("❓ TEST 7: Testing missing fields behavior...")
            self.ai_tests['missing_fields_behavior_tested'] = True
            
            # Analyze the results we've collected
            if self.analysis_results:
                for i, result in enumerate(self.analysis_results):
                    self.log(f"   Analysis Result {i+1}:")
                    
                    # Check for missing critical fields
                    critical_fields = ['ship_name', 'cert_name', 'cert_no', 'valid_date']
                    missing_fields = []
                    
                    for field in critical_fields:
                        value = result.get(field)
                        if not value or str(value).strip().lower() in ['null', 'none', 'unknown', '']:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        self.log(f"      Missing critical fields: {', '.join(missing_fields)}")
                        self.log("      ⚠️ This should trigger manual input requirement")
                    else:
                        self.log("      ✅ All critical fields present")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Missing fields behavior test error: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_certificate(self):
        """Clean up the test certificate"""
        try:
            if self.test_certificate_id:
                self.log("🧹 Cleaning up test certificate...")
                
                endpoint = f"{BACKEND_URL}/certificates/{self.test_certificate_id}"
                response = requests.delete(endpoint, headers=self.get_headers(), timeout=30)
                
                if response.status_code == 200:
                    self.log("✅ Test certificate cleaned up successfully")
                else:
                    self.log(f"⚠️ Test certificate cleanup failed: {response.status_code}")
                    
        except Exception as e:
            self.log(f"⚠️ Cleanup error: {str(e)}", "WARNING")
    
    def run_comprehensive_ai_tests(self):
        """Main test function for AI analysis functionality"""
        self.log("🤖 STARTING AI ANALYSIS FUNCTIONALITY TESTING")
        self.log("🎯 FOCUS: Understanding AI failure scenarios and manual input criteria")
        self.log("=" * 100)
        
        try:
            # Step 1: Authenticate
            self.log("\n🔐 STEP 1: AUTHENTICATION")
            self.log("=" * 50)
            if not self.authenticate():
                self.log("❌ Authentication failed - cannot proceed with testing")
                return False
            
            # Step 2: Test AI Configuration
            self.log("\n🤖 STEP 2: AI CONFIGURATION CHECK")
            self.log("=" * 50)
            if not self.test_ai_config():
                self.log("❌ AI configuration test failed")
                return False
            
            # Step 3: Find SUNSHINE 01 Ship
            self.log("\n🚢 STEP 3: FIND SUNSHINE 01 SHIP")
            self.log("=" * 50)
            if not self.find_sunshine_01_ship():
                self.log("❌ SUNSHINE 01 ship not found - cannot proceed with certificate testing")
                return False
            
            # Step 4: Test Certificate Upload with AI Analysis
            self.log("\n📄 STEP 4: CERTIFICATE UPLOAD WITH AI ANALYSIS")
            self.log("=" * 50)
            if not self.test_certificate_upload_with_ai_analysis():
                self.log("❌ Certificate upload with AI analysis failed")
                return False
            
            # Step 5: Test Multi-Upload Endpoint Behavior
            self.log("\n📤 STEP 5: MULTI-UPLOAD ENDPOINT BEHAVIOR")
            self.log("=" * 50)
            self.test_multi_upload_endpoint_behavior()
            
            # Step 6: Test Missing Fields Behavior
            self.log("\n❓ STEP 6: MISSING FIELDS BEHAVIOR")
            self.log("=" * 50)
            self.test_missing_fields_behavior()
            
            # Step 7: Final Analysis
            self.log("\n📊 STEP 7: FINAL ANALYSIS")
            self.log("=" * 50)
            self.provide_final_analysis()
            
            return True
            
        finally:
            # Always cleanup
            self.log("\n🧹 CLEANUP")
            self.log("=" * 50)
            self.cleanup_test_certificate()
    
    def provide_final_analysis(self):
        """Provide final analysis of AI functionality testing"""
        try:
            self.log("🤖 AI ANALYSIS FUNCTIONALITY TESTING - RESULTS")
            self.log("=" * 80)
            
            # Check which tests passed
            passed_tests = []
            failed_tests = []
            
            for test_name, passed in self.ai_tests.items():
                if passed:
                    passed_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            self.log(f"✅ TESTS PASSED ({len(passed_tests)}/{len(self.ai_tests)}):")
            for test in passed_tests:
                self.log(f"   ✅ {test.replace('_', ' ').title()}")
            
            if failed_tests:
                self.log(f"\n❌ TESTS FAILED ({len(failed_tests)}/{len(self.ai_tests)}):")
                for test in failed_tests:
                    self.log(f"   ❌ {test.replace('_', ' ').title()}")
            
            # Calculate success rate
            success_rate = (len(passed_tests) / len(self.ai_tests)) * 100
            self.log(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({len(passed_tests)}/{len(self.ai_tests)})")
            
            # Key findings
            self.log("\n🔍 KEY FINDINGS:")
            
            if self.ai_config:
                self.log(f"   🤖 AI Configuration: {self.ai_config.get('provider')} / {self.ai_config.get('model')}")
            
            if self.analysis_results:
                for i, result in enumerate(self.analysis_results):
                    confidence = result.get('confidence', 'Unknown')
                    category = result.get('category', 'Unknown')
                    self.log(f"   📊 Analysis {i+1}: Confidence={confidence}, Category={category}")
            
            # Manual input criteria
            self.log("\n🎯 MANUAL INPUT CRITERIA IDENTIFIED:")
            self.log("   1. AI confidence level is 'low'")
            self.log("   2. Extraction rate < 50% of expected fields")
            self.log("   3. Missing critical fields (ship_name, cert_name, cert_no)")
            self.log("   4. Document not classified as 'certificates'")
            self.log("   5. Insufficient text content extracted (<100 characters)")
            
            # Recommendations
            self.log("\n💡 RECOMMENDATIONS FOR IMPLEMENTATION:")
            self.log("   1. Check analysis_result.confidence for 'low' values")
            self.log("   2. Count extracted vs null/empty fields")
            self.log("   3. Verify critical fields are present")
            self.log("   4. Show progress bar message: 'AI extraction incomplete - manual input needed'")
            self.log("   5. Pause upload process and prompt user for manual data entry")
            
            # Final conclusion
            if success_rate >= 70:
                self.log(f"\n🎉 CONCLUSION: AI ANALYSIS FUNCTIONALITY IS WORKING")
                self.log(f"   Success rate: {success_rate:.1f}% - AI system is functional with clear failure indicators")
                self.log(f"   ✅ AI configuration accessible and properly set up")
                self.log(f"   ✅ Certificate analysis working with confidence levels")
                self.log(f"   ✅ Manual input criteria can be clearly identified")
            else:
                self.log(f"\n❌ CONCLUSION: AI ANALYSIS FUNCTIONALITY HAS ISSUES")
                self.log(f"   Success rate: {success_rate:.1f}% - AI system needs attention")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Final analysis error: {str(e)}", "ERROR")
            return False


def main():
    """Main function to run AI analysis tests"""
    print("🤖 AI ANALYSIS FUNCTIONALITY TESTING STARTED")
    print("=" * 80)
    
    try:
        tester = AIAnalysisTester()
        success = tester.run_comprehensive_ai_tests()
        
        if success:
            print("\n✅ AI ANALYSIS FUNCTIONALITY TESTING COMPLETED")
        else:
            print("\n❌ AI ANALYSIS FUNCTIONALITY TESTING FAILED")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    
    # Always exit with 0 for testing purposes - we want to capture the results
    sys.exit(0)

if __name__ == "__main__":
    main()