# 🚀 V1 TO V2 MIGRATION PLAN - ADD CREW FEATURES

## 📋 EXECUTIVE SUMMARY

**Objective:** Port critical missing features from V1 to V2 while maintaining V2's clean architecture

**Total Estimated Effort:** 24 hours (3 working days)

**Success Criteria:**
- ✅ V2 has feature parity with V1
- ✅ All tests pass
- ✅ Architecture remains clean and modular
- ✅ No breaking changes to existing endpoints

---

## 🎯 MIGRATION STRATEGY

### Core Principles:
1. **Keep V2 Architecture** - Maintain separation of concerns
2. **Incremental Migration** - Port features one by one
3. **Test-Driven** - Write tests before implementation
4. **Backward Compatible** - Don't break existing functionality

### Architecture Layers:
```
API Layer (crew.py)
    ↓
Service Layer (crew_service.py)
    ↓
Repository Layer (crew_repository.py)
    ↓
Database (MongoDB)
```

---

## 📅 MIGRATION PHASES

### PHASE 1: CRITICAL FEATURES (Day 1)
**Duration:** 8 hours
**Goal:** Fix breaking issues that affect core functionality

Tasks:
1. ✅ Add duplicate check to analysis endpoint (2h)
2. ✅ Implement comprehensive date parsing (2h)
3. ✅ Create file upload endpoint structure (4h)

---

### PHASE 2: GOOGLE DRIVE INTEGRATION (Day 2)
**Duration:** 10 hours
**Goal:** Enable file storage and management

Tasks:
4. ✅ Create Google Drive service module (4h)
5. ✅ Implement file upload to Drive (3h)
6. ✅ Implement summary file generation (3h)

---

### PHASE 3: ADDITIONAL FEATURES (Day 3)
**Duration:** 6 hours
**Goal:** Complete feature parity and improve robustness

Tasks:
7. ✅ Add audit trail system (3h)
8. ✅ Improve error handling (1h)
9. ✅ End-to-end testing (2h)

---

## 📝 DETAILED TASK BREAKDOWN

---

## 🔴 PHASE 1: CRITICAL FEATURES

### TASK 1.1: Add Duplicate Check to Analysis Endpoint

**Duration:** 2 hours
**Priority:** CRITICAL
**Files to Modify:**
- `/app/backend/app/api/v1/crew.py`

**Objective:**
Check if passport already exists BEFORE AI analysis completes, to save user time and AI credits.

**Implementation Steps:**

#### Step 1: Add helper function in crew.py

```python
# Add after imports in /app/backend/app/api/v1/crew.py

from app.repositories.crew_repository import CrewRepository

async def check_passport_duplicate(
    passport_number: str,
    company_id: str
) -> dict | None:
    """
    Check if passport already exists in the system
    
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
```

#### Step 2: Modify analyze_passport_file() endpoint

```python
# In analyze_passport_file() function, after AI analysis success
# Add this BEFORE returning the result (around line 295)

# Check for duplicate passport
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

# Store file content for later upload (IMPORTANT)
passport_data['_file_content'] = base64.b64encode(file_content).decode('utf-8')
passport_data['_filename'] = file.filename
passport_data['_content_type'] = file.content_type or 'application/octet-stream'
passport_data['_summary_text'] = text  # OCR extracted text
```

#### Step 3: Update frontend handler

Frontend already handles duplicate response, but verify:
```javascript
// In AddCrewModal.jsx
if (data.duplicate) {
  toast.error(`Passport ${data.existing_crew.passport} already exists for ${data.existing_crew.full_name}`);
  handleRemoveFile();
  return;
}
```

**Testing Checklist:**
- [ ] Upload passport that doesn't exist → Success
- [ ] Upload duplicate passport → Error with crew details
- [ ] Error message shows existing crew name and ship
- [ ] File is removed from upload area
- [ ] User can upload different file immediately
- [ ] Backend logs show duplicate check

**Acceptance Criteria:**
- Duplicate detection happens before crew creation
- User gets immediate feedback (< 2 seconds)
- No wasted AI credits for duplicates
- Error message is clear and actionable

---

### TASK 1.2: Implement Comprehensive Date Parsing

