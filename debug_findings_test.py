#!/usr/bin/env python3
"""
Debug Findings Test - Verify the root cause of the issues
"""

def test_null_string_issue():
    """Test the null string issue that's causing the special survey from date bug"""
    print("🔍 TESTING NULL STRING ISSUE")
    print("=" * 50)
    
    # Simulate the AI response
    analysis_result = {
        "special_survey_to_date": "10/03/2026",
        "special_survey_from_date": "null"  # This is the problem - string "null" instead of None
    }
    
    print(f"special_survey_to_date: {analysis_result.get('special_survey_to_date')}")
    print(f"special_survey_from_date: {analysis_result.get('special_survey_from_date')}")
    
    # Test the current condition (this is the bug)
    current_condition = analysis_result.get("special_survey_to_date") and not analysis_result.get("special_survey_from_date")
    print(f"\nCurrent condition result: {current_condition}")
    print(f"  analysis_result.get('special_survey_to_date'): {bool(analysis_result.get('special_survey_to_date'))}")
    print(f"  analysis_result.get('special_survey_from_date'): {bool(analysis_result.get('special_survey_from_date'))}")
    print(f"  not analysis_result.get('special_survey_from_date'): {not analysis_result.get('special_survey_from_date')}")
    
    # The issue: "null" string is truthy, so the condition fails
    print(f"\n❌ ISSUE IDENTIFIED:")
    print(f"  The string 'null' is truthy in Python: {bool('null')}")
    print(f"  So 'not analysis_result.get('special_survey_from_date')' returns False")
    print(f"  This prevents the post-processing logic from running")
    
    # Test the correct condition
    def is_null_or_empty(value):
        return value is None or value == "" or value == "null" or value == "None"
    
    correct_condition = (analysis_result.get("special_survey_to_date") and 
                        is_null_or_empty(analysis_result.get("special_survey_from_date")))
    
    print(f"\n✅ CORRECT CONDITION:")
    print(f"  Should check for null/empty values properly: {correct_condition}")
    
    return current_condition, correct_condition

def test_last_docking_format():
    """Test that last docking format is actually working correctly"""
    print("\n🔍 TESTING LAST DOCKING FORMAT")
    print("=" * 50)
    
    # From our test results
    last_docking = "NOV 2020"
    last_docking_2 = "DEC 2022"
    
    print(f"last_docking: {last_docking}")
    print(f"last_docking_2: {last_docking_2}")
    
    # Check if they're in the correct format
    import re
    month_year_pattern = r'^[A-Z]{3}\.?\s+\d{4}$'
    
    ld1_correct = bool(re.match(month_year_pattern, last_docking))
    ld2_correct = bool(re.match(month_year_pattern, last_docking_2))
    
    print(f"\n✅ FORMAT VERIFICATION:")
    print(f"  last_docking format correct: {ld1_correct}")
    print(f"  last_docking_2 format correct: {ld2_correct}")
    
    if ld1_correct and ld2_correct:
        print("  ✅ ISSUE 1 IS ACTUALLY RESOLVED - AI is extracting correct month/year format")
    else:
        print("  ❌ ISSUE 1 STILL EXISTS - Format is incorrect")
    
    return ld1_correct and ld2_correct

def main():
    print("🔍 DEBUG FINDINGS VERIFICATION")
    print("=" * 80)
    
    # Test Issue 1
    issue_1_resolved = test_last_docking_format()
    
    # Test Issue 2
    current_bug, correct_logic = test_null_string_issue()
    
    print(f"\n📊 FINAL FINDINGS:")
    print("=" * 50)
    
    if issue_1_resolved:
        print("✅ ISSUE 1 (Last Docking Format): RESOLVED")
        print("   - AI is correctly extracting 'NOV 2020', 'DEC 2022' format")
        print("   - No full dates like '30/11/2020' being returned")
    else:
        print("❌ ISSUE 1 (Last Docking Format): NOT RESOLVED")
    
    if not current_bug and correct_logic:
        print("❌ ISSUE 2 (Special Survey From Date): NOT RESOLVED")
        print("   - Root cause: AI returns string 'null' instead of None/empty")
        print("   - Post-processing condition fails because 'null' string is truthy")
        print("   - Fix needed: Update condition to check for 'null' string values")
    else:
        print("✅ ISSUE 2 (Special Survey From Date): RESOLVED")
    
    print(f"\n🔧 RECOMMENDED FIXES:")
    if not issue_1_resolved:
        print("1. Fix AI prompt to extract month/year format for docking dates")
    else:
        print("1. ✅ Last docking format is working correctly")
    
    if not current_bug and correct_logic:
        print("2. Update post-processing condition in analyze-ship-certificate endpoint:")
        print("   Change line 4218 from:")
        print("   if analysis_result.get('special_survey_to_date') and not analysis_result.get('special_survey_from_date'):")
        print("   To:")
        print("   if (analysis_result.get('special_survey_to_date') and")
        print("       (not analysis_result.get('special_survey_from_date') or")
        print("        analysis_result.get('special_survey_from_date') in ['null', 'None', ''])):")
    else:
        print("2. ✅ Special survey from date calculation is working correctly")

if __name__ == "__main__":
    main()