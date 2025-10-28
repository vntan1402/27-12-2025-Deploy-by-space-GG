# 🎯 KẾ HOẠCH CHIA NHỎ HOMEPAGE

**File gốc:** `/app/frontend/src/App.js` (HomePage: 23,872 dòng)  
**Mục tiêu:** Chia thành ~15-20 files nhỏ, mỗi file < 300 dòng

---

## 📊 PHÂN TÍCH CẤU TRÚC HOMEPAGE HIỆN TẠI

HomePage chứa **TẤT CẢ** các tính năng của ứng dụng:

| Module | States | Functions | Ước tính dòng |
|--------|--------|-----------|---------------|
| **Crew Management** | 28+ | 15+ | ~3,000 |
| **Crew Certificates** | 30+ | 25+ | ~4,500 |
| **Ship Management** | 19+ | 12+ | ~2,500 |
| **Ship Certificates** | 16+ | 18+ | ~3,000 |
| **Survey Reports** | 28+ | 20+ | ~3,500 |
| **Test Reports** | 26+ | 15+ | ~2,500 |
| **Drawings & Manuals** | 55+ | 26+ | ~2,000 |
| **Other Documents** | 25+ | 48+ | ~2,000 |
| **ISM/ISPS/MLC** | 5+ | 8+ | ~500 |
| **UI & Navigation** | 15+ | 10+ | ~1,000 |

**Tổng:** ~220 states, ~180 functions, ~23,872 dòng

---

## 🏗️ CẤU TRÚC MỚI ĐỀ XUẤT

