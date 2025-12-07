import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.crew import CrewCreate, CrewUpdate, CrewResponse, BulkDeleteCrewRequest
from app.models.user import UserResponse, UserRole
from app.repositories.crew_repository import CrewRepository
from app.repositories.crew_audit_log_repository import CrewAuditLogRepository
from app.utils.date_helpers import convert_dates_in_dict, CREW_DATE_FIELDS
from app.services.audit_trail_service import AuditTrailService
from app.services.crew_audit_log_service import CrewAuditLogService
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class CrewService:
    """Business logic for crew management"""
    
    # Initialize audit log service
    _audit_log_service = None
    
    @classmethod
    def get_audit_log_service(cls):
        """Get or create audit log service instance"""
        if cls._audit_log_service is None:
            repository = CrewAuditLogRepository(mongo_db.database)
            cls._audit_log_service = CrewAuditLogService(repository)
        return cls._audit_log_service
    
    @staticmethod
    async def get_all_crew(current_user: UserResponse) -> List[CrewResponse]:
        """Get all crew based on user's company"""
        # Filter by company for non-admin users
        if current_user.role in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            crew = await CrewRepository.find_all()
        else:
            crew = await CrewRepository.find_all(company_id=current_user.company)
        
        return [CrewResponse(**member) for member in crew]
    
    @staticmethod
    async def get_crew_by_id(crew_id: str, current_user: UserResponse) -> CrewResponse:
        """Get crew member by ID"""
        crew = await CrewRepository.find_by_id(crew_id)
        
        if not crew:
            raise HTTPException(status_code=404, detail="Crew member not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            if crew.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        return CrewResponse(**crew)
    
    @staticmethod
    async def create_crew(crew_data: CrewCreate, current_user: UserResponse) -> CrewResponse:
        """Create new crew member with comprehensive date handling"""
        # Auto-set company_id from current_user if not provided
        company_id = crew_data.company_id or current_user.company
        if not company_id:
            raise HTTPException(status_code=400, detail="Company ID is required")
        
        # Check if passport exists for this company
        existing = await CrewRepository.find_by_passport(crew_data.passport, company_id)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Crew member with this passport already exists for this company"
            )
        
        # Create crew document
        crew_dict = crew_data.dict()
        crew_dict["id"] = str(uuid.uuid4())
        crew_dict["company_id"] = company_id  # Ensure company_id is set
        crew_dict["created_at"] = datetime.now(timezone.utc)
        crew_dict["created_by"] = current_user.username
        
        # ✅ NEW: Convert all date fields to datetime objects
        crew_dict = convert_dates_in_dict(crew_dict, CREW_DATE_FIELDS)
        
        # Log date conversions for debugging
        for field in CREW_DATE_FIELDS:
            if field in crew_dict and crew_dict[field]:
                logger.info(f"✅ {field}: {crew_dict[field]}")
        
        await CrewRepository.create(crew_dict)
        
        # Log audit trail
        await AuditTrailService.log_action(
            user_id=current_user.id,
            action="CREATE_CREW",
            resource_type="crew_member",
            resource_id=crew_dict["id"],
            details={
                "crew_name": crew_data.full_name,
                "passport": crew_data.passport,
                "ship": crew_data.ship_sign_on,
                "status": crew_data.status
            },
            company_id=current_user.company
        )
        
        # Log crew audit log
        try:
            audit_service = CrewService.get_audit_log_service()
            user_dict = {
                'id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.full_name,
                'company': current_user.company
            }
            await audit_service.log_crew_create(crew_dict, user_dict, notes="Created new crew member")
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
        
        logger.info(f"✅ Crew member created: {crew_dict['full_name']}")
        
        return CrewResponse(**crew_dict)
    
    @staticmethod
    async def update_crew(
        crew_id: str, 
        crew_data: CrewUpdate, 
        current_user: UserResponse,
        expected_last_modified_at: Optional[str] = None
    ) -> CrewResponse:
        """Update crew member with conflict detection"""
        crew = await CrewRepository.find_by_id(crew_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Crew member not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            if crew.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Conflict detection
        if expected_last_modified_at:
            current_updated_at = crew.get('updated_at')
            
            # Parse expected timestamp
            try:
                expected_dt = datetime.fromisoformat(expected_last_modified_at.replace('Z', '+00:00'))
                
                # Check if crew was modified after expected time
                if current_updated_at and current_updated_at > expected_dt:
                    # Conflict detected!
                    logger.warning(f"⚠️ Conflict detected for crew {crew_id}: expected {expected_dt}, current {current_updated_at}")
                    
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error": "conflict",
                            "message": "Crew was modified by another user",
                            "current_ship": crew.get('ship_sign_on'),
                            "current_status": crew.get('status'),
                            "current_updated_at": current_updated_at.isoformat() if current_updated_at else None,
                            "updated_by": crew.get('updated_by'),
                            "your_values": crew_data.dict(exclude_unset=True)
                        }
                    )
            except ValueError as e:
                logger.error(f"❌ Invalid timestamp format: {expected_last_modified_at}, error: {e}")
                # Continue without conflict check if timestamp is invalid
        
        # Prepare update data
        update_data = crew_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = current_user.username
        
        # Check if rank is being updated
        rank_updated = 'rank' in update_data and update_data['rank'] != crew.get('rank')
        new_rank = update_data.get('rank') if rank_updated else None
        
        if update_data:
            await CrewRepository.update(crew_id, update_data)
        
        # If rank was updated, sync to all crew certificates
        if rank_updated and new_rank:
            try:
                from app.db.mongodb import mongo_db
                
                # Access database directly for update_many
                result = await mongo_db.database.crew_certificates.update_many(
                    {"crew_id": crew_id},
                    {"$set": {"rank": new_rank}}
                )
                
                if result.modified_count > 0:
                    logger.info(f"✅ Synced rank '{new_rank}' to {result.modified_count} certificates for crew {crew_id}")
                else:
                    logger.info(f"ℹ️ No certificates to update for crew {crew_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to sync rank to certificates: {e}")
                # Don't fail the whole operation if certificate sync fails
        
        # Get updated crew
        updated_crew = await CrewRepository.find_by_id(crew_id)
        
        # Detect if this is a sign on/off operation
        # Skip general update log if it's a status change between "Sign on" and "Standby"
        # because sign_on_crew() and sign_off_crew() will create specific logs
        old_status = crew.get('status')
        new_status = updated_crew.get('status')
        is_sign_on_off_operation = (
            (old_status == "Standby" and new_status == "Sign on") or
            (old_status == "Sign on" and new_status == "Standby")
        )
        
        # Log crew audit log (skip if it's sign on/off operation)
        if not is_sign_on_off_operation:
            try:
                audit_service = CrewService.get_audit_log_service()
                user_dict = {
                    'id': current_user.id,
                    'username': current_user.username,
                    'full_name': current_user.full_name,
                    'company': current_user.company
                }
                await audit_service.log_crew_update(crew_id, crew, updated_crew, user_dict, notes="Updated crew information")
            except Exception as e:
                logger.error(f"Failed to create audit log: {e}")
        
        logger.info(f"✅ Crew member updated: {crew_id}")
        
        return CrewResponse(**updated_crew)
    
    @staticmethod
    async def delete_crew(crew_id: str, current_user: UserResponse) -> dict:
        """Delete crew member and associated files"""
        crew = await CrewRepository.find_by_id(crew_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Crew member not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            if crew.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if crew has certificates
        from app.db.mongodb import mongo_db
        
        cert_count = await mongo_db.count("crew_certificates", {
            "crew_id": crew_id,
            "company_id": current_user.company
        })
        
        if cert_count > 0:
            crew_name = crew.get('full_name', 'Unknown')
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete crew member '{crew_name}' because they have {cert_count} certificate(s). Please delete all certificates first."
            )
        
        # Delete files from Google Drive
        passport_file_id = crew.get('passport_file_id')
        summary_file_id = crew.get('summary_file_id')
        
        if passport_file_id or summary_file_id:
            try:
                from app.services.google_drive_service import GoogleDriveService
                
                drive_service = GoogleDriveService()
                delete_result = await drive_service.delete_passport_files(
                    company_id=current_user.company,
                    passport_file_id=passport_file_id,
                    summary_file_id=summary_file_id
                )
                
                if delete_result.get('success'):
                    logger.info(f"✅ Google Drive files deleted: {delete_result.get('deleted_count')} files")
                else:
                    logger.warning(f"⚠️ Google Drive deletion failed: {delete_result.get('message')}")
            except Exception as e:
                logger.error(f"❌ Error deleting Google Drive files: {e}")
                # Continue with database deletion even if Drive deletion fails
        
        # Delete from database
        await CrewRepository.delete(crew_id)
        
        # Log audit trail
        await AuditTrailService.log_action(
            user_id=current_user.id,
            action="DELETE_CREW",
            resource_type="crew_member",
            resource_id=crew_id,
            details={
                "crew_name": crew.get('full_name'),
                "passport": crew.get('passport'),
                "ship": crew.get('ship_sign_on')
            },
            company_id=current_user.company
        )
        
        # Log crew audit log
        try:
            audit_service = CrewService.get_audit_log_service()
            user_dict = {
                'id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.full_name,
                'company': current_user.company
            }
            await audit_service.log_crew_delete(crew, user_dict, notes="Deleted crew member")
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
        
        logger.info(f"✅ Crew member deleted from database: {crew_id}")
        
        return {"message": "Crew member deleted successfully"}
    
    @staticmethod
    async def bulk_delete_crew(request: BulkDeleteCrewRequest, current_user: UserResponse) -> dict:
        """Bulk delete crew members and associated files"""
        from app.db.mongodb import mongo_db
        
        deleted_files_count = 0
        failed_deletions = []
        crew_with_certs = []
        
        # First, get all crew members and delete their Google Drive files
        for crew_id in request.crew_ids:
            try:
                crew = await CrewRepository.find_by_id(crew_id)
                if not crew:
                    logger.warning(f"⚠️ Crew member not found: {crew_id}")
                    failed_deletions.append(crew_id)
                    continue
                
                # Check access permission
                if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
                    if crew.get('company_id') != current_user.company:
                        logger.warning(f"⚠️ Access denied for crew: {crew_id}")
                        failed_deletions.append(crew_id)
                        continue
                
                # Check if crew has certificates
                cert_count = await mongo_db.count("crew_certificates", {
                    "crew_id": crew_id,
                    "company_id": current_user.company
                })
                
                if cert_count > 0:
                    crew_name = crew.get('full_name', 'Unknown')
                    logger.warning(f"⚠️ Cannot delete crew {crew_name} ({crew_id}) - has {cert_count} certificate(s)")
                    crew_with_certs.append({
                        "name": crew_name,
                        "cert_count": cert_count
                    })
                    failed_deletions.append(crew_id)
                    continue
                
                # Delete files from Google Drive
                passport_file_id = crew.get('passport_file_id')
                summary_file_id = crew.get('summary_file_id')
                
                if passport_file_id or summary_file_id:
                    try:
                        from app.services.google_drive_service import GoogleDriveService
                        
                        drive_service = GoogleDriveService()
                        delete_result = await drive_service.delete_passport_files(
                            company_id=current_user.company,
                            passport_file_id=passport_file_id,
                            summary_file_id=summary_file_id
                        )
                        
                        if delete_result.get('success'):
                            deleted_files_count += delete_result.get('deleted_count', 0)
                            logger.info(f"✅ Deleted {delete_result.get('deleted_count')} files for crew {crew_id}")
                        else:
                            logger.warning(f"⚠️ File deletion failed for crew {crew_id}: {delete_result.get('message')}")
                    except Exception as e:
                        logger.error(f"❌ Error deleting files for crew {crew_id}: {e}")
                        # Continue with database deletion even if Drive deletion fails
                
                # Log audit trail
                await AuditTrailService.log_action(
                    user_id=current_user.id,
                    action="DELETE_CREW",
                    resource_type="crew_member",
                    resource_id=crew_id,
                    details={
                        "crew_name": crew.get('full_name'),
                        "passport": crew.get('passport'),
                        "ship": crew.get('ship_sign_on'),
                        "bulk_delete": True
                    },
                    company_id=current_user.company
                )
                
            except Exception as e:
                logger.error(f"❌ Error processing crew {crew_id}: {e}")
                failed_deletions.append(crew_id)
        
        # Delete from database (only crew without certificates)
        allowed_crew_ids = [cid for cid in request.crew_ids if cid not in failed_deletions]
        deleted_count = await CrewRepository.bulk_delete(allowed_crew_ids)
        
        logger.info(f"✅ Bulk deleted {deleted_count} crew members and {deleted_files_count} files")
        
        # Build response message
        message = f"Successfully deleted {deleted_count} crew member(s)"
        if deleted_files_count > 0:
            message += f" and {deleted_files_count} file(s)"
        
        # Add warning about crew with certificates
        if crew_with_certs:
            cert_details = ", ".join([f"{c['name']} ({c['cert_count']} cert(s))" for c in crew_with_certs])
            message += f". Skipped {len(crew_with_certs)} crew member(s) with certificates: {cert_details}"
        
        return {
            "message": message,
            "deleted_count": deleted_count,
            "deleted_files_count": deleted_files_count,
            "failed_deletions": failed_deletions,
            "crew_with_certificates": crew_with_certs
        }