**Duration:** 2 hours
**Priority:** CRITICAL
**Files to Create/Modify:**
- Create: `/app/backend/app/utils/date_helpers.py`
- Modify: `/app/backend/app/services/crew_service.py`

**Objective:**
Support multiple date formats from AI and manual entry to prevent parsing errors.

**Implementation Steps:**

#### Step 1: Create date helper utility

```python
# Create new file: /app/backend/app/utils/date_helpers.py

"""
Date parsing utilities with comprehensive format support
"""

from datetime import datetime, timezone
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

def parse_date_flexible(date_value: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Parse date from various formats with comprehensive error handling
    
    Supported formats:
    - YYYY-MM-DD (HTML date input): "2023-01-15"
    - DD/MM/YYYY (European/AI format): "15/01/2023"
    - MM/DD/YYYY (US format): "01/15/2023"
    - ISO 8601 with time: "2023-01-15T10:30:00Z"
    - ISO 8601 without Z: "2023-01-15T10:30:00"
    
    Args:
        date_value: Date in various formats
        
    Returns:
        datetime object with UTC timezone or None if parsing fails
        
    Examples:
        >>> parse_date_flexible("2023-01-15")
        datetime(2023, 1, 15, 0, 0, tzinfo=timezone.utc)
        
        >>> parse_date_flexible("15/01/2023")
        datetime(2023, 1, 15, 0, 0, tzinfo=timezone.utc)
        
        >>> parse_date_flexible("2023-01-15T10:30:00Z")
        datetime(2023, 1, 15, 10, 30, tzinfo=timezone.utc)
    """
    if not date_value:
        return None
    
    # Already a datetime object
    if isinstance(date_value, datetime):
        if date_value.tzinfo is None:
            return date_value.replace(tzinfo=timezone.utc)
        return date_value
    
    # Not a string - cannot parse
    if not isinstance(date_value, str):
        logger.warning(f"⚠️ Invalid date type: {type(date_value)}")
        return None
    
    date_str = date_value.strip()
    
    if not date_str:
        return None
    
    try:
        # ISO format with time and timezone
        if 'T' in date_str:
            logger.debug(f"Parsing ISO format: {date_str}")
            
            if date_str.endswith('Z'):
                # Replace Z with +00:00 for proper parsing
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                parsed = datetime.fromisoformat(date_str)
                # Ensure UTC timezone
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed
        
        # Date with slashes (DD/MM/YYYY or MM/DD/YYYY)
        if '/' in date_str:
            logger.debug(f"Parsing slash format: {date_str}")
            
            parts = date_str.split('/')
            if len(parts) != 3:
                raise ValueError(f"Invalid date format: {date_str}")
            
            # Try DD/MM/YYYY first (more common internationally)
            try:
                parsed = datetime.strptime(date_str, '%d/%m/%Y')
                logger.debug(f"✅ Parsed as DD/MM/YYYY: {parsed}")
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                # Fallback to MM/DD/YYYY (US format)
                try:
                    parsed = datetime.strptime(date_str, '%m/%d/%Y')
                    logger.debug(f"✅ Parsed as MM/DD/YYYY: {parsed}")
                    return parsed.replace(tzinfo=timezone.utc)
                except ValueError:
                    raise ValueError(f"Could not parse date with slashes: {date_str}")
        
        # Standard YYYY-MM-DD format (HTML date input)
        logger.debug(f"Parsing YYYY-MM-DD format: {date_str}")
        parsed = datetime.strptime(date_str, '%Y-%m-%d')
        logger.debug(f"✅ Parsed as YYYY-MM-DD: {parsed}")
        return parsed.replace(tzinfo=timezone.utc)
        
    except (ValueError, TypeError) as e:
        logger.error(f"❌ Failed to parse date '{date_str}': {e}")
        return None


def convert_dates_in_dict(data: dict, date_fields: list) -> dict:
    """
    Convert all date fields in a dictionary to datetime objects
    
    Args:
        data: Dictionary containing date fields
        date_fields: List of field names that contain dates
        
    Returns:
        Modified dictionary with converted dates
    """
    for field in date_fields:
        if field in data and data[field]:
            parsed_date = parse_date_flexible(data[field])
            if parsed_date is None and data[field]:
                logger.warning(f"⚠️ Could not parse {field}: '{data[field]}' - setting to None")
            data[field] = parsed_date
    
    return data


# Common date field names
CREW_DATE_FIELDS = [
    'date_of_birth',
    'date_sign_on',
    'date_sign_off',
    'passport_issue_date',
    'passport_expiry_date'
]
```

