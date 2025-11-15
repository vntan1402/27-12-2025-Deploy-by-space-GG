import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile

from app.models.certificate import (
    CertificateCreate, 
    CertificateUpdate, 
    CertificateResponse,
    BulkDeleteRequest
)
from app.models.user import UserResponse
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.ship_repository import ShipRepository

logger = logging.getLogger(__name__)

class CertificateService:
    """Business logic for certificate management"""
    
    @staticmethod
    async def get_certificates(ship_id: Optional[str], current_user: UserResponse) -> List[CertificateResponse]:
        """Get certificates, optionally filtered by ship"""
        certificates = await CertificateRepository.find_all(ship_id=ship_id)
        
        # TODO: Add access control based on user's company
        
        return [CertificateResponse(**cert) for cert in certificates]
    
    @staticmethod
    async def get_certificate_by_id(cert_id: str, current_user: UserResponse) -> CertificateResponse:
        """Get certificate by ID"""
        cert = await CertificateRepository.find_by_id(cert_id)
        
        if not cert:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # TODO: Check access permission
        
        return CertificateResponse(**cert)
    
    @staticmethod
    async def create_certificate(cert_data: CertificateCreate, current_user: UserResponse) -> CertificateResponse:
        """Create new certificate"""
        # Verify ship exists
        ship = await ShipRepository.find_by_id(cert_data.ship_id)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Create certificate document
        cert_dict = cert_data.dict()
        cert_dict["id"] = str(uuid.uuid4())
        cert_dict["created_at"] = datetime.now(timezone.utc)
        
        await CertificateRepository.create(cert_dict)
        
        logger.info(f"✅ Certificate created: {cert_dict['cert_name']}")
        
        return CertificateResponse(**cert_dict)
    
    @staticmethod
    async def update_certificate(cert_id: str, cert_data: CertificateUpdate, current_user: UserResponse) -> CertificateResponse:
        """Update certificate"""
        cert = await CertificateRepository.find_by_id(cert_id)
        if not cert:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Prepare update data
        update_data = cert_data.dict(exclude_unset=True)
        
        if update_data:
            await CertificateRepository.update(cert_id, update_data)
        
        # Get updated certificate
        updated_cert = await CertificateRepository.find_by_id(cert_id)
        
        logger.info(f"✅ Certificate updated: {cert_id}")
        
        return CertificateResponse(**updated_cert)
    
    @staticmethod
    async def delete_certificate(cert_id: str, current_user: UserResponse) -> dict:
        """Delete certificate"""
        cert = await CertificateRepository.find_by_id(cert_id)
        if not cert:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        await CertificateRepository.delete(cert_id)
        
        logger.info(f"✅ Certificate deleted: {cert_id}")
        
        return {"message": "Certificate deleted successfully"}
    
    @staticmethod
    async def bulk_delete_certificates(request: BulkDeleteRequest, current_user: UserResponse) -> dict:
        """Bulk delete certificates"""
        deleted_count = await CertificateRepository.bulk_delete(request.certificate_ids)
        
        logger.info(f"✅ Bulk deleted {deleted_count} certificates")
        
        return {
            "message": f"Successfully deleted {deleted_count} certificates",
            "deleted_count": deleted_count
        }
    
    @staticmethod
    async def check_duplicate(ship_id: str, cert_name: str, cert_no: Optional[str], current_user: UserResponse) -> dict:
        """Check if certificate is duplicate"""
        existing = await CertificateRepository.check_duplicate(ship_id, cert_name, cert_no)
        
        return {
            "is_duplicate": existing is not None,
            "existing_certificate": CertificateResponse(**existing).dict() if existing else None
        }
    
    @staticmethod
    async def analyze_certificate_file(file: UploadFile, ship_id: Optional[str], current_user: UserResponse) -> dict:
        """Analyze certificate file using AI (simplified version)"""
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
        
        logger.info(f"📄 Analyzing certificate file: {file.filename} ({len(file_content)} bytes)")
        
        # TODO: Implement actual AI analysis using EMERGENT_LLM_KEY
        # For now, return mock data
        
        return {
            "success": True,
            "message": "Certificate analyzed successfully (mock data)",
            "analysis": {
                "cert_name": "SAFETY MANAGEMENT CERTIFICATE",
                "cert_type": "Full Term",
                "cert_no": "SMC-2024-001",
                "issue_date": "15/01/2024",
                "valid_date": "15/01/2029",
                "issued_by": "DNV GL",
                "ship_name": "MV Test Ship"
            }
        }