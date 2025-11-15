import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.models.ship import ShipCreate, ShipUpdate, ShipResponse
from app.models.user import UserResponse, UserRole
from app.services.ship_service import ShipService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[ShipResponse])
async def get_ships(current_user: UserResponse = Depends(get_current_user)):
    """
    Get all ships (filtered by company for non-admin users)
    """
    try:
        return await ShipService.get_all_ships(current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching ships: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ships")

@router.get("/{ship_id}", response_model=ShipResponse)
async def get_ship_by_id(
    ship_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get a specific ship by ID
    """
    try:
        return await ShipService.get_ship_by_id(ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching ship {ship_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ship")

@router.post("", response_model=ShipResponse)
async def create_ship(
    ship_data: ShipCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Create new ship (Editor+ role required)
    """
    try:
        return await ShipService.create_ship(ship_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating ship: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ship")

@router.put("/{ship_id}", response_model=ShipResponse)
async def update_ship(
    ship_id: str,
    ship_data: ShipUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Update ship (Editor+ role required)
    """
    try:
        return await ShipService.update_ship(ship_id, ship_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating ship: {e}")
        raise HTTPException(status_code=500, detail="Failed to update ship")

@router.delete("/{ship_id}")
async def delete_ship(
    ship_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Delete ship (Editor+ role required)
    """
    try:
        return await ShipService.delete_ship(ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting ship: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete ship")

# TODO: Add calculation endpoints
# - POST /ships/{ship_id}/calculate-anniversary-date
# - POST /ships/{ship_id}/calculate-next-docking
# - POST /ships/{ship_id}/calculate-special-survey-cycle
