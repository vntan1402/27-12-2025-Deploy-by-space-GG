# Logic xử lí Add Crew from Passport

## 📋 OVERVIEW
Có 2 flows để Add Crew from Passport:
1. **Single File Upload** - User chọn 1 file, xem trước, rồi submit
2. **Batch Upload** - User chọn nhiều files, tự động xử lí song song

---

## 🔄 FLOW CŨ (Trước Refactoring)
### Step 1: User chọn file passport
- **Location**: Frontend `handlePassportUpload()`
- **Action**: Upload file ngay lập tức

### Step 2: Backend analyze VÀ upload files
- **Endpoint**: `POST /crew/analyze-passport`
- **Actions**:
  1. Analyze passport với Document AI
  2. **Upload files lên Drive NGAY** (passport + summary)
  3. Return analysis data + file_ids

### Step 3: Frontend tạo crew
- **Action**: Submit form với file_ids đã có
- **Endpoint**: `POST /crew`
- **Problem**: Nếu crew creation fail → **orphaned files trên Drive!**

---

## ✅ FLOW MỚI (Sau Refactoring)
### SINGLE FILE FLOW

#### Step 1: User chọn file passport
**Frontend: `handlePassportUpload()` (App.js line ~5372)**
```javascript
const handlePassportUpload = async (file) => {
  // 1. Reset states
  setPassportAnalysis(null);
  setIsAnalyzingPassport(true);
  
  // 2. Create FormData
  const formData = new FormData();
  formData.append('passport_file', file);
  formData.append('ship_name', selectedShip?.name);
  
  // 3. Call backend to analyze (NO UPLOAD)
  const response = await axios.post(`${API}/crew/analyze-passport`, formData);
  
  // 4. Validate passport (not seaman book)
  const validation = validatePassportDocument(analysis);
  if (!validation.isValid) {
    // Stop if not a passport
    return;
  }
  
  // 5. Store analysis with FILE CONTENT (not file_ids)
  const analysisWithFiles = {
    ...analysis,
    _file_content: analysis._file_content,  // base64
    _filename: analysis._filename,
    _content_type: analysis._content_type,
    _summary_text: analysis._summary_text,
    _ship_name: analysis._ship_name
  };
  
  setPassportAnalysis(analysisWithFiles);
  
  // 6. Auto-fill form
  setNewCrewData({
    full_name: analysis.full_name || '',
    full_name_en: autoFillEnglishField(analysis.full_name),
    // ... other fields
  });
}
```

#### Step 2: Backend analyze passport (NO UPLOAD)
**Backend: `/crew/analyze-passport` (server.py line ~11383)**
```python
@api_router.post("/crew/analyze-passport")
async def analyze_passport_for_crew(...):
    # 1. Read file content
    file_content = await passport_file.read()
    
    # 2. Check for duplicate passport
    if passport_number:
        existing_crew = await mongo_db.find_one("crew_members", {
            "company_id": company_uuid,
            "passport": passport_number
        })
        if existing_crew:
            return {"duplicate": True, "existing_crew": {...}}
    
    # 3. Use Dual Apps Script Manager for AI analysis ONLY
    dual_manager = create_dual_apps_script_manager(company_uuid)
    
    analysis_only_result = await dual_manager.analyze_passport_only(
        file_content=file_content,
        filename=filename,
        content_type=passport_file.content_type,
        document_ai_config=document_ai_config
    )
    
    # 4. Extract fields from AI summary
    extracted_fields = await extract_maritime_document_fields_from_summary(
        summary_text, "passport", ai_provider, ai_model, use_emergent_key
    )
    
    # 5. Store file content for later upload (NOT uploaded yet!)
    analysis_result['_file_content'] = base64.b64encode(file_content).decode('utf-8')
    analysis_result['_filename'] = filename
    analysis_result['_content_type'] = passport_file.content_type
    analysis_result['_summary_text'] = summary_text
    analysis_result['_ship_name'] = ship_name
    analysis_result['raw_summary'] = summary_text  # For frontend validation
    
    return {
        "success": True,
        "analysis": analysis_result,
        "processing_method": "analysis_only_no_upload",
        "message": "Passport analyzed successfully (files will be uploaded after crew creation)"
    }
```

