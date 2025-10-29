# 📋 KẾ HOẠCH CHI TIẾT PHASE 4: SHIP MANAGEMENT FEATURE

**Ngày tạo:** 2025-10-29  
**Trạng thái:** 📝 Kế hoạch  
**Thời gian dự kiến:** 3-4 ngày  
**Độ ưu tiên:** Cao (Feature đầu tiên được migrate)

---

## 🎯 TỔNG QUAN

### Mục tiêu Phase 4

Trích xuất và migrate toàn bộ tính năng **Ship Management** (Quản lý Tàu) từ frontend-v1 sang frontend-v2 với kiến trúc modular, sử dụng các utilities, services và hooks đã xây dựng ở Phase 1-3.

### Phạm vi công việc

1. ✅ **Service Layer** - Đã hoàn thành (Phase 2)
2. 🔄 **Custom Hooks** - Tạo hook riêng cho Ship
3. 🔄 **Components** - Trích xuất 9 components từ V1
4. 🔄 **Modals** - Tạo Add/Edit/Delete modals
5. 🔄 **Page** - Tạo ShipManagementPage
6. 🔄 **Integration** - Tích hợp với Auth và Router
7. 🔄 **Testing** - Kiểm thử đầy đủ

### Tại sao bắt đầu với Ship Management?

- ✅ Tính năng cơ bản nhất (Foundation feature)
- ✅ Không phụ thuộc vào các feature khác
- ✅ Crew, Certificates, Reports đều cần Ship data
- ✅ Service layer đã sẵn sàng từ Phase 2
- ✅ Kiến trúc đơn giản, dễ migrate trước

---

## 📊 PHÂN TÍCH FRONTEND-V1

### Cấu trúc hiện tại trong App.js (V1)

| Component/Logic | Vị trí trong V1 | Số dòng | Mức độ phức tạp |
|----------------|-----------------|---------|-----------------|
| **Ship States** | Lines 300-350 | ~50 | Trung bình |
| **Ship Selector** | Lines 900-1000 | ~100 | Đơn giản |
| **Ship List Table** | Lines 1000-1200 | ~200 | Trung bình |
| **Ship Info Display** | Lines 1300-1500 | ~200 | Đơn giản |
| **Add Ship Modal** | Lines 1600-1800 | ~200 | Phức tạp |
| **Edit Ship Modal** | Lines 1900-2100 | ~200 | Phức tạp |
| **Delete Ship Modal** | Lines 2200-2300 | ~100 | Đơn giản |
| **Ship Handlers** | Lines 2400-2600 | ~200 | Trung bình |

**Tổng:** ~1,250 dòng code cần migrate

### API Calls cần migrate

```javascript
// Từ frontend-v1/src/App.js
1. GET /api/ships                    // Lấy danh sách tàu
2. GET /api/ships/:id                // Lấy thông tin 1 tàu
3. POST /api/ships                   // Tạo tàu mới
4. PUT /api/ships/:id                // Cập nhật tàu
5. DELETE /api/ships/:id             // Xóa tàu
6. GET /api/ships/:id/certificates   // Lấy chứng chỉ của tàu
7. GET /api/ships/:id/crew           // Lấy thuyền viên trên tàu
8. GET /api/ships/:id/reports        // Lấy báo cáo của tàu
```

✅ **Tất cả đã có trong `shipService.js` (Phase 2)**

### States cần migrate

```javascript
// Ship Management States (từ V1)
const [ships, setShips] = useState([]);
const [selectedShip, setSelectedShip] = useState(null);
const [showAddShipModal, setShowAddShipModal] = useState(false);
const [showEditShipModal, setShowEditShipModal] = useState(false);
const [showDeleteShipModal, setShowDeleteShipModal] = useState(false);
const [shipToEdit, setShipToEdit] = useState(null);
const [shipToDelete, setShipToDelete] = useState(null);
const [shipSortKey, setShipSortKey] = useState('name');
const [shipSortOrder, setShipSortOrder] = useState('asc');
const [shipSearchTerm, setShipSearchTerm] = useState('');
const [shipFilterStatus, setShipFilterStatus] = useState('all');
const [loadingShips, setLoadingShips] = useState(false);
const [shipError, setShipError] = useState(null);
```

🎯 **Sẽ được quản lý bởi custom hooks trong V2**

---

## 🏗️ KIẾN TRÚC MỚI (V2)

### Cấu trúc thư mục

