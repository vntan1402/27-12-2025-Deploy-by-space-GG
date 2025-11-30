"""
Crew Certificate Google Drive Service
Handles file uploads to Google Drive for crew certificates
"""
import logging
from typing import Optional, Dict
from fastapi import HTTPException

from app.repositories.crew_repository import CrewRepository

logger = logging.getLogger(__name__)


class CrewCertificateDriveService:
    """Service for managing crew certificate files on Google Drive"""
    
    @staticmethod
    async def upload_certificate_file(
        company_id: str,
        crew_id: str,
        file_content: bytes,
        filename: str,
        mime_type: str
    ) -> Dict[str, str]:
        """
        Upload crew certificate file to Google Drive
        
        Args:
            company_id: Company ID
            crew_id: Crew member ID
            file_content: File content in bytes
            filename: Original filename
            mime_type: MIME type of the file
            
        Returns:
            Dict with file_id and folder_path
        """
        from app.utils.google_drive_helper import GoogleDriveHelper
        
        try:
            # Get crew information to determine folder structure
            crew = await CrewRepository.find_by_id(crew_id)
            
            if not crew:
                raise HTTPException(status_code=404, detail="Crew member not found")
            
            # Determine folder path based on crew's ship_sign_on
            ship_sign_on = crew.get('ship_sign_on', '-')
            
            if ship_sign_on and ship_sign_on != '-':
                # Normal crew with ship assigned
                folder_path = f"{ship_sign_on}/Crew Records/Crew Cert"
                logger.info(f"📤 Uploading crew certificate (Normal): {folder_path}/{filename}")
            else:
                # Standby crew
                folder_path = "COMPANY DOCUMENT/Standby Crew/Crew Cert"
                logger.info(f"📤 Uploading crew certificate (Standby): {folder_path}/{filename}")
            
            # Initialize Google Drive helper
            drive_helper = GoogleDriveHelper(company_id)
            await drive_helper.load_config()
            
            # Upload file to Google Drive
            file_id = await drive_helper.upload_file(
                file_content=file_content,
                filename=filename,
                folder_path=folder_path,
                mime_type=mime_type
            )
            
            if not file_id:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to upload certificate file to Google Drive"
                )
            
            logger.info(f"✅ Certificate file uploaded successfully: {filename}")
            logger.info(f"   🆔 File ID: {file_id}")
            logger.info(f"   📁 Folder: {folder_path}")
            
            return {
                "file_id": file_id,
                "folder_path": folder_path,
                "filename": filename
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading crew certificate file: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload crew certificate: {str(e)}"
            )
    
    @staticmethod
    async def delete_certificate_file(
        company_id: str,
        file_id: str
    ) -> Dict[str, any]:
        """
        Delete crew certificate file from Google Drive
        
        Args:
            company_id: Company ID
            file_id: Google Drive file ID
            
        Returns:
            Dict with success status
        """
        from app.utils.google_drive_helper import GoogleDriveHelper
        
        try:
            if not file_id:
                logger.warning("⚠️ No file_id provided, skipping deletion")
                return {"success": True, "message": "No file to delete"}
            
            # Initialize Google Drive helper
            drive_helper = GoogleDriveHelper(company_id)
            await drive_helper.load_config()
            
            # Delete file from Google Drive
            success = await drive_helper.delete_file(file_id)
            
            if success:
                logger.info(f"✅ Certificate file deleted: {file_id}")
                return {"success": True, "message": "File deleted successfully"}
            else:
                logger.warning(f"⚠️ Failed to delete file: {file_id}")
                return {"success": False, "message": "File deletion failed"}
                
        except Exception as e:
            logger.error(f"❌ Error deleting crew certificate file: {e}")
            return {"success": False, "message": str(e)}
