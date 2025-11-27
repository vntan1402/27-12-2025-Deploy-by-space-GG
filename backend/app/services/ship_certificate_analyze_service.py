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


class ShipCertificateAnalyzeService:
    """Service for analyzing ship certificate files with AI"""
    
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
                document_type='other'  # Ship certificates - general type
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
                current_user=current_user
            )
            
            return {
                "success": True,
                "extracted_info": extracted_info,
                "summary_text": summary_text,  # ⭐ Return summary text for storage
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
            
            # Check for duplicates
            duplicate_warning = await ShipCertificateAnalyzeService.check_duplicate(
                ship_id=ship["id"],
                cert_name=extracted_info.get('cert_name'),
                cert_no=extracted_info.get('cert_no'),
                current_user=current_user
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
        current_user: UserResponse
    ) -> Optional[Dict[str, Any]]:
        """
        Check for duplicate certificates based on cert_no or cert_name
        
        Returns duplicate warning if found
        """
        try:
            if not cert_no and not cert_name:
                return None
            
            # Build query
            query = {"ship_id": ship_id}
            
            # Check by cert_no first (unique identifier)
            if cert_no:
                existing_cert = await mongo_db.find_one("certificates", {
                    "ship_id": ship_id,
                    "cert_no": cert_no
                })
                
                if existing_cert:
                    return {
                        "has_duplicate": True,
                        "message": f"Duplicate certificate number found: {cert_no}",
                        "existing_certificate": {
                            "id": existing_cert.get("id"),
                            "cert_name": existing_cert.get("cert_name"),
                            "cert_no": existing_cert.get("cert_no"),
                            "issue_date": existing_cert.get("issue_date")
                        }
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return None