```
/app/frontend/src/
├── features/
│   └── ship/
│       ├── components/
│       │   ├── ShipList.jsx           # Bảng danh sách tàu
│       │   ├── ShipCard.jsx           # Card hiển thị thông tin tàu
│       │   ├── ShipSelector.jsx       # Dropdown chọn tàu
│       │   ├── ShipInfo.jsx           # Panel thông tin chi tiết tàu
│       │   └── ShipFilters.jsx        # Bộ lọc và tìm kiếm
│       │
│       ├── modals/
│       │   ├── AddShipModal.jsx       # Modal thêm tàu mới
│       │   ├── EditShipModal.jsx      # Modal chỉnh sửa tàu
│       │   └── DeleteShipModal.jsx    # Modal xác nhận xóa tàu
│       │
│       ├── hooks/
│       │   ├── useShips.js            # Hook quản lý danh sách tàu
│       │   ├── useShipForm.js         # Hook quản lý form tàu
│       │   └── useShipFilters.js      # Hook quản lý bộ lọc
│       │
│       └── index.js                   # Export tất cả
│
├── pages/
│   └── ShipManagementPage.jsx         # Trang quản lý tàu
│
└── services/
    └── shipService.js                 # ✅ Đã có sẵn (Phase 2)
```

### Luồng dữ liệu (Data Flow)

```
User Action (UI)
    ↓
Component Event Handler
    ↓
Custom Hook (useShips)
    ↓
Service Layer (shipService)
    ↓
API Call (axios)
    ↓
Backend FastAPI
    ↓
MongoDB
    ↓
Response
    ↓
Hook Updates State
    ↓
Component Re-renders
```

---

## 📝 KẾ HOẠCH THỰC HIỆN CHI TIẾT

### **BƯỚC 1: Tạo Custom Hooks cho Ship** (4 giờ)

#### 1.1 Hook: `useShips.js`

**Chức năng:**
- Quản lý danh sách tàu (fetch, create, update, delete)
- Loading và error states
- Tích hợp với useCRUD hook

**API:**
```javascript
const {
  ships,              // Danh sách tàu
  loading,            // Trạng thái loading
  error,              // Thông báo lỗi
  fetchShips,         // Lấy danh sách tàu
  createShip,         // Tạo tàu mới
  updateShip,         // Cập nhật tàu
  deleteShip,         // Xóa tàu
  selectedShip,       // Tàu đang được chọn
  setSelectedShip     // Set tàu được chọn
} = useShips();
```

**Implementation:**
```javascript
// /app/frontend/src/features/ship/hooks/useShips.js
import { useState, useCallback } from 'react';
import { useCRUD } from '../../../hooks';
import { shipService } from '../../../services';

export const useShips = () => {
  const [selectedShip, setSelectedShip] = useState(null);
  
  const {
    items: ships,
    loading,
    error,
    fetchAll: fetchShips,
    create: createShip,
    update: updateShip,
    remove: deleteShip
  } = useCRUD({
    getAll: shipService.getAllShips,
    create: shipService.createShip,
    update: shipService.updateShip,
    delete: shipService.deleteShip
  });

  const selectShip = useCallback((ship) => {
    setSelectedShip(ship);
  }, []);

  return {
    ships,
    loading,
    error,
    fetchShips,
    createShip,
    updateShip,
    deleteShip,
    selectedShip,
    selectShip
  };
};
```

#### 1.2 Hook: `useShipForm.js`

**Chức năng:**
- Quản lý form state cho Add/Edit Ship
- Validation
- Submit handling

**API:**
```javascript
const {
  formData,           // Dữ liệu form
  errors,             // Lỗi validation
  handleChange,       // Xử lý thay đổi input
  handleSubmit,       // Xử lý submit
  resetForm,          // Reset form
  setFormData         // Set dữ liệu form (cho Edit)
} = useShipForm(onSubmit, initialData);
```

#### 1.3 Hook: `useShipFilters.js`

**Chức năng:**
- Quản lý search và filter
- Sorting
- Filtered data

**API:**
```javascript
const {
  searchTerm,         // Từ khóa tìm kiếm
  filterStatus,       // Trạng thái lọc
  sortKey,            // Trường sort
  sortOrder,          // Thứ tự sort
  filteredShips,      // Danh sách đã lọc
  handleSearch,       // Xử lý tìm kiếm
  handleFilter,       // Xử lý lọc
  handleSort          // Xử lý sort
} = useShipFilters(ships);
```

**Checklist Bước 1:**
- [ ] Tạo file `useShips.js`
- [ ] Tạo file `useShipForm.js`
- [ ] Tạo file `useShipFilters.js`
- [ ] Tạo file `index.js` để export hooks
- [ ] Viết JSDoc cho tất cả hooks
- [ ] Lint và fix errors

