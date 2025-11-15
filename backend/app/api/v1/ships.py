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

@router.post("/{ship_id}/calculate-anniversary-date")
async def calculate_anniversary_date(
    ship_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Calculate anniversary date from Full Term certificates (Editor+ role required)
    """
    try:
        return await ShipService.calculate_anniversary_date(ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error calculating anniversary date: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate anniversary date")

@router.post("/{ship_id}/calculate-special-survey-cycle")
async def calculate_special_survey_cycle(
    ship_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Calculate special survey cycle from Full Term Class certificates (Editor+ role required)
    """
    try:
        return await ShipService.calculate_special_survey_cycle(ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error calculating special survey cycle: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate special survey cycle")

@router.post("/{ship_id}/calculate-next-docking")
async def calculate_next_docking(
    ship_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Calculate next docking date from last docking (Editor+ role required)
    """
    try:
        return await ShipService.calculate_next_docking_date(ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error calculating next docking: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate next docking")

@router.post("/{ship_id}/logo")
async def upload_ship_logo(
    ship_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload ship logo (Editor+ role required)
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed")
        
        # Validate file size (5MB limit)
        if file.size and file.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 5MB")
        
        # Verify ship exists
        ship = await ShipService.get_ship_by_id(ship_id, current_user)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Create uploads directory
        import os
        from pathlib import Path
        
        upload_dir = Path(f"/app/uploads/ships/{ship_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine file extension
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        file_path = upload_dir / f"logo.{ext}"
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Update ship with logo path
        logo_url = f"/uploads/ships/{ship_id}/logo.{ext}"
        await ShipService.update_ship(
            ship_id,
            {"logo": logo_url},
            current_user
        )
        
        logger.info(f"✅ Ship logo uploaded: {ship_id}")
        
        return {
            "message": "Logo uploaded successfully",
            "logo_url": logo_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading ship logo: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload logo")

@router.get("/{ship_id}/logo")
async def get_ship_logo(
    ship_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get ship logo URL
    """
    try:
        ship = await ShipService.get_ship_by_id(ship_id, current_user)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        logo_url = ship.logo if hasattr(ship, 'logo') else None
        
        if not logo_url:
            raise HTTPException(status_code=404, detail="Ship has no logo")
        
        return {
            "logo_url": logo_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting ship logo: {e}")
        raise HTTPException(status_code=500, detail="Failed to get logo")
