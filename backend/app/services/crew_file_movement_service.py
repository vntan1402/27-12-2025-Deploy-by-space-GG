"""
Crew File Movement Service
Handles moving crew files between ships and standby in Google Drive
"""
import logging
from typing import Dict, List, Optional
from fastapi import HTTPException

from app.utils.google_drive_helper import GoogleDriveHelper
from app.repositories.crew_repository import CrewRepository
from app.repositories.crew_certificate_repository import CrewCertificateRepository

logger = logging.getLogger(__name__)


class CrewFileMovementService:
    """Service for moving crew files in Google Drive"""
    
    @staticmethod
    async def move_crew_files_to_standby(
        company_id: str,
        crew_id: str,
        crew_name: str,
        from_ship_name: str
    ) -> Dict:
        """
        Move all crew files from ship folder to Standby folder
        
        Scenario: Sign Off (Ship → Standby)
        
        Files to move:
        - Passport file (if exists)
        - Passport summary file (if exists)
        - All crew certificates
        - All certificate summaries
        
        Args:
            company_id: Company UUID
            crew_id: Crew member UUID
            crew_name: Crew member full name
            from_ship_name: Ship name to move from
            
        Returns:
            {
                "success": boolean,
                "files_moved": {
                    "passport_moved": boolean,
                    "certificates_moved": number,
                    "summaries_moved": number
                },
                "message": string,
                "details": list of moved files
            }
        """
        logger.info(f"🚢→🏠 Moving crew files to Standby")
        logger.info(f"   Crew: {crew_name} ({crew_id})")
        logger.info(f"   From Ship: {from_ship_name}")
        
        try:
            # Initialize Google Drive helper
            drive_helper = GoogleDriveHelper(company_id)
            await drive_helper.load_config()
            
            moved_details = []
            files_moved = {
                "passport_moved": False,
                "certificates_moved": 0,
                "summaries_moved": 0
            }
            
            # 1. Get crew info for passport file IDs
            crew = await CrewRepository.find_by_id(crew_id)
            if not crew:
                raise HTTPException(status_code=404, detail="Crew member not found")
            
            # 2. Move passport files (if exist)
            passport_file_id = crew.get('passport_file_id')
            summary_file_id = crew.get('summary_file_id')
            
            if passport_file_id:
                # Move passport from: {ship}/Crew Records/Crew Passport
                # To: COMPANY DOCUMENT/Standby Crew/Crew Passport
                success = await CrewFileMovementService._move_file(
                    drive_helper=drive_helper,
                    file_id=passport_file_id,
                    from_folder_path=f"{from_ship_name}/Crew Records/Crew Passport",
                    to_folder_path="COMPANY DOCUMENT/Standby Crew/Crew Passport",
                    filename=f"passport_{crew.get('passport', 'unknown')}.pdf"
                )
                
                if success:
                    files_moved["passport_moved"] = True
                    moved_details.append(f"Passport file moved")
                    logger.info(f"✅ Passport file moved")
            
            if summary_file_id:
                success = await CrewFileMovementService._move_file(
                    drive_helper=drive_helper,
                    file_id=summary_file_id,
                    from_folder_path=f"{from_ship_name}/Crew Records/Crew Passport",
                    to_folder_path="COMPANY DOCUMENT/Standby Crew/Crew Passport",
                    filename=f"passport_{crew.get('passport', 'unknown')}_summary.txt"
                )
                
                if success:
                    files_moved["summaries_moved"] += 1
                    moved_details.append(f"Passport summary moved")
                    logger.info(f"✅ Passport summary moved")
            
            # 3. Get all certificates for this crew
            certificates = await CrewCertificateRepository.find_by_crew_id(crew_id)
            logger.info(f"📋 Found {len(certificates)} certificates for crew")
            
            # 4. Move each certificate and its summary
            for cert in certificates:
                cert_file_id = cert.get('cert_file_id')
                cert_summary_file_id = cert.get('summary_file_id')
                cert_name = cert.get('cert_name', 'unknown')
                cert_no = cert.get('cert_no', 'unknown')
                
                if cert_file_id:
                    # Move certificate from: {ship}/Crew Records/Crew Cert
                    # To: COMPANY DOCUMENT/Standby Crew/Crew Cert
                    success = await CrewFileMovementService._move_file(
                        drive_helper=drive_helper,
                        file_id=cert_file_id,
                        from_folder_path=f"{from_ship_name}/Crew Records/Crew Cert",
                        to_folder_path="COMPANY DOCUMENT/Standby Crew/Crew Cert",
                        filename=f"{crew_name}_{cert_name}_{cert_no}.pdf"
                    )
                    
                    if success:
                        files_moved["certificates_moved"] += 1
                        moved_details.append(f"Certificate: {cert_name}")
                        logger.info(f"✅ Certificate moved: {cert_name}")
                
                if cert_summary_file_id:
                    success = await CrewFileMovementService._move_file(
                        drive_helper=drive_helper,
                        file_id=cert_summary_file_id,
                        from_folder_path=f"{from_ship_name}/Crew Records/Crew Cert",
                        to_folder_path="COMPANY DOCUMENT/Standby Crew/Crew Cert",
                        filename=f"{crew_name}_{cert_name}_{cert_no}_summary.txt"
                    )
                    
                    if success:
                        files_moved["summaries_moved"] += 1
                        logger.info(f"✅ Certificate summary moved: {cert_name}")
            
            total_files = (
                (1 if files_moved["passport_moved"] else 0) +
                files_moved["certificates_moved"] +
                files_moved["summaries_moved"]
            )
            
            logger.info(f"🎉 File movement complete: {total_files} files moved")
            
            return {
                "success": True,
                "files_moved": files_moved,
                "message": f"Successfully moved {total_files} files to Standby folder",
                "details": moved_details
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error moving crew files to standby: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "files_moved": {"passport_moved": False, "certificates_moved": 0, "summaries_moved": 0},
                "message": f"Failed to move files: {str(e)}",
                "details": []
            }
    
    @staticmethod
    async def move_crew_files_from_standby_to_ship(
        company_id: str,
        crew_id: str,
        crew_name: str,
        to_ship_name: str
    ) -> Dict:
        """
        Move all crew files from Standby folder to ship folder
        
        Scenario: Sign On (Standby → Ship)
        
        Args:
            company_id: Company UUID
            crew_id: Crew member UUID
            crew_name: Crew member full name
            to_ship_name: Ship name to move to
            
        Returns:
            Same structure as move_crew_files_to_standby
        """
        logger.info(f"🏠→🚢 Moving crew files from Standby to Ship")
        logger.info(f"   Crew: {crew_name} ({crew_id})")
        logger.info(f"   To Ship: {to_ship_name}")
        
        try:
            drive_helper = GoogleDriveHelper(company_id)
            await drive_helper.load_config()
            
            moved_details = []
            files_moved = {
                "passport_moved": False,
                "certificates_moved": 0,
                "summaries_moved": 0
            }
            
            # 1. Get crew info
            crew = await CrewRepository.find_by_id(crew_id)
            if not crew:
                raise HTTPException(status_code=404, detail="Crew member not found")
            
            # 2. Move passport files (if exist)
            passport_file_id = crew.get('passport_file_id')
            summary_file_id = crew.get('summary_file_id')
            
            if passport_file_id:
                success = await CrewFileMovementService._move_file(
                    drive_helper=drive_helper,
                    file_id=passport_file_id,
                    from_folder_path="COMPANY DOCUMENT/Standby Crew/Crew Passport",
                    to_folder_path=f"{to_ship_name}/Crew Records/Crew Passport",
                    filename=f"passport_{crew.get('passport', 'unknown')}.pdf"
                )
                
                if success:
                    files_moved["passport_moved"] = True
                    moved_details.append(f"Passport file moved")
                    logger.info(f"✅ Passport file moved")
            
            if summary_file_id:
                success = await CrewFileMovementService._move_file(
                    drive_helper=drive_helper,
                    file_id=summary_file_id,
                    from_folder_path="COMPANY DOCUMENT/Standby Crew/Crew Passport",
                    to_folder_path=f"{to_ship_name}/Crew Records/Crew Passport",
                    filename=f"passport_{crew.get('passport', 'unknown')}_summary.txt"
                )
                
                if success:
                    files_moved["summaries_moved"] += 1
                    moved_details.append(f"Passport summary moved")
                    logger.info(f"✅ Passport summary moved")
            
            # 3. Get all certificates
            certificates = await CrewCertificateRepository.find_by_crew_id(crew_id)
            logger.info(f"📋 Found {len(certificates)} certificates for crew")
            
            # 4. Move each certificate
            for cert in certificates:
                cert_file_id = cert.get('cert_file_id')
                cert_summary_file_id = cert.get('summary_file_id')
                cert_name = cert.get('cert_name', 'unknown')
                cert_no = cert.get('cert_no', 'unknown')
                
                if cert_file_id:
                    success = await CrewFileMovementService._move_file(
                        drive_helper=drive_helper,
                        file_id=cert_file_id,
                        from_folder_path="COMPANY DOCUMENT/Standby Crew/Crew Cert",
                        to_folder_path=f"{to_ship_name}/Crew Records/Crew Cert",
                        filename=f"{crew_name}_{cert_name}_{cert_no}.pdf"
                    )
                    
                    if success:
                        files_moved["certificates_moved"] += 1
                        moved_details.append(f"Certificate: {cert_name}")
                        logger.info(f"✅ Certificate moved: {cert_name}")
                
                if cert_summary_file_id:
                    success = await CrewFileMovementService._move_file(
                        drive_helper=drive_helper,
                        file_id=cert_summary_file_id,
                        from_folder_path="COMPANY DOCUMENT/Standby Crew/Crew Cert",
                        to_folder_path=f"{to_ship_name}/Crew Records/Crew Cert",
                        filename=f"{crew_name}_{cert_name}_{cert_no}_summary.txt"
                    )
                    
                    if success:
                        files_moved["summaries_moved"] += 1
                        logger.info(f"✅ Certificate summary moved: {cert_name}")
            
            total_files = (
                (1 if files_moved["passport_moved"] else 0) +
                files_moved["certificates_moved"] +
                files_moved["summaries_moved"]
            )
            
            logger.info(f"🎉 File movement complete: {total_files} files moved")
            
            return {
                "success": True,
                "files_moved": files_moved,
                "message": f"Successfully moved {total_files} files to {to_ship_name}",
                "details": moved_details
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error moving crew files from standby: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "files_moved": {"passport_moved": False, "certificates_moved": 0, "summaries_moved": 0},
                "message": f"Failed to move files: {str(e)}",
                "details": []
            }
    
    @staticmethod
    async def move_crew_files_between_ships(
        company_id: str,
        crew_id: str,
        crew_name: str,
        from_ship_name: str,
        to_ship_name: str
    ) -> Dict:
        """
        Move all crew files between two ships
        
        Scenario: Ship Transfer (Ship A → Ship B)
        
        Args:
            company_id: Company UUID
            crew_id: Crew member UUID
            crew_name: Crew member full name
            from_ship_name: Source ship name
            to_ship_name: Destination ship name
            
        Returns:
            Same structure as other move methods
        """
        logger.info(f"🚢→🚢 Moving crew files between ships")
        logger.info(f"   Crew: {crew_name} ({crew_id})")
        logger.info(f"   From: {from_ship_name} → To: {to_ship_name}")
        
        try:
            drive_helper = GoogleDriveHelper(company_id)
            await drive_helper.load_config()
            
            moved_details = []
            files_moved = {
                "passport_moved": False,
                "certificates_moved": 0,
                "summaries_moved": 0
            }
            
            # 1. Get crew info
            crew = await CrewRepository.find_by_id(crew_id)
            if not crew:
                raise HTTPException(status_code=404, detail="Crew member not found")
            
            # 2. Move passport files (if exist)
            passport_file_id = crew.get('passport_file_id')
            summary_file_id = crew.get('summary_file_id')
            
            if passport_file_id:
                success = await CrewFileMovementService._move_file(
                    drive_helper=drive_helper,
                    file_id=passport_file_id,
                    from_folder_path=f"{from_ship_name}/Crew Records/Crew Passport",
                    to_folder_path=f"{to_ship_name}/Crew Records/Crew Passport",
                    filename=f"passport_{crew.get('passport', 'unknown')}.pdf"
                )
                
                if success:
                    files_moved["passport_moved"] = True
                    moved_details.append(f"Passport file moved")
                    logger.info(f"✅ Passport file moved")
            
            if summary_file_id:
                success = await CrewFileMovementService._move_file(
                    drive_helper=drive_helper,
                    file_id=summary_file_id,
                    from_folder_path=f"{from_ship_name}/Crew Records/Crew Passport",
                    to_folder_path=f"{to_ship_name}/Crew Records/Crew Passport",
                    filename=f"passport_{crew.get('passport', 'unknown')}_summary.txt"
                )
                
                if success:
                    files_moved["summaries_moved"] += 1
                    moved_details.append(f"Passport summary moved")
                    logger.info(f"✅ Passport summary moved")
            
            # 3. Get all certificates
            certificates = await CrewCertificateRepository.find_by_crew_id(crew_id)
            logger.info(f"📋 Found {len(certificates)} certificates for crew")
            
            # 4. Move each certificate
            for cert in certificates:
                cert_file_id = cert.get('cert_file_id')
                cert_summary_file_id = cert.get('summary_file_id')
                cert_name = cert.get('cert_name', 'unknown')
                cert_no = cert.get('cert_no', 'unknown')
                
                if cert_file_id:
                    success = await CrewFileMovementService._move_file(
                        drive_helper=drive_helper,
                        file_id=cert_file_id,
                        from_folder_path=f"{from_ship_name}/Crew Records/Crew Cert",
                        to_folder_path=f"{to_ship_name}/Crew Records/Crew Cert",
                        filename=f"{crew_name}_{cert_name}_{cert_no}.pdf"
                    )
                    
                    if success:
                        files_moved["certificates_moved"] += 1
                        moved_details.append(f"Certificate: {cert_name}")
                        logger.info(f"✅ Certificate moved: {cert_name}")
                
                if cert_summary_file_id:
                    success = await CrewFileMovementService._move_file(
                        drive_helper=drive_helper,
                        file_id=cert_summary_file_id,
                        from_folder_path=f"{from_ship_name}/Crew Records/Crew Cert",
                        to_folder_path=f"{to_ship_name}/Crew Records/Crew Cert",
                        filename=f"{crew_name}_{cert_name}_{cert_no}_summary.txt"
                    )
                    
                    if success:
                        files_moved["summaries_moved"] += 1
                        logger.info(f"✅ Certificate summary moved: {cert_name}")
            
            total_files = (
                (1 if files_moved["passport_moved"] else 0) +
                files_moved["certificates_moved"] +
                files_moved["summaries_moved"]
            )
            
            logger.info(f"🎉 File movement complete: {total_files} files moved")
            
            return {
                "success": True,
                "files_moved": files_moved,
                "message": f"Successfully moved {total_files} files from {from_ship_name} to {to_ship_name}",
                "details": moved_details
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error moving crew files between ships: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "files_moved": {"passport_moved": False, "certificates_moved": 0, "summaries_moved": 0},
                "message": f"Failed to move files: {str(e)}",
                "details": []
            }
    
    @staticmethod
    async def _find_folder_id_by_path(
        drive_helper: GoogleDriveHelper,
        folder_path: str
    ) -> Optional[str]:
        """
        Find folder ID by traversing path using debug_folder_structure (V1 approach)
        
        Args:
            drive_helper: Initialized GoogleDriveHelper instance
            folder_path: Folder path (e.g., "BROTHER 36/Crew Records/Crew List")
            
        Returns:
            Folder ID if found, None otherwise
        """
        logger.info(f"🔍 Finding folder ID for path: {folder_path}")
        
        try:
            # Parse folder path
            path_parts = folder_path.split('/')
            if len(path_parts) < 1:
                logger.error(f"Invalid folder path: {folder_path}")
                return None
            
            logger.info(f"   Path parts: {path_parts}")
            
            # Start from root folder
            current_folder_id = drive_helper.folder_id
            
            # Traverse path
            for i, folder_name in enumerate(path_parts):
                logger.info(f"   Step {i+1}/{len(path_parts)}: Looking for '{folder_name}' in {current_folder_id}")
                
                # Use debug_folder_structure to list folders
                payload = {
                    "action": "debug_folder_structure",
                    "parent_folder_id": current_folder_id
                }
                
                result = await drive_helper.call_apps_script(payload, timeout=30.0)
                
                if not result.get('success'):
                    logger.error(f"❌ Failed to list folders: {result.get('message')}")
                    return None
                
                # Find matching folder
                folders = result.get('folders', [])
                found = False
                
                for folder in folders:
                    if folder.get('name', '').strip().lower() == folder_name.lower():
                        current_folder_id = folder.get('id')
                        logger.info(f"   ✅ Found '{folder_name}': {current_folder_id}")
                        found = True
                        break
                
                if not found:
                    logger.warning(f"   ❌ Folder not found: '{folder_name}'")
                    logger.info(f"   Available folders: {[f.get('name') for f in folders]}")
                    return None
            
            logger.info(f"✅ Final folder ID: {current_folder_id}")
            return current_folder_id
                
        except Exception as e:
            logger.error(f"❌ Error finding folder: {e}")
            return None
    
    @staticmethod
    async def _move_file(
        drive_helper: GoogleDriveHelper,
        file_id: str,
        from_folder_path: str,
        to_folder_path: str,
        filename: str
    ) -> bool:
        """
        Helper method to move a single file via Apps Script
        
        Strategy:
        1. Find target folder ID by path
        2. Call Apps Script move_file with target_folder_id
        
        Args:
            drive_helper: Initialized GoogleDriveHelper instance
            file_id: Google Drive file ID
            from_folder_path: Source folder path (for logging)
            to_folder_path: Destination folder path
            filename: Filename (for logging/debugging)
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"📦 Moving file: {filename}")
        logger.info(f"   From: {from_folder_path}")
        logger.info(f"   To: {to_folder_path}")
        logger.info(f"   File ID: {file_id}")
        
        try:
            # Step 1: Find target folder ID
            target_folder_id = await CrewFileMovementService._find_folder_id_by_path(
                drive_helper,
                to_folder_path
            )
            
            if not target_folder_id:
                logger.error(f"❌ Target folder not found: {to_folder_path}")
                return False
            
            logger.info(f"✅ Target folder ID: {target_folder_id}")
            
            # Step 2: Move file using folder ID
            payload = {
                "action": "move_file",
                "file_id": file_id,
                "target_folder_id": target_folder_id
            }
            
            result = await drive_helper.call_apps_script(payload, timeout=60.0)
            
            if result.get('success'):
                logger.info(f"✅ File moved successfully: {filename}")
                return True
            else:
                logger.warning(f"⚠️ File move failed: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error moving file {filename}: {e}")
            return False
