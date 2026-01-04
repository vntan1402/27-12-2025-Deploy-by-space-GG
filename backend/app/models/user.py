from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor" 
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    SYSTEM_ADMIN = "system_admin"  # Highest authority

class Department(str, Enum):
    TECHNICAL = "technical"
    OPERATIONS = "operations"
    LOGISTICS = "logistics"
    FINANCE = "finance"
    SHIP_CREW = "ship_crew"
    SSO = "sso"  # Ship Security Officer
    CSO = "cso"  # Company Security Officer
    CREWING = "crewing"
    SAFETY = "safety"
    COMMERCIAL = "commercial"
    DPA = "dpa"
    SUPPLY = "supply"

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: str
    role: UserRole
    department: List[str]  # Multiple departments supported
    company: Optional[str] = None
    ship: Optional[str] = None
    zalo: Optional[str] = None  # Optional field for Zalo contact
    gmail: Optional[str] = None
    is_active: bool = True
    signature_file_id: Optional[str] = None  # Google Drive file ID
    signature_url: Optional[str] = None  # URL to view signature image
    crew_id: Optional[str] = None  # Link to crew record for role=viewer (Crew)
    
    @field_validator('email', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        """Convert empty string to None for email field"""
        if v == '' or v is None:
            return None
        return v

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[List[str]] = None
    company: Optional[str] = None
    ship: Optional[str] = None
    zalo: Optional[str] = None
    gmail: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    crew_id: Optional[str] = None  # Link to crew record
    signature_file_id: Optional[str] = None
    signature_url: Optional[str] = None

class UserResponse(UserBase):
    id: str
    created_at: datetime
    permissions: Dict[str, Any] = {}
    signature_file_id: Optional[str] = None
    signature_url: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: Optional[bool] = False

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    remember_me: bool
