# 🚀 Flow Upload và Phân tích File trong CLASS & FLAG CERT > Add Ship Certificate

## 🎯 Tổng quan

Hệ thống upload chứng chỉ tàu sử dụng **AI-powered analysis** kết hợp với **Google Drive** để tự động trích xuất thông tin và lưu trữ tài liệu.

---

## 📊 Flow Chart

```
User Upload Files
      ↓
Frontend: AddShipCertificateModal.jsx
      ↓
[File Validation]
      ↓
API: POST /api/certificates/multi-upload
      ↓
Backend: CertificateMultiUploadService
      ↓
┌──────────────────────┐
│   AI Analysis Pipeline   │
│  1. AI Config Check      │
│  2. File Processing      │
│  3. Image Extraction     │
│  4. AI Analysis          │
│  5. Quality Check        │
│  6. Classification       │
│  7. Validation           │
└──────────────────────┘
      ↓
┌──────────────────────┐
│  Validation Checks    │
│  - IMO Number         │
│  - Ship Name          │
│  - Duplicate Check    │
└──────────────────────┘
      ↓
┌──────────────────────┐
│  Google Drive Upload  │
│  - Original File      │
│  - Summary File       │
└──────────────────────┘
      ↓
┌──────────────────────┐
│  Database Storage     │
│  - Certificate Record │
│  - Audit Log          │
└──────────────────────┘
      ↓
   Success/Error Response
```

---

## 💻 1. Frontend Flow (AddShipCertificateModal.jsx)

### Step 1: User Interface

**Component:** `/app/frontend/src/components/ShipCertificates/AddShipCertificateModal.jsx`

**Tính năng:**
- Upload nhiều files cùng lúc (multi-file upload)
- Hiển thị progress bar cho từng file
- Batch processing modal với real-time status
- 3 second delay giữa các files (tránh quá tải AI API)

### Step 2: File Upload Handler

```javascript
const handleMultiCertUpload = async (files) => {
  // 1. Check software expiry
  if (!checkAndWarn()) return;
  
  // 2. Validate ship selection
  if (!selectedShip?.id) {
    toast.error('❌ Vùi lòng chọn tàu');
    return;
  }
  
  // 3. Initialize tracking
  setIsMultiCertProcessing(true);
  const fileArray = Array.from(files);
  const totalFiles = fileArray.length;
  
  // 4. Upload files sequentially with 3s delay
  const uploadPromises = fileArray.map((file, i) => {
    return new Promise(async (resolve) => {
      // Delay before starting (except first file)
      if (i > 0) {
        await new Promise(r => setTimeout(r, 3000 * i));
      }
      
      // Create FormData
      const formData = new FormData();
      formData.append('files', file);
      
      // Upload with progress tracking
      const response = await api.post(
        `/api/certificates/multi-upload?ship_id=${selectedShip.id}`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            // Update progress state
          }
        }
      );
      
      // Process response
      const results = response.data.results || [];
      const result = results[0];
      
      if (result.status === 'success') {
        successCount++;
        // Store extracted info for auto-fill
        if (result.extracted_info) {
          firstSuccessInfo = result.extracted_info;
        }
      }
    });
  });
}
```

### Step 3: Progress Tracking

**States:**
- `fileStatusMap`: Status của từng file (waiting, processing, completed, error)
- `fileProgressMap`: Phần trăm upload (0-100)
- `fileSubStatusMap`: Sub-status (analyzing, uploading, etc.)
- `multiCertUploads`: Chi tiết từng upload
- `uploadSummary`: Tổng kết (success, failed, total)

---

## 🌐 2. API Endpoint

**URL:** `POST /api/certificates/multi-upload?ship_id={ship_id}`

**File:** `/app/backend/app/api/v1/certificates.py`

**Handler:**
```python
@router.post("/multi-upload")
async def multi_certificate_upload(
    ship_id: str = Query(...),
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: UserResponse = Depends(check_editor_permission)
):
    """
    Upload multiple certificate files with AI analysis
    
    Process:
    1. AI analysis for information extraction
    2. Quality check and classification
    3. IMO/ship name validation
    4. Duplicate detection
    5. Google Drive upload
    6. Certificate record creation
    """
    result = await CertificateMultiUploadService.process_multi_upload(
        ship_id=ship_id,
        files=files,
        current_user=current_user,
        background_tasks=background_tasks
    )
    return result
```

