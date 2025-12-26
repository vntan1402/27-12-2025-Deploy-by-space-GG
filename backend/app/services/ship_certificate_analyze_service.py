"""
Ship Certificate Analysis Service
Handles AI-powered analysis of ship certificate files (Class & Flag certificates)
Based on AuditCertificateAnalyzeService pattern
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
from app.utils.ship_certificate_ai import (
    extract_ship_certificate_fields_from_summary,
    SHIP_CERTIFICATE_CATEGORIES
)
from app.utils.issued_by_abbreviation import normalize_issued_by

logger = logging.getLogger(__name__)

# Constants
TEXT_LAYER_THRESHOLD = 400  # Minimum chars to use fast path


class ShipCertificateAnalyzeService:
    """Service for analyzing ship certificate files with AI"""
    
    @staticmethod
    def quick_check_processing_path(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Quick check to determine if file needs FAST PATH or SLOW PATH (background)
        This is a synchronous, fast operation (~100ms)
        
        Logic for Certificate:
        - PDF with text layer >= 400 chars → FAST PATH
        - PDF without text layer or image files → SLOW PATH (Document AI)
        
        Returns:
            dict: {
                "path": "FAST_PATH" | "SLOW_PATH",
                "has_text_layer": bool,
                "char_count": int,
                "text_content": str | None (only if FAST_PATH),
                "reason": str
            }
        """
        from app.utils.pdf_text_extractor import quick_check_text_layer
        
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # Image files always need SLOW PATH (Document AI)
        if file_ext in ['jpg', 'jpeg', 'png']:
            return {
                "path": "SLOW_PATH",
                "has_text_layer": False,
                "char_count": 0,
                "text_content": None,
                "reason": f"Image file ({file_ext}) requires Document AI OCR"
            }
        
        # For PDFs, check text layer
        if file_ext == 'pdf':
            text_check = quick_check_text_layer(file_bytes, filename)
            
            if text_check.get("has_sufficient_text"):
                return {
                    "path": "FAST_PATH",
                    "has_text_layer": True,
                    "char_count": text_check["char_count"],
                    "text_content": text_check["text_content"],
                    "page_count": text_check["page_count"],
                    "reason": f"Text layer found: {text_check['char_count']} chars >= {TEXT_LAYER_THRESHOLD} threshold"
                }
            else:
                return {
                    "path": "SLOW_PATH",
                    "has_text_layer": False,
                    "char_count": text_check.get("char_count", 0),
                    "text_content": None,
                    "reason": f"Insufficient text layer: {text_check.get('char_count', 0)} chars < {TEXT_LAYER_THRESHOLD} threshold (scanned PDF)"
                }
        
        # Unknown file type - try SLOW PATH
        return {
            "path": "SLOW_PATH",
            "has_text_layer": False,
            "char_count": 0,
            "text_content": None,
            "reason": f"Unknown file type: {file_ext}"
        }
    
    @staticmethod
    async def analyze_file(
        file_content: str,  # base64 encoded
        filename: str,
        content_type: str,
        ship_id: str,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """
        Analyze ship certificate file using Document AI + System AI
        
        Process (identical to Audit Certificate):
        1. Decode base64 file content
        2. Validate file (PDF/JPG/PNG, max 50MB, magic bytes)
        3. Check page count and split if >15 pages
        4. Process with Document AI (parallel for chunks)
        5. Extract fields from summary with System AI
        6. Normalize issued_by
        7. Validate ship name/IMO
        8. Check for duplicates
        9. Return analysis + validation warnings
        
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
                "summary_text": "...",  # ⭐ Document AI extracted text
                "validation_warning": {...} | null,
                "duplicate_warning": {...} | null
            }
        """
        try:
            logger.info(f"📋 Starting ship certificate analysis: {filename}")
            
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
                    detail="Unsupported file type. Supported: PDF, JPG, PNG"
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
            
            # Get AI configuration with fallback queries
            from app.utils.ai_config_helper import get_ai_config
            ai_config_doc = await get_ai_config()
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
                        return await ShipCertificateAnalyzeService._process_large_file(
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
                        return await ShipCertificateAnalyzeService._process_small_file(
                            file_bytes,
                            filename,
                            ship,
                            document_ai_config,
                            ai_config_doc,
                            current_user
                        )
                        
                except Exception as e:
                    logger.warning(f"⚠️ Could not detect page count: {e}, processing as single file")
                    return await ShipCertificateAnalyzeService._process_small_file(
                        file_bytes,
                        filename,
                        ship,
                        document_ai_config,
                        ai_config_doc,
                        current_user
                    )
            else:
                # Image file - process directly
                return await ShipCertificateAnalyzeService._process_small_file(
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
        """
        Process file ≤15 pages (or images) with SMART PATH selection:
        - FAST PATH: If text layer >= 400 chars, use text layer only (no Document AI)
        - SLOW PATH: If text layer < 400 chars, use Document AI (OCR)
        """
        try:
            # Determine file type
            file_ext = filename.lower().split('.')[-1] if '.' in filename else 'pdf'
            is_pdf = file_ext == 'pdf'
            
            # Import utilities
            from app.utils.pdf_text_extractor import (
                quick_check_text_layer, 
                format_text_layer_summary,
                TEXT_LAYER_THRESHOLD
            )
            
            summary_text = None
            processing_path = None
            
            # ⭐ SMART PATH SELECTION (PDF only)
            if is_pdf:
                logger.info(f"⚡ SMART PATH: Checking text layer for {filename}...")
                
                # Quick check text layer (synchronous, fast)
                text_check = quick_check_text_layer(file_bytes, filename)
                char_count = text_check.get("char_count", 0)
                
                if text_check.get("has_sufficient_text"):
                    # ✅ FAST PATH - Use text layer with AI correction
                    processing_path = "FAST_PATH"
                    logger.info(f"⚡ FAST PATH selected: {char_count} chars >= {TEXT_LAYER_THRESHOLD} threshold")
                    
                    # ⭐ NEW: Check text quality and apply AI correction if needed
                    from app.utils.text_layer_correction import (
                        correct_text_layer_with_ai,
                        detect_ocr_quality
                    )
                    
                    raw_text = text_check["text_content"]
                    quality_info = detect_ocr_quality(raw_text)
                    
                    logger.info(f"   📊 Text quality: {quality_info['quality_score']}%, needs_correction: {quality_info['needs_correction']}")
                    
                    if quality_info["needs_correction"]:
                        # Apply AI correction for low-quality text
                        logger.info(f"   🔧 Applying AI text correction (quality issues: {quality_info['issues_detected']})")
                        
                        correction_result = await correct_text_layer_with_ai(
                            text_content=raw_text,
                            filename=filename,
                            ai_config=ai_config_doc
                        )
                        
                        if correction_result["success"] and correction_result["correction_applied"]:
                            corrected_text = correction_result["corrected_text"]
                            logger.info(f"   ✅ Text corrected in {correction_result['processing_time']}s")
                            
                            # Format corrected text as summary
                            summary_text = format_text_layer_summary(
                                text_content=corrected_text,
                                filename=filename,
                                page_count=text_check["page_count"],
                                char_count=len(corrected_text)
                            )
                            
                            # Add correction note to summary
                            summary_text = summary_text.replace(
                                "Processing: FAST PATH (Native PDF Text)",
                                "Processing: FAST PATH (Native PDF Text + AI Correction)"
                            )
                        else:
                            # Correction failed, use original
                            logger.warning("   ⚠️ AI correction failed, using original text")
                            summary_text = format_text_layer_summary(
                                text_content=raw_text,
                                filename=filename,
                                page_count=text_check["page_count"],
                                char_count=char_count
                            )
                    else:
                        # Text quality is good, use as-is
                        logger.info("   ✅ Text quality good, skipping AI correction")
                        summary_text = format_text_layer_summary(
                            text_content=raw_text,
                            filename=filename,
                            page_count=text_check["page_count"],
                            char_count=char_count
                        )
                    
                    logger.info(f"✅ Text layer summary: {len(summary_text)} characters")
                else:
                    # ⚠️ SLOW PATH - Need Document AI
                    processing_path = "SLOW_PATH"
                    logger.info(f"🐢 SLOW PATH selected: {char_count} chars < {TEXT_LAYER_THRESHOLD} threshold")
                    logger.info("   📄 PDF appears to be scanned/image - calling Document AI...")
            else:
                # Image files always need Document AI
                processing_path = "SLOW_PATH"
                logger.info(f"🐢 SLOW PATH: Image file detected ({file_ext}), using Document AI")
            
            # ⚠️ SLOW PATH - Call Document AI
            if processing_path == "SLOW_PATH":
                from app.utils.document_ai_helper import analyze_document_with_document_ai
                from app.utils.pdf_text_extractor import merge_text_layer_and_document_ai, extract_text_layer_from_pdf
                
                mime_type_mapping = {
                    'pdf': 'application/pdf',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'png': 'image/png'
                }
                content_type = mime_type_mapping.get(file_ext, 'application/pdf')
                
                logger.info("🚀 Starting Document AI analysis...")
                
                # For PDF, also get text layer for merging
                if is_pdf:
                    import asyncio
                    text_layer_task = extract_text_layer_from_pdf(
                        file_content=file_bytes,
                        filename=filename
                    )
                    
                    doc_ai_task = analyze_document_with_document_ai(
                        file_content=file_bytes,
                        filename=filename,
                        content_type=content_type,
                        document_ai_config=document_ai_config,
                        document_type='other'
                    )
                    
                    text_layer_result, doc_ai_result = await asyncio.gather(
                        text_layer_task,
                        doc_ai_task,
                        return_exceptions=True
                    )
                    
                    if isinstance(text_layer_result, Exception):
                        text_layer_result = {"success": False, "text": "", "has_text_layer": False}
                    
                    if isinstance(doc_ai_result, Exception):
                        logger.error(f"❌ Document AI failed: {doc_ai_result}")
                        doc_ai_result = {"success": False}
                    
                    # Merge results
                    summary_text = merge_text_layer_and_document_ai(
                        text_layer_result=text_layer_result,
                        document_ai_result=doc_ai_result,
                        filename=filename
                    )
                else:
                    # Image file - Document AI + Targeted OCR for header/footer
                    doc_ai_result = await analyze_document_with_document_ai(
                        file_content=file_bytes,
                        filename=filename,
                        content_type=content_type,
                        document_ai_config=document_ai_config,
                        document_type='other'
                    )
                    
                    summary_text = ""
                    if doc_ai_result and doc_ai_result.get("success"):
                        summary_text = doc_ai_result.get("data", {}).get("summary", "")
                    
                    # ⭐ Add Targeted OCR for header/footer (especially for Cert No)
                    try:
                        from app.utils.targeted_ocr import get_ocr_processor
                        ocr_processor = get_ocr_processor()
                        
                        logger.info(f"🔍 Running targeted OCR for header/footer on image: {filename}")
                        
                        # For images, extract from the image directly
                        ocr_result = ocr_processor.extract_from_image(
                            file_bytes,
                            report_no_field='cert_no'
                        )
                        
                        if ocr_result.get('ocr_success'):
                            header_text = ocr_result.get('header_text', '').strip()
                            footer_text = ocr_result.get('footer_text', '').strip()
                            
                            if header_text or footer_text:
                                ocr_section = "\n\n" + "="*60 + "\n"
                                ocr_section += "ADDITIONAL INFORMATION FROM HEADER/FOOTER (Targeted OCR)\n"
                                ocr_section += "="*60 + "\n\n"
                                
                                if header_text:
                                    ocr_section += "=== HEADER TEXT ===\n" + header_text + "\n\n"
                                if footer_text:
                                    ocr_section += "=== FOOTER TEXT ===\n" + footer_text + "\n\n"
                                
                                summary_text = summary_text + ocr_section
                                logger.info(f"✅ Enhanced with targeted OCR: header={len(header_text)} chars, footer={len(footer_text)} chars")
                        else:
                            logger.info("ℹ️ Targeted OCR skipped or no additional text found")
                            
                    except Exception as ocr_error:
                        logger.warning(f"⚠️ Targeted OCR failed: {ocr_error}")
                        # Continue without OCR enhancement
                
                if doc_ai_result.get("success"):
                    doc_ai_summary = doc_ai_result.get("data", {}).get("summary", "")
                    logger.info(f"✅ Document AI completed: {len(doc_ai_summary)} characters")
            
            # Validate summary
            if not summary_text or len(summary_text.strip()) < 100:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract sufficient text from document"
                )
            
            logger.info(f"✅ Final summary ({processing_path}): {len(summary_text)} total characters")
            
            # Extract fields with System AI (Gemini)
            extracted_info = await extract_ship_certificate_fields_from_summary(
                summary_text=summary_text,
                filename=filename,
                ai_config=ai_config_doc
            )
            
            if not extracted_info:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract certificate information from document"
                )
            
            # Add processing metadata
            extracted_info['_processing_path'] = processing_path
            
            # Normalize issued_by
            if extracted_info.get('issued_by'):
                extracted_info['issued_by'] = normalize_issued_by(extracted_info['issued_by'])
            
            # Validate ship info
            validation_warning = await ShipCertificateAnalyzeService.validate_ship_info(
                extracted_imo=extracted_info.get('imo_number'),
                extracted_ship_name=extracted_info.get('ship_name'),
                current_ship=ship
            )
            
            # Check for duplicates
            duplicate_warning = await ShipCertificateAnalyzeService.check_duplicate(
                ship_id=ship["id"],
                cert_name=extracted_info.get('cert_name'),
                cert_no=extracted_info.get('cert_no'),
                current_user=current_user,
                issue_date=extracted_info.get('issue_date'),
                valid_date=extracted_info.get('valid_date'),
                last_endorse=extracted_info.get('last_endorse')
            )
            
            return {
                "success": True,
                "extracted_info": extracted_info,
                "summary_text": summary_text,
                "processing_path": processing_path,  # ⭐ Return which path was used
                "validation_warning": validation_warning,
                "duplicate_warning": duplicate_warning
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
                        document_type='other'
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
            extracted_info = await extract_ship_certificate_fields_from_summary(
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
            validation_warning = await ShipCertificateAnalyzeService.validate_ship_info(
                extracted_imo=extracted_info.get('imo_number'),
                extracted_ship_name=extracted_info.get('ship_name'),
                current_ship=ship
            )
            
            # Check for duplicates with all 5 fields
            duplicate_warning = await ShipCertificateAnalyzeService.check_duplicate(
                ship_id=ship["id"],
                cert_name=extracted_info.get('cert_name'),
                cert_no=extracted_info.get('cert_no'),
                current_user=current_user,
                issue_date=extracted_info.get('issue_date'),
                valid_date=extracted_info.get('valid_date'),
                last_endorse=extracted_info.get('last_endorse')
            )
            
            return {
                "success": True,
                "extracted_info": extracted_info,
                "summary_text": merged_summary,  # ⭐ Return merged summary
                "validation_warning": validation_warning,
                "duplicate_warning": duplicate_warning
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
        Validate extracted ship IMO and name against current ship
        
        Returns validation warning if mismatch found
        """
        try:
            current_ship_imo = (current_ship.get('imo') or '').strip()
            current_ship_name = (current_ship.get('name') or '').strip()
            
            extracted_imo_clean = (extracted_imo or '').replace(' ', '').replace('IMO', '').strip()
            extracted_ship_name_clean = (extracted_ship_name or '').strip()
            
            logger.info(f"🔍 Validation - Extracted IMO: '{extracted_imo_clean}' vs Current: '{current_ship_imo}'")
            logger.info(f"🔍 Validation - Extracted Ship: '{extracted_ship_name_clean}' vs Current: '{current_ship_name}'")
            
            # Check IMO mismatch (BLOCKING)
            if extracted_imo_clean and current_ship_imo:
                if extracted_imo_clean != current_ship_imo:
                    return {
                        "is_blocking": True,
                        "message": "Giấy chứng nhận của tàu khác, không thể lưu vào dữ liệu tàu hiện tại",
                        "type": "imo_mismatch",
                        "extracted_imo": extracted_imo,
                        "current_imo": current_ship_imo
                    }
            
            # Check ship name mismatch (WARNING only)
            if extracted_ship_name_clean and current_ship_name:
                if extracted_ship_name_clean.upper() != current_ship_name.upper():
                    return {
                        "is_blocking": False,
                        "message": "Tên tàu trong chứng chỉ khác với tàu hiện tại",
                        "override_note": "Chỉ để tham khảo",
                        "type": "ship_name_mismatch",
                        "extracted_ship_name": extracted_ship_name,
                        "current_ship_name": current_ship_name
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error validating ship info: {e}")
            return None
    
    @staticmethod
    async def check_duplicate(
        ship_id: str,
        cert_name: Optional[str],
        cert_no: Optional[str],
        current_user: UserResponse,
        issue_date: Optional[str] = None,
        valid_date: Optional[str] = None,
        last_endorse: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check for duplicate certificates based on 100% match on 5 fields:
        cert_name, cert_no, issue_date, valid_date, last_endorse
        
        Returns duplicate warning only if ALL provided fields match exactly
        """
        try:
            cert_name = (cert_name or '').strip()
            cert_no = (cert_no or '').strip()
            issue_date = (issue_date or '').strip()
            valid_date = (valid_date or '').strip()
            last_endorse = (last_endorse or '').strip()
            
            if not cert_name and not cert_no:
                return None
            
            # Build query to find potential duplicates by cert_no
            query = {"ship_id": ship_id}
            if cert_no:
                query["cert_no"] = cert_no
            
            # Find potential duplicates
            existing_certs = await mongo_db.find_all("certificates", query)
            
            if not existing_certs:
                return None
            
            # Check for 100% match on all provided fields
            for existing in existing_certs:
                matches = 0
                total = 0
                
                if cert_name:
                    total += 1
                    existing_cert_name = existing.get('cert_name') or ''
                    if existing_cert_name.strip().lower() == cert_name.lower():
                        matches += 1
                
                if cert_no:
                    total += 1
                    existing_cert_no = existing.get('cert_no') or ''
                    if existing_cert_no.strip() == cert_no:
                        matches += 1
                
                if issue_date:
                    total += 1
                    existing_issue_date = existing.get('issue_date') or ''
                    if existing_issue_date.strip() == issue_date:
                        matches += 1
                
                if valid_date:
                    total += 1
                    existing_valid_date = existing.get('valid_date') or ''
                    if existing_valid_date.strip() == valid_date:
                        matches += 1
                
                if last_endorse:
                    total += 1
                    existing_last_endorse = existing.get('last_endorse') or ''
                    if existing_last_endorse.strip() == last_endorse:
                        matches += 1
                
                # Only consider duplicate if 100% match
                if total > 0 and matches == total:
                    return {
                        "has_duplicate": True,
                        "message": f"Duplicate certificate found: {cert_name} ({cert_no})",
                        "existing_certificate": {
                            "id": existing.get("id"),
                            "cert_name": existing.get("cert_name"),
                            "cert_no": existing.get("cert_no"),
                            "issue_date": existing.get("issue_date"),
                            "valid_date": existing.get("valid_date"),
                            "last_endorse": existing.get("last_endorse")
                        }
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return None
