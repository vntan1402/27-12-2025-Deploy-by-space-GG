from typing import List, Optional
from datetime import datetime, timezone

class SystemAnnouncementRepository:
    def __init__(self, db):
        self.collection = db["system_announcements"]
    
    async def create(self, announcement_dict: dict) -> dict:
        """Create a new announcement"""
        await self.collection.insert_one(announcement_dict)
        return announcement_dict
    
    async def find_by_id(self, announcement_id: str) -> Optional[dict]:
        """Find announcement by ID"""
        return await self.collection.find_one({"id": announcement_id}, {"_id": 0})
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Find all announcements (for admin management)"""
        cursor = self.collection.find({}, {"_id": 0}).sort("priority", -1).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def find_active(self) -> List[dict]:
        """Find active announcements within date range"""
        now = datetime.now(timezone.utc).isoformat()
        
        query = {
            "is_active": True,
            "start_date": {"$lte": now},
            "end_date": {"$gte": now}
        }
        
        cursor = self.collection.find(query, {"_id": 0}).sort("priority", -1).sort("created_at", -1)
        return await cursor.to_list(length=None)
    
    async def update(self, announcement_id: str, update_data: dict) -> bool:
        """Update announcement"""
        result = await self.collection.update_one(
            {"id": announcement_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def delete(self, announcement_id: str) -> bool:
        """Delete announcement"""
        result = await self.collection.delete_one({"id": announcement_id})
        return result.deleted_count > 0
    
    async def count(self) -> int:
        """Count total announcements"""
        return await self.collection.count_documents({})
