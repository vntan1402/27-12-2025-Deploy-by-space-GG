# Quy trình "Add Crew Certificate From Certificate File (AI Analysis)"

## Tổng quan

Quy trình này cho phép thêm chứng chỉ thuyền viên bằng cách upload file và sử dụng AI để tự động trích xuất thông tin, giúp tiết kiệm thời gian nhập liệu thủ công.

## Các bước trong quy trình

### **BƯỚC 1: Upload File - Frontend** 
**File:** `/app/frontend/src/App.js`  
**Function:** `handleMultipleCertificateUpload()` (Line 8027)

**Input:**
- User upload 1 hoặc nhiều file (PDF, JPG, PNG, tối đa 10MB/file)
- User phải chọn crew member trước khi upload

**Validation:**
- ✅ Kiểm tra crew đã được chọn chưa
- ✅ Kiểm tra định dạng file (PDF, JPG, PNG)
- ✅ Kiểm tra kích thước file (<10MB)

**Phân nhánh:**
- **1 file**: Mở modal review → User có thể chỉnh sửa trước khi lưu
- **Nhiều file**: Xử lý batch tự động → Không mở modal review

---

### **BƯỚC 2: Gọi API Analyze - Frontend**
**Function:** `processSingleCertInBatch()` (Line 8169) hoặc `handleCertFileUpload()` (cho single file)

**API Call:**
```javascript
POST ${API}/crew-certificates/analyze-file
Content-Type: multipart/form-data

FormData:
- cert_file: File object
- ship_id: string
- crew_id: string (optional)
```

**Purpose:** Gửi file lên backend để phân tích bằng AI

---

### **BƯỚC 3: Phân tích File - Backend**
**File:** `/app/backend/server.py`  
**Endpoint:** `@api_router.post("/crew-certificates/analyze-file")` (Line 14009)  
**Function:** `analyze_certificate_file_for_crew()`

#### 3.1. Lấy thông tin cơ bản
- Đọc file content
- Lấy thông tin company, ship, crew từ database
- Validate crew member (nếu có crew_id)

#### 3.2. Phân tích với Google Document AI
**Module:** `dual_apps_script_manager.py`  
**Function:** `analyze_certificate_only()`

**Bước chi tiết:**
1. Gọi Google Document AI API
2. Nhận về raw text/summary từ certificate
3. **KHÔNG upload file lên Drive ở bước này** ⚠️

**Output:**
```json
{
  "success": true,
  "ai_analysis": {
    "success": true,
    "data": {
      "summary": "Full text extracted from certificate..."
    }
  }
}
```

#### 3.3. Trích xuất thông tin từ AI Summary
**Function:** `extract_crew_certificate_fields_from_summary()`

**Sử dụng System AI (Gemini/OpenAI) để extract:**
- `cert_name`: Tên chứng chỉ (COC, COE, STCW, Medical, etc.)
- `cert_no`: Số chứng chỉ
- `issued_by`: Đơn vị cấp
- `issued_date`: Ngày cấp
- `expiry_date`: Ngày hết hạn
- `holder_name`: Tên người được cấp (để validate)
- `rank`: Chức danh (nếu có)
- `note`: Ghi chú

**Detect Certificate Type:**
```python
cert_type = detect_certificate_type(filename, summary_text)
# Có thể là: COC, COE, STCW, Medical, Passport, etc.
```

#### 3.4. Validation - Name Matching
**Algorithm:** Permutation-insensitive name matching

**So sánh:**
- `holder_name` (từ certificate) 
- vs `crew_name` (Vietnamese)
- vs `crew_name_en` (English)

**Ví dụ:**
```
Certificate: "CHUONG SY HO"
Crew DB:     "HO SY CHUONG"
→ Match ✅ (các parts giống nhau: ["CHUONG", "HO", "SY"])
```

**Normalize process:**
1. Remove diacritics (á → a, ê → e, đ → d)
2. Convert to UPPERCASE
3. Split into parts
4. Sort parts alphabetically
5. Compare sorted parts

**Nếu không match:**
- Frontend hiển thị warning popup
- User có thể bypass (choose "Continue Anyway")
- Hoặc cancel và chọn crew khác

#### 3.5. Return Response
**Backend Response:**
```json
{
  "success": true,
  "analysis": {
    "cert_name": "Certificate of Competency",
    "cert_no": "123456",
    "issued_by": "Vietnam Maritime Administration",
    "issued_date": "2024-01-15",
    "expiry_date": "2029-01-15",
    "holder_name": "HO SY CHUONG",
    "rank": "Chief Engineer",
    "note": "",
    "confidence_score": 0.95,
    "processing_method": "analysis_only_no_upload",
    
    // File content được encode để upload sau
    "_file_content": "base64_encoded_file_content...",
    "_filename": "COC_Certificate.pdf",
    "_content_type": "application/pdf",
    "_summary_text": "Full extracted text..."
  },
  "crew_name": "HỒ SỸ CHƯỜNG",
  "crew_name_en": "HO SY CHUONG",
  "passport": "B1234567",
  "validation": {
    "holder_name_match": true,
    "dob_match": true
  }
}
```

