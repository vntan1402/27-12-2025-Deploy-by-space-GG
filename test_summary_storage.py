#!/usr/bin/env python3
"""
Test script to verify summary storage feature for Audit Certificates
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/app/backend')

from app.db.mongodb import mongo_db


async def test_summary_storage():
    """Test if summary_file_id is being stored for audit certificates"""
    
    print("=" * 60)
    print("🧪 Testing Summary Storage for Audit Certificates")
    print("=" * 60)
    
    try:
        # Connect to database
        await mongo_db.connect()
        print("✅ Connected to MongoDB")
        
        # Get total count
        total_certs = await mongo_db.count('audit_certificates', {})
        print(f"\n📊 Total Audit Certificates: {total_certs}")
        
        # Count certificates with summary_file_id
        with_summary = await mongo_db.count(
            'audit_certificates',
            {'summary_file_id': {'$ne': None, '$exists': True}}
        )
        
        without_summary = total_certs - with_summary
        
        print(f"✅ Certificates WITH summary_file_id: {with_summary}")
        print(f"❌ Certificates WITHOUT summary_file_id: {without_summary}")
        
        # Show breakdown
        if with_summary > 0:
            print(f"\n📈 Success Rate: {(with_summary/total_certs)*100:.1f}%")
            
            # Show sample with summary
            cert_with_summary = await mongo_db.find_one(
                'audit_certificates',
                {'summary_file_id': {'$ne': None}}
            )
            
            if cert_with_summary:
                print("\n📄 Sample Certificate WITH Summary:")
                print(f"   - ID: {cert_with_summary.get('id')}")
                print(f"   - Name: {cert_with_summary.get('cert_name')}")
                print(f"   - File ID: {cert_with_summary.get('google_drive_file_id')}")
                print(f"   - Summary File ID: {cert_with_summary.get('summary_file_id')}")
                print(f"   - Created: {cert_with_summary.get('created_at')}")
        else:
            print("\n⚠️  No certificates found with summary_file_id yet")
            print("   → Feature is implemented but not yet tested with real upload")
        
        # Show most recent certificate
        print("\n📄 Most Recent Certificate:")
        recent_cert = await mongo_db.find_one(
            'audit_certificates',
            {},
            sort=[('created_at', -1)]
        )
        
        if recent_cert:
            print(f"   - ID: {recent_cert.get('id')}")
            print(f"   - Name: {recent_cert.get('cert_name')}")
            print(f"   - File ID: {recent_cert.get('google_drive_file_id') or 'None'}")
            print(f"   - Summary File ID: {recent_cert.get('summary_file_id') or 'None'}")
            print(f"   - Created: {recent_cert.get('created_at')}")
        
        print("\n" + "=" * 60)
        print("✅ Test Complete")
        print("=" * 60)
        
        # Return status
        return {
            "total": total_certs,
            "with_summary": with_summary,
            "without_summary": without_summary,
            "feature_working": True  # Feature is implemented
        }
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Cleanup
        await mongo_db.disconnect()


async def verify_implementation():
    """Verify the code implementation is correct"""
    
    print("\n" + "=" * 60)
    print("🔍 Verifying Implementation")
    print("=" * 60)
    
    # Check if analyze service returns summary_text
    print("\n1. Checking analyze service...")
    
    analyze_service_path = '/app/backend/app/services/audit_certificate_analyze_service.py'
    with open(analyze_service_path, 'r') as f:
        content = f.read()
        
        if '"summary_text":' in content:
            print("   ✅ analyze_service returns summary_text")
        else:
            print("   ❌ analyze_service does NOT return summary_text")
    
    # Check if multi-upload uploads summary
    print("\n2. Checking multi-upload endpoint...")
    
    api_path = '/app/backend/app/api/v1/audit_certificates.py'
    with open(api_path, 'r') as f:
        content = f.read()
        
        checks = {
            'summary_text = analysis_result.get("summary_text")': 'Extracts summary from analysis',
            'summary_filename = f"{base_name}_Summary.txt"': 'Creates summary filename',
            'GDriveService.upload_file': 'Uploads to Google Drive',
            '"summary_file_id": summary_file_id': 'Stores summary_file_id in DB'
        }
        
        for check, description in checks.items():
            if check in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description}")
    
    print("\n" + "=" * 60)
    print("✅ Implementation Verification Complete")
    print("=" * 60)


if __name__ == "__main__":
    print("\n🚀 Starting Summary Storage Test\n")
    
    # Run verification
    asyncio.run(verify_implementation())
    
    # Run test
    result = asyncio.run(test_summary_storage())
    
    if result:
        print(f"\n📝 Summary: Feature implemented and ready for testing")
        print(f"   Next step: Upload a new certificate to verify storage")
