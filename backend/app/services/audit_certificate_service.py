import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.audit_certificate import AuditCertificateCreate, AuditCertificateUpdate, AuditCertificateResponse, BulkDeleteAuditCertificateRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db
from app.utils.certificate_abbreviation import generate_certificate_abbreviation

logger = logging.getLogger(__name__)

class AuditCertificateService:
    """Service for Audit Certificate operations (ISM/ISPS/MLC certificates)"""
    
    collection_name = "audit_certificates"
    
    @staticmethod
    async def get_audit_certificates(ship_id: Optional[str], cert_type: Optional[str], current_user: UserResponse) -> List[AuditCertificateResponse]:
        """Get audit certificates with optional ship and type filter"""
        filters = {}
        if ship_id:
            filters["ship_id"] = ship_id
        if cert_type:
            filters["cert_type"] = cert_type
        
        certs = await mongo_db.find_all(AuditCertificateService.collection_name, filters)
        
        # Handle backward compatibility and enhance with abbreviations
        result = []
        for cert in certs:
            if not cert.get("cert_name") and cert.get("doc_name"):
                cert["cert_name"] = cert.get("doc_name")
            
            if not cert.get("cert_no") and cert.get("doc_no"):
                cert["cert_no"] = cert.get("doc_no")
            
            if not cert.get("note") and cert.get("notes"):
                cert["note"] = cert.get("notes")
            
            if not cert.get("cert_name"):
                cert["cert_name"] = "Untitled Certificate"
            
            if not cert.get("status"):
                cert["status"] = "Valid"
            
            # Generate certificate abbreviation if not present
            if not cert.get("cert_abbreviation") and cert.get("cert_name"):
                cert["cert_abbreviation"] = await generate_certificate_abbreviation(cert.get("cert_name"))
            
            result.append(AuditCertificateResponse(**cert))
        
        return result
    
    @staticmethod
    async def get_audit_certificate_by_id(cert_id: str, current_user: UserResponse) -> AuditCertificateResponse:
        """Get audit certificate by ID"""
        cert = await mongo_db.find_one(AuditCertificateService.collection_name, {"id": cert_id})
        
        if not cert:
            raise HTTPException(status_code=404, detail="Audit Certificate not found")
        
        # Backward compatibility
        if not cert.get("cert_name") and cert.get("doc_name"):
            cert["cert_name"] = cert.get("doc_name")
        
        if not cert.get("cert_no") and cert.get("doc_no"):
            cert["cert_no"] = cert.get("doc_no")
        
        if not cert.get("note") and cert.get("notes"):
            cert["note"] = cert.get("notes")
        
        if not cert.get("cert_name"):
            cert["cert_name"] = "Untitled Certificate"
        
        if not cert.get("status"):
            cert["status"] = "Valid"
        
        # Generate certificate abbreviation if not present
        if not cert.get("cert_abbreviation") and cert.get("cert_name"):
            cert["cert_abbreviation"] = await generate_certificate_abbreviation(cert.get("cert_name"))
        
        return AuditCertificateResponse(**cert)
    
    @staticmethod
    async def create_audit_certificate(cert_data: AuditCertificateCreate, current_user: UserResponse) -> AuditCertificateResponse:
        """Create new audit certificate"""
        cert_dict = cert_data.dict()
        cert_dict["id"] = str(uuid.uuid4())
        cert_dict["created_at"] = datetime.now(timezone.utc)
        
        # Normalize issued_by to abbreviation
        if cert_dict.get("issued_by"):
            from app.utils.issued_by_abbreviation import normalize_issued_by
            try:
                original_issued_by = cert_dict["issued_by"]
                normalized_issued_by = normalize_issued_by(original_issued_by)
                cert_dict["issued_by"] = normalized_issued_by
                if normalized_issued_by != original_issued_by:
                    logger.info(f"✅ Normalized Issued By: '{original_issued_by}' → '{normalized_issued_by}'")
            except Exception as e:
                logger.warning(f"⚠️ Could not normalize issued_by: {e}")
        
        # Generate certificate abbreviation if not provided
        if not cert_dict.get("cert_abbreviation") and cert_dict.get("cert_name"):
            cert_dict["cert_abbreviation"] = await generate_certificate_abbreviation(cert_dict.get("cert_name"))
            logger.info(f"✅ Generated cert abbreviation: '{cert_dict['cert_name']}' → '{cert_dict['cert_abbreviation']}'")
        
        await mongo_db.create(AuditCertificateService.collection_name, cert_dict)
        
        logger.info(f"✅ Audit Certificate created: {cert_dict['cert_name']} ({cert_data.cert_type})")
        
        return AuditCertificateResponse(**cert_dict)
    
    @staticmethod
    async def update_audit_certificate(cert_id: str, cert_data: AuditCertificateUpdate, current_user: UserResponse) -> AuditCertificateResponse:
        """Update audit certificate"""
        cert = await mongo_db.find_one(AuditCertificateService.collection_name, {"id": cert_id})
        if not cert:
            raise HTTPException(status_code=404, detail="Audit Certificate not found")
        
        update_data = cert_data.dict(exclude_unset=True)
        
        # Normalize issued_by to abbreviation if it's being updated
        if update_data.get("issued_by"):
            from app.utils.issued_by_abbreviation import normalize_issued_by
            try:
                original_issued_by = update_data["issued_by"]
                normalized_issued_by = normalize_issued_by(original_issued_by)
                update_data["issued_by"] = normalized_issued_by
                if normalized_issued_by != original_issued_by:
                    logger.info(f"✅ Normalized Issued By: '{original_issued_by}' → '{normalized_issued_by}'")
            except Exception as e:
                logger.warning(f"⚠️ Could not normalize issued_by: {e}")
        
        if update_data:
            await mongo_db.update(AuditCertificateService.collection_name, {"id": cert_id}, update_data)
        
        updated_cert = await mongo_db.find_one(AuditCertificateService.collection_name, {"id": cert_id})
        
        if not updated_cert.get("cert_name") and updated_cert.get("doc_name"):
            updated_cert["cert_name"] = updated_cert.get("doc_name")
        
        logger.info(f"✅ Audit Certificate updated: {cert_id}")
        
        return AuditCertificateResponse(**updated_cert)
    
    @staticmethod
    async def delete_audit_certificate(cert_id: str, current_user: UserResponse) -> dict:
        """Delete audit certificate"""
        cert = await mongo_db.find_one(AuditCertificateService.collection_name, {"id": cert_id})
        if not cert:
            raise HTTPException(status_code=404, detail="Audit Certificate not found")
        
        await mongo_db.delete(AuditCertificateService.collection_name, {"id": cert_id})
        
        logger.info(f"✅ Audit Certificate deleted: {cert_id}")
        
        return {"message": "Audit Certificate deleted successfully"}
    
    @staticmethod
    async def bulk_delete_audit_certificates(request: BulkDeleteAuditCertificateRequest, current_user: UserResponse) -> dict:
        """Bulk delete audit certificates"""
        deleted_count = 0
        for cert_id in request.document_ids:
            try:
                await AuditCertificateService.delete_audit_certificate(cert_id, current_user)
                deleted_count += 1
            except:
                continue
        
        logger.info(f"✅ Bulk deleted {deleted_count} audit certificates")
        
        return {
            "message": f"Successfully deleted {deleted_count} audit certificates",
            "deleted_count": deleted_count
        }
    
    @staticmethod
    async def check_duplicate(ship_id: str, cert_name: str, cert_no: Optional[str], current_user: UserResponse) -> dict:
        """Check if audit certificate is duplicate"""
        filters = {
            "ship_id": ship_id,
            "cert_name": cert_name
        }
        
        if cert_no:
            filters["cert_no"] = cert_no
        
        existing = await mongo_db.find_one(AuditCertificateService.collection_name, filters)
        
        return {
            "is_duplicate": existing is not None,
            "existing_id": existing.get("id") if existing else None
        }