```
/frontend/src/
├── App.js (giữ lại, chỉ routing & auth - ~200 dòng)
│
├── pages/                          # Các trang chính
│   ├── HomePage.jsx               # Layout tổng (~150 dòng)
│   ├── ShipDocumentsPage.jsx      # Documents tab (~200 dòng)
│   ├── CrewManagementPage.jsx     # Crew tab (~200 dòng)
│   ├── ISMPage.jsx                # ISM tab (~150 dòng)
│   ├── ISPSPage.jsx               # ISPS tab (~150 dòng)
│   ├── MLCPage.jsx                # MLC tab (~150 dòng)
│   ├── SuppliesPage.jsx           # Supplies tab (~150 dòng)
│   └── AccountControlPage.jsx     # Account control (đã có)
│
├── features/                       # Feature modules
│   │
│   ├── ship/                      # Ship Management
│   │   ├── components/
│   │   │   ├── ShipList.jsx       # Ship list table (~150 dòng)
│   │   │   ├── ShipCard.jsx       # Ship info card (~100 dòng)
│   │   │   ├── ShipSelector.jsx   # Ship dropdown (~80 dòng)
│   │   │   └── ShipInfo.jsx       # Ship details view (~120 dòng)
│   │   ├── modals/
│   │   │   ├── AddShipModal.jsx   # Add ship (~200 dòng)
│   │   │   ├── EditShipModal.jsx  # Edit ship (~200 dòng)
│   │   │   └── DeleteShipModal.jsx # Delete ship (~150 dòng)
│   │   ├── hooks/
│   │   │   ├── useShips.js        # Ship CRUD logic (~100 dòng)
│   │   │   └── useShipFilters.js  # Ship filtering (~60 dòng)
│   │   └── services/
│   │       └── shipService.js     # Ship API calls (~80 dòng)
│   │
│   ├── crew/                      # Crew Management
│   │   ├── components/
│   │   │   ├── CrewList.jsx       # Crew list table (~200 dòng)
│   │   │   ├── CrewFilters.jsx    # Crew filters (~100 dòng)
│   │   │   └── CrewCard.jsx       # Crew info card (~80 dòng)
│   │   ├── modals/
│   │   │   ├── AddCrewModal.jsx   # Add crew (~250 dòng)
│   │   │   ├── EditCrewModal.jsx  # Edit crew (~250 dòng)
│   │   │   └── DeleteCrewModal.jsx # Delete crew (~100 dòng)
│   │   ├── hooks/
│   │   │   ├── useCrews.js        # Crew CRUD logic (~120 dòng)
│   │   │   ├── useCrewSort.js     # Crew sorting (~60 dòng)
│   │   │   └── usePassportUpload.js # Passport upload (~150 dòng)
│   │   └── services/
│   │       └── crewService.js     # Crew API calls (~100 dòng)
│   │
│   ├── certificates/              # Ship Certificates
│   │   ├── components/
│   │   │   ├── CertificateList.jsx       # Cert list (~200 dòng)
│   │   │   ├── CertificateCard.jsx       # Cert card (~100 dòng)
│   │   │   ├── CertificateFilters.jsx    # Filters (~120 dòng)
│   │   │   └── CertificateUpload.jsx     # Upload zone (~150 dòng)
│   │   ├── modals/
│   │   │   ├── AddCertificateModal.jsx   # Add cert (~250 dòng)
│   │   │   ├── EditCertificateModal.jsx  # Edit cert (~250 dòng)
│   │   │   └── DuplicateWarningModal.jsx # Duplicate warning (~120 dòng)
│   │   ├── hooks/
│   │   │   ├── useCertificates.js        # Cert CRUD (~120 dòng)
│   │   │   ├── useCertificateAI.js       # AI analysis (~200 dòng)
│   │   │   └── useCertificateUpload.js   # Upload logic (~180 dòng)
│   │   └── services/
│   │       └── certificateService.js     # Cert API (~120 dòng)
│   │
│   ├── crewCertificates/          # Crew Certificates
│   │   ├── components/
│   │   │   ├── CrewCertList.jsx          # Crew cert list (~200 dòng)
│   │   │   ├── CrewCertFilters.jsx       # Filters (~100 dòng)
│   │   │   └── CrewCertCard.jsx          # Cert card (~80 dòng)
│   │   ├── modals/
│   │   │   ├── AddCrewCertModal.jsx      # Add cert (~250 dòng)
│   │   │   ├── EditCrewCertModal.jsx     # Edit cert (~250 dòng)
│   │   │   ├── CrewSelectorModal.jsx     # Select crew (~150 dòng)
│   │   │   └── CertMismatchModal.jsx     # Holder mismatch (~150 dòng)
│   │   ├── hooks/
│   │   │   ├── useCrewCertificates.js    # CRUD logic (~150 dòng)
│   │   │   ├── useCrewCertAI.js          # AI analysis (~200 dòng)
│   │   │   └── useCrewCertUpload.js      # Upload (~180 dòng)
│   │   └── services/
│   │       └── crewCertificateService.js # API calls (~100 dòng)
│   │
│   ├── surveyReports/             # Survey Reports
│   │   ├── components/
│   │   │   ├── SurveyList.jsx            # Survey list (~200 dòng)
│   │   │   ├── SurveyFilters.jsx         # Filters (~100 dòng)
│   │   │   └── SurveyCard.jsx            # Survey card (~80 dòng)
│   │   ├── modals/
│   │   │   ├── AddSurveyModal.jsx        # Add survey (~250 dòng)
│   │   │   ├── EditSurveyModal.jsx       # Edit survey (~250 dòng)
│   │   │   └── SurveyUploadModal.jsx     # Batch upload (~200 dòng)
│   │   ├── hooks/
│   │   │   ├── useSurveyReports.js       # CRUD logic (~120 dòng)
│   │   │   ├── useSurveyAI.js            # AI analysis (~200 dòng)
│   │   │   └── useSurveyUpload.js        # Upload (~150 dòng)
│   │   └── services/
│   │       └── surveyReportService.js    # API calls (~100 dòng)
│   │
│   ├── testReports/               # Test Reports
│   │   ├── components/
│   │   │   ├── TestReportList.jsx        # Test list (~200 dòng)
│   │   │   ├── TestReportFilters.jsx     # Filters (~100 dòng)
│   │   │   └── TestReportCard.jsx        # Test card (~80 dòng)
│   │   ├── modals/
│   │   │   ├── AddTestReportModal.jsx    # Add test (~250 dòng)
│   │   │   ├── EditTestReportModal.jsx   # Edit test (~250 dòng)
│   │   │   └── TestUploadModal.jsx       # Batch upload (~200 dòng)
│   │   ├── hooks/
│   │   │   ├── useTestReports.js         # CRUD logic (~120 dòng)
│   │   │   ├── useTestReportAI.js        # AI analysis (~200 dòng)
│   │   │   └── useTestUpload.js          # Upload (~150 dòng)
│   │   └── services/
│   │       └── testReportService.js      # API calls (~100 dòng)
│   │
│   ├── drawingsManuals/           # Drawings & Manuals
│   │   ├── components/
│   │   │   ├── DrawingsList.jsx          # Drawings list (~200 dòng)
│   │   │   ├── DrawingsFilters.jsx       # Filters (~100 dòng)
│   │   │   └── DrawingsCard.jsx          # Drawing card (~80 dòng)
│   │   ├── modals/
│   │   │   ├── AddDrawingModal.jsx       # Add drawing (~200 dòng)
│   │   │   ├── EditDrawingModal.jsx      # Edit drawing (~200 dòng)
│   │   │   └── DrawingUploadModal.jsx    # Upload (~150 dòng)
│   │   ├── hooks/
│   │   │   ├── useDrawings.js            # CRUD logic (~120 dòng)
│   │   │   └── useDrawingUpload.js       # Upload (~100 dòng)
│   │   └── services/
│   │       └── drawingsService.js        # API calls (~80 dòng)
│   │
│   ├── otherDocuments/            # Other Documents
│   │   ├── components/
│   │   │   ├── OtherDocsList.jsx         # Docs list (~200 dòng)
│   │   │   ├── OtherDocsFilters.jsx      # Filters (~100 dòng)
│   │   │   └── OtherDocsCard.jsx         # Doc card (~80 dòng)
│   │   ├── modals/
│   │   │   ├── AddOtherDocModal.jsx      # Add doc (~200 dòng)
│   │   │   ├── EditOtherDocModal.jsx     # Edit doc (~200 dòng)
│   │   │   └── OtherDocUploadModal.jsx   # Upload (~150 dòng)
│   │   ├── hooks/
│   │   │   ├── useOtherDocs.js           # CRUD logic (~120 dòng)
│   │   │   └── useOtherDocUpload.js      # Upload (~100 dòng)
│   │   └── services/
│   │       └── otherDocsService.js       # API calls (~80 dòng)
│   │
│   └── ism/                       # ISM/ISPS/MLC (similar structure)
│       └── ... (tương tự các features trên)
│
├── components/                    # Shared UI components
│   ├── common/
│   │   ├── Sidebar.jsx            # Navigation sidebar (~150 dòng)
│   │   ├── Header.jsx             # Top header (~100 dòng)
│   │   ├── LoadingSpinner.jsx     # Loading states (~50 dòng)
│   │   ├── EmptyState.jsx         # Empty state UI (~60 dòng)
│   │   ├── ConfirmDialog.jsx      # Confirm actions (~100 dòng)
│   │   ├── SearchBar.jsx          # Search input (~80 dòng)
│   │   └── DatePicker.jsx         # Date picker (~100 dòng)
│   │
│   ├── layout/
│   │   ├── PageLayout.jsx         # Page wrapper (~80 dòng)
│   │   ├── TabLayout.jsx          # Tab container (~100 dòng)
│   │   └── ModalLayout.jsx        # Modal wrapper (~120 dòng)
│   │
│   └── ui/                        # shadcn/ui components (đã có)
│       └── ... (giữ nguyên)
│
├── hooks/                         # Shared custom hooks
│   ├── useAuth.js                 # Auth logic (đã có, cần extract)
│   ├── useFetch.js                # Generic fetch (~80 dòng)
│   ├── useModal.js                # Modal management (~60 dòng)
│   ├── usePagination.js           # Pagination (~80 dòng)
│   ├── useSort.js                 # Sorting logic (~70 dòng)
│   ├── useFilter.js               # Filtering logic (~90 dòng)
│   ├── useFileUpload.js           # File upload (~150 dòng)
│   ├── useBatchProcessing.js      # Batch processing (~200 dòng)
│   └── useToast.js                # Toast notifications (đã có)
│
├── services/                      # API services
│   ├── api.js                     # Axios instance (~100 dòng)
│   ├── authService.js             # Auth APIs (~80 dòng)
│   ├── uploadService.js           # File upload APIs (~100 dòng)
│   └── ... (feature services ở trên)
│
├── utils/                         # Utility functions
│   ├── dateHelpers.js             # Date formatting (~100 dòng)
│   ├── formatters.js              # Data formatters (~80 dòng)
│   ├── validators.js              # Form validation (~100 dòng)
│   ├── constants.js               # Constants (~150 dòng)
│   └── helpers.js                 # General helpers (~100 dòng)
│
└── contexts/                      # React contexts
    ├── AuthContext.jsx            # Auth context (extract từ App.js)
    ├── ShipContext.jsx            # Ship selection (~100 dòng)
    └── LanguageContext.jsx        # Language switching (~80 dòng)
```