#### Step 2: Update crew_service.py to use date helper

```python
# Modify /app/backend/app/services/crew_service.py
# Add import at top:

from app.utils.date_helpers import convert_dates_in_dict, CREW_DATE_FIELDS

# Modify create_crew method, after crew_dict creation:

@staticmethod
async def create_crew(crew_data: CrewCreate, current_user: UserResponse):
    """Create new crew member with comprehensive date handling"""
    
    # ... existing duplicate check code ...
    
    # Create crew document
    crew_dict = crew_data.dict()
    crew_dict["id"] = str(uuid.uuid4())
    crew_dict["created_at"] = datetime.now(timezone.utc)
    crew_dict["created_by"] = current_user.username
    
    # ✅ NEW: Convert all date fields to datetime objects
    crew_dict = convert_dates_in_dict(crew_dict, CREW_DATE_FIELDS)
    
    # Log date conversions for debugging
    for field in CREW_DATE_FIELDS:
        if field in crew_dict and crew_dict[field]:
            logger.info(f"✅ {field}: {crew_dict[field]}")
    
    # Save to database
    await CrewRepository.create(crew_dict)
    
    logger.info(f"✅ Crew member created: {crew_dict['full_name']}")
    
    return CrewResponse(**crew_dict)
```

#### Step 3: Create unit tests

```python
# Create new file: /app/backend/tests/test_date_helpers.py

import pytest
from datetime import datetime, timezone
from app.utils.date_helpers import parse_date_flexible, convert_dates_in_dict

def test_parse_yyyy_mm_dd():
    """Test YYYY-MM-DD format (HTML date input)"""
    result = parse_date_flexible("2023-01-15")
    assert result == datetime(2023, 1, 15, 0, 0, tzinfo=timezone.utc)

def test_parse_dd_mm_yyyy():
    """Test DD/MM/YYYY format (European/AI)"""
    result = parse_date_flexible("15/01/2023")
    assert result == datetime(2023, 1, 15, 0, 0, tzinfo=timezone.utc)

def test_parse_mm_dd_yyyy():
    """Test MM/DD/YYYY format (US)"""
    result = parse_date_flexible("01/15/2023")
    assert result == datetime(2023, 1, 15, 0, 0, tzinfo=timezone.utc)

def test_parse_iso_with_z():
    """Test ISO 8601 with Z"""
    result = parse_date_flexible("2023-01-15T10:30:00Z")
    assert result.year == 2023
    assert result.month == 1
    assert result.day == 15

def test_parse_iso_without_z():
    """Test ISO 8601 without Z"""
    result = parse_date_flexible("2023-01-15T10:30:00")
    assert result.tzinfo == timezone.utc

def test_parse_empty_string():
    """Test empty string returns None"""
    result = parse_date_flexible("")
    assert result is None

def test_parse_none():
    """Test None returns None"""
    result = parse_date_flexible(None)
    assert result is None

def test_parse_invalid_format():
    """Test invalid format returns None"""
    result = parse_date_flexible("invalid date")
    assert result is None

def test_convert_dates_in_dict():
    """Test converting multiple date fields"""
    data = {
        "name": "John Doe",
        "date_of_birth": "15/01/1990",
        "date_sign_on": "2023-01-15",
        "other_field": "keep this"
    }
    
    result = convert_dates_in_dict(data, ['date_of_birth', 'date_sign_on'])
    
    assert isinstance(result['date_of_birth'], datetime)
    assert isinstance(result['date_sign_on'], datetime)
    assert result['other_field'] == "keep this"
```

**Testing Checklist:**
- [ ] Parse YYYY-MM-DD format (HTML input)
- [ ] Parse DD/MM/YYYY format (AI output)
- [ ] Parse MM/DD/YYYY format (US)
- [ ] Parse ISO with time and timezone
- [ ] Handle empty/null values gracefully
- [ ] Handle invalid dates gracefully
- [ ] All unit tests pass
- [ ] Integration test: Create crew with various date formats

