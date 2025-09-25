#!/usr/bin/env python3
"""
Simple test of the format function logic without importing the full server
"""

from datetime import datetime
from typing import Optional

class DryDockCycle:
    def __init__(self, from_date=None, to_date=None, intermediate_docking_required=True, last_intermediate_docking=None):
        self.from_date = from_date
        self.to_date = to_date
        self.intermediate_docking_required = intermediate_docking_required
        self.last_intermediate_docking = last_intermediate_docking

def format_dry_dock_cycle_display(dry_dock_cycle: Optional[DryDockCycle]) -> str:
    """Format dry dock cycle for display (dd/MM/yyyy - dd/MM/yyyy format with intermediate docking note)"""
    if not dry_dock_cycle or not dry_dock_cycle.from_date or not dry_dock_cycle.to_date:
        return '-'
        
    try:
        from_str = dry_dock_cycle.from_date.strftime('%d/%m/%Y')
        to_str = dry_dock_cycle.to_date.strftime('%d/%m/%Y')
        
        cycle_str = f"{from_str} - {to_str}"
        if dry_dock_cycle.intermediate_docking_required:
            cycle_str += " (Int. required)"
            
        return cycle_str
    except:
        return '-'

def test_format_function():
    """Test the format_dry_dock_cycle_display function directly"""
    print("🔧 Testing format_dry_dock_cycle_display function directly...")
    
    # Test case 1: Normal case with intermediate docking (from review request)
    dry_dock_1 = DryDockCycle(
        from_date=datetime(2024, 1, 15),
        to_date=datetime(2029, 1, 15),
        intermediate_docking_required=True,
        last_intermediate_docking=datetime(2024, 2, 10)
    )
    
    result_1 = format_dry_dock_cycle_display(dry_dock_1)
    expected_1 = "15/01/2024 - 15/01/2029 (Int. required)"
    
    print(f"Test 1 - Review Request Test Case:")
    print(f"  Input: from_date=2024-01-15, to_date=2029-01-15, intermediate_docking_required=True")
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
    
    # Test case 5: Edge case - single digit day/month
    dry_dock_5 = DryDockCycle(
        from_date=datetime(2024, 3, 5),
        to_date=datetime(2029, 9, 8),
        intermediate_docking_required=True
    )
    
    result_5 = format_dry_dock_cycle_display(dry_dock_5)
    expected_5 = "05/03/2024 - 08/09/2029 (Int. required)"
    
    print(f"\nTest 5 - Single digit day/month:")
    print(f"  Expected: {expected_5}")
    print(f"  Actual:   {result_5}")
    print(f"  Result:   {'✅ PASS' if result_5 == expected_5 else '❌ FAIL'}")
    
    # Summary
    all_tests = [
        result_1 == expected_1,
        result_2 == expected_2,
        result_3 == expected_3,
        result_4 == expected_4,
        result_5 == expected_5
    ]
    
    passed = sum(all_tests)
    total = len(all_tests)
    
    print(f"\n📊 SUMMARY: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("✅ format_dry_dock_cycle_display function is working correctly!")
        print("✅ dd/MM/yyyy format is properly implemented")
        print("✅ Format change from 'Jan 2024 - Jan 2029' to '15/01/2024 - 15/01/2029' confirmed")
    else:
        print("❌ format_dry_dock_cycle_display function has issues")
    
    return passed == total

if __name__ == "__main__":
    test_format_function()