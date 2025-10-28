# 🔍 ĐÁNH GIÁ & PHÂN TÍCH FRONTEND CODE

**Ngày phân tích:** $(date +%Y-%m-%d)  
**File chính:** `/app/frontend/src/App.js`  
**Tổng số dòng:** 33,150 dòng

---

## 📊 TÓM TẮT TỔNG QUAN

### ⚠️ VẤN ĐỀ NGHIÊM TRỌNG

**File App.js có 33,150 dòng code** - Đây là một **MONOLITHIC GIANT** với các vấn đề nghiêm trọng:

| Metric | Giá trị | Đánh giá | Tiêu chuẩn industry |
|--------|---------|----------|---------------------|
| **Tổng dòng code** | 33,150 | 🔴 Cực kỳ cao | < 300 dòng/file |
| **State variables** | 298 | 🔴 Quá nhiều | < 10/component |
| **useState hooks** | 299 | 🔴 Quá nhiều | < 15/component |
| **useEffect hooks** | 33 | 🟡 Cao | < 5/component |
| **Functions** | 287 | 🔴 Quá nhiều | < 20/component |
| **API calls** | 144 | 🔴 Quá nhiều | Nên tách riêng |
| **Modal states** | 23 | 🔴 Quá nhiều | < 5/component |

---

## 🏗️ CẤU TRÚC HIỆN TẠI

### Các Components Chính

| Component | Dòng bắt đầu | Số dòng | % của file | Trạng thái |
|-----------|-------------|---------|------------|------------|
| **HomePage** | 881 | **23,872** | **72%** | 🔴 Quá lớn |
| **AccountControlPage** | 24,756 | 2,111 | 6.4% | 🟡 Lớn |
| **AIConfigModal** | 27,911 | 461 | 1.4% | 🟢 OK |
| **EditUserModal** | 28,771 | 493 | 1.5% | 🟢 OK |
| **GoogleDriveModal** | 26,870 | 436 | 1.3% | 🟢 OK |
| **CompanyGoogleDriveModal** | 27,309 | 433 | 1.3% | 🟢 OK |
| **LoginPage** | 511 | 284 | 0.9% | 🟢 OK |
| **AddUserModal** | 29,267 | 247 | 0.7% | 🟢 OK |
| **PermissionModal** | 27,745 | 163 | 0.5% | 🟢 OK |
| **AuthProvider** | 223 | 128 | 0.4% | 🟢 OK |

### 🎯 Vấn đề chính: **HomePage chiếm 72% của toàn bộ file (23,872 dòng)**

---

## 🔍 PHÂN TÍCH TÍNH NĂNG

Hệ thống quản lý **10 modules chính**, tất cả được nhồi nhét trong 1 file:

| Tính năng | Mentions | State vars | Độ phức tạp |
|-----------|----------|------------|-------------|
| **Crew Management** | 2,633 | 28 | 🔴 Cao nhất |
| **Ship Management** | 2,021 | 19 | 🔴 Cao |
| **Certificate Management** | 1,598 | 16 | 🟡 Trung bình |
| **Survey Reports** | 1,067 | 28 | 🟡 Trung bình |
| **Drawings & Manuals** | 1,049 | 55 | 🔴 Cao |
| **Google Drive** | 470 | 10 | 🟢 Thấp |
| **Test Reports** | 452 | 26 | 🟡 Trung bình |
| **Authentication** | 251 | 1 | 🟢 Thấp |
| **ISM/ISPS/MLC** | 222 | 5 | 🟢 Thấp |
| **AI Processing** | 130 | 0 | 🟢 Thấp |

---

## 🔄 CODE LẶP LẠI (Code Duplication)

**Các pattern lặp lại nhiều lần:**

| Pattern | Số lần | Vấn đề |
|---------|--------|--------|
| `handleAdd*` functions | 9 | 🔴 Nên dùng generic hook |
| `handleUpdate*` functions | 7 | 🔴 Nên dùng generic hook |
| `handleDelete*` functions | 14 | 🔴 Nên dùng generic hook |
| `fetch*` functions | 23 | 🔴 Nên tách API service layer |
| Modal state patterns | 23 | 🔴 Nên dùng modal manager |

