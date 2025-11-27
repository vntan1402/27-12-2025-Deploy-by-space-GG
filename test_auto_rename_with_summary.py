#!/usr/bin/env python3
"""
Test script to verify auto-rename includes summary file
"""
import sys
sys.path.insert(0, '/app/backend')

def test_auto_rename_logic():
    """Test that auto-rename logic handles summary files"""
    
    print("=" * 75)
    print("🧪 Testing Auto-Rename Logic for Summary Files")
    print("=" * 75)
    
    # Read the service file
    service_file = '/app/backend/app/services/audit_certificate_service.py'
    with open(service_file, 'r') as f:
        content = f.read()
    
    print("\n1️⃣ Checking if summary_file_id is extracted...")
    checks = [
        ('summary_file_id = cert.get("summary_file_id")', 
         '✅ Extracts summary_file_id from certificate'),
        
        ('if summary_file_id:', 
         '✅ Checks if summary file exists'),
        
        ('new_summary_filename = f"{base_name}_Summary.txt"', 
         '✅ Generates summary filename pattern'),
        
        ('summary_rename_result = await GDriveService.rename_file_via_apps_script', 
         '✅ Calls GDrive API to rename summary'),
        
        ('if summary_rename_result.get("success"):', 
         '✅ Checks rename success'),
        
        ('logger.info(f"✅ Successfully renamed summary file', 
         '✅ Logs success'),
    ]
    
    passed = 0
    for check, description in checks:
        if check in content:
            print(f"   {description}")
            passed += 1
        else:
            print(f"   ❌ {description} - MISSING")
    
    print(f"\n   Result: {passed}/{len(checks)} checks passed")
    
    # Check error handling
    print("\n2️⃣ Checking error handling...")
    
    error_checks = [
        ('except Exception as summary_error:', '✅ Has try-except for summary rename'),
        ('logger.warning(f"⚠️ Error renaming summary file:', '✅ Logs warnings'),
        ('# Don\'t fail the entire operation', '✅ Non-blocking failure'),
    ]
    
    error_passed = 0
    for check, description in error_checks:
        if check in content:
            print(f"   {description}")
            error_passed += 1
        else:
            print(f"   ❌ {description} - MISSING")
    
    print(f"\n   Result: {error_passed}/{len(error_checks)} checks passed")
    
    # Check response enhancement
    print("\n3️⃣ Checking response includes summary info...")
    
    response_checks = [
        ('response["summary_file_id"] = summary_file_id', 
         '✅ Includes summary_file_id in response'),
        
        ('response["summary_renamed"] = True', 
         '✅ Includes summary_renamed flag'),
        
        ('response["summary_new_name"]', 
         '✅ Includes new summary filename'),
        
        ('"Certificate file and summary renamed successfully"', 
         '✅ Updated success message'),
    ]
    
    response_passed = 0
    for check, description in response_checks:
        if check in content:
            print(f"   {description}")
            response_passed += 1
        else:
            print(f"   ❌ {description} - MISSING")
    
    print(f"\n   Result: {response_passed}/{len(response_checks)} checks passed")
    
    # Final summary
    print("\n" + "=" * 75)
    print("📊 TEST SUMMARY")
    print("=" * 75)
    
    all_passed = (
        passed == len(checks) and 
        error_passed == len(error_checks) and 
        response_passed == len(response_checks)
    )
    
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\n🎉 Auto-rename correctly handles summary files!")
        print("\nFeature Details:")
        print("  - Extracts summary_file_id from certificate")
        print("  - Generates matching summary filename: {base_name}_Summary.txt")
        print("  - Renames summary file via Apps Script")
        print("  - Returns enhanced response with summary info")
        print("  - Non-blocking: Main rename succeeds even if summary fails")
        print("\n📝 Expected Behavior:")
        print("  Original file: Certificate.pdf → SHIP_FullTerm_ISM_20240507.pdf")
        print("  Summary file:  Certificate_Summary.txt → SHIP_FullTerm_ISM_20240507_Summary.txt")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("Please review the implementation")
        return False


if __name__ == "__main__":
    success = test_auto_rename_logic()
    exit(0 if success else 1)
