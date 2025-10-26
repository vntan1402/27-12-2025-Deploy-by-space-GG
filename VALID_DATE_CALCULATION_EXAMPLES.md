# Valid Date Calculation - Detailed Examples

## 📊 Ví Dụ Chi Tiết về Tính Valid Date

### **Lưu ý Quan Trọng về "Next Year"**
```
Next Year = Year trong Issued Date + 1

VÍ DỤ:
- Nếu Issued Date = 2025-03-10 → Next Year = 2026
- Nếu Issued Date = 2024-11-20 → Next Year = 2025
- Nếu Issued Date = 2023-01-15 → Next Year = 2024
```

---

## 🔧 **Loại 1: Fixed 12 Months (Đơn giản)**

### Ví dụ 1.1: EEBD
```yaml
Input:
  Equipment: EEBD
  Issued Date: 2025-01-15
  
Calculation:
  1. Match "EEBD" → Type: months, Value: 12
  2. Valid Date = 2025-01-15 + 12 months = 2026-01-15
  
Output:
  Valid Date: 2026-01-15
```

### Ví dụ 1.2: Life Raft
```yaml
Input:
  Equipment: Life Raft Annual Service
  Issued Date: 2024-06-20
  
Calculation:
  1. Match "Life Raft" → Type: months, Value: 12
  2. Valid Date = 2024-06-20 + 12 months = 2025-06-20
  
Output:
  Valid Date: 2025-06-20
```

### Ví dụ 1.3: Fire Extinguisher
```yaml
Input:
  Equipment: Portable Fire Extinguisher
  Issued Date: 2025-02-28
  
Calculation:
  1. Match "Fire Extinguisher" → Type: months, Value: 12
  2. Valid Date = 2025-02-28 + 12 months = 2026-02-28
  
Output:
  Valid Date: 2026-02-28
```

---

## 🎯 **Loại 2: Next Annual Survey (Phức tạp hơn)**

### Ví dụ 2.1: EPIRB - Case A (Anniversary == Special Survey)

```yaml
Input:
  Equipment: EPIRB
  Issued Date: 2025-03-10
  Ship Data:
    - Anniversary: 15/May (day: 15, month: 5)
    - Special Survey Cycle To: 2026-05-15

Step-by-Step Calculation:
  
  Step 1: Parse Issued Date
    → Year = 2025
  
  Step 2: Calculate Next Year
    → Next Year = 2025 + 1 = 2026
  
  Step 3: Build Anniversary Date for Next Year
    → Anniversary Next Year = 2026-05-15 (day 15, month 5, year 2026)
  
  Step 4: Compare with Special Survey Cycle To
    → Anniversary Next Year: 2026-05-15
    → Special Survey To:     2026-05-15
    → Match? YES ✅
  
  Step 5: Apply Rule A (Anniversary == Special Survey)
    → Valid Date = Anniversary - 3 months
    → Valid Date = 2026-05-15 - 3 months = 2026-02-15
  
Output:
  Valid Date: 2026-02-15
  
Giải thích:
  Vì Anniversary Date trùng với Special Survey Cycle To,
  thiết bị phải được test TRƯỚC special survey → trừ 3 tháng
  (Giữ nguyên ngày 15, chỉ thay đổi tháng: 5 - 3 = 2)
```

---

### Ví dụ 2.2: Lifeboat - Case B (Anniversary ≠ Special Survey)

```yaml
Input:
  Equipment: Lifeboat
  Issued Date: 2025-04-01
  Ship Data:
    - Anniversary: 20/August (day: 20, month: 8)
    - Special Survey Cycle To: 2028-08-20

Step-by-Step Calculation:
  
  Step 1: Parse Issued Date
    → Year = 2025
  
  Step 2: Calculate Next Year
    → Next Year = 2025 + 1 = 2026
  
  Step 3: Build Anniversary Date for Next Year
    → Anniversary Next Year = 2026-08-20 (day 20, month 8, year 2026)
  
  Step 4: Compare with Special Survey Cycle To
    → Anniversary Next Year: 2026-08-20
    → Special Survey To:     2028-08-20
    → Match? NO ❌ (khác năm)
  
  Step 5: Apply Rule B (Anniversary ≠ Special Survey)
    → Valid Date = Anniversary + 3 months
    → Valid Date = 2026-08-20 + 90 days ≈ 2026-11-18
  
Output:
  Valid Date: 2026-11-18
  
Giải thích:
  Vì Anniversary Date KHÔNG trùng với Special Survey Cycle To,
  áp dụng window 3 tháng chuẩn → cộng 3 tháng
```

---

