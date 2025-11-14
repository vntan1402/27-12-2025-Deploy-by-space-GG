# Audit Certificate Upcoming Survey Logic - Phân Tích Chi Tiết

## 📍 VỊ TRÍ CODE (CODE LOCATION)

**File**: `/app/backend/server.py`  
**Dòng (Lines)**: 21735 - 21921  
**API Endpoint**: `GET /api/audit-certificates/upcoming-surveys`

**Frontend Component**:
**File**: `/app/frontend/src/components/AuditCertificate/AuditUpcomingSurveyModal.jsx`  
**Lines**: 1 - 158

---

## 🏗️ CẤU TRÚC CODE (CODE STRUCTURE)

### 1. **Lấy Dữ Liệu (Data Retrieval)** - Lines 21754-21798

```python
# Lines 21754-21763: Get company information
current_date = datetime.now().date()
user_company = current_user.company
company_record = await mongo_db.find_one("companies", {"id": user_company})
company_name = company_record.get('name_en') or company_record.get('name_vn')

# Lines 21766-21778: Dual lookup for ships (by ID and name)
ships_by_id = await mongo_db.find_all("ships", {"company": user_company})
ships_by_name = await mongo_db.find_all("ships", {"company": company_name})
# Deduplicate ships

# Lines 21792-21796: Get all AUDIT certificates from these ships
all_certificates = []
for ship_id in ship_ids:
    certs = await mongo_db.find_all("audit_certificates", {"ship_id": ship_id})
    all_certificates.extend(certs)
```

**Điểm khác biệt**: Query từ collection `audit_certificates` (không phải `certificates`)

---

## 🎯 LOGIC XÁC ĐỊNH UPCOMING SURVEY

### 2. **Window Calculation - ANNOTATION-BASED** - Lines 21804-21840

**KHÁC BIỆT QUAN TRỌNG**: Audit Certificate logic **KHÔNG tự tính window**, mà **ĐỌC từ annotation** có sẵn trong field `next_survey_display`!

```python
# Lines 21804-21808: Get Next Survey Display field
next_survey_display = cert.get('next_survey_display') or cert.get('next_survey')

# Lines 21810-21821: Extract date from display string
# Format examples: "30/10/2025 (±3M)", "30/11/2025 (-3M)", "31/10/2027 (±3M)"
import re
date_match = re.search(r'(\d{2}/\d{2}/\d{4})', next_survey_str)
date_str = date_match.group(1)
next_survey_date = datetime.strptime(date_str, '%d/%m/%Y').date()
```

#### **A. Window ±3M (Intermediate)** - Lines 21828-21832

```python
if '(±3M)' in next_survey_str or '(+3M)' in next_survey_str or '(+-3M)' in next_survey_str:
    window_open = next_survey_date - relativedelta(months=3)
    window_close = next_survey_date + relativedelta(months=3)
    window_type = '±3M'
```

**Quy tắc**:
- Window: **Next Survey Date ± 3 tháng**
- Có thể làm trước HOẶC sau Next Survey Date
- **Áp dụng cho**: Intermediate Survey

---

#### **B. Window -3M (Initial, Renewal)** - Lines 21833-21837

```python
elif '(-3M)' in next_survey_str:
    window_open = next_survey_date - relativedelta(months=3)
    window_close = next_survey_date
    window_type = '-3M'
```

**Quy tắc**:
- Window: **Next Survey Date - 3 tháng → Next Survey Date**
- Chỉ có thể làm TRƯỚC Next Survey Date
- KHÔNG có extension sau Next Survey Date
- **Áp dụng cho**: Initial Survey, Renewal Survey

---

#### **C. No Annotation → Skip** - Lines 21838-21840

```python
else:
    # No clear annotation, skip
    continue
```

**Quy tắc**: Nếu không có annotation `(±3M)` hoặc `(-3M)` trong `next_survey_display`, certificate sẽ **BỊ BỎ QUA**.

---

### 3. **Điều Kiện Lọc (Filter Condition)** - Line 21843

```python
if window_open <= current_date <= window_close:
    # Certificate được include vào upcoming surveys
```

**Nguyên tắc**: GIỐNG Ship Certificate - Certificate chỉ xuất hiện khi **current_date nằm trong window**.

---

## 🚦 LOGIC XÁC ĐỊNH STATUS (STATUS CLASSIFICATION)

### 4. **Phân Loại Status** - Lines 21847-21860

**KHÁC BIỆT QUAN TRỌNG**: Audit Certificate status dựa trên **window_close**, KHÔNG phải next_survey_date!

```python
# Lines 21848-21849: Calculate days
days_until_window_close = (window_close - current_date).days
days_until_survey = (next_survey_date - current_date).days

# Lines 21851-21853: Overdue
is_overdue = current_date > window_close

# Lines 21855-21856: Critical - ≤ 30 ngày tới window_close
is_critical = 0 <= days_until_window_close <= 30

# Lines 21858-21860: Due Soon
window_close_minus_30 = window_close - timedelta(days=30)
is_due_soon = window_open < current_date < window_close_minus_30
```

