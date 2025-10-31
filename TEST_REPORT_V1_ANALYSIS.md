# TEST REPORT V1 - DETAILED ANALYSIS
**Analyzed from: /app/frontend-v1/src/App.js (lines 15804-16253)**

---

## 1. PAGE HEADER & TITLE
```javascript
<h3 className="text-lg font-semibold text-gray-800">
  {language === 'vi' ? 'Danh sách Báo cáo Test' : 'Test Report List'}
</h3>
```
- **Font**: `text-lg` (18px)
- **Weight**: `font-semibold`
- **Color**: `text-gray-800`

---

## 2. ACTION BUTTONS (Right Side)

### Container
```javascript
<div className="flex gap-3">
```
- **Layout**: Horizontal flex with gap-3 (12px spacing)
- **Position**: Right side of header row
- **Contains**: 2 buttons (Add + Refresh)

### 2.1 Add Button (Green) - "Thêm Báo cáo Test"

#### Active State (When ship is selected)
```javascript
className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all bg-green-600 hover:bg-green-700 text-white cursor-pointer"
```
- **Text Vietnamese**: "Thêm Báo cáo Test"
- **Text English**: "Add Test Report"
- **Padding**: `px-4 py-2` (16px horizontal, 8px vertical)
- **Border radius**: `rounded-lg` (8px)
- **Font**: `text-sm font-medium` (14px, medium weight)
- **Background**: `bg-green-600` (green)
- **Hover**: `hover:bg-green-700` (darker green)
- **Text color**: `text-white`
- **Transition**: `transition-all` (smooth animation)
- **Cursor**: `cursor-pointer`
- **Icon**: Plus sign (➕) - `w-4 h-4` (16px × 16px)
  ```javascript
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
  </svg>
  ```
- **Icon position**: Left side, gap-2 (8px) from text

#### Disabled State (No ship selected)
```javascript
className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all bg-gray-400 cursor-not-allowed text-white"
disabled={!selectedShip}
```
- **Background**: `bg-gray-400` (gray)
- **Cursor**: `cursor-not-allowed`
- **Tooltip**: 
  - VN: "Vui lòng chọn tàu trước"
  - EN: "Please select a ship first"

#### Button Action
```javascript
onClick={() => selectedShip && setShowAddTestReportModal(true)}
```
- Opens "Add Test Report Modal"
- Only triggers if ship is selected

---

### 2.2 Refresh Button (Blue) - "Làm mới"

#### Active State (When ship is selected and not refreshing)
```javascript
className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all bg-blue-600 hover:bg-blue-700 text-white cursor-pointer"
```
- **Text Vietnamese**: "Làm mới"
- **Text English**: "Refresh"
- **Padding**: `px-4 py-2` (16px horizontal, 8px vertical)
- **Border radius**: `rounded-lg` (8px)
- **Font**: `text-sm font-medium` (14px, medium weight)
- **Background**: `bg-blue-600` (blue)
- **Hover**: `hover:bg-blue-700` (darker blue)
- **Text color**: `text-white`
- **Transition**: `transition-all` (smooth animation)
- **Cursor**: `cursor-pointer`

#### Normal Icon (Not loading)
```javascript
<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
</svg>
```
- **Icon**: Refresh/Rotate arrows (🔄)
- **Size**: `w-4 h-4` (16px × 16px)
- **Position**: Left side, gap-2 (8px) from text

#### Loading State (When refreshing)
```javascript
{isRefreshingTestReports ? (
  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
) : (...)}
```
- **Icon**: Spinning loader
- **Animation**: `animate-spin` (continuous rotation)
- **Size**: `h-4 w-4` (16px × 16px)

#### Disabled State (No ship selected OR refreshing)
```javascript
className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all bg-gray-400 cursor-not-allowed text-white"
disabled={!selectedShip || isRefreshingTestReports}
```
- **Background**: `bg-gray-400` (gray)
- **Cursor**: `cursor-not-allowed`
- **Tooltip**: 
  - VN: "Làm mới danh sách" (when enabled)
  - EN: "Refresh list" (when enabled)
  - VN: "Vui lòng chọn tàu trước" (when no ship)
  - EN: "Please select a ship first" (when no ship)

