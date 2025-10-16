#!/usr/bin/env python3
"""
Test Real Normalize Function
"""

def simulate_normalize(issued_by: str) -> tuple:
    """Simulate the normalize_issued_by logic"""
    
    issued_by_upper = issued_by.upper().strip()
    
    # Test variations
    MARITIME_AUTHORITIES = {
        'Panama Maritime Authority': [
            'PANAMA MARITIME AUTHORITY',
            'PANAMA MARITIME',
            'REPUBLIC OF PANAMA MARITIME',
        ],
        'Vietnam Maritime Administration': [
            'VIETNAM MARITIME ADMINISTRATION',
            'VIETNAM MARITIME',
            'SOCIALIST REPUBLIC OF VIETNAM MARITIME',
        ],
        'Det Norske Veritas': [
            'DET NORSKE VERITAS',
            'DNV GL',
            'DNV'
        ]
    }
    
    # Check for matches with STRICT rules
    for standard_name, variations in MARITIME_AUTHORITIES.items():
        for variation in variations:
            if issued_by_upper == variation:
                # Exact match
                return (standard_name, f"Exact match with '{variation}'")
            elif variation in issued_by_upper and len(issued_by_upper) > len(variation):
                # Substring match with longer input
                return (standard_name, f"Contains '{variation}', input longer")
    
    # No match
    return (issued_by, "No match, keep original")

def test_real_cases():
    print("=" * 80)
    print("TESTING REAL NORMALIZE CASES")
    print("=" * 80)
    
    test_cases = [
        # Should normalize
        ("Panama Maritime Authority", "Panama Maritime Authority", True),
        ("the RERL Maritime Authority of the Republic of Panama", "Panama Maritime Authority", True),
        ("Republic of Panama Maritime Authority", "Panama Maritime Authority", True),
        ("Vietnam Maritime Administration", "Vietnam Maritime Administration", True),
        ("Socialist Republic of Vietnam Maritime Administration", "Vietnam Maritime Administration", True),
        ("Det Norske Veritas", "Det Norske Veritas", True),
        ("DNV GL AS Company", "Det Norske Veritas", True),
        
        # Should NOT normalize
        ("Panama", "Panama", False),
        ("PANAMA", "PANAMA", False),
        ("Vietnam", "Vietnam", False),
        ("DNV", "DNV", False),
    ]
    
    print("\n📊 Test Results:\n")
    
    for input_val, expected_output, should_normalize in test_cases:
        result, reason = simulate_normalize(input_val)
        
        is_normalized = result != input_val
        status = "✅ PASS" if is_normalized == should_normalize else "❌ FAIL"
        
        print(f"{status}")
        print(f"  Input:    '{input_val}'")
        print(f"  Expected: '{expected_output}' ({'NORMALIZE' if should_normalize else 'KEEP ORIGINAL'})")
        print(f"  Got:      '{result}' ({'NORMALIZED' if is_normalized else 'KEPT'})")
        print(f"  Reason:   {reason}")
        print()

if __name__ == "__main__":
    test_real_cases()
