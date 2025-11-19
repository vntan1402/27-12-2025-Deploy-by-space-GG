"""
Audit Report Analysis Service
Handles AI-powered analysis of audit report PDFs (ISM/ISPS/MLC)
Based on Backend V1 and Approval Document Analyze Service pattern
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
from app.utils.audit_report_ai import extract_audit_report_fields_from_summary
from app.utils.issued_by_abbreviation import normalize_issued_by

logger = logging.getLogger(__name__)


class AuditReportAnalyzeService:
    """Service for analyzing audit report files with AI"""
    
    @staticmethod
    async def analyze_file(
        file: UploadFile,
        ship_id: str,
        bypass_validation: bool,
        current_user: UserResponse
    ) -> Dict[str, Any]:
        """
        Analyze audit report file using Document AI + System AI
        
        Process (identical to Backend V1):
        1. Validate PDF file (magic bytes, extension, size)
        2. Check page count and split if >15 pages
        3. Process with Document AI (parallel for chunks)
        4. Extract fields from summary with System AI
        5. Normalize issued_by
        6. Validate ship name/IMO (optional)
        7. Return analysis + base64 file content
        
        Based on Backend V1: analyze_audit_report_file()
        Location: /app/backend-v1/server.py lines 9746-10322
        
        Args:
            file: PDF file upload
            ship_id: Ship ID
            bypass_validation: Skip ship validation
            current_user: Current authenticated user
            
        Returns:
            dict: Analysis result with extracted fields + metadata
        """
        try:
            logger.info(f"📋 Starting audit report analysis for ship_id: {ship_id}")
            
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
                    detail="Invalid file type. Only PDF files are supported for audit reports."
                )
            
            # Check PDF magic bytes
            if not file_content.startswith(b'%PDF'):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid PDF file format. The file does not appear to be a valid PDF document."
                )
            
            logger.info(f"📄 Processing audit report file: {filename} ({len(file_content)} bytes)")
            
            # Get company UUID
            company_uuid = current_user.company
            if not company_uuid:
                raise HTTPException(status_code=404, detail="Company not found")
            
            # Check page count and decide if splitting is needed
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
            
            # Get ship info
            ship = await mongo_db.find_one("ships", {"id": ship_id, "company": company_uuid})
            if not ship and not bypass_validation:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            ship_name = ship.get("name", "Unknown Ship") if ship else "Unknown Ship"
            ship_imo = ship.get("imo", "") if ship else ""
            
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
                    detail="Incomplete Google Document AI configuration."
                )
            
            logger.info("🤖 Analyzing audit report with Google Document AI...")
            
            # Initialize analysis result
            analysis_result = {
                "audit_report_name": "",
                "audit_type": "",
                "report_form": "",
                "audit_report_no": "",
                "issued_by": "",
                "audit_date": "",
                "auditor_name": "",
                "ship_name": "",
                "ship_imo": "",
                "note": "",
                "status": "Valid",
                "confidence_score": 0.0,
                "processing_method": "clean_analysis",
                "original_filename": filename,  # Save for report_form re-extraction
                # Internal data for upload
                "_file_content": base64.b64encode(file_content).decode('utf-8'),
                "_filename": filename,
                "_content_type": file.content_type or 'application/octet-stream',
                "_ship_name": ship_name,
                "_summary_text": ''
            }
            
            # Get AI config
            ai_config = {
                "provider": ai_config_doc.get("provider", "google"),
                "model": ai_config_doc.get("model", "gemini-2.0-flash"),
                "use_emergent_key": ai_config_doc.get("use_emergent_key", True)
            }
            
            # Process PDF based on size
            if not needs_split:
                # Process small PDF (≤15 pages)
                analysis_result = await AuditReportAnalyzeService._process_small_pdf(
                    file_content=file_content,
                    filename=filename,
                    document_ai_config=document_ai_config,
                    ai_config=ai_config,
                    analysis_result=analysis_result,
                    company_id=company_uuid
                )
                
                analysis_result['_split_info'] = {
                    'was_split': False,
                    'total_pages': total_pages,
                    'chunks_count': 1
                }
            else:
                # Process large PDF (>15 pages) with splitting
                analysis_result = await AuditReportAnalyzeService._process_large_pdf(
                    file_content=file_content,
                    filename=filename,
                    ship_name=ship_name,
                    total_pages=total_pages,
                    splitter=splitter,
                    document_ai_config=document_ai_config,
                    ai_config=ai_config,
                    analysis_result=analysis_result,
                    company_id=company_uuid
                )
            
            # Normalize issued_by to standard abbreviation
            if analysis_result.get('issued_by'):
                try:
                    original_issued_by = analysis_result['issued_by']
                    normalized_issued_by = normalize_issued_by(original_issued_by)
                    
                    if normalized_issued_by != original_issued_by:
                        analysis_result['issued_by'] = normalized_issued_by
                        logger.info(f"✅ Normalized Issued By: '{original_issued_by}' → '{normalized_issued_by}'")
                    else:
                        logger.info(f"ℹ️ Issued By kept as: '{original_issued_by}'")
                        
                except Exception as norm_error:
                    logger.error(f"❌ Error normalizing issued_by: {norm_error}")
            
            # Ship validation (optional)
            if not bypass_validation:
                extracted_ship_name = (analysis_result.get('ship_name') or '').strip()
                extracted_ship_imo = (analysis_result.get('ship_imo') or '').strip()
                
                if extracted_ship_name or extracted_ship_imo:
                    validation_result = AuditReportAnalyzeService._validate_ship_info(
                        extracted_ship_name,
                        extracted_ship_imo,
                        ship_name,
                        ship_imo
                    )
                    
                    if not validation_result.get('overall_match'):
                        logger.warning("❌ Ship information does NOT match")
                        return {
                            "success": False,
                            "validation_error": True,
                            "extracted_ship_name": extracted_ship_name,
                            "extracted_ship_imo": extracted_ship_imo,
                            "expected_ship_name": ship_name,
                            "expected_ship_imo": ship_imo,
                            "message": "Ship name/IMO mismatch detected. Please verify the document belongs to the selected ship."
                        }
            
            logger.info("✅ Audit report analysis completed successfully")
            return {
                "success": True,
                "analysis": analysis_result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error analyzing audit report file: {e}")
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
        
        Based on Backend V1 lines 9913-10078
        """
        logger.info("📄 Processing as single file (≤15 pages)")
        
        try:
            # Get Document AI helper
            from app.utils.document_ai_helper import analyze_document_with_document_ai
            
            # Analyze with Document AI
            doc_ai_result = await analyze_document_with_document_ai(
                file_content=file_content,
                filename=filename,
                content_type='application/pdf',
                document_ai_config=document_ai_config,
                document_type='audit_report'  # Use audit_report document type
            )
            
            # Extract AI analysis from result
            ai_analysis = None
            if doc_ai_result.get('success'):
                ai_analysis = {
                    'summary_text': doc_ai_result.get('data', {}).get('summary', ''),
                    'confidence_score': doc_ai_result.get('data', {}).get('confidence_score', 0.0)
                }
            else:
                logger.warning(f"⚠️ Document AI failed: {doc_ai_result.get('message')}")
            
            if ai_analysis:
                summary_text = ai_analysis.get('summary_text', '')
                
                if summary_text and summary_text.strip():
                    analysis_result['_summary_text'] = summary_text
                    
                    # Extract fields from summary
                    logger.info("🧠 Extracting audit report fields from Document AI summary...")
                    
                    try:
                        extracted_fields = await extract_audit_report_fields_from_summary(
                            summary_text=summary_text,
                            filename=filename,
                            ai_config=ai_config
                        )
                        
                        if extracted_fields:
                            logger.info("✅ System AI audit report extraction completed successfully")
                            analysis_result.update(extracted_fields)
                            analysis_result["processing_method"] = "system_ai_extraction_from_summary"
                            logger.info(f"   📋 Extracted Audit Name: '{analysis_result.get('audit_report_name')}'")
                            logger.info(f"   📝 Extracted Audit Type: '{analysis_result.get('audit_type')}'")
                            logger.info(f"   📄 Extracted Report Form: '{analysis_result.get('report_form')}'")
                            logger.info(f"   🔢 Extracted Audit No: '{analysis_result.get('audit_report_no')}'")
                        else:
                            logger.warning("⚠️ No fields extracted from summary, using fallback")
                            analysis_result['audit_report_name'] = filename.replace('.pdf', '').replace('_', ' ')
                            analysis_result['note'] = "AI field extraction incomplete"
                    
                    except Exception as extraction_error:
                        logger.error(f"❌ Field extraction failed: {extraction_error}")
                        analysis_result['audit_report_name'] = filename.replace('.pdf', '').replace('_', ' ')
                        analysis_result['note'] = f"AI extraction error: {str(extraction_error)[:100]}"
                
                else:
                    logger.error("❌ Document AI returned empty summary - Cannot process file")
                    raise HTTPException(
                        status_code=400,
                        detail="Document AI returned empty summary. The file may be corrupted, unreadable, or not a valid audit report. Please check the file and try again."
                    )
                
                if 'confidence_score' in ai_analysis:
                    analysis_result['confidence_score'] = ai_analysis['confidence_score']
                
                logger.info("✅ Audit report file analyzed successfully")
            else:
                logger.error("❌ Document AI analysis failed - No data returned")
                raise HTTPException(
                    status_code=400,
                    detail="Document AI analysis failed. The file may be corrupted or unreadable. Please check the file and try again."
                )
                analysis_result['note'] = "AI analysis unavailable. Manual review required."
                
        except Exception as ai_error:
            logger.error(f"❌ Document AI analysis failed: {ai_error}")
            logger.warning("⚠️ Continuing without AI analysis - file upload will still work")
            analysis_result['audit_report_name'] = analysis_result.get('audit_report_name') or filename
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
        4. Merge results intelligently using pdf_splitter.merge_analysis_results()
        5. Create enhanced merged summary
        
        Based on Backend V1 lines 10080-10163
        """
        logger.info(f"📦 Processing large PDF ({total_pages} pages) with splitting...")
        
        try:
            # Split PDF into chunks
            chunks = splitter.split_pdf(file_content, filename)
            logger.info(f"✂️ Split into {len(chunks)} chunks")
            
            # Limit to first 5 chunks
            MAX_CHUNKS = 5
            chunks_to_process = chunks[:MAX_CHUNKS]
            
            if len(chunks) > MAX_CHUNKS:
                logger.warning(f"⚠️ PDF has {len(chunks)} chunks, processing only first {MAX_CHUNKS}")
            
            # Get Document AI helper
            from app.utils.document_ai_helper import analyze_document_with_document_ai
            
            # Process chunks in parallel
            tasks = []
            for i, chunk in enumerate(chunks_to_process):
                chunk_filename = f"{filename}_chunk_{i+1}"
                task = analyze_document_with_document_ai(
                    file_content=chunk['content'],
                    filename=chunk_filename,
                    content_type='application/pdf',
                    document_ai_config=document_ai_config,
                    document_type='audit_report'
                )
                tasks.append((i, chunk, task))
            
            # Wait for all chunks to complete
            logger.info(f"⏳ Processing {len(tasks)} chunks in parallel...")
            chunk_results = []
            
            for i, chunk, task in tasks:
                try:
                    doc_ai_result = await task
                    if doc_ai_result.get('success'):
                        summary_text = doc_ai_result.get('data', {}).get('summary', '')
                        
                        # Extract fields from this chunk's summary
                        extracted_fields = await extract_audit_report_fields_from_summary(
                            summary_text=summary_text,
                            filename=filename,
                            ai_config=ai_config
                        )
                        
                        chunk_results.append({
                            'chunk_index': i,
                            'page_range': chunk['page_range'],
                            'summary': summary_text,
                            'fields': extracted_fields
                        })
                        logger.info(f"✅ Chunk {i+1} processed successfully")
                    else:
                        logger.warning(f"⚠️ Chunk {i+1} Document AI failed: {doc_ai_result.get('message')}")
                        
                except Exception as chunk_error:
                    logger.error(f"❌ Chunk {i+1} processing failed: {chunk_error}")
            
            if chunk_results:
                logger.info(f"🔀 Merging results from {len(chunk_results)} successful chunks...")
                
                # Merge field results using pdf_splitter utility
                merged_fields = splitter.merge_analysis_results(
                    chunk_results=[r['fields'] for r in chunk_results],
                    document_type='audit_report'
                )
                
                # Update analysis result with merged fields
                analysis_result.update(merged_fields)
                
                # Create enhanced merged summary
                summary_parts = [r['summary'] for r in chunk_results]
                merged_summary = create_enhanced_merged_summary(
                    summary_parts=summary_parts,
                    filename=filename,
                    ship_name=ship_name,
                    document_type='audit_report'
                )
                
                analysis_result['_summary_text'] = merged_summary
                analysis_result['processing_method'] = 'merged_from_chunks'
                
                # Add split info
                analysis_result['_split_info'] = {
                    'was_split': True,
                    'total_pages': total_pages,
                    'chunks_count': len(chunks),
                    'processed_chunks': len(chunks_to_process),
                    'successful_chunks': len(chunk_results),
                    'failed_chunks': len(chunks_to_process) - len(chunk_results)
                }
                
                logger.info(f"✅ Merged analysis from {len(chunk_results)}/{len(chunks_to_process)} chunks")
                logger.info(f"   📋 Merged Audit Name: '{merged_fields.get('audit_report_name', '')[:50]}'")
                logger.info(f"   📝 Merged Audit Type: '{merged_fields.get('audit_type', '')}'")
            else:
                logger.error("❌ No chunks processed successfully")
                analysis_result['audit_report_name'] = filename.replace('.pdf', '').replace('_', ' ')
                analysis_result['note'] = "All chunks failed to process. Manual review required."
                analysis_result['_split_info'] = {
                    'was_split': True,
                    'total_pages': total_pages,
                    'chunks_count': len(chunks),
                    'processed_chunks': len(chunks_to_process),
                    'successful_chunks': 0,
                    'failed_chunks': len(chunks_to_process)
                }
            
        except Exception as split_error:
            logger.error(f"❌ Large PDF processing failed: {split_error}")
            logger.error(traceback.format_exc())
            analysis_result['audit_report_name'] = filename.replace('.pdf', '').replace('_', ' ')
            analysis_result['note'] = f"PDF splitting/processing error: {str(split_error)[:100]}"
        
        return analysis_result
    
    
    @staticmethod
    def _validate_ship_info(
        extracted_ship_name: str,
        extracted_ship_imo: str,
        expected_ship_name: str,
        expected_ship_imo: str
    ) -> Dict[str, Any]:
        """
        Validate ship information match
        
        Based on Backend V1 validate_ship_info_match()
        
        Returns:
            dict: {
                'overall_match': bool,
                'name_match': bool,
                'imo_match': bool,
                'confidence': str
            }
        """
        # Normalize for comparison
        extracted_name_clean = extracted_ship_name.upper().strip()
        expected_name_clean = expected_ship_name.upper().strip()
        
        # Check name similarity (fuzzy matching)
        name_match = (
            extracted_name_clean == expected_name_clean or
            extracted_name_clean in expected_name_clean or
            expected_name_clean in extracted_name_clean
        )
        
        # Check IMO (exact match required)
        imo_match = extracted_ship_imo == expected_ship_imo if extracted_ship_imo else False
        
        # Overall match: either name OR IMO matches
        overall_match = name_match or imo_match
        
        return {
            'overall_match': overall_match,
            'name_match': name_match,
            'imo_match': imo_match,
            'confidence': 'high' if (name_match and imo_match) else 'medium'
        }