---

### **BƯỚC 2: Tạo Basic Components** (6 giờ)

#### 2.1 Component: `ShipCard.jsx`

**Mục đích:** Hiển thị thông tin tàu dạng card (đơn giản nhất)

**Props:**
```javascript
{
  ship: {
    id: string,
    name: string,
    imo: string,
    flag: string,
    ship_type: string,
    built_year: number,
    dwt: number
  },
  onSelect: function,
  onEdit: function,
  onDelete: function,
  isSelected: boolean
}
```

**UI Elements:**
- Tên tàu (ship name)
- IMO number
- Flag (quốc kỳ)
- Ship type
- Built year
- DWT (trọng tải)
- Buttons: View, Edit, Delete

**Trích xuất từ:** Lines 1000-1200 (V1)

#### 2.2 Component: `ShipSelector.jsx`

**Mục đích:** Dropdown để chọn tàu

**Props:**
```javascript
{
  ships: Array,
  selectedShip: Object,
  onSelect: function,
  placeholder: string,
  disabled: boolean
}
```

**UI Elements:**
- Dropdown select
- Search trong dropdown
- Hiển thị: "Ship Name (IMO: xxxxxxx)"
- Empty state khi không có tàu

**Trích xuất từ:** Lines 900-1000 (V1)

#### 2.3 Component: `ShipInfo.jsx`

**Mục đích:** Panel hiển thị thông tin chi tiết tàu

**Props:**
```javascript
{
  ship: Object,
  onEdit: function,
  onClose: function
}
```

**UI Elements:**
- Tất cả thông tin của tàu
- Layout: 2 columns
- Sections: Basic Info, Technical Specs, Classification
- Edit button
- Close button

**Trích xuất từ:** Lines 1300-1500 (V1)

#### 2.4 Component: `ShipFilters.jsx`

**Mục đích:** Bộ lọc và tìm kiếm tàu

**Props:**
```javascript
{
  searchTerm: string,
  filterStatus: string,
  onSearch: function,
  onFilter: function,
  onReset: function
}
```

**UI Elements:**
- Search input (tìm theo tên, IMO)
- Filter dropdown (Active/Inactive/All)
- Reset button
- Result count

**Checklist Bước 2:**
- [ ] Tạo `ShipCard.jsx`
- [ ] Tạo `ShipSelector.jsx`
- [ ] Tạo `ShipInfo.jsx`
- [ ] Tạo `ShipFilters.jsx`
- [ ] Test render với mock data
- [ ] Lint và fix errors

---

### **BƯỚC 3: Tạo ShipList Component** (4 giờ)

#### 3.1 Component: `ShipList.jsx`

**Mục đích:** Bảng danh sách tàu với sorting và actions

**Props:**
```javascript
{
  ships: Array,
  loading: boolean,
  error: string,
  sortKey: string,
  sortOrder: string,
  onSort: function,
  onSelect: function,
  onEdit: function,
  onDelete: function,
  selectedShipId: string
}
```

**UI Structure:**
```jsx
<div className="ship-list">
  {/* Header with count */}
  <div className="header">
    <h2>Ship List ({ships.length})</h2>
    <button onClick={onAdd}>Add Ship</button>
  </div>

  {/* Loading State */}
  {loading && <LoadingSpinner />}

  {/* Error State */}
  {error && <ErrorMessage message={error} />}

  {/* Empty State */}
  {!loading && ships.length === 0 && (
    <EmptyState message="No ships found" />
  )}

  {/* Table */}
  <table>
    <thead>
      <tr>
        <th onClick={() => onSort('name')}>
          Ship Name {sortIndicator('name')}
        </th>
        <th onClick={() => onSort('imo')}>
          IMO {sortIndicator('imo')}
        </th>
        <th onClick={() => onSort('flag')}>
          Flag {sortIndicator('flag')}
        </th>
        <th onClick={() => onSort('ship_type')}>
          Type {sortIndicator('ship_type')}
        </th>
        <th onClick={() => onSort('built_year')}>
          Built {sortIndicator('built_year')}
        </th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {ships.map(ship => (
        <ShipRow
          key={ship.id}
          ship={ship}
          onSelect={onSelect}
          onEdit={onEdit}
          onDelete={onDelete}
          isSelected={selectedShipId === ship.id}
        />
      ))}
    </tbody>
  </table>
</div>
```

