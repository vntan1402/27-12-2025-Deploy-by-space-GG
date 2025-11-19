"""Audit Report models for ISM/ISPS/MLC - Matching backend-v1 schema"""
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime

class AuditReportBase(BaseModel):
    ship_id: str
    audit_report_name: str
    audit_type: Optional[str] = None  # ISM, ISPS, MLC, CICA, SMC, DOC, etc.
    report_form: Optional[str] = None
    audit_report_no: Optional[str] = None
    audit_date: Optional[Union[str, datetime]] = None
    issued_by: Optional[str] = None
    issued_by_abbreviation: Optional[str] = None
    status: Optional[str] = "Valid"
    note: Optional[str] = None
    auditor_name: Optional[str] = None
    next_audit_date: Optional[Union[str, datetime]] = None
    findings_count: Optional[int] = None
    nc_count: Optional[int] = None
    original_filename: Optional[str] = None  # Store original PDF filename for re-extraction

class AuditReportCreate(AuditReportBase):
    pass

class AuditReportUpdate(BaseModel):
    audit_report_name: Optional[str] = None
    audit_type: Optional[str] = None
    report_form: Optional[str] = None
    audit_report_no: Optional[str] = None
    audit_date: Optional[Union[str, datetime]] = None
    issued_by: Optional[str] = None
    issued_by_abbreviation: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None
    auditor_name: Optional[str] = None
    next_audit_date: Optional[Union[str, datetime]] = None
    findings_count: Optional[int] = None
    nc_count: Optional[int] = None
    original_filename: Optional[str] = None

class AuditReportResponse(BaseModel):
    id: str
    ship_id: str
    audit_report_name: Optional[str] = None
    audit_type: Optional[str] = None
    report_form: Optional[str] = None
    audit_report_no: Optional[str] = None
    audit_date: Optional[Union[str, datetime]] = None
    issued_by: Optional[str] = None
    issued_by_abbreviation: Optional[str] = None
    status: Optional[str] = "Valid"
    note: Optional[str] = None
    auditor_name: Optional[str] = None
    next_audit_date: Optional[Union[str, datetime]] = None
    findings_count: Optional[int] = None
    nc_count: Optional[int] = None
    audit_report_file_id: Optional[str] = None  # Fixed: was file_id
    audit_report_summary_file_id: Optional[str] = None  # Fixed: was summary_file_id
    created_at: datetime

class BulkDeleteAuditReportRequest(BaseModel):
    document_ids: List[str]
