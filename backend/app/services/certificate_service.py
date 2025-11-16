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
        
        # CRITICAL FIX: If next_survey is being updated, update next_survey_display to match
        # next_survey_display is the formatted display value shown in tables (with ±3M annotation)
        # When user manually updates next_survey, we must sync next_survey_display
        if "next_survey" in update_data and update_data["next_survey"]:
            from datetime import datetime
            # Format: dd/mm/yyyy (±3M) - preserve existing annotation if any, or add default
            next_survey_date = update_data["next_survey"]
            if isinstance(next_survey_date, datetime):
                formatted_date = next_survey_date.strftime("%d/%m/%Y")
                # Add default annotation (±3M) for Full Term certificates
                if cert.get("cert_type") == "Full Term":
                    update_data["next_survey_display"] = f"{formatted_date} (±3M)"
                else:
                    update_data["next_survey_display"] = formatted_date
                logger.info(f"🔄 Updated next_survey_display to: {update_data['next_survey_display']}")
        elif "next_survey" in update_data and not update_data["next_survey"]:
            # If next_survey is cleared, also clear next_survey_display
            update_data["next_survey_display"] = None
            logger.info(f"🔄 Cleared next_survey_display (next_survey was cleared)")
        
        # CRITICAL FIX: Auto-set has_notes flag when notes field is updated
        # This ensures the "*" indicator appears in the table when notes are saved
        if "notes" in update_data:
            if update_data["notes"] and update_data["notes"].strip():
                # Notes has content - set flag to True
                update_data["has_notes"] = True
                logger.info(f"✅ Set has_notes = True (notes provided)")
            else:
                # Notes is empty or None - set flag to False
                update_data["has_notes"] = False
                logger.info(f"✅ Set has_notes = False (notes cleared)")
        
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
                        
                        # Schedule background deletion with retry
                        background_tasks.add_task(
                            delete_file_background,
                            google_drive_file_id,
                            company_id,
                            "certificate",
                            cert_name,
                            GDriveService
                        )
                        logger.info(f"📋 Scheduled background deletion for certificate file: {google_drive_file_id}")
                        
                        return {
                            "success": True,
                            "message": "Certificate deleted successfully. File deletion in progress...",
                            "certificate_id": cert_id,
                            "background_deletion": True
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