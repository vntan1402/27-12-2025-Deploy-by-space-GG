# Class Survey Report List - Phân Tích Toàn Diện Cấu Trúc & Tính Năng

## 📋 TỔNG QUAN (OVERVIEW)

**Module**: Class Survey Report List  
**File chính**: `/app/frontend/src/components/ClassSurveyReport/ClassSurveyReportList.jsx`  
**Page**: `/app/frontend/src/pages/ClassSurveyReport.jsx`  
**Số dòng code**: 1213 lines (ClassSurveyReportList) + 714 lines (Page)

---

## 🏗️ CẤU TRÚC COMPONENT (COMPONENT STRUCTURE)

### 1. **Page Level** (`ClassSurveyReport.jsx`)

```
ClassSurveyReport Page
├── MainLayout
│   ├── Sidebar (Category Navigation)
│   └── SubMenuBar (SubMenu Navigation)
├── Ship Selection Interface
│   ├── Ship Cards Grid (when no ship selected)
│   └── Ship Selection Modal
├── Ship Detail Panel (when ship selected)
├── ClassSurveyReportList Component ⭐
├── Add Ship Modal
├── Edit Ship Modal
├── Delete Ship Modal
├── Batch Processing Modal
└── Batch Results Modal
```

---

## 📊 TABLE STRUCTURE (CẤU TRÚC BẢNG)

### **Table Headers** (8 columns):

| # | Column | Sortable | Filter | Description |
|---|--------|----------|--------|-------------|
| 1 | **Checkbox** | ❌ | ❌ | Select all/individual reports |
| 2 | **Survey Report Name** | ✅ | ✅ | Tên báo cáo + File icons (📄 📋) |
| 3 | **Report Form** | ✅ | ❌ | Mẫu báo cáo |
| 4 | **Survey Report No** | ✅ | ✅ | Số báo cáo (monospace font) |
| 5 | **Issued Date** | ✅ | ❌ | Ngày cấp (dd/mm/yyyy format) |
| 6 | **Issued By** | ✅ | ✅ | Cấp bởi (abbreviation with tooltip) |
| 7 | **Status** | ✅ | ✅ | Badge: Valid/Expired/Pending |
| 8 | **Note** | ✅ | ✅ | Asterisk (*) if has note, tooltip on hover |

---

## 🔘 ACTION BUTTONS (NÚT CHỨC NĂNG)

### **Top Action Bar** (Lines 696-736):

```jsx
┌──────────────────────────────────────────────────────┐
│ [Title: "Danh sách Báo cáo... for "Ship Name""]     │
│                                                      │
│                    [+ Add Survey Report] [🔄 Refresh]│
└──────────────────────────────────────────────────────┘
```

#### **1. Add Survey Report Button** (Green)
- **Location**: Top right
- **Icon**: ➕ Plus icon
- **Color**: `bg-green-600 hover:bg-green-700`
- **Action**: Opens Add Survey Report Modal
- **Label**: 
  - Vietnamese: "Thêm Survey Report"
  - English: "Add Survey Report"

#### **2. Refresh Button** (Blue)
- **Location**: Top right (next to Add button)
- **Icon**: 🔄 Refresh icon (spins when loading)
- **Color**: `bg-blue-600 hover:bg-blue-700`
- **Action**: Refreshes survey report list
- **States**:
  - Loading: Gray bg, spinning icon, disabled
  - Normal: Blue bg, static icon, enabled
- **Label**:
  - Vietnamese: "Làm mới"
  - English: "Refresh"

---

## 🔍 FILTERS (BỘ LỌC) - Lines 738-800

### **Filter Bar Structure**:

```
┌────────────────────────────────────────────────────────────────┐
│ [Tình trạng: [All ▼]] [Tìm kiếm: [🔍______X]]  [Hiển thị X/Y]│
└────────────────────────────────────────────────────────────────┘
```

### **1. Status Filter** (Dropdown)
- **Label**: "Tình trạng" / "Status"
- **Options**:
  - All (Tất cả)
  - Valid
  - Expired
  - Pending
