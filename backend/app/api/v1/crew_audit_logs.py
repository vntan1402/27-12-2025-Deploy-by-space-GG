"""
Crew Audit Logs API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from app.models.crew_audit_log import (
    CrewAuditLogResponse,
    CrewAuditLogFilter
)
from app.repositories.crew_audit_log_repository import CrewAuditLogRepository
from app.core.security import get_current_user
from app.db.mongodb import mongo_db

router = APIRouter()


def get_audit_log_repository() -> CrewAuditLogRepository:
    """Dependency to get audit log repository"""
    return CrewAuditLogRepository(mongo_db.database)


@router.get("/crew-audit-logs", response_model=dict)
async def get_crew_audit_logs(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    performed_by: Optional[str] = Query(None, description="Filter by username"),
    ship_name: Optional[str] = Query(None, description="Filter by ship name"),
    entity_id: Optional[str] = Query(None, description="Filter by crew ID"),
    search: Optional[str] = Query(None, description="Search crew name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    current_user: dict = Depends(get_current_user),
    repository: CrewAuditLogRepository = Depends(get_audit_log_repository)
):
    """
    Get filtered crew audit logs with pagination
    
    Only admin, super_admin, and system_admin can access
    """
    # Check permissions
    if current_user.role not in ['admin', 'super_admin', 'system_admin']:
        raise HTTPException(status_code=403, detail="Not authorized to view audit logs")
    
    company_id = current_user.company_id
    
    # Parse dates if provided
    start_date_parsed = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_date_parsed = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    # Get logs
    logs, total = await repository.get_logs(
        company_id=company_id,
        start_date=start_date_parsed,
        end_date=end_date_parsed,
        action=action,
        performed_by=performed_by,
        ship_name=ship_name,
        entity_id=entity_id,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return {
        'logs': logs,
        'total': total,
        'skip': skip,
        'limit': limit,
        'has_more': (skip + len(logs)) < total
    }


@router.get("/crew-audit-logs/{log_id}", response_model=CrewAuditLogResponse)
async def get_crew_audit_log_by_id(
    log_id: str,
    current_user: dict = Depends(get_current_user),
    repository: CrewAuditLogRepository = Depends(get_audit_log_repository)
):
    """
    Get single audit log by ID
    """
    # Check permissions
    if current_user.role not in ['admin', 'super_admin', 'system_admin']:
        raise HTTPException(status_code=403, detail="Not authorized to view audit logs")
    
    company_id = current_user.company_id
    
    log = await repository.get_log_by_id(log_id, company_id)
    
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    return log


@router.get("/crew-audit-logs/crew/{crew_id}", response_model=List[CrewAuditLogResponse])
async def get_crew_audit_logs_by_crew(
    crew_id: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    repository: CrewAuditLogRepository = Depends(get_audit_log_repository)
):
    """
    Get all audit logs for a specific crew member
    """
    # Check permissions
    if current_user.role not in ['admin', 'super_admin', 'system_admin']:
        raise HTTPException(status_code=403, detail="Not authorized to view audit logs")
    
    company_id = current_user.company_id
    
    logs = await repository.get_logs_by_crew(crew_id, company_id, limit)
    
    return logs


@router.get("/crew-audit-logs/filters/users", response_model=List[dict])
async def get_unique_users_for_filter(
    current_user: dict = Depends(get_current_user),
    repository: CrewAuditLogRepository = Depends(get_audit_log_repository)
):
    """
    Get unique users for filter dropdown
    """
    # Check permissions
    if current_user.role not in ['admin', 'super_admin', 'system_admin']:
        raise HTTPException(status_code=403, detail="Not authorized to view audit logs")
    
    company_id = current_user.company_id
    
    users = await repository.get_unique_users(company_id)
    
    return users


@router.get("/crew-audit-logs/filters/ships", response_model=List[str])
async def get_unique_ships_for_filter(
    current_user: dict = Depends(get_current_user),
    repository: CrewAuditLogRepository = Depends(get_audit_log_repository)
):
    """
    Get unique ship names for filter dropdown
    """
    # Check permissions
    if current_user.role not in ['admin', 'super_admin', 'system_admin']:
        raise HTTPException(status_code=403, detail="Not authorized to view audit logs")
    
    company_id = current_user.company_id
    
    ships = await repository.get_unique_ships(company_id)
    
    return ships


@router.delete("/crew-audit-logs/cleanup", response_model=dict)
async def cleanup_expired_logs(
    current_user: dict = Depends(get_current_user),
    repository: CrewAuditLogRepository = Depends(get_audit_log_repository)
):
    """
    Manual cleanup of expired logs (older than 1 year)
    Only system_admin can trigger this
    """
    # Check permissions
    if current_user.role != 'system_admin':
        raise HTTPException(status_code=403, detail="Only system admin can trigger cleanup")
    
    deleted_count = await repository.delete_expired_logs()
    
    return {
        'success': True,
        'deleted_count': deleted_count,
        'message': f'Deleted {deleted_count} expired log(s)'
    }
