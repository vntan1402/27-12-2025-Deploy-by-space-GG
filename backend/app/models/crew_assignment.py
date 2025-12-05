from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class FilesMoved(BaseModel):
    """Track files moved during assignment changes"""
    passport_moved: bool = False
    certificates_moved: int = 0
    summaries_moved: int = 0


class CrewAssignmentBase(BaseModel):
    """Base model for crew assignment history"""
    crew_id: str
    company_id: str
    action_type: Literal["SIGN_ON", "SIGN_OFF", "SHIP_TRANSFER"]
    from_ship: Optional[str] = None  # null if from standby
    to_ship: Optional[str] = None    # null if sign off to standby
    from_status: str
    to_status: str
    action_date: datetime
    performed_by: str
    notes: Optional[str] = None
    files_moved: FilesMoved = Field(default_factory=FilesMoved)


class CrewAssignmentCreate(CrewAssignmentBase):
    """Model for creating crew assignment history record"""
    pass


class CrewAssignmentResponse(CrewAssignmentBase):
    """Response model for crew assignment history"""
    id: str
    created_at: datetime


class SignOffRequest(BaseModel):
    """Request model for signing off crew"""
    sign_off_date: str  # ISO date string or DD/MM/YYYY
    place_sign_off: Optional[str] = None
    notes: Optional[str] = None


class SignOnRequest(BaseModel):
    """Request model for signing on crew"""
    ship_name: str
    sign_on_date: str  # ISO date string or DD/MM/YYYY
    place_sign_on: Optional[str] = None
    notes: Optional[str] = None


class TransferRequest(BaseModel):
    """Request model for transferring crew between ships"""
    to_ship_name: str
    transfer_date: str  # ISO date string or DD/MM/YYYY
    notes: Optional[str] = None
