# KẾ HOẠCH DI CHUYỂN TEST REPORT LIST TABLE - V1 TO V2
**Migration Plan with Complete Feature Parity (minus 2 date filters)**

---

## 🎯 MỤC TIÊU

Di chuyển **Test Report List Table** từ V1 sang V2 với:
- ✅ **BỐ CỤC**: 100% giống V1
- ✅ **CHỨC NĂNG**: 100% giống V1
- ❌ **BỎ**: Filter "Valid Date From" và "Valid Date To"
- ✅ **GIỮ NGUYÊN**: Tất cả features khác

---

## 📊 PHÂN TÍCH HIỆN TRẠNG

### V1 Location:
- **File**: `/app/frontend-v1/src/App.js`
- **Lines**: 15804 - 16253 (450 lines)
- **State management**: Inline trong App.js
- **Backend**: API endpoints đã có sẵn

### V2 Target:
- **Structure**: Component-based architecture
- **Files**: Separate components, services, and hooks
- **Route**: `/test-report`
- **Integration**: Sidebar menu + Ship selection context

---

## 🗂️ CẤU TRÚC FILE V2

```
/app/frontend/src/
├── pages/
│   └── TestReport.jsx                          (NEW - 150 lines)
│
├── components/
│   └── TestReport/
│       ├── TestReportList.jsx                  (NEW - 800 lines)
│       ├── AddTestReportModal.jsx              (NEW - 400 lines)
│       ├── EditTestReportModal.jsx             (NEW - 350 lines)
│       ├── TestReportNotesModal.jsx            (NEW - 150 lines)
│       └── index.js                            (NEW - exports)
│
├── services/
│   └── testReportService.js                    (NEW - 100 lines)
│
├── hooks/
│   └── useTestReportSort.js                    (NEW - optional)
│
├── routes/
│   └── AppRoutes.jsx                           (UPDATE - add route)
│
└── components/Layout/
    └── CategoryMenu.jsx                        (UPDATE - add menu item)
```

**Total**: ~2000 lines of new code

---

## 📋 ROADMAP TRIỂN KHAI

### **PHASE 1**: Chuẩn bị Backend (1-2 giờ)
### **PHASE 2**: Routing & Navigation (30 phút)
### **PHASE 3**: Service Layer (30 phút)
### **PHASE 4**: Page Container (30 phút)
### **PHASE 5**: Test Report List Component (4-5 giờ)
### **PHASE 6**: Modals (3-4 giờ)
### **PHASE 7**: Testing & Bug Fixes (2-3 giờ)

**Tổng thời gian ước tính**: 12-16 giờ

---

## 🔧 PHASE 1: CHUẨN BỊ BACKEND

### 1.1 Kiểm tra Backend APIs

**Endpoints cần có**:
```python
# File: /app/backend/server.py

# 1. GET - Lấy danh sách test reports
GET /api/test-reports?ship_id={ship_id}
Response: [
  {
    id, ship_id, company_id,
    test_report_name, report_form, test_report_no,
    issued_by, issued_date, valid_date, status,
    note, test_report_file_id, test_report_summary_file_id,
    created_at, updated_at
  }
]

# 2. POST - Tạo test report mới
POST /api/test-reports
Body: { ship_id, test_report_name, report_form, test_report_no, ... }
Response: { id, ..., message: "Test report created" }

# 3. POST - Upload file (background task)
POST /api/test-reports/{report_id}/upload-files
Body: FormData with test_report_file
Response: { 
  message: "File upload started",
  test_report_file_id: "...",
  test_report_summary_file_id: "..."
}

# 4. POST - AI analyze file
POST /api/test-reports/analyze-file
Body: FormData with test_report_file
Response: {
  test_report_name: "...",
  report_form: "...",
  test_report_no: "...",
  issued_by: "...",
  issued_date: "...",
  valid_date: "...",
  _file_content: "...",
  _summary_text: "..."
}

# 5. PUT - Cập nhật test report
PUT /api/test-reports/{report_id}
Body: { test_report_name, report_form, ... }
Response: { ..., message: "Test report updated" }

# 6. DELETE - Xóa test report
DELETE /api/test-reports/{report_id}
Response: { success: true, message: "..." }

# 7. POST - Bulk delete
POST /api/test-reports/bulk-delete
Body: { report_ids: ["id1", "id2", ...] }
Response: { 
  deleted_count: 2,
  errors: []
}
```

