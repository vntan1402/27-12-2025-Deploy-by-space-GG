"""
Google Drive Helper Functions
"""
import logging
import base64
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def upload_file_to_ship_folder(
    gdrive_config: Dict[str, Any],
    file_content: bytes,
    filename: str,
    ship_name: str,
    category: str
) -> Dict[str, Any]:
    """
    Upload file to existing ship folder structure using Apps Script
    
    Args:
        gdrive_config: Google Drive configuration with script_url and folder_id
        file_content: File content as bytes
        filename: Name of the file
        ship_name: Ship name for folder structure
        category: Category folder (e.g., "Certificates", "Test Reports")
    
    Returns:
        dict: Upload result with success status and file info
    """
    try:
        script_url = gdrive_config.get("web_app_url") or gdrive_config.get("apps_script_url")
        if not script_url:
            raise Exception("Apps Script URL not configured")
        
        parent_folder_id = gdrive_config.get("folder_id")
        if not parent_folder_id:
            raise Exception("Parent folder ID not configured")
        
        # Prepare payload for Apps Script
        payload = {
            "action": "upload_file_with_folder_creation",
            "parent_folder_id": parent_folder_id,
            "ship_name": ship_name,
            "category": category,
            "filename": filename,
            "file_content": base64.b64encode(file_content).decode('utf-8'),
            "content_type": "application/pdf"
        }
        
        logger.info(f"📤 Uploading {filename} to {ship_name}/{category} via Apps Script")
        
        # Call Apps Script
        response = requests.post(script_url, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success"):
            logger.info(f"✅ Uploaded {filename} to {ship_name}/{category}")
            return {
                "success": True,
                "file_id": result.get("file_id"),
                "folder_path": f"{ship_name}/{category}",
                "file_url": result.get("file_url"),
                "file_path": result.get("file_path")
            }
        else:
            error_msg = result.get("message", "Unknown error")
            logger.error(f"❌ Upload failed: {error_msg}")
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        logger.error(f"❌ Error uploading to ship folder: {e}")
        return {"success": False, "error": str(e)}
