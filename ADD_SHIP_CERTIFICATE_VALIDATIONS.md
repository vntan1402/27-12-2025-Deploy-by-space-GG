# 🔍 ADD SHIP CERTIFICATE - VALIDATIONS & CHECKS

## 📋 MỤC LỤC
1. [Frontend Validations](#frontend-validations)
2. [Backend Validations](#backend-validations)
3. [AI Analysis Checks](#ai-analysis-checks)
4. [Business Logic Checks](#business-logic-checks)
5. [Error Handling](#error-handling)

---

## 🎨 FRONTEND VALIDATIONS

### **1. Pre-Upload Checks (Before File Upload)**

#### **Check 1.1: Software Expiry Check**
**Location:** `AddShipCertificateModal.jsx:255`  
**Trigger:** User clicks upload button

```javascript
const { isSoftwareExpired, checkAndWarn } = useUploadGuard();

if (isSoftwareExpired) {
  toast.error('❌ Software expired. Please renew to upload certificates.');
  return; // Block upload
}
```

**Logic:**
- Check nếu software license đã expired
- **Action:** BLOCK upload nếu expired
- **User Feedback:** Toast error message

---

#### **Check 1.2: Ship Selection Check**
**Location:** `AddShipCertificateModal.jsx:260`  
**Trigger:** User clicks upload button

```javascript
if (!selectedShip?.id) {
  toast.error('❌ Vui lòng chọn tàu trước khi upload certificate');
  return; // Block upload
}
```

**Logic:**
- Kiểm tra có ship được chọn chưa
- **Action:** BLOCK upload nếu chưa chọn ship
- **User Feedback:** Toast error - yêu cầu chọn tàu

---

#### **Check 1.3: File Selection Check**
**Location:** `AddShipCertificateModal.jsx`  
**Trigger:** User selects files

```javascript
if (!files || files.length === 0) {
  toast.error('❌ Please select at least one file');
  return;
}
```

**Logic:**
- Kiểm tra có file nào được chọn không
- **Action:** BLOCK nếu không có file
- **User Feedback:** Toast error

---

### **2. Manual Entry Validations**

#### **Check 2.1: Certificate Name Required**
**Location:** `AddShipCertificateModal.jsx:900`  
**Trigger:** User submits manual entry form

```javascript
if (!certificateData.cert_name || !certificateData.cert_name.trim()) {
  toast.error('❌ Certificate name is required');
  return;
}
```

**Logic:**
- `cert_name` là required field
- **Action:** BLOCK submit nếu empty
- **User Feedback:** Toast error

---

## ⚙️ BACKEND VALIDATIONS

### **3. File Upload Validations**

#### **Check 3.1: File Type Validation**
**Location:** `ship_certificate_analyze_service.py:75`  
**Trigger:** Backend receives file

```python
supported_extensions = ['pdf', 'jpg', 'jpeg', 'png']
file_ext = filename.lower().split('.')[-1]

if file_ext not in supported_extensions:
    raise HTTPException(
        status_code=400,
        detail="Unsupported file type. Supported: PDF, JPG, PNG"
    )
```

**Logic:**
- Only accept: PDF, JPG, JPEG, PNG
- **Action:** REJECT file nếu không phải supported type
- **User Feedback:** 400 Error - "Unsupported file type"

---

#### **Check 3.2: File Size Validation**
**Location:** `ship_certificate_analyze_service.py:60`  
**Trigger:** After file decode

```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

if len(file_bytes) > MAX_FILE_SIZE:
    raise HTTPException(
        status_code=400,
        detail="File size exceeds 50MB limit"
    )
```

**Logic:**
- Maximum file size: 50MB
- **Action:** REJECT nếu file > 50MB
- **User Feedback:** 400 Error - "File size exceeds 50MB limit"

---

#### **Check 3.3: File Content Validation (Magic Bytes)**
**Location:** `ship_certificate_analyze_service.py:78-91`  
**Trigger:** After file type check

```python
# PDF Magic Bytes
if file_ext == 'pdf':
    if not file_bytes.startswith(b'%PDF'):
        raise HTTPException(400, "Invalid PDF file format")

# JPG Magic Bytes
elif file_ext in ['jpg', 'jpeg']:
    if not file_bytes.startswith(b'\xff\xd8\xff'):
        raise HTTPException(400, "Invalid JPG file format")

# PNG Magic Bytes
elif file_ext == 'png':
    if not file_bytes.startswith(b'\x89PNG'):
        raise HTTPException(400, "Invalid PNG file format")
```

**Logic:**
- Check file header (magic bytes) để verify file format
- Prevent file extension spoofing (e.g., `.exe` renamed to `.pdf`)
- **Action:** REJECT nếu magic bytes không match
- **User Feedback:** 400 Error - "Invalid {type} file format"

---

### **4. Configuration Validations**

#### **Check 4.1: Ship Exists**
**Location:** `ship_certificate_analyze_service.py:104`  
**Trigger:** Before analysis

```python
ship = await mongo_db.find_one("ships", {
    "id": ship_id, 
    "company": company_uuid
})

if not ship:
    raise HTTPException(status_code=404, detail="Ship not found")
```

**Logic:**
- Verify ship tồn tại trong database
- Verify ship thuộc đúng company
- **Action:** REJECT nếu không tìm thấy
- **User Feedback:** 404 Error - "Ship not found"

---

#### **Check 4.2: AI Configuration Check**
**Location:** `ship_certificate_analyze_service.py:114`  
**Trigger:** Before AI analysis

```python
ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})

if not ai_config_doc:
    raise HTTPException(
        status_code=404,
        detail="AI configuration not found. Please configure System AI in Settings."
    )
```

**Logic:**
- Check AI config tồn tại
- **Action:** REJECT nếu chưa configure
- **User Feedback:** 404 Error - yêu cầu configure AI

---

#### **Check 4.3: Document AI Enabled**
**Location:** `ship_certificate_analyze_service.py:120`  
**Trigger:** Before Document AI call

```python
document_ai_config = ai_config_doc.get("document_ai", {})

if not document_ai_config.get("enabled", False):
    raise HTTPException(
        status_code=400,
        detail="Google Document AI is not enabled in System Settings"
    )
```

**Logic:**
- Check Document AI được enable chưa
- **Action:** REJECT nếu disabled
- **User Feedback:** 400 Error - "Document AI not enabled"

---

#### **Check 4.4: Document AI Configuration Complete**
**Location:** `ship_certificate_analyze_service.py:125`  
**Trigger:** After enabled check

```python
required_fields = [
    document_ai_config.get("project_id"),
    document_ai_config.get("processor_id")
]

if not all(required_fields):
    raise HTTPException(
        status_code=400,
        detail="Incomplete Google Document AI configuration"
    )
```

**Logic:**
- Check `project_id` và `processor_id` có giá trị
- **Action:** REJECT nếu thiếu config
- **User Feedback:** 400 Error - "Incomplete configuration"

---

## 🤖 AI ANALYSIS CHECKS

### **5. Document AI Analysis**

#### **Check 5.1: PDF Page Count (Auto Split)**
**Location:** `ship_certificate_analyze_service.py:136`  
**Trigger:** For PDF files

```python
splitter = PDFSplitter(max_pages_per_chunk=12)
total_pages = splitter.get_page_count(file_bytes)
needs_split = splitter.needs_splitting(file_bytes)

if needs_split:
    # Process as large file (split into chunks)
    # Threshold: 15 pages
else:
    # Process as small file (single call)
```

**Logic:**
- Check số trang PDF
- Nếu > 15 pages → Split thành chunks (12 pages/chunk)
- Nếu ≤ 15 pages → Process trực tiếp
- **Action:** AUTO - không reject
- **Purpose:** Optimize Document AI processing

---

#### **Check 5.2: Document AI Text Extraction Success**
**Location:** `ship_certificate_analyze_service.py:194`  
**Trigger:** After Document AI call

```python
doc_ai_result = await analyze_document_with_document_ai(...)

if not doc_ai_result or not doc_ai_result.get("success"):
    error_msg = doc_ai_result.get("message", "Unknown error")
    raise HTTPException(
        status_code=400,
        detail=f"Document AI could not extract text from file: {error_msg}"
    )
```

**Logic:**
- Check Document AI có extract được text không
- **Action:** REJECT nếu extraction failed
- **User Feedback:** 400 Error với error message

---

#### **Check 5.3: Summary Text Not Empty**
**Location:** `ship_certificate_analyze_service.py:201`  
**Trigger:** After Document AI success

```python
summary_text = data.get("summary", "")

if not summary_text:
    raise HTTPException(
        status_code=400,
        detail="Document AI returned empty summary"
    )
```

**Logic:**
- Check summary text có nội dung
- **Action:** REJECT nếu empty
- **User Feedback:** 400 Error - "Empty summary"

---

### **6. System AI Field Extraction Checks**

#### **Check 6.1: Extraction Success**
**Location:** `ship_certificate_analyze_service.py:209`  
**Trigger:** After System AI call

```python
extracted_info = await extract_ship_certificate_fields_from_summary(...)

if not extracted_info:
    raise HTTPException(
        status_code=400,
        detail="Could not extract certificate information from document"
    )
```

**Logic:**
- Check System AI có extract được fields không
- **Action:** REJECT nếu extraction failed
- **User Feedback:** 400 Error

---

#### **Check 6.2: Critical Fields Present** (Implicit)
**Location:** `ship_certificate_ai.py:post_process_extracted_data()`  
**Trigger:** After AI extraction

```python
# Validate cert_type
if extracted_data.get('cert_type') not in VALID_CERTIFICATE_TYPES:
    logger.warning(f"Invalid cert_type, defaulting to 'Full Term'")
    extracted_data['cert_type'] = 'Full Term'

# Normalize IMO number
imo = str(extracted_data['imo_number']).replace(' ', '').replace('IMO', '')
if not (imo.isdigit() and len(imo) == 7):
    extracted_data['imo_number'] = None
```

**Logic:**
- Validate và normalize extracted data
- Fix invalid values
- **Action:** AUTO-FIX hoặc set to None
- **Purpose:** Data quality

---

## 🔐 BUSINESS LOGIC CHECKS

### **7. Ship Information Validation**

#### **Check 7.1: IMO Number Validation (BLOCKING)**
**Location:** `ship_certificate_analyze_service.py:validate_ship_info()`  
**Trigger:** After field extraction

```python
extracted_imo_clean = extracted_imo.replace(' ', '').replace('IMO', '').strip()
current_ship_imo_clean = current_ship_imo.strip()

if extracted_imo_clean and current_ship_imo:
    if extracted_imo_clean != current_ship_imo_clean:
        return {
            "is_blocking": True,
            "message": "Giấy chứng nhận của tàu khác, không thể lưu vào dữ liệu tàu hiện tại",
            "type": "imo_mismatch"
        }
```

**Logic:**
- So sánh IMO trong certificate với IMO của ship hiện tại
- Clean IMO (remove spaces, "IMO" prefix)
- Case-insensitive comparison
- **Action:** **BLOCK** upload nếu IMO không khớp
- **Reasoning:** Prevent uploading wrong ship's certificates
- **User Feedback:** Error status - "Certificate belongs to different ship"

---

#### **Check 7.2: Ship Name Validation (WARNING ONLY)**
**Location:** `ship_certificate_analyze_service.py:validate_ship_info()`  
**Trigger:** After IMO validation passes

```python
if extracted_ship_name_clean and current_ship_name:
    if extracted_ship_name_clean.upper() != current_ship_name.upper():
        return {
            "is_blocking": False,
            "message": "Tên tàu trong chứng chỉ khác với tàu hiện tại",
            "override_note": "Chỉ để tham khảo",
            "type": "ship_name_mismatch"
        }
```

**Logic:**
- So sánh ship name trong certificate với current ship
- Case-insensitive comparison
- **Action:** **WARNING only** - không block
- **Reasoning:** Ship name có thể thay đổi (renamed), nhưng IMO không đổi
- **User Feedback:** Certificate được tạo với note "Chỉ để tham khảo"

---

### **8. Duplicate Detection**

#### **Check 8.1: Duplicate by Certificate Number**
**Location:** `ship_certificate_analyze_service.py:check_duplicate()`  
**Trigger:** After validation checks

```python
if cert_no:
    existing_cert = await mongo_db.find_one("certificates", {
        "ship_id": ship_id,
        "cert_no": cert_no
    })
    
    if existing_cert:
        return {
            "has_duplicate": True,
            "message": f"Duplicate certificate number found: {cert_no}",
            "existing_certificate": {...}
        }
```

**Logic:**
- Search trong DB theo `ship_id` + `cert_no`
- **Action:** Return warning (không auto-block)
- **User Feedback:** Frontend shows DuplicateModal
  - Options: Skip / Replace / Keep Both
- **Purpose:** Prevent accidental duplicates

---

### **9. Google Drive Upload Validations**

#### **Check 9.1: GDrive Configuration Check**
**Location:** `certificate_multi_upload_service.py:629`  
**Trigger:** Before upload

```python
if not gdrive_config:
    raise Exception("Google Drive not configured for this company")

script_url = gdrive_config.get("web_app_url") or gdrive_config.get("apps_script_url")
if not script_url:
    raise Exception("Apps Script URL not configured")

parent_folder_id = gdrive_config.get("folder_id")
if not parent_folder_id:
    raise Exception("Parent folder ID not configured")
```

**Logic:**
- Check GDrive config tồn tại
- Check Apps Script URL
- Check parent folder ID
- **Action:** REJECT nếu thiếu config
- **User Feedback:** Error message

---

#### **Check 9.2: Upload Success Validation**
**Location:** `certificate_multi_upload_service.py:256`  
**Trigger:** After upload attempt

```python
upload_result = await _upload_to_gdrive(...)

if not upload_result.get("success"):
    return {
        "filename": file.filename,
        "status": "error",
        "message": f"Failed to upload to Google Drive: {upload_result.get('message')}"
    }
```

**Logic:**
- Check upload result từ Apps Script
- **Action:** Mark as error nếu upload failed
- **User Feedback:** Error trong BatchResultsModal
- **Retry:** User có thể retry failed uploads

---

## 📊 VALIDATION FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────┐
│                    USER UPLOADS FILE                    │
└─────────────────────────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │ FRONTEND           │                    │
    ▼                    │                    │
┌─────────┐              │                    │
│Software │ ──FAIL──> BLOCK                   │
│Expired? │              │                    │
└─────────┘              │                    │
    │PASS                │                    │
    ▼                    │                    │
┌─────────┐              │                    │
│ Ship    │ ──FAIL──> BLOCK                   │
│Selected?│              │                    │
└─────────┘              │                    │
    │PASS                │                    │
    ▼                    │                    │
┌─────────┐              │                    │
│Files    │ ──FAIL──> BLOCK                   │
│Present? │              │                    │
└─────────┘              │                    │
    │PASS                │                    │
    └────────────────────┘                    │
                         │                    │
    ┌────────────────────┘                    │
    │ BACKEND                                 │
    ▼                                         │
┌───────────┐                                 │
│File Type? │ ──UNSUPPORTED──> REJECT         │
└───────────┘                                 │
    │SUPPORTED                                │
    ▼                                         │
┌───────────┐                                 │
│File Size? │ ──>50MB──> REJECT               │
└───────────┘                                 │
    │≤50MB                                    │
    ▼                                         │
┌────────────┐                                │
│Magic Bytes?│ ──INVALID──> REJECT            │
└────────────┘                                │
    │VALID                                    │
    ▼                                         │
┌──────────┐                                  │
│AI Config?│ ──MISSING──> REJECT              │
└──────────┘                                  │
    │CONFIGURED                               │
    ▼                                         │
┌──────────────┐                              │
│Document AI   │ ──FAIL──> REJECT             │
│Extract Text? │                              │
└──────────────┘                              │
    │SUCCESS                                  │
    ▼                                         │
┌──────────────┐                              │
│System AI     │ ──FAIL──> REJECT             │
│Extract Fields│                              │
└──────────────┘                              │
    │SUCCESS                                  │
    ▼                                         │
┌──────────┐                                  │
│IMO Match?│ ──MISMATCH──> ⛔ BLOCK           │
└──────────┘                                  │
    │MATCH                                    │
    ▼                                         │
┌────────────┐                                │
│Ship Name   │ ──MISMATCH──> ⚠️ WARNING      │
│Match?      │              (Add note)        │
└────────────┘                                │
    │MATCH/WARNING                            │
    ▼                                         │
┌───────────┐                                 │
│Duplicate? │ ──FOUND──> 🔄 USER CHOICE       │
└───────────┘          (Skip/Replace/Keep)   │
    │NO DUPLICATE                             │
    ▼                                         │
┌─────────────┐                               │
│Upload to    │ ──FAIL──> ❌ ERROR            │
│Google Drive │                               │
└─────────────┘                               │
    │SUCCESS                                  │
    ▼                                         │
┌─────────────┐                               │
│Create DB    │                               │
│Record       │                               │
└─────────────┘                               │
    │                                         │
    ▼                                         │
┌─────────────┐                               │
│✅ SUCCESS   │                               │
└─────────────┘                               │
```

---

## 🎯 VALIDATION SUMMARY TABLE

| # | Check | Location | Type | Action | Severity |
|---|-------|----------|------|--------|----------|
| 1 | Software Expired | Frontend | Pre-upload | BLOCK | 🔴 CRITICAL |
| 2 | Ship Selected | Frontend | Pre-upload | BLOCK | 🔴 CRITICAL |
| 3 | Files Present | Frontend | Pre-upload | BLOCK | 🔴 CRITICAL |
| 4 | Cert Name (Manual) | Frontend | Form | BLOCK | 🔴 CRITICAL |
| 5 | File Type | Backend | Upload | REJECT | 🔴 CRITICAL |
| 6 | File Size | Backend | Upload | REJECT | 🔴 CRITICAL |
| 7 | Magic Bytes | Backend | Upload | REJECT | 🔴 CRITICAL |
| 8 | Ship Exists | Backend | Pre-analysis | REJECT | 🔴 CRITICAL |
| 9 | AI Config | Backend | Pre-analysis | REJECT | 🔴 CRITICAL |
| 10 | Document AI Enabled | Backend | Pre-analysis | REJECT | 🔴 CRITICAL |
| 11 | Document AI Config | Backend | Pre-analysis | REJECT | 🔴 CRITICAL |
| 12 | PDF Page Count | Backend | Analysis | AUTO-SPLIT | 🟢 INFO |
| 13 | Document AI Success | Backend | Analysis | REJECT | 🔴 CRITICAL |
| 14 | Summary Not Empty | Backend | Analysis | REJECT | 🔴 CRITICAL |
| 15 | Field Extraction | Backend | Analysis | REJECT | 🔴 CRITICAL |
| 16 | **IMO Match** | Backend | Validation | **⛔ BLOCK** | **🔴 BLOCKING** |
| 17 | Ship Name Match | Backend | Validation | ⚠️ WARNING | 🟡 WARNING |
| 18 | Duplicate Cert | Backend | Validation | 🔄 USER CHOICE | 🟡 WARNING |
| 19 | GDrive Config | Backend | Upload | REJECT | 🔴 CRITICAL |
| 20 | GDrive Upload | Backend | Upload | ERROR | 🔴 CRITICAL |

---

## 🚨 ERROR SEVERITY LEVELS

### 🔴 **CRITICAL (Blocking)**
- Completely prevent upload/creation
- User cannot proceed
- Examples: Software expired, Invalid file type, IMO mismatch

### 🟡 **WARNING (Non-blocking)**
- Allow upload with note/warning
- User can proceed
- Examples: Ship name mismatch

### 🟢 **INFO (Auto-handled)**
- System handles automatically
- No user action needed
- Examples: PDF splitting, Date format normalization

### 🔄 **USER CHOICE**
- Require user decision
- Multiple options available
- Examples: Duplicate handling (Skip/Replace/Keep)

---

## 💡 KEY INSIGHTS

### **1. Defense in Depth**
- Multiple layers of validation (Frontend → Backend → AI → Business Logic)
- Each layer catches different types of errors

### **2. IMO as Primary Key**
- IMO validation is **BLOCKING**
- Ship name validation is WARNING only
- **Reasoning:** IMO never changes, name can change

### **3. User Flexibility**
- Duplicates → User choice
- Ship name mismatch → Warning but allow
- Failed files → Retry option

### **4. Data Quality**
- Magic bytes check prevents spoofing
- AI confidence scoring
- Field normalization (dates, IMO format)

### **5. Configuration Dependencies**
- Requires: AI config, Document AI, Google Drive
- Early validation prevents wasted processing

---

**Document created:** 2024-11-27  
**Version:** 1.0  
**Total Checks:** 20+