### 1.2 MongoDB Schema

**Collection**: `test_reports`
```javascript
{
  id: "uuid-string",                    // Primary key
  ship_id: "uuid-string",               // Foreign key to ships
  company_id: "uuid-string",            // Foreign key to companies
  
  // Test Report Info
  test_report_name: "Annual Survey",
  report_form: "Form ABC",              // Optional
  test_report_no: "A/25/772",
  
  // Issue Info
  issued_by: "DNV GL",                  // Optional
  issued_date: "2024-01-15",           // Optional, ISO date
  valid_date: "2025-01-15",            // Optional, ISO date
  
  // Status (calculated from valid_date)
  status: "Valid",                      // Valid | Expired soon | Critical | Expired | Unknown
  
  // Additional
  note: "Some notes...",                // Optional
  
  // Google Drive Files
  test_report_file_id: "drive-file-id",           // Original file
  test_report_summary_file_id: "drive-summary-id", // Summary file
  
  // Timestamps
  created_at: ISODate("2024-01-15T10:30:00Z"),
  updated_at: ISODate("2024-01-15T10:30:00Z")
}
```

### 1.3 Status Calculation Logic

```python
def calculate_test_report_status(valid_date: date) -> str:
    """
    Calculate status based on valid_date
    
    Returns:
        - "Valid": More than 90 days remaining
        - "Expired soon": 30-90 days remaining
        - "Critical": 1-30 days remaining  
        - "Expired": 0 or negative days remaining
        - "Unknown": No valid_date
    """
    if not valid_date:
        return "Unknown"
    
    today = date.today()
    days_remaining = (valid_date - today).days
    
    if days_remaining > 90:
        return "Valid"
    elif days_remaining > 30:
        return "Expired soon"
    elif days_remaining > 0:
        return "Critical"
    else:
        return "Expired"
```

### 1.4 Google Drive Integration

**Upload Paths**:
```
Original file:
{SHIP_NAME}/Class & Flag Cert/Test Report/{filename}

Summary file:
SUMMARY/Class & Flag Document/{filename}_summary.txt
```

**Backend function** (should already exist, reuse from Survey Report):
```python
# File: /app/backend/dual_apps_script_manager.py

async def upload_test_report_and_summary(
    ship_name: str,
    test_report_file: UploadFile,
    summary_text: str
) -> dict:
    """
    Upload test report original file and summary file to Google Drive
    
    Returns:
        {
            "test_report_file_id": "...",
            "test_report_summary_file_id": "..."
        }
    """
```

---

## 🔗 PHASE 2: ROUTING & NAVIGATION

### 2.1 Add Route

**File**: `/app/frontend/src/routes/AppRoutes.jsx`

**Thêm import**:
```javascript
import { TestReport } from '../pages';
```

**Thêm route**:
```javascript
<Route path="/test-report" element={<TestReport />} />
```

### 2.2 Update Menu

**File**: `/app/frontend/src/components/Layout/CategoryMenu.jsx`

**Tìm phần Class & Flag Cert category và thêm**:
```javascript
{
  name: language === 'vi' ? 'Báo cáo Test' : 'Test Report',
  path: '/test-report',
  icon: '📋',
  submenu: 'test_reports'
}
```

### 2.3 Update Pages Index

**File**: `/app/frontend/src/pages/index.js`

**Thêm export**:
```javascript
export { TestReport } from './TestReport';
```

---

## 🛠️ PHASE 3: SERVICE LAYER

### 3.1 Create Test Report Service

**File**: `/app/frontend/src/services/testReportService.js`

