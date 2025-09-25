#!/usr/bin/env python3
"""
Direct test of the format_dry_dock_cycle_display function
"""

import sys
import os
sys.path.append('/app/backend')

from datetime import datetime
from server import format_dry_dock_cycle_display, DryDockCycle

def test_format_function():
    """Test the format_dry_dock_cycle_display function directly"""
    print("🔧 Testing format_dry_dock_cycle_display function directly...")
    
    # Test case 1: Normal case with intermediate docking
    dry_dock_1 = DryDockCycle(
        from_date=datetime(2024, 1, 15),
        to_date=datetime(2029, 1, 15),
        intermediate_docking_required=True,
        last_intermediate_docking=datetime(2024, 2, 10)
    )
    
    result_1 = format_dry_dock_cycle_display(dry_dock_1)
    expected_1 = "15/01/2024 - 15/01/2029 (Int. required)"
    
    print(f"Test 1 - With intermediate docking:")
    print(f"  Expected: {expected_1}")
    print(f"  Actual:   {result_1}")
    print(f"  Result:   {'✅ PASS' if result_1 == expected_1 else '❌ FAIL'}")
    
    # Test case 2: Without intermediate docking
    dry_dock_2 = DryDockCycle(
        from_date=datetime(2024, 1, 15),
        to_date=datetime(2029, 1, 15),
        intermediate_docking_required=False
    )
    
    result_2 = format_dry_dock_cycle_display(dry_dock_2)
    expected_2 = "15/01/2024 - 15/01/2029"
    
    print(f"\nTest 2 - Without intermediate docking:")
    print(f"  Expected: {expected_2}")
    print(f"  Actual:   {result_2}")
    print(f"  Result:   {'✅ PASS' if result_2 == expected_2 else '❌ FAIL'}")
    
    # Test case 3: Different dates
    dry_dock_3 = DryDockCycle(
        from_date=datetime(2023, 12, 31),
        to_date=datetime(2028, 12, 31),
        intermediate_docking_required=True
    )
    
    result_3 = format_dry_dock_cycle_display(dry_dock_3)
    expected_3 = "31/12/2023 - 31/12/2028 (Int. required)"
    
    print(f"\nTest 3 - Different dates:")
    print(f"  Expected: {expected_3}")
    print(f"  Actual:   {result_3}")
    print(f"  Result:   {'✅ PASS' if result_3 == expected_3 else '❌ FAIL'}")
    
    # Test case 4: None input
    result_4 = format_dry_dock_cycle_display(None)
    expected_4 = "-"
    
    print(f"\nTest 4 - None input:")
    print(f"  Expected: {expected_4}")
    print(f"  Actual:   {result_4}")
    print(f"  Result:   {'✅ PASS' if result_4 == expected_4 else '❌ FAIL'}")
    
    # Summary
    all_tests = [
        result_1 == expected_1,
        result_2 == expected_2,
        result_3 == expected_3,
        result_4 == expected_4
    ]
    
    passed = sum(all_tests)
    total = len(all_tests)
    
    print(f"\n📊 SUMMARY: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("✅ format_dry_dock_cycle_display function is working correctly!")
        print("✅ dd/MM/yyyy format is properly implemented")
    else:
        print("❌ format_dry_dock_cycle_display function has issues")
    
    return passed == total

if __name__ == "__main__":
    test_format_function()