#!/usr/bin/env python3
"""
Unit Test for Date Standardization Function
FOCUS: Test the standardize_passport_dates function directly with various input formats

This test simulates the date standardization function behavior by testing various
input formats that might come from AI responses and verifying they get converted
to clean DD/MM/YYYY format.
"""

import re
from datetime import datetime
import sys

def standardize_passport_dates(extracted_data: dict) -> dict:
    """
    Standardize date formats in passport extraction data to match certificate handling.
    Convert verbose AI responses like "February 14, 1983 (14/02/1983)" to clean "14/02/1983" format.
    This ensures consistency with existing certificate date processing.
    
    This is a copy of the function from server.py for testing purposes.
    """
    import re
    from datetime import datetime
    
    date_fields = ["date_of_birth", "issue_date", "expiry_date"]
    
    for field in date_fields:
        if field in extracted_data and extracted_data[field]:
            date_value = str(extracted_data[field]).strip()
            if not date_value or date_value.lower() in ['', 'null', 'none', 'n/a']:
                extracted_data[field] = ""
                continue
            
            print(f"🗓️ Standardizing {field}: '{date_value}'")
            
            # Pattern 1: Extract DD/MM/YYYY from parentheses like "February 14, 1983 (14/02/1983)"
            parentheses_pattern = r'\((\d{1,2}\/\d{1,2}\/\d{4})\)'
            parentheses_match = re.search(parentheses_pattern, date_value)
            if parentheses_match:
                clean_date = parentheses_match.group(1)
                # Ensure DD/MM/YYYY format with zero padding
                parts = clean_date.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    standardized_date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                    extracted_data[field] = standardized_date
                    print(f"   ✅ Extracted from parentheses: '{standardized_date}'")
                    continue
            
            # Pattern 2: Direct DD/MM/YYYY format (already correct)
            ddmm_pattern = r'^(\d{1,2})\/(\d{1,2})\/(\d{4})$'
            ddmm_match = re.match(ddmm_pattern, date_value)
            if ddmm_match:
                day, month, year = ddmm_match.groups()
                standardized_date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                extracted_data[field] = standardized_date
                print(f"   ✅ Already in DD/MM/YYYY format: '{standardized_date}'")
                continue
            
            # Pattern 3: Convert verbose month names using Python datetime for complex formats
            try:
                # Common verbose formats to try
                format_patterns = [
                    "%B %d, %Y",      # February 14, 1983
                    "%d %B %Y",       # 14 February 1983
                    "%B %d %Y",       # February 14 1983
                    "%d-%b-%Y",       # 14-Feb-1983
                    "%d %b %Y",       # 14 Feb 1983
                    "%b %d, %Y",      # Feb 14, 1983
                    "%b %d %Y",       # Feb 14 1983
                ]
                
                for fmt in format_patterns:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt)
                        standardized_date = f"{parsed_date.day:02d}/{parsed_date.month:02d}/{parsed_date.year}"
                        extracted_data[field] = standardized_date
                        print(f"   ✅ Parsed verbose format to DD/MM/YYYY: '{standardized_date}'")
                        break
                    except ValueError:
                        continue
                else:
                    # If no format worked, keep original value but log warning
                    print(f"   ⚠️ Could not standardize date format: '{date_value}' - keeping original")
                    
            except Exception as e:
                print(f"   ⚠️ Date parsing error for '{date_value}': {e} - keeping original")
    
    return extracted_data

