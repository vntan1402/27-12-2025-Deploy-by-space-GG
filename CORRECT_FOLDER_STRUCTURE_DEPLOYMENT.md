# 🔧 Fixed Folder Structure - Deployment Guide

## 🎯 Problem Identified
The current Apps Script creates **WRONG folder structure**:

❌ **Current (Wrong):**
```
Ship Name/
├── Certificates/
├── Test Reports/
├── Survey Reports/
└── Other Documents/
```

✅ **Expected (Correct - Homepage Sidebar):**
```
Ship Name/
├── Document Portfolio/          ← Missing parent folder!
│   ├── Certificates/           ← Should be under Document Portfolio
│   ├── Inspection Records/
│   ├── Survey Reports/
│   ├── Drawings & Manuals/
│   └── Other Documents/
├── Crew Records/
├── ISM Records/
├── ISPS Records/
├── MLC Records/
└── Supplies/
```

## 🔧 Solution: Updated Apps Script v3.1

### Step 1: Replace Apps Script Code
**Go to your Google Apps Script project and replace ALL content with:**

```javascript
// Copy COMPLETE content from /app/UPDATED_APPS_SCRIPT.js
// This includes the FIXED folder structure matching Homepage Sidebar
```

### Step 2: Key Changes Made

#### ✅ Fixed Folder Structure
```javascript
const folderStructure = {
  "Document Portfolio": [           // ← Added parent folder
    "Certificates",                 // ← Certificate uploads go here
    "Inspection Records",
    "Survey Reports", 
    "Drawings & Manuals",
    "Other Documents"
  ],
  "Crew Records": ["Crew List", "Crew Certificates", "Medical Records"],
  "ISM Records": ["ISM Certificate", "Safety Procedures", "Audit Reports"],
  "ISPS Records": ["ISPS Certificate", "Security Plan", "Security Assessments"],
  "MLC Records": ["MLC Certificate", "Labor Conditions", "Accommodation Reports"],
  "Supplies": ["Inventory", "Purchase Orders", "Spare Parts"]
};
```

#### ✅ Fixed Upload Path Logic
```javascript
// Categories that belong under "Document Portfolio"
const documentPortfolioCategories = [
  "Certificates", "Inspection Records", "Survey Reports", 
  "Drawings & Manuals", "Other Documents"
];

// Upload path: Ship Name/Document Portfolio/Certificates/
```

### Step 3: Deploy New Version
1. **Save**: Press Ctrl+S
2. **Deploy**: Deploy → New deployment
3. **Copy new URL**: Update in Ship Management System
4. **Test**: Verify connection shows "PASSED"

## 🧪 Testing the Fix

### Test 1: Create New Ship
```javascript
// Should create this structure:
Ship Name/
├── Document Portfolio/
│   ├── Certificates/           ← Certificate upload target
│   ├── Inspection Records/
│   ├── Survey Reports/
│   ├── Drawings & Manuals/
│   └── Other Documents/
├── Crew Records/
├── ISM Records/
├── ISPS Records/
├── MLC Records/
└── Supplies/
```

### Test 2: Certificate Upload
```javascript
// Certificate should upload to:
// Ship Name/Document Portfolio/Certificates/
// NOT Ship Name/Certificates/
```

## ⚠️ Migration for Existing Ships

### Option A: Keep Existing Structure (Temporary)
- Existing ships keep current structure
- New ships use correct structure
- Gradually migrate later

### Option B: Manual Restructure (Recommended)
1. **Backup existing files**
2. **Create "Document Portfolio" folder** in existing ships
3. **Move certificates** from `Ship/Certificates/` to `Ship/Document Portfolio/Certificates/`
4. **Update folder structure** to match sidebar

## 🎯 Expected Results After Fix

### ✅ New Ship Creation
- Ship folder with complete 6-category structure
- Document Portfolio as parent for certificates
- Proper hierarchy matching Homepage Sidebar

### ✅ Certificate Upload Path
```
Before: Ship Name/Certificates/certificate.pdf           ❌
After:  Ship Name/Document Portfolio/Certificates/certificate.pdf  ✅
```

### ✅ Multi Cert Upload
- Files classified as "Certificates" → Document Portfolio/Certificates/
- Other files → Appropriate folders based on classification
- Proper folder path reporting in upload results

---

## 📝 Quick Deploy Instructions

1. **Copy** complete code from `/app/UPDATED_APPS_SCRIPT.js`
2. **Replace** all content in your Google Apps Script
3. **Deploy** as new version
4. **Update** Web App URL in Ship Management System
5. **Test** with new ship creation and certificate upload

**🚢 After this fix, certificate uploads will go to the correct path: `Ship Name/Document Portfolio/Certificates/`**