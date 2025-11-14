# CREW LIST V1 - Complete Structure Analysis

## 1. TABLE STRUCTURE (12 VISIBLE COLUMNS)

| # | Column Name | Key | Sortable | Special Features |
|---|-------------|-----|----------|------------------|
| 1 | STT (No.) | - | ❌ | **Checkbox** for bulk selection |
| 2 | Full Name (Họ tên) | `full_name` | ✅ | **Double-click** to view certificates, Displays VN/EN name, **UPPERCASE** styling |
| 3 | Sex (Giới tính) | `sex` | ✅ | M/F display |
| 4 | Rank (Chức vụ) | `rank` | ✅ | **Right-click** for quick rank change |
| 5 | Date of Birth (Ngày sinh) | `date_of_birth` | ✅ | Formatted date display |
| 6 | Place of Birth (Nơi sinh) | `place_of_birth` | ✅ | Shows **nationality on hover**, uppercase, VN/EN support |
| 7 | Passport (Hộ chiếu) | `passport` | ✅ | **Right-click** for passport actions, Shows expiry date on hover, **File icons**: 📄 (original), 📋 (summary) |
| 8 | Status (Trạng thái) | `status` | ✅ | **Color-coded badges**: Green (Sign on), Yellow (Standby), Red (Leave) |
| 9 | Ship Sign On (Tàu đăng ký) | `ship_sign_on` | ✅ | Ship name display |
| 10 | Place Sign On (Nơi xuống tàu) | `place_sign_on` | ✅ | Place name |
| 11 | Date Sign On (Ngày xuống tàu) | `date_sign_on` | ✅ | Formatted date |
| 12 | Date Sign Off (Ngày rời tàu) | `date_sign_off` | ✅ | Formatted date |

**Hidden Column (in code but commented out):**
- Seamen Book (Sổ thuyền viên) - with right-click context menu

---

## 2. FILTERS & SEARCH SECTION

### Layout
```
┌─────────────────────────────────────────────────────────────────────┐
│ [Tàu đăng ký: ▼]  [Trạng thái: ▼]  [🔍 Tìm kiếm: _____]  Results  │
└─────────────────────────────────────────────────────────────────────┘
```

### Filter Options

**Ship Sign On Filter:**
- Dropdown with all ships
- Options: "Tất cả" (All), [Ship 1], [Ship 2], ..., "-"
- Backend filtering with API call

**Status Filter:**
- Options: 
  - "Tất cả" (All)
  - "Sign on" → "Đang làm việc" (Working)
  - "Standby" → "Chờ" (Standby)
  - "Leave" → "Nghỉ phép" (On Leave)
- Backend filtering

**Search Field:**
- Placeholder: "Tìm theo tên thuyền viên..." / "Search by crew name..."
- Icon: 🔍
- Real-time frontend search
- Searches in `full_name` and `full_name_en` fields

**Results Count Display:**
```
Hiển thị 15/50 thuyền viên  ✓ 12 đang làm việc
Showing 15/50 crew members  ✓ 12 working
```

---

## 3. ACTION BUTTONS (Header Section)

### Button Layout
```
┌──────────────────────────────────────────────────────────────┐
│  📋 Danh sách thuyền viên công ty                            │
│  Quản lý tất cả thuyền viên của công ty                      │
│                                        [👤 Thêm thuyền viên]  │
│                                        [🔄 Làm mới]           │
└──────────────────────────────────────────────────────────────┘
```

**Add Crew Button (👤 Thêm thuyền viên)**
- Role requirement: `manager`, `admin`, `super_admin`
- Opens Add Crew Modal
- Features: AI passport analysis, batch processing

**Refresh Button (🔄 Làm mới)**
- Refreshes crew list
- Shows success toast

---

## 4. CONTEXT MENUS

### 4.1 ROW CONTEXT MENU (Right-click on row)
**Trigger:** Right-click anywhere on crew row
**Conditions:** User role must be `company_officer`, `manager`, `admin`, or `super_admin`
**Auto-selection:** If crew not selected, automatically adds to selection

**Menu Options:**

