"""
Helper function to get AI configuration from database
Handles multiple query formats for backward compatibility
"""
import logging
from typing import Optional, Dict, Any
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

async def get_ai_config() -> Optional[Dict[str, Any]]:
    """
    Get AI configuration from database with multiple fallback queries
    Returns the config dict or None if not found
    """
    # Try 1: System-wide config (no company field) - new format
    ai_config_doc = await mongo_db.find_one("ai_config", {"company": {"$exists": False}})
    if ai_config_doc:
        logger.debug("Found AI config (system-wide format)")
        return ai_config_doc
    
    # Try 2: Legacy format with id = "system_ai"
    ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
    if ai_config_doc:
        logger.debug("Found AI config (legacy system_ai format)")
        return ai_config_doc
    
    # Try 3: Any ai_config document as last resort
    ai_config_doc = await mongo_db.find_one("ai_config", {})
    if ai_config_doc:
        logger.debug("Found AI config (any document)")
        return ai_config_doc
    
    logger.warning("No AI configuration found in database")
    return None