**API Calls phân tán:**
- GET: 31 | POST: 79 | PUT: 18 | DELETE: 13
- **Tổng: 141 API calls** trải khắp file

---

## ⚠️ VẤN ĐỀ CỤ THỂ

### 1. 🔴 **Monolithic Architecture (Kiến trúc Nguyên khối)**

**Vấn đề:**
- 1 file duy nhất chứa toàn bộ ứng dụng (33,150 dòng)
- HomePage chiếm 72% file (23,872 dòng)
- Không thể maintain, debug, hoặc test độc lập
- Thời gian compile và hot-reload chậm

**Tác động:**
- ❌ Khó đọc và hiểu code
- ❌ Khó tìm bugs
- ❌ Khó onboard developers mới
- ❌ Performance issues khi load/compile
- ❌ Git conflicts liên tục khi nhiều người làm việc

### 2. 🔴 **State Management Chaos (Quản lý state hỗn loạn)**

**Vấn đề:**
- 299 useState hooks trong 1 file
- 298 state variables
- Không có central state management
- State logic trải khắp component

**Ví dụ state variables:**
```javascript
// Crew states
const [crews, setCrews] = useState([])
const [selectedCrew, setSelectedCrew] = useState(null)
const [showAddCrewModal, setShowAddCrewModal] = useState(false)
// ... +25 crew-related states

// Ship states  
const [ships, setShips] = useState([])
const [selectedShip, setSelectedShip] = useState(null)
const [showAddShipModal, setShowAddShipModal] = useState(false)
// ... +19 ship-related states

// Certificate states
// ... +16 certificate states

// Survey Report states
// ... +28 survey states

// Test Report states
// ... +26 test report states
```

**Tác động:**
- ❌ Khó track state changes
- ❌ State inconsistencies
- ❌ Props drilling hell
- ❌ Re-render performance issues
- ❌ Khó debug state-related bugs

### 3. 🔴 **No Separation of Concerns (Không tách biệt logic)**

**Tất cả mix lộn trong 1 file:**
- ✗ UI Components
- ✗ Business Logic  
- ✗ API Calls
- ✗ State Management
- ✗ Form Handling
- ✗ Validation Logic
- ✗ Data Formatting
- ✗ Error Handling

### 4. 🔴 **Code Duplication (Code lặp lại quá nhiều)**

**Ví dụ patterns lặp lại:**

```javascript
// Pattern 1: Fetch data (lặp 23 lần)
const fetchCrews = async () => { /* ... */ }
const fetchShips = async () => { /* ... */ }
const fetchCertificates = async () => { /* ... */ }
// ... +20 fetch functions tương tự

// Pattern 2: Add handlers (lặp 9 lần)
const handleAddCrew = async () => { /* ... */ }
const handleAddShip = async () => { /* ... */ }
const handleAddCertificate = async () => { /* ... */ }
// ... +6 add handlers tương tự

// Pattern 3: Modal states (lặp 23 lần)
const [showAddCrewModal, setShowAddCrewModal] = useState(false)
const [showEditCrewModal, setShowEditCrewModal] = useState(false)
const [showAddShipModal, setShowAddShipModal] = useState(false)
// ... +20 modal states tương tự
```

### 5. 🔴 **No API Layer (Không có tầng API riêng)**

**Vấn đề:**
- 141 axios calls trải khắp component
- API endpoints hardcoded everywhere
- Không có error handling tập trung
- Không có request/response interceptors
- Không có caching strategy

**Ví dụ:**
```javascript
// API calls scattered everywhere in component
const fetchData = async () => {
  const response = await axios.get(`${API_URL}/api/crews`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  // ...
}

// Repeated 141 times với slight variations
```

### 6. 🟡 **Performance Issues (Vấn đề hiệu năng)**

**Vấn đề:**
- Không có useMemo (0 lần sử dụng)
- Không có useCallback (0 lần sử dụng)
- 33 useEffect hooks có thể gây re-render cascades
- Massive component re-renders do 299 states

### 7. 🟡 **No Type Safety (Không có type safety)**

**Vấn đề:**
- Pure JavaScript, không có TypeScript
- Không có PropTypes
- Runtime errors khó catch
- IDE autocomplete kém

