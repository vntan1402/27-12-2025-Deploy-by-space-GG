import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict

from app.core.security import get_current_user
from app.models.user import UserResponse
from app.utils.document_name_normalization import (
    normalize_document_name,
    add_custom_document_mapping,
    get_all_document_mappings,
    get_document_category
)
from app.utils.issued_by_abbreviation import (
    normalize_issued_by,
    add_custom_abbreviation,
    get_all_abbreviations
)

logger = logging.getLogger(__name__)
router = APIRouter()


class NormalizeRequest(BaseModel):
    """Request model for normalization"""
    text: str


class AddMappingRequest(BaseModel):
    """Request model for adding custom mapping"""
    pattern: str
    normalized: str


@router.post("/normalize-document-name")
async def api_normalize_document_name(
    request: NormalizeRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Normalize document name to standard format
    """
    try:
        normalized = normalize_document_name(request.text)
        category = get_document_category(request.text)
        
        return {
            "original": request.text,
            "normalized": normalized,
            "category": category
        }
    except Exception as e:
        logger.error(f"❌ Error normalizing document name: {e}")
        raise HTTPException(status_code=500, detail="Failed to normalize document name")


@router.post("/normalize-issued-by")
async def api_normalize_issued_by(
    request: NormalizeRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Normalize issued_by company name to abbreviation
    """
    try:
        normalized = normalize_issued_by(request.text)
        
        return {
            "original": request.text,
            "normalized": normalized
        }
    except Exception as e:
        logger.error(f"❌ Error normalizing issued_by: {e}")
        raise HTTPException(status_code=500, detail="Failed to normalize issued_by")


@router.get("/document-mappings")
async def get_document_mappings(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Get all registered document name mappings
    """
    try:
        return get_all_document_mappings()
    except Exception as e:
        logger.error(f"❌ Error getting document mappings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document mappings")


@router.get("/company-abbreviations")
async def get_company_abbreviations(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Get all registered company abbreviations
    """
    try:
        return get_all_abbreviations()
    except Exception as e:
        logger.error(f"❌ Error getting company abbreviations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get company abbreviations")


@router.post("/add-document-mapping")
async def add_document_mapping(
    request: AddMappingRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Add custom document name mapping (requires authentication)
    """
    try:
        add_custom_document_mapping(request.pattern, request.normalized)
        
        return {
            "message": "Document mapping added successfully",
            "pattern": request.pattern,
            "normalized": request.normalized
        }
    except Exception as e:
        logger.error(f"❌ Error adding document mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to add document mapping")


@router.post("/add-company-abbreviation")
async def add_company_abbreviation(
    request: AddMappingRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Add custom company abbreviation (requires authentication)
    """
    try:
        add_custom_abbreviation(request.pattern, request.normalized)
        
        return {
            "message": "Company abbreviation added successfully",
            "company_name": request.pattern,
            "abbreviation": request.normalized
        }
    except Exception as e:
        logger.error(f"❌ Error adding company abbreviation: {e}")
        raise HTTPException(status_code=500, detail="Failed to add company abbreviation")
