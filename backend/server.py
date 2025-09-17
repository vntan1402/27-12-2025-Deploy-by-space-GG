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
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from enum import Enum
import shutil
import requests
import re
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
    remember_me: Optional[bool] = False

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    remember_me: bool

class ShipBase(BaseModel):
    name: str
    imo: Optional[str] = None
    flag: str
    ship_type: str  # Class society (e.g., "DNV GL", "ABS", "Lloyd's Register")
    gross_tonnage: Optional[float] = None
    deadweight: Optional[float] = None
    built_year: Optional[int] = None
    ship_owner: Optional[str] = None
    company: str  # Company that owns/manages the ship

class ShipCreate(ShipBase):
    pass

class ShipUpdate(BaseModel):
    name: Optional[str] = None
    imo: Optional[str] = None
    flag: Optional[str] = None
    ship_type: Optional[str] = None
    gross_tonnage: Optional[float] = None
    deadweight: Optional[float] = None
    built_year: Optional[int] = None
    ship_owner: Optional[str] = None
    company: Optional[str] = None

class ShipResponse(ShipBase):
    id: str
    created_at: datetime
    # Legacy compatibility
    class_society: Optional[str] = None

    def __init__(self, **data):
        # Map ship_type to class_society for backward compatibility
        if 'ship_type' in data and 'class_society' not in data:
            data['class_society'] = data['ship_type']
        super().__init__(**data)

class CompanyBase(BaseModel):
    name_vn: str
    name_en: str
    address_vn: str
    address_en: str
    tax_id: str
    gmail: Optional[str] = None
    zalo: Optional[str] = None
    system_expiry: Optional[Union[str, datetime]] = None
    # Legacy fields for backward compatibility
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    
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
    system_expiry: Optional[Union[str, datetime]] = None
    # Legacy fields for backward compatibility
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime

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
    notes: Optional[str] = None  # NEW: Notes field for reference certificates

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
    notes: Optional[str] = None  # NEW: Notes field for reference certificates

class CertificateResponse(CertificateBase):
    id: str
    created_at: datetime
    cert_abbreviation: Optional[str] = None  # NEW: Certificate abbreviation
    status: Optional[str] = None  # NEW: Valid/Expired status
    issued_by_abbreviation: Optional[str] = None  # NEW: Organization abbreviation
    has_notes: Optional[bool] = None  # NEW: Flag to indicate if certificate has notes

# Google Drive models
class GoogleDriveConfig(BaseModel):
    service_account_json: str
    folder_id: str

class GoogleDriveStatus(BaseModel):
    status: str
    message: Optional[str] = None
    
class AIConfig(BaseModel):
    provider: str
    model: str
    api_key: str

class AIConfigResponse(BaseModel):
    provider: str
    model: str
    # Don't expose API key in response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Be more specific in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Google Drive Manager
gdrive_manager = GoogleDriveManager()

def generate_certificate_abbreviation(cert_name: str) -> str:
    """Generate certificate abbreviation from certificate name"""
    if not cert_name:
        return ""
    
    # Remove common words and focus on key terms, but keep important maritime terms
    common_words = {'the', 'of', 'and', 'a', 'an', 'for', 'in', 'on', 'at', 'to', 'is', 'are', 'was', 'were'}
    
    # Clean the name and split into words
    words = re.findall(r'\b[A-Za-z]+\b', cert_name.upper())
    
    # Filter out common words but keep all significant maritime terms
    significant_words = []
    for word in words:
        if word.lower() not in common_words:
            significant_words.append(word)
    
    # Handle special cases for maritime certificates
    if not significant_words:
        significant_words = words  # Fallback to all words
    
    # Generate abbreviation by taking first letter of each significant word
    abbreviation = ''.join([word[0] for word in significant_words[:6]])  # Max 6 letters
    
    # Remove trailing 'C' only if it's from the word "Certificate" (last word)
    if (abbreviation.endswith('C') and len(abbreviation) > 1 and 
        len(significant_words) > 0 and significant_words[-1].upper() == 'CERTIFICATE'):
        abbreviation = abbreviation[:-1]
    
    return abbreviation

def generate_organization_abbreviation(org_name: str) -> str:
    """Generate organization abbreviation from organization name using correct maritime industry standards"""
    if not org_name:
        return ""
    
    # Clean and normalize organization name for matching
    org_name_upper = org_name.upper().strip()
    
    # Exact mappings for well-known maritime organizations (CORRECT ABBREVIATIONS)
    exact_mappings = {
        # Panama Maritime Organizations
        'PANAMA MARITIME DOCUMENTATION SERVICES': 'PMDS',
        'PANAMA MARITIME DOCUMENTATION SERVICES INC': 'PMDS',
        'PANAMA MARITIME AUTHORITY': 'PMA',
        
        # Major Classification Societies (IACS Members)
        'DET NORSKE VERITAS': 'DNV',
        'DNV GL': 'DNV',  # DNV GL merged, now just DNV
        'AMERICAN BUREAU OF SHIPPING': 'ABS',
        'LLOYD\'S REGISTER': 'LR',
        'LLOYDS REGISTER': 'LR',
        'LLOYD\'S REGISTER OF SHIPPING': 'LR',
        'BUREAU VERITAS': 'BV',
        'CHINA CLASSIFICATION SOCIETY': 'CCS',
        'NIPPON KAIJI KYOKAI': 'ClassNK',
        'CLASS NK': 'ClassNK',
        'KOREAN REGISTER OF SHIPPING': 'KR',
        'REGISTRO ITALIANO NAVALE': 'RINA',
        'RUSSIAN MARITIME REGISTER OF SHIPPING': 'RS',
        'CROATIAN REGISTER OF SHIPPING': 'CRS',
        'POLISH REGISTER OF SHIPPING': 'PRS',
        'TURKISH LLOYD': 'TL',
        'INDIAN REGISTER OF SHIPPING': 'IRClass',
        
        # Other Flag State Authorities
        'LIBERIA MARITIME AUTHORITY': 'LISCR',  # Liberian International Ship and Corporate Registry
        'MARSHALL ISLANDS MARITIME AUTHORITY': 'MIMA',
        'SINGAPORE MARITIME AND PORT AUTHORITY': 'MPA',
        'MALAYSIA MARINE DEPARTMENT': 'MMD',
        'HONG KONG MARINE DEPARTMENT': 'MARDEP',
        
        # Government Maritime Administrations
        'MARITIME SAFETY ADMINISTRATION': 'MSA',
        'COAST GUARD': 'CG',
        'PORT STATE CONTROL': 'PSC',
        'INTERNATIONAL MARITIME ORGANIZATION': 'IMO',
    }
    
    # Check for exact matches first
    for full_name, abbreviation in exact_mappings.items():
        if full_name in org_name_upper:
            return abbreviation
    
    # Pattern-based matching for common variations
    if 'PANAMA MARITIME' in org_name_upper and 'DOCUMENTATION' in org_name_upper:
        return 'PMDS'
    elif 'PANAMA MARITIME' in org_name_upper and 'AUTHORITY' in org_name_upper:
        return 'PMA'
    elif 'DNV' in org_name_upper and ('GL' in org_name_upper or 'VERITAS' in org_name_upper):
        return 'DNV'
    elif 'AMERICAN BUREAU' in org_name_upper and 'SHIPPING' in org_name_upper:
        return 'ABS'
    elif 'LLOYD' in org_name_upper and 'REGISTER' in org_name_upper:
        return 'LR'
    elif 'BUREAU VERITAS' in org_name_upper:
        return 'BV'
    elif 'CHINA CLASSIFICATION' in org_name_upper:
        return 'CCS'
    elif 'NIPPON KAIJI' in org_name_upper or 'CLASS NK' in org_name_upper:
        return 'ClassNK'
    elif 'KOREAN REGISTER' in org_name_upper:
        return 'KR'
    elif 'RINA' in org_name_upper and ('ITALIANO' in org_name_upper or 'NAVALE' in org_name_upper):
        return 'RINA'
    elif 'RUSSIAN MARITIME' in org_name_upper or 'RMRS' in org_name_upper:
        return 'RS'
    elif 'LIBERIA' in org_name_upper and 'MARITIME' in org_name_upper:
        return 'LISCR'
    elif 'MARSHALL ISLANDS' in org_name_upper:
        return 'MIMA'
    
    # Fallback: Generate abbreviation from significant words
    common_org_words = {
        'the', 'of', 'and', 'a', 'an', 'for', 'in', 'on', 'at', 'to', 'is', 'are', 'was', 'were',
        'inc', 'ltd', 'llc', 'corp', 'corporation', 'company', 'co', 'limited', 'services',
        'international', 'group', 'holdings', 'management', 'administration', 'department'
    }
    
    # Clean the name and split into words
    import re
    words = re.findall(r'\b[A-Za-z]+\b', org_name_upper)
    
    # Filter out common words but keep important maritime terms
    significant_words = []
    for word in words:
        word_lower = word.lower()
        if word_lower not in common_org_words:
            significant_words.append(word)
        elif word_lower in ['authority', 'maritime', 'classification', 'society', 'register', 'bureau', 'class']:
            # Keep important maritime organization words
            significant_words.append(word)
    
    # Handle special cases for empty result
    if not significant_words:
        significant_words = words[:3]  # Take first 3 words as fallback
    
    # Generate abbreviation by taking first letter of each significant word
    abbreviation = ''.join([word[0] for word in significant_words[:4]])  # Max 4 letters for organizations
    
    return abbreviation if abbreviation else org_name[:4].upper()

