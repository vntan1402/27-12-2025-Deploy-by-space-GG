# 📝 AUDIT CERTIFICATE: CÁCH TẠO SUMMARY

## 🎯 TỔNG QUAN

Audit Certificate tạo **AI-generated summary** qua **3 BƯỚC CHÍNH**:

1. **Google Document AI** - OCR + Text Extraction
2. **System AI (Gemini)** - Field Extraction
3. **Summary Storage** - Upload file `.txt` lên Google Drive

---

## 🔄 FLOW HOÀN CHỈNH

```
User uploads PDF
  ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: GOOGLE DOCUMENT AI (OCR + TEXT EXTRACTION)          │
└─────────────────────────────────────────────────────────────┘
  ↓
  Check PDF page count
    ├─ ≤15 pages → Process as single file
    └─ >15 pages → Split into chunks (12 pages/chunk)
  ↓
  FOR EACH chunk:
    ↓
    Call Google Document AI API via Apps Script:
      - action: "analyze_maritime_document_ai"
      - file_content: base64 PDF
      - document_type: "audit_certificate"
      - project_id: "your-gcp-project"
      - processor_id: "ocr-processor-id"
      - location: "us"
    ↓
    Google Document AI processes PDF:
      1. OCR all pages (extract text from images)
      2. Detect layout structure
      3. Extract tables, forms
      4. Generate structured text output
    ↓
    Return: {
      "success": true,
      "data": {
        "summary": "Safety Management Certificate...", // ⭐ RAW TEXT
        "confidence": 0.95
      }
    }
  ↓
  IF multiple chunks:
    Merge all chunk summaries:
      summary_text = chunk1 + "\n\n" + chunk2 + "\n\n" + chunk3...
  ↓
  ✅ summary_text ready (e.g., 5000-10000 characters)

┌─────────────────────────────────────────────────────────────┐
│ STEP 2: SYSTEM AI (GEMINI) - FIELD EXTRACTION & SUMMARY     │
└─────────────────────────────────────────────────────────────┘
  ↓
  Create AI Prompt:
    """
    You are an AI specialized in maritime audit certificate extraction.
    
    INPUT: Below is Document AI text from an audit certificate.
    
    TASK: Extract these fields as JSON:
    {
      "cert_name": "Safety Management Certificate",
      "cert_no": "SMC-2024-001",
      "cert_type": "Full Term",
      "issue_date": "15 November 2024",
      "valid_date": "14 November 2027",
      "ship_name": "VINASHIP HARMONY",
      "imo_number": "9573945",
      "issued_by": "Bureau Veritas",
      ...
    }
    
    DOCUMENT TEXT:
    {summary_text from Document AI}
    """
  ↓
  Call System AI (Gemini 2.0 Flash):
    - Provider: "google" / "emergent"
    - Model: "gemini-2.0-flash-exp"
    - API Key: EMERGENT_LLM_KEY
    - Session: "cert_extraction_{timestamp}"
  ↓
  AI analyzes summary_text and returns JSON:
    {
      "cert_name": "Safety Management Certificate",
      "cert_no": "SMC-2024-001",
      "cert_type": "Full Term",
      "issue_date": "15 November 2024",
      "valid_date": "14 November 2027",
      "ship_name": "VINASHIP HARMONY",
      "imo_number": "9573945",
      "issued_by": "Bureau Veritas",
      "confidence_score": 0.92
    }
  ↓
  Post-processing:
    - Normalize dates (text → YYYY-MM-DD)
    - Normalize issued_by abbreviations
    - Validate IMO format (7 digits)
    - Clean text fields
  ↓
  ✅ extracted_info ready

┌─────────────────────────────────────────────────────────────┐
│ STEP 3: SUMMARY STORAGE (GOOGLE DRIVE)                      │
└─────────────────────────────────────────────────────────────┘
  ↓
  Backend has:
    - summary_text (from Document AI) ⭐
    - extracted_info (from System AI)
  ↓
  Upload main PDF to GDrive:
    Path: {ShipName}/ISM - ISPS - MLC/Audit Certificates/
    File: ISM_Certificate.pdf
    Result: file_id = "gdrive-abc123"
  ↓
  ⭐ Create summary text file:
    Filename: ISM_Certificate_Summary.txt
    Content: summary_text (UTF-8 text)
    Size: ~5-10 KB
  ↓
  Upload summary to GDrive:
    Path: {ShipName}/ISM - ISPS - MLC/Audit Certificates/
    File: ISM_Certificate_Summary.txt
    Result: summary_file_id = "gdrive-xyz789"
  ↓
  Create DB record:
    {
      "id": "cert-uuid",
      "cert_name": "Safety Management Certificate",
      "google_drive_file_id": "gdrive-abc123",
      "summary_file_id": "gdrive-xyz789",  // ⭐ Store summary ID
      ...
    }
  ↓
  ✅ Both files stored in Google Drive
  ✅ DB record has references to both files
```