**Permission:** Editor, Manager, Admin, System Admin, Super Admin

---

## 🤖 3. AI Analysis Pipeline (CertificateMultiUploadService)

**File:** `/app/backend/app/services/certificate_multi_upload_service.py`

### Step 1: AI Configuration

```python
# Get AI config from user settings
ai_config_obj = await AIConfigService.get_ai_config(current_user)
ai_config = {
    "provider": ai_config_obj.provider,  # openai, anthropic, google
    "model": ai_config_obj.model,        # gpt-4, claude-3, gemini-pro
    "temperature": ai_config_obj.temperature,
    "api_key": ai_config_obj.api_key
}
```

### Step 2: File Processing

**For each uploaded file:**

```python
for file in files:
    # 1. Read file content
    file_content = await file.read()
    
    # 2. Determine file type
    file_type = file.content_type  # application/pdf, image/jpeg, etc.
    
    # 3. Extract images from PDF (if needed)
    if file_type == 'application/pdf':
        images = extract_images_from_pdf(file_content)
    else:
        images = [file_content]
    
    # 4. Encode images to base64 for AI
    base64_images = [base64.b64encode(img).decode('utf-8') 
                     for img in images]
```

### Step 3: AI Analysis

**Prompt Template:**
```
You are a maritime certificate expert. Analyze this ship certificate and extract:

1. Certificate Information:
   - Certificate Name
   - Certificate Number
   - Certificate Type (Full Term/Short term/Interim)
   - Certificate Abbreviation

2. Dates:
   - Issue Date
   - Valid Until Date
   - Last Endorsement Date
   - Next Survey Date
   - Next Survey Type

3. Ship Information:
   - Ship Name
   - IMO Number
   - Flag

4. Issuer Information:
   - Issued By
   - Issued By Abbreviation

5. Quality Assessment:
   - Is this a valid marine certificate? (yes/no)
   - Quality score (0-100)
   - Completeness score (0-100)

Return as JSON.
```

**AI Call:**
```python
from emergentintegrations import ChatOpenAI, ChatAnthropic, ChatGoogle

if ai_config['provider'] == 'openai':
    client = ChatOpenAI(
        api_key=ai_config['api_key'],
        model=ai_config['model']
    )
elif ai_config['provider'] == 'anthropic':
    client = ChatAnthropic(
        api_key=ai_config['api_key'],
        model=ai_config['model']
    )

response = client.chat(
    messages=[
        {"role": "user", "content": prompt},
        {"role": "user", "images": base64_images}
    ],
    temperature=ai_config['temperature']
)

extracted_info = json.loads(response.content)
```

### Step 4: Quality Check

```python
# Check if it's a valid marine certificate
is_marine = extracted_info.get('is_marine_certificate', False)
quality_score = extracted_info.get('quality_score', 0)

if not is_marine or quality_score < 50:
    # Flag as non-marine or low quality
    summary['non_marine_files'] += 1
    continue
```

### Step 5: Classification

**Check if it's Audit Certificate (ISM/ISPS/MLC/CICA):**

```python
AUDIT_CERTIFICATE_CATEGORIES = {
    "ISM": ["SAFETY MANAGEMENT CERTIFICATE", "SMC", "DOC", ...],
    "ISPS": ["SHIP SECURITY CERTIFICATE", "ISSC", "SSP", ...],
    "MLC": ["MARITIME LABOUR CERTIFICATE", "MLC", "DMLC", ...],
    "CICA": ["CERTIFICATE OF INSPECTION", "CICA", ...]
}

cert_name_upper = extracted_info['cert_name'].upper()

for category, keywords in AUDIT_CERTIFICATE_CATEGORIES.items():
    if any(keyword in cert_name_upper for keyword in keywords):
        # Route to Audit Certificate collection
        is_audit_cert = True
        audit_type = category
        break
```

### Step 6: Validation

