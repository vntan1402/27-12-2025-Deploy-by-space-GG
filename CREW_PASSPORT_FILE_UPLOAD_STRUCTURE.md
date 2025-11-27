# 📁 CẤU TRÚC UPLOAD FILES CHO CREW MEMBER PASSPORT

## 🎯 TỔNG QUAN

Khi upload passport file cho crew member, hệ thống sẽ tạo 2 files trong Google Drive:
1. **File gốc** (passport PDF/image)
2. **File summary** (text file chứa OCR summary)

---

## 📂 FOLDER STRUCTURE TRONG GOOGLE DRIVE

### Case 1: Crew có tàu (Status = "Sign on" hoặc ship_name != "-")

```
[Company Root Folder]
└── [Ship Name]/
    └── Passport/
        ├── [original_filename].pdf          ← File passport gốc
        └── SUMMARY/
            └── [crew_name]_[passport_no]_summary.txt  ← File summary
```

**Example:**
```
Company Root/
└── BROTHER 36/
    └── Passport/
        ├── nguyen_van_a_passport.pdf        ← File gốc
        └── SUMMARY/
            └── NGUYEN_VAN_A_B1234567_summary.txt  ← Summary
```

---

### Case 2: Crew Standby (Status = "Standby" hoặc ship_name = "-")

```
[Company Root Folder]
└── Standby Crew/
    └── Passport/
        ├── [original_filename].pdf          ← File passport gốc
        └── SUMMARY/
            └── [crew_name]_[passport_no]_summary.txt  ← File summary
```

**Example:**
```
Company Root/
└── Standby Crew/
    └── Passport/
        ├── le_van_c_passport.pdf            ← File gốc
        └── SUMMARY/
            └── LE_VAN_C_B3456789_summary.txt  ← Summary
```

---

## 🔧 LOGIC XÁC ĐỊNH FOLDER PATH

### Code Implementation:

```python
# In GoogleDriveService.upload_passport_files()

# Determine folder path based on ship_name
if ship_name and ship_name != '-':
    # Crew có tàu
    folder_path = f"{ship_name}/Passport"
    summary_folder_path = f"{ship_name}/Passport/SUMMARY"
else:
    # Crew standby
    folder_path = "Standby Crew/Passport"
    summary_folder_path = "Standby Crew/Passport/SUMMARY"
```

### Upload Process:

```python
# 1. Upload file passport gốc
passport_file_id = await drive_helper.upload_file(
    file_content=file_content,
    filename=filename,                    # Original filename from upload
    folder_path=folder_path,              # [Ship Name]/Passport or Standby Crew/Passport
    mime_type=content_type                # application/pdf or image/jpeg
)

# 2. Upload file summary
summary_filename = f"{crew_name}_{passport_number}_summary.txt"
summary_file_id = await drive_helper.upload_file(
    file_content=summary_content.encode('utf-8'),
    filename=summary_filename,            # Generated filename
    folder_path=summary_folder_path,      # [Ship Name]/Passport/SUMMARY
    mime_type='text/plain'
)
```

---

## 📝 FILE NAMING CONVENTION

### 1. File Passport Gốc:
**Format:** Giữ nguyên tên file upload ban đầu

**Examples:**
- `passport_nguyen_van_a.pdf`
- `NGUYEN_VAN_A_passport_scan.jpg`
- `scan_20231215.pdf`

**Source:** Frontend upload filename

---

### 2. File Summary:
**Format:** `{CREW_NAME}_{PASSPORT_NO}_summary.txt`

**Rules:**
- `CREW_NAME`: Full name của crew (uppercase, spaces thành underscores)
- `PASSPORT_NO`: Số passport
- Extension: `.txt` (text/plain)

**Examples:**
- `NGUYEN_VAN_A_B1234567_summary.txt`
- `TRAN_THI_B_B2345678_summary.txt`
- `LE_VAN_C_B3456789_summary.txt`

**Code:**
```python
summary_filename = f"{crew_name}_{passport_number}_summary.txt"
```

---

## 📄 NỘI DUNG FILE SUMMARY

File summary chứa thông tin được extract từ OCR:

```text
PASSPORT ANALYSIS SUMMARY
Generated: 2025-01-27T14:30:00+00:00
Ship: BROTHER 36
Original File: nguyen_van_a_passport.pdf

CREW INFORMATION:
- Name: NGUYEN VAN A
- Passport Number: B1234567

OCR EXTRACTED TEXT:
[Full OCR text from passport...]

---
This summary was generated automatically using AI OCR for crew management.
```

