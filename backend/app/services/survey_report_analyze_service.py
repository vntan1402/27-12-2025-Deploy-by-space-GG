"""
Survey Report Analysis Service
Handles AI-powered analysis of survey report PDFs
"""
import logging
import base64
import traceback
from typing import Dict, Any, Optional
from fastapi import HTTPException, UploadFile

from app.db.mongodb import mongo_db
from app.models.user import UserResponse
from app.utils.pdf_splitter import PDFSplitter, merge_analysis_results, create_enhanced_merged_summary
from app.utils.survey_report_ai import extract_survey_report_fields_from_summary, extract_report_form_from_filename

logger = logging.getLogger(__name__)


class SurveyReportAnalyzeService:
    """Service for analyzing survey report files"""
    
    @staticmethod
    async def analyze_file(
        file: UploadFile,
        ship_id: str,
        bypass_validation: bool,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """
        Analyze survey report file using Google Document AI
        
        Process:
        1. Validate PDF file
        2. Check if PDF needs splitting (>15 pages)
        3. Process with Document AI
        4. Perform Targeted OCR on first page
        5. Extract fields with System AI
        6. Validate ship name/IMO
        7. Return analysis data + file content (base64) for later upload
        
        Args:
            file: PDF file uploaded
            ship_id: Ship ID to validate against
            bypass_validation: Skip ship validation if True
            current_user: Current authenticated user
        
        Returns:
            Dict with success status and analysis data
        """
        try:
            logger.info(f"📋 Starting survey report analysis for ship_id: {ship_id}")
            
            # Read file content
            file_content = await file.read()
            filename = file.filename
            
            # Validate file input
            if not filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            if not file_content or len(file_content) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Empty file provided. Please upload a valid PDF file."
                )
            
            # Validate file type
            if not filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Only PDF files are supported."
                )
            
            # Check PDF magic bytes
            if not file_content.startswith(b'%PDF'):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid PDF file format."
                )
            
            logger.info(f"📄 Processing survey report file: {filename} ({len(file_content)} bytes)")
            
            # Check if PDF needs splitting
            splitter = PDFSplitter(max_pages_per_chunk=12)
            
            try:
                total_pages = splitter.get_page_count(file_content)
                needs_split = splitter.needs_splitting(file_content)
                logger.info(f"📊 PDF Analysis: {total_pages} pages, Split needed: {needs_split}")
            except ValueError as e:
                logger.error(f"❌ Invalid PDF file: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid or corrupted PDF file: {str(e)}"
                )
            except Exception as e:
                logger.warning(f"⚠️ Could not detect page count: {e}")
                total_pages = 0
                needs_split = False
            
            # Get ship information
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            
            if not ship and not bypass_validation:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            ship_name = ship.get("name", "Unknown Ship") if ship else "Unknown Ship"
            ship_imo = ship.get("imo", "") if ship else ""
            
            # Get AI configuration with fallback queries
            from app.utils.ai_config_helper import get_ai_config
            ai_config_doc = await get_ai_config()
            if not ai_config_doc:
                raise HTTPException(
                    status_code=404,
                    detail="AI configuration not found. Please configure AI in System Settings."
                )
            
            document_ai_config = ai_config_doc.get("document_ai", {})
            
            if not document_ai_config.get("enabled", False):
                raise HTTPException(
                    status_code=400,
                    detail="Google Document AI is not enabled in System Settings"
                )
            
            # Validate Document AI config
            if not all([
                document_ai_config.get("project_id"),
                document_ai_config.get("processor_id")
            ]):
                raise HTTPException(
                    status_code=400,
                    detail="Incomplete Google Document AI configuration."
                )
            
            logger.info("🤖 Analyzing survey report with AI...")
            
            # Initialize analysis result
            analysis_result = {
                "survey_report_name": "",
                "report_form": "",
                "survey_report_no": "",
                "issued_by": "",
                "issued_date": "",
                "ship_name": "",
                "ship_imo": "",
                "surveyor_name": "",
                "note": "",
                "status": "Valid",
                "confidence_score": 0.0,
                "processing_method": "clean_analysis"
            }
            
            # Store file content for later upload
            analysis_result['_file_content'] = base64.b64encode(file_content).decode('utf-8')
            analysis_result['_filename'] = filename
            analysis_result['_content_type'] = file.content_type or 'application/octet-stream'
            analysis_result['_ship_name'] = ship_name
            analysis_result['_summary_text'] = ''
            
            try:
                # Process PDF based on size
                if not needs_split:
                    # Small PDF - process entire document
                    logger.info(f"🔄 Processing single PDF: {filename}")
                    analysis_result = await SurveyReportAnalyzeService._process_single_pdf(
                        file_content,
                        filename,
                        file.content_type or 'application/octet-stream',
                        document_ai_config,
                        ai_config_doc,
                        analysis_result,
                        total_pages
                    )
                else:
                    # Large PDF - split and process chunks
                    logger.info(f"🔪 Splitting PDF ({total_pages} pages) into chunks...")
                    analysis_result = await SurveyReportAnalyzeService._process_large_pdf(
                        file_content,
                        filename,
                        splitter,
                        document_ai_config,
                        ai_config_doc,
                        analysis_result,
                        total_pages
                    )
                
                # Validate ship name/IMO if not bypassed
                if not bypass_validation:
                    extracted_ship_name = analysis_result.get('ship_name', '').strip()
                    extracted_ship_imo = analysis_result.get('ship_imo', '').strip()
                    
                    # Fuzzy matching with 60% threshold (same as V1)
                    ship_name_match = False
                    ship_imo_match = False
                    similarity_score = 0.0
                    
                    if extracted_ship_name and ship_name:
                        # Calculate fuzzy similarity using difflib
                        from difflib import SequenceMatcher
                        
                        similarity_score = SequenceMatcher(
                            None, 
                            extracted_ship_name.lower(), 
                            ship_name.lower()
                        ).ratio()
                        
                        logger.info(f"🔍 Ship name similarity: {similarity_score:.2%} - '{extracted_ship_name}' vs '{ship_name}'")
                        
                        # 60% threshold
                        ship_name_match = similarity_score >= 0.6
                    
                    if extracted_ship_imo and ship_imo:
                        ship_imo_match = extracted_ship_imo == ship_imo
                        logger.info(f"🔍 IMO match: {ship_imo_match} - '{extracted_ship_imo}' vs '{ship_imo}'")
                    
                    # If neither matches, return validation error
                    if not ship_name_match and not ship_imo_match and extracted_ship_name:
                        logger.warning(
                            f"⚠️ Ship validation failed (similarity: {similarity_score:.2%}): "
                            f"Expected '{ship_name}' (IMO: {ship_imo}), "
                            f"Found '{extracted_ship_name}' (IMO: {extracted_ship_imo})"
                        )
                        
                        return {
                            "success": False,
                            "validation_error": True,
                            "extracted_ship_name": extracted_ship_name,
                            "extracted_ship_imo": extracted_ship_imo,
                            "expected_ship_name": ship_name,
                            "expected_ship_imo": ship_imo,
                            "similarity_score": similarity_score,
                            "message": f"Ship name mismatch (similarity: {similarity_score:.0%}). Please confirm or select correct ship."
                        }
                    elif ship_name_match:
                        logger.info(f"✅ Ship validation passed (similarity: {similarity_score:.2%})")
                
                # Success - return analysis
                logger.info("✅ Survey report analysis completed successfully")
                return {
                    "success": True,
                    "analysis": analysis_result
                }
                
            except Exception as e:
                logger.error(f"❌ Error during AI analysis: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Return partial result with file content (allows manual entry)
                return {
                    "success": False,
                    "message": "AI analysis failed. Please enter details manually.",
                    "analysis": {
                        "_file_content": analysis_result.get('_file_content'),
                        "_filename": filename,
                        "_content_type": file.content_type or 'application/octet-stream',
                        "_ship_name": ship_name,
                        "_summary_text": ""
                    }
                }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to analyze survey report: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze survey report: {str(e)}"
            )
    
    @staticmethod
    async def _process_single_pdf(
        file_content: bytes,
        filename: str,
        content_type: str,
        document_ai_config: Dict,
        ai_config_doc: Dict,
        analysis_result: Dict,
        total_pages: int
    ) -> Dict[str, Any]:
        """
        Process a single PDF with SMART PATH selection based on NEW LOGIC:
        
        - File ≤15 trang → Luôn dùng SLOW PATH (Document AI toàn bộ)
        - File >15 trang + có text layer (≥400 chars) → FAST PATH
        - File >15 trang + không có text layer → SLOW PATH (split 10+10)
        """
        from app.utils.pdf_text_extractor import (
            quick_check_text_layer,
            format_text_layer_summary,
            TEXT_LAYER_THRESHOLD
        )
        
        PAGE_THRESHOLD = 15  # Ngưỡng số trang
        
        logger.info(f"🔄 Processing single PDF: {filename} ({total_pages} pages)")
        
        analysis_result['_split_info'] = {
            'was_split': False,
            'total_pages': total_pages,
            'chunks_count': 1
        }
        
        summary_text = ""
        processing_path = None
        char_count = 0  # Initialize char_count
        text_check = None  # Initialize text_check
        text_layer_content = ""  # Store text layer content for merging
        
        # ⭐ NEW SMART PATH SELECTION LOGIC
        logger.info(f"⚡ SMART PATH: Checking file {filename} ({total_pages} pages)...")
        
        # Step 1: Check page count first
        if total_pages <= PAGE_THRESHOLD:
            # ≤15 trang → Check text layer để quyết định có gộp hay không
            text_check = quick_check_text_layer(file_content, filename)
            char_count = text_check.get("char_count", 0)
            
            if text_check.get("has_sufficient_text"):
                # ≤15 trang + có text layer → HYBRID PATH (Document AI + Text Layer song song)
                processing_path = "HYBRID_PATH"
                text_layer_content = text_check.get("text_content", "")
                logger.info(f"🔀 HYBRID PATH selected: File có {total_pages} trang (≤{PAGE_THRESHOLD}) + text layer ({char_count} chars) - gộp Document AI và Text Layer")
            else:
                # ≤15 trang + không có text layer → SLOW PATH (Document AI only)
                processing_path = "SLOW_PATH"
                logger.info(f"🐢 SLOW PATH selected: File có {total_pages} trang (≤{PAGE_THRESHOLD}) không có text layer - dùng Document AI toàn bộ")
            
        else:
            # >15 trang → Kiểm tra text layer
            text_check = quick_check_text_layer(file_content, filename)
            char_count = text_check.get("char_count", 0)
            
            if text_check.get("has_sufficient_text"):
                # >15 trang + có text layer → FAST PATH
                processing_path = "FAST_PATH"
                logger.info(f"⚡ FAST PATH selected: File {total_pages} trang (>{PAGE_THRESHOLD}) có text layer ({char_count} chars)")
            else:
                # >15 trang + không có text layer → SLOW PATH
                processing_path = "SLOW_PATH"
                logger.info(f"🐢 SLOW PATH selected: File {total_pages} trang (>{PAGE_THRESHOLD}) không có text layer ({char_count} chars)")
        
        # ⭐ Process based on selected path
        if processing_path == "HYBRID_PATH":
            # HYBRID PATH - Run Document AI và Text Layer SONG SONG, sau đó gộp
            import asyncio
            
            logger.info("🔀 HYBRID PATH: Running Document AI and Text Layer extraction in PARALLEL...")
            
            # Task 1: Document AI OCR
            async def run_document_ai():
                from app.utils.document_ai_helper import analyze_survey_report_with_document_ai
                return await analyze_survey_report_with_document_ai(
                    file_content=file_content,
                    filename=filename,
                    content_type=content_type,
                    document_ai_config=document_ai_config
                )
            
            # Task 2: Text Layer Correction (if needed)
            async def run_text_layer_correction():
                from app.utils.text_layer_correction import (
                    correct_text_layer_with_ai,
                    detect_ocr_quality
                )
                
                raw_text = text_layer_content
                quality_info = detect_ocr_quality(raw_text)
                
                if quality_info["needs_correction"]:
                    correction_result = await correct_text_layer_with_ai(
                        text_content=raw_text,
                        filename=filename,
                        ai_config=ai_config_doc
                    )
                    if correction_result["success"] and correction_result["correction_applied"]:
                        return {
                            "success": True,
                            "text": correction_result["corrected_text"],
                            "corrected": True
                        }
                
                return {"success": True, "text": raw_text, "corrected": False}
            
            # Run both tasks in parallel
            doc_ai_task = asyncio.create_task(run_document_ai())
            text_layer_task = asyncio.create_task(run_text_layer_correction())
            
            doc_ai_result, text_layer_result = await asyncio.gather(doc_ai_task, text_layer_task)
            
            # Merge results
            doc_ai_summary = ""
            if doc_ai_result.get('success'):
                doc_ai_summary = doc_ai_result.get('data', {}).get('summary', '')
                logger.info(f"   ✅ Document AI: {len(doc_ai_summary)} chars")
            else:
                logger.warning(f"   ⚠️ Document AI failed: {doc_ai_result.get('message')}")
            
            text_layer_text = text_layer_result.get("text", "")
            text_corrected = text_layer_result.get("corrected", False)
            logger.info(f"   ✅ Text Layer: {len(text_layer_text)} chars (corrected: {text_corrected})")
            
            # Create merged summary
            summary_parts = []
            summary_parts.append(f"=== SURVEY REPORT ANALYSIS ===")
            summary_parts.append(f"File: {filename}")
            summary_parts.append(f"Pages: {total_pages}")
            summary_parts.append(f"Processing: HYBRID PATH (Document AI + Text Layer merged)")
            summary_parts.append("")
            
            if doc_ai_summary:
                summary_parts.append("--- DOCUMENT AI OCR ---")
                summary_parts.append(doc_ai_summary)
                summary_parts.append("")
            
            if text_layer_text:
                summary_parts.append("--- TEXT LAYER CONTENT ---")
                if text_corrected:
                    summary_parts.append("(AI corrected)")
                summary_parts.append(text_layer_text)
            
            summary_text = "\n".join(summary_parts)
            logger.info(f"✅ HYBRID merged summary: {len(summary_text)} chars")
            
            analysis_result['processing_method'] = "hybrid_path_merged"
            
        elif processing_path == "FAST_PATH":
            # FAST PATH - Use text layer with AI correction if needed
            text_check = quick_check_text_layer(file_content, filename)
            char_count = text_check.get("char_count", 0)
            
            # Check text quality and apply AI correction if needed
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
                        char_count=len(corrected_text),
                        document_type="survey_report"
                    )
                    
                    # Add correction note to summary
                    summary_text = summary_text.replace(
                        "Processing: FAST PATH (Native PDF Text)",
                        "Processing: FAST PATH (Native PDF Text + AI Correction)"
                    )
                    analysis_result['processing_method'] = "text_layer_fast_path_corrected"
                else:
                    # Correction failed, use original
                    logger.warning("   ⚠️ AI correction failed, using original text")
                    summary_text = format_text_layer_summary(
                        text_content=raw_text,
                        filename=filename,
                        page_count=text_check["page_count"],
                        char_count=char_count,
                        document_type="survey_report"
                    )
                    analysis_result['processing_method'] = "text_layer_fast_path"
            else:
                # Text quality is good, use as-is
                logger.info("   ✅ Text quality good, skipping AI correction")
                summary_text = format_text_layer_summary(
                    text_content=raw_text,
                    filename=filename,
                    page_count=text_check["page_count"],
                    char_count=char_count,
                    document_type="survey_report"
                )
                analysis_result['processing_method'] = "text_layer_fast_path"
            
            logger.info(f"✅ Text layer summary: {len(summary_text)} characters")
            
        else:
            # ⚠️ SLOW PATH - Need Document AI
            logger.info("   📄 Calling Document AI for OCR processing...")
            
            from app.utils.document_ai_helper import analyze_survey_report_with_document_ai
            
            # Step 1: Call Document AI
            doc_ai_result = await analyze_survey_report_with_document_ai(
                file_content=file_content,
                filename=filename,
                content_type=content_type,
                document_ai_config=document_ai_config
            )
            
            if not doc_ai_result.get('success'):
                logger.warning(f"⚠️ Document AI failed: {doc_ai_result.get('message')}")
                analysis_result['processing_method'] = "document_ai_failed"
                analysis_result['_summary_text'] = ""
                analysis_result['_processing_path'] = processing_path
                return analysis_result
            
            summary_text = doc_ai_result.get('data', {}).get('summary', '')
            logger.info(f"✅ Document AI summary: {len(summary_text)} chars")
            analysis_result['processing_method'] = "document_ai_slow_path"
        
        # Add processing path metadata
        analysis_result['_processing_path'] = processing_path
        analysis_result['_text_layer_chars'] = char_count
        
        # Step 2: Perform Targeted OCR (for both paths)
        ocr_metadata = await SurveyReportAnalyzeService._perform_targeted_ocr(
            file_content,
            "single_pdf"
        )
        analysis_result['_ocr_info'] = ocr_metadata
        
        # Step 3: Merge OCR into summary if available
        enhanced_summary = summary_text
        
        if ocr_metadata.get('ocr_success') and ocr_metadata.get('ocr_text_merged'):
            try:
                from app.utils.targeted_ocr import get_ocr_processor
                ocr_processor = get_ocr_processor()
                ocr_result = ocr_processor.extract_from_pdf(
                    file_content, 
                    page_num=0,
                    report_no_field='survey_report_no'
                )
                
                if ocr_result.get('ocr_success'):
                    header_text = ocr_result.get('header_text', '').strip()
                    footer_text = ocr_result.get('footer_text', '').strip()
                    
                    if header_text or footer_text:
                        ocr_section = "\n\n" + "="*60 + "\n"
                        ocr_section += "ADDITIONAL INFORMATION FROM HEADER/FOOTER (OCR Extraction)\n"
                        ocr_section += "="*60 + "\n\n"
                        
                        if header_text:
                            ocr_section += "=== HEADER TEXT ===\n" + header_text + "\n\n"
                        if footer_text:
                            ocr_section += "=== FOOTER TEXT ===\n" + footer_text + "\n\n"
                        
                        enhanced_summary = summary_text + ocr_section
                        logger.info(f"✅ Enhanced summary with OCR: {len(enhanced_summary)} chars")
            except Exception as ocr_error:
                logger.warning(f"⚠️ Failed to merge OCR: {ocr_error}")
        
        # Step 4: Extract fields with System AI
        logger.info("🧠 Extracting fields with System AI...")
        
        ai_provider = ai_config_doc.get("provider", "google")
        ai_model = ai_config_doc.get("model", "gemini-2.0-flash-exp")
        use_emergent_key = ai_config_doc.get("use_emergent_key", True)
        
        # Log AI config for debugging
        logger.info(f"🔑 AI Config: use_emergent_key={use_emergent_key}, has_custom_key={bool(ai_config_doc.get('custom_api_key'))}")
        
        extracted_fields = await extract_survey_report_fields_from_summary(
            enhanced_summary,
            ai_provider,
            ai_model,
            use_emergent_key,
            filename,
            ai_config=ai_config_doc  # Pass full config for custom API key support
        )
        
        if extracted_fields:
            logger.info(f"✅ System AI extraction completed ({processing_path})")
            
            # Normalize issued_by to standard abbreviation
            if extracted_fields.get('issued_by'):
                try:
                    from app.utils.issued_by_abbreviation import normalize_issued_by
                    
                    original_issued_by = extracted_fields['issued_by']
                    normalized_issued_by = normalize_issued_by(original_issued_by)
                    
                    if normalized_issued_by != original_issued_by:
                        extracted_fields['issued_by'] = normalized_issued_by
                        logger.info(f"✅ Normalized Issued By: '{original_issued_by}' → '{normalized_issued_by}'")
                    else:
                        logger.info(f"ℹ️ Issued By kept as: '{original_issued_by}'")
                        
                except Exception as norm_error:
                    logger.error(f"❌ Error normalizing issued_by: {norm_error}")
            
            analysis_result.update(extracted_fields)
        else:
            logger.warning("⚠️ System AI extraction returned no fields")
            analysis_result['processing_method'] = f"{processing_path.lower()}_no_fields"
        
        # Try to extract report_form from filename if not found
        if not analysis_result.get('report_form'):
            filename_form = extract_report_form_from_filename(filename)
            if filename_form:
                analysis_result['report_form'] = filename_form
                logger.info(f"✅ Extracted report_form from filename: '{filename_form}'")
        
        analysis_result['_summary_text'] = enhanced_summary
        
        return analysis_result
    
    @staticmethod
    async def _process_large_pdf(
        file_content: bytes,
        filename: str,
        splitter: PDFSplitter,
        document_ai_config: Dict,
        ai_config_doc: Dict,
        analysis_result: Dict,
        total_pages: int
    ) -> Dict[str, Any]:
        """
        Process large PDF (>15 pages) with NEW SMART logic:
        
        1. Check text layer first (for entire PDF)
        2. If has text layer >= 400 chars → FAST PATH (no split, no Document AI)
        3. If no text layer → SLOW PATH:
           - Split: 10 first pages + 10 last pages
           - Document AI for 2 chunks
           - OCR header/footer for Report Form
        """
        from app.utils.document_ai_helper import analyze_survey_report_with_document_ai
        from app.utils.pdf_text_extractor import quick_check_text_layer, TEXT_LAYER_THRESHOLD
        from app.utils.pdf_splitter import split_first_and_last
        import time
        
        process_start_time = time.time()
        logger.info(f"⏱️ [TIMING] Starting large PDF processing: {filename} ({total_pages} pages)")
        
        # ⭐ Step 1: Check text layer for ENTIRE PDF
        logger.info(f"⚡ SMART PATH: Checking text layer for large PDF ({total_pages} pages)...")
        text_check = quick_check_text_layer(file_content, filename)
        char_count = text_check.get("char_count", 0)
        
        processing_path = None
        summary_text = ""
        
        if text_check.get("has_sufficient_text"):
            # ✅ FAST PATH - Use text layer with AI correction if needed
            processing_path = "FAST_PATH"
            logger.info(f"⚡ FAST PATH selected for large PDF: {char_count} chars >= {TEXT_LAYER_THRESHOLD} threshold")
            
            # ⭐ Check text quality and apply AI correction if needed
            from app.utils.text_layer_correction import (
                correct_text_layer_with_ai,
                detect_ocr_quality
            )
            from app.utils.pdf_text_extractor import format_text_layer_summary
            
            raw_text = text_check["text_content"]
            quality_info = detect_ocr_quality(raw_text)
            
            logger.info(f"   📊 Text quality: {quality_info['quality_score']}%, needs_correction: {quality_info['needs_correction']}")
            
            if quality_info["needs_correction"]:
                # Apply AI correction for low-quality text
                logger.info(f"   🔧 Applying AI text correction for large PDF (quality issues: {quality_info['issues_detected']})")
                
                correction_result = await correct_text_layer_with_ai(
                    text_content=raw_text,
                    filename=filename,
                    ai_config=ai_config_doc
                )
                
                if correction_result["success"] and correction_result["correction_applied"]:
                    corrected_text = correction_result["corrected_text"]
                    logger.info(f"   ✅ Text corrected in {correction_result['processing_time']}s")
                    
                    summary_text = format_text_layer_summary(
                        text_content=corrected_text,
                        filename=filename,
                        page_count=total_pages,
                        char_count=len(corrected_text),
                        document_type="survey_report"
                    )
                    
                    summary_text = summary_text.replace(
                        "Processing: FAST PATH (Native PDF Text)",
                        "Processing: FAST PATH (Native PDF Text + AI Correction)"
                    )
                    analysis_result['processing_method'] = "text_layer_fast_path_large_pdf_corrected"
                else:
                    logger.warning("   ⚠️ AI correction failed, using original text")
                    summary_text = format_text_layer_summary(
                        text_content=raw_text,
                        filename=filename,
                        page_count=total_pages,
                        char_count=char_count,
                        document_type="survey_report"
                    )
                    analysis_result['processing_method'] = "text_layer_fast_path_large_pdf"
            else:
                # Text quality is good, use as-is
                logger.info("   ✅ Text quality good, skipping AI correction")
                summary_text = format_text_layer_summary(
                    text_content=raw_text,
                    filename=filename,
                    page_count=total_pages,
                    char_count=char_count,
                    document_type="survey_report"
                )
                analysis_result['processing_method'] = "text_layer_fast_path_large_pdf"
            
            logger.info(f"✅ Text layer summary: {len(summary_text)} characters")
            
            analysis_result['_split_info'] = {
                'was_split': False,
                'total_pages': total_pages,
                'processing_path': 'FAST_PATH',
                'text_layer_chars': char_count,
                'document_ai_calls': 0,
                'note': 'Used text layer extraction - no splitting required'
            }
            analysis_result['processing_method'] = "text_layer_fast_path_large_pdf"
            
        else:
            # ⚠️ SLOW PATH - Need Document AI (10 first + 10 last pages)
            processing_path = "SLOW_PATH"
            logger.info(f"🐢 SLOW PATH selected for large PDF: {char_count} chars < {TEXT_LAYER_THRESHOLD} threshold")
            logger.info("   📄 Large scanned PDF - splitting into first 10 + last 10 pages")
            
            # Split into 2 chunks: first 10 + last 10 pages
            chunks = split_first_and_last(file_content, filename, first_pages=10, last_pages=10)
            
            analysis_result['_split_info'] = {
                'was_split': True,
                'total_pages': total_pages,
                'processing_path': 'SLOW_PATH',
                'text_layer_chars': char_count,
                'chunks_count': len(chunks),
                'chunks_description': 'first_10_last_10',
                'processed_pages': sum(c.get('page_count', 0) for c in chunks),
                'skipped_pages': total_pages - sum(c.get('page_count', 0) for c in chunks),
                'document_ai_calls': len(chunks)
            }
            
            # Process chunks with Document AI
            import asyncio
            
            async def process_chunk_with_doc_ai(chunk, chunk_index):
                """Process a single chunk with Document AI"""
                chunk_type = chunk.get('chunk_type', 'unknown')
                logger.info(f"🔄 Processing {chunk_type} chunk (pages {chunk['page_range']})")
                
                try:
                    doc_ai_result = await analyze_survey_report_with_document_ai(
                        file_content=chunk['content'],
                        filename=chunk['filename'],
                        content_type='application/pdf',
                        document_ai_config=document_ai_config
                    )
                    
                    if doc_ai_result.get('success'):
                        chunk_summary = doc_ai_result.get('data', {}).get('summary', '')
                        if chunk_summary:
                            logger.info(f"✅ {chunk_type.capitalize()} chunk completed - {len(chunk_summary)} chars")
                            return {
                                'success': True,
                                'chunk_type': chunk_type,
                                'chunk_num': chunk['chunk_num'],
                                'page_range': chunk['page_range'],
                                'summary_text': chunk_summary
                            }
                    
                    return {
                        'success': False,
                        'chunk_type': chunk_type,
                        'chunk_num': chunk['chunk_num'],
                        'page_range': chunk['page_range'],
                        'error': doc_ai_result.get('message', 'Empty or failed')
                    }
                    
                except Exception as e:
                    logger.error(f"❌ {chunk_type.capitalize()} chunk exception: {e}")
                    return {
                        'success': False,
                        'chunk_type': chunk_type,
                        'chunk_num': chunk['chunk_num'],
                        'error': str(e)
                    }
            
            # Process both chunks (can be parallel or sequential)
            logger.info(f"🚀 Processing {len(chunks)} chunks with Document AI...")
            
            chunk_results = []
            for i, chunk in enumerate(chunks):
                result = await process_chunk_with_doc_ai(chunk, i)
                chunk_results.append(result)
                # Small delay between chunks
                if i < len(chunks) - 1:
                    await asyncio.sleep(1)
            
            # Merge chunk summaries
            successful_chunks = [cr for cr in chunk_results if cr.get('success')]
            
            if not successful_chunks:
                logger.error("❌ All chunks failed processing")
                analysis_result['processing_method'] = "all_chunks_failed"
                analysis_result['_summary_text'] = ""
                return analysis_result
            
            # Build merged summary
            summary_parts = []
            summary_parts.append("=" * 80)
            summary_parts.append("SURVEY REPORT SUMMARY - FIRST/LAST PAGES EXTRACTION")
            summary_parts.append(f"File: {filename}")
            summary_parts.append(f"Total Pages: {total_pages}")
            summary_parts.append("Processing: SLOW PATH (Scanned PDF - Document AI)")
            summary_parts.append("=" * 80)
            summary_parts.append("")
            
            for cr in chunk_results:
                chunk_type = cr.get('chunk_type', 'unknown').upper()
                page_range = cr.get('page_range', 'Unknown')
                
                summary_parts.append("=" * 80)
                summary_parts.append(f"{chunk_type} PAGES (Pages {page_range})")
                summary_parts.append("=" * 80)
                
                if cr.get('success'):
                    summary_parts.append(cr.get('summary_text', ''))
                else:
                    summary_parts.append(f"[Processing failed: {cr.get('error', 'Unknown error')}]")
                
                summary_parts.append("")
            
            summary_text = "\n".join(summary_parts)
            logger.info(f"📄 Merged summary from {len(successful_chunks)}/{len(chunks)} chunks: {len(summary_text)} chars")
            
            analysis_result['_split_info']['successful_chunks'] = len(successful_chunks)
            analysis_result['_split_info']['failed_chunks'] = len(chunks) - len(successful_chunks)
            analysis_result['processing_method'] = "slow_path_first_last_pages"
        
        # ⭐ Step 2: OCR Header/Footer for Report Form (both paths)
        logger.info("🔍 Running targeted OCR for Report Form...")
        ocr_metadata = await SurveyReportAnalyzeService._perform_targeted_ocr(
            file_content,
            "large_pdf_first_page"
        )
        analysis_result['_ocr_info'] = ocr_metadata
        
        # Merge OCR text into summary
        if ocr_metadata.get('ocr_success') and ocr_metadata.get('ocr_text_merged'):
            try:
                from app.utils.targeted_ocr import get_ocr_processor
                ocr_processor = get_ocr_processor()
                ocr_result = ocr_processor.extract_from_pdf(
                    file_content, 
                    page_num=0,
                    report_no_field='survey_report_no'
                )
                
                if ocr_result.get('ocr_success'):
                    header_text = ocr_result.get('header_text', '').strip()
                    footer_text = ocr_result.get('footer_text', '').strip()
                    report_form = ocr_result.get('report_form')
                    report_no = ocr_result.get('survey_report_no')
                    
                    if header_text or footer_text or report_form or report_no:
                        ocr_section = "\n\n" + "="*60 + "\n"
                        ocr_section += "HEADER/FOOTER OCR EXTRACTION (First Page)\n"
                        ocr_section += "="*60 + "\n\n"
                        
                        if report_form:
                            ocr_section += f"Report Form (OCR): {report_form}\n"
                        if report_no:
                            ocr_section += f"Report No (OCR): {report_no}\n"
                        if header_text:
                            ocr_section += f"\n=== HEADER ===\n{header_text}\n"
                        if footer_text:
                            ocr_section += f"\n=== FOOTER ===\n{footer_text}\n"
                        
                        summary_text = summary_text + ocr_section
                        logger.info(f"✅ Enhanced summary with OCR: report_form={report_form}, report_no={report_no}")
            except Exception as ocr_error:
                logger.warning(f"⚠️ Failed to merge OCR: {ocr_error}")
        
        # ⭐ Step 3: Extract fields with Gemini AI
        logger.info("🧠 Extracting fields from summary...")
        
        ai_provider = ai_config_doc.get("provider", "google")
        ai_model = ai_config_doc.get("model", "gemini-2.0-flash-exp")
        use_emergent_key = ai_config_doc.get("use_emergent_key", True)
        
        # Log AI config for debugging
        logger.info(f"🔑 AI Config: use_emergent_key={use_emergent_key}, has_custom_key={bool(ai_config_doc.get('custom_api_key'))}")
        
        extracted_fields = await extract_survey_report_fields_from_summary(
            summary_text,
            ai_provider,
            ai_model,
            use_emergent_key,
            filename,
            ai_config=ai_config_doc  # Pass full config for custom API key support
        )
        
        if extracted_fields:
            logger.info(f"✅ Field extraction completed ({processing_path})")
            
            # Normalize issued_by
            if extracted_fields.get('issued_by'):
                try:
                    from app.utils.issued_by_abbreviation import normalize_issued_by
                    original = extracted_fields['issued_by']
                    normalized = normalize_issued_by(original)
                    if normalized != original:
                        extracted_fields['issued_by'] = normalized
                        logger.info(f"✅ Normalized Issued By: '{original}' → '{normalized}'")
                except Exception as e:
                    logger.warning(f"⚠️ Normalization error: {e}")
            
            analysis_result.update(extracted_fields)
        else:
            logger.warning("⚠️ Field extraction returned no results")
        
        # Try to extract report_form from filename if not found
        if not analysis_result.get('report_form'):
            filename_form = extract_report_form_from_filename(filename)
            if filename_form:
                analysis_result['report_form'] = filename_form
                logger.info(f"✅ Extracted report_form from filename: '{filename_form}'")
        
        analysis_result['_summary_text'] = summary_text
        analysis_result['_processing_path'] = processing_path
        
        # Log timing
        total_time = time.time() - process_start_time
        logger.info(f"⏱️ [TIMING] Large PDF processing completed in {total_time:.2f}s ({processing_path})")
        analysis_result['_timing'] = {
            'total_seconds': round(total_time, 2),
            'processing_path': processing_path,
            'total_pages': total_pages
        }
        
        return analysis_result
    
    @staticmethod
    async def _perform_targeted_ocr(pdf_content: bytes, source: str) -> Dict[str, Any]:
        """Perform Targeted OCR to extract header/footer text"""
        
        ocr_metadata = {
            'ocr_attempted': False,
            'ocr_success': False,
            'ocr_text_merged': False,
            'header_text_length': 0,
            'footer_text_length': 0,
            'note': f'OCR attempted on {source}'
        }
        
        try:
            from app.utils.targeted_ocr import get_ocr_processor
            
            ocr_processor = get_ocr_processor()
            ocr_metadata['ocr_attempted'] = True
            
            if ocr_processor.is_available():
                logger.info(f"✅ OCR processor available - extracting from {source}...")
                
                # Extract from first page (page 0)
                ocr_result = ocr_processor.extract_from_pdf(
                    pdf_content, 
                    page_num=0,
                    report_no_field='survey_report_no'
                )
                
                if ocr_result.get('ocr_success'):
                    logger.info("✅ Targeted OCR completed successfully")
                    
                    header_text = ocr_result.get('header_text', '').strip()
                    footer_text = ocr_result.get('footer_text', '').strip()
                    
                    ocr_metadata['ocr_success'] = True
                    ocr_metadata['header_text_length'] = len(header_text)
                    ocr_metadata['footer_text_length'] = len(footer_text)
                    
                    if header_text or footer_text:
                        ocr_metadata['ocr_text_merged'] = True
                else:
                    logger.warning("⚠️ OCR extraction returned no results")
            else:
                logger.warning("⚠️ OCR processor not available (Tesseract not installed)")
        except Exception as ocr_error:
            logger.error(f"❌ Error during OCR extraction: {ocr_error}")
            ocr_metadata['ocr_error'] = str(ocr_error)
        
        return ocr_metadata
