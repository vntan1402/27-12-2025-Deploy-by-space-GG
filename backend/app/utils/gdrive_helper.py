"""
Google Drive Helper Functions
"""
import logging
import base64
import requests
import aiohttp
import asyncio
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

async def upload_file_to_ship_folder(
    gdrive_config: Dict[str, Any],
    file_content: bytes,
    filename: str,
    ship_name: str,
    category: str,
    content_type: str = None  # ⭐ NEW: Allow custom content_type
) -> Dict[str, Any]:
    """
    Upload file to existing ship folder structure using Apps Script
    
    Args:
        gdrive_config: Google Drive configuration with script_url and folder_id
        file_content: File content as bytes
        filename: Name of the file
        ship_name: Ship name for folder structure
        category: Category folder (e.g., "Certificates", "Test Reports")
        content_type: MIME type (optional, auto-detected from filename)
    
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
        
        # ⭐ NEW: Detect MIME type from filename if not provided
        if not content_type:
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            mime_type_map = {
                'pdf': 'application/pdf',
                'txt': 'text/plain',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'doc': 'application/msword',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'xls': 'application/vnd.ms-excel',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            content_type = mime_type_map.get(file_ext, 'application/octet-stream')
            logger.info(f"🔍 Auto-detected MIME type for {filename}: {content_type}")
        
        # Prepare payload for Apps Script
        payload = {
            "action": "upload_file_with_folder_creation",
            "parent_folder_id": parent_folder_id,
            "ship_name": ship_name,
            "category": category,
            "filename": filename,
            "file_content": base64.b64encode(file_content).decode('utf-8'),
            "content_type": content_type  # ⭐ Use detected/provided MIME type
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


async def upload_file_with_parent_category(
    gdrive_config: Dict[str, Any],
    file_content: bytes,
    filename: str,
    ship_name: str,
    parent_category: str,  # e.g., "Class & Flag Cert"
    category: str  # e.g., "Other Documents"
) -> Dict[str, Any]:
    """
    Upload file to ship folder with parent_category and category
    Path: ShipName > parent_category > category > file
    Example: BROTHER 36 > Class & Flag Cert > Other Documents > file.pdf
    
    Args:
        gdrive_config: Google Drive configuration with script_url and folder_id
        file_content: File content as bytes
        filename: Name of the file
        ship_name: Ship name for folder structure
        parent_category: Parent category (e.g., "Class & Flag Cert")
        category: Category (e.g., "Other Documents")
    
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
        
        # Determine content type
        if filename.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            content_type = 'image/jpeg'
        else:
            content_type = 'application/octet-stream'
        
        # Prepare payload for Apps Script - MATCHING backend-v1 structure
        payload = {
            "action": "upload_file_with_folder_creation",
            "parent_folder_id": parent_folder_id,
            "ship_name": ship_name,
            "parent_category": parent_category,  # e.g., "Class & Flag Cert"
            "category": category,  # e.g., "Other Documents"
            "filename": filename,
            "file_content": base64.b64encode(file_content).decode('utf-8'),
            "content_type": content_type
        }
        
        logger.info(f"📤 Uploading {filename} to {ship_name}/{parent_category}/{category} via Apps Script")
        
        # Call Apps Script asynchronously
        async with aiohttp.ClientSession() as session:
            async with session.post(
                script_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                result = await response.json()
        
        if result.get("success"):
            logger.info(f"✅ Uploaded {filename} to {ship_name}/{parent_category}/{category}")
            return {
                "success": True,
                "file_id": result.get("file_id"),
                "folder_path": f"{ship_name}/{parent_category}/{category}",
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


async def upload_files_to_folder(
    gdrive_config: Dict[str, Any],
    files: List[Tuple[bytes, str]],  # List of (file_content, filename) tuples
    folder_name: str,
    ship_name: str,
    parent_category: str  # e.g., "Class & Flag Cert/Other Documents"
) -> Dict[str, Any]:
    """
    Upload multiple files to a subfolder on Google Drive
    Path: ShipName > parent_category > folder_name > files
    Example: BROTHER 36 > Class & Flag Cert/Other Documents > Radio Report > file.pdf
    
    Args:
        gdrive_config: Google Drive configuration with script_url and folder_id
        files: List of (file_content, filename) tuples
        folder_name: Name of the subfolder to create (e.g., "Radio Report")
        ship_name: Ship name for folder structure
        parent_category: Parent category path (e.g., "Class & Flag Cert/Other Documents")
    
    Returns:
        dict: Upload results with folder_id, folder_link, and file_ids
    """
    try:
        script_url = gdrive_config.get("web_app_url") or gdrive_config.get("apps_script_url")
        if not script_url:
            raise Exception("Apps Script URL not configured")
        
        parent_folder_id = gdrive_config.get("folder_id")
        if not parent_folder_id:
            raise Exception("Parent folder ID not configured")
        
        logger.info(f"📁 Uploading folder to Google Drive")
        logger.info(f"   Folder: {folder_name}")
        logger.info(f"   Files: {len(files)}")
        logger.info(f"   Parent category: {parent_category}")
        
        file_ids = []
        failed_files = []
        folder_id = None
        
        # Upload all files using the same nested category path
        for file_content, filename in files:
            try:
                # Determine content type
                if filename.lower().endswith('.pdf'):
                    content_type = 'application/pdf'
                elif filename.lower().endswith(('.jpg', '.jpeg')):
                    content_type = 'image/jpeg'
                else:
                    content_type = 'application/octet-stream'
                
                # Prepare payload for Apps Script
                payload = {
                    "action": "upload_file_with_folder_creation",
                    "parent_folder_id": parent_folder_id,
                    "ship_name": ship_name,
                    "parent_category": parent_category,  # e.g., "Class & Flag Cert/Other Documents"
                    "category": folder_name,  # e.g., "Radio Report"
                    "filename": filename,
                    "file_content": base64.b64encode(file_content).decode('utf-8'),
                    "content_type": content_type
                }
                
                logger.info(f"   📤 Uploading: {filename}")
                
                # Call Apps Script asynchronously
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        script_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=300)
                    ) as response:
                        result = await response.json()
                
                if result.get('success'):
                    file_ids.append(result.get('file_id'))
                    
                    # Extract folder_id from first successful upload
                    if not folder_id and result.get('folder_id'):
                        folder_id = result.get('folder_id')
                    
                    logger.info(f"   ✅ Uploaded: {filename}")
                else:
                    failed_files.append(filename)
                    logger.warning(f"   ⚠️ Failed to upload: {filename}")
                    
            except Exception as e:
                failed_files.append(filename)
                logger.error(f"   ❌ Error uploading {filename}: {e}")
        
        # Generate folder link from folder_id
        folder_link = f"https://drive.google.com/drive/folders/{folder_id}" if folder_id else None
        
        logger.info(f"✅ Folder upload completed: {len(file_ids)}/{len(files)} files successful")
        
        # Return results
        return {
            'success': True,
            'message': f'Folder uploaded successfully: {len(file_ids)}/{len(files)} files',
            'folder_id': folder_id,
            'folder_link': folder_link,
            'file_ids': file_ids,
            'failed_files': failed_files,
            'total_files': len(files),
            'successful_files': len(file_ids)
        }
        
    except Exception as e:
        logger.error(f"❌ Error uploading folder: {e}")
        return {
            'success': False,
            'message': f'Folder upload failed: {str(e)}',
            'error': str(e)
        }