#### Button Action
```javascript
onClick={async () => {
  if (selectedShip && !isRefreshingTestReports) {
    try {
      setIsRefreshingTestReports(true);
      await fetchTestReports(selectedShip.id);
      toast.success(language === 'vi' ? '✅ Đã cập nhật danh sách Test Reports!' : '✅ Test Reports list updated!');
    } catch (error) {
      console.error('Failed to refresh test reports:', error);
      toast.error(language === 'vi' ? '❌ Không thể làm mới danh sách' : '❌ Failed to refresh list');
    } finally {
      setIsRefreshingTestReports(false);
    }
  }
}}
```
- **Action**: Fetches test reports from backend
- **Success toast**: "✅ Đã cập nhật danh sách Test Reports!" / "✅ Test Reports list updated!"
- **Error toast**: "❌ Không thể làm mới danh sách" / "❌ Failed to refresh list"
- **State management**: Sets loading state during fetch

---

## 3. FILTERS SECTION
```javascript
className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-4"
```
- **Container**: White background with border and shadow
- **Layout**: Grid layout `grid-cols-1 md:grid-cols-4 gap-4`

### Filter Controls (4 filters in a row):

#### 3.1 Status Filter (Dropdown)
- **Label**: "Trạng thái" / "Status"
- **Options**: 
  - All / Tất cả
  - Valid / Còn hạn
  - Expired soon / Sắp hết hạn
  - Critical / Khẩn cấp
  - Expired / Hết hạn
- **Class**: `w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500`

#### 3.2 Search Filter (Text Input)
- **Label**: "Tìm kiếm" / "Search"
- **Placeholder**: "Tìm kiếm..." / "Search..."
- **Class**: `w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500`

#### 3.3 Valid Date From (Date Input)
- **Label**: "Hạn từ" / "Valid From"
- **Type**: `type="date"`
- **Class**: `w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500`

#### 3.4 Valid Date To (Date Input)
- **Label**: "Hạn đến" / "Valid To"
- **Type**: `type="date"`
- **Class**: `w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500`

### Clear Filters Button
```javascript
className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-all"
```
- **Text**: "Xóa bộ lọc" / "Clear filters"
- **Position**: Right-aligned (`justify-end`)
- **Visibility**: Only shown when filters are active

---

## 4. TABLE STRUCTURE

### Table Container
```javascript
className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden"
```
- White background with border and shadow
- Rounded corners
- Overflow hidden for proper border radius

### Table Element
```javascript
className="min-w-full"
```

### Table Head
```javascript
className="bg-gray-50 border-b border-gray-200"
```
- Light gray background
- Bottom border

---

## 5. TABLE COLUMNS (9 columns)

### Column 1: Checkbox + No.
```javascript
<th className="border border-gray-300 px-4 py-2 text-left">
  <div className="flex items-center">
    <input type="checkbox" className="w-4 h-4 mr-2" />
    <span>{language === 'vi' ? 'Số TT' : 'No.'}</span>
  </div>
</th>
```
- **Width**: Auto
- **Content**: Checkbox + sequential number
- **Alignment**: Left
- **Features**: Select all checkbox with indeterminate state

### Column 2: Test Report Name ⬆️⬇️ (Sortable)
```javascript
<th className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
    onClick={() => handleTestReportSort('test_report_name')}>
  <div className="flex items-center justify-between">
    <span>{language === 'vi' ? 'Tên Báo cáo Test' : 'Test Report Name'}</span>
    {testReportSort.column === 'test_report_name' && (
      <span className="ml-1 text-blue-600 text-sm font-bold">
        {testReportSort.direction === 'asc' ? '▲' : '▼'}
      </span>
    )}
  </div>
</th>
```
- **Sortable**: Yes (click header to sort)
- **Sort indicator**: Blue triangle (▲ ▼)
- **Cell content**: 
  - Report name text
  - 📄 Green icon (original file link) - clickable, opens Google Drive
  - 📋 Blue icon (summary file link) - clickable, opens Google Drive
- **File icon tooltips**: Show Drive path location

