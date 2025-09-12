from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    department: Department
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

def create_access_token(user_id: str, username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return UserResponse(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
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
    
    access_token = create_access_token(user["id"], user["username"], user["role"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user)
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
        department=user_data.department
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
    settings = await db.company_settings.find_one() or {}
    settings.update({
        "logo_url": f"/uploads/{file_path.name}",
        "updated_at": datetime.now(timezone.utc)
    })
    
    await db.company_settings.replace_one({}, settings, upsert=True)
    return {"logo_url": settings["logo_url"]}

# AI Analysis Routes
@api_router.post("/ai/analyze")
async def analyze_document(request: AIAnalysisRequest, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.VIEWER):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Find the document
    certificate = await db.certificates.find_one({"id": request.document_id})
    if not certificate:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        chat = await init_ai_chat()
        if not chat:
            raise HTTPException(status_code=500, detail="AI service not available")
        
        analysis_prompts = {
            "summary": f"Analyze this ship certificate: {certificate['cert_name']} (No: {certificate['cert_no']}). Provide a comprehensive summary including validity, compliance status, and key requirements.",
            "compliance_check": f"Perform a compliance check for certificate: {certificate['cert_name']}. Issue date: {certificate['issue_date']}, Valid until: {certificate['valid_date']}. Check for any compliance issues or upcoming requirements.",
            "expiry_alert": f"Check expiry status for certificate: {certificate['cert_name']} valid until {certificate['valid_date']}. Provide alerts for upcoming renewal requirements and recommended actions."
        }
        
        prompt = analysis_prompts.get(request.analysis_type, analysis_prompts["summary"])
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Store analysis result
        analysis = {
            "id": str(uuid.uuid4()),
            "document_id": request.document_id,
            "analysis_type": request.analysis_type,
            "result": response,
            "analyzed_by": current_user.id,
            "analyzed_at": datetime.now(timezone.utc)
        }
        
        await db.ai_analyses.insert_one(analysis)
        return {"analysis": response, "analysis_id": analysis["id"]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@api_router.get("/ai/search")
async def smart_search(query: str, current_user: UserResponse = Depends(get_current_user)):
    """AI-powered smart search across documents"""
    try:
        chat = await init_ai_chat()
        if not chat:
            raise HTTPException(status_code=500, detail="AI service not available")
        
        # Get all certificates for context
        certificates = await db.certificates.find().to_list(length=None)
        
        search_context = f"""
        Search Query: {query}
        
        Available Documents:
        """
        
        for cert in certificates[:20]:  # Limit context size
            search_context += f"- {cert['cert_name']} (No: {cert['cert_no']}) - Ship: {cert.get('ship_id', 'Unknown')} - Valid until: {cert['valid_date']}\n"
        
        search_context += f"\nBased on the query '{query}', identify the most relevant documents and provide detailed recommendations."
        
        user_message = UserMessage(text=search_context)
        response = await chat.send_message(user_message)
        
        return {"search_results": response, "query": query}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Company Settings Routes
@api_router.get("/settings")
async def get_settings(current_user: UserResponse = Depends(get_current_user)):
    settings = await db.company_settings.find_one() or {}
    # Remove MongoDB ObjectId if present
    if '_id' in settings:
        del settings['_id']
    return settings

@api_router.post("/settings")
async def update_settings(settings: CompanySettings, current_user: UserResponse = Depends(get_current_user)):
    if not has_permission(current_user, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    await db.company_settings.replace_one({}, settings.dict(), upsert=True)
    return settings

# Initialize default admin user
@app.on_event("startup")
async def create_default_admin():
    admin_exists = await db.users.find_one({"role": "super_admin"})
    if not admin_exists:
        default_admin = User(
            username="admin",
            email="admin@shipmanagement.com",
            password_hash=hash_password("admin123"),
            full_name="System Administrator",
            role=UserRole.SUPER_ADMIN,
            department=Department.TECHNICAL
        )
        await db.users.insert_one(default_admin.dict())
        print("Default admin user created: username=admin, password=admin123")

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