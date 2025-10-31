"""
Script to check and fix Document AI configuration
"""
import asyncio
import os
import sys
import logging
import json
from mongodb_database import mongo_db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_and_fix_ai_config():
    """Check Document AI configuration for whitespace issues"""
    try:
        # Connect to database
        logger.info("Connecting to MongoDB...")
        await mongo_db.connect()
        
        # Find AI config
        logger.info("Finding AI configuration...")
        ai_config = await mongo_db.database.ai_config.find_one({"id": "system_ai"})
        
        if not ai_config:
            logger.error("AI configuration not found!")
            return
        
        logger.info(f"Found AI config: {ai_config.get('id')}")
        
        # Check Document AI configuration
        document_ai = ai_config.get('document_ai', {})
        logger.info(f"\nDocument AI Configuration:")
        logger.info(f"  project_id: '{document_ai.get('project_id')}'")
        logger.info(f"  project_id (repr): {repr(document_ai.get('project_id'))}")
        logger.info(f"  location: '{document_ai.get('location')}'")
        logger.info(f"  processor_id: '{document_ai.get('processor_id')}'")
        
        # Check for whitespace
        project_id = document_ai.get('project_id', '')
        if project_id != project_id.strip():
            logger.warning(f"⚠️  Whitespace detected in project_id!")
            logger.info(f"  Before: '{project_id}'")
            logger.info(f"  After:  '{project_id.strip()}'")
            
            # Fix the whitespace
            document_ai['project_id'] = project_id.strip()
            
            # Update in database
            result = await mongo_db.database.ai_config.update_one(
                {"id": "system_ai"},
                {"$set": {"document_ai": document_ai}}
            )
            
            if result.modified_count > 0:
                logger.info("✅ Successfully fixed Document AI project_id whitespace!")
            else:
                logger.warning("⚠️  No changes made to database")
        else:
            logger.info("✅ No whitespace issues detected in project_id")
        
        # Check System AI configuration
        system_ai = ai_config.get('system_ai', {})
        logger.info(f"\nSystem AI Configuration:")
        logger.info(f"  apps_script_url: '{system_ai.get('apps_script_url')}'")
        
    except Exception as e:
        logger.error(f"❌ Error checking AI config: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Disconnect from database
        await mongo_db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_and_fix_ai_config())
