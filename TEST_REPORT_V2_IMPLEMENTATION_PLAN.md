# TEST REPORT V2 - IMPLEMENTATION PLAN
**Based on V1 Analysis with Modifications**

---

## 🎯 OBJECTIVE
Implement Test Report page in V2 matching V1 functionality, with one modification:
- ❌ **REMOVE**: Valid Date From/To filters
- ✅ **KEEP**: All other features identical to V1

---

## 📋 IMPLEMENTATION PHASES

---

## PHASE 1: BACKEND API ENDPOINTS

### 1.1 Test Report CRUD APIs
**File**: `/app/backend/server.py`

#### Endpoints to implement:
```python
# 1. Get all test reports for a ship
GET /api/test-reports?ship_id={ship_id}
Response: List[TestReport]

# 2. Create test report (with AI analysis support)
POST /api/test-reports
Body: {
  ship_id, test_report_name, report_form, test_report_no,
  issued_by, issued_date, valid_date, note
}
Response: { id, ...report_data }

# 3. Upload test report file (background task)
POST /api/test-reports/{report_id}/upload-files
Body: FormData with test_report_file
Response: { message, file_id, summary_file_id }

# 4. Update test report
PUT /api/test-reports/{report_id}
Body: { ...updated_fields }
Response: { ...updated_report }

# 5. Delete test report (single)
DELETE /api/test-reports/{report_id}
Response: { success, message }

# 6. Bulk delete test reports
POST /api/test-reports/bulk-delete
Body: { report_ids: [id1, id2, ...] }
Response: { deleted_count, errors: [...] }

# 7. AI analyze file (for auto-fill)
POST /api/test-reports/analyze-file
Body: FormData with test_report_file
Response: {
  test_report_name, report_form, test_report_no,
  issued_by, issued_date, valid_date, ...
}
```

### 1.2 Status Calculation Logic
**Function**: `calculate_test_report_status(valid_date)`
```python
def calculate_test_report_status(valid_date):
    """
    Calculate status based on valid_date:
    - Valid: > 90 days remaining
    - Expired soon: 30-90 days remaining
    - Critical: 1-30 days remaining
    - Expired: <= 0 days remaining
    - Unknown: no valid_date
    """
```

### 1.3 MongoDB Schema
**Collection**: `test_reports`
```javascript
{
  id: UUID,
  ship_id: UUID,
  company_id: UUID,
  test_report_name: String,
  report_form: String (optional),
  test_report_no: String,
  issued_by: String (optional),
  issued_date: Date (optional),
  valid_date: Date (optional),
  status: String (Valid/Expired soon/Critical/Expired/Unknown),
  note: String (optional),
  test_report_file_id: String (Google Drive),
  test_report_summary_file_id: String (Google Drive),
  created_at: DateTime,
  updated_at: DateTime
}
```

### 1.4 Google Drive Integration
**File paths**:
- Original file: `{SHIP_NAME}/Class & Flag Cert/Test Report/{filename}`
- Summary file: `SUMMARY/Class & Flag Document/{filename}_summary.txt`

---

## PHASE 2: FRONTEND STRUCTURE

### 2.1 File Structure
```
/app/frontend/src/
├── pages/
│   └── TestReport.jsx (NEW)
├── components/
│   └── TestReport/
│       ├── TestReportList.jsx (NEW)
│       ├── AddTestReportModal.jsx (NEW)
│       ├── EditTestReportModal.jsx (NEW)
│       ├── TestReportNotesModal.jsx (NEW)
│       └── index.js (NEW)
├── services/
│   └── testReportService.js (NEW)
├── routes/
│   └── AppRoutes.jsx (UPDATE - add TestReport route)
```

### 2.2 Route Configuration
**File**: `/app/frontend/src/routes/AppRoutes.jsx`
```javascript
<Route path="/test-report" element={<TestReport />} />
```

### 2.3 Menu Integration
**File**: `/app/frontend/src/components/Layout/CategoryMenu.jsx`
```javascript
// Add Test Report menu item under "Class & Flag Cert" category
{
  name: language === 'vi' ? 'Báo cáo Test' : 'Test Report',
  path: '/test-report',
  submenu: 'test_reports'
}
```

---