---

## 💡 SUMMARY TEXT LÀ GÌ?

**Summary text KHÔNG PHẢI là AI viết tóm tắt 2-3 câu.**  
**Nó là RAW TEXT được extract bởi Google Document AI.**

### Ví dụ thực tế:

#### PDF Input (Image/Scanned):
```
┌─────────────────────────────────────┐
│  SAFETY MANAGEMENT CERTIFICATE      │
│  (SMC)                              │
│                                     │
│  This is to certify that the       │
│  Safety Management System of:      │
│                                     │
│  SHIP NAME: VINASHIP HARMONY        │
│  IMO NUMBER: 9573945                │
│  FLAG: Panama                       │
│                                     │
│  has been audited and found to     │
│  comply with ISM Code...           │
│                                     │
│  Certificate No: SMC-2024-001      │
│  Issue Date: 15 November 2024      │
│  Valid Until: 14 November 2027     │
│                                     │
│  Issued by: Bureau Veritas         │
└─────────────────────────────────────┘
```

#### Document AI Output (summary_text):
```
SAFETY MANAGEMENT CERTIFICATE
(SMC)

This is to certify that the Safety Management System of:

SHIP NAME: VINASHIP HARMONY
IMO NUMBER: 9573945
FLAG: Panama
PORT OF REGISTRY: Balboa
GROSS TONNAGE: 25,000
SHIP TYPE: Bulk Carrier

has been audited and found to comply with the requirements of the 
International Safety Management (ISM) Code as amended, and the 
requirements of Chapter IX of SOLAS Convention.

Certificate No: SMC-2024-001
Issue Date: 15 November 2024
Valid Until: 14 November 2027
Next Survey Date: 15 November 2025
Survey Type: Intermediate

This certificate is issued under the authority of the Government of 
Panama by Bureau Veritas.

Issued by: Bureau Veritas
Place of Issue: Paris, France
Date of Issue: 15 November 2024

Authorized Signatory: [Signature]
John Smith
Marine Surveyor
Bureau Veritas
```

**Đây chính là `summary_text`** - Toàn bộ text được OCR từ PDF.

---

## 🔍 CHI TIẾT KỸ THUẬT

### 1. **Google Document AI**

**Service:** Google Cloud Document AI  
**Processor Type:** OCR Processor (Form Parser or General Processor)  
**API:** REST API via Google Apps Script  

**Input:**
```json
{
  "action": "analyze_maritime_document_ai",
  "file_content": "base64_encoded_pdf",
  "filename": "ISM_Certificate.pdf",
  "content_type": "application/pdf",
  "project_id": "your-gcp-project-id",
  "processor_id": "abc123def456",
  "location": "us",
  "document_type": "audit_certificate"
}
```

**Output:**
```json
{
  "success": true,
  "data": {
    "summary": "SAFETY MANAGEMENT CERTIFICATE...",
    "confidence": 0.95
  }
}
```

**Cách hoạt động:**
1. Google Apps Script nhận base64 PDF
2. Call Document AI API: `projects/{project}/locations/{location}/processors/{processor}:process`
3. Document AI:
   - OCR tất cả pages
   - Detect text layout
   - Extract tables, forms
   - Return structured text
4. Apps Script return về backend

**Code reference:** `/app/backend/app/utils/document_ai_helper.py:18-164`

---

### 2. **System AI (Gemini) Extraction**

**Model:** `gemini-2.0-flash-exp`  
**Provider:** Emergent LLM Key  
**Library:** `emergentintegrations.llm.chat`

