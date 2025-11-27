# 📋 FLOW CHI TIẾT: ADD SHIP CERTIFICATE (CLASS & FLAG CERT)

## 📚 MỤC LỤC
1. [Tổng quan](#tổng-quan)
2. [Frontend Flow](#frontend-flow)
3. [Backend Flow](#backend-flow)
4. [Các trường hợp đặc biệt](#các-trường-hợp-đặc-biệt)
5. [Database Operations](#database-operations)
6. [Error Handling](#error-handling)

---

## 🎯 TỔNG QUAN

**Module:** CLASS & FLAG CERT  
**Feature:** Add Ship Certificate  
**Endpoint chính:** `POST /api/certificates/multi-upload`  
**Component chính:** `AddShipCertificateModal.jsx`  
**Service:** `CertificateMultiUploadService`

### Các phương thức upload:
1. **Multi-file upload** (có AI analysis)
2. **Single manual entry** (nhập tay qua form)

---

## 🎨 FRONTEND FLOW

### 📍 Entry Point
- **File:** `/app/frontend/src/components/ShipCertificates/AddShipCertificateModal.jsx`
- **Trigger:** User clicks "Thêm chứng chỉ" button từ trang Certificates

### 🔄 Flow Steps

#### STEP 1: Mở Modal
```
User clicks "Thêm chứng chỉ"
  ↓
AddShipCertificateModal mở
  ↓
Check: selectedShip có được chọn chưa?
  ├─ Có → Cho phép upload
  └─ Không → Hiển thị warning & ship selector dropdown
```

#### STEP 2: User chọn phương thức

##### A. **MULTI-FILE UPLOAD (Có AI Analysis)**

```
User drag & drop hoặc chọn nhiều files
  ↓
handleMultiCertUpload() được trigger
  ↓
CHECK 1: Software expired?
  ├─ Có → Chặn & warning
  └─ Không → Continue
  ↓
CHECK 2: selectedShip có ID?
  ├─ Không → Error toast
  └─ Có → Continue
  ↓
Initialize tracking states:
  - fileStatusMap: { filename: 'waiting' }
  - fileProgressMap: { filename: 0 }
  - fileSubStatusMap: { filename: '' }
  - fileObjectsMap: { filename: File object }
  ↓
Show BatchProcessingModal (để user theo dõi progress)
  ↓
FOR EACH FILE (với delay 3s giữa mỗi file):
  ↓
  Update status: 'processing'
  ↓
  Create FormData & append file
  ↓
  POST /api/certificates/multi-upload?ship_id={ship_id}
  ↓
  BACKEND PROCESSING (xem Backend Flow)
  ↓
  Receive response:
    ├─ SUCCESS (status: 'success' hoặc 'completed')
    │   ├─ Update fileStatusMap → 'completed'
    │   ├─ Update progress → 100%
    │   ├─ Extract thông tin từ extracted_info
    │   └─ Lưu vào results array
    │
    ├─ ERROR (status: 'error')
    │   ├─ Update fileStatusMap → 'error'
    │   ├─ Lưu error message
    │   └─ Cho phép retry sau
    │
    ├─ REQUIRES_MANUAL_INPUT
    │   ├─ AI không extract đủ thông tin
    │   ├─ Show warning
    │   └─ User phải nhập manual
    │
    ├─ DUPLICATE_DETECTED
    │   ├─ Show DuplicateShipCertificateModal
    │   ├─ User chọn: Skip / Replace / Keep Both
    │   └─ Call /api/ships/{ship_id}/certificates/resolve-duplicate
    │
    └─ SHIP_NAME_MISMATCH
        ├─ Show ShipNameMismatchModal
        ├─ Warning: tên tàu không khớp
        └─ User xác nhận có muốn continue không
  ↓
END LOOP
  ↓
Close BatchProcessingModal
  ↓
Show BatchResultsModal với summary:
  - Tổng số files
  - Thành công: X files
  - Thất bại: Y files
  - Chi tiết từng file
  ↓
User có thể:
  - Retry failed files
  - Close modal
  - View details
```

**Key Functions:**
- `handleMultiCertUpload(files)` - Main orchestrator
- `handleRetryFailedFile(filename)` - Retry mechanism
- `handleDuplicateResolution(action)` - Xử lý duplicate

##### B. **MANUAL ENTRY (Nhập tay qua form)**

```
User điền form thủ công:
  - Certificate Name *
  - Certificate Abbreviation
  - Certificate No
  - Type (Full Term / Short Term / Interim)
  - Issue Date
  - Valid Date
  - Last Endorse Date
  - Next Survey Date
  - Next Survey Type
  - Issued By
  - Issued By Abbreviation
  - Notes
  ↓
User clicks "Thêm" button
  ↓
handleSubmit() được trigger
  ↓
VALIDATION:
  ├─ selectedShip có ID? → Không → Error
  └─ cert_name có giá trị? → Không → Error
  ↓
Convert dates sang UTC format
  ↓
POST /api/certificates
  ↓
Response:
  ├─ SUCCESS → Toast success, reset form, close modal, refresh list
  └─ ERROR → Toast error message
```

---

## ⚙️ BACKEND FLOW

### 📍 Entry Point
- **File:** `/app/backend/app/api/v1/certificates.py`
- **Endpoint:** `POST /api/certificates/multi-upload`

### 🔄 Processing Flow

```
REQUEST arrives at /api/certificates/multi-upload
  ↓
Parameters:
  - ship_id: str (query param)
  - files: List[UploadFile]
  - current_user: UserResponse (from auth)
  ↓
Delegate to CertificateMultiUploadService.process_multi_upload()
  ↓

═══════════════════════════════════════════════════════════
STEP 1: VERIFICATION & SETUP
═══════════════════════════════════════════════════════════
  ↓
1.1 Verify ship exists
    SELECT * FROM ships WHERE id = ship_id
    ├─ Không tồn tại → 404 Error
    └─ Tồn tại → Continue
  ↓
1.2 Get AI Configuration
    SELECT * FROM ai_configs WHERE user_id = current_user.id
    Config:
      - provider: (e.g., "openai")
      - model: (e.g., "gpt-5")
      - api_key: EMERGENT_LLM_KEY
    ├─ Không có config → 500 Error
    └─ Có config → Continue
  ↓
1.3 Get Google Drive Configuration
    SELECT * FROM company_gdrive_config 
    WHERE company_id = user_company_id
    ├─ Không có config → 500 Error
    └─ Có config → Continue
  ↓

═══════════════════════════════════════════════════════════
STEP 2: PROCESS EACH FILE
═══════════════════════════════════════════════════════════
FOR EACH file IN files:
  ↓
  _process_single_file(file):
    ↓
    2.1 Read file content
        file_content = await file.read()
    ↓
    2.2 VALIDATION
        ├─ File size > 50MB? → Error
        ├─ File type not in [PDF, JPG, PNG]? → Error
        └─ Valid → Continue
    ↓
    2.3 AI ANALYSIS
        _analyze_document_with_ai():
          ↓
          Convert file_content to base64
          ↓
          Call AI API với prompt:
            "Analyze this certificate and extract:
             - cert_name, cert_no, issue_date, valid_date
             - imo_number, ship_name
             - issued_by, category
             - confidence_score for each field"
          ↓
          Parse AI response (JSON format)
          ↓
          Return analysis_result {
            cert_name: str
            cert_no: str
            issue_date: str (DD/MM/YYYY)
            valid_date: str (DD/MM/YYYY)
            imo_number: str
            ship_name: str
            issued_by: str
            category: "certificates" | "other"
            confidence_score: float (0.0-1.0)
          }
    ↓
    2.4 AI EXTRACTION QUALITY CHECK
        _check_ai_extraction_quality():
          ↓
          Calculate:
            - confidence_score (average của các field)
            - critical_extraction_rate (bao nhiêu % critical fields được extract)
          ↓
          Critical fields: [cert_name, issue_date, valid_date]
          ↓
          DECISION:
            ├─ confidence < 0.5 OR critical_rate < 0.67
            │   → return { sufficient: False }
            │   → Frontend sẽ require manual input
            │
            └─ OK → return { sufficient: True }
    ↓
    2.5 CATEGORY VALIDATION
        ├─ category != "certificates"?
        │   → Return "requires_manual_review"
        │   → Không phải marine certificate
        └─ category == "certificates" → Continue
    ↓
    2.6 IMO & SHIP NAME VALIDATION
        Extract:
          - extracted_imo from AI result
          - current_ship_imo from ship record
        ↓
        Clean & compare (remove spaces, "IMO" prefix):
          ├─ IMO MISMATCH (extracted_imo != current_ship_imo)
          │   → Return ERROR
          │   → "Giấy chứng nhận của tàu khác"
          │   → Frontend block upload
          │
          ├─ IMO MATCH + Ship name mismatch
          │   → Add validation_note: "Chỉ để tham khảo"
          │   → Continue but warn user
          │
          └─ Both match → Continue
    ↓
    2.7 DUPLICATE CHECK
        _check_certificate_duplicates():
          ↓
          Query existing certificates trong DB:
            SELECT * FROM certificates 
            WHERE ship_id = ship_id
            AND (
              cert_no = extracted_cert_no 
              OR (cert_name = extracted_cert_name 
                  AND issue_date ≈ extracted_issue_date)
            )
          ↓
          FOUND DUPLICATES?
            ├─ Yes → Return "pending_duplicate_resolution"
            │         Frontend show modal cho user chọn
            └─ No → Continue
    ↓
    2.8 UPLOAD TO GOOGLE DRIVE
        _upload_to_google_drive():
          ↓
          Encode file_content to base64
          ↓
          Call Google Drive Apps Script API:
            POST {gdrive_config.script_url}
            Body: {
              data: base64_content,
              filename: "original_filename.pdf",
              folderId: gdrive_config.certificates_folder_id,
              mimeType: file.content_type
            }
          ↓
          Response: {
            fileId: "1abc...",
            fileUrl: "https://drive.google.com/..."
          }
          ↓
          Save to DB.files collection:
            {
              id: uuid,
              file_id: gdrive_fileId,
              original_name: filename,
              file_url: gdrive_fileUrl,
              folder: "certificates",
              uploaded_by: current_user.username,
              uploaded_at: datetime.now()
            }
    ↓
    2.9 CREATE CERTIFICATE RECORD
        Prepare certificate data:
          {
            id: uuid,
            ship_id: ship_id,
            cert_name: analysis.cert_name,
            cert_abbreviation: "",
            cert_no: analysis.cert_no,
            cert_type: "Full Term",
            issue_date: convert_to_utc(analysis.issue_date),
            valid_date: convert_to_utc(analysis.valid_date),
            issued_by: analysis.issued_by,
            file_id: uploaded_file_id,
            category: "certificates",
            validation_note: validation_note (if any),
            created_by: current_user.username,
            created_at: datetime.now(),
            updated_at: datetime.now()
          }
        ↓
        INSERT INTO certificates
        ↓
        Return SUCCESS result:
          {
            filename: file.filename,
            status: "success",
            certificate: certificate_data,
            analysis: analysis_result,
            extracted_info: { ... }
          }
  ↓
END LOOP

═══════════════════════════════════════════════════════════
STEP 3: RETURN RESPONSE
═══════════════════════════════════════════════════════════
  ↓
Aggregate all results:
  {
    results: [
      { filename, status, certificate, analysis, ... }
    ],
    summary: {
      total_files: N,
      successfully_created: X,
      errors: Y,
      marine_certificates: M,
      non_marine_files: O,
      certificates_created: [...],
      error_files: [...]
    },
    ship: {
      id: ship_id,
      name: ship_name
    }
  }
  ↓
Return to Frontend
```

---

## 🔀 CÁC TRƯỜNG HỢP ĐẶC BIỆT

### 1. 🔄 DUPLICATE RESOLUTION

**Khi nào xảy ra:**
- AI extract cert_no trùng với certificate đã tồn tại
- Hoặc: (cert_name + issue_date) trùng

**Flow:**
```
Backend phát hiện duplicate
  ↓
Return status: "pending_duplicate_resolution"
  ↓
Frontend show DuplicateShipCertificateModal
  ↓
User chọn 1 trong 3 options:
  ├─ SKIP: Bỏ qua file này
  ├─ REPLACE: Xóa certificate cũ, thay bằng mới
  └─ KEEP_BOTH: Giữ cả 2 (thêm suffix vào tên)
  ↓
Call API: POST /api/ships/{ship_id}/certificates/resolve-duplicate
  Body: {
    file_id: uploaded_file_id,
    action: "skip" | "replace" | "keep_both",
    analysis: analysis_result
  }
  ↓
Backend xử lý theo action
  ↓
Frontend auto-fill form với data từ analysis
```

### 2. ⚠️ SHIP NAME MISMATCH

**Khi nào xảy ra:**
- IMO number khớp
- Nhưng Ship name trong certificate ≠ Ship name trong DB

**Flow:**
```
Backend phát hiện mismatch
  ↓
Add validation_note: "Chỉ để tham khảo"
  ↓
Set progress_message cho user
  ↓
Certificate vẫn được tạo nhưng có note
  ↓
Frontend hiển thị warning icon/badge
```

### 3. ❌ IMO MISMATCH (BLOCKING)

**Khi nào xảy ra:**
- extracted_imo ≠ current_ship_imo

**Flow:**
```
Backend phát hiện IMO không khớp
  ↓
Return status: "error"
  ↓
message: "Giấy chứng nhận của tàu khác, không thể lưu..."
  ↓
Frontend:
  - Hiển thị error trong BatchResultsModal
  - Không cho phép upload certificate này
  - User phải chọn đúng tàu
```

### 4. 🤖 AI EXTRACTION INSUFFICIENT

**Khi nào xảy ra:**
- AI confidence score < 0.5
- Hoặc: Critical fields extraction rate < 67%

**Flow:**
```
Backend check AI quality
  ↓
Insufficient → Return status: "requires_manual_input"
  ↓
Frontend:
  - Hiển thị warning
  - File vẫn được upload lên GDrive
  - Nhưng certificate record chưa được tạo
  - User phải điền form manual để tạo certificate
```

### 5. 🔁 RETRY FAILED FILES

**Flow:**
```
User clicks "Retry" button trong BatchResultsModal
  ↓
handleRetryFailedFile(filename)
  ↓
Get original File object từ fileObjectsMap
  ↓
Show BatchProcessingModal (minimized mode)
  ↓
Re-upload SAME file
  ↓
POST /api/certificates/multi-upload (lại từ đầu)
  ↓
Update BatchResultsModal với kết quả mới
```

---

## 💾 DATABASE OPERATIONS

### Collections được sử dụng:

#### 1. **ships**
```json
{
  "id": "ship-uuid",
  "name": "VINASHIP HARMONY",
  "imo": "9573945",
  "flag": "Panama",
  "company": "company-id",
  ...
}
```

#### 2. **certificates**
```json
{
  "id": "cert-uuid",
  "ship_id": "ship-uuid",
  "cert_name": "Class Certificate",
  "cert_abbreviation": "CC",
  "cert_no": "ABC123456",
  "cert_type": "Full Term",
  "issue_date": "2024-01-15T00:00:00Z",
  "valid_date": "2029-01-15T00:00:00Z",
  "last_endorse": null,
  "next_survey": "2025-01-15T00:00:00Z",
  "next_survey_type": "Annual",
  "issued_by": "DNV",
  "issued_by_abbreviation": "DNV",
  "file_id": "file-uuid",
  "category": "certificates",
  "sensitivity_level": "internal",
  "notes": "",
  "validation_note": "Chỉ để tham khảo",
  "created_by": "admin1",
  "created_at": "2024-11-27T...",
  "updated_at": "2024-11-27T...",
  "_id": ObjectId("...")
}
```

#### 3. **files**
```json
{
  "id": "file-uuid",
  "file_id": "google-drive-file-id",
  "original_name": "certificate.pdf",
  "file_url": "https://drive.google.com/file/d/...",
  "folder": "certificates",
  "uploaded_by": "admin1",
  "uploaded_at": "2024-11-27T...",
  "_id": ObjectId("...")
}
```

#### 4. **ai_configs**
```json
{
  "user_id": "user-uuid",
  "provider": "openai",
  "model": "gpt-5",
  "created_at": "...",
  "_id": ObjectId("...")
}
```

#### 5. **company_gdrive_config**
```json
{
  "company_id": "company-id",
  "script_url": "https://script.google.com/...",
  "certificates_folder_id": "gdrive-folder-id",
  "audit_certificates_folder_id": "...",
  ...
}
```

---

## 🚨 ERROR HANDLING

### Frontend Errors:

| Error | Trigger | User Action |
|-------|---------|-------------|
| "Software expired" | isSoftwareExpired = true | Contact admin để renew |
| "No ship selected" | selectedShip = null | Chọn tàu trước khi upload |
| "Certificate name required" | cert_name empty | Điền tên certificate |
| "Upload failed" | Network/Server error | Retry hoặc check logs |

### Backend Errors:

| Status Code | Reason | Message |
|-------------|--------|---------|
| 404 | Ship not found | "Ship not found" |
| 500 | AI config not found | "AI configuration not found. Please configure AI settings first." |
| 500 | GDrive not configured | "Google Drive not configured. Please configure Google Drive first." |
| 400 | File too large | "File size exceeds 50MB limit" |
| 400 | Unsupported file type | "Unsupported file type. Supported: PDF, JPG, PNG" |

---

## 📊 FLOW DIAGRAM (Simplified)

```
┌─────────────────────────────────────────────────────────────────┐
│                     ADD SHIP CERTIFICATE                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├───────────────────┬──────────────────┐
                              │                   │                  │
                        ┌─────▼──────┐     ┌─────▼─────┐    ┌──────▼──────┐
                        │ Multi-File │     │  Single   │    │   Manual    │
                        │   Upload   │     │  w/ AI    │    │    Entry    │
                        └─────┬──────┘     └─────┬─────┘    └──────┬──────┘
                              │                   │                  │
                    ┌─────────▼───────────┐       │                  │
                    │  AI Analysis Loop   │◄──────┘                  │
                    │  (Each file 3s)     │                          │
                    └─────────┬───────────┘                          │
                              │                                      │
            ┌─────────────────┼─────────────────────┐                │
            │                 │                     │                │
      ┌─────▼─────┐    ┌─────▼─────┐       ┌──────▼──────┐          │
      │ Duplicate │    │ IMO Check │       │   Quality   │          │
      │   Check   │    │  (Block)  │       │    Check    │          │
      └─────┬─────┘    └─────┬─────┘       └──────┬──────┘          │
            │                │                     │                │
            └────────────────┼─────────────────────┘                │
                             │                                      │
                    ┌────────▼────────┐                             │
                    │ Upload to GDrive│                             │
                    └────────┬────────┘                             │
                             │                                      │
                    ┌────────▼────────┐                             │
                    │  Create Cert    │◄────────────────────────────┘
                    │   in MongoDB    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Return Success │
                    │  + Analysis Data│
                    └─────────────────┘
```

---

## ✅ CHECKLIST - FLOW HOÀN CHỈNH

- [x] User authentication & authorization
- [x] Ship selection validation
- [x] Software expiry check
- [x] File type & size validation
- [x] AI configuration check
- [x] Google Drive configuration check
- [x] AI document analysis (cert extraction)
- [x] AI extraction quality check
- [x] Category classification (marine vs non-marine)
- [x] IMO number validation (blocking)
- [x] Ship name validation (warning only)
- [x] Duplicate detection & resolution
- [x] Google Drive upload
- [x] Certificate record creation
- [x] Multi-file parallel processing (with 3s delay)
- [x] Progress tracking & UI updates
- [x] Batch results display
- [x] Retry mechanism for failed files
- [x] Manual entry fallback
- [x] Error handling & user feedback
- [x] Success confirmation & list refresh

---

## 🎓 KEY TAKEAWAYS

1. **AI-Driven**: Flow chủ yếu dựa vào AI để extract thông tin từ certificate files
2. **Quality Gates**: Nhiều bước validation để đảm bảo data quality
3. **User Flexibility**: Cung cấp cả automated (AI) và manual options
4. **Error Recovery**: Retry mechanism cho failed uploads
5. **Duplicate Handling**: User có quyền quyết định khi phát hiện duplicate
6. **IMO Validation**: Critical check - block upload nếu IMO không khớp
7. **Progress Tracking**: Real-time UI updates để user theo dõi quá trình upload

---

**Document created:** 2024-11-27  
**Last updated:** 2024-11-27  
**Version:** 1.0
