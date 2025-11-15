import logging
from typing import Optional
from datetime import datetime
import uuid

from app.db.mongodb import mongo_db
from app.models.gdrive_config import GDriveConfigCreate, GDriveConfigUpdate

logger = logging.getLogger(__name__)

class GDriveConfigRepository:
    """Repository for Google Drive Configuration operations"""
    
    collection_name = "gdrive_config"
    
    @staticmethod
    async def get_by_company(company: str) -> Optional[dict]:
        """Get Google Drive config by company"""
        try:
            config = await mongo_db.find_one(
                GDriveConfigRepository.collection_name,
                {"company": company}
            )
            return config
        except Exception as e:
            logger.error(f"Error getting GDrive config for company {company}: {e}")
            raise
    
    @staticmethod
    async def create(config_data: GDriveConfigCreate, company: str, user_id: str) -> dict:
        """Create new Google Drive configuration"""
        try:
            config_dict = {
                "id": str(uuid.uuid4()),
                "company": company,
                **config_data.dict(),
                "is_configured": bool(config_data.folder_id),
                "last_sync": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "updated_by": user_id
            }
            
            result = await mongo_db.insert_one(
                GDriveConfigRepository.collection_name,
                config_dict
            )
            
            return config_dict
        except Exception as e:
            logger.error(f"Error creating GDrive config: {e}")
            raise
    
    @staticmethod
    async def update(company: str, config_data: GDriveConfigUpdate, user_id: str) -> Optional[dict]:
        """Update Google Drive configuration"""
        try:
            update_dict = {k: v for k, v in config_data.dict(exclude_unset=True).items() if v is not None}
            
            update_dict["updated_at"] = datetime.utcnow()
            update_dict["updated_by"] = user_id
            
            # Update is_configured status
            if "folder_id" in update_dict:
                update_dict["is_configured"] = bool(update_dict["folder_id"])
            
            result = await mongo_db.update_one(
                GDriveConfigRepository.collection_name,
                {"company": company},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0 or result.matched_count > 0:
                return await GDriveConfigRepository.get_by_company(company)
            return None
        except Exception as e:
            logger.error(f"Error updating GDrive config: {e}")
            raise
    
    @staticmethod
    async def update_last_sync(company: str) -> bool:
        """Update last sync timestamp"""
        try:
            result = await mongo_db.update_one(
                GDriveConfigRepository.collection_name,
                {"company": company},
                {"$set": {"last_sync": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating last sync: {e}")
            return False
