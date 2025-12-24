"""
Helper function to get AI configuration from database
Handles multiple query formats for backward compatibility
"""
import logging
from typing import Optional, Dict, Any
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

# Deprecated models mapping to new models
DEPRECATED_MODELS = {
    "gemini-pro": "gemini-2.0-flash",
    "gemini-pro-vision": "gemini-2.0-flash",
    "gemini-1.0-pro": "gemini-2.0-flash",
}

async def get_ai_config() -> Optional[Dict[str, Any]]:
    """
    Get AI configuration from database with multiple fallback queries
    Returns the config dict or None if not found
    Automatically migrates deprecated models to new ones
    """
    ai_config_doc = None
    
    # Try 1: System-wide config (no company field) - new format
    ai_config_doc = await mongo_db.find_one("ai_config", {"company": {"$exists": False}})
    if ai_config_doc:
        logger.debug("Found AI config (system-wide format)")
    
    # Try 2: Legacy format with id = "system_ai"
    if not ai_config_doc:
        ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
        if ai_config_doc:
            logger.debug("Found AI config (legacy system_ai format)")
    
    # Try 3: Any ai_config document as last resort
    if not ai_config_doc:
        ai_config_doc = await mongo_db.find_one("ai_config", {})
        if ai_config_doc:
            logger.debug("Found AI config (any document)")
    
    if not ai_config_doc:
        logger.warning("No AI configuration found in database")
        return None
    
    # Auto-migrate deprecated models
    current_model = ai_config_doc.get("model", "")
    if current_model in DEPRECATED_MODELS:
        new_model = DEPRECATED_MODELS[current_model]
        logger.warning(f"⚠️ Deprecated model '{current_model}' detected, auto-migrating to '{new_model}'")
        ai_config_doc["model"] = new_model
        
        # Update in database for future requests
        try:
            config_id = ai_config_doc.get("id")
            if config_id:
                await mongo_db.update("ai_config", {"id": config_id}, {"model": new_model})
                logger.info(f"✅ Successfully migrated model from '{current_model}' to '{new_model}' in database")
        except Exception as e:
            logger.error(f"Failed to update deprecated model in database: {e}")
    
    return ai_config_doc
