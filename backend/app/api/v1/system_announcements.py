import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.models.system_announcement import (
    SystemAnnouncementCreate,
    SystemAnnouncementUpdate,
    SystemAnnouncementResponse
)
from app.models.user import UserResponse
from app.services.system_announcement_service import SystemAnnouncementService
from app.repositories.system_announcement_repository import SystemAnnouncementRepository
from app.db.mongodb import mongo_db
from app.auth.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def get_announcement_service():
    """Dependency to get SystemAnnouncementService"""
    repository = SystemAnnouncementRepository(mongo_db.database)
    return SystemAnnouncementService(repository)

def check_system_admin_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user is system_admin or super_admin"""
    if current_user.role not in ['system_admin', 'super_admin']:
        raise HTTPException(
            status_code=403,
            detail="Only system administrators can manage announcements"
        )
    return current_user

@router.get("/active", response_model=List[SystemAnnouncementResponse])
async def get_active_announcements(
    service: SystemAnnouncementService = Depends(get_announcement_service)
):
    """
    Get active announcements (PUBLIC - no auth required)
    
    Returns announcements where:
    - is_active = true
    - current date is between start_date and end_date
    """
    try:
        announcements = await service.get_active_announcements()
        logger.info(f"✅ Retrieved {len(announcements)} active announcements")
        return announcements
    except Exception as e:
        logger.error(f"Error getting active announcements: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active announcements")

@router.get("", response_model=List[SystemAnnouncementResponse])
async def get_all_announcements(
    skip: int = 0,
    limit: int = 100,
    current_user: UserResponse = Depends(check_system_admin_permission),
    service: SystemAnnouncementService = Depends(get_announcement_service)
):
    """
    Get all announcements (ADMIN ONLY)
    
    For announcement management in admin panel.
    """
    try:
        announcements = await service.get_all_announcements(skip, limit)
        logger.info(f"✅ Retrieved {len(announcements)} announcements for admin")
        return announcements
    except Exception as e:
        logger.error(f"Error getting all announcements: {e}")
        raise HTTPException(status_code=500, detail="Failed to get announcements")

@router.get("/{announcement_id}", response_model=SystemAnnouncementResponse)
async def get_announcement(
    announcement_id: str,
    current_user: UserResponse = Depends(check_system_admin_permission),
    service: SystemAnnouncementService = Depends(get_announcement_service)
):
    """Get announcement by ID (ADMIN ONLY)"""
    try:
        announcement = await service.get_announcement(announcement_id)
        return announcement
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting announcement {announcement_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get announcement")

@router.post("", response_model=SystemAnnouncementResponse)
async def create_announcement(
    announcement_data: SystemAnnouncementCreate,
    current_user: UserResponse = Depends(check_system_admin_permission),
    service: SystemAnnouncementService = Depends(get_announcement_service)
):
    """Create new announcement (ADMIN ONLY)"""
    try:
        announcement = await service.create_announcement(announcement_data, current_user)
        logger.info(f"✅ Announcement created: {announcement.id} by {current_user.username}")
        return announcement
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating announcement: {e}")
        raise HTTPException(status_code=500, detail="Failed to create announcement")

@router.put("/{announcement_id}", response_model=SystemAnnouncementResponse)
async def update_announcement(
    announcement_id: str,
    update_data: SystemAnnouncementUpdate,
    current_user: UserResponse = Depends(check_system_admin_permission),
    service: SystemAnnouncementService = Depends(get_announcement_service)
):
    """Update announcement (ADMIN ONLY)"""
    try:
        announcement = await service.update_announcement(announcement_id, update_data, current_user)
        logger.info(f"✅ Announcement updated: {announcement_id} by {current_user.username}")
        return announcement
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating announcement {announcement_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update announcement")

@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: str,
    current_user: UserResponse = Depends(check_system_admin_permission),
    service: SystemAnnouncementService = Depends(get_announcement_service)
):
    """Delete announcement (ADMIN ONLY)"""
    try:
        result = await service.delete_announcement(announcement_id)
        logger.info(f"✅ Announcement deleted: {announcement_id} by {current_user.username}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting announcement {announcement_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete announcement")
