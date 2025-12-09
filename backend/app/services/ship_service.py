import uuid
import logging
from typing import List
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.ship import ShipCreate, ShipUpdate, ShipResponse, AnniversaryDate
from app.models.user import UserResponse, UserRole
from app.repositories.ship_repository import ShipRepository
from app.utils.ship_calculations import (
    calculate_anniversary_date_from_certificates,
    calculate_special_survey_cycle_from_certificates,
    calculate_next_docking,
    format_anniversary_date_display
)

logger = logging.getLogger(__name__)

class ShipService:
    """Business logic for ship management"""
    
    @staticmethod
    def get_audit_log_service():
        """Get audit log service instance"""
        from app.db.mongodb import mongo_db
        from app.services.crew_audit_log_service import CrewAuditLogService
        from app.repositories.crew_audit_log_repository import CrewAuditLogRepository
        return CrewAuditLogService(CrewAuditLogRepository(mongo_db.database))
    
    @staticmethod
    async def get_all_ships(current_user: UserResponse) -> List[ShipResponse]:
        """Get all ships based on user's company"""
        # Filter by company for non-admin users
        if current_user.role in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            ships = await ShipRepository.find_all()
        else:
            ships = await ShipRepository.find_all(company=current_user.company)
        
        return [ShipResponse(**ship) for ship in ships]
    
    @staticmethod
    async def get_ship_by_id(ship_id: str, current_user: UserResponse) -> ShipResponse:
        """Get ship by ID"""
        ship = await ShipRepository.find_by_id(ship_id)
        
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            if ship.get('company') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        return ShipResponse(**ship)
    
    @staticmethod
    async def create_ship(ship_data: ShipCreate, current_user: UserResponse) -> ShipResponse:
        """Create new ship"""
        # Check if IMO exists for this company
        if ship_data.imo:
            existing = await ShipRepository.find_by_imo(ship_data.imo, ship_data.company)
            if existing:
                raise HTTPException(
                    status_code=400, 
                    detail="Ship with this IMO number already exists for this company"
                )
        
        # Create ship document
        ship_dict = ship_data.dict()
        ship_dict["id"] = str(uuid.uuid4())
        ship_dict["created_at"] = datetime.now(timezone.utc)
        
        # Set default GDrive folder status
        if "gdrive_folder_status" not in ship_dict:
            ship_dict["gdrive_folder_status"] = "pending"
        
        await ShipRepository.create(ship_dict)
        
        # Log audit
        try:
            audit_service = ShipService.get_audit_log_service()
            user_dict = {
                'id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.full_name,
                'company': current_user.company
            }
            await audit_service.log_ship_create(
                ship_data=ship_dict,
                user=user_dict
            )
            logger.info(f"✅ Ship audit log created")
        except Exception as e:
            logger.error(f"Failed to create ship audit log: {e}")
        
        logger.info(f"✅ Ship created: {ship_dict['name']}")
        
        return ShipResponse(**ship_dict)
    
    @staticmethod
    async def update_ship(ship_id: str, ship_data: ShipUpdate, current_user: UserResponse) -> ShipResponse:
        """Update ship"""
        # Check if ship exists
        existing_ship = await ShipRepository.find_by_id(ship_id)
        if not existing_ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            if existing_ship.get('company') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare update data
        update_data = ship_data.dict(exclude_unset=True)
        
        if update_data:
            await ShipRepository.update(ship_id, update_data)
        
        # Get updated ship
        updated_ship = await ShipRepository.find_by_id(ship_id)
        
        logger.info(f"✅ Ship updated: {ship_id}")
        
        return ShipResponse(**updated_ship)
    
    @staticmethod
    async def delete_ship(ship_id: str, current_user: UserResponse) -> dict:
        """Delete ship"""
        ship = await ShipRepository.find_by_id(ship_id)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            if ship.get('company') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # TODO: Check if ship has associated certificates before deletion
        
        await ShipRepository.delete(ship_id)
        
        logger.info(f"✅ Ship deleted: {ship_id}")
        
        return {"message": "Ship deleted successfully"}
    
    @staticmethod
    async def calculate_anniversary_date(ship_id: str, current_user: UserResponse) -> dict:
        """Calculate anniversary date from certificates"""
        # Check if ship exists
        ship = await ShipRepository.find_by_id(ship_id)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Calculate anniversary date
        calculated_anniversary = await calculate_anniversary_date_from_certificates(ship_id)
        
        if not calculated_anniversary:
            return {
                "success": False,
                "message": "No Full Term certificates with valid dates found",
                "anniversary_date": None
            }
        
        # Update ship
        update_data = {"anniversary_date": calculated_anniversary.dict()}
        await ShipRepository.update(ship_id, update_data)
        
        logger.info(f"✅ Anniversary date calculated for ship {ship_id}")
        
        return {
            "success": True,
            "message": f"Anniversary date calculated from {calculated_anniversary.source_certificate_type}",
            "anniversary_date": {
                "day": calculated_anniversary.day,
                "month": calculated_anniversary.month,
                "source": calculated_anniversary.source_certificate_type,
                "display": format_anniversary_date_display(calculated_anniversary)
            }
        }
    
    @staticmethod
    async def calculate_special_survey_cycle(ship_id: str, current_user: UserResponse) -> dict:
        """Calculate special survey cycle from certificates"""
        # Check if ship exists
        ship = await ShipRepository.find_by_id(ship_id)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Calculate cycle
        calculated_cycle = await calculate_special_survey_cycle_from_certificates(ship_id)
        
        if not calculated_cycle:
            return {
                "success": False,
                "message": "No Full Term Class certificates found",
                "special_survey_cycle": None
            }
        
        # Update ship
        update_data = {"special_survey_cycle": calculated_cycle.dict()}
        await ShipRepository.update(ship_id, update_data)
        
        from_str = calculated_cycle.from_date.strftime('%d/%m/%Y')
        to_str = calculated_cycle.to_date.strftime('%d/%m/%Y')
        
        logger.info(f"✅ Special Survey cycle calculated for ship {ship_id}")
        
        return {
            "success": True,
            "message": f"Special Survey cycle calculated from {calculated_cycle.cycle_type}",
            "special_survey_cycle": {
                "from_date": from_str,
                "to_date": to_str,
                "cycle_type": calculated_cycle.cycle_type,
                "intermediate_required": calculated_cycle.intermediate_required,
                "display": f"{from_str} - {to_str}"
            }
        }
    
    @staticmethod
    async def calculate_next_docking_date(ship_id: str, current_user: UserResponse) -> dict:
        """Calculate next docking date"""
        # Check if ship exists
        ship = await ShipRepository.find_by_id(ship_id)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        last_docking = ship.get('last_docking')
        if not last_docking:
            return {
                "success": False,
                "message": "No last docking date available",
                "next_docking": None
            }
        
        # Calculate next docking
        next_docking = await calculate_next_docking(ship_id, last_docking)
        
        if not next_docking:
            return {
                "success": False,
                "message": "Failed to calculate next docking",
                "next_docking": None
            }
        
        # Update ship
        update_data = {"next_docking": next_docking}
        await ShipRepository.update(ship_id, update_data)
        
        logger.info(f"✅ Next docking calculated for ship {ship_id}")
        
        return {
            "success": True,
            "message": "Next docking date calculated",
            "next_docking": next_docking.strftime('%d/%m/%Y'),
            "last_docking": last_docking.strftime('%d/%m/%Y') if isinstance(last_docking, datetime) else last_docking
        }