**Dual Apps Script Manager: `analyze_passport_only()` (dual_apps_script_manager.py line ~763)**
```python
async def analyze_passport_only(
    self, file_content, filename, content_type, document_ai_config
) -> Dict[str, Any]:
    """
    Analyze passport with Document AI WITHOUT uploading to Drive
    """
    # Call System AI Apps Script for Document AI analysis
    ai_analysis_result = await self._call_system_apps_script({
        'action': 'analyze_passport_document_ai',
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
        'message': 'Passport analyzed successfully (no upload)'
    }
```

#### Step 3: User clicks "Add Crew" button
**Frontend: `handleAddCrewSubmit()` (App.js line ~5505)**
```javascript
const handleAddCrewSubmit = async () => {
  // 1. Validate form
  if (!newCrewData.full_name || !newCrewData.passport) {
    toast.error('Please fill required fields!');
    return;
  }
  
  // 2. Process dates
  const processedData = {
    ...newCrewData,
    date_of_birth: convertDateInputToUTC(newCrewData.date_of_birth.split('T')[0]),
    // ... other dates
  };
  
  // 3. Create crew WITHOUT file_ids
  const response = await axios.post(`${API}/crew`, processedData);
  const crewId = response.data.id;
  
  // 4. ✅ NEW: Upload passport files AFTER crew creation
  if (passportAnalysis?._file_content) {
    try {
      const uploadResponse = await axios.post(
        `${API}/crew/${crewId}/upload-passport-files`,
        {
          file_content: passportAnalysis._file_content,
          filename: passportAnalysis._filename,
          content_type: passportAnalysis._content_type,
          summary_text: passportAnalysis._summary_text,
          ship_name: passportAnalysis._ship_name || selectedShip?.name
        }
      );
      
      if (uploadResponse.data.success) {
        console.log(`✅ Passport files uploaded`);
      } else {
        // Crew saved, but file upload failed (non-critical)
        toast.warning('Crew added but file upload failed');
      }
    } catch (uploadError) {
      // Don't throw - crew is already saved
      toast.warning('Crew added but file upload failed');
    }
  }
  
  // 5. Refresh crew list and close modal
  await fetchCrewMembers(selectedShip.name);
  resetAddCrewForm();
  setShowAddCrewModal(false);
}
```

#### Step 4: Backend upload files to Drive
**Backend: `/crew/{crew_id}/upload-passport-files` (server.py line ~12371)**
```python
@api_router.post("/crew/{crew_id}/upload-passport-files")
async def upload_passport_files_after_creation(crew_id: str, file_data: dict, ...):
    # 1. Verify crew exists
    crew = await mongo_db.find_one("crew_members", {
        "id": crew_id,
        "company_id": company_uuid
    })
    if not crew:
        raise HTTPException(status_code=404, detail="Crew member not found")
    
    # 2. Extract file data
    file_content_b64 = file_data.get('file_content')
    filename = file_data.get('filename')
    content_type = file_data.get('content_type')
    summary_text = file_data.get('summary_text')
    ship_name = file_data.get('ship_name')
    
    # 3. Decode file content
    file_content = base64.b64decode(file_content_b64)
    
    # 4. Upload files using dual manager
    dual_manager = create_dual_apps_script_manager(company_uuid)
    upload_result = await dual_manager.upload_passport_files(
        passport_file_content=file_content,
        passport_filename=filename,
        passport_content_type=content_type,
        ship_name=ship_name,
        summary_text=summary_text
    )
    
    # 5. Extract file IDs from upload results
    passport_file_id = upload_result['uploads']['passport'].get('file_id')
    summary_file_id = upload_result['uploads']['summary'].get('file_id')
    
    # 6. Update crew with file IDs
    await mongo_db.update("crew_members", {"id": crew_id}, {
        'passport_file_id': passport_file_id,
        'summary_file_id': summary_file_id,
        'updated_at': datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "passport_file_id": passport_file_id,
        "summary_file_id": summary_file_id
    }
```

