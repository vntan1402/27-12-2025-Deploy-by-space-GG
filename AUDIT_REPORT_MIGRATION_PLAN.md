# Audit Report Migration Plan - Copy từ Class Survey Report List

## 📋 TỔNG QUAN (OVERVIEW)

**Mục tiêu**: Copy toàn bộ structure, features, và functionality từ Class Survey Report List sang Audit Report placeholder trong ISM-ISPS-MLC module.

**Source**:
- `/app/frontend/src/components/ClassSurveyReport/ClassSurveyReportList.jsx`
- `/app/frontend/src/pages/ClassSurveyReport.jsx`

**Destination**:
- `/app/frontend/src/components/AuditReport/` (NEW)
- `/app/frontend/src/pages/IsmIspsMLc.jsx` (UPDATE - audit_report section)
- `/app/backend/server.py` (ADD new endpoints)

---

## 🎯 SCOPE OF WORK

### **1. Frontend Components** (NEW - 9 files)
### **2. Frontend Services** (NEW - 1 file)
### **3. Backend Endpoints** (NEW - 6 endpoints)
### **4. Page Integration** (UPDATE - 1 file)
### **5. Database Collections** (NEW - 1 collection)

---

## 📂 PHASE 1: CREATE COMPONENT STRUCTURE

### **Step 1.1: Create AuditReport Component Folder**

```bash
mkdir -p /app/frontend/src/components/AuditReport
```

### **Step 1.2: Copy & Rename Component Files**

Copy from ClassSurveyReport → AuditReport với renaming:

| Source File | Destination File | Changes |
|------------|------------------|---------|
| `ClassSurveyReportList.jsx` | `AuditReportList.jsx` | Rename component, update fields |
| `AddSurveyReportModal.jsx` | `AddAuditReportModal.jsx` | Update API calls, fields |
| `EditSurveyReportModal.jsx` | `EditAuditReportModal.jsx` | Update API calls, fields |
| `SurveyReportNotesModal.jsx` | `AuditReportNotesModal.jsx` | Update text labels |
| (NEW) | `DeleteAuditReportModal.jsx` | Create new deletion modal |
| `BatchProcessingModal.jsx` | (REUSE) | No changes needed |
| `BatchResultsModal.jsx` | (REUSE) | No changes needed |
| (NEW) | `index.js` | Export all components |

---

## 🔄 PHASE 2: FIELD MAPPING

### **Class Survey Report Fields** → **Audit Report Fields**

| Class Survey Report | Audit Report | Type | Notes |
|---------------------|--------------|------|-------|
| `id` | `id` | string (UUID) | Same |
| `ship_id` | `ship_id` | string (UUID) | Same |
| `survey_report_name` | **`audit_report_name`** | string | ⭐ RENAME |
| `report_form` | **`audit_type`** | string | ⭐ CHANGE (ISM/ISPS/MLC/SMC/DOC) |
| `survey_report_no` | **`audit_report_no`** | string | ⭐ RENAME |
| `issued_date` | **`audit_date`** | date | ⭐ RENAME |
| `issued_by` | **`audited_by`** | string | ⭐ RENAME (Auditor name/company) |
| `status` | `status` | string | Same (Valid/Expired/Pending) |
| `note` | `note` | string | Same |
| `surveyor_name` | **`auditor_name`** | string | ⭐ RENAME |
| `survey_report_file_id` | **`audit_report_file_id`** | string | ⭐ RENAME (Google Drive) |
| `survey_report_summary_file_id` | **`audit_report_summary_file_id`** | string | ⭐ RENAME (Summary) |
| (N/A) | **`next_audit_date`** | date | ⭐ NEW (Next audit due date) |
| (N/A) | **`findings_count`** | integer | ⭐ NEW (Number of findings) |
| (N/A) | **`nc_count`** | integer | ⭐ NEW (Non-conformities count) |

---

## 📊 PHASE 3: TABLE STRUCTURE

### **Updated Table Columns** (8 columns):

