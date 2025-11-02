# CREW CERTIFICATE V1 - COMPLETE ANALYSIS

## Overview
This document provides a comprehensive analysis of the Crew Certificate functionality in V1, covering all aspects including layout, features, columns, filters, context menus, and user interactions.

---

## 1. PAGE STRUCTURE & LAYOUT

### Navigation Flow
- **Entry Point**: From Crew List view → Double-click crew name → Opens Crew Certificates view
- **Back Button**: "← Quay lại danh sách thuyền viên" / "← Back to Crew List"
- **Ship Selector**: Hidden in Certificates view (only visible in Crew List view)
- **Ship Information Panel**: Hidden in Certificates view, replaced by Crew Information

### Header Section
```
┌─────────────────────────────────────────────────────────────┐
│ ← Back to Crew List    | Crew Certificates                   │
│                        | Quản lý chứng chỉ thuyền viên      │
├─────────────────────────────────────────────────────────────┤
│ Action Buttons:                                              │
│ • [📜 Add Crew Cert]  [🔄 Refresh]                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. TABLE COLUMNS (11 Total)

### Column Structure (Left to Right):

1. **Checkbox** (Select All)
   - Width: `px-3`
   - Centered alignment
   - Multi-select functionality

2. **STT / No.** (Sequential Number)
   - Width: `px-3`
   - Non-sortable
   - Auto-incremented

3. **Tên thuyền viên / Crew Name** ⬆️⬇️
   - Width: `px-4`
   - **Sortable**
   - Display: Vietnamese name OR English name (based on language toggle)
   - Style: `font-medium uppercase`

4. **Tàu / Trạng thái / Ship / Status** ⬆️⬇️
   - Width: `px-4`
   - **Sortable** (special handling: Standby first, then ships alphabetically)
   - Displays ship name from `crew.ship_sign_on`
   - Style:
     - Standby: `text-orange-600 font-medium`
     - Ship: `text-blue-600`

5. **Chức danh / Rank** ⬆️⬇️
   - Width: `px-4`
   - **Sortable**
   - Display crew rank (e.g., CAPT, C/O, 2/O)

6. **Tên chứng chỉ / Crew Cert Name** ⬆️⬇️
   - Width: `px-4`
   - **Sortable**
   - Includes file status indicators:
     - 📄 (Original file - `crew_cert_file_id`)
     - 📋 (Summary file - `crew_cert_summary_file_id`)
   - Clickable icons open file in Google Drive

7. **Số chứng chỉ / Crew Cert No.** ⬆️⬇️
   - Width: `px-4`
   - **Sortable**

8. **Cơ quan cấp / Issued By** ⬆️⬇️
   - Width: `px-4`
   - **Sortable**
   - Display: **Abbreviation** (first letters of each word)
   - Hover: Shows full organization name
   - Style: `font-medium cursor-help`

9. **Ngày cấp / Issued Date** ⬆️⬇️
   - Width: `px-4`
   - **Sortable**
   - Format: `DD/MM/YYYY`

10. **Ngày hết hạn / Crew Cert Expiry** ⬆️⬇️
    - Width: `px-4`
    - **Sortable**
    - Format: `DD/MM/YYYY`

11. **Trạng thái / Status** ⬆️⬇️
    - Width: `px-3`
    - **Sortable**
    - Badge-style display with color coding:
      - ✅ **Valid** (Còn hạn): `bg-green-100 text-green-800`
      - 🟠 **Critical** (Khẩn cấp): `bg-orange-200 text-orange-900`
      - ⚠️ **Expiring Soon** (Sắp hết hạn): `bg-yellow-100 text-yellow-800`
      - ❌ **Expired** (Hết hạn): `bg-red-100 text-red-800`
      - ❓ **Unknown**: `bg-gray-100 text-gray-800`

12. **Ghi chú / Note**
    - Width: `px-4`
    - Non-sortable
    - Style: `max-w-xs truncate` with full text on hover

---

## 3. FILTERS & SEARCH

### Filter Bar Layout (Single Row)
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 🔍 Search: [____] | Tàu: [Dropdown] | Thuyền viên: [Dropdown] |         │
│                                      Status: [Dropdown] | [Reset] |       │
│                                      Showing 15/50 certificates          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1. **Search Field**
- **Label**: "🔍 Tìm kiếm:" / "🔍 Search:"
- **Placeholder**: "Tên chứng chỉ, số..." / "Cert name, no..."
- **Search Fields**:
  - `cert.crew_name`
  - `cert.cert_name`
  - `cert.cert_no`
  - `cert.issued_by`
- **Width**: `w-64`
- **Type**: Text input with icon

### 2. **Ship Sign On Filter**
- **Label**: "Tàu:" / "Ship:"
- **Options**:
  - "Tất cả" / "All"
  - Dynamic list of ships (from certificates via crew lookup)
  - "Standby" (displayed as "-")
- **Sorting**: Standby first, then ships alphabetically
- **Style**: Dropdown select

### 3. **Crew Name Filter**
- **Label**: "Thuyền viên:" / "Crew:"
- **Options**:
  - "Tất cả" / "All"
  - Dynamic list based on Ship Sign On filter
  - Displays English name if language is EN
- **Dependencies**: Auto-filters crew based on selected ship
- **Auto-reset**: Resets to "all" when ship filter changes
- **Style**: Dropdown select with `max-w-xs`

### 4. **Status Filter**
- **Label**: "Trạng thái:" / "Status:"
- **Options**:
  - "Tất cả" / "All"
  - ✅ "Còn hiệu lực" / "Valid"
  - 🟠 "Khẩn cấp" / "Critical"
  - ⚠️ "Sắp hết hạn" / "Expiring Soon"
  - ❌ "Hết hiệu lực" / "Expired"
  - ❓ "Không xác định" / "Unknown"

### 5. **Reset Filters Button**
- **Label**: "🔄 Xóa bộ lọc" / "🔄 Clear"
- **Visibility**: Only shown when at least one filter is active
- **Action**: Resets all filters to default state

### 6. **Results Count**
- **Format**: "Showing X / Y certificates"
- **Position**: Far right, auto margin-left
- **Style**: Small text with bold numbers

---

## 4. SORTING FUNCTIONALITY

### Sort Icons
- **Unsorted**: No icon
- **Ascending**: `▲` (blue)
- **Descending**: `▼` (blue)

### Sortable Columns (9 total):
1. Crew Name
2. Ship / Status (special logic)
3. Rank
4. Cert Name
5. Cert No
6. Issued By
7. Issued Date
8. Cert Expiry
9. Status

### Special Sorting Logic - Ship/Status Column:
```javascript
if (aShipStatus.isStandby && !bShipStatus.isStandby) {
  comparison = -1; // Standby comes first
} else if (!aShipStatus.isStandby && bShipStatus.isStandby) {
  comparison = 1;
} else {
  comparison = aShipStatus.ship.localeCompare(bShipStatus.ship);
}
```

---

## 5. CONTEXT MENU (Right-Click)

### Trigger
- Right-click on any certificate row

### Menu Options:

#### Option 1: **Edit Certificate** ✏️
- Opens Edit Modal
- Pre-fills all fields with current certificate data

#### Option 2: **Delete Certificate** 🗑️
- Shows confirmation dialog
- Confirmation message includes:
  - Crew name
  - Certificate name
  - Warning: "⚠️ This action cannot be undone!"

#### Option 3: **View Original File** 👁️
- Opens certificate file in Google Drive (new tab)
- Only visible if `crew_cert_file_id` exists

#### Option 4: **View Summary File** 📋
- Opens summary file in Google Drive (new tab)
- Only visible if `crew_cert_summary_file_id` exists

#### Option 5: **Copy File Link** 🔗
- Copies Google Drive link to clipboard
- Shows toast notification on success

#### Option 6: **Download File** 📥
- Downloads certificate file
- Shows download progress

#### Option 7: **Auto Rename File** ⚡ (Bulk Option)
- **Single Certificate**: Renames current certificate file
- **Multiple Selected**: Renames all selected certificate files
- **Format**: `Rank_PersonName_CertificateName.pdf`
  - Example: `CAPT_Vu Ngoc Tan_Certificate of Competency.pdf`
- **Confirmation Dialog**: Shows preview of new filenames
- **Note**: "⚠️ This action cannot be undone!"

---

## 6. ROW INTERACTIONS

### 1. **Checkbox Selection**
- Click checkbox to select/deselect
- Visual feedback: Row background changes to `bg-blue-50`
- Multi-select enabled

### 2. **Right-Click Context Menu**
- Opens context menu at cursor position
- Works with both single and multiple selections

### 3. **File Icons**
- **📄 Icon**: Click to open original certificate file
- **📋 Icon**: Click to open summary file
- Hover shows file location tooltip

### 4. **Hover Effect**
- Row background: `hover:bg-gray-50`

---

## 7. BUTTONS & ACTIONS

### Top Action Buttons

#### 1. **Add Crew Cert Button** 📜
- **Label**: "Thêm chứng chỉ thuyền viên" / "Add Crew Cert"
- **Permissions**: manager, admin, super_admin only
- **Action**: Opens Add Certificate Modal
- **Style**: Blue primary button

#### 2. **Refresh Button** 🔄
- **Label**: "Làm mới" / "Refresh"
- **Action**: Fetches all certificates from API
- **Style**: Gray secondary button

### Select All Checkbox
- Located in table header
- Selects/deselects all **filtered** certificates
- Checked state depends on whether all visible items are selected

---

## 8. ADD CERTIFICATE MODAL

### Modal Structure

#### Header Section
```
┌─────────────────────────────────────────────────────────────┐
│ 📜 Thêm chứng chỉ thuyền viên        [─] [×]                │
│ Thuyền viên: VŨ NGỌC TÂN (C1571189)                         │
└─────────────────────────────────────────────────────────────┘
```

### Features:
1. **Minimize Button** (─): Minimizes modal to taskbar icon
2. **Close Button** (×): Closes modal with confirmation if data exists

### Content Sections

#### Section 1: From Certificate File (AI Analysis) 📄
- **Drag & Drop Area**:
  - Border: Blue dashed
  - Accepts: PDF, JPG, PNG (max 10MB)
  - Text: "Kéo thả file hoặc click để chọn"
- **AI Analysis Progress**:
  - Shows spinning loader during analysis
  - Displays extracted data with ✅ icons
  - Error handling with detailed messages

#### Section 2: Crew Selection (if no crew pre-selected)
- **Dropdown**: Select crew from list
- **Search**: Filter crew by name
- **Display**: Shows crew name, passport, rank
- **Auto-fill**: Populates crew-related fields

#### Section 3: Certificate Details (Manual Entry / AI Auto-fill)
- **Fields**:
  1. Crew Name (Vietnamese) *
  2. Crew Name (English)
  3. Passport *
  4. Rank
  5. Date of Birth
  6. Certificate Name * (with dropdown suggestions)
  7. Certificate Number *
  8. Issued By
  9. Issued Date
  10. Certificate Expiry
  11. Note (textarea)

### Certificate Name Dropdown
- **Common Names** (28 options):
  - Certificate of Competency (COC)
  - Certificate of Endorsement (COE)
  - Seaman Book for COC
  - GMDSS Certificate
  - Medical Certificate
  - Basic Safety Training
  - Advanced Fire Fighting
  - Ship Security Officer
  - And 20+ more...
- **Custom Names**: User can add new names (saved to localStorage)
- **Search**: Filter names by typing

### Validation
- **Required Fields** marked with (*)
- **Duplicate Check**: Checks for existing certificate with same `crew_id` + `cert_no`
- **Certificate Holder Mismatch**:
  - AI extracts holder name from certificate
  - Compares with selected crew
  - Shows warning if mismatch detected
- **Date of Birth Mismatch**:
  - AI extracts DOB from certificate
  - Compares with crew DOB
  - Shows confirmation dialog if mismatch

### Submit Action
1. Validates required fields
2. Checks for duplicates
3. Creates certificate in database
4. Uploads files to Google Drive (background)
5. Shows success/error toast
6. Refreshes certificate list

---

## 9. EDIT CERTIFICATE MODAL

### Similar to Add Modal with differences:
- **Title**: "Chỉnh sửa chứng chỉ thuyền viên" / "Edit Crew Certificate"
- **Pre-filled**: All fields populated with existing data
- **File Upload**: Optional (can keep existing files or replace)
- **Save Button**: "Lưu thay đổi" / "Save Changes"

---

## 10. BATCH UPLOAD FUNCTIONALITY

### Trigger
- User selects multiple certificate files
- Automatic batch processing starts

### Progress Modal
```
┌─────────────────────────────────────────────────────────────┐
│ 📤 Đang xử lý hàng loạt...                   [─] [×]        │
├─────────────────────────────────────────────────────────────┤
│ File hiện tại: certificate_001.pdf                          │
│ Tiến độ: 3/10 files                                         │
├─────────────────────────────────────────────────────────────┤
│ ✅ certificate_001.pdf - Completed                          │
│ ⏳ certificate_002.pdf - Processing                         │
│ ⏳ certificate_003.pdf - Waiting                            │
│ ...                                                          │
└─────────────────────────────────────────────────────────────┘
```

### Features:
- **Individual File Progress**: Each file shows status icon
- **Smooth Progress Bar**: 0-100% for current file
- **Stagger Delay**: 300ms between files
- **Status Icons**:
  - ⏳ Waiting
  - 🔄 Processing
  - ✅ Completed
  - ❌ Error

### Results Modal
Shows summary after completion:
- **Success Count**: Number of successful uploads
- **Error Count**: Number of failed uploads
- **Duplicate Count**: Number of duplicate certificates
- **Details Table**: Filename, Status, Cert Name, Cert No, Error Message

---

## 11. FILE MANAGEMENT

### File Structure in Google Drive
```
Company Root
└── Ship Name
    └── Crew Records
        └── Certificates
            ├── Crew_Name
            │   ├── Certificate_Name.pdf (Original)
            │   └── Certificate_Name_Summary.txt
            └── ...
