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

def parse_passport_response(response_text: str) -> dict:
    """
    Parse AI response for passport data extraction (V1 format)
    
    Maps from V1 format to V2 format:
    - Passport_Number → passport_no
    - Surname + Given_Names → full_name
    - Date_of_Birth → date_of_birth
    - etc.
    
    Args:
        response_text: Raw AI response text containing JSON (V1 format)
        
    Returns:
        Dict with passport fields (V2 format)
    """
    import re
    import json
    
    try:
        # Try to find JSON in the response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
        else:
            # If no JSON found, try to parse the whole response
            data = json.loads(response_text)
        
        # ✅ Map V1 format to V2 format
        surname = data.get("Surname", "")
        given_names = data.get("Given_Names", "")
        
        # Combine surname and given names for full_name
        full_name = f"{surname} {given_names}".strip() if (surname or given_names) else ""
        
        passport_data = {
            "full_name": full_name,
            "passport_no": data.get("Passport_Number", ""),
            "nationality": data.get("Nationality", ""),
            "date_of_birth": data.get("Date_of_Birth", ""),
            "issue_date": data.get("Date_of_Issue", ""),
            "expiry_date": data.get("Date_of_Expiry", ""),
            "place_of_birth": data.get("Place_of_Birth", ""),
            "sex": data.get("Sex", "")
        }
        
        logger.info(f"✅ Parsed passport data: {passport_data.get('full_name')} - {passport_data.get('passport_no')}")
        
        return passport_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from AI response: {e}")
        logger.error(f"Response text: {response_text[:500]}")
        return {}
    except Exception as e:
        logger.error(f"Error parsing passport response: {e}")
        return {}

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
    request_data: Dict = Body(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Update crew member (Editor+ role required)
    
    Supports conflict detection:
    - Send 'expected_last_modified_at' to detect concurrent edits
    - Returns 409 if crew was modified by another user
    """
    try:
        # Extract conflict detection parameter
        expected_last_modified_at = request_data.pop('expected_last_modified_at', None)
        
        # Parse crew data
        crew_data = CrewUpdate(**request_data)
        
        return await CrewService.update_crew(
            crew_id, 
            crew_data, 
            current_user,
            expected_last_modified_at=expected_last_modified_at
        )
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
        
        # 6. Extract file IDs and filename
        passport_file_id = upload_result.get('passport_file_id')
        passport_file_name = upload_result.get('passport_file_name')  # ⭐ NEW
        summary_file_id = upload_result.get('summary_file_id')
        
        # 7. Update crew record with file IDs and filename
        update_data = {
            'updated_at': datetime.now(timezone.utc),
            'updated_by': current_user.username
        }
        
        if passport_file_id:
            update_data['passport_file_id'] = passport_file_id
        if passport_file_name:  # ⭐ NEW
            update_data['passport_file_name'] = passport_file_name
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
        
        # ✅ Call Document AI using the same helper as Ship Certificate
        from app.utils.document_ai_helper import analyze_document_with_document_ai
        
        logger.info(f"🤖 Calling Document AI for passport analysis...")
        
        # Get Apps Script URL from document_ai_config
        apps_script_url = document_ai_config.get("apps_script_url")
        
        if not apps_script_url:
            logger.error("❌ Apps Script URL not configured in Document AI settings")
            return {
                "success": False,
                "message": "Apps Script URL not configured. Please configure Apps Script URL in Document AI settings (System AI).",
                "analysis": None
            }
        
        # Add apps_script_url to config for document_ai_helper
        document_ai_config_with_url = {
            **document_ai_config,
            "apps_script_url": apps_script_url
        }
        
        # Call Document AI
        doc_ai_result = await analyze_document_with_document_ai(
            file_content=file_content,
            filename=passport_file.filename,
            content_type=passport_file.content_type or 'application/pdf',
            document_ai_config=document_ai_config_with_url,
            document_type='other'  # Passport is general document type
        )
        
        if not doc_ai_result or not doc_ai_result.get("success"):
            error_msg = doc_ai_result.get("message", "Unknown error") if doc_ai_result else "No response from Document AI"
            logger.error(f"❌ Document AI failed: {error_msg}")
            return {
                "success": False,
                "message": f"Document AI analysis failed: {error_msg}",
                "analysis": None
            }
        
        # Get summary from Document AI (nested in "data" key)
        data = doc_ai_result.get("data", {})
        document_summary = data.get("summary", "")
        
        # Strip whitespace and check if meaningful content exists
        document_summary = document_summary.strip() if document_summary else ""
        
        logger.info(f"📄 Document AI summary length: {len(document_summary)} characters")
        
        if not document_summary or len(document_summary) < 20:
            logger.warning(f"⚠️ Document AI returned insufficient text: {len(document_summary)} characters")
            return {
                "success": False,
                "message": "Could not extract sufficient text from passport using Document AI",
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
        
        # Create AI prompt for passport field extraction from Document AI summary (V1 format)
        prompt = f"""You are an AI specialized in structured information extraction from maritime and identity documents.

Your task:
Analyze the following text summary of a passport and extract all key passport fields. 
The text already contains all relevant information about the document, so focus only on extracting and normalizing it into a structured JSON format.

=== CRITICAL INSTRUCTIONS FOR VIETNAMESE NAMES ===
**EXTREMELY IMPORTANT**: Vietnamese passports contain BOTH Vietnamese name (with diacritics) AND English name (without diacritics).
- Surname: Extract the VIETNAMESE surname WITH Vietnamese diacritics (ĐỖ, VŨ, NGUYỄN, etc.) - NOT the English version
- Given_Names: Extract the VIETNAMESE given names WITH Vietnamese diacritics (ÁNH BẢO, NGỌC TÂN, etc.) - NOT the English version
- DO NOT extract English transliteration (DO, VU, NGUYEN without diacritics)
- Vietnamese names are typically found in the main document content, NOT in the MRZ line
- MRZ line contains English transliteration - DO NOT use it for name extraction

=== INSTRUCTIONS ===
1. Extract only the passport-related fields listed below.
2. Return the output strictly in valid JSON format.
3. If a field is not found, leave it as an empty string "".
4. Normalize all dates to DD/MM/YYYY format.
5. Use uppercase for country codes and names.
6. Do not infer or fabricate any missing information.
7. Ensure names are written in correct Vietnamese format WITH DIACRITICS (Surname first, Given names after).

=== FIELDS TO EXTRACT ===
{{
  "Passport_Number": "",
  "Type": "",
  "Issuing_Country_Code": "",
  "Country_Name": "",
  "Surname": "",
  "Given_Names": "",
  "Sex": "",
  "Date_of_Birth": "",
  "Place_of_Birth": "",
  "Nationality": "",
  "Date_of_Issue": "",
  "Date_of_Expiry": "",
  "Place_of_Issue": "",
  "Authority": ""
}}

=== TEXT INPUT (Passport Summary) ===
{document_summary}

Return ONLY the JSON output with extracted fields. Do not include any explanations or additional text."""
        
        logger.info(f"🤖 Extracting passport fields using {provider} {model}...")
        
        # Initialize LLM
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        llm_chat = LlmChat(
            api_key=emergent_key,
            session_id="passport_analysis",
            system_message="You are an AI assistant that extracts passport information from OCR text."
        )
        
        # Map provider to correct format for emergentintegrations
        if provider in ["google", "emergent"]:
            # For Google/Emergent, use "gemini" as provider
            llm_chat = llm_chat.with_model("gemini", model)
        elif provider == "anthropic":
            llm_chat = llm_chat.with_model("claude", model)
        elif provider == "openai":
            llm_chat = llm_chat.with_model("openai", model)
        else:
            # Fallback to gemini
            logger.warning(f"Unknown provider {provider}, using gemini as fallback")
            llm_chat = llm_chat.with_model("gemini", model)
        
        # Call AI
        ai_response = await llm_chat.send_message(UserMessage(text=prompt))
        
        # Parse response - extract passport fields (NOT ship certificate fields)
        passport_data = parse_passport_response(ai_response)
        
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


# ============================================================================
# CREW ASSIGNMENT ENDPOINTS (Sign On, Sign Off, Transfer)
# ============================================================================

@router.post("/{crew_id}/sign-off")
async def sign_off_crew_member(
    crew_id: str,
    request_data: Dict = Body(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Sign off crew member and move files to Standby
    
    Request Body:
    {
        "sign_off_date": "2025-01-15" | "15/01/2025",  # ISO or DD/MM/YYYY
        "notes": "Contract ended",  # Optional
        "skip_validation": false  # Optional - Skip status validation if DB already updated
    }
    
    Response:
    {
        "success": true,
        "message": "Crew signed off successfully. X files moved to Standby.",
        "crew_id": "...",
        "crew_name": "...",
        "from_ship": "BROTHER 36",
        "sign_off_date": "2025-01-15",
        "files_moved": {
            "passport_moved": true,
            "certificates_moved": 3,
            "summaries_moved": 3
        },
        "assignment_id": "..."
    }
    """
    try:
        from app.services.crew_assignment_service import CrewAssignmentService
        from app.models.crew_assignment import SignOffRequest
        
        logger.info(f"🛑 Sign off request for crew: {crew_id}")
        
        # Validate request data
        try:
            sign_off_request = SignOffRequest(**request_data)
        except Exception as e:
            logger.error(f"❌ Invalid request data: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request data: {str(e)}"
            )
        
        # Call service
        skip_validation = request_data.get('skip_validation', False)
        result = await CrewAssignmentService.sign_off_crew(
            crew_id=crew_id,
            sign_off_date=sign_off_request.sign_off_date,
            notes=sign_off_request.notes,
            current_user=current_user,
            skip_validation=skip_validation,
            place_sign_off=sign_off_request.place_sign_off,
            from_ship=sign_off_request.from_ship
        )
        
        logger.info(f"✅ Sign off completed: {result.get('crew_name')}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Sign off endpoint error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Sign off failed: {str(e)}"
        )


@router.post("/{crew_id}/sign-on")
async def sign_on_crew_member(
    crew_id: str,
    request_data: Dict = Body(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Sign on crew member to a ship and move files from Standby
    
    Request Body:
    {
        "ship_name": "BROTHER 36",  # Required
        "sign_on_date": "2025-01-20" | "20/01/2025",  # ISO or DD/MM/YYYY
        "place_sign_on": "Singapore",  # Optional
        "notes": "New contract",  # Optional
        "skip_validation": false  # Optional - Skip status validation if DB already updated
    }
    
    Response:
    {
        "success": true,
        "message": "Crew signed on to BROTHER 36 successfully. X files moved.",
        "crew_id": "...",
        "crew_name": "...",
        "to_ship": "BROTHER 36",
        "sign_on_date": "2025-01-20",
        "place_sign_on": "Singapore",
        "files_moved": {...},
        "assignment_id": "..."
    }
    """
    try:
        from app.services.crew_assignment_service import CrewAssignmentService
        from app.models.crew_assignment import SignOnRequest
        
        logger.info(f"✅ Sign on request for crew: {crew_id}")
        
        # Validate request data
        try:
            sign_on_request = SignOnRequest(**request_data)
        except Exception as e:
            logger.error(f"❌ Invalid request data: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request data: {str(e)}"
            )
        
        # Call service
        skip_validation = request_data.get('skip_validation', False)
        result = await CrewAssignmentService.sign_on_crew(
            crew_id=crew_id,
            ship_name=sign_on_request.ship_name,
            sign_on_date=sign_on_request.sign_on_date,
            place_sign_on=sign_on_request.place_sign_on,
            notes=sign_on_request.notes,
            current_user=current_user,
            skip_validation=skip_validation
        )
        
        logger.info(f"✅ Sign on completed: {result.get('crew_name')} to {result.get('to_ship')}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Sign on endpoint error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Sign on failed: {str(e)}"
        )


@router.post("/{crew_id}/transfer-ship")
async def transfer_crew_to_ship(
    crew_id: str,
    request_data: Dict = Body(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Transfer crew from current ship to another ship
    
    Request Body:
    {
        "to_ship_name": "BROTHER 37",  # Required
        "transfer_date": "2025-01-25" | "25/01/2025",  # ISO or DD/MM/YYYY
        "notes": "Temporary transfer",  # Optional
        "skip_validation": false  # Optional - Skip status validation if DB already updated
    }
    
    Response:
    {
        "success": true,
        "message": "Crew transferred from BROTHER 36 to BROTHER 37 successfully. X files moved.",
        "crew_id": "...",
        "crew_name": "...",
        "from_ship": "BROTHER 36",
        "to_ship": "BROTHER 37",
        "transfer_date": "2025-01-25",
        "files_moved": {...},
        "assignment_id": "..."
    }
    """
    try:
        from app.services.crew_assignment_service import CrewAssignmentService
        from app.models.crew_assignment import TransferRequest
        
        logger.info(f"🔄 Transfer request for crew: {crew_id}")
        
        # Validate request data
        try:
            transfer_request = TransferRequest(**request_data)
        except Exception as e:
            logger.error(f"❌ Invalid request data: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request data: {str(e)}"
            )
        
        # Call service
        skip_validation = request_data.get('skip_validation', False)
        result = await CrewAssignmentService.transfer_crew_between_ships(
            crew_id=crew_id,
            to_ship_name=transfer_request.to_ship_name,
            transfer_date=transfer_request.transfer_date,
            notes=transfer_request.notes,
            current_user=current_user,
            skip_validation=skip_validation
        )
        
        logger.info(f"✅ Transfer completed: {result.get('crew_name')} from {result.get('from_ship')} to {result.get('to_ship')}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Transfer endpoint error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Transfer failed: {str(e)}"
        )



@router.post("/{crew_id}/auto-rename-passport")
async def auto_rename_crew_passport(
    crew_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Auto rename crew passport and summary files on Google Drive using naming convention:
    {Rank}_{Full Name (Eng)}_Passport.pdf
    
    Example: Master_NGUYEN VAN A_Passport.pdf
    
    Summary file: {Rank}_{Full Name (Eng)}_Passport_Summary.txt
    
    Response:
    {
        "success": true,
        "message": "Passport files renamed successfully",
        "crew_id": "...",
        "crew_name": "...",
        "new_filename": "Master_NGUYEN VAN A_ABC123456.pdf",
        "renamed_files": ["passport", "summary"]
    }
    """
    try:
        from app.services.crew_passport_rename_service import CrewPassportRenameService
        
        logger.info(f"🔄 Auto-rename passport request for crew: {crew_id}")
        
        # Call service
        result = await CrewPassportRenameService.auto_rename_passport_files(
            crew_id=crew_id,
            current_user=current_user
        )
        
        logger.info(f"✅ Auto-rename completed: {result.get('new_filename')}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Auto-rename passport endpoint error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to auto-rename passport files: {str(e)}"
        )


@router.get("/{crew_id}/assignment-history")
async def get_crew_assignment_history(
    crew_id: str,
    limit: int = 50,
    skip: int = 0,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get assignment history for a crew member
    
    Query Parameters:
    - limit: Max records to return (default: 50)
    - skip: Number of records to skip (default: 0)
    
    Response:
    {
        "success": true,
        "crew_id": "...",
        "total_count": 10,
        "history": [
            {
                "id": "...",
                "action_type": "SIGN_OFF",
                "from_ship": "BROTHER 36",
                "to_ship": null,
                "from_status": "Sign on",
                "to_status": "Standby",
                "action_date": "2025-01-15T10:00:00Z",
                "performed_by": "admin1",
                "notes": "Contract ended",
                "files_moved": {...},
                "created_at": "2025-01-15T10:00:00Z"
            },
            ...
        ]
    }
    """
    try:
        from app.repositories.crew_assignment_repository import CrewAssignmentRepository
        
        logger.info(f"📋 Getting assignment history for crew: {crew_id}")
        
        # Verify crew exists
        crew = await CrewRepository.find_by_id(crew_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Crew member not found")
        
        # Check access permission
        if current_user.role not in ["SYSTEM_ADMIN", "SUPER_ADMIN"]:
            if crew.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Get assignment history
        history = await CrewAssignmentRepository.find_by_crew_id(
            crew_id=crew_id,
            limit=limit,
            skip=skip
        )
        
        # Get total count
        total_count = await CrewAssignmentRepository.count_by_crew(crew_id)
        
        logger.info(f"✅ Found {len(history)} assignment records (total: {total_count})")
        
        return {
            "success": True,
            "crew_id": crew_id,
            "crew_name": crew.get('full_name', 'Unknown'),
            "total_count": total_count,
            "returned_count": len(history),
            "limit": limit,
            "skip": skip,
            "history": history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get assignment history error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get assignment history: {str(e)}"
        )


@router.delete("/{crew_id}/assignment-history")
async def clear_crew_assignment_history(
    crew_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Clear all assignment history for a crew member
    
    WARNING: This permanently deletes all assignment records for the crew member.
    This action cannot be undone.
    
    Response:
    {
        "success": true,
        "message": "Cleared N assignment records for crew member X",
        "crew_id": "...",
        "crew_name": "...",
        "records_deleted": 5
    }
    """
    try:
        from app.repositories.crew_assignment_repository import CrewAssignmentRepository
        
        logger.info(f"🗑️ Clearing assignment history for crew: {crew_id}")
        
        # Verify crew exists
        crew = await CrewRepository.find_by_id(crew_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Crew member not found")
        
        # Check access permission
        if current_user.role not in ["SYSTEM_ADMIN", "SUPER_ADMIN", "ADMIN"]:
            if crew.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        crew_name = crew.get('full_name', 'Unknown')
        
        # Count records before deletion
        count_before = await CrewAssignmentRepository.count_by_crew(crew_id)
        logger.info(f"   Found {count_before} records to delete")
        
        if count_before == 0:
            return {
                "success": True,
                "message": f"No assignment history to delete for {crew_name}",
                "crew_id": crew_id,
                "crew_name": crew_name,
                "records_deleted": 0
            }
        
        # Delete all assignment records for this crew
        from app.db.mongodb import mongo_db
        result = await mongo_db.database.crew_assignment_history.delete_many({
            "crew_id": crew_id
        })
        
        deleted_count = result.deleted_count
        logger.info(f"✅ Deleted {deleted_count} assignment records")
        
        return {
            "success": True,
            "message": f"Cleared {deleted_count} assignment records for {crew_name}",
            "crew_id": crew_id,
            "crew_name": crew_name,
            "records_deleted": deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Clear assignment history error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear assignment history: {str(e)}"
        )


@router.put("/{crew_id}/update-assignment-dates")
async def update_crew_assignment_dates(
    crew_id: str,
    request_data: Dict = Body(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Update assignment history dates when user edits date_sign_on or date_sign_off
    
    This endpoint updates the action_date in the corresponding assignment history record
    to match the new date entered by the user in Edit Crew Modal.
    
    Request Body:
    {
        "date_sign_on": "2024-12-20",  # Optional - if changed, update latest SIGN_ON/SHIP_TRANSFER
        "date_sign_off": "2024-11-15"  # Optional - if changed, update latest SIGN_OFF
    }
    
    Response:
    {
        "success": true,
        "message": "Assignment dates updated successfully",
        "updated": {
            "sign_on": true,
            "sign_off": false
        }
    }
    """
    try:
        from app.repositories.crew_assignment_repository import CrewAssignmentRepository
        
        logger.info(f"📅 Update assignment dates request for crew: {crew_id}")
        
        # Verify crew exists
        crew = await CrewRepository.find_by_id(crew_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Crew member not found")
        
        # Check access permission
        if current_user.role not in ["SYSTEM_ADMIN", "SUPER_ADMIN", "ADMIN"]:
            if crew.get('company_id') != current_user.company:
                raise HTTPException(status_code=403, detail="Access denied")
        
        updated = {
            "sign_on": False,
            "sign_off": False
        }
        
        # Update sign on date if provided
        if "date_sign_on" in request_data and request_data["date_sign_on"]:
            new_date_sign_on = request_data["date_sign_on"]
            
            # Try to parse the date
            try:
                if isinstance(new_date_sign_on, str):
                    # Parse date
                    from app.utils.date_helpers import parse_date_flexible
                    parsed_date = parse_date_flexible(new_date_sign_on)
                else:
                    parsed_date = new_date_sign_on
                
                # Find and update the latest SIGN_ON or SHIP_TRANSFER record
                # Try SHIP_TRANSFER first (most recent if crew was transferred)
                success = await CrewAssignmentRepository.update_latest_by_crew_and_type(
                    crew_id=crew_id,
                    action_type="SHIP_TRANSFER",
                    update_data={"action_date": parsed_date}
                )
                
                if not success:
                    # If no SHIP_TRANSFER found, try SIGN_ON
                    success = await CrewAssignmentRepository.update_latest_by_crew_and_type(
                        crew_id=crew_id,
                        action_type="SIGN_ON",
                        update_data={"action_date": parsed_date}
                    )
                
                updated["sign_on"] = success
                
            except Exception as e:
                logger.error(f"❌ Error parsing or updating sign on date: {e}")
        
        # Update sign off date if provided
        if "date_sign_off" in request_data and request_data["date_sign_off"]:
            new_date_sign_off = request_data["date_sign_off"]
            
            try:
                if isinstance(new_date_sign_off, str):
                    from app.utils.date_helpers import parse_date_flexible
                    parsed_date = parse_date_flexible(new_date_sign_off)
                else:
                    parsed_date = new_date_sign_off
                
                # Update the latest SIGN_OFF record
                success = await CrewAssignmentRepository.update_latest_by_crew_and_type(
                    crew_id=crew_id,
                    action_type="SIGN_OFF",
                    update_data={"action_date": parsed_date}
                )
                
                updated["sign_off"] = success
                
            except Exception as e:
                logger.error(f"❌ Error parsing or updating sign off date: {e}")
        
        if updated["sign_on"] or updated["sign_off"]:
            logger.info(f"✅ Assignment dates updated for crew {crew_id}: {updated}")
            return {
                "success": True,
                "message": "Assignment dates updated successfully",
                "updated": updated
            }
        else:
            return {
                "success": False,
                "message": "No assignment history records found to update",
                "updated": updated
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update assignment dates error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update assignment dates: {str(e)}"
        )


