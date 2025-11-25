"""
Audit Certificate Analysis Service
Handles AI-powered analysis of audit certificate files (ISM/ISPS/MLC/CICA)
Based on Audit Report Analyze Service pattern
"""
import logging
import base64
import asyncio
import traceback
from typing import Dict, Any, Optional
from fastapi import HTTPException

from app.db.mongodb import mongo_db
from app.models.user import UserResponse
from app.utils.pdf_splitter import PDFSplitter, create_enhanced_merged_summary
from app.utils.audit_certificate_ai import (
    extract_audit_certificate_fields_from_summary,
    AUDIT_CERTIFICATE_CATEGORIES
)
from app.utils.issued_by_abbreviation import normalize_issued_by

logger = logging.getLogger(__name__)


class AuditCertificateAnalyzeService:
    """Service for analyzing audit certificate files with AI"""
    
    @staticmethod
    async def analyze_file(
        file_content: str,  # base64 encoded
        filename: str,
        content_type: str,
        ship_id: str,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """
        Analyze audit certificate file using Document AI + System AI
        
        Process (identical to Audit Report):
        1. Decode base64 file content
        2. Validate file (PDF/JPG/PNG, max 50MB, magic bytes)
        3. Check page count and split if >15 pages
        4. Process with Document AI (parallel for chunks)
        5. Extract fields from summary with System AI
        6. Normalize issued_by
        7. Validate ship name/IMO
        8. Check for duplicates
        9. Check category (ISM/ISPS/MLC/CICA)
        10. Return analysis + validation warnings
        
        Based on: audit_report_analyze_service.py
        
        Args:
            file_content: base64 encoded file content
            filename: Original filename
            content_type: MIME type
            ship_id: Ship ID for validation
            current_user: Current authenticated user
            
        Returns:
            dict: {
                "success": true,
                "extracted_info": {...},
                "validation_warning": {...} | null,
                "duplicate_warning": {...} | null,
                "category_warning": {...} | null
            }
        """
        try:
            logger.info(f"📋 Starting audit certificate analysis: {filename}")
            
            # Validate inputs
            if not filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            if not file_content:
                raise HTTPException(status_code=400, detail="No file content provided")
            
            # Decode base64
            try:
                file_bytes = base64.b64decode(file_content)
            except Exception as e:
                logger.error(f"❌ Base64 decode error: {e}")
                raise HTTPException(status_code=400, detail="Invalid base64 file content")
            
            if not file_bytes or len(file_bytes) == 0:
                raise HTTPException(status_code=400, detail="Empty file provided")
            
            # Check file size (50MB max)
            if len(file_bytes) > 50 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail="File size exceeds 50MB limit"
                )
            
            # Validate file type
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            supported_extensions = ['pdf', 'jpg', 'jpeg', 'png']
            
            if file_ext not in supported_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type. Supported: PDF, JPG, PNG"
                )
            
            # Validate file format (magic bytes)
            if file_ext == 'pdf':
                if not file_bytes.startswith(b'%PDF'):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid PDF file format"
                    )
            elif file_ext in ['jpg', 'jpeg']:
                if not file_bytes.startswith(b'\xff\xd8\xff'):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid JPG file format"
                    )
            elif file_ext == 'png':
                if not file_bytes.startswith(b'\x89PNG'):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid PNG file format"
                    )
            
            logger.info(f"📄 Processing file: {filename} ({len(file_bytes)} bytes)")
            
            # Get company UUID
            company_uuid = current_user.company
            if not company_uuid:
                raise HTTPException(status_code=404, detail="Company not found")
            
            # Get ship info
            ship = await mongo_db.find_one("ships", {"id": ship_id, "company": company_uuid})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            ship_name = ship.get("name", "Unknown Ship")
            ship_imo = ship.get("imo", "")
            
            # Get AI configuration
            ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
            if not ai_config_doc:
                raise HTTPException(
                    status_code=404,
                    detail="AI configuration not found. Please configure System AI in Settings."
                )
            
            document_ai_config = ai_config_doc.get("document_ai", {})
            
            if not document_ai_config.get("enabled", False):
                raise HTTPException(
                    status_code=400,
                    detail="Google Document AI is not enabled in System Settings"
                )
            
            # Validate required Document AI configuration
            if not all([
                document_ai_config.get("project_id"),
                document_ai_config.get("processor_id")
            ]):
                raise HTTPException(
                    status_code=400,
                    detail="Incomplete Google Document AI configuration"
                )
            
            logger.info("🤖 Analyzing certificate with Google Document AI...")
            
            # Check if PDF needs splitting (>15 pages)
            if file_ext == 'pdf':
                splitter = PDFSplitter(max_pages_per_chunk=12)
                try:
                    total_pages = splitter.get_page_count(file_bytes)
                    needs_split = splitter.needs_splitting(file_bytes)
                    logger.info(f"📊 PDF: {total_pages} pages, Split needed: {needs_split}")
                    
                    if needs_split:
                        # Large file - split and process
                        return await AuditCertificateAnalyzeService._process_large_file(
                            file_bytes,
                            filename,
                            total_pages,
                            ship,
                            document_ai_config,
                            ai_config_doc,
                            current_user
                        )
                    else:
                        # Small file - process directly
                        return await AuditCertificateAnalyzeService._process_small_file(
                            file_bytes,
                            filename,
                            ship,
                            document_ai_config,
                            ai_config_doc,
                            current_user
                        )
                        
                except Exception as e:
                    logger.warning(f"⚠️ Could not detect page count: {e}, processing as single file")
                    return await AuditCertificateAnalyzeService._process_small_file(
                        file_bytes,
                        filename,
                        ship,
                        document_ai_config,
                        ai_config_doc,
                        current_user
                    )
            else:
                # Image file - process directly
                return await AuditCertificateAnalyzeService._process_small_file(
                    file_bytes,
                    filename,
                    ship,
                    document_ai_config,
                    ai_config_doc,
                    current_user
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error analyzing certificate: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    @staticmethod
    async def _process_small_file(
        file_bytes: bytes,
        filename: str,
        ship: dict,
        document_ai_config: dict,
        ai_config_doc: dict,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """Process file ≤15 pages (or images) - single Document AI call"""
        try:
            logger.info("📄 Processing small file/image (single Document AI call)")
            
            # Call Document AI
            from app.utils.document_ai_helper import analyze_document_with_document_ai
            
            # Determine MIME type
            file_ext = filename.lower().split('.')[-1] if '.' in filename else 'pdf'
            mime_type_mapping = {
                'pdf': 'application/pdf',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png'
            }
            content_type = mime_type_mapping.get(file_ext, 'application/pdf')
            
            # Process with Document AI
            doc_ai_result = await analyze_document_with_document_ai(
                file_content=file_bytes,
                filename=filename,
                content_type=content_type,
                document_ai_config=document_ai_config,
                document_type='audit_certificate'  # Use 'other' or specific type
            )
            
            if not doc_ai_result or not doc_ai_result.get("success"):
                error_msg = doc_ai_result.get("message", "Unknown error") if doc_ai_result else "No response"
                raise HTTPException(
                    status_code=400,
                    detail=f"Document AI could not extract text from file: {error_msg}"
                )
            
            data = doc_ai_result.get("data", {})
            summary_text = data.get("summary", "")
            
            if not summary_text:
                raise HTTPException(
                    status_code=400,
                    detail="Document AI returned empty summary"
                )
            
            logger.info(f"✅ Document AI extraction: {len(summary_text)} characters")
            
            # Extract fields with System AI
            extracted_info = await extract_audit_certificate_fields_from_summary(
                summary_text=summary_text,
                filename=filename,
                ai_config=ai_config_doc
            )
            
            if not extracted_info:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract certificate information from document"
                )
            
            # Normalize issued_by
            if extracted_info.get('issued_by'):
                extracted_info['issued_by'] = normalize_issued_by(extracted_info['issued_by'])
            
            # Validate ship info
            validation_warning = await AuditCertificateAnalyzeService.validate_ship_info(
                extracted_imo=extracted_info.get('imo_number'),
                extracted_ship_name=extracted_info.get('ship_name'),
                current_ship=ship
            )
            
            # Check for duplicates
            duplicate_warning = await AuditCertificateAnalyzeService.check_duplicate(
                ship_id=ship["id"],
                cert_name=extracted_info.get('cert_name'),
                cert_no=extracted_info.get('cert_no'),
                current_user=current_user
            )
            
            # Check category (ISM/ISPS/MLC/CICA)
            category_warning = await AuditCertificateAnalyzeService.check_category_ism_isps_mlc_cica(
                cert_name=extracted_info.get('cert_name', '')
            )
            
            return {
                "success": True,
                "extracted_info": extracted_info,
                "validation_warning": validation_warning,
                "duplicate_warning": duplicate_warning,
                "category_warning": category_warning
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error processing small file: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def _process_large_file(
        file_bytes: bytes,
        filename: str,
        total_pages: int,
        ship: dict,
        document_ai_config: dict,
        ai_config_doc: dict,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """Process file >15 pages with splitting - parallel Document AI calls"""
        try:
            logger.info(f"📚 Processing large file ({total_pages} pages) with splitting")
            
            # Split PDF
            splitter = PDFSplitter(max_pages_per_chunk=12)
            chunks = splitter.split_pdf(file_bytes)
            logger.info(f"✂️ Split into {len(chunks)} chunks")
            
            # Process chunks in parallel
            from app.utils.document_ai_helper import analyze_document_with_document_ai
            
            async def process_chunk(chunk_bytes, chunk_index):
                try:
                    result = await analyze_document_with_document_ai(
                        file_content=chunk_bytes,
                        filename=f"{filename}_chunk_{chunk_index}",
                        content_type='application/pdf',
                        document_ai_config=document_ai_config,
                        document_type='audit_certificate'
                    )
                    if result and result.get("success"):
                        data = result.get("data", {})
                        return data.get("summary", "")
                    return ""
                except Exception as e:
                    logger.error(f"❌ Chunk processing error: {e}")
                    return ""
            
            # Process all chunks in parallel
            tasks = [process_chunk(chunk, i) for i, chunk in enumerate(chunks)]
            chunk_texts = await asyncio.gather(*tasks)
            
            # Merge summaries
            merged_summary = create_enhanced_merged_summary(chunk_texts, filename)
            logger.info(f"✅ Merged summary: {len(merged_summary)} characters")
            
            # Extract fields with System AI
            extracted_info = await extract_audit_certificate_fields_from_summary(
                summary_text=merged_summary,
                filename=filename,
                ai_config=ai_config_doc
            )
            
            if not extracted_info:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract certificate information from document"
                )
            
            # Normalize issued_by
            if extracted_info.get('issued_by'):
                extracted_info['issued_by'] = normalize_issued_by(extracted_info['issued_by'])
            
            # Validate ship info
            validation_warning = await AuditCertificateAnalyzeService.validate_ship_info(
                extracted_imo=extracted_info.get('imo_number'),
                extracted_ship_name=extracted_info.get('ship_name'),
                current_ship=ship
            )
            
            # Check for duplicates
            duplicate_warning = await AuditCertificateAnalyzeService.check_duplicate(
                ship_id=ship["id"],
                cert_name=extracted_info.get('cert_name'),
                cert_no=extracted_info.get('cert_no'),
                current_user=current_user
            )
            
            # Check category (ISM/ISPS/MLC/CICA)
            category_warning = await AuditCertificateAnalyzeService.check_category_ism_isps_mlc_cica(
                cert_name=extracted_info.get('cert_name', '')
            )
            
            return {
                "success": True,
                "extracted_info": extracted_info,
                "validation_warning": validation_warning,
                "duplicate_warning": duplicate_warning,
                "category_warning": category_warning
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error processing large file: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def validate_ship_info(
        extracted_imo: Optional[str],
        extracted_ship_name: Optional[str],
        current_ship: dict
    ) -> Optional[Dict[str, Any]]:
        """
        Validate extracted ship info against current ship
        
        Rules (from Backend V1):
        - IMO mismatch → HARD REJECT (return error for frontend to block)
        - Ship name mismatch → SOFT WARNING (return warning with note)
        
        Returns:
            dict: {
                "type": "imo_mismatch" | "ship_name_mismatch",
                "message": str,
                "override_note": str
            } or None if valid
        """
        try:
            current_imo = current_ship.get("imo", "")
            current_ship_name = current_ship.get("name", "")
            
            # IMO validation (HARD REJECT)
            if extracted_imo and current_imo:
                # Clean IMO numbers for comparison
                extracted_imo_clean = extracted_imo.strip()
                current_imo_clean = current_imo.strip()
                
                if extracted_imo_clean != current_imo_clean:
                    logger.warning(f"⚠️ IMO MISMATCH: extracted='{extracted_imo_clean}' vs current='{current_imo_clean}'")
                    return {
                        "type": "imo_mismatch",
                        "message": f"IMO không khớp: Giấy chứng nhận của tàu khác (IMO: {extracted_imo_clean}), không thể lưu vào dữ liệu tàu hiện tại (IMO: {current_imo_clean})",
                        "is_blocking": True  # Frontend should block save
                    }
            
            # Ship name validation (SOFT WARNING)
            if extracted_ship_name and current_ship_name:
                extracted_name_upper = extracted_ship_name.upper().strip()
                current_name_upper = current_ship_name.upper().strip()
                
                if extracted_name_upper != current_name_upper:
                    logger.warning(f"⚠️ SHIP NAME MISMATCH: extracted='{extracted_ship_name}' vs current='{current_ship_name}'")
                    return {
                        "type": "ship_name_mismatch",
                        "message": f"Tên tàu không khớp: Giấy chứng nhận ghi '{extracted_ship_name}' nhưng tàu hiện tại là '{current_ship_name}'. Bạn có muốn tiếp tục?",
                        "override_note": "Chỉ để tham khảo",
                        "is_blocking": False  # User can choose to continue
                    }
            
            # All validations passed
            return None
            
        except Exception as e:
            logger.error(f"❌ Error validating ship info: {e}")
            return None
    
    @staticmethod
    def check_extraction_quality(extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if AI extraction is sufficient for automatic processing
        
        Based on Backend V1: check_ai_extraction_quality()
        
        Quality criteria:
        - Critical fields: cert_name, cert_no (MUST have both)
        - Confidence score >= 0.4
        - Overall extraction rate >= 0.3
        - Text quality >= 100 characters
        
        Returns:
            dict: {
                "sufficient": bool,
                "confidence_score": float,
                "critical_extraction_rate": float,
                "overall_extraction_rate": float,
                "text_quality_sufficient": bool,
                "missing_fields": list
            }
        """
        try:
            # Critical fields (MUST have)
            critical_fields = ['cert_name', 'cert_no']
            critical_extracted = sum(
                1 for field in critical_fields 
                if extracted_info.get(field) and extracted_info[field] not in ['', '-', None]
            )
            critical_extraction_rate = critical_extracted / len(critical_fields)
            
            # All fields (for overall rate)
            all_fields = [
                'cert_name', 'cert_no', 'cert_type', 'issue_date', 'valid_date',
                'issued_by'
            ]
            overall_extracted = sum(
                1 for field in all_fields
                if extracted_info.get(field) and extracted_info[field] not in ['', '-', None]
            )
            overall_extraction_rate = overall_extracted / len(all_fields)
            
            # Confidence score
            confidence_score = float(extracted_info.get('confidence_score', 0))
            
            # Text quality (check if we have meaningful text)
            text_quality = sum(
                len(str(extracted_info.get(field, '')))
                for field in all_fields
            )
            text_quality_sufficient = text_quality >= 100
            
            # Missing critical fields
            missing_fields = [
                field for field in critical_fields
                if not extracted_info.get(field) or extracted_info[field] in ['', '-', None]
            ]
            
            # Determine if sufficient
            sufficient = (
                critical_extraction_rate == 1.0 and  # All critical fields present
                confidence_score >= 0.4 and
                overall_extraction_rate >= 0.3 and
                text_quality_sufficient
            )
            
            logger.info(f"📊 Extraction Quality: sufficient={sufficient}, confidence={confidence_score}, critical_rate={critical_extraction_rate}")
            
            return {
                "sufficient": sufficient,
                "confidence_score": confidence_score,
                "critical_extraction_rate": critical_extraction_rate,
                "overall_extraction_rate": overall_extraction_rate,
                "text_quality_sufficient": text_quality_sufficient,
                "missing_fields": missing_fields
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking extraction quality: {e}")
            return {
                "sufficient": False,
                "missing_fields": critical_fields
            }
    
    @staticmethod
    async def check_category_ism_isps_mlc_cica(cert_name: str) -> Optional[Dict[str, Any]]:
        """
        Check if certificate belongs to ISM/ISPS/MLC/CICA categories
        
        ⭐ EXPANDED: Now includes CICA (Crew Accommodation)
        
        Rules:
        - cert_name must contain: "ISM", "ISPS", "MLC", or "CICA"
        - Special priority for "CREW ACCOMMODATION" → CICA
        - Case-insensitive search
        - If not found → Return error
        
        Returns:
            dict: {
                "is_valid": bool,
                "category": "ISM" | "ISPS" | "MLC" | "CICA" | null,
                "message": str
            } or None if valid
        """
        try:
            if not cert_name:
                return {
                    "type": "category_mismatch",
                    "message": "Certificate name is empty",
                    "is_valid": False
                }
            
            cert_name_upper = cert_name.upper().strip()
            
            # PRIORITY: Check for CREW ACCOMMODATION first
            if "CREW ACCOMMODATION" in cert_name_upper:
                logger.info("✅ Detected 'CREW ACCOMMODATION' → CICA category")
                return None  # Valid CICA certificate
            
            # Check against dictionary
            for category, cert_list in AUDIT_CERTIFICATE_CATEGORIES.items():
                for valid_cert in cert_list:
                    if valid_cert in cert_name_upper or cert_name_upper in valid_cert:
                        logger.info(f"✅ Matched certificate category: {category.upper()}")
                        return None  # Valid certificate
            
            # Not found in any category
            logger.warning(f"⚠️ Certificate '{cert_name}' does not belong to ISM/ISPS/MLC/CICA categories")
            return {
                "type": "category_mismatch",
                "message": f"Giấy chứng nhận '{cert_name}' không thuộc danh mục ISM/ISPS/MLC/CICA",
                "cert_name": cert_name,
                "is_valid": False
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking category: {e}")
            return None
    
    @staticmethod
    async def check_duplicate(
        ship_id: str,
        cert_name: Optional[str],
        cert_no: Optional[str],
        current_user: UserResponse
    ) -> Optional[Dict[str, Any]]:
        """
        Check if audit certificate is duplicate
        
        Match by: cert_name + cert_no
        
        Returns:
            dict: {
                "type": "duplicate",
                "message": str,
                "existing_certificate": dict
            } or None if not duplicate
        """
        try:
            if not cert_name or not cert_no:
                return None
            
            # Find existing certificate
            filters = {
                "ship_id": ship_id,
                "cert_name": cert_name,
                "cert_no": cert_no
            }
            
            existing = await mongo_db.find_one("audit_certificates", filters)
            
            if existing:
                logger.warning(f"⚠️ Duplicate found: {cert_name} - {cert_no}")
                return {
                    "type": "duplicate",
                    "message": f"Giấy chứng nhận '{cert_name}' số '{cert_no}' đã tồn tại trong hệ thống",
                    "existing_certificate": {
                        "id": existing.get("id"),
                        "cert_name": existing.get("cert_name"),
                        "cert_no": existing.get("cert_no"),
                        "cert_type": existing.get("cert_type"),
                        "issue_date": existing.get("issue_date"),
                        "valid_date": existing.get("valid_date"),
                        "issued_by": existing.get("issued_by")
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking duplicate: {e}")
            return None