---

## 📋 KẾ HOẠCH THỰC HIỆN (PHASED APPROACH)

### 🎯 PHASE 1: Chuẩn bị & Foundation (2 ngày)

#### Step 1.1: Extract Utilities & Helpers
```javascript
// utils/dateHelpers.js
export const formatDateDisplay = (dateValue) => { ... }
export const convertDateInputToUTC = (dateStr) => { ... }
export const parseDateSafely = (dateStr) => { ... }

// utils/formatters.js
export const formatCrewName = (crew) => { ... }
export const getAbbreviation = (fullName) => { ... }
export const removeVietnameseDiacritics = (str) => { ... }

// utils/constants.js
export const RANK_OPTIONS = [ ... ]
export const CERTIFICATE_TYPES = [ ... ]
export const STATUS_OPTIONS = [ ... ]
export const COMMON_CERTIFICATE_NAMES = [ ... ]
```

**Tác động:**
- Giảm ~500 dòng từ HomePage
- Code dễ test và reuse

#### Step 1.2: Setup API Service Layer
```javascript
// services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL,
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;

// services/shipService.js
import api from './api';

export const shipService = {
  getAll: () => api.get('/api/ships'),
  getById: (id) => api.get(`/api/ships/${id}`),
  create: (data) => api.post('/api/ships', data),
  update: (id, data) => api.put(`/api/ships/${id}`, data),
  delete: (id) => api.delete(`/api/ships/${id}`),
};
```

