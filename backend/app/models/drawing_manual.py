"""Drawing & Manual specific models - Matching backend-v1 schema"""
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime

class DrawingManualBase(BaseModel):
    ship_id: str
    document_name: str
    document_no: Optional[str] = None
    approved_by: Optional[str] = None
    approved_date: Optional[Union[str, datetime]] = None
    status: Optional[str] = "Unknown"
    note: Optional[str] = None

class DrawingManualCreate(DrawingManualBase):
    pass

class DrawingManualUpdate(BaseModel):
    document_name: Optional[str] = None
    document_no: Optional[str] = None
    approved_by: Optional[str] = None
    approved_date: Optional[Union[str, datetime]] = None
    status: Optional[str] = None
    note: Optional[str] = None

class DrawingManualResponse(BaseModel):
    id: str
    ship_id: str
    document_name: str  # Required field - matching backend-v1
    document_no: Optional[str] = None
    approved_by: Optional[str] = None
    approved_date: Optional[Union[str, datetime]] = None
    status: str  # Required - matching backend-v1
    note: Optional[str] = None
    file_id: Optional[str] = None
    summary_file_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None  # Add for backward compatibility
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class BulkDeleteDrawingManualRequest(BaseModel):
    document_ids: List[str]
