"""
Crew Assignment Service
Handles crew sign on, sign off, and ship transfers with file movement and audit trail
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException
import asyncio

from app.repositories.crew_repository import CrewRepository
from app.repositories.crew_assignment_repository import CrewAssignmentRepository
from app.services.crew_file_movement_service import CrewFileMovementService
from app.models.user import UserResponse
from app.utils.date_helpers import parse_date_flexible

logger = logging.getLogger(__name__)


def run_async_file_movement(coro):
    """
    Run async file movement in background without blocking the response
    """
    try:
        asyncio.create_task(coro)
    except Exception as e:
        logger.error(f"❌ Error creating background task: {e}")


class CrewAssignmentService:
    """Service for managing crew assignments (sign on, sign off, transfers)"""
    
    @staticmethod
    async def sign_off_crew(
        crew_id: str,
        sign_off_date: str,
        notes: Optional[str],
        current_user: UserResponse,
        skip_validation: bool = False,
        place_sign_off: Optional[str] = None,
        from_ship: Optional[str] = None
    ) -> Dict:
        """
        Sign off crew member and move files to Standby
        
        Steps:
        1. Validate crew is "Sign on" with a ship
        2. Move files from ship folder to Standby folder
        3. Update crew status to "Standby"
        4. Update ship_sign_on to "-"
        5. Update date_sign_off
        6. Create audit trail
        
        Args:
            crew_id: Crew member UUID
            sign_off_date: Sign off date (ISO or DD/MM/YYYY)
            notes: Optional notes
            current_user: Current user
            
        Returns:
            {
                "success": boolean,
                "message": string,
                "crew_id": string,
                "files_moved": {...},
                "assignment_id": string
            }
        """
        logger.info(f"🛑 SIGN OFF: Processing crew {crew_id}")
        
        try:
            # Step 1: Get and validate crew
            crew = await CrewRepository.find_by_id(crew_id)
            if not crew:
                raise HTTPException(status_code=404, detail="Crew member not found")
            
            # Check access permission
            if current_user.role not in ["SYSTEM_ADMIN", "SUPER_ADMIN", "ADMIN"]:
                if crew.get('company_id') != current_user.company:
                    raise HTTPException(status_code=403, detail="Access denied")
            
            crew_name = crew.get('full_name', 'Unknown')
            current_status = crew.get('status', '')
            current_ship = crew.get('ship_sign_on', '')
            
            # Use from_ship if provided (original ship before DB update), otherwise use current
            ship_to_search = from_ship if from_ship else current_ship
            
            logger.info(f"   Crew: {crew_name}")
            logger.info(f"   Current Status: {current_status}")
            logger.info(f"   Current Ship (from DB): {current_ship}")
            logger.info(f"   Original Ship (from request): {from_ship}")
            logger.info(f"   Ship to search in history: {ship_to_search}")
            logger.info(f"   Skip Validation: {skip_validation}")
            
            # Validate crew is on a ship (unless skip_validation=True)
            if not skip_validation and current_status != "Sign on":
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot sign off crew with status '{current_status}'. Crew must be 'Sign on'."
                )
            
            if not skip_validation and (not current_ship or current_ship in ["-", ""]):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot sign off crew without ship assignment"
                )
            
            # Step 2: Move files to Standby (use ship_to_search for file movement)
            logger.info(f"📦 Moving files from {ship_to_search} to Standby...")
            
            move_result = await CrewFileMovementService.move_crew_files_to_standby(
                company_id=current_user.company,
                crew_id=crew_id,
                crew_name=crew_name,
                from_ship_name=ship_to_search
            )
            
            if not move_result.get('success'):
                logger.warning(f"⚠️ File movement failed: {move_result.get('message')}")
                # Continue anyway - don't fail the whole operation
            
            files_moved = move_result.get('files_moved', {
                "passport_moved": False,
                "certificates_moved": 0,
                "summaries_moved": 0
            })
            
            # Step 3: Update crew in database
            logger.info(f"💾 Updating crew database...")
            
            # Parse date
            parsed_date = parse_date_flexible(sign_off_date)
            
            update_data = {
                'status': 'Standby',
                'ship_sign_on': '-',
                'date_sign_off': parsed_date,
                'place_sign_off': place_sign_off,
                'updated_at': datetime.now(timezone.utc),
                'updated_by': current_user.username
            }
            
            await CrewRepository.update(crew_id, update_data)
            logger.info(f"✅ Crew status updated to Standby")
            
            # Step 4: Update existing assignment record (not create new)
            logger.info(f"📝 Updating assignment history with sign off info...")
            
            # Find the most recent SIGN_ON record for this crew on the specified ship
            from app.db.mongodb import mongo_db
            
            existing_record = await mongo_db.database.crew_assignment_history.find_one(
                {
                    'crew_id': crew_id,
                    'to_ship': ship_to_search,  # Use ship_to_search (from request or DB)
                    'action_type': 'SIGN_ON',
                    'sign_off_date': None  # Not yet signed off
                },
                sort=[('action_date', -1)]  # Get most recent
            )
            
            logger.info(f"   Searching for open SIGN_ON record:")
            logger.info(f"     - crew_id: {crew_id}")
            logger.info(f"     - to_ship: {ship_to_search}")
            if existing_record:
                logger.info(f"   ✅ Found record: {existing_record['id']} for ship: {existing_record.get('to_ship')}")
            else:
                logger.warning(f"   ⚠️ No open SIGN_ON record found for ship: {ship_to_search}")
            
            assignment_id = None
            
            if existing_record:
                # Update existing record with sign off info
                logger.info(f"   Found existing SIGN_ON record: {existing_record['id']}")
                
                await mongo_db.database.crew_assignment_history.update_one(
                    {'_id': existing_record['_id']},
                    {
                        '$set': {
                            'sign_off_date': parsed_date,
                            'sign_off_place': place_sign_off,
                            'sign_off_by': current_user.username,
                            'sign_off_notes': notes or f"Sign off from {ship_to_search}",
                            'files_moved_on_sign_off': files_moved,
                            'updated_at': datetime.now(timezone.utc)
                        }
                    }
                )
                
                assignment_id = existing_record['id']
                logger.info(f"✅ Assignment record updated with sign off info: {assignment_id}")
                
            else:
                # Fallback: Create new record if no existing SIGN_ON found
                # This handles edge cases where history was cleared or corrupted
                logger.warning(f"⚠️ No existing SIGN_ON record found, creating new SIGN_OFF record")
                
                assignment_data = {
                    'id': str(uuid4()),
                    'crew_id': crew_id,
                    'company_id': current_user.company,
                    'action_type': 'SIGN_OFF',
                    'from_ship': current_ship,
                    'to_ship': None,
                    'from_status': current_status,
                    'to_status': 'Standby',
                    'action_date': parsed_date,
                    'sign_off_date': parsed_date,
                    'sign_off_place': place_sign_off,
                    'sign_off_by': current_user.username,
                    'sign_off_notes': notes or f"Sign off from {current_ship}",
                    'performed_by': current_user.username,
                    'notes': notes or f"Sign off from {current_ship}",
                    'files_moved': files_moved,
                    'created_at': datetime.now(timezone.utc)
                }
                
                await CrewAssignmentRepository.create(assignment_data)
                assignment_id = assignment_data['id']
                logger.info(f"✅ New SIGN_OFF record created: {assignment_id}")
            
            # Step 5: Return result
            total_files = (
                (1 if files_moved.get('passport_moved') else 0) +
                files_moved.get('certificates_moved', 0) +
                files_moved.get('summaries_moved', 0)
            )
            
            return {
                "success": True,
                "message": f"Crew {crew_name} signed off successfully. {total_files} files moved to Standby.",
                "crew_id": crew_id,
                "crew_name": crew_name,
                "from_ship": current_ship,
                "sign_off_date": sign_off_date,
                "files_moved": files_moved,
                "assignment_id": assignment_data['id']
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Sign off failed: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sign off crew: {str(e)}"
            )
    
    @staticmethod
    async def sign_on_crew(
        crew_id: str,
        ship_name: str,
        sign_on_date: str,
        place_sign_on: Optional[str],
        notes: Optional[str],
        current_user: UserResponse,
        skip_validation: bool = False
    ) -> Dict:
        """
        Sign on crew member to a ship and move files from Standby
        
        Steps:
        1. Validate crew is "Standby"
        2. Move files from Standby folder to ship folder
        3. Update crew status to "Sign on"
        4. Update ship_sign_on
        5. Update date_sign_on and place_sign_on
        6. Create audit trail
        
        Args:
            crew_id: Crew member UUID
            ship_name: Ship name to sign on to
            sign_on_date: Sign on date (ISO or DD/MM/YYYY)
            place_sign_on: Place of sign on (optional)
            notes: Optional notes
            current_user: Current user
            
        Returns:
            Same structure as sign_off_crew
        """
        logger.info(f"✅ SIGN ON: Processing crew {crew_id}")
        
        try:
            # Step 1: Get and validate crew
            crew = await CrewRepository.find_by_id(crew_id)
            if not crew:
                raise HTTPException(status_code=404, detail="Crew member not found")
            
            # Check access permission
            if current_user.role not in ["SYSTEM_ADMIN", "SUPER_ADMIN", "ADMIN"]:
                if crew.get('company_id') != current_user.company:
                    raise HTTPException(status_code=403, detail="Access denied")
            
            crew_name = crew.get('full_name', 'Unknown')
            current_status = crew.get('status', '')
            current_ship = crew.get('ship_sign_on', '')
            
            logger.info(f"   Crew: {crew_name}")
            logger.info(f"   Current Status: {current_status}")
            logger.info(f"   Target Ship: {ship_name}")
            logger.info(f"   Skip Validation: {skip_validation}")
            
            # Validate crew is on standby (unless skip_validation=True)
            if not skip_validation and current_status != "Standby":
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot sign on crew with status '{current_status}'. Crew must be 'Standby'."
                )
            
            # Validate ship name
            if not ship_name or ship_name.strip() in ["-", ""]:
                raise HTTPException(
                    status_code=400,
                    detail="Ship name is required for sign on"
                )
            
            # Step 2: Move files from Standby to Ship
            logger.info(f"📦 Moving files from Standby to {ship_name}...")
            
            move_result = await CrewFileMovementService.move_crew_files_from_standby_to_ship(
                company_id=current_user.company,
                crew_id=crew_id,
                crew_name=crew_name,
                to_ship_name=ship_name
            )
            
            if not move_result.get('success'):
                logger.warning(f"⚠️ File movement failed: {move_result.get('message')}")
                # Continue anyway
            
            files_moved = move_result.get('files_moved', {
                "passport_moved": False,
                "certificates_moved": 0,
                "summaries_moved": 0
            })
            
            # Step 3: Update crew in database
            logger.info(f"💾 Updating crew database...")
            
            # Parse date
            parsed_date = parse_date_flexible(sign_on_date)
            
            update_data = {
                'status': 'Sign on',
                'ship_sign_on': ship_name,
                'date_sign_on': parsed_date,
                'date_sign_off': None,  # Clear sign off date
                'place_sign_off': None,  # Clear sign off place
                'updated_at': datetime.now(timezone.utc),
                'updated_by': current_user.username
            }
            
            if place_sign_on:
                update_data['place_sign_on'] = place_sign_on
            
            await CrewRepository.update(crew_id, update_data)
            logger.info(f"✅ Crew status updated to Sign on")
            
            # Step 4: Create audit trail (sign on record)
            logger.info(f"📝 Creating assignment history record...")
            
            assignment_data = {
                'id': str(uuid4()),
                'crew_id': crew_id,
                'company_id': current_user.company,
                'action_type': 'SIGN_ON',
                'from_ship': None,
                'to_ship': ship_name,
                'from_status': current_status,
                'to_status': 'Sign on',
                'action_date': parsed_date,
                'sign_on_date': parsed_date,
                'sign_on_place': place_sign_on,
                'sign_on_by': current_user.username,
                'sign_on_notes': notes or f"Sign on to {ship_name}",
                'sign_off_date': None,  # Will be filled when sign off
                'sign_off_place': None,
                'sign_off_by': None,
                'sign_off_notes': None,
                'performed_by': current_user.username,
                'notes': notes or f"Sign on to {ship_name}",
                'files_moved': files_moved,
                'files_moved_on_sign_off': None,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
            
            await CrewAssignmentRepository.create(assignment_data)
            logger.info(f"✅ Audit trail created: {assignment_data['id']}")
            
            # Step 5: Return result
            total_files = (
                (1 if files_moved.get('passport_moved') else 0) +
                files_moved.get('certificates_moved', 0) +
                files_moved.get('summaries_moved', 0)
            )
            
            return {
                "success": True,
                "message": f"Crew {crew_name} signed on to {ship_name} successfully. {total_files} files moved.",
                "crew_id": crew_id,
                "crew_name": crew_name,
                "to_ship": ship_name,
                "sign_on_date": sign_on_date,
                "place_sign_on": place_sign_on,
                "files_moved": files_moved,
                "assignment_id": assignment_data['id']
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Sign on failed: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sign on crew: {str(e)}"
            )
    
    @staticmethod
    async def transfer_crew_between_ships(
        crew_id: str,
        to_ship_name: str,
        transfer_date: str,
        notes: Optional[str],
        current_user: UserResponse,
        skip_validation: bool = False
    ) -> Dict:
        """
        Transfer crew from one ship to another (without going through Standby)
        
        Steps:
        1. Validate crew is "Sign on" with a ship
        2. Move files from current ship to new ship
        3. Update ship_sign_on
        4. Update date_sign_on (optional)
        5. Create audit trail
        
        Args:
            crew_id: Crew member UUID
            to_ship_name: Destination ship name
            transfer_date: Transfer date (ISO or DD/MM/YYYY)
            notes: Optional notes
            current_user: Current user
            
        Returns:
            Same structure as other methods
        """
        logger.info(f"🔄 TRANSFER: Processing crew {crew_id}")
        
        try:
            # Step 1: Get and validate crew
            crew = await CrewRepository.find_by_id(crew_id)
            if not crew:
                raise HTTPException(status_code=404, detail="Crew member not found")
            
            # Check access permission
            if current_user.role not in ["SYSTEM_ADMIN", "SUPER_ADMIN", "ADMIN"]:
                if crew.get('company_id') != current_user.company:
                    raise HTTPException(status_code=403, detail="Access denied")
            
            crew_name = crew.get('full_name', 'Unknown')
            current_status = crew.get('status', '')
            from_ship = crew.get('ship_sign_on', '')
            
            logger.info(f"   Crew: {crew_name}")
            logger.info(f"   Current Status: {current_status}")
            logger.info(f"   From Ship: {from_ship}")
            logger.info(f"   To Ship: {to_ship_name}")
            logger.info(f"   Skip Validation: {skip_validation}")
            
            # Validate crew is on a ship (unless skip_validation=True)
            if not skip_validation and current_status != "Sign on":
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot transfer crew with status '{current_status}'. Crew must be 'Sign on'."
                )
            
            if not skip_validation and (not from_ship or from_ship in ["-", ""]):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot transfer crew without current ship assignment"
                )
            
            # Validate destination ship
            if not to_ship_name or to_ship_name.strip() in ["-", ""]:
                raise HTTPException(
                    status_code=400,
                    detail="Destination ship name is required"
                )
            
            # Check if same ship
            if from_ship.lower() == to_ship_name.lower():
                raise HTTPException(
                    status_code=400,
                    detail=f"Crew is already on {from_ship}"
                )
            
            # Step 2: Move files between ships
            logger.info(f"📦 Moving files from {from_ship} to {to_ship_name}...")
            
            move_result = await CrewFileMovementService.move_crew_files_between_ships(
                company_id=current_user.company,
                crew_id=crew_id,
                crew_name=crew_name,
                from_ship_name=from_ship,
                to_ship_name=to_ship_name
            )
            
            if not move_result.get('success'):
                logger.warning(f"⚠️ File movement failed: {move_result.get('message')}")
                # Continue anyway
            
            files_moved = move_result.get('files_moved', {
                "passport_moved": False,
                "certificates_moved": 0,
                "summaries_moved": 0
            })
            
            # Step 3: Update crew in database
            logger.info(f"💾 Updating crew database...")
            
            # Parse date
            parsed_date = parse_date_flexible(transfer_date)
            
            update_data = {
                'ship_sign_on': to_ship_name,
                'date_sign_on': parsed_date,  # Update sign on date to transfer date
                'updated_at': datetime.now(timezone.utc),
                'updated_by': current_user.username
            }
            
            await CrewRepository.update(crew_id, update_data)
            logger.info(f"✅ Crew ship updated to {to_ship_name}")
            
            # Step 4: Create audit trail
            logger.info(f"📝 Creating audit trail...")
            
            assignment_data = {
                'id': str(uuid4()),
                'crew_id': crew_id,
                'company_id': current_user.company,
                'action_type': 'SHIP_TRANSFER',
                'from_ship': from_ship,
                'to_ship': to_ship_name,
                'from_status': current_status,
                'to_status': current_status,  # Status remains "Sign on"
                'action_date': parsed_date,
                'performed_by': current_user.username,
                'notes': notes or f"Transfer from {from_ship} to {to_ship_name}",
                'files_moved': files_moved,
                'created_at': datetime.now(timezone.utc)
            }
            
            await CrewAssignmentRepository.create(assignment_data)
            logger.info(f"✅ Audit trail created: {assignment_data['id']}")
            
            # Step 5: Return result
            total_files = (
                (1 if files_moved.get('passport_moved') else 0) +
                files_moved.get('certificates_moved', 0) +
                files_moved.get('summaries_moved', 0)
            )
            
            return {
                "success": True,
                "message": f"Crew {crew_name} transferred from {from_ship} to {to_ship_name} successfully. {total_files} files moved.",
                "crew_id": crew_id,
                "crew_name": crew_name,
                "from_ship": from_ship,
                "to_ship": to_ship_name,
                "transfer_date": transfer_date,
                "files_moved": files_moved,
                "assignment_id": assignment_data['id']
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Transfer failed: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to transfer crew: {str(e)}"
            )
