# 📊 SO SÁNH: ADD SHIP CERTIFICATE vs ADD AUDIT CERTIFICATE

## 🎯 TỔNG QUAN

Cả hai flows đều sử dụng AI để extract thông tin từ certificate files, nhưng có những điểm khác biệt quan trọng về:
- **Mục đích sử dụng**
- **Validation logic**
- **Storage location**
- **Summary generation**
- **Data models**

---

## 📋 BẢNG SO SÁNH TỔNG QUÁT

| Tiêu chí | Ship Certificate (CLASS & FLAG) | Audit Certificate (ISM/ISPS/MLC) |
|----------|--------------------------------|----------------------------------|
| **Module** | Class & Flag Cert | ISM - ISPS - MLC |
| **Loại certificate** | Class certificates, Flag certificates (SOLAS, MARPOL, Load Line, etc.) | Audit certificates (ISM, ISPS, MLC, CICA) |
| **Frontend Component** | `AddShipCertificateModal.jsx` | `AddAuditCertificateModal.jsx` |
| **Backend Endpoint** | `POST /api/certificates/multi-upload` | `POST /api/ships/{ship_id}/audit-certificates/multi-upload` |
| **Service** | `CertificateMultiUploadService` | Direct trong `audit_certificates.py` |
| **GDrive Folder** | `{ShipName}/Class & Flag/Certificates` | `{ShipName}/ISM - ISPS - MLC/Audit Certificates` |
| **Summary Generation** | ❌ KHÔNG có | ✅ CÓ - AI tạo summary text |
| **Summary Storage** | ❌ KHÔNG | ✅ CÓ - Upload file `_Summary.txt` |

---

## 🔍 SO SÁNH CHI TIẾT

### 1. 📂 DATA MODEL

#### Ship Certificate:
```json
{
  "id": "cert-uuid",
  "ship_id": "ship-uuid",
  "cert_name": "Cargo Ship Safety Construction Certificate",
  "cert_abbreviation": "CSSC",
  "cert_no": "ABC123456",
  "cert_type": "Full Term",
  "issue_date": "2024-01-15T00:00:00Z",
  "valid_date": "2029-01-15T00:00:00Z",
  "last_endorse": null,
  "next_survey": "2025-01-15T00:00:00Z",
  "next_survey_type": "Annual",
  "issued_by": "DNV",
  "issued_by_abbreviation": "DNV",
  "file_id": "gdrive-file-id",
  "category": "certificates",
  "sensitivity_level": "internal",
  "notes": "",
  "validation_note": "Chỉ để tham khảo",
  "created_by": "admin1",
  "created_at": "...",
  "updated_at": "..."
}
```

#### Audit Certificate:
```json
{
  "id": "cert-uuid",
  "ship_id": "ship-uuid",
  "cert_name": "ISM Certificate",
  "cert_abbreviation": "ISM",
  "cert_no": "ISM-2024-001",
  "cert_type": "Full Term",
  "issue_date": "2024-01-15T00:00:00Z",
  "valid_date": "2027-01-15T00:00:00Z",
  "last_endorse": null,
  "next_survey_date": "2025-01-15T00:00:00Z",
  "next_survey_window": "±3M",
  "next_survey_type": "Annual",
  "issued_by": "Class NK",
  "issued_by_abbreviation": "NK",
  "extracted_ship_name": "VINASHIP HARMONY",  // ⭐ AI extracted
  "google_drive_file_id": "gdrive-file-id",
  "summary_file_id": "gdrive-summary-file-id",  // ⭐ NEW
  "file_name": "ISM_Certificate.pdf",
  "notes": "",
  "has_notes": false,
  "company": "company-id",
  "created_at": "...",
  "updated_at": "..."
}
```

**Điểm khác biệt:**
- ✅ Audit: có `summary_file_id` để lưu AI summary
- ✅ Audit: có `extracted_ship_name` (ship name từ AI)
- ✅ Audit: có `next_survey_window` (±3M, ±6M, etc.)
- ✅ Audit: có `has_notes` (boolean flag)
- ❌ Ship: không có summary fields
- ❌ Ship: có `sensitivity_level` (Audit không có)

