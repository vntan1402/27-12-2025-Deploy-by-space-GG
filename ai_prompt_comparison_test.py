#!/usr/bin/env python3
"""
AI Prompt Comparison Test - Compare the two different AI analysis endpoints
"""

import requests
import sys
import json
import os
import tempfile
from datetime import datetime, timezone
import time

class AIPromptComparisonTester:
    def __init__(self, base_url="https://shipmanage.preview.emergentagent.com"):
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

    def test_single_analysis_endpoint(self, pdf_path):
        """Test the single PDF analysis endpoint (/api/analyze-ship-certificate)"""
        print(f"\n🔍 Testing Single PDF Analysis Endpoint")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        with open(pdf_path, 'rb') as pdf_file:
            files = {'file': ('BROTHER_36_EIAPP.pdf', pdf_file, 'application/pdf')}
            
            response = requests.post(
                f"{self.api_url}/analyze-ship-certificate",
                files=files,
                headers=headers,
                timeout=120
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    analysis = data.get('analysis', {})
                    ship_name = analysis.get('ship_name')
                    
                    print(f"   Status: SUCCESS")
                    print(f"   Ship Name: {repr(ship_name)}")
                    print(f"   Flag: {repr(analysis.get('flag'))}")
                    print(f"   Built Year: {repr(analysis.get('built_year'))}")
                    
                    return {
                        'success': True,
                        'ship_name': ship_name,
                        'endpoint': 'single_analysis',
                        'full_response': analysis
                    }
                        
                except json.JSONDecodeError as e:
                    print(f"   Status: JSON ERROR - {e}")
                    return {'success': False, 'error': f"JSON decode error: {e}"}
            else:
                print(f"   Status: API ERROR - {response.status_code}")
                return {'success': False, 'error': f"API error {response.status_code}"}

    def test_multi_file_endpoint(self, pdf_path):
        """Test the multi-file upload endpoint (/api/certificates/upload-multi-files)"""
        print(f"\n📁 Testing Multi-File Upload Endpoint")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        with open(pdf_path, 'rb') as pdf_file:
            files = {'files': ('BROTHER_36_EIAPP.pdf', pdf_file, 'application/pdf')}
            
            response = requests.post(
                f"{self.api_url}/certificates/upload-multi-files",
                files=files,
                headers=headers,
                timeout=120
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    uploaded_files = data.get('uploaded_files', [])
                    
                    if uploaded_files:
                        file_result = uploaded_files[0]
                        extracted_info = file_result.get('extracted_info', {})
                        ship_name = extracted_info.get('ship_name')
                        
                        print(f"   Status: SUCCESS")
                        print(f"   Ship Name: {repr(ship_name)}")
                        print(f"   Category: {repr(extracted_info.get('category'))}")
                        print(f"   Cert Name: {repr(extracted_info.get('cert_name'))}")
                        
                        return {
                            'success': True,
                            'ship_name': ship_name,
                            'endpoint': 'multi_file',
                            'full_response': extracted_info
                        }
                    else:
                        print(f"   Status: NO FILES PROCESSED")
                        return {'success': False, 'error': 'No files processed'}
                        
                except json.JSONDecodeError as e:
                    print(f"   Status: JSON ERROR - {e}")
                    return {'success': False, 'error': f"JSON decode error: {e}"}
            else:
                try:
                    error_data = response.json()
                    print(f"   Status: API ERROR - {error_data}")
                    return {'success': False, 'error': f"API error {response.status_code}: {error_data}"}
                except:
                    print(f"   Status: API ERROR - {response.text}")
                    return {'success': False, 'error': f"API error {response.status_code}: {response.text}"}

    def run_comparison_test(self):
        """Run comparison test between the two endpoints"""
        print("🔍 AI Prompt Comparison Test")
        print("=" * 60)
        print(f"Target PDF: {self.test_pdf_url}")
        print(f"Expected Ship Name: {self.expected_ship_name}")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            return False
        
        # Step 2: Download PDF
        pdf_path = self.download_pdf()
        if not pdf_path:
            return False
        
        try:
            # Step 3: Test both endpoints
            single_result = self.test_single_analysis_endpoint(pdf_path)
            multi_result = self.test_multi_file_endpoint(pdf_path)
            
            # Step 4: Compare results
            print("\n" + "=" * 60)
            print("📊 COMPARISON RESULTS")
            print("=" * 60)
            
            print(f"Single Analysis Endpoint:")
            if single_result['success']:
                single_ship_name = single_result['ship_name']
                single_correct = single_ship_name == self.expected_ship_name
                print(f"  Ship Name: {repr(single_ship_name)} {'✅' if single_correct else '❌'}")
            else:
                print(f"  Status: FAILED - {single_result['error']}")
            
            print(f"\nMulti-File Upload Endpoint:")
            if multi_result['success']:
                multi_ship_name = multi_result['ship_name']
                multi_correct = multi_ship_name == self.expected_ship_name
                print(f"  Ship Name: {repr(multi_ship_name)} {'✅' if multi_correct else '❌'}")
            else:
                print(f"  Status: FAILED - {multi_result['error']}")
            
            # Analysis
            print(f"\n🔍 ANALYSIS:")
            if single_result['success'] and multi_result['success']:
                single_ship_name = single_result['ship_name']
                multi_ship_name = multi_result['ship_name']
                
                if single_ship_name == multi_ship_name == self.expected_ship_name:
                    print(f"✅ BOTH ENDPOINTS WORKING: Both correctly extract '{self.expected_ship_name}'")
                elif single_ship_name != multi_ship_name:
                    print(f"⚠️ INCONSISTENCY DETECTED: Different results between endpoints")
                    print(f"   Single endpoint: {repr(single_ship_name)}")
                    print(f"   Multi endpoint: {repr(multi_ship_name)}")
                    print(f"   This confirms different AI prompts are being used!")
                else:
                    print(f"❌ BOTH ENDPOINTS FAILING: Both return incorrect ship name")
            else:
                print(f"❌ API FAILURES: One or both endpoints failed to respond")
            
            return single_result['success'] or multi_result['success']
            
        finally:
            # Clean up
            try:
                os.unlink(pdf_path)
                print(f"\n   Cleaned up: {pdf_path}")
            except:
                pass

def main():
    """Main execution"""
    tester = AIPromptComparisonTester()
    
    success = tester.run_comparison_test()
    
    if success:
        print("\n🎉 Comparison test completed - at least one endpoint working")
        return 0
    else:
        print("\n⚠️ Comparison test found issues with both endpoints")
        return 1

if __name__ == "__main__":
    sys.exit(main())