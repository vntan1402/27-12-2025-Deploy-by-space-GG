# 📂 SO SÁNH UPLOAD PATH: BACKEND V1 VS V2

## 🎯 TỔNG QUAN

Document này so sánh folder structure khi upload passport files giữa Backend V1 và V2.

---

## 🔴 BACKEND V1 - FOLDER STRUCTURE

### Case 1: Crew có tàu (ship_name != "-")

**Path Structure:**
```
[Company Root]/
└── [Ship Name]/
    └── Crew Records/
        └── Crew List/
            ├── [passport_filename].pdf          ← File gốc
            └── [passport_filename]_Summary.txt  ← Summary (cùng folder)
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

**Code Logic V1:**
```python
# In dual_apps_script_manager.py (lines 1614-1626)

target_ship = ship_name
parent_category = "Crew Records"  # First level folder
target_category = "Crew List"     # Second level folder

# Result path: {ship_name}/Crew Records/Crew List/
```

---

### Case 2: Crew Standby (ship_name = "-")

**Path Structure:**
```
[Company Root]/
└── COMPANY DOCUMENT/
    └── Standby Crew/
        ├── [passport_filename].pdf          ← File gốc
        └── [passport_filename]_Summary.txt  ← Summary (cùng folder)
```

**Example:**
```
Company Root/
└── COMPANY DOCUMENT/
    └── Standby Crew/
        ├── le_van_c_passport.pdf
        └── le_van_c_passport_Summary.txt
```

**Code Logic V1:**
```python
# In dual_apps_script_manager.py (lines 1617-1620)

if ship_name == "-":
    target_ship = "COMPANY DOCUMENT"
    parent_category = None
    target_category = "Standby Crew"

# Result path: COMPANY DOCUMENT/Standby Crew/
```

---

## 🟢 BACKEND V2 - FOLDER STRUCTURE (CURRENT)

### Case 1: Crew có tàu (ship_name != "-")

**Path Structure:**
```
[Company Root]/
└── [Ship Name]/
    └── Passport/
        ├── [passport_filename].pdf           ← File gốc
        └── SUMMARY/
            └── [crew_name]_[passport]_summary.txt  ← Summary (subfolder)
```

**Example:**
```
Company Root/
└── BROTHER 36/
    └── Passport/
        ├── nguyen_van_a_passport.pdf
        └── SUMMARY/
            └── NGUYEN_VAN_A_B1234567_summary.txt
```

**Code Logic V2:**
```python
# In google_drive_service.py (lines 71-77)

if ship_name and ship_name != '-':
    folder_path = f"{ship_name}/Passport"
    summary_folder_path = f"{ship_name}/Passport/SUMMARY"

# Result path:
# - Passport: {ship_name}/Passport/
# - Summary: {ship_name}/Passport/SUMMARY/
```

---

### Case 2: Crew Standby (ship_name = "-")

**Path Structure:**
```
[Company Root]/
└── Standby Crew/
    └── Passport/
        ├── [passport_filename].pdf           ← File gốc
        └── SUMMARY/
            └── [crew_name]_[passport]_summary.txt  ← Summary (subfolder)
```

**Example:**
```
Company Root/
└── Standby Crew/
    └── Passport/
        ├── le_van_c_passport.pdf
        └── SUMMARY/
            └── LE_VAN_C_B3456789_summary.txt
```

**Code Logic V2:**
```python
# In google_drive_service.py (lines 71-77)

else:
    folder_path = "Standby Crew/Passport"
    summary_folder_path = "Standby Crew/Passport/SUMMARY"

