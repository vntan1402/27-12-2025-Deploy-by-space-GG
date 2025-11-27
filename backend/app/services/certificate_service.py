import uuid
import logging
import os
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile, BackgroundTasks

from app.models.certificate import (
    CertificateCreate, 
    CertificateUpdate, 
    CertificateResponse,
    BulkDeleteRequest
)
from app.models.user import UserResponse
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.ship_repository import ShipRepository
from app.utils.pdf_processor import PDFProcessor
from app.utils.ai_helper import AIHelper
from app.utils.certificate_abbreviation import generate_certificate_abbreviation
from app.utils.issued_by_abbreviation import generate_organization_abbreviation
from app.utils.background_tasks import delete_file_background

logger = logging.getLogger(__name__)

class CertificateService:
    """Business logic for certificate management"""
    
    @staticmethod
    async def get_certificates(ship_id: Optional[str], current_user: UserResponse) -> List[CertificateResponse]:
        """Get certificates, optionally filtered by ship"""
        certificates = await CertificateRepository.find_all(ship_id=ship_id)
        
        # TODO: Add access control based on user's company
        
        # Enhance certificates with abbreviations
        enhanced_certs = []
        for cert in certificates:
            # Generate certificate abbreviation if not present
            if not cert.get("cert_abbreviation") and cert.get("cert_name"):
                cert["cert_abbreviation"] = await generate_certificate_abbreviation(cert.get("cert_name"))
            
            # Generate organization abbreviation for issued_by if not present
            if not cert.get("issued_by_abbreviation") and cert.get("issued_by"):
                cert["issued_by_abbreviation"] = generate_organization_abbreviation(cert.get("issued_by"))
            
            enhanced_certs.append(CertificateResponse(**cert))
        
        return enhanced_certs
    
    @staticmethod
    async def get_certificate_by_id(cert_id: str, current_user: UserResponse) -> CertificateResponse:
        """Get certificate by ID"""
        cert = await CertificateRepository.find_by_id(cert_id)
        
        if not cert:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # TODO: Check access permission
        
        # Generate certificate abbreviation if not present
        if not cert.get("cert_abbreviation") and cert.get("cert_name"):
            cert["cert_abbreviation"] = await generate_certificate_abbreviation(cert.get("cert_name"))
        
        # Generate organization abbreviation for issued_by if not present
        if not cert.get("issued_by_abbreviation") and cert.get("issued_by"):
            cert["issued_by_abbreviation"] = generate_organization_abbreviation(cert.get("issued_by"))
        
        return CertificateResponse(**cert)
    
    @staticmethod
    async def create_certificate(cert_data: CertificateCreate, current_user: UserResponse) -> CertificateResponse:
        """Create new certificate"""
        # Verify ship exists
        ship = await ShipRepository.find_by_id(cert_data.ship_id)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        # Create certificate document
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
        
        # BUSINESS RULE: Interim certificates don't have next survey
        if cert_dict.get("cert_type") == "Interim":
            cert_dict["next_survey"] = None
            cert_dict["next_survey_display"] = "N/A"
            cert_dict["next_survey_type"] = "N/A"
            logger.info("✅ Set next_survey to N/A for Interim certificate")
        
        await CertificateRepository.create(cert_dict)
        
        logger.info(f"✅ Certificate created: {cert_dict['cert_name']}")
        
        return CertificateResponse(**cert_dict)
    
    @staticmethod
    async def update_certificate(cert_id: str, cert_data: CertificateUpdate, current_user: UserResponse) -> CertificateResponse:
        """Update certificate"""
        cert = await CertificateRepository.find_by_id(cert_id)
        if not cert:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Prepare update data
        update_data = cert_data.dict(exclude_unset=True)
        
        # DEBUG: Log what data we're receiving
        logger.info(f"🔍 DEBUG - Updating certificate {cert_id}")
        logger.info(f"🔍 DEBUG - Raw cert_data: {cert_data}")
        logger.info(f"🔍 DEBUG - update_data after exclude_unset: {update_data}")
        logger.info(f"🔍 DEBUG - next_survey in update_data: {update_data.get('next_survey')}")
        
        # BUSINESS RULE: Check if changing to Interim type
        if "cert_type" in update_data and update_data["cert_type"] == "Interim":
            # Force next_survey fields to N/A for Interim certificates
            update_data["next_survey"] = None
            update_data["next_survey_display"] = "N/A"
            update_data["next_survey_type"] = "N/A"
            logger.info("✅ Changed to Interim: Set next_survey to N/A")
        
        # BUSINESS RULE: For Interim certificates, NEVER calculate next_survey
        # Interim certificates are temporary and don't have next survey dates
        current_cert_type = cert.get("cert_type")
        is_interim = current_cert_type == "Interim" or update_data.get("cert_type") == "Interim"
        
        if is_interim:
            # Override any next_survey updates with N/A
            if "next_survey" in update_data:
                update_data["next_survey"] = None
                update_data["next_survey_display"] = "N/A"
                update_data["next_survey_type"] = "N/A"
                logger.info("⚠️ Prevented next_survey update for Interim certificate (forced to N/A)")
        else:
            # Only process next_survey updates for non-Interim certificates
            # Sync next_survey_display when next_survey is manually updated
            # next_survey_display is the formatted display value shown in tables (with ±3M annotation)
            # When user manually updates next_survey, we must sync next_survey_display
            if "next_survey" in update_data and update_data["next_survey"]:
                from datetime import datetime
                # Format: dd/mm/yyyy (±3M) - preserve existing annotation if any, or add default
                next_survey_date = update_data["next_survey"]
                if isinstance(next_survey_date, datetime):
                    formatted_date = next_survey_date.strftime("%d/%m/%Y")
                    # Add default annotation (±3M) for Full Term certificates
                    if cert.get("cert_type") == "Full Term" or update_data.get("cert_type") == "Full Term":
                        update_data["next_survey_display"] = f"{formatted_date} (±3M)"
                    else:
                        update_data["next_survey_display"] = formatted_date
                    logger.info(f"🔄 Updated next_survey_display to: {update_data['next_survey_display']}")
            elif "next_survey" in update_data and not update_data["next_survey"]:
                # If next_survey is cleared, also clear next_survey_display
                update_data["next_survey_display"] = None
                logger.info("🔄 Cleared next_survey_display (next_survey was cleared)")
        
        # CRITICAL FIX: Auto-set has_notes flag when notes field is updated
        # This ensures the "*" indicator appears in the table when notes are saved
        if "notes" in update_data:
            if update_data["notes"] and update_data["notes"].strip():
                # Notes has content - set flag to True
                update_data["has_notes"] = True
                logger.info("✅ Set has_notes = True (notes provided)")
            else:
                # Notes is empty or None - set flag to False
                update_data["has_notes"] = False
                logger.info("✅ Set has_notes = False (notes cleared)")
        
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
        
        # Regenerate organization abbreviation ONLY if issued_by is being updated AND user didn't provide abbreviation
        if update_data.get("issued_by") and not update_data.get("issued_by_abbreviation"):
            update_data["issued_by_abbreviation"] = generate_organization_abbreviation(update_data.get("issued_by"))
            logger.info(f"✅ Regenerated issued_by abbreviation: '{update_data['issued_by']}' → '{update_data['issued_by_abbreviation']}'")
        
        if update_data:
            logger.info(f"🔍 DEBUG - About to save to DB: {update_data}")
            await CertificateRepository.update(cert_id, update_data)
        
        # Get updated certificate
        updated_cert = await CertificateRepository.find_by_id(cert_id)
        logger.info(f"🔍 DEBUG - Certificate after update from DB: next_survey = {updated_cert.get('next_survey')}")
        
        # Generate certificate abbreviation if not present
        if not updated_cert.get("cert_abbreviation") and updated_cert.get("cert_name"):
            updated_cert["cert_abbreviation"] = await generate_certificate_abbreviation(updated_cert.get("cert_name"))
        
        # Generate organization abbreviation if not present
        if not updated_cert.get("issued_by_abbreviation") and updated_cert.get("issued_by"):
            updated_cert["issued_by_abbreviation"] = generate_organization_abbreviation(updated_cert.get("issued_by"))
        
        logger.info(f"✅ Certificate updated: {cert_id}")
        
        return CertificateResponse(**updated_cert)
    
    @staticmethod
    async def delete_certificate(
        cert_id: str, 
        current_user: UserResponse,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> dict:
        """Delete certificate and schedule Google Drive file deletion in background"""
        cert = await CertificateRepository.find_by_id(cert_id)
        if not cert:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Extract file info before deleting from DB
        google_drive_file_id = cert.get("google_drive_file_id")
        summary_file_id = cert.get("summary_file_id")  # ⭐ NEW: Get summary file ID
        cert_name = cert.get("cert_name", "Unknown")
        
        # Delete certificate from database immediately
        await CertificateRepository.delete(cert_id)
        logger.info(f"✅ Certificate deleted from DB: {cert_id} ({cert_name})")
        
        # Schedule Google Drive file deletion in background if file exists
        if google_drive_file_id and background_tasks:
            # Get ship to find company_id
            ship_id = cert.get("ship_id")
            if ship_id:
                ship = await ShipRepository.find_by_id(ship_id)
                if ship:
                    company_id = ship.get("company")
                    if company_id:
                        from app.services.gdrive_service import GDriveService
                        
                        # Schedule background deletion for main certificate file
                        background_tasks.add_task(
                            delete_file_background,
                            google_drive_file_id,
                            company_id,
                            "certificate",
                            cert_name,
                            GDriveService
                        )
                        logger.info(f"📋 Scheduled background deletion for certificate file: {google_drive_file_id}")
                        
                        # ⭐ NEW: Schedule background deletion for summary file
                        if summary_file_id:
                            background_tasks.add_task(
                                delete_file_background,
                                summary_file_id,
                                company_id,
                                "certificate_summary",
                                f"{cert_name} (Summary)",
                                GDriveService
                            )
                            logger.info(f"📋 Scheduled background deletion for summary file: {summary_file_id}")
                        
                        return {
                            "success": True,
                            "message": "Certificate deleted successfully. File deletion in progress...",
                            "certificate_id": cert_id,
                            "background_deletion": True,
                            "files_deleted": 2 if summary_file_id else 1  # ⭐ NEW
                        }
        
        return {
            "success": True,
            "message": "Certificate deleted successfully",
            "certificate_id": cert_id,
            "background_deletion": False
        }
    
    @staticmethod
    async def bulk_delete_certificates(
        request: BulkDeleteRequest, 
        current_user: UserResponse,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> dict:
        """Bulk delete certificates and schedule Google Drive files deletion in background"""
        from app.services.gdrive_service import GDriveService
        
        deleted_count = 0
        files_scheduled = 0
        errors = []
        
        for cert_id in request.certificate_ids:
            try:
                cert = await CertificateRepository.find_by_id(cert_id)
                if not cert:
                    errors.append(f"Certificate {cert_id} not found")
                    continue
                
                # Extract file info before deletion
                google_drive_file_id = cert.get("google_drive_file_id")
                cert_name = cert.get("cert_name", "Unknown")
                
                # Delete from database immediately
                await CertificateRepository.delete(cert_id)
                deleted_count += 1
                logger.info(f"✅ Certificate deleted from DB: {cert_id} ({cert_name})")
                
                # Schedule Google Drive file deletion in background
                if google_drive_file_id and background_tasks:
                    ship_id = cert.get("ship_id")
                    if ship_id:
                        ship = await ShipRepository.find_by_id(ship_id)
                        if ship:
                            company_id = ship.get("company")
                            if company_id:
                                background_tasks.add_task(
                                    delete_file_background,
                                    google_drive_file_id,
                                    company_id,
                                    "certificate",
                                    cert_name,
                                    GDriveService
                                )
                                files_scheduled += 1
                                logger.info(f"📋 Scheduled background deletion for file: {google_drive_file_id}")
                
            except Exception as e:
                errors.append(f"Error deleting certificate {cert_id}: {str(e)}")
                logger.error(f"❌ Error deleting certificate {cert_id}: {e}")
        
        message = f"Deleted {deleted_count} certificate(s)"
        if files_scheduled > 0:
            message += f". {files_scheduled} file(s) deletion in progress..."
        if errors:
            message += f", {len(errors)} error(s)"
        
        logger.info(f"✅ Bulk delete complete: {deleted_count} certificates, {files_scheduled} files scheduled for deletion")
        
        return {
            "success": True,
            "message": message,
            "deleted_count": deleted_count,
            "files_scheduled": files_scheduled,
            "errors": errors if errors else None,
            "partial_success": len(errors) > 0 and deleted_count > 0
        }
    
    @staticmethod
    async def check_duplicate(ship_id: str, cert_name: str, cert_no: Optional[str], current_user: UserResponse) -> dict:
        """Check if certificate is duplicate"""
        existing = await CertificateRepository.check_duplicate(ship_id, cert_name, cert_no)
        
        return {
            "is_duplicate": existing is not None,
            "existing_certificate": CertificateResponse(**existing).dict() if existing else None
        }
    
    @staticmethod
    async def analyze_certificate_file(file: UploadFile, ship_id: Optional[str], current_user: UserResponse) -> dict:
        """Analyze certificate file using AI with EMERGENT_LLM_KEY"""
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Validate file size (10MB limit)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
        
        # Read file content
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file received")
        
        logger.info(f"📄 Analyzing certificate file: {file.filename} ({len(file_content)} bytes)")
        
        try:
            # Step 1: Extract text from PDF
            logger.info("🔄 Extracting text from PDF...")
            text = await PDFProcessor.process_pdf(file_content, use_ocr_fallback=True)
            
            if not text or len(text) < 50:
                logger.warning("⚠️ Insufficient text extracted from PDF")
                # Return fallback data for manual input
                fallback_data = {
                    "ship_name": "",
                    "imo_number": "",
                    "flag": "",
                    "class_society": "",
                    "gross_tonnage": "",
                    "deadweight": "",
                    "built_year": "",
                    "ship_owner": "",
                    "delivery_date": "",
                    "ship_type": "",
                    "confidence": 0.0,
                    "processing_notes": [f"Could not extract text from {file.filename}. Manual input required."],
                    "error": "Text extraction failed"
                }
                return {
                    "success": True,
                    "message": "Could not extract text from PDF - please enter ship information manually",
                    "analysis": fallback_data,
                    "confidence": 0.0
                }
            
            logger.info(f"✅ Extracted {len(text)} characters from PDF")
            
            # Step 2: Get AI configuration
            from app.services.ai_config_service import AIConfigService
            try:
                ai_config = await AIConfigService.get_ai_config(current_user)
                provider = ai_config.provider
                model = ai_config.model
                logger.info(f"🤖 Using AI: {provider} / {model}")
            except Exception as e:
                logger.warning(f"Could not get AI config, using defaults: {e}")
                provider = "google"
                model = "gemini-2.0-flash-exp"  # Match backend-v1 default
            
            # Step 3: Call AI for analysis
            logger.info("🤖 Calling AI for certificate analysis...")
            
            try:
                # Get EMERGENT_LLM_KEY
                emergent_key = os.getenv("EMERGENT_LLM_KEY", "sk-emergent-eEe35Fb1b449940199")
                
                if not emergent_key:
                    raise HTTPException(status_code=500, detail="AI key not configured")
                
                # Import emergentintegrations
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                
                # Create prompt
                prompt = AIHelper.create_certificate_analysis_prompt(text, ship_id)
                
                # Initialize LLM chat
                llm_chat = LlmChat(
                    api_key=emergent_key,
                    session_id="cert_analysis",
                    system_message="You are an AI assistant that analyzes maritime certificates."
                )
                
                # Set provider and model correctly
                # Map provider to emergentintegrations format
                
                # Check if model is Gemini (regardless of provider value)
                if "gemini" in model.lower() or provider.lower() in ["google", "gemini", "emergent"]:
                    # For Gemini models with Emergent key
                    # Use the model name as-is from AI config (backend-v1 behavior)
                    # emergentintegrations will handle the model name validation
                    actual_model = model
                    
                    llm_chat = llm_chat.with_model("gemini", actual_model)
                    logger.info(f"🔄 Using Gemini model: {actual_model} (provider: {provider})")
                elif provider.lower() == "openai" or "gpt" in model.lower():
                    llm_chat = llm_chat.with_model("openai", model)
                    logger.info(f"🔄 Using OpenAI model: {model}")
                elif provider.lower() == "anthropic" or "claude" in model.lower():
                    llm_chat = llm_chat.with_model("anthropic", model)
                    logger.info(f"🔄 Using Anthropic model: {model}")
                else:
                    # Default: try to use as-is
                    logger.warning(f"⚠️ Unknown provider: {provider}, trying model as-is: {model}")
                    llm_chat = llm_chat.with_model("gemini", "gemini-1.5-flash")  # Safe fallback
                
                # Call AI
                ai_response = await llm_chat.send_message(UserMessage(text=prompt))
                
                # Extract response text (ai_response is already the text content)
                response_text = ai_response
                
                logger.info(f"✅ AI response received: {len(response_text)} characters")
                logger.info(f"🔍 AI Response Preview: {response_text[:500]}")
                
                # Step 4: Parse AI response
                cert_data = AIHelper.parse_ai_response(response_text)
                
                logger.info(f"🔍 Parsed fields count: {len(cert_data) if cert_data else 0}")
                logger.info(f"🔍 Parsed fields: {list(cert_data.keys()) if cert_data else []}")
                
                if not cert_data:
                    logger.error("❌ Failed to parse AI response")
                    return {
                        "success": False,
                        "message": "AI analysis failed - could not parse response",
                        "analysis": None
                    }
                
                # Step 5: Validate and clean data
                validated_data = AIHelper.validate_certificate_data(cert_data)
                
                # Step 6: Calculate confidence score
                confidence = AIHelper.calculate_confidence_score(validated_data, len(text))
                
                logger.info(f"✅ Certificate analyzed successfully (confidence: {confidence:.2f})")
                
                return {
                    "success": True,
                    "message": "Certificate analyzed successfully",
                    "analysis": validated_data,
                    "confidence": confidence,
                    "text_length": len(text)
                }
                
            except Exception as ai_error:
                logger.error(f"❌ AI analysis error: {ai_error}")
                # Return fallback data - empty fields for manual input (like backend-v1)
                fallback_data = {
                    "ship_name": "",
                    "imo_number": "",
                    "flag": "",
                    "class_society": "",
                    "gross_tonnage": "",
                    "deadweight": "",
                    "built_year": "",
                    "ship_owner": "",
                    "delivery_date": "",
                    "ship_type": "",
                    "last_docking": "",
                    "last_docking_2": "",
                    "next_docking": "",
                    "special_survey_from_date": "",
                    "special_survey_to_date": "",
                    "confidence": 0.0,
                    "processing_notes": [f"AI analysis failed for {file.filename}. Manual input required."],
                    "error": f"AI analysis failed: {str(ai_error)}"
                }
                
                return {
                    "success": True,  # Return success=True to allow manual input (backend-v1 behavior)
                    "message": "Auto-fill failed - please enter ship information manually",
                    "analysis": fallback_data,
                    "confidence": 0.0
                }
        
        except Exception as e:
            logger.error(f"❌ Certificate analysis error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze certificate: {str(e)}"
            )
    
    @staticmethod
    async def auto_rename_certificate_file(certificate_id: str, current_user: UserResponse) -> dict:
        """
        Auto rename certificate file on Google Drive using naming convention:
        {Ship Name}_{Cert Type}_{Cert Abbreviation}_{Issue Date}.pdf
        
        Priority for Certificate Abbreviation:
        1. User-defined mapping (from abbreviation_mappings collection)
        2. Database cert_abbreviation field
        3. Auto-generated abbreviation
        """
        from app.db.mongodb import mongo_db
        from app.repositories.ship_repository import ShipRepository
        from app.utils.certificate_abbreviation import generate_certificate_abbreviation
        from datetime import datetime
        import re
        import aiohttp
        
        # Get certificate data
        cert = await CertificateRepository.find_by_id(certificate_id)
        if not cert:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Check if certificate has Google Drive file
        file_id = cert.get("google_drive_file_id")
        if not file_id:
            raise HTTPException(status_code=400, detail="Certificate has no associated Google Drive file")
        
        # Get ship data
        ship = await ShipRepository.find_by_id(cert.get("ship_id"))
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found for certificate")
        
        # Build new filename components
        ship_name = ship.get("name", "Unknown Ship")
        cert_type = cert.get("cert_type", "Unknown Type")
        cert_name = cert.get("cert_name", "Unknown Certificate")
        cert_abbreviation = cert.get("cert_abbreviation", "")
        issue_date = cert.get("issue_date")
        
        # ========== PRIORITY LOGIC FOR ABBREVIATION ==========
        # Priority 1: Check user-defined abbreviation mappings FIRST
        user_defined_abbr = await mongo_db.database.certificate_abbreviation_mappings.find_one(
            {"cert_name": cert_name}
        )
        
        if user_defined_abbr and user_defined_abbr.get("abbreviation"):
            final_abbreviation = user_defined_abbr.get("abbreviation")
            logger.info(f"🔄 AUTO-RENAME - PRIORITY 1: Using user-defined mapping '{cert_name}' → '{final_abbreviation}'")
        elif cert_abbreviation:
            # Priority 2: Use database cert_abbreviation
            final_abbreviation = cert_abbreviation
            logger.info(f"🔄 AUTO-RENAME - PRIORITY 2: Using database abbreviation '{final_abbreviation}'")
        else:
            # Priority 3: Generate abbreviation as fallback
            final_abbreviation = await generate_certificate_abbreviation(cert_name)
            logger.info(f"🔄 AUTO-RENAME - PRIORITY 3: Generated abbreviation '{cert_name}' → '{final_abbreviation}'")
        
        cert_identifier = final_abbreviation
        
        # Format issue date
        date_str = "NoDate"
        if issue_date:
            try:
                if isinstance(issue_date, str):
                    date_obj = datetime.fromisoformat(issue_date.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%Y%m%d")
                elif isinstance(issue_date, datetime):
                    date_str = issue_date.strftime("%Y%m%d")
            except Exception as e:
                logger.warning(f"⚠️ Could not parse issue date: {e}")
                date_str = "NoDate"
        
        # Build new filename: Ship name_Cert type_Cert identifier_Issue date.pdf
        original_filename = cert.get("file_name", "")
        file_extension = ".pdf"  # Default
        if original_filename and "." in original_filename:
            file_extension = "." + original_filename.split(".")[-1]
        
        new_filename = f"{ship_name}_{cert_type}_{cert_identifier}_{date_str}{file_extension}"
        
        # Clean up filename: Remove special characters but KEEP spaces and underscores
        # Only allow: letters, numbers, spaces, underscores, hyphens, and dots
        new_filename = re.sub(r'[^a-zA-Z0-9 ._-]', '', new_filename)
        new_filename = re.sub(r'\s+', ' ', new_filename)  # Remove multiple spaces
        
        # Get company ID from user
        company_id = current_user.company
        
        # Get company Google Drive configuration
        gdrive_config = await mongo_db.database.company_gdrive_config.find_one(
            {"company_id": company_id}
        )
        
        if not gdrive_config:
            raise HTTPException(status_code=404, detail="Google Drive not configured for this company")
        
        # Get Apps Script URL
        apps_script_url = gdrive_config.get("web_app_url") or gdrive_config.get("apps_script_url")
        if not apps_script_url:
            raise HTTPException(status_code=400, detail="Apps Script URL not configured")
        
        # Check if Apps Script supports rename_file action
        logger.info("🔍 Checking Apps Script capabilities for auto-rename functionality...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test payload to get available actions
                async with session.post(
                    apps_script_url,
                    json={},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        test_result = await response.json()
                        available_actions = test_result.get("available_actions", [])
                        supported_actions = test_result.get("supported_actions", [])
                        all_actions = available_actions + supported_actions
                        
                        logger.info(f"📋 Apps Script available actions: {all_actions}")
                        
                        if "rename_file" not in all_actions:
                            logger.warning("⚠️ Apps Script does not support 'rename_file' action")
                            raise HTTPException(
                                status_code=501,
                                detail=f"Auto-rename feature not yet supported by Google Drive integration. Suggested filename: {new_filename}"
                            )
                        
                        logger.info("✅ Apps Script supports 'rename_file' action")
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"⚠️ Could not check Apps Script capabilities: {e}")
            # Continue anyway and let the actual rename call fail if needed
        
        # Call Apps Script to rename file
        payload = {
            "action": "rename_file",
            "file_id": file_id,
            "new_name": new_filename
        }
        
        logger.info(f"🔄 Auto-renaming certificate file {file_id} to '{new_filename}' for certificate {certificate_id}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    apps_script_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get("success"):
                            # Update certificate record with new filename
                            await CertificateRepository.update(
                                certificate_id,
                                {"file_name": new_filename}
                            )
                            
                            logger.info(f"✅ Successfully auto-renamed certificate file to '{new_filename}'")
                            
                            return {
                                "success": True,
                                "message": "Certificate file renamed successfully",
                                "certificate_id": certificate_id,
                                "file_id": file_id,
                                "old_name": result.get("old_name"),
                                "new_name": new_filename,
                                "naming_convention": {
                                    "ship_name": ship_name,
                                    "cert_type": cert_type,
                                    "cert_identifier": cert_identifier,
                                    "issue_date": date_str
                                },
                                "renamed_timestamp": result.get("renamed_timestamp")
                            }
                        else:
                            error_msg = result.get("error", "Unknown error occurred")
                            logger.error(f"❌ Apps Script auto-rename failed: {error_msg}")
                            raise HTTPException(
                                status_code=500,
                                detail=f"Failed to auto-rename file: {error_msg}"
                            )
                    else:
                        logger.error(f"❌ Apps Script request failed with status {response.status}")
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=500,
                            detail=f"Google Drive API request failed: {response.status} - {error_text}"
                        )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error calling Apps Script: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to communicate with Google Drive: {str(e)}"
            )