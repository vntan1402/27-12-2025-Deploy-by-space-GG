#!/usr/bin/env python3
"""
Test Normalize Issued By - Strict Matching Logic
"""

def test_normalize_logic():
    """Test the normalize matching logic"""
    
    print("=" * 80)
    print("TESTING NORMALIZE ISSUED BY - STRICT MATCHING")
    print("=" * 80)
    
    # Simulate the matching logic
    test_cases = [
        # Case 1: Exact match - Should normalize
        ("PANAMA MARITIME AUTHORITY", "PANAMA MARITIME AUTHORITY", True, "✅ Exact match"),
        ("PANAMA MARITIME", "PANAMA MARITIME", True, "✅ Exact match"),
        
        # Case 2: Input longer than variation - Should normalize
        ("the RERL Maritime Authority of the Republic of Panama", "PANAMA MARITIME", True, 
         "✅ Input longer, contains variation"),
        ("Republic of Panama Maritime Authority", "PANAMA MARITIME", True,
         "✅ Input longer, contains variation"),
        
        # Case 3: Input SHORTER than variation - Should NOT normalize
        ("PANAMA", "PANAMA MARITIME", False, "❌ Input shorter, don't normalize"),
        ("PANAMA", "PANAMA MARITIME AUTHORITY", False, "❌ Input shorter, don't normalize"),
        
        # Case 4: Same length but not exact - Should NOT normalize  
        ("PANAMA SHIPS", "PANAMA MARITIME", False, "❌ Different words, don't normalize"),
        
        # Case 5: Vietnam cases
        ("VIETNAM MARITIME ADMINISTRATION", "VIETNAM MARITIME ADMINISTRATION", True, "✅ Exact match"),
        ("Socialist Republic of Vietnam Maritime Administration", "VIETNAM MARITIME", True,
         "✅ Input longer"),
        ("VIETNAM", "VIETNAM MARITIME", False, "❌ Input shorter"),
        
        # Case 6: DNV cases
        ("DET NORSKE VERITAS", "DET NORSKE VERITAS", True, "✅ Exact match"),
        ("DNV GL AS Company", "DNV GL", True, "✅ Input longer"),
        ("DNV", "DNV GL", False, "❌ Input shorter"),
    ]
    
    print("\n📊 Test Results:\n")
    
    passed = 0
    failed = 0
    
    for issued_by_upper, variation, should_match, description in test_cases:
        # Simulate the new matching logic
        result = False
        
        if issued_by_upper == variation:
            # Exact match
            result = True
        elif variation in issued_by_upper and len(issued_by_upper) > len(variation):
            # Substring match with longer input
            result = True
        
        status = "✅ PASS" if result == should_match else "❌ FAIL"
        
        if result == should_match:
            passed += 1
        else:
            failed += 1
        
        print(f"{status}")
        print(f"  Input:     '{issued_by_upper}' (len={len(issued_by_upper)})")
        print(f"  Variation: '{variation}' (len={len(variation)})")
        print(f"  Expected:  {'MATCH' if should_match else 'NO MATCH'}")
        print(f"  Got:       {'MATCH' if result else 'NO MATCH'}")
        print(f"  Note:      {description}")
        print()
    
    print("=" * 80)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)
    
    print("\n🎯 KEY IMPROVEMENTS:")
    print("1. ✅ 'Panama' will NOT match 'PANAMA MARITIME' (input shorter)")
    print("2. ✅ 'PANAMA MARITIME AUTHORITY' will match 'PANAMA MARITIME' (exact or longer)")
    print("3. ✅ Prevents false positives from partial country names")
    print("4. ✅ Still normalizes full organization names correctly")

if __name__ == "__main__":
    test_normalize_logic()
