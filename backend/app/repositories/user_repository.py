import logging
from typing import Optional, List, Dict, Any
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class UserRepository:
    """Data access layer for users"""
    
    @staticmethod
    async def find_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Find user by username"""
        return await mongo_db.find_one("users", {"username": username})
    
    @staticmethod
    async def find_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Find user by email"""
        return await mongo_db.find_one("users", {"email": email})
    
    @staticmethod
    async def find_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by ID"""
        return await mongo_db.find_one("users", {"id": user_id})
    
    @staticmethod
    async def find_all() -> List[Dict[str, Any]]:
        """Get all users"""
        return await mongo_db.find_all("users")
    
    @staticmethod
    async def find_by_company(company: str) -> List[Dict[str, Any]]:
        """Find users by company"""
        return await mongo_db.find_all("users", {"company": company, "is_active": True})
    
    @staticmethod
    async def create(user_data: Dict[str, Any]) -> str:
        """Create new user"""
        return await mongo_db.create("users", user_data)
    
    @staticmethod
    async def update(user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user"""
        return await mongo_db.update("users", {"id": user_id}, update_data)
    
    @staticmethod
    async def delete(user_id: str) -> bool:
        """Delete user"""
        return await mongo_db.delete("users", {"id": user_id})
