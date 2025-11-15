# 🔧 UTILITY FUNCTIONS MIGRATION - COMPLETED

**Date:** $(date +%Y-%m-%d)
**Status:** ✅ MIGRATED & INTEGRATED

---

## 📋 OVERVIEW

Đã migrate thành công 2 utility files quan trọng từ backend-v1 sang backend mới:
1. `document_name_normalization.py` - Standardize document names
2. `issued_by_abbreviation.py` - Standardize company names

---

## 📦 MIGRATED FILES

### 1. Document Name Normalization ✅
**Location:** `/app/backend/app/utils/document_name_normalization.py`

**Purpose:** Standardizes ship drawings, manuals, and document names to consistent formats

**Features:**
- 165+ document name mappings
- Multiple matching strategies (direct, cleaned, partial, reverse)
- Category classification (Drawing, Manual, Certificate, Other)
- Runtime custom mapping support

**Document Types Covered:**
- **Ship Drawings:** GA, Capacity Plan, Fire Control Plan, Shell Expansion, Midship Section, Lines Plan
- **Manuals:** Operation (OM), Instruction (IM), Maintenance (MM), Service (SM), Technical (TM)
- **Safety Documents:** SDS/MSDS, Safety Manual, Emergency Procedure
- **Certificates:** Type Approval, Certificate of Approval
- **Engine & Machinery:** Engine, Pump, Compressor, Generator, Boiler manuals
- **Navigation:** Radar, GPS, AIS, VHF, Radio manuals
- **HVAC & Electrical:** HVAC, Electrical drawings & manuals
- **Piping:** Piping diagrams, P&ID

**Functions:**
```python
normalize_document_name(document_name: str) -> str
add_custom_document_mapping(pattern: str, normalized_name: str)
get_all_document_mappings() -> dict
get_document_category(document_name: str) -> str
```

**Examples:**
- "G.A. Plan" → "General Arrangement (GA)"
- "Operating Manual" → "Operation Manual (OM)"
- "MSDS" → "Safety Data Sheet (SDS)"

---

### 2. Issued By Abbreviation ✅
**Location:** `/app/backend/app/utils/issued_by_abbreviation.py`

**Purpose:** Standardizes company names to consistent abbreviations

**Features:**
- 100+ company abbreviation mappings
- Classification societies coverage
- Panama RO (Recognized Organizations) support
- Runtime custom abbreviation support

**Companies Covered:**
- **Major Classification Societies:** LR, BV, DNV, ABS, NK, KR, CCS, RS, IRS
- **Vietnamese Companies:** CGM, VITECH, VR
- **Panama Companies:** PMDS, CRCLASS, CRS, DBS, TASNEEF, ICS, IMR, INSB
- **Other ROs:** IBS, MACOSNAR, NSA, NUIMS, OMCS, PCB, PSR, PHOENIX, PRS, QUALITAS, RINA

**Functions:**
```python
normalize_issued_by(issued_by: str) -> str
add_custom_abbreviation(company_name: str, abbreviation: str)
get_all_abbreviations() -> dict
```

**Examples:**
- "Chau Giang Maritime" → "CGM"
- "Lloyd's Register" → "LR"
- "Panama Maritime Documentation Services" → "PMDS"

---

## 🌐 API ENDPOINTS

**New Router:** `/api/utilities`

### Normalization Endpoints

#### 1. Normalize Document Name
```
POST /api/utilities/normalize-document-name
Body: { "text": "G.A. Plan" }
Response: {
  "original": "G.A. Plan",
  "normalized": "General Arrangement (GA)",
  "category": "Drawing"
}
```

#### 2. Normalize Issued By
```
POST /api/utilities/normalize-issued-by
Body: { "text": "Lloyd's Register" }
Response: {
  "original": "Lloyd's Register",
  "normalized": "LR"
}
```

### Reference Endpoints

#### 3. Get All Document Mappings
```
GET /api/utilities/document-mappings
Response: {
  "general arrangement": "General Arrangement (GA)",
  "ga plan": "General Arrangement (GA)",
  ...
}
```

