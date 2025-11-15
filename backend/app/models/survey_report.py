"""Survey Report specific models"""
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime

class SurveyReportBase(BaseModel):
    ship_id: str
    survey_report_name: str
    survey_report_no: Optional[str] = None
    survey_type: Optional[str] = None
    issued_by: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    surveyor_name: Optional[str] = None
    file_uploaded: bool = False
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    notes: Optional[str] = None
    google_drive_file_id: Optional[str] = None
    google_drive_folder_path: Optional[str] = None

class SurveyReportCreate(SurveyReportBase):
    pass

class SurveyReportUpdate(BaseModel):
    survey_report_name: Optional[str] = None
    survey_report_no: Optional[str] = None
    survey_type: Optional[str] = None
    issued_by: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    surveyor_name: Optional[str] = None
    notes: Optional[str] = None
    file_uploaded: Optional[bool] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None

class SurveyReportResponse(BaseModel):
    id: str
    ship_id: str
    survey_report_name: Optional[str] = None
    survey_report_no: Optional[str] = None
    survey_type: Optional[str] = None
    issued_by: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    surveyor_name: Optional[str] = None
    file_uploaded: bool = False
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    notes: Optional[str] = None
    google_drive_file_id: Optional[str] = None
    google_drive_folder_path: Optional[str] = None
    created_at: datetime

class BulkDeleteSurveyReportRequest(BaseModel):
    document_ids: List[str]
