"""Other Document specific models - Matching backend-v1 schema"""
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime

class OtherDocumentBase(BaseModel):
    ship_id: str
    document_name: str
    date: Optional[Union[str, datetime]] = None
    status: Optional[str] = "Unknown"
    note: Optional[str] = None

class OtherDocumentCreate(OtherDocumentBase):
    file_ids: Optional[List[str]] = None
    folder_id: Optional[str] = None
    folder_link: Optional[str] = None

class OtherDocumentUpdate(BaseModel):
    document_name: Optional[str] = None
    date: Optional[Union[str, datetime]] = None
    status: Optional[str] = None
    note: Optional[str] = None
    file_ids: Optional[List[str]] = None
    folder_id: Optional[str] = None
    folder_link: Optional[str] = None

class OtherDocumentResponse(BaseModel):
    id: str
    ship_id: str
    document_name: Optional[str] = None
    date: Optional[Union[str, datetime]] = None
    status: Optional[str] = "Unknown"
    note: Optional[str] = None
    file_ids: Optional[List[str]] = None
    folder_id: Optional[str] = None
    folder_link: Optional[str] = None
    created_at: datetime

class BulkDeleteOtherDocumentRequest(BaseModel):
    document_ids: List[str]
