# ADD CREW PROCESS - V1 Complete Flow

## OVERVIEW
The Add Crew feature supports both single and batch passport processing with AI analysis.

---

## FRONTEND WORKFLOW

### 1. OPEN ADD CREW MODAL
**Trigger:** Click "Thêm thuyền viên" button
**Requirements:** User role = `manager`, `admin`, or `super_admin`

### 2. MODAL FEATURES

#### Header Section
- **Title:** "Thêm thuyền viên mới cho [Ship Name]"
- **Ship Select Dropdown:** Change target ship (only in normal mode)
- **Standby Mode Toggle:** Switch between "Sign on" and "Standby" status
- **Minimize Button:** Collapse modal to floating button
- **Close Button:** Close and reset form
- **Draggable:** Modal can be moved around screen

#### Body Section

**A. AI Passport Analysis Section (Top)**
```
┌─────────────────────────────────────────────────────────┐
│ 📄 Phân tích từ hộ chiếu (AI)                           │
│ Tải lên file hộ chiếu để tự động phân tích...           │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐         │
│ │ Kéo thả file(s) hoặc click để chọn     📁  │         │
│ │ Hỗ trợ: PDF, JPG, PNG (tối đa 10MB)        │         │
│ │ 1 file: Review | Nhiều file: Auto-add      │         │
│ └─────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

**File Upload Options:**
- **Single File:** Analyze → Review → Manual submit
- **Multiple Files:** Batch process → Auto-submit each → Results modal

**B. Manual Entry Form (Bottom)**
```
Required Fields:
- Full Name (Vietnamese) *
- Date of Birth *
- Place of Birth *
- Passport Number *

Optional Fields:
- Full Name (English)
- Sex (M/F)
- Place of Birth (English)
- Nationality
- Passport Expiry Date
- Rank
- Seamen Book
- Status (Sign on/Standby/Leave)
- Ship Sign On
- Place Sign On
- Date Sign On
- Date Sign Off
```

---

## SINGLE FILE FLOW

### Step 1: File Upload & Validation
```javascript
// Frontend validation
- File type: PDF, JPG, PNG
- File size: <= 10MB
- Valid file selected
```

### Step 2: Call Backend Analysis API
```javascript
POST /api/crew/analyze-passport
Content-Type: multipart/form-data

Body:
- passport_file: File
- ship_name: string
```

### Step 3: Backend AI Analysis Process

**3.1 File Processing**
- Read file content
- Get company UUID
- Validate AI configuration (Document AI)

**3.2 Document AI Analysis**
```javascript
// Call Google Apps Script
action: "analyze_passport_document_ai"
payload: {
  file_content: base64_encoded,
  filename: string,
  content_type: string,
  project_id: string,
  location: "us",
  processor_id: string
}
```

**3.3 AI Field Extraction**
```javascript
// Uses System AI (Gemini/GPT) to extract fields from Document AI summary
Extracted Fields:
- full_name
- sex
- date_of_birth
- place_of_birth
- passport_number
- nationality
- issue_date
- expiry_date
- confidence_score
```

**3.4 Duplicate Check**
```javascript
// Before uploading files
Query: { company_id, passport: passport_number }
If exists → Return duplicate error with crew details
```

**3.5 Validation - Passport vs Seaman Book**
```javascript
// Keywords to detect Seaman Book:
['seaman book', 'seamanbook', 'cdc', 
 'certificate of competency', 'endorsement', 
 'panama maritime authority', 'seafarer']

