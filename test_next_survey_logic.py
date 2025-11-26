"""
Test script for Next Survey calculation logic
"""
import sys
sys.path.insert(0, '/app/backend')

from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from app.services.audit_certificate_service import AuditCertificateService

def test_interim_certificate():
    """Test Case 1: Interim Certificate"""
    print("\n" + "="*60)
    print("TEST 1: INTERIM CERTIFICATE")
    print("="*60)
    
    cert_data = {
        'cert_name': 'ISM DOC',
        'cert_type': 'Interim',
        'valid_date': '2026-05-07',
        'last_endorse': None
    }
    
    result = AuditCertificateService.calculate_audit_certificate_next_survey(cert_data)
    
    print(f"Input:")
    print(f"  - Cert Type: {cert_data['cert_type']}")
    print(f"  - Valid Date: {cert_data['valid_date']}")
    print(f"  - Last Endorse: {cert_data.get('last_endorse')}")
    print(f"\nExpected:")
    print(f"  - Next Survey: 07/05/2026 (-3M)")
    print(f"  - Next Survey Type: Initial")
    print(f"  - Reasoning: Valid Date - 3 months")
    print(f"\nActual Result:")
    print(f"  - Next Survey: {result['next_survey']}")
    print(f"  - Next Survey Type: {result['next_survey_type']}")
    print(f"  - Reasoning: {result['reasoning']}")
    print(f"\n✅ PASS" if result['next_survey'] == '07/05/2026 (-3M)' and result['next_survey_type'] == 'Initial' else "❌ FAIL")

def test_full_term_no_endorse():
    """Test Case 2: Full Term WITHOUT Last Endorse"""
    print("\n" + "="*60)
    print("TEST 2: FULL TERM WITHOUT LAST ENDORSE")
    print("="*60)
    
    cert_data = {
        'cert_name': 'ISM Certificate',
        'cert_type': 'Full Term',
        'valid_date': '2027-05-07',  # Valid date is 2 years from now
        'last_endorse': None
    }
    
    result = AuditCertificateService.calculate_audit_certificate_next_survey(cert_data)
    
    print(f"Input:")
    print(f"  - Cert Type: {cert_data['cert_type']}")
    print(f"  - Valid Date: {cert_data['valid_date']}")
    print(f"  - Last Endorse: {cert_data.get('last_endorse')}")
    print(f"\nExpected:")
    print(f"  - Next Survey: 07/05/2025 (±3M)")
    print(f"  - Next Survey Type: Intermediate")
    print(f"  - Reasoning: Valid Date - 2 years (no Last Endorse)")
    print(f"\nActual Result:")
    print(f"  - Next Survey: {result['next_survey']}")
    print(f"  - Next Survey Type: {result['next_survey_type']}")
    print(f"  - Reasoning: {result['reasoning']}")
    print(f"\n✅ PASS" if result['next_survey'] == '07/05/2025 (±3M)' and result['next_survey_type'] == 'Intermediate' else "❌ FAIL")

def test_full_term_with_endorse():
    """Test Case 3: Full Term WITH Last Endorse"""
    print("\n" + "="*60)
    print("TEST 3: FULL TERM WITH LAST ENDORSE")
    print("="*60)
    
    cert_data = {
        'cert_name': 'ISPS Certificate',
        'cert_type': 'Full Term',
        'valid_date': '2027-05-07',
        'last_endorse': '2025-11-15'  # Has Last Endorse
    }
    
    result = AuditCertificateService.calculate_audit_certificate_next_survey(cert_data)
    
    print(f"Input:")
    print(f"  - Cert Type: {cert_data['cert_type']}")
    print(f"  - Valid Date: {cert_data['valid_date']}")
    print(f"  - Last Endorse: {cert_data.get('last_endorse')}")
    print(f"\nExpected:")
    print(f"  - Next Survey: 07/05/2027 (-3M)")
    print(f"  - Next Survey Type: Renewal")
    print(f"  - Reasoning: Valid Date - 3 months (has Last Endorse)")
    print(f"\nActual Result:")
    print(f"  - Next Survey: {result['next_survey']}")
    print(f"  - Next Survey Type: {result['next_survey_type']}")
    print(f"  - Reasoning: {result['reasoning']}")
    print(f"\n✅ PASS" if result['next_survey'] == '07/05/2027 (-3M)' and result['next_survey_type'] == 'Renewal' else "❌ FAIL")

def test_dmlc_certificate():
    """Test Case 4: DMLC Certificate (Special Document)"""
    print("\n" + "="*60)
    print("TEST 4: DMLC CERTIFICATE (SPECIAL DOCUMENT)")
    print("="*60)
    
    cert_data = {
        'cert_name': 'DMLC II',
        'cert_type': 'Other',
        'valid_date': '2026-04-07',
        'last_endorse': None
    }
    
    result = AuditCertificateService.calculate_audit_certificate_next_survey(cert_data)
    
    print(f"Input:")
    print(f"  - Cert Name: {cert_data['cert_name']}")
    print(f"  - Cert Type: {cert_data['cert_type']}")
    print(f"  - Valid Date: {cert_data['valid_date']}")
    print(f"\nExpected:")
    print(f"  - Next Survey: None")
    print(f"  - Next Survey Type: None")
    print(f"  - Reasoning: Special documents don't require Next Survey")
    print(f"\nActual Result:")
    print(f"  - Next Survey: {result['next_survey']}")
    print(f"  - Next Survey Type: {result['next_survey_type']}")
    print(f"  - Reasoning: {result['reasoning']}")
    print(f"\n✅ PASS" if result['next_survey'] is None and result['next_survey_type'] is None else "❌ FAIL")

def test_short_term_certificate():
    """Test Case 5: Short Term Certificate"""
    print("\n" + "="*60)
    print("TEST 5: SHORT TERM CERTIFICATE")
    print("="*60)
    
    cert_data = {
        'cert_name': 'Interim ISM',
        'cert_type': 'Short Term',
        'valid_date': '2025-12-31',
        'last_endorse': None
    }
    
    result = AuditCertificateService.calculate_audit_certificate_next_survey(cert_data)
    
    print(f"Input:")
    print(f"  - Cert Type: {cert_data['cert_type']}")
    print(f"  - Valid Date: {cert_data['valid_date']}")
    print(f"\nExpected:")
    print(f"  - Next Survey: None")
    print(f"  - Next Survey Type: None")
    print(f"  - Reasoning: Short Term certificates don't require Next Survey")
    print(f"\nActual Result:")
    print(f"  - Next Survey: {result['next_survey']}")
    print(f"  - Next Survey Type: {result['next_survey_type']}")
    print(f"  - Reasoning: {result['reasoning']}")
    print(f"\n✅ PASS" if result['next_survey'] is None and result['next_survey_type'] is None else "❌ FAIL")

if __name__ == "__main__":
    print("\n" + "🧪 TESTING AUDIT CERTIFICATE NEXT SURVEY CALCULATION ".center(60, "="))
    
    test_interim_certificate()
    test_full_term_no_endorse()
    test_full_term_with_endorse()
    test_dmlc_certificate()
    test_short_term_certificate()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60 + "\n")
