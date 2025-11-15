"""
Test Report specific models
"""
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime

class TestReportBase(BaseModel):
    ship_id: str
    test_report_name: str
    report_form: Optional[str] = None  # Report Form field (e.g., "Bunker Analysis", "Water Test")
    test_sample: Optional[str] = None
    test_report_no: Optional[str] = None
    issued_by: Optional[str] = None
    issued_date: Optional[Union[str, datetime]] = None  # Renamed from issue_date for consistency
    valid_date: Optional[Union[str, datetime]] = None
    status: Optional[str] = "Valid"  # Valid, Expired soon, Critical, Expired
    file_uploaded: bool = False
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    note: Optional[str] = None  # Frontend sends 'note' (singular)
    notes: Optional[str] = None  # Backend stores 'notes' (plural) for backward compatibility
    google_drive_file_id: Optional[str] = None
    google_drive_folder_path: Optional[str] = None

class TestReportCreate(TestReportBase):
    pass

class TestReportUpdate(BaseModel):
    test_report_name: Optional[str] = None
    report_form: Optional[str] = None
    test_sample: Optional[str] = None
    test_report_no: Optional[str] = None
    issued_by: Optional[str] = None
    issued_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    status: Optional[str] = None
    note: Optional[str] = None  # Frontend sends 'note' (singular)
    notes: Optional[str] = None  # Backend stores 'notes' (plural) for backward compatibility
    file_uploaded: Optional[bool] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None

class TestReportResponse(BaseModel):
    id: str
    ship_id: str
    test_report_name: Optional[str] = None  # Optional for old data
    report_form: Optional[str] = None
    test_sample: Optional[str] = None
    test_report_no: Optional[str] = None
    issued_by: Optional[str] = None
    issued_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    status: Optional[str] = "Valid"
    file_uploaded: bool = False
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    note: Optional[str] = None  # Frontend reads 'note' (singular)
    notes: Optional[str] = None  # Database stores 'notes' (plural)
    google_drive_file_id: Optional[str] = None
    google_drive_folder_path: Optional[str] = None
    test_report_file_id: Optional[str] = None  # For backward compatibility
    test_report_summary_file_id: Optional[str] = None  # For backward compatibility
    created_at: datetime

class BulkDeleteTestReportRequest(BaseModel):
    """Request model for bulk delete test report operations"""
    document_ids: List[str]