**Tác động:**
- Tách riêng ~141 API calls
- Giảm ~1,000 dòng từ HomePage
- Dễ mock cho testing

#### Step 1.3: Extract Custom Hooks
```javascript
// hooks/useModal.js
export const useModal = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [data, setData] = useState(null);
  
  const open = useCallback((modalData = null) => {
    setData(modalData);
    setIsOpen(true);
  }, []);
  
  const close = useCallback(() => {
    setIsOpen(false);
    setData(null);
  }, []);
  
  return { isOpen, data, open, close };
};

// hooks/useSort.js
export const useSort = (initialColumn = null) => {
  const [sort, setSort] = useState({
    column: initialColumn,
    direction: 'asc'
  });
  
  const handleSort = useCallback((column) => {
    setSort(prev => ({
      column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  }, []);
  
  return { sort, handleSort };
};
```

**Tác động:**
- Replace 23 modal states với useModal()
- Replace duplicate sorting logic với useSort()
- Giảm ~800 dòng từ HomePage

---

### 🎯 PHASE 2: Extract Ship Management (2-3 ngày)

#### Step 2.1: Ship Components
```javascript
// features/ship/components/ShipList.jsx
export const ShipList = ({ ships, onSelectShip, onEdit, onDelete }) => {
  return (
    <div className="ship-list">
      {ships.map(ship => (
        <ShipCard
          key={ship.id}
          ship={ship}
          onSelect={() => onSelectShip(ship)}
          onEdit={() => onEdit(ship)}
          onDelete={() => onDelete(ship)}
        />
      ))}
    </div>
  );
};

// features/ship/hooks/useShips.js
export const useShips = () => {
  const [ships, setShips] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const fetchShips = useCallback(async () => {
    setLoading(true);
    try {
      const response = await shipService.getAll();
      setShips(response.data);
    } catch (error) {
      toast.error('Failed to fetch ships');
    } finally {
      setLoading(false);
    }
  }, []);
  
  const createShip = useCallback(async (data) => {
    try {
      await shipService.create(data);
      toast.success('Ship created successfully');
      await fetchShips();
    } catch (error) {
      toast.error('Failed to create ship');
    }
  }, [fetchShips]);
  
  return { ships, loading, fetchShips, createShip, ... };
};
```

**Files tạo mới:**
- `features/ship/components/ShipList.jsx` (~150 dòng)
- `features/ship/components/ShipCard.jsx` (~100 dòng)
- `features/ship/components/ShipSelector.jsx` (~80 dòng)
- `features/ship/modals/AddShipModal.jsx` (~200 dòng)
- `features/ship/modals/EditShipModal.jsx` (~200 dòng)
- `features/ship/hooks/useShips.js` (~100 dòng)
- `features/ship/services/shipService.js` (~80 dòng)

**Tác động:**
- Giảm ~2,500 dòng từ HomePage
- Ship logic hoàn toàn độc lập

---

### 🎯 PHASE 3: Extract Crew Management (3-4 ngày)

Similar structure như Ship Management, nhưng phức tạp hơn vì có:
- Passport upload
- Batch processing
- More validation logic

**Files tạo mới:**
- ~10 component files
- ~5 modal files
- ~4 hook files
- ~2 service files

**Tác động:**
- Giảm ~3,500 dòng từ HomePage

---

