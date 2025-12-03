import logging
import aiohttp
from typing import Dict, List
from fastapi import HTTPException
from datetime import datetime, timezone

from app.db.mongodb import mongo_db
from app.models.user import UserResponse

logger = logging.getLogger(__name__)


class CrewCertificateRenameService:
    """Service for auto-renaming crew certificate files on Google Drive"""
    
    @staticmethod
    async def bulk_auto_rename_certificate_files(
        certificate_ids: List[str],
        current_user: UserResponse
    ) -> Dict:
        """
        Bulk auto rename crew certificate files using naming convention:
        {Rank}_{Full Name (Eng)}_{Certificate Name}.pdf
        
        Example: Master_NGUYEN VAN A_Certificate of Competency (COC).pdf
        
        Args:
            certificate_ids: List of certificate IDs to rename
            current_user: Current user making the request
            
        Returns:
            Dict with bulk rename result
        """
        try:
            company_id = current_user.company
            
            # Get Google Drive config once
            gdrive_config = await mongo_db.find_one("company_gdrive_config", {
                "company_id": company_id
            })
            
            if not gdrive_config:
                raise HTTPException(
                    status_code=404,
                    detail="Google Drive not configured for this company"
                )
            
            apps_script_url = gdrive_config.get("web_app_url") or gdrive_config.get("apps_script_url")
            
            if not apps_script_url:
                raise HTTPException(
                    status_code=500,
                    detail="Apps Script URL not found in Google Drive config"
                )
            
            results = {
                "success": 0,
                "failed": 0,
                "details": []
            }
            
            # Process each certificate
            for cert_id in certificate_ids:
                try:
                    result = await CrewCertificateRenameService._rename_single_certificate(
                        cert_id=cert_id,
                        company_id=company_id,
                        apps_script_url=apps_script_url
                    )
                    
                    if result["success"]:
                        results["success"] += 1
                        results["details"].append({
                            "cert_id": cert_id,
                            "status": "success",
                            "message": result["message"]
                        })
                    else:
                        results["failed"] += 1
                        results["details"].append({
                            "cert_id": cert_id,
                            "status": "failed",
                            "message": result["message"]
                        })
                        
                except Exception as e:
                    results["failed"] += 1
                    results["details"].append({
                        "cert_id": cert_id,
                        "status": "failed",
                        "message": str(e)
                    })
            
            return {
                "success": results["success"] > 0,
                "total": len(certificate_ids),
                "renamed": results["success"],
                "failed": results["failed"],
                "details": results["details"]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error in bulk_auto_rename_certificate_files: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to bulk rename certificate files: {str(e)}"
            )
    
    @staticmethod
    async def _rename_single_certificate(
        cert_id: str,
        company_id: str,
        apps_script_url: str
    ) -> Dict:
        """Rename a single certificate file"""
        try:
            # Get certificate
            cert = await mongo_db.find_one("crew_certificates", {
                "id": cert_id,
                "company_id": company_id
            })
            
            if not cert:
                return {
                    "success": False,
                    "message": "Certificate not found"
                }
            
            # Get crew member
            crew_id = cert.get("crew_id")
            if not crew_id:
                return {
                    "success": False,
                    "message": "Certificate has no associated crew member"
                }
            
            crew = await mongo_db.find_one("crew", {
                "id": crew_id,
                "company_id": company_id
            })
            
            if not crew:
                return {
                    "success": False,
                    "message": "Crew member not found"
                }
            
            # Get file ID
            cert_file_id = cert.get("crew_cert_file_id")
            summary_file_id = cert.get("crew_cert_summary_file_id")
            
            if not cert_file_id and not summary_file_id:
                return {
                    "success": False,
                    "message": "No files associated with this certificate"
                }
            
            # Generate new filename
            new_filename = await CrewCertificateRenameService._generate_certificate_filename(
                crew=crew,
                cert=cert
            )
            
            if not new_filename:
                return {
                    "success": False,
                    "message": "Cannot generate filename: Missing required fields"
                }
            
            renamed_files = []
            
            # Rename certificate file
            if cert_file_id:
                success = await CrewCertificateRenameService._rename_file_on_drive(
                    file_id=cert_file_id,
                    new_name=new_filename,
                    apps_script_url=apps_script_url,
                    file_type="certificate"
                )
                if success:
                    renamed_files.append("certificate")
            
            # Rename summary file
            if summary_file_id:
                summary_filename = new_filename.replace(".pdf", "_Summary.txt")
                success = await CrewCertificateRenameService._rename_file_on_drive(
                    file_id=summary_file_id,
                    new_name=summary_filename,
                    apps_script_url=apps_script_url,
                    file_type="summary"
                )
                if success:
                    renamed_files.append("summary")
            
            if renamed_files:
                return {
                    "success": True,
                    "message": f"Renamed: {', '.join(renamed_files)}",
                    "new_filename": new_filename
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to rename any files"
                }
                
        except Exception as e:
            logger.error(f"❌ Error renaming certificate {cert_id}: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    @staticmethod
    async def _generate_certificate_filename(crew: Dict, cert: Dict) -> str:
        """
        Generate filename for certificate using naming convention:
        {Rank}_{Full Name (Eng)}_{Certificate Name}.pdf
        
        If rank is missing: {Full Name (Eng)}_{Certificate Name}.pdf
        
        Examples: 
        - With rank: Master_NGUYEN VAN A_Certificate of Competency (COC).pdf
        - Without rank: NGUYEN VAN A_Medical Certificate.pdf
        
        Args:
            crew: Crew member data
            cert: Certificate data
            
        Returns:
            Generated filename string
        """
        try:
            # Get fields from crew
            rank = crew.get("rank", "").strip()
            full_name_en = crew.get("full_name_en", "").strip()
            
            # If full_name_en is empty, use full_name
            if not full_name_en:
                full_name_en = crew.get("full_name", "").strip()
            
            # Get certificate name
            cert_name = cert.get("cert_name", "").strip()
            
            # Validate required fields
            if not full_name_en or not cert_name:
                logger.warning("⚠️ Missing required fields for filename generation:")
                logger.warning(f"   Full Name (Eng): {full_name_en}")
                logger.warning(f"   Certificate Name: {cert_name}")
                return ""
            
            # Clean and format components
            name_clean = full_name_en.replace("\\", "-").replace(":", "").replace("/", "-")
            cert_name_clean = cert_name.replace("\\", "-").replace(":", "").replace("/", "-")
            
            # Generate filename
            if rank:
                rank_clean = rank.strip()
                filename = f"{rank_clean}_{name_clean}_{cert_name_clean}.pdf"
            else:
                filename = f"{name_clean}_{cert_name_clean}.pdf"
            
            logger.info(f"📝 Generated certificate filename: {filename}")
            
            return filename
            
        except Exception as e:
            logger.error(f"❌ Error generating certificate filename: {e}")
            return ""
    
    @staticmethod
    async def _rename_file_on_drive(
        file_id: str,
        new_name: str,
        apps_script_url: str,
        file_type: str
    ) -> bool:
        """Rename file on Google Drive via Apps Script"""
        try:
            payload = {
                "action": "rename_file",
                "file_id": file_id,
                "new_name": new_name
            }
            
            logger.info(f"🔄 Renaming {file_type} file on Google Drive...")
            logger.info(f"   File ID: {file_id}")
            logger.info(f"   New Name: {new_name}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    apps_script_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        text = await response.text()
                        logger.error(f"❌ Apps Script returned status {response.status}")
                        logger.error(f"   Response: {text}")
                        return False
                    
                    result = await response.json()
                    
                    if result.get("status") == "SUCCESS":
                        logger.info(f"✅ Successfully renamed {file_type} file: {new_name}")
                        return True
                    else:
                        error_msg = result.get("message", "Unknown error")
                        logger.error(f"❌ Failed to rename {file_type} file: {error_msg}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Error calling Apps Script to rename {file_type} file: {e}")
            return False