**Acceptance Criteria:**
- All common date formats are supported
- Invalid dates don't crash the system
- Dates are stored with UTC timezone
- Logging shows date conversion success/failure

---

### TASK 1.3: Create File Upload Endpoint Structure

**Duration:** 4 hours
**Priority:** CRITICAL
**Files to Create/Modify:**
- Modify: `/app/backend/app/api/v1/crew.py`
- Create: `/app/backend/app/services/google_drive_service.py` (stub)

**Objective:**
Create the endpoint structure to receive and process file uploads, with placeholder for Google Drive integration.

**Implementation Steps:**

#### Step 1: Add upload endpoint to crew.py

```python
# Add to /app/backend/app/api/v1/crew.py

import base64
from typing import Dict

@router.post("/{crew_id}/upload-passport-files")
async def upload_passport_files(
    crew_id: str,
    file_data: Dict,
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
        
        from app.repositories.crew_repository import CrewRepository
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
```

#### Step 2: Create Google Drive service stub

```python
# Create new file: /app/backend/app/services/google_drive_service.py

"""
Google Drive Service - Handles file operations with Google Drive

This service manages:
- Passport file uploads
- Summary file generation and uploads
- File deletion
- File renaming
- Folder structure management
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class GoogleDriveService:
    """Service for Google Drive file operations"""
    
    def __init__(self):
        """Initialize Google Drive service"""
        logger.info("🔧 Initializing Google Drive Service")
    
    async def upload_passport_files(
        self,
        company_id: str,
        upload_data: Dict
    ) -> Dict:
        """
        Upload passport and summary files to Google Drive
        
        Args:
            company_id: Company UUID
            upload_data: Dictionary containing:
                - file_content: bytes
                - filename: str
                - content_type: str
                - summary_text: str
                - ship_name: str
                - crew_id: str
                - crew_name: str
                - passport_number: str
        
        Returns:
            {
                "success": bool,
                "passport_file_id": str,
                "summary_file_id": str,
                "message": str
            }
        """
        try:
            logger.info(f"📤 Uploading passport files for crew: {upload_data.get('crew_name')}")
            
            # TODO: Implement actual Google Drive upload in Phase 2
            # For now, return mock success for testing
            
            logger.warning("⚠️ Google Drive upload not yet implemented - returning mock response")
            
            # Mock file IDs
            passport_file_id = f"mock-passport-{upload_data.get('crew_id')}"
            summary_file_id = f"mock-summary-{upload_data.get('crew_id')}"
            
            logger.info(f"✅ Mock upload successful")
            logger.info(f"   📎 Mock Passport ID: {passport_file_id}")
            logger.info(f"   📋 Mock Summary ID: {summary_file_id}")
            
            return {
                "success": True,
                "passport_file_id": passport_file_id,
                "summary_file_id": summary_file_id,
                "message": "Files uploaded successfully (MOCK)"
            }
            
        except Exception as e:
            logger.error(f"❌ Error in upload_passport_files: {e}")
            return {
                "success": False,
                "message": f"Upload failed: {str(e)}",
                "error": str(e)
            }
    
    async def delete_passport_files(
        self,
        passport_file_id: Optional[str],
        summary_file_id: Optional[str]
    ) -> Dict:
        """Delete passport files from Google Drive"""
        # TODO: Implement in Phase 2
        logger.warning("⚠️ delete_passport_files not yet implemented")
        return {"success": True, "message": "Delete not yet implemented"}
    
    async def rename_passport_files(
        self,
        passport_file_id: Optional[str],
        summary_file_id: Optional[str],
        new_crew_name: str,
        new_passport_number: str
    ) -> Dict:
        """Rename passport files in Google Drive"""
        # TODO: Implement in Phase 2
        logger.warning("⚠️ rename_passport_files not yet implemented")
        return {"success": True, "message": "Rename not yet implemented"}
```

**Testing Checklist:**
- [ ] Endpoint accepts correct file_data structure
- [ ] Validates required fields
- [ ] Decodes base64 correctly
- [ ] Validates file size
- [ ] Calls Google Drive service (mock)
- [ ] Updates crew with file IDs
- [ ] Returns correct response structure
- [ ] Handles errors gracefully
- [ ] Frontend receives mock file IDs