```

### File Naming Convention
**Auto-Rename Format**: `Rank_PersonName_CertificateName.pdf`
- **Rank**: No spaces, no special chars (e.g., `CAPT`, `CO`, `2O`)
- **PersonName**: English name, keep spaces
- **CertificateName**: Keep spaces
- **Separator**: Underscore `_` between main parts only

**Examples**:
- `CAPT_Vu Ngoc Tan_Certificate of Competency.pdf`
- `CO_Nguyen Van A_GMDSS Certificate.pdf`
- `2O_Tran Thi B_Basic Safety Training.pdf`

### File Indicators in Table
- **📄**: Original certificate file exists
- **📋**: Summary file exists
- **Tooltip**: Shows file location on hover
- **Click**: Opens file in Google Drive

---

## 12. KEY FEATURES

### 1. **Multi-Language Support**
- English / Vietnamese toggle
- All UI elements translated
- Displays English crew names when EN is selected

### 2. **AI-Powered Analysis**
- Automatic data extraction from certificate files
- Extracts: Crew name, cert name, cert no, issued by, dates, DOB, rank
- Validation: Certificate holder matching
- Error handling for failed analysis

### 3. **Duplicate Prevention**
- Checks `crew_id` + `cert_no` combination
- Shows existing certificate details if duplicate found
- Option to skip or update

### 4. **Certificate Holder Validation**
- AI extracts holder name from certificate
- Compares with selected crew
- Shows warning dialog if mismatch
- User can proceed or cancel

### 5. **Status Auto-Calculation**
- **Valid**: More than 90 days remaining
- **Critical**: 30-60 days remaining
- **Expiring Soon**: 60-90 days remaining
- **Expired**: Past expiry date
- **Unknown**: No expiry date

### 6. **Crew-Certificate Relationship**
- Ship association via `crew.ship_sign_on`
- Standby crew handling (ship_sign_on = "-")
- Dynamic filtering by ship

### 7. **Bulk Operations**
- Multi-select with checkboxes
- Bulk delete (with confirmation)
- Bulk auto-rename files
- Bulk file download

### 8. **Abbreviation Display**
- Issued By column shows abbreviations
- Hover to see full organization name
- Algorithm: First letter of each word

---

## 13. STYLING & DESIGN

### Color Scheme
- **Primary**: Blue (`#2563eb`)
- **Success**: Green (`#10b981`)
- **Warning**: Yellow (`#fbbf24`)
- **Danger**: Red (`#ef4444`)
- **Critical**: Orange (`#f59e0b`)
- **Gray**: Various shades for borders, backgrounds