---

### 2. 🤖 AI ANALYSIS PROCESS

#### Ship Certificate:
```
File Upload
  ↓
PDFProcessor.extract_text_from_pdf()  // ❌ KHÔNG có OCR fallback
  ↓
Check: text < 50 chars?
  ├─ Yes → Return "unknown", require manual
  └─ No → Continue
  ↓
Call AI với prompt: Extract cert info
  ↓
AI returns: {
  cert_name, cert_no, dates,
  imo_number, ship_name,
  issued_by, confidence
}
  ↓
Quality check: confidence + critical fields
  ↓
Return extracted info
```

#### Audit Certificate:
```
File Upload
  ↓
PDFProcessor.process_pdf(use_ocr_fallback=True)  // ✅ CÓ OCR
  ↓
Check: text < 50 chars?
  ├─ Yes → Return error
  └─ No → Continue
  ↓
Call AI với prompt: Extract cert info + GENERATE SUMMARY
  ↓
AI returns: {
  cert_name, cert_no, dates,
  imo_number, ship_name,
  issued_by, confidence,
  summary_text  // ⭐ NEW - AI generated summary
}
  ↓
Quality check: confidence + critical fields
  ↓
Return extracted info + summary
```

**Điểm khác biệt:**
- ✅ Audit: CÓ OCR fallback → Handle scanned PDFs
- ❌ Ship: KHÔNG có OCR → Scanned PDFs fail
- ✅ Audit: AI tạo summary text (2-3 câu tóm tắt)
- ❌ Ship: Không có summary

---

### 3. 📝 SUMMARY GENERATION & STORAGE

#### Ship Certificate:
```
❌ KHÔNG CÓ SUMMARY FEATURE
```

#### Audit Certificate:
```
AI Analysis
  ↓
AI generates summary_text:
  "This is an ISM Certificate issued by Class NK 
   for vessel VINASHIP HARMONY (IMO 9573945).
   Valid from 15/01/2024 to 14/01/2027."
  ↓
Upload main certificate → GDrive
  ↓
Upload summary file:
  - Filename: {original_name}_Summary.txt
  - Content: summary_text (UTF-8)
  - Location: Same folder as certificate
  - Store summary_file_id in DB
  ↓
SUCCESS: Both files uploaded
```

**Lợi ích của Summary:**
1. ✅ Quick overview không cần mở file PDF
2. ✅ Searchable text content
3. ✅ Easy to display in UI tooltips
4. ✅ Can be used for reports

---

### 4. 🔐 VALIDATION LOGIC

#### Ship Certificate:

```python
# IMO Validation (BLOCKING)
if extracted_imo != current_ship_imo:
    → REJECT - "Giấy chứng nhận của tàu khác"
    → Status: "error"

# Ship Name Validation (WARNING)
if extracted_ship_name != current_ship_name:
    → WARNING - "Chỉ để tham khảo"
    → Add validation_note
    → Still create certificate

# Category Validation
if category != "certificates":
    → Status: "requires_manual_review"
```

#### Audit Certificate:

```python
# Category Validation (ISM/ISPS/MLC/CICA) - STRICT
category_keywords = {
    "ism": ["International Safety Management", "ISM Code"],
    "isps": ["International Ship and Port Facility Security", "ISPS Code"],
    "mlc": ["Maritime Labour Convention", "MLC 2006"],
    "cica": ["Continuous Synopsis Record", "CSR"]
}

if cert_name not in expected_categories:
    → REJECT - "Không phải ISM/ISPS/MLC certificate"
    → Status: "error"
    → category_mismatch: true

# IMO Validation (BLOCKING)
if extracted_imo != current_ship_imo:
    → REJECT - "Giấy chứng nhận của tàu khác"
    → Status: "error"
    → validation_error

# Ship Name Validation (WARNING)
if extracted_ship_name != current_ship_name:
    → WARNING - "Chỉ để tham khảo"
    → Add validation_note
    → Still create certificate
```