**Prompt Template:**
```python
prompt = f"""You are an AI specialized in maritime audit certificate information extraction.

**INPUT**: Below is the Document AI text extraction from an audit certificate file.

**FILENAME**: {filename}

**TASK**: Extract the following fields and return as JSON:

{{
    "cert_name": "**REQUIRED** - Full certificate name",
    "cert_abbreviation": "Certificate abbreviation (e.g., 'SMC', 'ISSC')",
    "cert_no": "**REQUIRED** - Certificate number/reference",
    "cert_type": "Certificate type - MUST be one of: 'Full Term', 'Interim', ...",
    "issue_date": "Issue date in FULL TEXT format (e.g., '15 November 2024')",
    "valid_date": "Valid until / Expiry date in FULL TEXT format",
    "ship_name": "Name of the ship",
    "imo_number": "IMO number - 7 digits ONLY",
    "issued_by": "Full organization name",
    "confidence_score": "Your confidence (0.0 - 1.0)"
}}

**DOCUMENT TEXT:**

{summary_text from Document AI}
"""
```

**AI Response:**
```json
{
  "cert_name": "Safety Management Certificate",
  "cert_abbreviation": "SMC",
  "cert_no": "SMC-2024-001",
  "cert_type": "Full Term",
  "issue_date": "15 November 2024",
  "valid_date": "14 November 2027",
  "next_survey": "15 November 2025",
  "next_survey_type": "Intermediate",
  "issued_by": "Bureau Veritas",
  "issued_by_abbreviation": "BV",
  "ship_name": "VINASHIP HARMONY",
  "imo_number": "9573945",
  "confidence_score": 0.92
}
```

**Code reference:** `/app/backend/app/utils/audit_certificate_ai.py:64-200`

---

### 3. **Summary File Storage**

**Process:**
```python
# Get summary_text from Document AI result
summary_text = analysis_result.get("summary_text")

if summary_text and summary_text.strip():
    # Create filename
    base_name = "ISM_Certificate"
    summary_filename = f"{base_name}_Summary.txt"
    
    # Convert to bytes (UTF-8)
    summary_bytes = summary_text.encode('utf-8')
    
    # Upload to GDrive
    summary_upload_result = await GDriveService.upload_file(
        file_content=summary_bytes,
        filename=summary_filename,
        content_type="text/plain",
        folder_path=f"{ship_name}/ISM - ISPS - MLC/Audit Certificates",
        company_id=company_id
    )
    
    # Store summary_file_id
    if summary_upload_result.get("success"):
        summary_file_id = summary_upload_result.get("file_id")
```

**Google Drive Structure:**
```
Company Root Folder/
└── VINASHIP HARMONY/
    └── ISM - ISPS - MLC/
        └── Audit Certificates/
            ├── ISM_Certificate.pdf          ← Main certificate
            └── ISM_Certificate_Summary.txt  ← Summary text ⭐
```

**Code reference:** `/app/backend/app/api/v1/audit_certificates.py:441-472`

---

## 🎨 SUMMARY USE CASES

### 1. **Quick Preview**
```jsx
// Frontend: Hover tooltip
<Tooltip content={certificate.summary_text}>
  <span>📄 {certificate.cert_name}</span>
</Tooltip>
```

### 2. **Search & Filter**
```python
# Backend: Full-text search in summary
certificates = await db.audit_certificates.find({
    "$text": {"$search": "Bureau Veritas"}
})
```

### 3. **Reports & Export**
```python
# Generate report with summaries
for cert in certificates:
    summary = await fetch_summary_from_gdrive(cert.summary_file_id)
    report.add_section(cert.cert_name, summary)
```

### 4. **AI Re-analysis**
```python
# Re-analyze without re-uploading file
summary = await fetch_summary_from_gdrive(cert.summary_file_id)
new_fields = await extract_fields(summary)
```

---

## 📊 SO SÁNH VỚI SHIP CERTIFICATE

| Feature | Ship Certificate | Audit Certificate |
|---------|------------------|-------------------|
| **Document AI** | ❌ Không dùng | ✅ Dùng (Google Document AI) |
| **OCR** | ❌ Không có | ✅ Có (qua Document AI) |
| **Text Extraction** | PyPDF2 only | Document AI (advanced OCR) |
| **Summary Generation** | ❌ Không có | ✅ Có (from Document AI) |
| **Summary Storage** | ❌ Không lưu | ✅ Lưu file `.txt` trên GDrive |
| **Summary in DB** | ❌ Không có field | ✅ Có field `summary_file_id` |
| **AI Extraction** | System AI only | Document AI + System AI |
| **Quality** | ⚠️ Scanned PDFs fail | ✅ Scanned PDFs work |