## PHASE 3: MAIN PAGE COMPONENT

### 3.1 TestReport.jsx (Page Container)
**File**: `/app/frontend/src/pages/TestReport.jsx`

#### Responsibilities:
- Manage modal states (Add, Edit, Notes)
- Handle selected ship from context
- Pass callbacks to TestReportList
- Provide refresh trigger

#### State:
```javascript
const [showAddModal, setShowAddModal] = useState(false);
const [showEditModal, setShowEditModal] = useState(false);
const [editingReport, setEditingReport] = useState(null);
const [showNotesModal, setShowNotesModal] = useState(false);
const [notesReport, setNotesReport] = useState(null);
const [listRefreshKey, setListRefreshKey] = useState(0);
```

#### Layout:
```jsx
<div className="space-y-6">
  <TestReportList
    selectedShip={selectedShip}
    onAddReport={() => setShowAddModal(true)}
    onEditReport={(report) => { setEditingReport(report); setShowEditModal(true); }}
    onViewNotes={(report) => { setNotesReport(report); setShowNotesModal(true); }}
    refreshKey={listRefreshKey}
  />
  
  {/* Modals */}
  {showAddModal && <AddTestReportModal ... />}
  {showEditModal && <EditTestReportModal ... />}
  {showNotesModal && <TestReportNotesModal ... />}
</div>
```

---

## PHASE 4: TEST REPORT LIST COMPONENT

### 4.1 TestReportList.jsx
**File**: `/app/frontend/src/components/TestReport/TestReportList.jsx`

#### State Management:
```javascript
// Data
const [testReports, setTestReports] = useState([]);
const [loading, setLoading] = useState(false);
const [isRefreshing, setIsRefreshing] = useState(false);

// Filters (MODIFIED - NO Valid Date From/To)
const [filters, setFilters] = useState({
  status: 'all',
  search: ''
});

// Sorting
const [sort, setSort] = useState({
  column: null,
  direction: 'asc'
});

// Selection
const [selectedReports, setSelectedReports] = useState(new Set());

// Context Menu
const [contextMenu, setContextMenu] = useState({
  show: false,
  x: 0,
  y: 0,
  report: null
});

// Note Tooltip
const [noteTooltip, setNoteTooltip] = useState({
  show: false,
  x: 0,
  y: 0,
  content: ''
});
```

---

### 4.2 HEADER SECTION

#### Layout:
```jsx
<div className="flex justify-between items-center mb-4">
  {/* Left: Title */}
  <h3 className="text-lg font-semibold text-gray-800">
    {language === 'vi' ? 'Danh sách Báo cáo Test' : 'Test Report List'}
  </h3>
  
  {/* Right: Action Buttons */}
  <div className="flex gap-3">
    {/* Add Button (Green) */}
    <button
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
        selectedShip
          ? 'bg-green-600 hover:bg-green-700 text-white cursor-pointer'
          : 'bg-gray-400 cursor-not-allowed text-white'
      }`}
      onClick={() => selectedShip && onAddReport()}
      disabled={!selectedShip}
      title={...}
    >
      <svg className="w-4 h-4" ...>+</svg>
      {language === 'vi' ? 'Thêm Báo cáo Test' : 'Add Test Report'}
    </button>
    
    {/* Refresh Button (Blue) */}
    <button
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
        selectedShip && !isRefreshing
          ? 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer'
          : 'bg-gray-400 cursor-not-allowed text-white'
      }`}
      onClick={handleRefresh}
      disabled={!selectedShip || isRefreshing}
    >
      {isRefreshing ? (
        <svg className="animate-spin h-4 w-4" ...>spinner</svg>
      ) : (
        <svg className="w-4 h-4" ...>refresh</svg>
      )}
      {language === 'vi' ? 'Làm mới' : 'Refresh'}
    </button>
  </div>
</div>
```

---

### 4.3 FILTERS SECTION (MODIFIED)

