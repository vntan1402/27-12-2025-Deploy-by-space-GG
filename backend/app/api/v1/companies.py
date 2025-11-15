import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.models.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.models.user import UserResponse, UserRole
from app.services.company_service import CompanyService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_admin_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has admin permission"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[CompanyResponse])
async def get_companies(current_user: UserResponse = Depends(get_current_user)):
    """
    Get all companies
    """
    try:
        return await CompanyService.get_all_companies(current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching companies: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch companies")

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company_by_id(
    company_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get a specific company by ID
    """
    try:
        return await CompanyService.get_company_by_id(company_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch company")

@router.post("", response_model=CompanyResponse)
async def create_company(
    company_data: CompanyCreate,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Create new company (Admin only)
    """
    try:
        return await CompanyService.create_company(company_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating company: {e}")
        raise HTTPException(status_code=500, detail="Failed to create company")

@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_data: CompanyUpdate,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Update company (Admin only)
    """
    try:
        return await CompanyService.update_company(company_id, company_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating company: {e}")
        raise HTTPException(status_code=500, detail="Failed to update company")

@router.delete("/{company_id}")
async def delete_company(
    company_id: str,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Delete company (Admin only)
    """
    try:
        return await CompanyService.delete_company(company_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting company: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete company")

@router.post("/{company_id}/upload-logo")
async def upload_company_logo(
    company_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Upload company logo (Admin only)
    """
    try:
        return await CompanyService.upload_logo(company_id, file, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading company logo: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload company logo: {str(e)}")
