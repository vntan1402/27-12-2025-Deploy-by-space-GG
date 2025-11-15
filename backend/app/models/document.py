"""
Generic document models for all document types
Survey Reports, Test Reports, Drawings, ISM/ISPS/MLC/Supply Documents
"""
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime

class DocumentBase(BaseModel):
    ship_id: str
    doc_name: str
    doc_no: Optional[str] = None
    issued_by: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    category: str  # survey_report, test_report, etc.
    file_uploaded: bool = False
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    notes: Optional[str] = None
    google_drive_file_id: Optional[str] = None
    google_drive_folder_path: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    doc_name: Optional[str] = None
    doc_no: Optional[str] = None
    issued_by: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    notes: Optional[str] = None
    file_uploaded: Optional[bool] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None

class DocumentResponse(BaseModel):
    id: str
    ship_id: str
    doc_name: Optional[str] = None  # Optional for backward compatibility
    doc_no: Optional[str] = None
    issued_by: Optional[str] = None
    issue_date: Optional[Union[str, datetime]] = None
    valid_date: Optional[Union[str, datetime]] = None
    category: Optional[str] = None  # Optional for backward compatibility
    file_uploaded: bool = False
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    notes: Optional[str] = None
    google_drive_file_id: Optional[str] = None
    google_drive_folder_path: Optional[str] = None
    created_at: datetime

class BulkDeleteDocumentRequest(BaseModel):
    """Request model for bulk delete document operations"""
    document_ids: List[str]
