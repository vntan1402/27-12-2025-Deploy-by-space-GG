#!/usr/bin/env python3
"""
Test Issued By Abbreviation Logic - Direct Function Test
"""

import re

def test_abbreviation_detection():
    """Test the regex pattern for detecting manual abbreviations"""
    
    print("=" * 80)
    print("TESTING ABBREVIATION DETECTION PATTERN")
    print("=" * 80)
    
    test_cases = [
        # Should match (3-5 uppercase letters)
        ("PMA", True),
        ("VMA", True),
        ("DNV", True),
        ("ABS", True),
        ("PMDS", True),
        ("LISCR", True),
        
        # Should NOT match
        ("Panama Maritime Authority", False),
        ("Pma", False),  # Mixed case
        ("pma", False),  # Lowercase
        ("PM", False),   # Too short (2 letters)
        ("PMDSAB", False),  # Too long (6 letters)
        ("P M A", False),  # Has spaces
        ("DNV-GL", False),  # Has special char
        ("", False),  # Empty
    ]
    
    pattern = r'^[A-Z]{3,5}$'
    
    print("\n📊 Test Results:\n")
    
    passed = 0
    failed = 0
    
    for input_value, should_match in test_cases:
        result = bool(re.match(pattern, input_value))
        status = "✅ PASS" if result == should_match else "❌ FAIL"
        
        if result == should_match:
            passed += 1
        else:
            failed += 1
        
        print(f"{status}")
        print(f"  Input:    '{input_value}'")
        print(f"  Expected: {should_match}")
        print(f"  Got:      {result}")
        print()
    
    print("=" * 80)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)

if __name__ == "__main__":
    test_abbreviation_detection()
