from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
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

# Import our new database modules
from file_database import file_db
from google_drive_manager import gdrive_manager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection (TODO: Migrate to file_database)
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
app = FastAPI(title="Ship Management System API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Create uploads directory if it doesn't exist
os.makedirs("uploads/company_logos", exist_ok=True)

# Mount static files for serving uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Enums
class UserRole(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor" 
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class PermissionType(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE_USERS = "manage_users"
    SYSTEM_CONTROL = "system_control"

class DocumentCategory(str, Enum):
    CERTIFICATES = "certificates"
    INSPECTION_RECORDS = "inspection_records"
    SURVEY_REPORTS = "survey_reports"
    DRAWINGS_MANUALS = "drawings_manuals"
    OTHER_DOCUMENTS = "other_documents"

class Department(str, Enum):
    TECHNICAL = "technical"
    OPERATIONS = "operations"
    SAFETY = "safety"
    COMMERCIAL = "commercial"
    CREWING = "crewing"
    SHIP_CREW = "ship_crew"

class SensitivityLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    password_hash: str
    full_name: str
    role: UserRole
    department: Department
    company: Optional[str] = None
    ship: Optional[str] = None
    zalo: Optional[str] = None
    gmail: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    permissions: Dict[str, Any] = Field(default_factory=dict)

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    department: Department
    company: Optional[str] = None
    ship: Optional[str] = None
    zalo: Optional[str] = None
    gmail: Optional[str] = None

class UserUpdate(BaseModel):
    username: str
    email: EmailStr
    password: Optional[str] = None
    full_name: str
    role: UserRole
    department: Department
    company: Optional[str] = None
    ship: Optional[str] = None
    zalo: Optional[str] = None
    gmail: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    department: Department
    company: Optional[str] = None
    ship: Optional[str] = None
    zalo: Optional[str] = None
    gmail: Optional[str] = None
    is_active: bool
    created_at: datetime
    permissions: Dict[str, Any]

class PermissionRequest(BaseModel):
    user_ids: List[str]
    categories: List[DocumentCategory]
    departments: List[Department]
    sensitivity_levels: List[SensitivityLevel]
    permissions: List[PermissionType]

class Ship(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    imo_number: str
    class_society: str
    flag: str
    gross_tonnage: float
    deadweight: float
    built_year: int
    photo_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ShipCreate(BaseModel):
    name: str
    imo_number: str
    class_society: str
    flag: str
    gross_tonnage: float
    deadweight: float
    built_year: int

class Certificate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ship_id: str
    cert_name: str
    cert_no: str
    issue_date: datetime
    valid_date: datetime
    last_endorse: Optional[datetime] = None
    next_survey: Optional[datetime] = None
    category: DocumentCategory
    sensitivity_level: SensitivityLevel
    file_path: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CertificateCreate(BaseModel):
    ship_id: str
    cert_name: str
    cert_no: str
    issue_date: datetime
    valid_date: datetime
    last_endorse: Optional[datetime] = None
    next_survey: Optional[datetime] = None
    category: DocumentCategory
    sensitivity_level: SensitivityLevel

class AIAnalysisRequest(BaseModel):
    document_id: str
    analysis_type: str  # "summary", "compliance_check", "expiry_alert"

class CompanySettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str
    logo_url: Optional[str] = None
    language_preference: str = "en"  # "en" or "vi"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Company(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name_vn: str
    name_en: str
    address_vn: str
    address_en: str
    tax_id: str
    logo_url: Optional[str] = None
    gdrive_config: Optional[Dict[str, Any]] = None
    gmail: Optional[str] = None
    zalo: Optional[str] = None
    system_expiry: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str

class CompanyCreate(BaseModel):
    name_vn: str
    name_en: str
    address_vn: str
    address_en: str
    tax_id: str
    logo_url: Optional[str] = None
    gmail: Optional[str] = None
    zalo: Optional[str] = None
    system_expiry: Optional[datetime] = None
    gdrive_config: Optional[Dict[str, Any]] = None

class AIProviderConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: str  # "openai", "anthropic", "google"
    model: str
    is_active: bool = True
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str

class AIProviderConfigUpdate(BaseModel):
    provider: str
    model: str

class UsageTracking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    provider: str  # "openai", "anthropic", "google"
    model: str
    request_type: str  # "document_analysis", "smart_search", "other"
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    document_id: Optional[str] = None
    search_query: Optional[str] = None

class UsageStats(BaseModel):
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_estimated_cost: float
    requests_by_provider: Dict[str, int]
    requests_by_model: Dict[str, int]
    requests_by_type: Dict[str, int]
    daily_usage: List[Dict[str, Any]]
    recent_requests: List[UsageTracking]

class GoogleDriveConfig(BaseModel):
    service_account_json: str
    folder_id: str

class GoogleDriveStatus(BaseModel):
    configured: bool
    last_sync: Optional[str] = None
    local_files: int
    drive_files: int
    folder_id: Optional[str] = None

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_id: str, username: str, role: str, expiration_hours: int = JWT_EXPIRATION_HOURS) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=expiration_hours)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def estimate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost based on provider, model, and token usage"""
    # Pricing per 1M tokens (as of 2024)
    pricing = {
        "openai": {
            "gpt-4o": {"input": 5.0, "output": 15.0},
            "gpt-4": {"input": 30.0, "output": 60.0},
            "gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60}
        },
        "anthropic": {
            "claude-3-sonnet": {"input": 3.0, "output": 15.0},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
            "claude-3-opus": {"input": 15.0, "output": 75.0}
        },
        "google": {
            "gemini-pro": {"input": 0.5, "output": 1.5},
            "gemini-pro-vision": {"input": 0.5, "output": 1.5}
        }
    }
    
    if provider not in pricing or model not in pricing[provider]:
        # Default pricing if model not found
        return (input_tokens * 1.0 + output_tokens * 3.0) / 1000000
    
    model_pricing = pricing[provider][model]
    input_cost = (input_tokens * model_pricing["input"]) / 1000000
    output_cost = (output_tokens * model_pricing["output"]) / 1000000
    
    return input_cost + output_cost

def log_usage(user_id: str, provider: str, model: str, request_type: str, 
              input_tokens: int = 0, output_tokens: int = 0, success: bool = True,
              error_message: str = None, document_id: str = None, search_query: str = None):
    """Log AI usage for tracking"""
    try:
        estimated_cost = estimate_cost(provider, model, input_tokens, output_tokens)
        
        usage = UsageTracking(
            user_id=user_id,
            provider=provider,
            model=model,
            request_type=request_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimated_cost,
            success=success,
            error_message=error_message,
            document_id=document_id,
            search_query=search_query
        )
        
        file_db.insert_usage_tracking(usage.dict())
        logger.info(f"Usage logged: {provider}/{model} - {input_tokens}+{output_tokens} tokens - ${estimated_cost:.4f}")
        
    except Exception as e:
        logger.error(f"Failed to log usage: {e}")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = file_db.find_user({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return UserResponse(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def has_permission(user: UserResponse, required_role: UserRole = None, required_permission: PermissionType = None) -> bool:
    role_hierarchy = {
        UserRole.VIEWER: 1,
        UserRole.EDITOR: 2,
        UserRole.MANAGER: 3,
        UserRole.ADMIN: 4,
        UserRole.SUPER_ADMIN: 5
    }
    
    if required_role and role_hierarchy[user.role] < role_hierarchy[required_role]:
        return False
    
    return True

async def init_ai_chat():
    """Initialize AI chat for document analysis"""
    if not EMERGENT_LLM_KEY:
        return None
    
    return LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"ship-management-{datetime.now().isoformat()}",
        system_message="You are an AI assistant specialized in maritime document analysis and ship management. Provide accurate, detailed analysis of shipping documents, certificates, and compliance requirements."
    ).with_model("openai", "gpt-4o")

# Authentication Routes
@api_router.post("/auth/login")
async def login(user_credentials: UserLogin):
    user = file_db.find_user({"username": user_credentials.username})
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="Account disabled")
    
    # Check if remember me is requested (extend token expiration)
    remember_me = getattr(user_credentials, 'remember_me', False)
    expiration_hours = 24 * 30 if remember_me else JWT_EXPIRATION_HOURS  # 30 days vs 24 hours
    
    access_token = create_access_token(user["id"], user["username"], user["role"], expiration_hours)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user),
        "remember_me": remember_me
    }

@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, current_user: UserResponse = Depends(get_current_user)):
    # Only managers and above can create users
    if not has_permission(current_user, UserRole.MANAGER):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Check if user exists
    existing_user = file_db.find_user({"username": user_data.username})
    if not existing_user:
        existing_user = file_db.find_user({"email": user_data.email})
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user
    password_hash = hash_password(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        full_name=user_data.full_name,
        role=user_data.role,
        department=user_data.department,
        company=user_data.company,
        ship=user_data.ship,
        zalo=user_data.zalo,
        gmail=user_data.gmail
    )
    
    created_user = file_db.insert_user(user.dict())
    
    # Sync to Google Drive
    gdrive_manager.sync_to_drive()
    
    return UserResponse(**created_user)

# User Management Routes
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.MANAGER):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    users = file_db.find_all_users()
    
    # Filter users based on current user's role and company
    if current_user.role == UserRole.MANAGER:
        # Manager can only see users from their own company
        users = [user for user in users if user.get('company') == current_user.company]
    elif current_user.role == UserRole.ADMIN:
        # Admin can see all users (no filtering)
        pass
    elif current_user.role == UserRole.SUPER_ADMIN:
        # Super Admin can see all users (no filtering)
        pass
    
    return [UserResponse(**user) for user in users]

@api_router.post("/permissions/assign")
async def assign_permissions(request: PermissionRequest, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.MANAGER):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Update permissions for multiple users
    permission_update = {
        "permissions": {
            "categories": request.categories,
            "departments": request.departments,
            "sensitivity_levels": request.sensitivity_levels,
            "permissions": request.permissions,
            "assigned_by": current_user.id,
            "assigned_at": datetime.now(timezone.utc).isoformat()
        }
    }
    
    file_db.update_users(
        {"id": {"$in": request.user_ids}},
        permission_update
    )
    
    # Sync to Google Drive
    gdrive_manager.sync_to_drive()
    
    return {"message": f"Permissions assigned to {len(request.user_ids)} users"}

@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.MANAGER):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    user = file_db.find_user({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(**user)

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str, 
    user_update: UserUpdate, 
    current_user: UserResponse = Depends(get_current_user)
):
    if not has_permission(current_user, UserRole.MANAGER):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Find existing user
    existing_user = file_db.find_user({"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if username is being changed and if it's already taken
    if user_update.username != existing_user.get("username"):
        if file_db.find_user({"username": user_update.username}):
            raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email is being changed and if it's already taken
    if user_update.email != existing_user.get("email"):
        if file_db.find_user({"email": user_update.email}):
            raise HTTPException(status_code=400, detail="Email already exists")
    
    # Prepare update data
    update_data = {
        **existing_user,
        "username": user_update.username,
        "email": user_update.email,
        "full_name": user_update.full_name,
        "role": user_update.role,
        "company": user_update.company,
        "ship": user_update.ship,
        "department": user_update.department,
        "zalo": user_update.zalo,
        "gmail": user_update.gmail,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user.id
    }
    
    # Update password only if provided
    if user_update.password:
        update_data["password_hash"] = hash_password(user_update.password)
    
    # Update user
    file_db.update_user({"id": user_id}, update_data)
    
    # Sync to Google Drive
    gdrive_manager.sync_to_drive()
    
    return UserResponse(**update_data)

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Only Admin and above can delete users")
    
    # Find existing user
    existing_user = file_db.find_user({"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Prevent deletion of Super Admin by non-Super Admin
    if existing_user.get("role") == "super_admin" and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only Super Admin can delete Super Admin accounts")
    
    # Delete user
    file_db.delete_user({"id": user_id})
    
    # Sync to Google Drive
    gdrive_manager.sync_to_drive()
    
    return {"message": "User deleted successfully"}

# Ship Management Routes
@api_router.post("/ships", response_model=Ship)
async def create_ship(ship_data: ShipCreate, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.EDITOR):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    ship = Ship(**ship_data.dict())
    created_ship = file_db.insert_ship(ship.dict())
    
    # Sync to Google Drive
    gdrive_manager.sync_to_drive()
    
    return Ship(**created_ship)

@api_router.get("/ships", response_model=List[Ship])
async def get_ships(current_user: UserResponse = Depends(get_current_user)):
    ships = file_db.find_all_ships()
    return [Ship(**ship) for ship in ships]

@api_router.get("/ships/{ship_id}", response_model=Ship)
async def get_ship(ship_id: str, current_user: UserResponse = Depends(get_current_user)):
    ship = file_db.find_ship({"id": ship_id})
    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")
    return Ship(**ship)

# Certificate Management Routes
@api_router.post("/certificates", response_model=Certificate)
async def create_certificate(cert_data: CertificateCreate, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.EDITOR):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    certificate = Certificate(**cert_data.dict())
    created_cert = file_db.insert_certificate(certificate.dict())
    
    # Sync to Google Drive
    gdrive_manager.sync_to_drive()
    
    return Certificate(**created_cert)

@api_router.get("/ships/{ship_id}/certificates", response_model=List[Certificate])
async def get_ship_certificates(ship_id: str, current_user: UserResponse = Depends(get_current_user)):
    certificates = file_db.find_certificates({"ship_id": ship_id})
    return [Certificate(**cert) for cert in certificates]

# Google Drive Configuration Routes
@api_router.post("/gdrive/configure")
async def configure_google_drive(config: GoogleDriveConfig, current_user: UserResponse = Depends(get_current_user)):
    # Only admin and super_admin can configure Google Drive
    if not has_permission(current_user, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Only admin users can configure Google Drive")
    
    try:
        success = gdrive_manager.configure(config.service_account_json, config.folder_id)
        if success:
            return {"message": "Google Drive configured successfully", "status": "success"}
        else:
            raise HTTPException(status_code=400, detail="Failed to configure Google Drive")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")

@api_router.get("/gdrive/status", response_model=GoogleDriveStatus)
async def get_google_drive_status(current_user: UserResponse = Depends(get_current_user)):
    # Only admin and super_admin can view Google Drive status
    if not has_permission(current_user, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    status = gdrive_manager.get_sync_status()
    return GoogleDriveStatus(**status)

@api_router.post("/gdrive/sync-to-drive")
async def sync_to_google_drive(current_user: UserResponse = Depends(get_current_user)):
    # Only admin and super_admin can sync to Google Drive
    if not has_permission(current_user, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        success = gdrive_manager.sync_to_drive()
        if success:
            # Update last sync time
            config_path = os.path.join(gdrive_manager.local_data_path, 'gdrive_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                config['last_sync'] = datetime.now(timezone.utc).isoformat()
                with open(config_path, 'w') as f:
                    json.dump(config, f)
            
            return {"message": "Data synced to Google Drive successfully", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to sync to Google Drive")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

@api_router.post("/gdrive/sync-from-drive") 
async def sync_from_google_drive(current_user: UserResponse = Depends(get_current_user)):
    # Only admin and super_admin can sync from Google Drive
    if not has_permission(current_user, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        success = gdrive_manager.sync_from_drive()
        if success:
            return {"message": "Data synced from Google Drive successfully", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to sync from Google Drive")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

# File Upload Routes
@api_router.post("/upload/logo")
async def upload_logo(file: UploadFile = File(...), current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    file_path = UPLOAD_DIR / f"logo_{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update company settings
    settings = file_db.get_company_settings()
    settings.update({
        "logo_url": f"/uploads/{file_path.name}",
        "updated_at": datetime.now(timezone.utc).isoformat()
    })
    
    file_db.update_company_settings(settings)
    
    # Sync to Google Drive
    gdrive_manager.sync_to_drive()
    
    return {"logo_url": settings["logo_url"]}

# AI Analysis Routes
@api_router.post("/ai/analyze")
async def analyze_document(request: AIAnalysisRequest, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.VIEWER):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Find the document
    certificates = file_db.find_certificates({"id": request.document_id})
    if not certificates:
        raise HTTPException(status_code=404, detail="Document not found")
    
    certificate = certificates[0]
    
    # Get current AI config
    ai_config = file_db.get_ai_config()
    provider = ai_config.get("provider", "openai")
    model = ai_config.get("model", "gpt-4o")
    
    try:
        chat = await init_ai_chat()
        if not chat:
            # Log failed usage
            log_usage(
                user_id=current_user.id,
                provider=provider,
                model=model,
                request_type="document_analysis",
                success=False,
                error_message="AI service not available",
                document_id=request.document_id
            )
            raise HTTPException(status_code=500, detail="AI service not available")
        
        analysis_prompts = {
            "summary": f"Analyze this ship certificate: {certificate['cert_name']} (No: {certificate['cert_no']}). Provide a comprehensive summary including validity, compliance status, and key requirements.",
            "compliance_check": f"Perform a compliance check for certificate: {certificate['cert_name']}. Issue date: {certificate['issue_date']}, Valid until: {certificate['valid_date']}. Check for any compliance issues or upcoming requirements.",
            "expiry_alert": f"Check expiry status for certificate: {certificate['cert_name']} valid until {certificate['valid_date']}. Provide alerts for upcoming renewal requirements and recommended actions."
        }
        
        prompt = analysis_prompts.get(request.analysis_type, analysis_prompts["summary"])
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Estimate token usage (rough approximation)
        input_tokens = len(prompt.split()) * 1.3  # Rough token estimation
        output_tokens = len(response.split()) * 1.3
        
        # Log successful usage
        log_usage(
            user_id=current_user.id,
            provider=provider,
            model=model,
            request_type="document_analysis",
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            success=True,
            document_id=request.document_id
        )
        
        # Store analysis result
        analysis = {
            "id": str(uuid.uuid4()),
            "document_id": request.document_id,
            "analysis_type": request.analysis_type,
            "result": response,
            "analyzed_by": current_user.id,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "model": model,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens)
        }
        
        file_db.insert_ai_analysis(analysis)
        
        # Sync to Google Drive
        gdrive_manager.sync_to_drive()
        
        return {"analysis": response, "analysis_id": analysis["id"]}
        
    except Exception as e:
        # Log failed usage
        log_usage(
            user_id=current_user.id,
            provider=provider,
            model=model,
            request_type="document_analysis",
            success=False,
            error_message=str(e),
            document_id=request.document_id
        )
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@api_router.get("/ai/search")
async def smart_search(query: str, current_user: UserResponse = Depends(get_current_user)):
    """AI-powered smart search across documents"""
    
    # Get current AI config
    ai_config = file_db.get_ai_config()
    provider = ai_config.get("provider", "openai")
    model = ai_config.get("model", "gpt-4o")
    
    try:
        chat = await init_ai_chat()
        if not chat:
            # Log failed usage
            log_usage(
                user_id=current_user.id,
                provider=provider,
                model=model,
                request_type="smart_search",
                success=False,
                error_message="AI service not available",
                search_query=query
            )
            raise HTTPException(status_code=500, detail="AI service not available")
        
        # Get all certificates for context
        certificates = file_db.find_certificates({})
        
        search_context = f"""
        Search Query: {query}
        
        Available Documents:
        """
        
        for cert in certificates[:20]:  # Limit context size
            search_context += f"- {cert['cert_name']} (No: {cert['cert_no']}) - Ship: {cert.get('ship_id', 'Unknown')} - Valid until: {cert['valid_date']}\n"
        
        search_context += f"\nBased on the query '{query}', identify the most relevant documents and provide detailed recommendations."
        
        user_message = UserMessage(text=search_context)
        response = await chat.send_message(user_message)
        
        # Estimate token usage (rough approximation)
        input_tokens = len(search_context.split()) * 1.3
        output_tokens = len(response.split()) * 1.3
        
        # Log successful usage
        log_usage(
            user_id=current_user.id,
            provider=provider,
            model=model,
            request_type="smart_search",
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            success=True,
            search_query=query
        )
        
        return {"search_results": response, "query": query}
        
    except Exception as e:
        # Log failed usage
        log_usage(
            user_id=current_user.id,
            provider=provider,
            model=model,
            request_type="smart_search",
            success=False,
            error_message=str(e),
            search_query=query
        )
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Company Settings Routes
@api_router.get("/settings")
async def get_settings(current_user: UserResponse = Depends(get_current_user)):
    settings = file_db.get_company_settings()
    return settings

@api_router.post("/settings")
async def update_settings(settings: CompanySettings, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    file_db.update_company_settings(settings.dict())
    
    # Sync to Google Drive
    gdrive_manager.sync_to_drive()
    
    return settings

# AI Provider Configuration Routes (Super Admin only)
@api_router.get("/ai-config")
async def get_ai_config(current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only Super Admin can access AI configuration")
    
    # Get current AI configuration
    config = file_db.get_ai_config()
    if not config:
        # Return default configuration
        return {
            "provider": "openai",
            "model": "gpt-4o",
            "is_active": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.id
        }
    return config

@api_router.post("/ai-config")
async def update_ai_config(config_update: AIProviderConfigUpdate, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only Super Admin can configure AI provider")
    
    ai_config = AIProviderConfig(
        provider=config_update.provider,
        model=config_update.model,
        updated_by=current_user.id
    )
    
    file_db.update_ai_config(ai_config.dict())
    
    # Sync to Google Drive
    gdrive_manager.sync_to_drive()
    
    return {"message": "AI configuration updated successfully", "config": ai_config.dict()}

# Company Management Routes (Super Admin only)
@api_router.get("/companies", response_model=List[Company])
async def get_companies(current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only Super Admin can access company management")
    
    companies = file_db.find_all_companies()
    return [Company(**company) for company in companies]

@api_router.post("/companies", response_model=Company)
async def create_company(company_data: CompanyCreate, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only Super Admin can create companies")
    
    company = Company(
        **company_data.dict(),
        created_by=current_user.id
    )
    
    created_company = file_db.insert_company(company.dict())
    
    # Sync to Google Drive
    gdrive_manager.sync_to_drive()
    
    return Company(**created_company)

@api_router.get("/companies/{company_id}", response_model=Company)
async def get_company(company_id: str, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only Super Admin can access company details")
    
    company = file_db.find_company({"id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return Company(**company)

@api_router.put("/companies/{company_id}", response_model=Company)
async def update_company(company_id: str, company_data: CompanyCreate, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only Super Admin can update companies")
    
    existing_company = file_db.find_company({"id": company_id})
    if not existing_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    updated_data = {
        **existing_company,
        **company_data.dict(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    file_db.update_company({"id": company_id}, updated_data)
    
    # Sync to Google Drive
    gdrive_manager.sync_to_drive()
    
    return Company(**updated_data)

@api_router.delete("/companies/{company_id}")
async def delete_company(company_id: str, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only Super Admin can delete companies")
    
    existing_company = file_db.find_company({"id": company_id})
    if not existing_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    file_db.delete_company({"id": company_id})
    
    # Sync to Google Drive
    gdrive_manager.sync_to_drive()
    
    return {"message": "Company deleted successfully"}

@api_router.post("/companies/{company_id}/upload-logo")
async def upload_company_logo(
    company_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    if not has_permission(current_user, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only Super Admin can upload company logos")
    
    # Check if company exists
    existing_company = file_db.find_company({"id": company_id})
    if not existing_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(os.getcwd(), 'uploads', 'company_logos')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"company_{company_id}_{int(datetime.now().timestamp())}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Update company with logo URL (relative path for web serving)
        logo_url = f"/uploads/company_logos/{filename}"
        
        updated_data = {
            **existing_company,
            "logo_url": logo_url,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        file_db.update_company({"id": company_id}, updated_data)
        
        # Sync to Google Drive
        gdrive_manager.sync_to_drive()
        
        return {"message": "Logo uploaded successfully", "logo_url": logo_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload logo: {str(e)}")

# Usage Tracking Routes (Admin+ only)
@api_router.get("/usage-stats", response_model=UsageStats)
async def get_usage_stats(
    days: int = 30,
    page: int = 1,
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    if not has_permission(current_user, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Only Admin and above can access usage statistics")
    
    try:
        # Get usage data from the last N days
        usage_data = file_db.get_usage_stats(days=days, page=page, limit=limit)
        
        return UsageStats(**usage_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage stats: {str(e)}")

@api_router.get("/usage-tracking")
async def get_usage_tracking(
    days: int = 7,
    provider: str = None,
    user_id: str = None,
    current_user: UserResponse = Depends(get_current_user)
):
    if not has_permission(current_user, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Only Admin and above can access usage tracking")
    
    try:
        filters = {"days": days}
        if provider:
            filters["provider"] = provider
        if user_id:
            filters["user_id"] = user_id
            
        usage_logs = file_db.get_usage_tracking(filters)
        
        return {"usage_logs": usage_logs, "total": len(usage_logs)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage tracking: {str(e)}")

@api_router.delete("/usage-tracking")
async def clear_usage_tracking(
    days_older_than: int = 90,
    current_user: UserResponse = Depends(get_current_user)
):
    if not has_permission(current_user, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only Super Admin can clear usage tracking")
    
    try:
        cleared_count = file_db.clear_old_usage_tracking(days_older_than)
        
        # Sync to Google Drive
        gdrive_manager.sync_to_drive()
        
        return {"message": f"Cleared {cleared_count} usage records older than {days_older_than} days"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear usage tracking: {str(e)}")

# Initialize default admin user and migrate data
@app.on_event("startup")
async def startup_tasks():
    # Create default admin user if not exists
    admin_exists = file_db.find_user({"role": "super_admin"})
    if not admin_exists:
        default_admin = User(
            username="admin",
            email="admin@shipmanagement.com",
            password_hash=hash_password("admin123"),
            full_name="System Administrator",
            role=UserRole.SUPER_ADMIN,
            department=Department.TECHNICAL
        )
        file_db.insert_user(default_admin.dict())
        print("Default admin user created: username=admin, password=admin123")
    
    # Try to sync from Google Drive on startup
    if gdrive_manager.is_configured:
        try:
            gdrive_manager.sync_from_drive()
            print("Data synced from Google Drive on startup")
        except Exception as e:
            print(f"Failed to sync from Google Drive on startup: {e}")
            
    print("Ship Management System started successfully with file-based database")

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()