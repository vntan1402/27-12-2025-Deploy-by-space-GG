"""
Test Report specific models
"""
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime

class TestReportBase(BaseModel):
    ship_id: str
    test_report_name: str
    test_sample: Optional[str] = None
    test_report_no: Optional[str] = None
    issued_by: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    file_uploaded: bool = False
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    notes: Optional[str] = None
    google_drive_file_id: Optional[str] = None
    google_drive_folder_path: Optional[str] = None

class TestReportCreate(TestReportBase):
    pass

class TestReportUpdate(BaseModel):
    test_report_name: Optional[str] = None
    test_sample: Optional[str] = None
    test_report_no: Optional[str] = None
    issued_by: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    notes: Optional[str] = None
    file_uploaded: Optional[bool] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None

class TestReportResponse(BaseModel):
    id: str
    ship_id: str
    test_report_name: Optional[str] = None  # Optional for old data
    test_sample: Optional[str] = None
    test_report_no: Optional[str] = None
    issued_by: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    file_uploaded: bool = False
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    notes: Optional[str] = None
    google_drive_file_id: Optional[str] = None
    google_drive_folder_path: Optional[str] = None
    created_at: datetime

class BulkDeleteTestReportRequest(BaseModel):
    """Request model for bulk delete test report operations"""
    document_ids: List[str]
