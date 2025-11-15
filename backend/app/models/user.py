from pydantic import BaseModel, EmailStr
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
    zalo: str  # Required field
    gmail: Optional[str] = None
    is_active: bool = True

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

class UserResponse(UserBase):
    id: str
    created_at: datetime
    permissions: Dict[str, Any] = {}

class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: Optional[bool] = False

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    remember_me: bool
