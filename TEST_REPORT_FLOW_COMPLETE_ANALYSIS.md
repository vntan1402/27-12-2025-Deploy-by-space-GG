# PHÂN TÍCH TOÀN BỘ FLOW "ADD TEST REPORT" - BACKEND V1 & BACKEND MỚI

## Ngày phân tích: 2025
## Mục đích: So sánh và xác minh việc migration từ backend-v1 sang backend mới (modular FastAPI)

---

## 📋 MỤC LỤC

1. [Tổng quan Flow](#1-tổng-quan-flow)
2. [Frontend Flow - React](#2-frontend-flow---react)
3. [Backend V1 Flow (Legacy)](#3-backend-v1-flow-legacy)
4. [Backend Mới Flow (Migrated)](#4-backend-mới-flow-migrated)
5. [Endpoints được sử dụng](#5-endpoints-được-sử-dụng)
6. [Functions & Helpers](#6-functions--helpers)
7. [Document AI Integration](#7-document-ai-integration)
8. [Targeted OCR Process](#8-targeted-ocr-process)
9. [PDF Splitting Logic (>15 pages)](#9-pdf-splitting-logic-15-pages)
10. [File Upload to Google Drive](#10-file-upload-to-google-drive)
11. [Valid Date Calculator](#11-valid-date-calculator)
12. [So sánh Backend V1 vs Backend Mới](#12-so-sánh-backend-v1-vs-backend-mới)
13. [Tổng kết & Khuyến nghị](#13-tổng-kết--khuyến-nghị)

---

## 1. TỔNG QUAN FLOW

### Quy trình tổng thể:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ USER: Chọn tàu → Upload PDF file (Test Report)                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND: Gửi file đến /api/test-reports/analyze-file                  │
│ - FormData: test_report_file, ship_id, bypass_validation               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ BACKEND: Endpoint analyze-file                                          │
│ 1. Validate PDF file (magic bytes, size, format)                       │
│ 2. Check page count → Quyết định split hay không (>15 pages)           │
│ 3. Process with Document AI (Google Cloud)                             │
│ 4. Perform Targeted OCR (Tesseract + pdf2image)                        │
│ 5. Extract fields with System AI (LLM - GPT/Gemini)                    │
│ 6. Calculate Valid Date (based on equipment type + issued_date)        │
│ 7. Normalize issued_by (abbreviation)                                  │
│ 8. Validate ship name/IMO (fuzzy matching)                             │
│ 9. Return: analysis data + base64 file content + summary               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND: Nhận analysis result                                          │
│ - Auto-fill form fields (test_report_name, test_report_no, etc.)       │
│ - Store analyzed data (including _file_content, _summary_text)         │
│ - User có thể chỉnh sửa thủ công nếu cần                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND: User nhấn "Save" → POST /api/test-reports                    │
│ - Create record in database (without file IDs)                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND: Background upload                                             │
│ POST /api/test-reports/{report_id}/upload-files                        │
│ - Body: file_content (base64), filename, content_type, summary_text    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ BACKEND: upload-files endpoint                                          │
│ 1. Decode base64 file content                                          │
│ 2. Upload original file to Google Drive:                               │
│    → ShipName/Class & Flag Cert/Test Report/[filename]                 │
│ 3. Upload summary text file to Google Drive:                           │
│    → SUMMARY/Class & Flag Document/[filename]_Summary.txt              │
│ 4. Update record with file IDs:                                        │
│    - test_report_file_id                                               │
│    - test_report_summary_file_id                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND: Refresh list → Show file icons                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. FRONTEND FLOW - REACT

### File quan trọng:
- **Component**: `/app/frontend/src/components/TestReport/AddTestReportModal.jsx`
- **Service**: `/app/frontend/src/services/testReportService.js`

### Các bước trong Frontend:

#### A. File Upload & Analysis

```javascript
// AddTestReportModal.jsx

// Step 1: User upload file (drag & drop hoặc click)
const handleFileSelect = async (files) => {
  const fileArray = Array.from(files);
  
  // Validate: PDF only, max 50MB
  if (!file.name.endsWith('.pdf') || file.size > 50MB) {
    toast.error('Invalid file');
    return;
  }
  
  // Single file mode
  if (fileArray.length === 1) {
    setUploadedFile(fileArray[0]);
    await analyzeFile(fileArray[0]);
  }
  // Batch mode: multiple files
  else {
    onStartBatchProcessing(fileArray);
  }
};

// Step 2: Call backend analyze endpoint
const analyzeFile = async (file) => {
  // Check software expiry
  if (!checkAndWarn()) {
    setUploadedFile(null);
    return;
  }
  
  setIsAnalyzing(true);
  toast.info('🤖 Analyzing file with AI...');
  
  // Create FormData
  const formData = new FormData();
  formData.append('ship_id', selectedShip.id);
  formData.append('test_report_file', file);
  formData.append('bypass_validation', 'false');
  
  // API call
  const response = await fetch(`${BACKEND_URL}/api/test-reports/analyze-file`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  const data = await response.json();
  
  // Case 1: Ship validation error
  if (data.validation_error) {
    // Show confirmation modal
    // User can bypass or cancel
    return;
  }
  
  // Case 2: Success
  processAnalysisSuccess(data);
};

// Step 3: Auto-fill form với analyzed data
const processAnalysisSuccess = (data) => {
  // Store complete analysis
  setAnalyzedData(data);
  
  // Extract form fields
  const newFormData = {
    test_report_name: data.test_report_name || '',
    report_form: data.report_form || '',
    test_report_no: data.test_report_no || '',
    issued_by: data.issued_by || '',
    issued_date: data.issued_date || '',
    valid_date: data.valid_date || '',
    note: data.note || ''
  };
  
  setFormData(newFormData);
  
  // Show notifications
  if (data._split_info?.was_split) {
    toast.info(`File split into ${data._split_info.chunks_count} chunks`);
  }
  
  if (data._ocr_info?.ocr_success) {
    toast.success('OCR enhancement applied');
  }
  
  toast.success('Analysis complete!');
};
```

#### B. Create Record & Upload Files

```javascript
// Step 4: User clicks Save
const handleSubmit = async (e) => {
  e.preventDefault();
  
  // Validate form
  if (!formData.test_report_name.trim()) {
    toast.error('Please enter test report name');
    return;
  }
  
  setIsSaving(true);
  
  // Create record
  const reportData = {
    ship_id: selectedShip.id,
    test_report_name: formData.test_report_name.trim(),
    report_form: formData.report_form.trim() || null,
    test_report_no: formData.test_report_no.trim() || null,
    issued_by: formData.issued_by.trim() || null,
    issued_date: formData.issued_date || null,
    valid_date: formData.valid_date || null,
    note: formData.note.trim() || null
  };
  
  const createResponse = await testReportService.create(reportData);
  const createdReport = createResponse.data;
  
  toast.success('Test report added successfully');
  
  // Close modal
  onClose();
  
  // Refresh list (first time - without file icons)
  if (onReportAdded) {
    onReportAdded();
  }
  
  // Step 5: Background upload if file exists
  if (uploadedFile && analyzedData && createdReport.id) {
    if (analyzedData._file_content && analyzedData._filename) {
      uploadFilesInBackground(
        createdReport.id,
        analyzedData._file_content,
        analyzedData._filename,
        analyzedData._content_type,
        analyzedData._summary_text || ''
      );
    }
  }
};

// Step 6: Background upload to Google Drive
const uploadFilesInBackground = async (reportId, fileContent, filename, contentType, summaryText) => {
  setTimeout(async () => {
    try {
      toast.info('Uploading files to Google Drive...');
      
      await testReportService.uploadFiles(
        reportId,
        fileContent,
        filename,
        contentType,
        summaryText
      );
      
      toast.success('File upload complete!');
      
      // Refresh list again to show file icons
      if (onReportAdded) {
        onReportAdded();
      }
    } catch (error) {
      console.error('Failed to upload file:', error);
      toast.error('File upload failed');
    }
  }, 100);
};
```

---

## 3. BACKEND V1 FLOW (LEGACY)

### File quan trọng:
- **Main server**: `/app/backend-v1/server.py`
- **OCR processor**: `/app/backend-v1/targeted_ocr.py`
- **PDF splitter**: `/app/backend-v1/pdf_splitter.py`
- **Valid date calculator**: `/app/backend-v1/test_report_valid_date_calculator.py`
- **Issued by normalization**: `/app/backend-v1/issued_by_abbreviation.py`

### Endpoints trong V1:

#### A. Endpoint: `POST /api/test-reports/analyze-file` (Line 11014-11642)

**Input:**
- `test_report_file`: UploadFile (PDF)
- `ship_id`: str
- `bypass_validation`: str ("true" hoặc "false")

**Process Flow:**

```python
@api_router.post("/test-reports/analyze-file")
async def analyze_test_report_file(
    ship_id: str = Form(...),
    test_report_file: UploadFile = File(...),
    bypass_validation: str = Form("false"),
    current_user: UserResponse = Depends(...)
):
    """
    Step 1: Read file và validate
    """
    file_content = await test_report_file.read()
    filename = test_report_file.filename
    
    # Validate PDF file
    if not filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files supported")
    
    if not file_content.startswith(b'%PDF'):
        raise HTTPException(400, "Invalid PDF format")
    
    """
    Step 2: Check if PDF needs splitting (>15 pages)
    """
    from pdf_splitter import PDFSplitter
    splitter = PDFSplitter(max_pages_per_chunk=12)
    
    total_pages = splitter.get_page_count(file_content)
    needs_split = splitter.needs_splitting(file_content)  # True if > 15 pages
    
    logger.info(f"PDF: {total_pages} pages, Split needed: {needs_split}")
    
    """
    Step 3: Get ship & company info
    """
    ship = await mongo_db.find_one("ships", {"id": ship_id})
    if not ship and not bypass_validation:
        raise HTTPException(404, "Ship not found")
    
    ship_name = ship.get("name", "Unknown Ship")
    ship_imo = ship.get("imo", "")
    
    """
    Step 4: Get AI configuration
    """
    ai_config_doc = await mongo_db.find_one("ai_config", {"id": "system_ai"})
    if not ai_config_doc:
        raise HTTPException(404, "AI configuration not found")
    
    document_ai_config = ai_config_doc.get("document_ai", {})
    if not document_ai_config.get("enabled"):
        raise HTTPException(400, "Document AI not enabled")
    
    """
    Step 5: Initialize result & store file content
    """
    analysis_result = {
        "test_report_name": "",
        "report_form": "",
        "test_report_no": "",
        "issued_by": "",
        "issued_date": "",
        "valid_date": "",
        "note": "",
        "ship_name": "",
        "ship_imo": "",
        "confidence_score": 0.0,
        "processing_method": "clean_analysis"
    }
    
    # CRITICAL: Store file content FIRST
    analysis_result['_file_content'] = base64.b64encode(file_content).decode('utf-8')
    analysis_result['_filename'] = filename
    analysis_result['_content_type'] = test_report_file.content_type
    analysis_result['_ship_name'] = ship_name
    analysis_result['_summary_text'] = ''
    
    """
    Step 6A: Process based on PDF size - CASE 1: Large PDF (>15 pages)
    """
    if needs_split and total_pages > 15:
        logger.info("📦 Splitting large PDF into chunks...")
        
        chunks = splitter.split_pdf(file_content, filename)
        
        # Process each chunk with Document AI
        chunk_summaries = []
        successful_chunks = 0
        failed_chunks = 0
        
        for i, chunk in enumerate(chunks):
            chunk_result = await dual_manager.analyze_test_report_only(
                file_content=chunk['content'],
                filename=chunk['filename'],
                content_type='application/pdf',
                document_ai_config=document_ai_config
            )
            
            if chunk_result and chunk_result.get('success'):
                summary_text = chunk_result.get('summary_text', '')
                if summary_text:
                    chunk_summaries.append(summary_text)
                    successful_chunks += 1
        
        # Merge chunk summaries
        merged_summary_text = "\n\n=== DOCUMENT CONTINUATION ===\n\n".join(chunk_summaries)
        
        # Perform Targeted OCR on FIRST CHUNK
        logger.info("🔍 Starting Targeted OCR on FIRST CHUNK...")
        
        ocr_metadata = {
            'ocr_attempted': False,
            'ocr_success': False,
            'ocr_text_merged': False,
            'header_text_length': 0,
            'footer_text_length': 0,
            'note': 'OCR performed on first chunk only'
        }
        
        ocr_section = ""
        
        from targeted_ocr import get_ocr_processor
        ocr_processor = get_ocr_processor()
        
        if ocr_processor.is_available() and chunks:
            first_chunk_content = chunks[0]['content']
            ocr_result = ocr_processor.extract_from_pdf(first_chunk_content, page_num=0)
            
            if ocr_result.get('ocr_success'):
                header_text = ocr_result.get('header_text', '').strip()
                footer_text = ocr_result.get('footer_text', '').strip()
                
                ocr_metadata['ocr_success'] = True
                ocr_metadata['header_text_length'] = len(header_text)
                ocr_metadata['footer_text_length'] = len(footer_text)
                
                if header_text or footer_text:
                    ocr_section = "\n\n" + "="*60 + "\n"
                    ocr_section += "ADDITIONAL INFORMATION FROM HEADER/FOOTER (OCR Extraction)\n"
                    ocr_section += "(Extracted from first page of document)\n"
                    ocr_section += "="*60 + "\n\n"
                    
                    if header_text:
                        ocr_section += "=== HEADER TEXT (Top 15% of page) ===\n"
                        ocr_section += header_text + "\n\n"
                    
                    if footer_text:
                        ocr_section += "=== FOOTER TEXT (Bottom 15% of page) ===\n"
                        ocr_section += footer_text + "\n\n"
                    
                    ocr_section += "="*60
                    ocr_metadata['ocr_text_merged'] = True
                    
                    # Merge OCR into merged summary
                    merged_summary_text = merged_summary_text + ocr_section
        
        # Store enhanced summary
        analysis_result['_summary_text'] = merged_summary_text
        analysis_result['_ocr_info'] = ocr_metadata
        
        # Extract fields from merged summary (1 time only)
        ai_provider = ai_config_doc.get("provider", "google")
        ai_model = ai_config_doc.get("model", "gemini-2.0-flash-exp")
        use_emergent_key = ai_config_doc.get("use_emergent_key", True)
        
        extracted_fields = await extract_test_report_fields_from_summary(
            merged_summary_text,
            ai_provider,
            ai_model,
            use_emergent_key
        )
        
        if extracted_fields:
            analysis_result.update(extracted_fields)
        
        # Add split metadata
        analysis_result['_split_info'] = {
            'was_split': True,
            'total_pages': total_pages,
            'chunks_count': len(chunks),
            'successful_chunks': successful_chunks,
            'failed_chunks': failed_chunks
        }
    
    """
    Step 6B: Process based on PDF size - CASE 2: Small PDF (≤15 pages)
    """
    else:
        logger.info("📄 Processing as single file (≤15 pages)")
        
        # Analyze with Document AI
        ai_analysis = await dual_manager.analyze_test_report_file(
            file_content=file_content,
            filename=filename,
            content_type='application/pdf',
            document_ai_config=document_ai_config
        )
        
        if ai_analysis:
            summary_text = ai_analysis.get('summary_text', '')
            
            # Perform Targeted OCR
            logger.info("🔍 Starting Targeted OCR for header/footer extraction...")
            
            ocr_metadata = {
                'ocr_attempted': False,
                'ocr_success': False,
                'ocr_text_merged': False,
                'header_text_length': 0,
                'footer_text_length': 0
            }
            
            ocr_section = ""
            
            from targeted_ocr import get_ocr_processor
            ocr_processor = get_ocr_processor()
            
            if ocr_processor.is_available():
                ocr_result = ocr_processor.extract_from_pdf(file_content, page_num=0)
                
                if ocr_result.get('ocr_success'):
                    header_text = ocr_result.get('header_text', '').strip()
                    footer_text = ocr_result.get('footer_text', '').strip()
                    
                    ocr_metadata['ocr_success'] = True
                    ocr_metadata['header_text_length'] = len(header_text)
                    ocr_metadata['footer_text_length'] = len(footer_text)
                    
                    if header_text or footer_text:
                        ocr_section = "\n\n" + "="*60 + "\n"
                        ocr_section += "ADDITIONAL INFORMATION FROM HEADER/FOOTER (OCR Extraction)\n"
                        ocr_section += "="*60 + "\n\n"
                        
                        if header_text:
                            ocr_section += "=== HEADER TEXT (Top 15% of page) ===\n"
                            ocr_section += header_text + "\n\n"
                        
                        if footer_text:
                            ocr_section += "=== FOOTER TEXT (Bottom 15% of page) ===\n"
                            ocr_section += footer_text + "\n\n"
                        
                        ocr_section += "="*60
                        ocr_metadata['ocr_text_merged'] = True
            
            # Enhance summary with OCR
            if summary_text:
                if ocr_section:
                    summary_text = summary_text + ocr_section
            else:
                if ocr_section:
                    summary_text = ocr_section
            
            # Store enhanced summary
            analysis_result['_summary_text'] = summary_text
            analysis_result['_ocr_info'] = ocr_metadata
            
            # Extract fields from enhanced summary
            if summary_text:
                ai_provider = ai_config_doc.get("provider", "google")
                ai_model = ai_config_doc.get("model", "gemini-2.0-flash-exp")
                use_emergent_key = ai_config_doc.get("use_emergent_key", True)
                
                extracted_fields = await extract_test_report_fields_from_summary(
                    summary_text,
                    ai_provider,
                    ai_model,
                    use_emergent_key
                )
                
                if extracted_fields:
                    analysis_result.update(extracted_fields)
                    analysis_result["processing_method"] = "analysis_only_no_upload"
    
    """
    Step 7: Calculate Valid Date (CRITICAL STEP - UNIQUE TO TEST REPORTS)
    """
    logger.info("🧮 Calculating Valid Date from Issued Date + Equipment Interval...")
    
    try:
        from test_report_valid_date_calculator import calculate_valid_date
        
        test_report_name = analysis_result.get('test_report_name', '')
        issued_date = analysis_result.get('issued_date', '')
        
        if test_report_name and issued_date:
            calculated_valid_date = await calculate_valid_date(
                test_report_name=test_report_name,
                issued_date=issued_date,
                ship_id=ship_id,
                mongo_db=mongo_db
            )
            
            if calculated_valid_date:
                analysis_result['valid_date'] = calculated_valid_date
                logger.info(f"✅ Calculated Valid Date: {calculated_valid_date}")
            else:
                logger.warning("⚠️ Could not calculate Valid Date")
        else:
            logger.warning(f"⚠️ Missing required fields for Valid Date calculation")
    except Exception as calc_error:
        logger.error(f"❌ Error during Valid Date calculation: {calc_error}")
    
    """
    Step 8: Normalize issued_by to standard abbreviation
    """
    if analysis_result.get('issued_by'):
        try:
            from issued_by_abbreviation import normalize_issued_by
            
            original_issued_by = analysis_result['issued_by']
            normalized_issued_by = normalize_issued_by(original_issued_by)
            
            if normalized_issued_by != original_issued_by:
                analysis_result['issued_by'] = normalized_issued_by
                logger.info(f"✅ Normalized Issued By: '{original_issued_by}' → '{normalized_issued_by}'")
            else:
                logger.info(f"ℹ️ Issued By kept as: '{original_issued_by}'")
        except Exception as norm_error:
            logger.error(f"❌ Error normalizing issued_by: {norm_error}")
    
    """
    Step 9: Auto-calculate status if valid_date exists
    """
    if analysis_result.get('valid_date'):
        try:
            valid_date_obj = datetime.fromisoformat(analysis_result['valid_date'])
            analysis_result['status'] = calculate_test_report_status(valid_date_obj)
        except:
            analysis_result['status'] = 'Unknown'
    else:
        analysis_result['status'] = 'Unknown'
    
    """
    Step 10: Validate ship name/IMO
    """
    extracted_ship_name = analysis_result.get('ship_name', '').strip()
    extracted_ship_imo = analysis_result.get('ship_imo', '').strip()
    
    if extracted_ship_name or extracted_ship_imo:
        ship_name_match = extracted_ship_name.lower() == ship['name'].lower() if extracted_ship_name else False
        ship_imo_match = extracted_ship_imo == ship.get('imo', '') if extracted_ship_imo else False
        
        if not ship_name_match and not ship_imo_match and bypass_validation != "true":
            return {
                **analysis_result,
                "validation_warning": "Ship name or IMO in document doesn't match selected ship",
                "requires_confirmation": True
            }
    
    """
    Step 11: Return analysis result
    """
    logger.info("✅ Test report analysis completed successfully")
    return analysis_result
```

#### B. Endpoint: `POST /api/test-reports/{report_id}/upload-files` (Line 11646-11756)

**Process:**

```python
@api_router.post("/test-reports/{report_id}/upload-files")
async def upload_test_report_files(
    report_id: str,
    file_content: str = Body(...),
    filename: str = Body(...),
    content_type: str = Body(...),
    summary_text: Optional[str] = Body(None),
    current_user: UserResponse = Depends(...)
):
    """
    Upload test report files to Google Drive
    1. Decode base64 file content
    2. Upload original file to: ShipName/Class & Flag Cert/Test Report/
    3. Upload summary to: SUMMARY/Class & Flag Document/
    4. Update test report record with file IDs
    """
    
    # Validate report exists
    report = await mongo_db.find_one("test_reports", {"id": report_id})
    if not report:
        raise HTTPException(404, "Test report not found")
    
    # Get ship info
    ship_id = report.get("ship_id")
    ship = await mongo_db.find_one("ships", {"id": ship_id})
    
    ship_name = ship.get("name", "Unknown Ship")
    
    # Decode base64
    file_bytes = base64.b64decode(file_content)
    
    # Initialize Dual Apps Script Manager
    from dual_apps_script_manager import create_dual_apps_script_manager
    dual_manager = create_dual_apps_script_manager(company_uuid)
    
    # Upload files to Google Drive
    # NOTE: Test Report uses a DIFFERENT method than Survey Report
    upload_result = await dual_manager.upload_test_report_file(
        file_content=file_bytes,
        filename=filename,
        ship_name=ship_name,
        summary_text=summary_text
    )
    
    if not upload_result.get('success'):
        raise HTTPException(500, "File upload failed")
    
    # Extract file IDs
    original_file_id = upload_result.get('original_file_id')
    summary_file_id = upload_result.get('summary_file_id')
    
    # Update test report with file IDs
    update_data = {}
    if original_file_id:
        update_data['test_report_file_id'] = original_file_id
    if summary_file_id:
        update_data['test_report_summary_file_id'] = summary_file_id
    
    if update_data:
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        await mongo_db.update("test_reports", {"id": report_id}, update_data)
    
    return {
        "success": True,
        "message": "Test report files uploaded successfully",
        "original_file_id": original_file_id,
        "summary_file_id": summary_file_id
    }
```

---

## 4. BACKEND MỚI FLOW (MIGRATED)

### File quan trọng:
- **API Routes**: `/app/backend/app/api/v1/test_reports.py`
- **Service**: `/app/backend/app/services/test_report_service.py`
- **Models**: `/app/backend/app/models/test_report.py`

### ⚠️ TÌNH TRẠNG MIGRATION:

**Backend mới chỉ có BASIC endpoints:**

```python
# test_reports.py

@router.post("/analyze-file")
async def analyze_document_file(
    file: UploadFile = File(...),
    ship_id: Optional[str] = None,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Analyze Test Report file using AI (Editor+ role required)"""
    try:
        return await service.analyze_file(file, ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing Test Report file: {e}")
        raise HTTPException(500, f"Failed to analyze Test Report: {str(e)}")
```

**❌ PROBLEM: Backend mới THIẾU toàn bộ logic như V1:**

1. ❌ Không có PDF splitting logic
2. ❌ Không có Targeted OCR
3. ❌ Không có System AI extraction (LLM prompt)
4. ❌ Không có Valid Date calculator
5. ❌ Không có Issued By normalization
6. ❌ Không có ship validation
7. ❌ Upload-files endpoint chưa có hoặc chưa đầy đủ

**Backend mới chỉ delegate đến một service chưa được implement đầy đủ!**

---

## 5. ENDPOINTS ĐƯỢC SỬ DỤNG

### API Endpoints Summary:

| Endpoint | Method | Purpose | V1 Status | Backend Mới Status |
|----------|--------|---------|-----------|-------------------|
| `/api/test-reports/analyze-file` | POST | Phân tích file PDF với AI | ✅ Full | ⚠️ Incomplete |
| `/api/test-reports` | POST | Tạo record test report | ✅ | ✅ |
| `/api/test-reports/{report_id}/upload-files` | POST | Upload files lên Google Drive | ✅ | ⚠️ Unknown |
| `/api/test-reports/{report_id}` | DELETE | Xóa test report + files | ✅ | ✅ |
| `/api/test-reports/bulk-delete` | POST | Xóa nhiều test reports | ✅ | ✅ |
| `/api/test-reports/check-duplicate` | POST | Kiểm tra trùng lặp | ✅ | ✅ |

---

## 6. FUNCTIONS & HELPERS

### A. Extract Test Report Fields từ Summary

**Function**: `extract_test_report_fields_from_summary()`

**Location V1**: `/app/backend-v1/server.py` (line 7783-7858)
**Location Mới**: ❌ CHƯA CÓ

**Purpose**: Dùng System AI (LLM) để extract các trường từ summary text

**Input:**
- `summary_text`: str (Document AI summary + OCR text)
- `ai_provider`: str ("google", "openai", "anthropic")
- `ai_model`: str ("gemini-2.0-flash-exp", "gpt-5", etc.)
- `use_emergent_key`: bool

**Output:**
```python
{
    "test_report_name": "EEBD",  # Equipment name ONLY
    "report_form": "Service Chart A",
    "test_report_no": "TR-2024-001",
    "issued_by": "VITECH",  # Short name
    "issued_date": "2024-01-15",  # ISO format
    "valid_date": "2025-01-15",  # Calculated or extracted
    "ship_name": "MV Example Ship",
    "ship_imo": "9876543",
    "note": "All items in satisfactory condition"
}
```

### B. Create Test Report Extraction Prompt

**Function**: `create_test_report_extraction_prompt()`

**Location V1**: `/app/backend-v1/server.py` (line 8162-8341)
**Location Mới**: ❌ CHƯA CÓ

**Purpose**: Tạo AI prompt chi tiết để extract các trường từ test report

**Key points trong prompt:**

```
=== FIELD EXTRACTION RULES ===

**test_report_name**: 
- Test reports are about MAINTENANCE/TESTING of LIFESAVING and FIREFIGHTING EQUIPMENT
- Extract EQUIPMENT NAME only, NOT the test type
- Common equipment names:
  * EEBD (Emergency Escape Breathing Device)
  * SCBA (Self-Contained Breathing Apparatus)
  * Portable Fire Extinguisher
  * Life Raft / Liferaft
  * Lifeboat / Rescue Boat
  * CO2 System
  * Fire Detection System
  * Gas Detector
  * Immersion Suit
  * Life Jacket
  * EPIRB, SART
  * Fire Hose
  * Fireman Outfit
  * Breathing Apparatus
  * Fixed Fire Extinguishing System
  * Emergency Fire Pump
  * Davit / Launching Appliance

- Return ONLY equipment name (e.g., "EEBD", "Life Raft")
- Do NOT add "Test" or "Report" to the name

**report_form**: 
- Extract the SERVICE CHART or FORM
- Look for patterns:
  * "Service Chart [LETTER]" - e.g., "Service Chart A", "Service Chart K"
  * "Service Charts [LETTER]/[LETTER]" - e.g., "Service Charts H1/H2"
  * "SERVICE CHART [CODE]"
  * "Chart [CODE]"
  * "Form [NUMBER/LETTER]"

- Common patterns: Service Chart A, B, C, D, E, F, G, H, K, L, M, N
- May be combined: Service Charts H1/H2, K1/K2
- Extract complete chart/form identifier exactly as written

**test_report_no**: 
- Extract test report number or certificate number
- Look for:
  * "Test Report No." or "Test Report Number"
  * "Certificate Number" or "Certificate No."
  * "Report No."
  
- Common formats:
  * Numbers with dashes: "TR-2024-001"
  * Numbers with slashes: "TEST/2024/123"
  * Alphanumeric: "TR123456"

**issued_by**: 
- Extract who issued or conducted the test/maintenance
- **IMPORTANT: Extract ONLY the SHORT NAME**
- Rules:
  * ✅ "VITECH" (NOT "VITECH Technologies and Services JSC")
  * ✅ "Lloyd's Register" or "LR"
  * ✅ "DNV" (NOT "Det Norske Veritas")
  * ✅ "ABS" (NOT "American Bureau of Shipping")
  * ✅ Use common/trade name, NOT full legal entity name
  
- Remove legal suffixes: JSC, LLC, Inc., Co., Ltd., Corporation

**issued_date**: 
- Extract ACTUAL DATE when the inspection/maintenance was performed
- This is when SERVICE PROVIDER conducted the test/maintenance
- Look for phrases:
  * "underwent inspection on [DATE]"
  * "inspected on [DATE]"
  * "serviced on [DATE]"
  * "tested on [DATE]"
  * "maintenance performed on [DATE]"
  * "inspection date: [DATE]"
  
- **DO NOT extract:**
  * "Rev XX, issued by [COMPANY] on [DATE]" - form revision date
  * "Form issued on [DATE]" - form template date
  
- Focus on date when ACTUAL WORK was performed

**valid_date**: 
- Extract expiry date or next test due date
- Look for "Valid Until", "Expiry Date", "Next Test Due", "Expires"
- Date when test/certificate expires and needs renewal
```

### C. Calculate Valid Date (UNIQUE TO TEST REPORTS)

**Function**: `calculate_valid_date()`

**Location V1**: `/app/backend-v1/test_report_valid_date_calculator.py`
**Location Mới**: ❌ CHƯA CÓ

**Purpose**: Tính toán valid_date dựa trên loại thiết bị và issued_date

**Logic:**

```python
# test_report_valid_date_calculator.py

async def calculate_valid_date(
    test_report_name: str,
    issued_date: str,
    ship_id: str,
    mongo_db
) -> Optional[str]:
    """
    Calculate valid date based on equipment type and issued date
    
    Logic:
    1. Determine equipment type from test_report_name
    2. Get ship-specific intervals from ship's test_report_intervals
    3. If no ship-specific interval, use default interval
    4. Calculate: valid_date = issued_date + interval (months)
    
    Default intervals (months):
    - EEBD: 12 months
    - SCBA: 12 months
    - Portable Fire Extinguisher: 12 months
    - Life Raft: 12 months
    - Lifeboat: 12 months
    - CO2 System: 12 months
    - Fire Detection System: 12 months
    - Gas Detector: 12 months
    - Immersion Suit: 36 months (3 years)
    - Life Jacket: 36 months (3 years)
    - EPIRB: 24 months (2 years)
    - SART: 12 months
    - Fire Hose: 12 months
    - Fireman Outfit: 12 months
    - Breathing Apparatus: 12 months
    - Fixed Fire Extinguishing System: 12 months
    - Emergency Fire Pump: 12 months
    - Davit: 60 months (5 years)
    - Default: 12 months
    """
    
    # Parse issued_date
    from dateutil import parser
    issued_date_obj = parser.parse(issued_date)
    
    # Normalize equipment name
    equipment_name_normalized = test_report_name.lower().strip()
    
    # Default intervals dictionary
    DEFAULT_INTERVALS = {
        'eebd': 12,
        'emergency escape breathing device': 12,
        'scba': 12,
        'self-contained breathing apparatus': 12,
        'self contained breathing apparatus': 12,
        'portable fire extinguisher': 12,
        'fire extinguisher': 12,
        'life raft': 12,
        'liferaft': 12,
        'lifeboat': 12,
        'rescue boat': 12,
        'co2 system': 12,
        'carbon dioxide system': 12,
        'fire detection system': 12,
        'fire alarm system': 12,
        'gas detector': 12,
        'gas detection system': 12,
        'immersion suit': 36,
        'survival suit': 36,
        'life jacket': 36,
        'lifejacket': 36,
        'life vest': 36,
        'epirb': 24,
        'emergency position indicating radio beacon': 24,
        'sart': 12,
        'search and rescue transponder': 12,
        'fire hose': 12,
        'fire fighting hose': 12,
        'fireman outfit': 12,
        "fireman's outfit": 12,
        'breathing apparatus': 12,
        'fixed fire extinguishing system': 12,
        'sprinkler system': 12,
        'emergency fire pump': 12,
        'davit': 60,
        'launching appliance': 60
    }
    
    # Try to get ship-specific interval
    interval_months = None
    
    try:
        ship = await mongo_db.find_one("ships", {"id": ship_id})
        if ship:
            test_report_intervals = ship.get("test_report_intervals", {})
            
            # Try exact match first
            if equipment_name_normalized in test_report_intervals:
                interval_months = test_report_intervals[equipment_name_normalized]
            else:
                # Try partial match
                for key, value in test_report_intervals.items():
                    if key in equipment_name_normalized or equipment_name_normalized in key:
                        interval_months = value
                        break
    except Exception as e:
        logger.warning(f"Could not fetch ship-specific intervals: {e}")
    
    # If no ship-specific interval, use default
    if interval_months is None:
        # Try exact match
        if equipment_name_normalized in DEFAULT_INTERVALS:
            interval_months = DEFAULT_INTERVALS[equipment_name_normalized]
        else:
            # Try partial match
            for key, value in DEFAULT_INTERVALS.items():
                if key in equipment_name_normalized or equipment_name_normalized in key:
                    interval_months = value
                    break
            
            # If still not found, use default 12 months
            if interval_months is None:
                interval_months = 12
                logger.warning(f"No interval found for '{test_report_name}', using default 12 months")
    
    # Calculate valid date
    from dateutil.relativedelta import relativedelta
    valid_date_obj = issued_date_obj + relativedelta(months=interval_months)
    
    # Return in ISO format
    return valid_date_obj.strftime('%Y-%m-%d')
```

**Example:**

```python
# Equipment: EEBD
# Issued Date: 2024-01-15
# Interval: 12 months (default)
# Valid Date: 2025-01-15

# Equipment: Immersion Suit
# Issued Date: 2024-01-15
# Interval: 36 months (3 years)
# Valid Date: 2027-01-15

# Equipment: Davit
# Issued Date: 2024-01-15
# Interval: 60 months (5 years)
# Valid Date: 2029-01-15
```

### D. Normalize Issued By

**Function**: `normalize_issued_by()`

**Location V1**: `/app/backend-v1/issued_by_abbreviation.py`
**Location Mới**: ❌ CHƯA CÓ (hoặc có trong utilities?)

**Purpose**: Chuẩn hóa tên công ty thành tên ngắn gọn

**Logic:**

```python
def normalize_issued_by(issued_by: str) -> str:
    """
    Normalize issued_by to standard abbreviations
    
    Examples:
    - "VITECH Technologies and Services JSC" → "VITECH"
    - "Lloyd's Register of Shipping" → "Lloyd's Register"
    - "Det Norske Veritas" → "DNV"
    - "American Bureau of Shipping" → "ABS"
    - "Bureau Veritas" → "BV"
    """
    
    # Mapping dictionary
    ABBREVIATIONS = {
        'lloyd\'s register of shipping': 'Lloyd\'s Register',
        'lloyd\'s register': 'Lloyd\'s Register',
        'lr': 'LR',
        'det norske veritas': 'DNV',
        'dnv gl': 'DNV',
        'dnv': 'DNV',
        'american bureau of shipping': 'ABS',
        'abs': 'ABS',
        'bureau veritas': 'Bureau Veritas',
        'bv': 'BV',
        'vitech technologies and services jsc': 'VITECH',
        'vitech': 'VITECH',
        # ... more mappings
    }
    
    # Normalize to lowercase for comparison
    issued_by_lower = issued_by.lower().strip()
    
    # Check exact match
    if issued_by_lower in ABBREVIATIONS:
        return ABBREVIATIONS[issued_by_lower]
    
    # Check partial match
    for key, value in ABBREVIATIONS.items():
        if key in issued_by_lower:
            return value
    
    # If no match, remove common legal suffixes
    suffixes_to_remove = [
        ' jsc', ' llc', ' inc.', ' inc', ' co.', ' co', 
        ' ltd.', ' ltd', ' limited', ' corporation', ' corp.',
        ' technologies', ' services', ' company'
    ]
    
    result = issued_by
    for suffix in suffixes_to_remove:
        if issued_by_lower.endswith(suffix):
            result = issued_by[:-len(suffix)].strip()
            break
    
    return result
```

---

## 7. DOCUMENT AI INTEGRATION

**Giống như Survey Report**, Test Report cũng sử dụng Google Document AI.

- Configuration stored in `ai_config` collection
- Calls through `dual_apps_script_manager`
- Returns plain text summary of PDF

**Chi tiết xem trong Survey Report Flow Analysis**

---

## 8. TARGETED OCR PROCESS

**Hoàn toàn giống Survey Report**

- Extract header (top 15%) & footer (bottom 15%)
- Use Tesseract OCR + pdf2image + OpenCV
- Find Report Form và Report No patterns
- Merge into Document AI summary

**Chi tiết xem trong Survey Report Flow Analysis**

---

## 9. PDF SPLITTING LOGIC (>15 PAGES)

**Hoàn toàn giống Survey Report**

- Split PDFs > 15 pages into chunks of 12 pages
- Process each chunk with Document AI
- Merge summaries
- Perform OCR on first chunk only
- Extract fields from merged summary (1 time only)

**Chi tiết xem trong Survey Report Flow Analysis**

---

## 10. FILE UPLOAD TO GOOGLE DRIVE

### Khác biệt với Survey Report:

**Survey Report:**
```python
await dual_manager.upload_survey_report_file(...)
# Upload to: ShipName/Class & Flag Cert/Class Survey Report/
```

**Test Report:**
```python
await dual_manager.upload_test_report_file(...)
# Upload to: ShipName/Class & Flag Cert/Test Report/
```

### Upload Process:

```python
# dual_apps_script_manager.py

async def upload_test_report_file(
    self,
    file_content: bytes,
    filename: str,
    ship_name: str,
    summary_text: str
) -> Dict[str, Any]:
    """
    Upload test report files to Google Drive
    
    1. Upload original file to: ShipName/Class & Flag Cert/Test Report/[filename]
    2. Upload summary to: SUMMARY/Class & Flag Document/[filename]_Summary.txt
    """
    
    # Encode file to base64
    file_base64 = base64.b64encode(file_content).decode('utf-8')
    
    # Prepare request
    payload = {
        'action': 'uploadTestReportFile',
        'fileName': filename,
        'fileContent': file_base64,
        'contentType': 'application/pdf',
        'shipName': ship_name,
        'summaryText': summary_text
    }
    
    # Call Apps Script
    async with aiohttp.ClientSession() as session:
        async with session.post(
            self.apps_script_url,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as response:
            result = await response.json()
    
    if result.get('success'):
        return {
            'success': True,
            'original_file_id': result.get('originalFileId'),
            'summary_file_id': result.get('summaryFileId')
        }
    else:
        return {
            'success': False,
            'message': result.get('error', 'Unknown error')
        }
```

**Google Drive Folder Structure:**

```
Google Drive Root
├── ShipName/
│   └── Class & Flag Cert/
│       └── Test Report/           ← Original files here
│           ├── EEBD_Test_2024.pdf
│           ├── Life_Raft_Test.pdf
│           └── ...
└── SUMMARY/
    └── Class & Flag Document/     ← Summary files here
        ├── EEBD_Test_2024_Summary.txt
        ├── Life_Raft_Test_Summary.txt
        └── ...
```

---

## 11. VALID DATE CALCULATOR

### Đây là tính năng ĐỘC QUYỀN của Test Report (không có trong Survey Report)

**Purpose:** Tự động tính toán valid_date dựa trên:
1. Equipment type (extracted from test_report_name)
2. Issued date
3. Equipment-specific maintenance interval

**Why needed?**
- Test reports về thiết bị cứu sinh và chữa cháy
- Mỗi loại thiết bị có chu kỳ bảo dưỡng/kiểm tra khác nhau
- Ví dụ:
  - EEBD: 12 tháng
  - Life Jacket: 36 tháng (3 năm)
  - Davit: 60 tháng (5 năm)

**Process:**

```
1. Extract test_report_name từ AI: "EEBD"
2. Extract issued_date từ AI: "2024-01-15"
3. Lookup interval cho "EEBD": 12 months
4. Calculate: valid_date = issued_date + 12 months = "2025-01-15"
5. Store in analysis_result['valid_date']
```

**Equipment Intervals (Default):**

| Equipment | Interval | Example |
|-----------|----------|---------|
| EEBD | 12 months | 2024-01-15 → 2025-01-15 |
| SCBA | 12 months | 2024-01-15 → 2025-01-15 |
| Portable Fire Extinguisher | 12 months | 2024-01-15 → 2025-01-15 |
| Life Raft | 12 months | 2024-01-15 → 2025-01-15 |
| Lifeboat | 12 months | 2024-01-15 → 2025-01-15 |
| CO2 System | 12 months | 2024-01-15 → 2025-01-15 |
| Fire Detection System | 12 months | 2024-01-15 → 2025-01-15 |
| Gas Detector | 12 months | 2024-01-15 → 2025-01-15 |
| **Immersion Suit** | **36 months** | 2024-01-15 → **2027-01-15** |
| **Life Jacket** | **36 months** | 2024-01-15 → **2027-01-15** |
| **EPIRB** | **24 months** | 2024-01-15 → **2026-01-15** |
| SART | 12 months | 2024-01-15 → 2025-01-15 |
| Fire Hose | 12 months | 2024-01-15 → 2025-01-15 |
| Fireman Outfit | 12 months | 2024-01-15 → 2025-01-15 |
| Breathing Apparatus | 12 months | 2024-01-15 → 2025-01-15 |
| Fixed Fire Extinguishing System | 12 months | 2024-01-15 → 2025-01-15 |
| Emergency Fire Pump | 12 months | 2024-01-15 → 2025-01-15 |
| **Davit** | **60 months** | 2024-01-15 → **2029-01-15** |
| **Default (unknown)** | **12 months** | 2024-01-15 → 2025-01-15 |

**Ship-Specific Intervals:**

Ships có thể có custom intervals trong database:

```json
{
  "id": "ship-123",
  "name": "MV Example Ship",
  "test_report_intervals": {
    "eebd": 12,
    "life_raft": 12,
    "immersion_suit": 36,
    "custom_equipment": 24
  }
}
```

**Priority:**
1. Ship-specific interval (from ship.test_report_intervals)
2. Default interval (from DEFAULT_INTERVALS dictionary)
3. Fallback: 12 months

---

## 12. SO SÁNH BACKEND V1 VS BACKEND MỚI

### A. Cấu trúc code:

| Aspect | Backend V1 | Backend Mới |
|--------|-----------|-------------|
| **analyze-file endpoint** | ✅ Full implementation (600+ lines) | ⚠️ Skeleton only (10 lines) |
| **PDF Splitting** | ✅ Implemented | ❌ Missing |
| **Document AI** | ✅ Implemented | ❌ Missing |
| **Targeted OCR** | ✅ Implemented | ❌ Missing |
| **System AI Extraction** | ✅ Implemented | ❌ Missing |
| **Valid Date Calculator** | ✅ Implemented | ❌ Missing |
| **Issued By Normalization** | ✅ Implemented | ❌ Missing |
| **Ship Validation** | ✅ Implemented | ❌ Missing |
| **upload-files endpoint** | ✅ Implemented | ⚠️ Unknown |

### B. Feature Parity:

| Feature | Backend V1 | Backend Mới | Gap |
|---------|-----------|-------------|-----|
| **PDF validation** | ✅ | ⚠️ Unknown | Chưa rõ |
| **PDF splitting (>15 pages)** | ✅ | ❌ | **CRITICAL** |
| **Document AI** | ✅ | ❌ | **CRITICAL** |
| **Targeted OCR** | ✅ | ❌ | **CRITICAL** |
| **System AI extraction** | ✅ | ❌ | **CRITICAL** |
| **Valid Date Calculator** | ✅ | ❌ | **CRITICAL** |
| **Issued By normalization** | ✅ | ❌ | High |
| **Ship validation** | ✅ | ❌ | High |
| **File upload (original + summary)** | ✅ | ⚠️ | Unknown |
| **File deletion on record delete** | ✅ | ⚠️ | Unknown |
| **Bulk delete** | ✅ | ✅ | OK |

### C. Migration Status:

```
Test Report Migration: ~20% Complete ⚠️

✅ Migrated:
- CRUD endpoints (GET, POST, PUT, DELETE)
- Bulk delete
- Check duplicate

❌ CHƯA Migrated:
- analyze-file logic (PDF splitting, Document AI, OCR, AI extraction)
- Valid Date Calculator
- Issued By normalization
- Ship validation
- upload-files endpoint (hoặc logic không đầy đủ)
```

---

## 13. TỔNG KẾT & KHUYẾN NGHỊ

### A. Tóm tắt flow "Add Test Report":

**Giống Survey Report:**
1. Frontend upload file
2. Backend analyze with Document AI
3. Perform Targeted OCR
4. Extract fields with System AI
5. Validate ship info
6. Frontend auto-fill form
7. Frontend create record
8. Background upload to Google Drive

**Khác biệt quan trọng:**
1. ✅ **Valid Date Calculator** - Tính toán dựa trên equipment type + issued_date
2. ✅ **Equipment-specific intervals** - Mỗi loại thiết bị có chu kỳ khác nhau
3. ✅ **AI Prompt khác** - Tập trung vào lifesaving & firefighting equipment
4. ✅ **Issued By normalization** - Chuẩn hóa tên công ty
5. ✅ **Upload path khác** - Test Report folder thay vì Survey Report folder

### B. Backend Mới: CHƯA HOÀN THÀNH ⚠️

**Backend mới chỉ có skeleton:**

```python
# Hiện tại trong backend mới:
@router.post("/analyze-file")
async def analyze_document_file(...):
    return await service.analyze_file(...)
```

**Thiếu toàn bộ logic:**
- ❌ PDF splitting (~150 lines)
- ❌ Document AI integration (~100 lines)
- ❌ Targeted OCR (~100 lines)
- ❌ System AI extraction (~200 lines)
- ❌ Valid Date Calculator (~150 lines)
- ❌ Issued By normalization (~50 lines)
- ❌ Ship validation (~50 lines)

**Total: ~800 lines of critical logic MISSING**

### C. Khuyến nghị Migration:

#### Priority 1: MIGRATE CORE AI LOGIC (CRITICAL)

**Files cần tạo/update:**

1. **`/app/backend/app/services/test_report_analyze_service.py`**
   - Port toàn bộ analyze-file logic từ V1
   - Implement PDF splitting
   - Implement Document AI calls
   - Implement Targeted OCR
   - Implement System AI extraction

2. **`/app/backend/app/utils/test_report_ai.py`**
   - Port `extract_test_report_fields_from_summary()`
   - Port `create_test_report_extraction_prompt()`

3. **`/app/backend/app/utils/test_report_valid_date_calculator.py`**
   - Port `calculate_valid_date()`
   - Port default intervals dictionary
   - Implement ship-specific interval lookup

4. **`/app/backend/app/services/test_report_service.py`**
   - Implement `upload_files()` method
   - Similar to Survey Report upload logic

#### Priority 2: REUSE EXISTING UTILITIES

Test Report có thể reuse utilities đã có từ Survey Report:

- ✅ `pdf_splitter.py` - Đã có, không cần port
- ✅ `targeted_ocr.py` - Đã có, không cần port
- ⚠️ `issued_by_abbreviation.py` - Cần check xem đã có trong utilities chưa

#### Priority 3: TESTING

Sau khi migrate, cần test:

1. **PDF Splitting:**
   - Test với PDF 15, 20, 30 pages
   - Verify merged summary

2. **Valid Date Calculator:**
   - Test với mỗi equipment type
   - Verify intervals (12, 24, 36, 60 months)
   - Test ship-specific intervals

3. **AI Extraction:**
   - Test với các loại test reports:
     - EEBD test reports
     - Life Raft test reports
     - Fire Extinguisher test reports
     - Davit test reports
   - Verify equipment name extraction
   - Verify service chart extraction

4. **Issued By Normalization:**
   - Test với các tên công ty khác nhau
   - Verify abbreviation mapping

### D. Estimation:

**Time to complete Test Report migration:**

| Task | Lines of Code | Estimated Time |
|------|---------------|----------------|
| Port analyze_file logic | ~600 lines | 2-3 days |
| Port Valid Date Calculator | ~150 lines | 1 day |
| Port AI extraction prompt | ~200 lines | 1 day |
| Port upload_files logic | ~100 lines | 0.5 day |
| Testing & Bug fixes | - | 2 days |
| **TOTAL** | **~1050 lines** | **6-7 days** |

### E. Kết luận:

✅ **Survey Report:** Migration 100% complete
⚠️ **Test Report:** Migration 20% complete (CRITICAL GAPS)

**Recommendation:**
1. ✅ Survey Report đã sẵn sàng để decommission backend-v1
2. ⚠️ Test Report CẦN migrate gấp trước khi decommission backend-v1
3. 🔥 **Priority:** Port Test Report analyze-file logic (2-3 days)
4. 🔥 **Priority:** Port Valid Date Calculator (1 day)
5. ✅ Test thoroughly với real-world test reports

---

**Ngày hoàn thành phân tích**: 2025
**Version**: 2.0
**Status**: ⚠️ INCOMPLETE MIGRATION DETECTED

**⚠️ WARNING:** Backend mới cho Test Report chưa có đủ tính năng. Cần migrate gấp trước khi decommission backend-v1!

