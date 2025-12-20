"""
Centralized permission checking utilities

This module provides reusable permission check functions that can be used
across all services to enforce consistent access control.
"""
import logging
from typing import Optional, List
from fastapi import HTTPException
from app.models.user import UserResponse, UserRole
from app.core import messages
from app.core.department_permissions import can_manage_document_type, get_category_for_document_type

logger = logging.getLogger(__name__)


def check_company_access(current_user: UserResponse, target_company_id: str, action: str = "access") -> None:
    """
    Check if user has access to a specific company's data
    
    Rule: Admin can only access their own company
          System Admin / Super Admin can access all
    
    Args:
        current_user: Current user making the request
        target_company_id: Company ID to check access for
        action: Action being performed (for error message)
    
    Raises:
        HTTPException(403): If user doesn't have access
    """
    logger.info(f"🔍 CHECK_COMPANY_ACCESS: user={current_user.username}, role={current_user.role}, user_company={current_user.company}, target_company={target_company_id}, action={action}")
    
    # System Admin and Super Admin have access to everything
    if current_user.role in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
        logger.info(f"✅ PASS: System/Super Admin has full access")
        return
    
    # All other users (including Admin) can only access their own company
    if current_user.company != target_company_id:
        logger.warning(f"❌ BLOCK: Company mismatch - user_company={current_user.company} != target={target_company_id}")
        raise HTTPException(status_code=403, detail=messages.ACCESS_DENIED_COMPANY)
    
    logger.info(f"✅ PASS: Company access granted")


def check_ship_access(current_user: UserResponse, ship_company_id: str) -> None:
    """
    Check if user has access to a specific ship
    
    Rule: Users can only access ships within their company
          Editor/Viewer can only access ships they are assigned to (checked separately)
    
    Args:
        current_user: Current user making the request
        ship_company_id: Company ID of the ship
    
    Raises:
        HTTPException(403): If user doesn't have access
    """
    check_company_access(current_user, ship_company_id, "ship")


def check_editor_viewer_ship_scope(
    current_user: UserResponse,
    target_ship_id: str,
    action: str = "access"
) -> None:
    """
    Check if Editor/Viewer has access to specific ship
    
    Rule: Editor and Viewer can only access documents for their assigned ship
    
    Args:
        current_user: Current user making the request
        target_ship_id: Ship ID to check access for
        action: Action being performed
    
    Raises:
        HTTPException(403): If Editor/Viewer doesn't have access to this ship
    """
    from app.db.mongodb import mongo_db
    import asyncio
    
    # Only apply to Editor and Viewer roles
    if current_user.role not in [UserRole.EDITOR, UserRole.VIEWER]:
        return  # Higher roles have broader access
    
    # Get user's assigned ship NAME (not ID)
    user_assigned_ship_name = getattr(current_user, 'ship', None)
    
    if not user_assigned_ship_name or not user_assigned_ship_name.strip():
        # Editor/Viewer without assigned ship cannot access anything
        raise HTTPException(status_code=403, detail=messages.SHIP_ACCESS_DENIED)
    
    # Get target ship to compare by name
    async def get_ship_name():
        ship = await mongo_db.find_one("ships", {"id": target_ship_id})
        return ship.get('name', '') if ship else ''
    
    # Run async function
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're already in an async context, create a new task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, get_ship_name())
                target_ship_name = future.result()
        else:
            target_ship_name = loop.run_until_complete(get_ship_name())
    except RuntimeError:
        target_ship_name = asyncio.run(get_ship_name())
    
    # Check if target ship matches assigned ship (case-insensitive)
    if user_assigned_ship_name.lower() != target_ship_name.lower():
        raise HTTPException(status_code=403, detail=messages.SHIP_ACCESS_DENIED)


def check_manager_department_permission(
    current_user: UserResponse,
    document_type: str,
    action: str = "create"
) -> None:
    """
    Check if Manager has department permission for this document type
    
    Rule: Manager can only create/edit/delete documents within their department's scope
    
    Args:
        current_user: Current user making the request
        document_type: Type of document (e.g., 'ship_cert', 'crew_cert')
        action: Action being performed (for error message)
    
    Raises:
        HTTPException(403): If Manager's department doesn't have permission
    """
    logger.info(f"🔍 CHECK_MANAGER_DEPT: user={current_user.username}, role={current_user.role}, document_type={document_type}, action={action}")
    
    # Only apply to Manager role
    if current_user.role != UserRole.MANAGER:
        logger.info(f"✅ SKIP: Role {current_user.role} not subject to department restrictions")
        return  # Admin and System Admin have full access
    
    # Get user's departments
    user_departments = []
    if hasattr(current_user, 'department') and current_user.department:
        # department can be a string or list
        if isinstance(current_user.department, list):
            user_departments = current_user.department
        else:
            user_departments = [current_user.department]
    
    logger.info(f"   User departments: {user_departments}")
    
    if not user_departments:
        # Manager without department cannot manage anything
        logger.warning(f"❌ BLOCK: Manager has no departments assigned")
        raise HTTPException(status_code=403, detail=messages.DEPARTMENT_PERMISSION_DENIED)
    
    # Check if user's departments can manage this document type
    can_manage = can_manage_document_type(user_departments, document_type)
    category = get_category_for_document_type(document_type)
    
    logger.info(f"   Document category: {category}")
    logger.info(f"   Can manage: {can_manage}")
    
    if not can_manage:
        logger.warning(f"❌ BLOCK: Departments {user_departments} cannot manage {document_type} (category: {category})")
        error_msg = f"Department của bạn không có quyền quản lý loại tài liệu này (Category: {category}). Hãy liên hệ Manager của department tương ứng."
        raise HTTPException(status_code=403, detail=error_msg)
    
    logger.info(f"✅ PASS: Department permission granted")