**Điểm khác biệt:**
- ✅ Audit: STRICT category validation (ISM/ISPS/MLC only)
- ❌ Ship: Loose category validation (any marine certificate)
- ✅ Audit: Store extracted_ship_name cho reference
- ❌ Ship: Không lưu extracted ship name

---

### 5. 📁 GOOGLE DRIVE STORAGE

#### Ship Certificate:
```
Root: Company Folder
  └─ {Ship Name}/
      └─ Class & Flag/
          └─ Certificates/
              └─ certificate.pdf
```

#### Audit Certificate:
```
Root: Company Folder
  └─ {Ship Name}/
      └─ ISM - ISPS - MLC/
          └─ Audit Certificates/
              ├─ ISM_Certificate.pdf
              └─ ISM_Certificate_Summary.txt  // ⭐ Summary file
```

**Điểm khác biệt:**
- Audit: Lưu 2 files (PDF + Summary TXT)
- Ship: Chỉ lưu 1 file (PDF)
- Folder structure khác nhau

---

### 6. 🔄 MULTI-UPLOAD FLOW

#### Ship Certificate:
```
FOR EACH file (with 3s delay):
  ↓
  1. Upload file
  2. AI analysis (NO OCR)
  3. Quality check
  4. IMO validation
  5. Duplicate check
  6. Upload to GDrive
  7. Create certificate record
  ↓
  Result status:
    - success
    - error
    - requires_manual_input
    - pending_duplicate_resolution
    - requires_manual_review
```

#### Audit Certificate:
```
FOR EACH file:
  ↓
  1. Upload file
  2. AI analysis (WITH OCR + SUMMARY)
  3. Quality check
  4. Category validation (ISM/ISPS/MLC)
  5. IMO validation
  6. Duplicate check
  7. Upload PDF to GDrive
  8. Upload SUMMARY to GDrive  // ⭐ Extra step
  9. Create certificate record with summary_file_id
  ↓
  Result status:
    - success
    - error
    - pending_duplicate_resolution
    - category_mismatch  // ⭐ New status
    - validation_error
```

**Điểm khác biệt:**
- ✅ Audit: 2 GDrive uploads per file (PDF + Summary)
- ❌ Ship: 1 GDrive upload per file (PDF only)
- ✅ Audit: Thêm category validation step
- ✅ Audit: có OCR cho scanned PDFs

---

### 7. 📊 FRONTEND UI DIFFERENCES

#### Ship Certificate Modal:
```jsx
// File: AddShipCertificateModal.jsx

Features:
- Ship selector dropdown (hover to show)
- Single/Multi file upload
- Duplicate resolution modal
- Ship name mismatch modal
- Batch processing modal
- Batch results modal
- Manual entry form

Modals:
1. DuplicateShipCertificateModal
2. ShipNameMismatchModal
3. BatchProcessingModal
4. BatchResultsModal
```

#### Audit Certificate Modal:
```jsx
// File: AddAuditCertificateModal.jsx

Features:
- Ship auto-selected (already on ship page)
- Single/Multi file upload
- Category warning modal (ISM/ISPS/MLC)  // ⭐ NEW
- Validation confirmation modal
- Duplicate confirmation modal
- Error modal (unified)
- Batch processing modal
- Batch results modal
- Manual entry form

Modals:
1. CategoryModal (new)
2. ValidationModal
3. DuplicateModal
4. ErrorModal (unified)
5. BatchProcessingModal
6. BatchResultsModal
```

**Điểm khác biệt:**
- ✅ Audit: Category warning modal (check ISM/ISPS/MLC)
- ✅ Audit: Unified error modal
- ❌ Ship: Separate modals cho mỗi error type

---

### 8. 🗄️ DATABASE COLLECTIONS

#### Ship Certificate:
```
Collection: certificates
Index: ship_id, cert_no, created_at
```