**Acceptance Criteria:**
- Endpoint exists and is callable
- Request validation works
- Mock upload returns success
- Crew record updated with mock file IDs
- Ready for real Google Drive integration in Phase 2

---

## 🟡 PHASE 2: GOOGLE DRIVE INTEGRATION

### TASK 2.1: Implement Google Drive Service

**Duration:** 4 hours
**Priority:** HIGH
**Files to Create/Modify:**
- Modify: `/app/backend/app/services/google_drive_service.py`
- Create: `/app/backend/app/utils/google_drive_helper.py`

**Objective:**
Implement full Google Drive integration for uploading, deleting, and managing passport files.

**Implementation Steps:**

#### Step 1: Check if dual_apps_script_manager exists

```bash
# Check if V1's Google Drive manager can be reused
ls -la /app/backend-v1/dual_apps_script_manager.py
ls -la /app/backend-v1/company_google_drive_manager.py
```

#### Step 2: Create Google Drive helper utility

```python
# Create: /app/backend/app/utils/google_drive_helper.py

"""
Google Drive Helper - Utilities for Google Drive operations
Adapted from V1's dual_apps_script_manager.py
"""

import logging
import httpx
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)

class GoogleDriveHelper:
    """Helper class for Google Drive API operations via Apps Script"""
    
    def __init__(self, company_id: str):
        """
        Initialize with company-specific configuration
        
        Args:
            company_id: Company UUID to fetch Google Drive config
        """
        self.company_id = company_id
        self.apps_script_url = None
        self.folder_id = None
    
    async def load_config(self):
        """Load Google Drive configuration from database"""
        from app.db.mongodb import mongo_db
        
        # Get company's Google Drive configuration
        company = await mongo_db.find_one("companies", {"id": self.company_id})
        
        if not company:
            raise ValueError(f"Company {self.company_id} not found")
        
        gdrive_config = company.get('google_drive_config', {})
        
        self.apps_script_url = gdrive_config.get('apps_script_url')
        self.folder_id = gdrive_config.get('folder_id') or gdrive_config.get('main_folder_id')
        
        if not self.apps_script_url:
            raise ValueError("Google Apps Script URL not configured for company")
        
        if not self.folder_id:
            raise ValueError("Google Drive folder ID not configured for company")
        
        logger.info(f"✅ Google Drive config loaded for company {self.company_id}")
    
    async def call_apps_script(self, payload: Dict) -> Dict:
        """
        Call Google Apps Script with given payload
        
        Args:
            payload: Action and data to send to Apps Script
            
        Returns:
            Response from Apps Script
        """
        if not self.apps_script_url:
            await self.load_config()
        
        try:
            logger.info(f"📞 Calling Apps Script: {payload.get('action')}")
            
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    self.apps_script_url,
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✅ Apps Script response: {result.get('success')}")
                return result
                
        except httpx.TimeoutException:
            logger.error("❌ Apps Script call timed out")
            return {
                "success": False,
                "message": "Google Apps Script timeout",
                "error": "TIMEOUT"
            }
        except Exception as e:
            logger.error(f"❌ Apps Script call failed: {e}")
            return {
                "success": False,
                "message": str(e),
                "error": str(type(e).__name__)
            }
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        folder_path: str,
        mime_type: str = 'application/octet-stream'
    ) -> Optional[str]:
        """
        Upload a file to Google Drive
        
        Args:
            file_content: File content as bytes
            filename: Name of the file
            folder_path: Path within company folder (e.g., "BROTHER 36/Passport")
            mime_type: MIME type of the file
            
        Returns:
            File ID if successful, None otherwise
        """
        import base64
        
        payload = {
            "action": "upload_file",
            "parent_folder_id": self.folder_id,
            "folder_path": folder_path,
            "filename": filename,
            "file_content": base64.b64encode(file_content).decode('utf-8'),
            "mime_type": mime_type
        }
        
        result = await self.call_apps_script(payload)
        
        if result.get('success'):
            file_id = result.get('file_id')
            logger.info(f"✅ File uploaded: {filename} → {file_id}")
            return file_id
        else:
            logger.error(f"❌ File upload failed: {result.get('message')}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive"""
        payload = {
            "action": "delete_file",
            "file_id": file_id
        }
        
        result = await self.call_apps_script(payload)
        return result.get('success', False)
    
    async def rename_file(self, file_id: str, new_name: str) -> bool:
        """Rename a file in Google Drive"""
        payload = {
            "action": "rename_file",
            "file_id": file_id,
            "new_name": new_name
        }
        
        result = await self.call_apps_script(payload)
        return result.get('success', False)
```

