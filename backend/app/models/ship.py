from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SpecialSurveyCycle(BaseModel):
    """Special survey cycle representing maritime special survey requirements"""
    from_date: Optional[datetime] = None  # Start of special survey cycle
    to_date: Optional[datetime] = None    # End of special survey cycle
    intermediate_required: bool = False   # Whether intermediate surveys are required
    cycle_type: Optional[str] = None      # Type of special survey cycle (Annual, Intermediate, etc.)

class AnniversaryDate(BaseModel):
    """Anniversary date derived from Full Term certificates with manual override capability"""
    day: Optional[int] = None  # Day (1-31)
    month: Optional[int] = None  # Month (1-12)  
    auto_calculated: bool = True  # Whether calculated from certificates or manually set
    source_certificate_type: Optional[str] = None  # Type of certificate used for calculation
    manual_override: bool = False  # Whether manually overridden by user

class DryDockCycle(BaseModel):
    """Dry dock cycle representing maritime dry docking requirements"""
    from_date: Optional[datetime] = None  # Start of dry dock cycle
    to_date: Optional[datetime] = None    # End of dry dock cycle
    intermediate_docking_required: bool = True  # Whether intermediate docking is required
    last_intermediate_docking: Optional[datetime] = None  # Date of last intermediate docking

class ShipBase(BaseModel):
    name: str
    imo: Optional[str] = None
    flag: str
    ship_type: Optional[str] = None  # Ship type (e.g., "Container Ship", "Bulk Carrier", "Tanker")
    class_society: Optional[str] = None  # Class society (e.g., "DNV GL", "ABS", "Lloyd's Register", "BV")
    gross_tonnage: Optional[float] = None
    deadweight: Optional[float] = None
    built_year: Optional[int] = None  # Legacy field - year only
    delivery_date: Optional[datetime] = None  # Full delivery date
    keel_laid: Optional[datetime] = None  # Keel laid date
    last_docking: Optional[datetime] = None  # Last dry docking date (Docking 1)
    last_docking_2: Optional[datetime] = None  # Second last dry docking date (Docking 2)
    next_docking: Optional[datetime] = None  # Next scheduled docking date
    last_special_survey: Optional[datetime] = None  # Last special survey date
    last_intermediate_survey: Optional[datetime] = None  # Last intermediate survey date
    special_survey_cycle: Optional[SpecialSurveyCycle] = None  # Special survey cycle
    dry_dock_cycle: Optional[DryDockCycle] = None  # Dry dock cycle
    anniversary_date: Optional[AnniversaryDate] = None  # Anniversary date
    ship_owner: Optional[str] = None  # Ship owner company name
    company: str  # Company that manages the ship
    
    # Legacy fields for backward compatibility
    legacy_anniversary_date: Optional[datetime] = None
    
    # Google Drive folder creation status fields
    gdrive_folder_status: Optional[str] = "pending"
    gdrive_folder_error: Optional[str] = None
    gdrive_folder_created_at: Optional[datetime] = None

class ShipCreate(ShipBase):
    pass

class ShipUpdate(BaseModel):
    name: Optional[str] = None
    imo: Optional[str] = None
    flag: Optional[str] = None
    ship_type: Optional[str] = None
    class_society: Optional[str] = None
    gross_tonnage: Optional[float] = None
    deadweight: Optional[float] = None
    built_year: Optional[int] = None
    delivery_date: Optional[datetime] = None
    keel_laid: Optional[datetime] = None
    last_docking: Optional[datetime] = None
    last_docking_2: Optional[datetime] = None
    next_docking: Optional[datetime] = None
    last_special_survey: Optional[datetime] = None
    last_intermediate_survey: Optional[datetime] = None
    special_survey_cycle: Optional[SpecialSurveyCycle] = None
    anniversary_date: Optional[AnniversaryDate] = None
    ship_owner: Optional[str] = None
    company: Optional[str] = None
    legacy_anniversary_date: Optional[datetime] = None

class ShipResponse(ShipBase):
    id: str
    created_at: datetime