#### Layout:
```jsx
<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-4">
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    {/* Status Filter */}
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {language === 'vi' ? 'Trạng thái' : 'Status'}
      </label>
      <select
        value={filters.status}
        onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
      >
        <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
        <option value="valid">{language === 'vi' ? 'Còn hạn' : 'Valid'}</option>
        <option value="expired soon">{language === 'vi' ? 'Sắp hết hạn' : 'Expired soon'}</option>
        <option value="critical">{language === 'vi' ? 'Khẩn cấp' : 'Critical'}</option>
        <option value="expired">{language === 'vi' ? 'Hết hạn' : 'Expired'}</option>
      </select>
    </div>

    {/* Search Filter */}
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {language === 'vi' ? 'Tìm kiếm' : 'Search'}
      </label>
      <input
        type="text"
        placeholder={language === 'vi' ? 'Tìm kiếm...' : 'Search...'}
        value={filters.search}
        onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
      />
    </div>
    
    {/* ❌ REMOVED: Valid Date From */}
    {/* ❌ REMOVED: Valid Date To */}
  </div>

  {/* Clear Filters Button */}
  {(filters.status !== 'all' || filters.search) && (
    <div className="mt-3 flex justify-end">
      <button
        onClick={() => setFilters({ status: 'all', search: '' })}
        className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-all"
      >
        {language === 'vi' ? 'Xóa bộ lọc' : 'Clear filters'}
      </button>
    </div>
  )}
</div>
```

**Change from V1**: Grid changed from `grid-cols-4` to `grid-cols-2` (only 2 filters now)

---

### 4.4 TABLE STRUCTURE

#### Table Container:
```jsx
<div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
  <div className="overflow-x-auto">
    <table className="min-w-full">
      <thead className="bg-gray-50 border-b border-gray-200">
        {/* Headers */}
      </thead>
      <tbody>
        {/* Rows */}
      </tbody>
    </table>
  </div>
</div>
```

---

### 4.5 TABLE COLUMNS (9 columns)

