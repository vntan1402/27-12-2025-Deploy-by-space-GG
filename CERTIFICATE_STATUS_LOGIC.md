# Logic Tính Toán và Hiển Thị Ship Certificate Status

## Tổng quan

Certificate Status được tính toán **real-time** ở **FRONTEND** dựa trên:
1. **Next Survey Date** và **Window annotation** (±3M hoặc -3M)
2. **Valid Date** (fallback khi không có Next Survey)

Status được hiển thị trong bảng certificate với các màu sắc khác nhau.

---

## 1. CÁC LOẠI STATUS

| Status | Màu sắc | Ý nghĩa |
|--------|---------|---------|
| **Valid** | 🟢 Xanh lá | Chứng chỉ còn hiệu lực |
| **Due Soon** | 🟡 Vàng | Sắp hết hạn (trong 30 ngày) |
| **Expired** | 🔴 Đỏ | Đã hết hiệu lực |
| **Unknown** | ⚪ Xám | Không xác định được (thiếu dữ liệu) |

---

## 2. LOGIC TÍNH STATUS

### 2.1 Sơ đồ tổng quan

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CERTIFICATE STATUS CALCULATION                          │
└─────────────────────────────────────────────────────────────────────────────┘

                           ┌──────────────────────┐
                           │   Certificate Data   │
                           │  - next_survey       │
                           │  - valid_date        │
                           └──────────┬───────────┘
                                      │
                                      ▼
               ┌──────────────────────────────────────┐
               │   Has valid next_survey?             │
               │   (not null, not "N/A")              │
               └──────────────┬───────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
        ┌───────────┐                   ┌───────────┐
        │   YES     │                   │   NO      │
        │ (có Next  │                   │ (không có │
        │  Survey)  │                   │  Next     │
        └─────┬─────┘                   │  Survey)  │
              │                         └─────┬─────┘
              │                               │
              ▼                               ▼
    ┌─────────────────────┐         ┌─────────────────────┐
    │ Parse Next Survey   │         │ Use Valid Date      │
    │ & Calculate         │         │ as Reference        │
    │ Window Close        │         └─────────┬───────────┘
    └─────────┬───────────┘                   │
              │                               │
              ▼                               ▼
    ┌─────────────────────┐         ┌─────────────────────┐
    │ Compare Today vs    │         │ Compare Today vs    │
    │ Window Close        │         │ Valid Date          │
    └─────────┬───────────┘         └─────────┬───────────┘
              │                               │
              └───────────────┬───────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   DETERMINE STATUS  │
                    │   - Expired         │
                    │   - Due Soon        │
                    │   - Valid           │
                    └─────────────────────┘
```

### 2.2 Logic chi tiết (Code Frontend)

**File:** `/app/frontend/src/components/CertificateList/CertificateTable.jsx`

```javascript
const getCertificateStatus = (cert) => {
  const nextSurvey = cert.next_survey_display || cert.next_survey;
  const hasValidNextSurvey = nextSurvey && nextSurvey !== 'N/A' && nextSurvey !== 'n/a';
  
  // ====== CASE 1: KHÔNG CÓ NEXT SURVEY ======
  if (!hasValidNextSurvey) {
    // Fallback: sử dụng Valid Date
    if (!cert.valid_date) return 'Unknown';
    
    const today = new Date();
    const validDate = new Date(cert.valid_date);
    
    if (validDate < today) return 'Expired';
    
    const diffDays = Math.ceil((validDate - today) / (1000 * 60 * 60 * 24));
    if (diffDays <= 30) return 'Due Soon';
    return 'Valid';
  }
  
  // ====== CASE 2: CÓ NEXT SURVEY ======
  // Parse ngày từ next_survey (format: "DD/MM/YYYY (±3M)")
  const match = nextSurvey.match(/(\d{2}\/\d{2}\/\d{4})/);
  if (!match) {
    // Không parse được → fallback về Valid Date
    // ... (same logic as Case 1)
  }
  
  const [day, month, year] = match[1].split('/');
  const nextSurveyDate = new Date(year, month - 1, day);
  
  // ====== TÍNH WINDOW CLOSE ======
  let windowClose = new Date(nextSurveyDate);
  
  if (nextSurvey.includes('(±3M)') || nextSurvey.includes('(+-3M)')) {
    // Annual Survey: window_close = next_survey + 3 tháng
    windowClose.setMonth(windowClose.getMonth() + 3);
  }
  // Special Survey (-3M): window_close = next_survey (không cộng thêm)
  
  // ====== SO SÁNH VỚI HÔM NAY ======
  const today = new Date();
  
  if (today > windowClose) return 'Expired';
  
  const diffDays = Math.ceil((windowClose - today) / (1000 * 60 * 60 * 24));
  if (diffDays <= 30) return 'Due Soon';
  return 'Valid';
};
```

---

## 3. WINDOW CLOSE CALCULATION

### 3.1 Quy tắc

| Next Survey Annotation | Window Close |
|----------------------|--------------|
| `28/06/2026 (±3M)` | 28/06/2026 + 3 tháng = **28/09/2026** |
| `28/06/2028 (-3M)` | **28/06/2028** (không cộng thêm) |
| `28/06/2026` (no annotation) | **28/06/2026** |

### 3.2 Ví dụ

```
Certificate: International Air Pollution Prevention Certificate
Next Survey Display: "28/06/2026 (±3M)"
Hôm nay: 02/01/2026