#### Step 3: Implement real upload in GoogleDriveService

```python
# Modify: /app/backend/app/services/google_drive_service.py

from app.utils.google_drive_helper import GoogleDriveHelper
from datetime import datetime, timezone

class GoogleDriveService:
    """Service for Google Drive file operations"""
    
    async def upload_passport_files(
        self,
        company_id: str,
        upload_data: Dict
    ) -> Dict:
        """Upload passport and summary files to Google Drive"""
        try:
            # Extract data
            file_content = upload_data['file_content']
            filename = upload_data['filename']
            content_type = upload_data['content_type']
            summary_text = upload_data['summary_text']
            ship_name = upload_data['ship_name']
            crew_name = upload_data['crew_name']
            passport_number = upload_data['passport_number']
            
            logger.info(f"📤 Uploading files for: {crew_name} ({passport_number})")
            
            # Initialize Google Drive helper
            drive_helper = GoogleDriveHelper(company_id)
            await drive_helper.load_config()
            
            # Determine folder path
            if ship_name and ship_name != '-':
                folder_path = f"{ship_name}/Passport"
                summary_folder_path = f"{ship_name}/Passport/SUMMARY"
            else:
                folder_path = "Standby Crew/Passport"
                summary_folder_path = "Standby Crew/Passport/SUMMARY"
            
            # Upload original passport file
            logger.info(f"📁 Uploading to: {folder_path}/{filename}")
            passport_file_id = await drive_helper.upload_file(
                file_content=file_content,
                filename=filename,
                folder_path=folder_path,
                mime_type=content_type
            )
            
            if not passport_file_id:
                return {
                    "success": False,
                    "message": "Failed to upload passport file to Google Drive"
                }
            
            # Generate and upload summary file
            summary_filename = f"{crew_name}_{passport_number}_summary.txt"
            summary_content = self._generate_summary_content(
                crew_name=crew_name,
                passport_number=passport_number,
                ship_name=ship_name,
                summary_text=summary_text,
                filename=filename
            )
            
            logger.info(f"📝 Uploading summary to: {summary_folder_path}/{summary_filename}")
            summary_file_id = await drive_helper.upload_file(
                file_content=summary_content.encode('utf-8'),
                filename=summary_filename,
                folder_path=summary_folder_path,
                mime_type='text/plain'
            )
            
            logger.info(f"✅ Files uploaded successfully")
            logger.info(f"   📎 Passport: {passport_file_id}")
            logger.info(f"   📋 Summary: {summary_file_id}")
            
            return {
                "success": True,
                "passport_file_id": passport_file_id,
                "summary_file_id": summary_file_id,
                "message": "Files uploaded successfully"
            }
            
        except ValueError as e:
            logger.error(f"❌ Configuration error: {e}")
            return {
                "success": False,
                "message": f"Google Drive configuration error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ Upload error: {e}")
            return {
                "success": False,
                "message": f"Upload failed: {str(e)}"
            }
    
    def _generate_summary_content(
        self,
        crew_name: str,
        passport_number: str,
        ship_name: str,
        summary_text: str,
        filename: str
    ) -> str:
        """Generate summary file content"""
        return f"""PASSPORT ANALYSIS SUMMARY
Generated: {datetime.now(timezone.utc).isoformat()}
Ship: {ship_name}
Original File: {filename}

CREW INFORMATION:
- Name: {crew_name}
- Passport Number: {passport_number}

OCR EXTRACTED TEXT:
{summary_text}

---
This summary was generated automatically using AI OCR for crew management.
"""
```

