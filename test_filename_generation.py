"""
Unit tests for filename generation
"""
import sys
sys.path.insert(0, '/app/backend')

from app.utils.filename_helper import generate_audit_certificate_filename

def test_filename_generation():
    """Test various filename generation scenarios"""
    
    print("\n" + "="*70)
    print("TESTING FILENAME GENERATION")
    print("="*70)
    
    test_cases = [
        {
            "name": "Standard Full Term with extracted ship name",
            "input": {
                "ship_name": "MV EXAMPLE",
                "cert_type": "Full Term",
                "cert_abbreviation": "ISM-DOC",
                "issue_date": "2024-05-07",
                "original_filename": "certificate.pdf"
            },
            "expected_pattern": "MV_EXAMPLE_FullTerm_ISM-DOC_07052024.pdf"
        },
        {
            "name": "Interim with ship name from DB",
            "input": {
                "ship_name": "VINASHIP 01",
                "cert_type": "Interim",
                "cert_abbreviation": "ISPS",
                "issue_date": "15 November 2024",
                "original_filename": "scan.pdf"
            },
            "expected_pattern": "VINASHIP_01_Interim_ISPS_15112024.pdf"
        },
        {
            "name": "Short Term with special characters",
            "input": {
                "ship_name": "M/V TEST-SHIP #123",
                "cert_type": "Short term",
                "cert_abbreviation": "MLC (II)",
                "issue_date": "01/03/2024",
                "original_filename": "document.jpg"
            },
            "expected_contains": ["MV_TEST-SHIP_123", "ShortTerm", "MLC_II", "01032024", ".jpg"]
        },
        {
            "name": "Missing issue date (fallback to current)",
            "input": {
                "ship_name": "TEST VESSEL",
                "cert_type": "Full Term",
                "cert_abbreviation": "SSP",
                "issue_date": None,
                "original_filename": "file.pdf"
            },
            "expected_contains": ["TEST_VESSEL", "FullTerm", "SSP", ".pdf"]
        },
        {
            "name": "Long ship name (truncation test)",
            "input": {
                "ship_name": "VERY LONG SHIP NAME THAT EXCEEDS NORMAL LENGTH AND SHOULD BE TRUNCATED TO REASONABLE SIZE",
                "cert_type": "Full Term",
                "cert_abbreviation": "ISM",
                "issue_date": "2024-06-15",
                "original_filename": "cert.pdf"
            },
            "expected_contains": ["VERY_LONG_SHIP", "FullTerm", "ISM", "15062024"]
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'='*70}")
        
        # Generate filename
        result = generate_audit_certificate_filename(**test['input'])
        
        print(f"\nInput:")
        for key, value in test['input'].items():
            print(f"  {key}: {value}")
        
        print(f"\nGenerated filename:")
        print(f"  {result}")
        
        # Check result
        if 'expected_pattern' in test:
            if result == test['expected_pattern']:
                print(f"\n✅ PASS - Matches expected pattern exactly")
                passed += 1
            else:
                print(f"\n❌ FAIL")
                print(f"  Expected: {test['expected_pattern']}")
                print(f"  Got:      {result}")
                failed += 1
        elif 'expected_contains' in test:
            all_found = all(part in result for part in test['expected_contains'])
            if all_found:
                print(f"\n✅ PASS - Contains all expected parts")
                passed += 1
            else:
                print(f"\n❌ FAIL - Missing parts:")
                for part in test['expected_contains']:
                    if part not in result:
                        print(f"  Missing: {part}")
                failed += 1
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"\n{'✅ ALL TESTS PASSED' if failed == 0 else '❌ SOME TESTS FAILED'}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    test_filename_generation()
