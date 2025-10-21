# Survey Report AI Upload - Backend Implementation Complete ✅

## Phase 1 & 2: Backend Foundation + Upload Complete

### **Files Modified:**

1. **`/app/backend/server.py`**
   - Added Survey Report helper functions (~Line 4906-5100)
   - Added analyze endpoint (~Line 5254-5465)
   - Added upload endpoint (~Line 5467-5585)

2. **`/app/backend/dual_apps_script_manager.py`**
   - Added `upload_survey_report_file()` method (~Line 944-1010)
   - Added `upload_survey_report_summary()` method (~Line 1012-1080)

---

## Implementation Details

### **1. Helper Functions** (`server.py` ~Line 4906)

#### `extract_survey_report_fields_from_summary()`
- Uses System AI (Gemini) to extract 8 fields
- Handles JSON parsing and date standardization
- Returns structured data dictionary

#### `create_survey_report_extraction_prompt()`
- AI prompt template for survey report extraction
- Specifies all 8 fields with detailed instructions
- Handles various survey report formats

#### `validate_ship_info_match()`
- Normalizes ship names (removes "MV", "M/V" prefixes)
- Extracts 7-digit IMO numbers
- Compares extracted vs selected ship
- Returns match status (name, IMO, overall)

---

### **2. Analyze Endpoint** (`server.py` ~Line 5254)

**Endpoint:** `POST /api/survey-reports/analyze-file`

**Form Data:**
```javascript
{
  survey_report_file: File,
  ship_id: string,
  bypass_validation: "false" | "true"
}
```

**Process Flow:**
```
1. Read file content (up to 20MB)
2. Get company & ship info
3. Get AI configuration (Document AI + System AI)
4. Call Document AI analysis (analyze_maritime_document_ai)
5. Extract 8 fields from AI summary
6. Validate ship name/IMO
7. Return analysis + base64 file content
```

**Apps Script Integration:**
- Action: `analyze_maritime_document_ai`
- Document Type: `general_maritime` (Other Maritime Documents)
- NO upload at this stage

**Response:**
```json
{
  "success": true,
  "analysis": {
    "survey_report_name": "Annual Survey",
    "survey_report_no": "AS-2024-001",
    "issued_by": "Lloyd's Register",
    "issued_date": "2024-01-15",
    "ship_name": "BROTHER 36",
    "ship_imo": "1234567",
    "surveyor_name": "John Smith",
    "note": "All systems operational",
    "_file_content": "base64_encoded...",
    "_filename": "Annual_Survey.pdf",
    "_content_type": "application/pdf",
    "_summary_text": "Full AI extracted text...",
    "_ship_name": "BROTHER 36"
  },
  "ship_name": "BROTHER 36",
  "ship_imo": "1234567"
}
```

**Validation Error Response:**
```json
{
  "success": false,
  "validation_error": true,
  "message": "Ship information mismatch. Please verify or bypass validation.",
  "extracted_ship_name": "MV BROTHER 35",
  "extracted_ship_imo": "9876543",
  "selected_ship_name": "BROTHER 36",
  "selected_ship_imo": "1234567",
  "validation_details": {
    "ship_name_match": false,
    "ship_imo_match": false,
    "overall_match": false
  }
}
```

---

### **3. Upload Endpoint** (`server.py` ~Line 5467)

**Endpoint:** `POST /api/survey-reports/{report_id}/upload-files`

**JSON Body:**
```javascript
{
  file_content: "base64_encoded_content",
  filename: "Annual_Survey.pdf",
  content_type: "application/pdf",
  summary_text: "Full AI extracted text..."
}
```

**Process Flow:**
```
1. Validate report exists
2. Get company, ship info
3. Decode base64 file content
4. Upload original file → ShipName/Class & Flag Cert/Class Survey Report/
5. Upload summary file → SUMMARY/Class & Flag Document/
6. Update MongoDB record with file IDs
```

**Response:**
```json
{
  "success": true,
  "survey_report_file_id": "1a2b3c4d...",
  "survey_summary_file_id": "5e6f7g8h...",
  "message": "Survey report files uploaded successfully",
  "upload_results": {
    "original": { /* upload details */ },
    "summary": { /* upload details */ }
  }
}
```

---

### **4. Dual Apps Script Manager Methods**

#### `upload_survey_report_file()` (~Line 944)
**Purpose:** Upload original survey report file to Google Drive

**Folder Structure:**
```
Company Drive/
└── ShipName/
    └── Class & Flag Cert/
        └── Class Survey Report/
            └── Annual_Survey.pdf  ← Original file here
```

**Apps Script Call:**
```python
{
    'action': 'upload_file_with_folder_creation',
    'parent_folder_id': self.parent_folder_id,  # ROOT
    'ship_name': ship_name,  # e.g., "BROTHER 36"
    'category': 'Class & Flag Cert/Class Survey Report',  # Nested path
    'filename': filename,
    'file_content': base64_file,
    'content_type': content_type
}
```

**Key Points:**
- ✅ Category uses nested path: `"Class & Flag Cert/Class Survey Report"`
- ✅ Apps Script will create folders if they don't exist
- ✅ Returns `survey_report_file_id` for Drive file