def check_minimum_role(current_user: UserResponse, minimum_role: UserRole, action: str = "perform this action") -> None:
    """
    Check if user has at least the minimum required role
    
    Args:
        current_user: Current user making the request
        minimum_role: Minimum role required
        action: Action being performed (for error message)
    
    Raises:
        HTTPException(403): If user doesn't have minimum role
    """
    role_hierarchy = {
        UserRole.VIEWER: 0,
        UserRole.EDITOR: 1,
        UserRole.MANAGER: 2,
        UserRole.ADMIN: 3,
        UserRole.SUPER_ADMIN: 4,
        UserRole.SYSTEM_ADMIN: 5
    }
    
    user_level = role_hierarchy.get(current_user.role, -1)
    required_level = role_hierarchy.get(minimum_role, 999)
    
    if user_level < required_level:
        # Generate appropriate error message based on minimum role
        if minimum_role == UserRole.ADMIN:
            raise HTTPException(status_code=403, detail=messages.ADMIN_ONLY)
        elif minimum_role == UserRole.MANAGER:
            raise HTTPException(status_code=403, detail=messages.MANAGER_ONLY)
        elif minimum_role == UserRole.EDITOR:
            raise HTTPException(status_code=403, detail=messages.EDITOR_ONLY)
        elif minimum_role == UserRole.SYSTEM_ADMIN:
            raise HTTPException(status_code=403, detail=messages.SYSTEM_ADMIN_ONLY)
        else:
            raise HTTPException(status_code=403, detail=messages.PERMISSION_DENIED)


def check_create_permission(current_user: UserResponse, document_type: str, target_company_id: str) -> None:
    """
    Comprehensive check for create permission
    
    Combines:
    1. Company access check
    2. Role-based permission (Manager+ can create)
    3. Department-based permission (for Manager role)
    
    Args:
        current_user: Current user making the request
        document_type: Type of document being created
        target_company_id: Company ID for the document
    
    Raises:
        HTTPException(403): If user doesn't have permission
    """
    logger.info(f"🔐 CHECK_CREATE_PERMISSION: user={current_user.username}, doc_type={document_type}, target_company={target_company_id}")
    
    # Step 1: Check company access
    check_company_access(current_user, target_company_id, "create")
    
    # Step 2: Check minimum role (Manager+ can create)
    check_minimum_role(current_user, UserRole.MANAGER, "create documents")
    
    # Step 3: For Manager role, check department permission
    check_manager_department_permission(current_user, document_type, "create")
    
    logger.info(f"✅ CREATE PERMISSION GRANTED for {current_user.username}")


def check_edit_permission(current_user: UserResponse, document_type: str, target_company_id: str) -> None:
    """
    Comprehensive check for edit permission
    
    Same rules as create permission
    
    Args:
        current_user: Current user making the request
        document_type: Type of document being edited
        target_company_id: Company ID for the document
    
    Raises:
        HTTPException(403): If user doesn't have permission
    """
    # Step 1: Check company access
    check_company_access(current_user, target_company_id, "edit")
    
    # Step 2: Check minimum role (Manager+ can edit)
    check_minimum_role(current_user, UserRole.MANAGER, "edit documents")
    
    # Step 3: For Manager role, check department permission
    check_manager_department_permission(current_user, document_type, "edit")


def check_delete_permission(current_user: UserResponse, document_type: str, target_company_id: str) -> None:
    """
    Comprehensive check for delete permission
    
    Same rules as create/edit permission
    
    Args:
        current_user: Current user making the request
        document_type: Type of document being deleted
        target_company_id: Company ID for the document
    
    Raises:
        HTTPException(403): If user doesn't have permission
    """
    # Step 1: Check company access
    check_company_access(current_user, target_company_id, "delete")
    
    # Step 2: Check minimum role (Manager+ can delete)
    check_minimum_role(current_user, UserRole.MANAGER, "delete documents")
    
    # Step 3: For Manager role, check department permission
    check_manager_department_permission(current_user, document_type, "delete")


def filter_documents_by_ship_scope(
    documents: List[dict],
    current_user: UserResponse
) -> List[dict]:
    """
    Filter documents for Editor/Viewer based on their assigned ship
    
    Rule: Editor and Viewer can only see documents for their assigned ship
          Higher roles see all documents (company-filtered upstream)
    
    Args:
        documents: List of document dictionaries
        current_user: Current user making the request
    
    Returns:
        Filtered list of documents
    """
    # Only apply to Editor and Viewer roles
    if current_user.role not in [UserRole.EDITOR, UserRole.VIEWER]:
        return documents  # Higher roles see all
    
    # Get user's assigned ship
    user_assigned_ship = getattr(current_user, 'assigned_ship_id', None)
    
    if not user_assigned_ship:
        # Editor/Viewer without assigned ship sees nothing
        return []
    
    # Filter documents by ship_id
    filtered = [
        doc for doc in documents
        if doc.get('ship_id') == user_assigned_ship
    ]
    
    return filtered


def can_view_company_certificates(current_user: UserResponse) -> bool:
    """
    Check if user can view Company Certificates
    
    Rule: All roles except Viewer can view Company Certificates
          Viewer role cannot access Company Certificates
    
    Args:
        current_user: Current user making the request
    
    Returns:
        True if user can view Company Certificates
    """
    # Viewer role cannot view Company Certificates
    if current_user.role == UserRole.VIEWER:
        return False
    
    # All other roles (Editor, Manager, Admin, System Admin) can view
    return True
