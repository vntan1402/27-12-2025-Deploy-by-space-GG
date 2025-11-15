import logging
from typing import Optional
from datetime import datetime
import uuid

from app.db.mongodb import mongo_db
from app.models.ai_config import AIConfigCreate, AIConfigUpdate, AIConfigResponse

logger = logging.getLogger(__name__)

class AIConfigRepository:
    """Repository for AI Configuration operations"""
    
    collection_name = "ai_config"
    
    @staticmethod
    async def get_by_company(company: str) -> Optional[dict]:
        """Get AI config by company"""
        try:
            config = await mongo_db.find_one(
                AIConfigRepository.collection_name,
                {"company": company}
            )
            return config
        except Exception as e:
            logger.error(f"Error getting AI config for company {company}: {e}")
            raise
    
    @staticmethod
    async def create(config_data: AIConfigCreate, company: str, user_id: str) -> dict:
        """Create new AI configuration"""
        try:
            config_dict = {
                "id": str(uuid.uuid4()),
                "company": company,
                **config_data.dict(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "updated_by": user_id
            }
            
            # Don't store custom_api_key if using emergent key
            if config_dict.get("use_emergent_key"):
                config_dict["custom_api_key"] = None
            
            result = await mongo_db.insert_one(
                AIConfigRepository.collection_name,
                config_dict
            )
            
            return config_dict
        except Exception as e:
            logger.error(f"Error creating AI config: {e}")
            raise
    
    @staticmethod
    async def update(company: str, config_data: AIConfigUpdate, user_id: str) -> Optional[dict]:
        """Update AI configuration"""
        try:
            update_dict = {k: v for k, v in config_data.dict(exclude_unset=True).items() if v is not None}
            
            # Don't store custom_api_key if using emergent key
            if update_dict.get("use_emergent_key"):
                update_dict["custom_api_key"] = None
            
            update_dict["updated_at"] = datetime.utcnow()
            update_dict["updated_by"] = user_id
            
            result = await mongo_db.update_one(
                AIConfigRepository.collection_name,
                {"company": company},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                return await AIConfigRepository.get_by_company(company)
            return None
        except Exception as e:
            logger.error(f"Error updating AI config: {e}")
            raise
