from fastapi import APIRouter, Depends
from app.api.v1 import (
    auth, users, companies, ships, certificates, crew, crew_certificates,
    survey_reports, test_reports, drawings_manuals, other_documents,
    ism_documents, isps_documents, mlc_documents, supply_documents
)
from app.core.security import get_current_user

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(ships.router, prefix="/ships", tags=["ships"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["certificates"])
api_router.include_router(crew.router, prefix="/crew", tags=["crew"])
api_router.include_router(crew_certificates.router, prefix="/crew-certificates", tags=["crew-certificates"])

# Document type routers
api_router.include_router(survey_reports.router, prefix="/survey-reports", tags=["survey-reports"])
api_router.include_router(test_reports.router, prefix="/test-reports", tags=["test-reports"])
api_router.include_router(drawings_manuals.router, prefix="/drawings-manuals", tags=["drawings-manuals"])
api_router.include_router(other_documents.router, prefix="/other-documents", tags=["other-documents"])
api_router.include_router(ism_documents.router, prefix="/ism-documents", tags=["ism-documents"])
api_router.include_router(isps_documents.router, prefix="/isps-documents", tags=["isps-documents"])
api_router.include_router(mlc_documents.router, prefix="/mlc-documents", tags=["mlc-documents"])
api_router.include_router(supply_documents.router, prefix="/supply-documents", tags=["supply-documents"])

# IMPORTANT: Frontend compatibility routes
# Frontend calls various endpoints differently than our clean architecture
# We create aliases here for backward compatibility

@api_router.post("/login")
async def login_alias(credentials: auth.LoginRequest):
    """Alias for /api/auth/login to support frontend"""
    return await auth.login(credentials)

@api_router.get("/verify-token")
async def verify_token_alias(current_user = Depends(get_current_user)):
    """Alias for /api/auth/verify-token to support frontend"""
    return await auth.verify_token(current_user)

@api_router.get("/company")
async def get_current_user_company(current_user = Depends(get_current_user)):
    """Get current user's company - Frontend compatibility"""
    if not current_user.company:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User has no company assigned")
    return await companies.get_company_by_id(current_user.company, current_user)

@api_router.get("/ships/{ship_id}/certificates")
async def get_ship_certificates_alias(ship_id: str, current_user = Depends(get_current_user)):
    """Get certificates for a ship - Frontend compatibility"""
    return await certificates.get_certificates(ship_id=ship_id, current_user=current_user)

@api_router.get("/ai-config")
async def get_ai_config(current_user = Depends(get_current_user)):
    """Get AI configuration - Placeholder for frontend compatibility"""
    return {
        "provider": "openai",
        "model": "gpt-4",
        "use_emergent_key": True
    }

__all__ = ["api_router"]