| # | Column | Source | Destination | Changes |
|---|--------|--------|-------------|---------|
| 1 | Checkbox | ☑️ Checkbox | ☑️ Checkbox | Same |
| 2 | Name + Icons | Survey Report Name 📄📋 | **Audit Report Name 📄📋** | Rename field |
| 3 | Type | Report Form | **Audit Type** | Change (ISM/ISPS/MLC/SMC/DOC) |
| 4 | Number | Survey Report No | **Audit Report No** | Rename field |
| 5 | Date | Issued Date | **Audit Date** | Rename field |
| 6 | By | Issued By (Abbrev) | **Audited By (Abbrev)** | Rename field |
| 7 | Status | Status Badge | Status Badge | Same |
| 8 | Note | Note * | Note * | Same |

### **New Column Options** (Optional - Phase 2):

Add these columns in Phase 2 if needed:
- **Next Audit**: Next audit due date
- **Findings**: Number of findings
- **NC**: Non-conformities count

---

## 🔌 PHASE 4: BACKEND API ENDPOINTS

### **Create New Service File**

**File**: `/app/backend/audit_report_service.py` (Optional - or add to server.py)

### **Required Endpoints** (6):

#### **1. Get All Audit Reports**
```python
@api_router.get("/audit-reports")
async def get_audit_reports(
    ship_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all audit reports for a ship"""
    pass
```

#### **2. Create Audit Report**
```python
@api_router.post("/audit-reports")
async def create_audit_report(
    report_data: AuditReportCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create new audit report"""
    pass
```

#### **3. Update Audit Report**
```python
@api_router.put("/audit-reports/{report_id}")
async def update_audit_report(
    report_id: str,
    report_data: AuditReportUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update audit report"""
    pass
```

#### **4. Bulk Delete Audit Reports**
```python
@api_router.post("/audit-reports/bulk-delete")
async def bulk_delete_audit_reports(
    report_ids: List[str],
    current_user: UserResponse = Depends(get_current_user)
):
    """Bulk delete audit reports + Google Drive files"""
    pass
```

#### **5. Analyze Audit Report File (AI)**
```python
@api_router.post("/audit-reports/analyze")
async def analyze_audit_report_file(
    ship_id: str,
    file: UploadFile,
    bypass_validation: bool = False
):
    """AI analysis of audit report PDF"""
    pass
```

#### **6. Upload Audit Report Files**
```python
@api_router.post("/audit-reports/{report_id}/upload-files")
async def upload_audit_report_files(
    report_id: str,
    file_content: str,
    filename: str,
    content_type: str,
    summary_text: str = None
):
    """Upload files to Google Drive"""
    pass
```

---

## 💾 PHASE 5: DATABASE COLLECTION

### **New Collection**: `audit_reports`

**Schema**:
```javascript
{
  "_id": ObjectId,
  "id": "uuid-string",              // UUID
  "ship_id": "ship-uuid",           // Foreign key
  "audit_report_name": "string",    // Report name
  "audit_type": "ISM|ISPS|MLC|SMC|DOC", // Audit type
  "audit_report_no": "string",      // Report number
  "audit_date": "2025-01-15",       // Date of audit
  "audited_by": "string",           // Auditor/company name
  "auditor_name": "string",         // Auditor name
  "status": "Valid|Expired|Pending", // Status
  "note": "string",                  // Notes
  "audit_report_file_id": "gdrive-id", // Original file
  "audit_report_summary_file_id": "gdrive-id", // Summary file
  "next_audit_date": "2026-01-15",  // Optional
  "findings_count": 5,               // Optional
  "nc_count": 2,                     // Optional
  "created_at": "ISO date",
  "updated_at": "ISO date"
}
```

### **Indexes**:
```javascript
db.audit_reports.createIndex({ "ship_id": 1 })
db.audit_reports.createIndex({ "id": 1 }, { unique: true })
db.audit_reports.createIndex({ "audit_type": 1 })
db.audit_reports.createIndex({ "status": 1 })
```

---

## 🎨 PHASE 6: FRONTEND SERVICE

### **Create Service File**

**File**: `/app/frontend/src/services/auditReportService.js`

**Methods** (7):

