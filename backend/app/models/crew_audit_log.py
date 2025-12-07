"""
Crew Audit Log Models
Pydantic models for crew audit trail logging
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Literal
from datetime import datetime


class ChangeRecord(BaseModel):
    """Individual field change record"""
    field: str = Field(..., description="Field name (e.g., 'ship_sign_on')")
    field_label: str = Field(..., description="Display label (e.g., 'Ship Sign On')")
    old_value: Any = Field(None, description="Previous value")
    new_value: Any = Field(None, description="New value")
    value_type: str = Field(default="string", description="Data type: string, number, date, boolean")


class CrewAuditLogBase(BaseModel):
    """Base model for crew audit log"""
    entity_type: str = Field(default="crew", description="Entity type (always 'crew' for now)")
    entity_id: str = Field(..., description="Crew ID")
    entity_name: str = Field(..., description="Crew full name")
    company_id: str = Field(..., description="Company ID for multi-tenant isolation")
    ship_name: Optional[str] = Field(None, description="Current or relevant ship name")
    
    action: Literal["CREATE", "UPDATE", "DELETE", "SIGN_ON", "SIGN_OFF", "SHIP_TRANSFER", "BULK_UPDATE"] = Field(
        ..., description="Action performed"
    )
    action_category: Literal["LIFECYCLE", "DATA_CHANGE", "STATUS_CHANGE"] = Field(
        ..., description="Category of action"
    )
    
    performed_by: str = Field(..., description="Username who performed the action")
    performed_by_id: str = Field(..., description="User ID")
    performed_by_name: str = Field(..., description="User full name")
    performed_at: datetime = Field(default_factory=datetime.utcnow, description="When action was performed")
    
    changes: List[ChangeRecord] = Field(default_factory=list, description="List of field changes")
    notes: Optional[str] = Field(None, description="Additional notes or reason")
    source: str = Field(default="WEB_UI", description="Source of action: WEB_UI, API, BULK_IMPORT, SYSTEM")


class CrewAuditLogCreate(CrewAuditLogBase):
    """Model for creating audit log"""
    pass


class CrewAuditLogResponse(CrewAuditLogBase):
    """Response model for audit log"""
    id: str = Field(..., description="Log ID")
    created_at: datetime = Field(..., description="When log was created")
    expires_at: datetime = Field(..., description="When log will be auto-deleted (1 year)")

    class Config:
        from_attributes = True


class CrewAuditLogFilter(BaseModel):
    """Filter parameters for querying audit logs"""
    company_id: str = Field(..., description="Company ID (required for multi-tenant)")
    
    # Date range
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    
    # Filters
    action: Optional[str] = Field(None, description="Filter by action type")
    performed_by: Optional[str] = Field(None, description="Filter by username")
    ship_name: Optional[str] = Field(None, description="Filter by ship name")
    entity_id: Optional[str] = Field(None, description="Filter by crew ID")
    search: Optional[str] = Field(None, description="Search crew name")
    
    # Pagination
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Max records to return")