---

### **BƯỚC 4: Kiểm tra Duplicate - Frontend**
**Function:** `processSingleCertInBatch()` (Line 8249)

**API Call:**
```javascript
POST ${API}/crew-certificates/check-duplicate
Body: {
  crew_id: "crew-uuid",
  cert_no: "123456"
}
```

**Response:**
```json
{
  "is_duplicate": false  // or true
}
```

**Nếu duplicate:**
- Skip file này
- Log thông báo
- Tiếp tục xử lý file tiếp theo (batch mode)

---

### **BƯỚC 5: Tạo Certificate Record - Frontend**
**Function:** `processSingleCertInBatch()` (Line 8295)

**API Call:**
```javascript
POST ${API}/crew-certificates/manual?ship_id={ship_id}
Content-Type: application/json

Body: {
  crew_id: "crew-uuid",
  crew_name: "HỒ SỸ CHƯỜNG",
  crew_name_en: "HO SY CHUONG",
  passport: "B1234567",
  rank: "Chief Engineer",
  cert_name: "Certificate of Competency",
  cert_no: "123456",
  issued_by: "Vietnam Maritime Administration",
  issued_date: "2024-01-15T00:00:00Z",
  cert_expiry: "2029-01-15T00:00:00Z",
  note: "",
  crew_cert_file_id: "",  // Empty - sẽ update sau
  crew_cert_summary_file_id: ""  // Empty - sẽ update sau
}
```

**Backend tạo record trong MongoDB:**
- Collection: `crew_certificates`
- Auto-generate: `id` (UUID), `created_at`, `updated_at`
- Status: `active`

**Response:**
```json
{
  "id": "cert-uuid-123",
  "crew_id": "crew-uuid",
  "cert_name": "Certificate of Competency",
  // ... other fields
}
```

---

### **BƯỚC 6: Upload Files to Google Drive - Frontend**
**Function:** `processSingleCertInBatch()` (Line 8317)

**API Call:**
```javascript
POST ${API}/crew-certificates/{cert_id}/upload-files
Content-Type: application/json

Body: {
  file_content: "base64_encoded_content...",
  filename: "COC_Certificate.pdf",
  content_type: "application/pdf",
  summary_text: "Full extracted text from AI..."
}
```

**Backend Upload Process:**
**File:** `/app/backend/server.py`  
**Endpoint:** `@api_router.post("/crew-certificates/{cert_id}/upload-files")`

#### 6.1. Decode file content từ base64
```python
file_bytes = base64.b64decode(file_content)
```

#### 6.2. Upload Certificate File
**Google Drive Structure:**
```
Company Drive
└── ShipName/
    └── Crew Records/
        └── CrewName_Passport/
            └── Certificates/
                └── {CertName}/
                    ├── COC_Certificate.pdf  ← Original file
                    └── COC_Certificate_AI_Summary.txt  ← AI summary
```

**Upload using Dual Apps Script Manager:**
```python
cert_file_result = await dual_manager.upload_crew_certificate_file(
    file_content=file_bytes,
    filename=filename,
    content_type=content_type,
    crew_name=crew_name,
    passport=passport,
    cert_name=cert_name,
    ship_name=ship_name
)
```

**Return:**
- `crew_cert_file_id`: Google Drive file ID cho certificate
- `crew_cert_summary_file_id`: Google Drive file ID cho summary

#### 6.3. Update Certificate Record với File IDs
```python
await mongo_db.update("crew_certificates", 
    {"id": cert_id},
    {
        "crew_cert_file_id": crew_cert_file_id,
        "crew_cert_summary_file_id": crew_cert_summary_file_id,
        "updated_at": datetime.now(timezone.utc)
    }
)
```

**Response:**
```json
{
  "success": true,
  "crew_cert_file_id": "1a2b3c4d5e6f...",
  "crew_cert_summary_file_id": "7g8h9i0j1k2l...",
  "message": "Files uploaded successfully"
}
```

---

### **BƯỚC 7: Cập nhật UI - Frontend**

#### Batch Mode (Multiple Files):
**Function:** `startCertBatchProcessing()` (Line 8080)

**Xử lý parallel với staggered delay:**
- File 1: Start ngay lập tức (0s)
- File 2: Start sau 2s
- File 3: Start sau 4s
- ...

**Progress tracking:**
```javascript
certBatchProgress: {
  current: 2,  // đã xử lý 2 files
  total: 5     // tổng 5 files
}
```

**Results collection:**
```javascript
certBatchResults: [
  {
    filename: "COC.pdf",
    success: true,
    certCreated: true,
    fileUploaded: true,
    certName: "Certificate of Competency",
    certNo: "123456",
    crewName: "HỒ SỸ CHƯỜNG"
  },
  {
    filename: "Medical.pdf",
    success: false,
    error: "DUPLICATE",
    duplicateInfo: { /* existing cert info */ }
  }
]
```