```javascript
export const auditReportService = {
  // Get all audit reports for a ship
  getAll: async (shipId) => {
    return await api.get(`/api/audit-reports?ship_id=${shipId}`);
  },

  // Create audit report
  create: async (reportData) => {
    return await api.post('/api/audit-reports', reportData);
  },

  // Update audit report
  update: async (reportId, reportData) => {
    return await api.put(`/api/audit-reports/${reportId}`, reportData);
  },

  // Bulk delete
  bulkDelete: async (reportIds) => {
    return await api.post('/api/audit-reports/bulk-delete', { report_ids: reportIds });
  },

  // AI analysis
  analyzeFile: async (shipId, file, bypassValidation = false) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('ship_id', shipId);
    formData.append('bypass_validation', bypassValidation);
    return await api.post('/api/audit-reports/analyze', formData);
  },

  // Upload files
  uploadFiles: async (reportId, fileContent, filename, contentType, summaryText) => {
    return await api.post(`/api/audit-reports/${reportId}/upload-files`, {
      file_content: fileContent,
      filename: filename,
      content_type: contentType,
      summary_text: summaryText
    });
  },

  // Delete single report
  delete: async (reportId) => {
    return await api.delete(`/api/audit-reports/${reportId}`);
  }
};
```

**Export in** `/app/frontend/src/services/index.js`:
```javascript
export { auditReportService } from './auditReportService';
```

---

## 🔄 PHASE 7: PAGE INTEGRATION

### **Update**: `/app/frontend/src/pages/IsmIspsMLc.jsx`

#### **Step 7.1: Add Imports**

```javascript
// Add to imports (line ~6)
import {
  // ... existing imports
  AuditReportList,
  AddAuditReportModal,
  EditAuditReportModal,
  AuditReportNotesModal,
  BatchProcessingModal,
  BatchResultsModal
} from '../components/AuditReport';
import { auditReportService } from '../services';
```

#### **Step 7.2: Add State Variables**

```javascript
// Audit Report States (NEW)
const [auditReports, setAuditReports] = useState([]);
const [auditReportsLoading, setAuditReportsLoading] = useState(false);
const [selectedAuditReports, setSelectedAuditReports] = useState(new Set());

// Audit Report Modals (NEW)
const [showAddAuditReportModal, setShowAddAuditReportModal] = useState(false);
const [showEditAuditReportModal, setShowEditAuditReportModal] = useState(false);
const [showDeleteAuditReportModal, setShowDeleteAuditReportModal] = useState(false);
const [editingAuditReport, setEditingAuditReport] = useState(null);
const [deletingAuditReport, setDeletingAuditReport] = useState(null);

// Audit Report Filters & Sort (NEW)
const [auditReportFilters, setAuditReportFilters] = useState({
  auditType: 'all',
  status: 'all',
  search: ''
});
const [auditReportSort, setAuditReportSort] = useState({
  column: 'audit_date',
  direction: 'desc'
});

// Audit Report Actions (NEW)
const [isRefreshingAuditReports, setIsRefreshingAuditReports] = useState(false);

// Batch Processing (NEW)
const [isBatchProcessing, setIsBatchProcessing] = useState(false);
const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });
const [fileProgressMap, setFileProgressMap] = useState({});
const [fileStatusMap, setFileStatusMap] = useState({});
const [fileSubStatusMap, setFileSubStatusMap] = useState({});
const [batchResults, setBatchResults] = useState([]);
const [showBatchResults, setShowBatchResults] = useState(false);
const [isBatchModalMinimized, setIsBatchModalMinimized] = useState(false);

// Notes Modal (NEW)
const [auditReportNotesModal, setAuditReportNotesModal] = useState({
  show: false, report: null, notes: ''
});
```

#### **Step 7.3: Replace Placeholder Content**

**Find** (lines ~1138-1156):
```javascript
{selectedSubMenu === 'audit_report' && (
  <div className="text-center py-12">
    <div className="text-6xl mb-4">📋</div>
    <h3 className="text-2xl font-semibold text-gray-700 mb-2">
      {language === 'vi' ? 'Audit Report' : 'Audit Report'}
    </h3>
    <p className="text-gray-500">
      {language === 'vi' 
        ? 'Chức năng này sẽ được triển khai trong các giai đoạn tiếp theo' 
        : 'This feature will be implemented in upcoming phases'}
    </p>
  </div>
)}
```

