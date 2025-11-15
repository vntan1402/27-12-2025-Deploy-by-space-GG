import logging
from fastapi import APIRouter, Depends, HTTPException

from app.models.user import LoginRequest, LoginResponse, UserResponse
from app.services.user_service import UserService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    Authenticate user and return access token
    
    This endpoint handles login from /api/auth/login
    """
    try:
        logger.info(f"📝 Login request for: {credentials.username}")
        
        access_token, user = await UserService.authenticate(
            credentials.username, 
            credentials.password,
            credentials.remember_me
        )
        
        logger.info(f"✅ Login successful for: {credentials.username}")
        
        return LoginResponse(
            access_token=access_token,
            user=user,
            remember_me=credentials.remember_me
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.get("/verify-token")
async def verify_token(current_user: UserResponse = Depends(get_current_user)):
    """
    Verify if the current token is valid and return user info
    """
    try:
        return {
            "valid": True,
            "user": current_user.dict()
        }
    except Exception as e:
        logger.error(f"❌ Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