**IMO Number Validation:**
```python
if extracted_imo and ship['imo']:
    if extracted_imo != ship['imo']:
        # IMO mismatch - flag for review
        validation_warnings.append('IMO number mismatch')
```

**Ship Name Validation:**
```python
if extracted_ship_name:
    similarity = calculate_similarity(extracted_ship_name, ship['name'])
    if similarity < 0.7:
        # Ship name mismatch
        validation_warnings.append('Ship name mismatch')
```

**Duplicate Check:**
```python
existing_cert = await db.certificates.find_one({
    "ship_id": ship_id,
    "cert_no": extracted_info['cert_no']
})

if existing_cert:
    # Duplicate found
    return {
        "status": "duplicate",
        "existing_cert_id": existing_cert['id']
    }
```

---

## ☁️ 4. Google Drive Upload

### Step 1: Folder Structure

```
Google Drive Root
└── {Ship Name}
    └── Class & Flag Cert
        └── Certificates
            ├── {Ship Name}_{Cert Type}_{Cert Abbr}_{Issue Date}.pdf (Original)
            └── {Ship Name}_{Cert Type}_{Cert Abbr}_{Issue Date}_Summary.pdf (AI Generated)
```

### Step 2: Upload Original File

```python
from app.services.google_drive_service import GoogleDriveService

# Create folder path
folder_path = f"{ship['name']}/Class & Flag Cert/Certificates"

# Upload original file
original_file_id = await GoogleDriveService.upload_file(
    file_content=file_content,
    filename=file.filename,
    folder_path=folder_path,
    mime_type=file.content_type
)
```

### Step 3: Generate & Upload Summary

```python
# Create summary content (AI-generated text summary)
summary_text = f"""
CERTIFICATE SUMMARY
==================

Certificate: {extracted_info['cert_name']}
Number: {extracted_info['cert_no']}
Type: {extracted_info['cert_type']}
Issue Date: {extracted_info['issue_date']}
Valid Until: {extracted_info['valid_date']}

Ship: {ship['name']}
IMO: {ship['imo']}

Issued By: {extracted_info['issued_by']}

Quality Score: {extracted_info['quality_score']}/100
Completeness: {extracted_info['completeness_score']}/100
"""

# Convert to PDF
summary_pdf = generate_pdf_from_text(summary_text)

# Upload summary file
summary_file_id = await GoogleDriveService.upload_file(
    file_content=summary_pdf,
    filename=f"{filename}_Summary.pdf",
    folder_path=folder_path,
    mime_type='application/pdf'
)
```

---

## 💾 5. Database Storage

### Step 1: Create Certificate Record

```python
certificate_data = {
    "id": str(uuid.uuid4()),
    "ship_id": ship_id,
    "cert_name": extracted_info['cert_name'],
    "cert_abbreviation": extracted_info['cert_abbreviation'],
    "cert_no": extracted_info['cert_no'],
    "cert_type": extracted_info['cert_type'],
    "issue_date": extracted_info['issue_date'],
    "valid_date": extracted_info['valid_date'],
    "last_endorse": extracted_info.get('last_endorse'),
    "next_survey": extracted_info.get('next_survey'),
    "next_survey_type": extracted_info.get('next_survey_type'),
    "issued_by": extracted_info['issued_by'],
    "issued_by_abbreviation": extracted_info.get('issued_by_abbreviation'),
    "google_drive_file_id": original_file_id,
    "summary_file_id": summary_file_id,
    "ai_extracted": True,
    "ai_confidence_score": extracted_info.get('quality_score', 0),
    "created_by": current_user.username,
    "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc)
}

await db.certificates.insert_one(certificate_data)
```

### Step 2: Create Audit Log

```python
audit_log = {
    "id": str(uuid.uuid4()),
    "action": "CREATE_SHIP_CERTIFICATE",
    "user": current_user.username,
    "user_role": current_user.role,
    "timestamp": datetime.now(timezone.utc),
    "ship_id": ship_id,
    "ship_name": ship['name'],
    "document_type": "certificate",
    "document_id": certificate_data['id'],
    "certificate_name": certificate_data['cert_name'],
    "certificate_no": certificate_data['cert_no'],
    "details": {
        "ai_extracted": True,
        "quality_score": extracted_info.get('quality_score'),
        "file_name": file.filename
    }
}

await db.ship_audit_logs.insert_one(audit_log)
```