### Typography
- **Headers**: Bold, larger font
- **Table Headers**: Bold, uppercase
- **Crew Names**: Uppercase
- **Dates**: Regular weight

### Borders & Spacing
- **Table Borders**: `border-r border-gray-200` between columns
- **Row Padding**: `px-3` to `px-4`, `py-4`
- **Modal Padding**: `p-6`
- **Section Gaps**: `space-y-4`, `space-x-2`

### Responsive Design
- **Filters**: Flex wrap for smaller screens
- **Table**: Horizontal scroll on overflow
- **Modal**: Max-width constraints, vertical scroll

---

## 14. API ENDPOINTS USED

### Certificate Operations
- `GET /api/crew-certificates/all` - Fetch all certificates
- `GET /api/crew-certificates/all?crew_id={id}` - Fetch by crew
- `POST /api/crew-certificates/manual?ship_id={id}` - Create certificate
- `PUT /api/crew-certificates/{id}` - Update certificate
- `DELETE /api/crew-certificates/{id}` - Delete certificate
- `POST /api/crew-certificates/check-duplicate` - Check duplicate
- `POST /api/crew-certificates/{id}/upload-files` - Upload files
- `POST /api/crew-certificates/{id}/auto-rename-file` - Auto rename

### AI Analysis
- `POST /api/crew-certificates/analyze-file` - Analyze certificate file