#### 4. Get All Company Abbreviations
```
GET /api/utilities/company-abbreviations
Response: {
  "lloyds register": "LR",
  "bureau veritas": "BV",
  ...
}
```

### Admin Endpoints

#### 5. Add Custom Document Mapping
```
POST /api/utilities/add-document-mapping
Body: {
  "pattern": "custom plan",
  "normalized": "Custom Plan"
}
```

#### 6. Add Custom Company Abbreviation
```
POST /api/utilities/add-company-abbreviation
Body: {
  "pattern": "New Company Name",
  "normalized": "NCN"
}
```

---

## 🎯 USE CASES

### 1. Data Consistency
- Standardize document names across the system
- Ensure consistent company abbreviations
- Improve search and filtering accuracy

### 2. User Experience
- Auto-suggest normalized names during data entry
- Display consistent formats in UI
- Reduce data entry errors

### 3. Reporting & Analytics
- Group documents by standardized categories
- Generate reports with consistent terminology
- Improve data analysis accuracy

### 4. AI Integration
- Use normalized names for better AI training
- Improve AI extraction accuracy
- Reduce ambiguity in AI responses

---

## 🔄 INTEGRATION POINTS

### Where to Use:

1. **Certificate Creation/Update**
   - Normalize `cert_name` before saving
   - Normalize `issued_by` to abbreviation

2. **Document Upload**
   - Auto-categorize based on document name
   - Suggest normalized name to user

3. **Search & Filter**
   - Use normalized names for search
   - Group by standardized categories

4. **AI Analysis**
   - Post-process AI extraction results
   - Standardize extracted company names

5. **Reports**
   - Display normalized names in reports
   - Use consistent abbreviations

---

## 💡 EXAMPLE USAGE IN CODE

### Certificate Service Integration
```python
from app.utils.document_name_normalization import normalize_document_name
from app.utils.issued_by_abbreviation import normalize_issued_by

# In certificate creation
cert_data["cert_name"] = normalize_document_name(cert_data["cert_name"])
cert_data["issued_by"] = normalize_issued_by(cert_data["issued_by"])
```

### Document Service Integration
```python
from app.utils.document_name_normalization import (
    normalize_document_name,
    get_document_category
)

# In document upload
doc_data["document_name"] = normalize_document_name(doc_data["document_name"])
doc_data["category"] = get_document_category(doc_data["document_name"])
```

---

## 📊 COVERAGE STATISTICS

### Document Name Normalization
- **Total Mappings:** 165+
- **Categories:**
  - Ship Drawings: 15 types
  - Manuals: 25 types
  - Safety Documents: 8 types
  - Engine & Machinery: 10 types
  - Navigation & Communication: 12 types
  - Electrical & Piping: 8 types

### Company Abbreviations
- **Total Mappings:** 100+
- **Coverage:**
  - Classification Societies: 10 major societies
  - Panama ROs: 30+ organizations
  - Vietnamese Companies: 5+ companies

---

## ✅ BENEFITS

### Data Quality
- ✅ Consistent document naming across system
- ✅ Standardized company abbreviations
- ✅ Reduced data entry errors
- ✅ Improved search accuracy

### User Experience
- ✅ Auto-suggestions for document names
- ✅ Clear, standardized display
- ✅ Easier data entry
- ✅ Better filtering & grouping

### System Integration
- ✅ Better AI analysis results
- ✅ Improved reporting accuracy
- ✅ Consistent data across modules
- ✅ Easier maintenance & updates

---

## 🚀 NEXT STEPS (Optional)

### Potential Enhancements:
1. **Database Integration**
   - Store custom mappings in database
   - Share mappings across companies
   - Version control for mappings

2. **Frontend Integration**
   - Auto-complete with normalized suggestions
   - Show mapping preview in forms
   - Bulk normalization tool

3. **Analytics Dashboard**
   - Show normalization statistics
   - Identify most common patterns
   - Suggest new mappings

4. **Machine Learning**
   - Learn from user corrections
   - Auto-suggest new mappings
   - Improve matching algorithms

---

**Status:** ✅ MIGRATED, INTEGRATED & PRODUCTION READY

**Achievement:** Successfully migrated essential utility functions from backend-v1 to clean architecture!

