"""Audit Certificate models - For ISM/ISPS/MLC certificates (different from audit reports)"""
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime

class AuditCertificateBase(BaseModel):
    ship_id: str
    cert_name: str
    cert_type: Optional[str] = None  # ISM, ISPS, MLC, etc.
    cert_abbreviation: Optional[str] = None  # Certificate abbreviation
    cert_no: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    last_endorse: Optional[Union[str, datetime]] = None
    issued_by: Optional[str] = None
    issued_by_abbreviation: Optional[str] = None
    status: Optional[str] = "Valid"
    note: Optional[str] = None
    next_survey_date: Optional[Union[str, datetime]] = None
    next_survey: Optional[Union[str, datetime]] = None  # ISO datetime format
    next_survey_display: Optional[str] = None  # Display format with window annotation (e.g., "30/10/2025 (±3M)")
    next_survey_type: Optional[str] = None  # Survey type (Initial, Intermediate, Renewal, etc.)
    extracted_ship_name: Optional[str] = None  # Ship name extracted by AI from certificate

class AuditCertificateCreate(AuditCertificateBase):
    pass

class AuditCertificateUpdate(BaseModel):
    cert_name: Optional[str] = None
    cert_type: Optional[str] = None
    cert_abbreviation: Optional[str] = None  # Certificate abbreviation
    cert_no: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    last_endorse: Optional[Union[str, datetime]] = None
    issued_by: Optional[str] = None
    issued_by_abbreviation: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None
    next_survey_date: Optional[Union[str, datetime]] = None
    next_survey: Optional[Union[str, datetime]] = None  # ISO datetime format
    next_survey_display: Optional[str] = None  # Display format with window annotation
    next_survey_type: Optional[str] = None  # Survey type

class AuditCertificateResponse(BaseModel):
    id: str
    ship_id: str
    cert_name: Optional[str] = None
    cert_type: Optional[str] = None
    cert_abbreviation: Optional[str] = None  # Certificate abbreviation
    cert_no: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    last_endorse: Optional[Union[str, datetime]] = None
    issued_by: Optional[str] = None
    issued_by_abbreviation: Optional[str] = None
    status: Optional[str] = "Valid"
    note: Optional[str] = None
    next_survey_date: Optional[Union[str, datetime]] = None
    next_survey: Optional[Union[str, datetime]] = None  # ISO datetime format
    next_survey_display: Optional[str] = None  # Display format with window annotation
    next_survey_type: Optional[str] = None  # Survey type
    file_id: Optional[str] = None
    summary_file_id: Optional[str] = None
    created_at: datetime

class BulkDeleteAuditCertificateRequest(BaseModel):
    document_ids: List[str]
