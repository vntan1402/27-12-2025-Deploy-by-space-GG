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
        from app.utils.company_name_abbreviation import abbreviate_company_name
        
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
                cert["cert_abbreviation"] = await generate_certificate_abbreviation(
                    cert.get("cert_name"), 
                    cert.get("doc_type")
                )
            
            # Generate organization abbreviation for issued_by if not present
            if not cert.get("issued_by_abbreviation") and cert.get("issued_by"):
                cert["issued_by_abbreviation"] = generate_organization_abbreviation(cert.get("issued_by"))
            
            # Generate company name abbreviation for display
            if cert.get("company_name"):
                cert["company_name_display"] = abbreviate_company_name(cert.get("company_name"))
            
            result.append(CompanyCertResponse(**cert))
        
        return result
    
    @staticmethod
    async def get_company_cert_by_id(cert_id: str, current_user: UserResponse) -> CompanyCertResponse:
        """Get company certificate by ID"""
        from app.utils.certificate_abbreviation import generate_certificate_abbreviation
        from app.utils.issued_by_abbreviation import generate_organization_abbreviation
        from app.utils.company_name_abbreviation import abbreviate_company_name
        
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
        
        # Generate certificate abbreviation if not present
        if not cert.get("cert_abbreviation") and cert.get("cert_name"):
            cert["cert_abbreviation"] = await generate_certificate_abbreviation(
                cert.get("cert_name"),
                cert.get("doc_type")
            )
        
        # Generate organization abbreviation for issued_by if not present
        if not cert.get("issued_by_abbreviation") and cert.get("issued_by"):
            cert["issued_by_abbreviation"] = generate_organization_abbreviation(cert.get("issued_by"))
        
        # Generate company name abbreviation for display
        if cert.get("company_name"):
            cert["company_name_display"] = abbreviate_company_name(cert.get("company_name"))
        
        return CompanyCertResponse(**cert)
    
    @staticmethod
    async def create_company_cert(cert_data: CompanyCertCreate, current_user: UserResponse) -> CompanyCertResponse:
        """Create new company certificate"""
        from app.utils.certificate_abbreviation import generate_certificate_abbreviation
        from app.utils.issued_by_abbreviation import generate_organization_abbreviation
        from app.utils.doc_next_survey_calculator import calculate_next_survey
        
        cert_dict = cert_data.model_dump()
        cert_dict["id"] = str(uuid.uuid4())
        cert_dict["created_at"] = datetime.now(timezone.utc)
        cert_dict["created_by"] = current_user.id
        
        # Ensure company is set
        if not cert_dict.get("company"):
            cert_dict["company"] = current_user.company
        
        # Generate certificate abbreviation
        if cert_dict.get("cert_name"):
            cert_dict["cert_abbreviation"] = await generate_certificate_abbreviation(
                cert_dict["cert_name"],
                cert_dict.get("doc_type")
            )
            logger.info(f"📝 Generated abbreviation: {cert_dict['cert_name']} (doc_type: {cert_dict.get('doc_type')}) → {cert_dict['cert_abbreviation']}")
        
        # Generate organization abbreviation for issued_by
        if cert_dict.get("issued_by"):
            cert_dict["issued_by_abbreviation"] = generate_organization_abbreviation(cert_dict["issued_by"])
        
        # Auto-calculate next_audit if not provided
        if not cert_dict.get("next_audit") and cert_dict.get("doc_type"):
            # Convert string dates to datetime if needed
            valid_date = cert_dict.get("valid_date")
            issue_date = cert_dict.get("issue_date")
            last_endorse = cert_dict.get("last_endorse")
            
            if isinstance(valid_date, str):
                try:
                    valid_date = datetime.strptime(valid_date, "%Y-%m-%d")
                except:
                    valid_date = None
            
            if isinstance(issue_date, str):
                try:
                    issue_date = datetime.strptime(issue_date, "%Y-%m-%d")
                except:
                    issue_date = None
            
            if isinstance(last_endorse, str):
                try:
                    last_endorse = datetime.strptime(last_endorse, "%Y-%m-%d")
                except:
                    last_endorse = None
            
            next_survey = calculate_next_survey(
                cert_dict.get("doc_type"),
                valid_date,
                issue_date,
                last_endorse
            )
            
            if next_survey:
                cert_dict["next_audit"] = next_survey
                logger.info(f"📅 Auto-calculated next_audit: {next_survey.date()}")
        
        await mongo_db.insert_one(CompanyCertService.collection_name, cert_dict)
        
        logger.info(f"✅ Created company certificate: {cert_dict['id']}")
        return CompanyCertResponse(**cert_dict)
    
    @staticmethod
    async def update_company_cert(cert_id: str, cert_data: CompanyCertUpdate, current_user: UserResponse) -> CompanyCertResponse:
        """Update company certificate"""
        from app.utils.certificate_abbreviation import generate_certificate_abbreviation
        from app.utils.issued_by_abbreviation import generate_organization_abbreviation
        
        existing_cert = await mongo_db.find_one(CompanyCertService.collection_name, {"id": cert_id})
        
        if not existing_cert:
            raise HTTPException(status_code=404, detail="Company Certificate not found")
        
        update_data = cert_data.model_dump(exclude_unset=True)
        
        # If cert_name or doc_type is updated, regenerate abbreviation
        if "cert_name" in update_data or "doc_type" in update_data:
            cert_name = update_data.get("cert_name") or existing_cert.get("cert_name")
            doc_type = update_data.get("doc_type") if "doc_type" in update_data else existing_cert.get("doc_type")
            update_data["cert_abbreviation"] = await generate_certificate_abbreviation(cert_name, doc_type)
            logger.info(f"📝 Regenerated abbreviation: {cert_name} (doc_type: {doc_type}) → {update_data['cert_abbreviation']}")
        
        # If issued_by is updated, regenerate organization abbreviation
        if "issued_by" in update_data and update_data["issued_by"]:
            update_data["issued_by_abbreviation"] = generate_organization_abbreviation(update_data["issued_by"])
        
        if update_data:
            await mongo_db.update_one(
                CompanyCertService.collection_name,
                {"id": cert_id},
                update_data
            )
            logger.info(f"✅ Updated company certificate: {cert_id}")
        
        updated_cert = await mongo_db.find_one(CompanyCertService.collection_name, {"id": cert_id})
        
        # Map google_drive_file_id to file_id
        if updated_cert.get("google_drive_file_id") and not updated_cert.get("file_id"):
            updated_cert["file_id"] = updated_cert.get("google_drive_file_id")
        
        return CompanyCertResponse(**updated_cert)
    
    @staticmethod
    async def delete_company_cert(cert_id: str, current_user: UserResponse, background_tasks) -> dict:
        """Delete company certificate and schedule Google Drive file deletion"""
        from app.services.gdrive_service import GDriveService
        
        cert = await mongo_db.find_one(CompanyCertService.collection_name, {"id": cert_id})
        
        if not cert:
            raise HTTPException(status_code=404, detail="Company Certificate not found")
        
        # Extract file info before deleting
        file_id = cert.get("file_id") or cert.get("google_drive_file_id")
        summary_file_id = cert.get("summary_file_id")
        cert_name = cert.get("cert_name", "Unknown")
        company_id = cert.get("company")
        
        # Delete from database immediately
        await mongo_db.delete_one(CompanyCertService.collection_name, {"id": cert_id})
        logger.info(f"✅ Company Certificate deleted from DB: {cert_id} ({cert_name})")
        
        # Schedule Google Drive file deletion in background
        files_to_delete = []
        if file_id:
            files_to_delete.append((file_id, "main file"))
        if summary_file_id:
            files_to_delete.append((summary_file_id, "summary file"))
        
        deletion_msg = "Company Certificate deleted successfully"
        if files_to_delete and background_tasks:
            for drive_file_id, file_desc in files_to_delete:
                background_tasks.add_task(
                    delete_file_background,
                    file_id=drive_file_id,
                    company_id=company_id,
                    document_type="company_certificate",
                    document_name=f"{cert_name} ({file_desc})",
                    gdrive_service_class=GDriveService
                )
                logger.info(f"📋 Scheduled background deletion for: {drive_file_id} ({file_desc})")
            
            deletion_msg = f"Company Certificate deleted successfully. {len(files_to_delete)} file(s) deletion in progress..."
            return {
                "message": deletion_msg,
                "id": cert_id,
                "background_deletion": True,
                "files_scheduled": len(files_to_delete)
            }
        
        return {
            "message": deletion_msg,
            "id": cert_id,
            "background_deletion": False
        }
    
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
    
    @staticmethod
    async def recalculate_all_next_surveys(current_user: UserResponse) -> dict:
        """
        Recalculate next_audit for all certificates in user's company
        This updates all certificates with the latest business rules
        """
        from app.utils.doc_next_survey_calculator import calculate_next_survey
        
        logger.info(f"🔄 Starting recalculation of all next audits for company: {current_user.company}")
        
        # Get all certificates for this company
        filters = {"company": current_user.company}
        certs = await mongo_db.find_all(CompanyCertService.collection_name, filters)
        
        updated_count = 0
        skipped_count = 0
        failed_ids = []
        
        for cert in certs:
            try:
                # Get required fields
                doc_type = cert.get("doc_type")
                valid_date = cert.get("valid_date")
                issue_date = cert.get("issue_date")
                last_endorse = cert.get("last_endorse")
                
                # Skip if no doc_type
                if not doc_type:
                    logger.info(f"⏭️ Skipping cert {cert.get('id')} ({cert.get('cert_name')}): No doc_type")
                    skipped_count += 1
                    continue
                
                # Convert string dates to datetime if needed
                if isinstance(valid_date, str):
                    try:
                        valid_date = datetime.strptime(valid_date, "%Y-%m-%d")
                    except:
                        valid_date = None
                
                if isinstance(issue_date, str):
                    try:
                        issue_date = datetime.strptime(issue_date, "%Y-%m-%d")
                    except:
                        issue_date = None
                
                if isinstance(last_endorse, str):
                    try:
                        last_endorse = datetime.strptime(last_endorse, "%Y-%m-%d")
                    except:
                        last_endorse = None
                
                # Calculate next audit
                next_survey = calculate_next_survey(
                    doc_type,
                    valid_date,
                    issue_date,
                    last_endorse
                )
                
                # Update certificate
                update_data = {}
                
                # Convert datetime to string for storage
                if next_survey:
                    update_data["next_audit"] = next_survey.strftime("%Y-%m-%d")
                else:
                    # Set to None if no audit required (e.g., Short Term DOC)
                    update_data["next_audit"] = None
                
                if update_data:
                    await mongo_db.update_one(
                        CompanyCertService.collection_name,
                        {"id": cert.get("id")},
                        update_data
                    )
                    updated_count += 1
                    logger.info(f"✅ Updated cert {cert.get('id')} ({cert.get('cert_name')}): next_audit = {update_data.get('next_audit')}")
                
            except Exception as e:
                logger.error(f"❌ Failed to recalculate cert {cert.get('id')}: {e}")
                failed_ids.append(cert.get("id"))
        
        logger.info(f"✅ Recalculation complete: Updated={updated_count}, Skipped={skipped_count}, Failed={len(failed_ids)}")
        
        return {
            "message": f"Recalculation complete: {updated_count} updated, {skipped_count} skipped",
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids,
            "total_processed": len(certs)
        }