---

## 🎯 KẾ HOẠCH TÁI CẤU TRÚC (REFACTORING PLAN)

### 📋 PHASE 1: Chuẩn bị & Phân tích (1-2 ngày)

**Mục tiêu:** Hiểu rõ dependencies và tách biệt concerns

#### 1.1. Tạo dependency map
```bash
# Phân tích các dependencies giữa các phần code
- Liệt kê tất cả state variables và nơi chúng được dùng
- Xác định shared logic vs feature-specific logic
- Map ra API calls theo feature
```

#### 1.2. Thiết lập kiến trúc mới
```
/src
├── components/         # UI Components
│   ├── common/        # Shared components
│   ├── crew/          # Crew management components
│   ├── ship/          # Ship management components
│   ├── certificate/   # Certificate components
│   ├── survey/        # Survey report components
│   ├── test/          # Test report components
│   └── drawings/      # Drawings & manuals components
│
├── features/          # Feature modules (slice pattern)
│   ├── auth/
│   ├── crew/
│   ├── ship/
│   ├── certificate/
│   ├── survey/
│   ├── test/
│   └── drawings/
│
├── hooks/             # Custom hooks
│   ├── useAuth.js
│   ├── useFetch.js
│   ├── useModal.js
│   └── useForm.js
│
├── services/          # API layer
│   ├── api.js         # Axios instance
│   ├── crewService.js
│   ├── shipService.js
│   └── ...
│
├── store/             # State management
│   ├── slices/        # Redux slices (hoặc Context)
│   └── index.js
│
├── utils/             # Utility functions
│   ├── dateHelpers.js
│   ├── formatters.js
│   └── validators.js
│
└── App.js             # Main app (< 200 dòng)
```

---

### 📋 PHASE 2: Tách API Layer (2-3 ngày)

**Mục tiêu:** Centralize tất cả API calls

#### 2.1. Tạo base API service
```javascript
// services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL,
  timeout: 30000,
});

// Request interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Central error handling
    if (error.response?.status === 401) {
      // Handle unauthorized
    }
    return Promise.reject(error);
  }
);

export default api;
```

#### 2.2. Tạo feature services
```javascript
// services/crewService.js
import api from './api';

export const crewService = {
  getAll: (shipId) => api.get('/api/crews', { params: { ship_id: shipId } }),
  getById: (id) => api.get(`/api/crews/${id}`),
  create: (data) => api.post('/api/crews', data),
  update: (id, data) => api.put(`/api/crews/${id}`, data),
  delete: (id) => api.delete(`/api/crews/${id}`),
  bulkDelete: (ids) => api.post('/api/crews/bulk-delete', { crew_ids: ids }),
};

// Tương tự cho: shipService, certificateService, surveyService, etc.
```

