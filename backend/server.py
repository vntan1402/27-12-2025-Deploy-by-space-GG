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
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType

# Import our MongoDB database modules
from mongodb_database import mongo_db
from google_drive_manager import gdrive_manager

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

class ShipCreate(ShipBase):
    pass

class ShipUpdate(BaseModel):
    name: Optional[str] = None
    imo: Optional[str] = None
    flag: Optional[str] = None
    ship_type: Optional[str] = None
    gross_tonnage: Optional[float] = None
    year_built: Optional[int] = None

class ShipResponse(ShipBase):
    id: str
    created_at: datetime

# Certificate models
class CertificateBase(BaseModel):
    ship_id: str
    type: str
    issuer: str
    issue_date: datetime
    expiry_date: datetime
    status: str = "valid"

class CertificateCreate(CertificateBase):
    pass

class CertificateUpdate(BaseModel):
    type: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    status: Optional[str] = None

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