**Code:**
```python
def _generate_summary_content(
    self,
    crew_name: str,
    passport_number: str,
    ship_name: str,
    summary_text: str,
    filename: str
) -> str:
    return f"""PASSPORT ANALYSIS SUMMARY
Generated: {datetime.now(timezone.utc).isoformat()}
Ship: {ship_name}
Original File: {filename}

CREW INFORMATION:
- Name: {crew_name}
- Passport Number: {passport_number}

OCR EXTRACTED TEXT:
{summary_text}

---
This summary was generated automatically using AI OCR for crew management.
"""
```

---

## 🔄 LIFECYCLE MANAGEMENT

### 1. Upload (Crew Creation)
```
1. User uploads passport → AI analysis
2. User creates crew → backend receives file_content
3. Backend calls GoogleDriveService.upload_passport_files()
4. Upload passport file → Get passport_file_id
5. Upload summary file → Get summary_file_id
6. Update crew record in MongoDB with file IDs
```

### 2. Update (Crew Edit)
- File IDs remain unchanged
- Files remain in same location
- Only crew data updated in MongoDB

### 3. Delete (Crew Deletion)
```
1. User deletes crew
2. Backend calls GoogleDriveService.delete_passport_files()
3. Delete passport file by passport_file_id
4. Delete summary file by summary_file_id
5. Delete crew record from MongoDB
```

### 4. Move (Ship Change)
**TODO:** Not yet implemented
```
When crew.ship_sign_on changes:
1. Detect ship change
2. Move files from old ship folder to new ship folder
3. Update folder path in Drive
4. Keep same file IDs (just change parent folder)
```

---

## 🗂️ COMPLETE FOLDER STRUCTURE EXAMPLE

```
ABC Shipping Company/ (Company Root)
├── BROTHER 36/
│   ├── Passport/
│   │   ├── crew1_passport.pdf
│   │   ├── crew2_passport.jpg
│   │   └── SUMMARY/
│   │       ├── NGUYEN_VAN_A_B1234567_summary.txt
│   │       └── TRAN_VAN_B_B2345678_summary.txt
│   ├── Certificates/
│   │   └── ...
│   └── Documents/
│       └── ...
│
├── SISTER 20/
│   ├── Passport/
│   │   ├── crew3_passport.pdf
│   │   └── SUMMARY/
│   │       └── LE_VAN_C_C9876543_summary.txt
│   └── ...
│
└── Standby Crew/
    ├── Passport/
    │   ├── standby1_passport.pdf
    │   ├── standby2_passport.pdf
    │   └── SUMMARY/
    │       ├── PHAM_VAN_D_D1111111_summary.txt
    │       └── HOANG_THI_E_E2222222_summary.txt
    └── ...
```

---

## 🔍 DATABASE TRACKING

Crew record trong MongoDB lưu file IDs:

```json
{
  "id": "crew-uuid-123",
  "full_name": "NGUYEN VAN A",
  "passport": "B1234567",
  "ship_sign_on": "BROTHER 36",
  "status": "Sign on",
  
  "passport_file_id": "1ABC...XYZ",      // Google Drive file ID của passport
  "summary_file_id": "2DEF...UVW",       // Google Drive file ID của summary
  
  "created_at": "2025-01-27T10:30:00Z",
  ...
}
```

---

## 🎯 KEY POINTS

1. **2 Files per Crew:**
   - Passport file (original)
   - Summary file (OCR text)

2. **Folder Path Logic:**
   - Has ship → `[Ship Name]/Passport/`
   - Standby → `Standby Crew/Passport/`

3. **Summary Subfolder:**
   - Always in `/SUMMARY/` subfolder
   - Keeps passport folder clean

4. **File Naming:**
   - Passport: Original filename
   - Summary: `{NAME}_{PASSPORT}_summary.txt`

5. **Database References:**
   - Both file IDs stored in crew record
   - Used for deletion/management

---

## 📋 RELATED FILES

**Backend Implementation:**
- `/app/backend/app/services/google_drive_service.py` - Upload logic
- `/app/backend/app/utils/google_drive_helper.py` - Drive API wrapper
- `/app/backend/app/api/v1/crew.py` - Upload endpoint

**Frontend:**
- `/app/frontend/src/components/CrewList/AddCrewModal.jsx` - Upload UI
- `/app/frontend/src/services/crewService.js` - API calls

---

**Document Created:** 2025-01-27
**Last Updated:** 2025-01-27
**Version:** 2.0 (V2 Implementation)
