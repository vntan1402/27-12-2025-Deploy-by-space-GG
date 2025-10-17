# Trình Tự Upload Multi-File cho Crew Certificates

## 📋 Overview
Khi user upload nhiều file certificates cùng lúc, hệ thống sử dụng **staggered parallel processing** để xử lý hiệu quả.

---

## 🔄 Complete Flow

### **Step 1: User Selects Files**
```javascript
Location: handleMultipleCertificateUpload(files)
```

**Actions:**
1. User chọn nhiều files (PDF/Image) từ file input
2. System validates:
   - ✅ Crew member đã được chọn (`selectedCrewForCert` hoặc `certFilters.crewName`)
   - ✅ File type: PDF hoặc Image
   - ✅ File size: ≤ 10MB

**Validation Results:**
- ❌ If no crew selected → Show warning, stop
- ❌ If invalid files → Show error toast, filter out
- ✅ If valid → Continue to next step

**Decision:**
- **Single file** (1 file) → Go to **Review Mode** (single file processing)
- **Multiple files** (≥2 files) → Go to **Batch Processing Mode**

---

### **Step 2: Start Batch Processing**
```javascript
Location: startCertBatchProcessing(files)
```

**Actions:**
1. Initialize batch state:
   ```javascript
   setIsBatchProcessingCerts(true)
   setCertBatchProgress({ current: 0, total: files.length })
   setCertBatchResults([])
   ```

2. Show toast:
   - "Bắt đầu xử lý N file chứng chỉ (song song)..."

3. Capture current crew data:
   ```javascript
   const currentCrewData = filteredCrewData || []
   ```
   *(Để tránh state access issues trong async operations)*

4. **Create staggered promises:**
   - File 1: Starts immediately (0s delay)
   - File 2: Starts after 2s
   - File 3: Starts after 4s
   - File N: Starts after (N-1) × 2s

5. **Execute parallel processing:**
   ```javascript
   await Promise.all(processingPromises)
   ```

---

### **Step 3: Process Each File** (Parallel với Stagger)
```javascript
Location: processSingleCertInBatch(file, index, total, crewDataList)
```

**For Each File:**

#### **3.1. Wait for Stagger Delay**
```javascript
const delayMs = index * 2000  // 0s, 2s, 4s, 6s...
await new Promise(r => setTimeout(r, delayMs))
```

#### **3.2. Analyze Certificate via AI**
```javascript
POST /api/crew-certificates/analyze-file
FormData:
  - cert_file: file
  - ship_id: selectedShip.id
  - crew_id: selectedCrewForCert.id (if available)
```

**Backend Process:**
1. Google Apps Script receives file
2. Upload to Google Drive → Get `file_id`
3. Google Document AI analyzes → Extract text
4. AI (Gemini/GPT) extracts fields:
   - `cert_name`, `cert_no`, `holder_name`
   - `issued_by`, `issued_date`, `expiry_date`
   - `date_of_birth`, `note`
5. Create summary file on Drive → Get `summary_file_id`
6. Return analysis + `file_content` (base64) + file IDs

**Response:**
```javascript
{
  success: true,
  crew_name: "...",
  crew_name_en: "...",
  passport: "...",
  rank: "...",
  date_of_birth: "...",
  analysis: {
    cert_name: "...",
    cert_no: "...",
    issued_by: "...",
    issued_date: "...",
    expiry_date: "...",
    note: "...",
    _file_content: "base64...",
    _filename: "...",
    _content_type: "...",
    _summary_text: "...",
    crew_cert_file_id: "...",
    crew_cert_summary_file_id: "..."
  }
}
```

#### **3.3. Check for Duplicates**
```javascript
POST /api/crew-certificates/check-duplicate
Body:
  - crew_id: "..."
  - cert_no: "..."
```

**If Duplicate Found:**
- ⚠️ Skip this file
- Log: "Duplicate detected, skipping..."
- Return result with `error: 'DUPLICATE'`

**If No Duplicate:**
- ✅ Continue to next step

#### **3.4. Create Certificate Record**
```javascript
POST /api/crew-certificates/manual?ship_id=xxx
Body:
  {
    crew_id: "...",
    crew_name: "...",
    crew_name_en: "...",
    passport: "...",
    rank: "...",
    date_of_birth: "...",
    cert_name: "...",
    cert_no: "...",
    issued_by: "...",
    issued_date: "...",
    cert_expiry: "...",
    note: "...",
    crew_cert_file_id: "...",  // From analysis
    crew_cert_summary_file_id: "..."  // From analysis
  }
```

**Database Action:**
- Insert new crew certificate record in MongoDB
- Return: `{ id: "cert_id", ... }`

#### **3.5. Upload Files to Drive**
```javascript
POST /api/crew-certificates/{cert_id}/upload-files
Body:
  {
    file_content: "base64...",  // From analysis._file_content
    filename: "...",
    content_type: "...",
    summary_text: "..."
  }
```

**Backend Process:**
1. Decode base64 file content
2. Upload original file to Drive:
   - Location: `ShipName > Crew Records > crew_name > filename`
3. Create summary file on Drive:
   - Location: `ShipName > Crew Records > crew_name > filename_summary.txt`
