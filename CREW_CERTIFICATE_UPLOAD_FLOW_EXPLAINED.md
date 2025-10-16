# Logic xử lí Add Crew Certificate

## 📋 OVERVIEW
Crew Certificate upload flow ĐÃ ĐƯỢC REFACTOR giống như Passport flow:
- **Analyze FIRST** (không upload)
- **Create Certificate** trong database
- **Upload files** SAU KHI certificate được tạo thành công

---

## ✅ FLOW HIỆN TẠI (Đã Refactored)

### BATCH UPLOAD FLOW (Multiple Files)

#### Step 1: User chọn nhiều files certificate
**Frontend: File selection (App.js)**
```javascript
// User chọn multiple files từ file input
// Trigger startCertBatchProcessing()
```

#### Step 2: Frontend xử lý batch với staggered parallel
**Frontend: `startCertBatchProcessing()` (App.js line ~6683)**
```javascript
const startCertBatchProcessing = async (files) => {
  setIsBatchProcessing(true);
  setBatchProgress({ current: 0, total: files.length });
  
  // Parallel processing với 2s staggered delay
  const processingPromises = files.map((file, index) => {
    return new Promise(async (resolve) => {
      // Stagger start: 0s, 2s, 4s, 6s...
      const delayMs = index * 2000;
      if (delayMs > 0) {
        await new Promise(r => setTimeout(r, delayMs));
      }
      
      // Process this file
      const result = await processSingleCertInBatch(
        file, 
        index + 1, 
        files.length, 
        crewList
      );
      
      setBatchResults(prev => [...prev, result]);
      resolve(result);
    });
  });
  
  // Wait for all files to complete
  await Promise.all(processingPromises);
  
  // Show results modal
  setShowCertProcessingResultsModal(true);
}
```

#### Step 3: Process mỗi certificate file
**Frontend: `processSingleCertInBatch()` (App.js line ~6772)**
```javascript
const processSingleCertInBatch = async (file, current, total, crewDataList) => {
  
  // 1. Get crew info
  const crewId = selectedCrewForCert?.id;
  const crewName = selectedCrewForCert?.full_name;
  const crewNameEn = selectedCrewForCert?.full_name_en;
  const rank = selectedCrewForCert?.rank;
  
  // 2. Analyze certificate (NO UPLOAD)
  const formData = new FormData();
  formData.append('cert_file', file);
  formData.append('ship_id', selectedShip?.id);
  formData.append('crew_id', crewId);
  
  const response = await axios.post(
    `${API}/crew-certificates/analyze-file`,
    formData
  );
  
  if (response.data.success && response.data.analysis) {
    const analysis = response.data.analysis;
    
    // 3. Prepare certificate data
    const certData = {
      crew_id: crewId,
      crew_name: response.data.crew_name || crewName,
      crew_name_en: response.data.crew_name_en || crewNameEn,
      passport: response.data.passport,
      rank: analysis.rank || rank,
      cert_name: analysis.cert_name,
      cert_no: analysis.cert_no,
      issued_by: analysis.issued_by,
      issued_date: analysis.issued_date,
      cert_expiry: analysis.expiry_date,
      note: analysis.note,
      // ⚠️ NO file_ids - will be updated after upload
      crew_cert_file_id: '',
      crew_cert_summary_file_id: ''
    };
    
    // 4. Check for duplicate
    const duplicateCheck = await axios.post(
      `${API}/crew-certificates/check-duplicate`,
      { crew_id: certData.crew_id, cert_no: certData.cert_no }
    );
    
    if (duplicateCheck.data.is_duplicate) {
      // Skip duplicate
      return {
        filename: file.name,
        success: false,
        error: 'DUPLICATE',
        duplicateInfo: {...}
      };
    }
    
    // 5. Create certificate in database (WITHOUT file_ids)
    const createResponse = await axios.post(
      `${API}/crew-certificates/manual?ship_id=${selectedShip.id}`,
      certData
    );
    
    const certId = createResponse.data.id;
    console.log(`✅ Certificate created: ${certId}`);
    
    // 6. ✅ Upload files AFTER successful database save
    try {
      const uploadResponse = await axios.post(
        `${API}/crew-certificates/${certId}/upload-files`,
        {
          file_content: analysis._file_content,     // base64
          filename: analysis._filename,
          content_type: analysis._content_type,
          summary_text: analysis._summary_text
        }
      );
      
      if (uploadResponse.data.success) {
        console.log(`✅ Files uploaded to Drive`);
        return {
          filename: file.name,
          success: true,
          certCreated: true,
          fileUploaded: true,
          certName: certData.cert_name,
          certNo: certData.cert_no
        };
      }
    } catch (uploadError) {
      // Certificate saved, but upload failed (non-critical)
      console.error(`⚠️ Upload failed but cert saved`);
      return {
        filename: file.name,
        success: true,
        certCreated: true,
        fileUploaded: false
      };
    }
  }
}
```

