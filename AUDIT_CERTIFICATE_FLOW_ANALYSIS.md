# 📋 AUDIT CERTIFICATE FLOW - PHÂN TÍCH CHI TIẾT

## 🎯 TỔNG QUAN

**Audit Certificate** là các chứng chỉ audit ISM/ISPS/MLC cho tàu biển, khác với **Audit Reports** (báo cáo audit). Đây là flow cho việc thêm certificate, không phải report.

---

## 📊 KIẾN TRÚC HỆ THỐNG

### Frontend Components
```
/app/frontend/src/components/AuditCertificate/
├── AddAuditCertificateModal.jsx    ← Modal chính (1500+ lines)
├── AuditCertificateTable.jsx       ← Bảng hiển thị
├── EditAuditCertificateModal.jsx   ← Modal chỉnh sửa
└── ... (các component khác)
```

### Backend V1 (Production - Đang chạy)
```
/app/backend-v1/server.py
├── GET    /audit-certificates
├── GET    /audit-certificates/{cert_id}
├── POST   /audit-certificates
├── PUT    /audit-certificates/{cert_id}
├── DELETE /audit-certificates/{cert_id}
├── POST   /audit-certificates/multi-upload        ← ENDPOINT CHÍNH
└── POST   /audit-certificates/{cert_id}/auto-rename-file
```

### Backend V2 (Mới - Đang phát triển)
```
/app/backend/app/api/v1/audit_certificates.py
├── GET    /audit-certificates
├── GET    /audit-certificates/{cert_id}
├── POST   /audit-certificates
├── PUT    /audit-certificates/{cert_id}
├── DELETE /audit-certificates/{cert_id}
├── POST   /audit-certificates/bulk-delete
├── POST   /audit-certificates/check-duplicate
└── POST   /audit-certificates/analyze              ← TODO (chưa implement)
```

---

## 🚨 VẤN ĐỀ PHÁT HIỆN

### ❌ Frontend đang gọi các endpoint KHÔNG TỒN TẠI trong Backend V2:

1. **`/api/audit-certificates/analyze-file`** ❌
   - Frontend: `AddAuditCertificateModal.jsx` line 391
   - Backend V2: KHÔNG CÓ
   - Backend V1: Sử dụng `analyze_document_with_ai()` function

2. **`/api/audit-certificates/multi-upload`** ❌
   - Frontend: `AddAuditCertificateModal.jsx` lines 599, 875
   - Backend V2: KHÔNG CÓ
   - Backend V1: CÓ (lines 26961-27462)

3. **`/api/audit-certificates/create-with-file-override`** ❌
   - Frontend: `AddAuditCertificateModal.jsx` line 816
   - Backend V2: KHÔNG CÓ
   - Backend V1: Không có (có thể là logic mới)

---

## 📋 FLOW CHI TIẾT - BACKEND V1 (ĐANG HOẠT ĐỘNG)

### 1️⃣ **SINGLE FILE UPLOAD** - Analyze Only

**Frontend Flow:**
```javascript
// File: AddAuditCertificateModal.jsx
// Lines: 375-537

handleSingleFileAnalysis(file)
  ↓
1. Read file as ArrayBuffer
2. Convert to base64
3. POST /api/audit-certificates/analyze-file
   {
     file_content: base64String,
     filename: string,
     content_type: string,
     ship_id: string  // For validation
   }
  ↓
4. Backend returns extracted_info
5. Auto-fill form với dữ liệu
6. Store file object cho lúc Save
7. User review và click Save
```

**Backend V1 Processing (analyze_document_with_ai):**
```
Lines: 16143-16400

1. VALIDATE FILE TYPE
   - PDF: Check magic bytes %PDF
   - Images: JPG, PNG
   - Max size: 50MB

2. SMART PDF ANALYSIS
   ┌─ analyze_pdf_type() ─────────────┐
   │ • text_based → Direct extraction │
   │ • image_based → OCR processing   │
   │ • mixed → Hybrid approach        │
   └──────────────────────────────────┘

3. TEXT EXTRACTION
   • Text-based PDF: PyPDF2
   • Image-based PDF: Google Document AI (OCR)
   • Images: Google Document AI

4. AI FIELD EXTRACTION
   Provider: Emergent LLM / Google Gemini
   Model: gemini-2.0-flash (default)
   
   Extracted Fields:
   ├── cert_name            (required)
   ├── cert_abbreviation
   ├── cert_no              (required)
   ├── cert_type            (Full Term/Interim/...)
   ├── issue_date
   ├── valid_date
   ├── last_endorse
   ├── next_survey
   ├── next_survey_type
   ├── issued_by
   ├── issued_by_abbreviation
   ├── ship_name
   ├── imo_number
   └── confidence score

5. POST-PROCESSING
   • Normalize issued_by abbreviations
   • Validate certificate type
   • Format dates

6. RETURN JSON
   {
     "success": true,
     "extracted_info": {...},
     "validation_warning": {...},    // If IMO mismatch
     "duplicate_warning": {...},     // If duplicate found
     "category_warning": {...}       // If not ISM/ISPS/MLC
   }
```