def calculate_certificate_status(valid_date: datetime, cert_type: str = None) -> str:
    """Calculate certificate status based on maritime regulations and grace periods"""
    if not valid_date:
        return "Unknown"
    
    # Convert valid_date to timezone-aware datetime if it's naive
    if valid_date.tzinfo is None:
        valid_date = valid_date.replace(tzinfo=timezone.utc)
    
    current_date = datetime.now(timezone.utc)
    
    # Maritime certificate grace periods based on international conventions
    # SOLAS, STCW, MLC, MARPOL certificates generally have NO grace period for operation
    # However, some authorities may allow short administrative periods
    
    grace_periods = {
        # Statutory certificates (SOLAS) - NO grace period for operations
        'full term': timedelta(days=0),
        'interim': timedelta(days=0),  # Interim certificates are more strict
        'provisional': timedelta(days=0),
        'short term': timedelta(days=0),
        
        # Some flag states may allow very short administrative extensions
        # but this is rare and vessel should not operate
        'default': timedelta(days=0)
    }
    
    # Get grace period for certificate type
    cert_type_lower = (cert_type or 'default').lower()
    grace_period = grace_periods.get(cert_type_lower, grace_periods['default'])
    
    # Calculate status
    if current_date <= valid_date:
        return "Valid"
    elif current_date <= (valid_date + grace_period):
        # Even within potential grace period, certificate is technically expired
        # Maritime operations should not continue
        return "Expired"
    else:
        return "Expired"

def enhance_certificate_response(cert_dict: dict) -> dict:
    """Enhance certificate response with abbreviation and status"""
    try:
        # Generate certificate abbreviation
        cert_dict['cert_abbreviation'] = generate_certificate_abbreviation(cert_dict.get('cert_name', ''))
        
        # Generate organization abbreviation
        issued_by = cert_dict.get('issued_by', '')
        cert_dict['issued_by_abbreviation'] = generate_organization_abbreviation(issued_by)
        
        # Calculate status
        valid_date = cert_dict.get('valid_date')
        if isinstance(valid_date, str):
            try:
                valid_date = datetime.fromisoformat(valid_date.replace('Z', '+00:00'))
            except:
                valid_date = None
        
        cert_dict['status'] = calculate_certificate_status(valid_date, cert_dict.get('cert_type'))
        
        # Add has_notes flag
        cert_dict['has_notes'] = bool(cert_dict.get('notes'))
        
        return cert_dict
    except Exception as e:
        logger.error(f"Error enhancing certificate response: {e}")
        cert_dict['cert_abbreviation'] = ""
        cert_dict['issued_by_abbreviation'] = ""
        cert_dict['status'] = "Unknown"
        cert_dict['has_notes'] = False
        return cert_dict

def calculate_certificate_similarity(cert1: dict, cert2: dict) -> float:
    """Calculate similarity percentage between two certificates"""
    try:
        # Define fields to compare and their weights
        comparison_fields = {
            'cert_name': 0.25,
            'cert_type': 0.15,
            'cert_no': 0.20,
            'issue_date': 0.15,
            'valid_date': 0.15,
            'issued_by': 0.10
        }
        
        total_weight = 0
        matching_weight = 0
        
        for field, weight in comparison_fields.items():
            val1 = cert1.get(field)
            val2 = cert2.get(field)
            
            # Skip if either value is None or empty
            if not val1 or not val2:
                continue
                
            total_weight += weight
            
            # Compare values based on type
            if field in ['issue_date', 'valid_date']:
                # Date comparison - convert to datetime if string
                try:
                    if isinstance(val1, str):
                        val1 = datetime.fromisoformat(val1.replace('Z', '+00:00'))
                    if isinstance(val2, str):
                        val2 = datetime.fromisoformat(val2.replace('Z', '+00:00'))
                    
                    if val1 == val2:
                        matching_weight += weight
                except:
                    pass
            else:
                # String comparison - case insensitive
                if str(val1).lower().strip() == str(val2).lower().strip():
                    matching_weight += weight
                elif field == 'cert_name':
                    # Partial match for certificate names
                    similarity = calculate_string_similarity(str(val1), str(val2))
                    if similarity > 0.8:  # 80% string similarity
                        matching_weight += weight * similarity
        
        # Calculate percentage
        if total_weight == 0:
            return 0.0
        
        return (matching_weight / total_weight) * 100
        
    except Exception as e:
        logger.error(f"Error calculating certificate similarity: {e}")
        return 0.0

def calculate_string_similarity(str1: str, str2: str) -> float:
    """Calculate string similarity using simple character overlap"""
    try:
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()
        
        if str1 == str2:
            return 1.0
        
        # Simple character-based similarity
        set1 = set(str1.replace(' ', ''))
        set2 = set(str2.replace(' ', ''))
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        if len(union) == 0:
            return 0.0
        
        return len(intersection) / len(union)
        
    except Exception as e:
        logger.error(f"Error calculating string similarity: {e}")
        return 0.0

async def check_certificate_duplicates(analysis_result: dict, ship_id: str) -> list:
    """Check for duplicate certificates in the database"""
    try:
        # Get all certificates for comparison
        all_certificates = await mongo_db.find_all("certificates", {"ship_id": ship_id})
        
        duplicates = []
        
        for existing_cert in all_certificates:
            similarity = calculate_certificate_similarity(analysis_result, existing_cert)
            
            if similarity >= 70.0:  # 70% similarity threshold
                duplicates.append({
                    'certificate': existing_cert,
                    'similarity': similarity
                })
        
        # Sort by similarity descending
        duplicates.sort(key=lambda x: x['similarity'], reverse=True)
        
        return duplicates
        
    except Exception as e:
        logger.error(f"Error checking certificate duplicates: {e}")
        return []

async def check_ship_name_mismatch(analysis_result: dict, current_ship_id: str) -> dict:
    """Check if AI-detected ship name matches current selected ship"""
    try:
        ai_ship_name = analysis_result.get('ship_name', '').strip()
        if not ai_ship_name or ai_ship_name.upper() in ['UNKNOWN_SHIP', 'UNKNOWN SHIP', '']:
            return {"mismatch": False}
        
        # Get current ship
        current_ship = await mongo_db.find_one("ships", {"id": current_ship_id})
        if not current_ship:
            return {"mismatch": False}
        
        current_ship_name = current_ship.get('name', '').strip()
        
        # Compare ship names (case insensitive)
        if ai_ship_name.upper() == current_ship_name.upper():
            return {"mismatch": False}
        
        # Find the AI-detected ship in database
        ai_ship = await mongo_db.find_one("ships", {"name": {"$regex": f"^{ai_ship_name}$", "$options": "i"}})
        
        return {
            "mismatch": True,
            "ai_ship_name": ai_ship_name,
            "current_ship_name": current_ship_name,
            "ai_ship_exists": bool(ai_ship),
            "ai_ship": ai_ship
        }
        
    except Exception as e:
        logger.error(f"Error checking ship name mismatch: {e}")
        return {"mismatch": False}

