"""Company Certificate models - For company-level certificates (DOC, Safety Management, etc.)"""
from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime

class CompanyCertBase(BaseModel):
    cert_name: str
    cert_no: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None  # Optional field
    issued_by: Optional[str] = None
    status: Optional[str] = "Valid"
    notes: Optional[str] = None
    has_notes: Optional[bool] = None
    file_name: Optional[str] = None  # Original filename when uploaded
    file_id: Optional[str] = None  # Google Drive file ID
    file_url: Optional[str] = None  # Google Drive file URL

class CompanyCertCreate(CompanyCertBase):
    company: str  # Company ID (required on create)

class CompanyCertUpdate(BaseModel):
    cert_name: Optional[str] = None
    cert_no: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    issued_by: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    has_notes: Optional[bool] = None
    file_name: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None

class CompanyCertResponse(BaseModel):
    id: str
    company: str
    cert_name: Optional[str] = None
    cert_no: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    issued_by: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    has_notes: Optional[bool] = None
    file_name: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    summary_file_id: Optional[str] = None  # Google Drive summary text file ID
    summary_file_url: Optional[str] = None  # Google Drive summary text file URL
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

class BulkDeleteCompanyCertRequest(BaseModel):
    """Request model for bulk delete company certificates"""
    cert_ids: list[str]
