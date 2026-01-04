# Tổng Hợp Logic Xác Định Last Endorse / Next Survey / Next Survey Type

## 1. TỔNG QUAN

Hệ thống sử dụng các field sau để quản lý chu kỳ kiểm tra:
- **Last Endorse (last_endorse)**: Ngày xác nhận/endorsement gần nhất
- **Next Survey (next_survey)**: Ngày kiểm tra tiếp theo
- **Next Survey Type (next_survey_type)**: Loại kiểm tra tiếp theo

---

## 2. LAST ENDORSE

### 2.1 Nguồn dữ liệu
- Được **AI extraction** từ document PDF
- Các pattern tìm kiếm trong document:
  - "Last Endorse"
  - "Last Endorsed"
  - "Endorsement date"
  - "Last endorsed on"
  - "Endorsed"

### 2.2 Ý nghĩa theo loại certificate

| Loại Certificate | Ý nghĩa Last Endorse |
|-----------------|---------------------|
| **Full Term DOC** | Ngày Annual Audit gần nhất được hoàn thành |
| **Short Term DOC** | Không áp dụng |
| **Interim DOC** | Không áp dụng |
| **Ship Certificate** | Ngày xác nhận định kỳ gần nhất |
| **Audit Certificate** | Ngày audit gần nhất |

### 2.3 Format
- Input: Nhiều format text ("15 November 2024", "November 15, 2024", "15/11/2024")
- Output: `YYYY-MM-DD` (normalized)

---

## 3. NEXT SURVEY DATE & TYPE

### 3.1 Logic theo DOC Type (Company Certificate)

File: `/app/backend/app/utils/doc_next_survey_calculator.py`

#### A. SHORT TERM DOC
```
Next Survey: NULL
Next Survey Type: NULL
→ Không yêu cầu audit
```

#### B. INTERIM DOC
```
Next Survey: valid_date (ngày hết hạn)
Next Survey Type: "Initial"
→ Phải audit trước khi hết hạn interim
```

#### C. FULL TERM DOC (5-Year Cycle)

**Chu kỳ audit:**
```
Năm 1: 1st Annual Audit (Anniversary ±3 tháng)
Năm 2: 2nd Annual Audit (Anniversary ±3 tháng)
Năm 3: 3rd Annual Audit (Anniversary ±3 tháng)
Năm 4: 4th Annual Audit (Anniversary ±3 tháng)
Năm 5: Renewal Audit (Valid date -3 tháng)
```

**Anniversary Date:**
- Lấy ngày/tháng từ `valid_date`
- Ví dụ: valid_date = 15/06/2029 → Anniversary = 15/06 mỗi năm

**5-Year Cycle:**
```
cycle_start_year = valid_date.year - 5
cycle_end_year = valid_date.year

Ví dụ: valid_date = 15/06/2029
→ Cycle: 2024 - 2029
→ Audits:
   - 15/06/2025: 1st Annual
   - 15/06/2026: 2nd Annual
   - 15/06/2027: 3rd Annual
   - 15/06/2028: 4th Annual
   - 15/06/2029: Renewal
```

**Logic xác định Next Survey:**
1. Nếu có `last_endorse` → dùng làm reference date
2. Nếu không có `last_endorse` → fallback về `issue_date`
3. So sánh reference_date với các audit window:
   - Annual audit: reference_date nằm trong [audit_date - 3M, audit_date + 3M]
   - Renewal audit: reference_date nằm trong [audit_date - 3M, audit_date]
4. Tìm audit gần nhất đã hoàn thành
5. Next Survey = audit kế tiếp

**Ví dụ:**
```
valid_date = 15/06/2029
last_endorse = 20/06/2026

→ Check: 20/06/2026 nằm trong window của 2nd Annual (15/03/2026 - 15/09/2026)
→ 2nd Annual đã hoàn thành
→ Next Survey = 15/06/2027
→ Next Survey Type = "3rd Annual"
```

---

### 3.2 Logic cho Ship Certificate

File: `/app/backend/app/utils/ship_certificate_ai.py`

**Next Survey Type options:**
- Initial
- Intermediate
- Renewal
- Annual
- Special
- Other

**Logic:**
- AI extraction trực tiếp từ document
- Post-processing normalize:
  - Validate cert_type phải là giá trị hợp lệ
  - Normalize date formats

---

### 3.3 Logic cho Audit Certificate

File: `/app/backend/app/utils/audit_certificate_ai.py`

**Next Survey Type options:**
- Initial
- Intermediate
- Renewal
- Annual
- Other

**Special Cases:**

1. **ISPS Interim Certificate:**
   - Nếu document chứa "until the initial ISPS audit is conducted"
   - → `valid_date = issue_date + 6 tháng - 1 ngày`

