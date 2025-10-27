# 📊 File Size Report - Current Codebase

## 🎯 Top-level Summary

| Directory | Size | Percentage |
|-----------|------|------------|
| **Frontend** | 6.0G | ~67% (mostly node_modules) |
| **Backend** | 5.4M | ~0.6% |
| **Test Files (Root)** | ~8MB | ~0.1% |
| **Total Disk Usage** | 8.9G/9.8G | **91%** ⚠️ |

---

## 📁 Detailed Breakdown

### 1. Frontend (6.0G Total)

| Item | Size | Notes |
|------|------|-------|
| `node_modules/` | 6.0G | ✅ Normal (dependencies) |
| `src/` | 1.9M | Source code |
| `yarn.lock` | 504K | Lock file |
| `public/` | 12K | Static assets |
| Config files | ~20K | Tailwind, PostCSS, etc. |

**Frontend Source Files:**
| File | Size | Notes |
|------|------|-------|
| `src/App.js` | **1.6M** | ⚠️ VERY LARGE! Main component |
| `src/App.css` | 12K | Styles |
| `src/index.css` | 2.3K | Global styles |
| `src/index.js` | 255B | Entry point |

---

### 2. Backend (5.4M Total)

**Python Files:**
| File | Size | Notes |
|------|------|-------|
| `server.py` | **954K** | ⚠️ Main API server |
| `dual_apps_script_manager.py` | 90K | Apps Script integration |
| `server_filedb_complete_backup.py` | 53K | Backup (can delete?) |
| `server_filedb_backup.py` | 53K | Backup (can delete?) |
| `ocr_processor.py` | 39K | OCR processing |
| `google_drive_manager.py` | 28K | Drive integration |
| `test_report_valid_date_calculator.py` | 19K | Date calculations |
| `server_mongodb.py` | 19K | MongoDB alternative |
| `targeted_ocr.py` | 15K | OCR utilities |
| `migrate_to_mongodb.py` | 15K | Migration script |
| `file_database.py` | 15K | File DB |
| `mongodb_database.py` | 14K | MongoDB interface |
| `pdf_splitter.py` | 13K | PDF utilities |
| `company_google_drive_manager.py` | 11K | Company Drive |
| `document_name_normalization.py` | 9.4K | Normalization |
| `issued_by_abbreviation.py` | 5.6K | Abbreviations |
| `migrate_approved_by.py` | 3.0K | Migration |

---

### 3. 🗑️ Test Files in Root (CAN BE DELETED)

#### PDF Test Files (5.8MB)
| File | Size | Delete? |
|------|------|---------|
| `BWM-CHECK_LIST_11-23.pdf` | 1.1M | ✅ YES |
| `CU (02-19).pdf` | 988K | ✅ YES |
| `CCM_02-19.pdf` | 988K | ✅ YES |
| `test_coc_certificate.pdf` | 620K | ✅ YES |
| `Co2.pdf` | 500K | ✅ YES |
| `MINH_ANH_09_certificate.pdf` | 324K | ✅ YES |
| `2_CO_DUC_PP.pdf` | 228K | ✅ YES |
| `Chemical_Suit.pdf` | 204K | ✅ YES |
| `3_2O_THUONG_PP.pdf` | 204K | ✅ YES |
| `CG_02-19.pdf` | 144K | ✅ YES |
| `PASS_PORT_Tran_Trong_Toan.pdf` | 100K | ✅ YES |
| `test_gmdss_certificate.pdf` | 776B | ✅ YES |
| `test_passport.pdf` | 471B | ✅ YES |
| `test_poor_quality_cert.pdf` | 315B | ✅ YES |

#### Image Test Files (1.4MB)
| File | Size | Delete? |
|------|------|---------|
| `Ho_chieu_pho_thong.jpg` | 1.4M | ✅ YES |

#### Apps Script Files (40+ files, ~600KB)
| File | Size | Delete? |
|------|------|---------|
| `UPDATED_APPS_SCRIPT_SYNC.js` | 36K | ✅ YES |
| `COMPLETE_GOOGLE_APPS_SCRIPT_V4_MERGED.js` | 32K | ⚠️ KEEP (current) |
| `UPDATED_GOOGLE_APPS_SCRIPT_V3_7_FIXED.js` | 32K | ✅ YES |
| `UPDATED_APPS_SCRIPT_WITH_NEW_FEATURES.js` | 32K | ✅ YES |
| `UPDATED_MARITIME_APPS_SCRIPT_WITH_REAL_UPLOAD.js` | 28K | ✅ YES |
| ... 35+ more old versions | ~500K | ✅ YES (all old versions) |

