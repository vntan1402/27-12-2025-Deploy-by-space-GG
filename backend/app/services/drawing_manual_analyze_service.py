"""
Drawing & Manual Analysis Service
Handles AI-powered analysis of drawing & manual PDFs
Based on Test Report pattern but simpler (no valid_date calculation, no OCR)
"""
import logging
import base64
import asyncio
import traceback
from typing import Dict, Any
from fastapi import HTTPException, UploadFile

from app.db.mongodb import mongo_db
from app.models.user import UserResponse
from app.utils.pdf_splitter import PDFSplitter, create_enhanced_merged_summary
from app.utils.drawing_manual_ai import extract_drawings_manuals_fields_from_summary

logger = logging.getLogger(__name__)


class DrawingManualAnalyzeService:
    """Service for analyzing drawing & manual files"""
    
    @staticmethod
    async def analyze_file(
        file: UploadFile,
        ship_id: str,
        bypass_validation: bool,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """
        Analyze drawing/manual file using Google Document AI
        
        Process:
        1. Validate PDF file
        2. Check if PDF needs splitting (>15 pages)
        3. Process with Document AI
        4. Extract fields with System AI
        5. Normalize document_name & approved_by
        6. Return analysis data + file content (base64) for later upload
        
        Args:
            file: PDF file uploaded
            ship_id: Ship ID to validate against
            bypass_validation: Skip ship validation if True
            current_user: Current authenticated user
        
        Returns:
            Dict with success status and analysis data
        """
        try:
            logger.info(f"📐 Starting drawing/manual analysis for ship_id: {ship_id}")
            
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
            
            logger.info(f"📄 Processing drawing/manual file: {filename} ({len(file_content)} bytes)")
            
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
            
            logger.info("🤖 Analyzing drawing/manual with AI...")
            
            # Initialize analysis result
            analysis_result = {
                "document_name": "",
                "document_no": "",
                "approved_by": "",
                "approved_date": "",
                "note": "",
                "status": "Unknown",
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
                    analysis_result = await DrawingManualAnalyzeService._process_single_pdf(
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
                    analysis_result = await DrawingManualAnalyzeService._process_large_pdf(
                        file_content,
                        filename,
                        splitter,
                        document_ai_config,
                        ai_config_doc,
                        analysis_result,
                        total_pages
                    )
                
                # Success - return analysis
                logger.info("✅ Drawing/manual analysis completed successfully")
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
            logger.error(f"❌ Failed to analyze drawing/manual: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze drawing/manual: {str(e)}"
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
        """Process a single PDF (≤15 pages)"""
        from app.utils.document_ai_helper import analyze_document_with_document_ai
        
        logger.info(f"🔄 Processing single PDF: {filename} ({total_pages} pages)")
        
        analysis_result['_split_info'] = {
            'was_split': False,
            'total_pages': total_pages,
            'chunks_count': 1
        }
        
        # Step 1: Call Document AI
        doc_ai_result = await analyze_document_with_document_ai(
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
            
            # Step 2: Extract fields with System AI
            logger.info("🧠 Extracting fields with System AI...")
            
            ai_provider = ai_config_doc.get("provider", "google")
            ai_model = ai_config_doc.get("model", "gemini-2.0-flash-exp")
            use_emergent_key = ai_config_doc.get("use_emergent_key", True)
            
            extracted_fields = await extract_drawings_manuals_fields_from_summary(
                summary_text,
                ai_provider,
                ai_model,
                use_emergent_key,
                filename
            )
            
            if extracted_fields:
                logger.info("✅ System AI extraction completed")
                
                # Step 3: Normalize document_name
                if extracted_fields.get('document_name'):
                    try:
                        from app.utils.document_name_normalization import normalize_document_name
                        
                        original_doc_name = extracted_fields['document_name']
                        normalized_doc_name = normalize_document_name(original_doc_name)
                        
                        if normalized_doc_name != original_doc_name:
                            extracted_fields['document_name'] = normalized_doc_name
                            logger.info(f"✅ Normalized Document Name: '{original_doc_name}' → '{normalized_doc_name}'")
                        else:
                            logger.info(f"ℹ️ Document Name kept as: '{original_doc_name}'")
                            
                    except Exception as norm_error:
                        logger.error(f"❌ Error normalizing document_name: {norm_error}")
                
                # Step 4: Normalize approved_by to standard abbreviation
                if extracted_fields.get('approved_by'):
                    try:
                        from app.utils.issued_by_abbreviation import normalize_issued_by
                        
                        original_approved_by = extracted_fields['approved_by']
                        normalized_approved_by = normalize_issued_by(original_approved_by)
                        
                        if normalized_approved_by != original_approved_by:
                            extracted_fields['approved_by'] = normalized_approved_by
                            logger.info(f"✅ Normalized Approved By: '{original_approved_by}' → '{normalized_approved_by}'")
                        else:
                            logger.info(f"ℹ️ Approved By kept as: '{original_approved_by}'")
                            
                    except Exception as norm_error:
                        logger.error(f"❌ Error normalizing approved_by: {norm_error}")
                
                analysis_result.update(extracted_fields)
                analysis_result['processing_method'] = "full_analysis"
            else:
                logger.warning("⚠️ System AI extraction returned no fields")
                analysis_result['processing_method'] = "document_ai_only"
            
            analysis_result['_summary_text'] = summary_text
        
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
        Process a large PDF (>15 pages) by splitting into chunks
        
        KEY IMPROVEMENT: Parallel chunk processing with staggered start
        """
        from app.utils.document_ai_helper import analyze_with_document_ai
        
        chunks = splitter.split_pdf(file_content, filename)
        total_chunks = len(chunks)
        logger.info(f"📦 Created {total_chunks} chunks from {total_pages}-page PDF")
        
        # Limit to MAX_CHUNKS (same as backend-v1)
        MAX_CHUNKS = 5
        chunks_to_process = chunks[:MAX_CHUNKS]
        skipped_chunks = total_chunks - len(chunks_to_process)
        
        if skipped_chunks > 0:
            logger.warning(f"⚠️ File has {total_chunks} chunks. Processing first {MAX_CHUNKS} chunks only, skipping {skipped_chunks} chunks")
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
        # NEW: Parallel processing instead of sequential (backend-v1 used for loop)
        logger.info(f"🚀 Starting staggered parallel processing of {len(chunks_to_process)} chunks (2s delay between starts)...")
        
        async def process_single_chunk(chunk, chunk_index):
            """Process a single chunk with Document AI"""
            logger.info(f"🔄 Processing chunk {chunk_index+1}/{len(chunks_to_process)} (pages {chunk['page_range']})")
            
            try:
                doc_ai_result = await analyze_with_document_ai(
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
            'document_name': 'Processing...',
            'document_no': 'Processing...',
            'approved_by': 'Processing...',
            'approved_date': 'Processing...'
        }
        
        merged_summary = create_enhanced_merged_summary(
            chunk_results=chunk_results,
            merged_data=temp_merged_data,
            original_filename=filename,
            total_pages=total_pages,
            document_type='drawings_manuals'
        )
        
        logger.info(f"📄 Merged summary created: {len(merged_summary)} chars")
        
        # Step 3: Extract fields from merged summary
        logger.info("🧠 Extracting fields from merged summary...")
        
        ai_provider = ai_config_doc.get("provider", "google")
        ai_model = ai_config_doc.get("model", "gemini-2.0-flash-exp")
        use_emergent_key = ai_config_doc.get("use_emergent_key", True)
        
        extracted_fields = await extract_drawings_manuals_fields_from_summary(
            merged_summary,
            ai_provider,
            ai_model,
            use_emergent_key,
            filename
        )
        
        if extracted_fields:
            logger.info("✅ Field extraction from merged summary completed")
            
            # Normalize document_name
            if extracted_fields.get('document_name'):
                try:
                    from app.utils.document_name_normalization import normalize_document_name
                    
                    original_doc_name = extracted_fields['document_name']
                    normalized_doc_name = normalize_document_name(original_doc_name)
                    
                    if normalized_doc_name != original_doc_name:
                        extracted_fields['document_name'] = normalized_doc_name
                        logger.info(f"✅ Normalized Document Name: '{original_doc_name}' → '{normalized_doc_name}'")
                            
                except Exception as norm_error:
                    logger.error(f"❌ Error normalizing document_name: {norm_error}")
            
            # Normalize approved_by
            if extracted_fields.get('approved_by'):
                try:
                    from app.utils.issued_by_abbreviation import normalize_issued_by
                    
                    original_approved_by = extracted_fields['approved_by']
                    normalized_approved_by = normalize_issued_by(original_approved_by)
                    
                    if normalized_approved_by != original_approved_by:
                        extracted_fields['approved_by'] = normalized_approved_by
                        logger.info(f"✅ Normalized Approved By: '{original_approved_by}' → '{normalized_approved_by}'")
                            
                except Exception as norm_error:
                    logger.error(f"❌ Error normalizing approved_by: {norm_error}")
            
            analysis_result.update(extracted_fields)
            analysis_result['processing_method'] = "split_pdf_merged_analysis"
        else:
            logger.warning("⚠️ No fields extracted from merged summary")
            analysis_result['processing_method'] = "split_pdf_no_extraction"
        
        analysis_result['_summary_text'] = merged_summary
        
        # Update split info with chunk processing results
        analysis_result['_split_info'].update({
            'successful_chunks': len(successful_chunks),
            'failed_chunks': failed_chunks,
            'has_failures': failed_chunks > 0,
            'partial_success': len(successful_chunks) > 0 and failed_chunks > 0
        })
        
        return analysis_result
