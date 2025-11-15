import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.models.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("", response_model=List[UserResponse])
async def get_users(current_user: UserResponse = Depends(get_current_user)):
    """
    Get users list with role-based filtering
    """
    try:
        return await UserService.get_all_users(current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")

@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create new user
    """
    try:
        return await UserService.create_user(user_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update user
    """
    try:
        return await UserService.update_user(user_id, update_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete user
    """
    try:
        return await UserService.delete_user(user_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")