**Testing Checklist:**
- [ ] Google Drive config loads from database
- [ ] Apps Script URL is called correctly
- [ ] Passport file uploads to correct folder
- [ ] Summary file uploads to SUMMARY subfolder
- [ ] File IDs are returned correctly
- [ ] Standby crew files go to correct folder
- [ ] Error handling for missing config
- [ ] Error handling for upload failures

---

### TASK 2.2: Implement File Deletion

**Duration:** 2 hours
**Priority:** HIGH

```python
# Add to GoogleDriveService

async def delete_passport_files(
    self,
    company_id: str,
    passport_file_id: Optional[str],
    summary_file_id: Optional[str]
) -> Dict:
    """
    Delete passport files from Google Drive
    
    Called when deleting a crew member
    """
    try:
        drive_helper = GoogleDriveHelper(company_id)
        await drive_helper.load_config()
        
        deleted_files = []
        failed_files = []
        
        # Delete passport file
        if passport_file_id:
            logger.info(f"🗑️ Deleting passport file: {passport_file_id}")
            if await drive_helper.delete_file(passport_file_id):
                deleted_files.append(passport_file_id)
                logger.info(f"✅ Passport file deleted")
            else:
                failed_files.append(passport_file_id)
                logger.error(f"❌ Failed to delete passport file")
        
        # Delete summary file
        if summary_file_id:
            logger.info(f"🗑️ Deleting summary file: {summary_file_id}")
            if await drive_helper.delete_file(summary_file_id):
                deleted_files.append(summary_file_id)
                logger.info(f"✅ Summary file deleted")
            else:
                failed_files.append(summary_file_id)
                logger.error(f"❌ Failed to delete summary file")
        
        return {
            "success": len(failed_files) == 0,
            "deleted_count": len(deleted_files),
            "failed_count": len(failed_files),
            "message": f"Deleted {len(deleted_files)} files"
        }
        
    except Exception as e:
        logger.error(f"❌ Delete error: {e}")
        return {
            "success": False,
            "message": f"Delete failed: {str(e)}"
        }

# Update delete_crew in crew_service.py to call this:

@staticmethod
async def delete_crew(crew_id: str, current_user: UserResponse):
    """Delete crew member and associated files"""
    crew = await CrewRepository.find_by_id(crew_id)
    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")
    
    # Check permission
    if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        if crew.get('company_id') != current_user.company:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete files from Google Drive
    from app.services.google_drive_service import GoogleDriveService
    
    drive_service = GoogleDriveService()
    await drive_service.delete_passport_files(
        company_id=current_user.company,
        passport_file_id=crew.get('passport_file_id'),
        summary_file_id=crew.get('summary_file_id')
    )
    
    # Delete from database
    await CrewRepository.delete(crew_id)
    
    logger.info(f"✅ Crew member deleted: {crew_id}")
    
    return {"message": "Crew member deleted successfully"}
```

---

## 🟢 PHASE 3: ADDITIONAL FEATURES

### TASK 3.1: Implement Audit Trail

**Duration:** 3 hours
**Priority:** MEDIUM

```python
# Create: /app/backend/app/services/audit_trail_service.py

"""
Audit Trail Service - Track all important actions
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class AuditTrailService:
    """Service for logging audit trails"""
    
    @staticmethod
    async def log_action(
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Dict,
        company_id: str
    ) -> None:
        """
        Log an audit trail entry
        
        Args:
            user_id: User who performed the action
            action: Action type (CREATE_CREW, UPDATE_CREW, DELETE_CREW, etc.)
            resource_type: Type of resource (crew_member, certificate, etc.)
            resource_id: ID of the resource
            details: Additional details about the action
            company_id: Company UUID
        """
        try:
            audit_entry = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details,
                "company_id": company_id,
                "timestamp": datetime.now(timezone.utc),
                "ip_address": None,  # TODO: Get from request
                "user_agent": None   # TODO: Get from request
            }
            
            await mongo_db.create("audit_trail", audit_entry)
            
            logger.info(f"📝 Audit: {action} on {resource_type} by user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to log audit trail: {e}")
            # Don't fail the main operation if audit logging fails

# Use in crew_service.py:

from app.services.audit_trail_service import AuditTrailService

@staticmethod
async def create_crew(crew_data: CrewCreate, current_user: UserResponse):
    # ... existing code ...
    
    # Log audit trail
    await AuditTrailService.log_action(
        user_id=current_user.id,
        action="CREATE_CREW",
        resource_type="crew_member",
        resource_id=crew_dict["id"],
        details={
            "crew_name": crew_data.full_name,
            "passport": crew_data.passport,
            "ship": crew_data.ship_sign_on,
            "status": crew_data.status
        },
        company_id=current_user.company
    )
    
    return CrewResponse(**crew_dict)
```