**Replace with**:
```javascript
{selectedSubMenu === 'audit_report' && (
  <AuditReportList
    selectedShip={selectedShip}
    reports={auditReports}
    loading={auditReportsLoading}
    selectedReports={selectedAuditReports}
    onSelectReport={handleSelectAuditReport}
    onSelectAll={handleSelectAllAuditReports}
    filters={auditReportFilters}
    onFiltersChange={setAuditReportFilters}
    sort={auditReportSort}
    onSortChange={setAuditReportSort}
    onRefresh={handleRefreshAuditReports}
    isRefreshing={isRefreshingAuditReports}
    onStartBatchProcessing={startBatchProcessingAuditReports}
    onAddReport={() => setShowAddAuditReportModal(true)}
  />
)}
```

#### **Step 7.4: Add Handler Functions**

```javascript
// Fetch audit reports
const fetchAuditReports = async () => {
  if (!selectedShip) return;
  try {
    setAuditReportsLoading(true);
    const response = await auditReportService.getAll(selectedShip.id);
    const data = response.data || response || [];
    setAuditReports(Array.isArray(data) ? data : []);
  } catch (error) {
    console.error('Failed to fetch audit reports:', error);
    toast.error(language === 'vi' ? 'Không thể tải audit reports' : 'Failed to load audit reports');
    setAuditReports([]);
  } finally {
    setAuditReportsLoading(false);
  }
};

// Refresh handler
const handleRefreshAuditReports = async () => {
  // ... similar to Class Survey Report
};

// Selection handlers
const handleSelectAuditReport = (reportId) => {
  // ... similar to Class Survey Report
};

const handleSelectAllAuditReports = (checked) => {
  // ... similar to Class Survey Report
};

// Batch processing
const startBatchProcessingAuditReports = async (files) => {
  // ... similar to Class Survey Report
};

// Process single file
const processSingleAuditReportFile = async (file) => {
  // ... similar to Class Survey Report
};
```

#### **Step 7.5: Add Modals at Bottom**

```javascript
{/* Add Audit Report Modal */}
<AddAuditReportModal
  isOpen={showAddAuditReportModal}
  onClose={() => setShowAddAuditReportModal(false)}
  selectedShip={selectedShip}
  onReportAdded={() => {
    setShowAddAuditReportModal(false);
    fetchAuditReports();
  }}
  onStartBatchProcessing={(files) => {
    setShowAddAuditReportModal(false);
    startBatchProcessingAuditReports(files);
  }}
/>

{/* Edit Audit Report Modal */}
{showEditAuditReportModal && editingAuditReport && (
  <EditAuditReportModal
    isOpen={showEditAuditReportModal}
    onClose={() => {
      setShowEditAuditReportModal(false);
      setEditingAuditReport(null);
    }}
    report={editingAuditReport}
    onReportUpdated={() => {
      setShowEditAuditReportModal(false);
      setEditingAuditReport(null);
      fetchAuditReports();
    }}
  />
)}

{/* Audit Report Notes Modal */}
<AuditReportNotesModal
  isOpen={auditReportNotesModal.show}
  onClose={() => setAuditReportNotesModal({ show: false, report: null, notes: '' })}
  report={auditReportNotesModal.report}
  notes={auditReportNotesModal.notes}
  onNotesChange={(notes) => setAuditReportNotesModal(prev => ({ ...prev, notes }))}
  onSave={handleSaveAuditReportNotes}
  language={language}
/>

{/* Batch Processing Modal */}
<BatchProcessingModal
  isOpen={isBatchProcessing}
  isMinimized={isBatchModalMinimized}
  onMinimize={() => setIsBatchModalMinimized(true)}
  onRestore={() => setIsBatchModalMinimized(false)}
  progress={batchProgress}
  fileProgressMap={fileProgressMap}
  fileStatusMap={fileStatusMap}
  fileSubStatusMap={fileSubStatusMap}
/>

{/* Batch Results Modal */}
<BatchResultsModal
  isOpen={showBatchResults}
  onClose={() => {
    setShowBatchResults(false);
    setBatchResults([]);
    fetchAuditReports();
  }}
  results={batchResults}
/>
```

---

## 🎯 PHASE 8: CONTEXT MENU FEATURES

### **Features to Implement** (Same as Class Survey Report):