### 🎯 PHASE 4: Extract Certificate Management (3-4 ngày)

Chia thành 2 sub-features:
1. **Ship Certificates** (~3,000 dòng)
2. **Crew Certificates** (~4,500 dòng)

Both have:
- AI analysis
- File upload
- Duplicate detection
- Status tracking

**Tác động:**
- Giảm ~7,500 dòng từ HomePage

---

### 🎯 PHASE 5: Extract Reports (Survey + Test) (3-4 ngày)

Both have similar structure:
- List view with filters
- Add/Edit modals
- Batch upload
- AI analysis

**Tác động:**
- Giảm ~6,000 dòng từ HomePage

---

### 🎯 PHASE 6: Extract Drawings & Other Docs (2-3 ngày)

Simpler modules, mostly CRUD:
- Drawings & Manuals (~2,000 dòng)
- Other Documents (~2,000 dòng)

**Tác động:**
- Giảm ~4,000 dòng từ HomePage

---

### 🎯 PHASE 7: Final Cleanup & Integration (2 ngày)

- Extract remaining ISM/ISPS/MLC
- Create page components
- Update routing
- Final testing

**Tác động:**
- HomePage còn ~150 dòng (chỉ layout)

---

## 📊 TỔNG KẾT

### Metrics So Sánh

| Metric | Trước | Sau | Giảm |
|--------|-------|-----|------|
| **HomePage lines** | 23,872 | ~150 | **99.4%** |
| **Số files** | 1 | ~60 | **+5900%** |
| **Avg lines/file** | 23,872 | ~200 | **99.2%** |
| **States in HomePage** | 220 | ~10 | **95.5%** |
| **Functions in HomePage** | 180 | ~5 | **97.2%** |

### Thời gian ước tính

| Phase | Thời gian | Độ ưu tiên |
|-------|-----------|------------|
| Phase 1: Foundation | 2 ngày | 🔴 Cao nhất |
| Phase 2: Ship | 2-3 ngày | 🔴 Cao |
| Phase 3: Crew | 3-4 ngày | 🔴 Cao |
| Phase 4: Certificates | 3-4 ngày | 🟡 Trung bình |
| Phase 5: Reports | 3-4 ngày | 🟡 Trung bình |
| Phase 6: Drawings/Others | 2-3 ngày | 🟢 Thấp |
| Phase 7: Cleanup | 2 ngày | 🔴 Cao |

**Tổng: 17-24 ngày (3-4 tuần)**

### Lợi ích

✅ Code dễ đọc và maintain  
✅ Mỗi feature độc lập, dễ test  
✅ Performance tốt hơn (lazy loading)  
✅ Team có thể work parallel  
✅ Dễ onboard developers mới  
✅ Dễ add features mới  
✅ Git conflicts giảm 90%  

---

## 🚀 KHUYẾN NGHỊ

### Option 1: Full Refactor (17-24 ngày)
- Làm theo đúng plan trên
- Tất cả phases
- Kết quả tốt nhất

### Option 2: Incremental Refactor (Linh hoạt)
- Bắt đầu Phase 1 (Foundation)
- Chọn 1-2 features refactor trước (Ship + Crew)
- Còn lại làm sau
- **Khuyến nghị: Chọn option này**

### Option 3: Quick Win Approach
- Chỉ làm Phase 1 (2 ngày)
- Extract utils, services, hooks
- HomePage vẫn lớn nhưng clean hơn
- Impact: 40-50% improvement

---

## ✅ HÀNH ĐỘNG TIẾP THEO

**Tôi đề xuất bắt đầu với Option 2:**

1. **Ngay bây giờ: Phase 1 - Foundation (2 ngày)**
   - Extract utilities
   - Setup API services
   - Create custom hooks
   - **Impact: Giảm ~2,300 dòng từ HomePage**

2. **Sau đó: Phase 2 - Ship Management (2-3 ngày)**
   - Test pilot cho refactoring approach
   - Nếu thành công → tiếp tục
   - **Impact: Giảm thêm ~2,500 dòng**

3. **Tiếp theo: Phase 3 - Crew Management (3-4 ngày)**
   - Complex nhất, nhưng high value
   - **Impact: Giảm thêm ~3,500 dòng**

**Sau 3 phases đầu:**
- HomePage giảm từ 23,872 → ~15,600 dòng (35% nhỏ hơn)
- 3 modules lớn nhất đã được tách riêng
- Code structure rõ ràng hơn nhiều

---

**Bạn muốn tôi bắt đầu với Phase nào?** 🚀