# Result path:
# - Passport: Standby Crew/Passport/
# - Summary: Standby Crew/Passport/SUMMARY/
```

---

## 📊 SO SÁNH CHI TIẾT

### 1. Crew có tàu (Normal)

| Aspect | V1 | V2 |
|--------|----|----|
| **Ship Folder** | `{ship_name}` | `{ship_name}` |
| **Main Category** | `Crew Records` | `Passport` |
| **Sub Category** | `Crew List` | N/A |
| **Passport Path** | `{ship}/Crew Records/Crew List/` | `{ship}/Passport/` |
| **Summary Path** | `{ship}/Crew Records/Crew List/` | `{ship}/Passport/SUMMARY/` |
| **Summary in Subfolder?** | ❌ No (same folder) | ✅ Yes (SUMMARY subfolder) |

**Visual Comparison:**
```
V1: BROTHER 36/Crew Records/Crew List/file.pdf
V1: BROTHER 36/Crew Records/Crew List/file_Summary.txt

V2: BROTHER 36/Passport/file.pdf
V2: BROTHER 36/Passport/SUMMARY/NAME_PASSPORT_summary.txt
```

---

### 2. Crew Standby

| Aspect | V1 | V2 |
|--------|----|----|
| **Root Folder** | `COMPANY DOCUMENT` | `Standby Crew` |
| **Main Category** | `Standby Crew` | `Passport` |
| **Passport Path** | `COMPANY DOCUMENT/Standby Crew/` | `Standby Crew/Passport/` |
| **Summary Path** | `COMPANY DOCUMENT/Standby Crew/` | `Standby Crew/Passport/SUMMARY/` |
| **Summary in Subfolder?** | ❌ No (same folder) | ✅ Yes (SUMMARY subfolder) |

**Visual Comparison:**
```
V1: COMPANY DOCUMENT/Standby Crew/file.pdf
V1: COMPANY DOCUMENT/Standby Crew/file_Summary.txt

V2: Standby Crew/Passport/file.pdf
V2: Standby Crew/Passport/SUMMARY/NAME_PASSPORT_summary.txt
```

---

## 📝 FILE NAMING DIFFERENCES

### Summary File Naming

**V1 Format:**
```
{original_filename}_Summary.txt
```
**Examples:**
- `nguyen_van_a_passport_Summary.txt`
- `scan_20231215_Summary.txt`
- `passport_scan_Summary.txt`

**V2 Format:**
```
{CREW_NAME}_{PASSPORT_NO}_summary.txt
```
**Examples:**
- `NGUYEN_VAN_A_B1234567_summary.txt`
- `TRAN_THI_B_B2345678_summary.txt`
- `LE_VAN_C_B3456789_summary.txt`

---

## 🔄 NESTED STRUCTURE COMPARISON

### V1 Nested Structure (3 levels for normal crew)

```
Company Root/
├── BROTHER 36/                    Level 1: Ship
│   ├── Crew Records/              Level 2: Parent Category
│   │   └── Crew List/             Level 3: Category
│   │       ├── crew1.pdf
│   │       └── crew1_Summary.txt
│   └── Class & Flag Cert/         Level 2: Parent Category
│       └── ...
│
└── COMPANY DOCUMENT/              Level 1: Company-wide
    └── Standby Crew/              Level 2: Category
        ├── standby1.pdf
        └── standby1_Summary.txt
```

**Code Implementation V1:**
```python
passport_payload = {
    'action': 'upload_file_with_folder_creation',
    'parent_folder_id': self.parent_folder_id,
    'ship_name': target_ship,              # Level 1
    'parent_category': parent_category,    # Level 2 (if exists)
    'category': target_category,           # Level 3 or 2
    'filename': passport_filename,
    'file_content': base64_content,
    'content_type': content_type
}
```

---

### V2 Flat Structure (2 levels for normal crew)

```
Company Root/
├── BROTHER 36/                    Level 1: Ship
│   ├── Passport/                  Level 2: Category
│   │   ├── crew1.pdf
│   │   └── SUMMARY/               Level 3: Summary subfolder
│   │       └── NGUYEN_VAN_A_B1234567_summary.txt
│   └── Certificates/              Level 2: Category
│       └── ...
│
└── Standby Crew/                  Level 1: Standby
    └── Passport/                  Level 2: Category
        ├── standby1.pdf
        └── SUMMARY/               Level 3: Summary subfolder
            └── LE_VAN_C_B3456789_summary.txt
