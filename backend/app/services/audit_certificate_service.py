import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, BackgroundTasks

from app.models.audit_certificate import AuditCertificateCreate, AuditCertificateUpdate, AuditCertificateResponse, BulkDeleteAuditCertificateRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db
from app.utils.certificate_abbreviation import generate_certificate_abbreviation
from app.utils.issued_by_abbreviation import generate_organization_abbreviation
from app.utils.background_tasks import delete_file_background

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
            
            # Generate organization abbreviation for issued_by if not present
            if not cert.get("issued_by_abbreviation") and cert.get("issued_by"):
                cert["issued_by_abbreviation"] = generate_organization_abbreviation(cert.get("issued_by"))
            
            # ⭐ Map google_drive_file_id to file_id for frontend compatibility
            if cert.get("google_drive_file_id") and not cert.get("file_id"):
                cert["file_id"] = cert.get("google_drive_file_id")
            
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
        
        # Generate organization abbreviation for issued_by if not present
        if not cert.get("issued_by_abbreviation") and cert.get("issued_by"):
            cert["issued_by_abbreviation"] = generate_organization_abbreviation(cert.get("issued_by"))
        
        # ⭐ Map google_drive_file_id to file_id for frontend compatibility
        if cert.get("google_drive_file_id") and not cert.get("file_id"):
            cert["file_id"] = cert.get("google_drive_file_id")
        
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
        
        # Generate organization abbreviation for issued_by
        if cert_dict.get("issued_by"):
            cert_dict["issued_by_abbreviation"] = generate_organization_abbreviation(cert_dict.get("issued_by"))
            logger.info(f"✅ Generated issued_by abbreviation: '{cert_dict['issued_by']}' → '{cert_dict['issued_by_abbreviation']}'")
        
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
        
        # Regenerate certificate abbreviation if cert_name is being updated
        if update_data.get("cert_name") and not update_data.get("cert_abbreviation"):
            update_data["cert_abbreviation"] = await generate_certificate_abbreviation(update_data.get("cert_name"))
            logger.info(f"✅ Regenerated cert abbreviation: '{update_data['cert_name']}' → '{update_data['cert_abbreviation']}'")
        
        # Regenerate organization abbreviation if issued_by is being updated
        if update_data.get("issued_by"):
            update_data["issued_by_abbreviation"] = generate_organization_abbreviation(update_data.get("issued_by"))
            logger.info(f"✅ Regenerated issued_by abbreviation: '{update_data['issued_by']}' → '{update_data['issued_by_abbreviation']}'")
        
        if update_data:
            await mongo_db.update(AuditCertificateService.collection_name, {"id": cert_id}, update_data)
        
        updated_cert = await mongo_db.find_one(AuditCertificateService.collection_name, {"id": cert_id})
        
        if not updated_cert.get("cert_name") and updated_cert.get("doc_name"):
            updated_cert["cert_name"] = updated_cert.get("doc_name")
        
        # Generate certificate abbreviation if not present
        if not updated_cert.get("cert_abbreviation") and updated_cert.get("cert_name"):
            updated_cert["cert_abbreviation"] = await generate_certificate_abbreviation(updated_cert.get("cert_name"))
        
        # Generate organization abbreviation if not present
        if not updated_cert.get("issued_by_abbreviation") and updated_cert.get("issued_by"):
            updated_cert["issued_by_abbreviation"] = generate_organization_abbreviation(updated_cert.get("issued_by"))
        
        logger.info(f"✅ Audit Certificate updated: {cert_id}")
        
        return AuditCertificateResponse(**updated_cert)
    
    @staticmethod
    async def delete_audit_certificate(
        cert_id: str, 
        current_user: UserResponse,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> dict:
        """Delete audit certificate and schedule Google Drive file deletion"""
        cert = await mongo_db.find_one(AuditCertificateService.collection_name, {"id": cert_id})
        if not cert:
            raise HTTPException(status_code=404, detail="Audit Certificate not found")
        
        # Extract file info before deleting
        google_drive_file_id = cert.get("google_drive_file_id")
        cert_name = cert.get("cert_name", "Unknown")
        
        # Delete from database immediately
        await mongo_db.delete(AuditCertificateService.collection_name, {"id": cert_id})
        logger.info(f"✅ Audit Certificate deleted from DB: {cert_id} ({cert_name})")
        
        # Schedule Google Drive file deletion in background
        if google_drive_file_id and background_tasks:
            ship_id = cert.get("ship_id")
            if ship_id:
                from app.repositories.ship_repository import ShipRepository
                ship = await ShipRepository.find_by_id(ship_id)
                if ship:
                    company_id = ship.get("company")
                    if company_id:
                        from app.services.gdrive_service import GDriveService
                        background_tasks.add_task(
                            delete_file_background,
                            google_drive_file_id,
                            company_id,
                            "audit_certificate",
                            cert_name,
                            GDriveService
                        )
                        logger.info(f"📋 Scheduled background deletion for audit certificate file: {google_drive_file_id}")
                        
                        return {
                            "success": True,
                            "message": "Audit Certificate deleted successfully. File deletion in progress...",
                            "background_deletion": True
                        }
        
        return {
            "success": True,
            "message": "Audit Certificate deleted successfully",
            "background_deletion": False
        }
    
    @staticmethod
    async def bulk_delete_audit_certificates(
        request: BulkDeleteAuditCertificateRequest, 
        current_user: UserResponse,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> dict:
        """Bulk delete audit certificates and schedule file deletions"""
        deleted_count = 0
        files_scheduled = 0
        
        for cert_id in request.document_ids:
            try:
                result = await AuditCertificateService.delete_audit_certificate(
                    cert_id, 
                    current_user, 
                    background_tasks
                )
                deleted_count += 1
                if result.get("background_deletion"):
                    files_scheduled += 1
            except Exception as e:
                logger.error(f"Error deleting audit certificate {cert_id}: {e}")
                continue
        
        message = f"Deleted {deleted_count} audit certificate(s)"
        if files_scheduled > 0:
            message += f". {files_scheduled} file(s) deletion in progress..."
        
        logger.info(f"✅ Bulk delete complete: {deleted_count} audit certificates, {files_scheduled} files scheduled")
        
        return {
            "success": True,
            "message": message,
            "deleted_count": deleted_count,
            "files_scheduled": files_scheduled
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

    
    @staticmethod
    def calculate_audit_certificate_next_survey(certificate_data: dict) -> dict:
        """
        Calculate Next Survey and Next Survey Type for Audit Certificates (ISM/ISPS/MLC)
        
        Logic:
        1. Interim: Next Survey = Valid Date - 3M, Type = "Initial"
        2. Short Term: Next Survey = N/A, Type = N/A
        3. Full Term:
           - Priority 1 (check Last Endorse):
             * If no Last Endorse: Next Survey = Valid Date - 30 months ±6M, Type = "Intermediate"
             * If has Last Endorse: Next Survey = Valid Date - 3M, Type = "Renewal"
        4. Special documents (DMLC I, DMLC II, SSP): Next Survey = N/A, Type = N/A
        
        Args:
            certificate_data: Certificate information (cert_name, cert_type, valid_date, last_endorse)
        
        Returns:
            dict with next_survey, next_survey_type, and reasoning
        """
        try:
            from dateutil.relativedelta import relativedelta
            from app.utils.date_parser import parse_date_string
            
            # Extract certificate information
            cert_name = certificate_data.get('cert_name', '').upper()
            cert_type = certificate_data.get('cert_type', '').upper()
            valid_date = certificate_data.get('valid_date')
            last_endorse = certificate_data.get('last_endorse')
            current_date = datetime.now(timezone.utc)
            
            # Parse valid_date
            valid_dt = None
            if valid_date:
                if isinstance(valid_date, str):
                    valid_dt = parse_date_string(valid_date)
                else:
                    valid_dt = valid_date
            
            # Rule: No valid date = no Next Survey
            if not valid_dt:
                return {
                    'next_survey': None,
                    'next_survey_type': None,
                    'reasoning': 'No valid date available'
                }
            
            # Rule 4: Special documents (DMLC I, DMLC II, SSP) = N/A
            special_docs = ['DMLC I', 'DMLC II', 'DMLC PART I', 'DMLC PART II', 'SSP', 'SHIP SECURITY PLAN']
            if any(doc in cert_name for doc in special_docs):
                return {
                    'next_survey': None,
                    'next_survey_type': None,
                    'reasoning': f'{cert_name} does not require Next Survey calculation'
                }
            
            # Rule 2: Short Term = N/A
            if 'SHORT' in cert_type or 'SHORT TERM' in cert_type:
                return {
                    'next_survey': None,
                    'next_survey_type': None,
                    'reasoning': 'Short Term certificates do not require Next Survey'
                }
            
            # Rule 1: Interim = Valid Date - 3M, Type = "Initial"
            if 'INTERIM' in cert_type:
                next_survey_date = valid_dt - relativedelta(months=3)
                return {
                    'next_survey': valid_dt.strftime('%d/%m/%Y') + ' (-3M)',
                    'next_survey_type': 'Initial',
                    'reasoning': 'Interim certificate: Next Survey = Valid Date - 3 months',
                    'raw_date': next_survey_date.strftime('%d/%m/%Y'),
                    'window_months': 3
                }
            
            # Rule 3: Full Term certificates
            if 'FULL' in cert_type or 'FULL TERM' in cert_type or cert_type == 'FULL TERM':
                # Parse last_endorse if exists
                last_endorse_dt = None
                if last_endorse:
                    if isinstance(last_endorse, str):
                        last_endorse_dt = parse_date_string(last_endorse)
                    else:
                        last_endorse_dt = last_endorse
                
                # Priority 1: Check Last Endorse
                if last_endorse_dt:
                    # Has Last Endorse → Renewal
                    next_survey_date = valid_dt - relativedelta(months=3)
                    return {
                        'next_survey': valid_dt.strftime('%d/%m/%Y') + ' (-3M)',
                        'next_survey_type': 'Renewal',
                        'reasoning': 'Full Term with Last Endorse: Next Survey = Valid Date - 3 months (Renewal)',
                        'raw_date': next_survey_date.strftime('%d/%m/%Y'),
                        'window_months': 3
                    }
                else:
                    # No Last Endorse → Intermediate
                    intermediate_date = valid_dt - relativedelta(months=30)
                    return {
                        'next_survey': intermediate_date.strftime('%d/%m/%Y') + ' (±6M)',
                        'next_survey_type': 'Intermediate',
                        'reasoning': 'Full Term without Last Endorse: Next Survey = Valid Date - 30 months (Intermediate)',
                        'raw_date': intermediate_date.strftime('%d/%m/%Y'),
                        'window_months': 6
                    }
            
            # Default: Cannot determine
            return {
                'next_survey': None,
                'next_survey_type': None,
                'reasoning': f'Cannot determine Next Survey for cert_type: {cert_type}'
            }
            
        except Exception as e:
            logger.error(f"Error calculating audit certificate next survey: {e}")
            return {
                'next_survey': None,
                'next_survey_type': None,
                'reasoning': f'Error in calculation: {str(e)}'
            }
    
    @staticmethod
    async def update_ship_audit_certificates_next_survey(ship_id: str, current_user: UserResponse) -> dict:
        """
        Calculate and update Next Survey for all audit certificates of a ship
        
        Args:
            ship_id: Ship ID
            current_user: Current user making the request
            
        Returns:
            dict with success status, message, and results
        """
        try:
            # Get ship data
            ship_data = await mongo_db.find_one("ships", {"id": ship_id})
            if not ship_data:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            # Get all audit certificates for the ship
            certificates = await mongo_db.find_all(AuditCertificateService.collection_name, {"ship_id": ship_id})
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
                survey_info = AuditCertificateService.calculate_audit_certificate_next_survey(cert)
                
                # Prepare update data
                update_data = {}
                
                if survey_info['next_survey']:
                    if survey_info.get('raw_date'):
                        try:
                            from app.utils.date_parser import parse_date_string
                            parsed_date = datetime.strptime(survey_info['raw_date'], '%d/%m/%Y')
                            update_data['next_survey'] = parsed_date.isoformat() + 'Z'
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
                    update_data['updated_at'] = datetime.now(timezone.utc)
                    await mongo_db.update(AuditCertificateService.collection_name, {"id": cert["id"]}, update_data)
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
            logger.error(f"Error updating audit certificates next survey: {e}")
            raise HTTPException(status_code=500, detail=str(e))


    
    @staticmethod
    async def get_upcoming_audit_surveys(current_user: UserResponse, days: int = 30) -> dict:
        """
        Get upcoming audit surveys based on window logic
        
        Window Rules:
        - (±6M): Next Survey Date ± 6 months (Intermediate without Last Endorse)
        - (±3M): Next Survey Date ± 3 months (other Intermediate cases)
        - (-3M): Next Survey Date - 3 months → Next Survey Date (Initial, Renewal)
        
        Args:
            current_user: Current user making the request
            days: Number of days to look ahead (not used with new window logic)
            
        Returns:
            dict with upcoming_surveys list and metadata
        """
        try:
            import re
            from datetime import timedelta
            from dateutil.relativedelta import relativedelta
            
            # Get current date
            current_date = datetime.now(timezone.utc).date()
            user_company = current_user.company
            
            logger.info(f"Checking upcoming audit surveys for company: {user_company}")
            
            # Get company record
            company_record = await mongo_db.find_one("companies", {"id": user_company})
            company_name = None
            if company_record:
                company_name = company_record.get('name_en') or company_record.get('name_vn')
            
            # Get all ships for this company
            ships_by_id = await mongo_db.find_all("ships", {"company": user_company})
            ships_by_name = []
            if company_name:
                ships_by_name = await mongo_db.find_all("ships", {"company": company_name})
            
            # Combine and deduplicate ships
            all_ships_dict = {}
            for ship in ships_by_id + ships_by_name:
                ship_id = ship.get('id')
                if ship_id and ship_id not in all_ships_dict:
                    all_ships_dict[ship_id] = ship
            
            ships = list(all_ships_dict.values())
            ship_ids = [ship.get('id') for ship in ships if ship.get('id')]
            
            logger.info(f"Found {len(ships)} ships for company")
            
            if not ship_ids:
                return {
                    "upcoming_surveys": [],
                    "total_count": 0,
                    "company": user_company,
                    "company_name": company_name,
                    "check_date": current_date.isoformat()
                }
            
            # Get all audit certificates for these ships
            all_certificates = []
            for ship_id in ship_ids:
                certs = await mongo_db.find_all(AuditCertificateService.collection_name, {"ship_id": ship_id})
                all_certificates.extend(certs)
            
            logger.info(f"Found {len(all_certificates)} audit certificates to check")
            
            upcoming_surveys = []
            
            for cert in all_certificates:
                try:
                    # Get Next Survey Display field (contains date with annotation like "30/10/2025 (±3M)")
                    next_survey_display = cert.get('next_survey_display') or cert.get('next_survey')
                    
                    if not next_survey_display:
                        continue
                    
                    # Parse Next Survey to extract date and window annotation
                    next_survey_str = str(next_survey_display)
                    
                    # Extract date part (before annotation)
                    # Format examples: "30/10/2025 (±6M)", "30/11/2025 (-3M)", "31/10/2027 (±3M)"
                    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', next_survey_str)
                    if not date_match:
                        continue
                    
                    date_str = date_match.group(1)
                    next_survey_date = datetime.strptime(date_str, '%d/%m/%Y').date()
                    
                    # Determine window based on annotation
                    window_open = None
                    window_close = None
                    window_type = ''
                    has_explicit_annotation = False
                    
                    if '(±6M)' in next_survey_str:
                        # Window: Next Survey ± 6M (Intermediate without Last Endorse)
                        window_open = next_survey_date - relativedelta(months=6)
                        window_close = next_survey_date + relativedelta(months=6)
                        window_type = '±6M'
                        has_explicit_annotation = True
                    elif '(±3M)' in next_survey_str or '(+3M)' in next_survey_str or '(+-3M)' in next_survey_str:
                        # Window: Next Survey ± 3M
                        window_open = next_survey_date - relativedelta(months=3)
                        window_close = next_survey_date + relativedelta(months=3)
                        window_type = '±3M'
                        has_explicit_annotation = True
                    elif '(-3M)' in next_survey_str:
                        # Window: Next Survey - 3M → Next Survey (only before)
                        window_open = next_survey_date - relativedelta(months=3)
                        window_close = next_survey_date
                        window_type = '-3M'
                        has_explicit_annotation = True
                    else:
                        # No annotation found - DEFAULT to (-3M) for safety
                        window_open = next_survey_date - relativedelta(months=3)
                        window_close = next_survey_date
                        window_type = '-3M (default)'
                        logger.info(f"📌 Certificate {cert.get('id', 'unknown')} has no annotation - using default (-3M) window")
                    
                    # Check if current_date is within window
                    if window_open <= current_date <= window_close:
                        # Find ship information
                        ship_info = next((ship for ship in ships if ship.get('id') == cert.get('ship_id')), {})
                        
                        # Calculate status
                        days_until_window_close = (window_close - current_date).days
                        days_until_survey = (next_survey_date - current_date).days
                        
                        # Status logic
                        # Overdue: Past window_close
                        is_overdue = current_date > window_close
                        
                        # Critical: ≤ 30 days to window_close
                        is_critical = 0 <= days_until_window_close <= 30
                        
                        # Due Soon: window_open < current_date < (window_close - 30 days)
                        window_close_minus_30 = window_close - timedelta(days=30)
                        is_due_soon = window_open < current_date < window_close_minus_30
                        
                        # Get cert abbreviation
                        cert_abbreviation = cert.get('cert_abbreviation', '')
                        cert_name_display = f"{cert.get('cert_name', '')} ({cert_abbreviation})" if cert_abbreviation else cert.get('cert_name', '')
                        
                        upcoming_survey = {
                            'certificate_id': cert.get('id'),
                            'ship_id': cert.get('ship_id'),
                            'ship_name': ship_info.get('name', ''),
                            'cert_name': cert.get('cert_name', ''),
                            'cert_abbreviation': cert_abbreviation,
                            'cert_name_display': cert_name_display,
                            'next_survey': next_survey_display,
                            'next_survey_date': next_survey_date.isoformat(),
                            'next_survey_type': cert.get('next_survey_type', ''),
                            'valid_date': cert.get('valid_date'),
                            'last_endorse': cert.get('last_endorse', ''),
                            'status': cert.get('status', ''),
                            'days_until_survey': days_until_survey,
                            'days_until_window_close': days_until_window_close,
                            'is_overdue': is_overdue,
                            'is_due_soon': is_due_soon,
                            'is_critical': is_critical,
                            'is_within_window': True,
                            'window_open': window_open.isoformat(),
                            'window_close': window_close.isoformat(),
                            'window_type': window_type
                        }
                        
                        upcoming_surveys.append(upcoming_survey)
                        
                except Exception as cert_error:
                    logger.warning(f"Error processing audit certificate {cert.get('id', 'unknown')}: {cert_error}")
                    continue
            
            # Sort by next survey date (soonest first)
            upcoming_surveys.sort(key=lambda x: x['next_survey_date'] or '9999-12-31')
            
            logger.info(f"✅ Found {len(upcoming_surveys)} audit certificates with upcoming surveys")
            
            return {
                "upcoming_surveys": upcoming_surveys,
                "total_count": len(upcoming_surveys),
                "company": user_company,
                "company_name": company_name,
                "check_date": current_date.isoformat(),
                "logic_info": {
                    "description": "Audit Certificate survey windows based on Next Survey annotation",
                    "window_rules": {
                        "±6M": "Window: Next Survey Date ± 6 months (Intermediate without Last Endorse)",
                        "±3M": "Window: Next Survey Date ± 3 months",
                        "-3M": "Window: Next Survey Date - 3 months → Next Survey Date (Initial/Renewal)",
                        "Due Soon": "window_open < current_date < (window_close - 30 days)",
                        "Critical": "≤ 30 days to window_close",
                        "Overdue": "Past window_close"
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting upcoming audit surveys: {e}")
            raise HTTPException(status_code=500, detail=str(e))