```javascript
import api from './api';

export const testReportService = {
  /**
   * Get all test reports for a ship
   */
  getAll: async (shipId) => {
    const response = await api.get(`/api/test-reports?ship_id=${shipId}`);
    return response.data;
  },

  /**
   * Create new test report
   */
  create: async (data) => {
    const response = await api.post('/api/test-reports', data);
    return response.data;
  },

  /**
   * Upload test report file (background task)
   */
  uploadFile: async (reportId, file) => {
    const formData = new FormData();
    formData.append('test_report_file', file);
    const response = await api.post(
      `/api/test-reports/${reportId}/upload-files`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    return response.data;
  },

  /**
   * Analyze test report file with AI
   */
  analyzeFile: async (file) => {
    const formData = new FormData();
    formData.append('test_report_file', file);
    const response = await api.post(
      '/api/test-reports/analyze-file',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    return response.data;
  },

  /**
   * Update test report
   */
  update: async (reportId, data) => {
    const response = await api.put(`/api/test-reports/${reportId}`, data);
    return response.data;
  },

  /**
   * Delete single test report
   */
  delete: async (reportId) => {
    const response = await api.delete(`/api/test-reports/${reportId}`);
    return response.data;
  },

  /**
   * Bulk delete test reports
   */
  bulkDelete: async (reportIds) => {
    const response = await api.post('/api/test-reports/bulk-delete', {
      report_ids: reportIds
    });
    return response.data;
  },

  /**
   * View file in Google Drive (opens new tab)
   */
  viewFile: async (reportId, fileType) => {
    // fileType: 'original' or 'summary'
    const response = await api.get(
      `/api/test-reports/${reportId}/view-file?file_type=${fileType}`
    );
    return response.data.view_url;
  },

  /**
   * Get shareable link for file
   */
  getFileLink: async (reportId, fileType) => {
    const response = await api.get(
      `/api/test-reports/${reportId}/file-link?file_type=${fileType}`
    );
    return response.data.link;
  }
};
```

### 3.2 Update Services Index

**File**: `/app/frontend/src/services/index.js`

**Thêm export**:
```javascript
export { testReportService } from './testReportService';
```

---

## 📄 PHASE 4: PAGE CONTAINER

### 4.1 Create TestReport.jsx

**File**: `/app/frontend/src/pages/TestReport.jsx`

```javascript
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  TestReportList,
  AddTestReportModal,
  EditTestReportModal,
  TestReportNotesModal
} from '../components/TestReport';

export const TestReport = () => {
  const { selectedShip } = useAuth();

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showNotesModal, setShowNotesModal] = useState(false);
  
  // Current editing/viewing report
  const [editingReport, setEditingReport] = useState(null);
  const [notesReport, setNotesReport] = useState(null);
  
  // Refresh trigger
  const [listRefreshKey, setListRefreshKey] = useState(0);

  // Handlers
  const handleAddReport = () => {
    setShowAddModal(true);
  };

  const handleEditReport = (report) => {
    setEditingReport(report);
    setShowEditModal(true);
  };

  const handleViewNotes = (report) => {
    setNotesReport(report);
    setShowNotesModal(true);
  };

  const handleAddSuccess = () => {
    setShowAddModal(false);
    setListRefreshKey(prev => prev + 1);
  };

  const handleEditSuccess = () => {
    setShowEditModal(false);
    setEditingReport(null);
    setListRefreshKey(prev => prev + 1);
  };

  const handleNotesUpdate = () => {
    setListRefreshKey(prev => prev + 1);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Test Report List */}
      <TestReportList
        selectedShip={selectedShip}
        onAddReport={handleAddReport}
        onEditReport={handleEditReport}
        onViewNotes={handleViewNotes}
        refreshKey={listRefreshKey}
      />

      {/* Add Test Report Modal */}
      {showAddModal && (
        <AddTestReportModal
          selectedShip={selectedShip}
          onClose={() => setShowAddModal(false)}
          onSuccess={handleAddSuccess}
        />
      )}

      {/* Edit Test Report Modal */}
      {showEditModal && editingReport && (
        <EditTestReportModal
          report={editingReport}
          selectedShip={selectedShip}
          onClose={() => {
            setShowEditModal(false);
            setEditingReport(null);
          }}
          onSuccess={handleEditSuccess}
        />
      )}

      {/* Notes Modal */}
      {showNotesModal && notesReport && (
        <TestReportNotesModal
          report={notesReport}
          onClose={() => {
            setShowNotesModal(false);
            setNotesReport(null);
          }}
          onUpdate={handleNotesUpdate}
        />
      )}
    </div>
  );
};
```

---

## 📊 PHASE 5: TEST REPORT LIST COMPONENT

### 5.1 Component Structure Overview

**File**: `/app/frontend/src/components/TestReport/TestReportList.jsx`

**Sections**:
1. Imports & State Management (lines 1-80)
2. useEffect & Data Fetching (lines 81-120)
3. Filter Logic (lines 121-160)
4. Sort Logic (lines 161-200)
5. Selection Logic (lines 201-250)
6. Handler Functions (lines 251-350)
7. JSX - Header Section (lines 351-400)
8. JSX - Filters Section (lines 401-480)
9. JSX - Table (lines 481-700)
10. JSX - Context Menu (lines 701-780)
11. JSX - Note Tooltip (lines 781-800)

