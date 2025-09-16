#!/usr/bin/env python3
"""
Test script để xem AI analysis thực tế cho Ship Survey Status
"""
import asyncio
import os
import sys
sys.path.append('/app/backend')

from server import analyze_document_with_ai
import json

async def test_ai_analysis():
    """Test AI analysis with sample document"""
    
    # Mock AI config
    ai_config = {
        "provider": "emergent",
        "model": "gemini/gemini-2.0-flash",
        "api_key": "sk-emergent-eEe35Fb1b449940199"
    }
    
    # Mock file content (example text of a maritime certificate)
    sample_text = """
    PANAMA MARITIME AUTHORITY
    INTERNATIONAL AIR POLLUTION PREVENTION CERTIFICATE (IAPP)
    
    Ship Name: BROTHER 36
    IMO Number: 9876543
    Certificate Number: PM242838
    Certificate Type: Full Term
    Issue Date: 10 December 2024
    Valid Until: 18 March 2028
    Issued by: Panama Maritime Documentation Services Inc
    
    Survey Information:
    - Certificate Type: STATUTORY
    - Survey Type: Renewal
    - Issuance Date: 10 December 2024
    - Expiration Date: 18 March 2028
    - Renewal Range Start: 18 September 2027
    - Renewal Range End: 18 March 2029
    - Due Date 1: 18 March 2025
    - Due Date 2: 18 March 2026
    - Due Date 3: 18 March 2027
    """
    
    # Convert to bytes (simulate file content)
    file_content = sample_text.encode('utf-8')
    filename = "BROTHER_36_IAPP_Certificate.pdf"
    content_type = "application/pdf"
    
    print("🧪 Testing AI Analysis for Ship Survey Status...")
    print("=" * 60)
    
    try:
        # Call AI analysis
        result = await analyze_document_with_ai(file_content, filename, content_type, ai_config)
        
        print("📄 AI ANALYSIS RESULT:")
        print(json.dumps(result, indent=2, default=str))
        
        print("\n" + "=" * 60)
        print("📊 EXTRACTED INFORMATION BREAKDOWN:")
        print("=" * 60)
        
        # Certificate Info
        print("🏆 CERTIFICATE INFORMATION:")
        cert_fields = ['category', 'cert_name', 'cert_type', 'cert_no', 'issue_date', 'valid_date', 'issued_by']
        for field in cert_fields:
            value = result.get(field, 'Not found')
            print(f"  {field}: {value}")
        
        # Ship Info
        print("\n🚢 SHIP INFORMATION:")
        ship_name = result.get('ship_name', 'Not found')
        print(f"  ship_name: {ship_name}")
        
        # Survey Status Info
        print("\n📋 SURVEY STATUS INFORMATION:")
        survey_fields = ['certificate_type', 'survey_type', 'issuance_date', 'expiration_date', 
                        'renewal_range_start', 'renewal_range_end', 'due_dates']
        
        survey_info = result.get('survey_info', {})
        if survey_info:
            print("  Survey info found:")
            for field in survey_fields:
                value = survey_info.get(field, 'Not found')
                print(f"    {field}: {value}")
        else:
            print("  ❌ No survey_info found in AI response")
            
        # Check if all required fields exist
        print("\n" + "=" * 60)
        print("✅ VALIDATION SUMMARY:")
        print("=" * 60)
        
        # Required for Certificate creation
        cert_required = ['category', 'ship_name', 'cert_name']
        cert_missing = [f for f in cert_required if not result.get(f)]
        if cert_missing:
            print(f"❌ Missing certificate fields: {cert_missing}")
        else:
            print("✅ All required certificate fields present")
            
        # Required for Survey Status creation
        if survey_info:
            survey_required = ['certificate_type', 'survey_type']
            survey_missing = [f for f in survey_required if not survey_info.get(f)]
            if survey_missing:
                print(f"❌ Missing survey status fields: {survey_missing}")
            else:
                print("✅ All required survey status fields present")
        else:
            print("❌ No survey_info section found - Survey Status won't be created")
            
    except Exception as e:
        print(f"❌ Error during AI analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_analysis())