**Features:**
- ✅ Sortable columns (click header to sort)
- ✅ Row selection highlight
- ✅ Action buttons (View, Edit, Delete)
- ✅ Loading state
- ✅ Error state
- ✅ Empty state
- ✅ Responsive design

**Trích xuất từ:** Lines 1000-1200 (V1)

**Checklist Bước 3:**
- [ ] Tạo `ShipList.jsx`
- [ ] Tạo `ShipRow.jsx` (sub-component)
- [ ] Implement sorting với `useSort` hook
- [ ] Implement loading/error/empty states
- [ ] Test với mock data
- [ ] Lint và fix errors

---

### **BƯỚC 4: Tạo Modal Components** (8 giờ)

#### 4.1 Modal: `AddShipModal.jsx`

**Mục đích:** Form thêm tàu mới

**Props:**
```javascript
{
  isOpen: boolean,
  onClose: function,
  onSubmit: function,
  loading: boolean
}
```

**Form Fields:**
```javascript
// Basic Information
- name: string (required)           // Tên tàu
- imo: string (required, 7 digits)  // IMO number
- call_sign: string                 // Call sign
- flag: string (required)           // Quốc kỳ
- ship_type: string (required)      // Loại tàu

// Technical Specifications
- built_year: number                // Năm đóng
- dwt: number                       // Trọng tải
- gt: number                        // Gross Tonnage
- nt: number                        // Net Tonnage
- loa: number                       // Length Overall
- breadth: number                   // Chiều rộng
- depth: number                     // Chiều sâu

// Classification & Port
- class_society: string             // Tổ chức phân cấp
- port_of_registry: string          // Cảng đăng ký
- official_number: string           // Số đăng ký

// Additional Info
- registered_owner: string          // Chủ sở hữu
- operator: string                  // Người vận hành
- manager: string                   // Người quản lý
- note: string                      // Ghi chú
```

**Validation Rules:**
```javascript
// Required fields
- name: không được rỗng
- imo: 7 chữ số
- flag: không được rỗng
- ship_type: phải chọn từ dropdown

// Number fields
- built_year: 1900-2100
- dwt, gt, nt, loa, breadth, depth: >= 0

// IMO validation
- Format: 7 digits
- Check digit validation (theo IMO standard)
```

**UI Structure:**
```jsx
<Modal isOpen={isOpen} onClose={onClose} size="large">
  <ModalHeader>
    <h2>Add New Ship</h2>
    <CloseButton onClick={onClose} />
  </ModalHeader>

  <ModalBody>
    <form onSubmit={handleSubmit}>
      {/* Basic Info Section */}
      <FormSection title="Basic Information">
        <FormField label="Ship Name *" error={errors.name}>
          <input name="name" value={formData.name} onChange={handleChange} />
        </FormField>
        <FormField label="IMO Number *" error={errors.imo}>
          <input name="imo" value={formData.imo} onChange={handleChange} />
        </FormField>
        {/* ... more fields */}
      </FormSection>

      {/* Technical Specs Section */}
      <FormSection title="Technical Specifications">
        {/* ... fields */}
      </FormSection>

      {/* Classification Section */}
      <FormSection title="Classification & Port">
        {/* ... fields */}
      </FormSection>

      {/* Additional Info Section */}
      <FormSection title="Additional Information">
        {/* ... fields */}
      </FormSection>
    </form>
  </ModalBody>

  <ModalFooter>
    <Button variant="secondary" onClick={onClose}>
      Cancel
    </Button>
    <Button variant="primary" onClick={handleSubmit} loading={loading}>
      Add Ship
    </Button>
  </ModalFooter>
</Modal>
```

**Trích xuất từ:** Lines 1600-1800 (V1)

#### 4.2 Modal: `EditShipModal.jsx`

**Mục đích:** Form chỉnh sửa tàu

**Props:**
```javascript
{
  isOpen: boolean,
  onClose: function,
  onSubmit: function,
  ship: Object,
  loading: boolean
}
```

**Features:**
- ✅ Giống AddShipModal nhưng pre-fill data
- ✅ Hiển thị ship name trong header
- ✅ Validation giống Add
- ✅ Submit button text: "Update Ship"

**Trích xuất từ:** Lines 1900-2100 (V1)

#### 4.3 Modal: `DeleteShipModal.jsx`

**Mục đích:** Xác nhận xóa tàu

**Props:**
```javascript
{
  isOpen: boolean,
  onClose: function,
  onConfirm: function,
  ship: Object,
  loading: boolean
}
```

