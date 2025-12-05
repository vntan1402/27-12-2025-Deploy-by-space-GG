"""
Auto-initialize admin user on first startup
Ported from V1's init_admin_startup.py
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings
from app.core.security import hash_password
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

async def init_admin_if_needed() -> Optional[dict]:
    """
    Check if any admin exists. If not, create one from environment variables.
    This runs automatically on application startup.
    
    Returns:
        dict: Admin user data if created, None otherwise
    """
    try:
        # Check if any admin users exist
        admin_query = {
            "role": {"$in": ["system_admin", "SYSTEM_ADMIN", "super_admin", "SUPER_ADMIN"]}
        }
        existing_admin = await mongo_db.find_one("users", admin_query)
        
        if existing_admin:
            logger.info(f"✅ Admin user already exists: {existing_admin.get('username')}")
            return None
        
        logger.info("🔧 No admin users found. Creating initial admin from environment variables...")
        
        # Get admin credentials from environment variables
        admin_username = settings.INIT_ADMIN_USERNAME
        admin_email = settings.INIT_ADMIN_EMAIL
        admin_password = settings.INIT_ADMIN_PASSWORD
        admin_full_name = settings.INIT_ADMIN_FULL_NAME
        
        # Validate password exists
        if not admin_password:
            logger.error("❌ INIT_ADMIN_PASSWORD not set in environment variables!")
            logger.error("   Please set INIT_ADMIN_PASSWORD in .env file")
            logger.info("ℹ️  Required environment variables:")
            logger.info("   - INIT_ADMIN_USERNAME (optional, default: system_admin)")
            logger.info("   - INIT_ADMIN_PASSWORD (REQUIRED)")
            logger.info("   - INIT_ADMIN_EMAIL (optional, default: admin@company.com)")
            logger.info("   - INIT_ADMIN_FULL_NAME (optional, default: System Administrator)")
            return None
        
        # Hash password
        hashed_password = hash_password(admin_password)
        
        # Create system_admin user WITHOUT company
        # System Admin does NOT need a company - they manage ALL companies
        user_data = {
            'id': str(uuid.uuid4()),
            'username': admin_username,
            'email': admin_email,
            'full_name': admin_full_name,
            'password_hash': hashed_password,
            'password': hashed_password,  # Keep for compatibility
            'role': 'system_admin',
            'department': ['technical', 'operations', 'safety', 'commercial', 'crewing'],
            'company': '',  # Empty string - System Admin is not assigned to any company
            'ship': None,
            'zalo': '',
            'gmail': admin_email,
            'is_active': True,
            'created_at': datetime.now(timezone.utc),
            'created_by': 'system',
            'updated_at': None,
            'updated_by': None
        }
        
        # Insert user
        await mongo_db.create('users', user_data)
        
        # Log success
        logger.info("=" * 60)
        logger.info("✅ INITIAL SYSTEM ADMIN CREATED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"Username:     {admin_username}")
        logger.info(f"Email:        {admin_email}")
        logger.info(f"Role:         SYSTEM_ADMIN")
        logger.info(f"Company:      None (manages ALL companies)")
        logger.info("=" * 60)
        logger.info("ℹ️  System Admin can view and manage all companies in the system")
        logger.info("⚠️  IMPORTANT: Change the password after first login!")
        logger.info("=" * 60)
        
        return user_data
        
    except Exception as e:
        logger.error(f"❌ Error initializing admin: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