```
┌─────────────────────────────────────────┐
│ 2 thuyền viên đã chọn                   │ (if multiple selected)
├─────────────────────────────────────────┤
│ ✏️  Chỉnh sửa thuyền viên               │ (single only)
│ 📍 Chỉnh sửa nơi xuống tàu              │ (bulk supported)
│ 🚢 Chỉnh sửa tàu đăng ký                │ (bulk supported)
│ 📅 Chỉnh sửa ngày lên tàu               │ (bulk supported)
│ 📅 Chỉnh sửa ngày rời tàu               │ (bulk supported)
│ 🗑️  Xóa thuyền viên                     │ (bulk supported)
└─────────────────────────────────────────┘
```

**Special Features:**
- Bulk edit support for: Place Sign On, Ship Sign On, Date Sign On, Date Sign Off
- Delete validation: Cannot delete if crew has certificates
- Viewport boundary checking for menu position

---

### 4.2 PASSPORT CONTEXT MENU (Right-click on passport column)
**Trigger:** Right-click on passport cell
**Condition:** Crew must have passport number
**Event:** `e.stopPropagation()` to prevent row menu

**Menu Options:**

```
┌──────────────────────────────────────────────────┐
│ NGUYEN VAN A - C12345678                         │
├──────────────────────────────────────────────────┤
│ 👁️  Xem file hộ chiếu gốc                  📄   │
│ 📋 Sao chép link file gốc                  🔗   │
│ 📥 Tải xuống file gốc                       💾   │
│ ⚡ Tự động đổi tên file                     ⚡   │
└──────────────────────────────────────────────────┘
```

**Features:**
- **View Passport:** Opens Google Drive file in new tab (supports bulk)
- **Copy Link:** Copies Google Drive link to clipboard (supports bulk)
- **Download:** Downloads passport file (supports bulk)
- **Auto Rename:** Automatically renames passport files to standard format (supports bulk)

**File Indicators in Table:**
- 📄 = Original passport file exists (`passport_file_id`)
- 📋 = Summary file exists (`summary_file_id`)
- Hover shows file location: `[Ship Name]/Passport`

---

### 4.3 RANK CONTEXT MENU (Right-click on rank column)
**Trigger:** Right-click on rank cell
**Event:** `e.stopPropagation()` to prevent row menu

**Menu Display:**

```
┌─────────────────────────────────────┐
│ NGUYEN VAN A - Chọn Rank            │
├─────────────────────────────────────┤
│ • CE    Chief Engineer          ✓   │
│ • 2/E   Second Engineer              │
│ • 3/E   Third Engineer               │
│ • 4/E   Fourth Engineer              │
│ • C/O   Chief Officer                │
│ • 2/O   Second Officer               │
│ • 3/O   Third Officer                │
│ • C/M   Chief Mate                   │
│ • ...   [All rank options]           │
└─────────────────────────────────────┘
```

**Features:**
- Quick rank update without opening edit modal
- Shows checkmark (✓) for current rank
- Scrollable list (max-height: 300px)
- Auto-refreshes crew list after update
- Rank options from `RANK_OPTIONS` constant

**Available Ranks:**
CE, 2/E, 3/E, 4/E, 5/E, ETO, C/O, 2/O, 3/O, 4/O, Master, Bosun, AB, OS, Cook, Messman, Oiler, Wiper, Fitter, Electrician, Pumpman, etc.

---

## 5. ROW INTERACTIONS

### Double-Click Behavior
**Action:** Double-click on crew name
**Result:** Opens Crew Certificates view for that specific crew member
**Tooltip:** "Nhấp đúp để xem chứng chỉ | Chuột phải để xóa thuyền viên"

### Hover Effects
- **Full row:** `hover:bg-gray-50` with cursor pointer
- **Place of Birth cell:** `hover:bg-yellow-50` - shows nationality tooltip
- **Passport cell:** `hover:bg-blue-50` - shows expiry date and file options
- **Rank cell:** `hover:bg-gray-50` - indicates right-click available

### Cell-Specific Features

**Full Name Cell:**
- **Styling:** Uppercase, font-medium
- **Display:** Vietnamese name (default) or English name based on language setting
- **Tooltip:** Shows both VN and EN names
- **Color:** `text-gray-900`