**UI:**
```jsx
<Modal isOpen={isOpen} onClose={onClose} size="small">
  <ModalHeader>
    <h2>Delete Ship</h2>
  </ModalHeader>

  <ModalBody>
    <p>Are you sure you want to delete this ship?</p>
    <div className="ship-info-box">
      <strong>{ship.name}</strong>
      <span>IMO: {ship.imo}</span>
    </div>
    <p className="warning-text">
      ⚠️ This action cannot be undone. All related data 
      (crew, certificates, reports) will also be affected.
    </p>
  </ModalBody>

  <ModalFooter>
    <Button variant="secondary" onClick={onClose}>
      Cancel
    </Button>
    <Button variant="danger" onClick={onConfirm} loading={loading}>
      Delete Ship
    </Button>
  </ModalFooter>
</Modal>
```

**Trích xuất từ:** Lines 2200-2300 (V1)

**Checklist Bước 4:**
- [ ] Tạo `AddShipModal.jsx`
- [ ] Tạo `EditShipModal.jsx`
- [ ] Tạo `DeleteShipModal.jsx`
- [ ] Implement validation với `validators.js`
- [ ] Test form submission
- [ ] Test error handling
- [ ] Lint và fix errors

---

### **BƯỚC 5: Tạo ShipManagementPage** (4 giờ)

#### 5.1 Page: `ShipManagementPage.jsx`

**Mục đích:** Trang chính quản lý tàu, tích hợp tất cả components

**Structure:**
```jsx
import React, { useEffect } from 'react';
import { useShips, useShipFilters } from '../features/ship/hooks';
import { 
  ShipList, 
  ShipFilters, 
  ShipInfo 
} from '../features/ship/components';
import {
  AddShipModal,
  EditShipModal,
  DeleteShipModal
} from '../features/ship/modals';
import { useModal } from '../hooks';
import { toast } from 'react-toastify';

const ShipManagementPage = () => {
  // Custom hooks
  const {
    ships,
    loading,
    error,
    fetchShips,
    createShip,
    updateShip,
    deleteShip,
    selectedShip,
    selectShip
  } = useShips();

  const {
    searchTerm,
    filterStatus,
    sortKey,
    sortOrder,
    filteredShips,
    handleSearch,
    handleFilter,
    handleSort
  } = useShipFilters(ships);

  // Modal states
  const addModal = useModal();
  const editModal = useModal();
  const deleteModal = useModal();
  const infoPanel = useModal();

  // Fetch ships on mount
  useEffect(() => {
    fetchShips();
  }, []);

  // Handle add ship
  const handleAddShip = async (shipData) => {
    try {
      await createShip(shipData);
      addModal.close();
      toast.success('Ship added successfully!');
    } catch (err) {
      toast.error('Failed to add ship');
    }
  };

  // Handle edit ship
  const handleEditShip = async (shipData) => {
    try {
      await updateShip(selectedShip.id, shipData);
      editModal.close();
      toast.success('Ship updated successfully!');
    } catch (err) {
      toast.error('Failed to update ship');
    }
  };

  // Handle delete ship
  const handleDeleteShip = async () => {
    try {
      await deleteShip(selectedShip.id);
      deleteModal.close();
      selectShip(null);
      toast.success('Ship deleted successfully!');
    } catch (err) {
      toast.error('Failed to delete ship');
    }
  };

  return (
    <div className="ship-management-page">
      {/* Page Header */}
      <div className="page-header">
        <h1>Ship Management</h1>
        <button onClick={addModal.open}>Add New Ship</button>
      </div>

      {/* Filters */}
      <ShipFilters
        searchTerm={searchTerm}
        filterStatus={filterStatus}
        onSearch={handleSearch}
        onFilter={handleFilter}
      />

      {/* Ship List */}
      <ShipList
        ships={filteredShips}
        loading={loading}
        error={error}
        sortKey={sortKey}
        sortOrder={sortOrder}
        onSort={handleSort}
        onSelect={(ship) => {
          selectShip(ship);
          infoPanel.open();
        }}
        onEdit={(ship) => {
          selectShip(ship);
          editModal.open();
        }}
        onDelete={(ship) => {
          selectShip(ship);
          deleteModal.open();
        }}
        selectedShipId={selectedShip?.id}
      />

      {/* Modals */}
      <AddShipModal
        isOpen={addModal.isOpen}
        onClose={addModal.close}
        onSubmit={handleAddShip}
        loading={loading}
      />

      <EditShipModal
        isOpen={editModal.isOpen}
        onClose={editModal.close}
        onSubmit={handleEditShip}
        ship={selectedShip}
        loading={loading}
      />

      <DeleteShipModal
        isOpen={deleteModal.isOpen}
        onClose={deleteModal.close}
        onConfirm={handleDeleteShip}
        ship={selectedShip}
        loading={loading}
      />

      {/* Info Panel */}
      {infoPanel.isOpen && (
        <ShipInfo
          ship={selectedShip}
          onEdit={() => {
            infoPanel.close();
            editModal.open();
          }}
          onClose={infoPanel.close}
        />
      )}
    </div>
  );
};

export default ShipManagementPage;
```