- **Styling**: Border, rounded, focus ring blue

### **2. Search Filter** (Input với Icon)
- **Label**: "Tìm kiếm" / "Search"
- **Placeholder**: "Tìm theo tên, số..." / "Search by name, number..."
- **Features**:
  - 🔍 Search icon (left side)
  - ❌ Clear button (right side, shows when has text)
  - Width: `w-64` (256px)
  - Searches in:
    - `survey_report_name`
    - `survey_report_no`
    - `issued_by`
    - `note`

### **3. Results Counter** (Right aligned)
- **Format**: "Hiển thị X / Y báo cáo" / "Showing X / Y report(s)"
- **Dynamic**: Updates based on filters
- **Styling**: `text-sm text-gray-600`

---

## 📋 CONTEXT MENU (RIGHT-CLICK MENU) - Lines 1025-1144

### **Context Menu Structure**:

```
┌─────────────────────────────┐
│ [Single Item Actions]       │
│ ├─ 📂 Mở File              │
│ ├─ 📋 Copy Link            │
│ ├─────────────────────────  │
│ ├─ ✏️ Chỉnh sửa           │
│ └─ 🗑️ Xóa                 │
│                             │
│ [OR Bulk Actions]           │
│ ├─ 👁️ Xem file (X báo cáo)│
│ ├─ 📥 Tải xuống (X file)   │
│ ├─ 🔗 Sao chép link (X)    │
│ ├─────────────────────────  │
│ └─ 🗑️ Xóa X báo cáo       │
└─────────────────────────────┘
```

### **Single Item Actions** (selectedReports.size ≤ 1):

#### **1. View File** (Mở File)
- **Icon**: 📂 External link icon
- **Function**: `handleViewFile(report)`
- **Action**: Opens file in new tab
- **Logic**:
  1. Calls backend: `/api/gdrive/file/{file_id}/view`
  2. Gets `view_url` from response
  3. Fallback to direct Google Drive link if error
  4. Opens in new tab: `window.open(url, '_blank')`

#### **2. Copy Link**
- **Icon**: 📋 Copy icon
- **Function**: `handleCopyLink(report)`
- **Action**: Copies file link to clipboard
- **Logic**:
  1. Gets view URL from backend
  2. Copies to clipboard: `navigator.clipboard.writeText(link)`
  3. Shows toast: "Đã copy link"

#### **3. Edit** (Chỉnh sửa)
- **Icon**: ✏️ Edit icon
- **Function**: `handleEditReport(report)`
- **Action**: Opens Edit Survey Report Modal
- **Styling**: Gray text, hover gray-100

#### **4. Delete** (Xóa)
- **Icon**: 🗑️ Trash icon
- **Function**: `handleDeleteReport(report)`
- **Action**: Deletes report with confirmation
- **Styling**: **Red text**, hover red-50 (danger)
- **Logic**:
  1. Shows confirmation dialog
  2. Calls `surveyReportService.bulkDelete([report.id])`
  3. Two notifications:
     - Record deleted from database ✅
     - Files deleted from Google Drive 🗑️ (delayed 1s)
  4. Refreshes list

---

### **Bulk Actions** (selectedReports.size > 1):

#### **1. Bulk View Files** (Xem file)
- **Icon**: 👁️ Eye icon
- **Function**: `handleBulkView()`
- **Label**: "Xem file (X báo cáo)"
- **Action**: Opens multiple files in tabs
- **Logic**:
  - Filters reports with files
  - Opens up to 10 files (browser limit)
  - 100ms delay between opens
  - Shows warning if >10 files

#### **2. Bulk Download** (Tải xuống)
- **Icon**: 📥 Download icon
- **Function**: `handleBulkDownload()`
- **Label**: "Tải xuống (X file)"
- **Action**: Downloads multiple files
- **Logic**:
  1. Shows toast: "📥 Đang tải xuống X file..."
  2. For each report:
     - Fetches from `/api/gdrive/file/{file_id}/download`
     - Creates blob and downloads
     - 300ms delay between downloads
  3. Final toast: "✅ Đã tải xuống X/Y file"

