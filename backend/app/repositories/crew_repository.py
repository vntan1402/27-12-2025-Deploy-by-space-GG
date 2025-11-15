import logging
from typing import Optional, List, Dict, Any
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class CrewRepository:
    """Data access layer for crew"""
    
    @staticmethod
    async def find_all(company_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all crew, optionally filtered by company"""
        if company_id:
            return await mongo_db.find_all("crew", {"company_id": company_id})
        return await mongo_db.find_all("crew")
    
    @staticmethod
    async def find_by_id(crew_id: str) -> Optional[Dict[str, Any]]:
        """Find crew by ID"""
        return await mongo_db.find_one("crew", {"id": crew_id})
    
    @staticmethod
    async def find_by_passport(passport: str, company_id: str) -> Optional[Dict[str, Any]]:
        """Find crew by passport number"""
        return await mongo_db.find_one("crew", {"passport": passport, "company_id": company_id})
    
    @staticmethod
    async def create(crew_data: Dict[str, Any]) -> str:
        """Create new crew member"""
        return await mongo_db.create("crew", crew_data)
    
    @staticmethod
    async def update(crew_id: str, update_data: Dict[str, Any]) -> bool:
        """Update crew member"""
        return await mongo_db.update("crew", {"id": crew_id}, update_data)
    
    @staticmethod
    async def delete(crew_id: str) -> bool:
        """Delete crew member"""
        return await mongo_db.delete("crew", {"id": crew_id})
    
    @staticmethod
    async def bulk_delete(crew_ids: List[str]) -> int:
        """Delete multiple crew members"""
        deleted_count = 0
        for crew_id in crew_ids:
            success = await mongo_db.delete("crew", {"id": crew_id})
            if success:
                deleted_count += 1
        return deleted_count
