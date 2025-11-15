import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.models.crew import CrewCreate, CrewUpdate, CrewResponse, BulkDeleteCrewRequest
from app.models.user import UserResponse, UserRole
from app.services.crew_service import CrewService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[CrewResponse])
async def get_crew(current_user: UserResponse = Depends(get_current_user)):
    """
    Get all crew members (filtered by company for non-admin users)
    """
    try:
        return await CrewService.get_all_crew(current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching crew: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch crew")

@router.get("/{crew_id}", response_model=CrewResponse)
async def get_crew_by_id(
    crew_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get a specific crew member by ID
    """
    try:
        return await CrewService.get_crew_by_id(crew_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching crew {crew_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch crew member")

@router.post("", response_model=CrewResponse)
async def create_crew(
    crew_data: CrewCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Create new crew member (Editor+ role required)
    """
    try:
        return await CrewService.create_crew(crew_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating crew: {e}")
        raise HTTPException(status_code=500, detail="Failed to create crew member")

@router.put("/{crew_id}", response_model=CrewResponse)
async def update_crew(
    crew_id: str,
    crew_data: CrewUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Update crew member (Editor+ role required)
    """
    try:
        return await CrewService.update_crew(crew_id, crew_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating crew: {e}")
        raise HTTPException(status_code=500, detail="Failed to update crew member")

@router.delete("/{crew_id}")
async def delete_crew(
    crew_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Delete crew member (Editor+ role required)
    """
    try:
        return await CrewService.delete_crew(crew_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting crew: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete crew member")

@router.post("/bulk-delete")
async def bulk_delete_crew(
    request: BulkDeleteCrewRequest,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Bulk delete crew members (Editor+ role required)
    """
    try:
        return await CrewService.bulk_delete_crew(request, current_user)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting crew: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete crew members")

# TODO: Add additional crew endpoints
# - POST /crew/move-standby-files
# - POST /passport/analyze-file
