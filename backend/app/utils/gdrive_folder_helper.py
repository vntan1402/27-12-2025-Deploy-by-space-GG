"""
Google Drive folder creation helper for ships
"""
import logging
import asyncio
import aiohttp
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def create_google_drive_folder_background(
    ship_dict: dict, 
    current_user,
    mongo_db
):
    """
    Background task to create Google Drive folder structure with timeout
    
    Args:
        ship_dict: Ship data dictionary
        current_user: Current user object
        mongo_db: MongoDB instance
    """
    ship_name = ship_dict.get('name', 'Unknown Ship')
    ship_id = ship_dict.get('id')
    
    try:
        logger.info(f"🚀 Starting background Google Drive folder creation for ship: {ship_name}")
        
        # Set timeout of 180 seconds
        result = await asyncio.wait_for(
            create_google_drive_folder_for_new_ship(ship_dict, current_user, mongo_db),
            timeout=180.0
        )
        
        if result.get("success"):
            logger.info(f"✅ Background Google Drive folder creation completed successfully for ship: {ship_name}")
            
            # Store success status in database for frontend polling
            await mongo_db.update("ships", {"id": ship_id}, {
                "gdrive_folder_status": "completed",
                "gdrive_folder_created_at": datetime.now(timezone.utc).isoformat(),
                "gdrive_folder_error": None
            })
            
        else:
            error_msg = result.get("error", "Unknown error")
            logger.warning(f"❌ Background Google Drive folder creation failed for ship {ship_name}: {error_msg}")
            
            # Store error status in database
            await mongo_db.update("ships", {"id": ship_id}, {
                "gdrive_folder_status": "failed",
                "gdrive_folder_error": error_msg,
                "gdrive_folder_created_at": datetime.now(timezone.utc).isoformat()
            })
            
    except asyncio.TimeoutError:
        timeout_msg = "Google Drive folder creation timed out after 180 seconds"
        logger.error(f"⏰ {timeout_msg} for ship: {ship_name}")
        
        # Store timeout status in database
        await mongo_db.update("ships", {"id": ship_id}, {
            "gdrive_folder_status": "timeout",
            "gdrive_folder_error": timeout_msg,
            "gdrive_folder_created_at": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        error_msg = f"Background Google Drive folder creation failed with exception: {e}"
        logger.error(f"💥 {error_msg} for ship: {ship_name}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Store exception status in database
        await mongo_db.update("ships", {"id": ship_id}, {
            "gdrive_folder_status": "error",
            "gdrive_folder_error": str(e),
            "gdrive_folder_created_at": datetime.now(timezone.utc).isoformat()
        })


async def create_google_drive_folder_for_new_ship(
    ship_dict: dict,
    current_user,
    mongo_db
) -> Dict[str, Any]:
    """
    Create Google Drive folder structure for a newly created ship
    
    Args:
        ship_dict: Ship data dictionary
        current_user: Current user object
        mongo_db: MongoDB instance
        
    Returns:
        Dict with success status and error message if any
    """
    try:
        ship_name = ship_dict.get('name', 'Unknown Ship')
        company_id = ship_dict.get('company')
        
        if not company_id:
            # Try to get from user
            if hasattr(current_user, 'company'):
                company_id = current_user.company
            else:
                logger.warning(f"Could not resolve company ID for ship {ship_name}")
                return {"success": False, "error": "Could not resolve company ID"}
        
        # Get company-specific Google Drive configuration with retry logic
        gdrive_config_doc = None
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries and not gdrive_config_doc:
            if company_id:
                # Try company-specific Google Drive config
                gdrive_config_doc = await mongo_db.find_one(
                    "company_gdrive_config", 
                    {"company_id": company_id}
                )
                logger.info(f"Company Google Drive config lookup attempt {retry_count + 1} for {company_id}: {'Found' if gdrive_config_doc else 'Not found'}")
                
                if not gdrive_config_doc:
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.info(f"Retrying company config lookup in 1 second... (attempt {retry_count + 1}/{max_retries})")
                        await asyncio.sleep(1)
        
        # Company MUST have their own Google Drive configuration
        if not gdrive_config_doc:
            error_msg = "Google Drive is not configured for your company. Please contact administrator to setup Google Drive integration."
            logger.warning(f"No company-specific Google Drive config found for company: {company_id}")
            return {"success": False, "error": error_msg}
        
        # Validate configuration has required fields
        web_app_url = gdrive_config_doc.get("web_app_url") or gdrive_config_doc.get("apps_script_url")
        folder_id = gdrive_config_doc.get("folder_id") or gdrive_config_doc.get("main_folder_id")
        
        if not web_app_url or not folder_id:
            logger.warning(f"Incomplete Google Drive configuration - URL: {bool(web_app_url)}, Folder: {bool(folder_id)}")
            return {"success": False, "error": "Incomplete Google Drive configuration"}
        
        # Create ship folder structure using Apps Script
        logger.info(f"📁 Creating Google Drive folder structure for ship: {ship_name}")
        
        # Get backend API URL for dynamic structure fetching
        import os
        backend_api_url = os.environ.get('BACKEND_API_URL', 'https://test-report-api.preview.emergentagent.com')
        
        payload = {
            "action": "create_complete_ship_structure",
            "parent_folder_id": folder_id,
            "ship_name": ship_name,
            "ship_id": ship_dict.get('id'),
            "company_id": company_id,  # For dynamic structure
            "backend_api_url": backend_api_url  # Apps Script will call this to get categories
        }
        
        logger.info(f"Payload for Apps Script: {payload}")
        
        # Call Apps Script
        async with aiohttp.ClientSession() as session:
            async with session.post(
                web_app_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=150)
            ) as response:
                if response.status != 200:
                    error_msg = f"Apps Script request failed with status {response.status}"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
                
                result = await response.json()
                
                if result.get("success"):
                    logger.info(f"✅ Successfully created folder structure for ship: {ship_name}")
                    logger.info(f"📂 Main folder: {result.get('main_folder_name')}")
                    logger.info(f"📄 Subfolders: {result.get('subfolders_created', 0)}")
                    
                    return {
                        "success": True,
                        "main_folder_id": result.get("main_folder_id"),
                        "main_folder_name": result.get("main_folder_name"),
                        "subfolders_created": result.get("subfolders_created", 0),
                        "folder_url": result.get("folder_url")
                    }
                else:
                    error_msg = result.get("message", "Unknown error from Apps Script")
                    logger.error(f"Apps Script returned error: {error_msg}")
                    return {"success": False, "error": error_msg}
                    
    except aiohttp.ClientError as e:
        error_msg = f"Network error calling Apps Script: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Error creating Google Drive folder: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": error_msg}
