#!/usr/bin/env python3
"""
AI Consistency Test - Test multiple runs to identify inconsistency in ship name extraction
"""

import requests
import sys
import json
import os
import tempfile
from datetime import datetime, timezone
import time

class AIConsistencyTester:
    def __init__(self, base_url="https://continue-session.preview.emergentagent.com"):
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

    def test_single_analysis(self, pdf_path, run_number):
        """Test a single AI analysis"""
        headers = {'Authorization': f'Bearer {self.token}'}
        
        with open(pdf_path, 'rb') as pdf_file:
            files = {'file': (f'BROTHER_36_EIAPP_run_{run_number}.pdf', pdf_file, 'application/pdf')}
            
            # Make the request
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
                    
                    return {
                        'success': True,
                        'ship_name': ship_name,
                        'flag': analysis.get('flag'),
                        'built_year': analysis.get('built_year'),
                        'imo_number': analysis.get('imo_number'),
                        'full_response': analysis
                    }
                        
                except json.JSONDecodeError as e:
                    return {
                        'success': False,
                        'error': f"JSON decode error: {e}",
                        'raw_response': response.text
                    }
            else:
                try:
                    error_data = response.json()
                    return {
                        'success': False,
                        'error': f"API error {response.status_code}: {error_data}",
                        'status_code': response.status_code
                    }
                except:
                    return {
                        'success': False,
                        'error': f"API error {response.status_code}: {response.text}",
                        'status_code': response.status_code
                    }

    def run_consistency_test(self, num_runs=5):
        """Run multiple AI analysis tests to check consistency"""
        print("🔍 AI Consistency Test for Ship Name Extraction")
        print("=" * 60)
        print(f"Target PDF: {self.test_pdf_url}")
        print(f"Expected Ship Name: {self.expected_ship_name}")
        print(f"Number of test runs: {num_runs}")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            return False
        
        # Step 2: Download PDF
        pdf_path = self.download_pdf()
        if not pdf_path:
            return False
        
        try:
            results = []
            correct_extractions = 0
            null_extractions = 0
            incorrect_extractions = 0
            
            print(f"\n🤖 Running {num_runs} AI Analysis Tests...")
            
            for i in range(1, num_runs + 1):
                print(f"\n--- Run {i}/{num_runs} ---")
                
                result = self.test_single_analysis(pdf_path, i)
                results.append(result)
                
                if result['success']:
                    ship_name = result['ship_name']
                    
                    if ship_name == self.expected_ship_name:
                        print(f"✅ Run {i}: CORRECT - '{ship_name}'")
                        correct_extractions += 1
                    elif ship_name is None:
                        print(f"❌ Run {i}: NULL - ship_name is None")
                        null_extractions += 1
                    else:
                        print(f"⚠️ Run {i}: INCORRECT - '{ship_name}' (expected '{self.expected_ship_name}')")
                        incorrect_extractions += 1
                    
                    # Show other extracted fields for context
                    print(f"   Flag: {result['flag']}")
                    print(f"   Built Year: {result['built_year']}")
                    print(f"   IMO: {result['imo_number']}")
                else:
                    print(f"❌ Run {i}: FAILED - {result['error']}")
                
                # Small delay between requests
                time.sleep(2)
            
            # Summary
            print("\n" + "=" * 60)
            print("📊 CONSISTENCY TEST RESULTS")
            print("=" * 60)
            
            total_successful = correct_extractions + null_extractions + incorrect_extractions
            failed_requests = num_runs - total_successful
            
            print(f"Total Runs: {num_runs}")
            print(f"Successful API Calls: {total_successful}")
            print(f"Failed API Calls: {failed_requests}")
            print(f"")
            print(f"✅ Correct Ship Name Extractions: {correct_extractions} ({correct_extractions/num_runs*100:.1f}%)")
            print(f"❌ NULL Ship Name Extractions: {null_extractions} ({null_extractions/num_runs*100:.1f}%)")
            print(f"⚠️ Incorrect Ship Name Extractions: {incorrect_extractions} ({incorrect_extractions/num_runs*100:.1f}%)")
            
            # Analysis
            print(f"\n🔍 ANALYSIS:")
            if correct_extractions == num_runs:
                print(f"✅ ISSUE RESOLVED: All {num_runs} runs correctly extracted '{self.expected_ship_name}'")
            elif correct_extractions > 0 and null_extractions > 0:
                print(f"⚠️ INCONSISTENCY DETECTED: AI sometimes extracts correctly, sometimes returns NULL")
                print(f"   This suggests an issue with AI prompt consistency or PDF processing")
            elif null_extractions == num_runs:
                print(f"❌ PERSISTENT ISSUE: All {num_runs} runs returned NULL for ship_name")
                print(f"   This suggests a systematic issue with the AI prompt or PDF content extraction")
            else:
                print(f"⚠️ MIXED RESULTS: Inconsistent behavior detected")
            
            # Show detailed results for debugging
            print(f"\n📋 DETAILED RESULTS:")
            for i, result in enumerate(results, 1):
                if result['success']:
                    print(f"Run {i}: ship_name='{result['ship_name']}', flag='{result['flag']}', year={result['built_year']}")
                else:
                    print(f"Run {i}: FAILED - {result['error']}")
            
            return correct_extractions > 0
            
        finally:
            # Clean up
            try:
                os.unlink(pdf_path)
                print(f"\n   Cleaned up: {pdf_path}")
            except:
                pass

def main():
    """Main execution"""
    tester = AIConsistencyTester()
    
    # Run 5 tests to check consistency
    success = tester.run_consistency_test(num_runs=5)
    
    if success:
        print("\n🎉 AI analysis can extract ship name correctly (at least sometimes)")
        return 0
    else:
        print("\n⚠️ AI analysis consistently fails to extract ship name")
        return 1

if __name__ == "__main__":
    sys.exit(main())