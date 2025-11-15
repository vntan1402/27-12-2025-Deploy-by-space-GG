"""Approval Document models - Matching backend-v1 schema"""
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime

class ApprovalDocumentBase(BaseModel):
    ship_id: str
    approval_document_name: str
    approval_document_no: Optional[str] = None
    approved_by: Optional[str] = None
    approved_date: Optional[Union[str, datetime]] = None
    status: Optional[str] = "Unknown"
    note: Optional[str] = None

class ApprovalDocumentCreate(ApprovalDocumentBase):
    pass

class ApprovalDocumentUpdate(BaseModel):
    approval_document_name: Optional[str] = None
    approval_document_no: Optional[str] = None
    approved_by: Optional[str] = None
    approved_date: Optional[Union[str, datetime]] = None
    status: Optional[str] = None
    note: Optional[str] = None

class ApprovalDocumentResponse(BaseModel):
    id: str
    ship_id: str
    approval_document_name: Optional[str] = None
    approval_document_no: Optional[str] = None
    approved_by: Optional[str] = None
    approved_date: Optional[Union[str, datetime]] = None
    status: Optional[str] = "Unknown"
    note: Optional[str] = None
    file_id: Optional[str] = None
    summary_file_id: Optional[str] = None
    created_at: datetime

class BulkDeleteApprovalDocumentRequest(BaseModel):
    document_ids: List[str]