async def upload_file_to_folder_streaming(
    gdrive_config: Dict[str, Any],
    files: List,  # List[UploadFile]
    folder_name: str,
    ship_name: str,
    parent_category: str
) -> Dict[str, Any]:
    """
    Upload multiple files to folder using PARALLEL approach with streaming.
    
    Optimization:
    - Upload files in PARALLEL (not sequential)
    - Staggered start: 1 second delay between each file start
    - Memory efficient: Read file content only when needed (not all at once)
    - Much faster than sequential upload
    
    Args:
        gdrive_config: Google Drive configuration
        files: List of UploadFile objects
        folder_name: Subfolder name to create
        ship_name: Ship name
        parent_category: Parent category path
    
    Returns:
        dict: Upload results with folder_id, folder_link, file_ids
    """
    try:
        import asyncio
        from fastapi import UploadFile
        
        script_url = gdrive_config.get("web_app_url") or gdrive_config.get("apps_script_url")
        if not script_url:
            raise Exception("Apps Script URL not configured")
        
        parent_folder_id = gdrive_config.get("folder_id")
        if not parent_folder_id:
            raise Exception("Parent folder ID not configured")
        
        logger.info(f"📁 Starting PARALLEL upload with streaming")
        logger.info(f"   Folder: {folder_name}")
        logger.info(f"   Files: {len(files)}")
        logger.info(f"   Strategy: Staggered parallel (1s delay between starts)")
        
        # Async function to upload a single file with delay
        async def upload_single_file(file_obj: UploadFile, index: int):
            """Upload single file with staggered delay"""
            try:
                # Staggered delay: File 0 starts immediately, File 1 after 1s, File 2 after 2s, etc.
                delay = index * 1.0  # 1 second per file
                if delay > 0:
                    logger.info(f"   ⏰ File {index+1}/{len(files)} ({file_obj.filename}): Waiting {delay}s before upload...")
                    await asyncio.sleep(delay)
                
                # Read file content NOW (when needed, not all at once)
                logger.info(f"   📖 File {index+1}/{len(files)} ({file_obj.filename}): Reading file...")
                file_content = await file_obj.read()
                filename = file_obj.filename.split('/')[-1]  # Extract filename from path
                
                logger.info(f"   📤 File {index+1}/{len(files)} ({filename}): Uploading ({len(file_content)} bytes)...")
                
                # Determine content type
                if filename.lower().endswith('.pdf'):
                    content_type = 'application/pdf'
                elif filename.lower().endswith(('.jpg', '.jpeg')):
                    content_type = 'image/jpeg'
                else:
                    content_type = 'application/octet-stream'
                
                # Prepare payload
                payload = {
                    "action": "upload_file_with_folder_creation",
                    "parent_folder_id": parent_folder_id,
                    "ship_name": ship_name,
                    "parent_category": parent_category,
                    "category": folder_name,
                    "filename": filename,
                    "file_content": base64.b64encode(file_content).decode('utf-8'),
                    "content_type": content_type
                }
                
                # Upload to Apps Script
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        script_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=300)
                    ) as response:
                        result = await response.json()
                
                # Clear file content from memory
                del file_content
                
                if result.get('success'):
                    logger.info(f"   ✅ File {index+1}/{len(files)} ({filename}): Upload successful!")
                    return {
                        'success': True,
                        'filename': filename,
                        'file_id': result.get('file_id'),
                        'folder_id': result.get('folder_id')
                    }
                else:
                    logger.warning(f"   ⚠️ File {index+1}/{len(files)} ({filename}): Upload failed - {result.get('message')}")
                    return {
                        'success': False,
                        'filename': filename,
                        'error': result.get('message', 'Unknown error')
                    }
                    
            except Exception as e:
                logger.error(f"   ❌ File {index+1}/{len(files)} ({file_obj.filename}): Error - {e}")
                return {
                    'success': False,
                    'filename': file_obj.filename,
                    'error': str(e)
                }
        
        # Create tasks for all files
        logger.info(f"🚀 Creating {len(files)} parallel upload tasks...")
        tasks = [upload_single_file(file_obj, idx) for idx, file_obj in enumerate(files)]
        
        # Execute all tasks in parallel
        logger.info(f"⚡ Executing parallel uploads (staggered start: 1s delay)...")
        results = await asyncio.gather(*tasks)
        
        # Process results
        file_ids = []
        failed_files = []
        folder_id = None
        
        for result in results:
            if result['success']:
                file_ids.append(result['file_id'])
                # Get folder_id from first successful upload
                if not folder_id and result.get('folder_id'):
                    folder_id = result['folder_id']
            else:
                failed_files.append(result['filename'])
        
        # Generate folder link
        folder_link = f"https://drive.google.com/drive/folders/{folder_id}" if folder_id else None
        
        logger.info(f"✅ Parallel upload completed: {len(file_ids)}/{len(files)} files successful")
        if failed_files:
            logger.warning(f"⚠️ Failed files: {', '.join(failed_files)}")
        
        return {
            'success': True,
            'message': f'Folder uploaded: {len(file_ids)}/{len(files)} files',
            'folder_id': folder_id,
            'folder_link': folder_link,
            'file_ids': file_ids,
            'failed_files': failed_files,
            'total_files': len(files),
            'successful_files': len(file_ids)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in parallel folder upload: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'message': f'Parallel upload failed: {str(e)}',
            'error': str(e)
        }
