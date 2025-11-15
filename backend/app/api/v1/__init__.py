from fastapi import APIRouter, Depends
from app.api.v1 import auth, users, companies
from app.core.security import get_current_user

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])

# IMPORTANT: Frontend compatibility routes
# Frontend calls /api/login and /api/verify-token
# but our clean routes are /api/auth/login and /api/auth/verify-token
# We create aliases here for backward compatibility

@api_router.post("/login")
async def login_alias(credentials: auth.LoginRequest):
    """Alias for /api/auth/login to support frontend"""
    return await auth.login(credentials)

@api_router.get("/verify-token")
async def verify_token_alias(current_user = Depends(get_current_user)):
    """Alias for /api/auth/verify-token to support frontend"""
    return await auth.verify_token(current_user)

__all__ = ["api_router"]
