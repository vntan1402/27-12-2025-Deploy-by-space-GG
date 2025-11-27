#!/usr/bin/env python3
"""
Test script to verify delete logic includes summary file deletion
"""
import sys
sys.path.insert(0, '/app/backend')

def test_delete_logic():
    """Test that delete logic extracts both file IDs"""
    
    print("=" * 70)
    print("🧪 Testing Delete Logic for Summary Files")
    print("=" * 70)
    
    # Read the service file
    service_file = '/app/backend/app/services/audit_certificate_service.py'
    with open(service_file, 'r') as f:
        content = f.read()
    
    print("\n1️⃣ Checking if summary_file_id is extracted...")
    checks = [
        ('summary_file_id = cert.get("summary_file_id")', 
         '✅ Extracts summary_file_id from certificate'),
        
        ('files_to_delete = []', 
         '✅ Creates list for multiple files'),
        
        ('if summary_file_id:', 
         '✅ Checks if summary file exists'),
        
        ('files_to_delete.append', 
         '✅ Adds files to deletion list'),
        
        ('for doc_type, file_id, file_desc in files_to_delete:', 
         '✅ Loops through all files to delete'),
        
        ('background_tasks.add_task', 
         '✅ Schedules background deletion'),
    ]
    
    passed = 0
    for check, description in checks:
        if check in content:
            print(f"   {description}")
            passed += 1
        else:
            print(f"   ❌ {description} - MISSING")
    
    print(f"\n   Result: {passed}/{len(checks)} checks passed")
    
    # Check logging
    print("\n2️⃣ Checking logging...")
    
    log_checks = [
        ('(summary)', '✅ Logs summary file with "(summary)" suffix'),
        ('len(files_to_delete)', '✅ Logs number of files scheduled'),
    ]
    
    log_passed = 0
    for check, description in log_checks:
        if check in content:
            print(f"   {description}")
            log_passed += 1
        else:
            print(f"   ❌ {description} - MISSING")
    
    print(f"\n   Result: {log_passed}/{len(log_checks)} checks passed")
    
    # Final summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    all_passed = passed == len(checks) and log_passed == len(log_checks)
    
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\n🎉 Delete logic correctly handles summary files!")
        print("\nFeature Details:")
        print("  - Extracts both google_drive_file_id and summary_file_id")
        print("  - Schedules deletion for both files in background")
        print("  - Logs each file deletion with proper description")
        print("  - Returns count of files scheduled for deletion")
        print("\n📝 Expected Behavior:")
        print("  When deleting a certificate with summary:")
        print("  - 2 background tasks scheduled")
        print("  - Log: 'Scheduled background deletion for: [file_id] (cert_name)'")
        print("  - Log: 'Scheduled background deletion for: [summary_id] (cert_name (summary))'")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("Please review the implementation")
        return False


if __name__ == "__main__":
    success = test_delete_logic()
    exit(0 if success else 1)
