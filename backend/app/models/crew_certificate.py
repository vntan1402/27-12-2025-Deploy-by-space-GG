from pydantic import BaseModel
from typing import Optional, Union, List
from datetime import datetime, date

class CrewCertificateBase(BaseModel):
    crew_id: str
    crew_name: str
    crew_name_en: Optional[str] = None  # English name for bilingual support
    passport: str
    rank: Optional[str] = None  # Crew rank/position
    date_of_birth: Optional[Union[str, date, datetime]] = None  # Crew date of birth
    cert_name: str
    cert_no: str
    issued_by: Optional[str] = None
    issued_by_abbreviation: Optional[str] = None  # Abbreviation for display
    issued_date: Optional[Union[str, datetime]] = None
    cert_expiry: Optional[Union[str, datetime]] = None
    status: Optional[str] = "Valid"  # Valid, Expiring Soon, Expired
    note: Optional[str] = None
    # File references
    crew_cert_file_id: Optional[str] = None
    crew_cert_file_name: Optional[str] = None  # File name stored on Google Drive
    crew_cert_summary_file_id: Optional[str] = None  # Summary file ID from Google Drive

class CrewCertificateCreate(CrewCertificateBase):
    ship_id: Optional[str] = None  # Optional for Standby crew
    company_id: Optional[str] = None  # Auto-set from current_user in endpoint

class CrewCertificateUpdate(BaseModel):
    crew_name: Optional[str] = None
    crew_name_en: Optional[str] = None
    passport: Optional[str] = None
    rank: Optional[str] = None
    date_of_birth: Optional[Union[str, date, datetime]] = None
    cert_name: Optional[str] = None
    cert_no: Optional[str] = None
    issued_by: Optional[str] = None
    issued_date: Optional[Union[str, datetime]] = None
    cert_expiry: Optional[Union[str, datetime]] = None
    status: Optional[str] = None
    note: Optional[str] = None
    crew_cert_file_id: Optional[str] = None
    crew_cert_file_name: Optional[str] = None
    crew_cert_summary_file_id: Optional[str] = None

class CrewCertificateResponse(CrewCertificateBase):
    id: str
    ship_id: Optional[str] = None  # Allow None for Standby crew certificates
    company_id: str
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

class BulkDeleteCrewCertificateRequest(BaseModel):
    """Request model for bulk delete crew certificate operations"""
    certificate_ids: List[str]

class CrewCertificateCheckDuplicate(BaseModel):
    """Request model for checking duplicate crew certificates"""
    crew_id: str
    cert_no: str