---

### 2️⃣ **MULTI FILE UPLOAD** - Batch Processing with Auto-create

**Frontend Flow:**
```javascript
// File: AddAuditCertificateModal.jsx
// Lines: 540-776

handleMultiFileBatchUpload(fileArray)
  ↓
1. Initialize upload tracking state
2. Create staggered parallel uploads
   • File 0 → starts immediately
   • File 1 → starts after 2s
   • File 2 → starts after 4s
   • ...
  ↓
3. For each file (parallel):
   FormData.append('files', file)
   POST /api/audit-certificates/multi-upload?ship_id={id}
   
4. Track progress with onUploadProgress
5. Update UI với status cho mỗi file
6. Show results modal
```

**Backend V1 Multi-Upload Endpoint:**
```
Lines: 26961-27462

POST /audit-certificates/multi-upload?ship_id={id}
Body: multipart/form-data (files array)

FOR EACH FILE:

STEP 1: VALIDATE FILE
├── Check size (max 50MB)
├── Check type (PDF, JPG, PNG)
└── Read file content

STEP 2: AI ANALYSIS
└── Call analyze_document_with_ai()
    ├── Smart PDF processing
    ├── Text/OCR extraction
    └── AI field extraction

STEP 3: QUALITY CHECK
├── check_ai_extraction_quality()
│   ├── Critical fields: cert_name, cert_no
│   ├── All fields: 6 total
│   ├── Confidence score >= 0.4
│   └── Text quality >= 100 chars
│
└── If INSUFFICIENT:
    └── Return: "requires_manual_input"

STEP 4: CATEGORY VALIDATION
└── check_ism_isps_mlc_category(cert_name)
    ├── Must be: ISM / ISPS / MLC
    └── If NOT: Return error

STEP 5: IMO/SHIP NAME VALIDATION
├── Compare extracted_imo vs current_ship_imo
│   ├── If MISMATCH → REJECT (hard error)
│   └── If MATCH → Continue
│
└── Compare extracted_ship_name vs current_ship_name
    └── If MISMATCH → Add note "Chỉ để tham khảo"

STEP 6: DUPLICATE CHECK
└── check_audit_certificate_duplicates()
    ├── Match by: cert_name + cert_no
    └── If FOUND: Return "pending_duplicate_resolution"

STEP 7: UPLOAD TO GOOGLE DRIVE
├── Path: {ShipName}/ISM-ISPS-MLC/Audit Certificates/
├── Use: dual_apps_script_manager
├── Convert file to base64
└── Get: file_id, folder_id

STEP 8: CREATE DB RECORD
├── Collection: "audit_certificates"
├── Fields:
│   ├── id (UUID)
│   ├── ship_id
│   ├── ship_name
│   ├── cert_name
│   ├── cert_abbreviation
│   ├── cert_no
│   ├── cert_type
│   ├── issue_date
│   ├── valid_date
│   ├── last_endorse
│   ├── next_survey
│   ├── next_survey_type
│   ├── issued_by
│   ├── issued_by_abbreviation
│   ├── notes (validation note if any)
│   ├── google_drive_file_id
│   ├── google_drive_folder_id
│   ├── file_name
│   ├── created_at
│   └── company
│
└── Return: "success" + cert_id

RESPONSE:
{
  "success": true,
  "message": "...",
  "results": [
    {
      "filename": "...",
      "status": "success" | "error" | "requires_manual_input" | "pending_duplicate_resolution",
      "message": "...",
      "extracted_info": {...},
      "cert_id": "..."
    }
  ],
  "summary": {
    "total_files": 3,
    "successfully_created": 2,
    "errors": 1,
    "certificates_created": [...]
  }
}
```

