"""
Certificate Multi-Upload Service
Migrated from backend-v1 for feature parity with AI analysis and GDrive integration
"""
import logging
import os
import json
import uuid
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorClient

from app.models.user import UserResponse, UserRole
from app.db.mongodb import mongo_db
from app.services.ai_config_service import AIConfigService
from app.repositories.ship_repository import ShipRepository
from app.repositories.certificate_repository import CertificateRepository

logger = logging.getLogger(__name__)

class CertificateMultiUploadService:
    """Service for handling multi-certificate uploads with AI analysis"""
    
    @staticmethod
    async def process_multi_upload(
        ship_id: str,
        files: List[UploadFile],
        current_user: UserResponse,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """
        Process multiple certificate file uploads with AI analysis
        
        This is the main orchestrator migrated from backend-v1
        """
        try:
            db = await get_db()
            
            # Step 1: Verify ship exists
            ship = await db.ships.find_one({"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            # Initialize results tracking
            results = []
            summary = {
                "total_files": len(files),
                "marine_certificates": 0,
                "non_marine_files": 0,
                "successfully_created": 0,
                "errors": 0,
                "certificates_created": [],
                "non_marine_files_list": [],
                "error_files": []
            }
            
            # Step 2: Get AI configuration
            try:
                ai_config_obj = await AIConfigService.get_ai_config(current_user)
                ai_config = {
                    "provider": ai_config_obj.provider,
                    "model": ai_config_obj.model,
                    "api_key": os.getenv("EMERGENT_LLM_KEY"),
                    "use_emergent_key": True
                }
                logger.info(f"🤖 Using AI: {ai_config['provider']} / {ai_config['model']}")
            except Exception as e:
                logger.error(f"AI configuration not found: {e}")
                raise HTTPException(
                    status_code=500, 
                    detail="AI configuration not found. Please configure AI settings first."
                )
            
            # Step 3: Get Google Drive configuration
            user_company_id = await CertificateMultiUploadService._resolve_company_id(current_user)
            
            gdrive_config_doc = None
            if user_company_id:
                gdrive_config_doc = await db.company_gdrive_config.find_one({"company_id": user_company_id})
                logger.info(f"Company Google Drive config for {user_company_id}: {'Found' if gdrive_config_doc else 'Not found'}")
            
            if not gdrive_config_doc:
                raise HTTPException(
                    status_code=500, 
                    detail="Google Drive not configured. Please configure Google Drive first."
                )
            
            # Step 4: Process each file
            for file in files:
                try:
                    file_result = await CertificateMultiUploadService._process_single_file(
                        file=file,
                        ship_id=ship_id,
                        ship=ship,
                        ai_config=ai_config,
                        gdrive_config_doc=gdrive_config_doc,
                        current_user=current_user,
                        db=db
                    )
                    
                    # Update summary based on result
                    if file_result["status"] == "success":
                        summary["successfully_created"] += 1
                        summary["marine_certificates"] += 1
                        summary["certificates_created"].append({
                            "filename": file.filename,
                            "cert_name": file_result.get("analysis", {}).get("cert_name", "Unknown"),
                            "cert_no": file_result.get("analysis", {}).get("cert_no", "N/A"),
                            "certificate_id": file_result.get("certificate", {}).get("id")
                        })
                    elif file_result["status"] == "error":
                        summary["errors"] += 1
                        summary["error_files"].append({
                            "filename": file.filename,
                            "error": file_result.get("message", "Unknown error")
                        })
                    
                    results.append(file_result)
                    
                except Exception as file_error:
                    logger.error(f"Error processing file {file.filename}: {file_error}")
                    summary["errors"] += 1
                    summary["error_files"].append({
                        "filename": file.filename,
                        "error": str(file_error)
                    })
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": str(file_error)
                    })
            
            return {
                "results": results,
                "summary": summary,
                "ship": {
                    "id": ship_id,
                    "name": ship.get("name", "Unknown Ship")
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Multi-cert upload error: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    @staticmethod
    async def _process_single_file(
        file: UploadFile,
        ship_id: str,
        ship: Dict[str, Any],
        ai_config: Dict[str, Any],
        gdrive_config_doc: Dict[str, Any],
        current_user: UserResponse,
        db: Any
    ) -> Dict[str, Any]:
        """Process a single certificate file"""
        
        # Read file content
        file_content = await file.read()
        
        # Check file size (50MB limit)
        if len(file_content) > 50 * 1024 * 1024:
            return {
                "filename": file.filename,
                "status": "error",
                "message": "File size exceeds 50MB limit"
            }
        
        # Check file type - support PDF, JPG, PNG
        supported_types = ["application/pdf", "image/jpeg", "image/jpg", "image/png"]
        if file.content_type not in supported_types:
            # Also check by file extension as backup
            file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
            supported_extensions = ['pdf', 'jpg', 'jpeg', 'png']
            
            if file_ext not in supported_extensions:
                return {
                    "filename": file.filename,
                    "status": "error",
                    "message": f"Unsupported file type. Supported: PDF, JPG, PNG. Got: {file.content_type}"
                }
        
        # Analyze document with AI
        analysis_result = await CertificateMultiUploadService._analyze_document_with_ai(
            file_content, file.filename, file.content_type, ai_config
        )
        
        logger.info(f"🔍 AI Analysis for {file.filename}:")
        logger.info(f"   Category: {analysis_result.get('category')}")
        
        # Check if it's a Marine Certificate
        is_marine_certificate = analysis_result.get("category") == "certificates"
        
        # AI EXTRACTION QUALITY CHECK
        extraction_quality = CertificateMultiUploadService._check_ai_extraction_quality(
            analysis_result, is_marine_certificate
        )
        
        logger.info(f"🤖 AI Extraction Quality for {file.filename}:")
        logger.info(f"   Confidence: {extraction_quality['confidence_score']}")
        logger.info(f"   Sufficient: {extraction_quality['sufficient']}")
        
        # If AI extraction is insufficient, request manual input
        if not extraction_quality['sufficient']:
            logger.warning(f"⚠️ AI extraction insufficient for {file.filename}")
            
            reasons = []
            if extraction_quality['confidence_score'] < 0.5:
                reasons.append(f"Low confidence ({extraction_quality['confidence_score']:.1f})")
            if extraction_quality['critical_extraction_rate'] < 0.67:
                reasons.append(f"Missing critical fields")
            if not is_marine_certificate:
                reasons.append(f"Not classified as certificate")
            
            reason_text = ", ".join(reasons)
            
            return {
                "filename": file.filename,
                "status": "requires_manual_input",
                "message": f"AI không thể trích xuất đủ thông tin từ '{file.filename}'. Vui lòng nhập thủ công.",
                "progress_message": f"AI không thể trích xuất đủ thông tin - Cần nhập thủ công ({reason_text})",
                "analysis": analysis_result,
                "extraction_quality": extraction_quality,
                "is_marine": is_marine_certificate,
                "requires_manual_input": True,
                "manual_input_reason": reason_text
            }
        
        # If not marine certificate
        if not is_marine_certificate:
            logger.info(f"⚠️ File {file.filename} not classified as marine certificate")
            return {
                "filename": file.filename,
                "status": "requires_manual_review",
                "message": f"System did not classify '{file.filename}' as a marine certificate.",
                "detected_category": analysis_result.get("category", "unknown"),
                "analysis": analysis_result,
                "is_marine": False
            }
        
        # IMO and Ship Name Validation
        extracted_imo = analysis_result.get('imo_number', '').strip()
        extracted_ship_name = analysis_result.get('ship_name', '').strip()
        current_ship_imo = ship.get('imo', '').strip()
        current_ship_name = ship.get('name', '').strip()
        validation_note = None
        progress_message = None
        
        logger.info(f"🔍 IMO/Ship Name Validation for {file.filename}:")
        logger.info(f"   Extracted IMO: '{extracted_imo}' vs Current: '{current_ship_imo}'")
        logger.info(f"   Extracted Ship: '{extracted_ship_name}' vs Current: '{current_ship_name}'")
        
        # Check IMO validation
        if extracted_imo and current_ship_imo:
            extracted_imo_clean = extracted_imo.replace(' ', '').replace('IMO', '').upper()
            current_ship_imo_clean = current_ship_imo.replace(' ', '').replace('IMO', '').upper()
            
            if extracted_imo_clean != current_ship_imo_clean:
                logger.warning(f"❌ IMO mismatch for {file.filename} - SKIPPING")
                return {
                    "filename": file.filename,
                    "status": "error",
                    "message": "Giấy chứng nhận của tàu khác, không thể lưu vào dữ liệu tàu hiện tại",
                    "progress_message": "Giấy chứng nhận của tàu khác, không thể lưu vào dữ liệu tàu hiện tại",
                    "analysis": analysis_result,
                    "is_marine": True,
                    "validation_error": {
                        "type": "imo_mismatch",
                        "extracted_imo": extracted_imo,
                        "current_ship_imo": current_ship_imo
                    }
                }
            
            # IMO matches - check ship name for note
            if extracted_ship_name and current_ship_name:
                if extracted_ship_name.upper() != current_ship_name.upper():
                    validation_note = "Chỉ để tham khảo"
                    progress_message = "Giấy chứng nhận này có tên tàu khác với tàu hiện tại, thông tin chỉ để tham khảo"
                    logger.info(f"⚠️ Ship name mismatch - adding reference note")
        
        # Check for duplicates
        duplicates = await CertificateMultiUploadService._check_certificate_duplicates(
            analysis_result, ship_id, db
        )
        
        if duplicates:
            existing_cert = duplicates[0]['certificate']
            return {
                "filename": file.filename,
                "status": "pending_duplicate_resolution",
                "message": f"Duplicate certificate detected: {existing_cert.get('cert_name', 'Unknown')}",
                "analysis": analysis_result,
                "duplicates": duplicates,
                "is_marine": True,
                "requires_user_choice": True,
                "duplicate_info": {
                    "existing_certificate": {
                        "cert_name": existing_cert.get('cert_name'),
                        "cert_no": existing_cert.get('cert_no'),
                        "issue_date": existing_cert.get('issue_date'),
                        "valid_date": existing_cert.get('valid_date')
                    },
                    "new_certificate": {
                        "cert_name": analysis_result.get('cert_name'),
                        "cert_no": analysis_result.get('cert_no'),
                        "issue_date": analysis_result.get('issue_date'),
                        "valid_date": analysis_result.get('valid_date')
                    }
                }
            }
        
        # Upload to Google Drive
        ship_name = ship.get("name", "Unknown_Ship")
        upload_result = await CertificateMultiUploadService._upload_to_gdrive(
            gdrive_config_doc, file_content, file.filename, ship_name, "Certificates"
        )
        
        # Create certificate record
        cert_result = await CertificateMultiUploadService._create_certificate_from_analysis(
            analysis_result, upload_result, current_user, ship_id, validation_note, db
        )
        
        # Determine final status
        if validation_note and progress_message:
            return {
                "filename": file.filename,
                "status": "success_with_reference_note",
                "analysis": analysis_result,
                "upload": upload_result,
                "certificate": cert_result,
                "is_marine": True,
                "progress_message": progress_message,
                "validation_note": validation_note
            }
        else:
            return {
                "filename": file.filename,
                "status": "success",
                "analysis": analysis_result,
                "upload": upload_result,
                "certificate": cert_result,
                "is_marine": True
            }
    
    @staticmethod
    async def _resolve_company_id(current_user: UserResponse) -> Optional[str]:
        """Resolve company name to UUID"""
        user_company = current_user.company if hasattr(current_user, 'company') and current_user.company else None
        
        if not user_company:
            return None
        
        # Check if it's already a UUID
        if len(user_company) > 10 and '-' in user_company:
            return user_company
        else:
            # Find company by name
            db = await get_db()
            company_doc = (
                await db.companies.find_one({"name_vn": user_company}) or
                await db.companies.find_one({"name_en": user_company}) or
                await db.companies.find_one({"name": user_company})
            )
            if company_doc:
                return company_doc.get("id")
            return None
    
    @staticmethod
    async def _analyze_document_with_ai(
        file_content: bytes, 
        filename: str, 
        content_type: str, 
        ai_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze document using AI - simplified version focusing on certificate extraction
        Uses the same logic as certificate_service.py
        """
        from app.services.certificate_service import CertificateService
        from app.utils.pdf_extractor import PDFExtractor
        
        try:
            # Extract text from PDF
            if content_type == "application/pdf":
                text = PDFExtractor.extract_text_from_bytes(file_content)
                if not text or len(text.strip()) < 50:
                    logger.warning(f"Insufficient text from {filename}")
                    return {"category": "unknown", "confidence": 0.0}
            else:
                # For images, would need OCR (not implemented yet)
                logger.warning(f"Image file {filename} - OCR not available")
                return {"category": "unknown", "confidence": 0.0}
            
            # Call AI for analysis using existing certificate service logic
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            from app.utils.ai_helper import AIHelper
            
            emergent_key = ai_config.get("api_key")
            provider = ai_config.get("provider", "google").lower()
            model = ai_config.get("model", "gemini-2.0-flash-exp")
            
            # Create comprehensive prompt for certificate extraction
            prompt = CertificateMultiUploadService._create_certificate_extraction_prompt(text)
            
            # Initialize LLM chat
            llm_chat = LlmChat(
                api_key=emergent_key,
                session_id="cert_multi_upload",
                system_message="You are an AI that analyzes maritime certificates."
            )
            
            # Set model based on provider
            if "gemini" in model.lower() or provider in ["google", "gemini", "emergent"]:
                llm_chat = llm_chat.with_model("gemini", model)
            elif provider == "openai" or "gpt" in model.lower():
                llm_chat = llm_chat.with_model("openai", model)
            elif provider == "anthropic" or "claude" in model.lower():
                llm_chat = llm_chat.with_model("anthropic", model)
            
            # Call AI
            ai_response = await llm_chat.send_message(UserMessage(text=prompt))
            
            # Parse response
            cert_data = AIHelper.parse_ai_response(ai_response)
            
            if not cert_data:
                return {"category": "unknown", "confidence": 0.0}
            
            # Add text_content for quality checks
            cert_data["text_content"] = text
            
            return cert_data
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {"category": "unknown", "confidence": 0.0, "error": str(e)}
    
    @staticmethod
    def _create_certificate_extraction_prompt(text: str) -> str:
        """Create prompt for certificate extraction with classification"""
        return f"""
Analyze this maritime document and extract certificate information.

Document Text:
{text[:8000]}

Extract and return ONLY a valid JSON object with these fields:

{{
  "category": "certificates or other (MUST be 'certificates' if this is a ship certificate)",
  "cert_name": "Certificate name",
  "cert_no": "Certificate number",
  "issue_date": "Issue date (DD/MM/YYYY format)",
  "valid_date": "Valid until date (DD/MM/YYYY format)",
  "last_endorse": "Last endorsement date (DD/MM/YYYY format)",
  "issued_by": "Issuing authority",
  "ship_name": "Ship name from certificate",
  "imo_number": "IMO number (7 digits)",
  "confidence": "high/medium/low",
  "text_content": "First 500 chars of extracted text"
}}

CLASSIFICATION RULES:
- If document contains "Certificate" + maritime context → category = "certificates"
- If document has IMO number + certificate keywords → category = "certificates"
- Otherwise → category = "other"

Return ONLY the JSON, no markdown blocks.
"""
    
    @staticmethod
    def _check_ai_extraction_quality(analysis_result: Dict[str, Any], is_marine_certificate: bool) -> Dict[str, Any]:
        """Check if AI extraction is sufficient for automatic processing"""
        
        confidence = analysis_result.get("confidence", "")
        
        # Convert confidence to numeric
        confidence_score = 0.0
        if isinstance(confidence, str):
            if confidence.lower() == 'high':
                confidence_score = 0.8
            elif confidence.lower() == 'medium':
                confidence_score = 0.6
            elif confidence.lower() == 'low':
                confidence_score = 0.3
            else:
                try:
                    confidence_score = float(confidence)
                except:
                    confidence_score = 0.0
        elif isinstance(confidence, (int, float)):
            confidence_score = float(confidence)
        
        # Check critical fields
        critical_fields = ['cert_name', 'cert_no', 'ship_name']
        extracted_critical_fields = 0
        
        for field in critical_fields:
            value = analysis_result.get(field, '').strip() if analysis_result.get(field) else ''
            if value and value.lower() not in ['unknown', 'null', 'none', '']:
                extracted_critical_fields += 1
        
        critical_extraction_rate = extracted_critical_fields / len(critical_fields)
        
        # Check all fields
        all_fields = ['ship_name', 'imo_number', 'cert_name', 'cert_no', 'issue_date', 'valid_date', 'issued_by']
        extracted_all_fields = 0
        
        for field in all_fields:
            value = analysis_result.get(field, '').strip() if analysis_result.get(field) else ''
            if value and value.lower() not in ['unknown', 'null', 'none', '']:
                extracted_all_fields += 1
        
        overall_extraction_rate = extracted_all_fields / len(all_fields)
        
        # Check text content quality
        text_content = analysis_result.get('text_content', '')
        text_quality_sufficient = len(text_content) >= 100 if text_content else False
        
        # Calculate confidence if not provided
        if confidence_score == 0.0 and not confidence:
            if critical_extraction_rate >= 0.67 and overall_extraction_rate >= 0.5:
                confidence_score = 0.8
            elif critical_extraction_rate >= 0.33 and overall_extraction_rate >= 0.3:
                confidence_score = 0.6
            else:
                confidence_score = 0.3
        
        # Determine if sufficient
        extraction_sufficient = (
            confidence_score >= 0.4 and
            critical_extraction_rate >= 0.67 and
            overall_extraction_rate >= 0.3 and
            text_quality_sufficient and
            is_marine_certificate
        )
        
        return {
            'sufficient': extraction_sufficient,
            'confidence_score': confidence_score,
            'critical_extraction_rate': critical_extraction_rate,
            'overall_extraction_rate': overall_extraction_rate,
            'text_quality_sufficient': text_quality_sufficient,
            'extracted_critical_fields': extracted_critical_fields,
            'total_critical_fields': len(critical_fields)
        }
    
    @staticmethod
    async def _check_certificate_duplicates(
        analysis_result: Dict[str, Any],
        ship_id: str,
        db: Any
    ) -> List[Dict[str, Any]]:
        """Check for duplicate certificates based on key fields"""
        
        cert_name = analysis_result.get('cert_name', '').strip()
        cert_no = analysis_result.get('cert_no', '').strip()
        issue_date = analysis_result.get('issue_date', '').strip()
        valid_date = analysis_result.get('valid_date', '').strip()
        last_endorse = analysis_result.get('last_endorse', '').strip()
        
        if not cert_name and not cert_no:
            return []
        
        # Build query
        query = {"ship_id": ship_id}
        
        # Match on cert_no if available (most specific)
        if cert_no:
            query["cert_no"] = cert_no
        
        # Find potential duplicates
        existing_certs = await db.certificates.find(query).to_list(length=10)
        
        if not existing_certs:
            return []
        
        # Check for exact matches
        duplicates = []
        for existing in existing_certs:
            # Calculate similarity
            similarity = 0.0
            matches = 0
            total = 0
            
            if cert_name:
                total += 1
                if existing.get('cert_name', '').strip().lower() == cert_name.lower():
                    matches += 1
            
            if cert_no:
                total += 1
                if existing.get('cert_no', '').strip() == cert_no:
                    matches += 1
            
            if issue_date:
                total += 1
                if existing.get('issue_date', '').strip() == issue_date:
                    matches += 1
            
            if valid_date:
                total += 1
                if existing.get('valid_date', '').strip() == valid_date:
                    matches += 1
            
            if total > 0:
                similarity = matches / total
            
            # Consider it a duplicate if similarity >= 50%
            if similarity >= 0.5:
                duplicates.append({
                    'certificate': existing,
                    'similarity': similarity
                })
        
        return duplicates
    
    @staticmethod
    async def _upload_to_gdrive(
        gdrive_config: Dict[str, Any],
        file_content: bytes,
        filename: str,
        ship_name: str,
        folder: str
    ) -> Dict[str, Any]:
        """Upload file to Google Drive"""
        try:
            # Import GDrive helper
            from app.utils.gdrive_helper import upload_file_to_ship_folder
            
            result = await upload_file_to_ship_folder(
                gdrive_config, file_content, filename, ship_name, folder
            )
            
            if result.get("success"):
                logger.info(f"✅ Uploaded {filename} to GDrive")
                return result
            else:
                logger.warning(f"⚠️ GDrive upload failed for {filename}: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Google Drive upload failed"),
                    "folder_path": f"{ship_name}/{folder}"
                }
                
        except Exception as e:
            logger.error(f"❌ GDrive upload error: {e}")
            return {
                "success": False,
                "error": str(e),
                "folder_path": f"{ship_name}/{folder}"
            }
    
    @staticmethod
    async def _create_certificate_from_analysis(
        analysis_result: Dict[str, Any],
        upload_result: Dict[str, Any],
        current_user: UserResponse,
        ship_id: str,
        validation_note: Optional[str],
        db: Any
    ) -> Dict[str, Any]:
        """Create certificate record from AI analysis"""
        try:
            cert_id = str(uuid.uuid4())
            
            # Build certificate document
            cert_doc = {
                "id": cert_id,
                "ship_id": ship_id,
                "cert_name": analysis_result.get("cert_name", ""),
                "cert_no": analysis_result.get("cert_no", ""),
                "cert_type": analysis_result.get("cert_type", "Full Term"),
                "issue_date": analysis_result.get("issue_date", ""),
                "valid_date": analysis_result.get("valid_date", ""),
                "last_endorse": analysis_result.get("last_endorse", ""),
                "next_survey": analysis_result.get("next_survey", ""),
                "next_survey_type": analysis_result.get("next_survey_type", ""),
                "issued_by": analysis_result.get("issued_by", ""),
                "notes": validation_note if validation_note else analysis_result.get("notes", ""),
                "category": "certificates",
                "sensitivity_level": "internal",
                "created_by": current_user.email,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "google_drive_file_id": upload_result.get("file_id"),
                "google_drive_file_url": upload_result.get("file_url"),
                "file_path": upload_result.get("file_path")
            }
            
            # Insert into database
            await db.certificates.insert_one(cert_doc)
            
            logger.info(f"✅ Created certificate {cert_id}")
            
            return {
                "id": cert_id,
                "success": True,
                "cert_name": cert_doc["cert_name"],
                "cert_no": cert_doc["cert_no"]
            }
            
        except Exception as e:
            logger.error(f"❌ Certificate creation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
