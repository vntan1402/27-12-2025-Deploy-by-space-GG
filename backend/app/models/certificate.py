from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

class CertificateBase(BaseModel):
    ship_id: str
    cert_name: str
    cert_abbreviation: Optional[str] = None  # Certificate abbreviation
    cert_type: Optional[str] = None  # Full Term, Interim, Provisional, Short term, Conditional, Other
    cert_no: Optional[str] = None
    issue_date: Optional[datetime] = None
    valid_date: Optional[datetime] = None
    last_endorse: Optional[datetime] = None
    next_survey: Optional[datetime] = None
    next_survey_type: Optional[str] = None  # Annual, Intermediate, Special, Renewal, etc.
    issued_by: Optional[str] = None  # Classification Society, Flag, Insurance, etc.
    category: str = "certificates"
    sensitivity_level: str = "public"
    file_uploaded: bool = False
    google_drive_file_id: Optional[str] = None
    google_drive_folder_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    notes: Optional[str] = None
    ship_name: Optional[str] = None  # For folder organization

class CertificateCreate(CertificateBase):
    pass

class CertificateUpdate(BaseModel):
    cert_name: Optional[str] = None
    cert_abbreviation: Optional[str] = None
    cert_no: Optional[str] = None
    cert_type: Optional[str] = None
    issue_date: Optional[datetime] = None
    valid_date: Optional[datetime] = None
    last_endorse: Optional[datetime] = None
    next_survey: Optional[datetime] = None
    next_survey_type: Optional[str] = None
    issued_by: Optional[str] = None
    issued_by_abbreviation: Optional[str] = None
    category: Optional[str] = None
    sensitivity_level: Optional[str] = None
    notes: Optional[str] = None
    exclude_from_auto_update: Optional[bool] = None

class CertificateResponse(BaseModel):
    id: str
    ship_id: Optional[str] = None
    cert_name: Optional[str] = None
    cert_type: Optional[str] = None
    cert_no: Optional[str] = None
    issue_date: Optional[datetime] = None
    valid_date: Optional[datetime] = None
    last_endorse: Optional[datetime] = None
    next_survey: Optional[datetime] = None
    next_survey_type: Optional[str] = None
    issued_by: Optional[str] = None
    category: Optional[str] = "certificates"
    sensitivity_level: Optional[str] = "public"
    file_uploaded: Optional[bool] = False
    google_drive_file_id: Optional[str] = None
    google_drive_folder_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    notes: Optional[str] = None
    ship_name: Optional[str] = None
    created_at: datetime
    cert_abbreviation: Optional[str] = None
    status: Optional[str] = None  # Valid/Expired status
    issued_by_abbreviation: Optional[str] = None
    has_notes: Optional[bool] = None
    next_survey_display: Optional[str] = None
    extracted_ship_name: Optional[str] = None
    text_content: Optional[str] = None
    exclude_from_auto_update: Optional[bool] = False
    
    @field_validator('next_survey', mode='before')
    @classmethod
    def validate_next_survey(cls, v):
        """Handle both datetime and string formats for next_survey field"""
        if v is None:
            return None
        
        if isinstance(v, datetime):
            return v
        
        if isinstance(v, str):
            # Try dd/MM/yyyy format
            try:
                return datetime.strptime(v, '%d/%m/%Y')
            except ValueError:
                pass
            
            # Try ISO format
            try:
                if v.endswith('Z'):
                    v = v[:-1] + '+00:00'
                return datetime.fromisoformat(v)
            except ValueError:
                pass
        
        return None

class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete operations"""
    certificate_ids: List[str]