---

### 3️⃣ **SAVE FORM** - Manual Entry or After Single File Analysis

**Frontend Flow:**
```javascript
// File: AddAuditCertificateModal.jsx
// Lines: 778-1003

handleSubmit(e)
  ↓
IF certificateFile EXISTS:
  ┌─────────────────────────────────────────┐
  │ IF validationApproved = true:           │
  │   → Use create-with-file-override       │
  │   → Bypass validation                   │
  │ ELSE:                                   │
  │   → Use multi-upload                    │
  │   → Normal validation                   │
  └─────────────────────────────────────────┘
ELSE:
  ┌─────────────────────────────────────────┐
  │ → Call onSave(certPayload)              │
  │ → Create DB record only (no file)      │
  └─────────────────────────────────────────┘
```

---

## 🔧 HELPER FUNCTIONS & UTILITIES

### Backend V1 Key Functions:

1. **`analyze_document_with_ai()`** (Line 16143)
   - Smart PDF type detection
   - Text/OCR extraction
   - AI field extraction with dynamic prompt

2. **`check_ai_extraction_quality()`** (Line 27053)
   - Validate critical fields
   - Calculate confidence score
   - Determine if sufficient for auto-processing

3. **`check_ism_isps_mlc_category()`**
   - Validate certificate belongs to ISM/ISPS/MLC
   - Prevent wrong category uploads

4. **`check_audit_certificate_duplicates()`** (Line 4376)
   - Match by cert_name + cert_no
   - Return similarity score

5. **`validate_certificate_type()`**
   - Normalize cert_type values
   - Options: Full Term, Interim, Provisional, Short term, Conditional, Other

6. **`normalize_issued_by()`**
   - Convert organization names to abbreviations
   - e.g., "Det Norske Veritas GL" → "DNV GL"

7. **`generate_certificate_abbreviation()`**
   - Auto-generate abbreviations from cert_name

### Document AI Integration:

```python
# Google Document AI
project_id = ai_config['document_ai']['project_id']
processor_id = ai_config['document_ai']['processor_id']
location = ai_config['document_ai']['location']

# OCR Processor (from backend-v1)
from ocr_processor import OCRProcessor
ocr_processor = OCRProcessor(
    project_id=project_id,
    location=location,
    processor_id=processor_id
)

# Methods:
- process_pdf_with_ocr()
- process_image_with_ocr()
- analyze_pdf_type()
```

### Google Drive Upload:

```python
# Dual Apps Script Manager
from dual_apps_script_manager import create_dual_apps_script_manager

dual_manager = create_dual_apps_script_manager(company_id)
await dual_manager._load_configuration()

# Upload file
upload_result = await dual_manager._call_company_apps_script({
    'action': 'upload_file_with_folder_creation',
    'parent_folder_id': parent_folder_id,
    'ship_name': ship_name,
    'parent_category': 'ISM-ISPS-MLC',
    'category': 'Audit Certificates',
    'filename': filename,
    'file_content': base64_content,
    'content_type': content_type
})

# Returns:
{
  "success": true,
  "file_id": "...",
  "folder_id": "..."
}
```

---

## 🎨 UI/UX FEATURES

### Modal Capabilities:

1. **Multi Cert Upload Section**
   - AI Model display (e.g., "Emergent LLM - gemini-2.0-flash")
   - Upload guidelines
   - Single file → Analyze only
   - Multiple files → Auto-create DB records

2. **Upload Progress Tracking**
   - Real-time progress bars
   - File status indicators
   - Staggered parallel uploads (2s delay)
   - Error messages

3. **Manual Entry Form**
   - Ship Name, IMO Number (AI auto-fill)
   - Certificate Name* (required)
   - Certificate Abbreviation
   - Certificate Number
   - Certificate Type dropdown
   - Issue Date, Valid Date
   - Last Endorse, Next Survey, Next Survey Type
   - Issued By, Abbreviation
   - Notes

4. **Validation Modals**
   - IMO Mismatch Warning
   - Duplicate Detection
   - Category Mismatch (not ISM/ISPS/MLC)

---

## 📊 DATA FLOW DIAGRAM