---

## 📦 6. Response Format

### Success Response

```json
{
  "results": [
    {
      "filename": "IOPP_Certificate.pdf",
      "status": "success",
      "message": "Certificate created successfully",
      "certificate_id": "abc-123-def",
      "extracted_info": {
        "cert_name": "INTERNATIONAL OIL POLLUTION PREVENTION",
        "cert_no": "IOPP-2024-001",
        "cert_type": "Full Term",
        "cert_abbreviation": "IOPP",
        "issue_date": "2024-01-15",
        "valid_date": "2029-01-15",
        "issued_by": "Class NK",
        "quality_score": 95,
        "completeness_score": 98
      }
    }
  ],
  "summary": {
    "total_files": 1,
    "marine_certificates": 1,
    "non_marine_files": 0,
    "successfully_created": 1,
    "errors": 0,
    "certificates_created": ["abc-123-def"],
    "non_marine_files_list": [],
    "error_files": []
  }
}
```

### Error Response

```json
{
  "results": [
    {
      "filename": "invalid_doc.pdf",
      "status": "error",
      "message": "Not a valid marine certificate",
      "error": "Quality score too low: 35/100"
    }
  ],
  "summary": {
    "total_files": 1,
    "marine_certificates": 0,
    "non_marine_files": 1,
    "successfully_created": 0,
    "errors": 1,
    "non_marine_files_list": ["invalid_doc.pdf"],
    "error_files": ["invalid_doc.pdf"]
  }
}
```

---

## ⏱️ 7. Timing & Performance

**Frontend:**
- 3 second delay giữa các files
- Sequential upload (không parallel tại frontend)
- Progress tracking real-time

**Backend:**
- AI analysis: 2-5 giây/file (tùy model)
- Google Drive upload: 1-2 giây/file
- Database operations: <1 giây
- **Tổng thời gian/file: ~5-10 giây**

**Ví dụ:**
- 10 files = ~50-100 giây (với 3s delay)

---

## 🛡️ 8. Error Handling

### Frontend Error Scenarios

1. **No ship selected:** Toast error, không upload
2. **Software expired:** Warning modal, block upload
3. **Upload failed:** Retry option, show error detail
4. **Partial success:** Show summary modal với success/failed breakdown

### Backend Error Scenarios

1. **Ship not found:** 404 error
2. **AI analysis failed:** Fallback to manual entry
3. **Google Drive error:** Store locally, retry background
4. **Duplicate certificate:** Show warning, allow override
5. **IMO mismatch:** Flag for review, still create
6. **Invalid file format:** Skip, add to non-marine list

---

## ⚙️ 9. Configuration

### AI Models Supported

**OpenAI:**
- gpt-4o
- gpt-4-turbo
- gpt-4

**Anthropic:**
- claude-3-opus
- claude-3-sonnet
- claude-3-haiku

**Google:**
- gemini-pro-vision
- gemini-pro

### User Settings

```javascript
// AI Config per user
{
  "provider": "openai",
  "model": "gpt-4o",
  "temperature": 0.2,
  "api_key": "sk-..."
}
```

---

## 📊 10. Metrics & Monitoring

**Tracked metrics:**
- Upload success rate
- AI extraction accuracy
- Average processing time
- Error types frequency
- Non-marine file rate
- Duplicate detection rate

**Logs:**
- Upload start/complete events
- AI analysis results
- Validation warnings
- Google Drive operations
- Database operations

---

## 🚀 11. Future Enhancements

1. **Parallel processing:** Upload multiple files đồng thời (backend)
2. **Batch summary generation:** Tạo summary cho nhiều files cùng lúc
3. **Smart retry:** Tự động retry với exponential backoff
4. **OCR fallback:** Khi AI không extract được, dùng OCR
5. **Template learning:** AI học từ các certificate đã approved
6. **Auto-categorization:** Tự động phân loại certificate type

---

**Document created:** December 2025
**Last updated:** December 2025
