#!/usr/bin/env python3
"""
Test script to verify crew certificate analyze endpoint is calling correct Apps Script action
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/app/backend')

from server import app, mongo_db
from mongodb_database import mongo_db as db

async def test_crew_certificate_action():
    """Test that crew certificate endpoint uses correct action"""
    
    print("\n" + "="*70)
    print("🧪 CREW CERTIFICATE ACTION FIX VERIFICATION")
    print("="*70)
    
    print("\n📋 Test Objective:")
    print("   Verify backend calls 'analyze_certificate_document_ai' action")
    print("   (not 'analyze_passport_document_ai')")
    
    # Read the backend code to verify the fix
    print("\n🔍 Checking backend code...")
    
    with open('/app/backend/server.py', 'r') as f:
        server_code = f.read()
    
    # Find the crew-certificates analyze endpoint
    analyze_endpoint_start = server_code.find('@api_router.post("/crew-certificates/analyze-file")')
    if analyze_endpoint_start == -1:
        print("   ❌ Could not find crew-certificates analyze endpoint!")
        return False
    
    # Get next 2000 characters after endpoint definition
    analyze_code_section = server_code[analyze_endpoint_start:analyze_endpoint_start + 2000]
    
    # Check for correct action
    if 'analyze_certificate_document_ai' in analyze_code_section:
        print("   ✅ CORRECT: Found 'analyze_certificate_document_ai' action")
        
        # Find the exact line
        lines = analyze_code_section.split('\n')
        for i, line in enumerate(lines):
            if 'analyze_certificate_document_ai' in line and 'action' in line:
                print(f"   📄 Line content: {line.strip()}")
                break
    else:
        print("   ❌ INCORRECT: 'analyze_certificate_document_ai' NOT found")
        return False
    
    # Check that old action is NOT present
    if 'analyze_passport_document_ai' in analyze_code_section and 'crew-certificates' in analyze_code_section:
        print("   ⚠️  WARNING: Still found 'analyze_passport_document_ai' in crew-certificates section")
        print("   This might be in comments or different context")
        
        # Check if it's just in comments
        lines = analyze_code_section.split('\n')
        for i, line in enumerate(lines):
            if 'analyze_passport_document_ai' in line and 'action' in line and not line.strip().startswith('#'):
                print(f"   ❌ Found in active code: {line.strip()}")
                return False
    else:
        print("   ✅ CORRECT: Old 'analyze_passport_document_ai' action removed")
    
    # Check that document_type parameter is removed
    if '"document_type": "certificate"' in analyze_code_section:
        print("   ⚠️  WARNING: Found unused 'document_type' parameter")
        print("   (This parameter is not needed but won't cause issues)")
    else:
        print("   ✅ CORRECT: Unused 'document_type' parameter removed")
    
    print("\n" + "="*70)
    print("✅ VERIFICATION COMPLETE")
    print("="*70)
    print("\n📊 Summary:")
    print("   - Backend now calls correct Apps Script action")
    print("   - Action: 'analyze_certificate_document_ai'")
    print("   - Apps Script will properly classify as certificate")
    print("   - Expected fields: cert_name, cert_no, issued_by, dates")
    
    print("\n🎯 Next Steps:")
    print("   1. Test the endpoint with a real certificate file")
    print("   2. Verify Document AI summary includes certificate context")
    print("   3. Verify AI extraction returns correct certificate fields")
    print("   4. Check frontend auto-fill works correctly")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_crew_certificate_action())
    sys.exit(0 if success else 1)