#### **3. Bulk Copy Links** (Sao chép link)
- **Icon**: 🔗 Link icon
- **Function**: `handleBulkCopyLinks()`
- **Label**: "Sao chép link (X file)"
- **Action**: Copies all links to clipboard
- **Format**: 
  ```
  Report Name 1: https://drive.google.com/...
  Report Name 2: https://drive.google.com/...
  ```

#### **4. Bulk Delete** (Xóa)
- **Icon**: 🗑️ Trash icon (RED)
- **Function**: `handleBulkDelete()`
- **Label**: "Xóa X báo cáo đã chọn"
- **Styling**: **Red text**, hover red-50
- **Action**: Deletes multiple reports
- **Logic**:
  1. Shows confirmation
  2. Calls `bulkDelete(reportIds[])`
  3. Shows three notifications:
     - Records deleted count ✅
     - Files deleted count 🗑️
     - Errors count (if any) ⚠️
  4. Clears selection
  5. Refreshes list

---

## ✅ CHECKBOX SELECTION SYSTEM - Lines 180-209

### **Selection Features**:

#### **1. Select All Checkbox** (Header)
- **Location**: First column header
- **States**:
  - ☐ Unchecked: No items selected
  - ☑️ Checked: All items selected
  - ▬ Indeterminate: Some items selected
- **Function**: `handleSelectAll(checked)`
- **Logic**:
  - Checked: Selects all filtered reports
  - Unchecked: Clears all selections

#### **2. Individual Checkboxes** (Each row)
- **Location**: First column of each row
- **Function**: `handleSelectReport(reportId)`
- **Logic**: Toggles report ID in/out of `selectedReports` Set
- **Click handling**: `e.stopPropagation()` to prevent row click

#### **3. Selection State**:
```javascript
const [selectedReports, setSelectedReports] = useState(new Set());
```
- Uses **Set** for O(1) add/remove/check
- Maintains selected report IDs

---

## 📄 TABLE ROW FEATURES

### **Row Structure** (Lines 911-1018):

```
┌──────┬─────────────────┬──────────┬───────┬──────┬────────┬────────┬──────┐
│ [☑ 1]│ Report Name 📄📋│ Form     │ No    │ Date │ Abbrev │ Badge  │  *   │
└──────┴─────────────────┴──────────┴───────┴──────┴────────┴────────┴──────┘
```

### **Column Details**:

#### **1. Checkbox + Index**
- **Content**: Checkbox + Bold index number
- **Layout**: `flex items-center justify-center space-x-2`

#### **2. Survey Report Name + File Icons** ⭐
- **Content**: Report name + Icons
- **Icons**:
  - 📄 **Original File** (Green):
    - Shows if `survey_report_file_id` exists
    - Click to open: Google Drive view
    - Tooltip: "📄 File gốc\n📁 Đường dẫn: {Ship}/Class & Flag Cert/Class Survey Report/"
    - Color: `text-green-500 hover:text-green-600`
  
  - 📋 **Summary File** (Blue):
    - Shows if `survey_report_summary_file_id` exists
    - Click to open: Google Drive view
    - Tooltip: "📋 File tóm tắt (Summary)\n📁 Đường dẫn: ..."
    - Color: `text-blue-500 hover:text-blue-600`

#### **3. Report Form**
- **Content**: `report.report_form` or '-'
- **Styling**: Default text

#### **4. Survey Report No**
- **Content**: `report.survey_report_no` or '-'
- **Styling**: **Monospace font** (`font-mono`)
- **Purpose**: Better readability for report numbers

#### **5. Issued Date**
- **Content**: Date formatted as dd/mm/yyyy
- **Function**: `formatDateDisplay(report.issued_date)`
- **Fallback**: '-' if no date

