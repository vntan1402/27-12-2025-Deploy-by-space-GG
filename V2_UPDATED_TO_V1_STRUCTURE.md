# ✅ BACKEND V2 ĐÃ CẬP NHẬT THEO STRUCTURE V1

## 🎯 THAY ĐỔI

Backend V2 đã được cập nhật để sử dụng **CÙNG folder structure** với Backend V1 để đảm bảo tính nhất quán.

---

## 📂 STRUCTURE MỚI (V2 = V1)

### **Case 1: Crew có tàu (ship_name != "-")**

**Path:**
```
[Company Root]/[Ship Name]/Crew Records/Crew List/
├── [passport_filename].pdf
└── [passport_filename]_Summary.txt
```

**Example:**
```
Company Root/
└── BROTHER 36/
    └── Crew Records/
        └── Crew List/
            ├── nguyen_van_a_passport.pdf
            └── nguyen_van_a_passport_Summary.txt
```

---

### **Case 2: Crew Standby (ship_name = "-")**

**Path:**
```
[Company Root]/COMPANY DOCUMENT/Standby Crew/
├── [passport_filename].pdf
└── [passport_filename]_Summary.txt
```

**Example:**
```
Company Root/
└── COMPANY DOCUMENT/
    └── Standby Crew/
        ├── le_van_c_passport.pdf
        └── le_van_c_passport_Summary.txt
```

---

## 🔧 CODE CHANGES

### File Modified: `/app/backend/app/services/google_drive_service.py`

**BEFORE (V2 Original):**
```python
# Determine folder path
if ship_name and ship_name != '-':
    folder_path = f"{ship_name}/Passport"
    summary_folder_path = f"{ship_name}/Passport/SUMMARY"
else:
    folder_path = "Standby Crew/Passport"
    summary_folder_path = "Standby Crew/Passport/SUMMARY"

# Summary filename
summary_filename = f"{crew_name}_{passport_number}_summary.txt"

# Upload to different folders
passport_file_id = await drive_helper.upload_file(..., folder_path=folder_path)
summary_file_id = await drive_helper.upload_file(..., folder_path=summary_folder_path)
```

**AFTER (V2 Updated = V1):**
```python
# ✅ V1 STRUCTURE: Determine folder path matching Backend V1
if ship_name and ship_name != '-':
    # Normal crew: {Ship Name}/Crew Records/Crew List/
    folder_path = f"{ship_name}/Crew Records/Crew List"
else:
    # Standby crew: COMPANY DOCUMENT/Standby Crew/
    folder_path = "COMPANY DOCUMENT/Standby Crew"

# ✅ V1 STRUCTURE: Summary filename matching V1
base_name = filename.rsplit('.', 1)[0]  # Remove extension
summary_filename = f"{base_name}_Summary.txt"

# Upload to SAME folder (V1 behavior)
passport_file_id = await drive_helper.upload_file(..., folder_path=folder_path)
summary_file_id = await drive_helper.upload_file(..., folder_path=folder_path)  # Same folder
```

---

## 📊 COMPARISON TABLE

| Feature | V2 Before | V2 After (= V1) |
|---------|-----------|-----------------|
| **Path (Normal)** | `{Ship}/Passport/` | `{Ship}/Crew Records/Crew List/` ✅ |
| **Path (Standby)** | `Standby Crew/Passport/` | `COMPANY DOCUMENT/Standby Crew/` ✅ |
| **Nesting Levels (Normal)** | 2 levels | 3 levels ✅ |
| **Summary Location** | Separate `SUMMARY/` subfolder | Same folder as passport ✅ |
| **Summary Naming** | `{NAME}_{PASSPORT}_summary.txt` | `{filename}_Summary.txt` ✅ |

**Result:** ✅ **100% MATCH với Backend V1**

---

## 🎯 KEY CHANGES SUMMARY

### 1. Folder Path Changes

**Normal Crew:**
- ❌ OLD: `BROTHER 36/Passport/`
- ✅ NEW: `BROTHER 36/Crew Records/Crew List/`

