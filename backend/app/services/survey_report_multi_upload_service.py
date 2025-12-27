"""
Survey Report Multi-Upload Service
Handles Smart Upload with FAST/SLOW path for Survey Reports
"""
import logging
import os
import base64
import tempfile
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import UploadFile, HTTPException, BackgroundTasks

from app.db.mongodb import mongo_db
from app.models.user import UserResponse, UserRole
from app.services.ai_config_service import AIConfigService
from app.services.upload_task_service import UploadTaskService
from app.models.upload_task import TaskStatus, ProcessingType

logger = logging.getLogger(__name__)

# Thresholds for path selection
PAGE_THRESHOLD = 15  # Ngưỡng số trang để quyết định path
TEXT_LAYER_THRESHOLD = 400  # Ngưỡng ký tự cho text layer


class SurveyReportMultiUploadService:
    """Service for handling survey report uploads with Smart Upload"""
    
    @staticmethod
    def get_pdf_page_count(file_content: bytes) -> int:
        """
        Get number of pages in PDF file
        
        Args:
            file_content: PDF file bytes
            
        Returns:
            Number of pages, or 0 if cannot determine
        """
        try:
            import pdfplumber
            pdf_file = io.BytesIO(file_content)
            with pdfplumber.open(pdf_file) as pdf:
                return len(pdf.pages)
        except Exception as e:
            logger.warning(f"Cannot get page count: {e}")
            return 0
    
    @staticmethod
    def quick_check_processing_path(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Determine whether file should use FAST or SLOW path
        
        Logic mới:
        - File ≤15 trang → SLOW PATH (Document AI xử lý toàn bộ)
        - File >15 trang + có text layer (≥400 chars) → FAST PATH
        - File >15 trang + không có text layer → SLOW PATH (split 10 đầu + 10 cuối)
        """
        from app.utils.pdf_text_extractor import extract_text_from_pdf_text_layer
        
        result = {
            "path": "SLOW_PATH",
            "reason": "Default to SLOW path",
            "has_text_layer": False,
            "text_char_count": 0,
            "page_count": 0,
            "is_image": False,
            "needs_split": False
        }
        
        # Check if image file - always SLOW PATH
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp')):
            result["is_image"] = True
            result["reason"] = "Image file - dùng Document AI"
            return result
        
        # Check if PDF
        if not filename.lower().endswith('.pdf'):
            result["reason"] = f"Unknown file type: {filename}"
            return result
        
        # Step 1: Get page count
        page_count = SurveyReportMultiUploadService.get_pdf_page_count(file_content)
        result["page_count"] = page_count
        
        logger.info(f"📄 {filename}: {page_count} trang")
        
        # Step 2: If ≤15 pages → SLOW PATH (Document AI processes entire file)
        if page_count <= PAGE_THRESHOLD:
            result["path"] = "SLOW_PATH"
            result["reason"] = f"File có {page_count} trang (≤{PAGE_THRESHOLD}) - dùng Document AI toàn bộ"
            return result
        
        # Step 3: File >15 pages → Check text layer
        try:
            text_content = extract_text_from_pdf_text_layer(file_content)
            char_count = len(text_content.strip()) if text_content else 0
            
            result["text_char_count"] = char_count
            result["has_text_layer"] = char_count >= TEXT_LAYER_THRESHOLD
            
            if char_count >= TEXT_LAYER_THRESHOLD:
                # >15 pages + has text layer → FAST PATH
                result["path"] = "FAST_PATH"
                result["reason"] = f"File {page_count} trang (>{PAGE_THRESHOLD}) có text layer ({char_count} chars) - dùng FAST PATH"
            else:
                # >15 pages + no text layer → SLOW PATH with split
                result["path"] = "SLOW_PATH"
                result["needs_split"] = True
                result["reason"] = f"File {page_count} trang (>{PAGE_THRESHOLD}) không có text layer - split 10 đầu + 10 cuối, dùng Document AI"
                
        except Exception as e:
            logger.warning(f"Text extraction failed for {filename}: {e}")
            result["path"] = "SLOW_PATH"
            result["needs_split"] = page_count > PAGE_THRESHOLD
            result["reason"] = "Text extraction failed - dùng Document AI"
        
        return result
    
    @staticmethod
    async def process_multi_upload_smart(
        ship_id: str,
        files: List[UploadFile],
        current_user: UserResponse,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """
        Smart multi-upload with automatic FAST/SLOW path selection
        
        - FAST PATH: PDF with text layer >= threshold → Process immediately
        - SLOW PATH: Scanned PDF/Image → Create background task, return task_id
        """
        try:
            db = mongo_db.database
            
            # Step 1: Verify ship and permissions
            ship = await db.ships.find_one({"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            from app.core.permission_checks import (
                check_company_access,
                check_create_permission,
                check_editor_viewer_ship_scope
            )
            
            ship_company_id = ship.get("company")
            check_company_access(current_user, ship_company_id, "create survey reports")
            check_create_permission(current_user, "survey_report", ship_company_id)
            check_editor_viewer_ship_scope(current_user, ship_id, "create survey reports")
            
            # Step 2: Get AI configuration
            try:
                ai_config_obj = await AIConfigService.get_ai_config(current_user)
                ai_config = {
                    "provider": ai_config_obj.provider,
                    "model": ai_config_obj.model,
                    "api_key": os.getenv("EMERGENT_LLM_KEY"),
                    "use_emergent_key": True
                }
            except Exception:
                raise HTTPException(status_code=500, detail="AI configuration not found")
            
            # Get Document AI config
            ai_config_doc = await db.ai_config.find_one({})
            if not ai_config_doc:
                raise HTTPException(status_code=500, detail="AI configuration not found in database")
            
            document_ai_config = ai_config_doc.get("document_ai", {})
            if not document_ai_config.get("enabled", False):
                raise HTTPException(status_code=400, detail="Google Document AI is not enabled")
            
            # Get Google Drive config
            user_company_id = current_user.company
            gdrive_config_doc = await db.company_gdrive_config.find_one({"company_id": user_company_id})
            
            if not gdrive_config_doc:
                raise HTTPException(status_code=500, detail="Google Drive not configured")
            
            # Step 3: Categorize files into FAST and SLOW paths
            fast_path_files = []
            slow_path_files = []
            
            for file in files:
                file_content = await file.read()
                await file.seek(0)  # Reset for later use
                
                path_info = SurveyReportMultiUploadService.quick_check_processing_path(
                    file_content, file.filename
                )
                
                logger.info(f"📁 {file.filename}: {path_info['path']} - {path_info['reason']}")
                
                if path_info["path"] == "FAST_PATH":
                    fast_path_files.append({
                        "file": file,
                        "content": file_content,
                        "path_info": path_info
                    })
                else:
                    slow_path_files.append({
                        "file": file,
                        "content": file_content,
                        "path_info": path_info
                    })
            
            logger.info(f"📊 Path distribution: {len(fast_path_files)} FAST, {len(slow_path_files)} SLOW")
            
            # Step 4: Process FAST PATH files immediately
            fast_results = []
            for file_data in fast_path_files:
                try:
                    result = await SurveyReportMultiUploadService._process_single_file_fast(
                        file_content=file_data["content"],
                        filename=file_data["file"].filename,
                        content_type=file_data["file"].content_type or "application/pdf",
                        ship_id=ship_id,
                        ship=ship,
                        ai_config=ai_config,
                        ai_config_doc=ai_config_doc,
                        gdrive_config_doc=gdrive_config_doc,
                        current_user=current_user,
                        db=db
                    )
                    result["processing_path"] = "FAST_PATH"
                    fast_results.append(result)
                    
                except Exception as e:
                    logger.error(f"❌ FAST PATH error for {file_data['file'].filename}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    fast_results.append({
                        "filename": file_data["file"].filename,
                        "status": "error",
                        "message": str(e),
                        "processing_path": "FAST_PATH"
                    })
            
            # Step 5: Create background task for SLOW PATH files
            task_id = None
            if slow_path_files:
                # Save files to temp storage
                temp_files = []
                for file_data in slow_path_files:
                    temp_dir = tempfile.mkdtemp(prefix="survey_upload_")
                    temp_path = os.path.join(temp_dir, file_data["file"].filename)
                    
                    with open(temp_path, "wb") as f:
                        f.write(file_data["content"])
                    
                    temp_files.append({
                        "temp_path": temp_path,
                        "filename": file_data["file"].filename,
                        "content_type": file_data["file"].content_type,
                        "path_info": file_data["path_info"]
                    })
                
                # Create task in database
                task_id = await UploadTaskService.create_task(
                    task_type="survey_report",
                    ship_id=ship_id,
                    filenames=[f["filename"] for f in temp_files],
                    current_user=current_user
                )
                
                # Schedule background processing
                background_tasks.add_task(
                    SurveyReportMultiUploadService._process_slow_path_background,
                    task_id=task_id,
                    temp_files=temp_files,
                    ship_id=ship_id,
                    ship=ship,
                    ai_config=ai_config,
                    ai_config_doc=ai_config_doc,
                    gdrive_config_doc=gdrive_config_doc,
                    user_id=current_user.id,
                    company_id=current_user.company
                )
                
                logger.info(f"📋 Created background task {task_id} for {len(slow_path_files)} SLOW PATH files")
            
            # Step 6: Build response
            response = {
                "fast_path_results": fast_results,
                "slow_path_task_id": task_id,
                "summary": {
                    "total_files": len(files),
                    "fast_path_count": len(fast_path_files),
                    "slow_path_count": len(slow_path_files),
                    "fast_path_completed": len([r for r in fast_results if r.get("status") == "success"]),
                    "fast_path_errors": len([r for r in fast_results if r.get("status") == "error"]),
                    "slow_path_processing": len(slow_path_files) > 0
                },
                "ship": {
                    "id": ship_id,
                    "name": ship.get("name", "Unknown Ship")
                }
            }
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Smart multi-upload error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    @staticmethod
    async def _process_single_file_fast(
        file_content: bytes,
        filename: str,
        content_type: str,
        ship_id: str,
        ship: Dict[str, Any],
        ai_config: Dict[str, Any],
        ai_config_doc: Dict[str, Any],
        gdrive_config_doc: Dict[str, Any],
        current_user: UserResponse,
        db
    ) -> Dict[str, Any]:
        """
        Process single survey report file via FAST PATH (text layer)
        Uses AI Text Correction for better quality
        """
        from app.utils.pdf_text_extractor import extract_text_from_pdf_text_layer, create_summary_from_text_layer
        from app.utils.text_layer_correction import correct_text_layer_with_ai, detect_ocr_quality
        from app.utils.survey_report_ai import extract_survey_report_fields_from_summary, extract_report_form_from_filename
        from app.services.survey_report_service import SurveyReportService
        
        logger.info(f"🚀 FAST PATH processing: {filename}")
        
        try:
            # Step 1: Extract text layer
            text_content = extract_text_from_pdf_text_layer(file_content)
            
            if not text_content or len(text_content.strip()) < TEXT_LAYER_THRESHOLD:
                return {
                    "filename": filename,
                    "status": "error",
                    "message": f"Text layer too short ({len(text_content or '')} chars)"
                }
            
            # Step 2: Check text quality and correct if needed
            quality_info = detect_ocr_quality(text_content)
            
            if quality_info.get("needs_correction", False):
                logger.info(f"🔧 Text needs correction (quality: {quality_info.get('quality_score', 0)})")
                
                correction_result = await correct_text_layer_with_ai(
                    text_content,
                    filename,
                    ai_config
                )
                
                if correction_result.get("success") and correction_result.get("correction_applied"):
                    text_content = correction_result["corrected_text"]
                    logger.info(f"✅ AI correction applied for {filename}")
            
            # Step 3: Create summary
            summary_text = create_summary_from_text_layer(text_content, filename)
            
            # Add processing info header
            summary_header = f"""{"="*80}
SURVEY REPORT SUMMARY - FAST PATH (Text Layer)
File: {filename}
Processing: Text Layer Extraction + AI Correction
{"="*80}

"""
            summary_text = summary_header + summary_text
            
            # Step 4: Extract fields with Gemini AI
            ai_provider = ai_config_doc.get("provider", "google")
            ai_model = ai_config_doc.get("model", "gemini-2.0-flash-exp")
            use_emergent_key = ai_config_doc.get("use_emergent_key", True)
            
            extracted_fields = await extract_survey_report_fields_from_summary(
                summary_text,
                ai_provider,
                ai_model,
                use_emergent_key,
                filename
            )
            
            # Normalize issued_by
            if extracted_fields and extracted_fields.get('issued_by'):
                try:
                    from app.utils.issued_by_abbreviation import normalize_issued_by
                    original = extracted_fields['issued_by']
                    normalized = normalize_issued_by(original)
                    if normalized != original:
                        extracted_fields['issued_by'] = normalized
                except Exception:
                    pass
            
            # Try to extract report_form from filename if not found
            if extracted_fields and not extracted_fields.get('report_form'):
                filename_form = extract_report_form_from_filename(filename)
                if filename_form:
                    extracted_fields['report_form'] = filename_form
            
            # Step 5: Create survey report record
            report_data = {
                "ship_id": ship_id,
                "survey_report_name": extracted_fields.get("survey_report_name", "") if extracted_fields else "",
                "report_form": extracted_fields.get("report_form", "") if extracted_fields else "",
                "survey_report_no": extracted_fields.get("survey_report_no", "") if extracted_fields else "",
                "issued_date": extracted_fields.get("issued_date") if extracted_fields else None,
                "issued_by": extracted_fields.get("issued_by", "") if extracted_fields else "",
                "status": extracted_fields.get("status", "Valid") if extracted_fields else "Valid",
                "note": extracted_fields.get("note", "") if extracted_fields else "",
                "surveyor_name": extracted_fields.get("surveyor_name", "") if extracted_fields else ""
            }
            
            # If no name extracted, use filename
            if not report_data["survey_report_name"]:
                report_data["survey_report_name"] = filename.replace(".pdf", "").replace(".PDF", "")
            
            from app.models.survey_report import SurveyReportCreate
            report_create = SurveyReportCreate(**report_data)
            
            created_report = await SurveyReportService.create_survey_report(report_create, current_user)
            
            logger.info(f"✅ Created survey report: {created_report.id}")
            
            # Step 6: Upload files to Google Drive
            file_content_b64 = base64.b64encode(file_content).decode('utf-8')
            
            try:
                await SurveyReportService.upload_files(
                    report_id=created_report.id,
                    file_content=file_content_b64,
                    filename=filename,
                    content_type=content_type,
                    summary_text=summary_text,
                    current_user=current_user
                )
                logger.info(f"✅ Uploaded files for report {created_report.id}")
            except Exception as upload_error:
                logger.warning(f"⚠️ File upload failed: {upload_error}")
            
            return {
                "filename": filename,
                "status": "success",
                "message": "Survey report created successfully",
                "report_id": created_report.id,
                "extracted_info": {
                    "survey_report_name": report_data["survey_report_name"],
                    "report_form": report_data["report_form"],
                    "survey_report_no": report_data["survey_report_no"],
                    "issued_by": report_data["issued_by"]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ FAST PATH error for {filename}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "filename": filename,
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    async def _process_slow_path_background(
        task_id: str,
        temp_files: List[Dict],
        ship_id: str,
        ship: Dict[str, Any],
        ai_config: Dict[str, Any],
        ai_config_doc: Dict[str, Any],
        gdrive_config_doc: Dict[str, Any],
        user_id: str,
        company_id: str
    ):
        """
        Background task to process SLOW PATH files with Document AI
        """
        from app.services.survey_report_analyze_service import SurveyReportAnalyzeService
        from app.services.survey_report_service import SurveyReportService
        from app.models.survey_report import SurveyReportCreate
        
        logger.info(f"🔄 Starting background processing for task {task_id}")
        
        try:
            # Update task status
            await UploadTaskService.update_task_status(task_id, TaskStatus.PROCESSING)
            
            db = mongo_db.database
            
            # Get user from database
            user_doc = await db.users.find_one({"id": user_id})
            if not user_doc:
                logger.error(f"❌ User not found: {user_id}")
                await UploadTaskService.update_task_status(task_id, TaskStatus.FAILED)
                return
            
            # Build UserResponse
            real_user = UserResponse(
                id=user_doc["id"],
                email=user_doc.get("email") or "",
                username=user_doc["username"],
                full_name=user_doc.get("full_name", ""),
                role=UserRole(user_doc.get("role", "viewer")),
                company=user_doc.get("company") or company_id,
                department=user_doc.get("department") or [],
                ship=user_doc.get("ship"),
                zalo=user_doc.get("zalo"),
                gmail=user_doc.get("gmail"),
                is_active=user_doc.get("is_active", True),
                signature_file_id=user_doc.get("signature_file_id"),
                signature_url=user_doc.get("signature_url"),
                crew_id=user_doc.get("crew_id"),
                created_at=user_doc.get("created_at") or datetime.now(timezone.utc),
                permissions=user_doc.get("permissions") or {}
            )
            
            # Process each file
            for i, temp_file in enumerate(temp_files):
                try:
                    logger.info(f"🔄 [{i+1}/{len(temp_files)}] Processing: {temp_file['filename']}")
                    
                    # Update progress
                    await UploadTaskService.update_file_status(
                        task_id, i, TaskStatus.PROCESSING,
                        progress=10,
                        processing_type=ProcessingType.DOCUMENT_AI
                    )
                    
                    # Read file content
                    with open(temp_file["temp_path"], "rb") as f:
                        file_content = f.read()
                    
                    # Create mock UploadFile
                    from io import BytesIO
                    from starlette.datastructures import UploadFile as StarletteUploadFile, Headers
                    
                    file_obj = BytesIO(file_content)
                    content_type = temp_file.get("content_type", "application/pdf")
                    headers = Headers({"content-type": content_type})
                    
                    mock_file = StarletteUploadFile(
                        file=file_obj,
                        filename=temp_file["filename"],
                        headers=headers
                    )
                    
                    # Update progress
                    await UploadTaskService.update_file_status(
                        task_id, i, TaskStatus.PROCESSING,
                        progress=30
                    )
                    
                    # Analyze with Document AI
                    analysis_result = await SurveyReportAnalyzeService.analyze_file(
                        file=mock_file,
                        ship_id=ship_id,
                        bypass_validation=True,
                        current_user=real_user
                    )
                    
                    # Update progress
                    await UploadTaskService.update_file_status(
                        task_id, i, TaskStatus.PROCESSING,
                        progress=70,
                        message="Creating record..."
                    )
                    
                    if analysis_result.get("success"):
                        analysis = analysis_result.get("analysis", {})
                        
                        # ⚡ OPTIMIZED: Create survey report record FIRST (without file_id)
                        report_data = {
                            "ship_id": ship_id,
                            "survey_report_name": analysis.get("survey_report_name", temp_file["filename"]),
                            "report_form": analysis.get("report_form", ""),
                            "survey_report_no": analysis.get("survey_report_no", ""),
                            "issued_date": analysis.get("issued_date"),
                            "issued_by": analysis.get("issued_by", ""),
                            "status": analysis.get("status", "Valid"),
                            "note": analysis.get("note", ""),
                            "surveyor_name": analysis.get("surveyor_name", "")
                        }
                        
                        report_create = SurveyReportCreate(**report_data)
                        created_report = await SurveyReportService.create_survey_report(report_create, real_user)
                        
                        logger.info(f"✅ [{i+1}/{len(temp_files)}] Record created: {created_report.id} (GDrive upload pending)")
                        
                        # Update file status - completed IMMEDIATELY (user sees success faster)
                        await UploadTaskService.update_file_status(
                            task_id, i, TaskStatus.COMPLETED,
                            progress=100,
                            result={
                                "report_id": created_report.id,
                                "survey_report_name": report_data["survey_report_name"],
                                "report_form": report_data["report_form"],
                                "survey_report_no": report_data["survey_report_no"],
                                "status": "success",
                                "extracted_info": {
                                    "survey_report_name": report_data["survey_report_name"],
                                    "report_form": report_data["report_form"],
                                    "survey_report_no": report_data["survey_report_no"],
                                    "issued_by": report_data["issued_by"]
                                },
                                "gdrive_pending": True
                            }
                        )
                        await UploadTaskService.increment_completed(task_id, success=True)
                        
                        logger.info(f"✅ [{i+1}/{len(temp_files)}] Completed (record created): {temp_file['filename']}")
                        
                        # ⚡ Upload files to Google Drive in DEFERRED background (non-blocking)
                        if analysis.get("_file_content"):
                            import asyncio
                            asyncio.create_task(
                                SurveyReportMultiUploadService._deferred_gdrive_upload(
                                    report_id=created_report.id,
                                    file_content=analysis["_file_content"],
                                    filename=analysis.get("_filename", temp_file["filename"]),
                                    content_type=analysis.get("_content_type", "application/pdf"),
                                    summary_text=analysis.get("_summary_text", ""),
                                    user_id=user_id,
                                    company_id=company_id
                                )
                            )
                    else:
                        # Analysis failed
                        error_msg = analysis_result.get("message", "Analysis failed")
                        await UploadTaskService.update_file_status(
                            task_id, i, TaskStatus.FAILED,
                            progress=100,
                            error=error_msg
                        )
                        await UploadTaskService.increment_completed(task_id, success=False)
                        logger.error(f"❌ [{i+1}/{len(temp_files)}] Failed: {temp_file['filename']} - {error_msg}")
                    
                except Exception as file_error:
                    logger.error(f"❌ Error processing {temp_file['filename']}: {file_error}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    await UploadTaskService.update_file_status(
                        task_id, i, TaskStatus.FAILED,
                        progress=100,
                        error=str(file_error)
                    )
                    await UploadTaskService.increment_completed(task_id, success=False)
                
                finally:
                    # Clean up temp file
                    try:
                        if os.path.exists(temp_file["temp_path"]):
                            os.remove(temp_file["temp_path"])
                            parent_dir = os.path.dirname(temp_file["temp_path"])
                            if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                                os.rmdir(parent_dir)
                    except Exception:
                        pass
            
            logger.info(f"✅ Background task {task_id} completed")
            
        except Exception as e:
            logger.error(f"❌ Background task {task_id} failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await UploadTaskService.update_task_status(task_id, TaskStatus.FAILED)
