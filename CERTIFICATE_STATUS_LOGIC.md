# Logic Tính Toán và Hiển Thị Ship Certificate Status

## Tổng quan

Certificate Status được tính toán **hoàn toàn ở Frontend** dựa trên các trường dữ liệu từ Backend. Status không được lưu trong database mà được tính toán realtime mỗi khi hiển thị.

---

## 1. CÁC TRẠNG THÁI (STATUS)

| Status | Tiếng Việt | Màu sắc | Mô tả |
|--------|------------|---------|-------|
| **Valid** | Còn hiệu lực | 🟢 Xanh lá (`bg-green-100`) | Certificate còn hiệu lực |
| **Due Soon** | Sắp hết hạn | 🟠 Cam (`bg-orange-100`) | Sắp đến hạn kiểm tra/hết hạn |
| **Over Due** | Quá hạn | 🟠 Cam (`bg-orange-100`) | Đã quá hạn kiểm tra (Class & Flag) |
| **Expired** | Hết hiệu lực | 🔴 Đỏ (`bg-red-100`) | Certificate đã hết hạn |

---

## 2. NGUỒN DỮ LIỆU ĐỂ TÍNH STATUS

### 2.1 Thứ tự ưu tiên

```
Priority 1: next_survey_display / next_survey (nếu có)
    ↓ (nếu không có hoặc = "N/A")
Priority 2: valid_date
    ↓ (nếu không có valid_date)
Default: "Valid"
```

### 2.2 Các trường dữ liệu

| Trường | Mô tả | Format |
|--------|-------|--------|
| `next_survey_display` | Ngày kiểm tra tiếp theo (hiển thị) | `"28/06/2026 (±3M)"` |
| `next_survey` | Ngày kiểm tra tiếp theo (ISO) | `"2026-06-28T00:00:00Z"` |
| `valid_date` | Ngày hết hạn certificate | `"28/06/2028"` hoặc `"2028-06-28"` |

---

## 3. LOGIC TÍNH TOÁN CHI TIẾT

### 3.1 Function chính: `getCertificateStatusFromDate()`

**File**: `/app/frontend/src/utils/dateHelpers.js`

```javascript
export const getCertificateStatusFromDate = (cert, options = {}) => {
  const dueSoonDays = options.dueSoonDays || 90;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  // ========== PRIORITY 1: CHECK NEXT_SURVEY ==========
  const nextSurvey = cert.next_survey_display || cert.next_survey;
  const hasValidNextSurvey = nextSurvey && nextSurvey !== 'N/A' && nextSurvey !== 'n/a';
  
  if (hasValidNextSurvey) {
    // Extract date from "DD/MM/YYYY (±XM)" format
    const match = nextSurvey.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})/);
    
    if (match) {
      const nextSurveyDate = new Date(year, month - 1, day);
      
      // Calculate window_close based on annotation
      let windowClose = new Date(nextSurveyDate);
      
      if (nextSurvey.includes('(±6M)')) {
        windowClose.setMonth(windowClose.getMonth() + 6);
      } else if (nextSurvey.includes('(±3M)')) {
        windowClose.setMonth(windowClose.getMonth() + 3);
      }
      // For (-3M) or (-6M): windowClose = nextSurveyDate
      
      if (today > windowClose) return 'Expired';
      
      const diffDays = Math.ceil((windowClose - today) / (1000 * 60 * 60 * 24));
      if (diffDays <= dueSoonDays) return 'Due Soon';
      return 'Valid';
    }
  }
  
  // ========== PRIORITY 2: CHECK VALID_DATE ==========
  if (!cert.valid_date) return 'Valid';  // No valid_date = always Valid
  
  const validDate = parseDdMmYyyy(cert.valid_date);
  if (!validDate) return 'Valid';  // Can't parse = treat as Valid
  
  if (validDate < today) return 'Expired';
  
  const diffDays = Math.ceil((validDate - today) / (1000 * 60 * 60 * 24));
  if (diffDays <= dueSoonDays) return 'Due Soon';
  return 'Valid';
};
```

### 3.2 Date Parsing Function: `parseDdMmYyyy()`

