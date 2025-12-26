"""
Upload Task Model
For tracking background processing of certificate/survey report uploads
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingType(str, Enum):
    """Processing type enum"""
    TEXT_LAYER = "text_layer"  # Fast path - has text layer
    DOCUMENT_AI = "document_ai"  # Slow path - needs OCR


class FileTaskStatus(BaseModel):
    """Status for individual file in upload task"""
    filename: str
    status: TaskStatus = TaskStatus.PENDING
    processing_type: Optional[ProcessingType] = None
    progress: int = 0  # 0-100
    has_text_layer: Optional[bool] = None
    text_char_count: Optional[int] = None
    result: Optional[Dict[str, Any]] = None  # Certificate data if success
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class UploadTask(BaseModel):
    """Upload task model for background processing"""
    task_id: str
    task_type: str = "certificate"  # "certificate" or "survey_report"
    status: TaskStatus = TaskStatus.PENDING
    files: List[FileTaskStatus] = []
    
    # Context
    ship_id: str
    user_id: str
    company_id: str
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    # Summary
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    
    class Config:
        use_enum_values = True


class UploadTaskCreate(BaseModel):
    """Create upload task request"""
    task_type: str = "certificate"
    ship_id: str
    filenames: List[str]


class UploadTaskResponse(BaseModel):
    """Upload task response"""
    task_id: str
    status: str
    task_type: str
    total_files: int
    completed_files: int
    failed_files: int
    files: List[FileTaskStatus]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    # Results (when completed)
    results: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[Dict[str, Any]]] = None
