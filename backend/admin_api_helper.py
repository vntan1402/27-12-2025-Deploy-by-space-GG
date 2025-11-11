"""
Admin API Helper - For production admin management
Provides API endpoints to check and create admin users
"""
import os
from fastapi import APIRouter, HTTPException, Header
from mongodb_database import mongo_db
import bcrypt
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/admin/status")
async def check_admin_status():
    """
    Check if any admin exists in the database
    Public endpoint - no authentication required
    """
    try:
        # Check for admins
        system_admins = await mongo_db.find_all('users', {'role': 'system_admin'})
        super_admins = await mongo_db.find_all('users', {'role': 'super_admin'})
        admins = await mongo_db.find_all('users', {'role': 'admin'})
        
        total_admins = len(system_admins) + len(super_admins) + len(admins)
        
        return {
            "success": True,
            "admin_exists": total_admins > 0,
            "total_admins": total_admins,
            "breakdown": {
                "system_admin": len(system_admins),
                "super_admin": len(super_admins),
                "admin": len(admins)
            },
            "users": [
                {
                    "username": u.get("username"),
                    "role": u.get("role"),
                    "email": u.get("email"),
                    "is_active": u.get("is_active")
                }
                for u in (system_admins + super_admins + admins)
            ]
        }
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return {
            "success": False,
            "error": str(e),
            "admin_exists": False
        }


@router.post("/admin/create-from-env")
async def create_admin_from_env(
    x_admin_secret: str = Header(None, alias="X-Admin-Secret")
):
    """
    Create admin from environment variables
    Protected by secret key from env
    """
    try:
        # Get secret from env
        expected_secret = os.getenv('ADMIN_CREATION_SECRET', 'default-secret-change-me')
        
        # Verify secret
        if not x_admin_secret or x_admin_secret != expected_secret:
            raise HTTPException(
                status_code=403,
                detail="Invalid or missing X-Admin-Secret header"
            )
        
        # Check if admin already exists
        system_admins = await mongo_db.find_all('users', {'role': 'system_admin'})
        super_admins = await mongo_db.find_all('users', {'role': 'super_admin'})
        
        if system_admins or super_admins:
            return {
                "success": False,
                "message": "Admin already exists",
                "existing_admins": len(system_admins) + len(super_admins)
            }
        
        # Get credentials from env
        username = os.getenv('INIT_ADMIN_USERNAME', 'system_admin')
        email = os.getenv('INIT_ADMIN_EMAIL', 'admin@company.com')
        password = os.getenv('INIT_ADMIN_PASSWORD')
        full_name = os.getenv('INIT_ADMIN_FULL_NAME', 'System Administrator')
        company_name = os.getenv('INIT_COMPANY_NAME', 'Default Company')
        
        if not password:
            raise HTTPException(
                status_code=400,
                detail="INIT_ADMIN_PASSWORD not set in environment variables"
            )
        
        # Create company
        company_id = str(uuid.uuid4())
        company_data = {
            'id': company_id,
            'name': company_name,
            'email': email,
            'phone': '',
            'address': '',
            'logo_url': '',
            'tax_id': f'AUTO-{company_id[:8]}',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        db = mongo_db.client['ship_management']
        await db['companies'].insert_one(company_data)
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        # Create admin
        user_data = {
            'id': str(uuid.uuid4()),
            'username': username,
            'email': email,
            'full_name': full_name,
            'password_hash': hashed_password,
            'role': 'system_admin',
            'department': ['technical', 'operations'],
            'company': company_id,
            'ship': None,
            'zalo': '',
            'gmail': email,
            'is_active': True,
            'created_at': datetime.now()
        }
        
        await db['users'].insert_one(user_data)
        
        logger.info(f"✅ Admin created via API: {username}")
        
        return {
            "success": True,
            "message": "Admin created successfully",
            "credentials": {
                "username": username,
                "email": email,
                "role": "system_admin",
                "company": company_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating admin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/env-check")
async def check_env_variables():
    """
    Check if environment variables are set
    Public endpoint - shows only if variables exist, not their values
    """
    env_vars = {
        "INIT_ADMIN_USERNAME": bool(os.getenv('INIT_ADMIN_USERNAME')),
        "INIT_ADMIN_EMAIL": bool(os.getenv('INIT_ADMIN_EMAIL')),
        "INIT_ADMIN_PASSWORD": bool(os.getenv('INIT_ADMIN_PASSWORD')),
        "INIT_ADMIN_FULL_NAME": bool(os.getenv('INIT_ADMIN_FULL_NAME')),
        "INIT_COMPANY_NAME": bool(os.getenv('INIT_COMPANY_NAME')),
        "ADMIN_CREATION_SECRET": bool(os.getenv('ADMIN_CREATION_SECRET'))
    }
    
    # Show first 3 chars of username if exists (for verification)
    username_hint = None
    if os.getenv('INIT_ADMIN_USERNAME'):
        username = os.getenv('INIT_ADMIN_USERNAME')
        username_hint = username[:3] + '*' * (len(username) - 3)
    
    return {
        "env_variables_set": env_vars,
        "all_required_set": all([
            env_vars["INIT_ADMIN_USERNAME"],
            env_vars["INIT_ADMIN_PASSWORD"]
        ]),
        "username_hint": username_hint
    }
