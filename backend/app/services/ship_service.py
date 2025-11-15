import uuid
import logging
from typing import List
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.ship import ShipCreate, ShipUpdate, ShipResponse
from app.models.user import UserResponse, UserRole
from app.repositories.ship_repository import ShipRepository

logger = logging.getLogger(__name__)

class ShipService:
    """Business logic for ship management"""
    
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