---

## 15. STATE MANAGEMENT

### Key State Variables
```javascript
// View State
const [showCertificatesView, setShowCertificatesView] = useState(false);
const [selectedCrewForCertificates, setSelectedCrewForCertificates] = useState(null);

// Data State
const [crewCertificates, setCrewCertificates] = useState([]);
const [crewList, setCrewList] = useState([]);

// Filter State
const [certificatesSearch, setCertificatesSearch] = useState('');
const [certFilters, setCertFilters] = useState({
  shipSignOn: 'all',
  status: 'all',
  crewName: 'all'
});

// Sort State
const [certificateSort, setCertificateSort] = useState({
  column: null,
  direction: 'asc'
});

// Selection State
const [selectedCrewCertificates, setSelectedCrewCertificates] = useState(new Set());

// Modal State
const [showAddCrewCertModal, setShowAddCrewCertModal] = useState(false);
const [showEditCrewCertModal, setShowEditCrewCertModal] = useState(false);
const [isAddCrewCertModalMinimized, setIsAddCrewCertModalMinimized] = useState(false);

// Context Menu State
const [certContextMenu, setCertContextMenu] = useState({
  show: false,
  x: 0,
  y: 0,
  cert: null
});

// File Upload State
const [certFile, setCertFile] = useState(null);
const [isAnalyzingCert, setIsAnalyzingCert] = useState(false);
const [certAnalysis, setCertAnalysis] = useState(null);

// Batch Processing State
const [isBatchProcessingCerts, setIsBatchProcessingCerts] = useState(false);
const [certBatchProgress, setCertBatchProgress] = useState({ current: 0, total: 0 });
const [certBatchResults, setCertBatchResults] = useState([]);
```

