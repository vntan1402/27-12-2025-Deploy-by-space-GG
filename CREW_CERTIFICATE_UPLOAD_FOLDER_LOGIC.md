# Crew Certificate Upload - Folder Determination Logic

## Question
**"Khi Add Crew Certificate, File upload sẽ xác định Upload folder như thế nào?"**

Translation: "When adding Crew Certificate, how does File upload determine the Upload folder?"

## Answer Summary

Khi upload Crew Certificate, hệ thống xác định folder theo **SHIP NAME**:

**Cấu trúc folder:**
```
ROOT FOLDER (Company Drive)
└── {Ship Name}/
    └── Crew Records/
        ├── Certificate_File.pdf (Original file)
        └── ...

SUMMARY Folder (for AI-extracted summary)
└── SUMMARY/
    └── Crew Records/
        └── Certificate_File_Summary.txt
```

**Ví dụ:** Ship "BROTHER 36" → Upload vào `BROTHER 36/Crew Records/`

---

## Detailed Flow Analysis

### 1. Frontend: Add Crew Certificate

**Location:** `/app/frontend/src/App.js` - `handleAddCrewCertificateSubmit()`

**Flow:**
1. User selects ship from dropdown (required field)
2. User selects crew member (optional - for validation)
3. User uploads certificate file(s)
4. Frontend sends to backend endpoint: `POST /api/crew-certificates/manual`

**Key Data Sent:**
```javascript
{
  ship_id: selectedShip,  // Ship ID is REQUIRED
  crew_id: selectedCrew,  // Crew ID (optional)
  cert_name: "...",
  cert_no: "...",
  // ... other fields
  _file_content: base64_content,  // Stored temporarily
  _filename: "certificate.pdf",
  _content_type: "application/pdf"
}
```

### 2. Backend: Certificate Creation

**Location:** `/app/backend/server.py` - `POST /crew-certificates/manual` (line ~13671)

**Step 1: Validate Ship**
```python
# Get ship info to determine folder structure
ship = await mongo_db.find_one("ships", {
    "id": ship_id,
    "company_id": company_uuid
})

if not ship:
    raise HTTPException(status_code=404, detail="Ship not found")

ship_name = ship.get("name")  # ← KEY INFORMATION for folder
```

**Step 2: Create Certificate in Database**
```python
# Create certificate record FIRST (without file IDs)
await mongo_db.insert_one("crew_certificates", cert_data)
```

**Step 3: Upload Files to Drive**
```python
# Call upload endpoint with file data
await upload_certificate_files_after_creation(
    cert_id=cert_id,
    file_data={
        'file_content': file_content,
        'filename': filename,
        'content_type': content_type,
        'summary_text': summary_text
    }
)
```

### 3. Backend: File Upload to Drive

**Location:** `/app/backend/server.py` - `upload_certificate_files_after_creation()` (line ~14193)

**Critical Logic:**
```python
# Get ship info to determine upload folder
ship = await mongo_db.find_one("ships", {
    "id": cert.get("ship_id"),
    "company_id": company_uuid
})

ship_name = ship.get("name", "Unknown Ship")  # ← FOLDER DETERMINATION KEY

# Upload using dual manager
upload_result = await dual_manager.upload_certificate_files(
    cert_file_content=file_content,
    cert_filename=filename,
    cert_content_type=content_type,
    ship_name=ship_name,  # ← SHIP NAME determines folder
    summary_text=summary_text
)
```

### 4. Dual Apps Script Manager: Actual Upload

**Location:** `/app/backend/dual_apps_script_manager.py` - `upload_certificate_files()` (line ~665)

**Upload Logic:**

**Original Certificate File:**
```python
# Upload to: {ship_name}/Crew Records/
cert_upload = await self._call_company_apps_script({
    'action': 'upload_file_with_folder_creation',
    'parent_folder_id': self.parent_folder_id,  # Company Drive ROOT
    'ship_name': ship_name,  # ← Creates/finds ship folder
    'category': 'Crew Records',  # ← Creates/finds subfolder
    'filename': cert_filename,
    'file_content': base64_content,
    'content_type': cert_content_type
})
```

**Summary File (if AI extracted):**
```python
# Upload to: SUMMARY/Crew Records/
summary_upload = await self._call_company_apps_script({
    'action': 'upload_file_with_folder_creation',
    'parent_folder_id': self.parent_folder_id,
    'ship_name': 'SUMMARY',  # ← Fixed folder name
    'category': 'Crew Records',
    'filename': summary_filename,
    'file_content': base64_summary,
    'content_type': 'text/plain'
})
```

### 5. Google Apps Script: Folder Creation

**Location:** Google Apps Script deployed as Web App

**Action:** `upload_file_with_folder_creation`

**Logic:**
```javascript
// Input parameters:
// - parent_folder_id: Company Drive ROOT folder ID
// - ship_name: "BROTHER 36" or "SUMMARY"
// - category: "Crew Records"

// Step 1: Find or create ship folder in ROOT
var shipFolder = findOrCreateFolder(parentFolder, shipName);

// Step 2: Find or create category folder in ship folder
var categoryFolder = findOrCreateFolder(shipFolder, category);

// Step 3: Upload file to category folder
var file = categoryFolder.createFile(blob);

// Returns: file_id, folder_id, etc.
```

---

## Folder Structure Examples

### Example 1: Certificate for "BROTHER 36"

**Input:**
- Ship: BROTHER 36 (ship_id: xxx)
- File: GMDSS_Certificate.pdf

