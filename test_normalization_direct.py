#!/usr/bin/env python3
"""
Direct test of the normalize_issued_by function
"""

import sys
import os
sys.path.append('/app/backend')

# Import the normalization function directly
from server import normalize_issued_by

def test_normalize_function():
    """Test the normalize_issued_by function directly"""
    
    print("🔍 Testing normalize_issued_by function directly...")
    
    # Test cases
    test_cases = [
        {
            "input": {"issued_by": "RERL Maritime Authority of the Republic of Panama"},
            "expected": "Panama Maritime Authority"
        },
        {
            "input": {"issued_by": "Socialist Republic of Vietnam Maritime Administration"},
            "expected": "Vietnam Maritime Administration"
        },
        {
            "input": {"issued_by": "The Government of Marshall Islands"},
            "expected": "Marshall Islands Maritime Administrator"
        },
        {
            "input": {"issued_by": "Panama Maritime Authority"},
            "expected": "Panama Maritime Authority"  # Should remain the same
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}:")
        print(f"   Input: {test_case['input']['issued_by']}")
        
        # Call the normalization function
        result = normalize_issued_by(test_case['input'].copy())
        
        print(f"   Output: {result.get('issued_by', 'NOT FOUND')}")
        print(f"   Expected: {test_case['expected']}")
        
        if result.get('issued_by') == test_case['expected']:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")
    
    print("\n🔍 Testing with empty/missing issued_by...")
    
    # Test with empty issued_by
    empty_test = normalize_issued_by({"issued_by": ""})
    print(f"   Empty string result: {empty_test}")
    
    # Test with missing issued_by
    missing_test = normalize_issued_by({})
    print(f"   Missing field result: {missing_test}")
    
    print("\n✅ Direct normalization function test completed")

if __name__ == "__main__":
    test_normalize_function()