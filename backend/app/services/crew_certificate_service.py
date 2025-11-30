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
        # Verify crew exists
        crew = await CrewRepository.find_by_id(cert_data.crew_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Crew member not found")
        
        # Create certificate document
        cert_dict = cert_data.dict()
        cert_dict["id"] = str(uuid.uuid4())
        cert_dict["created_at"] = datetime.now(timezone.utc)
        cert_dict["created_by"] = current_user.username
        
        await CrewCertificateRepository.create(cert_dict)
        
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
                
                # TODO: Delete Google Drive files if configured
                # For now, just delete from database
                
                # Delete from database
                await mongo_db.delete("crew_certificates", {"id": cert_id})
                deleted_count += 1
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
        """Analyze crew certificate file using Document AI + LLM extraction"""
        import base64
        import os
        from app.utils.document_ai_helper import DocumentAIHelper
        from app.utils.ai_helper import AIHelper
        from app.services.ai_config_service import AIConfigService
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
            
            # Step 1: Call Document AI for OCR
            doc_ai_helper = DocumentAIHelper()
            doc_ai_result = await doc_ai_helper.process_document(file_content, file.content_type)
            
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
            
            # Create AI prompt for crew certificate field extraction
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

=== CERTIFICATE TYPES ===
Common maritime certificates:
- CERTIFICATE OF COMPETENCY (COC)
- CERTIFICATE OF ENDORSEMENT (COE)
- STCW certificates (Basic Safety, Advanced Fire Fighting, etc.)
- Medical Certificate (Medical Fitness Certificate)
- Passport
- Seaman Book / Discharge Book
- Flag State Endorsement
- GMDSS certificates
- Tanker certificates (Oil/Chemical/Gas)

=== FIELDS TO EXTRACT ===
{{
  "cert_name": "",           // Full certificate name (e.g., "CERTIFICATE OF COMPETENCY")
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
            
            ai_response = await AIHelper.get_completion(
                prompt=prompt,
                provider=provider,
                model=model,
                api_key=emergent_key,
                temperature=0.0,
                response_format="json"
            )
            
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
            try:
                parsed_data = json.loads(ai_response) if isinstance(ai_response, str) else ai_response
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse AI response as JSON: {e}")
                return {
                    "success": False,
                    "message": "Failed to parse AI response",
                    "analysis": None
                }
            
            # Add file content for later upload
            parsed_data['_file_content'] = base64.b64encode(file_content).decode('utf-8')
            parsed_data['_filename'] = file.filename
            parsed_data['_content_type'] = file.content_type
            
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
