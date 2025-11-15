import logging
from typing import Optional
from fastapi import HTTPException

from app.models.ai_config import AIConfigCreate, AIConfigUpdate, AIConfigResponse
from app.models.user import UserResponse
from app.repositories.ai_config_repository import AIConfigRepository

logger = logging.getLogger(__name__)

class AIConfigService:
    """Service for AI Configuration business logic"""
    
    @staticmethod
    async def get_ai_config(current_user: UserResponse) -> AIConfigResponse:
        """Get AI configuration for current user's company"""
        try:
            if not current_user.company:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            config = await AIConfigRepository.get_by_company(current_user.company)
            
            # If no config exists, create default
            if not config:
                logger.info(f"No AI config found for company {current_user.company}, creating default")
                default_config = AIConfigCreate(
                    provider="google",
                    model="gemini-2.0-flash",
                    use_emergent_key=True,
                    temperature=0.1,
                    max_tokens=2000
                )
                config = await AIConfigRepository.create(
                    default_config,
                    current_user.company,
                    current_user.id
                )
            
            return AIConfigResponse(**config)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting AI config: {e}")
            raise HTTPException(status_code=500, detail="Failed to get AI configuration")
    
    @staticmethod
    async def update_ai_config(
        config_data: AIConfigUpdate,
        current_user: UserResponse
    ) -> AIConfigResponse:
        """Update AI configuration"""
        try:
            if not current_user.company:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            
            # Note: Provider validation removed for flexibility
            # Backend-v1 accepts any provider value
            # Common providers: openai, google, anthropic, but others may be added
            
            # Check if config exists
            existing_config = await AIConfigRepository.get_by_company(current_user.company)
            
            if existing_config:
                # Update existing config
                updated_config = await AIConfigRepository.update(
                    current_user.company,
                    config_data,
                    current_user.id
                )
                if not updated_config:
                    raise HTTPException(status_code=404, detail="Failed to update AI configuration")
            else:
                # Create new config
                create_data = AIConfigCreate(
                    provider=config_data.provider or "google",
                    model=config_data.model or "gemini-2.0-flash",
                    use_emergent_key=config_data.use_emergent_key if config_data.use_emergent_key is not None else True,
                    custom_api_key=config_data.custom_api_key,
                    temperature=config_data.temperature if config_data.temperature is not None else 0.1,
                    max_tokens=config_data.max_tokens or 2000
                )
                updated_config = await AIConfigRepository.create(
                    create_data,
                    current_user.company,
                    current_user.id
                )
            
            return AIConfigResponse(**updated_config)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating AI config: {e}")
            raise HTTPException(status_code=500, detail="Failed to update AI configuration")
