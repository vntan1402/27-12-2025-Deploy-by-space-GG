"""
Test Upcoming Surveys window logic
"""
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def test_window_logic():
    """Test window calculation logic for different annotations"""
    
    print("\n" + "="*70)
    print("TESTING UPCOMING SURVEYS WINDOW LOGIC")
    print("="*70)
    
    # Mock current date
    current_date = datetime(2026, 3, 15).date()  # Middle of window
    
    test_cases = [
        {
            "name": "Interim Certificate with (-3M)",
            "next_survey_display": "07/05/2026 (-3M)",
            "expected_window_open": "2026-02-07",
            "expected_window_close": "2026-05-07",
            "expected_within_window": True,
            "window_type": "-3M"
        },
        {
            "name": "Intermediate with (±3M)",
            "next_survey_display": "15/04/2026 (±3M)",
            "expected_window_open": "2026-01-15",
            "expected_window_close": "2026-07-15",
            "expected_within_window": True,
            "window_type": "±3M"
        },
        {
            "name": "Intermediate without endorse (±6M)",
            "next_survey_display": "01/06/2026 (±6M)",
            "expected_window_open": "2025-12-01",
            "expected_window_close": "2026-12-01",
            "expected_within_window": True,
            "window_type": "±6M"
        },
        {
            "name": "Future survey (outside window)",
            "next_survey_display": "01/12/2026 (-3M)",
            "expected_window_open": "2026-09-01",
            "expected_window_close": "2026-12-01",
            "expected_within_window": False,
            "window_type": "-3M"
        },
        {
            "name": "Past survey (outside window)",
            "next_survey_display": "01/01/2026 (-3M)",
            "expected_window_open": "2025-10-01",
            "expected_window_close": "2026-01-01",
            "expected_within_window": False,
            "window_type": "-3M"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"TEST CASE {i}: {test['name']}")
        print(f"{'='*70}")
        
        next_survey_str = test['next_survey_display']
        
        # Parse date
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', next_survey_str)
        if not date_match:
            print(f"❌ FAIL: Cannot parse date")
            failed += 1
            continue
        
        date_str = date_match.group(1)
        next_survey_date = datetime.strptime(date_str, '%d/%m/%Y').date()
        
        # Determine window based on annotation
        window_open = None
        window_close = None
        window_type = ''
        
        if '(±6M)' in next_survey_str:
            window_open = next_survey_date - relativedelta(months=6)
            window_close = next_survey_date + relativedelta(months=6)
            window_type = '±6M'
        elif '(±3M)' in next_survey_str or '(+3M)' in next_survey_str or '(+-3M)' in next_survey_str:
            window_open = next_survey_date - relativedelta(months=3)
            window_close = next_survey_date + relativedelta(months=3)
            window_type = '±3M'
        elif '(-3M)' in next_survey_str:
            window_open = next_survey_date - relativedelta(months=3)
            window_close = next_survey_date
            window_type = '-3M'
        
        is_within_window = window_open <= current_date <= window_close
        
        # Verify
        print(f"\nInput:")
        print(f"  Current Date: {current_date}")
        print(f"  Next Survey Display: {next_survey_str}")
        
        print(f"\nCalculated:")
        print(f"  Next Survey Date: {next_survey_date}")
        print(f"  Window Open: {window_open}")
        print(f"  Window Close: {window_close}")
        print(f"  Window Type: {window_type}")
        print(f"  Is Within Window: {is_within_window}")
        
        print(f"\nExpected:")
        print(f"  Window Open: {test['expected_window_open']}")
        print(f"  Window Close: {test['expected_window_close']}")
        print(f"  Within Window: {test['expected_within_window']}")
        print(f"  Window Type: {test['window_type']}")
        
        # Check if test passed
        window_open_match = str(window_open) == test['expected_window_open']
        window_close_match = str(window_close) == test['expected_window_close']
        within_match = is_within_window == test['expected_within_window']
        type_match = window_type == test['window_type']
        
        all_match = window_open_match and window_close_match and within_match and type_match
        
        if all_match:
            print(f"\n✅ PASS")
            passed += 1
        else:
            print(f"\n❌ FAIL")
            if not window_open_match:
                print(f"  Window Open mismatch")
            if not window_close_match:
                print(f"  Window Close mismatch")
            if not within_match:
                print(f"  Within Window mismatch")
            if not type_match:
                print(f"  Window Type mismatch")
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
    test_window_logic()