#### **6. Issued By (Abbreviation)** ⭐
- **Content**: First letters of each word (max 4)
- **Function**: `getAbbreviation(issuedBy)`
- **Styling**: `text-sm font-semibold text-blue-700`
- **Tooltip**: Shows full name on hover
- **Examples**:
  - "Lloyd's Register" → "LR"
  - "Bureau Veritas" → "BV"
  - "American Bureau of Shipping" → "ABS"
  - "Det Norske Veritas" → "DNV"

#### **7. Status Badge** ⭐
- **Content**: Status with color-coded badge
- **Variants**:
  
  | Status | Background | Text | Badge |
  |--------|-----------|------|-------|
  | **Valid** | `bg-green-100` | `text-green-800` | Valid |
  | **Expired** | `bg-red-100` | `text-red-800` | Expired |
  | **Pending** | `bg-yellow-100` | `text-yellow-800` | Pending |
  | **Unknown** | `bg-gray-100` | `text-gray-800` | Unknown |

- **Styling**: `px-2 py-1 rounded text-xs font-medium`

#### **8. Note (Asterisk with Tooltip)** ⭐
- **Content**: 
  - Has note: **Red asterisk** (*)
  - No note: Gray dash (-)
- **Interactive**:
  - **Click**: Opens Notes Modal to view/edit
  - **Hover**: Shows note tooltip
- **Asterisk Styling**: `text-red-600 text-lg font-bold`
- **Tooltip**: Shows full note content on hover
- **Tooltip Position**: Smart positioning to avoid overflow

---

## 💡 NOTE TOOLTIP SYSTEM - Lines 569-614

### **Tooltip Features**:

#### **Smart Positioning**:
```javascript
// Calculates position to avoid viewport overflow
- Checks right edge overflow → aligns to left
- Checks bottom overflow → positions above element
- Minimum padding: 10px from edges
- Max width: 320px
- Position: fixed (viewport coordinates)
```

#### **Tooltip Styling**:
```jsx
className="fixed bg-gray-800 text-white text-sm p-3 rounded-lg shadow-lg z-[100] max-w-xs"
```

#### **Handlers**:
- `handleNoteMouseEnter(e, note)` - Shows tooltip
- `handleNoteMouseLeave()` - Hides tooltip

---

## 🎨 SORTING SYSTEM - Lines 115-131

### **Sortable Columns** (6 out of 8):
1. Survey Report Name
2. Report Form
3. Survey Report No
4. Issued Date (special date handling)
5. Issued By
6. Status
7. Note

### **Sort Functionality**:

#### **Sort State**:
```javascript
const [sort, setSort] = useState({
  column: null,        // Current sort column
  direction: 'asc'     // 'asc' or 'desc'
});
```

#### **Sort Toggle Logic**:
- First click: Sort ascending
- Second click: Sort descending
- Click other column: Sort that column ascending

#### **Sort Indicator** (Icon):
- **Ascending**: ▲ (blue triangle up)
- **Descending**: ▼ (blue triangle down)
- **No sort**: No icon
- **Styling**: `text-blue-600 text-sm font-bold`

#### **Date Sorting**:
```javascript
// Special handling for issued_date
if (sort.column === 'issued_date') {
  aValue = a.issued_date ? new Date(a.issued_date).getTime() : 0;
  bValue = b.issued_date ? new Date(b.issued_date).getTime() : 0;
}
```

---

## 🔄 DATA FLOW & STATE MANAGEMENT

### **Component State** (Lines 17-59):

```javascript
// Data States
surveyReports       // Array of all reports
loading             // Initial load state
isRefreshing        // Refresh action state

// Filter States
filters.status      // 'all', 'valid', 'expired', 'pending'
filters.search      // Search text

// Sort States
sort.column         // Column name or null
sort.direction      // 'asc' or 'desc'

// Selection States
selectedReports     // Set of selected report IDs

// Modal States
showAddModal        // Add Survey Report Modal
showEditModal       // Edit Survey Report Modal
editingReport       // Report being edited
showNotesModal      // Notes Modal
notesReport         // Report with notes open
notesValue          // Note text value

// Context Menu States
contextMenu         // { show, x, y, report }

// Tooltip States
noteTooltip         // { show, x, y, content }
```