**Passport Cell:**
- **File Icons:** Clickable to open Google Drive directly
- **Tooltip:** Shows passport expiry date and file location
- **Context Menu:** Extensive file management options

**Status Cell:**
- **Badge Styling:**
  - Sign on: `bg-green-100 text-green-800`
  - Standby: `bg-yellow-100 text-yellow-800`
  - Leave: `bg-red-100 text-red-800`
  - Default: `bg-gray-100 text-gray-800`
- **Size:** `text-xs`, `px-2 py-1`, `rounded-full`

---

## 6. BULK SELECTION FEATURES

### Checkbox Selection
- **Header Checkbox:** Select/deselect all filtered crew
- **Row Checkboxes:** Individual crew selection
- **State Management:** `selectedCrewMembers` (Set)

### Bulk Actions Available
1. **Delete Multiple Crew** - with certificate validation
2. **Edit Place Sign On** - for all selected
3. **Edit Ship Sign On** - for all selected  
4. **Edit Date Sign On** - for all selected
5. **Edit Date Sign Off** - for all selected
6. **View Multiple Passports** - opens all in tabs with delay
7. **Copy Multiple Passport Links** - formatted list with names
8. **Download Multiple Passports** - sequential download
9. **Auto-rename Multiple Passport Files** - batch processing

---

## 7. SORTING FUNCTIONALITY

### Sort State
```javascript
const [crewSort, setCrewSort] = useState({
  column: null,
  direction: 'asc'  // 'asc' or 'desc'
});
```

### Sort Icons
- No sort: `-` (neutral)
- Ascending: `▲`
- Descending: `▼`

### Sortable Columns (All 11 data columns)
- Full Name, Sex, Rank, Date of Birth, Place of Birth
- Passport, Status, Ship Sign On, Place Sign On
- Date Sign On, Date Sign Off

### Sort Toggle Behavior
- Click once: Ascending
- Click again: Descending
- Click third time: (continues alternating)

---

## 8. DATA MODEL

### Crew Member Fields
```javascript
{
  id: string (UUID),
  company_id: string (UUID),
  full_name: string (required),
  full_name_en: string (optional),
  sex: string (M/F),
  date_of_birth: datetime (required),
  place_of_birth: string (required),
  place_of_birth_en: string (optional),
  passport: string (required),
  nationality: string (optional),
  rank: string (optional),
  seamen_book: string (optional),
  status: string (default: "Sign on"),
  ship_sign_on: string (default: "-"),
  place_sign_on: string (optional),
  date_sign_on: datetime (optional),
  date_sign_off: datetime (optional),
  passport_issue_date: datetime (optional),
  passport_expiry_date: datetime (optional),
  passport_file_id: string (optional - Google Drive),
  summary_file_id: string (optional - Google Drive),
  created_at: datetime,
  created_by: string,
  updated_at: datetime (optional),
  updated_by: string (optional)
}
```

---

## 9. EMPTY STATE

```
┌─────────────────────────────────────┐
│              👥                     │
│                                     │
│  Không tìm thấy thuyền viên phù hợp │
│  No crew members found              │
│                                     │
│  Thử thay đổi bộ lọc hoặc          │
│  thêm thuyền viên mới               │
│  Try changing filters or            │
│  add new crew members               │
└─────────────────────────────────────┘
```
**Colspan:** 13 columns

---

## 10. STYLING & DESIGN

### Table Container
```css
.bg-white 
.rounded-lg 
.shadow-sm 
.border 
.border-gray-200 
.overflow-hidden
```

### Table Header
```css
.bg-gray-50
.px-3 py-3 (padding)
.text-sm font-bold text-gray-700
.border-r border-gray-200 (column separators)
```

### Table Body Rows
```css
.hover:bg-gray-50
.cursor-pointer
```

### Table Cells
```css
.px-3 py-4 (standard padding)
.px-4 py-4 (wider columns)
.whitespace-nowrap
.text-sm text-gray-900
.border-r border-gray-200
```

---

## 11. SPECIAL FEATURES

### AI-Powered Passport Analysis
- Upload passport → AI extracts data
- Auto-fills: Name, DOB, Passport No, Nationality, etc.
- Supports batch processing of multiple passports