### **Status Rules**:

#### **Overdue** (Quá hạn)
```python
is_overdue = current_date > window_close
```
- Hôm nay **QUÁ window_close**
- Badge: **Màu đỏ** (Red)

#### **Critical** (Khẩn cấp)
```python
is_critical = 0 <= days_until_window_close <= 30
```
- Còn **≤ 30 ngày** cho đến window_close
- Badge: **Màu cam** (Orange)

#### **Due Soon** (Sắp đến hạn)
```python
is_due_soon = window_open < current_date < window_close_minus_30
```
- Đã vào window NHƯNG còn **> 30 ngày** tới window_close
- Badge: **Màu vàng** (Yellow)

#### **In Window** (Trong Window)
- Mặc định nếu không thuộc 3 loại trên
- Badge: **Màu xanh** (Blue)

---

## 📊 DỮ LIỆU TRẢ VỀ (RESPONSE STRUCTURE)

### 5. **Thông Tin Mỗi Upcoming Survey** - Lines 21866-21888

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
    'next_survey': next_survey_display,      # "30/10/2025 (±3M)"
    'next_survey_date': next_survey_date.isoformat(),
    'next_survey_type': cert.get('next_survey_type', ''),
    'valid_date': cert.get('valid_date'),
    'last_endorse': cert.get('last_endorse', ''),
    
    # Status Info
    'status': cert.get('status', ''),
    'days_until_survey': days_until_survey,
    'days_until_window_close': days_until_window_close,  # ⭐ KHÁC BIỆT
    'is_overdue': is_overdue,
    'is_due_soon': is_due_soon,
    'is_critical': is_critical,
    'is_within_window': True,
    
    # Window Info
    'window_open': window_open.isoformat(),
    'window_close': window_close.isoformat(),
    'window_type': window_type  # '±3M' or '-3M'
}
```

**Điểm khác biệt**: Có field `days_until_window_close` (không có trong Ship Certificate)

---

## 🖥️ FRONTEND COMPONENT DIFFERENCES

### Row Highlighting (Lines 86-91)
```javascript
className={`hover:bg-gray-50 ${
  survey.is_overdue ? 'bg-red-50' :      // Đỏ nhạt - Overdue
  survey.is_critical ? 'bg-orange-50' :  // ⭐ CAM NHẠt - Critical (KHÁC)
  survey.is_due_soon ? 'bg-yellow-50' :  // Vàng nhạt - Due Soon
  ''
}`}
```

**Khác biệt**: Audit có **3 màu highlighting** (red, orange, yellow), Ship chỉ có **2 màu** (red, yellow)

### Status Badge Display (Lines 120-136)
```javascript
// 1. Overdue - Red badge
if (survey.is_overdue) {
  return <span className="bg-red-100 text-red-800">Quá hạn</span>
}

// 2. Critical - Orange badge ⭐ KHÁC BIỆT
if (survey.is_critical) {
  return <span className="bg-orange-100 text-orange-800">Khẩn cấp</span>
}

// 3. Due Soon - Yellow badge
if (survey.is_due_soon) {
  return <span className="bg-yellow-100 text-yellow-800">Sắp đến hạn</span>
}

