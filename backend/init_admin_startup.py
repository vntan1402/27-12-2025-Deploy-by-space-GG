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
        company_name = os.getenv('INIT_COMPANY_NAME', 'Default Company')
        
        if not admin_password:
            logger.error("❌ INIT_ADMIN_PASSWORD not set in environment variables!")
            logger.error("   Please set INIT_ADMIN_PASSWORD in .env file")
            # Don't disconnect - main app needs the connection
            # await mongo_db.disconnect()
            return
        
        # Create company first
        company_id = str(uuid.uuid4())
        company_data = {
            'id': company_id,
            'name': company_name,
            'email': admin_email,
            'phone': '',
            'address': '',
            'logo_url': '',
            'tax_id': f'AUTO-{company_id[:8]}',  # Auto-generated unique tax_id
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        db = mongo_db.client['ship_management']
        await db['companies'].insert_one(company_data)
        logger.info(f"✅ Company created: {company_name}")
        
        # Hash password
        hashed_password = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()).decode()
        
        # Create system_admin user
        user_data = {
            'id': str(uuid.uuid4()),
            'username': admin_username,
            'email': admin_email,
            'full_name': admin_full_name,
            'password': hashed_password,
            'role': 'system_admin',
            'department': ['technical', 'operations'],
            'company': company_id,
            'ship': None,
            'zalo': '',
            'gmail': admin_email,
            'is_active': True,
            'created_at': datetime.now()
        }
        
        await db['users'].insert_one(user_data)
        
        logger.info("=" * 60)
        logger.info("✅ INITIAL ADMIN USER CREATED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"Username:     {admin_username}")
        logger.info(f"Email:        {admin_email}")
        logger.info(f"Role:         SYSTEM_ADMIN")
        logger.info(f"Company:      {company_name}")
        logger.info("=" * 60)
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