**Standby Crew:**
- ❌ OLD: `Standby Crew/Passport/`
- ✅ NEW: `COMPANY DOCUMENT/Standby Crew/`

---

### 2. Summary File Location

**Before:**
```
BROTHER 36/
└── Passport/
    ├── file.pdf
    └── SUMMARY/
        └── NGUYEN_VAN_A_B1234567_summary.txt
```

**After:**
```
BROTHER 36/
└── Crew Records/
    └── Crew List/
        ├── file.pdf
        └── file_Summary.txt  ← Same folder
```

---

### 3. Summary File Naming

**Before:**
```python
summary_filename = f"{crew_name}_{passport_number}_summary.txt"
# Example: NGUYEN_VAN_A_B1234567_summary.txt
```

**After:**
```python
base_name = filename.rsplit('.', 1)[0]
summary_filename = f"{base_name}_Summary.txt"
# Example: nguyen_van_a_passport_Summary.txt
```

---

## ✅ BENEFITS OF THIS CHANGE

1. **✅ Consistency:** V1 và V2 giờ sử dụng cùng structure
2. **✅ No Migration:** Không cần migrate existing V1 files
3. **✅ Backward Compatible:** Files uploaded từ V1 và V2 ở cùng location
4. **✅ Unified System:** Toàn bộ hệ thống sử dụng 1 folder structure duy nhất

---

## 🔍 VISUAL COMPARISON

### Before Update (V2 Original):

```
Company Root/
├── BROTHER 36/
│   └── Passport/
│       ├── file1.pdf
│       └── SUMMARY/
│           └── NAME_PASSPORT_summary.txt
│
└── Standby Crew/
    └── Passport/
        ├── file2.pdf
        └── SUMMARY/
            └── NAME_PASSPORT_summary.txt
```

### After Update (V2 = V1):

```
Company Root/
├── BROTHER 36/
│   └── Crew Records/
│       └── Crew List/
│           ├── file1.pdf
│           └── file1_Summary.txt
│
└── COMPANY DOCUMENT/
    └── Standby Crew/
        ├── file2.pdf
        └── file2_Summary.txt
```

---

## 🚀 DEPLOYMENT STATUS

- ✅ Code updated in `/app/backend/app/services/google_drive_service.py`
- ✅ Backend restarted successfully
- ✅ No errors in logs
- ✅ Service running (PID 1474)

---

## 📋 TESTING CHECKLIST

To verify the changes work correctly:

- [ ] Upload passport for normal crew → Check path: `{Ship}/Crew Records/Crew List/`
- [ ] Upload passport for standby crew → Check path: `COMPANY DOCUMENT/Standby Crew/`
- [ ] Verify summary file in same folder as passport
- [ ] Verify summary filename format: `{original}_Summary.txt`
- [ ] Test with existing V1 data (should be compatible)
- [ ] Delete crew → Verify both files deleted

---

## 🔗 RELATED DOCUMENTS

- **Original V1 vs V2 Comparison:** `/app/CREW_PASSPORT_UPLOAD_PATH_V1_VS_V2.md`
- **V2 Structure Guide (OLD):** `/app/CREW_PASSPORT_FILE_UPLOAD_STRUCTURE.md` ⚠️ OUTDATED
- **Migration Plan:** `/app/V1_TO_V2_MIGRATION_PLAN.md`

---

## 📝 NOTES

**Important:** Document `/app/CREW_PASSPORT_FILE_UPLOAD_STRUCTURE.md` is now **OUTDATED** because it describes the old V2 structure. The current V2 now follows V1 structure as documented in this file.

For current structure reference, see:
- This document: `/app/V2_UPDATED_TO_V1_STRUCTURE.md`
- Or original V1 documentation

---

**Document Created:** 2025-01-27
**Last Updated:** 2025-01-27  
**Version:** 1.0
**Status:** ✅ ACTIVE - V2 now matches V1 structure