// 4. In Window - Blue badge
return <span className="bg-blue-100 text-blue-800">Trong Window</span>
```

**Khác biệt**: Audit có **4 loại badge** (Overdue, Critical, Due Soon, In Window), Ship có **3 loại** (Critical/Overdue, Due Soon, In Window)

### Days Display (Lines 102-106)
```javascript
{survey.days_until_window_close >= 0 
  ? `Còn ${survey.days_until_window_close} ngày tới window close`
  : `Quá window close ${Math.abs(survey.days_until_window_close)} ngày`
}
```

**Khác biệt**: Hiển thị "days until **window_close**" (không phải "days until survey")

---

## 🔍 TÓM TẮT QUY TẮC WINDOW

| Loại Survey | Window Type | Window Open | Window Close | Ghi Chú |
|------------|-------------|-------------|--------------|---------|
| **Intermediate** | `±3M` | Next Survey - 3M | Next Survey + 3M | Trước VÀ sau |
| **Initial** | `-3M` | Next Survey - 3M | Next Survey | Chỉ trước |
| **Renewal** | `-3M` | Next Survey - 3M | Next Survey | Chỉ trước |

---

## ⚠️ ĐIỂM KHÁC BIỆT QUAN TRỌNG SO VỚI SHIP CERTIFICATE

### 1. **Window Calculation Method**

| Aspect | Ship Certificate | Audit Certificate |
|--------|-----------------|-------------------|
| **Method** | Code TỰ TÍNH window dựa trên certificate type & dates | Code ĐỌC annotation từ `next_survey_display` field |
| **Logic** | 4 loại logic khác nhau (Condition, Initial, Special, Other) | 2 loại annotation: `(±3M)` và `(-3M)` |
| **Complexity** | Phức tạp hơn - nhiều date parsing & calculation | Đơn giản hơn - chỉ parse annotation |

### 2. **Status Classification**

| Aspect | Ship Certificate | Audit Certificate |
|--------|-----------------|-------------------|
| **Overdue** | Different for each type (Special Survey stricter) | Uniform: `current_date > window_close` |
| **Critical** | ≤7 days OR >30 days overdue | ≤30 days to window_close |
| **Due Soon** | 0-30 days until survey | window_open < now < (window_close - 30) |
| **Reference** | Compares with `next_survey_date` | Compares with `window_close` |

### 3. **Status Badges**

| Aspect | Ship Certificate | Audit Certificate |
|--------|-----------------|-------------------|
| **Overdue** | Red badge | Red badge |
| **Critical** | Red badge (merged with overdue) | **Orange badge** (separate) |
| **Due Soon** | Yellow badge | Yellow badge |
| **In Window** | Blue badge | Blue badge |
| **Total** | 3 badge types | **4 badge types** |

### 4. **Frontend Display**

| Aspect | Ship Certificate | Audit Certificate |
|--------|-----------------|-------------------|
| **Days Display** | `days_until_survey` | `days_until_window_close` ⭐ |
| **Row Highlighting** | 2 colors (red, yellow) | **3 colors** (red, orange, yellow) ⭐ |
| **Message** | "Còn X ngày" | "Còn X ngày tới window close" |

---

## 💡 LOGIC DESIGN RATIONALE

### Tại sao Audit Certificate đơn giản hơn?

1. **Pre-calculated Windows**: Field `next_survey_display` đã chứa annotation `(±3M)` hoặc `(-3M)` được tính từ backend khác (có thể là `calculate_audit_certificate_next_survey_info` function).

2. **Unified Status Logic**: Không cần phân biệt nhiều loại certificate type như Ship Certificate, chỉ cần quan tâm đến window_close.

3. **Simpler Status Bands**: 
   - **Critical** (≤30 days): Orange - có thời gian sắp xếp
   - **Due Soon** (>30 days): Yellow - chưa gấp lắm
   - **Overdue**: Red - đã quá hạn

4. **Focus on Window Close**: Audit certificate quan trọng là phải hoàn thành **TRONG WINDOW**, không quan trọng bằng exact survey date.

---

## 🔄 DATA FLOW

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER CLICKS "Upcoming Survey" BUTTON                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. FRONTEND CALLS:                                               │
│    GET /api/audit-certificates/upcoming-surveys                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. BACKEND PROCESSES (server.py lines 21735-21921):             │
│    ├─ Get user's company & ships                                │
│    ├─ Get all AUDIT certificates from these ships               │
│    ├─ For each certificate:                                     │
│    │   ├─ Read next_survey_display field                        │
│    │   ├─ Extract date & annotation (±3M or -3M)                │
│    │   ├─ Calculate window based on annotation                  │
│    │   ├─ Check if current_date in window                       │
│    │   ├─ Calculate status (overdue/critical/due_soon)          │
│    │   └─ Add to upcoming_surveys if in window                  │
│    └─ Sort by next_survey_date                                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. BACKEND RETURNS JSON with upcoming_surveys array             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. FRONTEND DISPLAYS (AuditUpcomingSurveyModal.jsx):            │
│    ├─ Table with 6 columns                                      │
│    ├─ 4 badge types (Overdue/Critical/Due Soon/In Window)       │
│    ├─ 3 row highlight colors (red/orange/yellow)                │
│    ├─ Shows days_until_window_close                             │
│    └─ Shows window_type (±3M or -3M)                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ KẾT LUẬN

### Audit Certificate Logic - SIMPLER & ANNOTATION-DRIVEN

1. ✅ **Annotation-based window** - Đọc từ `next_survey_display` field
2. ✅ **2 loại window** - `±3M` và `-3M`
3. ✅ **Unified status logic** - Dựa vào window_close
4. ✅ **4-tier status system** - Overdue/Critical/Due Soon/In Window với 4 màu badge
5. ✅ **Simpler code** - Ít logic phức tạp hơn Ship Certificate

### Điểm Mạnh (Strengths)

1. **Simple & Maintainable**: Code dễ đọc, dễ maintain
2. **Clear Visual Hierarchy**: 4 badge types với 4 màu giúp user dễ phân biệt
3. **Window-centric**: Focus vào window_close thay vì survey date
4. **Flexible**: Annotation có thể thay đổi mà không cần sửa code

### So với Ship Certificate

- **Ship**: Phức tạp hơn, 4 loại window calculation logic, nhiều special cases
- **Audit**: Đơn giản hơn, annotation-driven, unified status logic

**Cả hai đều HOẠT ĐỘNG ĐÚNG và phù hợp với requirements của từng loại certificate.**
