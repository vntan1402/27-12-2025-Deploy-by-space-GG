# 🔄 ADD CREW CERTIFICATE - WORKFLOW HIỆN TẠI & PHÂN TÍCH

## 📊 TỔNG QUAN WORKFLOW

```
┌──────────────────────────────────────────────────────────────────┐
│                    ADD CREW CERTIFICATE WORKFLOW                 │
│                     (2 Phương Thức: AI & Manual)                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎯 PHƯƠNG THỨC 1: TỪ FILE (AI ANALYSIS)

### ✅ **ĐÃ IMPLEMENT**

#### **Frontend (App.js):**

**Step 1: User Upload File**
- ✅ Drag & drop hoặc click để chọn file
- ✅ Validate file type (PDF, JPG, PNG)
- ✅ Validate file size (max 10MB)
- ✅ Location: lines 5566-5705 (`handleCertFileUpload`)

**Step 2: Call Backend API**
```javascript
POST /api/crew-certificates/analyze-file
FormData:
  - cert_file: <file>
  - ship_id: <ship_id>
  - crew_id: <crew_id> (optional)
```
- ✅ Gọi API với FormData
- ✅ Timeout: 2 minutes
- ✅ Loading indicator: "Đang phân tích file với AI..."

**Step 3: Auto-Fill Form**
- ✅ Nhận kết quả phân tích từ backend
- ✅ Auto-fill các trường:
  - `crew_name` (từ response.crew_name)
  - `passport` (từ response.passport)
  - `cert_name` (từ analysis.cert_name)
  - `cert_no` (từ analysis.cert_no)
  - `issued_by` (từ analysis.issued_by)
  - `issued_date` (từ analysis.issued_date)
  - `cert_expiry` (từ analysis.expiry_date)
  - `note` (từ analysis.note)
  - `cert_file_id` (từ analysis.cert_file_id)
- ✅ Location: lines 5666-5677

**Step 4: User Review & Submit**
- ✅ User có thể edit các trường đã auto-fill
- ✅ Submit form → Manual API endpoint
- ✅ Location: lines 5490-5560 (`handleAddCrewCertificateSubmit`)

---

#### **Backend (server.py):**

**Endpoint: POST /api/crew-certificates/analyze-file**
Location: Lines 12907-13108

**Step 1: Validate Request** ✅
- ✅ Check ship_id exists
- ✅ Check ship belongs to user's company
- ✅ Get ship name for folder structure
- ✅ Get crew info (optional)

**Step 2: Get AI Configuration** ✅
- ✅ Get Document AI config from MongoDB
- ✅ Validate project_id, processor_id
- ✅ Check Document AI is enabled

**Step 3: Call Apps Script - Document AI** ✅
```python
apps_script_payload = {
    "action": "analyze_certificate_document_ai",  # ✅ FIXED!
    "file_content": base64_encoded,
    "filename": filename,
    "content_type": mime_type,
    "project_id": project_id,
    "processor_id": processor_id,
    "location": location
}
```
- ✅ Call Apps Script
- ✅ Receive document summary from Document AI

**Step 4: AI Field Extraction** ✅
- ✅ Use System AI (Gemini) to extract fields from summary
- ✅ Functions:
  - `detect_certificate_type()` - Xác định loại cert
  - `extract_crew_certificate_fields_from_summary()` - Trích xuất fields
  - `create_certificate_extraction_prompt()` - Tạo AI prompt
  - `standardize_certificate_dates()` - Chuẩn hóa dates
- ✅ Extract fields:
  - cert_name
  - cert_no (Seaman's Book number)
  - issued_by
  - issued_date (DD/MM/YYYY)
  - expiry_date (DD/MM/YYYY)
  - note

**Step 5: Upload File to Google Drive** ⚠️ **ISSUE HERE!**
```python
upload_payload = {
    "action": "upload_crew_certificate",  # ❌ Action KHÔNG TỒN TẠI!
    "ship_name": ship_name,
    "crew_name": crew_name,
    "filename": filename,
    "file_content": base64_encoded
}
```
- ❌ **VẤN ĐỀ:** Apps Script KHÔNG CÓ action `upload_crew_certificate`
- ❌ File upload sẽ FAIL
- ❌ `cert_file_id` sẽ KHÔNG được trả về
- ⚠️ Location: Lines 13066-13092

**Step 6: Return Results** ✅
- ✅ Return analysis_result với extracted fields
- ✅ Return crew_name, passport
- ✅ Return cert_file_id (nếu upload thành công)

---

#### **Apps Script:**

**Action: analyze_certificate_document_ai** ✅
- ✅ Nhận file từ backend
- ✅ Call Google Document AI
- ✅ Generate structured summary với:
  - Document Type: Maritime Certificate
  - Key Fields: certificate_name, certificate_number, etc.
  - Document Content: extracted text
  - Identified Patterns: STCW, COC, COP, etc.
- ✅ Return summary cho backend

**Action: upload_crew_certificate** ❌
- ❌ **KHÔNG TỒN TẠI**
- ❌ Backend gọi action này nhưng Apps Script không có
- ❌ Cần implement hoặc dùng action khác

---

## 🎯 PHƯƠNG THỨC 2: MANUAL ENTRY

### ✅ **ĐÃ IMPLEMENT HOÀN TOÀN**

#### **Frontend (App.js):**

**Step 1: User Fills Form**
- ✅ Crew Name (required)
- ✅ Passport (required)
- ✅ Cert Name (required)
- ✅ Cert No (required)
- ✅ Issued By
- ✅ Issued Date
- ✅ Cert Expiry
- ✅ Note
- ✅ Location: Lines 9085-9250

**Step 2: Submit Form**
```javascript
POST /api/crew-certificates/manual?ship_id={ship_id}
Body: newCrewCertificate (JSON)
```
- ✅ Validate required fields
- ✅ Call backend API
- ✅ Show success/error toast
- ✅ Refresh certificates list
- ✅ Close modal
- ✅ Location: Lines 5490-5560

---

#### **Backend (server.py):**

**Endpoint: POST /api/crew-certificates/manual**
Location: Lines 12842-12904

**Step 1: Validate Request** ✅
- ✅ Check ship_id parameter
- ✅ Validate required fields
- ✅ Check ship exists and belongs to user's company

**Step 2: Find or Match Crew** ✅
- ✅ Try to find crew by passport + ship
- ✅ If found, use crew_id
- ✅ If not found, use data from form

**Step 3: Calculate Status** ✅
- ✅ Call `calculate_certificate_status(cert_expiry)`
- ✅ Status logic:
  - No expiry → "Unknown"
  - Expired → "Expired"
  - < 30 days → "Expiring Soon"
  - ≥ 30 days → "Valid"

**Step 4: Save to MongoDB** ✅
- ✅ Generate UUID for cert
- ✅ Save to `crew_certificates` collection
- ✅ Include all fields + company_id + ship_id

**Step 5: Create Audit Log** ✅
- ✅ Log action: ADD_CREW_CERTIFICATE
- ✅ Track user, timestamp, details

**Step 6: Return Response** ✅
- ✅ Return created certificate as CrewCertificateResponse

---

## 📋 CÁC ENDPOINTS KHÁC

### ✅ **GET /api/crew-certificates/{ship_id}**
Location: Lines 13111-13147

**Chức năng:**
- ✅ Get all certificates for a ship
- ✅ Optional filter by crew_id
- ✅ Recalculate status for each certificate
- ✅ Return list of certificates

**Query Parameters:**
- `ship_id`: Required
- `crew_id`: Optional (filter by crew)

---

### ✅ **PUT /api/crew-certificates/{cert_id}**
Location: Lines 13150+

**Chức năng:**
- ✅ Update existing certificate
- ✅ Validate cert exists and belongs to user's company
- ✅ Update fields
- ✅ Recalculate status
- ✅ Create audit log

---

### ✅ **DELETE /api/crew-certificates/{cert_id}**

**Chức năng:**
- ✅ Delete certificate
- ✅ Validate ownership
- ✅ Remove from MongoDB
- ✅ Create audit log

---

### ✅ **DELETE /api/crew-certificates/bulk-delete**

**Chức năng:**
- ✅ Delete multiple certificates
- ✅ Validate each certificate
- ✅ Remove from MongoDB
- ✅ Create audit logs

---

## ❌ CÁC BƯỚC CHƯA IMPLEMENT

### 🔴 **CRITICAL: File Upload to Google Drive**

**Vấn đề:**
```python
# Backend đang gọi:
upload_payload = {
    "action": "upload_crew_certificate",  # ❌ KHÔNG TỒN TẠI
    ...
}
```

**Apps Script chỉ có:**
- ✅ `analyze_certificate_document_ai`
- ✅ `analyze_passport_document_ai`
- ✅ `analyze_medical_document_ai`
- ✅ `upload_file` (mock - không thực sự upload)

**Giải pháp:**

**Option 1: Implement action mới trong Apps Script**
```javascript
case "upload_crew_certificate":
  return handleCrewCertificateUpload(requestData);

