import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile

from app.models.crew_certificate import (
    CrewCertificateCreate,
    CrewCertificateUpdate,
    CrewCertificateResponse,
    BulkDeleteCrewCertificateRequest
)
from app.models.user import UserResponse, UserRole
from app.repositories.crew_certificate_repository import CrewCertificateRepository
from app.repositories.crew_repository import CrewRepository

logger = logging.getLogger(__name__)

class CrewCertificateService:
    """Business logic for crew certificate management"""
    
    @staticmethod
    async def get_all_crew_certificates(
        crew_id: Optional[str],
        current_user: UserResponse
    ) -> List[CrewCertificateResponse]:
        """
        Get ALL crew certificates for the company (no ship filter)
        Includes both ship-assigned and Standby crew certificates
        """
        filters = {}
        
        # Add company filter - required for all users except system admin
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            if not current_user.company:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            filters["company_id"] = current_user.company
        
        # Add crew_id filter if provided
        if crew_id:
            filters["crew_id"] = crew_id
        
        certificates = await CrewCertificateRepository.find_all(filters)
        
        logger.info(f"📋 Retrieved {len(certificates)} crew certificates for company (all ships + standby)")
        
        return [CrewCertificateResponse(**cert) for cert in certificates]
    
    @staticmethod
    async def get_crew_certificates(
        crew_id: Optional[str], 
        company_id: Optional[str],
        current_user: UserResponse
    ) -> List[CrewCertificateResponse]:
        """Get crew certificates with optional filters"""
        filters = {}
        
        # Add crew_id filter if provided
        if crew_id:
            filters["crew_id"] = crew_id
        
        # Add company filter for non-admin users
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            filters["company_id"] = current_user.company
        elif company_id:
            filters["company_id"] = company_id
        
        certificates = await CrewCertificateRepository.find_all(filters)
        return [CrewCertificateResponse(**cert) for cert in certificates]
    
    @staticmethod
    async def get_crew_certificate_by_id(cert_id: str, current_user: UserResponse) -> CrewCertificateResponse:
        """Get crew certificate by ID"""
        cert = await CrewCertificateRepository.find_by_id(cert_id)
        
        if not cert:
            raise HTTPException(status_code=404, detail="Crew certificate not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            if cert.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        return CrewCertificateResponse(**cert)
    
    @staticmethod
    async def create_crew_certificate(cert_data: CrewCertificateCreate, current_user: UserResponse) -> CrewCertificateResponse:
        """Create new crew certificate"""
        # Verify crew exists
        crew = await CrewRepository.find_by_id(cert_data.crew_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Crew member not found")
        
        # Create certificate document
        cert_dict = cert_data.dict()
        cert_dict["id"] = str(uuid.uuid4())
        cert_dict["created_at"] = datetime.now(timezone.utc)
        cert_dict["created_by"] = current_user.username
        
        await CrewCertificateRepository.create(cert_dict)
        
        logger.info(f"✅ Crew certificate created: {cert_dict['cert_name']} for crew {cert_data.crew_id}")
        
        return CrewCertificateResponse(**cert_dict)
    
    @staticmethod
    async def update_crew_certificate(
        cert_id: str, 
        cert_data: CrewCertificateUpdate, 
        current_user: UserResponse
    ) -> CrewCertificateResponse:
        """Update crew certificate"""
        cert = await CrewCertificateRepository.find_by_id(cert_id)
        if not cert:
            raise HTTPException(status_code=404, detail="Crew certificate not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            if cert.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare update data
        update_data = cert_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = current_user.username
        
        if update_data:
            await CrewCertificateRepository.update(cert_id, update_data)
        
        # Get updated certificate
        updated_cert = await CrewCertificateRepository.find_by_id(cert_id)
        
        logger.info(f"✅ Crew certificate updated: {cert_id}")
        
        return CrewCertificateResponse(**updated_cert)
    
    @staticmethod
    async def delete_crew_certificate(cert_id: str, current_user: UserResponse) -> dict:
        """Delete crew certificate"""
        cert = await CrewCertificateRepository.find_by_id(cert_id)
        if not cert:
            raise HTTPException(status_code=404, detail="Crew certificate not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            if cert.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        await CrewCertificateRepository.delete(cert_id)
        
        logger.info(f"✅ Crew certificate deleted: {cert_id}")
        
        return {"message": "Crew certificate deleted successfully"}
    
    @staticmethod
    async def bulk_delete_crew_certificates(
        request: BulkDeleteCrewCertificateRequest, 
        current_user: UserResponse
    ) -> dict:
        """Bulk delete crew certificates including associated Google Drive files"""
        from app.db.mongodb import mongo_db
        
        # Get company ID
        company_id = current_user.company
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            if not company_id:
                raise HTTPException(status_code=400, detail="User has no company assigned")
        
        cert_ids = request.certificate_ids
        logger.info(f"🗑️ Bulk delete crew certificates request: {len(cert_ids)} certificate(s)")
        
        deleted_count = 0
        files_deleted = 0
        errors = []
        
        for cert_id in cert_ids:
            try:
                # Check if certificate exists
                cert = await mongo_db.find_one("crew_certificates", {
                    "id": cert_id,
                    "company_id": company_id
                })
                
                if not cert:
                    logger.warning(f"⚠️ Certificate not found: {cert_id}")
                    errors.append(f"Certificate {cert_id} not found")
                    continue
                
                # TODO: Delete Google Drive files if configured
                # For now, just delete from database
                
                # Delete from database
                await mongo_db.delete("crew_certificates", {"id": cert_id})
                deleted_count += 1
                logger.info(f"✅ Crew certificate deleted: {cert_id}")
                
            except Exception as e:
                error_msg = f"Error deleting certificate {cert_id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        # If no certificates were deleted at all, return error
        if deleted_count == 0 and len(errors) > 0:
            error_details = "; ".join(errors)
            raise HTTPException(status_code=404, detail=f"No certificates deleted. {error_details}")
        
        message = f"Deleted {deleted_count} certificate(s)"
        if files_deleted > 0:
            message += f", {files_deleted} file(s) deleted from Google Drive"
        if errors:
            message += f", {len(errors)} error(s)"
        
        logger.info(f"✅ Bulk delete complete: {deleted_count} certificates deleted")
        
        return {
            "success": True,
            "message": message,
            "deleted_count": deleted_count,
            "files_deleted": files_deleted,
            "errors": errors if errors else None,
            "partial_success": len(errors) > 0 and deleted_count > 0
        }
    
    @staticmethod
    async def check_duplicate(
        crew_id: str, 
        cert_name: str, 
        cert_no: Optional[str],
        current_user: UserResponse
    ) -> dict:
        """Check if crew certificate is duplicate"""
        existing = await CrewCertificateRepository.check_duplicate(crew_id, cert_name, cert_no)
        
        return {
            "is_duplicate": existing is not None,
            "existing_certificate": CrewCertificateResponse(**existing).dict() if existing else None
        }
    
    @staticmethod
    async def analyze_crew_certificate_file(
        file: UploadFile, 
        crew_id: str,
        current_user: UserResponse
    ) -> dict:
        """Analyze crew certificate file using AI (simplified version)"""
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Validate file size (10MB limit)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
        
        # Read file content
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file received")
        
        logger.info(f"📄 Analyzing crew certificate file: {file.filename} ({len(file_content)} bytes)")
        
        # TODO: Implement actual AI analysis
        # For now, return mock data
        
        return {
            "success": True,
            "message": "Crew certificate analyzed successfully (mock data)",
            "analysis": {
                "crew_name": "Nguyen Van A",
                "passport": "N1234567",
                "cert_name": "CERTIFICATE OF COMPETENCY",
                "cert_no": "COC-2024-001",
                "issued_date": "15/01/2024",
                "cert_expiry": "15/01/2029",
                "issued_by": "Vietnam Maritime Administration",
                "rank": "Chief Engineer"
            }
        }
