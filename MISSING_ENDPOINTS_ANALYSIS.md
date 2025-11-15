# 🔍 PHÂN TÍCH ENDPOINTS CHƯA MIGRATE

**Ngày:** $(date +%Y-%m-%d)
**Status:** Backend migration gần hoàn tất, cần bổ sung một số endpoints phụ trợ

---

## ✅ ĐÃ MIGRATE HOÀN TẤT

### 1. Authentication (100%)
- ✅ POST `/api/auth/login` (có alias `/api/login`)
- ✅ GET `/api/auth/verify-token` (có alias `/api/verify-token`)

### 2. Core Modules (100%)
- ✅ **Users** - Full CRUD (8 endpoints)
- ✅ **Companies** - Full CRUD (7 endpoints)
- ✅ **Ships** - Basic CRUD + Calculations (15+ endpoints)
- ✅ **Certificates** - Full CRUD + AI analysis (10+ endpoints)
- ✅ **Crew** - Full CRUD (10+ endpoints)
- ✅ **Crew Certificates** - Full CRUD (8 endpoints)

### 3. Document Types (100%)
- ✅ **Survey Reports** - Full CRUD + AI analysis
- ✅ **Test Reports** - Full CRUD + AI analysis
- ✅ **Drawings & Manuals** - Full CRUD
- ✅ **Other Documents** - Full CRUD
- ✅ **ISM Documents** - Full CRUD
- ✅ **ISPS Documents** - Full CRUD
- ✅ **MLC Documents** - Full CRUD
- ✅ **Supply Documents** - Full CRUD

---

## ⚠️ CẦN BỔ SUNG / HOÀN THIỆN

### 1. AI Configuration (CRITICAL - Priority: HIGH)
**Status:** Hiện có PLACEHOLDER trong `/api/ai-config`

**Thiếu:**
- ❌ GET `/api/ai-config` - Đang trả mock data
- ❌ PUT `/api/ai-config` - Chưa implement
- ❌ POST `/api/ai-config/test` - Test AI connection

**Cần làm:**
1. Tạo model `AIConfig` với fields:
   - provider: str (openai, google, anthropic)
   - model: str (gpt-4, gemini-2.0-flash, etc.)
   - use_emergent_key: bool
   - custom_api_key: Optional[str]
2. Tạo repository & service cho AI config
3. Lưu config trong MongoDB (collection: ai_config)
4. Implement GET/PUT endpoints
5. Integrate EMERGENT_LLM_KEY

### 2. Certificate AI Analysis (CRITICAL - Priority: HIGH)
**Status:** Endpoint tồn tại nhưng dùng MOCK DATA

**File:** `/app/backend/app/services/certificate_service.py`
**Endpoint:** `POST /api/certificates/analyze-file`

**Thiếu:**
- ❌ PDF text extraction (đang dùng mock)
- ❌ OCR fallback cho scanned PDFs
- ❌ Real AI analysis với LLM
- ❌ Date parsing intelligence

**Cần làm:**
1. Install `emergentintegrations` library
2. Implement PDF text extraction (PyPDF2/pdfplumber)
3. Implement OCR fallback (pytesseract - đã có sẵn)
4. Call LLM với EMERGENT_LLM_KEY
5. Parse AI response và extract fields:
   - cert_name, cert_type, cert_no
   - issue_date, valid_date, last_endorse
   - issued_by, ship_name, imo_number
   - flag, class_society, confidence score

### 3. Ship Logo Upload
**Status:** Chưa implement

**Thiếu:**
- ❌ POST `/api/ships/{ship_id}/logo` - Upload ship logo
- ❌ GET `/api/ships/{ship_id}/logo` - Get ship logo URL

**Frontend expects:** `API_ENDPOINTS.SHIP_LOGO: (id) => /api/ships/${id}/logo`

**Cần làm:**
1. Add logo upload endpoint trong `ships.py`
2. Handle file upload và lưu trong `/uploads/ships/{ship_id}/logo.jpg`
3. Return logo URL

### 4. Ship Certificate Analysis
**Status:** Chưa migrate

**Thiếu:**
- ❌ POST `/api/analyze-ship-certificate` - Analyze ship certificate for "Add Ship" feature

**Frontend expects:** `API_ENDPOINTS.SHIP_ANALYZE_CERTIFICATE: '/api/analyze-ship-certificate'`

**Cần làm:**
1. Tạo endpoint trong `ships.py` hoặc `certificates.py`
2. Logic tương tự `analyze_certificate_file` nhưng extract thêm ship info
3. Return ship data để auto-fill form "Add Ship"

### 5. Certificate File Operations
**Status:** Một phần chưa migrate

**Thiếu:**
- ❌ POST `/api/certificates/{cert_id}/upload-files` - Upload multiple files
- ❌ GET `/api/certificates/{cert_id}/file-link` - Get file download link

**Frontend expects:**
```js
CERTIFICATE_UPLOAD_FILES: (id) => `/api/certificates/${id}/upload-files`
CERTIFICATE_FILE_LINK: (id) => `/api/certificates/${id}/file-link`
```

**Cần làm:**
1. Add file upload endpoint cho certificates
2. Add file link generator endpoint
3. Tương tự cho crew-certificates, survey-reports, test-reports

### 6. Google Drive Integration
**Status:** Chưa migrate

**Thiếu:** (10 endpoints)
- ❌ GET `/api/gdrive-config` - Get GDrive config
- ❌ POST `/api/gdrive/upload` - Upload to GDrive
- ❌ GET `/api/companies/{id}/gdrive/config` - Get company GDrive config
- ❌ POST `/api/companies/{id}/gdrive/configure` - Configure GDrive
- ❌ POST `/api/companies/{id}/gdrive/configure-proxy` - Test proxy
- ❌ GET `/api/companies/{id}/gdrive/status` - Get sync status

