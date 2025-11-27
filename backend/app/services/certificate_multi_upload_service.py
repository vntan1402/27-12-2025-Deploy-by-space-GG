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
            db = mongo_db.database
            
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
        
        # ⭐ NEW: Analyze document with advanced AI pipeline (Document AI + OCR)
        analysis_result = await CertificateMultiUploadService._analyze_document_with_ai(
            file_content, 
            file.filename, 
            file.content_type, 
            ai_config,
            ship_id,
            current_user
        )
        
        # Check if analysis was successful
        if not analysis_result.get("success"):
            error_msg = analysis_result.get("message", "Analysis failed")
            return {
                "filename": file.filename,
                "status": "error",
                "message": error_msg
            }
        
        # Extract components from new analysis result
        extracted_info = analysis_result.get("extracted_info", {})
        summary_text = analysis_result.get("summary_text", "")  # ⭐ NEW: Document AI text
        validation_warning = analysis_result.get("validation_warning")
        duplicate_warning = analysis_result.get("duplicate_warning")
        
        logger.info(f"✅ AI Analysis successful for {file.filename}")
        logger.info(f"   Summary text: {len(summary_text)} characters")
        logger.info(f"   Extracted fields: {list(extracted_info.keys())}")
        
        # Check for validation warnings (IMO mismatch - BLOCKING)
        if validation_warning and validation_warning.get("is_blocking"):
            logger.error(f"❌ Blocking validation error for {file.filename}")
            return {
                "filename": file.filename,
                "status": "error",
                "message": validation_warning.get("message"),
                "validation_error": validation_warning
            }
        
        # Check for duplicates
        if duplicate_warning and duplicate_warning.get("has_duplicate"):
            logger.warning(f"⚠️ Duplicate detected for {file.filename}")
            return {
                "filename": file.filename,
                "status": "pending_duplicate_resolution",
                "message": duplicate_warning.get("message"),
                "duplicate_info": duplicate_warning,
                "analysis": extracted_info,
                "summary_text": summary_text  # ⭐ Pass summary for later use
            }
        
        # Extract key fields for further processing
        extracted_imo = extracted_info.get('imo_number', '').strip()
        extracted_ship_name = extracted_info.get('ship_name', '').strip()
        current_ship_imo = (ship.get('imo') or '').strip()
        current_ship_name = (ship.get('name') or '').strip()
        validation_note = None
        progress_message = None
        
        # Prepare validation note (if ship name mismatch warning exists)
        validation_note = None
        progress_message = None
        if validation_warning and not validation_warning.get("is_blocking"):
            validation_note = validation_warning.get("override_note", "Chỉ để tham khảo")
            progress_message = validation_warning.get("message")
            logger.info(f"⚠️ Non-blocking validation warning: {progress_message}")
        
        # Upload main certificate to Google Drive
        ship_name = ship.get("name", "Unknown_Ship")
        upload_result = await CertificateMultiUploadService._upload_to_gdrive(
            gdrive_config_doc, file_content, file.filename, ship_name, "Certificates"
        )
        
        if not upload_result.get("success"):
            return {
                "filename": file.filename,
                "status": "error",
                "message": f"Failed to upload to Google Drive: {upload_result.get('message')}"
            }
        
        # ⭐ NEW: Upload summary file to Google Drive (if available)
        summary_file_id = None
        if summary_text and summary_text.strip():
            try:
                logger.info(f"📋 Uploading summary file for {file.filename}")
                
                # Create summary filename
                base_name = file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename
                summary_filename = f"{base_name}_Summary.txt"
                
                # Convert summary text to bytes
                summary_bytes = summary_text.encode('utf-8')
                
                # Upload summary to GDrive with text/plain MIME type
                summary_upload_result = await CertificateMultiUploadService._upload_to_gdrive(
                    gdrive_config_doc, summary_bytes, summary_filename, ship_name, "Certificates",
                    content_type="text/plain"  # ⭐ Explicitly set MIME type for text files
                )
                
                if summary_upload_result.get("success"):
                    summary_file_id = summary_upload_result.get("file_id")
                    logger.info(f"✅ Summary file uploaded: {summary_file_id}")
                else:
                    logger.warning(f"⚠️ Summary upload failed: {summary_upload_result.get('message')}")
            
            except Exception as summary_error:
                logger.warning(f"⚠️ Failed to upload summary: {summary_error}")
                # Don't fail the entire upload if summary fails
        
        # Create certificate record with summary_file_id
        cert_result = await CertificateMultiUploadService._create_certificate_from_analysis(
            extracted_info, 
            upload_result, 
            current_user, 
            ship_id, 
            validation_note, 
            db,
            summary_file_id=summary_file_id,  # ⭐ NEW: Pass summary file ID
            extracted_ship_name=extracted_ship_name  # ⭐ NEW: Pass extracted ship name
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
            db = mongo_db.database
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
        ai_config: Dict[str, Any],
        ship_id: str,
        current_user: Any
    ) -> Dict[str, Any]:
        """
        Analyze document using AI with advanced Document AI pipeline
        
        ⭐ UPGRADED: Now uses ShipCertificateAnalyzeService with Document AI + OCR
        
        Returns:
            dict: {
                "success": bool,
                "extracted_info": {...},
                "summary_text": str,  # ⭐ NEW: Document AI extracted text
                "validation_warning": {...} | None,
                "duplicate_warning": {...} | None
            }
        """
        try:
            logger.info(f"🤖 Analyzing document with advanced AI pipeline: {filename}")
            
            # Use new ShipCertificateAnalyzeService (with Document AI + OCR)
            from app.services.ship_certificate_analyze_service import ShipCertificateAnalyzeService
            import base64
            
            # Convert bytes to base64
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # Call analysis service
            analysis_result = await ShipCertificateAnalyzeService.analyze_file(
                file_content=file_base64,
                filename=filename,
                content_type=content_type,
                ship_id=ship_id,
                current_user=current_user
            )
            
            if analysis_result.get("success"):
                logger.info(f"✅ Document AI analysis successful for {filename}")
                return analysis_result
            else:
                logger.error(f"❌ Document AI analysis failed for {filename}")
                return {
                    "success": False,
                    "message": "Analysis failed"
                }
            
        except Exception as e:
            logger.error(f"❌ AI analysis error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "message": f"Analysis failed: {str(e)}"
            }
    
    @staticmethod
    def _create_certificate_extraction_prompt(text: str) -> str:
        """Create prompt for certificate extraction with classification"""
        return f"""
Analyze this maritime ship certificate document and extract information.

Document Text:
{text[:10000]}

CRITICAL: You MUST extract and return a JSON object with ALL these fields.

{{
  "category": "certificates (MUST be 'certificates' if this contains ship certificate information - look for keywords: Certificate, SOLAS, MARPOL, Classification Society, IMO, Ship Safety)",
  "confidence": "high or medium or low",
  "text_content": "{text[:500][:500]}",
  
  "cert_name": "Full certificate name (e.g., 'Cargo Ship Safety Construction Certificate', 'Load Line Certificate')",
  "cert_abbreviation": "Certificate abbreviation if visible (e.g., 'CSSC', 'LLC', 'IOPP'). Look for abbreviated forms near the title or in headers.",
  "cert_no": "Certificate number (alphanumeric)",
  "cert_type": "Certificate type - MUST be EXACTLY ONE of these 6 options: 'Full Term', 'Interim', 'Provisional', 'Short term', 'Conditional', 'Other'. Look for keywords: 'Full Term' (standard long-validity certificate), 'Interim' (temporary/between surveys), 'Provisional' (pending full certification), 'Short term' (limited validity), 'Conditional' (with conditions), 'Other' (if none match). Default to 'Full Term' if not explicitly stated.",
  "issue_date": "Issue date in DD/MM/YYYY format - SEARCH FOR: 'Date of issue', 'Issue date', 'Issued on', 'Date issued', or dates near beginning of document. Examples: '7 November 2025' → '07/11/2025', '15 January 2023' → '15/01/2023'",
  "valid_date": "Valid until date in DD/MM/YYYY format - SEARCH FOR: 'Valid until', 'Expiry date', 'Date of expiry', 'Expires', 'Valid to'",
  "last_endorse": "Last endorsement date in DD/MM/YYYY format - SEARCH FOR: 'Last endorsement', 'Endorsed on', 'Date of endorsement'",
  "issued_by": "Full name of issuing authority (e.g., 'Lloyd\\'s Register', 'Panama Maritime Authority', 'NIPPON KAIJI KYOKAI')",
  
  "ship_name": "Ship name (look for 'NAME OF SHIP', 'Ship Name', 'Vessel Name', 'M.V.', 'M/V')",
  "imo_number": "IMO number - 7 digits starting with 8 or 9 (look for 'IMO No', 'IMO Number', 'IMO:')",
  "flag": "Flag state (look for 'Flag', 'Port of Registry', 'Government of')",
  "class_society": "Classification society full name (e.g., 'Lloyd\\'s Register', 'DNV GL', 'American Bureau of Shipping')",
  "ship_owner": "Ship owner / registered owner name",
  "ship_type": "ONE OF: General Cargo, Bulk Carrier, Oil Tanker, Chemical Tanker, LPG/LNG Carrier, Container Ship, Passenger Ship, Ro-Ro Cargo, Fishing Vessel, Tug/Supply Vessel, Other",
  "gross_tonnage": "Gross tonnage (numeric only, no units)",
  "deadweight": "Deadweight (numeric only, no units)"
}}

CLASSIFICATION RULES - MUST classify as "certificates" if:
✓ Document contains "Certificate" word
✓ Has IMO number
✓ Has ship name + issuing authority
✓ Has validity dates
✓ Mentions SOLAS, MARPOL, or maritime safety regulations
✓ Issued by Classification Society or Maritime Authority

EXTRACTION RULES:
1. For dates: Convert to DD/MM/YYYY format. Month names → numbers:
   - "7 November 2025" → "07/11/2025"
   - "15 January 2023" → "15/01/2023"
   - "28 July 2025" → "28/07/2025"
   - "3 Dec 2024" → "03/12/2024"
   - Month mapping: January=01, February=02, March=03, April=04, May=05, June=06, July=07, August=08, September=09, October=10, November=11, December=12
2. For ship_type: Pick ONE from the list that matches
3. For numbers: Extract digits only (e.g., "25,000 MT" → "25000")
4. If field not found: Use null (not empty string)
5. confidence: "high" if 5+ fields extracted, "medium" if 3-4 fields, "low" if <3 fields
6. Issue date priority: Search document from top to bottom. The first date near "Date of issue" or "THIS IS TO CERTIFY" section is usually the issue date

Return ONLY the JSON object, no markdown blocks, no explanation.

Example output:
{{"category":"certificates","confidence":"high","cert_name":"Cargo Ship Safety Construction Certificate","cert_no":"CSSC-12345","issue_date":"15/01/2023","valid_date":"14/01/2028","issued_by":"Lloyd's Register","ship_name":"M.V. OCEAN STAR","imo_number":"9123456","text_content":"....."}}

IMPORTANT DATE EXAMPLES:
- "7 November 2025" → "07/11/2025"
- "13 September 2030" → "13/09/2030"
- "28 July 2025" → "28/07/2025"
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
        
        cert_name = (analysis_result.get('cert_name') or '').strip()
        cert_no = (analysis_result.get('cert_no') or '').strip()
        issue_date = (analysis_result.get('issue_date') or '').strip()
        valid_date = (analysis_result.get('valid_date') or '').strip()
        last_endorse = (analysis_result.get('last_endorse') or '').strip()
        
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
        folder: str,
        content_type: str = None  # ⭐ NEW: Optional MIME type
    ) -> Dict[str, Any]:
        """Upload file to Google Drive"""
        try:
            # Import GDrive helper
            from app.utils.gdrive_helper import upload_file_to_ship_folder
            
            result = await upload_file_to_ship_folder(
                gdrive_config, file_content, filename, ship_name, folder, content_type
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
    def _parse_date_to_iso(date_str: Optional[str]) -> Optional[str]:
        """
        Parse date string to ISO format (YYYY-MM-DD)
        Handles multiple formats from backend-v1
        """
        if not date_str or not isinstance(date_str, str) or date_str.lower() in ['null', 'none', 'n/a', '']:
            return None
        
        import re
        from datetime import datetime
        
        try:
            date_str_clean = str(date_str).strip()
            
            # Handle "DD MONTH YYYY" formats (e.g., "28 July 2025", "9 Aug 2023")
            if re.match(r'^\d{1,2}\s+\w+\s+\d{4}$', date_str_clean):
                for fmt in ['%d %B %Y', '%d %b %Y']:
                    try:
                        parsed = datetime.strptime(date_str_clean, fmt)
                        return parsed.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            
            # Handle "MONTH YYYY" formats (e.g., "NOV 2020", "July 2025")
            if re.match(r'^\w{3,4}\.?\s+\d{4}$', date_str_clean):
                for fmt in ['%b %Y', '%b. %Y', '%B %Y']:
                    try:
                        parsed = datetime.strptime(date_str_clean, fmt)
                        return parsed.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            
            # Try standard formats
            date_formats = [
                '%Y-%m-%d',      # 2025-11-07 (ISO)
                '%d/%m/%Y',      # 07/11/2025 (DD/MM/YYYY)
                '%m/%d/%Y',      # 11/07/2025 (MM/DD/YYYY)
                '%d-%m-%Y',      # 07-11-2025
                '%Y/%m/%d',      # 2025/11/07
                '%m/%Y',         # 11/2025 (Month/Year only)
            ]
            
            for fmt in date_formats:
                try:
                    parsed = datetime.strptime(date_str_clean, fmt)
                    return parsed.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date: {date_str}")
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None
    
    @staticmethod
    async def _create_certificate_from_analysis(
        analysis_result: Dict[str, Any],
        upload_result: Dict[str, Any],
        current_user: UserResponse,
        ship_id: str,
        validation_note: Optional[str],
        db: Any,
        summary_file_id: Optional[str] = None,  # ⭐ NEW
        extracted_ship_name: Optional[str] = None  # ⭐ NEW
    ) -> Dict[str, Any]:
        """Create certificate record from AI analysis"""
        try:
            cert_id = str(uuid.uuid4())
            
            # Parse dates to ISO format
            issue_date_iso = CertificateMultiUploadService._parse_date_to_iso(
                analysis_result.get("issue_date")
            )
            valid_date_iso = CertificateMultiUploadService._parse_date_to_iso(
                analysis_result.get("valid_date")
            )
            last_endorse_iso = CertificateMultiUploadService._parse_date_to_iso(
                analysis_result.get("last_endorse")
            )
            next_survey_iso = CertificateMultiUploadService._parse_date_to_iso(
                analysis_result.get("next_survey")
            )
            
            # Get cert_abbreviation with priority: User mappings → AI → Auto-generation
            from app.utils.certificate_abbreviation import generate_certificate_abbreviation, validate_certificate_type
            cert_name = analysis_result.get("cert_name", "Unknown Certificate")
            
            # Validate and normalize cert_type
            cert_type = validate_certificate_type(analysis_result.get("cert_type", "Full Term"))
            
            # TODO: Implement get_user_defined_abbreviation when needed
            # For now, use AI extraction or auto-generation
            cert_abbreviation = analysis_result.get('cert_abbreviation')
            if not cert_abbreviation:
                cert_abbreviation = await generate_certificate_abbreviation(cert_name)
                logger.info(f"⚙️ Generated abbreviation: '{cert_name}' → '{cert_abbreviation}'")
            else:
                logger.info(f"🤖 Using AI extracted abbreviation: '{cert_abbreviation}'")
            
            # Get ship info for additional fields
            ship = await db.ships.find_one({"id": ship_id})
            ship_name = ship.get("name", "Unknown Ship") if ship else "Unknown Ship"
            
            # Build certificate document (match backend-v1 fields)
            cert_doc = {
                "id": cert_id,
                "ship_id": ship_id,
                "ship_name": ship_name,
                "extracted_ship_name": extracted_ship_name or analysis_result.get("ship_name"),  # ⭐ Ship name from certificate
                "cert_name": cert_name,
                "cert_abbreviation": cert_abbreviation,
                "cert_no": analysis_result.get("cert_no", "Unknown"),
                "cert_type": cert_type,
                "issue_date": issue_date_iso,
                "valid_date": valid_date_iso,
                "last_endorse": last_endorse_iso,
                "next_survey": next_survey_iso,
                "next_survey_type": analysis_result.get("next_survey_type"),
                "issued_by": analysis_result.get("issued_by"),
                "notes": validation_note if validation_note else analysis_result.get("notes"),
                "category": "certificates",
                "sensitivity_level": "internal",
                "file_name": analysis_result.get("filename"),  # Original filename
                "file_uploaded": upload_result.get("success", False),
                "google_drive_file_id": upload_result.get("file_id"),
                "google_drive_file_url": upload_result.get("file_url"),
                "google_drive_folder_path": upload_result.get("folder_path"),
                "file_path": upload_result.get("file_path"),
                "summary_file_id": summary_file_id,  # ⭐ NEW: Summary file ID
                "text_content": analysis_result.get("text_content"),  # For future re-analysis
                "created_by": current_user.email,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Remove None values but preserve important fields
            preserved_fields = ['extracted_ship_name', 'text_content', 'notes']
            cert_doc = {k: v for k, v in cert_doc.items() if v is not None or k in preserved_fields}
            
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