#### Column Definitions:
```javascript
const columns = [
  // 1. Checkbox + No.
  {
    key: 'no',
    header: language === 'vi' ? 'Số TT' : 'No.',
    sortable: false,
    width: 'auto',
    render: (report, index) => (
      <div className="flex items-center">
        <input
          type="checkbox"
          checked={selectedReports.has(report.id)}
          onChange={() => handleReportSelect(report.id)}
          className="w-4 h-4 mr-3"
          onClick={(e) => e.stopPropagation()}
        />
        <span>{index + 1}</span>
      </div>
    )
  },
  
  // 2. Test Report Name (sortable)
  {
    key: 'test_report_name',
    header: language === 'vi' ? 'Tên Báo cáo Test' : 'Test Report Name',
    sortable: true,
    render: (report) => (
      <div className="flex items-center gap-2">
        <span>{report.test_report_name}</span>
        
        {/* Original File Icon */}
        {report.test_report_file_id && (
          <span 
            className="text-green-500 text-xs cursor-pointer hover:text-green-600" 
            title={`${language === 'vi' ? 'File gốc' : 'Original file'}\n📁 ${selectedShip?.name}/Class & Flag Cert/Test Report`}
            onClick={(e) => handleOpenFile(e, report.test_report_file_id)}
          >
            📄
          </span>
        )}
        
        {/* Summary File Icon */}
        {report.test_report_summary_file_id && (
          <span 
            className="text-blue-500 text-xs cursor-pointer hover:text-blue-600" 
            title={`${language === 'vi' ? 'File tóm tắt' : 'Summary file'}\n📁 SUMMARY/Class & Flag Document`}
            onClick={(e) => handleOpenFile(e, report.test_report_summary_file_id)}
          >
            📋
          </span>
        )}
      </div>
    )
  },
  
  // 3. Report Form (sortable)
  {
    key: 'report_form',
    header: language === 'vi' ? 'Mẫu Báo cáo' : 'Report Form',
    sortable: true,
    render: (report) => report.report_form || '-'
  },
  
  // 4. Test Report No. (sortable, monospace)
  {
    key: 'test_report_no',
    header: language === 'vi' ? 'Số Báo cáo' : 'Test Report No.',
    sortable: true,
    className: 'font-mono',
    render: (report) => report.test_report_no
  },
  
  // 5. Issued By (sortable)
  {
    key: 'issued_by',
    header: language === 'vi' ? 'Cấp bởi' : 'Issued By',
    sortable: true,
    render: (report) => report.issued_by || '-'
  },
  
  // 6. Issued Date (sortable)
  {
    key: 'issued_date',
    header: language === 'vi' ? 'Ngày cấp' : 'Issued Date',
    sortable: true,
    render: (report) => report.issued_date ? formatDate(report.issued_date) : '-'
  },
  
  // 7. Valid Date (sortable, with info icon)
  {
    key: 'valid_date',
    header: (
      <div className="flex items-center gap-1">
        <span>{language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}</span>
        <span 
          className="text-blue-500 cursor-help text-sm"
          title={language === 'vi' 
            ? 'Thông tin hạn bảo dưỡng được tính bởi AI có thể gặp sai sót. Vui lòng kiểm tra và sửa lại nếu cần' 
            : 'Valid Date calculated by AI may contain errors. Please verify and correct if needed'}
          onClick={(e) => e.stopPropagation()}
        >
          ⓘ
        </span>
      </div>
    ),
    sortable: true,
    render: (report) => (
      <span
        className="cursor-help"
        title={language === 'vi' 
          ? 'Thông tin hạn bảo dưỡng được tính bởi AI có thể gặp sai sót. Vui lòng kiểm tra và sửa lại nếu cần' 
          : 'Valid Date calculated by AI may contain errors. Please verify and correct if needed'}
      >
        {report.valid_date ? formatDate(report.valid_date) : '-'}
      </span>
    )
  },
  
  // 8. Status (sortable, colored badge)
  {
    key: 'status',
    header: language === 'vi' ? 'Trạng thái' : 'Status',
    sortable: true,
    render: (report) => (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
        report.status === 'Valid' ? 'bg-green-100 text-green-800' :
        report.status === 'Expired soon' ? 'bg-yellow-100 text-yellow-800' :
        report.status === 'Critical' ? 'bg-orange-100 text-orange-800' :
        report.status === 'Expired' ? 'bg-red-100 text-red-800' :
        'bg-gray-100 text-gray-800'
      }`}>
        {report.status}
      </span>
    )
  },
  
  // 9. Note (not sortable, red asterisk)
  {
    key: 'note',
    header: language === 'vi' ? 'Ghi chú' : 'Note',
    sortable: false,
    align: 'center',
    render: (report) => (
      report.note ? (
        <span 
          className="text-red-600 cursor-help text-lg font-bold"
          onMouseEnter={(e) => handleNoteMouseEnter(e, report.note)}
          onMouseLeave={handleNoteMouseLeave}
          onClick={(e) => {
            e.stopPropagation();
            onViewNotes(report);
          }}
        >
          *
        </span>
      ) : (
        '-'
      )
    )
  }
];
```

---

### 4.6 SORTING LOGIC

```javascript
const handleSort = (column) => {
  setSort(prev => ({
    column,
    direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
  }));
};

const getSortedReports = (reports) => {
  if (!sort.column) return reports;
  
  return [...reports].sort((a, b) => {
    let aVal = a[sort.column];
    let bVal = b[sort.column];
    
    // Handle null/undefined
    if (!aVal) return 1;
    if (!bVal) return -1;
    
    // Date comparison
    if (sort.column.includes('date')) {
      aVal = new Date(aVal);
      bVal = new Date(bVal);
    }
    
    // String comparison (case-insensitive)
    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }
    
    if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1;
    return 0;
  });
};
```

#### Sort Indicator in Header:
```jsx
{column.sortable && (
  <th 
    className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
    onClick={() => handleSort(column.key)}
  >
    <div className="flex items-center justify-between">
      {column.header}
      {sort.column === column.key && (
        <span className="ml-1 text-blue-600 text-sm font-bold">
          {sort.direction === 'asc' ? '▲' : '▼'}
        </span>
      )}
    </div>
  </th>
)}
```

---

### 4.7 FILTERING LOGIC

```javascript
const getFilteredReports = () => {
  let filtered = [...testReports];
  
  // Status filter
  if (filters.status !== 'all') {
    filtered = filtered.filter(report => {
      const status = report.status?.toLowerCase();
      return status === filters.status.toLowerCase();
    });
  }
  
  // Search filter (searches in name, form, number, issued_by)
  if (filters.search) {
    const searchLower = filters.search.toLowerCase();
    filtered = filtered.filter(report => 
      report.test_report_name?.toLowerCase().includes(searchLower) ||
      report.report_form?.toLowerCase().includes(searchLower) ||
      report.test_report_no?.toLowerCase().includes(searchLower) ||
      report.issued_by?.toLowerCase().includes(searchLower)
    );
  }
  
  // ❌ REMOVED: Valid Date From/To filtering logic
  
  return getSortedReports(filtered);
};
```

---

### 4.8 SELECTION LOGIC

```javascript
// Select single report
const handleReportSelect = (reportId) => {
  setSelectedReports(prev => {
    const newSet = new Set(prev);
    if (newSet.has(reportId)) {
      newSet.delete(reportId);
    } else {
      newSet.add(reportId);
    }
    return newSet;
  });
};