// Must have:
- passport_number
- date_of_birth OR nationality
```

### Step 4: Frontend Receives Analysis
```javascript
Response: {
  success: true,
  analysis_result: {...extracted_fields},
  raw_summary: "...",
  _file_content: base64_string,  // Stored for later upload
  _filename: string,
  _content_type: string,
  _summary_text: string,
  _ship_name: string
}
```

### Step 5: Auto-fill Form
- Pre-fill all form fields with AI-extracted data
- User can review and edit
- Display "✅ Hộ chiếu đã được phân tích thành công"

### Step 6: User Review & Submit
- User edits/confirms data
- Click "Thêm thuyền viên" button
- Validation of required fields

### Step 7: Create Crew Member
```javascript
POST /api/crew
Body: {
  full_name: string,
  full_name_en: string,
  sex: string,
  date_of_birth: datetime,
  place_of_birth: string,
  place_of_birth_en: string,
  passport: string,
  nationality: string,
  rank: string,
  seamen_book: string,
  status: "Sign on" | "Standby" | "Leave",
  ship_sign_on: string,
  place_sign_on: string,
  date_sign_on: datetime,
  date_sign_off: datetime,
  passport_expiry_date: datetime
}
```

**Backend Process:**
1. Validate required fields
2. Check passport duplication
3. Create crew record in MongoDB
4. Return crew ID

### Step 8: Upload Passport Files (After Creation)
```javascript
POST /api/crew/{crew_id}/upload-passport-files
Body: {
  file_content: base64_string,
  filename: string,
  content_type: string,
  summary_text: string,
  ship_name: string
}
```

**Upload Process:**
1. Decode base64 file content
2. Call `dual_apps_script_manager.upload_passport_files()`
3. Upload to Drive: `[Ship Name]/Passport/`
   - Original file: `[filename]`
   - Summary file: `[name]_[passport]_summary.txt`
4. Get file IDs from Google Drive
5. Update crew record with `passport_file_id` and `summary_file_id`

**Drive Folder Structure:**
```
Company Root/
└── [Ship Name]/
    └── Passport/
        ├── [original_filename].pdf
        └── SUMMARY/
            └── [name]_[passport]_summary.txt
```

### Step 9: Auto-move to Standby (if applicable)
```javascript
if (crew.status === "Standby") {
  // Move files from ship folder to Standby folder
  moveStandbyCrewFiles([crew_id], crew.full_name);
}
```

### Step 10: Refresh & Close
- Refresh crew list
- Show success toast
- Close modal
- Reset form

---

## BATCH PROCESSING FLOW

### Step 1: Multiple Files Selected
- User drops/selects multiple files (2+ files)
- Frontend validates each file
- Triggers batch processing

### Step 2: Parallel Processing with Staggered Start
```javascript
startBatchProcessing(files) {
  // Process files in parallel with 1-second stagger
  files.forEach((file, index) => {
    setTimeout(() => {
      processSinglePassportInBatch(file);
    }, index * 1000);
  });
}
```

### Step 3: Process Each File
```javascript
processSinglePassportInBatch(file) {
  1. Analyze passport (same API as single file)
  2. If duplicate → Skip with error
  3. If invalid (Seaman Book) → Skip with error
  4. Auto-create crew member (no user review)
  5. Upload files immediately
  6. Return result { success, filename, crew_name, error }
}
```

### Step 4: Progress Tracking
```javascript
// Live progress display
Current: 3/10
Progress Bar: 30%
Status: Processing [filename]
Success: 2
Failed: 1
```

### Step 5: Close Modal During Processing
- Modal closes automatically
- Batch continues in background
- Progress tracked in state

### Step 6: Show Results Modal
```javascript
// After all files processed
Results:
┌─────────────────────────────────────────┐
│ Batch Processing Results                │
├─────────────────────────────────────────┤
│ Total: 10                               │
│ Success: 8                              │
│ Failed: 2                               │
├─────────────────────────────────────────┤
│ ✅ John_Smith.pdf → NGUYEN VAN A       │
│ ✅ Jane_Doe.pdf → TRAN THI B           │
│ ❌ CDC_123.pdf → Not a passport        │
│ ❌ Passport_456.pdf → Duplicate        │
│ ...                                     │
└─────────────────────────────────────────┘
```

---

## BACKEND API ENDPOINTS

### 1. Analyze Passport
```
POST /api/crew/analyze-passport
Authorization: Bearer {token}
Content-Type: multipart/form-data

Request:
- passport_file: File
- ship_name: string

Response: {
  success: boolean,
  analysis_result: {
    full_name: string,
    sex: string,
    date_of_birth: string,
    place_of_birth: string,
    passport_number: string,
    nationality: string,
    issue_date: string,
    expiry_date: string,
    confidence_score: number
  },
  raw_summary: string,
  duplicate?: boolean,
  existing_crew?: object
}
```

### 2. Create Crew Member
```
POST /api/crew
Authorization: Bearer {token}
Content-Type: application/json

Request: CrewCreate (Pydantic model)

Response: CrewResponse {
  id: uuid,
  company_id: uuid,
  ...all crew fields,
  created_at: datetime,
  created_by: string
}

Errors:
- 400: Passport already exists
- 400: Missing required fields
```

### 3. Upload Passport Files
```
POST /api/crew/{crew_id}/upload-passport-files
Authorization: Bearer {token}
Content-Type: application/json

Request: {
  file_content: string (base64),
  filename: string,
  content_type: string,
  summary_text: string,
  ship_name: string
}