#### Step 4: Backend analyze certificate (NO UPLOAD)
**Backend: `POST /crew-certificates/analyze-file` (server.py line ~13070)**
```python
@api_router.post("/crew-certificates/analyze-file")
async def analyze_certificate_file_for_crew(
    cert_file: UploadFile = File(...),
    ship_id: str = Form(...),
    crew_id: str = Form(None),
    current_user: UserResponse = Depends(...)
):
    """
    Analyze crew certificate WITHOUT uploading to Drive
    """
    
    # 1. Read file content
    file_content = await cert_file.read()
    filename = cert_file.filename
    
    # 2. Get ship and crew information
    ship = await mongo_db.find_one("ships", {
        "id": ship_id,
        "company_id": company_uuid
    })
    ship_name = ship.get("name")
    
    crew = await mongo_db.find_one("crew_members", {"id": crew_id})
    crew_name = crew.get("full_name")
    crew_name_en = crew.get("full_name_en")
    passport = crew.get("passport")
    
    # 3. Get AI configuration
    ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
    document_ai_config = ai_config_doc.get("document_ai", {})
    
    # 4. Use Dual Apps Script Manager for AI analysis ONLY
    dual_manager = create_dual_apps_script_manager(company_uuid)
    
    analysis_only_result = await dual_manager.analyze_certificate_only(
        file_content=file_content,
        filename=filename,
        content_type=cert_file.content_type,
        document_ai_config=document_ai_config
    )
    
    # 5. Extract fields from AI summary
    summary_text = analysis_only_result['ai_analysis']['data']['summary']
    
    cert_type = detect_certificate_type(filename, summary_text)
    
    extracted_fields = await extract_crew_certificate_fields_from_summary(
        summary_text,
        cert_type,
        ai_provider,
        ai_model,
        use_emergent_key
    )
    
    analysis_result.update(extracted_fields)
    
    # 6. ✅ Store file content for later upload (NOT uploaded yet!)
    analysis_result['_file_content'] = base64.b64encode(file_content).decode('utf-8')
    analysis_result['_filename'] = filename
    analysis_result['_content_type'] = cert_file.content_type
    analysis_result['_summary_text'] = summary_text
    analysis_result['_ship_name'] = ship_name
    
    # 7. Normalize issued_by field
    analysis_result = normalize_issued_by(analysis_result)
    
    return {
        "success": True,
        "analysis": analysis_result,
        "crew_name": crew_name,
        "crew_name_en": crew_name_en,
        "passport": passport,
        "message": "Certificate analyzed successfully (files NOT uploaded yet)"
    }
```

**Dual Apps Script Manager: `analyze_certificate_only()` (dual_apps_script_manager.py line ~616)**
```python
async def analyze_certificate_only(
    self, 
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze certificate with Document AI WITHOUT uploading to Drive
    """
    await self._load_configuration()
    
    if not self.system_apps_script_url:
        raise ValueError("System AI Apps Script URL not configured")
    
    # Call System AI Apps Script for Document AI analysis
    ai_analysis_result = await self._call_system_apps_script({
        'action': 'analyze_certificate_document_ai',
        'file_content': base64.b64encode(file_content).decode('utf-8'),
        'filename': filename,
        'content_type': content_type,
        'project_id': document_ai_config.get("project_id"),
        'location': document_ai_config.get("location", "us"),
        'processor_id': document_ai_config.get("processor_id")
    })
    
    # Return AI analysis result ONLY (no file uploads)
    return {
        'success': True,
        'ai_analysis': ai_analysis_result,
        'message': 'Certificate analyzed successfully (no upload)'
    }
```