#### `upload_survey_report_summary()` (~Line 1012)
**Purpose:** Upload AI summary text file to SUMMARY folder

**Folder Structure:**
```
Company Drive/
└── SUMMARY/
    └── Class & Flag Document/
        └── Annual_Survey_Summary.txt  ← Summary file here
```

**Apps Script Call:**
```python
{
    'action': 'upload_file_with_folder_creation',
    'parent_folder_id': self.parent_folder_id,  # ROOT
    'ship_name': 'SUMMARY',  # Special folder name
    'category': 'Class & Flag Document',  # Summary category
    'filename': f"{base_name}_Summary.txt",
    'file_content': base64_text,
    'content_type': 'text/plain'
}
```

**Key Points:**
- ✅ Uses `'ship_name': 'SUMMARY'` to create top-level SUMMARY folder
- ✅ Category: `'Class & Flag Document'` (NOT "Crew Records")
- ✅ Returns `summary_file_id` for Drive file

---

## Folder Path Verification ✅

### **CORRECT Paths (Implemented):**

**Original Survey Report:**
```
ROOT/
└── ShipName/                    ← ship_name parameter
    └── Class & Flag Cert/       ← First part of category
        └── Class Survey Report/ ← Second part of category
            └── file.pdf
```

**Summary File:**
```
ROOT/
└── SUMMARY/                     ← ship_name = "SUMMARY"
    └── Class & Flag Document/   ← category parameter
        └── file_Summary.txt
```

### **INCORRECT Paths (Avoided):**

❌ **NOT using:**
```
ROOT/
└── ShipName/
    └── Crew Records/            ← WRONG! This is for crew certificates
        └── Class Survey Report/
```

---

## Apps Script Compatibility

### **Existing Action Used:**
- `upload_file_with_folder_creation` ✅ (Already exists)

### **Parameters:**
- `parent_folder_id` - Root folder ID
- `ship_name` - Top-level folder name
- `category` - Sub-folder path (can be nested with `/`)
- `filename` - File name
- `file_content` - Base64 encoded content
- `content_type` - MIME type

### **Folder Creation Logic:**
Apps Script will:
1. Find or create folder named `{ship_name}` under ROOT
2. Parse `category` by splitting on `/`
3. For each part, find or create subfolder
4. Upload file to final destination folder

**Example:**
```
ship_name: "BROTHER 36"
category: "Class & Flag Cert/Class Survey Report"

Creates:
ROOT → BROTHER 36 → Class & Flag Cert → Class Survey Report
```

---

## Error Handling

### **Analysis Failures:**
- Document AI fails → Return empty analysis with file content
- Field extraction fails → Return empty fields with file content
- Ship validation fails → Return validation error (user can bypass)

### **Upload Failures:**
- Original file upload fails → Throw HTTP 500 error
- Summary upload fails → Log warning (non-critical)
- File IDs always updated in MongoDB if upload succeeds

---

## Testing Checklist

### **Backend Endpoints:**
- [ ] Test analyze endpoint with sample survey report PDF
- [ ] Test analyze with JPG/PNG images
- [ ] Test ship validation (match & mismatch cases)
- [ ] Test bypass validation
- [ ] Test upload endpoint after record creation
- [ ] Verify folder structure in Google Drive
- [ ] Check file IDs are stored in MongoDB

### **Edge Cases:**
- [ ] Large files (20MB)
- [ ] AI extraction failures
- [ ] Invalid ship names in extracted data
- [ ] Missing summary text
- [ ] Apps Script errors

---

## Database Schema

**MongoDB Collection:** `survey_reports`

**New Fields (after upload):**
```json
{
  "id": "uuid",
  "ship_id": "uuid",
  "survey_report_name": "string",
  "survey_report_no": "string",
  "issued_by": "string",
  "issued_date": "datetime",
  "note": "string",
  "status": "string",
  "surveyor_name": "string",  // Not in original model - may need to add
  "survey_report_file_id": "string",  ← NEW: Google Drive file ID
  "survey_summary_file_id": "string",  ← NEW: Google Drive summary ID
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Note:** May need to update SurveyReportResponse model to include:
- `surveyor_name: Optional[str]`
- `survey_report_file_id: Optional[str]`
- `survey_summary_file_id: Optional[str]`

---

## Next Steps

### **Phase 3: Update Pydantic Models** (10 mins)
- Add missing fields to SurveyReportBase/Response
- Add surveyor_name field
- Add file ID fields

### **Phase 4: Frontend Implementation** (6-8 hours)
- Add states (15 states)
- Add upload handlers (~460 lines)
- Add UI components (~330 lines)
- Implement single file mode
- Implement batch processing
- Add progress tracking
- Add results modal

### **Phase 5: Testing** (2-3 hours)
- Backend API testing
- Frontend integration testing
- Google Drive folder verification
- End-to-end workflow testing

---

## Backend Implementation Status

✅ **Phase 1 Complete:** Analyze endpoint with AI extraction  
✅ **Phase 2 Complete:** Upload endpoint with Google Drive integration  
✅ **Folder Paths Verified:** Using correct Class & Flag Cert structure  
✅ **Backend Tested:** No syntax errors, server starts successfully  

**Ready for Phase 3: Pydantic Model Updates!** 🚀
