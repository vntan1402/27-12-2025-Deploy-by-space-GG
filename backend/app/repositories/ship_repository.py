import logging
from typing import Optional, List, Dict, Any
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class ShipRepository:
    """Data access layer for ships"""
    
    @staticmethod
    async def find_all(company: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all ships, optionally filtered by company"""
        if company:
            return await mongo_db.find_all("ships", {"company": company})
        return await mongo_db.find_all("ships")
    
    @staticmethod
    async def find_by_id(ship_id: str) -> Optional[Dict[str, Any]]:
        """Find ship by ID"""
        return await mongo_db.find_one("ships", {"id": ship_id})
    
    @staticmethod
    async def find_by_imo(imo: str, company: str) -> Optional[Dict[str, Any]]:
        """Find ship by IMO number and company"""
        return await mongo_db.find_one("ships", {"imo": imo, "company": company})
    
    @staticmethod
    async def create(ship_data: Dict[str, Any]) -> str:
        """Create new ship"""
        return await mongo_db.create("ships", ship_data)
    
    @staticmethod
    async def update(ship_id: str, update_data: Dict[str, Any]) -> bool:
        """Update ship"""
        return await mongo_db.update("ships", {"id": ship_id}, update_data)
    
    @staticmethod
    async def delete(ship_id: str) -> bool:
        """Delete ship"""
        return await mongo_db.delete("ships", {"id": ship_id})