# Authentication functions
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_current_user(token_data: dict = Depends(verify_token)) -> UserResponse:
    try:
        user = await mongo_db.find_one("users", {"id": token_data["sub"]})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return UserResponse(**user)
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# User permissions checking
def check_permission(required_roles: List[UserRole]):
    def permission_checker(current_user: UserResponse = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return permission_checker

# Auth endpoints
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    try:
        # Find user by username
        user = await mongo_db.find_one("users", {"username": credentials.username})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not bcrypt.checkpw(credentials.password.encode('utf-8'), user["password_hash"].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="Account is disabled")
        
        # Create access token with extended expiry if remember_me is True
        token_expires = timedelta(days=30) if credentials.remember_me else timedelta(hours=JWT_EXPIRATION_HOURS)
        
        # Create token data
        token_data = {
            "sub": user["id"],
            "username": user["username"],
            "role": user["role"],
            "company": user.get("company"),
            "full_name": user.get("full_name", user["username"])
        }
        
        access_token = create_access_token(data=token_data, expires_delta=token_expires)
        
        # Remove password hash from response
        user.pop("password_hash", None)
        
        return LoginResponse(
            access_token=access_token,
            user=UserResponse(**user),
            remember_me=credentials.remember_me
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

# User management endpoints
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    try:
        users = await mongo_db.find_all("users")
        return [UserResponse(**user) for user in users]
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")

@api_router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    try:
        # Check if username already exists
        existing_user = await mongo_db.find_one("users", {"username": user_data.username})
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Hash password
        password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user document
        user_dict = user_data.dict()
        user_dict.pop("password")  # Remove plain password
        user_dict["password_hash"] = password_hash
        user_dict["id"] = str(uuid.uuid4())
        user_dict["created_at"] = datetime.now(timezone.utc)
        
        # Create user in database
        await mongo_db.create("users", user_dict)
        
        return UserResponse(**user_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")
@api_router.get("/users/filtered", response_model=List[UserResponse])
async def get_filtered_users(
    company: Optional[str] = None,
    department: Optional[str] = None, 
    ship: Optional[str] = None,
    sort_by: Optional[str] = "full_name",
    sort_order: Optional[str] = "asc",
    current_user: UserResponse = Depends(check_permission([UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    """Get filtered and sorted users with query parameters"""
    try:
        # Build filter criteria
        filter_criteria = {}
        
        if company:
            filter_criteria["company"] = company
        if department:
            filter_criteria["department"] = department
        if ship:
            filter_criteria["ship"] = ship
        
        # For Manager role, filter by same company only
        if current_user.role == UserRole.MANAGER:
            filter_criteria["company"] = current_user.company
        
        # Get users from database
        users = await mongo_db.find_all("users", filter_criteria)
        
        # Sort users
        valid_sort_fields = ["full_name", "company", "department", "role", "ship", "created_at"]
        if sort_by not in valid_sort_fields:
            sort_by = "full_name"
        
        reverse_sort = sort_order.lower() == "desc"
        
        def safe_get(user, field):
            value = user.get(field, "")
            return value if value is not None else ""
        
        users.sort(key=lambda user: safe_get(user, sort_by), reverse=reverse_sort)
        
        return [UserResponse(**user) for user in users]
        
    except Exception as e:
        logger.error(f"Error fetching filtered users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch filtered users")

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    try:
        # Find existing user
        existing_user = await mongo_db.find_one("users", {"id": user_id})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare update data
        update_data = {}
        for field, value in user_data.dict(exclude_unset=True).items():
            if field == "password" and value:
                # Hash new password
                update_data["password_hash"] = bcrypt.hashpw(value.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            else:
                update_data[field] = value
        
        if update_data:  # Only update if there's data to update
            await mongo_db.update("users", {"id": user_id}, update_data)
        
        # Get updated user
        updated_user = await mongo_db.find_one("users", {"id": user_id})
        return UserResponse(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    try:
        # Check if user exists
        existing_user = await mongo_db.find_one("users", {"id": user_id})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Don't allow deleting yourself
        if user_id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        await mongo_db.delete("users", {"id": user_id})
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")

# Company endpoints
@api_router.get("/companies", response_model=List[CompanyResponse])
async def get_companies(current_user: UserResponse = Depends(get_current_user)):
    try:
        companies = await mongo_db.find_all("companies")
        
        # Fix companies that don't have 'name' field but have 'name_en' or 'name_vn'
        fixed_companies = []
        for company in companies:
            if 'name' not in company:
                # Use name_en if available, otherwise name_vn, otherwise create default
                company['name'] = company.get('name_en') or company.get('name_vn') or 'Unknown Company'
            fixed_companies.append(company)
        
        return [CompanyResponse(**company) for company in fixed_companies]
    except Exception as e:
        logger.error(f"Error fetching companies: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch companies")

@api_router.post("/companies", response_model=CompanyResponse)
async def create_company(company_data: CompanyCreate, current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    try:
        # Create company document
        company_dict = company_data.dict()
        company_dict["id"] = str(uuid.uuid4())
        company_dict["created_at"] = datetime.now(timezone.utc)
        
        # Ensure legacy 'name' field for backward compatibility
        if not company_dict.get('name'):
            company_dict['name'] = company_dict.get('name_en') or company_dict.get('name_vn') or 'Unknown Company'
        
        await mongo_db.create("companies", company_dict)
        return CompanyResponse(**company_dict)
        
    except Exception as e:
        logger.error(f"Error creating company: {e}")
        raise HTTPException(status_code=500, detail="Failed to create company")

@api_router.put("/companies/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: str, company_data: CompanyUpdate, current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    try:
        # Check if company exists
        existing_company = await mongo_db.find_one("companies", {"id": company_id})
        if not existing_company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Prepare update data
        update_data = company_data.dict(exclude_unset=True)
        
        # Handle system_expiry field - convert string to datetime if needed
        if 'system_expiry' in update_data and update_data['system_expiry']:
            if isinstance(update_data['system_expiry'], str):
                try:
                    update_data['system_expiry'] = datetime.fromisoformat(update_data['system_expiry'].replace('Z', '+00:00'))
                except ValueError:
                    # If parsing fails, keep as string and let MongoDB handle it
                    pass
        
        # Update legacy 'name' field for backward compatibility
        if 'name_en' in update_data or 'name_vn' in update_data:
            name_en = update_data.get('name_en') or existing_company.get('name_en')
            name_vn = update_data.get('name_vn') or existing_company.get('name_vn')
            update_data['name'] = name_en or name_vn or 'Unknown Company'
        
        if update_data:  # Only update if there's data to update
            await mongo_db.update("companies", {"id": company_id}, update_data)
        
        # Get updated company
        updated_company = await mongo_db.find_one("companies", {"id": company_id})
        
        # Fix companies that don't have 'name' field but have 'name_en' or 'name_vn'
        if 'name' not in updated_company:
            updated_company['name'] = updated_company.get('name_en') or updated_company.get('name_vn') or 'Unknown Company'
        
        return CompanyResponse(**updated_company)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company: {e}")
        raise HTTPException(status_code=500, detail="Failed to update company")

# Ship endpoints
@api_router.get("/ships", response_model=List[ShipResponse])
async def get_ships(current_user: UserResponse = Depends(get_current_user)):
    try:
        ships = await mongo_db.find_all("ships")
        return [ShipResponse(**ship) for ship in ships]
    except Exception as e:
        logger.error(f"Error fetching ships: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ships")

@api_router.post("/ships", response_model=ShipResponse)
async def create_ship(ship_data: ShipCreate, current_user: UserResponse = Depends(check_permission([UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    try:
        # Create ship document
        ship_dict = ship_data.dict()
        ship_dict["id"] = str(uuid.uuid4())
        ship_dict["created_at"] = datetime.now(timezone.utc)
        
        await mongo_db.create("ships", ship_dict)
        return ShipResponse(**ship_dict)
        
    except Exception as e:
        logger.error(f"Error creating ship: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ship")

@api_router.get("/ships/{ship_id}", response_model=ShipResponse)
async def get_ship(ship_id: str, current_user: UserResponse = Depends(get_current_user)):
    try:
        ship = await mongo_db.find_one("ships", {"id": ship_id})
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        return ShipResponse(**ship)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ship: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ship")

@api_router.put("/ships/{ship_id}", response_model=ShipResponse)
async def update_ship(ship_id: str, ship_data: ShipUpdate, current_user: UserResponse = Depends(check_permission([UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    try:
        # Check if ship exists
        existing_ship = await mongo_db.find_one("ships", {"id": ship_id})
        if not existing_ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Prepare update data
        update_data = ship_data.dict(exclude_unset=True)
        
        if update_data:  # Only update if there's data to update
            await mongo_db.update("ships", {"id": ship_id}, update_data)
        
        # Get updated ship
        updated_ship = await mongo_db.find_one("ships", {"id": ship_id})
        return ShipResponse(**updated_ship)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ship: {e}")
        raise HTTPException(status_code=500, detail="Failed to update ship")

@api_router.delete("/ships/{ship_id}")
async def delete_ship(ship_id: str, current_user: UserResponse = Depends(check_permission([UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    try:
        # Check if ship exists
        existing_ship = await mongo_db.find_one("ships", {"id": ship_id})
        if not existing_ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        await mongo_db.delete("ships", {"id": ship_id})
        return {"message": "Ship deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ship: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete ship")

# Certificate endpoints
@api_router.get("/ships/{ship_id}/certificates", response_model=List[CertificateResponse])
async def get_ship_certificates(ship_id: str, current_user: UserResponse = Depends(get_current_user)):
    try:
        certificates = await mongo_db.find_all("certificates", {"ship_id": ship_id})
        # Enhance each certificate with abbreviation and status
        enhanced_certificates = [enhance_certificate_response(cert) for cert in certificates]
        return [CertificateResponse(**cert) for cert in enhanced_certificates]
    except Exception as e:
        logger.error(f"Error fetching certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch certificates")

@api_router.post("/certificates", response_model=CertificateResponse)
async def create_certificate(cert_data: CertificateCreate, current_user: UserResponse = Depends(check_permission([UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    try:
        # Create certificate document
        cert_dict = cert_data.dict()
        cert_dict["id"] = str(uuid.uuid4())
        cert_dict["created_at"] = datetime.now(timezone.utc)
        
        await mongo_db.create("certificates", cert_dict)
        
        # Enhance response with abbreviation and status
        enhanced_cert = enhance_certificate_response(cert_dict)
        return CertificateResponse(**enhanced_cert)
        
    except Exception as e:
        logger.error(f"Error creating certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to create certificate")

@api_router.put("/certificates/{cert_id}", response_model=CertificateResponse)
async def update_certificate(cert_id: str, cert_data: CertificateUpdate, current_user: UserResponse = Depends(check_permission([UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    try:
        # Check if certificate exists
        existing_cert = await mongo_db.find_one("certificates", {"id": cert_id})
        if not existing_cert:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Prepare update data
        update_data = cert_data.dict(exclude_unset=True)
        
        if update_data:  # Only update if there's data to update
            await mongo_db.update("certificates", {"id": cert_id}, update_data)
        
        # Get updated certificate
        updated_cert = await mongo_db.find_one("certificates", {"id": cert_id})
        enhanced_cert = enhance_certificate_response(updated_cert)
        return CertificateResponse(**enhanced_cert)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to update certificate")

@api_router.delete("/certificates/{cert_id}")
async def delete_certificate(cert_id: str, current_user: UserResponse = Depends(check_permission([UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    try:
        # Check if certificate exists
        existing_cert = await mongo_db.find_one("certificates", {"id": cert_id})
        if not existing_cert:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        await mongo_db.delete("certificates", {"id": cert_id})
        return {"message": "Certificate deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting certificate: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete certificate")

# General certificates endpoint
@api_router.get("/certificates", response_model=List[CertificateResponse])
async def get_all_certificates(current_user: UserResponse = Depends(get_current_user)):
    """Get all certificates with filtering"""
    try:
        certificates = await mongo_db.find_all("certificates", {})
        # Enhance each certificate with abbreviation and status
        enhanced_certificates = [enhance_certificate_response(cert) for cert in certificates]
        return [CertificateResponse(**cert) for cert in enhanced_certificates]
    except Exception as e:
        logger.error(f"Error fetching all certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch certificates")
# Ship Survey Status endpoints
@api_router.get("/ships/{ship_id}/survey-status", response_model=List[ShipSurveyStatusResponse])
async def get_ship_survey_status(ship_id: str, current_user: UserResponse = Depends(get_current_user)):
    try:
        survey_statuses = await mongo_db.find_all("ship_survey_status", {"ship_id": ship_id})
        return [ShipSurveyStatusResponse(**status) for status in survey_statuses]
    except Exception as e:
        logger.error(f"Error fetching ship survey status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ship survey status")

@api_router.post("/ships/{ship_id}/survey-status", response_model=ShipSurveyStatusResponse)
async def create_ship_survey_status(ship_id: str, status_data: ShipSurveyStatusCreate, current_user: UserResponse = Depends(check_permission([UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    try:
        # Create survey status document
        status_dict = status_data.dict()
        status_dict["id"] = str(uuid.uuid4())
        status_dict["created_at"] = datetime.now(timezone.utc)
        
        await mongo_db.create("ship_survey_status", status_dict)
        return ShipSurveyStatusResponse(**status_dict)
        
    except Exception as e:
        logger.error(f"Error creating ship survey status: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ship survey status")

# Settings endpoints
@api_router.get("/settings")
async def get_settings(current_user: UserResponse = Depends(get_current_user)):
    try:
        settings = await mongo_db.find_one("settings", {"id": "system_settings"})
        if not settings:
            # Return default settings
            return {
                "company_name": "",
                "logo_url": None,
                "theme": "default"
            }
        return settings
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch settings")

@api_router.post("/settings/upload-logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create company logos directory
        logo_dir = UPLOAD_DIR / "company_logos"
        logo_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'png'
        filename = f"logo_{uuid.uuid4()}.{file_extension}"
        file_path = logo_dir / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Update settings
        logo_url = f"/uploads/company_logos/{filename}"
        settings_data = {
            "id": "system_settings",
            "logo_url": logo_url,
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Update or create settings
        existing_settings = await mongo_db.find_one("settings", {"id": "system_settings"})
        if existing_settings:
            await mongo_db.update("settings", {"id": "system_settings"}, {"logo_url": logo_url})
        else:
            await mongo_db.create("settings", settings_data)
        
        return {"logo_url": logo_url, "message": "Logo uploaded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading logo: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload logo")

# AI Configuration endpoints
@api_router.get("/ai-config", response_model=AIConfigResponse)
async def get_ai_config(current_user: UserResponse = Depends(get_current_user)):
    try:
        config = await mongo_db.find_one("ai_config", {"id": "system_ai"})
        if not config:
            # Return default config
            return AIConfigResponse(provider="openai", model="gpt-4")
        
        # Don't expose the API key
        return AIConfigResponse(
            provider=config.get("provider", "openai"),
            model=config.get("model", "gpt-4")
        )
    except Exception as e:
        logger.error(f"Error fetching AI config: {e}")
        # Return default on error
        return AIConfigResponse(provider="openai", model="gpt-4")

@api_router.post("/ai-config")
async def update_ai_config(
    config: AIConfig,
    current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    try:
        config_data = {
            "id": "system_ai",
            "provider": config.provider,
            "model": config.model,
            "api_key": config.api_key,
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Update or create AI config
        existing_config = await mongo_db.find_one("ai_config", {"id": "system_ai"})
        if existing_config:
            await mongo_db.update("ai_config", {"id": "system_ai"}, config_data)
        else:
            await mongo_db.create("ai_config", config_data)
        
        return {"message": "AI configuration updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating AI config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update AI configuration")

# File upload endpoints
@api_router.post("/certificates/check-duplicates-and-mismatch")
async def check_duplicates_and_mismatch(
    analysis_data: dict,
    current_user: UserResponse = Depends(check_permission([UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    """Check for certificate duplicates and ship name mismatch before processing"""
    try:
        ship_id = analysis_data.get('ship_id')
        analysis_result = analysis_data.get('analysis_result', {})
        
        if not ship_id or not analysis_result:
            raise HTTPException(status_code=400, detail="Missing ship_id or analysis_result")
        
        # Check for duplicates
        duplicates = await check_certificate_duplicates(analysis_result, ship_id)
        
        # Check for ship name mismatch
        ship_mismatch = await check_ship_name_mismatch(analysis_result, ship_id)
        
        return {
            "duplicates": duplicates,
            "ship_mismatch": ship_mismatch,
            "has_issues": len(duplicates) > 0 or ship_mismatch.get("mismatch", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking duplicates and mismatch: {e}")
        raise HTTPException(status_code=500, detail=f"Check failed: {str(e)}")

@api_router.post("/certificates/process-with-resolution")
async def process_certificate_with_resolution(
    resolution_data: dict,
    current_user: UserResponse = Depends(check_permission([UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    """Process certificate upload with user resolution for duplicates and mismatch"""
    try:
        analysis_result = resolution_data.get('analysis_result', {})
        upload_result = resolution_data.get('upload_result', {})
        ship_id = resolution_data.get('ship_id')
        
        # Resolution decisions
        duplicate_resolution = resolution_data.get('duplicate_resolution')  # 'overwrite' or 'cancel'
        duplicate_target_id = resolution_data.get('duplicate_target_id')
        
        mismatch_resolution = resolution_data.get('mismatch_resolution')  # 'use_ai_ship' or 'use_current_ship'
        target_ship_id = resolution_data.get('target_ship_id', ship_id)
        
        # Handle duplicate resolution
        if duplicate_resolution == 'cancel':
            return {
                "status": "cancelled",
                "message": "Certificate upload cancelled by user"
            }
        elif duplicate_resolution == 'overwrite' and duplicate_target_id:
            # Delete the existing certificate
            await mongo_db.delete("certificates", {"id": duplicate_target_id})
            logger.info(f"Overwritten existing certificate: {duplicate_target_id}")
        
        # Prepare certificate data
        notes = None
        if mismatch_resolution == 'use_current_ship':
            # Add reference note when saving to current ship despite mismatch
            ai_ship_name = analysis_result.get('ship_name', 'Unknown Ship')
            notes = f"Giấy chứng nhận này để tham khảo, không phải của tàu này. Ship name từ AI: {ai_ship_name}"
        
        # Create certificate record
        cert_result = await create_certificate_from_analysis_with_notes(
            analysis_result, upload_result, current_user, target_ship_id, notes
        )
        
        # Update ship survey status if relevant information exists
        await update_ship_survey_status(analysis_result, current_user)
        
        return {
            "status": "success",
            "certificate": cert_result,
            "resolution": {
                "duplicate_resolution": duplicate_resolution,
                "mismatch_resolution": mismatch_resolution,
                "notes_added": bool(notes)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing certificate with resolution: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@api_router.post("/certificates/upload-multi-files")
async def upload_multi_files(
    files: List[UploadFile] = File(...),
    current_user: UserResponse = Depends(check_permission([UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    """Upload multiple certificate files with AI analysis and Google Drive integration"""
    try:
        results = []
        
        # Get AI configuration
        ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
        if not ai_config_doc:
            raise HTTPException(status_code=500, detail="AI configuration not found. Please configure AI settings first.")
        
        ai_config = {
            "provider": ai_config_doc.get("provider", "openai"),
            "model": ai_config_doc.get("model", "gpt-4"),
            "api_key": ai_config_doc.get("api_key")
        }
        
        # Get Google Drive configuration
        gdrive_config_doc = await mongo_db.find_one("gdrive_config", {"id": "system_gdrive"})
        if not gdrive_config_doc:
            raise HTTPException(status_code=500, detail="Google Drive not configured. Please configure Google Drive first.")
        
        for file in files:
            try:
                # Read file content
                file_content = await file.read()
                
                # Check file size (150MB limit)
                if len(file_content) > 150 * 1024 * 1024:
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": "File size exceeds 150MB limit"
                    })
                    continue
                
                # Analyze document with AI
                analysis_result = await analyze_document_with_ai(
                    file_content, file.filename, file.content_type, ai_config
                )
                
                logger.info(f"AI Analysis results for {file.filename}:")
                for key, value in analysis_result.items():
                    logger.info(f"  {key}: {repr(value)}")
                
                # Upload to Google Drive and create folder structure
                upload_result = await upload_file_to_gdrive_with_analysis(
                    file_content, file.filename, analysis_result, gdrive_config_doc, current_user
                )
                
                # Create certificate record if classified as certificate
                cert_result = None
                if analysis_result.get("category") == "certificates":
                    # Find ship by name from AI analysis
                    ship_name = analysis_result.get("ship_name", "Unknown_Ship")
                    ship = None
                    if isinstance(ship_name, str) and ship_name.strip():
                        ship = await mongo_db.find_one("ships", {"name": {"$regex": f"^{ship_name}$", "$options": "i"}})
                    
                    if ship:
                        cert_result = await create_certificate_from_analysis_with_notes(
                            analysis_result, upload_result, current_user, ship['id'], None
                        )
                    else:
                        logger.warning(f"Ship not found for certificate: {ship_name}")
                        cert_result = {"success": False, "error": f"Ship '{ship_name}' not found"}
                
                # Update ship survey status if relevant information exists
                await update_ship_survey_status(analysis_result, current_user)
                
                # Track usage
                await track_ai_usage(current_user, "document_analysis", ai_config)
                
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "analysis": analysis_result,
                    "upload": upload_result,
                    "certificate": cert_result
                })
                
            except Exception as file_error:
                logger.error(f"Error processing file {file.filename}: {file_error}")
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": str(file_error)
                })
        
        return {"results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-file upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def analyze_document_with_ai(file_content: bytes, filename: str, content_type: str, ai_config: dict) -> dict:
    """Analyze document using configured AI to extract information and classify"""
    try:
        # Use system AI configuration instead of hardcoded Emergent LLM
        provider = ai_config.get("provider", "openai").lower()
        model = ai_config.get("model", "gpt-4")
        api_key = ai_config.get("api_key")
        
        if not api_key:
            logger.error("No API key found in AI configuration")
            return classify_by_filename(filename)
        
        # Create AI analysis prompt
        analysis_prompt = f"""
Analyze this maritime document ({filename}) and extract the following information:

1. DOCUMENT CLASSIFICATION - Classify into one of these categories:
   - certificates: Maritime certificates issued by Classification Society, Flag State, Port State, or Maritime Authorities. 
     Examples: Safety Management Certificate, IAPP Certificate, IOPP Certificate, Load Line Certificate, 
     Radio Survey Certificate, Safety Construction Certificate, Tonnage Certificate, etc.
   - test_reports: Test/maintenance reports for lifesaving, firefighting, radio equipment, safety systems
   - survey_reports: Survey reports issued by Classification Society (annual, intermediate, special surveys)
   - drawings_manuals: DWG files, technical drawings, equipment manuals, ship plans
   - other_documents: Documents not fitting above categories (crew lists, commercial documents, etc.)

2. SHIP INFORMATION - Extract ship details:
   - ship_name: Full name of the vessel (look for "Ship Name", "Vessel Name", "M.V.", "S.S.", etc.)
   
3. CERTIFICATE INFORMATION (if category is 'certificates'):
   - cert_name: Full certificate name (e.g., "International Air Pollution Prevention Certificate")
   - cert_type: Certificate type (Interim, Provisional, Short term, Full Term, Initial, etc.)
   - cert_no: Certificate number or reference number
   - issue_date: Issue date (convert to ISO format YYYY-MM-DD)
   - valid_date: Valid until/expiry date (convert to ISO format YYYY-MM-DD)
   - last_endorse: Last endorsement date (ISO format YYYY-MM-DD, if available)
   - next_survey: Next survey date (ISO format YYYY-MM-DD, if available)
   - issued_by: Issuing authority/organization - Be very thorough in identifying this. Look for:
     * Classification Societies: DNV GL, ABS, Lloyd's Register, Bureau Veritas, RINA, ClassNK, CCS, KR, RS, etc.
     * Flag State Authorities: Panama Maritime Authority, Liberia Maritime Authority, Marshall Islands Maritime Authority, etc.
     * Port State Control Authorities: Various national maritime administrations
     * Survey Companies: Maritime survey and inspection companies
     * Government Agencies: Coast Guard, Maritime Safety Administration, etc.
     * Look for signatures, letterheads, company stamps, contact information
     * Check for phrases like "Issued by", "Certified by", "Authorized by", "On behalf of"

4. SURVEY STATUS INFORMATION (if relevant):
   IMPORTANT: Always include this section as 'survey_info' in your JSON response when analyzing certificates.
   - certificate_type: CLASS, STATUTORY, AUDITS, Bottom Surveys
   - survey_type: Annual, Intermediate, Renewal, Change of RO, Approval, Initial Audit
   - issuance_date: When certificate was issued
   - expiration_date: When certificate expires
   - renewal_range_start: Renewal range start date
   - renewal_range_end: Renewal range end date
   - due_dates: Any due dates mentioned (as array)

IMPORTANT CLASSIFICATION RULES:
- ANY document with "Certificate" in the name AND maritime/ship information = "certificates"
- Documents from Classification Societies (DNV GL, ABS, Lloyd's Register, etc.) = usually "certificates" or "survey_reports"
- Flag State documents (Panama, Liberia, Marshall Islands, etc.) = usually "certificates"
- IAPP, IOPP, SMC, DOC, ISM, ISPS certificates = "certificates"

CRITICAL: Pay special attention to identifying the "issued_by" organization. This is crucial information that must be extracted accurately by examining:
- Document headers and letterheads
- Signature blocks
- Official stamps or seals
- Contact information
- Any text indicating the certifying authority

Return response as JSON format. If information is not found, return null for that field.
Mark any uncertain extractions in a 'confidence' field (high/medium/low).

MANDATORY: For certificates, ALWAYS include a 'survey_info' section with the survey status information, even if you need to infer some values from the certificate dates.

EXAMPLE OUTPUT:
{{
  "category": "certificates",
  "ship_name": "BROTHER 36",
  "cert_name": "International Air Pollution Prevention Certificate",
  "cert_type": "Full Term",
  "cert_no": "PM242838",
  "issue_date": "2024-12-10",
  "valid_date": "2028-03-18",
  "issued_by": "Panama Maritime Documentation Services Inc (on behalf of Panama Maritime Authority)",
  "confidence": "high",
  "survey_info": {{
    "certificate_type": "STATUTORY",
    "survey_type": "Renewal",
    "issuance_date": "2024-12-10",
    "expiration_date": "2028-03-18",
    "renewal_range_start": "2027-09-18",
    "renewal_range_end": "2029-03-18",
    "due_dates": ["2025-03-18", "2026-03-18", "2027-03-18"]
  }}
}}
"""

        # Use different AI providers based on configuration
        if provider == "openai":
            return await analyze_with_openai(file_content, filename, content_type, api_key, model, analysis_prompt)
        elif provider == "anthropic":
            return await analyze_with_anthropic(file_content, filename, content_type, api_key, model, analysis_prompt)
        elif provider == "google":
            return await analyze_with_google(file_content, filename, content_type, api_key, model, analysis_prompt)
        elif provider == "emergent" or not provider:
            # Fallback to Emergent LLM if provider is emergent or not specified
            return await analyze_with_emergent_llm(file_content, filename, content_type, api_key, analysis_prompt)
        else:
            logger.error("Unsupported AI provider: " + provider)
            return classify_by_filename(filename)
            
    except Exception as e:
        logger.error("AI document analysis failed: " + str(e))
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
        # Validate ship_name
        if not ship_name or not isinstance(ship_name, str) or ship_name.strip() == "":
            ship_name = "Unknown_Ship"
        else:
            ship_name = ship_name.strip()
        
        auth_method = gdrive_config.get("auth_method", "service_account")
        
        if auth_method == "apps_script":
            # Use Apps Script API
            return await create_folders_via_apps_script(gdrive_config, ship_name)
        else:
            # Legacy service account method
            logger.warning("Service account method deprecated, falling back to Apps Script")
            return await create_folders_via_apps_script(gdrive_config, ship_name)
            
    except Exception as e:
        logger.error(f"Folder creation failed: {e}")
        return {"success": False, "error": str(e)}

async def create_folders_via_apps_script(gdrive_config: dict, ship_name: str) -> dict:
    """Create folders using Google Apps Script"""
    try:
        script_url = gdrive_config.get("apps_script_url")
        if not script_url:
            raise Exception("Apps Script URL not configured")
            
        payload = {
            "action": "create_folder_structure",
            "ship_name": ship_name
        }
        
        response = requests.post(script_url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success"):
            logger.info(f"Successfully created folder structure for {ship_name}")
            return {
                "success": True,
                "ship_folder_id": result.get("ship_folder_id"),
                "subfolders": result.get("subfolders", {})
            }
        else:
            logger.error(f"Apps Script folder creation failed: {result.get('error')}")
            return {"success": False, "error": result.get("error", "Unknown error")}
            
    except Exception as e:
        logger.error(f"Apps Script folder creation failed: {e}")
        return {"success": False, "error": str(e)}

async def upload_file_to_category_folder(gdrive_config: dict, file_content: bytes, filename: str, ship_name: str, category: str) -> dict:
    """Upload file to specific category folder"""
    try:
        auth_method = gdrive_config.get("auth_method", "service_account")
        
        if auth_method == "apps_script":
            return await upload_file_via_apps_script(gdrive_config, file_content, filename, ship_name, category)
        else:
            logger.warning("Service account method deprecated, falling back to Apps Script")
            return await upload_file_via_apps_script(gdrive_config, file_content, filename, ship_name, category)
            
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        return {"success": False, "error": str(e)}

async def upload_file_via_apps_script(gdrive_config: dict, file_content: bytes, filename: str, ship_name: str, category: str) -> dict:
    """Upload file using Google Apps Script"""
    try:
        script_url = gdrive_config.get("apps_script_url")
        if not script_url:
            raise Exception("Apps Script URL not configured")
        
        # Map category to folder name
        category_mapping = {
            "certificates": "Certificates",
            "test_reports": "Test Reports", 
            "survey_reports": "Survey Reports",
            "drawings_manuals": "Drawings & Manuals",
            "other_documents": "Other Documents"
        }
        
        folder_name = category_mapping.get(category, "Other Documents")
        
        # Encode file content to base64
        import base64
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        payload = {
            "action": "upload_file",
            "ship_name": ship_name,
            "folder_name": folder_name,
            "filename": filename,
            "file_content": file_base64
        }
        
        response = requests.post(script_url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success"):
            logger.info(f"Successfully uploaded {filename} to {ship_name}/{folder_name}")
            return {
                "success": True,
                "file_id": result.get("file_id"),
                "folder_path": f"{ship_name}/{folder_name}"
            }
        else:
            logger.error(f"Apps Script file upload failed: {result.get('error')}")
            return {"success": False, "error": result.get("error", "Unknown error")}
            
    except Exception as e:
        logger.error(f"Apps Script file upload failed: {e}")
        return {"success": False, "error": str(e)}

async def upload_file_to_gdrive_with_analysis(file_content: bytes, filename: str, analysis_result: dict, gdrive_config: dict, current_user) -> dict:
    """Upload file to Google Drive based on AI analysis"""
    try:
        ship_name = analysis_result.get("ship_name", "Unknown_Ship")
        category = analysis_result.get("category", "other_documents")
        
        # Create folder structure if needed
        folder_result = await create_ship_folder_structure(gdrive_config, ship_name)
        
        # Upload file to appropriate category folder
        upload_result = await upload_file_to_category_folder(
            gdrive_config, file_content, filename, ship_name, category
        )
        
        return upload_result
        
    except Exception as e:
        logger.error(f"Google Drive upload with analysis failed: {e}")
        return {"success": False, "error": str(e)}


async def create_certificate_from_analysis_with_notes(analysis_result: dict, upload_result: dict, current_user, ship_id: str, notes: str = None) -> dict:
    """Create certificate record from AI analysis results with support for notes and specific ship_id"""
    try:
        # Get ship by ID
        ship = await mongo_db.find_one("ships", {"id": ship_id})
        
        if not ship:
            logger.warning(f"Ship not found with ID: {ship_id}")
            return {"success": False, "error": f"Ship with ID '{ship_id}' not found"}
        
        # Create certificate data
        cert_data = {
            'id': str(uuid.uuid4()),
            'ship_id': ship_id,
            'cert_name': analysis_result.get('cert_name', 'Unknown Certificate'),
            'cert_type': analysis_result.get('cert_type', 'Full Term'),
            'cert_no': analysis_result.get('cert_no', 'Unknown'),
            'issue_date': parse_date_string(analysis_result.get('issue_date')),
            'valid_date': parse_date_string(analysis_result.get('valid_date')),
            'last_endorse': parse_date_string(analysis_result.get('last_endorse')),
            'next_survey': parse_date_string(analysis_result.get('next_survey')),
            'issued_by': analysis_result.get('issued_by'),
            'category': analysis_result.get('category', 'certificates'),
            'file_uploaded': upload_result.get('success', False),
            'google_drive_file_id': upload_result.get('file_id'),
            'google_drive_folder_path': upload_result.get('folder_path'),
            'file_name': analysis_result.get('filename'),
            'ship_name': ship.get('name'),
            'notes': notes,  # Add notes field
            'created_at': datetime.now(timezone.utc)
        }
        
        # Remove None values
        cert_data = {k: v for k, v in cert_data.items() if v is not None}
        
        await mongo_db.create("certificates", cert_data)
        
        cert_dict = dict(cert_data)
        logger.info(f"Certificate created successfully: {cert_dict.get('cert_name')} for ship {ship.get('name')} with notes: {bool(notes)}")
        
        return cert_dict
        
    except Exception as e:
        logger.error(f"Certificate creation from analysis with notes failed: {e}")
        raise

async def update_ship_survey_status(analysis_result: dict, current_user) -> None:
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
    """Parse date string to datetime object with enhanced error handling"""
    if not date_str or date_str in ['', 'null', 'None', 'N/A']:
        return None
    
    try:
        # Handle various date formats
        date_formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%d-%m-%Y',
            '%Y/%m/%d'
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(str(date_str), fmt)
                return parsed_date.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        
        # If no format works, log and return None
        logger.warning(f"Could not parse date: {date_str}")
        return None
        
    except Exception as e:
        logger.error(f"Date parsing error for '{date_str}': {e}")
        return None

async def analyze_with_emergent_llm(file_content: bytes, filename: str, content_type: str, api_key: str, analysis_prompt: str) -> dict:
    """Analyze document using Emergent LLM"""
    try:
        # Initialize LLM chat with required parameters
        chat = LlmChat(
            api_key=api_key,
            session_id=f"cert_analysis_{uuid.uuid4().hex[:8]}",
            system_message="You are a maritime document analysis expert. Analyze documents and extract certificate information in JSON format."
        )
        
        # Create temporary file for LLM analysis
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Create file content for LLM
            file_obj = FileContentWithMimeType(
                mime_type=content_type,
                file_path=temp_file_path
            )
        
        # Create user message with file
        user_message = UserMessage(content=analysis_prompt, files=[file_obj])
        
        # Get AI response
        response = await chat.achat([user_message])
        
        logger.info(f"AI Response type: {type(response)}")
        logger.info(f"AI Response content (first 200 chars): {str(response)[:200]}")
        
        # Parse JSON response
        response_text = str(response)
        
        # Clean up response (remove markdown code blocks if present)
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.rfind("```")
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.rfind("```")
            response_text = response_text[start:end].strip()
        
            try:
                parsed_response = json.loads(response_text)
                return parsed_response
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                logger.error(f"Raw response: {response_text}")
                return classify_by_filename(filename)
        
        finally:
            # Clean up temporary file
            import os
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    except Exception as e:
        logger.error(f"Emergent LLM analysis failed: {e}")
        return classify_by_filename(filename)

async def analyze_with_openai(file_content: bytes, filename: str, content_type: str, api_key: str, model: str, analysis_prompt: str) -> dict:
    """Analyze document using OpenAI"""
    # Implementation for OpenAI API calls
    return classify_by_filename(filename)

async def analyze_with_anthropic(file_content: bytes, filename: str, content_type: str, api_key: str, model: str, analysis_prompt: str) -> dict:
    """Analyze document using Anthropic"""
    # Implementation for Anthropic API calls
    return classify_by_filename(filename)

async def analyze_with_google(file_content: bytes, filename: str, content_type: str, api_key: str, model: str, analysis_prompt: str) -> dict:
    """Analyze document using Google"""
    # Implementation for Google API calls
    return classify_by_filename(filename)

async def track_ai_usage(current_user, operation_type: str, ai_config: dict):
    """Track AI usage for analytics"""
    try:
        usage_data = {
            'id': str(uuid.uuid4()),
            'user_id': current_user.id,
            'operation_type': operation_type,
            'provider': ai_config.get('provider'),
            'model': ai_config.get('model'),
            'timestamp': datetime.now(timezone.utc)
        }
        
        await mongo_db.create("usage_tracking", usage_data)
        
    except Exception as e:
        logger.error(f"Usage tracking failed: {e}")
        # Don't raise exception for usage tracking failures

# Google Drive endpoints
@api_router.get("/gdrive/config")
async def get_gdrive_config(current_user: UserResponse = Depends(get_current_user)):
    try:
        config = await mongo_db.find_one("gdrive_config", {"id": "system_gdrive"})
        if not config:
            return {
                "configured": False, 
                "auth_method": None,
                "folder_id": None,
                "apps_script_url": None
            }
        
        # Don't expose sensitive data
        return {
            "configured": True,
            "auth_method": config.get("auth_method"),
            "folder_id": config.get("folder_id"),
            "apps_script_url": config.get("apps_script_url") is not None
        }
    except Exception as e:
        logger.error(f"Error fetching Google Drive config: {e}")
        return {"configured": False, "error": str(e)}

@api_router.get("/gdrive/file/{file_id}/view")
async def get_gdrive_file_view_url(
    file_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get Google Drive file view URL for opening in new window"""
    try:
        # Get Google Drive configuration
        gdrive_config = await mongo_db.find_one("gdrive_config", {"id": "system_gdrive"})
        if not gdrive_config:
            raise HTTPException(status_code=500, detail="Google Drive not configured")
        
        auth_method = gdrive_config.get("auth_method", "apps_script")
        
        if auth_method == "apps_script":
            script_url = gdrive_config.get("apps_script_url")
            if not script_url:
                raise HTTPException(status_code=500, detail="Apps Script URL not configured")
            
            try:
                # Get file view URL from Apps Script
                payload = {
                    "action": "get_file_view_url",
                    "file_id": file_id
                }
                
                response = requests.post(script_url, json=payload, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("success"):
                    view_url = result.get("view_url")
                    if view_url:
                        return {"success": True, "view_url": view_url}
                    else:
                        # Fallback to standard Google Drive view URL
                        view_url = f"https://drive.google.com/file/d/{file_id}/view"
                        return {"success": True, "view_url": view_url}
                else:
                    # Fallback to standard Google Drive view URL
                    view_url = f"https://drive.google.com/file/d/{file_id}/view"
                    return {"success": True, "view_url": view_url}
                    
            except Exception as e:
                logger.error(f"Apps Script file view URL failed: {e}")
                # Fallback to standard Google Drive view URL
                view_url = f"https://drive.google.com/file/d/{file_id}/view"
                return {"success": True, "view_url": view_url}
        else:
            # Fallback to standard Google Drive view URL
            view_url = f"https://drive.google.com/file/d/{file_id}/view"
            return {"success": True, "view_url": view_url}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Google Drive file view URL: {e}")
        # Final fallback
        view_url = f"https://drive.google.com/file/d/{file_id}/view"
        return {"success": True, "view_url": view_url}

@api_router.post("/gdrive/config")
async def update_gdrive_config(
    config_data: dict,
    current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    try:
        config_dict = {
            "id": "system_gdrive",
            "auth_method": config_data.get("auth_method", "apps_script"),
            "folder_id": config_data.get("folder_id"),
            "apps_script_url": config_data.get("apps_script_url"),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Update or create config
        existing_config = await mongo_db.find_one("gdrive_config", {"id": "system_gdrive"})
        if existing_config:
            await mongo_db.update("gdrive_config", {"id": "system_gdrive"}, config_dict)
        else:
            await mongo_db.create("gdrive_config", config_dict)
        
        return {"message": "Google Drive configuration updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating Google Drive config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Google Drive configuration")

@api_router.get("/gdrive/status")
async def get_gdrive_status(current_user: UserResponse = Depends(get_current_user)):
    try:
        config = await mongo_db.find_one("gdrive_config", {"id": "system_gdrive"})
        if not config:
            return {"status": "not_configured", "message": "Google Drive not configured"}
        
        # Test connection
        auth_method = config.get("auth_method", "apps_script")
        
        if auth_method == "apps_script":
            script_url = config.get("apps_script_url")
            if not script_url:
                return {"status": "error", "message": "Apps Script URL not configured"}
            
            try:
                # Test connection to Apps Script
                response = requests.post(script_url, json={"action": "test_connection"}, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        return {"status": "connected", "message": "Google Drive connected via Apps Script"}
                    else:
                        return {"status": "error", "message": f"Apps Script error: {result.get('error')}"}
                else:
                    return {"status": "error", "message": f"Apps Script connection failed: {response.status_code}"}
            except Exception as e:
                return {"status": "error", "message": f"Connection test failed: {str(e)}"}
        
        else:
            return {"status": "error", "message": "Unsupported authentication method"}
        
    except Exception as e:
        logger.error(f"Error checking Google Drive status: {e}")
        return {"status": "error", "message": str(e)}

@api_router.post("/gdrive/sync-to-drive-proxy")
async def sync_to_drive_proxy(current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    """Sync local files to Google Drive via Apps Script proxy"""
    try:
        # Get Google Drive configuration
        config = await mongo_db.find_one("gdrive_config", {"id": "system_gdrive"})
        if not config:
            raise HTTPException(status_code=400, detail="Google Drive not configured")
        
        web_app_url = config.get("web_app_url")
        if not web_app_url:
            raise HTTPException(status_code=400, detail="Apps Script URL not configured")
        
        # Get all data from collections
        collections_to_sync = ["users", "companies", "ships", "certificates", "ship_survey_status"]
        files_uploaded = 0
        upload_details = []
        
        for collection_name in collections_to_sync:
            try:
                # Get data from collection
                data = await mongo_db.find_all(collection_name, {})
                if not data:
                    continue
                
                # Convert to JSON string
                json_data = json.dumps(data, default=str, indent=2)
                
                # Upload to Google Drive via Apps Script
                payload = {
                    "action": "upload_file",
                    "folder_id": config.get("folder_id", ""),
                    "filename": f"{collection_name}.json",
                    "content": json_data,
                    "mimeType": "application/json"
                }
                
                response = requests.post(web_app_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        files_uploaded += 1
                        upload_details.append({
                            "collection": collection_name,
                            "filename": f"{collection_name}.json",
                            "status": "uploaded",
                            "records": len(data),
                            "file_id": result.get("file_id")
                        })
                    else:
                        upload_details.append({
                            "collection": collection_name,
                            "filename": f"{collection_name}.json", 
                            "status": "failed",
                            "error": result.get("error")
                        })
                else:
                    upload_details.append({
                        "collection": collection_name,
                        "filename": f"{collection_name}.json",
                        "status": "failed", 
                        "error": f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                upload_details.append({
                    "collection": collection_name,
                    "filename": f"{collection_name}.json",
                    "status": "failed",
                    "error": str(e)
                })
        
        # Update last sync timestamp
        await mongo_db.update(
            "gdrive_config",
            {"id": "system_gdrive"},
            {"last_sync": datetime.now(timezone.utc)}
        )
        
        return {
            "success": True,
            "message": f"Sync completed. {files_uploaded} files uploaded",
            "files_uploaded": files_uploaded,
            "upload_details": upload_details
        }
        
    except Exception as e:
        logger.error(f"Error syncing to Google Drive: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@api_router.post("/gdrive/sync-to-drive") 
async def sync_to_drive(current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    """Legacy sync endpoint - redirects to proxy version"""
@api_router.post("/gdrive/configure-proxy")
async def configure_google_drive_proxy(
    web_app_url: str = None,
    folder_id: str = None,
    current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    """Configure Google Drive Apps Script proxy and test connection"""
    try:
        if not web_app_url or not folder_id:
            raise HTTPException(status_code=400, detail="web_app_url and folder_id are required")
        
        # Test the Apps Script URL first
        test_payload = {
            "action": "test_connection",
            "folder_id": folder_id
        }
        
        response = requests.post(web_app_url, json=test_payload, timeout=30)
        
        if response.status_code != 200:
            return {
                "success": False,
                "message": f"Apps Script test failed with status {response.status_code}",
                "error": f"HTTP {response.status_code}",
                "response_text": response.text[:500] if response.text else "No response"
            }
        
        try:
            result = response.json()
            
            if result.get("success"):
                # If test successful, update the database configuration
                config_update = {
                    "web_app_url": web_app_url,
                    "folder_id": folder_id,
                    "auth_method": "apps_script",
                    "last_tested": datetime.now(timezone.utc).isoformat(),
                    "test_result": "success"
                }
                
                await mongo_db.update(
                    "gdrive_config",
                    {"id": "system_gdrive"},
                    config_update,
                    upsert=True
                )
                
                return {
                    "success": True,
                    "message": "Google Drive configuration successful!",
                    "folder_name": result.get("folder_name", "Unknown"),
                    "folder_id": folder_id,
                    "test_result": "PASSED",
                    "configuration_saved": True
                }
            else:
                return {
                    "success": False,
                    "message": f"Apps Script test failed: {result.get('message', 'Unknown error')}",
                    "error": result.get("error", "Test connection failed"),
                    "apps_script_response": result
                }
                
        except json.JSONDecodeError:
            return {
                "success": False,
                "message": "Apps Script returned invalid JSON response",
                "error": "Invalid JSON response",
                "response_text": response.text[:500]
            }
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "Apps Script request timed out",
            "error": "Request timeout after 30 seconds"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Apps Script request failed: {str(e)}",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Error configuring Google Drive proxy: {e}")
        return {
            "success": False,
            "message": f"Configuration failed: {str(e)}",
            "error": str(e)
        }
# Company-specific Google Drive endpoints
@api_router.get("/companies/{company_id}/gdrive/config")
async def get_company_gdrive_config(
    company_id: str,
    current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    """Get Google Drive configuration for specific company"""
    try:
        # Check if company exists
        company = await mongo_db.find_one("companies", {"id": company_id})
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get company-specific Google Drive config
        config = await mongo_db.find_one("company_gdrive_config", {"company_id": company_id})
        
        if config:
            return {
                "success": True,
                "config": {
                    "web_app_url": config.get("web_app_url", ""),
                    "folder_id": config.get("folder_id", ""),
                    "auth_method": config.get("auth_method", "apps_script"),
                    "service_account_email": config.get("service_account_email", ""),
                    "project_id": config.get("project_id", "")
                },
                "company_name": company.get("name_en", company.get("name", "Unknown"))
            }
        else:
            # Return empty config for new setup
            return {
                "success": True,
                "config": {
                    "web_app_url": "",
                    "folder_id": "",
                    "auth_method": "apps_script",
                    "service_account_email": "",
                    "project_id": ""
                },
                "company_name": company.get("name_en", company.get("name", "Unknown"))
            }
            
    except Exception as e:
        logger.error(f"Error fetching company Google Drive config: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch configuration")

@api_router.get("/companies/{company_id}/gdrive/status")
async def get_company_gdrive_status(
    company_id: str,
    current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    """Get Google Drive connection status for specific company"""
    try:
        # Check if company exists
        company = await mongo_db.find_one("companies", {"id": company_id})
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get company-specific Google Drive config
        config = await mongo_db.find_one("company_gdrive_config", {"company_id": company_id})
        
        if not config or not config.get("web_app_url"):
            return {
                "success": True,
                "status": "not_configured",
                "message": "Google Drive not configured for this company",
                "last_tested": None,
                "test_result": "pending"
            }
        
        return {
            "success": True,
            "status": "configured" if config.get("web_app_url") else "not_configured",
            "message": "Google Drive configured" if config.get("web_app_url") else "Not configured",
            "last_tested": config.get("last_tested"),
            "test_result": config.get("test_result", "unknown"),
            "folder_id": config.get("folder_id"),
            "auth_method": config.get("auth_method", "apps_script")
        }
        
    except Exception as e:
        logger.error(f"Error fetching company Google Drive status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch status")

@api_router.post("/companies/{company_id}/gdrive/configure")
async def configure_company_gdrive(
    company_id: str,
    config_data: dict,
    current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    """Configure Google Drive for specific company"""
    try:
        # Check if company exists
        company = await mongo_db.find_one("companies", {"id": company_id})
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        web_app_url = config_data.get("web_app_url")
        folder_id = config_data.get("folder_id")
        
        if not web_app_url or not folder_id:
            raise HTTPException(status_code=400, detail="web_app_url and folder_id are required")
        
        # Test the configuration first
        test_payload = {
            "action": "test_connection",
            "folder_id": folder_id
        }
        
        try:
            response = requests.post(web_app_url, json=test_payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    # Save configuration to database
                    config_update = {
                        "company_id": company_id,
                        "web_app_url": web_app_url,
                        "folder_id": folder_id,
                        "auth_method": config_data.get("auth_method", "apps_script"),
                        "service_account_email": config_data.get("service_account_email", ""),
                        "project_id": config_data.get("project_id", ""),
                        "last_tested": datetime.now(timezone.utc).isoformat(),
                        "test_result": "success",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    await mongo_db.update(
                        "company_gdrive_config",
                        {"company_id": company_id},
                        config_update,
                        upsert=True
                    )
                    
                    return {
                        "success": True,
                        "message": "Google Drive configured successfully!",
                        "folder_name": result.get("folder_name", "Unknown"),
                        "test_result": "PASSED",
                        "configuration_saved": True
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Apps Script test failed: {result.get('message', 'Unknown error')}",
                        "error": result.get("error", "Test failed")
                    }
            else:
                return {
                    "success": False,
                    "message": f"Apps Script request failed with status {response.status_code}",
                    "error": f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "Apps Script request timed out",
                "error": "Request timeout"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Apps Script request failed: {str(e)}",
                "error": str(e)
            }
        
    except Exception as e:
        logger.error(f"Error configuring company Google Drive: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")

# Proxy endpoint for frontend compatibility
@api_router.post("/companies/{company_id}/gdrive/configure-proxy")
async def configure_company_gdrive_proxy(
    company_id: str,
    config_data: dict,
    current_user: UserResponse = Depends(check_permission([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    """Company-specific Google Drive configuration proxy (frontend compatibility)"""
    return await configure_company_gdrive(company_id, config_data, current_user)
# Usage statistics endpoint
@api_router.get("/usage-stats")
async def get_usage_stats(
    days: int = 30,
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get usage data
        usage_data = await mongo_db.find_all("usage_tracking", {
            "timestamp": {
                "$gte": start_date,
                "$lte": end_date
            }
        })
        
        # Process statistics
        total_operations = len(usage_data)
        operations_by_type = {}
        operations_by_provider = {}
        
        for record in usage_data:
            op_type = record.get('operation_type', 'unknown')
            provider = record.get('provider', 'unknown')
            
            operations_by_type[op_type] = operations_by_type.get(op_type, 0) + 1
            operations_by_provider[provider] = operations_by_provider.get(provider, 0) + 1
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_operations": total_operations,
            "operations_by_type": operations_by_type,
            "operations_by_provider": operations_by_provider
        }
        
    except Exception as e:
        logger.error(f"Error fetching usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch usage statistics")

# Add the router to the main app
app.include_router(api_router)

# Static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Initialize database connection
@app.on_event("startup")
async def startup_event():
    await mongo_db.connect()

@app.on_event("shutdown") 
async def shutdown_event():
    await mongo_db.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)