### Column 3: Report Form ⬆️⬇️ (Sortable)
```javascript
<span>{language === 'vi' ? 'Mẫu Báo cáo' : 'Report Form'}</span>
```
- **Sortable**: Yes
- **Content**: Text (e.g., "Form ABC")
- **Default**: "-" if empty

### Column 4: Test Report No. ⬆️⬇️ (Sortable)
```javascript
<span>{language === 'vi' ? 'Số Báo cáo' : 'Test Report No.'}</span>
```
- **Sortable**: Yes
- **Content**: Monospace font (`font-mono`)
- **Style**: `className="border border-gray-300 px-4 py-2 font-mono"`

### Column 5: Issued By ⬆️⬇️ (Sortable)
```javascript
<span>{language === 'vi' ? 'Cấp bởi' : 'Issued By'}</span>
```
- **Sortable**: Yes
- **Content**: Organization name
- **Default**: "-" if empty

### Column 6: Issued Date ⬆️⬇️ (Sortable)
```javascript
<span>{language === 'vi' ? 'Ngày cấp' : 'Issued Date'}</span>
```
- **Sortable**: Yes
- **Content**: Formatted date (`formatDate()`)
- **Default**: "-" if empty

### Column 7: Valid Date ⬆️⬇️ (Sortable) ⓘ
```javascript
<div className="flex items-center gap-1">
  <span>{language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}</span>
  <span className="text-blue-500 cursor-help text-sm" title="..." onClick={(e) => e.stopPropagation()}>
    ⓘ
  </span>
</div>
```
- **Sortable**: Yes
- **Special**: Info icon (ⓘ) with tooltip
- **Tooltip text**: "Valid Date calculated by AI may contain errors. Please verify and correct if needed"
- **Cell has same tooltip**: `cursor-help` on hover
- **Content**: Formatted date
- **Default**: "-" if empty

### Column 8: Status ⬆️⬇️ (Sortable)
```javascript
<span>{language === 'vi' ? 'Trạng thái' : 'Status'}</span>
```
- **Sortable**: Yes
- **Cell content**: Badge with color
```javascript
<span className={`px-2 py-1 rounded-full text-xs font-semibold ${
  report.status === 'Valid' ? 'bg-green-100 text-green-800' :
  report.status === 'Expired soon' ? 'bg-yellow-100 text-yellow-800' :
  report.status === 'Critical' ? 'bg-orange-100 text-orange-800' :
  report.status === 'Expired' ? 'bg-red-100 text-red-800' :
  'bg-gray-100 text-gray-800'
}`}>
  {report.status}
</span>
```
- **Badge styles**:
  - Valid: Green background (bg-green-100 text-green-800)
  - Expired soon: Yellow (bg-yellow-100 text-yellow-800)
  - Critical: Orange (bg-orange-100 text-orange-800)
  - Expired: Red (bg-red-100 text-red-800)
  - Unknown: Gray (bg-gray-100 text-gray-800)

### Column 9: Note (Ghi chú)
```javascript
<th className="border border-gray-300 px-4 py-2 text-center">
  {language === 'vi' ? 'Ghi chú' : 'Note'}
</th>
```
- **Not sortable**
- **Alignment**: Center
- **Cell content**:
  - Red asterisk (*) if note exists
  - "-" if no note
```javascript
{report.note ? (
  <span 
    className="text-red-600 cursor-help text-lg font-bold"
    onMouseEnter={(e) => handleTestReportNoteMouseEnter(e, report.note)}
    onMouseLeave={handleTestReportNoteMouseLeave}
  >
    *
  </span>
) : (
  '-'
)}
```
- **Note indicator**: 
  - Red asterisk (*): `text-red-600 text-lg font-bold`
  - Hover shows tooltip with note content

---

## 6. TABLE ROW BEHAVIOR

### Row Classes
```javascript
className="hover:bg-gray-50 cursor-pointer"
```
- Light gray background on hover
- Cursor pointer to indicate clickable

### Row Events
- **Right-click**: Opens context menu
```javascript
onContextMenu={(e) => handleTestReportContextMenu(e, report)}
```

