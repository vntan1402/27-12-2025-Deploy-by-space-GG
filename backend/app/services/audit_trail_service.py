"""
Audit Trail Service - Track all important actions for compliance and debugging
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class AuditTrailService:
    """Service for logging audit trails"""
    
    @staticmethod
    async def log_action(
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Dict,
        company_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log an audit trail entry
        
        Args:
            user_id: User who performed the action
            action: Action type (CREATE_CREW, UPDATE_CREW, DELETE_CREW, etc.)
            resource_type: Type of resource (crew_member, certificate, etc.)
            resource_id: ID of the resource
            details: Additional details about the action
            company_id: Company UUID
            ip_address: IP address of the request (optional)
            user_agent: User agent string (optional)
        """
        try:
            audit_entry = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details,
                "company_id": company_id,
                "timestamp": datetime.now(timezone.utc),
                "ip_address": ip_address,
                "user_agent": user_agent
            }
            
            await mongo_db.create("audit_trail", audit_entry)
            
            logger.info(f"📝 Audit: {action} on {resource_type}/{resource_id} by user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to log audit trail: {e}")
            # Don't fail the main operation if audit logging fails
    
    @staticmethod
    async def get_audit_trail(
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Retrieve audit trail entries with filters
        
        Args:
            resource_type: Filter by resource type
            resource_id: Filter by specific resource ID
            user_id: Filter by user
            company_id: Filter by company
            limit: Maximum number of entries to return
            
        Returns:
            List of audit trail entries
        """
        try:
            query = {}
            
            if resource_type:
                query["resource_type"] = resource_type
            if resource_id:
                query["resource_id"] = resource_id
            if user_id:
                query["user_id"] = user_id
            if company_id:
                query["company_id"] = company_id
            
            # Sort by timestamp descending (newest first)
            entries = await mongo_db.find_all("audit_trail", query)
            
            # Sort in Python
            entries.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
            
            # Limit results
            return entries[:limit]
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve audit trail: {e}")
            return []
