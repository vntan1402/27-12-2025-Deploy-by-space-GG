# Logic Xác Định Last Endorse / Next Survey / Next Survey Type

## Tổng quan

Hệ thống tự động tính toán **Last Endorse**, **Next Survey**, và **Next Survey Type** cho các chứng chỉ tàu dựa trên quy định IMO và chu kỳ kiểm tra 5 năm.

---

## 1. LAST ENDORSE (Ngày Endorse Cuối)

### 1.1 Nguồn dữ liệu
- Được trích xuất từ file PDF certificate bằng AI
- Lấy từ các section "Endorsement", "Annual surveys", "Verification"

### 1.2 Logic trích xuất AI

#### Format chuẩn (IAPP, IOPP, Load Line, etc.)
```
Endorsement for annual and intermediate surveys
Annual survey
Signed:
Place of survey: Vung Tau (VN)
Date: 16 July 2025    ← LAST ENDORSE
```

#### Format DG (Dangerous Goods)
```
Annual surveys
1st Annual survey
Credited by the Loosing Society on 30 August 2024  ← IGNORE (không phải endorsement thực)
...
2nd Annual survey
Signed:
Place of survey Vung Tau (VN) Hoai Nguyen Van
Date 16 July 2025    ← LAST ENDORSE (survey gần nhất có "Place of survey" và "Date")
3rd Annual survey
Signed:
Place of survey      ← Trống = chưa hoàn thành
Date
```

### 1.3 Quy tắc quan trọng

| Quy tắc | Mô tả |
|---------|-------|
| **Lấy ngày MỚI NHẤT** | Nếu có nhiều endorsements, luôn lấy ngày gần nhất |
| **Bỏ qua "Credited by"** | "Credited by the Losing/Loosing Society" KHÔNG phải endorsement thực |
| **Kiểm tra completion** | Chỉ lấy từ survey đã hoàn thành (có "Place of survey" và "Date" được điền) |

### 1.4 File xử lý
- `/app/backend/app/utils/ship_certificate_ai.py` - Class & Flag certificates
- `/app/backend/app/utils/audit_certificate_ai.py` - ISM/ISPS/MLC certificates
- `/app/backend/app/utils/company_cert_ai.py` - DOC certificates

---

## 2. NEXT SURVEY (Ngày Kiểm Tra Tiếp Theo)

### 2.1 Điều kiện tiên quyết

Certificate **CẦN** Annual Survey endorsement:
```python
INCLUDED_KEYWORDS = [
    'CLASS', 'CLASSIFICATION',
    'SAFETY CONSTRUCTION', 'SAFETY EQUIPMENT', 'SAFETY RADIO',
    'CARGO SHIP SAFETY', 'PASSENGER SHIP SAFETY',
    'LOAD LINE', 'LOADLINE',
    'IOPP', 'OIL POLLUTION',
    'IAPP', 'AIR POLLUTION',
    'ISPP',  # Sewage (with annual)
    'IEE', 'ENERGY EFFICIENCY',
    'BALLAST WATER', 'BWM'
]
```

Certificate **KHÔNG CẦN** Annual Survey:
```python
EXCLUDED_KEYWORDS = [
    'IMSBC', 'MSMC', 'REGISTRY', 'STATION LICENSE',
    'MINIMUM SAFE MANNING', 'CONTINUOUS SYNOPSIS',
    'TONNAGE', 'SEWAGE' (no annual), 'ANTI-FOULING',
    'CLC', 'BUNKER', 'WRECK REMOVAL',
    'FINANCIAL SECURITY', 'INSURANCE'
]
```

#### Trường hợp đặc biệt: DG (Dangerous Goods)
- Kiểm tra nội dung certificate để xác định
- Nếu có: `'ANNUAL SURVEY'`, `'ANNUAL SURVEYS'`, `'1ST ANNUAL SURVEY'`, `'2ND ANNUAL SURVEY'` → CẦN Annual Survey
- Nếu không có các từ khóa trên → KHÔNG tính Next Survey

### 2.2 Công thức tính

#### Bước 1: Xác định Anniversary Date
```
Anniversary Date = Ngày/Tháng từ Valid Date của certificate
Ví dụ: Valid Date = 28/06/2028 → Anniversary = 28/06
```

#### Bước 2: Xác định chu kỳ 5 năm
```
Cycle Start = Valid Date - 5 năm
Cycle End = Valid Date

Ví dụ:
Valid Date = 28/06/2028
→ Cycle Start = 28/06/2023
→ Cycle End = 28/06/2028
```

#### Bước 3: Tạo danh sách Annual Surveys
```
1st Annual Survey: 28/06/2024 (window: 28/03/2024 - 28/09/2024)
2nd Annual Survey: 28/06/2025 (window: 28/03/2025 - 28/09/2025)
3rd Annual Survey: 28/06/2026 (window: 28/03/2026 - 28/09/2026)
4th Annual Survey: 28/06/2027 (window: 28/03/2027 - 28/09/2027)
Special Survey:    28/06/2028 (window: 28/03/2028 - 28/06/2028) ← chỉ -3M
```

#### Bước 4: Xác định Next Survey dựa trên Last Endorse

```python
for survey in annual_surveys:
    survey_completed = False
    
    if last_endorse_dt:
        # Survey hoàn thành nếu:
        # 1. Last Endorse nằm TRONG window của survey, HOẶC
        # 2. Last Endorse SAU ngày survey (đã làm survey rồi)
        
        if window_open <= last_endorse_dt <= window_close:
            survey_completed = True  # Case 1
        elif last_endorse_dt > survey_date:
            survey_completed = True  # Case 2
    
    if not survey_completed:
        next_survey = survey
        break
```