**Frontend expects:** (từ api.js)
```js
COMPANY_GDRIVE_CONFIG: (id) => `/api/companies/${id}/gdrive/config`
COMPANY_GDRIVE_CONFIGURE: (id) => `/api/companies/${id}/gdrive/configure`
COMPANY_GDRIVE_TEST_PROXY: (id) => `/api/companies/${id}/gdrive/configure-proxy`
COMPANY_GDRIVE_STATUS: (id) => `/api/companies/${id}/gdrive/status`
GDRIVE_CONFIG: '/api/gdrive-config'
GDRIVE_UPLOAD: '/api/gdrive/upload'
```

**Cần làm:**
1. Tạo file `app/api/v1/gdrive.py`
2. Migrate Google Drive logic từ backend-v1
3. Add OAuth2 flow cho Google Drive
4. Implement upload/sync features

### 7. Passport Analysis (Crew)
**Status:** Chưa migrate

**Thiếu:**
- ❌ POST `/api/passport/analyze-file` - AI analyze passport

**Frontend expects:** `API_ENDPOINTS.PASSPORT_ANALYZE: '/api/passport/analyze-file'`

**Cần làm:**
1. Tạo endpoint trong `crew.py`
2. AI analysis cho passport data
3. Extract: name, passport_no, nationality, issue_date, expiry_date, photo

### 8. Crew Move Standby Files
**Status:** Chưa migrate

**Thiếu:**
- ❌ POST `/api/crew/move-standby-files` - Move files when crew changes ship

**Frontend expects:** `API_ENDPOINTS.CREW_MOVE_STANDBY_FILES: '/api/crew/move-standby-files'`

**Cần làm:**
1. Add endpoint trong `crew.py`
2. Logic move files từ standby folder sang ship folder

### 9. Company Logo Upload
**Status:** Chưa migrate

**Thiếu:**
- ❌ POST `/api/companies/{company_id}/upload-logo` - Upload company logo

**Frontend expects:** `API_ENDPOINTS.COMPANY_LOGO: (id) => /api/companies/${id}/upload-logo`

**Cần làm:**
1. Add logo upload endpoint trong `companies.py`
2. Handle file upload và lưu trong `/uploads/companies/{company_id}/logo.jpg`

---

## 📊 TÓM TẮT

**Tổng số endpoints trong frontend/src/constants/api.js:** ~60 unique endpoints

**Đã migrate:** ~45 endpoints (75%)

**Còn thiếu:** ~15 endpoints (25%)

### Breakdown theo mức độ ưu tiên:

#### 🔴 CRITICAL (Cần làm ngay - PHASE 1)
1. ✅ AI Config endpoints (GET/PUT /api/ai-config) - **DOING NOW**
2. ✅ Certificate AI Analysis (implement real logic) - **DOING NOW**
3. Ship/Company Logo Upload (2 endpoints)
4. Ship Certificate Analysis (1 endpoint)

#### 🟡 MEDIUM (Có thể làm sau - PHASE 2)
5. Certificate/Crew Cert file operations (6 endpoints)
6. Passport Analysis (1 endpoint)
7. Crew Move Standby Files (1 endpoint)

#### 🟢 LOW (Có thể skip hoặc làm cuối - PHASE 3)
8. Google Drive Integration (10 endpoints) - Complex, có thể defer

---

## 🎯 KẾ HOẠCH THỰC HIỆN

### PHASE 1A: AI Configuration & Analysis (30-45 min) ✅ COMPLETED
1. ✅ Tạo AI Config model, repository, service
2. ✅ Implement GET/PUT /api/ai-config endpoints
3. ✅ Integrate EMERGENT_LLM_KEY
4. ⏳ Test AI config endpoints (NEXT)

### PHASE 1B: Real Certificate AI Analysis (30-45 min) ✅ COMPLETED
1. ✅ Install emergentintegrations library
2. ✅ Implement PDF text extraction (pdf_processor.py)
3. ✅ Implement OCR fallback (pytesseract)
4. ✅ Implement LLM call for certificate analysis (ai_helper.py)
5. ✅ Replace mock data với real AI analysis
6. ⏳ Test với real certificates (NEXT)

### PHASE 1C: Logo & File Uploads (15-20 min) ✅ COMPLETED
1. ✅ Ship logo upload endpoint (POST/GET /api/ships/{id}/logo)
2. ✅ Company logo upload endpoint (POST /api/companies/{id}/upload-logo)
3. ✅ Certificate file operations (POST /api/certificates/{id}/upload-files, GET /api/certificates/{id}/file-link)
4. ✅ Crew certificate file operations (POST /api/crew-certificates/{id}/upload-files, GET /api/crew-certificates/{id}/file-link)

### PHASE 2: Auxiliary Features (30-45 min) ✅ COMPLETED
1. ✅ Passport analysis (POST /api/passport/analyze-file)
2. ✅ Crew file operations (POST /api/crew/move-standby-files)
3. ✅ Ship certificate analysis endpoint (POST /api/analyze-ship-certificate)

### PHASE 3: Google Drive (Optional - 60+ min)
- Complex integration
- Có thể defer nếu không urgent
- Cần OAuth2 flow và extensive testing

---

**Next Steps:**
1. Bắt đầu với PHASE 1A: AI Configuration
2. Tiếp tục PHASE 1B: Real AI Analysis
3. Test thoroughly với backend testing agent
4. Update progress trong file này

