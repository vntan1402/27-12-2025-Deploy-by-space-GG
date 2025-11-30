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
    async def create_crew_certificate(cert_data: CrewCertificateCreate, current_user: UserResponse) -> CrewCertificateResponse:
        """Create new crew certificate"""
        from app.services.audit_trail_service import AuditTrailService
        
        # Auto-set company_id from current_user if not provided
        company_id = cert_data.company_id or current_user.company
        if not company_id:
            raise HTTPException(status_code=400, detail="Company ID is required")
        
        # Verify crew exists
        crew = await CrewRepository.find_by_id(cert_data.crew_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Crew member not found")
        
        # Create certificate document
        cert_dict = cert_data.dict()
        cert_dict["id"] = str(uuid.uuid4())
        cert_dict["company_id"] = company_id  # Ensure company_id is set
        
        # Override rank with crew's current rank (not rank from certificate)
        # This ensures consistency - all certificates for same crew show same rank
        cert_dict["rank"] = crew.get("rank", "") or cert_dict.get("rank", "")
        
        # Generate issued_by_abbreviation for display (like Class & Flag Cert)
        if cert_dict.get("issued_by"):
            from app.utils.issued_by_abbreviation import generate_organization_abbreviation
            cert_dict["issued_by_abbreviation"] = generate_organization_abbreviation(cert_dict["issued_by"])
            logger.info(f"📋 Generated abbreviation: {cert_dict['issued_by']} → {cert_dict['issued_by_abbreviation']}")
        
        cert_dict["created_at"] = datetime.now(timezone.utc)
        cert_dict["created_by"] = current_user.username
        
        await CrewCertificateRepository.create(cert_dict)
        
        # Log audit trail
        await AuditTrailService.log_action(
            user_id=current_user.id,
            action="CREATE_CREW_CERTIFICATE",
            resource_type="crew_certificate",
            resource_id=cert_dict["id"],
            details={
                "crew_name": cert_data.crew_name,
                "cert_name": cert_data.cert_name,
                "cert_no": cert_data.cert_no,
                "ship_id": cert_data.ship_id
            },
            company_id=current_user.company
        )
        
        logger.info(f"✅ Crew certificate created: {cert_dict['cert_name']} for crew {cert_data.crew_id}")
        
        return CrewCertificateResponse(**cert_dict)
    
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
    async def check_duplicate(
        crew_id: str, 
        cert_name: str, 
        cert_no: Optional[str],
        current_user: UserResponse
    ) -> dict:
        """Check if crew certificate is duplicate"""
        existing = await CrewCertificateRepository.check_duplicate(crew_id, cert_name, cert_no)
        
        return {
            "is_duplicate": existing is not None,
            "existing_certificate": CrewCertificateResponse(**existing).dict() if existing else None
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
Analyze the following text summary of a crew certificate and extract all key certificate fields.
The text contains information about the document, so focus on extracting and normalizing it into structured JSON format.

=== CREW INFORMATION ===
Expected Crew Name: {crew_name}
Expected Passport: {passport}
Expected Rank: {rank}

=== INSTRUCTIONS ===
1. Extract only the certificate-related fields listed below.
2. Return the output strictly in valid JSON format.
3. If a field is not found, leave it as an empty string "".
4. Normalize all dates to DD/MM/YYYY format.
5. Use uppercase for official names and codes.
6. Do not infer or fabricate any missing information.
7. **IMPORTANT**: For cert_name, you MUST classify and match to ONE of the standard certificate types listed below. If you cannot find an exact match, choose the closest/most similar one. Only if absolutely none match, you may use the original name from the document.

=== STANDARD CERTIFICATE TYPES (Choose from this list) ===
{standard_certs_list}

=== FIELDS TO EXTRACT ===
{{
  "cert_name": "",           // **MUST be ONE of the standard certificate types listed above** (e.g., "Certificate of Competency (COC)", "Medical Certificate"). Classify the certificate from the document into the closest matching standard type.
  "cert_no": "",             // Certificate number/ID
  "issued_by": "",           // Issuing authority (e.g., "Vietnam Maritime Administration", "Panama Maritime Authority")
  "issued_date": "",         // Issue date in DD/MM/YYYY format
  "cert_expiry": "",         // Expiry date in DD/MM/YYYY format
  "rank": "",                // Rank/capacity authorized (e.g., "Chief Engineer", "Master Mariner")
  "crew_name": "",           // Name on certificate (should match expected crew)
  "passport": "",            // Passport number if mentioned
  "date_of_birth": "",       // Date of birth if mentioned
  "note": ""                 // Any additional important info (limitations, restrictions, etc.)
}}

=== TEXT TO ANALYZE ===
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
            
            # Post-processing: Ensure cert_name matches standard types
            extracted_cert_name = parsed_data.get('cert_name', '').strip()
            if extracted_cert_name:
                # Check if it's already an exact match (case-insensitive)
                matched = False
                for standard_name in STANDARD_CERT_NAMES:
                    if extracted_cert_name.lower() == standard_name.lower():
                        parsed_data['cert_name'] = standard_name  # Use standard format
                        matched = True
                        logger.info(f"✅ Cert name exact match: {standard_name}")
                        break
                
                # If no exact match, try fuzzy matching based on keywords
                if not matched:
                    logger.info(f"⚠️ No exact match for: {extracted_cert_name}")
                    extracted_lower = extracted_cert_name.lower()
                    
                    # Fuzzy matching logic based on keywords
                    if any(keyword in extracted_lower for keyword in ['competency', 'competence', 'coc', 'master', 'officer certificate']):
                        parsed_data['cert_name'] = 'Certificate of Competency (COC)'
                        logger.info(f"🔍 Fuzzy matched to: Certificate of Competency (COC)")
                    elif any(keyword in extracted_lower for keyword in ['endorsement', 'coe', 'recognition']):
                        parsed_data['cert_name'] = 'Certificate of Endorsement (COE)'
                        logger.info(f"🔍 Fuzzy matched to: Certificate of Endorsement (COE)")
                    elif any(keyword in extracted_lower for keyword in ['medical', 'fitness', 'health']):
                        parsed_data['cert_name'] = 'Medical Certificate'
                        logger.info(f"🔍 Fuzzy matched to: Medical Certificate")
                    elif any(keyword in extracted_lower for keyword in ['gmdss', 'radio', 'communication']):
                        parsed_data['cert_name'] = 'GMDSS Certificate'
                        logger.info(f"🔍 Fuzzy matched to: GMDSS Certificate")
                    elif any(keyword in extracted_lower for keyword in ['basic safety', 'bst', 'stcw basic']):
                        parsed_data['cert_name'] = 'Basic Safety Training (BST)'
                        logger.info(f"🔍 Fuzzy matched to: Basic Safety Training (BST)")
                    elif any(keyword in extracted_lower for keyword in ['fire fighting', 'aff', 'advanced fire']):
                        parsed_data['cert_name'] = 'Advanced Fire Fighting (AFF)'
                        logger.info(f"🔍 Fuzzy matched to: Advanced Fire Fighting (AFF)")
                    elif any(keyword in extracted_lower for keyword in ['sso', 'ship security officer']):
                        parsed_data['cert_name'] = 'Ship Security Officer (SSO)'
                        logger.info(f"🔍 Fuzzy matched to: Ship Security Officer (SSO)")
                    elif any(keyword in extracted_lower for keyword in ['ecdis', 'electronic chart']):
                        parsed_data['cert_name'] = 'ECDIS'
                        logger.info(f"🔍 Fuzzy matched to: ECDIS")
                    elif any(keyword in extracted_lower for keyword in ['bridge resource', 'brm']):
                        parsed_data['cert_name'] = 'Bridge Resource Management (BRM)'
                        logger.info(f"🔍 Fuzzy matched to: Bridge Resource Management (BRM)")
                    elif any(keyword in extracted_lower for keyword in ['engine resource', 'erm']):
                        parsed_data['cert_name'] = 'Engine Resource Management (ERM)'
                        logger.info(f"🔍 Fuzzy matched to: Engine Resource Management (ERM)")
                    elif any(keyword in extracted_lower for keyword in ['oil tanker', 'tanker oil']):
                        if 'advanced' in extracted_lower:
                            parsed_data['cert_name'] = 'Oil Tanker Advanced'
                            logger.info(f"🔍 Fuzzy matched to: Oil Tanker Advanced")
                        else:
                            parsed_data['cert_name'] = 'Oil Tanker Familiarization'
                            logger.info(f"🔍 Fuzzy matched to: Oil Tanker Familiarization")
                    elif any(keyword in extracted_lower for keyword in ['chemical tanker', 'tanker chemical']):
                        if 'advanced' in extracted_lower:
                            parsed_data['cert_name'] = 'Chemical Tanker Advanced'
                            logger.info(f"🔍 Fuzzy matched to: Chemical Tanker Advanced")
                        else:
                            parsed_data['cert_name'] = 'Chemical Tanker Familiarization'
                            logger.info(f"🔍 Fuzzy matched to: Chemical Tanker Familiarization")
                    elif any(keyword in extracted_lower for keyword in ['gas tanker', 'lng', 'liquefied gas']):
                        if 'advanced' in extracted_lower:
                            parsed_data['cert_name'] = 'Liquefied Gas Tanker Advanced'
                            logger.info(f"🔍 Fuzzy matched to: Liquefied Gas Tanker Advanced")
                        else:
                            parsed_data['cert_name'] = 'Liquefied Gas Tanker Familiarization'
                            logger.info(f"🔍 Fuzzy matched to: Liquefied Gas Tanker Familiarization")
                    elif any(keyword in extracted_lower for keyword in ['survival craft', 'rescue boat', 'lifeboat']):
                        parsed_data['cert_name'] = 'Proficiency in Survival Craft and Rescue Boats'
                        logger.info(f"🔍 Fuzzy matched to: Proficiency in Survival Craft and Rescue Boats")
                    elif any(keyword in extracted_lower for keyword in ['crowd management', 'crowd control']):
                        parsed_data['cert_name'] = 'Crowd Management'
                        logger.info(f"🔍 Fuzzy matched to: Crowd Management")
                    elif any(keyword in extracted_lower for keyword in ['welding', 'welder']):
                        parsed_data['cert_name'] = 'Welding Certificate'
                        logger.info(f"🔍 Fuzzy matched to: Welding Certificate")
                    elif any(keyword in extracted_lower for keyword in ['radar', 'arpa']):
                        parsed_data['cert_name'] = 'Radar Certificate'
                        logger.info(f"🔍 Fuzzy matched to: Radar Certificate")
                    elif any(keyword in extracted_lower for keyword in ['seaman book', 'discharge book', 'seamans book']):
                        if 'gmdss' in extracted_lower:
                            parsed_data['cert_name'] = 'Seaman book for GMDSS'
                            logger.info(f"🔍 Fuzzy matched to: Seaman book for GMDSS")
                        else:
                            parsed_data['cert_name'] = 'Seaman Book for COC'
                            logger.info(f"🔍 Fuzzy matched to: Seaman Book for COC")
                    else:
                        # No fuzzy match - keep original but log it
                        logger.warning(f"⚠️ No standard match found for: {extracted_cert_name} - keeping original")
            
            # Add file content for later upload
            parsed_data['_file_content'] = base64.b64encode(file_content).decode('utf-8')
            parsed_data['_filename'] = file.filename
            parsed_data['_content_type'] = file.content_type
            parsed_data['_summary_text'] = document_summary  # Add summary for upload to Google Drive
            
            logger.info(f"✅ Certificate analysis successful: {parsed_data.get('cert_name', 'Unknown')}")
            
            return {
                "success": True,
                "message": "Crew certificate analyzed successfully",
                "analysis": parsed_data
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error analyzing crew certificate: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to analyze certificate: {str(e)}")