---

## 🧪 TESTING STRATEGY

### Unit Tests
```python
# /app/backend/tests/test_crew_service.py

import pytest
from app.services.crew_service import CrewService
from app.models.crew import CrewCreate

@pytest.mark.asyncio
async def test_create_crew_with_various_date_formats():
    """Test crew creation with different date formats"""
    test_dates = [
        ("2023-01-15", "YYYY-MM-DD"),
        ("15/01/2023", "DD/MM/YYYY"),
        ("01/15/2023", "MM/DD/YYYY"),
        ("2023-01-15T10:30:00Z", "ISO with Z")
    ]
    
    for date_str, format_name in test_dates:
        crew_data = CrewCreate(
            full_name="Test User",
            date_of_birth=date_str,
            place_of_birth="Test Place",
            passport="TEST123",
            company_id="test-company"
        )
        
        # Should not raise exception
        crew = await CrewService.create_crew(crew_data, mock_user)
        assert crew.date_of_birth is not None
```

### Integration Tests
```bash
# Run full integration test
pytest /app/backend/tests/test_crew_integration.py -v
```

### End-to-End Tests
```bash
# Use testing agent
python /app/backend/tests/e2e_test_add_crew.py
```

---

## 📋 DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Code review completed
- [ ] Migration scripts ready (if needed)

### Phase 1 Deployment
- [ ] Deploy duplicate check
- [ ] Deploy date parsing
- [ ] Deploy file upload endpoint (mock)
- [ ] Test with frontend
- [ ] Monitor logs for errors

### Phase 2 Deployment
- [ ] Configure Google Drive for test company
- [ ] Deploy Google Drive service
- [ ] Test file upload end-to-end
- [ ] Test file deletion
- [ ] Verify files in Google Drive

### Phase 3 Deployment
- [ ] Deploy audit trail
- [ ] Verify audit logs
- [ ] Test all flows end-to-end
- [ ] Performance testing

---

## 🎯 SUCCESS METRICS

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Feature Parity | 100% | All V1 features working in V2 |
| Test Coverage | >80% | pytest --cov |
| API Response Time | <2s | Load testing |
| File Upload Success | >95% | Monitor logs |
| Duplicate Detection | 100% | Functional testing |
| Date Parse Success | >99% | Unit tests |

---

## 🔄 ROLLBACK PLAN

If issues arise during deployment:

### Phase 1 Rollback:
```bash
git revert <commit-hash>
sudo supervisorctl restart backend
```

### Phase 2 Rollback:
- Disable Google Drive integration
- Use mock upload temporarily
- Files already uploaded remain in Drive

### Phase 3 Rollback:
- Audit trail is optional
- Can be disabled without affecting core functionality

---

## 📞 SUPPORT & COMMUNICATION

### Daily Standup Format:
- What was completed yesterday
- What will be worked on today
- Any blockers

### Testing Checkpoints:
- End of Phase 1: Test with frontend team
- End of Phase 2: Test Google Drive integration
- End of Phase 3: Full regression testing

---

## 🎓 KNOWLEDGE TRANSFER

### Documentation to Create:
1. Google Drive Service API documentation
2. Date parsing utility guide
3. Audit trail usage examples
4. Troubleshooting guide

### Code Comments:
- Every new function needs docstring
- Complex logic needs inline comments
- Migration notes in commit messages

---

**Plan Created:** 2025-01-XX
**Estimated Completion:** 3 working days
**Owner:** Development Team
**Reviewer:** Tech Lead

**Status:**
- [ ] Plan Approved
- [ ] Phase 1 Started
- [ ] Phase 2 Started
- [ ] Phase 3 Started
- [ ] Migration Complete