---

### 5.2 Imports & State Management

```javascript
/**
 * Test Report List Component
 * Displays test reports table with filters, sorting, CRUD operations
 * Migrated from V1 with 100% feature parity (minus date filters)
 */
import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { testReportService } from '../../services';
import { toast } from 'sonner';
import { formatDateDisplay } from '../../utils/dateHelpers';

export const TestReportList = ({ 
  selectedShip, 
  onAddReport, 
  onEditReport, 
  onViewNotes,
  refreshKey 
}) => {
  const { language } = useAuth();

  // ========== DATA STATE ==========
  const [testReports, setTestReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // ========== FILTERS STATE (MODIFIED - NO DATE FILTERS) ==========
  const [filters, setFilters] = useState({
    status: 'all',
    search: ''
    // ❌ REMOVED: validDateFrom: ''
    // ❌ REMOVED: validDateTo: ''
  });

  // ========== SORTING STATE ==========
  const [sort, setSort] = useState({
    column: null,
    direction: 'asc'
  });

  // ========== SELECTION STATE ==========
  const [selectedReports, setSelectedReports] = useState(new Set());

  // ========== CONTEXT MENU STATE ==========
  const [contextMenu, setContextMenu] = useState({
    show: false,
    x: 0,
    y: 0,
    report: null
  });

  // ========== NOTE TOOLTIP STATE ==========
  const [noteTooltip, setNoteTooltip] = useState({
    show: false,
    x: 0,
    y: 0,
    width: 300,
    content: ''
  });

  // ========== REFS ==========
  const contextMenuRef = useRef(null);

  // ... (continue with useEffect and functions)
```

---

### 5.3 Data Fetching

```javascript
  // ========== FETCH TEST REPORTS ==========
  useEffect(() => {
    if (selectedShip) {
      fetchTestReports();
    } else {
      setTestReports([]);
    }
  }, [selectedShip, refreshKey]);

  const fetchTestReports = async () => {
    if (!selectedShip) return;

    try {
      setLoading(true);
      const data = await testReportService.getAll(selectedShip.id);
      setTestReports(data);
    } catch (error) {
      console.error('Failed to fetch test reports:', error);
      toast.error(
        language === 'vi' 
          ? 'Không thể tải danh sách báo cáo test' 
          : 'Failed to load test reports'
      );
    } finally {
      setLoading(false);
    }
  };

  // ========== REFRESH HANDLER ==========
  const handleRefresh = async () => {
    if (!selectedShip || isRefreshing) return;

    try {
      setIsRefreshing(true);
      await fetchTestReports();
      toast.success(
        language === 'vi' 
          ? '✅ Đã cập nhật danh sách Test Reports!' 
          : '✅ Test Reports list updated!'
      );
    } catch (error) {
      console.error('Failed to refresh test reports:', error);
      toast.error(
        language === 'vi' 
          ? '❌ Không thể làm mới danh sách' 
          : '❌ Failed to refresh list'
      );
    } finally {
      setIsRefreshing(false);
    }
  };
```

---

### 5.4 Filter Logic (MODIFIED)

```javascript
  // ========== FILTER LOGIC (MODIFIED - NO DATE FILTERS) ==========
  const getFilteredReports = () => {
    let filtered = [...testReports];

    // Status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(report => {
        const status = report.status?.toLowerCase();
        return status === filters.status.toLowerCase();
      });
    }

    // Search filter (searches: name, form, number, issued_by)
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(report =>
        report.test_report_name?.toLowerCase().includes(searchLower) ||
        report.report_form?.toLowerCase().includes(searchLower) ||
        report.test_report_no?.toLowerCase().includes(searchLower) ||
        report.issued_by?.toLowerCase().includes(searchLower)
      );
    }

    // ❌ REMOVED: Valid Date From filtering
    // ❌ REMOVED: Valid Date To filtering

    return getSortedReports(filtered);
  };
```

---

### 5.5 Sort Logic