#### Step 5: Backend upload files to Drive
**Backend: `POST /crew-certificates/{cert_id}/upload-files` (server.py line ~13312)**
```python
@api_router.post("/crew-certificates/{cert_id}/upload-files")
async def upload_certificate_files_after_creation(
    cert_id: str,
    file_data: dict,
    current_user: UserResponse = Depends(...)
):
    """
    Upload certificate files AFTER successful certificate creation
    """
    
    # 1. Verify certificate exists
    cert = await mongo_db.find_one("crew_certificates", {
        "id": cert_id,
        "company_id": company_uuid
    })
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    # 2. Get ship info
    ship = await mongo_db.find_one("ships", {"id": cert.get("ship_id")})
    ship_name = ship.get("name")
    
    # 3. Extract file data from request
    file_content_b64 = file_data.get('file_content')
    filename = file_data.get('filename')
    content_type = file_data.get('content_type')
    summary_text = file_data.get('summary_text')
    
    # 4. Decode file content
    file_content = base64.b64decode(file_content_b64)
    
    # 5. Upload files using dual manager
    dual_manager = create_dual_apps_script_manager(company_uuid)
    
    upload_result = await dual_manager.upload_certificate_files(
        cert_file_content=file_content,
        cert_filename=filename,
        cert_content_type=content_type,
        ship_name=ship_name,
        summary_text=summary_text
    )
    
    # 6. Extract file IDs from upload results
    cert_file_id = upload_result['uploads']['certificate'].get('file_id')
    summary_file_id = upload_result['uploads']['summary'].get('file_id')
    
    # 7. Update certificate with file IDs
    await mongo_db.update("crew_certificates", {"id": cert_id}, {
        'crew_cert_file_id': cert_file_id,
        'crew_cert_summary_file_id': summary_file_id,
        'updated_at': datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "crew_cert_file_id": cert_file_id,
        "crew_cert_summary_file_id": summary_file_id
    }
```

**Dual Apps Script Manager: `upload_certificate_files()` (dual_apps_script_manager.py line ~650)**
```python
async def upload_certificate_files(
    self,
    cert_file_content: bytes,
    cert_filename: str,
    cert_content_type: str,
    ship_name: str,
    summary_text: Optional[str] = None
) -> Dict[str, Any]:
    """Upload certificate files to Drive AFTER crew creation"""
    
    await self._load_configuration()
    
    upload_results = {}
    
    # Upload 1: Certificate file to Ship/Crew Records
    logger.info(f"📤 Uploading certificate: {ship_name}/Crew Records/{cert_filename}")
    cert_upload = await self._call_company_apps_script({
        'action': 'upload_file_with_folder_creation',
        'parent_folder_id': self.parent_folder_id,
        'ship_name': ship_name,               # e.g., "BROTHER 36"
        'category': 'Crew Records',            # Direct path
        'filename': cert_filename,
        'file_content': base64.b64encode(cert_file_content).decode('utf-8'),
        'content_type': cert_content_type
    })
    upload_results['certificate'] = cert_upload
    
    # Upload 2: Summary file to SUMMARY/Crew Records
    if summary_text:
        base_name = cert_filename.rsplit('.', 1)[0]
        summary_filename = f"{base_name}_Summary.txt"
        
        logger.info(f"📋 Uploading summary: SUMMARY/Crew Records/{summary_filename}")
        summary_upload = await self._call_company_apps_script({
            'action': 'upload_file_with_folder_creation',
            'parent_folder_id': self.parent_folder_id,
            'ship_name': 'SUMMARY',
            'category': 'Crew Records',
            'filename': summary_filename,
            'file_content': base64.b64encode(summary_text.encode('utf-8')).decode('utf-8'),
            'content_type': 'text/plain'
        })
        upload_results['summary'] = summary_upload
    
    return {
        'success': True,
        'uploads': upload_results
    }
```