**Dual Apps Script Manager: `upload_passport_files()` (dual_apps_script_manager.py line ~802)**
```python
async def upload_passport_files(
    self, passport_file_content, passport_filename, passport_content_type, 
    ship_name, summary_text
) -> Dict[str, Any]:
    """Upload passport files to Drive AFTER crew creation"""
    
    upload_results = {}
    
    # Upload 1: Passport file to Ship/Crew Records
    logger.info(f"📤 Uploading passport file: {ship_name}/Crew Records/{passport_filename}")
    passport_upload = await self._call_company_apps_script({
        'action': 'upload_file_with_folder_creation',
        'parent_folder_id': self.parent_folder_id,
        'ship_name': ship_name,
        'category': 'Crew Records',  # ⚠️ This should create Ship/Crew Records
        'filename': passport_filename,
        'file_content': base64.b64encode(passport_file_content).decode('utf-8'),
        'content_type': passport_content_type
    })
    upload_results['passport'] = passport_upload
    
    # Upload 2: Summary file to SUMMARY/Crew Records
    if summary_text:
        summary_filename = f"{passport_filename.rsplit('.', 1)[0]}_Summary.txt"
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

#### Step 5: Apps Script uploads to Google Drive
**Apps Script: `handleUploadFixed()` (COMPLETE_GOOGLE_APPS_SCRIPT_V4_MERGED.js line ~128)**
```javascript
function handleUploadFixed(requestData) {
  // 1. Extract parameters
  var shipName = requestData.ship_name;        // "BROTHER 36" or "SUMMARY"
  var category = requestData.category;         // "Crew Records"
  var filename = requestData.filename;
  var fileContent = requestData.file_content;
  var parentFolderId = requestData.parent_folder_id;
  
  // 2. Get parent folder
  var parentFolder = DriveApp.getFolderById(parentFolderId);
  
  // 3. Find or create ship folder
  var shipFolder = findOrCreateFolderSafe(parentFolder, shipName);
  // Result: Creates "BROTHER 36" or "SUMMARY" folder
  
  // 4. Determine target folder based on category
  var targetFolder;
  if (category) {
    // Normalize category name
    var normalizedCategory = category.trim();
    
    // ⚠️ CRITICAL CHECK: Is this Crew Records?
    if (normalizedCategory === "Crew Records" || normalizedCategory === "Crew records") {
      // Create direct path: Ship/Crew Records
      Logger.log("📁 Creating Crew Records (direct path): " + shipName + "/Crew Records");
      targetFolder = createFolderPathSafe(shipFolder, ["Crew Records"]);
      // ✅ Should create: BROTHER 36/Crew Records
      
    } else if (!parentCategory) {
      // ⚠️ FOR OTHER CATEGORIES: Try to find "Class & Flag Cert" first
      var classFlagFolder = findFolderByNameSafe(shipFolder, "Class & Flag Cert");
      if (classFlagFolder) {
        // Found Class & Flag Cert → use nested structure
        Logger.log("📁 Using Class & Flag Cert structure");
        targetFolder = findOrCreateFolderSafe(classFlagFolder, normalizedCategory);
        // Result: BROTHER 36/Class & Flag Cert/[category]
      } else {
        // No Class & Flag Cert → create direct
        targetFolder = createFolderPathSafe(shipFolder, [normalizedCategory]);
      }
    }
  }
  
  // 5. Upload file to target folder
  var binaryData = Utilities.base64Decode(fileContent);
  var blob = Utilities.newBlob(binaryData, "application/pdf", filename);
  var uploadedFile = targetFolder.createFile(blob);
  
  return {
    success: true,
    file_id: uploadedFile.getId(),
    folder_path: shipName + "/Crew Records"  // or actual path
  };
}

