import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.company_cert import CompanyCertCreate, CompanyCertUpdate, CompanyCertResponse, BulkDeleteCompanyCertRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db
from app.utils.background_tasks import delete_file_background

logger = logging.getLogger(__name__)

class CompanyCertService:
    """Service for Company Certificate operations"""
    
    collection_name = "company_certificates"
    
    @staticmethod
    async def get_company_certs(company: Optional[str], current_user: UserResponse) -> List[CompanyCertResponse]:
        """Get company certificates, optionally filtered by company"""
        filters = {}
        if company:
            filters["company"] = company
        else:
            # If no company specified, return certs for user's company
            filters["company"] = current_user.company
        
        certs = await mongo_db.find_all(CompanyCertService.collection_name, filters)
        
        # Import abbreviation utilities
        from app.utils.certificate_abbreviation import generate_certificate_abbreviation
        from app.utils.issued_by_abbreviation import generate_organization_abbreviation
        
        result = []
        for cert in certs:
            if not cert.get("cert_name"):
                cert["cert_name"] = "Untitled Certificate"
            
            if not cert.get("status"):
                cert["status"] = "Valid"
            
            # Map google_drive_file_id to file_id for backward compatibility
            if cert.get("google_drive_file_id") and not cert.get("file_id"):
                cert["file_id"] = cert.get("google_drive_file_id")
            
            # Generate certificate abbreviation if not present
            if not cert.get("cert_abbreviation") and cert.get("cert_name"):
                cert["cert_abbreviation"] = await generate_certificate_abbreviation(cert.get("cert_name"))
            
            # Generate organization abbreviation for issued_by if not present
            if not cert.get("issued_by_abbreviation") and cert.get("issued_by"):
                cert["issued_by_abbreviation"] = generate_organization_abbreviation(cert.get("issued_by"))
            
            result.append(CompanyCertResponse(**cert))
        
        return result
    
    @staticmethod
    async def get_company_cert_by_id(cert_id: str, current_user: UserResponse) -> CompanyCertResponse:
        """Get company certificate by ID"""
        cert = await mongo_db.find_one(CompanyCertService.collection_name, {"id": cert_id})
        
        if not cert:
            raise HTTPException(status_code=404, detail="Company Certificate not found")
        
        if not cert.get("cert_name"):
            cert["cert_name"] = "Untitled Certificate"
        
        if not cert.get("status"):
            cert["status"] = "Valid"
        
        # Map google_drive_file_id to file_id
        if cert.get("google_drive_file_id") and not cert.get("file_id"):
            cert["file_id"] = cert.get("google_drive_file_id")
        
        return CompanyCertResponse(**cert)
    
    @staticmethod
    async def create_company_cert(cert_data: CompanyCertCreate, current_user: UserResponse) -> CompanyCertResponse:
        """Create new company certificate"""
        cert_dict = cert_data.model_dump()
        cert_dict["id"] = str(uuid.uuid4())
        cert_dict["created_at"] = datetime.now(timezone.utc)
        cert_dict["created_by"] = current_user.id
        
        # Ensure company is set
        if not cert_dict.get("company"):
            cert_dict["company"] = current_user.company
        
        await mongo_db.insert_one(CompanyCertService.collection_name, cert_dict)
        
        logger.info(f"✅ Created company certificate: {cert_dict['id']}")
        return CompanyCertResponse(**cert_dict)
    
    @staticmethod
    async def update_company_cert(cert_id: str, cert_data: CompanyCertUpdate, current_user: UserResponse) -> CompanyCertResponse:
        """Update company certificate"""
        existing_cert = await mongo_db.find_one(CompanyCertService.collection_name, {"id": cert_id})
        
        if not existing_cert:
            raise HTTPException(status_code=404, detail="Company Certificate not found")
        
        update_data = cert_data.model_dump(exclude_unset=True)
        
        if update_data:
            await mongo_db.update_one(
                CompanyCertService.collection_name,
                {"id": cert_id},
                {"$set": update_data}
            )
            logger.info(f"✅ Updated company certificate: {cert_id}")
        
        updated_cert = await mongo_db.find_one(CompanyCertService.collection_name, {"id": cert_id})
        
        # Map google_drive_file_id to file_id
        if updated_cert.get("google_drive_file_id") and not updated_cert.get("file_id"):
            updated_cert["file_id"] = updated_cert.get("google_drive_file_id")
        
        return CompanyCertResponse(**updated_cert)
    
    @staticmethod
    async def delete_company_cert(cert_id: str, current_user: UserResponse, background_tasks) -> dict:
        """Delete company certificate"""
        cert = await mongo_db.find_one(CompanyCertService.collection_name, {"id": cert_id})
        
        if not cert:
            raise HTTPException(status_code=404, detail="Company Certificate not found")
        
        # Delete from database
        await mongo_db.delete_one(CompanyCertService.collection_name, {"id": cert_id})
        
        # Schedule background file deletion if file exists
        file_id = cert.get("file_id") or cert.get("google_drive_file_id")
        summary_file_id = cert.get("summary_file_id")
        
        if file_id or summary_file_id:
            background_tasks.add_task(
                delete_file_background,
                file_id=file_id,
                summary_file_id=summary_file_id,
                cert_id=cert_id,
                cert_name=cert.get("cert_name", "Unknown")
            )
        
        logger.info(f"✅ Deleted company certificate: {cert_id}")
        return {"message": "Company Certificate deleted successfully", "id": cert_id}
    
    @staticmethod
    async def bulk_delete_company_certs(request: BulkDeleteCompanyCertRequest, current_user: UserResponse, background_tasks) -> dict:
        """Bulk delete company certificates"""
        deleted_count = 0
        failed_ids = []
        
        for cert_id in request.cert_ids:
            try:
                await CompanyCertService.delete_company_cert(cert_id, current_user, background_tasks)
                deleted_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to delete company certificate {cert_id}: {e}")
                failed_ids.append(cert_id)
        
        return {
            "message": f"Deleted {deleted_count} company certificates",
            "deleted_count": deleted_count,
            "failed_ids": failed_ids
        }