```javascript
export const parseDdMmYyyy = (dateStr) => {
  // Handle DD/MM/YYYY format
  const ddmmyyyyPattern = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
  const match = ddmmyyyyPattern.exec(dateStr.trim());
  
  if (match) {
    const day = parseInt(match[1], 10);
    const month = parseInt(match[2], 10) - 1;  // 0-indexed
    const year = parseInt(match[3], 10);
    return new Date(year, month, day, 0, 0, 0, 0);
  }
  
  // Handle YYYY-MM-DD (ISO) format
  const isoPattern = /^(\d{4})-(\d{1,2})-(\d{1,2})/;
  const isoMatch = isoPattern.exec(dateStr.trim());
  
  if (isoMatch) {
    return new Date(year, month - 1, day, 0, 0, 0, 0);
  }
  
  return null;
};
```

---

## 4. CẤU HÌNH THEO LOẠI CERTIFICATE

### 4.1 Class & Flag Certificates

**Pages**: `ClassAndFlagCert.jsx`, `CertificateTable.jsx`

| Cấu hình | Giá trị |
|----------|---------|
| `dueSoonDays` | **30 ngày** |
| Status mapping | `"Due Soon"` → `"Over Due"` |

```javascript
// ClassAndFlagCert.jsx
const getCertificateStatus = (cert) => {
  const status = getCertificateStatusFromDate(cert, { dueSoonDays: 30 });
  return status === 'Due Soon' ? 'Over Due' : status;
};
```

### 4.2 Audit Certificates (ISM/ISPS/MLC)

**Pages**: `IsmIspsMLc.jsx`, `AuditCertificateTable.jsx`

| Cấu hình | Giá trị |
|----------|---------|
| `dueSoonDays` | **90 ngày** |
| Status mapping | Giữ nguyên (`"Due Soon"`) |

```javascript
// IsmIspsMLc.jsx
const getCertificateStatus = (cert) => {
  return getCertificateStatusFromDate(cert, { dueSoonDays: 90 });
};
```

---

## 5. LOGIC TÍNH WINDOW CLOSE

### 5.1 Dựa trên annotation trong `next_survey_display`

| Annotation | Window Close |
|------------|--------------|
| `(±6M)` hoặc `(+-6M)` | next_survey_date + 6 tháng |
| `(±3M)` hoặc `(+-3M)` | next_survey_date + 3 tháng |
| `(-3M)` hoặc `(-6M)` | next_survey_date (không cộng thêm) |
| Không có annotation | next_survey_date |

### 5.2 Ví dụ

```
next_survey_display = "28/06/2026 (±3M)"
→ next_survey_date = 28/06/2026
→ window_close = 28/09/2026 (+3 tháng)

Today = 29/12/2025
window_close - today = ~9 tháng = 270 ngày

Với dueSoonDays = 90:
270 > 90 → Status = "Valid"
```

---

## 6. HIỂN THỊ TRÊN UI

### 6.1 Màu sắc CSS

```jsx
<span className={`px-2 py-1 rounded-full text-xs font-medium ${
  status === 'Valid' ? 'bg-green-100 text-green-800' :
  status === 'Expired' ? 'bg-red-100 text-red-800' :
  status === 'Due Soon' ? 'bg-orange-100 text-orange-800' :
  status === 'Over Due' ? 'bg-orange-100 text-orange-800' :
  'bg-gray-100 text-gray-800'
}`}>
  {status === 'Valid' ? 'Còn hiệu lực' :
   status === 'Expired' ? 'Hết hiệu lực' :
   status === 'Due Soon' ? 'Sắp hết hạn' :
   status === 'Over Due' ? 'Quá hạn' : 'Unknown'}
</span>
```

### 6.2 Sorting by Status

```javascript
// Sort priority: Expired (1) > Due Soon/Over Due (2) > Valid (3)
const statusPriority = { 'Expired': 1, 'Due Soon': 2, 'Over Due': 2, 'Valid': 3 };

// Sort function
filtered.sort((a, b) => {
  if (sortColumn === 'status') {
    const aStatus = getCertificateStatus(a);
    const bStatus = getCertificateStatus(b);
    const aVal = statusPriority[aStatus] || 4;
    const bVal = statusPriority[bStatus] || 4;
    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  }
  // ... other columns
});
```

