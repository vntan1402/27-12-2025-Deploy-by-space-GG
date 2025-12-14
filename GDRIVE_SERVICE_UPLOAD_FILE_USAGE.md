# GDriveService.upload_file() Usage Summary

## 📋 OVERVIEW

`GDriveService.upload_file()` is the **NEW unified method** for uploading files to Google Drive with automatic folder creation using `createNestedFolders()` in Apps Script.

**Method signature:**
```python
async def upload_file(
    file_content: bytes,
    filename: str,
    content_type: str,
    folder_path: str,      # Format: "ShipName/ParentCategory/Category" or "COMPANY DOCUMENT/..."
    company_id: str
) -> dict
```

---

## 📁 SHIP-BASED DOCUMENTS (9 Types)

All ship documents use format: `{ShipName}/ParentCategory/Category/`

### **1. Ship Certificate (Certificates)** ✅
- **Service:** `certificate_multi_upload_service.py` (after fix)
- **Folder Path:** `{ShipName}/Class & Flag Cert/Certificates/`
- **Files:** 
  - Main: `certificate.pdf`
  - Summary: `certificate_Summary.txt`
- **Status:** Fixed to use `_upload_to_gdrive_with_parent()` which calls `GDriveService.upload_file()`

### **2. Audit Certificate (ISM/ISPS/MLC)** ✅
- **API:** `audit_certificates.py` (line 421, 457, 630, 663)
- **Folder Path:** `{ShipName}/ISM - ISPS - MLC/Audit Certificates/`
- **Files:**
  - Main: `audit_cert.pdf`
  - Summary: `audit_cert_Summary.txt`
- **Usage:** Multi-upload endpoint + single upload

### **3. Survey Report (Class Survey Report)** ✅
- **Service:** `survey_report_service.py` (line 405, 447)
- **Folder Path:** `{ShipName}/Class & Flag Cert/Class Survey Report/`
- **Files:**
  - Main: `survey_report.pdf`
  - Summary: `survey_report_Summary.txt`

### **4. Test Report** ✅
- **Service:** `test_report_service.py` (line 451, 485)
- **Folder Path:** `{ShipName}/Class & Flag Cert/Test Report/`
- **Files:**
  - Main: `test_report.pdf`
  - Summary: `test_report_Summary.txt`

### **5. Drawings & Manuals** ✅
- **Service:** `drawing_manual_service.py` (line 351, 385)
- **Folder Path:** `{ShipName}/Class & Flag Cert/Drawings & Manuals/`
- **Files:**
  - Main: `drawing.pdf` / `manual.pdf`
  - Summary: `drawing_Summary.txt`

### **6. Audit Report** ✅
- **Service:** `audit_report_service.py` (line 432, 465)
- **Folder Path:** `{ShipName}/ISM - ISPS - MLC/Audit Report/`
- **Files:**
  - Main: `audit_report.pdf`
  - Summary: `audit_report_Summary.txt`

### **7. Approval Document** ✅
- **Service:** `approval_document_service.py` (line 409, 444)
- **Folder Path:** `{ShipName}/ISM - ISPS - MLC/Approval Document/`
- **Files:**
  - Main: `approval_doc.pdf`
  - Summary: `approval_doc_Summary.txt`

### **8. Other Documents** (Assumed - not found in grep)
- **Folder Path:** `{ShipName}/Class & Flag Cert/Other Documents/` (likely)

### **9. Crew Certificates** (Possible - needs verification)
- **Folder Path:** `{ShipName}/Crew Records/Crew Certificates/` (likely)

---

## 🏢 COMPANY-BASED DOCUMENTS (1 Type)

Company documents use format: `COMPANY DOCUMENT/Category/Subcategory/`

### **10. Company Certificate (SMS)** ✅
- **API:** `company_certs.py` (line 206, 235, 299, 324)
- **Folder Path:** `COMPANY DOCUMENT/SMS/Company Certificates/`
- **Files:**
  - Main: `company_cert.pdf`
  - Summary: `company_cert_Summary.txt`
- **Note:** This is NOT ship-specific, stored at company level

---

## 📊 SUMMARY TABLE