function handleCrewCertificateUpload(data) {
  // 1. Decode base64 file
  var fileBlob = Utilities.newBlob(
    Utilities.base64Decode(data.file_content),
    data.content_type,
    data.filename
  );
  
  // 2. Find or create folder: ShipName > Crew Records
  var shipFolder = findOrCreateFolder(data.ship_name);
  var crewRecordsFolder = findOrCreateFolder("Crew Records", shipFolder.getId());
  
  // 3. Upload file
  var file = crewRecordsFolder.createFile(fileBlob);
  
  // 4. Return file_id
  return createJsonResponse(true, "Certificate uploaded", {
    file_id: file.getId(),
    file_name: file.getName(),
    folder_path: data.ship_name + "/Crew Records"
  });
}
```

**Option 2: Dùng lại analyze_certificate_document_ai**
- ✅ Action này ĐÃ CÓ upload file logic
- ✅ Backend chỉ cần parse response để lấy file_id
- ⚠️ Cần check Apps Script có return file_id không

**Option 3: Tách riêng 2 bước**
- Step 1: Analyze → Get summary
- Step 2: Upload → Get file_id (dùng action khác)

---

### 🟡 **Frontend Features Chưa Hoàn Chỉnh**

#### **1. Default Filter cho Selected Crew** ⚠️
**Hiện tại:**
- ✅ Backend hỗ trợ filter by crew_id
- ❌ Frontend chưa tự động filter

**Cần làm:**
```javascript
// When switching to Certificates view
const fetchCrewCertificates = async (crewId) => {
  const response = await axios.get(
    `${API}/crew-certificates/${shipId}?crew_id=${crewId}`,  // ← Add crew_id filter
    { headers: { Authorization: `Bearer ${token}` }}
  );
  setCrewCertificates(response.data);
};
```

---

#### **2. Context Menu** ❌ **CHƯA CÓ**

**Cần implement:**
- ❌ Right-click context menu on certificate rows
- ❌ Options:
  - Edit Certificate
  - Delete Certificate
  - View Certificate File
  - Copy Link
  - Download File
- ❌ Bulk operations (select multiple)

**Tương tự như Crew List context menu**

---

#### **3. Search/Filter Functionality** ❌ **CHƯA CÓ**

**UI đã có:**
- ✅ Search input field visible in UI

**Chưa có:**
- ❌ Search logic for crew_name, cert_name
- ❌ Filter dropdown (by status, by cert type)
- ❌ Real-time search as user types

**Cần implement:**
```javascript
const filteredCertificates = crewCertificates.filter(cert => {
  const matchesSearch = 
    cert.crew_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cert.cert_name.toLowerCase().includes(searchTerm.toLowerCase());
  return matchesSearch;
});
```

---

#### **4. Sorting** ⚠️ **PARTIAL**

**Hiện tại:**
- ✅ Table columns có sorting icons
- ❌ Sorting logic chưa hoàn chỉnh

**Cần làm:**
- ❌ Sort by expiry date
- ❌ Sort by status
- ❌ Sort by crew name
- ❌ Sort by cert name

---

#### **5. Bulk Operations** ❌ **CHƯA CÓ**

**Backend đã có:**
- ✅ Bulk delete endpoint

**Frontend chưa có:**
- ❌ Checkbox selection for multiple certificates
- ❌ Bulk delete button
- ❌ Bulk edit (if needed)
- ❌ Select all / deselect all

---

#### **6. View/Download Certificate Files** ❌ **CHƯA CÓ**

**Backend có:**
- ✅ cert_file_id stored in database

**Frontend chưa có:**
- ❌ "View File" button/link
- ❌ Open file in Google Drive
- ❌ Download file
- ❌ Copy Drive link

**Cần implement:**
```javascript
const handleViewCertificateFile = (certFileId) => {
  const driveUrl = `https://drive.google.com/file/d/${certFileId}/view`;
  window.open(driveUrl, '_blank');
};
```

---

## 📊 TIẾN ĐỘ TỔNG THỂ

### ✅ **ĐÃ HOÀN THÀNH (80%)**

#### Backend:
- ✅ CRUD API endpoints (Create, Read, Update, Delete)
- ✅ AI Analysis endpoint (analyze-file)
- ✅ Document AI integration
- ✅ System AI field extraction
- ✅ Certificate type detection
- ✅ Status calculation logic
- ✅ Date standardization
- ✅ Audit logging
- ✅ Bulk delete

#### Frontend:
- ✅ Add Crew Certificate modal UI
- ✅ File upload (drag & drop)
- ✅ Manual entry form
- ✅ Auto-fill from AI analysis
- ✅ Form validation
- ✅ Submit to backend
- ✅ Display certificates table
- ✅ Basic UI/UX

---

### ❌ **CHƯA HOÀN THÀNH (20%)**

#### Backend:
- ❌ Google Drive file upload (`upload_crew_certificate` action)
- ⚠️ Hoặc parse file_id từ analyze_certificate_document_ai response

#### Frontend:
- ❌ Default filter for selected crew
- ❌ Context menu (Edit/Delete/View/Download/Copy)
- ❌ Search/filter functionality
- ❌ Complete sorting implementation
- ❌ Bulk operations UI (checkbox selection)
- ❌ View/Download certificate files
- ❌ Copy Drive link

---

## 🎯 PRIORITY ACTION ITEMS

### 🔴 **HIGH PRIORITY (Blocking)**

1. **Fix Google Drive File Upload** ⚠️
   - Option A: Implement `upload_crew_certificate` in Apps Script
   - Option B: Parse file_id from `analyze_certificate_document_ai` response
   - Option C: Use separate upload action

### 🟡 **MEDIUM PRIORITY (Important)**

2. **Default Filter for Selected Crew**
   - Add crew_id to API call when crew is selected

3. **Context Menu Implementation**
   - Right-click menu with Edit/Delete/View options

4. **Search & Filter**
   - Real-time search for crew/cert names
   - Filter by status

### 🟢 **LOW PRIORITY (Nice to Have)**

5. **View/Download Files**
   - Open files in Google Drive
   - Download files
   - Copy Drive links

6. **Bulk Operations UI**
   - Checkbox selection
   - Bulk delete button

7. **Enhanced Sorting**
   - Multi-column sorting
   - Sort indicators

---

## 🧪 TESTING STATUS

### ✅ **Đã Test**
- ✅ Manual entry workflow
- ✅ Backend CRUD operations
- ✅ AI extraction accuracy (100% for COC)

### ❌ **Chưa Test**
- ❌ File upload end-to-end với Apps Script mới
- ❌ Auto-fill từ AI analysis
- ❌ Context menu operations
- ❌ Bulk operations
- ❌ Search/filter

---

## 📝 NOTES

1. **Apps Script Action Issue là blocking issue chính**
   - Cần fix trước khi test end-to-end

2. **Frontend features còn lại có thể implement song song**
   - Không phụ thuộc vào nhau

3. **Backend đã sẵn sàng**
   - Chỉ cần fix file upload action

4. **Priority:**
   - Fix file upload > Default filter > Context menu > Search > Bulk ops > View/Download

---

**Bạn muốn tôi bắt đầu từ đâu? Fix Apps Script file upload hay implement frontend features?**
