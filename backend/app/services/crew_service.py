import uuid
import logging
from typing import List
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.crew import CrewCreate, CrewUpdate, CrewResponse, BulkDeleteCrewRequest
from app.models.user import UserResponse, UserRole
from app.repositories.crew_repository import CrewRepository
from app.utils.date_helpers import convert_dates_in_dict, CREW_DATE_FIELDS

logger = logging.getLogger(__name__)

class CrewService:
    """Business logic for crew management"""
    
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
        # Check if passport exists for this company
        existing = await CrewRepository.find_by_passport(crew_data.passport, crew_data.company_id)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Crew member with this passport already exists for this company"
            )
        
        # Create crew document
        crew_dict = crew_data.dict()
        crew_dict["id"] = str(uuid.uuid4())
        crew_dict["created_at"] = datetime.now(timezone.utc)
        crew_dict["created_by"] = current_user.username
        
        # ✅ NEW: Convert all date fields to datetime objects
        crew_dict = convert_dates_in_dict(crew_dict, CREW_DATE_FIELDS)
        
        # Log date conversions for debugging
        for field in CREW_DATE_FIELDS:
            if field in crew_dict and crew_dict[field]:
                logger.info(f"✅ {field}: {crew_dict[field]}")
        
        await CrewRepository.create(crew_dict)
        
        logger.info(f"✅ Crew member created: {crew_dict['full_name']}")
        
        return CrewResponse(**crew_dict)
    
    @staticmethod
    async def update_crew(crew_id: str, crew_data: CrewUpdate, current_user: UserResponse) -> CrewResponse:
        """Update crew member"""
        crew = await CrewRepository.find_by_id(crew_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Crew member not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            if crew.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare update data
        update_data = crew_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = current_user.username
        
        if update_data:
            await CrewRepository.update(crew_id, update_data)
        
        # Get updated crew
        updated_crew = await CrewRepository.find_by_id(crew_id)
        
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
        
        logger.info(f"✅ Crew member deleted from database: {crew_id}")
        
        return {"message": "Crew member deleted successfully"}
    
    @staticmethod
    async def bulk_delete_crew(request: BulkDeleteCrewRequest, current_user: UserResponse) -> dict:
        """Bulk delete crew members"""
        deleted_count = await CrewRepository.bulk_delete(request.crew_ids)
        
        logger.info(f"✅ Bulk deleted {deleted_count} crew members")
        
        return {
            "message": f"Successfully deleted {deleted_count} crew members",
            "deleted_count": deleted_count
        }