// Select all reports
const handleSelectAll = (checked) => {
  if (checked) {
    const allIds = getFilteredReports().map(r => r.id);
    setSelectedReports(new Set(allIds));
  } else {
    setSelectedReports(new Set());
  }
};

// Check if all selected
const isAllSelected = () => {
  const filtered = getFilteredReports();
  return filtered.length > 0 && filtered.every(r => selectedReports.has(r.id));
};

// Check if indeterminate
const isIndeterminate = () => {
  const filtered = getFilteredReports();
  const selectedCount = filtered.filter(r => selectedReports.has(r.id)).length;
  return selectedCount > 0 && selectedCount < filtered.length;
};
```

---

### 4.9 CONTEXT MENU

#### Trigger:
```jsx
<tr 
  key={report.id}
  className="hover:bg-gray-50 cursor-pointer"
  onContextMenu={(e) => handleContextMenu(e, report)}
>
  {/* cells */}
</tr>
```

#### Handler:
```javascript
const handleContextMenu = (e, report) => {
  e.preventDefault();
  setContextMenu({
    show: true,
    x: e.clientX,
    y: e.clientY,
    report
  });
};
```

#### Menu Component:
```jsx
{contextMenu.show && (
  <>
    {/* Overlay to close menu */}
    <div 
      className="fixed inset-0 z-40"
      onClick={() => setContextMenu({ show: false, x: 0, y: 0, report: null })}
    />
    
    {/* Menu */}
    <div
      className="fixed bg-white shadow-xl rounded-lg border border-gray-200 py-2 z-50"
      style={{ 
        left: `${contextMenu.x}px`,
        top: `${contextMenu.y}px`,
        minWidth: '180px'
      }}
    >
      {selectedReports.size > 1 ? (
        // Multiple selection - Bulk Delete
        <button
          onClick={handleBulkDelete}
          className="w-full px-4 py-2 text-left hover:bg-red-50 text-gray-700 hover:text-red-600 transition-all flex items-center gap-2 font-medium"
        >
          <svg className="w-4 h-4" ...>trash</svg>
          {language === 'vi' ? `Xóa ${selectedReports.size} mục đã chọn` : `Delete ${selectedReports.size} Selected`}
        </button>
      ) : (
        // Single selection - Edit + Delete
        <>
          <button
            onClick={() => handleEdit(contextMenu.report)}
            className="w-full px-4 py-2 text-left hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-all flex items-center gap-2"
          >
            <svg className="w-4 h-4" ...>edit</svg>
            {language === 'vi' ? 'Chỉnh sửa' : 'Edit'}
          </button>
          
          <button
            onClick={() => handleDelete(contextMenu.report)}
            className="w-full px-4 py-2 text-left hover:bg-red-50 text-gray-700 hover:text-red-600 transition-all flex items-center gap-2"
          >
            <svg className="w-4 h-4" ...>trash</svg>
            {language === 'vi' ? 'Xóa' : 'Delete'}
          </button>
        </>
      )}
    </div>
  </>
)}
```

---

### 4.10 NOTE TOOLTIP

```jsx
{noteTooltip.show && (
  <div
    className="fixed bg-gray-800 text-white p-3 rounded-lg shadow-2xl z-50 border border-gray-600"
    style={{
      left: `${noteTooltip.x}px`,
      top: `${noteTooltip.y}px`,
      width: `${noteTooltip.width}px`,
      maxHeight: '200px',
      overflowY: 'auto',
      fontSize: '14px',
      lineHeight: '1.5'
    }}
  >
    {noteTooltip.content}
  </div>
)}
```

#### Handlers:
```javascript
const handleNoteMouseEnter = (e, note) => {
  const rect = e.target.getBoundingClientRect();
  setNoteTooltip({
    show: true,
    x: rect.left,
    y: rect.bottom + 5,
    width: 300,
    content: note
  });
};