1. Parse date: 28/06/2026
2. Annotation: ±3M → window_close = 28/06/2026 + 3M = 28/09/2026
3. So sánh: 02/01/2026 < 28/09/2026
4. Diff days: 269 ngày > 30 ngày
5. Status: ✅ VALID
```

```
Certificate: Safety Equipment Certificate
Next Survey Display: "15/01/2026 (±3M)"
Hôm nay: 02/01/2026

1. Parse date: 15/01/2026
2. Annotation: ±3M → window_close = 15/01/2026 + 3M = 15/04/2026
3. So sánh: 02/01/2026 < 15/04/2026
4. Diff days: 103 ngày > 30 ngày
5. Status: ✅ VALID
```

```
Certificate: Load Line Certificate
Next Survey Display: "25/12/2025 (±3M)"
Hôm nay: 02/01/2026

1. Parse date: 25/12/2025
2. Annotation: ±3M → window_close = 25/12/2025 + 3M = 25/03/2026
3. So sánh: 02/01/2026 < 25/03/2026
4. Diff days: 82 ngày > 30 ngày
5. Status: ✅ VALID
```

```
Certificate: Class Certificate (Special Survey)
Next Survey Display: "15/12/2025 (-3M)"
Hôm nay: 02/01/2026

1. Parse date: 15/12/2025
2. Annotation: -3M → window_close = 15/12/2025 (không cộng)
3. So sánh: 02/01/2026 > 15/12/2025
4. Status: ❌ EXPIRED
```

---

## 4. HIỂN THỊ TRÊN GIAO DIỆN

### 4.1 CSS Classes

```javascript
// Trong CertificateTable.jsx
getCertificateStatus(cert) === 'Valid' 
  ? 'bg-green-100 text-green-800'   // Xanh lá
  : getCertificateStatus(cert) === 'Expired' 
    ? 'bg-red-100 text-red-800'     // Đỏ
    : 'bg-yellow-100 text-yellow-800' // Vàng (Due Soon)
```

### 4.2 Labels

| Status | Tiếng Việt | Tiếng Anh |
|--------|------------|-----------|
| Valid | Còn hiệu lực | Valid |
| Expired | Hết hiệu lực | Expired |
| Due Soon | Sắp hết hạn | Due Soon |

### 4.3 Tooltip

Khi hover vào status, hiển thị thông tin chi tiết:
- Số ngày còn lại / đã quá hạn
- Nguồn dữ liệu (Next Survey Date / Valid Date)

```javascript
// Tooltip content
if (daysRemaining >= 0) {
  tooltip = `${daysRemaining} days remaining\n(Based on ${source})`;
} else {
  tooltip = `Expired ${Math.abs(daysRemaining)} days ago\n(Based on ${source})`;
}
```

---

## 5. TRƯỜNG HỢP ĐẶC BIỆT

### 5.1 Interim Certificate

```
Next Survey: "N/A"
Valid Date: 15/06/2026
Hôm nay: 02/01/2026

→ Fallback về Valid Date
→ Status: Valid (còn 164 ngày)
```

### 5.2 Certificate không có Valid Date

```
Next Survey: null
Valid Date: null

→ Status: Unknown
```

### 5.3 Certificate chỉ có Valid Date (không có Next Survey)

```
Next Survey: null
Valid Date: 15/02/2026
Hôm nay: 02/01/2026

→ Dùng Valid Date làm reference
→ Diff: 44 ngày > 30 ngày
→ Status: Valid
```

---

## 6. FILES LIÊN QUAN

| File | Vai trò |
|------|---------|
| `/app/frontend/src/components/CertificateList/CertificateTable.jsx` | Logic tính status (Frontend) |
| `/app/backend/app/services/audit_certificate_service.py` | Default status = "Valid" |
| `/app/backend/app/utils/ship_calculations.py` | Tính Next Survey + Window |

---

## 7. LƯU Ý QUAN TRỌNG

1. **Status được tính REAL-TIME**: Mỗi lần render bảng, status được tính lại dựa trên ngày hiện tại.

2. **Không lưu status vào database**: Status không được lưu trữ, luôn được tính động.

3. **Priority**: 
   - Ưu tiên 1: Next Survey Date + Window
   - Ưu tiên 2: Valid Date (khi không có Next Survey)

4. **Window chỉ cộng khi ±3M**: 
   - `(±3M)` → window_close = date + 3 tháng
   - `(-3M)` → window_close = date (không cộng)

5. **30 ngày**: Ngưỡng cảnh báo "Due Soon"

---

*Cập nhật lần cuối: 02/01/2026*
