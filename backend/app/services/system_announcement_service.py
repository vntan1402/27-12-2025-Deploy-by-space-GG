import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import HTTPException
from app.repositories.system_announcement_repository import SystemAnnouncementRepository
from app.models.system_announcement import SystemAnnouncementCreate, SystemAnnouncementUpdate, SystemAnnouncementResponse
from app.models.user import UserResponse

class SystemAnnouncementService:
    def __init__(self, repository: SystemAnnouncementRepository):
        self.repository = repository
    
    async def create_announcement(
        self, 
        announcement_data: SystemAnnouncementCreate,
        current_user: UserResponse
    ) -> SystemAnnouncementResponse:
        """Create a new system announcement"""
        
        # Validate dates
        try:
            start_date = datetime.fromisoformat(announcement_data.start_date.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(announcement_data.end_date.replace('Z', '+00:00'))
            
            if end_date < start_date:
                raise HTTPException(status_code=400, detail="End date must be after start date")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
        
        now = datetime.now(timezone.utc).isoformat()
        
        announcement_dict = {
            "id": str(uuid.uuid4()),
            **announcement_data.dict(),
            "created_by": current_user.username,
            "created_at": now,
            "updated_at": now
        }
        
        await self.repository.create(announcement_dict)
        
        return SystemAnnouncementResponse(**announcement_dict)
    
    async def get_announcement(self, announcement_id: str) -> SystemAnnouncementResponse:
        """Get announcement by ID"""
        announcement = await self.repository.find_by_id(announcement_id)
        
        if not announcement:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        return SystemAnnouncementResponse(**announcement)
    
    async def get_all_announcements(self, skip: int = 0, limit: int = 100) -> List[SystemAnnouncementResponse]:
        """Get all announcements (admin only)"""
        announcements = await self.repository.find_all(skip, limit)
        return [SystemAnnouncementResponse(**a) for a in announcements]
    
    async def get_active_announcements(self) -> List[SystemAnnouncementResponse]:
        """Get active announcements (public)"""
        announcements = await self.repository.find_active()
        return [SystemAnnouncementResponse(**a) for a in announcements]
    
    async def update_announcement(
        self,
        announcement_id: str,
        update_data: SystemAnnouncementUpdate,
        current_user: UserResponse
    ) -> SystemAnnouncementResponse:
        """Update announcement"""
        
        # Check if announcement exists
        existing = await self.repository.find_by_id(announcement_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        # Validate dates if provided
        if update_data.start_date and update_data.end_date:
            try:
                start_date = datetime.fromisoformat(update_data.start_date.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(update_data.end_date.replace('Z', '+00:00'))
                
                if end_date < start_date:
                    raise HTTPException(status_code=400, detail="End date must be after start date")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format")
        
        # Prepare update dict
        update_dict = {k: v for k, v in update_data.dict(exclude_unset=True).items() if v is not None}
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.repository.update(announcement_id, update_dict)
        
        # Get updated announcement
        updated = await self.repository.find_by_id(announcement_id)
        return SystemAnnouncementResponse(**updated)
    
    async def delete_announcement(self, announcement_id: str) -> dict:
        """Delete announcement"""
        
        # Check if announcement exists
        existing = await self.repository.find_by_id(announcement_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        deleted = await self.repository.delete(announcement_id)
        
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete announcement")
        
        return {"message": "Announcement deleted successfully"}