2. **Statement of Facts:**
   - Nếu document header chứa "STATEMENT OF FACTS"
   - → `cert_type = "Statement"`

3. **DMLC Detection:**
   - "DMLC Part II" / "DMLC-II" → `cert_name = "DMLC II"`
   - "DMLC Part I" / "DMLC-I" → `cert_name = "DMLC I"`

---

## 4. AUDIT WINDOW

### Window Types:

| Audit Type | Window |
|-----------|--------|
| Annual (1st-4th) | ±3 tháng từ anniversary date |
| Renewal | -3 tháng từ valid_date |
| Initial | Trước valid_date |

### Ví dụ Window Calculation:
```
Anniversary Date: 15/06/2027 (3rd Annual)

Window Start: 15/03/2027 (anniversary - 3 tháng)
Window End: 15/09/2027 (anniversary + 3 tháng)

→ Audit hợp lệ nếu thực hiện trong khoảng 15/03 - 15/09/2027
```

---

## 5. CODE FLOW

### 5.1 Company Certificate (DOC)
```
Upload PDF
    ↓
Document AI (extract text)
    ↓
AI Extraction (company_cert_ai.py)
    - Extract: cert_name, cert_no, doc_type, issue_date, valid_date, last_endorse, issued_by
    ↓
Calculate Next Survey (doc_next_survey_calculator.py)
    - Input: doc_type, valid_date, issue_date, last_endorse
    - Output: next_survey, next_survey_type
    ↓
Save to Database
```

### 5.2 Ship Certificate
```
Upload PDF
    ↓
Document AI (extract text)
    ↓
AI Extraction (ship_certificate_ai.py)
    - Extract: cert_name, cert_no, cert_type, issue_date, valid_date, last_endorse, 
               next_survey, next_survey_type, imo_number, ship_name, flag, issued_by
    ↓
Post-processing (normalize dates, validate types)
    ↓
Save to Database
```

### 5.3 Audit Certificate
```
Upload PDF
    ↓
Document AI (extract text)
    ↓
AI Extraction (audit_certificate_ai.py)
    - Extract: cert_name, cert_no, cert_type, issue_date, valid_date, last_endorse,
               next_survey, next_survey_type, imo_number, ship_name, issued_by
    ↓
Post-processing:
    - Normalize dates
    - Check ISPS interim → auto-calculate valid_date
    - Check Statement of Facts → force cert_type
    - Check DMLC → force cert_name
    ↓
Save to Database
```

---

## 6. FILES LIÊN QUAN

| File | Mục đích |
|------|----------|
| `/app/backend/app/utils/doc_next_survey_calculator.py` | Tính Next Survey cho Company DOC |
| `/app/backend/app/utils/company_cert_ai.py` | AI extraction cho Company Certificate |
| `/app/backend/app/utils/ship_certificate_ai.py` | AI extraction cho Ship Certificate |
| `/app/backend/app/utils/audit_certificate_ai.py` | AI extraction cho Audit Certificate |
| `/app/backend/app/utils/survey_report_ai.py` | AI extraction cho Survey Report |

---

## 7. VALID VALUES

### 7.1 DOC Type (Company Certificate)
- `full_term`: DOC đầy đủ 5 năm
- `short_term`: DOC ngắn hạn
- `interim`: DOC tạm thời

### 7.2 Certificate Type (Ship/Audit)
- `Full Term`: Chứng chỉ đầy đủ
- `Short Term`: Chứng chỉ ngắn hạn
- `Interim`: Chứng chỉ tạm thời
- `Statement`: Bản khai (Statement of Facts)

### 7.3 Next Survey Type
- `Initial`: Kiểm tra ban đầu
- `1st Annual` / `2nd Annual` / `3rd Annual` / `4th Annual`: Kiểm tra hàng năm
- `Intermediate`: Kiểm tra giữa kỳ
- `Renewal`: Kiểm tra gia hạn
- `Special`: Kiểm tra đặc biệt
- `Other`: Khác

---

## 8. LƯU Ý

1. **Date Format:**
   - Input: Nhiều format (text, DD/MM/YYYY, MM/DD/YYYY, etc.)
   - Output (database): `YYYY-MM-DD`

2. **Priority khi thiếu dữ liệu:**
   - Có `last_endorse` → dùng `last_endorse`
   - Không có `last_endorse` → fallback về `issue_date`
   - Không có cả hai → tính từ thời điểm hiện tại

3. **Special handling:**
   - ISPS Interim: Auto-calculate valid_date
   - DMLC: Auto-detect Part I/II từ nội dung
   - Statement of Facts: Auto-detect từ header
