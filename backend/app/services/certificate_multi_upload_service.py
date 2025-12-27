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

# ⭐ ISM/ISPS/MLC/CICA Certificate Categories (from audit_certificate_ai.py)
AUDIT_CERTIFICATE_CATEGORIES = {
    "ISM": [
        "SAFETY MANAGEMENT CERTIFICATE",
        "INTERIM SAFETY MANAGEMENT CERTIFICATE",
        "SMC",
        "DOCUMENT OF COMPLIANCE",
        "INTERIM DOCUMENT OF COMPLIANCE",
        "DOC",
    ],
    "ISPS": [
        "INTERNATIONAL SHIP SECURITY CERTIFICATE",
        "INTERIM INTERNATIONAL SHIP SECURITY CERTIFICATE",
        "ISSC",
        "SHIP SECURITY PLAN",
        "SSP",
    ],
    "MLC": [
        "MARITIME LABOUR CERTIFICATE",
        "INTERIM MARITIME LABOUR CERTIFICATE",
        "MLC",
        "DECLARATION OF MARITIME LABOUR COMPLIANCE",
        "DMLC",
        "DMLC PART I",
        "DMLC PART II",
    ],
    "CICA": [
        "CERTIFICATE OF INSPECTION",
        "CREW ACCOMMODATION CERTIFICATE",
        "STATEMENT OF COMPLIANCE OF CREW ACCOMMODATION",
        "CERTIFICATE OF INSPECTION / STATEMENT OF COMPLIANCE OF CREW ACCOMMODATION",
        "CREW ACCOMMODATION INSPECTION",
        "CICA",
    ]
}

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
            
            # ⭐ NEW: Permission checks
            from app.core.permission_checks import (
                check_company_access,
                check_create_permission,
                check_editor_viewer_ship_scope
            )
            
            # Check company access
            ship_company_id = ship.get("company")
            check_company_access(current_user, ship_company_id, "create ship certificates")
            
            # Check create permission (includes role + department checks)
            check_create_permission(current_user, "ship_cert", ship_company_id)
            
            # For Editor/Viewer: check ship scope
            check_editor_viewer_ship_scope(current_user, ship_id, "create ship certificates")
            
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
            
            # Step 3.5: Warmup Apps Script to avoid cold start delay
            apps_script_url = gdrive_config_doc.get("web_app_url") or gdrive_config_doc.get("apps_script_url")
            if apps_script_url and len(files) > 0:
                import aiohttp
                import time
                warmup_start = time.time()
                logger.info("🔥 Warming up Apps Script before processing certificates...")
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            apps_script_url,
                            json={"action": "ping"},
                            timeout=aiohttp.ClientTimeout(total=15)
                        ) as response:
                            warmup_elapsed = time.time() - warmup_start
                            logger.info(f"🔥 Apps Script warmup completed in {warmup_elapsed:.2f}s (status: {response.status})")
                except Exception as warmup_error:
                    logger.warning(f"⚠️ Apps Script warmup failed (continuing anyway): {warmup_error}")
            
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
    async def process_multi_upload_smart(
        ship_id: str,
        files: List[UploadFile],
        current_user: UserResponse,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """
        Smart multi-upload - ALL files go to SLOW PATH (background processing)
        
        This ensures:
        - Immediate response (~1-2 seconds) - NO TIMEOUT
        - All processing happens in background
        - Health checks always respond
        - Frontend polls for completion
        
        Returns task_id for polling
        """
        from app.services.upload_task_service import UploadTaskService
        from app.models.upload_task import TaskStatus, ProcessingType
        import tempfile
        import os as os_module
        
        try:
            db = mongo_db.database
            
            # Step 1: Verify ship and permissions (fast - ~100ms)
            ship = await db.ships.find_one({"id": ship_id})
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
            
            from app.core.permission_checks import (
                check_company_access,
                check_create_permission,
                check_editor_viewer_ship_scope
            )
            
            ship_company_id = ship.get("company")
            check_company_access(current_user, ship_company_id, "create ship certificates")
            check_create_permission(current_user, "ship_cert", ship_company_id)
            check_editor_viewer_ship_scope(current_user, ship_id, "create ship certificates")
            
            # Step 2: Get configurations (fast - ~100ms)
            try:
                ai_config_obj = await AIConfigService.get_ai_config(current_user)
                ai_config = {
                    "provider": ai_config_obj.provider,
                    "model": ai_config_obj.model,
                    "api_key": os.getenv("EMERGENT_LLM_KEY"),
                    "use_emergent_key": True
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail="AI configuration not found")
            
            user_company_id = await CertificateMultiUploadService._resolve_company_id(current_user)
            gdrive_config_doc = await db.company_gdrive_config.find_one({"company_id": user_company_id})
            
            if not gdrive_config_doc:
                raise HTTPException(status_code=500, detail="Google Drive not configured")
            
            # Step 3: Save ALL files to temp storage (fast - ~500ms)
            # NO PROCESSING HERE - just save files for background task
            logger.info(f"📊 Queueing {len(files)} files for BACKGROUND processing")
            
            temp_files = []
            for file in files:
                file_content = await file.read()
                
                # Save to temp file
                temp_dir = tempfile.mkdtemp(prefix="cert_upload_")
                temp_path = os_module.path.join(temp_dir, file.filename)
                
                with open(temp_path, "wb") as f:
                    f.write(file_content)
                
                temp_files.append({
                    "temp_path": temp_path,
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "path_info": {"path": "BACKGROUND", "reason": "All files processed in background for reliability"}
                })
                
                logger.info(f"📁 {file.filename}: Saved to temp, queued for background processing")
            
            # Step 4: Create task in database (fast - ~100ms)
            task_id = await UploadTaskService.create_task(
                task_type="certificate",
                ship_id=ship_id,
                filenames=[f["filename"] for f in temp_files],
                current_user=current_user
            )
            
            # Step 5: Schedule background processing (immediate - no blocking)
            background_tasks.add_task(
                CertificateMultiUploadService._process_all_files_background,
                task_id=task_id,
                temp_files=temp_files,
                ship_id=ship_id,
                ship=ship,
                ai_config=ai_config,
                gdrive_config_doc=gdrive_config_doc,
                user_id=current_user.id,
                company_id=current_user.company
            )
            
            logger.info(f"📋 Created background task {task_id} for {len(files)} files - returning immediately")
            
            # Step 6: Return IMMEDIATELY with task_id
            # Total time: ~1 second (no blocking operations)
            response = {
                "fast_path_results": [],  # All files go to background
                "slow_path_task_id": task_id,
                "summary": {
                    "total_files": len(files),
                    "fast_path_count": 0,
                    "slow_path_count": len(files),
                    "fast_path_completed": 0,
                    "fast_path_errors": 0,
                    "slow_path_processing": True
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
    async def _process_all_files_background(
        task_id: str,
        temp_files: List[Dict],
        ship_id: str,
        ship: Dict[str, Any],
        ai_config: Dict[str, Any],
        gdrive_config_doc: Dict[str, Any],
        user_id: str,
        company_id: str
    ):
        """
        Background task to process ALL certificate files
        This runs asynchronously after returning immediate response to client
        Ensures health checks always respond
        """
        from app.services.upload_task_service import UploadTaskService
        from app.models.upload_task import TaskStatus
        from app.models.user import UserResponse
        import os as os_module
        import asyncio
        
        logger.info(f"🔄 Starting background processing for task {task_id} ({len(temp_files)} files)")
        
        try:
            # Update task status to processing
            logger.info(f"🔄 Task {task_id}: Updating status to PROCESSING")
            await UploadTaskService.update_task_status(task_id, TaskStatus.PROCESSING)
            
            db = mongo_db.database
            
            # Get user info
            logger.info(f"🔄 Task {task_id}: Finding user {user_id}")
            user_doc = await db.users.find_one({"id": user_id})
            if not user_doc:
                logger.error(f"❌ Task {task_id}: User not found: {user_id}")
                await UploadTaskService.update_task_status(task_id, TaskStatus.FAILED)
                return
            
            # Process each file
            for i, temp_file in enumerate(temp_files):
                try:
                    filename = temp_file["filename"]
                    logger.info(f"📄 [{i+1}/{len(temp_files)}] Processing: {filename}")
                    
                    # Update file status
                    await UploadTaskService.update_file_status_by_name(
                        task_id, filename, "processing", progress=10
                    )
                    
                    # Read file content
                    with open(temp_file["temp_path"], "rb") as f:
                        file_content = f.read()
                    
                    # Step 1: Analyze with AI
                    await UploadTaskService.update_file_status_by_name(
                        task_id, filename, "processing", progress=20,
                        message="Analyzing document with AI..."
                    )
                    
                    analysis_result = await CertificateMultiUploadService._analyze_document_with_ai(
                        file_content, filename, temp_file["content_type"],
                        ai_config, ship_id, None  # No current_user in background
                    )
                    
                    if not analysis_result.get("success"):
                        raise Exception(analysis_result.get("message", "Analysis failed"))
                    
                    extracted_info = analysis_result.get("extracted_info", {})
                    summary_text = analysis_result.get("summary_text", "")
                    extracted_info["filename"] = filename
                    
                    await UploadTaskService.update_file_status_by_name(
                        task_id, filename, "processing", progress=50,
                        message="AI analysis complete, uploading to Google Drive..."
                    )
                    
                    # Step 2: Upload PDF and Summary to GDrive in parallel
                    ship_name = ship.get("name", "Unknown_Ship")
                    
                    upload_tasks = [
                        CertificateMultiUploadService._upload_to_gdrive_with_parent(
                            gdrive_config_doc, file_content, filename, ship_name,
                            "Class & Flag Cert", "Certificates"
                        )
                    ]
                    
                    if summary_text and summary_text.strip():
                        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                        summary_filename = f"{base_name}_Summary.txt"
                        summary_bytes = summary_text.encode('utf-8')
                        upload_tasks.append(
                            CertificateMultiUploadService._upload_to_gdrive_with_parent(
                                gdrive_config_doc, summary_bytes, summary_filename, ship_name,
                                "Class & Flag Cert", "Certificates", content_type="text/plain"
                            )
                        )
                    
                    upload_results = await asyncio.gather(*upload_tasks, return_exceptions=True)
                    
                    pdf_result = upload_results[0] if len(upload_results) > 0 else None
                    summary_result = upload_results[1] if len(upload_results) > 1 else None
                    
                    await UploadTaskService.update_file_status(
                        task_id, filename, "processing", progress=80,
                        message="Creating certificate record..."
                    )
                    
                    # Step 3: Create certificate record
                    upload_data = {
                        "success": True,
                        "file_id": pdf_result.get("file_id") if pdf_result and not isinstance(pdf_result, Exception) else None,
                        "file_url": pdf_result.get("file_url") if pdf_result and not isinstance(pdf_result, Exception) else None,
                        "folder_path": f"{ship_name}/Class & Flag Cert/Certificates"
                    }
                    
                    summary_file_id = None
                    if summary_result and not isinstance(summary_result, Exception) and summary_result.get("success"):
                        summary_file_id = summary_result.get("file_id")
                    
                    # Create minimal user response for certificate creation
                    from app.models.user import UserRole
                    mock_user = UserResponse(
                        id=user_id,
                        username=user_doc.get("username", "system"),
                        email=user_doc.get("email", "system@system.com"),
                        role=UserRole(user_doc.get("role", "admin")),
                        company=company_id,
                        department=user_doc.get("department"),
                        is_active=True
                    )
                    
                    cert_result = await CertificateMultiUploadService._create_certificate_from_analysis(
                        extracted_info, upload_data, mock_user, ship_id,
                        None, db, summary_file_id=summary_file_id,
                        extracted_ship_name=extracted_info.get("ship_name")
                    )
                    
                    # Mark file as completed
                    await UploadTaskService.update_file_status(
                        task_id, filename, "completed", progress=100,
                        result={
                            "certificate_id": cert_result.get("id"),
                            "extracted_info": extracted_info,
                            "file_id": upload_data.get("file_id")
                        }
                    )
                    
                    logger.info(f"✅ [{i+1}/{len(temp_files)}] Completed: {filename}")
                    
                except Exception as file_error:
                    logger.error(f"❌ [{i+1}/{len(temp_files)}] Error processing {temp_file['filename']}: {file_error}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    await UploadTaskService.update_file_status(
                        task_id, temp_file["filename"], "failed",
                        error=str(file_error)
                    )
                
                finally:
                    # Clean up temp file
                    try:
                        if os_module.path.exists(temp_file["temp_path"]):
                            os_module.remove(temp_file["temp_path"])
                            os_module.rmdir(os_module.path.dirname(temp_file["temp_path"]))
                    except:
                        pass
            
            # Mark task as completed
            await UploadTaskService.update_task_status(task_id, TaskStatus.COMPLETED)
            logger.info(f"✅ Background task {task_id} completed")
            
        except Exception as e:
            logger.error(f"❌ Background task {task_id} failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await UploadTaskService.update_task_status(task_id, TaskStatus.FAILED)
    
    @staticmethod
    async def _process_slow_path_background(
        task_id: str,
        temp_files: List[Dict],
        ship_id: str,
        ship: Dict[str, Any],
        ai_config: Dict[str, Any],
        gdrive_config_doc: Dict[str, Any],
        user_id: str,
        company_id: str
    ):
        """
        Background task to process SLOW PATH files with Document AI
        This runs asynchronously after returning response to client
        """
        from app.services.upload_task_service import UploadTaskService
        from app.models.upload_task import TaskStatus, ProcessingType
        from app.models.user import UserResponse
        import os as os_module
        
        logger.info(f"🔄 Starting background processing for task {task_id}")
        
        try:
            # Update task status to processing
            await UploadTaskService.update_task_status(task_id, TaskStatus.PROCESSING)
            
            db = mongo_db.database
            
            # Create a minimal user object for permission checks
            user_doc = await db.users.find_one({"id": user_id})
            if not user_doc:
                logger.error(f"❌ User not found: {user_id}")
                await UploadTaskService.update_task_status(task_id, TaskStatus.FAILED)
                return
            
            # Process each file
            for i, temp_file in enumerate(temp_files):
                try:
                    logger.info(f"🔄 [{i+1}/{len(temp_files)}] Processing: {temp_file['filename']}")
                    
                    # Update file status to processing
                    await UploadTaskService.update_file_status(
                        task_id, i, TaskStatus.PROCESSING,
                        progress=10,
                        processing_type=ProcessingType.DOCUMENT_AI
                    )
                    
                    # Read file from temp storage
                    with open(temp_file["temp_path"], "rb") as f:
                        file_content = f.read()
                    
                    # Create mock UploadFile with headers for content_type
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
                    
                    # Get real user from database (convert document to UserResponse)
                    from app.models.user import UserResponse, UserRole
                    from datetime import datetime, timezone
                    
                    # Build UserResponse from database document
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
                    
                    # Update progress - starting Document AI
                    await UploadTaskService.update_file_status(
                        task_id, i, TaskStatus.PROCESSING,
                        progress=20
                    )
                    
                    # Process file (this will use SLOW PATH with Document AI)
                    result = await CertificateMultiUploadService._process_single_file(
                        file=mock_file,
                        ship_id=ship_id,
                        ship=ship,
                        ai_config=ai_config,
                        gdrive_config_doc=gdrive_config_doc,
                        current_user=real_user,
                        db=db
                    )
                    
                    # Update file status based on result
                    if result.get("status") == "success":
                        await UploadTaskService.update_file_status(
                            task_id, i, TaskStatus.COMPLETED,
                            progress=100,
                            result=result
                        )
                        await UploadTaskService.increment_completed(task_id, success=True)
                        logger.info(f"✅ [{i+1}/{len(temp_files)}] Completed: {temp_file['filename']}")
                    else:
                        await UploadTaskService.update_file_status(
                            task_id, i, TaskStatus.FAILED,
                            progress=100,
                            error=result.get("message", "Processing failed")
                        )
                        await UploadTaskService.increment_completed(task_id, success=False)
                        logger.error(f"❌ [{i+1}/{len(temp_files)}] Failed: {temp_file['filename']}")
                    
                except Exception as file_error:
                    logger.error(f"❌ Error processing {temp_file['filename']}: {file_error}")
                    await UploadTaskService.update_file_status(
                        task_id, i, TaskStatus.FAILED,
                        progress=100,
                        error=str(file_error)
                    )
                    await UploadTaskService.increment_completed(task_id, success=False)
                
                finally:
                    # Cleanup temp file
                    try:
                        if os_module.path.exists(temp_file["temp_path"]):
                            os_module.remove(temp_file["temp_path"])
                            # Also remove temp directory if empty
                            temp_dir = os_module.path.dirname(temp_file["temp_path"])
                            if os_module.path.exists(temp_dir) and not os_module.listdir(temp_dir):
                                os_module.rmdir(temp_dir)
                    except Exception as cleanup_error:
                        logger.warning(f"⚠️ Cleanup error: {cleanup_error}")
            
            logger.info(f"✅ Background task {task_id} completed")
            
        except Exception as e:
            logger.error(f"❌ Background task {task_id} failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await UploadTaskService.update_task_status(task_id, TaskStatus.FAILED)
    
    @staticmethod
    async def _process_single_file(
        file: UploadFile,
        ship_id: str,
        ship: Dict[str, Any],
        ai_config: Dict[str, Any],
        gdrive_config_doc: Dict[str, Any],
        current_user: UserResponse,
        db: Any,
        background_tasks: Any = None  # Optional for background GDrive upload
    ) -> Dict[str, Any]:
        """
        Process a single certificate file - OPTIMIZED VERSION
        
        Flow:
        1. Extract text from PDF (fast)
        2. Extract fields with Gemini AI (~4-5s)
        3. Create DB record immediately → Return to frontend
        4. Background: Upload PDF + Summary to GDrive in parallel
        5. Update DB with file URLs when upload completes
        """
        import time
        import asyncio
        
        timing = {}
        total_start = time.time()
        
        # Read file content
        step_start = time.time()
        file_content = await file.read()
        timing['1_read_file'] = round(time.time() - step_start, 2)
        
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
        
        # ⭐ Step 2: Analyze document with AI pipeline
        step_start = time.time()
        analysis_result = await CertificateMultiUploadService._analyze_document_with_ai(
            file_content, 
            file.filename, 
            file.content_type, 
            ai_config,
            ship_id,
            current_user
        )
        timing['2_ai_analysis'] = round(time.time() - step_start, 2)
        
        # Check if analysis was successful
        if not analysis_result.get("success"):
            error_msg = analysis_result.get("message", "Analysis failed")
            return {
                "filename": file.filename,
                "status": "error",
                "message": error_msg
            }
        
        # Extract components from analysis result
        extracted_info = analysis_result.get("extracted_info", {})
        summary_text = analysis_result.get("summary_text", "")
        validation_warning = analysis_result.get("validation_warning")
        duplicate_warning = analysis_result.get("duplicate_warning")
        
        # Add filename to extracted_info
        extracted_info["filename"] = file.filename
        
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
                "summary_text": summary_text
            }
        
        # Check if certificate belongs to ISM/ISPS/MLC/CICA categories (BLOCKING)
        cert_name = extracted_info.get('cert_name', '').strip()
        audit_category = CertificateMultiUploadService._check_if_audit_certificate(cert_name)
        if audit_category:
            error_message = f"Giấy chứng nhận này thuộc danh mục {audit_category}, vui lòng upload vào đúng danh mục"
            logger.error(f"🚫 Blocking: {file.filename} is {audit_category} certificate")
            return {
                "filename": file.filename,
                "status": "error",
                "message": error_message,
                "category_error": {
                    "detected_category": audit_category,
                    "cert_name": cert_name,
                    "message": error_message
                }
            }
        
        # Prepare validation note
        extracted_ship_name = extracted_info.get('ship_name', '').strip()
        validation_note = None
        progress_message = None
        if validation_warning and not validation_warning.get("is_blocking"):
            validation_note = validation_warning.get("override_note", "Chỉ để tham khảo")
            progress_message = validation_warning.get("message")
            logger.info(f"⚠️ Non-blocking validation warning: {progress_message}")
        
        # ⭐ Step 3: Create certificate record IMMEDIATELY (without file URLs)
        # This allows frontend to refresh UI right away
        step_start = time.time()
        ship_name = ship.get("name", "Unknown_Ship")
        
        cert_result = await CertificateMultiUploadService._create_certificate_from_analysis(
            extracted_info, 
            {"success": True, "file_id": None, "file_url": None, "folder_path": f"{ship_name}/Class & Flag Cert/Certificates"},  # Placeholder
            current_user, 
            ship_id, 
            validation_note, 
            db,
            summary_file_id=None,  # Will update later
            extracted_ship_name=extracted_ship_name,
            file_pending_upload=True  # Mark as pending upload
        )
        timing['3_create_db_record'] = round(time.time() - step_start, 2)
        
        cert_id = cert_result.get("id")
        logger.info(f"✅ Created certificate record {cert_id} (file upload pending)")
        
        # ⭐ Step 4: Schedule background upload for GDrive (PDF + Summary in parallel)
        if background_tasks and cert_id:
            background_tasks.add_task(
                CertificateMultiUploadService._upload_files_to_gdrive_background,
                cert_id=cert_id,
                file_content=file_content,
                filename=file.filename,
                summary_text=summary_text,
                ship_name=ship_name,
                gdrive_config_doc=gdrive_config_doc
            )
            logger.info(f"📤 Scheduled background GDrive upload for {file.filename}")
        else:
            # Fallback: Upload synchronously if no background_tasks
            logger.info(f"📤 Uploading to GDrive synchronously (no background_tasks)")
            step_start = time.time()
            
            # Upload PDF and Summary in parallel using asyncio.gather
            upload_tasks = []
            
            # Task 1: Upload main PDF
            upload_tasks.append(
                CertificateMultiUploadService._upload_to_gdrive_with_parent(
                    gdrive_config_doc, file_content, file.filename, ship_name,
                    "Class & Flag Cert", "Certificates"
                )
            )
            
            # Task 2: Upload Summary (if available)
            if summary_text and summary_text.strip():
                base_name = file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename
                summary_filename = f"{base_name}_Summary.txt"
                summary_bytes = summary_text.encode('utf-8')
                
                upload_tasks.append(
                    CertificateMultiUploadService._upload_to_gdrive_with_parent(
                        gdrive_config_doc, summary_bytes, summary_filename, ship_name,
                        "Class & Flag Cert", "Certificates", content_type="text/plain"
                    )
                )
            
            # Execute uploads in parallel
            upload_results = await asyncio.gather(*upload_tasks, return_exceptions=True)
            timing['4_gdrive_upload_parallel'] = round(time.time() - step_start, 2)
            
            # Process results
            pdf_result = upload_results[0] if len(upload_results) > 0 else None
            summary_result = upload_results[1] if len(upload_results) > 1 else None
            
            # Update certificate record with file URLs
            update_data = {}
            if pdf_result and not isinstance(pdf_result, Exception) and pdf_result.get("success"):
                update_data["google_drive_file_id"] = pdf_result.get("file_id")
                update_data["google_drive_file_url"] = pdf_result.get("file_url")
                update_data["file_uploaded"] = True
                update_data["file_pending_upload"] = False
                logger.info(f"✅ PDF uploaded: {pdf_result.get('file_id')}")
            
            if summary_result and not isinstance(summary_result, Exception) and summary_result.get("success"):
                update_data["summary_file_id"] = summary_result.get("file_id")
                logger.info(f"✅ Summary uploaded: {summary_result.get('file_id')}")
            
            if update_data and cert_id:
                await db.certificates.update_one(
                    {"id": cert_id},
                    {"$set": update_data}
                )
        
        # Calculate total time
        timing['TOTAL'] = round(time.time() - total_start, 2)
        
        # Log timing analysis
        logger.info(f"⏱️ TIMING for {file.filename}:")
        for step, duration in timing.items():
            logger.info(f"   {step}: {duration}s")
        
        # Return success - UI can refresh immediately
        if validation_note and progress_message:
            return {
                "filename": file.filename,
                "status": "success_with_reference_note",
                "extracted_info": extracted_info,
                "summary_text": summary_text,
                "analysis": extracted_info,
                "certificate": cert_result,
                "is_marine": True,
                "progress_message": progress_message,
                "validation_note": validation_note,
                "timing": timing
            }
        else:
            return {
                "filename": file.filename,
                "status": "success",
                "extracted_info": extracted_info,
                "summary_text": summary_text,
                "analysis": extracted_info,
                "certificate": cert_result,
                "is_marine": True,
                "timing": timing
            }
    
    @staticmethod
    async def _upload_files_to_gdrive_background(
        cert_id: str,
        file_content: bytes,
        filename: str,
        summary_text: str,
        ship_name: str,
        gdrive_config_doc: Dict[str, Any]
    ):
        """
        Background task to upload PDF and Summary to GDrive in parallel
        Updates certificate record with file URLs when complete
        """
        import asyncio
        
        try:
            logger.info(f"🔄 Background upload starting for cert {cert_id}: {filename}")
            
            upload_tasks = []
            
            # Task 1: Upload main PDF
            upload_tasks.append(
                CertificateMultiUploadService._upload_to_gdrive_with_parent(
                    gdrive_config_doc, file_content, filename, ship_name,
                    "Class & Flag Cert", "Certificates"
                )
            )
            
            # Task 2: Upload Summary (if available)
            if summary_text and summary_text.strip():
                base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                summary_filename = f"{base_name}_Summary.txt"
                summary_bytes = summary_text.encode('utf-8')
                
                upload_tasks.append(
                    CertificateMultiUploadService._upload_to_gdrive_with_parent(
                        gdrive_config_doc, summary_bytes, summary_filename, ship_name,
                        "Class & Flag Cert", "Certificates", content_type="text/plain"
                    )
                )
            
            # Execute uploads in parallel
            upload_results = await asyncio.gather(*upload_tasks, return_exceptions=True)
            
            # Process results
            pdf_result = upload_results[0] if len(upload_results) > 0 else None
            summary_result = upload_results[1] if len(upload_results) > 1 else None
            
            # Update certificate record with file URLs
            db = mongo_db.database
            update_data = {"file_pending_upload": False}
            
            if pdf_result and not isinstance(pdf_result, Exception) and pdf_result.get("success"):
                update_data["google_drive_file_id"] = pdf_result.get("file_id")
                update_data["google_drive_file_url"] = pdf_result.get("file_url")
                update_data["file_uploaded"] = True
                logger.info(f"✅ Background: PDF uploaded for cert {cert_id}")
            else:
                logger.error(f"❌ Background: PDF upload failed for cert {cert_id}")
                update_data["file_upload_error"] = str(pdf_result) if isinstance(pdf_result, Exception) else "Upload failed"
            
            if summary_result and not isinstance(summary_result, Exception) and summary_result.get("success"):
                update_data["summary_file_id"] = summary_result.get("file_id")
                logger.info(f"✅ Background: Summary uploaded for cert {cert_id}")
            
            await db.certificates.update_one(
                {"id": cert_id},
                {"$set": update_data}
            )
            
            logger.info(f"✅ Background upload completed for cert {cert_id}")
            
        except Exception as e:
            logger.error(f"❌ Background upload error for cert {cert_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Mark upload as failed
            try:
                db = mongo_db.database
                await db.certificates.update_one(
                    {"id": cert_id},
                    {"$set": {
                        "file_pending_upload": False,
                        "file_upload_error": str(e)
                    }}
                )
            except:
                pass
    
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
            
            # Compare last_endorse field
            if last_endorse:
                total += 1
                if existing.get('last_endorse', '').strip() == last_endorse:
                    matches += 1
            
            if total > 0:
                similarity = matches / total
            
            # Consider it a duplicate only if similarity = 100% (exact match)
            if similarity >= 1.0:
                duplicates.append({
                    'certificate': existing,
                    'similarity': similarity
                })
        
        return duplicates
    
    
    @staticmethod
    def _check_if_audit_certificate(cert_name: str) -> Optional[str]:
        """
        Check if certificate belongs to ISM/ISPS/MLC/CICA categories
        
        Returns:
            Category name (ISM/ISPS/MLC/CICA) if match found, None otherwise
        """
        if not cert_name:
            return None
        
        cert_name_upper = cert_name.upper().strip()
        
        # Check each category
        for category, keywords in AUDIT_CERTIFICATE_CATEGORIES.items():
            for keyword in keywords:
                if keyword.upper() in cert_name_upper:
                    logger.info(f"🚫 Detected {category} certificate: '{cert_name}' matches keyword '{keyword}'")
                    return category
        
        return None

    @staticmethod
    async def _upload_to_gdrive_with_parent(
        gdrive_config: Dict[str, Any],
        file_content: bytes,
        filename: str,
        ship_name: str,
        parent_category: str,  # e.g., "Class & Flag Cert"
        category: str,         # e.g., "Certificates"
        content_type: str = None  # ⭐ Optional MIME type
    ) -> Dict[str, Any]:
        """
        Upload file to Google Drive with parent_category structure
        This uses the same logic as Audit Certificate - auto-creates folders if needed
        
        Path: {ship_name}/{parent_category}/{category}/
        Example: "MV OCEAN/Class & Flag Cert/Certificates/"
        """
        try:
            # Import GDrive helper with parent_category support
            from app.utils.gdrive_helper import upload_file_with_parent_category
            
            result = await upload_file_with_parent_category(
                gdrive_config, 
                file_content, 
                filename, 
                ship_name, 
                parent_category,
                category,
                content_type
            )
            
            if result.get("success"):
                logger.info(f"✅ Uploaded {filename} to GDrive: {ship_name}/{parent_category}/{category}/")
                return result
            else:
                logger.warning(f"⚠️ GDrive upload failed for {filename}: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Google Drive upload failed"),
                    "folder_path": f"{ship_name}/{parent_category}/{category}"
                }
                
        except Exception as e:
            logger.error(f"❌ GDrive upload error: {e}")
            return {
                "success": False,
                "error": str(e),
                "folder_path": f"{ship_name}/{parent_category}/{category}"
            }
    
    @staticmethod
    async def _upload_to_gdrive(
        gdrive_config: Dict[str, Any],
        file_content: bytes,
        filename: str,
        ship_name: str,
        folder: str,
        content_type: str = None  # ⭐ NEW: Optional MIME type
    ) -> Dict[str, Any]:
        """
        Upload file to Google Drive (LEGACY METHOD - kept for backward compatibility)
        Consider using _upload_to_gdrive_with_parent() instead for auto-folder creation
        """
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
        summary_file_id: Optional[str] = None,
        extracted_ship_name: Optional[str] = None,
        file_pending_upload: bool = False  # ⭐ NEW: Flag for background upload
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
                "extracted_ship_name": extracted_ship_name or analysis_result.get("ship_name"),
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
                "file_uploaded": upload_result.get("success", False) if not file_pending_upload else False,
                "file_pending_upload": file_pending_upload,  # ⭐ NEW: Track pending upload
                "google_drive_file_id": upload_result.get("file_id"),
                "google_drive_file_url": upload_result.get("file_url"),
                "google_drive_folder_path": upload_result.get("folder_path"),
                "file_path": upload_result.get("file_path"),
                "summary_file_id": summary_file_id,
                "text_content": analysis_result.get("text_content"),  # For future re-analysis
                "created_by": current_user.email,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Remove None values but preserve important fields
            preserved_fields = ['extracted_ship_name', 'text_content', 'notes', 'file_pending_upload']
            cert_doc = {k: v for k, v in cert_doc.items() if v is not None or k in preserved_fields}
            
            # Insert into database
            await db.certificates.insert_one(cert_doc)
            
            # Log audit
            try:
                from app.services.certificate_service import CertificateService
                audit_service = CertificateService.get_audit_log_service()
                user_dict = {
                    'id': current_user.id,
                    'username': current_user.username,
                    'full_name': current_user.full_name,
                    'company': current_user.company
                }
                await audit_service.log_ship_certificate_create(
                    ship_name=ship_name,
                    cert_data=cert_doc,
                    user=user_dict
                )
                logger.info(f"✅ Audit log created for multi-uploaded certificate")
            except Exception as audit_error:
                logger.error(f"Failed to create audit log: {audit_error}")
            
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