#### **Single Item Actions**:
1. 📂 **View File** - Open in new tab
2. 📋 **Copy Link** - Copy Google Drive link
3. ✏️ **Edit** - Open edit modal
4. 🗑️ **Delete** - Delete with confirmation

#### **Bulk Actions**:
1. 👁️ **View Files** (up to 10)
2. 📥 **Download Files**
3. 🔗 **Copy Links**
4. 🗑️ **Bulk Delete**

---

## 🚀 PHASE 9: SPECIAL FEATURES

### **Features to Copy**:

1. ✅ **File Icons** (📄 Original, 📋 Summary)
2. ✅ **Abbreviation System** (Audited By → 2-4 letters)
3. ✅ **Status Badges** (Color-coded)
4. ✅ **Note Tooltip** (Smart positioning)
5. ✅ **Sorting** (Multi-column)
6. ✅ **Checkbox Selection** (Indeterminate state)
7. ✅ **Filters** (Type + Status + Search)
8. ✅ **Refresh Button** (with animation)
9. ✅ **Batch Upload** (AI analysis)
10. ✅ **Google Drive Integration**

---

## 📝 PHASE 10: TEXT LABELS & TRANSLATIONS

### **Key Label Changes**:

| English | Vietnamese | Context |
|---------|-----------|---------|
| Survey Report | Audit Report | Title |
| Survey Report Name | Audit Report Name | Column |
| Report Form | Audit Type | Column |
| Survey Report No | Audit Report No | Column |
| Issued Date | Audit Date | Column |
| Issued By | Audited By | Column |
| Surveyor | Auditor | Label |
| Add Survey Report | Add Audit Report | Button |
| No survey reports | No audit reports | Empty state |

---

## 🧪 PHASE 11: TESTING CHECKLIST

### **Frontend Testing**:
- [ ] Table displays correctly with 8 columns
- [ ] Sorting works on all columns
- [ ] Filters work (Type, Status, Search)
- [ ] Checkbox selection (all/individual)
- [ ] Context menu appears on right-click
- [ ] Single item actions work
- [ ] Bulk actions work
- [ ] Add modal opens and submits
- [ ] Edit modal opens and updates
- [ ] Delete confirmation works
- [ ] Notes modal works
- [ ] File icons clickable
- [ ] Tooltips show correctly
- [ ] Refresh button works

### **Backend Testing**:
- [ ] GET all audit reports
- [ ] POST create audit report
- [ ] PUT update audit report
- [ ] POST bulk delete
- [ ] POST analyze file (AI)
- [ ] POST upload files
- [ ] Google Drive integration
- [ ] Database CRUD operations

### **Integration Testing**:
- [ ] Batch upload works
- [ ] Batch processing modal shows progress
- [ ] Batch results modal shows summary
- [ ] Files uploaded to Google Drive
- [ ] Files viewable in Drive
- [ ] Files downloadable
- [ ] Links copyable
- [ ] Bulk delete removes files from Drive

---

## ⏱️ ESTIMATED TIMELINE

### **Phase-by-Phase Breakdown**:

| Phase | Task | Time | Dependencies |
|-------|------|------|--------------|
| **1** | Component Structure | 30 min | - |
| **2** | Field Mapping | 1 hour | Phase 1 |
| **3** | Table Structure | 1 hour | Phase 2 |
| **4** | Backend Endpoints | 3 hours | Phase 2 |
| **5** | Database Collection | 30 min | Phase 4 |
| **6** | Frontend Service | 1 hour | Phase 4 |
| **7** | Page Integration | 2 hours | Phase 1-6 |
| **8** | Context Menu | 1 hour | Phase 7 |
| **9** | Special Features | 2 hours | Phase 7-8 |
| **10** | Labels & i18n | 30 min | Phase 7-9 |
| **11** | Testing | 2 hours | All phases |

**Total Estimated Time**: **14-16 hours**

---

## 📦 DELIVERABLES

### **New Files Created** (10+):

