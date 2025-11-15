"""Drawing & Manual specific models"""
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime

class DrawingManualBase(BaseModel):
    ship_id: str
    document_name: str
    document_no: Optional[str] = None
    document_type: Optional[str] = None  # Drawing or Manual
    approved_by: Optional[str] = None
    approved_date: Optional[Union[str, datetime]] = None
    revision_no: Optional[str] = None
    revision_date: Optional[Union[str, datetime]] = None
    file_uploaded: bool = False
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    notes: Optional[str] = None
    google_drive_file_id: Optional[str] = None
    google_drive_folder_path: Optional[str] = None

class DrawingManualCreate(DrawingManualBase):
    pass

class DrawingManualUpdate(BaseModel):
    document_name: Optional[str] = None
    document_no: Optional[str] = None
    document_type: Optional[str] = None
    approved_by: Optional[str] = None
    approved_date: Optional[Union[str, datetime]] = None
    revision_no: Optional[str] = None
    revision_date: Optional[Union[str, datetime]] = None
    notes: Optional[str] = None
    file_uploaded: Optional[bool] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None

class DrawingManualResponse(BaseModel):
    id: str
    ship_id: str
    document_name: Optional[str] = None
    document_no: Optional[str] = None
    document_type: Optional[str] = None
    approved_by: Optional[str] = None
    approved_date: Optional[Union[str, datetime]] = None
    revision_no: Optional[str] = None
    revision_date: Optional[Union[str, datetime]] = None
    file_uploaded: bool = False
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    notes: Optional[str] = None
    google_drive_file_id: Optional[str] = None
    google_drive_folder_path: Optional[str] = None
    created_at: datetime

class BulkDeleteDrawingManualRequest(BaseModel):
    document_ids: List[str]