### Ví dụ 2.3: SART - Case B (Issued Date năm khác)

```yaml
Input:
  Equipment: SART
  Issued Date: 2024-11-20
  Ship Data:
    - Anniversary: 10/March (day: 10, month: 3)
    - Special Survey Cycle To: 2027-03-10

Step-by-Step Calculation:
  
  Step 1: Parse Issued Date
    → Year = 2024
  
  Step 2: Calculate Next Year
    → Next Year = 2024 + 1 = 2025
  
  Step 3: Build Anniversary Date for Next Year
    → Anniversary Next Year = 2025-03-10 (day 10, month 3, year 2025)
  
  Step 4: Compare with Special Survey Cycle To
    → Anniversary Next Year: 2025-03-10
    → Special Survey To:     2027-03-10
    → Match? NO ❌ (khác năm: 2025 vs 2027)
  
  Step 5: Apply Rule B (Anniversary ≠ Special Survey)
    → Valid Date = Anniversary + 3 months
    → Valid Date = 2025-03-10 + 90 days ≈ 2025-06-08
  
Output:
  Valid Date: 2025-06-08
  
Giải thích:
  Issued Date năm 2024 → Next Year = 2025
  Anniversary trong năm 2025 khác với Special Survey (2027)
  → Áp dụng Rule B: +3 tháng
```

---

### Ví dụ 2.4: AIS - Không có Special Survey Cycle To

```yaml
Input:
  Equipment: AIS
  Issued Date: 2025-07-15
  Ship Data:
    - Anniversary: 5/December (day: 5, month: 12)
    - Special Survey Cycle To: NULL (không có)

Step-by-Step Calculation:
  
  Step 1: Parse Issued Date
    → Year = 2025
  
  Step 2: Calculate Next Year
    → Next Year = 2025 + 1 = 2026
  
  Step 3: Build Anniversary Date for Next Year
    → Anniversary Next Year = 2026-12-05 (day 5, month 12, year 2026)
  
  Step 4: Special Survey Cycle To = NULL
    → Không có dữ liệu để so sánh
  
  Step 5: Apply Default Rule (No Special Survey data)
    → Valid Date = Anniversary + 3 months (default)
    → Valid Date = 2026-12-05 + 90 days ≈ 2027-03-05
  
Output:
  Valid Date: 2027-03-05
  
Giải thích:
  Khi không có Special Survey Cycle To,
  mặc định áp dụng +3 tháng sau Anniversary
```

---

## 📊 Bảng So Sánh Các Trường Hợp

| Issued Date | Equipment | Anniversary | Special Survey To | Next Year | Anniversary Next Year | Rule | Valid Date | Note |
|------------|-----------|-------------|-------------------|-----------|----------------------|------|-----------|------|
| 2025-03-10 | EPIRB | 15/May | 2026-05-15 | 2026 | 2026-05-15 | A (match) | 2026-02-14 | -3M |
| 2025-04-01 | Lifeboat | 20/Aug | 2028-08-20 | 2026 | 2026-08-20 | B (no match) | 2026-11-18 | +3M |
| 2024-11-20 | SART | 10/Mar | 2027-03-10 | 2025 | 2025-03-10 | B (no match) | 2025-06-08 | +3M |
| 2025-07-15 | AIS | 5/Dec | NULL | 2026 | 2026-12-05 | Default | 2027-03-05 | +3M |
| 2025-01-15 | EEBD | N/A | N/A | N/A | N/A | 12 months | 2026-01-15 | Fixed |

---

## 🔍 Điểm Quan Trọng

### **1. Next Year luôn = Year của Issued Date + 1**
```
✅ ĐÚNG:
  Issued: 2025-03-10 → Next Year = 2026
  Issued: 2024-12-31 → Next Year = 2025

❌ SAI:
  Không dùng Current Year + 1
  Không dùng năm hiện tại của hệ thống
```

### **2. So sánh Anniversary với Special Survey**
```
Chỉ khớp khi:
  - Cùng năm (year)
  - Cùng tháng (month)
  - Cùng ngày (day)

Ví dụ:
  ✅ 2026-05-15 == 2026-05-15 → Match
  ❌ 2026-08-20 != 2028-08-20 → No match (khác năm)
  ❌ 2026-05-15 != 2026-05-20 → No match (khác ngày)
```

### **3. Logic +/- 3 tháng**
```
Rule A (Match): Anniversary - 3 months
  → Test TRƯỚC special survey
  
Rule B (No Match): Anniversary + 3 months
  → Window 3 tháng SAU anniversary (tiêu chuẩn)
```

---

*Last Updated: 2025-01-26*
