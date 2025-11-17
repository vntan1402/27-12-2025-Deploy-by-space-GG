"""
Test Report Analysis Service
Handles AI-powered analysis of test report PDFs
Based on Survey Report pattern with Test Report specifics
"""
import logging
import base64
import traceback
from typing import Dict, Any
from fastapi import HTTPException, UploadFile

from app.db.mongodb import mongo_db
from app.models.user import UserResponse
from app.utils.pdf_splitter import PDFSplitter, create_enhanced_merged_summary
from app.utils.test_report_ai import extract_test_report_fields_from_summary, extract_report_form_from_filename
from app.utils.test_report_valid_date_calculator import calculate_valid_date

logger = logging.getLogger(__name__)


class TestReportAnalyzeService:
    """Service for analyzing test report files"""
    
    @staticmethod
    async def analyze_file(
        file: UploadFile,
        ship_id: str,
        bypass_validation: bool,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """
        Analyze test report file using Google Document AI
        
        Process:
        1. Validate PDF file
        2. Check if PDF needs splitting (>15 pages)
        3. Process with Document AI
        4. Perform Targeted OCR on first page
        5. Extract fields with System AI
        6. Calculate Valid Date (UNIQUE TO TEST REPORT)
        7. Normalize issued_by
        8. Validate ship name/IMO
        9. Return analysis data + file content (base64) for later upload
        
        Args:
            file: PDF file uploaded
            ship_id: Ship ID to validate against
            bypass_validation: Skip ship validation if True
            current_user: Current authenticated user
        
        Returns:
            Dict with success status and analysis data
        """
        try:
            logger.info(f"📋 Starting test report analysis for ship_id: {ship_id}")
            
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
            
            logger.info(f"📄 Processing test report file: {filename} ({len(file_content)} bytes)")
            
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
            
            # Get AI configuration
            ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
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
            
            logger.info("🤖 Analyzing test report with AI...")
            
            # Initialize analysis result
            analysis_result = {
                "test_report_name": "",
                "report_form": "",
                "test_report_no": "",
                "issued_by": "",
                "issued_date": "",
                "valid_date": "",
                "ship_name": "",
                "ship_imo": "",
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
                    analysis_result = await TestReportAnalyzeService._process_single_pdf(
                        file_content,
                        filename,
                        file.content_type or 'application/octet-stream',
                        document_ai_config,
                        ai_config_doc,
                        analysis_result,
                        total_pages,
                        ship_id
                    )
                else:
                    # Large PDF - split and process chunks
                    logger.info(f"🔪 Splitting PDF ({total_pages} pages) into chunks...")
                    analysis_result = await TestReportAnalyzeService._process_large_pdf(
                        file_content,
                        filename,
                        splitter,
                        document_ai_config,
                        ai_config_doc,
                        analysis_result,
                        total_pages,
                        ship_id
                    )
                
                # Validate ship name/IMO if not bypassed
                if not bypass_validation:
                    extracted_ship_name = analysis_result.get('ship_name', '').strip()
                    extracted_ship_imo = analysis_result.get('ship_imo', '').strip()
                    
                    # Fuzzy matching with 60% threshold (same as Survey Report)
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
                logger.info("✅ Test report analysis completed successfully")
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
            logger.error(f"❌ Failed to analyze test report: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze test report: {str(e)}"
            )
    
    @staticmethod
    async def _process_single_pdf(
        file_content: bytes,
        filename: str,
        content_type: str,
        document_ai_config: Dict,
        ai_config_doc: Dict,
        analysis_result: Dict,
        total_pages: int,
        ship_id: str
    ) -> Dict[str, Any]:
        """Process a single PDF (≤15 pages)"""
        from app.utils.document_ai_helper import analyze_test_report_with_document_ai
        
        logger.info(f"🔄 Processing single PDF: {filename} ({total_pages} pages)")
        
        analysis_result['_split_info'] = {
            'was_split': False,
            'total_pages': total_pages,
            'chunks_count': 1
        }
        
        # Step 1: Call Document AI
        doc_ai_result = await analyze_test_report_with_document_ai(
            file_content=file_content,
            filename=filename,
            content_type=content_type,
            document_ai_config=document_ai_config
        )
        
        if not doc_ai_result.get('success'):
            logger.warning(f"⚠️ Document AI failed: {doc_ai_result.get('message')}")
            analysis_result['processing_method'] = "document_ai_failed"
            analysis_result['_summary_text'] = ""
        else:
            summary_text = doc_ai_result.get('data', {}).get('summary', '')
            logger.info(f"✅ Document AI summary: {len(summary_text)} chars")
            
            # Step 2: Perform Targeted OCR
            ocr_metadata = await TestReportAnalyzeService._perform_targeted_ocr(
                file_content,
                "single_pdf"
            )
            analysis_result['_ocr_info'] = ocr_metadata
            
            # Step 3: Merge OCR into summary if available
            enhanced_summary = summary_text
            
            if ocr_metadata.get('ocr_success') and ocr_metadata.get('ocr_text_merged'):
                # Get OCR text from processor
                try:
                    from app.utils.targeted_ocr import get_ocr_processor
                    ocr_processor = get_ocr_processor()
                    ocr_result = ocr_processor.extract_from_pdf(
                        file_content, 
                        page_num=0,
                        report_no_field='test_report_no'
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
            
            extracted_fields = await extract_test_report_fields_from_summary(
                enhanced_summary,
                ai_provider,
                ai_model,
                use_emergent_key,
                filename
            )
            
            if extracted_fields:
                logger.info("✅ System AI extraction completed")
                
                # Step 5: Calculate Valid Date (UNIQUE TO TEST REPORT)
                test_report_name = extracted_fields.get('test_report_name', '')
                issued_date = extracted_fields.get('issued_date', '')
                
                if test_report_name and issued_date:
                    logger.info("🧮 Calculating Valid Date from Issued Date + Equipment Interval...")
                    
                    try:
                        calculated_valid_date = await calculate_valid_date(
                            test_report_name=test_report_name,
                            issued_date=issued_date,
                            ship_id=ship_id,
                            mongo_db=mongo_db
                        )
                        
                        if calculated_valid_date:
                            extracted_fields['valid_date'] = calculated_valid_date
                            logger.info(f"✅ Calculated Valid Date: {calculated_valid_date}")
                        else:
                            logger.warning("⚠️ Could not calculate Valid Date")
                    except Exception as calc_error:
                        logger.error(f"❌ Error during Valid Date calculation: {calc_error}")
                else:
                    logger.warning(f"⚠️ Missing fields for Valid Date calculation: test_report_name={bool(test_report_name)}, issued_date={bool(issued_date)}")
                
                # Step 6: Normalize issued_by to standard abbreviation
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
                        # Keep original value if normalization fails
                
                analysis_result.update(extracted_fields)
                analysis_result['processing_method'] = "full_analysis"
            else:
                logger.warning("⚠️ System AI extraction returned no fields")
                analysis_result['processing_method'] = "document_ai_only"
            
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
        total_pages: int,
        ship_id: str
    ) -> Dict[str, Any]:
        """Process a large PDF (>15 pages) by splitting into chunks"""
        from app.utils.document_ai_helper import analyze_test_report_with_document_ai
        
        chunks = splitter.split_pdf(file_content, filename)
        total_chunks = len(chunks)
        logger.info(f"📦 Created {total_chunks} chunks from {total_pages}-page PDF")
        
        # LIMIT: Process max 5 chunks only (like backend-v1)
        MAX_CHUNKS = 5
        chunks_to_process = chunks[:MAX_CHUNKS]
        skipped_chunks = total_chunks - len(chunks_to_process)
        
        if skipped_chunks > 0:
            logger.warning(f"⚠️ File has {total_chunks} chunks. Processing first {MAX_CHUNKS} chunks only, skipping {skipped_chunks} chunks")
            # Calculate skipped pages
            skipped_pages = sum(chunk.get('page_count', 0) for chunk in chunks[MAX_CHUNKS:])
            processed_pages = total_pages - skipped_pages
            logger.info(f"📊 Processing {processed_pages}/{total_pages} pages ({skipped_pages} pages skipped)")
        
        analysis_result['_split_info'] = {
            'was_split': True,
            'total_pages': total_pages,
            'total_chunks': total_chunks,
            'processed_chunks': len(chunks_to_process),
            'skipped_chunks': skipped_chunks,
            'max_chunks_limit': MAX_CHUNKS,
            'was_limited': skipped_chunks > 0
        }
        
        # Step 1: Process chunks with Document AI (Staggered Parallel Processing)
        # Start each chunk with 2s delay to avoid rate limits, but process in parallel
        import asyncio
        
        async def process_single_chunk(chunk, chunk_index):
            """Process a single chunk with Document AI"""
            logger.info(f"🔄 Processing chunk {chunk_index+1}/{len(chunks_to_process)} (pages {chunk['page_range']})")
            
            try:
                doc_ai_result = await analyze_test_report_with_document_ai(
                    file_content=chunk['content'],
                    filename=chunk['filename'],
                    content_type='application/pdf',
                    document_ai_config=document_ai_config
                )
                
                if doc_ai_result.get('success'):
                    summary_text = doc_ai_result.get('data', {}).get('summary', '')
                    
                    if summary_text:
                        logger.info(f"✅ Chunk {chunk_index+1} completed - {len(summary_text)} chars")
                        return {
                            'success': True,
                            'chunk_num': chunk['chunk_num'],
                            'page_range': chunk['page_range'],
                            'summary_text': summary_text
                        }
                    else:
                        logger.warning(f"⚠️ Chunk {chunk_index+1} returned empty summary")
                        return {
                            'success': False,
                            'chunk_num': chunk['chunk_num'],
                            'page_range': chunk['page_range'],
                            'error': 'Empty summary'
                        }
                else:
                    error_msg = doc_ai_result.get('message', 'Unknown error')
                    logger.error(f"❌ Chunk {chunk_index+1} failed: {error_msg}")
                    return {
                        'success': False,
                        'chunk_num': chunk['chunk_num'],
                        'page_range': chunk['page_range'],
                        'error': error_msg
                    }
            except Exception as e:
                logger.error(f"❌ Chunk {chunk_index+1} exception: {e}")
                return {
                    'success': False,
                    'chunk_num': chunk['chunk_num'],
                    'page_range': chunk['page_range'],
                    'error': str(e)
                }
        
        # Create tasks with staggered start (2s delay between each chunk start)
        logger.info(f"🚀 Starting staggered parallel processing of {len(chunks_to_process)} chunks (2s delay between starts)...")
        tasks = []
        for i, chunk in enumerate(chunks_to_process):
            # Add 2s delay before starting each chunk (except first)
            if i > 0:
                logger.info(f"⏳ Waiting 2s before starting chunk {i+1}...")
                await asyncio.sleep(2)
            
            # Create and start task immediately
            task = asyncio.create_task(process_single_chunk(chunk, i))
            tasks.append(task)
            logger.info(f"🚀 Chunk {i+1} task created and started")
        
        # Wait for all chunks to complete (parallel execution)
        logger.info(f"⏳ Waiting for all {len(chunks_to_process)} chunks to complete...")
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(chunk_results):
            if isinstance(result, Exception):
                logger.error(f"❌ Chunk {i+1} raised exception: {result}")
                processed_results.append({
                    'success': False,
                    'chunk_num': i + 1,
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        chunk_results = processed_results
        
        # Step 2: Merge summaries
        successful_chunks = [cr for cr in chunk_results if cr.get('success')]
        
        if not successful_chunks:
            logger.error("❌ All chunks failed processing")
            analysis_result['processing_method'] = "all_chunks_failed"
            analysis_result['_summary_text'] = ""
            return analysis_result
        
        failed_chunks = len(chunks_to_process) - len(successful_chunks)
        logger.info(f"✅ Split PDF processing complete: {len(successful_chunks)}/{len(chunks_to_process)} chunks successful, {failed_chunks} failed, {skipped_chunks} chunks skipped")
        
        # Create merged summary using PDFSplitter helper
        temp_merged_data = {
            'test_report_name': 'Processing...',
            'test_report_no': 'Processing...',
            'issued_by': 'Processing...',
            'issued_date': 'Processing...'
        }
        
        merged_summary = create_enhanced_merged_summary(
            chunk_results=chunk_results,
            merged_data=temp_merged_data,
            original_filename=filename,
            total_pages=total_pages,
            document_type='test_report'
        )
        
        logger.info(f"📄 Merged summary created: {len(merged_summary)} chars")
        
        # Step 3: Perform Targeted OCR on first chunk
        if chunks:
            ocr_metadata = await TestReportAnalyzeService._perform_targeted_ocr(
                chunks[0]['content'],
                "first_chunk"
            )
            analysis_result['_ocr_info'] = ocr_metadata
            
            # Merge OCR if successful
            if ocr_metadata.get('ocr_success'):
                try:
                    from app.utils.targeted_ocr import get_ocr_processor
                    ocr_processor = get_ocr_processor()
                    ocr_result = ocr_processor.extract_from_pdf(
                        chunks[0]['content'], 
                        page_num=0,
                        report_no_field='test_report_no'
                    )
                    
                    if ocr_result.get('ocr_success'):
                        header_text = ocr_result.get('header_text', '').strip()
                        footer_text = ocr_result.get('footer_text', '').strip()
                        
                        if header_text or footer_text:
                            ocr_section = "\n\n" + "="*60 + "\n"
                            ocr_section += "OCR HEADER/FOOTER (from first page)\n"
                            ocr_section += "="*60 + "\n\n"
                            
                            if header_text:
                                ocr_section += "=== HEADER ===\n" + header_text + "\n\n"
                            if footer_text:
                                ocr_section += "=== FOOTER ===\n" + footer_text + "\n\n"
                            
                            merged_summary = merged_summary + ocr_section
                            logger.info(f"✅ Merged summary with OCR: {len(merged_summary)} chars")
                except Exception as ocr_error:
                    logger.warning(f"⚠️ Failed to merge OCR: {ocr_error}")
        
        # Step 4: Extract fields from merged summary with System AI
        logger.info("🧠 Extracting fields from merged summary...")
        
        ai_provider = ai_config_doc.get("provider", "google")
        ai_model = ai_config_doc.get("model", "gemini-2.0-flash-exp")
        use_emergent_key = ai_config_doc.get("use_emergent_key", True)
        
        extracted_fields = await extract_test_report_fields_from_summary(
            merged_summary,
            ai_provider,
            ai_model,
            use_emergent_key,
            filename
        )
        
        if extracted_fields:
            logger.info("✅ System AI extraction from merged summary completed")
            
            # Step 5: Calculate Valid Date (UNIQUE TO TEST REPORT - for large PDF)
            test_report_name = extracted_fields.get('test_report_name', '')
            issued_date = extracted_fields.get('issued_date', '')
            
            if test_report_name and issued_date:
                logger.info("🧮 Calculating Valid Date from Issued Date + Equipment Interval (large PDF)...")
                
                try:
                    calculated_valid_date = await calculate_valid_date(
                        test_report_name=test_report_name,
                        issued_date=issued_date,
                        ship_id=ship_id,
                        mongo_db=mongo_db
                    )
                    
                    if calculated_valid_date:
                        extracted_fields['valid_date'] = calculated_valid_date
                        logger.info(f"✅ Calculated Valid Date (large PDF): {calculated_valid_date}")
                    else:
                        logger.warning("⚠️ Could not calculate Valid Date (large PDF)")
                except Exception as calc_error:
                    logger.error(f"❌ Error during Valid Date calculation (large PDF): {calc_error}")
            else:
                logger.warning(f"⚠️ Missing fields for Valid Date calculation (large PDF): test_report_name={bool(test_report_name)}, issued_date={bool(issued_date)}")
            
            # Step 6: Normalize issued_by to standard abbreviation (large PDF)
            if extracted_fields.get('issued_by'):
                try:
                    from app.utils.issued_by_abbreviation import normalize_issued_by
                    
                    original_issued_by = extracted_fields['issued_by']
                    normalized_issued_by = normalize_issued_by(original_issued_by)
                    
                    if normalized_issued_by != original_issued_by:
                        extracted_fields['issued_by'] = normalized_issued_by
                        logger.info(f"✅ Normalized Issued By (large PDF): '{original_issued_by}' → '{normalized_issued_by}'")
                    else:
                        logger.info(f"ℹ️ Issued By kept as (large PDF): '{original_issued_by}'")
                        
                except Exception as norm_error:
                    logger.error(f"❌ Error normalizing issued_by (large PDF): {norm_error}")
                    # Keep original value if normalization fails
            
            analysis_result.update(extracted_fields)
            
            # Recreate summary with extracted data
            final_summary = create_enhanced_merged_summary(
                chunk_results=chunk_results,
                merged_data=extracted_fields,
                original_filename=filename,
                total_pages=total_pages,
                document_type='test_report'
            )
            
            analysis_result['_summary_text'] = final_summary
            analysis_result['processing_method'] = "split_pdf_full_analysis"
            
            # Update split info
            analysis_result['_split_info']['successful_chunks'] = len(successful_chunks)
            analysis_result['_split_info']['failed_chunks'] = len(chunks) - len(successful_chunks)
        else:
            logger.warning("⚠️ System AI extraction returned no fields")
            analysis_result['_summary_text'] = merged_summary
            analysis_result['processing_method'] = "split_pdf_merge_only"
        
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
            
            ocr_result = ocr_processor.extract_from_pdf(
                pdf_content,
                page_num=0,
                report_no_field='test_report_no'
            )
            
            if ocr_result.get('ocr_success'):
                ocr_metadata['ocr_success'] = True
                ocr_metadata['ocr_text_merged'] = True
                
                header_text = ocr_result.get('header_text', '')
                footer_text = ocr_result.get('footer_text', '')
                
                ocr_metadata['header_text_length'] = len(header_text)
                ocr_metadata['footer_text_length'] = len(footer_text)
                
                logger.info(f"✅ OCR successful - Header: {len(header_text)} chars, Footer: {len(footer_text)} chars")
            else:
                logger.warning(f"⚠️ OCR failed: {ocr_result.get('ocr_error', 'Unknown error')}")
                
        except Exception as e:
            logger.warning(f"⚠️ OCR processing error: {e}")
            ocr_metadata['note'] = f"OCR error: {str(e)}"
        
        return ocr_metadata