**Sau khi hoàn thành:**
1. Đóng "Add Crew Certificate" modal
2. Mở "Processing Results" modal
3. Hiển thị kết quả từng file (Success/Failed)
4. Refresh crew certificates list

#### Single File Mode:
- Modal vẫn mở
- User review thông tin được extract
- User có thể edit trước khi submit
- Submit manually bằng form

---

## Sơ đồ luồng dữ liệu

```
┌─────────────┐
│   USER      │
│ Upload File │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  FRONTEND                       │
│  - Validate file                │
│  - Check crew selected          │
└──────┬──────────────────────────┘
       │
       ▼ POST /crew-certificates/analyze-file
┌─────────────────────────────────┐
│  BACKEND - Analyze              │
│  1. Get crew/ship info          │
│  2. Google Document AI          │
│     → Extract raw text          │
│  3. System AI (Gemini/OpenAI)   │
│     → Extract structured fields │
│  4. Validate holder name        │
│  5. Return analysis + file_content│
└──────┬──────────────────────────┘
       │
       ▼ Return analysis JSON
┌─────────────────────────────────┐
│  FRONTEND - Check & Create      │
│  1. Check duplicate             │
│  2. Create cert record          │
└──────┬──────────────────────────┘
       │
       ▼ POST /crew-certificates/manual
┌─────────────────────────────────┐
│  BACKEND - Create Record        │
│  - Save to MongoDB              │
│  - Return cert_id               │
└──────┬──────────────────────────┘
       │
       ▼ Return cert_id
┌─────────────────────────────────┐
│  FRONTEND - Upload Files        │
└──────┬──────────────────────────┘
       │
       ▼ POST /crew-certificates/{cert_id}/upload-files
┌─────────────────────────────────┐
│  BACKEND - Upload to Drive      │
│  1. Decode base64 file          │
│  2. Upload original file        │
│  3. Upload AI summary file      │
│  4. Update cert record with IDs │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  FRONTEND - Show Result         │
│  - Close modal / Show results   │
│  - Refresh certificates list    │
└─────────────────────────────────┘
```

---

## Các trường hợp đặc biệt

### 1. AI Analysis thất bại
- Backend vẫn return `success: true`
- Nhưng `analysis` fields rỗng
- File content vẫn được giữ lại
- User có thể nhập manual

### 2. Name không match
- Frontend hiển thị warning popup
- Cho user 2 lựa chọn:
  - "Continue Anyway" (bypass validation)
  - "Cancel" (chọn crew khác)

### 3. Duplicate certificate
- Skip file này trong batch mode
- Hiển thị thông tin cert đã tồn tại
- Continue với file tiếp theo

### 4. File upload to Drive thất bại
- Certificate record vẫn được lưu
- File IDs để trống
- Log warning nhưng không throw error
- User có thể upload lại sau

---

## Điểm quan trọng

✅ **Separate Analysis & Upload:**
- Analyze KHÔNG upload file (chỉ extract info)
- Upload xảy ra SAU KHI certificate record được tạo thành công

✅ **File Content Preservation:**
- File content được encode base64 ngay từ đầu
- Đảm bảo có thể upload ngay cả khi AI analysis fail

✅ **Batch Processing:**
- Parallel processing với staggered delay (2s giữa mỗi file)
- Tránh overwhelming backend
- Better UX với progress tracking

✅ **Validation:**
- Name matching với permutation-insensitive algorithm
- Duplicate check trước khi create
- DOB validation (optional)

✅ **Error Handling:**
- Graceful degradation (AI fail → manual entry)
- Partial success (cert saved, upload failed)
- Detailed error messages

---

## Files liên quan

### Frontend
- `/app/frontend/src/App.js`
  - `handleMultipleCertificateUpload()` (Line 8027)
  - `startCertBatchProcessing()` (Line 8080)
  - `processSingleCertInBatch()` (Line 8169)
  - `handleCertFileUpload()` (single file mode)

### Backend
- `/app/backend/server.py`
  - `analyze_certificate_file_for_crew()` (Line 14009)
  - `upload_crew_certificate_files()` (upload endpoint)
  - `extract_crew_certificate_fields_from_summary()`
  - `detect_certificate_type()`

### Modules
- `/app/backend/dual_apps_script_manager.py`
  - `analyze_certificate_only()` - AI analysis only
  - `upload_crew_certificate_file()` - Upload to Drive

---

## Cải tiến có thể thực hiện

1. **Better AI Prompts:** Fine-tune prompts cho từng loại certificate
2. **OCR Enhancement:** Xử lý tốt hơn cho ảnh chất lượng thấp
3. **Auto-categorization:** Tự động phân loại certificate type
4. **Smart field mapping:** Học từ user corrections
5. **Batch optimization:** Reduce delay giữa files khi backend ổn định