#### Step 6: Apps Script uploads to Google Drive
**Apps Script: `handleUploadFixed()` (COMPLETE_GOOGLE_APPS_SCRIPT_V4_MERGED.js)**
```javascript
function handleUploadFixed(requestData) {
  var shipName = requestData.ship_name;        // "BROTHER 36" or "SUMMARY"
  var category = requestData.category;         // "Crew Records"
  var filename = requestData.filename;
  var fileContent = requestData.file_content;
  var parentFolderId = requestData.parent_folder_id;
  
  // 1. Get parent folder
  var parentFolder = DriveApp.getFolderById(parentFolderId);
  
  // 2. Find or create ship folder
  var shipFolder = findOrCreateFolderSafe(parentFolder, shipName);
  
  // 3. Handle Crew Records special case
  var targetFolder;
  var normalizedCategory = category.trim();
  
  if (normalizedCategory === "Crew Records" || normalizedCategory === "Crew records") {
    // ✅ Create direct path: Ship/Crew Records
    Logger.log("📁 Creating Crew Records (direct): " + shipName + "/Crew Records");
    targetFolder = createFolderPathSafe(shipFolder, ["Crew Records"]);
  } else {
    // Other categories may use nested structure
    // ...
  }
  
  // 4. Upload file
  var binaryData = Utilities.base64Decode(fileContent);
  var blob = Utilities.newBlob(binaryData, "application/pdf", filename);
  var uploadedFile = targetFolder.createFile(blob);
  
  return {
    success: true,
    file_id: uploadedFile.getId(),
    folder_path: shipName + "/Crew Records"
  };
}
```

---

## 📂 FOLDER STRUCTURE

### Certificate Files:
```
📁 [Company Drive Root]
├── 📁 BROTHER 36
│   └── 📁 Crew Records
│       ├── 📄 COC_Certificate_John.pdf
│       ├── 📄 STCW_Certificate_Mary.pdf
│       └── 📄 Medical_Certificate_Tom.pdf
│
└── 📁 SUMMARY
    └── 📁 Crew Records
        ├── 📄 COC_Certificate_John_Summary.txt
        ├── 📄 STCW_Certificate_Mary_Summary.txt
        └── 📄 Medical_Certificate_Tom_Summary.txt
```

---

## ✨ KEY FEATURES

### 1. Staggered Parallel Processing
- Multiple files được xử lý song song
- Mỗi file bắt đầu cách nhau 2 giây
- Giảm tải cho backend và Document AI API

### 2. Duplicate Detection
- Check duplicate trước khi tạo certificate
- Based on: `crew_id` + `cert_no`
- Skip duplicates trong batch mode
- Warn user trong single file mode

### 3. File Upload AFTER Database Save
- ✅ Analyze certificate → AI extraction
- ✅ Create certificate trong database
- ✅ Upload files to Drive (only if cert created)
- ✅ Update certificate với file IDs

### 4. Error Handling
- Certificate được lưu ngay cả khi upload thất bại
- Upload failure không làm certificate bị mất
- Detailed error reporting trong results modal

### 5. Processing Results Modal
- Shows detailed results cho mỗi file
- Status: Success / Duplicate / Error
- File upload status
- Certificate details (name, number, expiry)

---

## 🔍 SO SÁNH VỚI PASSPORT FLOW

| Feature | Passport Flow | Certificate Flow |
|---------|---------------|------------------|
| **Analyze endpoint** | `/crew/analyze-passport` | `/crew-certificates/analyze-file` |
| **Upload endpoint** | `/crew/{crew_id}/upload-passport-files` | `/crew-certificates/{cert_id}/upload-files` |
| **Stagger delay** | 1 second | 2 seconds |
| **Validation** | Passport vs Seaman book | Certificate type detection |
| **Duplicate check** | Passport number | crew_id + cert_no |
| **File location** | Ship/Crew Records | Ship/Crew Records |
| **Summary location** | SUMMARY/Crew Records | SUMMARY/Crew Records |

**Cả 2 flows đều:**
- ✅ Analyze FIRST (không upload)
- ✅ Create record trong database
- ✅ Upload files SAU KHI record created
- ✅ Tránh orphaned files
- ✅ Consistent folder structure

---

## 🎯 BENEFITS

1. **No Orphaned Files**: Files chỉ upload SAU KHI certificate được tạo thành công
2. **Data Integrity**: Certificate data luôn được lưu trước
3. **Error Recovery**: Upload thất bại không làm mất certificate data
4. **Consistent Structure**: Giống với Passport flow
5. **Better UX**: Detailed progress và results feedback
6. **Scalability**: Parallel processing với rate limiting

---

## 📝 NOTES

- Certificate type được detect tự động từ filename và content
- Issued By field được normalize để consistent
- Status được tính tự động based on expiry date
- Supports multiple certificate types: COC, COE, STCW, Medical, GMDSS, etc.
- English và Vietnamese crew names đều được lưu
