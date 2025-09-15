#!/usr/bin/env python3
"""
Debug AI Analysis Function
Test the analyze_document_with_ai function directly to understand the issue
"""

import requests
import sys
import json
import tempfile
import os
import asyncio
from datetime import datetime, timezone

# Add the backend directory to the path so we can import the function
sys.path.append('/app/backend')

# Import the function we want to test
from server import analyze_document_with_ai, EMERGENT_LLM_KEY

class AIAnalysisDebugger:
    def __init__(self):
        self.test_pdf_url = "https://customer-assets.emergentagent.com/job_vessel-docs-1/artifacts/nzwrda4b_BROTHER%2036%20-%20IAPP%20-%20PM242838.pdf"

    def download_pdf(self):
        """Download the test PDF"""
        print("📥 Downloading test PDF...")
        try:
            response = requests.get(self.test_pdf_url, timeout=30)
            if response.status_code == 200:
                print(f"✅ Downloaded {len(response.content)} bytes")
                return response.content
            else:
                print(f"❌ Download failed: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Download error: {str(e)}")
            return None

    async def test_ai_analysis_function(self):
        """Test the analyze_document_with_ai function directly"""
        print("\n🤖 Testing analyze_document_with_ai function...")
        
        # Download PDF
        pdf_content = self.download_pdf()
        if not pdf_content:
            return False
        
        # Test AI configuration
        ai_config = {
            "provider": "OPENAI",
            "model": "gpt-4o",
            "api_key": EMERGENT_LLM_KEY,
            "max_tokens": 1000,
            "temperature": 0.1
        }
        
        print(f"🔑 Using Emergent LLM Key: {EMERGENT_LLM_KEY[:20]}..." if EMERGENT_LLM_KEY else "❌ No Emergent LLM Key found")
        
        try:
            # Call the function
            result = await analyze_document_with_ai(
                pdf_content, 
                "BROTHER_36_IAPP_PM242838.pdf", 
                "application/pdf", 
                ai_config
            )
            
            print(f"✅ AI Analysis completed successfully")
            print(f"📊 Result type: {type(result)}")
            print(f"📊 Result: {json.dumps(result, indent=2, default=str)}")
            
            # Check expected fields
            expected_category = "certificates"
            expected_ship_name = "BROTHER 36"
            
            category = result.get("category") if result else None
            ship_name = result.get("ship_name") if result else None
            
            print(f"\n🎯 Verification:")
            print(f"   Category: {category} (Expected: {expected_category}) {'✅' if category == expected_category else '❌'}")
            print(f"   Ship Name: {ship_name} (Expected: {expected_ship_name}) {'✅' if ship_name == expected_ship_name else '❌'}")
            
            return result is not None and category == expected_category and ship_name == expected_ship_name
            
        except Exception as e:
            print(f"❌ AI Analysis failed: {str(e)}")
            print(f"   Error type: {type(e)}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return False

    async def run_debug_test(self):
        """Run the debug test"""
        print("🔍 AI ANALYSIS FUNCTION DEBUG TEST")
        print("=" * 50)
        
        success = await self.test_ai_analysis_function()
        
        print("\n" + "=" * 50)
        print("📊 DEBUG TEST RESULTS")
        print("=" * 50)
        
        if success:
            print("🎉 AI Analysis function is working correctly!")
            print("✅ Document classification and ship name extraction working")
        else:
            print("⚠️ AI Analysis function has issues")
            print("❌ Need to investigate further")
        
        return success

async def main():
    """Main debug execution"""
    debugger = AIAnalysisDebugger()
    success = await debugger.run_debug_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))