import logging
from typing import Optional, List, Dict, Any
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class CompanyRepository:
    """Data access layer for companies"""
    
    @staticmethod
    async def find_all() -> List[Dict[str, Any]]:
        """Get all companies"""
        return await mongo_db.find_all("companies")
    
    @staticmethod
    async def find_by_id(company_id: str) -> Optional[Dict[str, Any]]:
        """Find company by ID"""
        return await mongo_db.find_one("companies", {"id": company_id})
    
    @staticmethod
    async def find_by_tax_id(tax_id: str) -> Optional[Dict[str, Any]]:
        """Find company by tax ID"""
        return await mongo_db.find_one("companies", {"tax_id": tax_id})
    
    @staticmethod
    async def create(company_data: Dict[str, Any]) -> str:
        """Create new company"""
        return await mongo_db.create("companies", company_data)
    
    @staticmethod
    async def update(company_id: str, update_data: Dict[str, Any]) -> bool:
        """Update company"""
        return await mongo_db.update("companies", {"id": company_id}, update_data)
    
    @staticmethod
    async def delete(company_id: str) -> bool:
        """Delete company"""
        return await mongo_db.delete("companies", {"id": company_id})
