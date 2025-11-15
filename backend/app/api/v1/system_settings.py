import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.user import UserResponse, UserRole
from app.core.security import get_current_user
from app.db.mongodb import mongo_db
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()

def check_admin_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has admin permission"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("/base-fee")
async def get_base_fee(current_user: UserResponse = Depends(get_current_user)):
    """
    Get system-wide base fee
    """
    try:
        # Fetch base fee from system_settings collection
        settings = await mongo_db.find_one("system_settings", {"setting_key": "base_fee"})
        
        if settings and "value" in settings:
            return {
                "success": True,
                "base_fee": settings["value"]
            }
        
        # Return default if not found
        return {
            "success": True,
            "base_fee": 0.0
        }
    except Exception as e:
        logger.error(f"❌ Error fetching base fee: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/base-fee")
async def update_base_fee(
    base_fee: float = Query(..., description="New base fee value"),
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Update system-wide base fee (Admin only)
    """
    try:
        # Validation
        if base_fee < 0:
            raise HTTPException(status_code=400, detail="Base fee must be non-negative")
        
        # Upsert base fee setting
        await mongo_db.update(
            "system_settings",
            {"setting_key": "base_fee"},
            {
                "setting_key": "base_fee",
                "value": base_fee,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": current_user.id
            },
            upsert=True
        )
        
        logger.info(f"✅ Base fee updated to {base_fee} by user {current_user.username}")
        
        return {
            "success": True,
            "message": "Base fee updated successfully",
            "base_fee": base_fee
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating base fee: {e}")
        raise HTTPException(status_code=500, detail=str(e))