### Cell Borders
```javascript
className="border border-gray-300 px-4 py-2"
```
- All cells have gray borders
- Padding: `px-4 py-2`

---

## 7. CONTEXT MENU

### Menu Container
```javascript
className="fixed bg-white shadow-xl rounded-lg border border-gray-200 py-2 z-50"
style={{ left: `${x}px`, top: `${y}px`, minWidth: '180px' }}
```

### Menu Options

#### Single Selection (2 options):
1. **Edit** (Blue hover)
```javascript
className="w-full px-4 py-2 text-left hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-all flex items-center gap-2"
```
- Icon: Edit pencil
- Text: "Chỉnh sửa" / "Edit"

2. **Delete** (Red hover)
```javascript
className="w-full px-4 py-2 text-left hover:bg-red-50 text-gray-700 hover:text-red-600 transition-all flex items-center gap-2"
```
- Icon: Trash can
- Text: "Xóa" / "Delete"

#### Multiple Selection (1 option):
**Delete Selected** (Red hover)
```javascript
className="w-full px-4 py-2 text-left hover:bg-red-50 text-gray-700 hover:text-red-600 transition-all flex items-center gap-2 font-medium"
```
- Icon: Trash can
- Text: "Xóa X mục đã chọn" / "Delete X Selected"

---

## 8. NOTE TOOLTIP

### Tooltip Container
```javascript
className="fixed bg-gray-800 text-white p-3 rounded-lg shadow-2xl z-50 border border-gray-600"
style={{
  left: `${x}px`,
  top: `${y}px`,
  width: `${width}px`,
  maxHeight: '200px',
  overflowY: 'auto',
  fontSize: '14px',
  lineHeight: '1.5'
}}
```
- **Background**: Dark gray (bg-gray-800)
- **Text**: White
- **Max height**: 200px with scroll
- **Font size**: 14px
- **Dynamic width**: Based on content

---

## 9. EMPTY STATE

```javascript
<td colSpan="9" className="border border-gray-300 px-4 py-8 text-center text-gray-500">
  {testReports.length === 0 
    ? (language === 'vi' ? 'Chưa có báo cáo test nào' : 'No test reports available')
    : (language === 'vi' ? 'Không có báo cáo test nào phù hợp với bộ lọc' : 'No test reports match the current filters')
  }
</td>
```
- **Spans**: All 9 columns
- **Padding**: Extra vertical padding (py-8)
- **Text**: Gray, centered
- **Messages**:
  - No reports: "Chưa có báo cáo test nào" / "No test reports available"
  - Filtered out: "Không có báo cáo test nào phù hợp với bộ lọc" / "No test reports match the current filters"

---

## 10. SORTING SYSTEM

### Sort State
```javascript
const [testReportSort, setTestReportSort] = useState({
  column: null,
  direction: 'asc'
});
```

### Sortable Columns (7 columns):
1. test_report_name
2. report_form
3. test_report_no
4. issued_by
5. issued_date
6. valid_date
7. status

### Sort Handler
```javascript
const handleTestReportSort = (column) => {
  setTestReportSort(prev => ({
    column,
    direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
  }));
};
```
- Toggle between ascending/descending on same column
- Reset to ascending when switching columns

### Sort Indicator
```javascript
{testReportSort.column === 'column_name' && (
  <span className="ml-1 text-blue-600 text-sm font-bold">
    {testReportSort.direction === 'asc' ? '▲' : '▼'}
  </span>
)}
```
- **Color**: Blue (text-blue-600)
- **Icon**: Triangle (▲ ascending, ▼ descending)
- **Font**: Small, bold

---

## 11. SELECTION SYSTEM

### Checkbox in Header
- Select all / Deselect all
- Indeterminate state when some selected

### Checkbox in Rows
```javascript
<input
  type="checkbox"
  checked={selectedTestReports.has(report.id)}
  onChange={() => handleTestReportSelect(report.id)}
  className="w-4 h-4 mr-3"
  onClick={(e) => e.stopPropagation()}
/>
```
- **Size**: `w-4 h-4`
- **Margin**: `mr-3`
- **Stops propagation**: Prevents row click