```javascript
  // ========== SORT LOGIC ==========
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

---

### 5.6 Selection Logic

```javascript
  // ========== SELECTION LOGIC ==========
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

  const handleSelectAll = (checked) => {
    if (checked) {
      const allIds = getFilteredReports().map(r => r.id);
      setSelectedReports(new Set(allIds));
    } else {
      setSelectedReports(new Set());
    }
  };

  const isAllSelected = () => {
    const filtered = getFilteredReports();
    return filtered.length > 0 && filtered.every(r => selectedReports.has(r.id));
  };

  const isIndeterminate = () => {
    const filtered = getFilteredReports();
    const selectedCount = filtered.filter(r => selectedReports.has(r.id)).length;
    return selectedCount > 0 && selectedCount < filtered.length;
  };
```

---

### 5.7 Context Menu Handlers

```javascript
  // ========== CONTEXT MENU HANDLERS ==========
  const handleContextMenu = (e, report) => {
    e.preventDefault();
    setContextMenu({
      show: true,
      x: e.clientX,
      y: e.clientY,
      report
    });
  };

  const handleEdit = (report) => {
    setContextMenu({ show: false, x: 0, y: 0, report: null });
    onEditReport(report);
  };

  const handleDelete = async (report) => {
    setContextMenu({ show: false, x: 0, y: 0, report: null });

    const confirmMsg = language === 'vi'
      ? 'Bạn có chắc muốn xóa báo cáo test này?'
      : 'Are you sure you want to delete this test report?';

    if (!window.confirm(confirmMsg)) return;

    try {
      await testReportService.delete(report.id);
      toast.success(
        language === 'vi' 
          ? 'Đã xóa báo cáo test' 
          : 'Test report deleted successfully'
      );
      fetchTestReports();
      setSelectedReports(new Set());
    } catch (error) {
      console.error('Failed to delete test report:', error);
      toast.error(
        language === 'vi' 
          ? 'Không thể xóa báo cáo test' 
          : 'Failed to delete test report'
      );
    }
  };

  const handleBulkDelete = async () => {
    setContextMenu({ show: false, x: 0, y: 0, report: null });

    const reportCount = selectedReports.size;
    const confirmMsg = language === 'vi'
      ? `Bạn có chắc muốn xóa ${reportCount} báo cáo test đã chọn? Thao tác này cũng sẽ xóa các file liên quan trên Google Drive.`
      : `Are you sure you want to delete ${reportCount} test report(s)? This will also delete associated files from Google Drive.`;

    if (!window.confirm(confirmMsg)) return;

    const toastMsg = language === 'vi'
      ? `🗑️ Đang xóa ${reportCount} báo cáo test và file...`
      : `🗑️ Deleting ${reportCount} test report(s) and files...`;

    toast.loading(toastMsg);

    try {
      const reportIds = Array.from(selectedReports);
      const result = await testReportService.bulkDelete(reportIds);

      toast.dismiss();

      if (result.errors && result.errors.length > 0) {
        toast.warning(
          language === 'vi'
            ? `⚠️ Đã xóa ${result.deleted_count} báo cáo test, ${result.errors.length} lỗi`
            : `⚠️ Deleted ${result.deleted_count} test report(s), ${result.errors.length} error(s)`
        );
      } else {
        toast.success(
          language === 'vi'
            ? `✅ Đã xóa ${result.deleted_count} báo cáo test thành công`
            : `✅ Successfully deleted ${result.deleted_count} test report(s)`
        );
      }

      fetchTestReports();
      setSelectedReports(new Set());
    } catch (error) {
      console.error('Failed to bulk delete:', error);
      toast.dismiss();
      toast.error(
        language === 'vi' 
          ? '❌ Lỗi khi xóa báo cáo test' 
          : '❌ Failed to delete test reports'
      );
    }
  };
```

---

### 5.8 File Handlers

```javascript
  // ========== FILE HANDLERS ==========
  const handleOpenFile = async (e, fileId) => {
    e.stopPropagation();
    if (!fileId) return;
    
    // Open Google Drive file in new tab
    window.open(`https://drive.google.com/file/d/${fileId}/view`, '_blank');
  };
```

---

### 5.9 Note Tooltip Handlers

```javascript
  // ========== NOTE TOOLTIP HANDLERS ==========
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
    setNoteTooltip({ show: false, x: 0, y: 0, width: 300, content: '' });
  };

  const handleNoteClick = (e, report) => {
    e.stopPropagation();
    handleNoteMouseLeave();
    onViewNotes(report);
  };