**Checklist Bước 5:**
- [ ] Tạo `ShipManagementPage.jsx`
- [ ] Integrate tất cả components
- [ ] Integrate tất cả hooks
- [ ] Test CRUD workflow
- [ ] Test error handling
- [ ] Lint và fix errors

---

### **BƯỚC 6: Tích hợp với Router** (2 giờ)

#### 6.1 Update AppRoutes

**File:** `/app/frontend/src/routes/AppRoutes.jsx`

```javascript
import ShipManagementPage from '../pages/ShipManagementPage';

// Add route
<Route path="/ships" element={<ShipManagementPage />} />
```

#### 6.2 Update Navigation Menu

**File:** `/app/frontend/src/pages/HomePage.jsx` hoặc Navigation component

```jsx
<nav>
  <NavLink to="/ships">Ship Management</NavLink>
  {/* ... other links */}
</nav>
```

**Checklist Bước 6:**
- [ ] Add route to AppRoutes
- [ ] Add navigation link
- [ ] Test navigation
- [ ] Verify protected route works

---

### **BƯỚC 7: Styling & UI Polish** (4 giờ)

#### 7.1 TailwindCSS Classes

**Components cần style:**
- ShipList (table responsive)
- ShipCard (card layout)
- ShipSelector (dropdown)
- ShipFilters (filter bar)
- Modals (form layout)

**Design Guidelines:**
```css
/* Colors */
Primary: #3B82F6 (blue-500)
Secondary: #6B7280 (gray-500)
Success: #10B981 (green-500)
Danger: #EF4444 (red-500)
Warning: #F59E0B (amber-500)

/* Spacing */
Container padding: p-6
Card padding: p-4
Modal padding: p-6
Button padding: px-4 py-2

/* Typography */
Page title: text-2xl font-bold
Section title: text-lg font-semibold
Body text: text-base
Label text: text-sm font-medium
```

**Responsive Design:**
```jsx
// Desktop: 3 columns
<div className="grid grid-cols-3 gap-4">

// Tablet: 2 columns
<div className="grid grid-cols-1 md:grid-cols-2 gap-4">

// Mobile: 1 column
<div className="grid grid-cols-1 gap-4">
```

**Checklist Bước 7:**
- [ ] Style ShipList table
- [ ] Style ShipCard
- [ ] Style ShipSelector dropdown
- [ ] Style modals
- [ ] Test responsive design
- [ ] Add hover effects
- [ ] Add loading animations

---

### **BƯỚC 8: Testing & Bug Fixes** (6 giờ)

#### 8.1 Unit Testing (Optional)

**Test hooks:**
```javascript
// useShips.test.js
test('should fetch ships on mount', async () => {
  // ...
});

test('should create ship', async () => {
  // ...
});

test('should update ship', async () => {
  // ...
});

test('should delete ship', async () => {
  // ...
});
```

#### 8.2 Integration Testing

**Test scenarios:**

1. **Fetch Ships on Page Load**
   - ✅ Loading state hiển thị
   - ✅ Ships list hiển thị sau khi load
   - ✅ Error handling nếu API fail

2. **Add New Ship**
   - ✅ Click "Add Ship" button
   - ✅ Modal mở
   - ✅ Fill form
   - ✅ Submit
   - ✅ Modal đóng
   - ✅ New ship xuất hiện trong list
   - ✅ Success toast hiển thị

3. **Edit Ship**
   - ✅ Click "Edit" button
   - ✅ Modal mở với data pre-filled
   - ✅ Change data
   - ✅ Submit
   - ✅ Ship updated trong list
   - ✅ Success toast hiển thị

4. **Delete Ship**
   - ✅ Click "Delete" button
   - ✅ Confirmation modal mở
   - ✅ Confirm delete
   - ✅ Ship removed từ list
   - ✅ Success toast hiển thị

5. **Search & Filter**
   - ✅ Search by ship name
   - ✅ Search by IMO
   - ✅ Filter by status
   - ✅ Clear filters

6. **Sorting**
   - ✅ Sort by name (asc/desc)
   - ✅ Sort by IMO (asc/desc)
   - ✅ Sort by built year (asc/desc)