### Batch Processing Modal
- Shows progress: "Processing 3/10 passports..."
- Results modal: Success/Failed count with details
- Error handling for each file

### File Management
- **Automatic Rename:** Standardizes file names to `[Name]_[Passport].pdf`
- **Google Drive Integration:** Direct links and viewing
- **Folder Structure:** `[Company]/[Ship]/Passport/[Files]`

### Delete Protection
- Cannot delete crew with existing certificates
- Shows error: "Cannot delete crew: [Name] ([X] certificates). Please delete all certificates first."

### Bilingual Support
- Vietnamese (default)
- English (toggle in header)
- All UI elements, tooltips, and messages

---

## 12. ROLE-BASED PERMISSIONS

### Add/Edit/Delete Actions
**Allowed Roles:**
- `manager`
- `admin`
- `super_admin`

### Context Menu Access
**Allowed Roles:**
- `company_officer`
- `manager`
- `admin`
- `super_admin`

### View-Only Access
**Allowed Roles:**
- `viewer`
- `crew`

---

## 13. BACKEND API INTEGRATION

### Endpoints Used
```
GET  /api/crew                      - Fetch all crew (with filters)
GET  /api/crew/{crew_id}            - Fetch single crew
POST /api/crew                      - Create crew
PUT  /api/crew/{crew_id}            - Update crew
DELETE /api/crew/{crew_id}          - Delete crew
POST /api/crew/move-files-to-ship   - Move passport files to ship folder
POST /api/crew/{crew_id}/upload-passport-files - Upload passport files
```

### Filtering
```javascript
// Backend filtering via query params
await fetchCrewMembers(ship_sign_on, status);

// Frontend search (real-time)
const filtered = crewList.filter(crew => 
  (crew.full_name?.toLowerCase().includes(search) ||
   crew.full_name_en?.toLowerCase().includes(search))
);
```

---

## 14. KEY STATE MANAGEMENT

```javascript
// Main States
const [crewList, setCrewList] = useState([]);
const [selectedCrewMembers, setSelectedCrewMembers] = useState(new Set());
const [crewSort, setCrewSort] = useState({ column: null, direction: 'asc' });

// Filter States
const [crewFilters, setCrewFilters] = useState({
  ship_sign_on: 'All',
  status: 'All',
  search: ''
});

// Context Menu States
const [crewContextMenu, setCrewContextMenu] = useState({ show: false, x: 0, y: 0, crew: null });
const [passportContextMenu, setPassportContextMenu] = useState({ show: false, x: 0, y: 0, crew: null });
const [rankContextMenu, setRankContextMenu] = useState({ show: false, x: 0, y: 0, crew: null });

// Modal States
const [showAddCrewModal, setShowAddCrewModal] = useState(false);
const [showEditCrewModal, setShowEditCrewModal] = useState(false);
```

---

## 15. MIGRATION NOTES FOR V2

### Components to Create
1. **CrewListTable.jsx** - Main table component
2. **AddCrewModal.jsx** - With AI passport analysis
3. **EditCrewModal.jsx** - Edit crew details
4. **BatchProcessingModal.jsx** - For multiple passport uploads
5. **BatchResultsModal.jsx** - Show upload results
6. **CrewListFilters.jsx** - Filter and search section
7. **CrewContextMenu.jsx** - Row context menu
8. **PassportContextMenu.jsx** - Passport-specific actions
9. **RankContextMenu.jsx** - Quick rank selection

### Services to Create
- `crewService.js` - CRUD operations
- `crewFileService.js` - File operations (upload, rename, etc.)

### Constants to Add
- `RANK_OPTIONS` - List of all maritime ranks
- Crew-related constants

### Key Features to Implement
1. ✅ AI-powered passport analysis (Document AI / Tesseract)
2. ✅ Batch passport processing
3. ✅ Bulk edit operations
4. ✅ Context menus (row, passport, rank)
5. ✅ File management (view, download, copy link, auto-rename)
6. ✅ Google Drive integration
7. ✅ Certificate validation before delete
8. ✅ Bilingual support (VN/EN)
9. ✅ Role-based permissions

---

**Last Updated:** 2025-01-01
**V1 Reference:** `/app/frontend-v1/src/App.js` lines 19100-19900