```

---

### 5.10 JSX - Main Return

```javascript
  // ========== RENDER ==========
  const filteredReports = getFilteredReports();

  return (
    <div className="space-y-4">
      {/* ========== HEADER SECTION ========== */}
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
            title={
              selectedShip
                ? (language === 'vi' ? 'Thêm báo cáo test mới' : 'Add new test report')
                : (language === 'vi' ? 'Vui lòng chọn tàu trước' : 'Please select a ship first')
            }
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
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
            title={
              selectedShip
                ? (language === 'vi' ? 'Làm mới danh sách' : 'Refresh list')
                : (language === 'vi' ? 'Vui lòng chọn tàu trước' : 'Please select a ship first')
            }
          >
            {isRefreshing ? (
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            {language === 'vi' ? 'Làm mới' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Continue with Filters Section... */}
```

---

### 5.11 JSX - Filters Section (MODIFIED)

```javascript
      {/* ========== FILTERS SECTION (MODIFIED) ========== */}
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

**NOTE**: Grid changed from `grid-cols-4` (V1) to `grid-cols-2` (V2) because we only have 2 filters now.

---

### 5.12 JSX - Table Structure

```javascript
      {/* ========== TABLE ========== */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            {/* Table Head */}
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {/* Column 1: Checkbox + No. */}
                <th className="border border-gray-300 px-4 py-2 text-left">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={isAllSelected()}
                      ref={el => {
                        if (el) {
                          el.indeterminate = isIndeterminate();
                        }
                      }}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="w-4 h-4 mr-2"
                    />
                    <span>{language === 'vi' ? 'Số TT' : 'No.'}</span>
                  </div>
                </th>

                {/* Column 2: Test Report Name (sortable) */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('test_report_name')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Tên Báo cáo Test' : 'Test Report Name'}</span>
                    {sort.column === 'test_report_name' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 3: Report Form (sortable) */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('report_form')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Mẫu Báo cáo' : 'Report Form'}</span>
                    {sort.column === 'report_form' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 4: Test Report No. (sortable) */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('test_report_no')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Số Báo cáo' : 'Test Report No.'}</span>
                    {sort.column === 'test_report_no' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 5: Issued By (sortable) */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('issued_by')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Cấp bởi' : 'Issued By'}</span>
                    {sort.column === 'issued_by' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 6: Issued Date (sortable) */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('issued_date')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Ngày cấp' : 'Issued Date'}</span>
                    {sort.column === 'issued_date' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 7: Valid Date (sortable) with info icon */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('valid_date')}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1">
                      <span>{language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}</span>
                      <span
                        className="text-blue-500 cursor-help text-sm"
                        title={
                          language === 'vi'
                            ? 'Thông tin hạn bảo dưỡng được tính bởi AI có thể gặp sai sót. Vui lòng kiểm tra và sửa lại nếu cần'
                            : 'Valid Date calculated by AI may contain errors. Please verify and correct if needed'
                        }
                        onClick={(e) => e.stopPropagation()}
                      >
                        ⓘ
                      </span>
                    </div>
                    {sort.column === 'valid_date' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 8: Status (sortable) */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('status')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Trạng thái' : 'Status'}</span>
                    {sort.column === 'status' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 9: Note (not sortable) */}
                <th className="border border-gray-300 px-4 py-2 text-center">
                  {language === 'vi' ? 'Ghi chú' : 'Note'}
                </th>
              </tr>
            </thead>

            {/* Table Body */}
            <tbody>
              {/* Continue with rows... */}
```

---

### 5.13 JSX - Table Rows

```javascript
              {filteredReports.length === 0 ? (
                // Empty State
                <tr>
                  <td colSpan="9" className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                    {testReports.length === 0
                      ? (language === 'vi' ? 'Chưa có báo cáo test nào' : 'No test reports available')
                      : (language === 'vi' ? 'Không có báo cáo test nào phù hợp với bộ lọc' : 'No test reports match the current filters')
                    }
                  </td>
                </tr>
              ) : (
                // Render Rows
                filteredReports.map((report, index) => (
                  <tr
                    key={report.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onContextMenu={(e) => handleContextMenu(e, report)}
                  >
                    {/* Cell 1: Checkbox + No. */}
                    <td className="border border-gray-300 px-4 py-2">
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
                    </td>

                    {/* Cell 2: Test Report Name + File Icons */}
                    <td className="border border-gray-300 px-4 py-2">
                      <div className="flex items-center gap-2">
                        <span>{report.test_report_name}</span>

                        {/* Original File Icon (📄 green) */}
                        {report.test_report_file_id && (
                          <span
                            className="text-green-500 text-xs cursor-pointer hover:text-green-600"
                            title={`${language === 'vi' ? 'File gốc' : 'Original file'}\n📁 ${selectedShip?.name || 'Unknown'}/Class & Flag Cert/Test Report`}
                            onClick={(e) => handleOpenFile(e, report.test_report_file_id)}
                          >
                            📄
                          </span>
                        )}

                        {/* Summary File Icon (📋 blue) */}
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
                    </td>

                    {/* Cell 3: Report Form */}
                    <td className="border border-gray-300 px-4 py-2">
                      {report.report_form || '-'}
                    </td>

                    {/* Cell 4: Test Report No. (monospace font) */}
                    <td className="border border-gray-300 px-4 py-2 font-mono">
                      {report.test_report_no}
                    </td>

                    {/* Cell 5: Issued By */}
                    <td className="border border-gray-300 px-4 py-2">
                      {report.issued_by || '-'}
                    </td>

                    {/* Cell 6: Issued Date */}
                    <td className="border border-gray-300 px-4 py-2">
                      {report.issued_date ? formatDateDisplay(report.issued_date) : '-'}
                    </td>

                    {/* Cell 7: Valid Date (with tooltip) */}
                    <td
                      className="border border-gray-300 px-4 py-2 cursor-help"
                      title={
                        language === 'vi'
                          ? 'Thông tin hạn bảo dưỡng được tính bởi AI có thể gặp sai sót. Vui lòng kiểm tra và sửa lại nếu cần'
                          : 'Valid Date calculated by AI may contain errors. Please verify and correct if needed'
                      }
                    >
                      {report.valid_date ? formatDateDisplay(report.valid_date) : '-'}
                    </td>

                    {/* Cell 8: Status Badge */}
                    <td className="border border-gray-300 px-4 py-2">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          report.status === 'Valid' ? 'bg-green-100 text-green-800' :
                          report.status === 'Expired soon' ? 'bg-yellow-100 text-yellow-800' :
                          report.status === 'Critical' ? 'bg-orange-100 text-orange-800' :
                          report.status === 'Expired' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {report.status}
                      </span>
                    </td>

                    {/* Cell 9: Note (red asterisk *) */}
                    <td className="border border-gray-300 px-4 py-2 text-center">
                      {report.note ? (
                        <span
                          className="text-red-600 cursor-help text-lg font-bold"
                          onMouseEnter={(e) => handleNoteMouseEnter(e, report.note)}
                          onMouseLeave={handleNoteMouseLeave}
                          onClick={(e) => handleNoteClick(e, report)}
                        >
                          *
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
```

---

### 5.14 JSX - Context Menu

```javascript
      {/* ========== CONTEXT MENU ========== */}
      {contextMenu.show && (
        <>
          {/* Overlay to close menu */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setContextMenu({ show: false, x: 0, y: 0, report: null })}
          />

          {/* Menu */}
          <div
            ref={contextMenuRef}
            className="fixed bg-white shadow-xl rounded-lg border border-gray-200 py-2 z-50"
            style={{
              left: `${contextMenu.x}px`,
              top: `${contextMenu.y}px`,
              minWidth: '180px'
            }}
          >
            {selectedReports.size > 1 ? (
              // Multiple Selection - Bulk Delete
              <button
                onClick={handleBulkDelete}
                className="w-full px-4 py-2 text-left hover:bg-red-50 text-gray-700 hover:text-red-600 transition-all flex items-center gap-2 font-medium"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                {language === 'vi' ? `Xóa ${selectedReports.size} mục đã chọn` : `Delete ${selectedReports.size} Selected`}
              </button>
            ) : (
              // Single Selection - Edit + Delete
              <>
                <button
                  onClick={() => handleEdit(contextMenu.report)}
                  className="w-full px-4 py-2 text-left hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  {language === 'vi' ? 'Chỉnh sửa' : 'Edit'}
                </button>

                <button
                  onClick={() => handleDelete(contextMenu.report)}
                  className="w-full px-4 py-2 text-left hover:bg-red-50 text-gray-700 hover:text-red-600 transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  {language === 'vi' ? 'Xóa' : 'Delete'}
                </button>
              </>
            )}
          </div>
        </>
      )}

      {/* ========== NOTE TOOLTIP ========== */}
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
    </div>
  );
};
```

---

## 📝 PHASE 6: MODALS

### 6.1 AddTestReportModal.jsx

**Location**: `/app/frontend/src/components/TestReport/AddTestReportModal.jsx`

**Features**:
- File upload with drag & drop
- AI analysis button
- Auto-fill form fields
- Manual editing
- Background file upload
- Success toast

**Key Implementation Notes**:
- Copy structure from `AddSurveyReportModal.jsx`
- Change field names to match test reports
- Reuse AI analysis logic
- Background file upload after creation

---

### 6.2 EditTestReportModal.jsx

**Location**: `/app/frontend/src/components/TestReport/EditTestReportModal.jsx`

**Features**:
- Pre-filled form
- Edit all fields
- Show existing file links
- Update report

**Key Implementation Notes**:
- Copy structure from `EditSurveyReportModal.jsx`
- Pre-populate with report data
- No file re-upload

---

### 6.3 TestReportNotesModal.jsx

**Location**: `/app/frontend/src/components/TestReport/TestReportNotesModal.jsx`

**Features**:
- View full note
- Edit note
- Save changes

**Key Implementation Notes**:
- Copy structure from `SurveyReportNotesModal.jsx`
- Update API calls to test reports

---

### 6.4 Component Index

**File**: `/app/frontend/src/components/TestReport/index.js`

```javascript
export { TestReportList } from './TestReportList';
export { AddTestReportModal } from './AddTestReportModal';
export { EditTestReportModal } from './EditTestReportModal';
export { TestReportNotesModal } from './TestReportNotesModal';
```

---

## ✅ PHASE 7: TESTING CHECKLIST

### Backend Tests:
- [ ] GET /api/test-reports returns correct data
- [ ] POST /api/test-reports creates report
- [ ] POST /api/test-reports/{id}/upload-files uploads to Drive
- [ ] POST /api/test-reports/analyze-file extracts data
- [ ] PUT /api/test-reports/{id} updates report
- [ ] DELETE /api/test-reports/{id} deletes report + files
- [ ] POST /api/test-reports/bulk-delete works
- [ ] Status calculation is correct

### Frontend Tests:
- [ ] Page loads without errors
- [ ] Table displays with 9 columns
- [ ] 7 columns are sortable (click header)
- [ ] 2 filters work (Status, Search)
- [ ] Clear filters button appears when active
- [ ] Checkbox selection works
- [ ] Select all/none works
- [ ] Context menu opens on right-click
- [ ] Edit button opens modal with data
- [ ] Delete button shows confirmation
- [ ] Bulk delete shows confirmation
- [ ] File icons open Google Drive
- [ ] Note tooltip shows on hover
- [ ] Note click opens modal
- [ ] Status badges show correct colors
- [ ] Empty states display correctly
- [ ] Add button disabled without ship
- [ ] Refresh button works
- [ ] Loading states show

### Integration Tests:
- [ ] Add test report end-to-end
- [ ] AI analysis auto-fills form
- [ ] File upload background task
- [ ] Edit saves and refreshes
- [ ] Delete removes from list
- [ ] Bulk delete removes all
- [ ] Filters update table
- [ ] Sort persists after filter

---

## 📊 SUMMARY: V1 vs V2 CHANGES

### ✅ IDENTICAL TO V1:
- 9 table columns with same order
- 7 sortable columns
- Status badges (green/yellow/orange/red)
- File icons (📄 original, 📋 summary)
- Note indicator (red asterisk *)
- Info icon (ⓘ) on Valid Date
- Context menu (Edit, Delete, Bulk Delete)
- Checkbox selection
- Add/Refresh buttons
- Empty states
- Tooltips
- All CRUD operations

### ❌ REMOVED FROM V1:
- **Valid Date From filter**
- **Valid Date To filter**

### 🔄 MODIFIED FROM V1:
- **Filters section**: 4-column grid → 2-column grid
- **Clear filters check**: 4 filters → 2 filters
- **Architecture**: Monolithic → Component-based

---

## 🚀 READY TO START!

**Estimated Timeline**: 12-16 hours
**Complexity**: Medium (reusing Survey Report patterns)
**Risk**: Low (well-defined scope, existing backend)