---

## 📥 DATA FETCHING - Lines 82-97

### **Fetch Function**:

```javascript
const fetchSurveyReports = async () => {
  if (!selectedShip) return;
  
  try {
    setLoading(true);
    const response = await surveyReportService.getAll(selectedShip.id);
    const data = response.data || response || [];
    setSurveyReports(Array.isArray(data) ? data : []);
  } catch (error) {
    toast.error('Không thể tải danh sách báo cáo');
    setSurveyReports([]);
  } finally {
    setLoading(false);
  }
};
```

### **Trigger Points**:
1. On component mount (with selectedShip)
2. After adding new report
3. After editing report
4. After deleting report(s)
5. After saving notes
6. Manual refresh button click

---

## 🎭 MODALS (CÁC MODAL)

### **1. Add Survey Report Modal** (Lines 1160-1177)
- **Trigger**: "Add Survey Report" button
- **Component**: `<AddSurveyReportModal>`
- **Features**:
  - Single file upload with AI analysis
  - Batch upload mode
  - Manual data entry
- **Callbacks**:
  - `onReportAdded`: Refresh list
  - `onStartBatchProcessing`: Start batch mode

### **2. Edit Survey Report Modal** (Lines 1179-1194)
- **Trigger**: Context menu "Edit" option
- **Component**: `<EditSurveyReportModal>`
- **Props**: `report={editingReport}`
- **Callback**: `onReportUpdated`: Refresh list

### **3. Survey Report Notes Modal** (Lines 1196-1209)
- **Trigger**: Click on note cell (asterisk or dash)
- **Component**: `<SurveyReportNotesModal>`
- **Features**:
  - View full note content
  - Edit note (textarea)
  - Save changes
- **State**: `notesValue` for editing
- **Callback**: `onSave`: Updates report and refreshes

---

## 🎨 LAYOUT & STYLING

### **Top Section** (Action Buttons):
```
┌────────────────────────────────────────────────┐
│ [Title]              [Add Button] [Refresh]    │
└────────────────────────────────────────────────┘
```
- **Layout**: `flex items-center justify-between gap-4`
- **Title**: `text-lg font-semibold text-gray-800`
- **Buttons**: `flex items-center gap-3`

### **Filter Section**:
```
┌────────────────────────────────────────────────┐
│ [Status] [Search]                    [Counter] │
└────────────────────────────────────────────────┘
```
- **Container**: `p-4 bg-gray-50 rounded-lg border`
- **Layout**: `flex gap-4 items-center flex-wrap`
- **Counter**: `ml-auto` (right-aligned)

### **Table Section**:
- **Container**: `overflow-x-auto`
- **Table**: `min-w-full bg-white border border-gray-200 rounded-lg`
- **Header**: `bg-gray-50`
- **Cells**: `border border-gray-300`
- **Row hover**: `hover:bg-gray-50`

---

## 🔔 NOTIFICATIONS (TOAST MESSAGES)

### **Success Messages**:
- ✅ List refreshed
- ✅ Report deleted from database
- 🗑️ Files deleted from Google Drive
- 📄 Opened X files
- 📋 Link copied
- ✅ Downloaded X/Y files
- 🔗 Copied X links
- ✅ Notes saved

### **Warning Messages**:
- ⚠️ No file available
- ⚠️ No reports have attached files
- 📄 Opened first 10 files (browser limit)
- ⚠️ X errors occurred

### **Error Messages**:
- ❌ Failed to load survey reports
- ❌ Failed to refresh
- ❌ Failed to delete report
- ❌ Error opening files
- ❌ Error downloading files
- ❌ Error copying links
- ❌ Failed to save notes

### **Info Messages**:
- 📥 Downloading X files...
- ℹ️ Processing...

---

## 🎯 KEY FEATURES SUMMARY