**Upload Location:**
```
Company Drive ROOT
└── BROTHER 36/
    └── Crew Records/
        └── GMDSS_Certificate.pdf

SUMMARY/
└── Crew Records/
    └── GMDSS_Certificate_Summary.txt
```

### Example 2: Certificate for "MINH ANH 09"

**Input:**
- Ship: MINH ANH 09 (ship_id: yyy)
- File: COC_Certificate.pdf

**Upload Location:**
```
Company Drive ROOT
└── MINH ANH 09/
    └── Crew Records/
        └── COC_Certificate.pdf

SUMMARY/
└── Crew Records/
    └── COC_Certificate_Summary.txt
```

### Example 3: Multiple Certificates, Same Ship

**Input:**
- Ship: BROTHER 36
- Files: STCW.pdf, Medical.pdf, Passport.pdf

**Upload Location:**
```
Company Drive ROOT
└── BROTHER 36/
    └── Crew Records/
        ├── STCW.pdf
        ├── Medical.pdf
        └── Passport.pdf

SUMMARY/
└── Crew Records/
    ├── STCW_Summary.txt
    ├── Medical_Summary.txt
    └── Passport_Summary.txt
```

---

## Key Determination Factors

### Primary Factor: SHIP NAME
The upload folder is **100% determined by the ship selected** when adding the certificate.

**Why Ship Name?**
1. Certificates are ship-specific documents
2. Crew members work on specific ships
3. Documents must be organized by ship for easy access
4. Maritime industry standard: ship-based document organization

### Configuration Dependencies

**1. Company Google Drive Config:**
```javascript
{
  company_id: "...",
  folder_id: "ROOT_FOLDER_ID",  // ← Parent of all ship folders
  web_app_url: "https://script.google.com/..."
}
```

**2. Ship Record:**
```javascript
{
  id: "ship_uuid",
  name: "BROTHER 36",  // ← This determines folder name
  company_id: "..."
}
```

**3. Certificate Record:**
```javascript
{
  id: "cert_uuid",
  ship_id: "ship_uuid",  // ← Links certificate to ship
  crew_id: "crew_uuid",
  cert_name: "GMDSS Certificate",
  // ... other fields
  crew_cert_file_id: "drive_file_id",
  crew_cert_summary_file_id: "drive_summary_id"
}
```

---

## Important Notes

### 1. Folder Creation is Automatic
- Ship folder is created if it doesn't exist
- "Crew Records" subfolder is created if it doesn't exist
- No manual folder setup required

### 2. Ship Selection is REQUIRED
- Cannot add certificate without selecting a ship
- Frontend enforces this validation
- Backend validates ship exists

### 3. Folder Path is NOT Stored (for Certificates)
Unlike Passport/Standby Crew files, certificate records do NOT store `folder_path`.
The folder can always be determined from the ship name.

**Passport/Standby Crew:**
```javascript
{
  passport_folder_path: "COMPANY DOCUMENT/Standby Crew"
}
```

**Crew Certificate:**
```javascript
{
  // No folder_path field
  // Folder determined by ship_id → ship.name → "{ship_name}/Crew Records"
}
```

### 4. Multiple Ships = Multiple Folders
If a crew member works on multiple ships:
- Each certificate goes to the ship's folder where it was issued/valid
- Separate certificate records for each ship

### 5. File Movement (Standby Status)
When a crew member's status changes to "Standby", their certificate files are moved:

**From:**
```
{Ship Name}/Crew Records/Certificate.pdf
```

**To:**
```
COMPANY DOCUMENT/Standby Crew/Certificate.pdf
```

This is handled by the `/crew/move-standby-files` endpoint.

---

## Related Endpoints

### Create Certificate
```
POST /api/crew-certificates/manual
```
- Creates certificate record in database
- Calls upload endpoint automatically

### Upload Certificate Files
```
POST /api/crew-certificates/{cert_id}/upload-files
```
- Uploads files to Google Drive
- Uses ship name from certificate's ship_id
- Updates certificate record with file IDs

### Move Standby Files
```
POST /api/crew/move-standby-files
```
- Moves certificate files when crew becomes Standby
- Changes folder from ship-specific to shared Standby folder

---

## Folder Determination Algorithm (Pseudocode)

```python
def determine_certificate_upload_folder(cert_data):
    """
    Determine where to upload crew certificate file
    
    Returns: Google Drive folder path
    """
    # Step 1: Get ship ID from certificate
    ship_id = cert_data['ship_id']
    
    # Step 2: Get ship name from database
    ship = database.find_ship(ship_id)
    ship_name = ship['name']  # e.g., "BROTHER 36"
    
    # Step 3: Construct folder path
    folder_path = f"{ship_name}/Crew Records"
    
    # Step 4: Apps Script creates folders if needed
    # - Finds/creates ship folder in ROOT
    # - Finds/creates "Crew Records" subfolder
    
    return folder_path

# Examples:
# Ship: "BROTHER 36" → "BROTHER 36/Crew Records"
# Ship: "MINH ANH 09" → "MINH ANH 09/Crew Records"
# Ship: "OCEAN STAR" → "OCEAN STAR/Crew Records"
```

---

## Summary

**Upload folder xác định bởi:**
1. **Ship được chọn** khi thêm certificate (REQUIRED)
2. Ship Name từ database → Tên folder
3. Category cố định: "Crew Records"
4. Folder structure: `{Ship Name}/Crew Records/`

**Ví dụ:**
- Ship "BROTHER 36" → Upload vào `BROTHER 36/Crew Records/`
- Ship "MINH ANH 09" → Upload vào `MINH ANH 09/Crew Records/`

**Key Point:** Ship Name là yếu tố duy nhất quyết định folder upload!
