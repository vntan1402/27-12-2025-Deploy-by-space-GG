"""
System Endpoints
"""
import logging
import uuid
import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)
router = APIRouter()

# Secret key for admin creation (should be set in production env)
ADMIN_CREATION_SECRET = "ship-management-admin-init-2024"

class InitAdminRequest(BaseModel):
    secret_key: str
    username: str = "admin"
    password: str = "Admin@123456"
    email: str = "admin@company.com"
    full_name: str = "System Administrator"

@router.post("/init-admin")
async def init_admin(request: InitAdminRequest):
    """
    Initialize admin user in empty database
    Requires secret key for security
    """
    # Verify secret key
    if request.secret_key != ADMIN_CREATION_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    # Check if admin already exists
    existing_admin = await mongo_db.find_one("users", {"username": request.username})
    if existing_admin:
        raise HTTPException(status_code=400, detail=f"User '{request.username}' already exists")
    
    # Hash password
    hashed_password = hashlib.sha256(request.password.encode()).hexdigest()
    
    # Create admin user
    user_data = {
        'id': str(uuid.uuid4()),
        'username': request.username,
        'email': request.email,
        'full_name': request.full_name,
        'password_hash': hashed_password,
        'password': hashed_password,
        'role': 'system_admin',
        'department': ['technical', 'operations', 'safety', 'commercial', 'crewing'],
        'company': '',
        'ship': None,
        'zalo': '',
        'gmail': request.email,
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'created_by': 'system',
        'updated_at': None,
        'updated_by': None
    }
    
    await mongo_db.create('users', user_data)
    
    logger.info(f"✅ Admin user '{request.username}' created successfully!")
    
    return {
        "success": True,
        "message": f"Admin user '{request.username}' created successfully",
        "username": request.username,
        "role": "system_admin"
    }

@router.get("/current-datetime")
async def get_current_datetime():
    """
    Get current server date and time for debugging
    Migrated from backend-v1
    """
    now = datetime.now()
    return {
        "current_date": now.date().isoformat(),
        "current_datetime": now.isoformat(),
        "current_timestamp": now.timestamp(),
        "timezone": str(now.astimezone().tzinfo),
        "timezone_offset": now.astimezone().strftime('%z'),
        "formatted": now.strftime('%d/%m/%Y %H:%M:%S')
    }