### **Core Features**:
1. ✅ **Table Display** - 8 columns with rich data
2. ✅ **Sorting** - 6 sortable columns with indicators
3. ✅ **Filtering** - Status + search filters
4. ✅ **Selection** - Checkbox system (all/individual)
5. ✅ **Context Menu** - Right-click actions
6. ✅ **File Icons** - Original (📄) + Summary (📋)
7. ✅ **Abbreviations** - Issued By shortened with tooltip
8. ✅ **Status Badges** - Color-coded (Valid/Expired/Pending)
9. ✅ **Note System** - Asterisk with tooltip + modal
10. ✅ **Refresh** - Manual list refresh

### **Single Item Actions**:
1. 📂 View File
2. 📋 Copy Link
3. ✏️ Edit
4. 🗑️ Delete

### **Bulk Actions** (Multi-select):
1. 👁️ View Files (up to 10)
2. 📥 Download Files
3. 🔗 Copy Links
4. 🗑️ Bulk Delete

### **Advanced Features**:
- Smart tooltip positioning
- Monospace font for report numbers
- File icon indicators
- Abbreviation system
- Date formatting (dd/mm/yyyy)
- Real-time filter results count
- Indeterminate checkbox state
- Empty state messaging
- Loading states

---

## 🔧 TECHNICAL DETAILS

### **Dependencies**:
```javascript
import { useAuth } from '../../contexts/AuthContext';
import { surveyReportService } from '../../services';
import { toast } from 'sonner';
import { formatDateDisplay } from '../../utils/dateHelpers';
```

### **API Endpoints Used**:
1. `GET /api/survey-reports?ship_id={id}` - Get all reports
2. `GET /api/gdrive/file/{file_id}/view` - Get file view URL
3. `GET /api/gdrive/file/{file_id}/download` - Download file
4. `POST /api/survey-reports/bulk-delete` - Delete reports
5. `PUT /api/survey-reports/{id}` - Update report

### **Service Methods**:
- `surveyReportService.getAll(shipId)`
- `surveyReportService.bulkDelete(reportIds)`
- `surveyReportService.update(reportId, data)`

---

## 📊 PERFORMANCE CONSIDERATIONS

### **Optimizations**:
1. **Set for selections**: O(1) add/remove operations
2. **Filtered memoization**: Computed once per render
3. **Debounced search**: (if implemented)
4. **Lazy loading**: (if needed for large lists)
5. **Batch delays**: 100ms (view), 300ms (download) between operations

### **Limits**:
- **Bulk view**: Max 10 files (browser popup blocker)
- **Bulk download**: No hard limit, 300ms delay
- **Bulk copy links**: No limit

---

## 🎨 COLOR SCHEME

### **Button Colors**:
- **Add**: Green (`bg-green-600`)
- **Refresh**: Blue (`bg-blue-600`)
- **Edit**: Gray (`text-gray-700`)
- **Delete**: Red (`text-red-600`)

### **Status Badge Colors**:
- **Valid**: Green (`bg-green-100 text-green-800`)
- **Expired**: Red (`bg-red-100 text-red-800`)
- **Pending**: Yellow (`bg-yellow-100 text-yellow-800`)
- **Unknown**: Gray (`bg-gray-100 text-gray-800`)

### **Icon Colors**:
- **Original File**: Green (`text-green-500`)
- **Summary File**: Blue (`text-blue-500`)
- **Note Asterisk**: Red (`text-red-600`)

---

## ✅ CONCLUSION

Class Survey Report List là một **component phức tạp và đầy đủ tính năng** với:

1. **8 table columns** với sorting, filtering
2. **2 action buttons** (Add, Refresh)
3. **2 filters** (Status dropdown, Search input)
4. **Checkbox selection system** (Select all + individual)
5. **Context menu** với 9 actions (4 single + 5 bulk)
6. **3 modals** (Add, Edit, Notes)
7. **Smart tooltip system** với positioning logic
8. **File management** (View, Download, Copy links)
9. **Rich data display** (Icons, badges, abbreviations)
10. **Comprehensive notifications** (Success, warning, error, info)

**Total functionality**: ~20 distinct features integrated seamlessly.
