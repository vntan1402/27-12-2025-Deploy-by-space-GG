from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import json
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from enum import Enum
import shutil
import requests
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType

# Import our MongoDB database modules
from mongodb_database import mongo_db
from google_drive_manager import GoogleDriveManager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# AI Configuration
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Create upload directory
UPLOAD_DIR = Path(ROOT_DIR) / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Security
security = HTTPBearer()

# Create the main app
app = FastAPI(title="Ship Management System API", version="2.0.0 - MongoDB")
api_router = APIRouter(prefix="/api")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models (keep existing models)
class UserRole(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor" 
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class Department(str, Enum):
    TECHNICAL = "technical"
    OPERATIONS = "operations"
    LOGISTICS = "logistics"
    FINANCE = "finance"
    SHIP_CREW = "ship_crew"
    CREWING = "crewing"
    SAFETY = "safety"
    COMMERCIAL = "commercial"

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: str
    role: UserRole
    department: Department
    company: Optional[str] = None
    ship: Optional[str] = None
    zalo: str  # Now required field
    gmail: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[Department] = None
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
    remember_me: bool = False

class CompanyBase(BaseModel):
    name_vn: str
    name_en: str
    address_vn: str
    address_en: str
    tax_id: str
    gmail: Optional[str] = None
    zalo: Optional[str] = None
    system_expiry: Optional[datetime] = None
    gdrive_config: Optional[Dict[str, Any]] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name_vn: Optional[str] = None
    name_en: Optional[str] = None
    address_vn: Optional[str] = None
    address_en: Optional[str] = None
    tax_id: Optional[str] = None
    gmail: Optional[str] = None
    zalo: Optional[str] = None
    system_expiry: Optional[datetime] = None
    gdrive_config: Optional[Dict[str, Any]] = None

class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None

# Ship models
class ShipBase(BaseModel):
    name: str
    imo: Optional[str] = None
    flag: Optional[str] = None
    ship_type: Optional[str] = None
    gross_tonnage: Optional[float] = None
    year_built: Optional[int] = None
    ship_owner: Optional[str] = None
    company: Optional[str] = None

class ShipCreate(ShipBase):
    pass

class ShipUpdate(BaseModel):
    name: Optional[str] = None
    imo: Optional[str] = None
    flag: Optional[str] = None
    ship_type: Optional[str] = None
    gross_tonnage: Optional[float] = None
    year_built: Optional[int] = None
    ship_owner: Optional[str] = None
    company: Optional[str] = None

class ShipResponse(ShipBase):
    id: str
    created_at: datetime

# Ship Survey Status models
class ShipSurveyStatusBase(BaseModel):
    ship_id: str
    certificate_type: str  # CLASS, STATUTORY, AUDITS, Bottom Surveys
    certificate_number: Optional[str] = None
    survey_type: str  # Annual, Intermediate, Renewal, Change of RO, Approval, Initial Audit
    issuance_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    renewal_range_start: Optional[datetime] = None
    renewal_range_end: Optional[datetime] = None
    due_date_1: Optional[datetime] = None
    due_date_2: Optional[datetime] = None
    due_date_3: Optional[datetime] = None
    due_date_4: Optional[datetime] = None
    last_annual_survey_place: Optional[str] = None
    survey_status: str = "due"  # due, completed, overdue, pending
    surveyor: Optional[str] = None
    remarks: Optional[str] = None

class ShipSurveyStatusCreate(ShipSurveyStatusBase):
    pass

class ShipSurveyStatusUpdate(BaseModel):
    certificate_type: Optional[str] = None
    certificate_number: Optional[str] = None
    survey_type: Optional[str] = None
    issuance_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    renewal_range_start: Optional[datetime] = None
    renewal_range_end: Optional[datetime] = None
    due_date_1: Optional[datetime] = None
    due_date_2: Optional[datetime] = None
    due_date_3: Optional[datetime] = None
    due_date_4: Optional[datetime] = None
    last_annual_survey_place: Optional[str] = None
    survey_status: Optional[str] = None
    surveyor: Optional[str] = None
    remarks: Optional[str] = None

class ShipSurveyStatusResponse(ShipSurveyStatusBase):
    id: str
    created_at: datetime

# Certificate models
class CertificateBase(BaseModel):
    ship_id: str
    cert_name: str
    cert_type: Optional[str] = None  # Interim, Provisional, Short term, Full Term
    cert_no: str
    issue_date: datetime
    valid_date: datetime
    last_endorse: Optional[datetime] = None
    next_survey: Optional[datetime] = None
    issued_by: Optional[str] = None  # Classification Society, Flag, Insurance, etc.
    category: str = "certificates"
    sensitivity_level: str = "public"
    file_uploaded: bool = False
    google_drive_file_id: Optional[str] = None
    google_drive_folder_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    ship_name: Optional[str] = None  # For folder organization

class CertificateCreate(CertificateBase):
    pass

class CertificateUpdate(BaseModel):
    cert_name: Optional[str] = None
    cert_no: Optional[str] = None
    issue_date: Optional[datetime] = None
    valid_date: Optional[datetime] = None
    last_endorse: Optional[datetime] = None
    next_survey: Optional[datetime] = None
    category: Optional[str] = None
    sensitivity_level: Optional[str] = None

class CertificateResponse(CertificateBase):
    id: str
    created_at: datetime

# Google Drive models
class GoogleDriveConfig(BaseModel):
    service_account_json: str
    folder_id: str

class GoogleDriveStatus(BaseModel):
    configured: bool
    last_sync: Optional[str] = None
    local_files: int = 0
    drive_files: int = 0
    folder_id: Optional[str] = None
    service_account_email: Optional[str] = None

class GoogleDriveTestResponse(BaseModel):
    success: bool
    message: str
    folder_name: Optional[str] = None
    service_account_email: Optional[str] = None

# Google Drive OAuth Models
class GoogleDriveOAuthConfig(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    folder_id: str

class GoogleDriveOAuthRequest(BaseModel):
    authorization_code: str
    state: str
    folder_id: str

class GoogleDriveOAuthResponse(BaseModel):
    success: bool
    message: str
    authorization_url: Optional[str] = None
    state: Optional[str] = None

# Google Drive Apps Script Models
class GoogleDriveAppsScriptConfig(BaseModel):
    web_app_url: str
    folder_id: str

class GoogleDriveProxyResponse(BaseModel):
    success: bool
    message: str
    folder_name: Optional[str] = None

# Usage tracking
class UsageRequest(BaseModel):
    user_id: str
    action: str
    resource: str
    details: Optional[Dict[str, Any]] = None

class UsageStats(BaseModel):
    total_requests: int
    requests_by_user: Dict[str, int]
    requests_by_action: Dict[str, int]
    requests_by_type: Dict[str, int]
    date_range: str

# Helper Functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_id: str, username: str, role: str, company: str = None, full_name: str = None, expiration_hours: int = JWT_EXPIRATION_HOURS) -> str:
    """Create JWT access token"""
    expire = datetime.now(timezone.utc) + timedelta(hours=expiration_hours)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "company": company,
        "full_name": full_name,
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """Get current user from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        username = payload.get("username")
        
        if not user_id or not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        # Get user from MongoDB
        user_data = await mongo_db.find_one("users", {"id": user_id})
        if not user_data:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        return UserResponse(**user_data)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def has_permission(user: UserResponse, required_role: UserRole) -> bool:
    """Check if user has required role or higher"""
    role_hierarchy = {
        UserRole.VIEWER: 1,
        UserRole.EDITOR: 2,
        UserRole.MANAGER: 3,
        UserRole.ADMIN: 4,
        UserRole.SUPER_ADMIN: 5
    }
    
    user_level = role_hierarchy.get(UserRole(user.role), 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

def can_edit_user_role(current_user: UserResponse, target_role: UserRole) -> bool:
    """Check if current user can edit user with target role"""
    role_hierarchy = {
        UserRole.VIEWER: 1,
        UserRole.EDITOR: 2,
        UserRole.MANAGER: 3,
        UserRole.ADMIN: 4,
        UserRole.SUPER_ADMIN: 5
    }
    
    current_level = role_hierarchy.get(UserRole(current_user.role), 0)
    target_level = role_hierarchy.get(target_role, 0)
    
    return current_level > target_level

# Authentication Routes
@api_router.post("/auth/login")
async def login(login_request: LoginRequest):
    """User authentication"""
    try:
        # Find user by username
        user = await mongo_db.find_user_by_username(login_request.username)
        
        if not user or not verify_password(login_request.password, user['password_hash']):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        if not user.get('is_active', True):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account disabled")
        
        # Create token with different expiration based on remember_me
        expiration_hours = 24 * 7 if login_request.remember_me else JWT_EXPIRATION_HOURS
        access_token = create_access_token(
            user["id"], 
            user["username"], 
            user["role"], 
            user.get("company"),
            user.get("full_name"),
            expiration_hours
        )
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": user["id"],
            "action": "login",
            "resource": "auth",
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(**user).dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")

# User Management Routes
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: UserResponse = Depends(get_current_user)):
    """Get all users (filtered by role and company)"""
    try:
        # Role-based filtering
        if current_user.role in ['manager', 'admin']:
            # Manager and Admin only see users from their company
            users = await mongo_db.find_users_by_company(current_user.company or "")
        else:
            # Super Admin sees all users
            users = await mongo_db.find_all("users", {"is_active": True})
        
        return [UserResponse(**user) for user in users]
        
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch users")

@api_router.get("/users/filtered", response_model=List[UserResponse])
async def get_users_filtered(
    company: Optional[str] = None,
    department: Optional[str] = None, 
    ship: Optional[str] = None,
    sort_by: Optional[str] = "full_name",
    sort_order: Optional[str] = "asc",
    current_user: UserResponse = Depends(get_current_user)
):
    """Get users with filtering and sorting options"""
    try:
        # Check permissions
        if not has_permission(current_user, UserRole.MANAGER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Build filter query
        filter_query = {"is_active": True}
        
        # Apply role-based filtering first
        if current_user.role in ['manager', 'admin']:
            # Manager and Admin only see users from their company
            if current_user.company:
                filter_query["company"] = current_user.company
        
        # Apply additional filters
        if company:
            filter_query["company"] = company
        if department:
            filter_query["department"] = department
        if ship:
            filter_query["ship"] = ship
        
        # Get users from database
        users = await mongo_db.find_all("users", filter_query)
        
        # Sort users
        valid_sort_fields = ["full_name", "username", "company", "department", "role", "ship", "zalo", "gmail", "created_at"]
        if sort_by not in valid_sort_fields:
            sort_by = "full_name"
        
        reverse_order = sort_order.lower() == "desc"
        
        # Handle None values in sorting
        users_sorted = sorted(users, key=lambda x: (
            x.get(sort_by) is None,  # None values go to end
            str(x.get(sort_by, "")).lower() if x.get(sort_by) is not None else ""
        ), reverse=reverse_order)
        
        return [UserResponse(**user) for user in users_sorted]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching filtered users: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch filtered users")

@api_router.post("/users", response_model=UserResponse)
async def create_user(user_create: UserCreate, current_user: UserResponse = Depends(get_current_user)):
    """Create new user"""
    try:
        # Check permissions
        if not has_permission(current_user, UserRole.MANAGER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Check if user can create user with this role
        if not can_edit_user_role(current_user, user_create.role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create user with higher or equal role")
        
        # Check if username already exists
        existing_user = await mongo_db.find_user_by_username(user_create.username)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        
        # Check if email already exists (if provided)
        if user_create.email:
            existing_email = await mongo_db.find_user_by_email(user_create.email)
            if existing_email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        
        # Validate Zalo field (required)
        if not user_create.zalo or user_create.zalo.strip() == "":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Zalo field is required")
        
        # Create user data
        user_data = user_create.dict()
        user_data['id'] = str(uuid.uuid4())
        user_data['password_hash'] = hash_password(user_create.password)
        user_data['created_at'] = datetime.now(timezone.utc)
        user_data['permissions'] = {}
        
        # Remove plain password
        del user_data['password']
        
        # Save to MongoDB
        await mongo_db.create("users", user_data)
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "create_user",
            "resource": "users",
            "details": {"new_user_id": user_data['id']},
            "timestamp": datetime.now(timezone.utc)
        })
        
        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate, current_user: UserResponse = Depends(get_current_user)):
    """Update user"""
    try:
        # Check permissions
        if not has_permission(current_user, UserRole.MANAGER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Get existing user
        existing_user = await mongo_db.find_one("users", {"id": user_id})
        if not existing_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Check if current user can edit this user's role
        if not can_edit_user_role(current_user, UserRole(existing_user['role'])):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit user with higher or equal role")
        
        # Check if trying to update to a role they can't assign
        if user_update.role and not can_edit_user_role(current_user, user_update.role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot assign higher or equal role")
        
        # Prepare update data
        update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items() if v is not None}
        
        # Handle password update
        if 'password' in update_data:
            update_data['password_hash'] = hash_password(update_data['password'])
            del update_data['password']
        
        # Check email uniqueness if updating email
        if 'email' in update_data and update_data['email']:
            existing_email = await mongo_db.find_one("users", {"email": update_data['email'], "id": {"$ne": user_id}})
            if existing_email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        
        # Update user
        success = await mongo_db.update("users", {"id": user_id}, update_data)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Get updated user
        updated_user = await mongo_db.find_one("users", {"id": user_id})
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "update_user",
            "resource": "users",
            "details": {"updated_user_id": user_id},
            "timestamp": datetime.now(timezone.utc)
        })
        
        return UserResponse(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user")

@api_router.put("/users/{user_id}/self-edit")
async def self_edit_user(user_id: str, user_update: UserUpdate, current_user: UserResponse = Depends(get_current_user)):
    """Allow users to edit their own email and zalo (crew can only edit email/zalo)"""
    try:
        # Check if user is editing themselves
        if user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only edit your own profile")
        
        # Get existing user
        existing_user = await mongo_db.find_one("users", {"id": user_id})
        if not existing_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Define what fields each role can edit
        allowed_fields = set()
        if current_user.role == 'viewer':  # Crew role
            allowed_fields = {'email', 'zalo'}
        else:
            # Higher roles can edit more fields
            allowed_fields = {'email', 'zalo', 'full_name'}
        
        # Filter update data to only allowed fields
        update_data = {}
        for field, value in user_update.dict(exclude_unset=True).items():
            if field in allowed_fields and value is not None:
                update_data[field] = value
        
        # Handle password update (all users can change their own password)
        if user_update.password:
            update_data['password_hash'] = hash_password(user_update.password)
        
        # Check email uniqueness if updating email
        if 'email' in update_data and update_data['email']:
            existing_email = await mongo_db.find_one("users", {"email": update_data['email'], "id": {"$ne": user_id}})
            if existing_email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No allowed fields to update")
        
        # Update user
        success = await mongo_db.update("users", {"id": user_id}, update_data)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Get updated user
        updated_user = await mongo_db.find_one("users", {"id": user_id})
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "self_edit_user",
            "resource": "users",
            "details": {"updated_fields": list(update_data.keys())},
            "timestamp": datetime.now(timezone.utc)
        })
        
        return UserResponse(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in self-edit user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update profile")

@api_router.get("/users/{user_id}/editable-fields")
async def get_editable_fields(user_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Get list of fields the current user can edit for the specified user"""
    try:
        # Check if user is editing themselves
        if user_id == current_user.id:
            # Self-edit permissions
            if current_user.role == 'viewer':  # Crew role
                return {"editable_fields": ["email", "zalo", "password"]}
            else:
                return {"editable_fields": ["email", "zalo", "full_name", "password"]}
        else:
            # Check management permissions
            existing_user = await mongo_db.find_one("users", {"id": user_id})
            if not existing_user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            
            if not can_edit_user_role(current_user, UserRole(existing_user['role'])):
                return {"editable_fields": []}
            
            # Full edit permissions for managers/admins
            return {"editable_fields": ["username", "email", "full_name", "role", "department", "company", "ship", "zalo", "gmail", "is_active", "password"]}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting editable fields: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get editable fields")

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Delete user (soft delete by setting is_active=False)"""
    try:
        # Check permissions
        if not has_permission(current_user, UserRole.MANAGER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Get existing user
        existing_user = await mongo_db.find_one("users", {"id": user_id})
        if not existing_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Check if current user can delete this user
        if not can_edit_user_role(current_user, UserRole(existing_user['role'])):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete user with higher or equal role")
        
        # Soft delete (set is_active=False)
        success = await mongo_db.update("users", {"id": user_id}, {"is_active": False})
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "delete_user",
            "resource": "users",
            "details": {"deleted_user_id": user_id},
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete user")

# Company Management Routes
@api_router.get("/companies", response_model=List[CompanyResponse])
async def get_companies(current_user: UserResponse = Depends(get_current_user)):
    """Get all companies (filtered by role)"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        if current_user.role == UserRole.ADMIN:
            # Admin can only see their own company
            companies = await mongo_db.find_all("companies", {
                "$or": [
                    {"name_vn": current_user.company},
                    {"name_en": current_user.company}
                ]
            })
        else:
            # Super Admin can see all companies
            companies = await mongo_db.find_all("companies")
        
        return [CompanyResponse(**company) for company in companies]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching companies: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch companies")

@api_router.post("/companies", response_model=CompanyResponse)
async def create_company(company_data: CompanyCreate, current_user: UserResponse = Depends(get_current_user)):
    """Create new company"""
    try:
        if not has_permission(current_user, UserRole.SUPER_ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Super Admin can create companies")
        
        # Check if tax_id already exists
        existing_company = await mongo_db.find_company_by_tax_id(company_data.tax_id)
        if existing_company:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company with this tax ID already exists")
        
        # Create company data
        company_dict = company_data.dict()
        company_dict['id'] = str(uuid.uuid4())
        company_dict['created_at'] = datetime.now(timezone.utc)
        company_dict['created_by'] = current_user.id
        
        # Save to MongoDB
        await mongo_db.create("companies", company_dict)
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "create_company",
            "resource": "companies",
            "details": {"company_id": company_dict['id']},
            "timestamp": datetime.now(timezone.utc)
        })
        
        return CompanyResponse(**company_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating company: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create company")

@api_router.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company_by_id(company_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Get company by ID"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        company = await mongo_db.find_one("companies", {"id": company_id})
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        
        # Check if Admin can access this company
        if current_user.role == UserRole.ADMIN:
            if company.get('name_vn') != current_user.company and company.get('name_en') != current_user.company:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this company")
        
        return CompanyResponse(**company)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch company")

@api_router.put("/companies/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: str, company_update: CompanyUpdate, current_user: UserResponse = Depends(get_current_user)):
    """Update company"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Get existing company
        existing_company = await mongo_db.find_one("companies", {"id": company_id})
        if not existing_company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        
        # Check if Admin can edit this company
        if current_user.role == UserRole.ADMIN:
            if existing_company.get('name_vn') != current_user.company and existing_company.get('name_en') != current_user.company:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this company")
        
        # Prepare update data
        update_data = {k: v for k, v in company_update.dict(exclude_unset=True).items() if v is not None}
        
        # Check tax_id uniqueness if updating tax_id
        if 'tax_id' in update_data:
            existing_tax = await mongo_db.find_one("companies", {"tax_id": update_data['tax_id'], "id": {"$ne": company_id}})
            if existing_tax:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tax ID already exists")
        
        # Update company
        success = await mongo_db.update("companies", {"id": company_id}, update_data)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        
        # Get updated company
        updated_company = await mongo_db.find_one("companies", {"id": company_id})
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "update_company",
            "resource": "companies",
            "details": {"company_id": company_id},
            "timestamp": datetime.now(timezone.utc)
        })
        
        return CompanyResponse(**updated_company)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update company")

@api_router.delete("/companies/{company_id}")
async def delete_company(company_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Delete company"""
    try:
        if not has_permission(current_user, UserRole.SUPER_ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Super Admin can delete companies")
        
        # Check if company exists
        existing_company = await mongo_db.find_one("companies", {"id": company_id})
        if not existing_company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        
        # Delete company
        success = await mongo_db.delete("companies", {"id": company_id})
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "delete_company",
            "resource": "companies",
            "details": {"company_id": company_id},
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {"message": "Company deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete company")

# Google Drive Configuration Routes
@api_router.post("/gdrive/configure")
async def configure_google_drive(config: GoogleDriveConfig, current_user: UserResponse = Depends(get_current_user)):
    """Configure Google Drive integration"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Store configuration in MongoDB
        config_data = {
            "service_account_json": config.service_account_json,
            "folder_id": config.folder_id,
            "configured_by": current_user.id,
            "configured_at": datetime.now(timezone.utc)
        }
        
        # Remove existing config and insert new one
        await mongo_db.database.gdrive_config.delete_many({})
        await mongo_db.create("gdrive_config", config_data)
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "configure_gdrive",
            "resource": "gdrive",
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {"message": "Google Drive configured successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring Google Drive: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to configure Google Drive")

@api_router.get("/gdrive/status", response_model=GoogleDriveStatus)
async def get_google_drive_status(current_user: UserResponse = Depends(get_current_user)):
    """Get Google Drive status"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Check if configured
        config = await mongo_db.find_one("gdrive_config", {})
        configured = config is not None
        
        if configured:
            # Count documents in each collection
            local_files = (
                await mongo_db.count("users") +
                await mongo_db.count("companies") +
                await mongo_db.count("ships") +
                await mongo_db.count("certificates")
            )
            
            # Count files on Google Drive
            drive_files = 0
            try:
                gdrive_manager = GoogleDriveManager()
                
                # Configure based on auth method
                auth_method = config.get("auth_method", "service_account")
                configured_successfully = False
                
                if auth_method == "oauth":
                    # OAuth configuration
                    client_config = config.get("client_config")
                    oauth_credentials = config.get("oauth_credentials")
                    folder_id = config.get("folder_id")
                    
                    if client_config and oauth_credentials and folder_id:
                        configured_successfully = gdrive_manager.configure_oauth(client_config, oauth_credentials, folder_id)
                else:
                    # Service Account configuration (legacy)
                    service_account_json = config.get("service_account_json")
                    folder_id = config.get("folder_id")
                    
                    if service_account_json and folder_id:
                        configured_successfully = gdrive_manager.configure_service_account(service_account_json, folder_id)
                
                if configured_successfully:
                    drive_files_list = gdrive_manager.list_files()
                    drive_files = len(drive_files_list)
            except Exception as e:
                logger.warning(f"Could not count Google Drive files: {e}")
            
            return GoogleDriveStatus(
                configured=True,
                last_sync=config.get("last_sync"),
                local_files=local_files,
                drive_files=drive_files,
                folder_id=config.get("folder_id"),
                service_account_email=config.get("service_account_email")
            )
        else:
            return GoogleDriveStatus(configured=False)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Google Drive status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get Google Drive status")

@api_router.get("/gdrive/config")
async def get_google_drive_config(current_user: UserResponse = Depends(get_current_user)):
    """Get current Google Drive configuration (without sensitive data)"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        config = await mongo_db.find_one("gdrive_config", {})
        
        if config:
            # Get service account email based on auth method
            service_account_email = ""
            auth_method = config.get("auth_method", "service_account")
            
            if auth_method == "apps_script":
                # For Apps Script, use the stored service_account_email
                service_account_email = config.get("service_account_email", "")
            else:
                # For service account, parse from JSON
                try:
                    import json
                    sa_data = json.loads(config.get("service_account_json", "{}"))
                    service_account_email = sa_data.get("client_email", "")
                except:
                    pass
            
            return {
                "configured": True,
                "folder_id": config.get("folder_id", ""),
                "service_account_email": service_account_email,
                "auth_method": auth_method,
                "last_sync": config.get("last_sync")
            }
        else:
            return {
                "configured": False,
                "folder_id": "",
                "service_account_email": "",
                "last_sync": None
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Google Drive config: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get Google Drive config")

@api_router.post("/gdrive/test", response_model=GoogleDriveTestResponse)
async def test_google_drive_connection(config: GoogleDriveConfig, current_user: UserResponse = Depends(get_current_user)):
    """Test Google Drive connection with provided credentials"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        import json
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        # Clean up folder_id (remove any extra characters or duplicates)
        folder_id = config.folder_id.strip()
        if not folder_id:
            return GoogleDriveTestResponse(
                success=False,
                message="Folder ID cannot be empty"
            )
        
        # Check if folder_id looks valid (basic validation)
        if len(folder_id) < 20 or len(folder_id) > 100 or ' ' in folder_id:
            return GoogleDriveTestResponse(
                success=False,
                message=f"Folder ID format appears invalid. Got: '{folder_id}' (length: {len(folder_id)}). Please check your folder ID."
            )
        
        # Parse service account JSON
        try:
            service_account_info = json.loads(config.service_account_json)
            service_account_email = service_account_info.get('client_email', 'Unknown')
        except json.JSONDecodeError:
            return GoogleDriveTestResponse(
                success=False,
                message="Invalid Service Account JSON format"
            )
        
        # Create credentials
        scopes = ['https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=scopes)
        
        # Build Google Drive service
        service = build('drive', 'v3', credentials=credentials)
        
        # Test access to the specified folder
        try:
            folder_info = service.files().get(fileId=folder_id).execute()
            folder_name = folder_info.get('name', 'Unknown Folder')
            
            return GoogleDriveTestResponse(
                success=True,
                message=f"Successfully connected to Google Drive folder: {folder_name}",
                folder_name=folder_name,
                service_account_email=service_account_email
            )
        except Exception as folder_error:
            error_msg = str(folder_error)
            
            # Provide more specific error messages
            if "404" in error_msg or "not found" in error_msg.lower():
                return GoogleDriveTestResponse(
                    success=False,
                    message=f"Folder not found with ID '{folder_id}'. Please check: 1) Folder ID is correct, 2) Folder exists, 3) Service account has access to the folder."
                )
            elif "403" in error_msg or "forbidden" in error_msg.lower():
                return GoogleDriveTestResponse(
                    success=False,
                    message=f"Access denied to folder '{folder_id}'. Please share the folder with service account email: {service_account_email}"
                )
            else:
                return GoogleDriveTestResponse(
                    success=False,
                    message=f"Cannot access folder with ID '{folder_id}'. Error: {error_msg}"
                )
            
    except Exception as e:
        return GoogleDriveTestResponse(
            success=False,
            message=f"Connection test failed: {str(e)}"
        )

# Google Apps Script Proxy Models
class GoogleAppsScriptConfig(BaseModel):
    web_app_url: str
    folder_id: str

@api_router.post("/gdrive/configure-proxy")
async def configure_google_apps_script_proxy(config: GoogleAppsScriptConfig, current_user: UserResponse = Depends(get_current_user)):
    """Configure Google Drive using Apps Script proxy"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Test connection to Apps Script
        test_response = requests.post(config.web_app_url, 
            json={"action": "test_connection"},
            timeout=30
        )
        
        if test_response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to connect to Apps Script proxy. Status: {test_response.status_code}")
        
        # Check if response has content before parsing JSON
        if not test_response.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Apps Script returned empty response. Please check: 1) Apps Script is deployed, 2) URL is correct, 3) Script has proper doPost function"
            )
        
        # Check content type
        content_type = test_response.headers.get('content-type', '').lower()
        if 'application/json' not in content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Apps Script returned non-JSON response (Content-Type: {content_type}). Response: {test_response.text[:200]}"
            )
        
        try:
            result = test_response.json()
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Apps Script returned invalid JSON response: {str(e)}. Response: {test_response.text[:200]}"
            )
        
        if not result.get("success"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Apps Script test failed: {result.get('error', 'Unknown error')}")
        
        # Save configuration
        await mongo_db.update("gdrive_config", {}, {
            "auth_method": "apps_script",
            "web_app_url": config.web_app_url,
            "folder_id": config.folder_id,
            "service_account_email": result.get("service_account_email"),
            "configured_at": datetime.now(timezone.utc).isoformat()
        }, upsert=True)
        
        return GoogleDriveTestResponse(
            success=True,
            message="Google Apps Script proxy configured successfully",
            folder_name=result.get("folder_name"),
            service_account_email=result.get("service_account_email")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring Apps Script proxy: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to configure proxy: {str(e)}")

@api_router.post("/gdrive/sync-to-drive-proxy")
async def sync_to_drive_using_proxy(current_user: UserResponse = Depends(get_current_user)):
    """Sync data to Google Drive using Apps Script proxy"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Get Apps Script configuration
        config = await mongo_db.find_one("gdrive_config", {"auth_method": "apps_script"})
        if not config:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Apps Script proxy not configured")
        
        # Export data from MongoDB
        export_data = await mongo_db.export_to_json()
        
        # Prepare files for upload
        files_to_upload = []
        data_path = "/app/backend/data"
        
        for filename in os.listdir(data_path):
            if filename.endswith('.json'):
                file_path = os.path.join(data_path, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                files_to_upload.append({
                    "name": filename,
                    "content": content
                })
        
        # Send to Apps Script
        response = requests.post(config["web_app_url"], 
            json={
                "action": "sync_to_drive",
                "files": files_to_upload
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to sync via Apps Script proxy")
        
        result = response.json()
        if not result.get("success"):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Sync failed: {result.get('error', 'Unknown error')}")
        
        # Update last_sync timestamp
        await mongo_db.update("gdrive_config", {}, {
            "last_sync": datetime.now(timezone.utc).isoformat()
        })
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "sync_to_drive_proxy",
            "resource": "gdrive",
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {"message": f"Data synced successfully via Apps Script. {result.get('uploaded_files', 0)} files uploaded.", "success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing via Apps Script proxy: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to sync: {str(e)}")

# Google Drive OAuth Endpoints
@api_router.post("/gdrive/oauth/authorize", response_model=GoogleDriveOAuthResponse)
async def initiate_google_drive_oauth(config: GoogleDriveOAuthConfig, current_user: UserResponse = Depends(get_current_user)):
    """Initiate Google Drive OAuth 2.0 authorization flow"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Create client config
        client_config = {
            "web": {
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [config.redirect_uri]
            },
            "redirect_uri": config.redirect_uri
        }
        
        # Initialize Google Drive manager
        gdrive_manager = GoogleDriveManager()
        
        # Get authorization URL
        authorization_url, state = gdrive_manager.get_oauth_authorization_url(client_config)
        
        if not authorization_url:
            return GoogleDriveOAuthResponse(
                success=False,
                message="Failed to generate authorization URL"
            )
        
        # Store client config and folder_id for later use (in session or database)
        await mongo_db.update("gdrive_oauth_temp", {}, {
            "client_config": client_config,
            "folder_id": config.folder_id,
            "state": state,
            "user_id": current_user.id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }, upsert=True)
        
        return GoogleDriveOAuthResponse(
            success=True,
            message="Authorization URL generated successfully",
            authorization_url=authorization_url,
            state=state
        )
        
    except Exception as e:
        logger.error(f"Error initiating OAuth: {e}")
        return GoogleDriveOAuthResponse(
            success=False,
            message=f"Failed to initiate OAuth: {str(e)}"
        )

@api_router.post("/gdrive/oauth/callback", response_model=GoogleDriveOAuthResponse)
async def handle_google_drive_oauth_callback(request: GoogleDriveOAuthRequest, current_user: UserResponse = Depends(get_current_user)):
    """Handle Google Drive OAuth 2.0 callback and complete configuration"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Get temporary OAuth data
        oauth_temp = await mongo_db.find_one("gdrive_oauth_temp", {"state": request.state, "user_id": current_user.id})
        if not oauth_temp:
            return GoogleDriveOAuthResponse(
                success=False,
                message="Invalid state parameter or expired OAuth session"
            )
        
        # Construct authorization response URL
        client_config = oauth_temp.get("client_config")
        redirect_uri = client_config.get("redirect_uri")
        authorization_response = f"{redirect_uri}?code={request.authorization_code}&state={request.state}"
        
        # Initialize Google Drive manager
        gdrive_manager = GoogleDriveManager()
        
        # Handle OAuth callback
        oauth_credentials = gdrive_manager.handle_oauth_callback(authorization_response)
        
        if not oauth_credentials:
            return GoogleDriveOAuthResponse(
                success=False,
                message="Failed to exchange authorization code for tokens"
            )
        
        # Configure Google Drive with OAuth credentials
        folder_id = oauth_temp.get("folder_id")
        if not gdrive_manager.configure_oauth(client_config, oauth_credentials, folder_id):
            return GoogleDriveOAuthResponse(
                success=False,
                message="Failed to configure Google Drive with OAuth credentials"
            )
        
        # Save configuration to MongoDB
        await mongo_db.update("gdrive_config", {}, {
            "auth_method": "oauth",
            "client_config": client_config,
            "oauth_credentials": oauth_credentials,
            "folder_id": folder_id,
            "service_account_email": oauth_credentials.get("client_id"),  # Use client_id as identifier
            "configured_at": datetime.now(timezone.utc).isoformat()
        }, upsert=True)
        
        # Clean up temporary data
        await mongo_db.delete("gdrive_oauth_temp", {"state": request.state})
        
        return GoogleDriveOAuthResponse(
            success=True,
            message="Google Drive configured successfully with OAuth 2.0"
        )
        
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        return GoogleDriveOAuthResponse(
            success=False,
            message=f"Failed to handle OAuth callback: {str(e)}"
        )

@api_router.post("/gdrive/sync-to-drive")
async def sync_to_drive(current_user: UserResponse = Depends(get_current_user)):
    """Sync data to Google Drive"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Get Google Drive configuration from MongoDB
        config = await mongo_db.find_one("gdrive_config", {})
        if not config:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google Drive not configured")
        
        # Initialize Google Drive manager with configuration
        gdrive_manager = GoogleDriveManager()
        
        # Configure based on auth method
        auth_method = config.get("auth_method", "service_account")
        
        if auth_method == "oauth":
            # OAuth configuration
            client_config = config.get("client_config")
            oauth_credentials = config.get("oauth_credentials")
            folder_id = config.get("folder_id")
            
            if not gdrive_manager.configure_oauth(client_config, oauth_credentials, folder_id):
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initialize Google Drive OAuth connection")
        else:
            # Service Account configuration (legacy)
            service_account_json = config.get("service_account_json")
            folder_id = config.get("folder_id")
            
            if not gdrive_manager.configure_service_account(service_account_json, folder_id):
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initialize Google Drive Service Account connection")
        
        # Export data from MongoDB to JSON files
        export_data = await mongo_db.export_to_json()
        
        # Actually sync to Google Drive using the manager
        sync_success = gdrive_manager.sync_to_drive()
        
        if not sync_success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to sync data to Google Drive")
        
        # Update last_sync timestamp
        await mongo_db.update("gdrive_config", {}, {
            "last_sync": datetime.now(timezone.utc).isoformat()
        })
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "sync_to_drive",
            "resource": "gdrive",
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {"message": "Data synced to Google Drive successfully", "success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing to Google Drive: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to sync to Google Drive: {str(e)}")

@api_router.post("/gdrive/sync-from-drive")
async def sync_from_drive(current_user: UserResponse = Depends(get_current_user)):
    """Sync data from Google Drive""" 
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Get Google Drive configuration from MongoDB
        config = await mongo_db.find_one("gdrive_config", {})
        if not config:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google Drive not configured")
        
        # Initialize Google Drive manager with configuration
        gdrive_manager = GoogleDriveManager()
        
        # Configure based on auth method
        auth_method = config.get("auth_method", "service_account")
        
        if auth_method == "oauth":
            # OAuth configuration
            client_config = config.get("client_config")
            oauth_credentials = config.get("oauth_credentials")
            folder_id = config.get("folder_id")
            
            if not gdrive_manager.configure_oauth(client_config, oauth_credentials, folder_id):
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initialize Google Drive OAuth connection")
        else:
            # Service Account configuration (legacy)
            service_account_json = config.get("service_account_json")
            folder_id = config.get("folder_id")
            
            if not gdrive_manager.configure_service_account(service_account_json, folder_id):
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initialize Google Drive Service Account connection")
        
        # Actually sync from Google Drive using the manager
        sync_success = gdrive_manager.sync_from_drive()
        
        if not sync_success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to sync data from Google Drive")
        
        # Import data from downloaded JSON files to MongoDB
        import_results = await mongo_db.import_from_json()
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "sync_from_drive",
            "resource": "gdrive",
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {
            "message": "Data synced from Google Drive successfully", 
            "success": True,
            "import_results": import_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing from Google Drive: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to sync from Google Drive: {str(e)}")

# Company Google Drive Configuration Routes
@api_router.get("/companies/{company_id}/gdrive/config")
async def get_company_gdrive_config(company_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Get company-specific Google Drive configuration"""
    try:
        # Check if user can access this company's Google Drive config
        if not has_permission(current_user, UserRole.ADMIN):
            # For non-admin users, check if they belong to this company
            company = await mongo_db.find_one("companies", {"id": company_id})
            if not company:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
            
            if current_user.role != 'super_admin' and current_user.company not in [company.get('name_vn'), company.get('name_en')]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access other company's configuration")
        
        # Get company
        company = await mongo_db.find_one("companies", {"id": company_id})
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        
        gdrive_config = company.get('gdrive_config') or {}
        
        # Return configuration with safe information (hide sensitive data)
        config_response = {
            "configured": bool(gdrive_config.get('configured', False)),
            "auth_method": gdrive_config.get('auth_method', 'service_account'),
            "folder_id": gdrive_config.get('folder_id', ''),
            "service_account_email": gdrive_config.get('service_account_email', ''),
            "last_sync": gdrive_config.get('last_sync')
        }
        
        return config_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company Google Drive config: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch Google Drive configuration")

@api_router.get("/companies/{company_id}/gdrive/status")
async def get_company_gdrive_status(company_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Get company-specific Google Drive status"""
    try:
        # Check permissions
        if not has_permission(current_user, UserRole.ADMIN):
            company = await mongo_db.find_one("companies", {"id": company_id})
            if not company:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
            
            if current_user.role != 'super_admin' and current_user.company not in [company.get('name_vn'), company.get('name_en')]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access other company's status")
        
        # Get company
        company = await mongo_db.find_one("companies", {"id": company_id})
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        
        gdrive_config = company.get('gdrive_config') or {}
        
        # Initialize status response
        status_response = {
            "configured": bool(gdrive_config.get('configured', False)),
            "auth_method": gdrive_config.get('auth_method', 'service_account'),
            "last_sync": gdrive_config.get('last_sync'),
            "local_files": 0,
            "drive_files": 0,
            "folder_id": gdrive_config.get('folder_id'),
            "service_account_email": gdrive_config.get('service_account_email')
        }
        
        # Count local files for this company (simplified)
        local_files_count = 0
        
        # If configured, try to get drive files count
        if gdrive_config.get('configured') and gdrive_config.get('folder_id'):
            try:
                auth_method = gdrive_config.get("auth_method", "service_account")
                gdrive_manager = GoogleDriveManager()
                
                if auth_method == "apps_script":
                    # For Apps Script, we can't easily count files without making a request
                    status_response["drive_files"] = "N/A"
                elif auth_method == "oauth":
                    client_config = gdrive_config.get("client_config")
                    oauth_credentials = gdrive_config.get("oauth_credentials")
                    folder_id = gdrive_config.get("folder_id")
                    
                    if gdrive_manager.configure_oauth(client_config, oauth_credentials, folder_id):
                        drive_files_list = gdrive_manager.list_files()
                        status_response["drive_files"] = len(drive_files_list)
                else:
                    # Service Account
                    service_account_json = gdrive_config.get("service_account_json")
                    folder_id = gdrive_config.get("folder_id")
                    
                    if gdrive_manager.configure_service_account(service_account_json, folder_id):
                        drive_files_list = gdrive_manager.list_files()
                        status_response["drive_files"] = len(drive_files_list)
                        
            except Exception as e:
                logger.warning(f"Could not get drive files count for company {company_id}: {e}")
                status_response["drive_files"] = "Error"
        
        return status_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company Google Drive status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch Google Drive status")

@api_router.post("/companies/{company_id}/gdrive/configure-proxy")
async def configure_company_gdrive_proxy(company_id: str, config: GoogleDriveAppsScriptConfig, current_user: UserResponse = Depends(get_current_user)):
    """Configure company-specific Google Drive using Apps Script proxy"""
    try:
        # Check permissions
        if not has_permission(current_user, UserRole.ADMIN):
            company = await mongo_db.find_one("companies", {"id": company_id})
            if not company:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
            
            if current_user.role != 'super_admin' and current_user.company not in [company.get('name_vn'), company.get('name_en')]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot configure other company's Google Drive")
        
        # Get company
        company = await mongo_db.find_one("companies", {"id": company_id})
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        
        # Test Apps Script connection first
        try:
            response = requests.post(config.web_app_url, 
                json={"action": "test_connection", "folder_id": config.folder_id},
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                return GoogleDriveProxyResponse(
                    success=False,
                    message=f"Apps Script returned HTTP {response.status_code}. Please check your deployment."
                )
            
            # Check if response is JSON
            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' not in content_type and 'text/plain' not in content_type:
                return GoogleDriveProxyResponse(
                    success=False,
                    message=f"Apps Script returned invalid content type: {content_type}. Expected JSON response."
                )
            
            # Try to parse response
            try:
                result = response.json()
            except json.JSONDecodeError:
                response_preview = response.text[:200] + "..." if len(response.text) > 200 else response.text
                return GoogleDriveProxyResponse(
                    success=False,
                    message=f"Apps Script returned invalid JSON. Response preview: {response_preview}"
                )
            
            if not result.get('success'):
                return GoogleDriveProxyResponse(
                    success=False,
                    message=result.get('message', 'Apps Script test failed')
                )
                
        except requests.exceptions.RequestException as e:
            return GoogleDriveProxyResponse(
                success=False,
                message=f"Cannot connect to Apps Script URL: {str(e)}"
            )
        except Exception as e:
            return GoogleDriveProxyResponse(
                success=False,
                message=f"Apps Script test error: {str(e)}"
            )
        
        # Save configuration to company
        gdrive_config = {
            "auth_method": "apps_script",
            "web_app_url": config.web_app_url,
            "folder_id": config.folder_id,
            "configured": True,
            "service_account_email": current_user.email,  # Store configuring user's email
            "configured_at": datetime.now(timezone.utc).isoformat(),
            "configured_by": current_user.id
        }
        
        # Update company with Google Drive config
        update_data = {"gdrive_config": gdrive_config}
        await mongo_db.update("companies", {"id": company_id}, update_data)
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "configure_company_gdrive_proxy",
            "resource": f"company_gdrive:{company_id}",
            "timestamp": datetime.now(timezone.utc)
        })
        
        return GoogleDriveProxyResponse(
            success=True,
            message="Company Google Drive Apps Script proxy configured successfully",
            folder_name=result.get('folder_name', 'Google Drive Folder')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring company Google Drive proxy: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to configure Google Drive proxy: {str(e)}")

@api_router.post("/companies/{company_id}/gdrive/configure")
async def configure_company_gdrive_service_account(company_id: str, config: GoogleDriveConfig, current_user: UserResponse = Depends(get_current_user)):
    """Configure company-specific Google Drive using Service Account"""
    try:
        # Check permissions
        if not has_permission(current_user, UserRole.ADMIN):
            company = await mongo_db.find_one("companies", {"id": company_id})
            if not company:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
            
            if current_user.role != 'super_admin' and current_user.company not in [company.get('name_vn'), company.get('name_en')]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot configure other company's Google Drive")
        
        # Get company
        company = await mongo_db.find_one("companies", {"id": company_id})
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        
        # Save configuration to company
        gdrive_config = {
            "auth_method": "service_account",
            "service_account_json": config.service_account_json,
            "folder_id": config.folder_id,
            "configured": True,
            "configured_at": datetime.now(timezone.utc).isoformat(),
            "configured_by": current_user.id
        }
        
        # Extract service account email for display
        try:
            service_account_data = json.loads(config.service_account_json)
            gdrive_config["service_account_email"] = service_account_data.get("client_email", "")
        except:
            pass
        
        # Update company with Google Drive config
        update_data = {"gdrive_config": gdrive_config}
        await mongo_db.update("companies", {"id": company_id}, update_data)
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "configure_company_gdrive",
            "resource": f"company_gdrive:{company_id}",
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {"success": True, "message": "Company Google Drive configured successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring company Google Drive: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to configure Google Drive: {str(e)}")

@api_router.post("/companies/{company_id}/gdrive/oauth/authorize", response_model=GoogleDriveOAuthResponse)
async def company_gdrive_oauth_authorize(company_id: str, config: GoogleDriveOAuthConfig, current_user: UserResponse = Depends(get_current_user)):
    """Initiate company-specific Google Drive OAuth 2.0 authorization"""
    try:
        # Check permissions
        if not has_permission(current_user, UserRole.ADMIN):
            company = await mongo_db.find_one("companies", {"id": company_id})
            if not company:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
            
            if current_user.role != 'super_admin' and current_user.company not in [company.get('name_vn'), company.get('name_en')]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot configure other company's Google Drive")
        
        # Get company
        company = await mongo_db.find_one("companies", {"id": company_id})
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        
        # Prepare OAuth configuration
        client_config = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "redirect_uri": config.redirect_uri
        }
        
        # Initialize Google Drive manager
        gdrive_manager = GoogleDriveManager()
        
        # Get authorization URL
        authorization_url, state = gdrive_manager.get_oauth_authorization_url(client_config)
        
        if not authorization_url:
            return GoogleDriveOAuthResponse(
                success=False,
                message="Failed to generate authorization URL"
            )
        
        # Store client config and folder_id for later use (company-specific)
        await mongo_db.update(f"company_gdrive_oauth_temp_{company_id}", {}, {
            "client_config": client_config,
            "folder_id": config.folder_id,
            "state": state,
            "user_id": current_user.id,
            "company_id": company_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }, upsert=True)
        
        return GoogleDriveOAuthResponse(
            success=True,
            message="Authorization URL generated successfully",
            authorization_url=authorization_url,
            state=state
        )
        
    except Exception as e:
        logger.error(f"Error initiating company OAuth: {e}")
        return GoogleDriveOAuthResponse(
            success=False,
            message=f"Failed to initiate OAuth: {str(e)}"
        )

@api_router.post("/companies/{company_id}/gdrive/sync-to-drive-proxy")
async def sync_company_to_drive_proxy(company_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Sync company data to Google Drive using Apps Script proxy"""
    try:
        # Check permissions
        if not has_permission(current_user, UserRole.ADMIN):
            company = await mongo_db.find_one("companies", {"id": company_id})
            if not company:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
            
            if current_user.role != 'super_admin' and current_user.company not in [company.get('name_vn'), company.get('name_en')]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot sync other company's data")
        
        # Get company with Google Drive configuration
        company = await mongo_db.find_one("companies", {"id": company_id})
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        
        gdrive_config = company.get('gdrive_config', {})
        if gdrive_config.get("auth_method") != "apps_script":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company Google Drive not configured with Apps Script")
        
        web_app_url = gdrive_config.get("web_app_url")
        folder_id = gdrive_config.get("folder_id")
        
        if not web_app_url or not folder_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company Google Drive configuration missing")
        
        # Get company-specific data for sync
        company_data = {
            "company_info": company,
            "users": await mongo_db.find_all("users", {"company": {"$in": [company.get('name_vn'), company.get('name_en')]}}),
            "ships": await mongo_db.find_all("ships", {"company_id": company_id}) if await mongo_db.find_one("ships", {"company_id": company_id}) else [],
            "certificates": []  # Get company-specific certificates if needed
        }
        
        # Sync data to Google Drive via Apps Script
        files_uploaded = []
        
        for data_type, data in company_data.items():
            if not data:
                continue
                
            try:
                payload = {
                    "action": "sync_to_drive",
                    "folder_id": folder_id,
                    "file_name": f"{company.get('name_en', 'company')}_{data_type}.json",
                    "file_content": json.dumps(data, indent=2, default=str)
                }
                
                response = requests.post(web_app_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        files_uploaded.append({
                            "file": f"{company.get('name_en', 'company')}_{data_type}.json",
                            "status": "uploaded",
                            "file_id": result.get('file_id')
                        })
                    else:
                        files_uploaded.append({
                            "file": f"{company.get('name_en', 'company')}_{data_type}.json",
                            "status": "failed",
                            "error": result.get('message')
                        })
                else:
                    files_uploaded.append({
                        "file": f"{company.get('name_en', 'company')}_{data_type}.json",
                        "status": "failed",
                        "error": f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                files_uploaded.append({
                    "file": f"{company.get('name_en', 'company')}_{data_type}.json",
                    "status": "failed",
                    "error": str(e)
                })
        
        # Update last sync timestamp
        gdrive_config["last_sync"] = datetime.now(timezone.utc).isoformat()
        await mongo_db.update("companies", {"id": company_id}, {"gdrive_config": gdrive_config})
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "sync_company_to_drive_proxy",
            "resource": f"company_gdrive:{company_id}",
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {
            "message": f"Company data synced to Google Drive: {len([f for f in files_uploaded if f['status'] == 'uploaded'])} files uploaded successfully",
            "success": True,
            "files": files_uploaded
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing company to Google Drive: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to sync to Google Drive: {str(e)}")

# Ships Management Routes
@api_router.get("/ships", response_model=List[ShipResponse])
async def get_ships(current_user: UserResponse = Depends(get_current_user)):
    """Get all ships"""
    try:
        if not has_permission(current_user, UserRole.VIEWER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        ships = await mongo_db.find_all("ships")
        return [ShipResponse(**ship) for ship in ships]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ships: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch ships")

@api_router.post("/ships", response_model=ShipResponse)
async def create_ship(ship_data: ShipCreate, current_user: UserResponse = Depends(get_current_user)):
    """Create new ship"""
    try:
        if not has_permission(current_user, UserRole.EDITOR):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Check if IMO already exists (if provided)
        if ship_data.imo:
            existing_ship = await mongo_db.find_ship_by_imo(ship_data.imo)
            if existing_ship:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ship with this IMO already exists")
        
        # Create ship data
        ship_dict = ship_data.dict()
        ship_dict['id'] = str(uuid.uuid4())
        ship_dict['created_at'] = datetime.now(timezone.utc)
        
        # Handle empty fields - convert empty strings to None and remove None values for unique constraints
        if not ship_dict.get('imo') or ship_dict.get('imo', '').strip() == '':
            # Remove IMO field entirely if empty to avoid unique constraint issues
            ship_dict.pop('imo', None)
        
        # Convert empty strings to None for optional fields
        for field in ['gross_tonnage', 'year_built']:
            if ship_dict.get(field) == '' or ship_dict.get(field) == 0:
                ship_dict[field] = None
        
        # Save to MongoDB
        await mongo_db.create("ships", ship_dict)
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "create_ship",
            "resource": "ships",
            "details": {"ship_id": ship_dict['id']},
            "timestamp": datetime.now(timezone.utc)
        })
        
        return ShipResponse(**ship_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ship: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create ship")

@api_router.get("/ships/{ship_id}", response_model=ShipResponse)
async def get_ship(ship_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Get ship by ID"""
    try:
        if not has_permission(current_user, UserRole.VIEWER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        ship = await mongo_db.find_one("ships", {"id": ship_id})
        if not ship:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")
        
        return ShipResponse(**ship)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ship: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch ship")

@api_router.put("/ships/{ship_id}", response_model=ShipResponse)
async def update_ship(ship_id: str, ship_update: ShipUpdate, current_user: UserResponse = Depends(get_current_user)):
    """Update ship"""
    try:
        if not has_permission(current_user, UserRole.EDITOR):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Get existing ship
        existing_ship = await mongo_db.find_one("ships", {"id": ship_id})
        if not existing_ship:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")
        
        # Prepare update data
        update_data = {k: v for k, v in ship_update.dict(exclude_unset=True).items() if v is not None}
        
        # Check IMO uniqueness if updating IMO
        if 'imo' in update_data and update_data['imo']:
            existing_imo = await mongo_db.find_one("ships", {"imo": update_data['imo'], "id": {"$ne": ship_id}})
            if existing_imo:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="IMO already exists")
        
        # Update ship
        success = await mongo_db.update("ships", {"id": ship_id}, update_data)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")
        
        # Get updated ship
        updated_ship = await mongo_db.find_one("ships", {"id": ship_id})
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "update_ship",
            "resource": "ships",
            "details": {"ship_id": ship_id},
            "timestamp": datetime.now(timezone.utc)
        })
        
        return ShipResponse(**updated_ship)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ship: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update ship")

@api_router.delete("/ships/{ship_id}")
async def delete_ship(ship_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Delete ship"""
    try:
        if not has_permission(current_user, UserRole.MANAGER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Check if ship exists
        existing_ship = await mongo_db.find_one("ships", {"id": ship_id})
        if not existing_ship:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")
        
        # Delete ship
        success = await mongo_db.delete("ships", {"id": ship_id})
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "delete_ship",
            "resource": "ships",
            "details": {"ship_id": ship_id},
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {"message": "Ship deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ship: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete ship")

# Certificates Management Routes
@api_router.get("/certificates", response_model=List[CertificateResponse])
async def get_certificates(current_user: UserResponse = Depends(get_current_user)):
    """Get all certificates"""
    try:
        if not has_permission(current_user, UserRole.VIEWER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        certificates = await mongo_db.find_all("certificates")
        
        # Transform certificates to match the expected schema
        transformed_certificates = []
        for cert in certificates:
            # Map old field names to new ones for backward compatibility
            transformed_cert = {
                'id': cert.get('id'),
                'ship_id': cert.get('ship_id'),
                'type': cert.get('cert_name', cert.get('type', 'Unknown')),  # cert_name -> type
                'issuer': cert.get('cert_no', cert.get('issuer', 'Unknown')),  # cert_no -> issuer (temporary mapping)
                'issue_date': cert.get('issue_date'),
                'expiry_date': cert.get('valid_date', cert.get('expiry_date')),  # valid_date -> expiry_date
                'status': cert.get('status', 'valid'),
                'created_at': cert.get('created_at')
            }
            transformed_certificates.append(CertificateResponse(**transformed_cert))
        
        return transformed_certificates
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching certificates: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch certificates")

@api_router.post("/certificates", response_model=CertificateResponse)
async def create_certificate(cert_data: CertificateCreate, current_user: UserResponse = Depends(get_current_user)):
    """Create new certificate (metadata only, without file upload)"""
    try:
        if not has_permission(current_user, UserRole.EDITOR):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Verify ship exists
        ship = await mongo_db.find_one("ships", {"id": cert_data.ship_id})
        if not ship:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ship not found")
        
        # Create certificate data
        cert_dict = cert_data.dict()
        cert_dict['id'] = str(uuid.uuid4())
        cert_dict['created_at'] = datetime.now(timezone.utc)
        
        # Save to MongoDB
        await mongo_db.create("certificates", cert_dict)
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "create_certificate",
            "resource": "certificates",
            "details": {"certificate_id": cert_dict['id'], "ship_id": cert_data.ship_id},
            "timestamp": datetime.now(timezone.utc)
        })
        
        return CertificateResponse(**cert_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating certificate: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create certificate")

@api_router.get("/ships/{ship_id}/certificates", response_model=List[CertificateResponse])
async def get_ship_certificates(ship_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Get all certificates for a specific ship"""
    try:
        if not has_permission(current_user, UserRole.VIEWER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Verify ship exists
        ship = await mongo_db.find_one("ships", {"id": ship_id})
        if not ship:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")
        
        certificates = await mongo_db.find_certificates_by_ship(ship_id)
        return [CertificateResponse(**cert) for cert in certificates]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ship certificates: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch ship certificates")

# Helper Functions for AI Document Processing

async def analyze_document_with_ai(file_content: bytes, filename: str, content_type: str, ai_config: dict) -> dict:
    """Analyze document using configured AI to extract information and classify"""
    try:
        # Convert file content to base64 for AI analysis
        import base64
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Create AI analysis prompt
        analysis_prompt = f"""
Analyze this document ({filename}) and extract the following information:

1. DOCUMENT CLASSIFICATION - Classify into one of these categories:
   - certificates: Certificates issued by Classification Society, Flags, Insurance
   - test_reports: Test/maintenance reports for lifesaving, firefighting, radio equipment
   - survey_reports: Survey reports issued by Classification Society
   - drawings_manuals: DWG files, technical drawings, manuals
   - other_documents: Documents not fitting above categories

2. SHIP INFORMATION:
   - ship_name: Name of the ship mentioned in the document

3. CERTIFICATE INFORMATION (if category is 'certificates'):
   - cert_name: Full certificate name
   - cert_type: Type (Interim, Provisional, Short term, Full Term)
   - cert_no: Certificate number
   - issue_date: Issue date (ISO format YYYY-MM-DD)
   - valid_date: Valid until date (ISO format YYYY-MM-DD)
   - last_endorse: Last endorsement date (ISO format YYYY-MM-DD, if available)
   - next_survey: Next survey date (ISO format YYYY-MM-DD, if available)
   - issued_by: Issuing authority/organization

4. SURVEY STATUS INFORMATION (if relevant):
   - certificate_type: CLASS, STATUTORY, AUDITS, Bottom Surveys
   - survey_type: Annual, Intermediate, Renewal, Change of RO, Approval, Initial Audit
   - issuance_date: When certificate was issued
   - expiration_date: When certificate expires
   - renewal_range_start: Renewal range start date
   - renewal_range_end: Renewal range end date
   - due_dates: Any due dates mentioned (as array)

Return response as JSON format. If information is not found, return null for that field.
Mark any uncertain extractions in a 'confidence' field (high/medium/low).
"""

        # Use Emergent LLM key for analysis
        if EMERGENT_LLM_KEY:
            try:
                llm_chat = LlmChat(
                    api_key=EMERGENT_LLM_KEY,
                    session_id=f"multi_doc_analysis_{uuid.uuid4()}",
                    system_message="You are an expert maritime document analyzer. Classify and extract information from ship documents accurately."
                )
                
                # Create temporary file for analysis
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as temp_file:
                    temp_file.write(file_content)
                    temp_file_path = temp_file.name
                
                try:
                    # Create file content for analysis
                    file_obj = FileContentWithMimeType(
                        mime_type=content_type or "application/pdf",
                        file_path=temp_file_path
                    )
                    
                    response = await llm_chat.with_model("google", "gemini-2.0-flash-exp").send_message(
                        UserMessage(text=analysis_prompt, file_contents=[file_obj])
                    )
                    
                    # Parse AI response as JSON
                    import json
                    analysis_result = json.loads(response)
                    return analysis_result
                    
                finally:
                    # Clean up temporary file
                    import os
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                
            except Exception as e:
                logger.error(f"Emergent LLM analysis failed: {e}")
                # Return basic classification based on filename
                return classify_by_filename(filename)
        
        else:
            # Fallback to filename-based classification
            return classify_by_filename(filename)
            
    except Exception as e:
        logger.error(f"AI document analysis failed: {e}")
        return classify_by_filename(filename)

def classify_by_filename(filename: str) -> dict:
    """Fallback classification based on filename"""
    filename_lower = filename.lower()
    
    # Basic classification rules
    if any(ext in filename_lower for ext in ['.dwg', 'drawing', 'manual', 'handbook']):
        category = "drawings_manuals"
    elif any(term in filename_lower for term in ['test', 'maintenance', 'inspection', 'check']):
        category = "test_reports"
    elif any(term in filename_lower for term in ['survey', 'audit', 'examination']):
        category = "survey_reports"
    elif any(term in filename_lower for term in ['certificate', 'cert', 'license', 'permit']):
        category = "certificates"
    else:
        category = "other_documents"
    
    return {
        "category": category,
        "ship_name": "Unknown_Ship",
        "confidence": "low",
        "cert_name": None,
        "cert_type": None,
        "cert_no": None,
        "issue_date": None,
        "valid_date": None,
        "issued_by": None
    }

async def create_ship_folder_structure(gdrive_config: dict, ship_name: str) -> dict:
    """Create folder structure: Ship Name -> 5 category subfolders"""
    try:
        auth_method = gdrive_config.get("auth_method", "service_account")
        
        if auth_method == "apps_script":
            web_app_url = gdrive_config.get("web_app_url")
            folder_id = gdrive_config.get("folder_id")
            
            if not web_app_url or not folder_id:
                raise Exception("Apps Script configuration incomplete")
            
            # Create main ship folder
            ship_folder_payload = {
                "action": "create_folder_structure",
                "parent_folder_id": folder_id,
                "folder_path": ship_name
            }
            
            response = requests.post(web_app_url, json=ship_folder_payload, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Failed to create ship folder: HTTP {response.status_code}")
            
            result = response.json()
            if not result.get('success'):
                raise Exception(f"Ship folder creation failed: {result.get('message')}")
            
            ship_folder_id = result.get('folder_id')
            
            # Create 5 category subfolders
            categories = [
                "Certificates",
                "Test Reports", 
                "Survey Reports",
                "Drawings & Manuals",
                "Other Documents"
            ]
            
            subfolder_ids = {}
            for category in categories:
                subfolder_payload = {
                    "action": "create_folder_structure",
                    "parent_folder_id": ship_folder_id,
                    "folder_path": category
                }
                
                subfolder_response = requests.post(web_app_url, json=subfolder_payload, timeout=30)
                
                if subfolder_response.status_code == 200:
                    subfolder_result = subfolder_response.json()
                    if subfolder_result.get('success'):
                        subfolder_ids[category] = subfolder_result.get('folder_id')
            
            return {
                "ship_folder_id": ship_folder_id,
                "subfolder_ids": subfolder_ids
            }
        
        else:
            raise Exception("Only Apps Script method supported for folder creation")
            
    except Exception as e:
        logger.error(f"Folder structure creation failed: {e}")
        raise

async def upload_file_to_category_folder(gdrive_config: dict, file_content: bytes, filename: str, ship_name: str, category: str, folder_structure: dict = None) -> dict:
    """Upload file to appropriate category subfolder"""
    try:
        auth_method = gdrive_config.get("auth_method", "service_account")
        
        if auth_method == "apps_script":
            web_app_url = gdrive_config.get("web_app_url")
            
            # Map category to folder name
            category_folders = {
                "certificates": "Certificates",
                "test_reports": "Test Reports",
                "survey_reports": "Survey Reports", 
                "drawings_manuals": "Drawings & Manuals",
                "other_documents": "Other Documents"
            }
            
            folder_name = category_folders.get(category, "Other Documents")
            
            # Use provided folder_structure or create new one
            if not folder_structure:
                folder_structure = await create_ship_folder_structure(gdrive_config, ship_name)
            
            target_folder_id = folder_structure["subfolder_ids"].get(folder_name)
            
            if not target_folder_id:
                # Debug info
                available_folders = list(folder_structure["subfolder_ids"].keys())
                raise Exception(f"Target folder not found for category: {category} -> {folder_name}. Available folders: {available_folders}")
            
            # Upload file
            import base64
            file_content_base64 = base64.b64encode(file_content).decode('utf-8')
            
            upload_payload = {
                "action": "upload_file",
                "folder_id": target_folder_id,
                "file_name": filename,
                "file_content": file_content_base64,
                "mime_type": "application/octet-stream"
            }
            
            upload_response = requests.post(web_app_url, json=upload_payload, timeout=60)
            
            if upload_response.status_code != 200:
                raise Exception(f"File upload failed: HTTP {upload_response.status_code}")
            
            upload_result = upload_response.json()
            if not upload_result.get('success'):
                raise Exception(f"File upload failed: {upload_result.get('message')}")
            
            return {
                "file_id": upload_result.get('file_id'),
                "folder_path": f"{ship_name}/{folder_name}"
            }
        
        else:
            raise Exception("Only Apps Script method supported for file upload")
            
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise

async def create_certificate_from_analysis(analysis_result: dict, current_user: UserResponse, filename: str, file_size: int, google_drive_file_id: str) -> dict:
    """Create certificate record from AI analysis results"""
    try:
        # Find or create ship based on ship_name
        ship_name = analysis_result.get("ship_name", "Unknown_Ship")
        ship = None
        
        # Try to find existing ship by name
        if ship_name != "Unknown_Ship":
            ship = await mongo_db.find_one("ships", {"name": {"$regex": ship_name, "$options": "i"}})
        
        # If no ship found, create a basic ship record
        if not ship:
            ship_data = {
                "id": str(uuid.uuid4()),
                "name": ship_name,
                "company": current_user.company,
                "created_at": datetime.now(timezone.utc)
            }
            await mongo_db.create("ships", ship_data)
            ship = ship_data
        
        # Create certificate record
        cert_dict = {
            'id': str(uuid.uuid4()),
            'ship_id': ship['id'],
            'cert_name': analysis_result.get('cert_name') or f'Certificate from {filename}',
            'cert_type': analysis_result.get('cert_type'),
            'cert_no': analysis_result.get('cert_no') or f'AUTO-{int(datetime.now().timestamp())}',
            'issue_date': parse_date_string(analysis_result.get('issue_date')) or datetime.now(timezone.utc),
            'valid_date': parse_date_string(analysis_result.get('valid_date')) or datetime.now(timezone.utc) + timedelta(days=365),
            'last_endorse': parse_date_string(analysis_result.get('last_endorse')),
            'next_survey': parse_date_string(analysis_result.get('next_survey')),
            'issued_by': analysis_result.get('issued_by'),
            'category': 'certificates',
            'sensitivity_level': 'internal',
            'created_at': datetime.now(timezone.utc),
            'file_uploaded': True,
            'google_drive_file_id': google_drive_file_id,
            'file_name': filename,
            'file_size': file_size,
            'ship_name': ship_name
        }
        
        # Save to MongoDB
        await mongo_db.create("certificates", cert_dict)
        
        return cert_dict
        
    except Exception as e:
        logger.error(f"Certificate creation from analysis failed: {e}")
        raise

async def update_ship_survey_status(analysis_result: dict, current_user: UserResponse) -> None:
    """Update ship survey status from analysis results"""
    try:
        survey_info = analysis_result.get("survey_info", {})
        if not survey_info:
            return
        
        # Find ship
        ship_name = analysis_result.get("ship_name", "Unknown_Ship")
        ship = await mongo_db.find_one("ships", {"name": {"$regex": ship_name, "$options": "i"}})
        
        if not ship:
            return
        
        # Create survey status record
        survey_data = {
            'id': str(uuid.uuid4()),
            'ship_id': ship['id'],
            'certificate_type': survey_info.get('certificate_type', 'CLASS'),
            'certificate_number': survey_info.get('certificate_number'),
            'survey_type': survey_info.get('survey_type', 'Annual'),
            'issuance_date': parse_date_string(survey_info.get('issuance_date')),
            'expiration_date': parse_date_string(survey_info.get('expiration_date')),
            'renewal_range_start': parse_date_string(survey_info.get('renewal_range_start')),
            'renewal_range_end': parse_date_string(survey_info.get('renewal_range_end')),
            'survey_status': 'completed',
            'created_at': datetime.now(timezone.utc)
        }
        
        # Handle multiple due dates
        due_dates = survey_info.get('due_dates', [])
        if due_dates:
            for i, due_date in enumerate(due_dates[:4]):  # Max 4 due dates
                survey_data[f'due_date_{i+1}'] = parse_date_string(due_date)
        
        await mongo_db.create("ship_survey_status", survey_data)
        
    except Exception as e:
        logger.error(f"Survey status update failed: {e}")
        raise

def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime object"""
    if not date_str:
        return None
    
    try:
        # Try ISO format first
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            # Try date only format
            return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except:
        return None

# Certificate Upload with Company Google Drive Integration
@api_router.post("/certificates/upload-with-file", response_model=CertificateResponse)
async def create_certificate_with_file_upload(
    file: UploadFile = File(...),
    ship_id: str = Form(...),
    cert_name: str = Form(...),
    cert_no: str = Form(...),
    issue_date: str = Form(...),
    valid_date: str = Form(...),
    last_endorse: Optional[str] = Form(None),
    next_survey: Optional[str] = Form(None),
    category: str = Form(...),
    sensitivity_level: str = Form(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Create new certificate with file upload to Company Google Drive"""
    try:
        if not has_permission(current_user, UserRole.EDITOR):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # File size validation (150MB limit as specified by user)
        MAX_FILE_SIZE = 150 * 1024 * 1024  # 150MB in bytes
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 150MB limit")
        
        # Verify ship exists
        ship = await mongo_db.find_one("ships", {"id": ship_id})
        if not ship:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ship not found")
        
        # Get user's company information
        if not current_user.company:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not associated with any company")
        
        # Find company by name (matching either name_vn or name_en)
        company = await mongo_db.find_one("companies", {
            "$or": [
                {"name_vn": current_user.company},
                {"name_en": current_user.company}
            ]
        })
        
        if not company:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company not found")
        
        # Check if company has Google Drive configured
        gdrive_config = company.get('gdrive_config', {})
        if not gdrive_config.get('configured', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Google Drive not configured for your company. Please contact administrator to configure Google Drive."
            )
        
        # Create certificate metadata
        cert_dict = {
            'id': str(uuid.uuid4()),
            'ship_id': ship_id,
            'cert_name': cert_name,
            'cert_no': cert_no,
            'issue_date': datetime.fromisoformat(issue_date.replace('Z', '+00:00')),
            'valid_date': datetime.fromisoformat(valid_date.replace('Z', '+00:00')),
            'last_endorse': datetime.fromisoformat(last_endorse.replace('Z', '+00:00')) if last_endorse and last_endorse.strip() else None,
            'next_survey': datetime.fromisoformat(next_survey.replace('Z', '+00:00')) if next_survey and next_survey.strip() else None,
            'category': category,
            'sensitivity_level': sensitivity_level,
            'created_at': datetime.now(timezone.utc),
            'file_uploaded': False,
            'google_drive_file_id': None,
            'file_name': file.filename,
            'file_size': file.size
        }
        
        # Read file content
        file_content = await file.read()
        
        # Upload file to Company Google Drive "DATA INPUT" folder organized by date
        try:
            upload_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            
            auth_method = gdrive_config.get("auth_method", "service_account")
            
            if auth_method == "apps_script":
                # Upload via Apps Script proxy
                web_app_url = gdrive_config.get("web_app_url")
                folder_id = gdrive_config.get("folder_id")
                
                if not web_app_url or not folder_id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google Drive configuration incomplete")
                
                # Create DATA INPUT folder structure: ROOT_FOLDER/DATA INPUT/YYYY-MM-DD/
                folder_structure_payload = {
                    "action": "create_folder_structure",
                    "parent_folder_id": folder_id,
                    "folder_path": f"DATA INPUT/{upload_date}"
                }
                
                folder_response = requests.post(web_app_url, json=folder_structure_payload, timeout=30)
                
                if folder_response.status_code != 200:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                      detail="Failed to create folder structure in Google Drive")
                
                folder_result = folder_response.json()
                if not folder_result.get('success'):
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                      detail=f"Failed to create folder: {folder_result.get('message')}")
                
                target_folder_id = folder_result.get('folder_id')
                
                # Upload file to the date-organized folder
                import base64
                file_content_base64 = base64.b64encode(file_content).decode('utf-8')
                
                upload_payload = {
                    "action": "upload_file",
                    "folder_id": target_folder_id,
                    "file_name": f"{cert_name}_{cert_no}_{file.filename}",
                    "file_content": file_content_base64,
                    "mime_type": file.content_type or "application/octet-stream"
                }
                
                upload_response = requests.post(web_app_url, json=upload_payload, timeout=60)
                
                if upload_response.status_code != 200:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                      detail="Failed to upload file to Google Drive")
                
                upload_result = upload_response.json()
                if not upload_result.get('success'):
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                      detail=f"File upload failed: {upload_result.get('message')}")
                
                cert_dict['file_uploaded'] = True
                cert_dict['google_drive_file_id'] = upload_result.get('file_id')
                cert_dict['google_drive_folder_path'] = f"DATA INPUT/{upload_date}"
                
            elif auth_method == "service_account":
                # Upload via Service Account (to be implemented if needed)
                raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, 
                                  detail="Service Account upload not yet implemented")
            
            elif auth_method == "oauth":
                # Upload via OAuth (to be implemented if needed)
                raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, 
                                  detail="OAuth upload not yet implemented")
            
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                  detail="Unsupported Google Drive authentication method")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Drive upload error: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                              detail="Failed to upload file to Google Drive")
        
        # Save certificate record to MongoDB
        await mongo_db.create("certificates", cert_dict)
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "create_certificate_with_file",
            "resource": "certificates",
            "details": {
                "certificate_id": cert_dict['id'], 
                "ship_id": ship_id,
                "company_id": company['id'],
                "file_name": file.filename,
                "file_size": file.size,
                "google_drive_uploaded": cert_dict['file_uploaded']
            },
            "timestamp": datetime.now(timezone.utc)
        })
        
        return CertificateResponse(**cert_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating certificate with file upload: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                          detail="Failed to create certificate with file upload")

# Multi-File Upload with AI Classification and Processing
@api_router.post("/certificates/upload-multi-files")
async def upload_multi_files_with_ai_processing(
    files: List[UploadFile] = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload multiple files, AI classify and process automatically"""
    try:
        if not has_permission(current_user, UserRole.EDITOR):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # File size validation (150MB limit per file)
        MAX_FILE_SIZE = 150 * 1024 * 1024  # 150MB in bytes
        for file in files:
            if file.size and file.size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"File {file.filename} exceeds 150MB limit"
                )
        
        # Get user's company information
        if not current_user.company:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not associated with any company")
        
        # Find company by name
        company = await mongo_db.find_one("companies", {
            "$or": [
                {"name_vn": current_user.company},
                {"name_en": current_user.company}
            ]
        })
        
        if not company:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company not found")
        
        # Check if company has Google Drive configured
        gdrive_config = company.get('gdrive_config', {})
        if not gdrive_config.get('configured', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Google Drive not configured for your company. Please contact administrator to configure Google Drive."
            )
        
        # Get AI configuration
        ai_config = await mongo_db.find_one("ai_config", {})
        if not ai_config:
            ai_config = {
                "provider": "OPENAI",
                "model": "gpt-4o",
                "api_key": EMERGENT_LLM_KEY,  # Fallback to Emergent LLM key
                "max_tokens": 1000,
                "temperature": 0.1
            }
        
        processing_results = []
        
        # Process each file
        for file in files:
            try:
                file_result = {
                    "filename": file.filename,
                    "size": file.size,
                    "status": "processing",
                    "category": None,
                    "ship_name": None,
                    "certificate_created": False,
                    "survey_status_updated": False,
                    "google_drive_uploaded": False,
                    "errors": [],
                    "extracted_info": {}
                }
                
                # Read file content
                file_content = await file.read()
                
                # AI Analysis using configured AI
                try:
                    analysis_result = await analyze_document_with_ai(
                        file_content, file.filename, file.content_type, ai_config
                    )
                    
                    file_result["extracted_info"] = analysis_result
                    file_result["category"] = analysis_result.get("category", "other_documents")
                    file_result["ship_name"] = analysis_result.get("ship_name", "Unknown_Ship")
                    
                except Exception as e:
                    file_result["errors"].append(f"AI analysis failed: {str(e)}")
                    file_result["category"] = "other_documents"
                    file_result["ship_name"] = "Unknown_Ship"
                
                # Create/ensure folder structure exists
                folder_structure = None
                try:
                    folder_structure = await create_ship_folder_structure(
                        gdrive_config, file_result["ship_name"]
                    )
                    file_result["folder_created"] = True
                except Exception as e:
                    file_result["errors"].append(f"Folder creation failed: {str(e)}")
                
                # Upload file to appropriate category folder
                try:
                    upload_result = await upload_file_to_category_folder(
                        gdrive_config, file_content, file.filename, 
                        file_result["ship_name"], file_result["category"], folder_structure
                    )
                    file_result["google_drive_uploaded"] = True
                    file_result["google_drive_file_id"] = upload_result.get("file_id")
                except Exception as e:
                    file_result["errors"].append(f"File upload failed: {str(e)}")
                
                # Auto-create certificate record if category is "certificates"
                if file_result["category"] == "certificates" and analysis_result:
                    try:
                        cert_record = await create_certificate_from_analysis(
                            analysis_result, current_user, file.filename, file.size,
                            file_result.get("google_drive_file_id")
                        )
                        file_result["certificate_created"] = True
                        file_result["certificate_id"] = cert_record["id"]
                    except Exception as e:
                        file_result["errors"].append(f"Certificate creation failed: {str(e)}")
                
                # Update Ship Survey Status if relevant information found
                if analysis_result and analysis_result.get("survey_info"):
                    try:
                        await update_ship_survey_status(analysis_result, current_user)
                        file_result["survey_status_updated"] = True
                    except Exception as e:
                        file_result["errors"].append(f"Survey status update failed: {str(e)}")
                
                file_result["status"] = "completed" if not file_result["errors"] else "completed_with_errors"
                processing_results.append(file_result)
                
            except Exception as e:
                file_result["status"] = "failed"
                file_result["errors"].append(f"Processing failed: {str(e)}")
                processing_results.append(file_result)
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "multi_file_upload_ai_processing",
            "resource": "certificates",
            "details": {
                "files_processed": len(files),
                "successful_uploads": len([r for r in processing_results if r["status"] == "completed"]),
                "certificates_created": len([r for r in processing_results if r["certificate_created"]]),
                "company_id": company['id']
            },
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {
            "message": f"Processed {len(files)} files",
            "total_files": len(files),
            "successful_uploads": len([r for r in processing_results if r["google_drive_uploaded"]]),
            "certificates_created": len([r for r in processing_results if r["certificate_created"]]),
            "results": processing_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-file upload processing: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                          detail="Failed to process multi-file upload")

# Ship Survey Status Routes
@api_router.get("/ships/{ship_id}/survey-status", response_model=List[ShipSurveyStatusResponse])
async def get_ship_survey_status(ship_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Get survey status for a ship"""
    try:
        if not has_permission(current_user, UserRole.VIEWER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Verify ship exists
        ship = await mongo_db.find_one("ships", {"id": ship_id})
        if not ship:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ship not found")
        
        # Get survey status records
        survey_statuses = await mongo_db.find_many("ship_survey_status", {"ship_id": ship_id})
        
        return [ShipSurveyStatusResponse(**status) for status in survey_statuses]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ship survey status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch ship survey status")

@api_router.post("/ships/{ship_id}/survey-status", response_model=ShipSurveyStatusResponse)
async def create_ship_survey_status(ship_id: str, status_data: ShipSurveyStatusCreate, current_user: UserResponse = Depends(get_current_user)):
    """Create new survey status record"""
    try:
        if not has_permission(current_user, UserRole.EDITOR):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Verify ship exists
        ship = await mongo_db.find_one("ships", {"id": ship_id})
        if not ship:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ship not found")
        
        # Create survey status data
        status_dict = status_data.dict()
        status_dict['id'] = str(uuid.uuid4())
        status_dict['created_at'] = datetime.now(timezone.utc)
        
        # Save to MongoDB
        await mongo_db.create("ship_survey_status", status_dict)
        
        return ShipSurveyStatusResponse(**status_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ship survey status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create ship survey status")

# AI Configuration Routes  
@api_router.get("/ai-config")
async def get_ai_config(current_user: UserResponse = Depends(get_current_user)):
    """Get AI configuration"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        config = await mongo_db.find_one("ai_config", {})
        if config:
            # Remove _id and other MongoDB fields
            if '_id' in config:
                del config['_id']
            return config
        else:
            return {
                "provider": "OPENAI",
                "model": "gpt-4o",
                "api_key": "",
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI config: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get AI config")

@api_router.post("/ai-config")
async def update_ai_config(config_data: dict, current_user: UserResponse = Depends(get_current_user)):
    """Update AI configuration"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Add metadata
        config_data['updated_by'] = current_user.id
        config_data['updated_at'] = datetime.now(timezone.utc)
        
        # Remove existing config and insert new one
        await mongo_db.database.ai_config.delete_many({})
        await mongo_db.create("ai_config", config_data)
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "update_ai_config",
            "resource": "ai_config",
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {"message": "AI configuration updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating AI config: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update AI config")

# Usage Statistics Routes
@api_router.get("/usage-stats")
async def get_usage_stats(current_user: UserResponse = Depends(get_current_user)):
    """Get usage statistics"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Get usage data from last 30 days
        usage_data = await mongo_db.get_usage_stats(days=30)
        
        # Process and aggregate data
        total_requests = len(usage_data)
        requests_by_user = {}
        requests_by_action = {}
        
        for record in usage_data:
            user_id = record.get('user_id', 'unknown')
            action = record.get('action', 'unknown')
            
            requests_by_user[user_id] = requests_by_user.get(user_id, 0) + 1
            requests_by_action[action] = requests_by_action.get(action, 0) + 1
        
        return {
            "total_requests": total_requests,
            "requests_by_user": requests_by_user,
            "requests_by_action": requests_by_action,
            "date_range": "Last 30 days"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get usage stats")

# System Settings Routes
@api_router.get("/settings")
async def get_settings(current_user: UserResponse = Depends(get_current_user)):
    """Get system settings"""
    try:
        if not has_permission(current_user, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        settings = await mongo_db.find_one("company_settings", {})
        if settings:
            # Remove _id and other MongoDB fields
            if '_id' in settings:
                del settings['_id']
            return settings
        else:
            return {
                "system_name": "Ship Management System",
                "version": "2.0.0",
                "maintenance_mode": False,
                "max_users": 100
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get settings")

@api_router.post("/settings")
async def update_settings(settings_data: dict, current_user: UserResponse = Depends(get_current_user)):
    """Update system settings"""
    try:
        if not has_permission(current_user, UserRole.SUPER_ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Super Admin can update settings")
        
        # Add metadata
        settings_data['updated_by'] = current_user.id
        settings_data['updated_at'] = datetime.now(timezone.utc)
        
        # Remove existing settings and insert new one
        await mongo_db.database.company_settings.delete_many({})
        await mongo_db.create("company_settings", settings_data)
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "update_settings",
            "resource": "settings",
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {"message": "Settings updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update settings")

# AI Features Routes (Placeholder)
@api_router.post("/ai/analyze")
async def ai_analyze(request: dict, current_user: UserResponse = Depends(get_current_user)):
    """AI document analysis (placeholder)"""
    try:
        if not has_permission(current_user, UserRole.EDITOR):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Placeholder for AI analysis functionality
        # This would integrate with actual AI service when implemented
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "ai_analyze",
            "resource": "ai",
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {
            "message": "AI analysis feature not yet implemented",
            "status": "placeholder",
            "request_logged": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI analyze: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI analysis failed")

@api_router.get("/ai/search")
async def ai_search(q: str = "", current_user: UserResponse = Depends(get_current_user)):
    """AI smart search (placeholder)"""
    try:
        if not has_permission(current_user, UserRole.VIEWER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Placeholder for AI search functionality
        # This would integrate with actual AI service when implemented
        
        # Log usage
        await mongo_db.create("usage_tracking", {
            "user_id": current_user.id,
            "action": "ai_search",
            "resource": "ai",
            "details": {"query": q},
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {
            "message": "AI search feature not yet implemented",
            "query": q,
            "status": "placeholder",
            "results": []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI search: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI search failed")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize MongoDB connection on startup"""
    try:
        await mongo_db.connect()
        logger.info("✅ MongoDB connection established")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown"""
    try:
        await mongo_db.disconnect()
        logger.info("✅ MongoDB connection closed")
    except Exception as e:
        logger.error(f"❌ Error closing MongoDB connection: {e}")

# PDF Analysis Route
@api_router.post("/analyze-ship-certificate")
async def analyze_ship_certificate(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Analyze PDF certificate to extract ship information using AI"""
    try:
        # Check permissions
        if not has_permission(current_user, UserRole.EDITOR):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Validate file type and size
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 5MB limit")
        
        # Save file temporarily
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        temp_file_path = temp_dir / f"{uuid.uuid4()}_{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)
        
        try:
            # Initialize AI chat with Emergent LLM key
            api_key = os.environ.get('EMERGENT_LLM_KEY')
            if not api_key:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI service not configured")
            
            # Create LLM chat instance with Gemini for file support
            chat = LlmChat(
                api_key=api_key,
                session_id=f"pdf_analysis_{uuid.uuid4()}",
                system_message="""You are an expert ship certificate analyzer. Extract ship information from PDF certificates.
                
                Return ONLY a JSON object with these exact fields (use null for missing information):
                {
                    "ship_name": "string or null",
                    "imo_number": "string or null", 
                    "class_society": "string or null",
                    "flag": "string or null",
                    "gross_tonnage": "number or null",
                    "deadweight": "number or null", 
                    "built_year": "number or null",
                    "ship_owner": "string or null"
                }
                
                IMPORTANT: Do NOT extract company/management company information. Only extract the fields listed above.
                Extract only accurate information from the document. Do not make assumptions."""
            ).with_model("gemini", "gemini-2.0-flash")
            
            # Create file content for analysis
            pdf_file = FileContentWithMimeType(
                file_path=str(temp_file_path),
                mime_type="application/pdf"
            )
            
            # Send message for analysis
            user_message = UserMessage(
                text="Analyze this ship certificate PDF and extract the ship information. Return only the JSON object with the specified structure.",
                file_contents=[pdf_file]
            )
            
            response = await chat.send_message(user_message)
            
            # Parse AI response
            try:
                # Clean the response to extract JSON
                response_text = response.strip()
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()
                
                analysis_result = json.loads(response_text)
                
                # Validate extracted data structure (excluding company field)
                expected_fields = ['ship_name', 'imo_number', 'class_society', 'flag', 'gross_tonnage', 'deadweight', 'built_year', 'ship_owner']
                cleaned_result = {}
                
                for field in expected_fields:
                    value = analysis_result.get(field)
                    if value == "" or value == "null" or value == "N/A":
                        cleaned_result[field] = None
                    else:
                        cleaned_result[field] = value
                
                # Log usage
                await mongo_db.create("usage_tracking", {
                    "user_id": current_user.id,
                    "action": "pdf_analysis",
                    "resource": "ship_certificate",
                    "details": {"filename": file.filename, "file_size": file_size},
                    "timestamp": datetime.now(timezone.utc)
                })
                
                return {
                    "success": True,
                    "analysis": cleaned_result,
                    "message": "PDF analysis completed successfully"
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {response}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI response parsing failed")
                
        finally:
            # Clean up temporary file
            if temp_file_path.exists():
                temp_file_path.unlink()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing PDF certificate: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF analysis failed: {str(e)}")

# CORS middleware
origins = os.environ.get('CORS_ORIGINS', '*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)