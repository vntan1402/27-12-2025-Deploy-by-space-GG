from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class GDriveConfigBase(BaseModel):
    """Base Google Drive Configuration model"""
    auth_method: str = Field(default="apps_script", description="Auth method: apps_script, oauth, service_account")
    web_app_url: Optional[str] = Field(default=None, description="Google Apps Script Web App URL")
    folder_id: Optional[str] = Field(default=None, description="Root folder ID in Google Drive")
    service_account_json: Optional[str] = Field(default=None, description="Service account JSON credentials")
    client_id: Optional[str] = Field(default=None, description="OAuth Client ID")
    client_secret: Optional[str] = Field(default=None, description="OAuth Client Secret")
    redirect_uri: Optional[str] = Field(default=None, description="OAuth Redirect URI")

class GDriveConfigCreate(GDriveConfigBase):
    """Model for creating Google Drive configuration"""
    pass

class GDriveConfigUpdate(BaseModel):
    """Model for updating Google Drive configuration"""
    auth_method: Optional[str] = None
    web_app_url: Optional[str] = None
    folder_id: Optional[str] = None
    service_account_json: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None

class GDriveConfigResponse(GDriveConfigBase):
    """Response model for Google Drive configuration"""
    id: str
    company: str
    is_configured: bool = False
    last_sync: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class GDriveSyncRequest(BaseModel):
    """Request model for Google Drive sync operations"""
    force: bool = Field(default=False, description="Force sync even if no changes")

class GDriveTestRequest(BaseModel):
    """Request model for testing Google Drive connection"""
    service_account_json: Optional[str] = None
    folder_id: Optional[str] = None
    web_app_url: Optional[str] = None

class GDriveProxyConfigRequest(BaseModel):
    """Request model for Apps Script proxy configuration"""
    web_app_url: str = Field(description="Google Apps Script Web App URL")
    folder_id: str = Field(description="Root folder ID in Google Drive")
