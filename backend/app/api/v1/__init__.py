from fastapi import APIRouter
from app.api.v1 import auth, users

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

# IMPORTANT: Frontend compatibility route
# Frontend calls /api/login but our clean route is /api/auth/login
# We create an alias here for backward compatibility
@api_router.post("/login")
async def login_alias(credentials: auth.LoginRequest):
    """Alias for /api/auth/login to support frontend"""
    return await auth.login(credentials)

__all__ = ["api_router"]
