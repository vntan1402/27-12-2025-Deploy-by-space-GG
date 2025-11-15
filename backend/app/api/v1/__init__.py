from fastapi import APIRouter, Depends, UploadFile, File
from app.api.v1 import (
    auth, users, companies, ships, certificates, crew, crew_certificates,
    survey_reports, test_reports, drawings_manuals, other_documents,
    supply_documents, ai_config, utilities, gdrive, audit_reports,
    audit_certificates, approval_documents, other_audit_documents, system_settings,
    ships_analysis, sidebar
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
api_router.include_router(system_settings.router, prefix="/system-settings", tags=["system-settings"])
api_router.include_router(ships_analysis.router, prefix="", tags=["ships-analysis"])
api_router.include_router(sidebar.router, prefix="", tags=["sidebar"])

# Document type routers
api_router.include_router(survey_reports.router, prefix="/survey-reports", tags=["survey-reports"])
api_router.include_router(test_reports.router, prefix="/test-reports", tags=["test-reports"])
api_router.include_router(drawings_manuals.router, prefix="/drawings-manuals", tags=["drawings-manuals"])
api_router.include_router(other_documents.router, prefix="/other-documents", tags=["other-documents"])
# ISM/ISPS/MLC endpoints removed - not used by frontend
# Frontend uses unified /api/audit-reports endpoint instead
api_router.include_router(supply_documents.router, prefix="/supply-documents", tags=["supply-documents"])

# AI Configuration router
api_router.include_router(ai_config.router, prefix="/ai-config", tags=["ai-config"])

# Utilities router
api_router.include_router(utilities.router, prefix="/utilities", tags=["utilities"])

# Google Drive router
api_router.include_router(gdrive.router, prefix="/gdrive", tags=["google-drive"])

# Audit Reports router (unified ISM/ISPS/MLC)
api_router.include_router(audit_reports.router, prefix="/audit-reports", tags=["audit-reports"])

# Audit Certificates router (ISM/ISPS/MLC certificates)
api_router.include_router(audit_certificates.router, prefix="/audit-certificates", tags=["audit-certificates"])

# Approval Documents router
api_router.include_router(approval_documents.router, prefix="/approval-documents", tags=["approval-documents"])

# Other Audit Documents router
api_router.include_router(other_audit_documents.router, prefix="/other-audit-documents", tags=["other-audit-documents"])

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

# AI Config compatibility route removed - now handled by /api/ai-config router

__all__ = ["api_router"]

@api_router.post("/analyze-ship-certificate")
async def analyze_ship_certificate(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Analyze ship certificate for Add Ship feature - Frontend compatibility"""

@api_router.post("/passport/analyze-file")
async def analyze_passport_file(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Analyze passport file - Frontend compatibility"""
    return await crew.analyze_passport_file(file=file, current_user=current_user)

    return await certificates.analyze_certificate_file(file=file, ship_id=None, current_user=current_user)

@api_router.post("/test-document-ai")
async def test_document_ai(
    test_config: dict,
    current_user = Depends(get_current_user)
):
    """Test Document AI connection - Frontend compatibility"""
    return await ai_config.test_document_ai_connection(test_config=test_config, current_user=current_user)

# Ship certificate analysis is handled by ships_analysis router
# Registered below in include_router section

