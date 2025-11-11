"""
Initialize admin user on first startup
This runs automatically when the app starts
"""
import asyncio
from mongodb_database import mongo_db
import bcrypt
from datetime import datetime
import uuid
import os
import logging

logger = logging.getLogger(__name__)

async def init_admin_if_needed():
    """
    Check if any admin exists. If not, create one from environment variables.
    This should run on application startup.
    
    Note: Assumes mongo_db is already connected by the main startup event.
    """
    try:
        # Don't connect here - should already be connected
        # await mongo_db.connect()
        
        # Check if any admin users exist
        system_admins = await mongo_db.find_all('users', {'role': 'system_admin'})
        super_admins = await mongo_db.find_all('users', {'role': 'super_admin'})
        
        if system_admins or super_admins:
            logger.info(f"✅ Admin users already exist ({len(system_admins)} system_admin, {len(super_admins)} super_admin)")
            # Don't disconnect - main app needs the connection
            # await mongo_db.disconnect()
            return
        
        logger.info("🔧 No admin users found. Creating initial admin from environment variables...")
        
        # Get admin credentials from environment variables
        admin_username = os.getenv('INIT_ADMIN_USERNAME', 'system_admin')
        admin_email = os.getenv('INIT_ADMIN_EMAIL', 'admin@company.com')
        admin_password = os.getenv('INIT_ADMIN_PASSWORD')
        admin_full_name = os.getenv('INIT_ADMIN_FULL_NAME', 'System Administrator')
        # Note: INIT_COMPANY_NAME is no longer needed since system_admin doesn't belong to any company
        
        if not admin_password:
            logger.error("❌ INIT_ADMIN_PASSWORD not set in environment variables!")
            logger.error("   Please set INIT_ADMIN_PASSWORD in .env file")
            logger.info("ℹ️  Required environment variables:")
            logger.info("   - INIT_ADMIN_USERNAME (optional, default: system_admin)")
            logger.info("   - INIT_ADMIN_PASSWORD (REQUIRED)")
            logger.info("   - INIT_ADMIN_EMAIL (optional, default: admin@company.com)")
            logger.info("   - INIT_ADMIN_FULL_NAME (optional, default: System Administrator)")
            # Don't disconnect - main app needs the connection
            # await mongo_db.disconnect()
            return
        
        # System Admin does NOT need a company - they manage ALL companies
        # No company creation for system_admin
        logger.info("ℹ️  System Admin will not be assigned to any company (manages all companies)")
        logger.info("ℹ️  Note: INIT_COMPANY_NAME is no longer required")
        
        # Hash password
        hashed_password = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()).decode()
        
        # Create system_admin user WITHOUT company
        user_data = {
            'id': str(uuid.uuid4()),
            'username': admin_username,
            'email': admin_email,
            'full_name': admin_full_name,
            'password_hash': hashed_password,  # Changed from 'password' to 'password_hash' to match login endpoint
            'password': hashed_password,  # Add 'password' field as well for compatibility
            'role': 'system_admin',
            'department': ['technical', 'operations', 'safety', 'commercial', 'crewing'],
            'company': '',  # Empty string - System Admin is not assigned to any company
            'ship': None,
            'zalo': '',
            'gmail': admin_email,
            'is_active': True,
            'created_at': datetime.now()
        }
        
        # Use mongo_db.create() instead of direct insert_one() to avoid permission issues
        await mongo_db.create('users', user_data)
        
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
        
        # Don't disconnect here - main app still needs the connection
        # await mongo_db.disconnect()
        
    except Exception as e:
        logger.error(f"❌ Error initializing admin: {str(e)}")
        # Don't disconnect on error - main app still needs the connection

if __name__ == "__main__":
    # For testing
    asyncio.run(init_admin_if_needed())