#### Frontend:
1. `/app/frontend/src/components/AuditReport/AuditReportList.jsx`
2. `/app/frontend/src/components/AuditReport/AddAuditReportModal.jsx`
3. `/app/frontend/src/components/AuditReport/EditAuditReportModal.jsx`
4. `/app/frontend/src/components/AuditReport/AuditReportNotesModal.jsx`
5. `/app/frontend/src/components/AuditReport/DeleteAuditReportModal.jsx`
6. `/app/frontend/src/components/AuditReport/index.js`
7. `/app/frontend/src/services/auditReportService.js`

#### Backend:
8. Backend endpoints in `/app/backend/server.py` (or separate file)

#### Database:
9. MongoDB collection: `audit_reports`

### **Files Modified** (2):

1. `/app/frontend/src/pages/IsmIspsMLc.jsx` - Replace placeholder
2. `/app/frontend/src/services/index.js` - Add export

---

## 🔧 IMPLEMENTATION STEPS (DETAILED)

### **Step-by-Step Execution**:

#### **Step 1: Backend First** (3.5 hours)
1. Create Pydantic models for AuditReport
2. Add 6 API endpoints to server.py
3. Implement Google Drive integration
4. Test endpoints with Postman/curl
5. Create database collection and indexes

#### **Step 2: Frontend Service** (1 hour)
1. Create auditReportService.js
2. Add all 7 methods
3. Export in services/index.js
4. Test API calls

#### **Step 3: Components** (4 hours)
1. Copy ClassSurveyReportList → AuditReportList
2. Copy modal components (Add, Edit, Notes, Delete)
3. Update all field names and labels
4. Update API service calls
5. Create index.js for exports

#### **Step 4: Page Integration** (2 hours)
1. Update IsmIspsMLc.jsx imports
2. Add state variables
3. Add handler functions
4. Replace placeholder with AuditReportList
5. Add modals at bottom

#### **Step 5: Testing** (2 hours)
1. Test table display
2. Test CRUD operations
3. Test context menu
4. Test batch operations
5. Test file operations
6. Fix bugs

#### **Step 6: Polish** (1.5 hours)
1. Update translations
2. Fix styling issues
3. Add loading states
4. Add error handling
5. Final testing

---

## ✅ SUCCESS CRITERIA

### **Functional Requirements**:
- ✅ Audit Report list displays correctly
- ✅ All CRUD operations work
- ✅ File upload and AI analysis work
- ✅ Google Drive integration works
- ✅ Bulk operations work
- ✅ Context menu functions properly
- ✅ Modals open and submit correctly
- ✅ Filters and sorting work
- ✅ Selection system works

### **UI/UX Requirements**:
- ✅ Layout matches Class Survey Report
- ✅ Colors and styling consistent
- ✅ Icons display correctly
- ✅ Tooltips positioned properly
- ✅ Responsive design
- ✅ Loading states clear
- ✅ Error messages helpful

### **Performance Requirements**:
- ✅ List loads in < 2 seconds
- ✅ Filters apply instantly
- ✅ Sorting is smooth
- ✅ File operations don't block UI
- ✅ Batch processing shows progress

---

## 🎯 FINAL NOTES

### **Key Differences from Class Survey Report**:

1. **Field Names**: survey → audit (report_name, report_no, date, by)
2. **Audit Type**: ISM/ISPS/MLC/SMC/DOC (instead of Report Form)
3. **Context**: Maritime audit reports (compliance, safety management)
4. **Optional Fields**: Next audit date, findings count, NC count

### **Reusable Components**:
- BatchProcessingModal
- BatchResultsModal
- File upload logic
- Google Drive integration
- Context menu system
- Tooltip system

### **Must Copy Exactly**:
- Table structure (8 columns)
- Checkbox selection system
- Context menu with 9 actions
- File icons (📄 📋)
- Abbreviation logic
- Status badge colors
- Note tooltip with smart positioning
- Sorting indicators

---

## 🚀 READY TO IMPLEMENT

**Prerequisites**:
- ✅ Class Survey Report fully functional
- ✅ Google Drive integration working
- ✅ AI analysis working
- ✅ MongoDB connection established
- ✅ ISM-ISPS-MLC page structure ready

**Next Steps**:
1. Review and approve this plan
2. Start with Phase 1 (Backend)
3. Follow phases sequentially
4. Test after each phase
5. Deploy to production

**Estimated Timeline**: 2 working days (14-16 hours)

---

**Plan created and ready for implementation! 🎉**