### 2.3 Ví dụ thực tế

```
Certificate: IAPP
Valid Date: 28/06/2028
Last Endorse: 16/07/2025
Ngày hôm nay: 29/12/2025

Kiểm tra:
├── 1st Annual (28/06/2024): Last Endorse (16/07/2025) > 28/06/2024 → ✅ Completed
├── 2nd Annual (28/06/2025): Last Endorse (16/07/2025) > 28/06/2025 → ✅ Completed
└── 3rd Annual (28/06/2026): Last Endorse (16/07/2025) < 28/06/2026 → ⭐ NEXT SURVEY

Kết quả: Next Survey = 28/06/2026 (±3M)
```

### 2.4 Trường hợp đặc biệt

| Trường hợp | Xử lý |
|------------|-------|
| **Certificate hết hạn** | Next Survey = "-" |
| **Interim certificate** | Next Survey = "N/A" (không tính) |
| **Condition certificate** | Next Survey = Valid Date |
| **Next Survey > Valid Date** | Next Survey = Valid Date |
| **Không có Valid Date** | Next Survey = null |

---

## 3. NEXT SURVEY TYPE (Loại Kiểm Tra Tiếp Theo)

### 3.1 Các loại survey

| Type | Mô tả |
|------|-------|
| **1st Annual Survey** | Kiểm tra hàng năm lần 1 |
| **2nd Annual Survey/Intermediate Survey** | Kiểm tra hàng năm lần 2 (có thể kết hợp Intermediate) |
| **3rd Annual Survey** hoặc **Intermediate Survey** | Tùy thuộc vào Last Intermediate Survey |
| **4th Annual Survey** | Kiểm tra hàng năm lần 4 |
| **Special Survey** | Kiểm tra đặc biệt cuối chu kỳ 5 năm |

### 3.2 Logic xác định Intermediate Survey

```python
if survey_number == 2:
    next_survey_type = "2nd Annual Survey/Intermediate Survey"

elif survey_number == 3:
    if ship.last_intermediate_survey:
        if last_intermediate < next_survey_date:
            next_survey_type = "3rd Annual Survey"
        else:
            next_survey_type = "Intermediate Survey"
    else:
        next_survey_type = "Intermediate Survey"
```

---

## 4. SURVEY WINDOW (Cửa sổ kiểm tra)

### 4.1 Quy tắc

| Loại Survey | Window |
|-------------|--------|
| Annual Survey | ±3 tháng (trước và sau ngày anniversary) |
| Special Survey | -3 tháng (chỉ trước ngày anniversary) |

### 4.2 Hiển thị

```
28/06/2026 (±3M)  → Annual Survey có window ±3 tháng
28/06/2028 (-3M)  → Special Survey chỉ có window -3 tháng
```

---

## 5. AUTO-RECALCULATE

### 5.1 Khi nào tự động tính lại?

1. **Khi cập nhật Last Endorse**: Hệ thống tự động tính lại Next Survey
2. **Khi click "Cập nhật loại Survey"**: Tính lại tất cả certificates của tàu

### 5.2 File xử lý
- `/app/backend/app/services/certificate_service.py` - Auto-recalculate khi update
- `/app/backend/app/api/v1/ships.py` - Endpoint `/ships/{ship_id}/update-next-survey`

---

## 6. SƠ ĐỒ TỔNG QUAN

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CERTIFICATE UPLOAD FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

                           ┌──────────────┐
                           │  Upload PDF  │
                           └──────┬───────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │   AI Extract from Summary   │
                    │  - cert_name, cert_no       │
                    │  - issue_date, valid_date   │
                    │  - last_endorse  ⭐         │
                    │  - issued_by                │
                    └─────────────┬───────────────┘
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │  is_certificate_requires_annual()?   │
               └──────────────┬───────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
        ┌───────────┐                   ┌───────────┐
        │   TRUE    │                   │   FALSE   │
        │ (Class,   │                   │ (IMSBC,   │
        │  IAPP,    │                   │  Tonnage, │
        │  IOPP...) │                   │  CLC...)  │
        └─────┬─────┘                   └─────┬─────┘
              │                               │
              ▼                               ▼
    ┌─────────────────────┐           ┌─────────────────┐
    │ calculate_next_     │           │ next_survey = - │
    │ survey_info()       │           │ (không tính)    │
    │                     │           └─────────────────┘
    │ 1. Get Anniversary  │
    │ 2. Build 5-year     │
    │    cycle surveys    │
    │ 3. Check Last       │
    │    Endorse vs       │
    │    each survey      │
    │ 4. Find first       │
    │    incomplete       │
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │         NEXT SURVEY RESULT          │
    │  - next_survey: "28/06/2026"        │
    │  - next_survey_display: "28/06/2026 │
    │    (±3M)"                           │
    │  - next_survey_type: "3rd Annual    │
    │    Survey"                          │
    └─────────────────────────────────────┘
```

---

## 7. FILES LIÊN QUAN

| File | Chức năng |
|------|-----------|
| `/app/backend/app/utils/ship_calculations.py` | Logic chính tính Next Survey |
| `/app/backend/app/utils/ship_certificate_ai.py` | AI prompt cho Class & Flag certs |
| `/app/backend/app/utils/audit_certificate_ai.py` | AI prompt cho ISM/ISPS/MLC certs |
| `/app/backend/app/utils/company_cert_ai.py` | AI prompt cho DOC certs |
| `/app/backend/app/services/certificate_service.py` | Auto-recalculate on update |
| `/app/backend/app/api/v1/ships.py` | API endpoints |

---

*Cập nhật lần cuối: 02/01/2026*
