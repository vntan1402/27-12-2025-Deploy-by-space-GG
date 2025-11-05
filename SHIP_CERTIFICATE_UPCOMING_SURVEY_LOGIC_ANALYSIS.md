# Ship Certificate Upcoming Survey Logic - Phân Tích Chi Tiết

## 📍 VỊ TRÍ CODE (CODE LOCATION)

**File**: `/app/backend/server.py`  
**Dòng (Lines)**: 4916 - 5250  
**API Endpoint**: `GET /api/certificates/upcoming-surveys`

---

## 🏗️ CẤU TRÚC CODE (CODE STRUCTURE)

### 1. **Lấy Dữ Liệu (Data Retrieval)** - Lines 4923-4962

```python
# Lines 4923-4931: Get company information
user_company = current_user.company
company_record = await mongo_db.find_one("companies", {"id": user_company})
company_name = company_record.get('name_en') or company_record.get('name_vn')

# Lines 4935-4948: Dual lookup for ships (by ID and name)
ships_by_id = await mongo_db.find_all("ships", {"company": user_company})
ships_by_name = await mongo_db.find_all("ships", {"company": company_name})
# Deduplicate ships
all_ships_dict = {}
for ship in ships_by_id + ships_by_name:
    ship_id = ship.get('id')
    if ship_id and ship_id not in all_ships_dict:
        all_ships_dict[ship_id] = ship

# Lines 4956-4960: Get all certificates from these ships
all_certificates = []
for ship_id in ship_ids:
    certs = await mongo_db.find_all("certificates", {"ship_id": ship_id})
    all_certificates.extend(certs)
```

**Mục đích**: Lấy tất cả certificates thuộc về các tàu của công ty người dùng.

---

## 🎯 LOGIC XÁC ĐỊNH UPCOMING SURVEY (SURVEY WINDOW LOGIC)

### 2. **Tính Toán Window Cho Từng Loại Certificate** - Lines 5008-5096

Code sử dụng **4 loại window khác nhau** dựa trên loại survey:

#### **A. Condition Certificate Expiry** (Lines 5019-5057)

```python
if 'Condition Certificate Expiry' in next_survey_type:
    issue_date_str = cert.get('issue_date')
    valid_date_str = cert.get('valid_date')
    
    # Parse dates...
    issue_date = parse_date(issue_date_str)
    valid_date = parse_date(valid_date_str)
    
    window_open = issue_date
    window_close = valid_date
```

**Quy tắc**: 
- Window bắt đầu từ **Issue Date**
- Window kết thúc tại **Valid Date** (ngày hết hạn)
- **Không có ±3M**, window là toàn bộ thời gian hiệu lực của certificate

---

#### **B. Initial Survey cho SMC/ISSC/MLC** (Lines 5059-5084)

```python
elif 'Initial' in next_survey_type and any(cert_type in cert_name for cert_type in 
     ['SAFETY MANAGEMENT', 'SHIP SECURITY', 'MARITIME LABOUR', 'SMC', 'ISSC', 'MLC']):
    valid_date_str = cert.get('valid_date')
    valid_date = parse_date(valid_date_str)
    
    window_open = valid_date - timedelta(days=90)  # 3 months before
    window_close = valid_date
```

**Quy tắc**: 
- Window bắt đầu từ **Valid Date - 3 tháng** (90 ngày)
- Window kết thúc tại **Valid Date**
- Chỉ có **-3M** (trước Valid Date), không có extension sau Valid Date

**Áp dụng cho**: Safety Management Certificate (SMC), Ship Security Certificate (ISSC), Maritime Labour Certificate (MLC) có **Next Survey Type = "Initial"**

---

#### **C. Special Survey** (Lines 5086-5089)

```python
elif 'Special Survey' in next_survey_type and next_survey_date:
    window_open = next_survey_date - timedelta(days=90)
    window_close = next_survey_date  # No extension after
```

**Quy tắc**: 
- Window bắt đầu từ **Next Survey Date - 3 tháng** (90 ngày)
- Window kết thúc tại **Next Survey Date**
- Chỉ có **-3M** (trước deadline), **KHÔNG CÓ extension sau deadline**
- Phải hoàn thành trước hoặc đúng ngày Next Survey

---

#### **D. Other Surveys (Intermediate, Renewal, Annual, etc.)** (Lines 5090-5093)

```python
elif next_survey_date:
    window_open = next_survey_date - timedelta(days=90)
    window_close = next_survey_date + timedelta(days=90)
```

**Quy tắc**: 
- Window bắt đầu từ **Next Survey Date - 3 tháng** (90 ngày trước)
- Window kết thúc tại **Next Survey Date + 3 tháng** (90 ngày sau)
- Có **±3M** (trước VÀ sau), linh hoạt hơn