#### Audit Certificate:
```
Collection: audit_certificates
Index: ship_id, cert_no, next_survey_date, created_at
```

**Separate collections** → Dễ dàng query và manage riêng biệt

---

### 9. 🎨 STATUS COLUMN RENDERING

#### Ship Certificate:
```jsx
// Static status based on cert_type
Full Term → 🟢 Green
Interim → 🟡 Orange
Expired → 🔴 Red (based on valid_date)
```

#### Audit Certificate:
```jsx
// ⭐ DYNAMIC status based on next_survey_date + window
Calculate days until next survey:
  - days > 90: 🟢 "Valid"
  - days ≤ 90: 🟡 "Due Soon"
  - days < 0: 🔴 "Expired"

Window annotation (±3M, ±6M) affects calculation
```

**Điểm khác biệt:**
- Audit: Dynamic, calculated real-time
- Ship: Static, based on DB field

---

## 🔑 KEY TAKEAWAYS

### Ship Certificate (CLASS & FLAG):
1. ❌ **Problem:** Không có OCR → Scanned PDFs fail
2. ❌ Không có summary generation
3. ✅ Simple validation logic
4. ✅ Suitable cho standard Class/Flag certificates

### Audit Certificate (ISM/ISPS/MLC):
1. ✅ **Better:** Có OCR → Handle scanned PDFs
2. ✅ AI generates summary cho quick reference
3. ✅ Strict category validation (ISM/ISPS/MLC only)
4. ✅ Summary lifecycle management (delete/rename)
5. ✅ Dynamic status calculation
6. ✅ More advanced features

---

## 🎯 RECOMMENDATIONS

### Cho Ship Certificate:
1. **Urgent:** Add OCR support (copy từ Audit flow)
   ```python
   # Fix line 391 in certificate_multi_upload_service.py
   text = await PDFProcessor.process_pdf(file_content, use_ocr_fallback=True)
   ```

2. **Optional:** Xem xét thêm summary generation
   - Giúp user xem quick overview
   - Dễ dàng search và reference

3. **Optional:** Unified error handling modals
   - Học từ Audit Certificate
   - Cleaner UX

### Cho Audit Certificate:
1. ✅ Flow đã rất tốt
2. ✅ Features hoàn chỉnh
3. **Maintain:** Giữ các features đã có
4. **Monitor:** Performance của summary generation

---

## 📈 FEATURE COMPARISON MATRIX

| Feature | Ship Cert | Audit Cert |
|---------|-----------|------------|
| Multi-file upload | ✅ | ✅ |
| AI extraction | ✅ | ✅ |
| OCR for scanned PDFs | ❌ | ✅ |
| Summary generation | ❌ | ✅ |
| Summary file upload | ❌ | ✅ |
| Summary lifecycle (delete/rename) | ❌ | ✅ |
| IMO validation (blocking) | ✅ | ✅ |
| Ship name validation (warning) | ✅ | ✅ |
| Category validation (strict) | ❌ | ✅ |
| Duplicate detection | ✅ | ✅ |
| Duplicate resolution UI | ✅ | ✅ |
| Batch processing UI | ✅ | ✅ |
| Retry failed files | ✅ | ✅ |
| Manual entry fallback | ✅ | ✅ |
| Dynamic status calculation | ❌ | ✅ |
| Notes management | ✅ | ✅ |
| Notes hover preview | ❌ | ✅ |

---

## 🏆 SCORING

**Ship Certificate Flow:** 70/100
- ✅ Good: Basic AI extraction, Multi-upload
- ❌ Missing: OCR, Summary, Dynamic status
- ⚠️ Issue: Scanned PDFs không work

**Audit Certificate Flow:** 95/100
- ✅ Excellent: OCR, Summary, Dynamic status
- ✅ Advanced: Category validation, Lifecycle management
- ✅ Complete: Full-featured, well-tested
- 🎯 Best Practice: Should be reference cho các module khác

---

**Document created:** 2024-11-27  
**Purpose:** Technical comparison for development reference  
**Version:** 1.0
