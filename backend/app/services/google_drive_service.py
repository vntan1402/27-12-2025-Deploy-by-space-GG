"""
Google Drive Service - Handles file operations with Google Drive

This service manages:
- Passport file uploads
- Summary file generation and uploads
- File deletion
- File renaming
- Folder structure management
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class GoogleDriveService:
    """Service for Google Drive file operations"""
    
    def __init__(self):
        """Initialize Google Drive service"""
        logger.info("🔧 Initializing Google Drive Service")
    
    async def upload_passport_files(
        self,
        company_id: str,
        upload_data: Dict
    ) -> Dict:
        """
        Upload passport and summary files to Google Drive
        
        Args:
            company_id: Company UUID
            upload_data: Dictionary containing:
                - file_content: bytes
                - filename: str
                - content_type: str
                - summary_text: str
                - ship_name: str
                - crew_id: str
                - crew_name: str
                - passport_number: str
        
        Returns:
            {
                "success": bool,
                "passport_file_id": str,
                "summary_file_id": str,
                "message": str
            }
        """
        try:
            # Extract data
            file_content = upload_data['file_content']
            filename = upload_data['filename']
            content_type = upload_data['content_type']
            summary_text = upload_data['summary_text']
            ship_name = upload_data['ship_name']
            crew_name = upload_data['crew_name']
            passport_number = upload_data['passport_number']
            
            logger.info(f"📤 Uploading files for: {crew_name} ({passport_number})")
            
            # Initialize Google Drive helper
            from app.utils.google_drive_helper import GoogleDriveHelper
            
            drive_helper = GoogleDriveHelper(company_id)
            await drive_helper.load_config()
            
            # ✅ UNIFIED STRUCTURE: Using "Crew Passport" folder for all passport files
            # Normal crew: {Ship Name}/Crew Records/Crew Passport/
            # Standby crew: COMPANY DOCUMENT/Standby Crew/Crew Passport/
            if ship_name and ship_name != '-':
                # Normal crew with ship
                folder_path = f"{ship_name}/Crew Records/Crew Passport"
                logger.info(f"📤 Uploading passport file (Normal): {folder_path}/{filename}")
            else:
                # Standby crew
                folder_path = "COMPANY DOCUMENT/Standby Crew/Crew Passport"
                logger.info(f"📤 Uploading passport file (Standby): {folder_path}/{filename}")
            
            logger.info(f"📁 Target folder: {folder_path}")
            
            # Upload original passport file
            logger.info(f"📄 Uploading passport file: {filename}")
            passport_file_id = await drive_helper.upload_file(
                file_content=file_content,
                filename=filename,
                folder_path=folder_path,
                mime_type=content_type
            )
            
            if not passport_file_id:
                return {
                    "success": False,
                    "message": "Failed to upload passport file to Google Drive"
                }
            
            # ✅ V1 STRUCTURE: Generate summary filename matching V1
            # Format: {original_filename}_Summary.txt (same folder as passport)
            base_name = filename.rsplit('.', 1)[0]  # Remove extension
            summary_filename = f"{base_name}_Summary.txt"
            
            summary_content = self._generate_summary_content(
                crew_name=crew_name,
                passport_number=passport_number,
                ship_name=ship_name,
                summary_text=summary_text,
                filename=filename
            )
            
            # Upload summary to SAME folder as passport (V1 behavior)
            logger.info(f"📝 Uploading summary file: {folder_path}/{summary_filename}")
            summary_file_id = await drive_helper.upload_file(
                file_content=summary_content.encode('utf-8'),
                filename=summary_filename,
                folder_path=folder_path,  # Same folder as passport
                mime_type='text/plain'
            )
            
            if not summary_file_id:
                logger.warning("⚠️ Summary file upload failed, but passport file uploaded")
            
            logger.info(f"✅ Files uploaded successfully")
            logger.info(f"   📎 Passport ID: {passport_file_id}")
            logger.info(f"   📋 Summary ID: {summary_file_id}")
            
            return {
                "success": True,
                "passport_file_id": passport_file_id,
                "passport_file_name": filename,  # ⭐ NEW: Include filename
                "summary_file_id": summary_file_id,
                "message": "Files uploaded successfully"
            }
            
        except ValueError as e:
            logger.error(f"❌ Configuration error: {e}")
            return {
                "success": False,
                "message": f"Google Drive configuration error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ Upload error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "message": f"Upload failed: {str(e)}"
            }
    
    async def delete_passport_files(
        self,
        company_id: str,
        passport_file_id: Optional[str],
        summary_file_id: Optional[str]
    ) -> Dict:
        """
        Delete passport files from Google Drive
        
        Called when deleting a crew member
        
        Args:
            company_id: Company UUID
            passport_file_id: Google Drive file ID of passport
            summary_file_id: Google Drive file ID of summary
            
        Returns:
            {
                "success": bool,
                "deleted_count": int,
                "failed_count": int,
                "message": str
            }
        """
        try:
            from app.utils.google_drive_helper import GoogleDriveHelper
            
            drive_helper = GoogleDriveHelper(company_id)
            await drive_helper.load_config()
            
            deleted_files = []
            failed_files = []
            
            # Delete passport file
            if passport_file_id:
                logger.info(f"🗑️ Deleting passport file: {passport_file_id}")
                if await drive_helper.delete_file(passport_file_id):
                    deleted_files.append(passport_file_id)
                    logger.info(f"✅ Passport file deleted")
                else:
                    failed_files.append(passport_file_id)
                    logger.error(f"❌ Failed to delete passport file")
            
            # Delete summary file
            if summary_file_id:
                logger.info(f"🗑️ Deleting summary file: {summary_file_id}")
                if await drive_helper.delete_file(summary_file_id):
                    deleted_files.append(summary_file_id)
                    logger.info(f"✅ Summary file deleted")
                else:
                    failed_files.append(summary_file_id)
                    logger.error(f"❌ Failed to delete summary file")
            
            success = len(failed_files) == 0
            message = f"Deleted {len(deleted_files)} files"
            if failed_files:
                message += f", failed to delete {len(failed_files)} files"
            
            return {
                "success": success,
                "deleted_count": len(deleted_files),
                "failed_count": len(failed_files),
                "message": message
            }
            
        except Exception as e:
            logger.error(f"❌ Delete error: {e}")
            return {
                "success": False,
                "deleted_count": 0,
                "failed_count": 0,
                "message": f"Delete failed: {str(e)}"
            }
    
    async def rename_passport_files(
        self,
        passport_file_id: Optional[str],
        summary_file_id: Optional[str],
        new_crew_name: str,
        new_passport_number: str
    ) -> Dict:
        """Rename passport files in Google Drive"""
        # TODO: Implement in Phase 2
        logger.warning("⚠️ rename_passport_files not yet implemented")
        return {"success": True, "message": "Rename not yet implemented (MOCK)"}
    
    def _generate_summary_content(
        self,
        crew_name: str,
        passport_number: str,
        ship_name: str,
        summary_text: str,
        filename: str
    ) -> str:
        """Generate summary file content"""
        return f"""PASSPORT ANALYSIS SUMMARY
Generated: {datetime.now(timezone.utc).isoformat()}
Ship: {ship_name}
Original File: {filename}

CREW INFORMATION:
- Name: {crew_name}
- Passport Number: {passport_number}

OCR EXTRACTED TEXT:
{summary_text}

---
This summary was generated automatically using AI OCR for crew management.
"""
