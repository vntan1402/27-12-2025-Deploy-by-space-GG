import logging
from fastapi import APIRouter
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/sidebar-structure")
async def get_sidebar_structure():
    """
    Get current homepage sidebar structure for Google Apps Script - Main Categories Only
    
    Returns main categories that Apps Script will use to create folder structure
    """
    try:
        # Define the main sidebar categories that match the frontend
        # Returns dictionary with empty arrays - Apps Script will create only main category folders
        # Structure: {Ship Name}/{Category}/ (no subcategories)
        sidebar_structure = {
            "Class & Flag Cert": [],
            "Crew Records": [],
            "ISM - ISPS - MLC": [],
            "Safety Management System": [],
            "Technical Infor": [],
            "Supplies": []
        }
        
        # Calculate statistics
        total_categories = len(sidebar_structure)
        total_subcategories = sum(len(subcats) for subcats in sidebar_structure.values())
        
        return {
            "success": True,
            "message": "Sidebar structure retrieved successfully",
            "structure": sidebar_structure,
            "metadata": {
                "total_categories": total_categories,
                "total_subcategories": total_subcategories,
                "structure_version": "v4.0",
                "structure_type": "main_categories_only",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "source": "homepage_sidebar_main_categories"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting sidebar structure: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