**Lợi ích:**
- ✅ DRY principle (Don't Repeat Yourself)
- ✅ Easy to mock for testing
- ✅ Central error handling
- ✅ Easy to add caching/retry logic
- ✅ Type-safe with TypeScript (future)

---

### 📋 PHASE 3: Tạo Custom Hooks (3-4 ngày)

**Mục tiêu:** Extract reusable logic

#### 3.1. useFetch hook (Generic data fetching)
```javascript
// hooks/useFetch.js
import { useState, useEffect } from 'react';

export const useFetch = (fetchFn, deps = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    
    const fetchData = async () => {
      setLoading(true);
      try {
        const result = await fetchFn();
        if (!cancelled) {
          setData(result.data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchData();
    
    return () => { cancelled = true; };
  }, deps);

  return { data, loading, error, refetch: () => fetchData() };
};

// Usage:
const { data: crews, loading, error } = useFetch(
  () => crewService.getAll(shipId),
  [shipId]
);
```

#### 3.2. useModal hook (Generic modal management)
```javascript
// hooks/useModal.js
import { useState, useCallback } from 'react';

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

// Usage:
const addCrewModal = useModal();
const editCrewModal = useModal();

// Open modals:
addCrewModal.open();
editCrewModal.open(crewData);
```

#### 3.3. useCRUD hook (Generic CRUD operations)
```javascript
// hooks/useCRUD.js
import { useState, useCallback } from 'react';
import { toast } from 'sonner';

export const useCRUD = (service, resourceName) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchAll = useCallback(async (params) => {
    setLoading(true);
    try {
      const response = await service.getAll(params);
      setItems(response.data);
    } catch (error) {
      toast.error(`Failed to fetch ${resourceName}`);
    } finally {
      setLoading(false);
    }
  }, [service, resourceName]);

  const create = useCallback(async (data) => {
    try {
      await service.create(data);
      toast.success(`${resourceName} created successfully`);
      await fetchAll();
    } catch (error) {
      toast.error(`Failed to create ${resourceName}`);
    }
  }, [service, resourceName, fetchAll]);

  const update = useCallback(async (id, data) => {
    try {
      await service.update(id, data);
      toast.success(`${resourceName} updated successfully`);
      await fetchAll();
    } catch (error) {
      toast.error(`Failed to update ${resourceName}`);
    }
  }, [service, resourceName, fetchAll]);

  const remove = useCallback(async (id) => {
    try {
      await service.delete(id);
      toast.success(`${resourceName} deleted successfully`);
      await fetchAll();
    } catch (error) {
      toast.error(`Failed to delete ${resourceName}`);
    }
  }, [service, resourceName, fetchAll]);

  return {
    items,
    loading,
    fetchAll,
    create,
    update,
    remove,
  };
};

// Usage:
const {
  items: crews,
  loading,
  create: createCrew,
  update: updateCrew,
  remove: deleteCrew,
} = useCRUD(crewService, 'Crew');
```

**Lợi ích:**
- ✅ Giảm 287 functions xuống ~30-40 custom hooks
- ✅ Reusable logic
- ✅ Easier testing
- ✅ Clean component code

---

### 📋 PHASE 4: Tách Components (5-7 ngày)

**Mục tiêu:** Break down HomePage thành smaller components

#### 4.1. Feature-based component structure

```javascript
// components/crew/CrewList.jsx
export const CrewList = ({ crews, onEdit, onDelete }) => {
  return (
    <div className="crew-list">
      {/* Crew list UI */}
    </div>
  );
};

// components/crew/CrewModal.jsx
export const CrewModal = ({ isOpen, crew, onClose, onSubmit }) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      {/* Crew modal UI */}
    </Dialog>
  );
};

// components/crew/CrewFilters.jsx
export const CrewFilters = ({ filters, onChange }) => {
  return (
    <div className="filters">
      {/* Filter UI */}
    </div>
  );
};
```

#### 4.2. Page structure (sau khi tách)

```javascript
// pages/CrewPage.jsx
import { CrewList } from '../components/crew/CrewList';
import { CrewModal } from '../components/crew/CrewModal';
import { CrewFilters } from '../components/crew/CrewFilters';
import { useCRUD } from '../hooks/useCRUD';
import { useModal } from '../hooks/useModal';
import { crewService } from '../services/crewService';

export const CrewPage = () => {
  const { items: crews, loading, create, update, remove } = useCRUD(crewService, 'Crew');
  const addModal = useModal();
  const editModal = useModal();
  
  return (
    <div className="crew-page">
      <CrewFilters onChange={handleFilterChange} />
      <CrewList
        crews={crews}
        loading={loading}
        onEdit={editModal.open}
        onDelete={remove}
      />
      <CrewModal
        isOpen={addModal.isOpen}
        onClose={addModal.close}
        onSubmit={create}
      />
      <CrewModal
        isOpen={editModal.isOpen}
        crew={editModal.data}
        onClose={editModal.close}
        onSubmit={update}
      />
    </div>
  );
};

// Kết quả: 1 page ~100-150 dòng thay vì 23,872 dòng!
```

**Component breakdown:**
```
HomePage (23,872 dòng) →
  ├── CrewPage (~150 dòng)
  │   ├── CrewList (~80 dòng)
  │   ├── CrewModal (~120 dòng)
  │   └── CrewFilters (~60 dòng)
  │
  ├── ShipPage (~200 dòng)
  │   ├── ShipList (~100 dòng)
  │   ├── ShipModal (~150 dòng)
  │   └── ShipDetails (~200 dòng)
  │
  ├── CertificatePage (~180 dòng)
  │   ├── CertificateList (~90 dòng)
  │   ├── CertificateModal (~130 dòng)
  │   └── CertificateUpload (~100 dòng)
  │
  └── ... (các pages khác)
```

---

### 📋 PHASE 5: State Management (3-4 ngày)

**Option 1: React Context (Đơn giản hơn)**

```javascript
// context/CrewContext.jsx
import { createContext, useContext, useState, useCallback } from 'react';

const CrewContext = createContext();

export const CrewProvider = ({ children }) => {
  const [crews, setCrews] = useState([]);
  const [selectedCrew, setSelectedCrew] = useState(null);
  
  const addCrew = useCallback((crew) => {
    setCrews(prev => [...prev, crew]);
  }, []);
  
  return (
    <CrewContext.Provider value={{ crews, selectedCrew, addCrew }}>
      {children}
    </CrewContext.Provider>
  );
};

export const useCrews = () => useContext(CrewContext);

// Usage:
const { crews, addCrew } = useCrews();
```

**Option 2: Redux Toolkit (Phức tạp hơn, powerful hơn)**

```javascript
// store/slices/crewSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { crewService } from '../../services/crewService';

export const fetchCrews = createAsyncThunk(
  'crew/fetchAll',
  async (shipId) => {
    const response = await crewService.getAll(shipId);
    return response.data;
  }
);

const crewSlice = createSlice({
  name: 'crew',
  initialState: {
    items: [],
    loading: false,
    error: null,
  },
  reducers: {
    // Synchronous actions
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCrews.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchCrews.fulfilled, (state, action) => {
        state.items = action.payload;
        state.loading = false;
      })
      .addCase(fetchCrews.rejected, (state, action) => {
        state.error = action.error.message;
        state.loading = false;
      });
  },
});

export default crewSlice.reducer;

// Usage:
const crews = useSelector(state => state.crew.items);
const dispatch = useDispatch();
dispatch(fetchCrews(shipId));
```

**Recommendation:** Bắt đầu với **React Context** cho đơn giản, migrate sang Redux sau nếu cần.

---

### 📋 PHASE 6: Add TypeScript (4-5 ngày) - OPTIONAL

**Lợi ích:**
- ✅ Type safety
- ✅ Better IDE support
- ✅ Catch errors at compile time
- ✅ Self-documenting code

```typescript
// types/crew.ts
export interface Crew {
  id: string;
  name: string;
  rank: string;
  ship_id: string;
  status: 'active' | 'standby';
  created_at: string;
  updated_at: string;
}

// services/crewService.ts
import { Crew } from '../types/crew';

export const crewService = {
  getAll: (shipId: string): Promise<Crew[]> => 
    api.get('/api/crews', { params: { ship_id: shipId } }),
  // ...
};

// components/crew/CrewList.tsx
interface CrewListProps {
  crews: Crew[];
  onEdit: (crew: Crew) => void;
  onDelete: (id: string) => void;
}

export const CrewList: React.FC<CrewListProps> = ({ crews, onEdit, onDelete }) => {
  // ...
};
```

---

## 📊 KẾT QUẢ SAU REFACTORING

### Metrics Comparison

| Metric | Trước | Sau | Cải thiện |
|--------|-------|-----|-----------|
| **Dòng code/file** | 33,150 | < 300 | ✅ 99% |
| **Số files** | 1 | ~50-60 | ✅ Modular |
| **State/component** | 298 | < 10 | ✅ 97% |
| **Functions/component** | 287 | < 20 | ✅ 93% |
| **Code duplication** | Cao | Thấp | ✅ 80% |
| **Testability** | 🔴 Không thể | ✅ Dễ dàng | ✅ 100% |
| **Maintainability** | 🔴 Cực khó | ✅ Dễ dàng | ✅ 100% |
| **Performance** | 🟡 Chậm | ✅ Nhanh | ✅ 50%+ |

### Code Quality

```
TRƯỚC:
❌ 1 file 33,150 dòng
❌ 299 useState hooks
❌ 298 state variables
❌ 287 functions
❌ 141 API calls scattered
❌ 23 modal states
❌ Không thể test
❌ Không thể maintain

SAU:
✅ ~50-60 files, mỗi file < 300 dòng
✅ < 10 states per component
✅ Reusable hooks (useFetch, useModal, useCRUD)
✅ Centralized API layer
✅ Testable components
✅ Maintainable codebase
✅ Performance optimized
✅ TypeScript ready
```

---

## 🚀 KHUYẾN NGHỊ

### ⚡ URGENT (Làm ngay)

1. **Tạo API Service Layer** (2-3 ngày)
   - Tách tất cả axios calls ra khỏi components
   - Central error handling
   - Request/response interceptors

2. **Extract Custom Hooks** (3-4 ngày)
   - useFetch cho data fetching
   - useModal cho modal management
   - useCRUD cho CRUD operations

3. **Tách HomePage thành Feature Pages** (5-7 ngày)
   - CrewPage, ShipPage, CertificatePage, etc.
   - Mỗi page < 200 dòng

### 🎯 HIGH PRIORITY (Làm sau)

4. **Component Library** (3-4 ngày)
   - Reusable UI components
   - Common patterns (List, Modal, Form)

5. **State Management** (3-4 ngày)
   - React Context hoặc Redux Toolkit
   - Centralized state logic

### 💡 NICE TO HAVE (Làm nếu có thời gian)

6. **TypeScript Migration** (4-5 ngày)
   - Type safety
   - Better developer experience

7. **Testing Setup** (3-4 ngày)
   - Unit tests cho hooks
   - Integration tests cho components

---

## 📝 TỔNG KẾT

### Tình trạng hiện tại: 🔴 **CRITICAL** - Cần refactor NGAY

**Vấn đề lớn nhất:**
1. 🔴 Monolithic architecture (33,150 dòng trong 1 file)
2. 🔴 HomePage component quá lớn (23,872 dòng - 72% của file)
3. 🔴 Quá nhiều state (299 useState hooks)
4. 🔴 Code duplication nghiêm trọng
5. 🔴 Không có API layer
6. 🟡 Performance issues

### Độ khó refactoring: 🟡 **TRUNG BÌNH - CAO**

- **Ước tính thời gian:** 3-4 tuần (nếu full-time)
- **Rủi ro:** TRUNG BÌNH (có thể break existing features)
- **Chiến lược:** Incremental refactoring (từng phần, test kỹ từng bước)

### Lợi ích sau khi hoàn thành:

✅ **Code dễ maintain hơn 10x**  
✅ **Performance tăng 50%+**  
✅ **Dễ onboard developers mới**  
✅ **Dễ add features mới**  
✅ **Dễ debug và fix bugs**  
✅ **Testable codebase**  
✅ **Professional architecture**

---

## 🎬 HÀNH ĐỘNG TIẾP THEO

### Bạn có 3 options:

1. **🚀 Bắt đầu refactor toàn bộ** (3-4 tuần)
   - Theo plan chi tiết ở trên
   - Làm từng phase một
   - Test kỹ từng bước

2. **⚡ Refactor từng phần** (linh hoạt)
   - Bắt đầu với API layer (quan trọng nhất)
   - Sau đó extract hooks
   - Cuối cùng tách components

3. **🔧 Giữ nguyên và fix issues** (không khuyến khích)
   - Chỉ fix bugs khi gặp
   - Tiếp tục maintain monolith
   - ⚠️ Càng để lâu càng khó refactor

### 💡 Khuyến nghị của tôi:

**Chọn Option 2: Refactor từng phần**

Bắt đầu với:
1. ✅ Tạo API Service Layer (3 ngày) - HIGH IMPACT
2. ✅ Extract useFetch, useModal, useCRUD hooks (3 ngày) - HIGH IMPACT
3. ✅ Tách Crew Management ra riêng (2 ngày) - TEST PILOT
4. ✅ Nếu thành công → tiếp tục với các features khác

**Lý do:**
- Ít rủi ro hơn
- Có thể test từng phần
- Deliver value sớm hơn
- Learn & adapt along the way

---

**Bạn muốn tôi bắt đầu với phần nào?** 🤔