| Document Type | Parent Category | Category | Folder Path |
|---------------|-----------------|----------|-------------|
| **Ship Certificate** | Class & Flag Cert | Certificates | `{Ship}/Class & Flag Cert/Certificates/` |
| **Survey Report** | Class & Flag Cert | Class Survey Report | `{Ship}/Class & Flag Cert/Class Survey Report/` |
| **Test Report** | Class & Flag Cert | Test Report | `{Ship}/Class & Flag Cert/Test Report/` |
| **Drawings & Manuals** | Class & Flag Cert | Drawings & Manuals | `{Ship}/Class & Flag Cert/Drawings & Manuals/` |
| **Audit Certificate** | ISM - ISPS - MLC | Audit Certificates | `{Ship}/ISM - ISPS - MLC/Audit Certificates/` |
| **Audit Report** | ISM - ISPS - MLC | Audit Report | `{Ship}/ISM - ISPS - MLC/Audit Report/` |
| **Approval Document** | ISM - ISPS - MLC | Approval Document | `{Ship}/ISM - ISPS - MLC/Approval Document/` |
| **Company Certificate** | N/A (company-level) | N/A | `COMPANY DOCUMENT/SMS/Company Certificates/` |

---

## 🔄 FOLDER AUTO-CREATION BEHAVIOR

All uses of `GDriveService.upload_file()` have **automatic folder creation** via Apps Script's `createNestedFolders()`:

```javascript
function createNestedFolders(parentFolder, folderNames) {
  var currentFolder = parentFolder;
  
  for (var i = 0; i < folderNames.length; i++) {
    var folderName = folderNames[i];
    
    // Check if folder exists
    var folders = currentFolder.getFoldersByName(folderName);
    if (folders.hasNext()) {
      currentFolder = folders.next();  // Reuse existing
    } else {
      currentFolder = currentFolder.createFolder(folderName);  // Create new
    }
  }
  
  return currentFolder;
}
```

**Benefits:**
- ✅ No need for folders to exist beforehand
- ✅ Automatically creates missing folders
- ✅ Reuses existing folders (no duplicates)
- ✅ Works with new ship folder structure (6 main categories only)

---

## 🆚 OLD METHOD vs NEW METHOD

### **OLD: `upload_file_to_ship_folder()`**
```python
# From gdrive_helper.py
await upload_file_to_ship_folder(
    gdrive_config, file_content, filename, ship_name, "Certificates"
)
```
**Issues:**
- ❌ Required hardcoded folder structure in Apps Script
- ❌ Failed if folders didn't exist
- ❌ Limited to specific category mappings

### **NEW: `GDriveService.upload_file()`**
```python
# From gdrive_service.py
await GDriveService.upload_file(
    file_content=file_bytes,
    filename=filename,
    content_type=content_type,
    folder_path=f"{ship_name}/Class & Flag Cert/Certificates",
    company_id=company_id
)
```
**Advantages:**
- ✅ Auto-creates folder structure
- ✅ Flexible folder path (any level of nesting)
- ✅ Works with dynamic folder structures
- ✅ Unified API across all document types

---

## 📝 MIGRATION STATUS

| Document Type | Method Used | Status |
|---------------|-------------|--------|
| Ship Certificate | `_upload_to_gdrive_with_parent()` → `upload_file_with_parent_category()` | ✅ FIXED (similar to GDriveService) |
| Audit Certificate | `GDriveService.upload_file()` | ✅ ALREADY USING |
| Survey Report | `GDriveService.upload_file()` | ✅ ALREADY USING |
| Test Report | `GDriveService.upload_file()` | ✅ ALREADY USING |
| Drawings & Manuals | `GDriveService.upload_file()` | ✅ ALREADY USING |
| Audit Report | `GDriveService.upload_file()` | ✅ ALREADY USING |
| Approval Document | `GDriveService.upload_file()` | ✅ ALREADY USING |
| Company Certificate | `GDriveService.upload_file()` | ✅ ALREADY USING |

**Conclusion:** All major document types now use auto-folder-creation logic! 🎉

---

## 🔍 APPS SCRIPT REQUIREMENTS

For `GDriveService.upload_file()` to work correctly, the Apps Script must support:

1. **Action:** `upload_file_with_folder_creation`
2. **Payload format:**
```json
{
  "action": "upload_file_with_folder_creation",
  "parent_folder_id": "...",
  "ship_name": "MV OCEAN",
  "parent_category": "Class & Flag Cert",
  "category": "Certificates",
  "filename": "cert.pdf",
  "file_content": "base64...",
  "content_type": "application/pdf"
}
```

3. **Functions required:**
   - `handleUploadFileWithFolderCreation()`
   - `createNestedFolders(parentFolder, folderNames)`

---

## 🎯 CONCLUSION

**`GDriveService.upload_file()` is used for:**
- ✅ 7 Ship-based document types (Certificates, Reports, etc.)
- ✅ 1 Company-based document type (Company Certificates)
- ✅ All summary files (`.txt` files with AI analysis)

**Total:** 8 document types actively using this method in production code.

**Key advantage:** Unified, auto-folder-creation approach across all document types! 🚀