```

**Code Implementation V2:**
```python
# Simpler, flat structure
if ship_name and ship_name != '-':
    folder_path = f"{ship_name}/Passport"
    summary_folder_path = f"{ship_name}/Passport/SUMMARY"
else:
    folder_path = "Standby Crew/Passport"
    summary_folder_path = "Standby Crew/Passport/SUMMARY"
```

---

## 🎯 KEY DIFFERENCES SUMMARY

| Feature | V1 | V2 |
|---------|----|----|
| **Nested Levels (Normal)** | 3 levels | 2 levels |
| **Nested Levels (Standby)** | 2 levels | 2 levels |
| **Parent Category (Normal)** | `Crew Records` | N/A (flat) |
| **Category (Normal)** | `Crew List` | `Passport` |
| **Standby Root** | `COMPANY DOCUMENT` | `Standby Crew` |
| **Summary Subfolder** | ❌ Same folder | ✅ `SUMMARY/` subfolder |
| **Summary Naming** | `{filename}_Summary.txt` | `{NAME}_{PASSPORT}_summary.txt` |
| **Cleaner Structure** | ❌ Deeper nesting | ✅ Flatter, cleaner |

---

## 💡 PROS & CONS

### V1 Structure

**Pros:**
- ✅ Organized by "Crew Records" → "Crew List" hierarchy
- ✅ Clear separation of crew-related documents
- ✅ Consistent with other document types (Class & Flag Cert, etc.)

**Cons:**
- ❌ Deeper nesting (3 levels for normal crew)
- ❌ Summary files mixed with passport files
- ❌ Summary filename tied to original filename (not standardized)
- ❌ Extra folder level ("Crew Records") may be unnecessary

---

### V2 Structure

**Pros:**
- ✅ Flatter structure (2 levels instead of 3)
- ✅ Summary files in separate subfolder (cleaner)
- ✅ Standardized summary naming (`{NAME}_{PASSPORT}_summary.txt`)
- ✅ More direct: `{Ship}/Passport/` vs `{Ship}/Crew Records/Crew List/`
- ✅ Easier to navigate and manage

**Cons:**
- ❌ Different structure from V1 (migration needed)
- ❌ Less hierarchical organization
- ⚠️ May conflict with existing V1 files

---

## 🔄 MIGRATION CONSIDERATIONS

### If migrating from V1 to V2:

**Option 1: Move files to new structure**
```
OLD: BROTHER 36/Crew Records/Crew List/file.pdf
NEW: BROTHER 36/Passport/file.pdf

OLD: BROTHER 36/Crew Records/Crew List/file_Summary.txt
NEW: BROTHER 36/Passport/SUMMARY/NAME_PASSPORT_summary.txt
```

**Option 2: Keep both structures (dual write)**
- Upload to both V1 and V2 paths
- Maintain backward compatibility
- Gradually deprecate V1

**Option 3: Use V1 structure in V2**
- Modify V2 code to use V1 paths
- No migration needed
- Keeps consistency

---

## 🚀 RECOMMENDATION

**For New Implementations:**
- ✅ Use V2 structure (cleaner, flatter)

**For Existing Systems:**
- If V1 data exists: Consider Option 3 (use V1 structure in V2)
- If starting fresh: Use V2 structure
- If migrating: Implement gradual migration with dual write

---

## 📋 CODE REFERENCES

**V1 Implementation:**
- `/app/backend-v1/dual_apps_script_manager.py` lines 1580-1698
- `/app/backend-v1/server.py` lines 22104-22198

**V2 Implementation:**
- `/app/backend/app/services/google_drive_service.py` lines 20-130
- `/app/backend/app/utils/google_drive_helper.py`
- `/app/backend/app/api/v1/crew.py` lines 140-267

---

**Document Created:** 2025-01-27
**Last Updated:** 2025-01-27
**Version:** 1.0