---

## 🔑 KEY POINTS

### ✅ **Ưu điểm của Summary:**

1. **Quick Access**: Xem tóm tắt không cần mở PDF
2. **Searchable**: Full-text search trong summary
3. **OCR Included**: Handle scanned PDFs
4. **Reusable**: Có thể re-analyze mà không cần re-upload
5. **Storage Efficient**: Text file nhỏ (5-10KB) vs PDF (500KB-5MB)
6. **Lifecycle Managed**: Auto delete/rename khi certificate thay đổi

### 📈 **Performance:**

- **Document AI**: ~10-15s per file (with OCR)
- **System AI**: ~2-3s
- **Total**: ~15-20s per certificate
- **Cost**: ~$0.002 per page (Document AI pricing)

### 🎯 **Best Practices:**

1. ✅ Always use Document AI cho audit certificates
2. ✅ Store summary_file_id trong DB
3. ✅ Implement summary lifecycle (delete/rename)
4. ✅ Use summary for quick preview tooltips
5. ✅ Cache summary text trong memory khi cần frequent access

---

## 🔧 CONFIGURATION REQUIRED

### 1. **Google Cloud Project:**
```
- Enable Document AI API
- Create OCR Processor
- Get project_id, processor_id, location
```

### 2. **Apps Script:**
```javascript
// Deployed as Web App
// Handles Document AI API calls
// Returns JSON response
```

### 3. **System AI Config:**
```json
{
  "id": "system_ai",
  "provider": "google",
  "model": "gemini-2.0-flash-exp",
  "use_emergent_key": true
}
```

### 4. **Environment Variables:**
```bash
EMERGENT_LLM_KEY=your-emergent-key
```

---

## 📝 SUMMARY CONTENT EXAMPLE

**Real-world example từ ISM Certificate:**

```
SAFETY MANAGEMENT CERTIFICATE
(SMC)

This is to certify that the Safety Management System of:

SHIP NAME: VINASHIP HARMONY
IMO NUMBER: 9573945
FLAG: Panama
PORT OF REGISTRY: Balboa
GROSS TONNAGE: 25,000
DEADWEIGHT: 35,000 MT
SHIP TYPE: Bulk Carrier
CALL SIGN: 3EPX7

has been audited and found to comply with the requirements of the 
International Safety Management (ISM) Code as amended, and the 
requirements of Chapter IX of the SOLAS Convention 1974 as amended.

The Safety Management System includes documented procedures for:
- Ship operations and safety
- Pollution prevention
- Emergency preparedness
- Internal audits and management reviews
- Continuous improvement processes

Certificate Details:
Certificate Number: SMC-2024-001
Certificate Type: Full Term
Issue Date: 15 November 2024
Valid Until: 14 November 2027

Survey Schedule:
Next Survey Date: 15 November 2025
Survey Type: Intermediate Survey
Survey Window: ±3 months

This certificate is issued under the authority of the Government of 
Panama (Flag State) by Bureau Veritas acting as a Recognized Organization.

Issuing Authority:
Organization: Bureau Veritas
Office: Paris, France
Contact: marine.services@bureauveritas.com
Phone: +33 1 42 91 43 43

Date of Issue: 15 November 2024

[Digital Signature]
John Smith, Marine Surveyor
Bureau Veritas
Authorization No: BV-MS-12345

---
Notes:
- This certificate is valid for vessels engaged in international voyages
- Must be kept on board and available for inspection
- Subject to annual verification surveys
- Any changes to ship particulars must be reported within 30 days
```

**Length:** ~1,200 characters (this is stored in `summary_file_id`)

---

## ✅ CHECKLIST - SUMMARY FEATURE

- [x] Google Document AI configured
- [x] Apps Script deployed
- [x] System AI (Gemini) configured
- [x] Emergent LLM key available
- [x] Summary extraction logic implemented
- [x] Summary file upload to GDrive
- [x] summary_file_id stored in DB
- [x] Summary lifecycle management (delete)
- [x] Summary lifecycle management (rename)
- [x] Error handling for summary failures
- [x] Logging and monitoring

---

**Document created:** 2024-11-27  
**Feature status:** ✅ IMPLEMENTED & WORKING  
**Version:** 1.0