const handleNoteMouseLeave = () => {
  setNoteTooltip({ show: false, x: 0, y: 0, content: '' });
};
```

---

### 4.11 EMPTY STATES

```jsx
{getFilteredReports().length === 0 ? (
  <tr>
    <td colSpan="9" className="border border-gray-300 px-4 py-8 text-center text-gray-500">
      {testReports.length === 0 
        ? (language === 'vi' ? 'Chưa có báo cáo test nào' : 'No test reports available')
        : (language === 'vi' ? 'Không có báo cáo test nào phù hợp với bộ lọc' : 'No test reports match the current filters')
      }
    </td>
  </tr>
) : (
  // Render rows
)}
```

---

## PHASE 5: MODALS

### 5.1 AddTestReportModal.jsx

#### Features:
- File upload with drag & drop
- AI analysis auto-fill (analyze file button)
- Manual form input
- Background file upload after creation
- Progress indicator

#### Fields:
```javascript
{
  test_report_name: '',
  report_form: '',
  test_report_no: '',
  issued_by: '',
  issued_date: '',
  valid_date: '',
  note: ''
}
```

#### Flow:
1. User uploads file
2. Click "Analyze with AI" button
3. Backend analyzes file and returns extracted data
4. Auto-fill form fields
5. User reviews/edits data
6. Click "Save"
7. Create report in database
8. Background upload file to Google Drive
9. Show success toast
10. Close modal and refresh list

---

### 5.2 EditTestReportModal.jsx

#### Features:
- Pre-filled form with existing data
- Same fields as Add modal
- Can update all fields except file
- Shows current file links

#### Flow:
1. Load existing report data
2. User edits fields
3. Click "Save"
4. Update report in database
5. Show success toast
6. Close modal and refresh list

---

### 5.3 TestReportNotesModal.jsx

#### Features:
- View full note content
- Edit note
- Save changes

#### Layout:
```jsx
<Modal>
  <Header>
    {language === 'vi' ? 'Ghi chú' : 'Note'}
  </Header>
  
  <Body>
    <textarea
      value={note}
      onChange={(e) => setNote(e.target.value)}
      rows={10}
      className="w-full border rounded p-2"
    />
  </Body>
  
  <Footer>
    <button onClick={handleSave}>
      {language === 'vi' ? 'Lưu' : 'Save'}
    </button>
    <button onClick={onClose}>
      {language === 'vi' ? 'Đóng' : 'Close'}
    </button>
  </Footer>
</Modal>
```

---

## PHASE 6: SERVICE LAYER

### 6.1 testReportService.js

```javascript
import api from './api';

