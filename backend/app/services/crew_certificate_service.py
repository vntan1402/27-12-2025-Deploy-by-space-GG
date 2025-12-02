import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile

from app.models.crew_certificate import (
    CrewCertificateCreate,
    CrewCertificateUpdate,
    CrewCertificateResponse,
    BulkDeleteCrewCertificateRequest
)
from app.models.user import UserResponse, UserRole
from app.repositories.crew_certificate_repository import CrewCertificateRepository
from app.repositories.crew_repository import CrewRepository

logger = logging.getLogger(__name__)

class CrewCertificateService:
    """Business logic for crew certificate management"""
    
    @staticmethod
    def _classify_certificate_v1_logic(
        extracted_cert_name: str,
        note: str,
        rank: str,
        document_summary: str
    ) -> str:
        """
        Classify certificate type using V1's priority-based logic
        
        Priority System (V1 Approach):
        - PRIORITY 0.5: Seaman Book combinations (check document type FIRST)
        - PRIORITY 1: GMDSS standalone
        - PRIORITY 1.5: OIC keywords
        - PRIORITY 2: Specific certificates (SSO, BST, Medical, etc.)
        - PRIORITY 3: Rank keywords → COC
        
        Returns: Classified certificate name
        """
        # Convert all to uppercase for comparison
        note_upper = note.upper()
        rank_upper = rank.upper()
        summary_upper = document_summary.upper()
        cert_name_upper = extracted_cert_name.upper()
        
        # Combine all text for keyword search
        all_text = f"{cert_name_upper} {note_upper} {rank_upper} {summary_upper}"
        
        # ===================================================
        # PRIORITY 0.5: Seaman Book combinations (HIGHEST)
        # Check document type FIRST before qualifications
        # ===================================================
        SEAMAN_BOOK_KEYWORDS = [
            'SEAMAN BOOK', "SEAMAN'S BOOK", 'SEAMANS BOOK',
            'LIBRETA DE EMBARQUE', 'LIBRETA',
            'MERCHANT MARINER',
            'P-NUMBER', 'P NUMBER', 'P-0', 'P0196554A',
            'DOCUMENT OF IDENTITY', 'SEAFARER IDENTITY',
            'DISCHARGE BOOK', 'SERVICE BOOK',
            'REPUBLICA DE PANAMA'
        ]
        
        has_seaman_book = any(kw in all_text for kw in SEAMAN_BOOK_KEYWORDS)
        
        if has_seaman_book:
            logger.info("📖 PRIORITY 0.5: Seaman Book detected, checking qualification...")
            
            # Check for GMDSS + Seaman Book → "Seaman book for GMDSS"
            GMDSS_KEYWORDS = [
                'GMDSS', 'MDSS',  # MDSS = typo variant
                'GLOBAL MARITIME DISTRESS',
                'RADIO OPERATOR', 'RADIO COMMUNICATION',
                'MDSS GENERAL OPERATOR', 'GMDSS GENERAL OPERATOR',
                'GOC', 'ROC'
            ]
            # Check for IV/2 separately with boundary check to avoid matching II/2, I/2
            has_gmdss = any(kw in all_text for kw in GMDSS_KEYWORDS)
            
            # Check for IV/2 (GMDSS code) but NOT II/2 or I/2 (Officer codes)
            if not has_gmdss and 'IV/2' in all_text:
                # Only match if IV/2 is standalone, not part of II/2 or III/2
                if ' IV/2' in all_text or '\nIV/2' in all_text or 'IV/2 ' in all_text or 'IV/2\n' in all_text:
                    has_gmdss = True
            
            if has_gmdss:
                logger.info("✅ PRIORITY 0.5: Seaman Book + GMDSS → 'Seaman book for GMDSS'")
                return 'Seaman book for GMDSS'
            
            # Check for Rank + Seaman Book → "Seaman Book for COC"
            RANK_KEYWORDS = [
                'MASTER', 'CAPTAIN', 'CAPT',
                'CHIEF MATE', 'CHIEF OFFICER', 'C/MATE', 'C/M',
                'SECOND MATE', 'SECOND OFFICER', '2ND MATE', '2/M',
                'THIRD MATE', 'THIRD OFFICER', '3RD MATE', '3/M',
                'CHIEF ENGINEER', 'C/E', 'C/ENG',
                'SECOND ENGINEER', '2ND ENGINEER', '2/E',
                'THIRD ENGINEER', '3RD ENGINEER', '3/E',
                'DECK OFFICER', 'ENGINE OFFICER', 'OFFICER', 'OOW',
                'CAPACITY', 'MASTER LIMITED', 'MASTER UNLIMITED',
                'II/1', 'II/2', 'II/3', 'III/1', 'III/2', 'III/3'
            ]
            has_rank = any(kw in all_text for kw in RANK_KEYWORDS)
            
            if has_rank:
                logger.info("✅ PRIORITY 0.5: Seaman Book + Rank → 'Seaman Book for COC'")
                return 'Seaman Book for COC'
            
            # Generic Seaman Book (no specific qualification)
            logger.info("✅ PRIORITY 0.5: Seaman Book (generic)")
            return 'Seaman Book'
        
        # ===================================================
        # PRIORITY 1: GMDSS standalone (not seaman book)
        # ===================================================
        GMDSS_KEYWORDS = [
            'GMDSS', 'MDSS',
            'GLOBAL MARITIME DISTRESS',
            'RADIO OPERATOR', 'RADIO COMMUNICATION',
            'MDSS GENERAL OPERATOR', 'GMDSS GENERAL OPERATOR'
        ]
        
        for keyword in GMDSS_KEYWORDS:
            if keyword in all_text:
                logger.info(f"✅ PRIORITY 1: Found GMDSS keyword '{keyword}' → 'GMDSS Certificate'")
                return 'GMDSS Certificate'
        
        # ===================================================
        # PRIORITY 1.5: OIC keywords → COC
        # ===================================================
        OIC_KEYWORDS = [
            'OFFICER IN CHARGE OF A NAVIGATIONAL WATCH',
            'OFFICER IN CHARGE OF NAVIGATIONAL WATCH',
            'OIC NAVIGATIONAL WATCH',
            'OIC-NW', 'OICNW'
        ]
        
        for keyword in OIC_KEYWORDS:
            if keyword in all_text:
                logger.info(f"✅ PRIORITY 1.5: Found OIC keyword '{keyword}' → COC")
                return 'Certificate of Competency (COC)'
        
        # ===================================================
        # PRIORITY 2: Specific training certificates
        # NOTE: BRM/ERM removed from here - they should be checked AFTER rank keywords
        # because COC certificates often mention these as part of competencies
        # ===================================================
        SPECIFIC_CERT_KEYWORDS = {
            'SHIP SECURITY OFFICER': 'Ship Security Officer (SSO)',
            'SSO TRAINING': 'Ship Security Officer (SSO)',
            'ADVANCED FIRE FIGHTING': 'Advanced Fire Fighting (AFF)',
            'FIRE FIGHTING': 'Advanced Fire Fighting (AFF)',
            'BASIC SAFETY TRAINING': 'Basic Safety Training (BST)',
            'BASIC SAFETY': 'Basic Safety Training (BST)',
            'MEDICAL CERTIFICATE': 'Medical Certificate',
            'MEDICAL EXAMINATION': 'Medical Certificate',
            'MEDICAL FITNESS': 'Medical Certificate',
            'ECDIS': 'ECDIS'
        }
        
        for keyword, cert_name in SPECIFIC_CERT_KEYWORDS.items():
            if keyword in all_text:
                logger.info(f"✅ PRIORITY 2: Found specific cert keyword '{keyword}' → {cert_name}")
                return cert_name
        
        # ===================================================
        # PRIORITY 3: Rank keywords → COC or COE
        # If rank + endorsement keywords → COE
        # If rank only → COC
        # ===================================================
        RANK_KEYWORDS = [
            'MASTER', 'CAPTAIN', 'CAPT',
            'CHIEF MATE', 'CHIEF OFFICER', 'C/MATE', 'C/M',
            'SECOND MATE', 'SECOND OFFICER', '2ND MATE', '2/M',
            'THIRD MATE', 'THIRD OFFICER', '3RD MATE', '3/M',
            'CHIEF ENGINEER', 'C/E', 'C/ENG',
            'SECOND ENGINEER', '2ND ENGINEER', '2/E',
            'THIRD ENGINEER', '3RD ENGINEER', '3/E',
            'DECK OFFICER', 'ENGINE OFFICER', 'OFFICER', 'OOW',
            'CAPACITY', 'MASTER LIMITED', 'MASTER UNLIMITED',
            'II/1', 'II/2', 'II/3', 'III/1', 'III/2', 'III/3'
        ]
        
        ENDORSEMENT_KEYWORDS = [
            'ENDORSEMENT', 'REFRENDO', 'RECOGNITION',
            'RECONOCIMIENTO', 'ATTESTING'
        ]
        
        for rank_kw in RANK_KEYWORDS:
            if rank_kw in all_text:
                # Check if it's an endorsement certificate
                has_endorsement = any(kw in all_text for kw in ENDORSEMENT_KEYWORDS)
                
                if has_endorsement:
                    logger.info(f"✅ PRIORITY 3: Found rank '{rank_kw}' + endorsement → COE")
                    return 'Certificate of Endorsement (COE)'
                else:
                    logger.info(f"✅ PRIORITY 3: Found rank keyword '{rank_kw}' → COC")
                    return 'Certificate of Competency (COC)'
        
        # ===================================================
        # PRIORITY 3.5: BRM/ERM training certificates
        # Checked AFTER rank keywords because COC certs often mention these
        # Only classify as BRM/ERM if no rank keywords found
        # ===================================================
        RESOURCE_MANAGEMENT_KEYWORDS = {
            'BRIDGE RESOURCE MANAGEMENT': 'Bridge Resource Management (BRM)',
            'BRM TRAINING': 'Bridge Resource Management (BRM)',
            'ENGINE RESOURCE MANAGEMENT': 'Engine Resource Management (ERM)',
            'ERM TRAINING': 'Engine Resource Management (ERM)'
        }
        
        for keyword, cert_name in RESOURCE_MANAGEMENT_KEYWORDS.items():
            if keyword in all_text:
                logger.info(f"✅ PRIORITY 3.5: Found resource mgmt keyword '{keyword}' → {cert_name}")
                return cert_name
        
        # ===================================================
        # PRIORITY 4: Fallback to AI extracted name if exists
        # ===================================================
        if extracted_cert_name and extracted_cert_name.strip():
            logger.info(f"⚠️ No priority match, using AI extracted: {extracted_cert_name}")
            return extracted_cert_name
        
        # ===================================================
        # Default: Unknown
        # ===================================================
        logger.warning("⚠️ No classification match found, returning 'Unknown'")
        return 'Unknown'
    
    @staticmethod
    async def get_all_crew_certificates(
        crew_id: Optional[str],
        current_user: UserResponse
    ) -> List[CrewCertificateResponse]:
        """
        Get ALL crew certificates for the company (no ship filter)
        Includes both ship-assigned and Standby crew certificates
        """
        filters = {}
        
        # Add company filter - required for all users except system admin
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            if not current_user.company:
                raise HTTPException(status_code=400, detail="User has no company assigned")
            filters["company_id"] = current_user.company
        
        # Add crew_id filter if provided
        if crew_id:
            filters["crew_id"] = crew_id
        
        certificates = await CrewCertificateRepository.find_all(filters)
        
        logger.info(f"📋 Retrieved {len(certificates)} crew certificates for company (all ships + standby)")
        
        return [CrewCertificateResponse(**cert) for cert in certificates]
    
    @staticmethod
    async def get_crew_certificates(
        crew_id: Optional[str], 
        company_id: Optional[str],
        current_user: UserResponse
    ) -> List[CrewCertificateResponse]:
        """Get crew certificates with optional filters"""
        filters = {}
        
        # Add crew_id filter if provided
        if crew_id:
            filters["crew_id"] = crew_id
        
        # Add company filter for non-admin users
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            filters["company_id"] = current_user.company
        elif company_id:
            filters["company_id"] = company_id
        
        certificates = await CrewCertificateRepository.find_all(filters)
        return [CrewCertificateResponse(**cert) for cert in certificates]
    
    @staticmethod
    async def get_crew_certificate_by_id(cert_id: str, current_user: UserResponse) -> CrewCertificateResponse:
        """Get crew certificate by ID"""
        cert = await CrewCertificateRepository.find_by_id(cert_id)
        
        if not cert:
            raise HTTPException(status_code=404, detail="Crew certificate not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            if cert.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        return CrewCertificateResponse(**cert)
    
    @staticmethod
    async def check_duplicate(crew_id: str, cert_no: str, current_user: UserResponse) -> dict:
        """
        Check if a crew certificate is duplicate based on crew_id + cert_no
        Returns existing certificate info if duplicate found
        """
        from app.db.mongodb import mongo_db
        
        company_id = current_user.company
        
        # Check if certificate already exists with same crew_id + cert_no
        existing_cert = await mongo_db.find_one("crew_certificates", {
            "company_id": company_id,
            "crew_id": crew_id,
            "cert_no": cert_no
        })
        
        if existing_cert:
            logger.warning(f"⚠️ Duplicate found: {existing_cert.get('cert_name')} - {cert_no}")
            return {
                "is_duplicate": True,
                "existing_certificate": {
                    "id": existing_cert.get("id"),
                    "cert_name": existing_cert.get("cert_name"),
                    "cert_no": existing_cert.get("cert_no"),
                    "crew_name": existing_cert.get("crew_name"),
                    "issued_date": existing_cert.get("issued_date"),
                    "cert_expiry": existing_cert.get("cert_expiry"),
                    "issued_by": existing_cert.get("issued_by")
                },
                "message": f"Certificate with number '{cert_no}' already exists for this crew member"
            }
        else:
            logger.info("✅ No duplicate found")
            return {
                "is_duplicate": False,
                "message": "No duplicate found"
            }
    
    @staticmethod
    async def create_crew_certificate(cert_data: CrewCertificateCreate, current_user: UserResponse) -> CrewCertificateResponse:
        """Create new crew certificate with V1 validations"""
        from app.services.audit_trail_service import AuditTrailService
        from app.db.mongodb import mongo_db
        
        # 1. Validate crew_id is required
        if not cert_data.crew_id:
            raise HTTPException(status_code=400, detail="crew_id is required")
        
        # Auto-set company_id from current_user if not provided
        company_id = cert_data.company_id or current_user.company
        if not company_id:
            raise HTTPException(status_code=400, detail="Company ID is required")
        
        # 2. Verify crew exists
        crew = await CrewRepository.find_by_id(cert_data.crew_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Crew member not found")
        
        # 3. Auto-determine ship_id based on crew's ship_sign_on (V1 logic)
        crew_ship_sign_on = crew.get("ship_sign_on", "-")
        ship_id = None
        ship_name = None
        
        if crew_ship_sign_on and crew_ship_sign_on != "-":
            # Crew is assigned to a ship - find ship by name
            ship = await mongo_db.find_one("ships", {
                "name": crew_ship_sign_on,
                "company_id": company_id
            })
            
            if ship:
                ship_id = ship.get("id")
                ship_name = ship.get("name")
                logger.info(f"✅ Found ship: {ship_name} (ID: {ship_id})")
            else:
                logger.warning(f"⚠️ Ship '{crew_ship_sign_on}' not found in database")
                # Continue with ship_id = None (will upload to Standby folder)
        else:
            # Crew is Standby (ship_sign_on = "-")
            logger.info("📍 Crew is Standby (ship_sign_on = '-'), certificate will go to Standby Crew")
        
        # Create certificate document
        cert_dict = cert_data.dict()
        cert_dict["id"] = str(uuid.uuid4())
        cert_dict["company_id"] = company_id
        cert_dict["ship_id"] = ship_id  # Auto-determined from crew's ship_sign_on
        
        # Override rank with crew's current rank
        cert_dict["rank"] = crew.get("rank", "") or cert_dict.get("rank", "")
        
        # 4. Normalize issued_by (V1 logic)
        if cert_dict.get("issued_by"):
            cert_dict["issued_by"] = CrewCertificateService._normalize_issued_by(cert_dict["issued_by"])
            
            # Generate abbreviation
            from app.utils.issued_by_abbreviation import generate_organization_abbreviation
            cert_dict["issued_by_abbreviation"] = generate_organization_abbreviation(cert_dict["issued_by"])
            logger.info(f"📋 Normalized & abbreviated: {cert_dict['issued_by']} → {cert_dict['issued_by_abbreviation']}")
        
        # 5. Auto-calculate status from cert_expiry (V1 logic)
        if cert_dict.get("cert_expiry"):
            cert_dict["status"] = CrewCertificateService._calculate_certificate_status(cert_dict["cert_expiry"])
            logger.info(f"🔄 Auto-calculated status: {cert_dict['status']}")
        
        cert_dict["created_at"] = datetime.now(timezone.utc)
        cert_dict["created_by"] = current_user.username
        
        await CrewCertificateRepository.create(cert_dict)
        
        # 6. Log audit trail
        await AuditTrailService.log_action(
            user_id=current_user.id,
            action="CREATE_CREW_CERTIFICATE",
            resource_type="crew_certificate",
            resource_id=cert_dict["id"],
            details={
                "crew_name": cert_data.crew_name,
                "cert_name": cert_data.cert_name,
                "cert_no": cert_data.cert_no,
                "ship_id": ship_id
            },
            company_id=current_user.company
        )
        
        logger.info(f"✅ Crew certificate created: {cert_dict['cert_name']} for crew {cert_data.crew_id}")
        
        return CrewCertificateResponse(**cert_dict)
    
    @staticmethod
    def _normalize_issued_by(issued_by: str) -> str:
        """Normalize issued_by to standard maritime authority names (V1 logic)"""
        if not issued_by:
            return issued_by
        
        issued_lower = issued_by.lower()
        
        # Vietnam
        if "vietnam" in issued_lower or "viet nam" in issued_lower:
            return "Vietnam Maritime Administration"
        # Panama
        elif "panama" in issued_lower:
            return "Panama Maritime Authority"
        # Marshall Islands
        elif "marshall" in issued_lower:
            return "Marshall Islands Maritime Administrator"
        # Liberia
        elif "liberia" in issued_lower:
            return "Liberia Maritime Authority"
        # Singapore
        elif "singapore" in issued_lower:
            return "Maritime and Port Authority of Singapore"
        # UK
        elif "uk" in issued_lower or "united kingdom" in issued_lower or "british" in issued_lower:
            return "UK Maritime and Coastguard Agency"
        # Malaysia
        elif "malaysia" in issued_lower:
            return "Marine Department Malaysia"
        else:
            return issued_by
    
    @staticmethod
    def _calculate_certificate_status(cert_expiry) -> str:
        """Auto-calculate certificate status based on expiry date (V1 logic)"""
        if not cert_expiry:
            return "Unknown"
        
        # Convert to datetime if string
        if isinstance(cert_expiry, str):
            try:
                cert_expiry = datetime.fromisoformat(cert_expiry.replace('Z', '+00:00'))
            except:
                return "Unknown"
        
        now = datetime.now(timezone.utc)
        
        # Check if expired
        if cert_expiry < now:
            return "Expired"
        
        # Check if expiring within 3 months
        days_until_expiry = (cert_expiry - now).days
        if days_until_expiry <= 90:  # 3 months
            return "Expiring Soon"
        
        return "Valid"
    
    @staticmethod
    async def update_crew_certificate(
        cert_id: str, 
        cert_data: CrewCertificateUpdate, 
        current_user: UserResponse
    ) -> CrewCertificateResponse:
        """Update crew certificate"""
        cert = await CrewCertificateRepository.find_by_id(cert_id)
        if not cert:
            raise HTTPException(status_code=404, detail="Crew certificate not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            if cert.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare update data
        update_data = cert_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = current_user.username
        
        # If issued_by is updated, regenerate abbreviation
        if "issued_by" in update_data and update_data["issued_by"]:
            from app.utils.issued_by_abbreviation import generate_organization_abbreviation
            update_data["issued_by_abbreviation"] = generate_organization_abbreviation(update_data["issued_by"])
            logger.info(f"📋 Regenerated abbreviation: {update_data['issued_by']} → {update_data['issued_by_abbreviation']}")
        
        if update_data:
            await CrewCertificateRepository.update(cert_id, update_data)
        
        # Get updated certificate
        updated_cert = await CrewCertificateRepository.find_by_id(cert_id)
        
        logger.info(f"✅ Crew certificate updated: {cert_id}")
        
        return CrewCertificateResponse(**updated_cert)
    
    @staticmethod
    async def delete_crew_certificate(cert_id: str, current_user: UserResponse) -> dict:
        """Delete crew certificate including associated Google Drive files"""
        from app.services.crew_certificate_drive_service import CrewCertificateDriveService
        
        cert = await CrewCertificateRepository.find_by_id(cert_id)
        if not cert:
            raise HTTPException(status_code=404, detail="Crew certificate not found")
        
        # Check access permission
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            if cert.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete Google Drive files if they exist
        files_deleted = 0
        company_id = cert.get('company_id')
        
        cert_file_id = cert.get('crew_cert_file_id')
        summary_file_id = cert.get('crew_cert_summary_file_id')
        
        if cert_file_id or summary_file_id:
            try:
                if cert_file_id:
                    result = await CrewCertificateDriveService.delete_certificate_file(
                        company_id=company_id,
                        file_id=cert_file_id
                    )
                    if result.get('success'):
                        files_deleted += 1
                        logger.info(f"✅ Deleted certificate file: {cert_file_id}")
                
                if summary_file_id:
                    result = await CrewCertificateDriveService.delete_certificate_file(
                        company_id=company_id,
                        file_id=summary_file_id
                    )
                    if result.get('success'):
                        files_deleted += 1
                        logger.info(f"✅ Deleted summary file: {summary_file_id}")
            except Exception as e:
                logger.warning(f"⚠️ Error deleting files from Google Drive: {e}")
                # Continue with database deletion even if file deletion fails
        
        # Delete from database
        await CrewCertificateRepository.delete(cert_id)
        
        # Log audit trail
        from app.services.audit_trail_service import AuditTrailService
        await AuditTrailService.log_action(
            user_id=current_user.id,
            action="DELETE_CREW_CERTIFICATE",
            resource_type="crew_certificate",
            resource_id=cert_id,
            details={
                "crew_name": cert.get('crew_name'),
                "cert_name": cert.get('cert_name'),
                "cert_no": cert.get('cert_no'),
                "files_deleted": files_deleted
            },
            company_id=company_id
        )
        
        message = f"Crew certificate deleted successfully"
        if files_deleted > 0:
            message += f" ({files_deleted} file(s) deleted from Google Drive)"
        
        logger.info(f"✅ Crew certificate deleted: {cert_id}")
        
        return {"message": message, "files_deleted": files_deleted}
    
    @staticmethod
    async def bulk_delete_crew_certificates(
        request: BulkDeleteCrewCertificateRequest, 
        current_user: UserResponse
    ) -> dict:
        """Bulk delete crew certificates including associated Google Drive files"""
        from app.db.mongodb import mongo_db
        
        # Get company ID
        company_id = current_user.company
        if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            if not company_id:
                raise HTTPException(status_code=400, detail="User has no company assigned")
        
        cert_ids = request.certificate_ids
        logger.info(f"🗑️ Bulk delete crew certificates request: {len(cert_ids)} certificate(s)")
        
        deleted_count = 0
        files_deleted = 0
        errors = []
        
        for cert_id in cert_ids:
            try:
                # Check if certificate exists
                cert = await mongo_db.find_one("crew_certificates", {
                    "id": cert_id,
                    "company_id": company_id
                })
                
                if not cert:
                    logger.warning(f"⚠️ Certificate not found: {cert_id}")
                    errors.append(f"Certificate {cert_id} not found")
                    continue
                
                # Delete Google Drive files if they exist
                from app.services.crew_certificate_drive_service import CrewCertificateDriveService
                
                cert_file_id = cert.get('crew_cert_file_id')
                summary_file_id = cert.get('crew_cert_summary_file_id')
                
                if cert_file_id or summary_file_id:
                    try:
                        if cert_file_id:
                            result = await CrewCertificateDriveService.delete_certificate_file(
                                company_id=company_id,
                                file_id=cert_file_id
                            )
                            if result.get('success'):
                                files_deleted += 1
                                logger.info(f"✅ Deleted certificate file: {cert_file_id}")
                        
                        if summary_file_id:
                            result = await CrewCertificateDriveService.delete_certificate_file(
                                company_id=company_id,
                                file_id=summary_file_id
                            )
                            if result.get('success'):
                                files_deleted += 1
                                logger.info(f"✅ Deleted summary file: {summary_file_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error deleting files for cert {cert_id}: {e}")
                        # Continue with database deletion
                
                # Delete from database
                await mongo_db.delete("crew_certificates", {"id": cert_id})
                deleted_count += 1
                
                # Log audit trail
                from app.services.audit_trail_service import AuditTrailService
                await AuditTrailService.log_action(
                    user_id=current_user.id,
                    action="DELETE_CREW_CERTIFICATE",
                    resource_type="crew_certificate",
                    resource_id=cert_id,
                    details={
                        "crew_name": cert.get('crew_name'),
                        "cert_name": cert.get('cert_name'),
                        "cert_no": cert.get('cert_no'),
                        "bulk_delete": True
                    },
                    company_id=company_id
                )
                
                logger.info(f"✅ Crew certificate deleted: {cert_id}")
                
            except Exception as e:
                error_msg = f"Error deleting certificate {cert_id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        # If no certificates were deleted at all, return error
        if deleted_count == 0 and len(errors) > 0:
            error_details = "; ".join(errors)
            raise HTTPException(status_code=404, detail=f"No certificates deleted. {error_details}")
        
        message = f"Deleted {deleted_count} certificate(s)"
        if files_deleted > 0:
            message += f", {files_deleted} file(s) deleted from Google Drive"
        if errors:
            message += f", {len(errors)} error(s)"
        
        logger.info(f"✅ Bulk delete complete: {deleted_count} certificates deleted")
        
        return {
            "success": True,
            "message": message,
            "deleted_count": deleted_count,
            "files_deleted": files_deleted,
            "errors": errors if errors else None,
            "partial_success": len(errors) > 0 and deleted_count > 0
        }
    
    @staticmethod
    async def analyze_crew_certificate_file(
        file: UploadFile, 
        crew_id: str,
        current_user: UserResponse
    ) -> dict:
        """Analyze crew certificate file using Document AI + LLM extraction (matches passport pattern)"""
        import base64
        import os
        from app.db.mongodb import mongo_db
        
        # Validate file type
        if not file.content_type or not (file.content_type == "application/pdf" or file.content_type.startswith("image/")):
            raise HTTPException(status_code=400, detail="Only PDF or image files are allowed")
        
        # Read file content
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file received")
        
        logger.info(f"📄 Analyzing crew certificate file: {file.filename} ({len(file_content)} bytes)")
        
        try:
            # Get crew information
            crew = await CrewRepository.find_by_id(crew_id)
            if not crew:
                raise HTTPException(status_code=404, detail="Crew member not found")
            
            crew_name = crew.get('full_name', 'Unknown')
            crew_name_en = crew.get('full_name_en', '')
            passport = crew.get('passport', 'Unknown')
            rank = crew.get('rank', '')
            date_of_birth = crew.get('date_of_birth')
            
            logger.info(f"👤 Analyzing certificate for: {crew_name} (Passport: {passport})")
            
            # Step 1: Get Document AI configuration (EXACT MATCH with passport)
            ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
            if not ai_config_doc:
                return {
                    "success": False,
                    "message": "AI configuration not found",
                    "analysis": None
                }
            
            document_ai_config = ai_config_doc.get("document_ai", {})
            
            if not document_ai_config.get("enabled", False):
                return {
                    "success": False,
                    "message": "Google Document AI is not enabled in System Settings",
                    "analysis": None
                }
            
            # Validate required Document AI configuration
            if not all([
                document_ai_config.get("project_id"),
                document_ai_config.get("processor_id")
            ]):
                return {
                    "success": False,
                    "message": "Incomplete Google Document AI configuration. Please check Project ID and Processor ID.",
                    "analysis": None
                }
            
            # Get Apps Script URL from document_ai_config
            apps_script_url = document_ai_config.get("apps_script_url")
            
            if not apps_script_url:
                logger.error("❌ Apps Script URL not configured in Document AI settings")
                return {
                    "success": False,
                    "message": "Apps Script URL not configured. Please configure Apps Script URL in Document AI settings (System AI).",
                    "analysis": None
                }
            
            # Add apps_script_url to config for document_ai_helper
            document_ai_config_with_url = {
                **document_ai_config,
                "apps_script_url": apps_script_url
            }
            
            # Step 2: Call Document AI (EXACT MATCH with passport)
            from app.utils.document_ai_helper import analyze_document_with_document_ai
            
            logger.info(f"🤖 Calling Document AI for certificate analysis...")
            
            doc_ai_result = await analyze_document_with_document_ai(
                file_content=file_content,
                filename=file.filename,
                content_type=file.content_type or 'application/pdf',
                document_ai_config=document_ai_config_with_url,
                document_type='other'  # Certificate is general document type
            )
            
            if not doc_ai_result or not doc_ai_result.get("success"):
                error_msg = doc_ai_result.get("message", "Unknown error") if doc_ai_result else "No response from Document AI"
                logger.error(f"❌ Document AI failed: {error_msg}")
                return {
                    "success": False,
                    "message": f"Document AI analysis failed: {error_msg}",
                    "analysis": None
                }
            
            # Get summary from Document AI
            data = doc_ai_result.get("data", {})
            document_summary = data.get("summary", "").strip()
            
            logger.info(f"📄 Document AI summary length: {len(document_summary)} characters")
            
            if not document_summary or len(document_summary) < 20:
                logger.warning(f"⚠️ Document AI returned insufficient text: {len(document_summary)} characters")
                return {
                    "success": False,
                    "message": "Could not extract sufficient text from certificate using Document AI",
                    "analysis": None
                }
            
            logger.info(f"✅ Document AI extracted {len(document_summary)} characters")
            
            # Step 2: Use LLM AI to extract certificate fields from summary
            try:
                ai_config = await AIConfigService.get_ai_config(current_user)
                provider = ai_config.provider
                model = ai_config.model
            except:
                ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
                provider = ai_config_doc.get("provider", "google") if ai_config_doc else "google"
                model = ai_config_doc.get("model", "gemini-2.0-flash") if ai_config_doc else "gemini-2.0-flash"
            
            emergent_key = os.getenv("EMERGENT_LLM_KEY", "sk-emergent-eEe35Fb1b449940199")
            
            # Define standard certificate names (must match frontend dropdown)
            STANDARD_CERT_NAMES = [
                'Certificate of Competency (COC)',
                'Certificate of Endorsement (COE)',
                'Seaman Book for COC',
                'Seaman book for GMDSS',
                'GMDSS Certificate',
                'Medical Certificate',
                'Basic Safety Training (BST)',
                'Advanced Fire Fighting (AFF)',
                'Ship Security Officer (SSO)',
                'Ship Security Awareness',
                'Proficiency in Survival Craft and Rescue Boats',
                'Crowd Management',
                'Crisis Management and Human Behavior',
                'Passenger Ship Safety',
                'ECDIS',
                'Bridge Resource Management (BRM)',
                'Engine Resource Management (ERM)',
                'High Voltage Certificate',
                'Ratings Forming Part of a Watch',
                'Ratings as Able Seafarer Deck',
                'Ratings as Able Seafarer Engine',
                'Oil Tanker Familiarization',
                'Chemical Tanker Familiarization',
                'Liquefied Gas Tanker Familiarization',
                'Oil Tanker Advanced',
                'Chemical Tanker Advanced',
                'Liquefied Gas Tanker Advanced',
                'Welding Certificate',
                'Radar Certificate'
            ]
            
            # Create AI prompt for crew certificate field extraction with classification
            standard_certs_list = '\n'.join([f"- {name}" for name in STANDARD_CERT_NAMES])
            
            prompt = f"""You are an AI specialized in extracting structured information from maritime crew certificates.

Your task:
Analyze the COMPLETE text summary below to extract all key certificate fields.
**IMPORTANT**: Read through the ENTIRE document content carefully before classifying the certificate type.

=== CREW INFORMATION ===
Expected Crew Name: {crew_name}
Expected Passport: {passport}
Expected Rank: {rank}

=== INSTRUCTIONS ===
1. **READ THE ENTIRE DOCUMENT SUMMARY** below before making any classification decision
2. Extract only the certificate-related fields listed below
3. Return the output strictly in valid JSON format
4. If a field is not found, leave it as an empty string ""
5. Normalize all dates to DD/MM/YYYY format
6. Use uppercase for official names and codes
7. Do not infer or fabricate any missing information

=== STANDARD CERTIFICATE TYPES (Choose from this list) ===
{standard_certs_list}

=== FIELDS TO EXTRACT ===
{{
  "cert_name": "",           // **MUST be ONE of the standard certificate types listed above**. Analyze the FULL document content to determine the correct type.
  "cert_no": "",             // Certificate number/ID
  "issued_by": "",           // Issuing authority (e.g., "Vietnam Maritime Administration", "Panama Maritime Authority")
  "issued_date": "",         // Issue date in DD/MM/YYYY format
  "cert_expiry": "",         // Expiry date in DD/MM/YYYY format
  "rank": "",                // Rank/capacity/qualification authorized (e.g., "Chief Engineer", "Master Mariner", "GMDSS General Operator", "IV/2")
  "crew_name": "",           // Name on certificate (should match expected crew)
  "passport": "",            // Passport number if mentioned
  "date_of_birth": "",       // Date of birth if mentioned
  "note": ""                 // Any additional important info (limitations, restrictions, specific qualifications)
}}

**CRITICAL CLASSIFICATION RULES - ANALYZE FULL DOCUMENT CONTENT**:

**STEP 1: Identify Document Type from FULL CONTENT**
Read through the entire document summary and look for these indicators:
- Document title/header (e.g., "Seaman's Book", "Libreta de embarque", "Certificate", "Discharge Book")
- Document structure and layout
- Type of information presented (identity document vs qualification certificate)
- Official stamps and authority names

**STEP 2: If SEAMAN BOOK detected:**
Look for these keywords ANYWHERE in the document:
- "Seaman's Book", "Seaman Book", "Seamans Book"
- "Libreta de embarque" (Spanish for Seaman's Book)
- "Discharge Book", "Service Book"
- "Seafarer's Identity Document"

If it's a Seaman Book, check the **qualification/capacity/rank** field in the document:
- If contains: "GMDSS", "General Operator", "GOC", "Restricted Operator", "ROC", "IV/2", "Radio Operator"
  → Classify as: "Seaman book for GMDSS"
- If contains: "Master", "Chief Engineer", "Officer", "II/1", "II/2", "III/1", "III/2", "COC", "Competency"
  → Classify as: "Seaman Book for COC"
- Otherwise (no specific qualification or generic seafarer)
  → Classify as: "Seaman Book"

**STEP 3: If STANDALONE CERTIFICATE detected:**
If document is NOT a seaman book but a separate certificate:
- Check document title and main content for qualification type
- "Certificate of Competency", "COC", "Master", "Chief Engineer", "Deck Officer", "Engineer Officer"
  → Classify as: "Certificate of Competency (COC)"
- "GMDSS Certificate", "Radio Operator Certificate", "GOC", "ROC" (as main qualification, not seaman book)
  → Classify as: "GMDSS Certificate"
- "Medical Certificate", "Medical Fitness", "Health Certificate"
  → Classify as: "Medical Certificate"
- "Endorsement" or "Recognition" (ONLY if no other functional qualification)
  → Classify as: "Certificate of Endorsement (COE)"
- And so on for other certificate types...

**CRITICAL NOTES:**
1. **Context Matters**: A document mentioning "GMDSS" in different contexts should be classified differently:
   - "Seaman's Book" with "GMDSS General Operator" capacity → "Seaman book for GMDSS"
   - Standalone "GMDSS Certificate" document → "GMDSS Certificate"
   - COC with radiocommunications function → "Certificate of Competency (COC)"

2. **Look at Multiple Fields**: Don't rely on just one field - check title, document type, capacity/rank, and content
3. **Put qualification details in rank field**: Extract the specific rank/capacity/qualification (e.g., "GMDSS GENERAL OPERATOR IV/2", "Master Mariner")
4. **Put additional context in note field**: Any restrictions, limitations, or additional qualifications

=== TEXT TO ANALYZE (FULL DOCUMENT CONTENT) ===
{document_summary}

Return ONLY the JSON object with extracted fields. No additional text."""

            logger.info("🤖 Calling LLM AI to extract certificate fields...")
            
            # Use emergentintegrations to call LLM (match crew passport pattern)
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            llm_chat = LlmChat(
                api_key=emergent_key,
                session_id="crew_certificate_analysis",
                system_message="You are an AI assistant that extracts crew certificate information from OCR text."
            )
            
            # Map provider to correct format for emergentintegrations
            if provider in ["google", "emergent"]:
                llm_chat = llm_chat.with_model("gemini", model)
            elif provider == "anthropic":
                llm_chat = llm_chat.with_model("claude", model)
            elif provider == "openai":
                llm_chat = llm_chat.with_model("openai", model)
            else:
                logger.warning(f"Unknown provider {provider}, using gemini as fallback")
                llm_chat = llm_chat.with_model("gemini", model)
            
            # Call AI
            ai_response = await llm_chat.send_message(UserMessage(text=prompt))
            
            logger.info(f"📦 AI response type: {type(ai_response)}")
            logger.info(f"📦 AI response value: {str(ai_response)[:500]}")
            
            if not ai_response:
                logger.error("❌ AI returned no response")
                return {
                    "success": False,
                    "message": "AI extraction failed - no response",
                    "analysis": None
                }
            
            logger.info(f"✅ AI extraction completed")
            
            # Parse AI response
            import json
            
            # Handle different response types
            response_text = None
            if isinstance(ai_response, str):
                response_text = ai_response
            elif hasattr(ai_response, 'content'):
                response_text = ai_response.content
            elif hasattr(ai_response, 'text'):
                response_text = ai_response.text
            else:
                response_text = str(ai_response)
            
            logger.info(f"📝 Response text length: {len(response_text) if response_text else 0}")
            
            # Clean response text - remove markdown code fences if present
            if response_text:
                response_text = response_text.strip()
                # Remove ```json ... ``` or ``` ... ``` markdown formatting
                if response_text.startswith('```'):
                    # Find first newline after opening fence
                    first_newline = response_text.find('\n')
                    if first_newline != -1:
                        response_text = response_text[first_newline + 1:]
                    # Remove closing fence
                    if response_text.endswith('```'):
                        response_text = response_text[:-3]
                    response_text = response_text.strip()
                
                logger.info(f"✂️ Cleaned response length: {len(response_text)}")
            
            try:
                parsed_data = json.loads(response_text) if response_text else {}
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse AI response as JSON: {e}")
                logger.error(f"   Response text: {response_text[:200]}")
                return {
                    "success": False,
                    "message": "Failed to parse AI response",
                    "analysis": None
                }
            
            # Post-processing: Classify certificate using V1 priority-based logic
            extracted_cert_name = parsed_data.get('cert_name', '').strip()
            extracted_note = parsed_data.get('note', '').strip()
            extracted_rank = parsed_data.get('rank', '').strip()
            
            # Use V1 classification logic with priority system
            logger.info("🔄 Starting V1 priority-based classification...")
            classified_cert_name = CrewCertificateService._classify_certificate_v1_logic(
                extracted_cert_name=extracted_cert_name,
                note=extracted_note,
                rank=extracted_rank,
                document_summary=document_summary
            )
            
            # Update parsed data with classified name
            parsed_data['cert_name'] = classified_cert_name
            logger.info(f"✅ Final classification: {classified_cert_name}")
            
            # Add file content for later upload
            parsed_data['_file_content'] = base64.b64encode(file_content).decode('utf-8')
            parsed_data['_filename'] = file.filename
            parsed_data['_content_type'] = file.content_type
            parsed_data['_summary_text'] = document_summary  # Add summary for upload to Google Drive
            
            logger.info(f"✅ Certificate analysis successful: {parsed_data.get('cert_name', 'Unknown')}")
            
            # Fetch crew info for batch upload (passport, rank, date_of_birth)
            crew = await CrewRepository.find_by_id(crew_id)
            crew_info = {}
            name_mismatch_warning = None
            
            if crew:
                crew_info = {
                    "crew_name": crew.get("full_name", ""),
                    "crew_name_en": crew.get("full_name_en", ""),
                    "passport": crew.get("passport", ""),
                    "rank": crew.get("rank", ""),
                    "date_of_birth": crew.get("date_of_birth", "")
                }
                
                # Check name mismatch with permutation support
                ai_extracted_name = parsed_data.get('crew_name', '')
                db_crew_name = crew.get('full_name', '')
                db_crew_name_en = crew.get('full_name_en', '')
                
                if ai_extracted_name:
                    from app.utils.name_matcher import check_name_match, format_name_mismatch_message
                    
                    is_match, similarity, matched_variant = check_name_match(
                        extracted_name=ai_extracted_name,
                        database_name=db_crew_name,
                        database_name_en=db_crew_name_en
                    )
                    
                    if not is_match:
                        # Name mismatch detected - BLOCK the flow
                        logger.error("❌ Name mismatch detected - BLOCKING analysis!")
                        logger.error(f"   AI extracted: {ai_extracted_name}")
                        logger.error(f"   Database: {db_crew_name} ({db_crew_name_en})")
                        
                        # Log to audit trail
                        from app.services.audit_trail_service import AuditTrailService
                        await AuditTrailService.log_action(
                            user_id=current_user.id,
                            action="CREW_CERT_NAME_MISMATCH_BLOCKED",
                            resource_type="crew_certificate",
                            resource_id=f"{crew_id}_blocked",
                            details={
                                "ai_extracted": ai_extracted_name,
                                "database_name": db_crew_name,
                                "database_name_en": db_crew_name_en,
                                "crew_id": crew_id,
                                "filename": file.filename,
                                "status": "blocked"
                            },
                            company_id=current_user.company
                        )
                        
                        # Raise HTTPException to block the flow
                        error_message = (
                            f"Name mismatch detected!\n\n"
                            f"Certificate name: {ai_extracted_name}\n"
                            f"Database name: {db_crew_name}"
                        )
                        if db_crew_name_en:
                            error_message += f" ({db_crew_name_en})"
                        error_message += (
                            f"\n\nPlease verify:\n"
                            f"1. Did you select the correct crew member?\n"
                            f"2. Is the certificate for this crew member?\n\n"
                            f"Note: System accepts name permutations (e.g., 'A TRAN VAN' matches 'TRAN VAN A')"
                        )
                        
                        raise HTTPException(
                            status_code=400,
                            detail=error_message
                        )
                    else:
                        # Name matches (exact or permutation)
                        logger.info(f"✅ Name match confirmed: {ai_extracted_name} → {matched_variant}")
                
                # Check Date of Birth mismatch AFTER name matches
                # If name matches but DoB is different, it means two different crew members with same name
                ai_extracted_dob = parsed_data.get('date_of_birth', '').strip()
                db_crew_dob = crew.get('date_of_birth')
                
                if ai_extracted_dob and db_crew_dob:
                    # Normalize both dates for comparison
                    from app.utils.date_normalizer import normalize_date_for_comparison
                    
                    normalized_ai_dob = normalize_date_for_comparison(ai_extracted_dob)
                    normalized_db_dob = normalize_date_for_comparison(db_crew_dob)
                    
                    logger.info(f"🔍 DoB Check - AI: {normalized_ai_dob}, DB: {normalized_db_dob}")
                    
                    if normalized_ai_dob and normalized_db_dob and normalized_ai_dob != normalized_db_dob:
                        # Date of Birth mismatch detected - BLOCK the flow
                        logger.error("❌ Date of Birth mismatch detected - BLOCKING analysis!")
                        logger.error(f"   AI extracted DoB: {ai_extracted_dob} ({normalized_ai_dob})")
                        logger.error(f"   Database DoB: {db_crew_dob} ({normalized_db_dob})")
                        
                        # Log to audit trail
                        from app.services.audit_trail_service import AuditTrailService
                        await AuditTrailService.log_action(
                            user_id=current_user.id,
                            action="CREW_CERT_DOB_MISMATCH_BLOCKED",
                            resource_type="crew_certificate",
                            resource_id=f"{crew_id}_dob_blocked",
                            details={
                                "ai_extracted_name": ai_extracted_name,
                                "ai_extracted_dob": ai_extracted_dob,
                                "database_name": db_crew_name,
                                "database_dob": str(db_crew_dob),
                                "crew_id": crew_id,
                                "filename": file.filename,
                                "status": "blocked_dob_mismatch"
                            },
                            company_id=current_user.company
                        )
                        
                        # Raise HTTPException to block the flow
                        # Use consistent format with name mismatch for easier frontend detection
                        error_message = (
                            f"Date of Birth mismatch detected!\n\n"
                            f"Crew name: {ai_extracted_name}\n"
                            f"Certificate DoB: {ai_extracted_dob}\n"
                            f"Database DoB: {db_crew_dob}\n\n"
                            f"This indicates two different crew members with the same name.\n\n"
                            f"Please verify:\n"
                            f"1. Did you select the correct crew member?\n"
                            f"2. Is this certificate for {db_crew_name} born on {db_crew_dob}?"
                        )
                        
                        raise HTTPException(
                            status_code=400,
                            detail=error_message
                        )
                    else:
                        # DoB matches or both are normalized successfully
                        logger.info(f"✅ Date of Birth match confirmed: {normalized_ai_dob}")
                elif ai_extracted_dob and not db_crew_dob:
                    logger.warning(f"⚠️ AI extracted DoB ({ai_extracted_dob}) but crew has no DoB in database")
                elif not ai_extracted_dob:
                    logger.info(f"ℹ️ No Date of Birth extracted from certificate - skipping DoB validation")
            
            return {
                "success": True,
                "message": "Crew certificate analyzed successfully",
                "analysis": parsed_data,
                "name_mismatch_warning": name_mismatch_warning,  # Add warning at root level
                # Include crew info for batch upload (root level for easy access)
                **crew_info
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error analyzing crew certificate: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to analyze certificate: {str(e)}")
