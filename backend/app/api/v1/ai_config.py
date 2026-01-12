import logging
from fastapi import APIRouter, Depends, HTTPException

from app.models.ai_config import AIConfigUpdate, AIConfigResponse
from app.models.user import UserResponse, UserRole
from app.services.ai_config_service import AIConfigService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()
from app.core import messages
# Original: from app.core.messages import ADMIN_ONLY

def check_admin_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has admin or higher permission"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail=messages.ADMIN_ONLY)
    return current_user

@router.get("", response_model=AIConfigResponse)
async def get_ai_config(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get AI configuration for current company (All authenticated users can view)
    Note: Only Admin+ can update AI config
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
        # Clear API key cache when config is updated
        from app.utils.llm_wrapper import clear_api_key_cache
        clear_api_key_cache()
        
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
        # Clear API key cache when config is updated
        from app.utils.llm_wrapper import clear_api_key_cache
        clear_api_key_cache()
        
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


@router.post("/test-ai-connection")
async def test_ai_connection(
    current_user: UserResponse = Depends(check_admin_permission)
):
    """
    Test AI connection with current configuration (Admin+ role required)
    """
    try:
        from app.utils.llm_wrapper import LlmChat, UserMessage
        
        # Get current AI config
        ai_config_response = await AIConfigService.get_ai_config(current_user)
        ai_config = {
            'provider': ai_config_response.provider,
            'model': ai_config_response.model,
            'use_emergent_key': ai_config_response.use_emergent_key,
            'custom_api_key': ai_config_response.custom_api_key,
            'temperature': ai_config_response.temperature,
        }
        
        logger.info(f"🧪 Testing AI connection with config: use_emergent_key={ai_config['use_emergent_key']}, has_custom_key={bool(ai_config['custom_api_key'])}")
        
        # Create LlmChat and test
        chat = LlmChat(ai_config=ai_config).with_model("gemini", ai_config['model'] or "gemini-2.0-flash")
        
        # Simple test
        response = await chat.send_message(UserMessage(text="Say 'Connection successful' in exactly those two words."))
        
        return {
            "success": True,
            "message": "AI connection test successful",
            "response": str(response).strip()[:100],
            "config": {
                "provider": ai_config['provider'],
                "model": ai_config['model'],
                "use_emergent_key": ai_config['use_emergent_key'],
                "has_custom_api_key": bool(ai_config['custom_api_key'])
            }
        }
            
    except Exception as e:
        logger.error(f"❌ AI connection test error: {e}")
        return {
            "success": False,
            "message": f"AI connection test failed: {str(e)}",
            "config": {
                "use_emergent_key": ai_config.get('use_emergent_key') if 'ai_config' in dir() else None,
                "has_custom_api_key": bool(ai_config.get('custom_api_key')) if 'ai_config' in dir() else None
            }
        }