#### Documentation Files
| File | Size | Notes |
|------|------|-------|
| `test_result.md` | 1.7M | ✅ KEEP (important) |
| `CLEANUP_REPORT.md` | ~10K | ✅ KEEP (recent) |
| `README.md` | ~4K | ✅ KEEP |

---

## 🚨 Issues Identified

### 1. **App.js is TOO LARGE (1.6MB)**
- **Current:** 1.6MB, ~33,000 lines
- **Recommended:** Split into multiple components
- **Impact:** Slow loading, hard to maintain

**Suggestions:**
- Split into: `HomePage.js`, `CertificateList.js`, `CrewList.js`, etc.
- Use component folders
- Implement lazy loading

### 2. **Test Files Not Cleaned**
- **PDF/JPG files:** ~7MB of test files in root
- **Old Apps Scripts:** ~600KB of duplicate scripts
- **Impact:** Wasting disk space

### 3. **Backend Backup Files**
- `server_filedb_backup.py` (53K)
- `server_filedb_complete_backup.py` (53K)
- **Recommendation:** Move to `/backup/` folder or delete

---

## 💡 Recommendations for Further Cleanup

### Priority 1: Delete Test Files (Immediate)
```bash
# Will free: ~7-8MB
cd /app && rm -f *.pdf *.jpg *.jpeg
```

### Priority 2: Delete Old Apps Scripts
```bash
# Will free: ~600KB
# Keep only: COMPLETE_GOOGLE_APPS_SCRIPT_V4_MERGED.js
cd /app && rm -f UPDATED_*.js FIXED_*.js CLEAN_*.js DEBUG_*.js MARITIME_*.js DOCUMENT_AI_*.js FINAL_*.js WORKING_*.js SIMPLE_*.js BASIC_*.js SUMMARY_*.js
```

### Priority 3: Refactor App.js (Long-term)
- Split into 20-30 smaller components
- Target: 50-100KB per component
- Use React.lazy() for code splitting

### Priority 4: Clean Backend Backups
```bash
# Move to backup folder or delete
cd /app/backend
mkdir -p backup
mv *backup*.py backup/
```

---

## 📊 Expected Disk Usage After Cleanup

| Action | Space Freed | New Usage |
|--------|-------------|-----------|
| Current | - | 8.9G (91%) |
| Delete test PDFs/JPGs | -7MB | 8.89G (90.7%) |
| Delete old Apps Scripts | -600KB | 8.88G (90.6%) |
| **Total Potential Savings** | **~8MB** | **~90.6%** |

---

## ✅ Files to KEEP

**Root Directory:**
- ✅ `test_result.md` (1.7M) - Testing protocol
- ✅ `CLEANUP_REPORT.md` - Cleanup history
- ✅ `README.md` - Documentation
- ✅ `COMPLETE_GOOGLE_APPS_SCRIPT_V4_MERGED.js` - Current Apps Script
- ✅ `clear_all_crew_data.py` - Utility
- ✅ `create_admin_user.py` - Utility
- ✅ `database_management.py` - Utility

**Backend:**
- ✅ All production `.py` files
- ⚠️ Consider moving backup files

**Frontend:**
- ✅ All production code
- ⚠️ Consider refactoring App.js

---

## 🎯 Summary

**Current Issues:**
1. ⚠️ App.js too large (1.6MB) - needs refactoring
2. ⚠️ ~7MB test files still in root - should delete
3. ⚠️ ~40 old Apps Script versions - should delete
4. ✅ node_modules size normal (6.0G)
5. ✅ Backend size reasonable (5.4M)

**Quick Wins:**
- Delete test PDFs/JPGs: **7MB freed**
- Delete old Apps Scripts: **600KB freed**
- Total immediate savings: **~8MB**

**Long-term Improvements:**
- Refactor App.js into smaller components
- Implement code splitting
- Use lazy loading for better performance