---

## 16. USER PERMISSIONS

### Role-Based Access
- **Viewer (Crew)**: View only
- **Editor (Ship Officer)**: View only
- **Manager (Company Officer)**: View, Add, Edit
- **Admin**: View, Add, Edit, Delete
- **Super Admin**: Full access

### Button Visibility
- **Add Crew Cert**: manager, admin, super_admin only
- **Edit**: manager, admin, super_admin only
- **Delete**: admin, super_admin only

---

## 17. NOTIFICATIONS (Toast Messages)

### Success Messages
- "✅ Certificate added successfully!"
- "✅ Certificate updated!"
- "✅ Certificate deleted!"
- "✅ File copied to clipboard!"
- "✅ Automatically renamed X file(s)!"

### Error Messages
- "❌ Failed to add certificate"
- "❌ Failed to load certificates"
- "❌ File analysis failed"
- "❌ Duplicate certificate detected"

### Warning Messages
- "⚠️ Certificate holder mismatch"
- "⚠️ Date of birth mismatch"
- "⚠️ No certificates selected"

### Info Messages
- "ℹ️ Modal minimized. Click icon below to restore."
- "ℹ️ Batch processing started..."

---

## SUMMARY

The V1 Crew Certificate module is a comprehensive, feature-rich system with:
- **11-column table** with extensive sorting and filtering
- **AI-powered certificate analysis** for automatic data extraction
- **Batch upload** with progress tracking
- **Context menu** with 7+ actions
- **Multi-language support** (EN/VI)
- **Role-based permissions**
- **Advanced file management** with auto-rename
- **Duplicate prevention** and validation
- **Responsive design** with modern UI/UX

All features are tightly integrated with the existing crew management system, Google Drive storage, and AI analysis capabilities.
