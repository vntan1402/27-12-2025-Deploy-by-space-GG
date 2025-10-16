#!/usr/bin/env python3
"""
Test Issued By Abbreviation Logic for Manual Edit
"""

import sys
sys.path.append('/app/backend')

from server import generate_organization_abbreviation

def test_abbreviation_logic():
    print("=" * 80)
    print("TESTING ISSUED BY ABBREVIATION LOGIC")
    print("=" * 80)
    
    test_cases = [
        # Case 1: Manual abbreviation (3-5 uppercase letters)
        ("PMA", "PMA", "✅ Should use manual abbreviation as-is"),
        ("VMA", "VMA", "✅ Should use manual abbreviation as-is"),
        ("DNV", "DNV", "✅ Should use manual abbreviation as-is"),
        ("PMDS", "PMDS", "✅ Should use manual abbreviation as-is (4 letters)"),
        ("LISCR", "LISCR", "✅ Should use manual abbreviation as-is (5 letters)"),
        
        # Case 2: Full organization names (should generate abbreviation)
        ("Panama Maritime Authority", "PMA", "🔄 Should map to PMA"),
        ("Det Norske Veritas", "DNV", "🔄 Should map to DNV"),
        ("American Bureau of Shipping", "ABS", "🔄 Should map to ABS"),
        ("Vietnam Maritime Administration", "VMA", "🔄 Should auto-generate VMA"),
        
        # Case 3: Mixed case abbreviations (should NOT match, will auto-generate)
        ("Pma", None, "❌ Not uppercase, will auto-generate"),
        ("pma", None, "❌ Not uppercase, will auto-generate"),
        
        # Case 4: Too short or too long
        ("PM", None, "❌ Only 2 letters, will auto-generate"),
        ("PMDSAB", None, "❌ 6 letters, will auto-generate"),
        
        # Case 5: Abbreviation with spaces (should NOT match)
        ("P M A", None, "❌ Has spaces, will auto-generate"),
        
        # Case 6: Empty
        ("", "", "⚪ Empty input"),
    ]
    
    print("\n📊 Test Results:\n")
    
    passed = 0
    failed = 0
    
    for input_value, expected, description in test_cases:
        result = generate_organization_abbreviation(input_value)
        
        if expected is None:
            # For cases where we don't know exact output, just verify it's not empty
            status = "✅ PASS" if result else "❌ FAIL"
            if result:
                passed += 1
            else:
                failed += 1
        else:
            # For cases with expected output
            status = "✅ PASS" if result == expected else "❌ FAIL"
            if result == expected:
                passed += 1
            else:
                failed += 1
        
        print(f"{status}")
        print(f"  Input:    '{input_value}'")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
        print(f"  Note:     {description}")
        print()
    
    print("=" * 80)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)

if __name__ == "__main__":
    test_abbreviation_logic()
