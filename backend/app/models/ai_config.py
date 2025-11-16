from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class DocumentAIConfig(BaseModel):
    """Google Document AI Configuration"""
    enabled: bool = Field(default=False, description="Enable Document AI")
    project_id: Optional[str] = Field(default=None, description="GCP Project ID")
    processor_id: Optional[str] = Field(default=None, description="Document AI Processor ID")
    location: Optional[str] = Field(default="us", description="Document AI location")
    apps_script_url: Optional[str] = Field(default=None, description="Apps Script URL for Document AI")

class AIConfigBase(BaseModel):
    """Base AI Configuration model"""
    provider: str = Field(default="google", description="AI provider: openai, google, anthropic")
    model: str = Field(default="gemini-2.0-flash", description="AI model name")
    use_emergent_key: bool = Field(default=True, description="Use Emergent LLM key")
    custom_api_key: Optional[str] = Field(default=None, description="Custom API key (optional)")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0, description="Temperature for AI generation")
    max_tokens: int = Field(default=2000, ge=100, le=8000, description="Maximum tokens for response")
    document_ai: Optional[Dict[str, Any]] = Field(default=None, description="Google Document AI configuration")

class AIConfigCreate(AIConfigBase):
    """Model for creating AI configuration"""
    pass

class AIConfigUpdate(BaseModel):
    """Model for updating AI configuration"""
    provider: Optional[str] = None
    model: Optional[str] = None
    use_emergent_key: Optional[bool] = None
    custom_api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class AIConfigResponse(AIConfigBase):
    """Response model for AI configuration"""
    id: str
    company: str
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
