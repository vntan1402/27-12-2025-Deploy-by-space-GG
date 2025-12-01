import logging
import aiohttp
from typing import Dict, List
from fastapi import HTTPException
from datetime import datetime, timezone

from app.repositories.crew_repository import CrewRepository
from app.repositories.company_gdrive_config_repository import CompanyGDriveConfigRepository
from app.models.user import UserResponse

logger = logging.getLogger(__name__)


class CrewPassportRenameService:
    """Service for auto-renaming crew passport files on Google Drive"""
    
    @staticmethod
    async def auto_rename_passport_files(
        crew_id: str,
        current_user: UserResponse
    ) -> Dict:
        """
        Auto rename crew passport and summary files using naming convention:
        {Rank}_{Full Name (Eng)}_Passport.pdf
        
        Example: Master_NGUYEN VAN A_Passport.pdf
        
        Args:
            crew_id: Crew member ID
            current_user: Current user making the request
            
        Returns:
            Dict with rename result
        """
        try:
            # Get crew member
            crew_repo = CrewRepository()
            crew = await crew_repo.find_one({
                "id": crew_id,
                "company_id": current_user.company_id
            })
            
            if not crew:
                raise HTTPException(status_code=404, detail="Crew member not found")
            
            # Get file IDs
            passport_file_id = crew.get("passport_file_id")
            summary_file_id = crew.get("summary_file_id")
            
            if not passport_file_id and not summary_file_id:
                raise HTTPException(
                    status_code=400,
                    detail="No passport files associated with this crew member"
                )
            
            # Generate new filename
            new_filename = await CrewPassportRenameService._generate_passport_filename(crew)
            
            if not new_filename:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot generate filename: Missing required field (full_name_en)"
                )
            
            # Get Google Drive config
            gdrive_repo = CompanyGDriveConfigRepository()
            gdrive_config = await gdrive_repo.find_one({
                "company_id": current_user.company_id
            })
            
            if not gdrive_config:
                raise HTTPException(
                    status_code=404,
                    detail="Google Drive not configured for this company"
                )
            
            apps_script_url = gdrive_config.get("web_app_url") or gdrive_config.get("apps_script_url")
            
            if not apps_script_url:
                raise HTTPException(
                    status_code=400,
                    detail="Apps Script URL not configured"
                )
            
            # Check if Apps Script supports rename_file action
            logger.info("🔍 Checking Apps Script capabilities for passport rename...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    apps_script_url,
                    json={},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        test_result = await response.json()
                        available_actions = test_result.get("available_actions", [])
                        supported_actions = test_result.get("supported_actions", [])
                        
                        all_actions = available_actions + supported_actions
                        logger.info(f"📋 Apps Script available actions: {all_actions}")
                        
                        if "rename_file" not in all_actions:
                            logger.warning("⚠️ Apps Script does not support 'rename_file' action")
                            raise HTTPException(
                                status_code=501,
                                detail=f"Auto-rename feature not supported by Google Drive integration. Suggested filename: {new_filename}"
                            )
                        else:
                            logger.info("✅ Apps Script supports 'rename_file' action")
            
            # Rename files
            renamed_files = []
            
            # Rename passport file
            if passport_file_id:
                success = await CrewPassportRenameService._rename_file_on_drive(
                    file_id=passport_file_id,
                    new_name=new_filename,
                    apps_script_url=apps_script_url,
                    file_type="passport"
                )
                if success:
                    renamed_files.append("passport")
            
            # Rename summary file
            if summary_file_id:
                # Generate summary filename
                base_name = new_filename.rsplit('.', 1)[0]
                summary_filename = f"{base_name}_Summary.txt"
                
                success = await CrewPassportRenameService._rename_file_on_drive(
                    file_id=summary_file_id,
                    new_name=summary_filename,
                    apps_script_url=apps_script_url,
                    file_type="summary"
                )
                if success:
                    renamed_files.append("summary")
            
            # Return result
            if renamed_files:
                file_list = ", ".join(renamed_files)
                message = f"Files renamed successfully: {file_list}"
                
                return {
                    "success": True,
                    "message": message,
                    "crew_id": crew_id,
                    "crew_name": crew.get("full_name"),
                    "new_filename": new_filename,
                    "renamed_files": renamed_files
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to rename any files"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error in auto_rename_passport_files: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to rename passport files: {str(e)}"
            )
    
    @staticmethod
    async def _generate_passport_filename(crew: Dict) -> str:
        """
        Generate filename for passport using naming convention:
        {Rank}_{Full Name (Eng)}_Passport.pdf
        
        If rank is missing: {Full Name (Eng)}_Passport.pdf
        
        Examples: 
        - With rank: Master_NGUYEN VAN A_Passport.pdf
        - Without rank: NGUYEN VAN A_Passport.pdf
        
        Args:
            crew: Crew member data
            
        Returns:
            Generated filename string
        """
        try:
            # Get fields
            rank = crew.get("rank", "").strip()
            full_name_en = crew.get("full_name_en", "").strip()
            
            # If full_name_en is empty, use full_name
            if not full_name_en:
                full_name_en = crew.get("full_name", "").strip()
            
            # Validate full_name is required
            if not full_name_en:
                logger.warning("⚠️ Missing required field for filename generation:")
                logger.warning(f"   Full Name (Eng): {full_name_en}")
                return ""
            
            # Clean and format components
            # Remove special characters that are not allowed in filenames
            name_clean = full_name_en.replace("/", "-").replace("\\", "-").replace(":", "")
            
            # Generate filename with "Passport" as literal text
            if rank:
                rank_clean = rank.replace("/", "-").replace("\\", "-").replace(":", "")
                filename = f"{rank_clean}_{name_clean}_Passport.pdf"
            else:
                # No rank - skip rank part
                filename = f"{name_clean}_Passport.pdf"
                logger.info("ℹ️ Rank is empty, generating filename without rank")
            
            logger.info(f"📝 Generated filename: {filename}")
            
            return filename
            
        except Exception as e:
            logger.error(f"❌ Error generating filename: {e}")
            return ""
    
    @staticmethod
    async def _rename_file_on_drive(
        file_id: str,
        new_name: str,
        apps_script_url: str,
        file_type: str = "file"
    ) -> bool:
        """
        Rename a file on Google Drive via Apps Script
        
        Args:
            file_id: Google Drive file ID
            new_name: New filename
            apps_script_url: Apps Script web app URL
            file_type: Type of file (for logging)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🔄 Renaming {file_type} file {file_id} to {new_name}")
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "action": "rename_file",
                    "file_id": file_id,
                    "new_name": new_name
                }
                
                async with session.post(
                    apps_script_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success"):
                            logger.info(f"✅ {file_type.capitalize()} file renamed successfully")
                            return True
                        else:
                            error_msg = result.get("message", "Unknown error")
                            logger.warning(f"⚠️ Failed to rename {file_type} file: {error_msg}")
                            return False
                    else:
                        logger.warning(f"⚠️ Failed to rename {file_type} file: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Error renaming {file_type} file {file_id}: {e}")
            return False
