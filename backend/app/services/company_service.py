import uuid
import os
import time
import logging
from typing import List
from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile

from app.models.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.models.user import UserResponse
from app.repositories.company_repository import CompanyRepository

logger = logging.getLogger(__name__)

class CompanyService:
    """Business logic for company management"""
    
    @staticmethod
    def get_audit_log_service():
        """Get audit log service instance"""
        from app.db.mongodb import mongo_db
        from app.services.crew_audit_log_service import CrewAuditLogService
        from app.repositories.crew_audit_log_repository import CrewAuditLogRepository
        return CrewAuditLogService(CrewAuditLogRepository(mongo_db.database))
    
    @staticmethod
    async def get_all_companies(current_user: UserResponse) -> List[CompanyResponse]:
        """Get all companies"""
        companies = await CompanyRepository.find_all()
        
        # Fix companies that don't have 'name' field but have 'name_en' or 'name_vn'
        fixed_companies = []
        for company in companies:
            if 'name' not in company:
                company['name'] = company.get('name_en') or company.get('name_vn') or 'Unknown Company'
            fixed_companies.append(company)
        
        return [CompanyResponse(**company) for company in fixed_companies]
    
    @staticmethod
    async def get_company_by_id(company_id: str, current_user: UserResponse) -> CompanyResponse:
        """Get company by ID with real-time ship and crew counts"""
        company = await CompanyRepository.find_by_id(company_id)
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Fix company that doesn't have 'name' field
        if 'name' not in company:
            company['name'] = company.get('name_en') or company.get('name_vn') or 'Unknown Company'
        
        # ⭐ Calculate real-time counts
        from app.db.mongodb import mongo_db
        db = mongo_db.database
        
        # Ships collection uses "company" field (not "company_id")
        total_ships = await db.ships.count_documents({"company": company_id})
        
        # Crew collection uses "company_id" field
        total_crew = await db.crew.count_documents({"company_id": company_id})
        
        # Add counts to response
        company['total_ships'] = total_ships
        company['total_crew'] = total_crew
        
        logger.info(f"✅ Company {company.get('name')}: {total_ships} ships, {total_crew} crew")
        
        return CompanyResponse(**company)
    
    @staticmethod
    async def create_company(company_data: CompanyCreate, current_user: UserResponse) -> CompanyResponse:
        """Create new company"""
        # Check if tax_id exists
        existing = await CompanyRepository.find_by_tax_id(company_data.tax_id)
        if existing:
            raise HTTPException(status_code=400, detail="Company with this tax ID already exists")
        
        # Create company document
        company_dict = company_data.dict()
        company_dict["id"] = str(uuid.uuid4())
        company_dict["created_at"] = datetime.now(timezone.utc)
        
        # Ensure legacy 'name' field for backward compatibility
        if not company_dict.get('name'):
            company_dict['name'] = company_dict.get('name_en') or company_dict.get('name_vn') or 'Unknown Company'
        
        await CompanyRepository.create(company_dict)
        
        # Log audit
        try:
            audit_service = CompanyService.get_audit_log_service()
            user_dict = {
                'id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.full_name,
                'company': current_user.company
            }
            await audit_service.log_company_create(
                company_data=company_dict,
                user=user_dict
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
        
        logger.info(f"✅ Company created: {company_dict['name']}")
        
        return CompanyResponse(**company_dict)
    
    @staticmethod
    async def update_company(company_id: str, company_data: CompanyUpdate, current_user: UserResponse) -> CompanyResponse:
        """Update company"""
        # Check if company exists
        existing_company = await CompanyRepository.find_by_id(company_id)
        if not existing_company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Prepare update data
        update_data = company_data.dict(exclude_unset=True)
        
        # Handle software_expiry field - convert string to datetime if needed
        if 'software_expiry' in update_data and update_data['software_expiry']:
            if isinstance(update_data['software_expiry'], str):
                try:
                    update_data['software_expiry'] = datetime.fromisoformat(
                        update_data['software_expiry'].replace('Z', '+00:00')
                    )
                except ValueError:
                    # If parsing fails, remove the field
                    del update_data['software_expiry']
        
        # Update legacy 'name' field for backward compatibility
        if 'name_en' in update_data or 'name_vn' in update_data:
            name_en = update_data.get('name_en') or existing_company.get('name_en')
            name_vn = update_data.get('name_vn') or existing_company.get('name_vn')
            update_data['name'] = name_en or name_vn or 'Unknown Company'
        
        if update_data:
            await CompanyRepository.update(company_id, update_data)
        
        # Get updated company
        updated_company = await CompanyRepository.find_by_id(company_id)
        
        # Fix company name field
        if 'name' not in updated_company:
            updated_company['name'] = updated_company.get('name_en') or updated_company.get('name_vn') or 'Unknown Company'
        
        # Log audit
        try:
            audit_service = CompanyService.get_audit_log_service()
            user_dict = {
                'id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.full_name,
                'company': current_user.company
            }
            await audit_service.log_company_update(
                old_company=existing_company,
                new_company=updated_company,
                user=user_dict
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
        
        logger.info(f"✅ Company updated: {company_id}")
        
        return CompanyResponse(**updated_company)
    
    @staticmethod
    async def delete_company(company_id: str, current_user: UserResponse) -> dict:
        """Delete company"""
        company = await CompanyRepository.find_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # TODO: Check if company has associated ships/users before deletion
        
        await CompanyRepository.delete(company_id)
        
        logger.info(f"✅ Company deleted: {company_id}")
        
        return {"message": "Company deleted successfully"}
    
    @staticmethod
    async def upload_logo(company_id: str, file: UploadFile, current_user: UserResponse) -> dict:
        """Upload company logo"""
        # Check if company exists
        company = await CompanyRepository.find_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create uploads directory (shared with backend-v1)
        upload_dir = "/app/uploads/company_logos"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        filename = f"{company_id}_{int(time.time())}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Update company with logo URL
        logo_url = f"/uploads/company_logos/{filename}"
        await CompanyRepository.update(company_id, {"logo_url": logo_url})
        
        logger.info(f"✅ Company logo uploaded: {logo_url}")
        
        return {
            "logo_url": logo_url,
            "message": "Company logo uploaded successfully"
        }
