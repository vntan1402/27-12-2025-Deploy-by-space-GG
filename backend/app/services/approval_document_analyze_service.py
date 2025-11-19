"""
Approval Document Analysis Service
Handles AI-powered analysis of approval document PDFs
Based on Backend V1 and Drawing Manual Analyze Service pattern
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
from app.utils.approval_document_ai import extract_approval_document_fields_from_summary
from app.utils.issued_by_abbreviation import normalize_issued_by

logger = logging.getLogger(__name__)


class ApprovalDocumentAnalyzeService:
    """Service for analyzing approval document files with AI"""
    
    @staticmethod
    async def analyze_file(
        file: UploadFile,
        ship_id: str,
        bypass_validation: bool,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """
        Analyze approval document file using Document AI + System AI
        
        Process (identical to Backend V1):
        1. Validate PDF file (magic bytes, extension, size)
        2. Check page count and split if >15 pages
        3. Process with Document AI (parallel for chunks)
        4. Extract fields from summary with System AI
        5. Normalize approved_by
        6. Return analysis + base64 file content
        
        Args:
            file: PDF file upload
            ship_id: Ship ID
            bypass_validation: Skip validation (for testing)
            current_user: Current authenticated user
            
        Returns:
            dict: Analysis result with extracted fields + metadata
        """
        try:
            logger.info(f"✅ Starting approval document analysis for ship_id: {ship_id}")
            
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
                    detail="Invalid file type. Only PDF files are supported for approval documents."
                )
            
            # Check PDF magic bytes
            if not file_content.startswith(b'%PDF'):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid PDF file format. The file does not appear to be a valid PDF document."
                )
            
            # Check file size (50MB limit)
            max_size = 50 * 1024 * 1024  # 50MB
            if len(file_content) > max_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size is 50MB. Your file is {len(file_content) / (1024*1024):.1f}MB"
                )
            
            logger.info(f"📄 Processing approval document file: {filename} ({len(file_content)} bytes)")
            
            # Check if PDF needs splitting (>15 pages)
            splitter = PDFSplitter(max_pages_per_chunk=12)
            
            try:
                total_pages = splitter.get_page_count(file_content)
                needs_split = splitter.needs_splitting(file_content)
                logger.info(f"📊 PDF Analysis: {total_pages} pages, Split needed: {needs_split}")
            except ValueError as e:
                logger.error(f"❌ Invalid PDF file: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid or corrupted PDF file: {str(e)}. Please ensure the file is a valid PDF document."
                )
            except Exception as e:
                logger.warning(f"⚠️ Could not detect page count: {e}, assuming single file processing")
                total_pages = 0
                needs_split = False
            
            # Get company information
            company_id = current_user.company
            if not company_id:
                raise HTTPException(status_code=404, detail="Company not found")
            
            # Get ship information
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            # Verify company access
            ship_company = ship.get("company")
            if ship_company != company_id:
                logger.warning(f"Access denied: ship company '{ship_company}' != user company '{company_id}'")
                raise HTTPException(status_code=403, detail="Access denied to this ship")
            
            ship_name = ship.get("name", "Unknown Ship")
            
            # Get AI configuration for Document AI
            ai_config = await mongo_db.find_one("ai_config", {"id": "system_ai"})
            if not ai_config:
                raise HTTPException(
                    status_code=404,
                    detail="AI configuration not found. Please configure AI in System Settings."
                )
            
            document_ai_config = ai_config.get("document_ai", {})
            
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
                    detail="Incomplete Google Document AI configuration."
                )
            
            logger.info("🤖 Analyzing approval document with Google Document AI...")
            
            # Initialize empty analysis data
            analysis_result = {
                "approval_document_name": "",
                "approval_document_no": "",
                "approved_by": "",
                "approved_date": "",
                "note": "",
                "confidence_score": 0.0,
                "processing_method": "clean_analysis",
                "_filename": filename,
                "_summary_text": ""
            }
            
            # Store file content FIRST before any analysis
            analysis_result['_file_content'] = base64.b64encode(file_content).decode('utf-8')
            analysis_result['_filename'] = filename
            analysis_result['_content_type'] = file.content_type or 'application/pdf'
            analysis_result['_ship_name'] = ship_name
            analysis_result['_summary_text'] = ''
            
            # Process based on file size
            if needs_split and total_pages > 15:
                # Large PDF processing with splitting
                analysis_result = await ApprovalDocumentAnalyzeService._process_large_pdf(
                    file_content=file_content,
                    filename=filename,
                    ship_name=ship_name,
                    total_pages=total_pages,
                    splitter=splitter,
                    document_ai_config=document_ai_config,
                    ai_config=ai_config,
                    analysis_result=analysis_result,
                    company_id=company_id
                )
            else:
                # Small PDF: Normal single-file processing
                analysis_result = await ApprovalDocumentAnalyzeService._process_small_pdf(
                    file_content=file_content,
                    filename=filename,
                    document_ai_config=document_ai_config,
                    ai_config=ai_config,
                    analysis_result=analysis_result,
                    company_id=company_id
                )
            
            # Normalize approved_by to standard abbreviation
            if analysis_result.get('approved_by'):
                try:
                    original_approved_by = analysis_result['approved_by']
                    normalized_approved_by = normalize_issued_by(original_approved_by)
                    
                    if normalized_approved_by != original_approved_by:
                        analysis_result['approved_by'] = normalized_approved_by
                        logger.info(f"✅ Normalized Approved By: '{original_approved_by}' → '{normalized_approved_by}'")
                    else:
                        logger.info(f"ℹ️ Approved By kept as: '{original_approved_by}'")
                        
                except Exception as norm_error:
                    logger.error(f"❌ Error normalizing approved_by: {norm_error}")
            
            logger.info("✅ Approval document analysis completed successfully")
            return analysis_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error analyzing approval document file: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @staticmethod
    async def _process_small_pdf(
        file_content: bytes,
        filename: str,
        document_ai_config: Dict,
        ai_config: Dict,
        analysis_result: Dict,
        company_id: str
    ) -> Dict:
        """
        Process small PDF (≤15 pages) with Document AI + System AI
        
        Reference: Backend V1 server.py lines 13735-13804
        """
        logger.info("📄 Processing as single file (≤15 pages)")
        
        try:
            # Get Document AI helper (same as drawing manuals)
            from app.utils.document_ai_helper import analyze_document_with_document_ai
            
            # Analyze with Document AI
            ai_analysis = await analyze_document_with_document_ai(
                file_content=file_content,
                filename=filename,
                content_type='application/pdf',
                document_ai_config=document_ai_config,
                company_id=company_id
            )
            
            if ai_analysis:
                summary_text = ai_analysis.get('summary_text', '')
                
                if summary_text and summary_text.strip():
                    analysis_result['_summary_text'] = summary_text
                    
                    # Extract fields from summary
                    logger.info("🧠 Extracting approval document fields from Document AI summary...")
                    
                    ai_provider = ai_config.get("provider", "google")
                    ai_model = ai_config.get("model", "gemini-2.0-flash-exp")
                    use_emergent_key = ai_config.get("use_emergent_key", True)
                    
                    try:
                        extracted_fields = await extract_approval_document_fields_from_summary(
                            summary_text,
                            ai_provider,
                            ai_model,
                            use_emergent_key
                        )
                        
                        if extracted_fields:
                            logger.info("✅ System AI approval document extraction completed successfully")
                            analysis_result.update(extracted_fields)
                            analysis_result["processing_method"] = "analysis_only_no_upload"
                            logger.info(f"   📋 Extracted Document Name: '{analysis_result.get('approval_document_name')}'")
                            logger.info(f"   🔢 Extracted Document No: '{analysis_result.get('approval_document_no')}'")
                        else:
                            logger.warning("⚠️ No fields extracted from summary, using fallback")
                            analysis_result['approval_document_name'] = filename.replace('.pdf', '').replace('_', ' ')
                            analysis_result['note'] = "AI field extraction incomplete"
                    
                    except Exception as extraction_error:
                        logger.error(f"❌ Field extraction failed: {extraction_error}")
                        analysis_result['approval_document_name'] = filename.replace('.pdf', '').replace('_', ' ')
                        analysis_result['note'] = f"AI extraction error: {str(extraction_error)[:100]}"
                
                else:
                    logger.warning("⚠️ Document AI returned empty summary")
                    analysis_result['_summary_text'] = ''
                    analysis_result['approval_document_name'] = filename.replace('.pdf', '').replace('_', ' ')
                    analysis_result['note'] = "AI analysis returned empty result. Manual review required."
                
                if 'confidence_score' in ai_analysis:
                    analysis_result['confidence_score'] = ai_analysis['confidence_score']
                
                logger.info("✅ Approval document file analyzed successfully")
            else:
                logger.warning("⚠️ AI analysis returned no data, using fallback")
                analysis_result['approval_document_name'] = filename.replace('.pdf', '').replace('_', ' ')
                analysis_result['note'] = "AI analysis unavailable. Manual review required."
                
        except Exception as ai_error:
            logger.error(f"❌ Document AI analysis failed: {ai_error}")
            logger.warning("⚠️ Continuing without AI analysis - file upload will still work")
            analysis_result['approval_document_name'] = analysis_result.get('approval_document_name') or filename
            analysis_result['note'] = f"AI analysis failed: {str(ai_error)}"
        
        return analysis_result
    
    
    @staticmethod
    async def _process_large_pdf(
        file_content: bytes,
        filename: str,
        ship_name: str,
        total_pages: int,
        splitter: PDFSplitter,
        document_ai_config: Dict,
        ai_config: Dict,
        analysis_result: Dict,
        company_id: str
    ) -> Dict:
        """
        Process large PDF (>15 pages) with splitting and batch processing
        
        Process:
        1. Split PDF into chunks (12 pages each)
        2. Process first 5 chunks only (MAX_CHUNKS = 5)
        3. Extract fields from each chunk
        4. Merge results intelligently
        5. Create enhanced merged summary
        
        Reference: Backend V1 server.py lines 13724-13732
        """
        logger.info("📦 Large PDF - using split processing")
        analysis_result['processing_method'] = 'split_pdf_batch_processing'
        
        try:
            # Split PDF into chunks
            chunks = splitter.split_pdf(file_content, filename)
            total_chunks = len(chunks)
            
            # Limit to first 5 chunks
            MAX_CHUNKS = 5
            chunks_to_process = chunks[:MAX_CHUNKS]
            
            if total_chunks > MAX_CHUNKS:
                skipped_chunks = total_chunks - MAX_CHUNKS
                logger.warning(f"⚠️ File has {total_chunks} chunks. Processing first {MAX_CHUNKS} chunks only, skipping {skipped_chunks} chunks")
                
                skipped_pages = sum(chunk.get('page_count', 0) for chunk in chunks[MAX_CHUNKS:])
                logger.info(f"📊 Processing {len(chunks_to_process)} chunks (~{sum(c.get('page_count', 0) for c in chunks_to_process)} pages), skipping ~{skipped_pages} pages")
            
            # Process chunks (reuse from drawing manuals)
            from app.utils.document_ai_helper import analyze_document_with_document_ai
            
            chunk_results = []
            
            for chunk in chunks_to_process:
                try:
                    chunk_num = chunk['chunk_num']
                    chunk_content = chunk['content']
                    page_range = chunk['page_range']
                    
                    logger.info(f"🔄 Processing chunk {chunk_num}/{len(chunks_to_process)} (pages {page_range})...")
                    
                    # Analyze chunk with Document AI
                    ai_analysis = await analyze_document_with_document_ai(
                        file_content=chunk_content,
                        filename=f"{filename}_chunk{chunk_num}",
                        content_type='application/pdf',
                        document_ai_config=document_ai_config,
                        company_id=company_id
                    )
                    
                    if ai_analysis and ai_analysis.get('summary_text'):
                        summary_text = ai_analysis['summary_text']
                        
                        # Extract fields from this chunk
                        ai_provider = ai_config.get("provider", "google")
                        ai_model = ai_config.get("model", "gemini-2.0-flash-exp")
                        use_emergent_key = ai_config.get("use_emergent_key", True)
                        
                        extracted_fields = await extract_approval_document_fields_from_summary(
                            summary_text,
                            ai_provider,
                            ai_model,
                            use_emergent_key
                        )
                        
                        chunk_results.append({
                            'success': True,
                            'chunk_num': chunk_num,
                            'page_range': page_range,
                            'summary_text': summary_text,
                            'extracted_fields': extracted_fields or {}
                        })
                        
                        logger.info(f"✅ Chunk {chunk_num} processed successfully")
                    else:
                        logger.warning(f"⚠️ Chunk {chunk_num} returned no summary")
                        chunk_results.append({
                            'success': False,
                            'chunk_num': chunk_num,
                            'page_range': page_range,
                            'error': 'No summary returned'
                        })
                    
                except Exception as chunk_error:
                    logger.error(f"❌ Error processing chunk {chunk_num}: {chunk_error}")
                    chunk_results.append({
                        'success': False,
                        'chunk_num': chunk_num,
                        'page_range': page_range,
                        'error': str(chunk_error)
                    })
            
            # Merge results from all chunks
            from app.utils.pdf_splitter import merge_approval_document_results
            
            merged_data = merge_approval_document_results(chunk_results)
            
            if merged_data.get('success'):
                # Update analysis_result with merged data
                analysis_result.update({
                    'approval_document_name': merged_data.get('approval_document_name', ''),
                    'approval_document_no': merged_data.get('approval_document_no', ''),
                    'approved_by': merged_data.get('approved_by', ''),
                    'approved_date': merged_data.get('approved_date', ''),
                    'note': merged_data.get('note', '')
                })
                
                # Create enhanced merged summary
                merged_summary = create_enhanced_merged_summary(
                    chunk_results,
                    merged_data,
                    filename,
                    total_pages
                )
                
                analysis_result['_summary_text'] = merged_summary
                
                # Add split info
                successful_chunks = [cr for cr in chunk_results if cr.get('success')]
                failed_chunks = len(chunk_results) - len(successful_chunks)
                all_chunks_failed = len(successful_chunks) == 0
                partial_success = len(successful_chunks) > 0 and failed_chunks > 0
                
                analysis_result['_split_info'] = {
                    'was_split': True,
                    'total_pages': total_pages,
                    'total_chunks': total_chunks,
                    'processed_chunks': len(chunks_to_process),
                    'successful_chunks': len(successful_chunks),
                    'failed_chunks': failed_chunks,
                    'all_chunks_failed': all_chunks_failed,
                    'partial_success': partial_success,
                    'has_failures': failed_chunks > 0,
                    'was_limited': total_chunks > MAX_CHUNKS,
                    'max_chunks_limit': MAX_CHUNKS,
                    'skipped_chunks': total_chunks - MAX_CHUNKS if total_chunks > MAX_CHUNKS else 0
                }
                
                logger.info("✅ Large PDF processing completed with merged results")
            else:
                logger.error("❌ Failed to merge chunk results")
                analysis_result['approval_document_name'] = filename.replace('.pdf', '').replace('_', ' ')
                analysis_result['note'] = "Failed to merge chunk results. Manual review required."
            
        except Exception as split_error:
            logger.error(f"❌ Error in split PDF processing: {split_error}")
            analysis_result['approval_document_name'] = filename.replace('.pdf', '').replace('_', ' ')
            analysis_result['note'] = f"Split processing error: {str(split_error)}"
        
        return analysis_result