export const testReportService = {
  // Get all test reports for a ship
  getAll: async (shipId) => {
    const response = await api.get(`/api/test-reports?ship_id=${shipId}`);
    return response.data;
  },
  
  // Create test report
  create: async (data) => {
    const response = await api.post('/api/test-reports', data);
    return response.data;
  },
  
  // Upload test report file (background)
  uploadFile: async (reportId, file) => {
    const formData = new FormData();
    formData.append('test_report_file', file);
    const response = await api.post(`/api/test-reports/${reportId}/upload-files`, formData);
    return response.data;
  },
  
  // AI analyze file
  analyzeFile: async (file) => {
    const formData = new FormData();
    formData.append('test_report_file', file);
    const response = await api.post('/api/test-reports/analyze-file', formData);
    return response.data;
  },
  
  // Update test report
  update: async (reportId, data) => {
    const response = await api.put(`/api/test-reports/${reportId}`, data);
    return response.data;
  },
  
  // Delete test report
  delete: async (reportId) => {
    const response = await api.delete(`/api/test-reports/${reportId}`);
    return response.data;
  },
  
  // Bulk delete test reports
  bulkDelete: async (reportIds) => {
    const response = await api.post('/api/test-reports/bulk-delete', { report_ids: reportIds });
    return response.data;
  }
};
```

---

## PHASE 7: TESTING CHECKLIST

### Backend Testing:
- [ ] CRUD operations working
- [ ] AI analysis extracting correct data
- [ ] File upload to Google Drive successful
- [ ] Status calculation correct
- [ ] Bulk delete working
- [ ] Error handling proper

### Frontend Testing:
- [ ] Table displays correctly
- [ ] 9 columns with correct data
- [ ] Sorting working on 7 columns
- [ ] 2 filters working (Status, Search)
- [ ] Clear filters button appears/works
- [ ] Checkbox selection working
- [ ] Select all/none working
- [ ] Context menu opens on right-click
- [ ] Edit modal opens with correct data
- [ ] Delete confirmation shows
- [ ] Bulk delete confirmation shows
- [ ] File icons clickable and open Drive
- [ ] Note tooltip shows on hover
- [ ] Note modal opens on click
- [ ] Status badges colored correctly
- [ ] Empty states display correctly
- [ ] Add button disabled without ship
- [ ] Refresh button works
- [ ] Loading states show correctly

### Integration Testing:
- [ ] Add test report end-to-end
- [ ] AI analysis auto-fill working
- [ ] File upload background task
- [ ] Edit test report saves
- [ ] Delete removes from list
- [ ] Bulk delete removes all selected
- [ ] Filters update table correctly
- [ ] Sort persists after filter
- [ ] Selection clears after delete
- [ ] Context menu closes properly

---

## PHASE 8: KEY DIFFERENCES FROM V1

### ✅ KEPT FROM V1:
- All 9 table columns
- 7 sortable columns
- Status badges with colors
- File icons (📄 original, 📋 summary)
- Note indicator (red asterisk *)
- Info icon (ⓘ) on Valid Date
- Context menu (Edit, Delete, Bulk Delete)
- Checkbox selection
- Add/Refresh buttons
- Empty states
- Tooltips

### ❌ REMOVED FROM V1:
- **Valid Date From filter**
- **Valid Date To filter**

### 🔄 MODIFIED FROM V1:
- **Filters section**: Changed from 4-column grid to 2-column grid
- **Clear filters logic**: Only checks status and search (not date filters)

---

## PHASE 9: IMPLEMENTATION ORDER

### Day 1: Backend
1. ✅ Create MongoDB schema
2. ✅ Implement CRUD APIs
3. ✅ Add AI analysis endpoint
4. ✅ Implement status calculation
5. ✅ Test all endpoints with Postman

### Day 2: Frontend Structure
1. ✅ Create file structure
2. ✅ Add route configuration
3. ✅ Update menu integration
4. ✅ Create TestReport page component
5. ✅ Create service layer

### Day 3: Test Report List
1. ✅ Build table structure
2. ✅ Implement 9 columns
3. ✅ Add sorting logic
4. ✅ Add filtering logic (2 filters only)
5. ✅ Implement selection

### Day 4: Features
1. ✅ Context menu
2. ✅ Note tooltip
3. ✅ File icons with links
4. ✅ Status badges
5. ✅ Empty states

### Day 5: Modals
1. ✅ Add Test Report Modal
2. ✅ Edit Test Report Modal
3. ✅ Notes Modal
4. ✅ AI analysis integration

### Day 6: Testing
1. ✅ Backend testing
2. ✅ Frontend testing
3. ✅ Integration testing
4. ✅ Bug fixes

---

## PHASE 10: NOTES & TIPS

### Performance:
- Use React.memo for table rows
- Debounce search input
- Lazy load modals
- Optimize sort/filter functions

### UX:
- Show loading states
- Disable buttons during operations
- Show toast notifications
- Keep selection state visible

### Error Handling:
- Catch all API errors
- Show user-friendly messages
- Log errors to console
- Provide retry options

### Accessibility:
- Keyboard navigation
- ARIA labels
- Focus management
- Screen reader support

---

## ✅ READY TO IMPLEMENT!

This plan provides complete specifications to build Test Report in V2 matching V1 functionality, with the requested modification of removing Valid Date From/To filters.