```
USER UPLOADS FILE(S)
        ↓
    [Frontend]
   ┌──────────────┐
   │ 1 file?      │
   │ Multiple?    │
   └──────┬───────┘
          │
   ┌──────┴──────────────────────────────┐
   │                                     │
   ↓ SINGLE FILE                         ↓ MULTIPLE FILES
[Analyze Only]                    [Auto-create Records]
   │                                     │
   ↓                                     ↓
[Backend V1]                       [Backend V1]
analyze_document_with_ai()         multi_audit_cert_upload()
   │                                     │
   ↓                                     │
[Text/OCR Extraction]                   │
[AI Field Extraction]                   │
   │                                     │
   ↓                                     │
[Return JSON]                            │
   │                                     │
   ↓                                     ↓
[Auto-fill Form]              FOR EACH FILE:
[User Reviews]                 ├─ Analyze
[Clicks Save]                  ├─ Quality Check
   │                           ├─ Category Check
   ↓                           ├─ IMO Validation
[Submit Form]                  ├─ Duplicate Check
   │                           ├─ Upload to GDrive
   │                           └─ Create DB Record
   │                                     │
   └─────────────────┬─────────────────┘
                     ↓
            [Certificate Created]
            [Display in Table]
```

---

## 🔑 KEY DATA STRUCTURES

### Extracted Info (from AI):
```typescript
interface ExtractedInfo {
  cert_name: string;              // required
  cert_abbreviation?: string;
  cert_no: string;                // required
  cert_type?: string;
  issue_date?: string;            // YYYY-MM-DD or DD/MM/YYYY
  valid_date?: string;
  last_endorse?: string;
  next_survey?: string;
  next_survey_type?: string;
  issued_by?: string;
  issued_by_abbreviation?: string;
  ship_name?: string;
  imo_number?: string;
  confidence?: string | number;
  text_content?: string;
}
```

### Certificate Database Schema:
```typescript
interface AuditCertificate {
  id: string;                     // UUID
  ship_id: string;
  ship_name: string;
  cert_name: string;
  cert_abbreviation: string;
  cert_no: string;
  cert_type: string;              // Full Term, Interim, etc.
  issue_date: string;             // ISO datetime
  valid_date: string;             // ISO datetime
  last_endorse?: string;          // ISO datetime
  next_survey?: string;           // ISO datetime
  next_survey_type?: string;      // Initial, Intermediate, Renewal
  issued_by: string;
  issued_by_abbreviation: string;
  notes?: string;
  google_drive_file_id?: string;
  google_drive_folder_id?: string;
  file_name?: string;
  created_at: datetime;
  updated_at?: datetime;
  company: string;
}
```

---

## 🚀 MIGRATION PLAN - Backend V2

### ❗ Các Endpoint Cần Implement:

#### 1. **POST /api/audit-certificates/analyze-file**
```python
# Tương tự: audit_reports.py analyze_file endpoint
# File: backend/app/api/v1/audit_certificates.py

@router.post("/analyze-file")
async def analyze_audit_certificate_file(
    file_content: str = Form(...),
    filename: str = Form(...),
    content_type: str = Form(...),
    ship_id: str = Form(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Analyze audit certificate file using AI
    
    Process:
    1. Validate PDF/Image file
    2. Call Document AI for text/OCR extraction
    3. Use System AI for field extraction
    4. Validate ship name/IMO
    5. Check for duplicates
    6. Check category (ISM/ISPS/MLC)
    7. Return extracted_info + warnings
    """
    # TODO: Implement similar to audit_report_analyze_service.py
    pass
```

#### 2. **POST /api/audit-certificates/multi-upload**
```python
# File: backend/app/api/v1/audit_certificates.py

@router.post("/multi-upload")
async def multi_upload_audit_certificates(
    ship_id: str = Query(...),
    files: List[UploadFile] = File(...),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload multiple audit certificate files with AI analysis
    
    Process:
    1. For each file:
       - Analyze with AI
       - Check quality
       - Validate category (ISM/ISPS/MLC)
       - Validate IMO/ship name
       - Check duplicates
       - Upload to Google Drive
       - Create DB record
    2. Return batch results
    """
    # TODO: Port from backend-v1 server.py lines 26961-27462
    pass
```

#### 3. **POST /api/audit-certificates/create-with-file-override**
```python
# File: backend/app/api/v1/audit_certificates.py

@router.post("/create-with-file-override")
async def create_audit_certificate_with_file_override(
    ship_id: str = Query(...),
    file: UploadFile = File(...),
    cert_data: str = Form(...),  # JSON string
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Create audit certificate with file, bypassing validation
    (Used when user approves validation warning)
    
    Process:
    1. Parse cert_data JSON
    2. Upload file to Google Drive
    3. Create DB record with validation note
    """
    # TODO: Implement for override flow
    pass
```

