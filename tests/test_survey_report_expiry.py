"""
Test Suite for Survey Report Expiry Calculation Feature
Tests the refactored backend logic where expiry_date and status are calculated on the backend
instead of frontend fetching certificates.

Features tested:
1. Backend: expiry_date and status calculated on create
2. Backend: expiry_date and status recalculated on update
3. API returns correct status values (Valid/Expired/Due Soon)
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://code-resume-17.preview.emergentagent.com')
TEST_SHIP_ID = "ba47e580-1504-4728-94d0-dcddcbf7d8e1"
TEST_CREDENTIALS = {"username": "admin1", "password": "123456"}


class TestSurveyReportExpiryCalculation:
    """Test suite for Survey Report expiry_date and status calculation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        token = response.json().get("access_token")
        assert token, "No access token received"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.created_report_ids = []
        
        yield
        
        # Cleanup: Delete test-created reports
        for report_id in self.created_report_ids:
            try:
                self.session.post(
                    f"{BASE_URL}/api/survey-reports/bulk-delete",
                    json={"report_ids": [report_id]}
                )
            except:
                pass
    
    def test_01_get_existing_survey_reports_with_status(self):
        """Test: Existing survey reports have status and expiry_date from backend"""
        response = self.session.get(f"{BASE_URL}/api/survey-reports?ship_id={TEST_SHIP_ID}")
        
        assert response.status_code == 200, f"Failed to get survey reports: {response.text}"
        
        reports = response.json()
        assert isinstance(reports, list), "Response should be a list"
        
        # Check that reports have status and expiry_date fields
        for report in reports:
            assert "status" in report, f"Report {report.get('id')} missing 'status' field"
            assert "expiry_date" in report, f"Report {report.get('id')} missing 'expiry_date' field"
            
            # Validate status values
            valid_statuses = ["Valid", "Expired", "Due Soon", "Pending"]
            assert report["status"] in valid_statuses, f"Invalid status: {report['status']}"
            
            print(f"✅ Report '{report.get('survey_report_name')}': status={report['status']}, expiry_date={report.get('expiry_date')}")
    
    def test_02_verify_expired_status_calculation(self):
        """Test: Report with old issued_date should have 'Expired' status"""
        response = self.session.get(f"{BASE_URL}/api/survey-reports?ship_id={TEST_SHIP_ID}")
        assert response.status_code == 200
        
        reports = response.json()
        
        # Find the test report with TSR-2025-001 (issued 2024-06-15, should be Expired)
        expired_report = next(
            (r for r in reports if r.get("survey_report_no") == "TSR-2025-001"),
            None
        )
        
        if expired_report:
            assert expired_report["status"] == "Expired", \
                f"Expected 'Expired' status for old report, got '{expired_report['status']}'"
            print(f"✅ Report TSR-2025-001 correctly has 'Expired' status")
        else:
            pytest.skip("Test report TSR-2025-001 not found")
    
    def test_03_verify_valid_status_calculation(self):
        """Test: Report with recent issued_date should have 'Valid' status"""
        response = self.session.get(f"{BASE_URL}/api/survey-reports?ship_id={TEST_SHIP_ID}")
        assert response.status_code == 200
        
        reports = response.json()
        
        # Find the test report with TSR-2025-002 (issued 2025-01-01, should be Valid)
        valid_report = next(
            (r for r in reports if r.get("survey_report_no") == "TSR-2025-002"),
            None
        )
        
        if valid_report:
            assert valid_report["status"] == "Valid", \
                f"Expected 'Valid' status for recent report, got '{valid_report['status']}'"
            print(f"✅ Report TSR-2025-002 correctly has 'Valid' status")
        else:
            pytest.skip("Test report TSR-2025-002 not found")
    
    def test_04_create_survey_report_calculates_expiry(self):
        """Test: Creating a new survey report calculates expiry_date and status"""
        # Create a new survey report with recent issued_date
        today = datetime.now()
        issued_date = today.strftime("%Y-%m-%d")
        
        new_report = {
            "ship_id": TEST_SHIP_ID,
            "survey_report_name": "TEST_Auto_Expiry_Calculation",
            "report_form": "Annual Survey",
            "survey_report_no": f"TEST-{today.strftime('%Y%m%d%H%M%S')}",
            "issued_date": issued_date,
            "issued_by": "DNV GL",
            "note": "Test auto expiry calculation"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/survey-reports",
            json=new_report
        )
        
        assert response.status_code == 200, f"Failed to create survey report: {response.text}"
        
        created_report = response.json()
        self.created_report_ids.append(created_report["id"])
        
        # Verify expiry_date and status are calculated
        assert "expiry_date" in created_report, "Created report missing 'expiry_date'"
        assert "status" in created_report, "Created report missing 'status'"
        assert created_report["expiry_date"] is not None, "expiry_date should not be None"
        assert created_report["status"] == "Valid", \
            f"New report with today's date should be 'Valid', got '{created_report['status']}'"
        
        print(f"✅ Created report has expiry_date={created_report['expiry_date']}, status={created_report['status']}")
    
    def test_05_create_survey_report_with_old_date_gets_expired_status(self):
        """Test: Creating a survey report with old issued_date gets 'Expired' status"""
        # Create a report with issued_date from 2 years ago
        old_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        
        new_report = {
            "ship_id": TEST_SHIP_ID,
            "survey_report_name": "TEST_Old_Date_Expired",
            "report_form": "Annual Survey",
            "survey_report_no": f"TEST-OLD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "issued_date": old_date,
            "issued_by": "LR",
            "note": "Test old date gets expired status"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/survey-reports",
            json=new_report
        )
        
        assert response.status_code == 200, f"Failed to create survey report: {response.text}"
        
        created_report = response.json()
        self.created_report_ids.append(created_report["id"])
        
        # Verify status is Expired for old date
        assert created_report["status"] == "Expired", \
            f"Report with old date should be 'Expired', got '{created_report['status']}'"
        
        print(f"✅ Report with old date correctly has 'Expired' status")
    
    def test_06_update_survey_report_recalculates_expiry(self):
        """Test: Updating issued_date recalculates expiry_date and status"""
        # First create a report with old date (should be Expired)
        old_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        
        new_report = {
            "ship_id": TEST_SHIP_ID,
            "survey_report_name": "TEST_Update_Recalculate",
            "report_form": "Annual Survey",
            "survey_report_no": f"TEST-UPD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "issued_date": old_date,
            "issued_by": "DNV",
            "note": "Test update recalculates expiry"
        }
        
        create_response = self.session.post(
            f"{BASE_URL}/api/survey-reports",
            json=new_report
        )
        
        assert create_response.status_code == 200
        created_report = create_response.json()
        self.created_report_ids.append(created_report["id"])
        
        # Verify initial status is Expired
        assert created_report["status"] == "Expired", "Initial status should be Expired"
        print(f"✅ Initial status: {created_report['status']}")
        
        # Now update with recent date
        recent_date = datetime.now().strftime("%Y-%m-%d")
        update_data = {
            "issued_date": recent_date,
            "note": "Updated to recent date"
        }
        
        update_response = self.session.put(
            f"{BASE_URL}/api/survey-reports/{created_report['id']}",
            json=update_data
        )
        
        assert update_response.status_code == 200, f"Failed to update: {update_response.text}"
        
        updated_report = update_response.json()
        
        # Verify status is recalculated to Valid
        assert updated_report["status"] == "Valid", \
            f"After update with recent date, status should be 'Valid', got '{updated_report['status']}'"
        assert updated_report["expiry_date"] != created_report.get("expiry_date"), \
            "expiry_date should be recalculated after update"
        
        print(f"✅ After update: status={updated_report['status']}, expiry_date={updated_report['expiry_date']}")
    
    def test_07_issued_by_normalization(self):
        """Test: issued_by is normalized to abbreviation (e.g., 'DNV GL' -> 'DNV')"""
        new_report = {
            "ship_id": TEST_SHIP_ID,
            "survey_report_name": "TEST_Issued_By_Normalization",
            "report_form": "Annual Survey",
            "survey_report_no": f"TEST-NORM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "issued_date": datetime.now().strftime("%Y-%m-%d"),
            "issued_by": "DNV GL",  # Should be normalized to "DNV"
            "note": "Test issued_by normalization"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/survey-reports",
            json=new_report
        )
        
        assert response.status_code == 200
        created_report = response.json()
        self.created_report_ids.append(created_report["id"])
        
        # Check if issued_by is normalized
        assert created_report["issued_by"] == "DNV", \
            f"Expected 'DNV' after normalization, got '{created_report['issued_by']}'"
        
        print(f"✅ issued_by normalized: 'DNV GL' -> '{created_report['issued_by']}'")


class TestNoFetchCertificatesForSurveyReports:
    """Test that frontend doesn't need to fetch certificates for survey report status"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS
        )
        assert response.status_code == 200
        
        token = response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_survey_reports_api_returns_complete_data(self):
        """Test: Survey reports API returns all needed fields without needing certificates"""
        response = self.session.get(f"{BASE_URL}/api/survey-reports?ship_id={TEST_SHIP_ID}")
        
        assert response.status_code == 200
        reports = response.json()
        
        # Required fields that should be in API response
        required_fields = [
            "id", "ship_id", "survey_report_name", "report_form",
            "survey_report_no", "issued_date", "issued_by", "status",
            "expiry_date", "note"
        ]
        
        for report in reports:
            for field in required_fields:
                assert field in report, f"Missing required field: {field}"
            
            # Verify status is pre-calculated (not null/empty)
            assert report["status"], f"Status should be pre-calculated, got: {report['status']}"
        
        print(f"✅ API returns all required fields including pre-calculated status and expiry_date")
        print(f"   Total reports: {len(reports)}")
        for r in reports:
            print(f"   - {r['survey_report_name']}: status={r['status']}, expiry={r.get('expiry_date')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