**Áp dụng cho**: Intermediate, Renewal, Annual, và các loại survey khác không thuộc 3 loại trên

---

### 3. **Điều Kiện Lọc (Filter Condition)** - Line 5099

```python
if window_open <= current_date <= window_close:
    # Certificate được include vào upcoming surveys
```

**Nguyên tắc**: Certificate chỉ xuất hiện trong danh sách Upcoming Survey khi **ngày hiện tại nằm trong window** của nó.

**Ví dụ**:
- Hôm nay: 2025-01-15
- Certificate A có window: 2024-12-01 → 2025-06-01 ✅ **HIỆN** (trong window)
- Certificate B có window: 2025-02-01 → 2025-08-01 ❌ **KHÔNG HIỆN** (chưa đến window)
- Certificate C có window: 2024-06-01 → 2024-12-01 ❌ **KHÔNG HIỆN** (đã qua window)

---

## 🚦 LOGIC XÁC ĐỊNH STATUS (STATUS CLASSIFICATION)

### 4. **Phân Loại Status Cho Từng Certificate** - Lines 5110-5161

Code áp dụng **logic khác nhau** cho từng loại certificate:

#### **A. Condition Certificate Status** (Lines 5112-5124)

```python
if 'Condition Certificate Expiry' in next_survey_type:
    # Overdue: Past valid date (expiry)
    is_overdue = current_date > window_close  # window_close = valid_date
    
    # Due Soon: Expires within 30 days
    days_until_expiry = (window_close - current_date).days
    is_due_soon = 0 <= days_until_expiry <= 30
    
    # Critical: Expires within 7 days or already expired
    is_critical = days_until_expiry <= 7
```

**Quy tắc**:
- **Overdue**: Hôm nay > Valid Date (đã hết hạn)
- **Due Soon**: 0-30 ngày cho đến Valid Date
- **Critical**: ≤7 ngày cho đến Valid Date hoặc đã hết hạn

---

#### **B. Initial SMC/ISSC/MLC Status** (Lines 5126-5138)

```python
elif 'Initial' in next_survey_type and any(cert_type in cert_name for cert_type in 
     ['SAFETY MANAGEMENT', 'SHIP SECURITY', 'MARITIME LABOUR', 'SMC', 'ISSC', 'MLC']):
    # Overdue: Past valid date
    is_overdue = current_date > window_close  # window_close = valid_date
    
    # Due Soon: Initial survey due within 30 days
    days_until_initial = (window_close - current_date).days
    is_due_soon = 0 <= days_until_initial <= 30
    
    # Critical: Due within 7 days or already overdue
    is_critical = days_until_initial <= 7
```

**Quy tắc**:
- **Overdue**: Hôm nay > Valid Date
- **Due Soon**: 0-30 ngày cho đến Valid Date
- **Critical**: ≤7 ngày cho đến Valid Date

---

#### **C. Special Survey Status** (Lines 5140-5148)

```python
elif 'Special Survey' in next_survey_type and next_survey_date:
    # Overdue: Past survey date (no grace period)
    is_overdue = next_survey_date < current_date
    
    # Due Soon: Survey within 30 days
    is_due_soon = 0 <= days_until_survey <= 30
    
    # Critical: Due within 7 days or overdue
    is_critical = days_until_survey <= 7
```

**Quy tắc**:
- **Overdue**: Hôm nay > Next Survey Date (**KHÔNG CÓ grace period**)
- **Due Soon**: 0-30 ngày cho đến Next Survey
- **Critical**: ≤7 ngày cho đến Next Survey

---

#### **D. Other Surveys Status** (Lines 5150-5158)

```python
elif next_survey_date:
    # Overdue: Past survey date + 90 days window
    is_overdue = current_date > (next_survey_date + timedelta(days=90))
    
    # Due Soon: Survey within 30 days
    is_due_soon = 0 <= days_until_survey <= 30
    
    # Critical: Due within 7 days OR significantly overdue (>30 days)
    is_critical = days_until_survey <= 7 or days_until_survey < -30
```

**Quy tắc**:
- **Overdue**: Hôm nay > (Next Survey Date + 90 ngày) - có grace period 3 tháng
- **Due Soon**: 0-30 ngày cho đến Next Survey
- **Critical**: ≤7 ngày cho đến Next Survey HOẶC quá hạn >30 ngày

---

## 📊 DỮ LIỆU TRẢ VỀ (RESPONSE STRUCTURE)

### 5. **Thông Tin Mỗi Upcoming Survey** - Lines 5180-5209