Response: {
  success: boolean,
  message: string,
  passport_file_id: string,
  summary_file_id: string
}
```

### 4. Get Crew List
```
GET /api/crew?ship_name=...&status=...
Authorization: Bearer {token}

Response: CrewResponse[]
```

---

## KEY FEATURES

### ✅ AI-Powered Analysis
- Google Document AI for OCR
- Gemini/GPT for field extraction
- Confidence scoring
- Raw summary preservation

### ✅ Duplicate Prevention
- Check before file upload
- Return detailed duplicate info
- Prevent wasted Drive storage

### ✅ Document Validation
- Detect Seaman Books vs Passports
- Keyword-based filtering
- Field presence validation

### ✅ Batch Processing
- Parallel processing with stagger
- Live progress tracking
- Individual error handling
- Detailed results summary

### ✅ Google Drive Integration
- Auto-upload to ship folders
- Separate summary files
- File ID tracking in database
- Auto-move for Standby crew

### ✅ Flexible Workflow
- Single file: Review before submit
- Multiple files: Auto-submit
- Manual entry fallback
- Edit AI-extracted data

---

## ERROR HANDLING

### Common Errors

**1. Duplicate Passport**
```javascript
Response: {
  success: false,
  duplicate: true,
  error: "DUPLICATE_PASSPORT",
  existing_crew: {...}
}
Action: Skip or notify user
```

**2. Invalid Document (Seaman Book)**
```javascript
Error: "This is a Seaman Book, not a Passport"
Action: Skip with warning
```

**3. AI Analysis Failed**
```javascript
Error: "Document AI processing failed"
Fallback: Return empty fields for manual entry
```

**4. File Upload Failed**
```javascript
Warning: "Crew added but file upload failed"
Result: Crew saved, files not uploaded
```

**5. Missing AI Configuration**
```javascript
Error: "AI configuration not found"
Action: Redirect to System Settings
```

---

## STATE MANAGEMENT

### Key States
```javascript
// Modal states
const [showAddCrewModal, setShowAddCrewModal] = useState(false);
const [isAddCrewModalMinimized, setIsAddCrewModalMinimized] = useState(false);

// Form data
const [newCrewData, setNewCrewData] = useState({...});

// File upload states
const [passportFile, setPassportFile] = useState(null);
const [passportAnalysis, setPassportAnalysis] = useState(null);
const [isAnalyzingPassport, setIsAnalyzingPassport] = useState(false);
const [passportError, setPassportError] = useState('');

// Batch processing states
const [selectedFiles, setSelectedFiles] = useState([]);
const [isBatchProcessing, setIsBatchProcessing] = useState(false);
const [currentFileIndex, setCurrentFileIndex] = useState(0);
const [batchResults, setBatchResults] = useState([]);
const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });
const [showProcessingResultsModal, setShowProcessingResultsModal] = useState(false);
const [processingResults, setProcessingResults] = useState([]);

// Submission
const [isSubmittingCrew, setIsSubmittingCrew] = useState(false);
```

---

## VALIDATION RULES

### Required Fields (Backend)
```javascript
✅ full_name
✅ date_of_birth
✅ place_of_birth
✅ passport
```

### Optional but Recommended
```javascript
- full_name_en (for bilingual support)
- sex
- nationality
- passport_expiry_date
- rank
- ship_sign_on
```

### Date Processing
```javascript
// All dates converted to UTC to avoid timezone shifts
convertDateInputToUTC(date_string)
```

---

## MIGRATION NOTES FOR V2

### Components to Create
1. **AddCrewModal.jsx** - Main modal with AI upload
2. **BatchProcessingModal.jsx** - Live progress tracking
3. **BatchResultsModal.jsx** - Results summary

### Services to Create
```javascript
// crewService.js
- analyzePa ssport(file, shipName)
- createCrew(crewData)
- uploadPassportFiles(crewId, fileData)
- getCrewList(filters)
```

### Key Features to Implement
1. ✅ Drag & drop file upload
2. ✅ Single file review flow
3. ✅ Batch processing with parallel execution
4. ✅ AI-powered passport analysis
5. ✅ Duplicate detection
6. ✅ Seaman Book filtering
7. ✅ Google Drive integration
8. ✅ Progress tracking
9. ✅ Results modal
10. ✅ Standby mode toggle
11. ✅ Ship selection dropdown
12. ✅ Draggable & minimizable modal

---

**Last Updated:** 2025-01-01
**V1 Reference:** `/app/frontend-v1/src/App.js` lines 9516-10127, 22719-23500
**Backend Reference:** `/app/backend/server.py` lines 16688-17772