### 📁 Services Cần Tạo:

#### 1. **AuditCertificateAnalyzeService**
```python
# File: backend/app/services/audit_certificate_analyze_service.py

class AuditCertificateAnalyzeService:
    @staticmethod
    async def analyze_file(...) -> Dict[str, Any]:
        """Analyze audit certificate file with AI"""
        
    @staticmethod
    async def check_quality(...) -> Dict[str, Any]:
        """Check AI extraction quality"""
        
    @staticmethod
    async def check_category(...) -> Dict[str, Any]:
        """Validate ISM/ISPS/MLC category"""
        
    @staticmethod
    async def check_duplicate(...) -> Dict[str, Any]:
        """Check for duplicate certificates"""
```

#### 2. **AuditCertificateAI Utilities**
```python
# File: backend/app/utils/audit_certificate_ai.py

async def extract_audit_certificate_fields(
    summary_text: str,
    filename: str,
    ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Extract certificate fields from Document AI summary"""
    
def create_audit_certificate_extraction_prompt(
    summary_text: str,
    filename: str
) -> str:
    """Create AI prompt for field extraction"""
```

---

## ✅ TESTING CHECKLIST

### Single File Upload:
- [ ] Upload PDF certificate
- [ ] Upload JPG certificate
- [ ] Upload PNG certificate
- [ ] AI extracts all required fields
- [ ] Form auto-fills correctly
- [ ] Dates format correctly (YYYY-MM-DD)
- [ ] User can edit before Save

### Multi File Upload:
- [ ] Upload 3 files simultaneously
- [ ] Staggered upload works (2s delay)
- [ ] Progress bars update correctly
- [ ] All 3 certificates created in DB
- [ ] All 3 files uploaded to GDrive
- [ ] Correct folder path: {Ship}/ISM-ISPS-MLC/Audit Certificates/

### Validation:
- [ ] IMO mismatch → Hard reject
- [ ] Ship name mismatch → Add note
- [ ] Duplicate detected → Show modal
- [ ] Wrong category (not ISM/ISPS/MLC) → Reject
- [ ] Low quality AI extraction → Request manual input

### Edge Cases:
- [ ] File size > 50MB → Reject
- [ ] Unsupported file type → Reject
- [ ] Empty/corrupted PDF → Reject
- [ ] AI confidence too low → Request manual input
- [ ] Network error during upload → Show error

---

## 📚 REFERENCES

### Backend V1 Files:
- `/app/backend-v1/server.py` (lines 26961-27500)
- `/app/backend-v1/ocr_processor.py`
- `/app/backend-v1/dual_apps_script_manager.py`

### Frontend Files:
- `/app/frontend/src/components/AuditCertificate/AddAuditCertificateModal.jsx`
- `/app/frontend/src/services/auditCertificateService.js`

### Backend V2 Files (TO DO):
- `/app/backend/app/api/v1/audit_certificates.py` (need to add endpoints)
- `/app/backend/app/services/audit_certificate_analyze_service.py` (need to create)
- `/app/backend/app/utils/audit_certificate_ai.py` (need to create)

---

## 🎯 PRIORITY ACTIONS

1. **HIGH**: Implement `/api/audit-certificates/analyze-file` endpoint
2. **HIGH**: Implement `/api/audit-certificates/multi-upload` endpoint  
3. **MEDIUM**: Implement `/api/audit-certificates/create-with-file-override` endpoint
4. **MEDIUM**: Create `AuditCertificateAnalyzeService`
5. **LOW**: Port helper functions to Backend V2

---

## 📝 NOTES

- Backend V1 đang hoạt động tốt, frontend đang sử dụng các endpoint từ V1
- Backend V2 thiếu 3 endpoints chính cho upload & analysis
- Cần port logic từ V1 sang V2 với cùng cấu trúc như Audit Reports
- GDrive upload path: `{ShipName}/ISM-ISPS-MLC/Audit Certificates/`
- Category validation: ONLY accept ISM/ISPS/MLC certificates
- IMO validation: HARD REJECT if mismatch
- Ship name validation: SOFT WARNING (add note)

---

**Generated**: 2025-01-XX  
**Status**: ✅ Complete Analysis  
**Next Steps**: Implement missing Backend V2 endpoints