7. **Error Handling**
   - ✅ API error hiển thị toast
   - ✅ Validation errors hiển thị
   - ✅ Network error handling

#### 8.3 Backend Testing với curl

```bash
# Get all ships
curl -X GET http://localhost:8001/api/ships \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create ship
curl -X POST http://localhost:8001/api/ships \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Ship",
    "imo": "1234567",
    "flag": "Panama",
    "ship_type": "Container Ship"
  }'

# Update ship
curl -X PUT http://localhost:8001/api/ships/SHIP_ID \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Ship Name"
  }'

# Delete ship
curl -X DELETE http://localhost:8001/api/ships/SHIP_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Checklist Bước 8:**
- [ ] Test fetch ships
- [ ] Test add ship workflow
- [ ] Test edit ship workflow
- [ ] Test delete ship workflow
- [ ] Test search functionality
- [ ] Test filter functionality
- [ ] Test sorting
- [ ] Test error handling
- [ ] Fix all bugs found
- [ ] Backend API testing với curl

---

## 📊 TIMELINE & MILESTONES

### Ngày 1 (8 giờ)
- ✅ **Morning (4h):** Bước 1 - Custom Hooks
- ✅ **Afternoon (4h):** Bước 2 - Basic Components (ShipCard, ShipSelector)

### Ngày 2 (8 giờ)
- ✅ **Morning (4h):** Bước 2 (tiếp) - ShipInfo, ShipFilters
- ✅ **Afternoon (4h):** Bước 3 - ShipList Component

### Ngày 3 (8 giờ)
- ✅ **Morning (4h):** Bước 4 - AddShipModal, EditShipModal
- ✅ **Afternoon (4h):** Bước 4 (tiếp) - DeleteShipModal

### Ngày 4 (8 giờ)
- ✅ **Morning (4h):** Bước 5 - ShipManagementPage + Bước 6 - Router Integration
- ✅ **Afternoon (4h):** Bước 7 - Styling & UI Polish

### Ngày 5 (nếu cần) (6 giờ)
- ✅ **All day:** Bước 8 - Testing & Bug Fixes

**Tổng thời gian:** 32-38 giờ (4-5 ngày)

---

## ✅ CHECKLIST TỔNG THỂ

### Setup
- [ ] Tạo thư mục structure (`features/ship/`)
- [ ] Tạo các file cần thiết

### Custom Hooks (4 files)
- [ ] `useShips.js` - Ship CRUD operations
- [ ] `useShipForm.js` - Form management
- [ ] `useShipFilters.js` - Search & filter
- [ ] `hooks/index.js` - Export file

### Components (8 files)
- [ ] `ShipCard.jsx` - Card display
- [ ] `ShipSelector.jsx` - Dropdown selector
- [ ] `ShipInfo.jsx` - Info panel
- [ ] `ShipFilters.jsx` - Filter bar
- [ ] `ShipList.jsx` - Main table
- [ ] `AddShipModal.jsx` - Add form
- [ ] `EditShipModal.jsx` - Edit form
- [ ] `DeleteShipModal.jsx` - Delete confirmation

### Page
- [ ] `ShipManagementPage.jsx` - Main page

### Integration
- [ ] Add route to AppRoutes
- [ ] Add navigation link
- [ ] Test navigation flow

### Testing
- [ ] Unit tests (hooks)
- [ ] Integration tests (workflows)
- [ ] Backend API tests (curl)
- [ ] Bug fixes

### Documentation
- [ ] JSDoc for all functions
- [ ] README for feature
- [ ] Update migration tracker

---

## 🎯 TIÊU CHÍ THÀNH CÔNG

### Functional Requirements ✅

1. **CRUD Operations**
   - ✅ User có thể xem danh sách tàu
   - ✅ User có thể thêm tàu mới
   - ✅ User có thể chỉnh sửa tàu
   - ✅ User có thể xóa tàu
   - ✅ User có thể tìm kiếm tàu
   - ✅ User có thể lọc tàu
   - ✅ User có thể sort tàu

2. **UI/UX**
   - ✅ Loading states hiển thị đúng
   - ✅ Error messages hiển thị đúng
   - ✅ Success toasts hiển thị đúng
   - ✅ Empty states hiển thị đúng
   - ✅ Modals mở/đóng smooth
   - ✅ Form validation hoạt động
   - ✅ Responsive trên mobile/tablet/desktop

3. **Performance**
   - ✅ Page load < 2s
   - ✅ API calls optimized
   - ✅ No unnecessary re-renders
   - ✅ Smooth animations

### Technical Requirements ✅

1. **Code Quality**
   - ✅ All components modular
   - ✅ No code duplication
   - ✅ Clean separation of concerns
   - ✅ Proper error handling
   - ✅ JSDoc documentation
   - ✅ ESLint validation passed

2. **Architecture**
   - ✅ Uses custom hooks
   - ✅ Uses service layer
   - ✅ Uses utilities
   - ✅ Follows V2 structure
   - ✅ No V1 dependencies

3. **Testing**
   - ✅ All workflows tested
   - ✅ Error scenarios tested
   - ✅ Backend integration tested
   - ✅ No console errors

---

## 🚨 RỦI RO & GIẢI PHÁP

### Rủi ro 1: Form validation phức tạp

**Vấn đề:** Ship form có nhiều fields, validation rules phức tạp

**Giải pháp:**
- Sử dụng `validators.js` đã có sẵn
- Tạo custom validator cho IMO number
- Show error inline cho từng field
- Validate on blur + on submit

### Rủi ro 2: Modal state management

**Vấn đề:** Nhiều modals, dễ bị conflict state

**Giải pháp:**
- Dùng `useModal` hook cho mỗi modal
- Độc lập state cho từng modal
- Clear state khi close modal
- Prevent multiple modals cùng lúc

### Rủi ro 3: Performance với nhiều ships

**Vấn đề:** Nếu có 100+ ships, render chậm

**Giải pháp:**
- Implement pagination (future)
- Virtualized list (future)
- Optimize re-renders với React.memo
- Debounce search input

### Rủi ro 4: IMO validation

**Vấn đề:** IMO có check digit algorithm phức tạp

**Giải pháp:**
- Implement IMO check digit validation
- Reference: https://en.wikipedia.org/wiki/IMO_number
- Provide clear error message
- Allow override nếu cần

---

## 📚 TÀI LIỆU THAM KHẢO

### Internal Docs
- `/app/PHASE_0_COMPLETE.md` - Setup reference
- `/app/PHASE_1_COMPLETE.md` - Utilities reference
- `/app/PHASE_2_COMPLETE.md` - Services reference
- `/app/PHASE_3_COMPLETE.md` - Hooks reference
- `/app/frontend-v1/src/App.js` - Source code V1

### External Resources
- [React Hooks](https://react.dev/reference/react)
- [TailwindCSS](https://tailwindcss.com/docs)
- [React Router](https://reactrouter.com/)
- [IMO Number Standard](https://en.wikipedia.org/wiki/IMO_number)

### API Documentation
- Backend: `http://localhost:8001/docs`
- Service Layer: `/app/frontend/src/services/shipService.js`

