# 📋 AUDIT CERTIFICATE MIGRATION - EXECUTIVE SUMMARY

## 🎯 OVERVIEW

**Objective**: Migrate module "Add Audit Certificate" từ Backend V1 sang Backend V2

**Key Updates**:
1. ✅ Port full AI analysis infrastructure
2. ✅ Implement 3 new endpoints (analyze-file, multi-upload, create-with-file-override)
3. ✅ **Fix Google Drive path**: `ISM-ISPS-MLC` → `ISM - ISPS - MLC` (add spaces)
4. ✅ **⭐ NEW: Expand support for CICA (CREW ACCOMMODATION) certificates**

---

## 📊 SCOPE

### Backend V1 → Backend V2 Migration

**Files to Create (2):**
1. `/app/backend/app/utils/audit_certificate_ai.py`
2. `/app/backend/app/services/audit_certificate_analyze_service.py`

**Files to Update (3):**
1. `/app/backend/app/api/v1/audit_certificates.py` - Add 3 endpoints
2. `/app/backend/app/services/audit_certificate_service.py` - Enhance duplicate check
3. `/app/backend/app/services/gdrive_service.py` - Fix path spacing

**Frontend Updates (3):**
1. `AuditCertificateFilters.jsx` - Add CICA filter option
2. `AuditCertificateTable.jsx` - Add CICA badge (orange)
3. `AddAuditCertificateModal.jsx` - Update guidelines

---

## ⭐ MAJOR CHANGE: CICA EXPANSION

### What is CICA?

**CICA** = Certificate of Inspection for Crew Accommodation
- Crew accommodation compliance certificates
- Now accepted alongside ISM/ISPS/MLC

### Changes Made:

#### 1. Backend Dictionary (EXPANDED):
```python
AUDIT_CERTIFICATE_CATEGORIES = {
    "ism": [...],
    "isps": [...],
    "mlc": [...],
    "cica": [  # ⭐ NEW
        "CERTIFICATE OF INSPECTION",
        "CREW ACCOMMODATION CERTIFICATE",
        "STATEMENT OF COMPLIANCE OF CREW ACCOMMODATION",
        "CERTIFICATE OF INSPECTION / STATEMENT OF COMPLIANCE OF CREW ACCOMMODATION",
        "CREW ACCOMMODATION INSPECTION",
        "CICA",
    ]
}
```

#### 2. Validation Logic (UPDATED):
- Function renamed: `check_category_ism_isps_mlc()` → `check_category_ism_isps_mlc_cica()`
- Special detection for "CREW ACCOMMODATION" keyword (highest priority)
- Error message: "Certificate does not belong to ISM/ISPS/MLC/CICA categories"

#### 3. AI Prompt (ENHANCED):
- Added CICA detection rules
- Priority: "CREW ACCOMMODATION" → CICA
- Support for CICA abbreviations

#### 4. Frontend (3 Changes):
- **Filter**: Added CICA option in type dropdown
- **Badge**: Orange color for CICA (`bg-orange-100 text-orange-800`)
- **Guidelines**: Mention CICA support

#### 5. Google Drive Path (UNCHANGED):
```
{ShipName}/ISM - ISPS - MLC/Audit Certificates/{filename}
```
**Note**: CICA certificates stored in same folder (no separate path needed)

---

## 📝 KEY ENDPOINTS

### 1. POST /api/audit-certificates/analyze-file
**Purpose**: Analyze single file with AI (no DB create)

**Flow**:
```
User uploads file → Validate → Document AI → System AI → Return extracted fields
```

**Use Case**: Single file upload → Auto-fill form → User reviews → Saves manually

---

### 2. POST /api/audit-certificates/multi-upload
**Purpose**: Batch upload with auto-create DB records

**Flow**:
```
User uploads multiple files
  ↓
For each file:
  1. Validate file (size, type)
  2. AI analysis
  3. Quality check
  4. Category check (ISM/ISPS/MLC/CICA) ⭐
  5. IMO/Ship validation
  6. Duplicate check
  7. Upload to GDrive
  8. Create DB record
  ↓
Return batch results
```

