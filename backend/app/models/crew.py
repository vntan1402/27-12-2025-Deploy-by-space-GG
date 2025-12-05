from pydantic import BaseModel
from typing import Optional, Union, List
from datetime import datetime

class CrewBase(BaseModel):
    full_name: str
    full_name_en: Optional[str] = None
    sex: str  # M or F
    date_of_birth: Union[str, datetime]
    place_of_birth: str
    place_of_birth_en: Optional[str] = None
    passport: str
    nationality: Optional[str] = None
    rank: Optional[str] = None
    seamen_book: Optional[str] = None
    status: str = "Sign on"  # Sign on, Standby, Leave
    ship_sign_on: Optional[str] = "-"
    place_sign_on: Optional[str] = None
    date_sign_on: Optional[Union[str, datetime]] = None
    place_sign_off: Optional[str] = None
    date_sign_off: Optional[Union[str, datetime]] = None
    passport_issue_date: Optional[Union[str, datetime]] = None
    passport_expiry_date: Optional[Union[str, datetime]] = None
    passport_file_id: Optional[str] = None
    passport_file_name: Optional[str] = None  # File name stored on Google Drive
    summary_file_id: Optional[str] = None

class CrewCreate(CrewBase):
    company_id: Optional[str] = None  # Will be set automatically from current_user if not provided

class CrewUpdate(BaseModel):
    full_name: Optional[str] = None
    full_name_en: Optional[str] = None
    sex: Optional[str] = None
    date_of_birth: Optional[Union[str, datetime]] = None
    place_of_birth: Optional[str] = None
    place_of_birth_en: Optional[str] = None
    passport: Optional[str] = None
    nationality: Optional[str] = None
    rank: Optional[str] = None
    seamen_book: Optional[str] = None
    status: Optional[str] = None
    ship_sign_on: Optional[str] = None
    place_sign_on: Optional[str] = None
    date_sign_on: Optional[Union[str, datetime]] = None
    date_sign_off: Optional[Union[str, datetime]] = None
    passport_issue_date: Optional[Union[str, datetime]] = None
    passport_expiry_date: Optional[Union[str, datetime]] = None
    passport_file_id: Optional[str] = None
    passport_file_name: Optional[str] = None  # File name stored on Google Drive
    summary_file_id: Optional[str] = None

class CrewResponse(CrewBase):
    id: str
    company_id: str
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

class BulkDeleteCrewRequest(BaseModel):
    """Request model for bulk delete crew operations"""
    crew_ids: List[str]
