from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SystemAnnouncementBase(BaseModel):
    title_vn: str = Field(..., min_length=1, max_length=200)
    title_en: str = Field(..., min_length=1, max_length=200)
    content_vn: str = Field(..., min_length=1, max_length=1000)
    content_en: str = Field(..., min_length=1, max_length=1000)
    type: str = Field(default="info", pattern="^(info|warning|success|error)$")
    priority: int = Field(default=1, ge=1, le=10)
    is_active: bool = Field(default=True)
    start_date: str  # ISO format date string
    end_date: str    # ISO format date string

class SystemAnnouncementCreate(SystemAnnouncementBase):
    pass

class SystemAnnouncementUpdate(BaseModel):
    title_vn: Optional[str] = Field(None, min_length=1, max_length=200)
    title_en: Optional[str] = Field(None, min_length=1, max_length=200)
    content_vn: Optional[str] = Field(None, min_length=1, max_length=1000)
    content_en: Optional[str] = Field(None, min_length=1, max_length=1000)
    type: Optional[str] = Field(None, pattern="^(info|warning|success|error)$")
    priority: Optional[int] = Field(None, ge=1, le=10)
    is_active: Optional[bool] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class SystemAnnouncementResponse(SystemAnnouncementBase):
    id: str
    created_by: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