**Validation Rules**:
- ❌ IMO mismatch → **HARD REJECT**
- ⚠️ Ship name mismatch → **SOFT WARNING** (add note)
- ❌ Non-ISM/ISPS/MLC/CICA → **REJECT**
- 🔁 Duplicate → **PENDING USER CHOICE**
- 📊 Low AI quality → **REQUEST MANUAL INPUT**

---

### 3. POST /api/audit-certificates/create-with-file-override
**Purpose**: Create with file, bypass validation warnings

**Flow**:
```
User clicks "Continue" on validation warning
  ↓
Upload file + cert_data (JSON)
  ↓
Upload to GDrive → Create DB record (with validation note)
```

**Use Case**: User approves ship name mismatch → Save with note "Chỉ để tham khảo"

---

## 🔧 TECHNICAL STACK

### AI Services:
1. **Google Document AI**: PDF/Image OCR & text extraction
2. **Emergent LLM / Gemini**: Field extraction from text
3. **System AI Config**: Stored in MongoDB `ai_config` collection

### Storage:
1. **MongoDB**: Certificate records
2. **Google Drive**: File storage via Apps Script API

### Validation Layers:
1. File validation (size, type, magic bytes)
2. AI quality check (confidence, critical fields)
3. Category validation (ISM/ISPS/MLC/CICA) ⭐
4. Ship info validation (IMO, ship name)
5. Duplicate detection (cert_name + cert_no)

---

## 📊 SUPPORTED CERTIFICATE CATEGORIES (4 TYPES)

### 1. ISM - International Safety Management
- Safety Management Certificate (SMC)
- Document of Compliance (DOC)
- **Badge Color**: Blue

### 2. ISPS - Ship and Port Facility Security
- International Ship Security Certificate (ISSC)
- Ship Security Plan (SSP)
- **Badge Color**: Green

### 3. MLC - Maritime Labour Convention
- Maritime Labour Certificate
- Declaration of Maritime Labour Compliance (DMLC)
- **Badge Color**: Purple

### 4. ⭐ CICA - Crew Accommodation (NEW)
- Certificate of Inspection
- Crew Accommodation Certificate
- Statement of Compliance
- **Badge Color**: Orange
- **Detection**: "CREW ACCOMMODATION" keyword

---

## 🧪 TESTING STRATEGY

### Unit Tests (Backend):
- AI extraction accuracy
- Category validation (4 types including CICA)
- Quality checks
- Ship validation
- Duplicate detection

### Integration Tests:
- Single file analysis
- Multi-file upload (mixed ISM/ISPS/MLC/CICA)
- Validation workflows
- GDrive integration
- Error handling

### Manual Tests:
- Upload 1 CICA certificate → Check CICA badge
- Upload mixed types (4 files) → Check all categories
- Filter by CICA → Check results
- Upload duplicate CICA → Check modal
- Upload CICA with IMO mismatch → Check rejection

---

## ⏱️ TIMELINE

### Day 1-2: Backend Development (7 hours)
- Create `audit_certificate_ai.py` (2 hours)
- Create `audit_certificate_analyze_service.py` (3 hours)
- Add 3 API endpoints (2 hours)
- **CICA expansion**: +1 hour

### Day 3: Frontend Updates (3 hours)
- Update filters (add CICA)
- Update table badges (add orange)
- Update upload guidelines
- **CICA UI**: +1 hour

### Day 4: Testing (4 hours)
- Unit tests
- Integration tests
- **CICA-specific tests**: +1 hour
- Manual testing

### Day 5-6: Deployment & Monitoring
- Staging deployment
- Production deployment
- Monitoring & bug fixes

**Total**: 6 days (1 developer)

---

## 🎯 SUCCESS METRICS

### Performance:
- ⏱️ Single file analysis: < 10 seconds
- ⏱️ Multi-upload (3 files): < 30 seconds
- 📊 AI extraction accuracy: > 90%
- 🎯 CICA detection accuracy: > 95%

### Quality:
- 🐛 Zero critical bugs
- ✅ 100% test coverage for core logic
- 📝 Full API documentation
- 👥 User satisfaction: Positive

