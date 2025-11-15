import logging
import asyncio
from typing import List, Set
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.models.ship import ShipCreate, ShipUpdate, ShipResponse
from app.models.user import UserResponse, UserRole
from app.services.ship_service import ShipService
from app.core.security import get_current_user
from app.utils.gdrive_folder_helper import create_google_drive_folder_background
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)
router = APIRouter()

# Track background tasks to prevent garbage collection
background_tasks: Set[asyncio.Task] = set()

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[ShipResponse])
async def get_ships(current_user: UserResponse = Depends(get_current_user)):
    """
    Get all ships (filtered by company for non-admin users)
    """
    try:
        return await ShipService.get_all_ships(current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching ships: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ships")

@router.get("/{ship_id}", response_model=ShipResponse)
async def get_ship_by_id(
    ship_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get a specific ship by ID
    """
    try:
        return await ShipService.get_ship_by_id(ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching ship {ship_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ship")

@router.post("", response_model=ShipResponse)
async def create_ship(
    ship_data: ShipCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Create new ship with automatic Google Drive folder creation (Editor+ role required)
    """
    try:
        # Create ship in database
        ship_response = await ShipService.create_ship(ship_data, current_user)
        ship_dict = ship_response.dict()
        
        # Start Google Drive folder creation in background
        logger.info(f"🚀 Scheduling Google Drive folder creation for ship: {ship_dict['name']}")
        
        task = asyncio.create_task(
            create_google_drive_folder_background(
                ship_dict,
                current_user,
                mongo_db
            )
        )
        
        # Add to tracking set to prevent garbage collection
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
        
        logger.info(f"✅ Ship created: {ship_dict['name']} (Google Drive folder creation in progress)")
        
        return ship_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating ship: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ship")

@router.put("/{ship_id}", response_model=ShipResponse)
async def update_ship(
    ship_id: str,
    ship_data: ShipUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Update ship (Editor+ role required)
    """
    try:
        return await ShipService.update_ship(ship_id, ship_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating ship: {e}")
        raise HTTPException(status_code=500, detail="Failed to update ship")

@router.delete("/{ship_id}")
async def delete_ship(
    ship_id: str,
    delete_google_drive_folder: bool = False,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Delete ship with optional Google Drive folder deletion (Editor+ role required)
    
    Args:
        ship_id: Ship ID to delete
        delete_google_drive_folder: If True, also delete Google Drive folder structure (default: False)
        current_user: Current authenticated user
    """
    try:
        import aiohttp
        
        # Get ship info before deletion
        from app.repositories.ship_repository import ShipRepository
        ship = await ShipRepository.find_by_id(ship_id)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        ship_name = ship.get('name', 'Unknown Ship')
        company_id = ship.get('company')
        
        logger.info(f"🗑️ Deleting ship: {ship_name} (ID: {ship_id}, delete_gdrive: {delete_google_drive_folder})")
        
        # Delete ship from database
        result = await ShipService.delete_ship(ship_id, current_user)
        
        # Prepare response
        response = {
            "message": f"Ship '{ship_name}' deleted successfully",
            "ship_id": ship_id,
            "ship_name": ship_name,
            "database_deletion": "success",
            "google_drive_deletion_requested": delete_google_drive_folder
        }
        
        # Delete Google Drive folder if requested
        if delete_google_drive_folder and company_id:
            try:
                logger.info(f"📁 Attempting to delete Google Drive folder for ship: {ship_name}")
                
                # Get company Google Drive config
                gdrive_config = await mongo_db.find_one("company_gdrive_config", {"company_id": company_id})
                
                if not gdrive_config:
                    logger.warning(f"⚠️ No Google Drive configuration found for company {company_id}")
                    response["google_drive_deletion"] = {
                        "success": False,
                        "message": "Google Drive integration not configured for this company"
                    }
                else:
                    # Get Apps Script URL
                    web_app_url = gdrive_config.get("web_app_url") or gdrive_config.get("apps_script_url")
                    folder_id = gdrive_config.get("folder_id") or gdrive_config.get("main_folder_id")
                    
                    if not web_app_url or not folder_id:
                        response["google_drive_deletion"] = {
                            "success": False,
                            "message": "Incomplete Google Drive configuration"
                        }
                    else:
                        # Call Apps Script to delete folder
                        payload = {
                            "action": "delete_complete_ship_structure",
                            "parent_folder_id": folder_id,
                            "ship_name": ship_name,
                            "permanent_delete": False  # Move to trash by default for safety
                        }
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.post(
                                web_app_url,
                                json=payload,
                                timeout=aiohttp.ClientTimeout(total=60)
                            ) as gdrive_response:
                                if gdrive_response.status == 200:
                                    gdrive_result = await gdrive_response.json()
                                    response["google_drive_deletion"] = gdrive_result
                                    
                                    if gdrive_result.get("success"):
                                        logger.info(f"✅ Google Drive folder deleted successfully for ship: {ship_name}")
                                    else:
                                        logger.warning(f"⚠️ Google Drive deletion reported failure: {gdrive_result.get('message')}")
                                else:
                                    response["google_drive_deletion"] = {
                                        "success": False,
                                        "message": f"Apps Script request failed with status {gdrive_response.status}"
                                    }
                        
            except Exception as gdrive_error:
                logger.error(f"❌ Error during Google Drive folder deletion: {str(gdrive_error)}")
                response["google_drive_deletion"] = {
                    "success": False,
                    "message": f"Google Drive deletion failed: {str(gdrive_error)}"
                }
        elif delete_google_drive_folder and not company_id:
            response["google_drive_deletion"] = {
                "success": False,
                "message": "Could not resolve company ID for Google Drive deletion"
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting ship: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete ship")


@router.post("/{ship_id}/update-next-survey")
async def update_ship_next_survey(
    ship_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Update Next Survey and Next Survey Type for all certificates of a ship
    based on IMO regulations and 5-year survey cycle
    Migrated from backend-v1
    """
    from app.services.survey_calculation_service import SurveyCalculationService
    from app.db.mongodb import mongo_db
    
    try:
        # Get ship data
        ship_data = await mongo_db.database.ships.find_one({"id": ship_id})
        if not ship_data:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Get all certificates for the ship
        certificates = await mongo_db.database.certificates.find({"ship_id": ship_id}).to_list(length=1000)
        if not certificates:
            return {
                "success": True,
                "message": "No certificates found for this ship",
                "updated_count": 0,
                "results": []
            }
        
        updated_count = 0
        results = []
        
        for cert in certificates:
            # Skip certificates that are excluded from auto-update
            if cert.get('exclude_from_auto_update', False):
                logger.info(f"⏭️ Skipping certificate {cert.get('id')} - excluded from auto-update")
                continue
            
            # Calculate next survey info
            survey_info = SurveyCalculationService.calculate_next_survey_info(cert, ship_data)
            
            # Prepare update data
            update_data = {}
            
            if survey_info['next_survey']:
                # Store next_survey as ISO datetime for compatibility
                if survey_info.get('raw_date'):
                    try:
                        # Parse dd/MM/yyyy format and convert to ISO datetime
                        from datetime import datetime
                        parsed_date = datetime.strptime(survey_info['raw_date'], '%d/%m/%Y')
                        update_data['next_survey'] = parsed_date.isoformat() + 'Z'  # Add Z for UTC (backend-v1 format)
                    except:
                        update_data['next_survey'] = None
                else:
                    update_data['next_survey'] = None
                    
                update_data['next_survey_display'] = survey_info['next_survey']  # Store display format with window
            else:
                update_data['next_survey'] = None
                update_data['next_survey_display'] = None
                
            if survey_info['next_survey_type']:
                update_data['next_survey_type'] = survey_info['next_survey_type']
            else:
                update_data['next_survey_type'] = None
            
            # Update certificate if there are changes
            current_next_survey = cert.get('next_survey')
            current_next_survey_type = cert.get('next_survey_type')
            
            if (update_data.get('next_survey') != current_next_survey or 
                update_data.get('next_survey_type') != current_next_survey_type):
                
                await mongo_db.database.certificates.update_one(
                    {"id": cert['id']},
                    {"$set": update_data}
                )
                updated_count += 1
                
                results.append({
                    'cert_id': cert['id'],
                    'cert_name': cert.get('cert_name', 'Unknown'),
                    'cert_type': cert.get('cert_type', 'Unknown'),
                    'old_next_survey': current_next_survey,
                    'new_next_survey': update_data.get('next_survey_display'),
                    'old_next_survey_type': current_next_survey_type,
                    'new_next_survey_type': update_data.get('next_survey_type'),
                    'reasoning': survey_info['reasoning']
                })
        
        logger.info(f"✅ Updated next survey info for {updated_count} certificates in ship {ship_id}")
        
        return {
            "success": True,
            "message": f"Updated next survey information for {updated_count} certificates",
            "ship_id": ship_id,
            "ship_name": ship_data.get('name', 'Unknown'),
            "updated_count": updated_count,
            "total_certificates": len(certificates),
            "results": results[:10]  # Show first 10 results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating next survey: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update next survey: {str(e)}")

@router.post("/{ship_id}/audit-certificates/update-next-survey")
async def update_ship_audit_certificates_next_survey(
    ship_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Calculate and update Next Survey for all audit certificates of a ship
    Migrated from backend-v1
    """
    from app.services.survey_calculation_service import SurveyCalculationService
    from app.db.mongodb import mongo_db
    from datetime import datetime, timezone
    
    try:
        # Get ship data
        ship_data = await mongo_db.database.ships.find_one({"id": ship_id})
        if not ship_data:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Get all audit certificates for the ship
        certificates = await mongo_db.database.audit_certificates.find({"ship_id": ship_id}).to_list(length=1000)
        if not certificates:
            return {
                "success": True,
                "message": "No audit certificates found for this ship",
                "updated_count": 0,
                "results": []
            }
        
        updated_count = 0
        results = []
        
        for cert in certificates:
            # Calculate next survey
            survey_info = SurveyCalculationService.calculate_audit_certificate_next_survey(cert)
            
            # Prepare update data
            update_data = {}
            
            if survey_info['next_survey']:
                if survey_info.get('raw_date'):
                    try:
                        parsed_date = datetime.strptime(survey_info['raw_date'], '%d/%m/%Y')
                        update_data['next_survey'] = parsed_date.isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to parse date {survey_info['raw_date']}: {e}")
                        update_data['next_survey'] = None
                else:
                    update_data['next_survey'] = None
                    
                update_data['next_survey_display'] = survey_info['next_survey']
            else:
                update_data['next_survey'] = None
                update_data['next_survey_display'] = None
                
            if survey_info['next_survey_type']:
                update_data['next_survey_type'] = survey_info['next_survey_type']
            else:
                update_data['next_survey_type'] = None
            
            # Update certificate if there are changes
            if update_data:
                update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
                await mongo_db.database.audit_certificates.update_one(
                    {"id": cert["id"]},
                    {"$set": update_data}
                )
                updated_count += 1
            
            results.append({
                "cert_id": cert["id"],
                "cert_name": cert.get("cert_name", "Unknown"),
                "cert_type": cert.get("cert_type", "Unknown"),
                "next_survey": survey_info['next_survey'],
                "next_survey_type": survey_info['next_survey_type'],
                "updated": bool(update_data)
            })
        
        logger.info(f"✅ Updated next survey for {updated_count} audit certificates")
        
        return {
            "success": True,
            "message": f"Updated next survey for {updated_count} audit certificates",
            "updated_count": updated_count,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating audit certificates next survey: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update audit certificates: {str(e)}")

        raise
    except Exception as e:
        logger.error(f"❌ Error updating next survey: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update next survey: {str(e)}")

@router.post("/{ship_id}/calculate-anniversary-date")
async def calculate_anniversary_date(
    ship_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Calculate anniversary date from Full Term certificates (Editor+ role required)
    """
    try:
        return await ShipService.calculate_anniversary_date(ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error calculating anniversary date: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate anniversary date")

@router.post("/{ship_id}/calculate-special-survey-cycle")
async def calculate_special_survey_cycle(
    ship_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Calculate special survey cycle from Full Term Class certificates (Editor+ role required)
    """
    try:
        return await ShipService.calculate_special_survey_cycle(ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error calculating special survey cycle: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate special survey cycle")

@router.post("/{ship_id}/calculate-next-docking")
async def calculate_next_docking(
    ship_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Calculate next docking date from last docking (Editor+ role required)
    """
    try:
        return await ShipService.calculate_next_docking_date(ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error calculating next docking: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate next docking")

@router.post("/{ship_id}/logo")
async def upload_ship_logo(
    ship_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload ship logo (Editor+ role required)
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed")
        
        # Validate file size (5MB limit)
        if file.size and file.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 5MB")
        
        # Verify ship exists
        ship = await ShipService.get_ship_by_id(ship_id, current_user)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Create uploads directory
        import os
        from pathlib import Path
        
        upload_dir = Path(f"/app/uploads/ships/{ship_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine file extension
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        file_path = upload_dir / f"logo.{ext}"
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Update ship with logo path
        logo_url = f"/uploads/ships/{ship_id}/logo.{ext}"
        await ShipService.update_ship(
            ship_id,
            {"logo": logo_url},
            current_user
        )
        
        logger.info(f"✅ Ship logo uploaded: {ship_id}")
        
        return {
            "message": "Logo uploaded successfully",
            "logo_url": logo_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading ship logo: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload logo")

@router.get("/{ship_id}/logo")
async def get_ship_logo(
    ship_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get ship logo URL
    """
    try:
        ship = await ShipService.get_ship_by_id(ship_id, current_user)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        logo_url = ship.logo if hasattr(ship, 'logo') else None
        
        if not logo_url:
            raise HTTPException(status_code=404, detail="Ship has no logo")
        
        return {
            "logo_url": logo_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting ship logo: {e}")
        raise HTTPException(status_code=500, detail="Failed to get logo")
