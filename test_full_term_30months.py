"""
Test Full Term certificate with 30 months logic
"""
import sys
sys.path.insert(0, '/app/backend')

from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from app.services.audit_certificate_service import AuditCertificateService

def test_full_term_30_months():
    """Test Full Term WITHOUT Last Endorse with 30 months calculation"""
    print("\n" + "="*70)
    print("TEST: FULL TERM WITHOUT LAST ENDORSE - 30 MONTHS LOGIC")
    print("="*70)
    
    # Test Case 1: Valid Date is exactly 30 months from now
    print("\n📋 Test Case 1: Valid Date = 2027-05-07 (30 months from now)")
    cert_data_1 = {
        'cert_name': 'ISM Certificate',
        'cert_type': 'Full Term',
        'valid_date': '2027-05-07',
        'last_endorse': None
    }
    
    result_1 = AuditCertificateService.calculate_audit_certificate_next_survey(cert_data_1)
    
    print(f"\nInput:")
    print(f"  Valid Date: {cert_data_1['valid_date']}")
    print(f"  Last Endorse: None")
    
    print(f"\nExpected Result:")
    print(f"  Next Survey: 07/11/2024 (±6M)")
    print(f"  Formula: 2027-05-07 - 30 months = 2024-11-07")
    print(f"  Window: ±6 months (May 2024 to May 2025)")
    
    print(f"\nActual Result:")
    print(f"  Next Survey: {result_1['next_survey']}")
    print(f"  Next Survey Type: {result_1['next_survey_type']}")
    print(f"  Raw Date: {result_1.get('raw_date')}")
    print(f"  Window: ±{result_1.get('window_months')} months")
    
    # Verify
    is_correct_1 = (
        result_1['next_survey'] == '07/11/2024 (±6M)' and 
        result_1['next_survey_type'] == 'Intermediate' and
        result_1.get('window_months') == 6
    )
    print(f"\n{'✅ PASS' if is_correct_1 else '❌ FAIL'}")
    
    # Test Case 2: Different valid date
    print("\n" + "="*70)
    print("\n📋 Test Case 2: Valid Date = 2028-12-31")
    cert_data_2 = {
        'cert_name': 'ISPS Certificate',
        'cert_type': 'Full Term',
        'valid_date': '2028-12-31',
        'last_endorse': None
    }
    
    result_2 = AuditCertificateService.calculate_audit_certificate_next_survey(cert_data_2)
    
    print(f"\nInput:")
    print(f"  Valid Date: {cert_data_2['valid_date']}")
    print(f"  Last Endorse: None")
    
    print(f"\nExpected Result:")
    print(f"  Next Survey: 31/06/2026 (±6M)")
    print(f"  Formula: 2028-12-31 - 30 months = 2026-06-31")
    print(f"  Window: ±6 months")
    
    print(f"\nActual Result:")
    print(f"  Next Survey: {result_2['next_survey']}")
    print(f"  Next Survey Type: {result_2['next_survey_type']}")
    print(f"  Raw Date: {result_2.get('raw_date')}")
    print(f"  Window: ±{result_2.get('window_months')} months")
    
    is_correct_2 = (
        '(±6M)' in result_2['next_survey'] and 
        result_2['next_survey_type'] == 'Intermediate' and
        result_2.get('window_months') == 6
    )
    print(f"\n{'✅ PASS' if is_correct_2 else '❌ FAIL'}")
    
    # Test Case 3: Verify it's different from WITH Last Endorse
    print("\n" + "="*70)
    print("\n📋 Test Case 3: Full Term WITH Last Endorse (for comparison)")
    cert_data_3 = {
        'cert_name': 'MLC Certificate',
        'cert_type': 'Full Term',
        'valid_date': '2027-05-07',
        'last_endorse': '2025-11-15'
    }
    
    result_3 = AuditCertificateService.calculate_audit_certificate_next_survey(cert_data_3)
    
    print(f"\nInput:")
    print(f"  Valid Date: {cert_data_3['valid_date']}")
    print(f"  Last Endorse: {cert_data_3['last_endorse']}")
    
    print(f"\nExpected Result:")
    print(f"  Next Survey: 07/05/2027 (-3M)")
    print(f"  Formula: Valid Date - 3 months (Renewal)")
    print(f"  Window: -3 months only (before deadline)")
    
    print(f"\nActual Result:")
    print(f"  Next Survey: {result_3['next_survey']}")
    print(f"  Next Survey Type: {result_3['next_survey_type']}")
    print(f"  Window: {result_3.get('window_months')} months")
    
    is_correct_3 = (
        result_3['next_survey'] == '07/05/2027 (-3M)' and 
        result_3['next_survey_type'] == 'Renewal' and
        result_3.get('window_months') == 3
    )
    print(f"\n{'✅ PASS' if is_correct_3 else '❌ FAIL'}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"Test Case 1 (30 months): {'✅ PASS' if is_correct_1 else '❌ FAIL'}")
    print(f"Test Case 2 (30 months): {'✅ PASS' if is_correct_2 else '❌ FAIL'}")
    print(f"Test Case 3 (3 months):  {'✅ PASS' if is_correct_3 else '❌ FAIL'}")
    
    all_pass = is_correct_1 and is_correct_2 and is_correct_3
    print(f"\n{'✅ ALL TESTS PASSED' if all_pass else '❌ SOME TESTS FAILED'}")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_full_term_30_months()