---

## 📚 DOCUMENTATION LINKS

**Detailed Plans**:
1. `/app/AUDIT_CERTIFICATE_MIGRATION_PLAN.md` - Full migration plan
2. `/app/AUDIT_CERTIFICATE_CICA_EXPANSION.md` - CICA expansion details
3. `/app/AUDIT_CERTIFICATE_CICA_CLARIFICATION.md` - CICA decision rationale
4. `/app/AUDIT_CERTIFICATE_FLOW_ANALYSIS.md` - Current flow analysis

**Code Architecture**:
```
/app/backend/app/
├── utils/
│   └── audit_certificate_ai.py              ⭐ NEW
├── services/
│   ├── audit_certificate_analyze_service.py ⭐ NEW
│   ├── audit_certificate_service.py         📝 UPDATE
│   └── gdrive_service.py                    📝 UPDATE (path fix)
└── api/v1/
    └── audit_certificates.py                📝 UPDATE (3 endpoints)

/app/frontend/src/components/AuditCertificate/
├── AuditCertificateFilters.jsx              📝 UPDATE (CICA filter)
├── AuditCertificateTable.jsx                📝 UPDATE (CICA badge)
└── AddAuditCertificateModal.jsx             📝 UPDATE (guidelines)
```

---

## ✅ FINAL CHECKLIST

### Backend:
- [ ] Create `audit_certificate_ai.py`
- [ ] Create `audit_certificate_analyze_service.py`
- [ ] Add `POST /analyze-file` endpoint
- [ ] Add `POST /multi-upload` endpoint
- [ ] Add `POST /create-with-file-override` endpoint
- [ ] Update `check_duplicate()` in service
- [ ] Fix GDrive path spacing (ISM - ISPS - MLC)
- [ ] Add CICA to categories dictionary ⭐
- [ ] Update validation to accept CICA ⭐
- [ ] Update AI prompt for CICA ⭐

### Frontend:
- [ ] Add CICA filter option ⭐
- [ ] Add CICA badge (orange) ⭐
- [ ] Update upload guidelines (mention CICA) ⭐
- [ ] Test filter by CICA
- [ ] Test mixed upload (ISM + ISPS + MLC + CICA)

### Testing:
- [ ] Unit tests (with CICA cases)
- [ ] Integration tests
- [ ] Manual testing
- [ ] CICA-specific test cases ⭐
- [ ] Performance testing

### Documentation:
- [ ] Update API docs (Swagger)
- [ ] Update developer guide
- [ ] Update user guide
- [ ] Release notes

---

## 🚨 CRITICAL NOTES

### 1. CICA Integration
- ⭐ CICA now supported (4th category)
- Keyword: "CREW ACCOMMODATION" auto-detects CICA
- Same validation rules as ISM/ISPS/MLC
- Orange badge color

### 2. Google Drive Path
- Old: `ISM-ISPS-MLC` (no spaces)
- New: `ISM - ISPS - MLC` (with spaces)
- CICA uses same path (no separate folder)
- No migration needed (old files stay in old path)

### 3. Backward Compatibility
- ✅ Existing ISM/ISPS/MLC data unchanged
- ✅ New CICA category additive (not breaking)
- ✅ Frontend filters backward compatible
- ✅ API responses include CICA type

### 4. Validation Priority
1. File validation (size, type)
2. AI quality check
3. **Category check (must be ISM/ISPS/MLC/CICA)** ⭐
4. IMO validation (hard reject if mismatch)
5. Ship name validation (soft warning)
6. Duplicate check (user choice)

---

## 📞 NEXT STEPS

1. **Review this summary with user** ✅
2. **Confirm plan approval** ⬜
3. **Begin implementation** ⬜
4. **Test thoroughly** ⬜
5. **Deploy to production** ⬜

---

**Status**: ✅ Plan Complete - Ready for Implementation  
**Updated**: 2025-01-XX  
**Estimated Effort**: 6 days (1 developer)  
**Breaking Changes**: None  
**New Feature**: CICA Support ⭐
