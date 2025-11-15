from fastapi import APIRouter

api_router = APIRouter()

# Routers will be included here as we create them
# Example:
# from app.api.v1 import auth, users
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(users.router, prefix="/users", tags=["users"])

__all__ = ["api_router"]
