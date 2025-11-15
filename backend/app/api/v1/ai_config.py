import logging
from fastapi import APIRouter, Depends, HTTPException

from app.models.ai_config import AIConfigUpdate, AIConfigResponse
from app.models.user import UserResponse, UserRole
from app.services.ai_config_service import AIConfigService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def check_admin_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has admin or higher permission"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Admin permission required")
    return current_user

@router.get("", response_model=AIConfigResponse)
async def get_ai_config(
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Get AI configuration for current company (Admin+ role required)
    """
    try:
        return await AIConfigService.get_ai_config(current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting AI config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI configuration")

@router.put("", response_model=AIConfigResponse)
async def update_ai_config(
    config_data: AIConfigUpdate,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Update AI configuration (Admin+ role required)
    """
    try:
        return await AIConfigService.update_ai_config(config_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating AI config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update AI configuration")

@router.post("", response_model=AIConfigResponse)
async def create_or_update_ai_config(
    config_data: AIConfigUpdate,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Create or update AI configuration (Admin+ role required) - Frontend compatibility
    """
    try:
        return await AIConfigService.update_ai_config(config_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating AI config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update AI configuration")

@router.post("/test-document-ai")
async def test_document_ai_connection(
    test_config: dict,
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Test Google Document AI connection (Admin+ role required)
    """
    try:
        project_id = test_config.get("project_id")
        location = test_config.get("location", "us")
        processor_id = test_config.get("processor_id")
        
        if not project_id or not processor_id:
            raise HTTPException(status_code=400, detail="Project ID and Processor ID are required")
            
        logger.info(f"🧪 Testing Document AI connection: Project={project_id}, Processor={processor_id}")
        
        # For now, return a mock success response
        # TODO: Implement actual Document AI testing via Apps Script
        return {
            "success": True,
            "message": "Document AI test endpoint available (implementation pending)",
            "processor_name": "Test Processor",
            "processor_type": "OCR_PROCESSOR"
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Document AI test error: {e}")
        raise HTTPException(status_code=500, detail="Failed to test Document AI connection")