4. Update certificate record with file IDs
5. Return: `{ success: true, crew_cert_file_id: "...", crew_cert_summary_file_id: "..." }`

**If Upload Fails:**
- ⚠️ Log warning but DON'T throw error
- Certificate record is already saved in DB
- Return result with partial success

#### **3.6. Update Progress**
```javascript
setCertBatchResults(prev => [...prev, result])
setCertBatchProgress({ current: updated.length, total: files.length })
```

---

### **Step 4: Complete Batch Processing**
```javascript
Location: startCertBatchProcessing (after Promise.all completes)
```

**Actions:**
1. Wait for all files to complete:
   ```javascript
   const collectedResults = await Promise.all(processingPromises)
   ```

2. Calculate statistics:
   - Total files processed
   - Success count
   - Failed count
   - Duplicate count

3. **Close Add Certificate Modal:**
   ```javascript
   setShowAddCrewCertModal(false)
   ```

4. **Show Results Modal:**
   ```javascript
   setCertProcessingResults(collectedResults)
   setShowCertProcessingResultsModal(true)
   ```

5. **Refresh Certificate List:**
   ```javascript
   await fetchCrewCertificates(null)
   ```

6. **Reset batch states:**
   ```javascript
   setIsBatchProcessingCerts(false)
   setCertBatchResults([])
   setCertBatchProgress({ current: 0, total: 0 })
   ```

---

## 📊 Result Structure

Each file returns a result object:

### **Success Result:**
```javascript
{
  filename: "certificate.pdf",
  success: true,
  certCreated: true,
  fileUploaded: true,
  summaryCreated: true,
  certId: "cert_id",
  certName: "COC - Master",
  certNo: "P123456",
  crewName: "NGUYEN VAN A",
  fileId: "drive_file_id",
  summaryFileId: "drive_summary_id",
  index: 1
}
```

### **Duplicate Result:**
```javascript
{
  filename: "certificate.pdf",
  success: false,
  certCreated: false,
  error: 'DUPLICATE',
  certName: "COC - Master",
  certNo: "P123456",
  crewName: "NGUYEN VAN A",
  duplicateInfo: {
    cert_name: "...",
    cert_no: "...",
    issued_date: "...",
    cert_expiry: "...",
    issued_by: "..."
  },
  index: 2
}
```

### **Error Result:**
```javascript
{
  filename: "certificate.pdf",
  success: false,
  error: "Error message...",
  index: 3
}
```

---

## ⏱️ Timing Example

**3 files uploaded:**
```
Time 0s:  File 1 → Start analyzing
Time 2s:  File 2 → Start analyzing
Time 4s:  File 3 → Start analyzing
Time 10s: File 1 → Analysis complete → Create record → Upload files
Time 12s: File 2 → Analysis complete → Create record → Upload files
Time 14s: File 3 → Analysis complete → Create record → Upload files
Time 15s: All complete → Show results modal
```

**Parallel + Staggered = Fast but Controlled**
- Prevents API rate limiting
- Reduces server load spikes
- Better error handling
- Progress tracking per file

---

## 🎯 Key Features

### 1. **Staggered Parallel Processing**
- Multiple files process simultaneously
- 2-second delay between starts
- Prevents overwhelming backend/AI services

### 2. **Optimistic Update**
- Certificate list refreshes after batch completes
- User sees results immediately

### 3. **Duplicate Detection**
- Checks before creating record
- Skips duplicate certificates
- Shows which certificates are duplicates

### 4. **Error Resilience**
- Individual file failures don't stop batch
- Database record saved even if file upload fails
- Clear error messages for each file

### 5. **Progress Tracking**
- Real-time progress counter
- Per-file status updates
- Final results summary modal

---

## 🔧 Technical Notes

### **Why Staggered?**
- Google Apps Script has rate limits
- AI API (Gemini/GPT) has concurrent request limits
- Reduces server load
- Better error handling and debugging

### **Why Upload Files After DB Record?**
- Ensures data consistency
- Certificate record exists even if upload fails
- Files can be re-uploaded later if needed
- Cleaner transaction handling

### **Why Base64 in Memory?**
- File content preserved through validation steps
- No temporary file storage needed
- Direct upload to Drive via API
- Works in stateless environment

---

## 📝 User Experience Flow

```
1. User: Select 5 certificate files
2. System: "Bắt đầu xử lý 5 file chứng chỉ (song song)..."
3. System: Progress shows "1/5", "2/5", "3/5", "4/5", "5/5"
4. System: Modal closes, certificate list refreshes
5. System: Shows results modal:
   ✅ 3 certificates added successfully
   ⚠️ 1 duplicate skipped
   ❌ 1 failed (error message)
6. User: Can immediately add more certificates or continue work
```

---

## 🚀 Performance

- **Single File:** ~5-10 seconds (AI analysis + validation + DB + upload)
- **5 Files (Parallel):** ~15-20 seconds (vs 25-50 seconds sequential)
- **10 Files (Parallel):** ~30-40 seconds (vs 50-100 seconds sequential)

**Speedup Factor:** ~2-3x faster than sequential processing