class DateStandardizationTester:
    def __init__(self):
        self.test_cases = [
            # Test case format: (input_data, expected_output, test_description)
            (
                {
                    "date_of_birth": "February 14, 1983 (14/02/1983)",
                    "issue_date": "March 15, 2020 (15/03/2020)",
                    "expiry_date": "March 14, 2030 (14/03/2030)"
                },
                {
                    "date_of_birth": "14/02/1983",
                    "issue_date": "15/03/2020",
                    "expiry_date": "14/03/2030"
                },
                "Parentheses format extraction"
            ),
            (
                {
                    "date_of_birth": "14/02/1983",
                    "issue_date": "15/03/2020",
                    "expiry_date": "14/03/2030"
                },
                {
                    "date_of_birth": "14/02/1983",
                    "issue_date": "15/03/2020",
                    "expiry_date": "14/03/2030"
                },
                "Already correct DD/MM/YYYY format"
            ),
            (
                {
                    "date_of_birth": "February 14, 1983",
                    "issue_date": "March 15, 2020",
                    "expiry_date": "March 14, 2030"
                },
                {
                    "date_of_birth": "14/02/1983",
                    "issue_date": "15/03/2020",
                    "expiry_date": "14/03/2030"
                },
                "Verbose month names (Month DD, YYYY)"
            ),
            (
                {
                    "date_of_birth": "14 February 1983",
                    "issue_date": "15 March 2020",
                    "expiry_date": "14 March 2030"
                },
                {
                    "date_of_birth": "14/02/1983",
                    "issue_date": "15/03/2020",
                    "expiry_date": "14/03/2030"
                },
                "Verbose format (DD Month YYYY)"
            ),
            (
                {
                    "date_of_birth": "Feb 14, 1983",
                    "issue_date": "Mar 15, 2020",
                    "expiry_date": "Mar 14, 2030"
                },
                {
                    "date_of_birth": "14/02/1983",
                    "issue_date": "15/03/2020",
                    "expiry_date": "14/03/2030"
                },
                "Abbreviated month names"
            ),
            (
                {
                    "date_of_birth": "14-Feb-1983",
                    "issue_date": "15-Mar-2020",
                    "expiry_date": "14-Mar-2030"
                },
                {
                    "date_of_birth": "14/02/1983",
                    "issue_date": "15/03/2020",
                    "expiry_date": "14/03/2030"
                },
                "Hyphenated format (DD-Mon-YYYY)"
            ),
            (
                {
                    "date_of_birth": "1/5/1990",
                    "issue_date": "2/3/2020",
                    "expiry_date": "1/3/2030"
                },
                {
                    "date_of_birth": "01/05/1990",
                    "issue_date": "02/03/2020",
                    "expiry_date": "01/03/2030"
                },
                "Single digit padding"
            ),
            (
                {
                    "date_of_birth": "",
                    "issue_date": "null",
                    "expiry_date": "N/A"
                },
                {
                    "date_of_birth": "",
                    "issue_date": "",
                    "expiry_date": ""
                },
                "Empty/null values handling"
            ),
        ]
        
        self.results = []
    
    def run_test_case(self, input_data, expected_output, description):
        """Run a single test case"""
        print(f"\n🧪 Testing: {description}")
        print(f"Input: {input_data}")
        
        # Make a copy to avoid modifying the original
        test_data = input_data.copy()
        
        # Run the standardization function
        result = standardize_passport_dates(test_data)
        
        print(f"Output: {result}")
        print(f"Expected: {expected_output}")
        
        # Check if the result matches expected output
        success = True
        for field in ["date_of_birth", "issue_date", "expiry_date"]:
            if field in expected_output:
                if result.get(field) != expected_output[field]:
                    success = False
                    print(f"   ❌ FAIL: {field} = '{result.get(field)}', expected '{expected_output[field]}'")
                else:
                    print(f"   ✅ PASS: {field} = '{result.get(field)}'")
        
        if success:
            print(f"   ✅ TEST PASSED: {description}")
        else:
            print(f"   ❌ TEST FAILED: {description}")
        
        return success
    
    def run_all_tests(self):
        """Run all test cases"""
        print("🚀 STARTING DATE STANDARDIZATION UNIT TESTS")
        print("=" * 80)
        
        passed_tests = 0
        total_tests = len(self.test_cases)
        
        for i, (input_data, expected_output, description) in enumerate(self.test_cases, 1):
            print(f"\nTest {i}/{total_tests}:")
            if self.run_test_case(input_data, expected_output, description):
                passed_tests += 1
                self.results.append(("PASS", description))
            else:
                self.results.append(("FAIL", description))
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
        print("")
        
        for status, description in self.results:
            status_icon = "✅" if status == "PASS" else "❌"
            print(f"   {status_icon} {status} - {description}")
        
        print("\n🎯 CRITICAL SUCCESS CRITERIA:")
        if passed_tests == total_tests:
            print("   ✅ ALL TESTS PASSED")
            print("   ✅ Date standardization function working correctly")
            print("   ✅ All date formats properly converted to DD/MM/YYYY")
            print("   ✅ Edge cases handled properly")
        else:
            print("   ❌ SOME TESTS FAILED")
            print(f"   ❌ Only {passed_tests}/{total_tests} tests passed")
            print("   ❌ Date standardization function needs attention")
        
        print("=" * 80)
        
        return passed_tests == total_tests

def main():
    """Main function to run the date standardization tests"""
    tester = DateStandardizationTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()