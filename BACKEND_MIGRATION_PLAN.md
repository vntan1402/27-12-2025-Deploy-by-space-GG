# 🚀 BACKEND MIGRATION PLAN - Chi Tiết Thực Hiện

**Mục tiêu:** Migrate từ backend monolithic (28,692 lines) sang Clean Architecture
**Strategy:** Safe Parallel Migration với backup backend-v1
**Timeline ước tính:** 3-4 tuần
**Ngày tạo:** $(date)

---

## 📋 MỤC LỤC

1. [Pre-Migration Checklist](#pre-migration-checklist)
2. [Phase 0: Preparation & Backup](#phase-0-preparation--backup)
3. [Phase 1: Infrastructure Setup](#phase-1-infrastructure-setup)
4. [Phase 2: Core Authentication](#phase-2-core-authentication)
5. [Phase 3: User Management](#phase-3-user-management)
6. [Phase 4: Company Management](#phase-4-company-management)
7. [Phase 5: Ship Management](#phase-5-ship-management)
8. [Phase 6: Certificate Management](#phase-6-certificate-management)
9. [Phase 7: Crew Management](#phase-7-crew-management)
10. [Phase 8: Additional Features](#phase-8-additional-features)
11. [Phase 9: Testing & Validation](#phase-9-testing--validation)
12. [Phase 10: Cleanup & Documentation](#phase-10-cleanup--documentation)
13. [Rollback Procedures](#rollback-procedures)
14. [Risk Assessment & Mitigation](#risk-assessment--mitigation)

---

## 🔍 PRE-MIGRATION CHECKLIST

### ✅ Trước khi bắt đầu:

- [ ] **Backup database**
  ```bash
  # Export MongoDB data
  mongodump --uri="$MONGO_URL" --out=/app/database_backup_$(date +%Y%m%d)
  ```

- [ ] **Document current state**
  - [ ] List tất cả endpoints đang hoạt động
  - [ ] List tất cả background jobs
  - [ ] List tất cả environment variables
  - [ ] Screenshot current system status

- [ ] **Verify current system health**
  - [ ] Backend đang chạy không có errors
  - [ ] Frontend kết nối được với backend
  - [ ] Database connection stable
  - [ ] Test 5-10 endpoints quan trọng

- [ ] **Prepare tools**
  - [ ] Testing agent sẵn sàng
  - [ ] Git initialized và committed current state
  - [ ] Supervisor configuration reviewed

---

## 🔄 PHASE 0: PREPARATION & BACKUP

**Timeline:** 30 phút
**Priority:** CRITICAL

### Step 0.1: Backup Backend hiện tại

```bash
# 1. Stop backend service
sudo supervisorctl stop backend

# 2. Rename backend folder
cd /app
mv backend backend-v1

# 3. Verify backup
ls -la backend-v1/
```

### Step 0.2: Git snapshot

```bash
cd /app
git add -A
git commit -m "Snapshot before backend migration - backend renamed to backend-v1"
```

### Step 0.3: Document current endpoints

```bash
# Extract all endpoints from backend-v1
cd /app/backend-v1
grep -n "@api_router\." server.py | tee /app/CURRENT_ENDPOINTS.txt
```

**Output:** File `CURRENT_ENDPOINTS.txt` chứa danh sách 179+ endpoints

### ✅ Success Criteria:
- [ ] backend-v1 folder exists và intact
- [ ] Git commit created
- [ ] CURRENT_ENDPOINTS.txt created

---

## 🏗️ PHASE 1: INFRASTRUCTURE SETUP

**Timeline:** 2-3 giờ
**Priority:** CRITICAL

### Step 1.1: Tạo cấu trúc folder mới

```bash
cd /app
mkdir -p backend/app/{core,models,api/v1,services,repositories,db,utils}
mkdir -p backend/migrations
mkdir -p backend/scripts
mkdir -p backend/tests
```

### Step 1.2: Tạo các files cơ bản

#### 1.2.1: `backend/app/__init__.py`
```python
"""
Ship Management System API - Backend V2
Clean Architecture Implementation
"""
__version__ = "2.0.0"
```

#### 1.2.2: `backend/app/main.py`

**Nội dung chính:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.db.mongodb import mongo_db
from app.api.v1 import api_router

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Ship Management System API - V2"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    await mongo_db.connect()
    # TODO: Initialize admin if needed
    # TODO: Setup schedulers

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    await mongo_db.disconnect()

# Mount uploads folder
app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")

# Include API router
app.include_router(api_router, prefix="/api")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
```

**Action items:**
- [ ] Tạo file `backend/app/main.py`
- [ ] Copy đoạn code trên
- [ ] Verify imports (sẽ tạo các modules này ở steps sau)

#### 1.2.3: `backend/app/core/__init__.py`
```python
from app.core.config import settings
from app.core.security import create_access_token, verify_token, get_current_user

__all__ = ["settings", "create_access_token", "verify_token", "get_current_user"]
```

#### 1.2.4: `backend/app/core/config.py`

**Nội dung:**
```python
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Ship Management System API"
    VERSION: str = "2.0.0"
    
    # Security
    JWT_SECRET: str = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRATION_HOURS: int = 24
    
    # Database
    MONGO_URL: str = os.getenv('MONGO_URL', '')
    DB_NAME: str = os.getenv('DB_NAME', 'ship_management')
    
    # AI
    EMERGENT_LLM_KEY: Optional[str] = os.getenv('EMERGENT_LLM_KEY')
    
    # Paths
    UPLOAD_DIR: Path = ROOT_DIR / "uploads"
    
    class Config:
        case_sensitive = True

settings = Settings()
```

**Action items:**
- [ ] Tạo file với nội dung trên
- [ ] Install `pydantic-settings` nếu chưa có: `pip install pydantic-settings`

#### 1.2.5: `backend/app/core/security.py`

**Migrate từ backend-v1/server.py (lines 4500-4590)**

**Nội dung:**
```python
import os
import jwt
import bcrypt
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)
security = HTTPBearer()

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    token = credentials.credentials
    token_data = verify_token(token)
    
    try:
        user = await mongo_db.find_one("users", {"id": token_data["sub"]})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Import here to avoid circular dependency
        from app.models.user import UserResponse
        return UserResponse(**user)
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False
```

**Action items:**
- [ ] Tạo file
- [ ] Copy code từ backend-v1
- [ ] Update imports

#### 1.2.6: `backend/app/db/__init__.py`
```python
from app.db.mongodb import mongo_db

__all__ = ["mongo_db"]
```

#### 1.2.7: `backend/app/db/mongodb.py`

**Copy từ backend-v1/mongodb_database.py**

```bash
cp /app/backend-v1/mongodb_database.py /app/backend/app/db/mongodb.py
```

**Modifications cần thiết:**
```python
# Update imports at the top
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
import json

# Rest of the code giữ nguyên
```

**Action items:**
- [ ] Copy file
- [ ] Verify imports

#### 1.2.8: `backend/.env`

**Copy từ backend-v1/.env**

```bash
cp /app/backend-v1/.env /app/backend/.env
```

**Verify các biến quan trọng:**
```env
MONGO_URL=mongodb+srv://...
DB_NAME=ship_management
JWT_SECRET=...
EMERGENT_LLM_KEY=...
```

#### 1.2.9: `backend/requirements.txt`

**Copy từ backend-v1**

```bash
cp /app/backend-v1/requirements.txt /app/backend/requirements.txt
```

**Thêm dependencies mới:**
```txt
pydantic-settings>=2.0.0
```

#### 1.2.10: Install dependencies

```bash
cd /app/backend
pip install -r requirements.txt
```

### Step 1.3: Test infrastructure

#### Test script: `backend/test_infrastructure.py`

```python
"""Test basic infrastructure"""
import asyncio
from app.db.mongodb import mongo_db
from app.core.config import settings

async def test_db_connection():
    print(f"Testing MongoDB connection to: {settings.DB_NAME}")
    try:
        await mongo_db.connect()
        print("✅ Database connected successfully")
        
        # Test a simple query
        collections = await mongo_db.list_collections()
        print(f"✅ Found {len(collections)} collections: {collections}")
        
        await mongo_db.disconnect()
        print("✅ Database disconnected successfully")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_config():
    print("\nTesting configuration:")
    print(f"  PROJECT_NAME: {settings.PROJECT_NAME}")
    print(f"  VERSION: {settings.VERSION}")
    print(f"  DB_NAME: {settings.DB_NAME}")
    print(f"  JWT_SECRET: {'***' if settings.JWT_SECRET else 'NOT SET'}")
    print(f"  EMERGENT_LLM_KEY: {'***' if settings.EMERGENT_LLM_KEY else 'NOT SET'}")
    print("✅ Configuration loaded")

async def main():
    print("=" * 50)
    print("INFRASTRUCTURE TEST")
    print("=" * 50)
    
    await test_config()
    await test_db_connection()
    
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED ✅")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
```

**Run test:**
```bash
cd /app/backend
python test_infrastructure.py
```

### ✅ Phase 1 Success Criteria:

- [ ] Folder structure created
- [ ] All core files created
- [ ] Dependencies installed
- [ ] `test_infrastructure.py` passes
- [ ] No import errors

**Checkpoint:** Git commit
```bash
git add -A
git commit -m "Phase 1 complete: Infrastructure setup"
```

---

## 🔐 PHASE 2: CORE AUTHENTICATION

**Timeline:** 2-3 giờ
**Priority:** CRITICAL
**Dependencies:** Phase 1 complete

### Step 2.1: Tạo User Models

#### File: `backend/app/models/__init__.py`
```python
from app.models.user import (
    UserRole,
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    LoginResponse
)

__all__ = [
    "UserRole",
    "UserBase", 
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "LoginResponse"
]
```

#### File: `backend/app/models/user.py`

**Migrate từ backend-v1/server.py (lines 1380-1444)**

```python
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    SYSTEM_ADMIN = "system_admin"
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    SHIP_OFFICER = "ship_officer"
    CREW = "crew"
    EDITOR = "editor"
    VIEWER = "viewer"
    ACCOUNTANT = "accountant"
    DPA = "dpa"
    SUPPLY = "supply"

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: str
    role: UserRole
    department: List[str]
    company: Optional[str] = None
    ship: Optional[str] = None
    zalo: str
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
```

**Action items:**
- [ ] Tạo file với nội dung trên
- [ ] Test import: `python -c "from app.models.user import UserResponse"`

### Step 2.2: Tạo User Repository

#### File: `backend/app/repositories/__init__.py`
```python
from app.repositories.user_repository import UserRepository

__all__ = ["UserRepository"]
```

#### File: `backend/app/repositories/user_repository.py`

```python
import logging
from typing import Optional, List, Dict, Any
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class UserRepository:
    """Data access layer for users"""
    
    @staticmethod
    async def find_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Find user by username"""
        return await mongo_db.find_one("users", {"username": username})
    
    @staticmethod
    async def find_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Find user by email"""
        return await mongo_db.find_one("users", {"email": email})
    
    @staticmethod
    async def find_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by ID"""
        return await mongo_db.find_one("users", {"id": user_id})
    
    @staticmethod
    async def find_all() -> List[Dict[str, Any]]:
        """Get all users"""
        return await mongo_db.find_all("users")
    
    @staticmethod
    async def find_by_company(company: str) -> List[Dict[str, Any]]:
        """Find users by company"""
        return await mongo_db.find_all("users", {"company": company, "is_active": True})
    
    @staticmethod
    async def create(user_data: Dict[str, Any]) -> str:
        """Create new user"""
        return await mongo_db.create("users", user_data)
    
    @staticmethod
    async def update(user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user"""
        return await mongo_db.update("users", {"id": user_id}, update_data)
    
    @staticmethod
    async def delete(user_id: str) -> bool:
        """Delete user"""
        return await mongo_db.delete("users", {"id": user_id})
```

### Step 2.3: Tạo User Service

#### File: `backend/app/services/__init__.py`
```python
from app.services.user_service import UserService

__all__ = ["UserService"]
```

#### File: `backend/app/services/user_service.py`

```python
import uuid
import logging
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from app.models.user import UserCreate, UserUpdate, UserResponse, UserRole
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token

logger = logging.getLogger(__name__)

class UserService:
    """Business logic for user management"""
    
    @staticmethod
    async def authenticate(username: str, password: str, remember_me: bool = False) -> tuple[str, UserResponse]:
        """
        Authenticate user and return access token
        Returns: (access_token, user)
        """
        # Find user
        user = await UserRepository.find_by_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if active
        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="Account is disabled")
        
        # Create token
        token_expires = timedelta(days=30) if remember_me else timedelta(hours=24)
        token_data = {
            "sub": user["id"],
            "username": user["username"],
            "role": user["role"],
            "company": user.get("company"),
            "full_name": user.get("full_name", user["username"])
        }
        access_token = create_access_token(data=token_data, expires_delta=token_expires)
        
        # Remove password hash
        user.pop("password_hash", None)
        
        return access_token, UserResponse(**user)
    
    @staticmethod
    async def get_all_users(current_user: UserResponse) -> List[UserResponse]:
        """Get users based on current user's role"""
        users = await UserRepository.find_all()
        
        # Filter based on role
        if current_user.role in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            filtered = users
        elif current_user.role == UserRole.ADMIN:
            filtered = [u for u in users if u.get('company') == current_user.company]
        else:
            filtered = [u for u in users if u.get('id') == current_user.id]
        
        return [UserResponse(**u) for u in filtered]
    
    @staticmethod
    async def create_user(user_data: UserCreate, current_user: UserResponse) -> UserResponse:
        """Create new user"""
        # Check if username exists
        existing = await UserRepository.find_by_username(user_data.username)
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check email if provided
        if user_data.email:
            existing_email = await UserRepository.find_by_email(user_data.email)
            if existing_email:
                raise HTTPException(status_code=400, detail="Email already exists")
        
        # Create user dict
        user_dict = user_data.dict()
        password = user_dict.pop("password")
        user_dict["password_hash"] = hash_password(password)
        user_dict["id"] = str(uuid.uuid4())
        user_dict["created_at"] = datetime.now(timezone.utc)
        user_dict["permissions"] = {}
        
        # Create in database
        await UserRepository.create(user_dict)
        
        # Return user without password
        user_dict.pop("password_hash")
        return UserResponse(**user_dict)
    
    @staticmethod
    async def update_user(user_id: str, update_data: UserUpdate, current_user: UserResponse) -> UserResponse:
        """Update user"""
        # Find user
        user = await UserRepository.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare update dict
        update_dict = update_data.dict(exclude_unset=True)
        
        # Handle password update
        if "password" in update_dict and update_dict["password"]:
            update_dict["password_hash"] = hash_password(update_dict.pop("password"))
        
        # Update
        await UserRepository.update(user_id, update_dict)
        
        # Get updated user
        updated_user = await UserRepository.find_by_id(user_id)
        updated_user.pop("password_hash", None)
        return UserResponse(**updated_user)
    
    @staticmethod
    async def delete_user(user_id: str, current_user: UserResponse) -> dict:
        """Delete user"""
        user = await UserRepository.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await UserRepository.delete(user_id)
        return {"message": "User deleted successfully"}
```

### Step 2.4: Tạo Auth API Routes

#### File: `backend/app/api/__init__.py`
```python
# Empty file
```

#### File: `backend/app/api/v1/__init__.py`

```python
from fastapi import APIRouter
from app.api.v1 import auth, users

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

__all__ = ["api_router"]
```

#### File: `backend/app/api/v1/auth.py`

**Migrate endpoints:**
- POST `/api/auth/login`
- GET `/api/verify-token`

```python
import logging
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import LoginRequest, LoginResponse, UserResponse
from app.services.user_service import UserService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    Authenticate user and return access token
    """
    try:
        access_token, user = await UserService.authenticate(
            credentials.username, 
            credentials.password,
            credentials.remember_me
        )
        
        return LoginResponse(
            access_token=access_token,
            user=user,
            remember_me=credentials.remember_me
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.get("/verify-token")
async def verify_token(current_user: UserResponse = Depends(get_current_user)):
    """
    Verify if the current token is valid and return user info
    """
    try:
        return {
            "valid": True,
            "user": current_user.dict()
        }
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Step 2.5: Tạo Users API Routes

#### File: `backend/app/api/v1/users.py`

**Migrate endpoints:**
- GET `/api/users`
- POST `/api/users`
- PUT `/api/users/{user_id}`
- DELETE `/api/users/{user_id}`

```python
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.models.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("", response_model=List[UserResponse])
async def get_users(current_user: UserResponse = Depends(get_current_user)):
    """
    Get users list with role-based filtering
    """
    try:
        return await UserService.get_all_users(current_user)
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")

@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create new user
    """
    try:
        return await UserService.create_user(user_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update user
    """
    try:
        return await UserService.update_user(user_id, update_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete user
    """
    try:
        return await UserService.delete_user(user_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")
```

### Step 2.6: Update supervisor config

#### File: `/etc/supervisor/conf.d/backend.conf`

**Backup first:**
```bash
sudo cp /etc/supervisor/conf.d/backend.conf /etc/supervisor/conf.d/backend-v1.conf.backup
```

**Update:**
```bash
sudo nano /etc/supervisor/conf.d/backend.conf
```

**Change:**
```ini
[program:backend]
command=/usr/local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
directory=/app/backend
# ... rest remains same
```

**Reload:**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart backend
```

### Step 2.7: Test Authentication

**Manual test:**
```bash
# Check logs
sudo supervisorctl tail -f backend

# Check if server started
curl http://localhost:8001/health

# Test login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'
```

**Backend testing agent:**
```
Test authentication module:
1. Health check endpoint /health
2. Login endpoint /api/auth/login with valid credentials
3. Login with invalid credentials (should fail)
4. Verify token endpoint /api/verify-token with valid token
5. Get users endpoint /api/users with valid token
```

### ✅ Phase 2 Success Criteria:

- [ ] All auth files created
- [ ] Backend starts without errors
- [ ] Health check returns 200
- [ ] Login works and returns token
- [ ] Verify token works
- [ ] Get users endpoint works

**Checkpoint:** Git commit
```bash
git add -A
git commit -m "Phase 2 complete: Authentication & User Management"
```

---

## 🏢 PHASE 3: COMPANY MANAGEMENT

**Timeline:** 2 giờ
**Priority:** HIGH
**Dependencies:** Phase 2 complete

### Endpoints to migrate:
- GET `/api/companies`
- GET `/api/companies/{company_id}`
- POST `/api/companies`
- PUT `/api/companies/{company_id}`
- DELETE `/api/companies/{company_id}`
- POST `/api/companies/{company_id}/upload-logo`
- GET `/api/files/{folder}/{filename}`

### Files to create:
1. `app/models/company.py` - Company models
2. `app/repositories/company_repository.py` - Data access
3. `app/services/company_service.py` - Business logic
4. `app/api/v1/companies.py` - API routes

**Detailed steps similar to Phase 2...**

---

## 🚢 PHASE 4: SHIP MANAGEMENT

**Timeline:** 3-4 giờ
**Priority:** HIGH
**Dependencies:** Phase 3 complete

### Endpoints to migrate (30+ endpoints):
- GET `/api/ships`
- POST `/api/ships`
- GET `/api/ships/{ship_id}`
- PUT `/api/ships/{ship_id}`
- DELETE `/api/ships/{ship_id}`
- POST `/api/ships/{ship_id}/calculate-anniversary-date`
- POST `/api/ships/{ship_id}/calculate-next-docking`
- POST `/api/ships/{ship_id}/calculate-docking-dates`
- ... (và các endpoints khác)

### Files to create:
1. `app/models/ship.py`
2. `app/repositories/ship_repository.py`
3. `app/services/ship_service.py`
4. `app/api/v1/ships.py`
5. `app/utils/ship_calculations.py` - Helper for docking calculations

---

## 📜 PHASE 5: CERTIFICATE MANAGEMENT

**Timeline:** 4-5 giờ
**Priority:** HIGH
**Dependencies:** Phase 4 complete

### Endpoints to migrate (40+ endpoints):
- GET `/api/ships/{ship_id}/certificates`
- POST `/api/certificates/analyze-file`
- PUT `/api/certificates/{cert_id}`
- DELETE `/api/certificates/{cert_id}`
- POST `/api/certificates/bulk-delete`
- ... (AI analysis endpoints)

### Files to create:
1. `app/models/certificate.py`
2. `app/repositories/certificate_repository.py`
3. `app/services/certificate_service.py`
4. `app/services/ai_service.py` - AI/LLM integration
5. `app/api/v1/certificates.py`
6. `app/utils/ocr_processor.py` - Copy from backend-v1

---

## 👥 PHASE 6: CREW MANAGEMENT

**Timeline:** 3-4 giờ
**Priority:** MEDIUM
**Dependencies:** Phase 5 complete

### Endpoints to migrate (30+ endpoints):
- GET `/api/crew`
- POST `/api/crew`
- PUT `/api/crew/{crew_id}`
- DELETE `/api/crew/{crew_id}`
- GET `/api/crew-certificates/analyze-file`
- ... (crew certificates endpoints)

### Files to create:
1. `app/models/crew.py`
2. `app/repositories/crew_repository.py`
3. `app/services/crew_service.py`
4. `app/api/v1/crew.py`

---

## 🔧 PHASE 7: ADDITIONAL FEATURES

**Timeline:** 4-5 giờ
**Priority:** MEDIUM

### Modules to migrate:
1. **Google Drive Integration**
   - `app/services/gdrive_service.py`
   - `app/api/v1/gdrive.py`
   
2. **System Settings**
   - `app/api/v1/system.py`
   
3. **Background Jobs**
   - `app/services/scheduler_service.py`
   - Certificate expiry notifications
   - GDrive sync jobs

4. **Admin API**
   - `app/api/v1/admin.py`
   - Copy from backend-v1/admin_api_helper.py

---

## 🧪 PHASE 8: TESTING & VALIDATION

**Timeline:** 1 tuần
**Priority:** CRITICAL

### Step 8.1: Backend Testing

**Test từng module:**
```bash
# Test auth
deep_testing_backend_v2: "Test all authentication endpoints..."

# Test users
deep_testing_backend_v2: "Test all user management endpoints..."

# Test companies
deep_testing_backend_v2: "Test all company endpoints..."

# Test ships
deep_testing_backend_v2: "Test all ship endpoints..."

# Test certificates
deep_testing_backend_v2: "Test all certificate endpoints..."

# Test crew
deep_testing_backend_v2: "Test all crew endpoints..."
```

### Step 8.2: Integration Testing

**Test workflows:**
1. Complete user journey: Login → Create ship → Upload certificate
2. AI analysis workflow
3. GDrive sync workflow
4. Multi-user scenarios
5. Permission checks

### Step 8.3: Frontend Integration

**Update frontend if needed:**
- Verify all API calls work
- Check error handling
- Test all features end-to-end

### Step 8.4: Performance Testing

**Compare với backend-v1:**
- Response times
- Memory usage
- Database query efficiency

---

## 🧹 PHASE 9: CLEANUP & DOCUMENTATION

**Timeline:** 1-2 ngày
**Priority:** MEDIUM

### Step 9.1: Code cleanup
- Remove unused imports
- Add docstrings
- Format code consistently
- Run linters

### Step 9.2: Documentation
- API documentation (auto-generated by FastAPI)
- Architecture documentation
- Deployment guide
- Migration notes

### Step 9.3: Delete backend-v1

**After 100% verification:**
```bash
cd /app
rm -rf backend-v1
git add -A
git commit -m "Migration complete: Removed backend-v1"
```

---

## 🔄 ROLLBACK PROCEDURES

### If issues occur during migration:

#### Level 1: Quick Rollback (2 minutes)
```bash
# Stop new backend
sudo supervisorctl stop backend

# Restore backend-v1
cd /app
rm -rf backend
mv backend-v1 backend

# Update supervisor config
sudo nano /etc/supervisor/conf.d/backend.conf
# Change: directory=/app/backend
# Change: command=python -m uvicorn server:app ...

# Restart
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart backend
```

#### Level 2: Git Rollback
```bash
# Find last good commit
git log --oneline

# Rollback
git reset --hard <commit_hash>

# Restart services
sudo supervisorctl restart all
```

#### Level 3: Database Restore
```bash
# If database was corrupted
mongorestore --uri="$MONGO_URL" /app/database_backup_YYYYMMDD
```

---

## ⚠️ RISK ASSESSMENT & MITIGATION

### Risk 1: Database Schema Changes
**Probability:** Medium
**Impact:** High
**Mitigation:**
- Always backup before migration
- Test with read-only access first
- Use migration scripts for schema changes

### Risk 2: Missing Endpoints
**Probability:** Medium
**Impact:** Medium
**Mitigation:**
- Create comprehensive endpoint checklist
- Test systematically
- Keep backend-v1 for reference

### Risk 3: Performance Degradation
**Probability:** Low
**Impact:** Medium
**Mitigation:**
- Benchmark before and after
- Use same database queries
- Profile slow endpoints

### Risk 4: Frontend Breaking
**Probability:** Medium
**Impact:** High
**Mitigation:**
- Keep API contracts identical
- Test frontend after each phase
- Use testing agent

### Risk 5: Lost Business Logic
**Probability:** Low
**Impact:** High
**Mitigation:**
- Carefully review all helper functions
- Test edge cases
- Compare responses with backend-v1

---

## 📊 PROGRESS TRACKING

### Migration Checklist

#### Infrastructure
- [ ] Phase 0: Backup complete
- [ ] Phase 1: Infrastructure setup
- [ ] Phase 2: Authentication working

#### Core Features
- [ ] Phase 3: Company management
- [ ] Phase 4: Ship management
- [ ] Phase 5: Certificate management
- [ ] Phase 6: Crew management

#### Additional
- [ ] Phase 7: GDrive, System, Admin APIs
- [ ] Phase 8: Testing complete
- [ ] Phase 9: Documentation & cleanup

#### Endpoints Migration Status
```
Total endpoints: 179
Migrated: 0
Remaining: 179
Progress: 0%
```

---

## 📅 TIMELINE SUMMARY

| Phase | Duration | Priority | Status |
|-------|----------|----------|--------|
| Phase 0 | 30 min | CRITICAL | ⬜ Not started |
| Phase 1 | 2-3 hrs | CRITICAL | ⬜ Not started |
| Phase 2 | 2-3 hrs | CRITICAL | ⬜ Not started |
| Phase 3 | 2 hrs | HIGH | ⬜ Not started |
| Phase 4 | 3-4 hrs | HIGH | ⬜ Not started |
| Phase 5 | 4-5 hrs | HIGH | ⬜ Not started |
| Phase 6 | 3-4 hrs | MEDIUM | ⬜ Not started |
| Phase 7 | 4-5 hrs | MEDIUM | ⬜ Not started |
| Phase 8 | 1 week | CRITICAL | ⬜ Not started |
| Phase 9 | 1-2 days | MEDIUM | ⬜ Not started |

**Total estimated time:** 3-4 tuần (với testing kỹ lưỡng)

---

## 🎯 SUCCESS METRICS

### Definition of Done:

1. **Functionality**
   - ✅ All 179 endpoints working
   - ✅ All features parity with backend-v1
   - ✅ No regressions

2. **Quality**
   - ✅ All tests passing
   - ✅ No critical bugs
   - ✅ Performance equal or better

3. **Code Quality**
   - ✅ Clean architecture implemented
   - ✅ Code documented
   - ✅ Linters pass

4. **Deployment**
   - ✅ Runs in production
   - ✅ Stable for 1 week
   - ✅ Backend-v1 deleted

---

## 📞 SUPPORT & ESCALATION

### If stuck:
1. Check backend-v1 code
2. Review this migration plan
3. Use troubleshoot_agent
4. Ask user for clarification

### Critical issues:
- Database corruption → Restore from backup
- Service down → Rollback immediately
- Data loss → Escalate to user

---

**END OF MIGRATION PLAN**

*Last updated: $(date)*
*Version: 1.0*