---

## 7. SƠ ĐỒ FLOW TÍNH STATUS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CERTIFICATE STATUS CALCULATION FLOW                       │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────┐
                    │   Certificate Data    │
                    │  from Backend API     │
                    │  - next_survey_display│
                    │  - valid_date         │
                    └───────────┬───────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │  Has next_survey_display?     │
                │  (not null, not "N/A")        │
                └───────────────┬───────────────┘
                                │
              ┌─────────────────┴─────────────────┐
              │ YES                               │ NO
              ▼                                   ▼
    ┌─────────────────────┐           ┌─────────────────────┐
    │ Parse next_survey   │           │  Has valid_date?    │
    │ Extract date +      │           └──────────┬──────────┘
    │ annotation          │                      │
    └──────────┬──────────┘          ┌───────────┴───────────┐
               │                     │ YES                   │ NO
               ▼                     ▼                       ▼
    ┌─────────────────────┐   ┌─────────────────┐   ┌─────────────┐
    │ Calculate           │   │ Parse           │   │ Return      │
    │ window_close:       │   │ valid_date      │   │ "Valid"     │
    │ ±3M: +3 months      │   │ (DD/MM/YYYY)    │   └─────────────┘
    │ ±6M: +6 months      │   └────────┬────────┘
    │ -3M/-6M: no change  │            │
    └──────────┬──────────┘            │
               │                       │
               ▼                       ▼
    ┌─────────────────────────────────────────────┐
    │              Compare with TODAY              │
    └─────────────────────────────────────────────┘
               │
               ▼
    ┌─────────────────────────────────────────────┐
    │  date < today?                              │
    │  ─────────────                              │
    │  YES → "Expired"                            │
    │                                             │
    │  date - today <= dueSoonDays?               │
    │  ──────────────────────────────             │
    │  YES → "Due Soon" (or "Over Due")           │
    │                                             │
    │  Otherwise → "Valid"                        │
    └─────────────────────────────────────────────┘
```

---

## 8. TRƯỜNG HỢP ĐẶC BIỆT

### 8.1 Certificate không có valid_date
```
valid_date = null hoặc ""
→ Status = "Valid" (default)
```

### 8.2 Certificate không có next_survey
```
next_survey_display = null hoặc "N/A"
→ Fallback to valid_date
→ Nếu valid_date cũng null → "Valid"
```

### 8.3 Date format không parse được
```
valid_date = "invalid" hoặc format lạ
→ parseDdMmYyyy() return null
→ Status = "Valid" (safer default)
```

### 8.4 Special Survey annotation
```
next_survey_display = "28/06/2028 (-3M)"
→ window_close = 28/06/2028 (không cộng thêm)
→ So sánh trực tiếp với next_survey_date
```

---

## 9. FILES LIÊN QUAN

| File | Chức năng |
|------|-----------|
| `/app/frontend/src/utils/dateHelpers.js` | Functions chính: `getCertificateStatusFromDate()`, `parseDdMmYyyy()` |
| `/app/frontend/src/pages/ClassAndFlagCert.jsx` | Class & Flag certificates (30 days, "Over Due") |
| `/app/frontend/src/pages/IsmIspsMLc.jsx` | Audit certificates (90 days, "Due Soon") |
| `/app/frontend/src/components/CertificateList/CertificateTable.jsx` | Table component cho Class & Flag |
| `/app/frontend/src/components/AuditCertificate/AuditCertificateTable.jsx` | Table component cho Audit certs |

---

## 10. SO SÁNH GIỮA CÁC LOẠI CERTIFICATE

| Thuộc tính | Class & Flag | Audit (ISM/ISPS/MLC) |
|------------|--------------|----------------------|
| **dueSoonDays** | 30 ngày | 90 ngày |
| **Status label** | "Over Due" | "Due Soon" |
| **Primary date** | next_survey_display | next_survey_display |
| **Fallback date** | valid_date | valid_date |
| **Sort priority** | Expired > Over Due > Valid | Expired > Due Soon > Valid |

---

*Cập nhật lần cuối: 02/01/2026*