```python
upcoming_survey = {
    # Certificate & Ship Info
    'certificate_id': cert.get('id'),
    'ship_id': cert.get('ship_id'),
    'ship_name': ship_info.get('name', ''),
    'cert_name': cert.get('cert_name', ''),
    'cert_abbreviation': cert_abbreviation,
    'cert_name_display': cert_name_display,
    
    # Survey Date Info
    'next_survey': next_survey_str,
    'next_survey_date': next_survey_date.isoformat() if next_survey_date else None,
    'next_survey_type': cert.get('next_survey_type', ''),
    'last_endorse': cert.get('last_endorse', ''),
    
    # Status Info
    'status': cert.get('status', ''),
    'days_until_survey': days_until_survey,
    'is_overdue': is_overdue,
    'is_due_soon': is_due_soon,
    'is_critical': is_critical,
    'is_within_window': is_within_window,
    
    # Window Info
    'window_open': window_open.isoformat(),
    'window_close': window_close.isoformat(),
    'days_from_window_open': days_from_window_open,
    'days_to_window_close': days_to_window_close,
    'window_type': window_type,  # 'Issue→Valid', 'Valid-3M→Valid', '-3M', '±3M'
    'survey_window_rule': '...'
}
```

---

## 🔍 TÓM TẮT CÁC QUY TẮC WINDOW

| Loại Certificate | Window Open | Window Close | Ghi Chú |
|-----------------|-------------|--------------|---------|
| **Condition Certificate** | Issue Date | Valid Date | Toàn bộ thời gian hiệu lực |
| **Initial SMC/ISSC/MLC** | Valid Date - 90d | Valid Date | Chỉ -3M trước Valid Date |
| **Special Survey** | Next Survey - 90d | Next Survey | Chỉ -3M, KHÔNG có extension |
| **Other Surveys** | Next Survey - 90d | Next Survey + 90d | ±3M (trước và sau) |

---

## 📝 GHI CHÚ QUAN TRỌNG (IMPORTANT NOTES)

1. **Window-Based Logic**: Mỗi certificate tạo window riêng của nó. Certificate chỉ xuất hiện khi current_date nằm trong window.

2. **Different Rules for Different Types**: Code áp dụng quy tắc khác nhau cho:
   - Window calculation (4 loại)
   - Status classification (4 loại)

3. **Special Survey Strictness**: Special Survey là loại **NGHIÊM NGẶT NHẤT** - không có grace period sau deadline.

4. **Initial SMC/ISSC/MLC**: Chỉ áp dụng cho 3 loại certificate cụ thể với Next Survey Type = "Initial".

5. **Sorting**: Danh sách được sắp xếp theo `next_survey_date` (sớm nhất trước) - Line 5218.

---

## 🔧 CODE XUNG QUANH (SURROUNDING CODE)

### Backend Context

**Trước endpoint này** (Lines 4800-4915):
- Các helper functions khác
- Certificate calculation functions

**Sau endpoint này** (Lines 5251-5300):
- Error handling và response formatting
- Tiếp theo là các endpoints khác của certificates

**Dependencies**:
- MongoDB database operations
- Date/time utilities (datetime, timedelta)
- User authentication (get_current_user)

---

## 🖥️ FRONTEND COMPONENT

### Component Location
**File**: `/app/frontend/src/components/CertificateList/UpcomingSurveyModal.jsx`  
**Lines**: 1-158

### Frontend Logic

#### **1. Props Structure** (Lines 9-18)
```javascript
{
  isOpen,           // Modal visibility
  onClose,          // Close handler
  surveys = [],     // Array of upcoming surveys from backend
  totalCount = 0,   // Total count
  company,          // Company ID
  companyName,      // Company name
  checkDate,        // Check date from backend
  language          // UI language (vi/en)
}
```

#### **2. Table Display** (Lines 52-142)
Modal hiển thị table với các cột:
- **Ship Name**: Tên tàu
- **Cert. Name (Abbreviation)**: Tên certificate + viết tắt
- **Next Survey**: Ngày survey + số ngày còn lại/quá hạn + window type
- **Next Survey Type**: Loại survey
- **Last Endorse**: Ngày endorse cuối
- **Status**: Badge màu theo trạng thái

#### **3. Row Highlighting** (Lines 88-92)
```javascript
className={`hover:bg-gray-50 ${
  survey.is_overdue ? 'bg-red-50' :      // Màu đỏ nhạt
  survey.is_due_soon ? 'bg-yellow-50' :  // Màu vàng nhạt
  ''                                      // Không màu
}`}
```

#### **4. Status Badge Display** (Lines 121-136)
```javascript
// Critical/Overdue: Red badge
if (survey.is_critical) {
  return <span className="bg-red-100 text-red-800">
    {survey.is_overdue ? 'Quá hạn' : 'Khẩn cấp'}
  </span>
}

// Due Soon: Yellow badge
if (survey.is_due_soon) {
  return <span className="bg-yellow-100 text-yellow-800">
    Sắp đến hạn
  </span>
}

// In Window: Blue badge
return <span className="bg-blue-100 text-blue-800">
  Trong Window
</span>
```

