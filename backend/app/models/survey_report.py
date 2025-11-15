"""Survey Report specific models - Matching backend-v1 schema"""
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime

class SurveyReportBase(BaseModel):
    ship_id: str
    survey_report_name: str
    report_form: Optional[str] = None
    survey_report_no: Optional[str] = None
    issued_date: Optional[Union[str, datetime]] = None
    issued_by: Optional[str] = None
    status: Optional[str] = "Valid"
    note: Optional[str] = None
    surveyor_name: Optional[str] = None

class SurveyReportCreate(SurveyReportBase):
    pass

class SurveyReportUpdate(BaseModel):
    survey_report_name: Optional[str] = None
    report_form: Optional[str] = None
    survey_report_no: Optional[str] = None
    issued_date: Optional[Union[str, datetime]] = None
    issued_by: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None
    surveyor_name: Optional[str] = None

class SurveyReportResponse(BaseModel):
    id: str
    ship_id: str
    survey_report_name: Optional[str] = None
    report_form: Optional[str] = None
    survey_report_no: Optional[str] = None
    issued_date: Optional[Union[str, datetime]] = None
    issued_by: Optional[str] = None
    status: Optional[str] = "Valid"
    note: Optional[str] = None
    surveyor_name: Optional[str] = None
    file_id: Optional[str] = None
    summary_file_id: Optional[str] = None
    created_at: datetime

class BulkDeleteSurveyReportRequest(BaseModel):
    document_ids: List[str]
