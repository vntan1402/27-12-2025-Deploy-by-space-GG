import logging
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Form
from datetime import datetime, timezone

from app.models.crew import CrewCreate, CrewUpdate, CrewResponse, BulkDeleteCrewRequest
from app.models.user import UserResponse, UserRole
from app.services.crew_service import CrewService
from app.core.security import get_current_user
from app.repositories.crew_repository import CrewRepository
import base64

logger = logging.getLogger(__name__)
router = APIRouter()

async def check_passport_duplicate(
    passport_number: str,
    company_id: str
) -> dict | None:
    """
    Check if passport already exists in the system
    
    Args:
        passport_number: Passport number to check
        company_id: Company UUID
        
    Returns:
        dict with duplicate info if found, None otherwise
    """
    if not passport_number or not passport_number.strip():
        return None
    
    passport_number = passport_number.strip().upper()
    
    existing_crew = await CrewRepository.find_by_passport(
        passport_number,
        company_id
    )
    
    if existing_crew:
        logger.warning(f"❌ Duplicate passport found: {passport_number}")
        return {
            "duplicate": True,
            "error": "DUPLICATE_PASSPORT",
            "message": f"Passport {passport_number} already exists for crew member {existing_crew.get('full_name', 'Unknown')}",
            "existing_crew": {
                "id": existing_crew.get('id'),
                "full_name": existing_crew.get('full_name', 'Unknown'),
                "passport": existing_crew.get('passport'),
                "ship_sign_on": existing_crew.get('ship_sign_on', 'Unknown'),
                "status": existing_crew.get('status', 'Unknown')
            }
        }
    
    logger.info(f"✅ No duplicate found for passport: {passport_number}")
    return None

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[CrewResponse])
async def get_crew(current_user: UserResponse = Depends(get_current_user)):
    """
    Get all crew members (filtered by company for non-admin users)
    """
    try:
        return await CrewService.get_all_crew(current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching crew: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch crew")

@router.get("/{crew_id}", response_model=CrewResponse)
async def get_crew_by_id(
    crew_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get a specific crew member by ID
    """
    try:
        return await CrewService.get_crew_by_id(crew_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching crew {crew_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch crew member")

@router.post("", response_model=CrewResponse)
async def create_crew(
    crew_data: CrewCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Create new crew member (Editor+ role required)
    """
    try:
        return await CrewService.create_crew(crew_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating crew: {e}")
        raise HTTPException(status_code=500, detail="Failed to create crew member")

@router.put("/{crew_id}", response_model=CrewResponse)
async def update_crew(
    crew_id: str,
    crew_data: CrewUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Update crew member (Editor+ role required)
    """
    try:
        return await CrewService.update_crew(crew_id, crew_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating crew: {e}")
        raise HTTPException(status_code=500, detail="Failed to update crew member")

@router.delete("/{crew_id}")
async def delete_crew(
    crew_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Delete crew member (Editor+ role required)
    """
    try:
        return await CrewService.delete_crew(crew_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting crew: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete crew member")


@router.post("/{crew_id}/upload-passport-files")
async def upload_passport_files(
    crew_id: str,
    file_data: Dict = Body(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload passport files to Google Drive AFTER successful crew creation
    
    This endpoint is called by the frontend after:
    1. User uploads passport file
    2. AI analysis completes
    3. User reviews and creates crew member
    
    Request Body Structure:
    {
        "file_content": "base64_encoded_file_content",
        "filename": "passport.pdf",
        "content_type": "application/pdf",
        "summary_text": "OCR extracted text from passport",
        "ship_name": "BROTHER 36"
    }
    
    Returns:
    {
        "success": true,
        "message": "Files uploaded successfully",
        "passport_file_id": "gdrive-file-id-xxx",
        "summary_file_id": "gdrive-file-id-yyy"
    }
    """
    try:
        logger.info(f"📤 Upload passport files request for crew: {crew_id}")
        
        # 1. Verify crew exists and user has access
        crew = await CrewService.get_crew_by_id(crew_id, current_user)
        if not crew:
            raise HTTPException(
                status_code=404,
                detail=f"Crew member {crew_id} not found"
            )
        
        # 2. Validate required fields in request
        required_fields = ['file_content', 'filename', 'ship_name']
        missing_fields = [f for f in required_fields if f not in file_data]
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # 3. Decode and validate file content
        try:
            file_content = base64.b64decode(file_data['file_content'])
            logger.info(f"✅ Decoded file content: {len(file_content)} bytes")
        except Exception as e:
            logger.error(f"❌ Failed to decode base64: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid base64 file content: {str(e)}"
            )
        
        # Validate file size (max 10MB)
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > 10:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {file_size_mb:.2f}MB (max 10MB)"
            )
        
        # 4. Prepare upload data
        upload_data = {
            'file_content': file_content,
            'filename': file_data['filename'],
            'content_type': file_data.get('content_type', 'application/octet-stream'),
            'summary_text': file_data.get('summary_text', ''),
            'ship_name': file_data['ship_name'],
            'crew_id': crew_id,
            'crew_name': crew.full_name,
            'passport_number': crew.passport
        }
        
        # 5. Upload files to Google Drive
        from app.services.google_drive_service import GoogleDriveService
        
        drive_service = GoogleDriveService()
        upload_result = await drive_service.upload_passport_files(
            company_id=current_user.company,
            upload_data=upload_data
        )
        
        if not upload_result.get('success'):
            logger.error(f"❌ Google Drive upload failed: {upload_result.get('message')}")
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {upload_result.get('message', 'Unknown error')}"
            )
        
        # 6. Extract file IDs
        passport_file_id = upload_result.get('passport_file_id')
        summary_file_id = upload_result.get('summary_file_id')
        
        # 7. Update crew record with file IDs
        update_data = {
            'updated_at': datetime.now(timezone.utc),
            'updated_by': current_user.username
        }
        
        if passport_file_id:
            update_data['passport_file_id'] = passport_file_id
        if summary_file_id:
            update_data['summary_file_id'] = summary_file_id
        
        await CrewRepository.update(crew_id, update_data)
        
        logger.info(f"✅ Passport files uploaded for crew {crew_id}")
        logger.info(f"   📎 Passport File ID: {passport_file_id}")
        logger.info(f"   📋 Summary File ID: {summary_file_id}")
        
        return {
            "success": True,
            "message": "Passport files uploaded successfully",
            "passport_file_id": passport_file_id,
            "summary_file_id": summary_file_id,
            "crew_id": crew_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading passport files: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload passport files: {str(e)}"
        )

@router.post("/bulk-delete")
async def bulk_delete_crew(
    request: BulkDeleteCrewRequest,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Bulk delete crew members (Editor+ role required)
    """
    try:
        return await CrewService.bulk_delete_crew(request, current_user)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting crew: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete crew members")

@router.post("/move-standby-files")
async def move_standby_files(
    crew_id: str,
    from_ship_id: Optional[str] = None,
    to_ship_id: Optional[str] = None,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Move crew files between ships or to/from standby (Editor+ role required)
    """
    try:
        import os
        import shutil
        from pathlib import Path
        
        # Verify crew exists
        crew = await CrewService.get_crew_by_id(crew_id, current_user)
        if not crew:
            raise HTTPException(status_code=404, detail="Crew member not found")
        
        # Determine source and destination paths
        if from_ship_id:
            source_dir = Path(f"/app/uploads/ships/{from_ship_id}/crew/{crew_id}")
        else:
            source_dir = Path(f"/app/uploads/standby-crew/{crew_id}")
        
        if to_ship_id:
            dest_dir = Path(f"/app/uploads/ships/{to_ship_id}/crew/{crew_id}")
        else:
            dest_dir = Path(f"/app/uploads/standby-crew/{crew_id}")
        
        # Check if source exists
        if not source_dir.exists():
            logger.warning(f"Source directory does not exist: {source_dir}")
            return {
                "message": "No files to move",
                "moved_count": 0
            }
        
        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Move files
        moved_count = 0
        for file_path in source_dir.iterdir():
            if file_path.is_file():
                dest_file = dest_dir / file_path.name
                shutil.move(str(file_path), str(dest_file))
                moved_count += 1
        
        # Remove empty source directory
        if source_dir.exists() and not list(source_dir.iterdir()):
            source_dir.rmdir()
        
        logger.info(f"✅ Moved {moved_count} files for crew {crew_id}")
        
        return {
            "message": f"Successfully moved {moved_count} files",
            "moved_count": moved_count,
            "from_path": str(source_dir),
            "to_path": str(dest_dir)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error moving crew files: {e}")
        raise HTTPException(status_code=500, detail="Failed to move crew files")

@router.post("/analyze-passport")
async def analyze_passport_file(
    passport_file: UploadFile = File(...),
    ship_name: str = Form(None),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze passport file using AI (Editor+ role required)
    
    Args:
        passport_file: Passport file (PDF or image)
        ship_name: Ship name for the crew (optional, used for logging)
        current_user: Authenticated user
    """
    try:
        # Validate file type
        if not passport_file.content_type or not passport_file.content_type.startswith("image/"):
            if passport_file.content_type != "application/pdf":
                raise HTTPException(status_code=400, detail="Only image or PDF files are allowed")
        
        # Validate file size (10MB limit)
        if passport_file.size and passport_file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
        
        # Read file content
        file_content = await passport_file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file received")
        
        logger.info(f"📄 Analyzing passport file: {passport_file.filename} ({len(file_content)} bytes)")
        
        # ✅ USE GOOGLE DOCUMENT AI via Apps Script (same as V1)
        logger.info("🤖 Using Google Document AI for passport analysis...")
        
        # Get company information
        from app.db.mongodb import mongo_db
        
        company_id = current_user.company
        
        # Get AI configuration for Document AI (system-wide configuration)
        ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
        if not ai_config_doc:
            return {
                "success": False,
                "message": "AI configuration not found. Please configure Google Document AI in System Settings.",
                "analysis": None
            }
        
        document_ai_config = ai_config_doc.get("document_ai", {})
        
        if not document_ai_config.get("enabled", False):
            return {
                "success": False,
                "message": "Google Document AI is not enabled in System Settings",
                "analysis": None
            }
        
        # Validate required Document AI configuration
        if not all([
            document_ai_config.get("project_id"),
            document_ai_config.get("processor_id")
        ]):
            return {
                "success": False,
                "message": "Incomplete Google Document AI configuration. Please check Project ID and Processor ID.",
                "analysis": None
            }
        
        # Call Google Apps Script to analyze passport with Document AI
        from app.utils.google_drive_helper import GoogleDriveHelper
        import asyncio
        
        drive_helper = GoogleDriveHelper(company_id)
        
        # Load Google Drive configuration
        try:
            await drive_helper.load_config()
        except ValueError as e:
            logger.error(f"❌ Google Drive configuration error: {e}")
            return {
                "success": False,
                "message": f"Google Drive configuration error: {str(e)}. Please configure Google Apps Script URL in company settings.",
                "analysis": None
            }
        
        apps_script_payload = {
            "action": "analyze_passport_document_ai",
            "file_content": base64.b64encode(file_content).decode('utf-8'),
            "filename": passport_file.filename,
            "content_type": passport_file.content_type or 'application/octet-stream',
            "project_id": document_ai_config.get("project_id"),
            "location": document_ai_config.get("location", "us"),
            "processor_id": document_ai_config.get("processor_id")
        }
        
        logger.info(f"📞 Calling Google Apps Script for Document AI analysis...")
        
        # Make request with timeout
        try:
            analysis_response = await asyncio.wait_for(
                drive_helper.call_apps_script(apps_script_payload, timeout=90.0),
                timeout=90.0
            )
        except asyncio.TimeoutError:
            logger.error("❌ Document AI analysis timed out after 90 seconds")
            return {
                "success": False,
                "message": "Document AI analysis timed out. The file may be too large or complex.",
                "analysis": None
            }
        
        if not analysis_response.get("success"):
            logger.error(f"❌ Document AI failed: {analysis_response.get('message')}")
            return {
                "success": False,
                "message": f"Document AI analysis failed: {analysis_response.get('message', 'Unknown error')}",
                "analysis": None
            }
        
        # Get summary from Document AI
        document_summary = analysis_response.get("data", {}).get("summary", "")
        
        if not document_summary:
            logger.warning("Document AI returned empty summary")
            return {
                "success": False,
                "message": "Could not extract text from passport using Document AI",
                "analysis": None
            }
        
        logger.info(f"✅ Document AI extracted {len(document_summary)} characters")
        
        # Use System AI to extract passport fields from summary
        from app.utils.ai_helper import AIHelper
        from app.services.ai_config_service import AIConfigService
        
        try:
            ai_config = await AIConfigService.get_ai_config(current_user)
            provider = ai_config.provider
            model = ai_config.model
        except:
            provider = ai_config_doc.get("provider", "google")
            model = ai_config_doc.get("model", "gemini-2.0-flash")
        
        import os
        emergent_key = os.getenv("EMERGENT_LLM_KEY", "sk-emergent-eEe35Fb1b449940199")
        
        # Create AI prompt for passport field extraction from Document AI summary
        prompt = f"""
You are an AI assistant that extracts passport information from OCR text. Extract key information from the following Document AI summary.

Document AI Summary:
{document_summary}

Please extract and return ONLY a valid JSON object with the following fields:
{{
  "full_name": "Full name from passport",
  "passport_no": "Passport number",
  "nationality": "Nationality/Country",
  "date_of_birth": "Date of birth in DD/MM/YYYY format",
  "issue_date": "Issue date in DD/MM/YYYY format",
  "expiry_date": "Expiry date in DD/MM/YYYY format",
  "place_of_birth": "Place of birth or null",
  "sex": "M or F or null"
}}

IMPORTANT:
- Return ONLY the JSON object, no additional text
- Use DD/MM/YYYY format for all dates
- If a field is not found, use null
- Look for passport number patterns (alphanumeric, 6-12 characters)
- Extract the full name as written on the passport
"""
        
        logger.info(f"🤖 Extracting passport fields using {provider} {model}...")
        
        # Initialize LLM
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        llm_chat = LlmChat(
            api_key=emergent_key,
            session_id="passport_analysis",
            system_message="You are an AI assistant that extracts passport information from OCR text."
        )
        
        if provider == "google":
            llm_chat = llm_chat.with_model("gemini", model)
        else:
            llm_chat = llm_chat.with_model(provider, model)
        
        # Call AI
        ai_response = await llm_chat.send_message(UserMessage(text=prompt))
        
        # Parse response
        passport_data = AIHelper.parse_ai_response(ai_response)
        
        if not passport_data:
            return {
                "success": False,
                "message": "AI analysis failed - could not parse response",
                "analysis": None
            }
        
        logger.info("✅ Passport analyzed successfully")
        
        # ✅ NEW: Check for duplicate passport BEFORE returning
        passport_no = passport_data.get('passport_no', '').strip()
        if passport_no:
            duplicate_info = await check_passport_duplicate(
                passport_no,
                current_user.company
            )
            
            if duplicate_info:
                logger.warning(f"Duplicate detected during analysis: {passport_no}")
                return {
                    "success": False,
                    **duplicate_info
                }
        
        # ✅ NEW: Store file content for later upload
        passport_data['_file_content'] = base64.b64encode(file_content).decode('utf-8')
        passport_data['_filename'] = passport_file.filename
        passport_data['_content_type'] = passport_file.content_type or 'application/octet-stream'
        passport_data['_summary_text'] = document_summary  # Document AI summary text
        
        logger.info("✅ File content stored for later upload")
        
        return {
            "success": True,
            "message": "Passport analyzed successfully",
            "analysis": passport_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Passport analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze passport: {str(e)}")