---

## 📝 GHI CHÚ

### Migration Strategy

Phase 4 là phase đầu tiên migrate một feature hoàn chỉnh. Chiến lược:

1. **Bottom-up approach:**
   - Hooks trước (business logic)
   - Components đơn giản trước (Card, Selector)
   - Components phức tạp sau (List, Modals)
   - Page cuối cùng (tích hợp tất cả)

2. **Test sớm, test thường xuyên:**
   - Test từng component riêng
   - Test integration dần dần
   - Fix bugs ngay khi phát hiện

3. **Reuse maximum:**
   - Dùng hooks từ Phase 3
   - Dùng services từ Phase 2
   - Dùng utilities từ Phase 1
   - Không reinvent the wheel

### Lessons Learned (sẽ cập nhật sau Phase 4)

- [ ] What worked well?
- [ ] What challenges faced?
- [ ] What to improve for Phase 5?
- [ ] Time estimation accuracy?

---

## 🎉 KẾT LUẬN

Phase 4 là bước quan trọng nhất vì đây là feature đầu tiên được migrate hoàn chỉnh. Thành công của Phase 4 sẽ là template cho các phases tiếp theo (Crew, Certificates, Reports).

**Key Success Factors:**
1. ✅ Follow plan chi tiết
2. ✅ Test thoroughly
3. ✅ Keep code clean and modular
4. ✅ Document as you go
5. ✅ Ask for help when stuck

**After Phase 4:**
- Có template rõ ràng cho feature migration
- Có workflow chuẩn cho CRUD operations
- Có component patterns có thể reuse
- Ready cho Phase 5 (Crew Management)

---

**Người tạo kế hoạch:** AI Engineer  
**Ngày tạo:** 2025-10-29  
**Status:** Ready for Implementation  
**Next Step:** Get user confirmation and start Bước 1

🚀 **Let's build Ship Management V2!**
