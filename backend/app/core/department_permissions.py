"""
Department-based permission utilities
"""
from typing import List, Dict
from app.models.user import UserRole, Department

# Category to Department mapping
CATEGORY_DEPARTMENT_MAPPING: Dict[str, List[str]] = {
    "Class & Flag Cert": ["technical", "supply"],
    "Crew Records": ["crewing"],
    "ISM - ISPS - MLC": ["safety", "dpa", "cso"],
    "Safety Management System": ["dpa"],
    "Technical Infor": ["technical"],
    "Supplies": ["supply"]
}

# Document type to Category mapping
DOCUMENT_TYPE_CATEGORY_MAPPING: Dict[str, str] = {
    "ship_cert": "Class & Flag Cert",
    "survey_report": "Class & Flag Cert",
    "test_report": "Class & Flag Cert",
    "drawing_manual": "Class & Flag Cert",
    "other_document": "Class & Flag Cert",
    "crew_cert": "Crew Records",
    "crew_passport": "Crew Records",
    "crew_management": "Crew Records",  # ⭐ NEW: For crew creation/management
    "audit_cert": "ISM - ISPS - MLC",
    "audit_report": "ISM - ISPS - MLC",
    "approval_doc": "ISM - ISPS - MLC",
    "other_audit_doc": "ISM - ISPS - MLC",
    "company_cert": "Safety Management System"
}

def get_managed_categories(departments: List[str]) -> List[str]:
    """
    Get categories that user's departments can manage
    
    Args:
        departments: List of user's departments (lowercase)
    
    Returns:
        List of category names user can manage
    """
    if not departments:
        return []
    
    # Normalize to lowercase
    normalized_depts = [dept.lower() if dept else "" for dept in departments]
    
    managed_categories = []
    for category, allowed_depts in CATEGORY_DEPARTMENT_MAPPING.items():
        if any(dept in allowed_depts for dept in normalized_depts):
            managed_categories.append(category)
    
    return managed_categories

def can_manage_category(user_departments: List[str], category: str) -> bool:
    """
    Check if user's departments can manage this category
    
    Args:
        user_departments: List of user's departments
        category: Category name to check
    
    Returns:
        True if user can manage this category
    """
    if not user_departments or not category:
        return False
    
    # Normalize to lowercase
    normalized_depts = [dept.lower() if dept else "" for dept in user_departments]
    
    # Get allowed departments for this category
    allowed_depts = CATEGORY_DEPARTMENT_MAPPING.get(category, [])
    
    # Check if any user department matches
    return any(dept in allowed_depts for dept in normalized_depts)

def can_manage_document_type(user_departments: List[str], document_type: str) -> bool:
    """
    Check if user's departments can manage this document type
    
    Args:
        user_departments: List of user's departments
        document_type: Document type (e.g., 'ship_cert', 'crew_cert')
    
    Returns:
        True if user can manage this document type
    """
    if not user_departments or not document_type:
        return False
    
    # Get category for this document type
    category = DOCUMENT_TYPE_CATEGORY_MAPPING.get(document_type)
    
    if not category:
        # Unknown document type - deny by default
        return False
    
    # Check if user can manage this category
    return can_manage_category(user_departments, category)

def get_category_for_document_type(document_type: str) -> str:
    """
    Get category name for a document type
    
    Args:
        document_type: Document type (e.g., 'ship_cert', 'crew_cert')
    
    Returns:
        Category name or 'Unknown'
    """
    return DOCUMENT_TYPE_CATEGORY_MAPPING.get(document_type, "Unknown")