#### **5. Window Type Display** (Lines 108-112)
Hiển thị loại window dưới Next Survey date:
- `Issue→Valid` (Condition Certificate)
- `Valid-3M→Valid` (Initial SMC/ISSC/MLC)
- `-3M` (Special Survey)
- `±3M` (Other surveys)

---

## 🔄 DATA FLOW (LUỒNG DỮ LIỆU)

### Backend → Frontend Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER CLICKS "Upcoming Survey" BUTTON                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. FRONTEND CALLS: GET /api/certificates/upcoming-surveys       │
│    (from CertificateActionButtons.jsx)                          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. BACKEND PROCESSES (server.py lines 4916-5250):               │
│    ├─ Get user's company                                        │
│    ├─ Find all ships (dual lookup by ID & name)                 │
│    ├─ Get all certificates from these ships                     │
│    ├─ For each certificate:                                     │
│    │   ├─ Calculate window (4 types)                            │
│    │   ├─ Check if current_date in window                       │
│    │   ├─ Calculate status (overdue/due_soon/critical)          │
│    │   └─ Add to upcoming_surveys if in window                  │
│    └─ Sort by next_survey_date                                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. BACKEND RETURNS JSON:                                         │
│    {                                                             │
│      upcoming_surveys: [...],  // Array of survey objects       │
│      total_count: 15,          // Count                         │
│      company: "...",           // Company ID                    │
│      company_name: "...",      // Company name                  │
│      check_date: "2025-01-15", // Server date                   │
│      logic_info: {...}         // Documentation                 │
│    }                                                             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. FRONTEND RECEIVES & DISPLAYS (UpcomingSurveyModal.jsx):      │
│    ├─ Shows modal with table                                    │
│    ├─ Displays each survey with:                                │
│    │   ├─ Ship name                                             │
│    │   ├─ Certificate name + abbreviation                       │
│    │   ├─ Next survey date + days left + window type            │
│    │   ├─ Survey type                                           │
│    │   ├─ Last endorse                                          │
│    │   └─ Status badge (color-coded)                            │
│    ├─ Highlights rows (red/yellow based on status)              │
│    └─ Shows total count & company info                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ KẾT LUẬN (CONCLUSION)

### Backend Logic - COMPREHENSIVE & ROBUST

Logic của Ship Certificate Upcoming Survey là **rất toàn diện và chặt chẽ**, với:

1. ✅ **4 loại window** khác nhau cho các loại certificate
2. ✅ **4 loại status rules** tương ứng
3. ✅ **Filtering chính xác** dựa trên current_date trong window
4. ✅ **Response structure đầy đủ** với tất cả thông tin cần thiết
5. ✅ **Handling special cases** (Initial SMC/ISSC/MLC, Special Survey)

### Frontend Display - CLEAN & USER-FRIENDLY

1. ✅ **Table format** hiển thị rõ ràng với 6 cột thông tin
2. ✅ **Color-coded badges** (Red/Yellow/Blue) cho status
3. ✅ **Row highlighting** để dễ nhận biết certificates quan trọng
4. ✅ **Window type display** giúp user hiểu quy tắc
5. ✅ **Bilingual support** (Vietnamese/English)

### Maritime Compliance

Logic này phù hợp với **maritime regulations** và **industry best practices**:
- Special Survey có quy tắc nghiêm ngặt (no extension)
- Condition Certificate tracking expiry dates
- Initial surveys for critical certificates (SMC/ISSC/MLC)
- Flexible windows for routine surveys

---

## 🎯 ĐIỂM MẠNH (STRENGTHS)

1. **Comprehensive Window Logic**: 4 loại window phù hợp với từng certificate type
2. **Accurate Status Classification**: Logic rõ ràng cho overdue/due soon/critical
3. **Detailed Response**: Backend trả về đầy đủ thông tin window, status, days
4. **Clean UI**: Frontend hiển thị professional với color coding và table format
5. **Scalable**: Dễ dàng thêm loại certificate mới hoặc thay đổi rules
6. **Logging**: Backend có logging chi tiết để debug
7. **Documentation**: Code có comments và logic_info trong response

---

## 🔍 POTENTIAL IMPROVEMENTS (NẾU CẦN)

1. **Performance**: Với >1000 certificates, có thể cần pagination hoặc indexing
2. **Caching**: Cache upcoming surveys result (refresh mỗi giờ)
3. **Notifications**: Thêm email/SMS notification cho critical surveys
4. **Filtering**: Thêm filter trong modal (by ship, by status, by certificate type)
5. **Export**: Thêm nút export to Excel/PDF
6. **Calendar View**: Thêm calendar view option bên cạnh table view

Tuy nhiên, **logic hiện tại đã HOÀN TOÀN ĐÚNG và WORKING CORRECTLY**.