function createFolderPathSafe(parentFolder, folderNames) {
  var currentFolder = parentFolder;
  
  for (var i = 0; i < folderNames.length; i++) {
    var folderName = folderNames[i];
    
    // ✅ IMPORTANT: Check if folder exists first
    var existingFolder = findFolderByNameSafe(currentFolder, folderName);
    
    if (existingFolder) {
      Logger.log("   ✅ Found existing: " + folderName);
      currentFolder = existingFolder;
    } else {
      Logger.log("   🆕 Creating new: " + folderName);
      currentFolder = currentFolder.createFolder(folderName);
    }
  }
  
  return currentFolder;
}
```

---

## 🔄 BATCH UPLOAD FLOW

### Frontend: `processSinglePassportInBatch()` (App.js line ~5179)
```javascript
const processSinglePassportInBatch = async (file, current, total) => {
  // 1. Analyze passport (same as single file)
  const response = await axios.post(`${API}/crew/analyze-passport`, formData);
  const analysis = response.data.analysis;
  
  // 2. Validate passport
  const validation = validatePassportDocument(analysis);
  if (!validation.isValid) {
    return { success: false, error: 'NOT_PASSPORT' };
  }
  
  // 3. Create crew WITHOUT file_ids
  const crewData = {
    full_name: analysis.full_name,
    passport: analysis.passport_number,
    // ... other fields
  };
  
  const createResponse = await axios.post(`${API}/crew`, crewData);
  const crewId = createResponse.data.id;
  
  // 4. ✅ Upload files AFTER crew creation
  try {
    const uploadResponse = await axios.post(
      `${API}/crew/${crewId}/upload-passport-files`,
      {
        file_content: analysis._file_content,
        filename: analysis._filename,
        content_type: analysis._content_type,
        summary_text: analysis._summary_text,
        ship_name: analysis._ship_name
      }
    );
    
    return {
      filename: file.name,
      success: true,
      recordCreated: true,
      fileUploaded: !!uploadResponse.data.passport_file_id
    };
  } catch (uploadError) {
    // Crew saved, but upload failed
    return {
      filename: file.name,
      success: true,
      recordCreated: true,
      fileUploaded: false
    };
  }
}
```

---

## 🐛 VẤN ĐỀ HIỆN TẠI

### Symptoms:
Files được lưu vào: `BROTHER 36/Class & Flag Cert/Crew Records/passport.pdf`
Thay vì: `BROTHER 36/Crew Records/passport.pdf`

### Possible Causes:

1. **Apps Script chưa được cập nhật**
   - Bạn có thể chưa copy code mới vào Google Apps Script Editor
   - Hoặc đang dùng Apps Script URL cũ

2. **Logic fallback trong Apps Script**
   - Line 188-192: Nếu tìm thấy folder "Class & Flag Cert", sẽ dùng nested structure
   - Điều này xảy ra khi:
     - `category !== "Crew Records"` (case sensitivity)
     - Hoặc có khoảng trắng thừa trong tên

3. **Request parameters sai**
   - Backend gửi `category` với tên khác
   - Hoặc có `parent_category` được set

### Debug Steps:

1. **Check Apps Script logs**
   - Xem request nhận được category là gì
   - Xem logic nào được chạy (direct path hay nested)

2. **Check backend logs**
   - Xem backend gửi category là gì
   - Line: `logger.info(f"📤 Uploading passport file: {ship_name}/Crew Records/{passport_filename}")`

3. **Verify Apps Script URL**
   - Đảm bảo đang dùng Apps Script mới nhất
   - Check trong `company_gdrive_config` collection

---

## ✅ EXPECTED RESULT

```
📁 [Company Drive Root]
├── 📁 BROTHER 36
│   └── 📁 Crew Records
│       └── 📄 passport_nguyen_van_a.pdf
│
└── 📁 SUMMARY
    └── 📁 Crew Records
        └── 📄 passport_nguyen_van_a_Summary.txt
```

---

## 🔍 NEXT STEPS

1. Kiểm tra Apps Script có được cập nhật chưa
2. Check backend logs để xem request parameters
3. Check Apps Script logs để xem logic nào được chạy
4. Verify không có duplicate "Crew Records" folders với tên khác nhau