---

## 12. FILE ICONS & LINKS

### Original File Icon (📄)
```javascript
<span 
  className="text-green-500 text-xs cursor-pointer hover:text-green-600" 
  title={`${language === 'vi' ? 'File gốc' : 'Original file'}\n📁 ${selectedShip?.name || 'Unknown'}/Class & Flag Cert/Test Report`}
  onClick={(e) => {
    e.stopPropagation();
    window.open(`https://drive.google.com/file/d/${report.test_report_file_id}/view`, '_blank');
  }}
>
  📄
</span>
```
- **Icon**: 📄 (green)
- **Color**: Green (text-green-500, hover: text-green-600)
- **Tooltip**: Shows file path
- **Action**: Opens Google Drive link in new tab

### Summary File Icon (📋)
```javascript
<span 
  className="text-blue-500 text-xs cursor-pointer hover:text-blue-600" 
  title={`${language === 'vi' ? 'File tóm tắt' : 'Summary file'}\n📁 SUMMARY/Class & Flag Document`}
  onClick={(e) => {
    e.stopPropagation();
    window.open(`https://drive.google.com/file/d/${report.test_report_summary_file_id}/view`, '_blank');
  }}
>
  📋
</span>
```
- **Icon**: 📋 (blue)
- **Color**: Blue (text-blue-500, hover: text-blue-600)
- **Tooltip**: Shows summary file path
- **Action**: Opens Google Drive link in new tab

---

## 13. KEY FEATURES SUMMARY

✅ **9 columns** in table
✅ **4 filters** in filter section (Status, Search, Valid Date From, Valid Date To)
✅ **7 sortable columns** with visual indicators
✅ **Checkbox selection** (single + bulk)
✅ **Context menu** (right-click) - Edit / Delete / Bulk Delete
✅ **File icons** with Drive links (original + summary)
✅ **Status badges** with color coding
✅ **Note indicator** (red asterisk *) with tooltip
✅ **Info icon (ⓘ)** on Valid Date column with AI warning
✅ **Hover tooltips** on file icons and note cells
✅ **Empty states** for no data / no filtered results
✅ **Action buttons** (Add + Refresh) with disabled states
✅ **Clear filters** button when filters active

---

## 14. FONT SIZES & STYLING

- **Page title**: `text-lg font-semibold text-gray-800` (18px)
- **Table headers**: Default size, `border border-gray-300 px-4 py-2`
- **Table cells**: Default size, `border border-gray-300 px-4 py-2`
- **Report number**: `font-mono` (monospace font)
- **Status badges**: `text-xs font-semibold` (12px)
- **File icons**: `text-xs` (12px)
- **Note asterisk**: `text-lg font-bold` (18px)
- **Sort indicators**: `text-sm font-bold` (14px)
- **Info icon**: `text-sm` (14px)

---

## 15. COLOR PALETTE

### Primary Colors:
- **Green buttons**: bg-green-600, hover:bg-green-700
- **Blue buttons**: bg-blue-600, hover:bg-blue-700
- **Gray disabled**: bg-gray-400

### Status Colors:
- **Valid**: bg-green-100 text-green-800
- **Expired soon**: bg-yellow-100 text-yellow-800
- **Critical**: bg-orange-100 text-orange-800
- **Expired**: bg-red-100 text-red-800
- **Unknown**: bg-gray-100 text-gray-800

### Text Colors:
- **Headings**: text-gray-800
- **Labels**: text-gray-700
- **Note asterisk**: text-red-600
- **File icons**: text-green-500 (original), text-blue-500 (summary)
- **Sort indicator**: text-blue-600
- **Info icon**: text-blue-500

### Background Colors:
- **Filter section**: bg-white with border
- **Table head**: bg-gray-50
- **Row hover**: hover:bg-gray-50
- **Header hover**: hover:bg-gray-100

---

## 16. NO FEATURES IN V1 (NOT IMPLEMENTED)

❌ No "Showing X / Y reports" count display
❌ No batch processing modal for multiple file uploads
❌ No Add/Edit modal integrated in this section (handled separately)
❌ No inline note editing

---

