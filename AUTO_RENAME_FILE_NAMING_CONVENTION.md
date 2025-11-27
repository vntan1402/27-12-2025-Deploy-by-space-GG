# 📝 AUTO RENAME FILE - NAMING CONVENTION

## 🎯 **CẤU TRÚC TÊN FILE:**

```
{Ship Name}_{Cert Type}_{Cert Abbreviation}_{Issue Date}.{extension}
```

---

## 📊 **CÁC THÀNH PHẦN:**

### **1. Ship Name (Tên tàu)**
- **Source:** Từ database `ships` collection
- **Field:** `ship.name`
- **Example:** `VINASHIP HARMONY`, `MV OCEAN STAR`
- **Default:** `Unknown Ship` (nếu không tìm thấy)

---

### **2. Cert Type (Loại chứng chỉ)**
- **Source:** Từ database `certificates` collection
- **Field:** `cert_type`
- **Values:**
  - `Full Term`
  - `Interim`
  - `Provisional`
  - `Short term`
  - `Conditional`
  - `Other`
- **Default:** `Unknown Type` (nếu không có)

---

### **3. Cert Abbreviation (Viết tắt chứng chỉ)**

**⭐ PRIORITY LOGIC (Thứ tự ưu tiên):**

#### **Priority 1: User-Defined Mapping** (Cao nhất)
- **Source:** `certificate_abbreviation_mappings` collection
- **Logic:** Tìm mapping theo `cert_name`
- **Example:**
  ```json
  {
    "cert_name": "Cargo Ship Safety Construction Certificate",
    "abbreviation": "CSSC"
  }
  ```
- **Log:** `"🔄 AUTO-RENAME - PRIORITY 1: Using user-defined mapping..."`

#### **Priority 2: Database Certificate Abbreviation**
- **Source:** `certificates.cert_abbreviation` field
- **Logic:** Dùng giá trị có sẵn trong DB
- **Example:** Certificate record có field `cert_abbreviation: "LLC"`
- **Log:** `"🔄 AUTO-RENAME - PRIORITY 2: Using database abbreviation..."`

#### **Priority 3: Auto-Generated Abbreviation** (Fallback)
- **Source:** Auto-generated bởi `generate_certificate_abbreviation()` utility
- **Logic:** 
  - Lấy chữ cái đầu của mỗi từ quan trọng
  - Loại bỏ stop words (Certificate, of, the, etc.)
- **Examples:**
  - `"Load Line Certificate"` → `"LLC"`
  - `"International Oil Pollution Prevention Certificate"` → `"IOPP"`
  - `"Safety Management Certificate"` → `"SMC"`
- **Log:** `"🔄 AUTO-RENAME - PRIORITY 3: Generated abbreviation..."`

---

### **4. Issue Date (Ngày cấp)**
- **Source:** `certificates.issue_date` field
- **Format:** `YYYYMMDD` (8 số)
- **Examples:**
  - `2024-11-27` → `20241127`
  - `2025-01-15` → `20250115`
- **Default:** `NoDate` (nếu không có hoặc parse failed)

---

### **5. Extension (Đuôi file)**
- **Source:** Original filename's extension
- **Examples:** `.pdf`, `.jpg`, `.png`, `.docx`
- **Default:** `.pdf` (nếu không detect được)

---

## 📋 **VÍ DỤ CỤ THỂ:**

### **Example 1: Load Line Certificate**
```
Input Data:
- Ship Name: "VINASHIP HARMONY"
- Cert Type: "Full Term"
- Cert Name: "Load Line Certificate"
- Cert Abbreviation: "LLC" (from DB)
- Issue Date: "2024-11-27"
- Original File: "certificate.pdf"

Output Filename:
VINASHIP HARMONY_Full Term_LLC_20241127.pdf
```

---

### **Example 2: Safety Certificate (User-Defined Mapping)**
```
Input Data:
- Ship Name: "MV OCEAN STAR"
- Cert Type: "Interim"
- Cert Name: "Cargo Ship Safety Construction Certificate"
- User Mapping: "CSSC" (Priority 1)
- Issue Date: "2025-01-15"
- Original File: "scan_001.pdf"

Output Filename:
MV OCEAN STAR_Interim_CSSC_20250115.pdf
```

---

### **Example 3: Auto-Generated Abbreviation**
```
Input Data:
- Ship Name: "PACIFIC GLORY"
- Cert Type: "Full Term"
- Cert Name: "International Oil Pollution Prevention Certificate"
- Cert Abbreviation: null (không có trong DB)
- User Mapping: null (không có mapping)
- Auto-Generated: "IOPP" (Priority 3)
- Issue Date: "2024-06-30"

Output Filename:
PACIFIC GLORY_Full Term_IOPP_20240630.pdf
```

---

### **Example 4: No Issue Date**
```
Input Data:
- Ship Name: "HARMONY ONE"
- Cert Type: "Provisional"
- Cert Abbreviation: "TON"
- Issue Date: null

Output Filename:
HARMONY ONE_Provisional_TON_NoDate.pdf
```

---

## 🧹 **FILENAME CLEANING (Sanitization):**

Sau khi build filename, system sẽ clean up:

### **Rules:**
1. **Remove special characters** (chỉ giữ: letters, numbers, spaces, `_`, `-`, `.`)
   ```python
   re.sub(r'[^a-zA-Z0-9 ._-]', '', new_filename)
   ```

2. **Remove multiple spaces** (thay bằng 1 space)
   ```python
   re.sub(r'\s+', ' ', new_filename)
   ```

### **Examples:**
```
Before: "SHIP@NAME!_Full Term_#LLC_20241127.pdf"
After:  "SHIPNAME_Full Term_LLC_20241127.pdf"

Before: "HARMONY    ONE_Full Term_LLC_20241127.pdf"
After:  "HARMONY ONE_Full Term_LLC_20241127.pdf"
```

---

## 🔄 **SUMMARY FILE NAMING:**

Summary files cũng follow cùng convention, nhưng thêm suffix `_Summary.txt`:

```
{Ship Name}_{Cert Type}_{Cert Abbreviation}_{Issue Date}_Summary.txt
```

### **Example:**
```
Main File:
VINASHIP HARMONY_Full Term_LLC_20241127.pdf

Summary File:
VINASHIP HARMONY_Full Term_LLC_20241127_Summary.txt
```

---

## 🎛️ **USER CUSTOMIZATION:**

### **Cách tạo User-Defined Mapping:**

Users có thể tạo custom abbreviation mappings trong database:

```javascript
// MongoDB collection: certificate_abbreviation_mappings
{
  "cert_name": "Cargo Ship Safety Construction Certificate",
  "abbreviation": "CSSC",
  "created_by": "admin@company.com",
  "created_at": "2024-11-27T10:00:00Z"
}
```

**Benefits:**
- Standardize abbreviations across company
- Override auto-generated abbreviations
- Maintain consistency

---

## 📊 **ABBREVIATION EXAMPLES:**

| Certificate Name | Auto-Generated | Recommended Custom |
|------------------|----------------|-------------------|
| Load Line Certificate | LLC | LLC |
| Cargo Ship Safety Construction Certificate | CSSC | CSSC |
| International Oil Pollution Prevention Certificate | IOPP | IOPP |
| Safety Management Certificate | SMC | SMC |
| International Ship and Port Facility Security Certificate | ISPS | ISPS |
| Minimum Safe Manning Certificate | MSMC | MSMC |
| Certificate of Registry | COR | CR |
| Tonnage Certificate | TC | ITC |
| Ballast Water Management Certificate | BWMC | BWMC |

---

## 🔍 **DEBUGGING & LOGS:**

Khi auto-rename được trigger, system log chi tiết:

```
INFO: 🔄 AUTO-RENAME - PRIORITY 1: Using user-defined mapping 'Cargo Ship Safety Construction Certificate' → 'CSSC'
INFO: 🔄 Auto-renaming certificate file abc123 to 'VINASHIP HARMONY_Full Term_CSSC_20241127.pdf'
INFO: ✅ Successfully auto-renamed certificate file to 'VINASHIP HARMONY_Full Term_CSSC_20241127.pdf'
```

---

## ⚙️ **API ENDPOINT:**

```
POST /api/certificates/{certificate_id}/auto-rename-file
```

**Response:**
```json
{
  "success": true,
  "message": "Certificate file renamed successfully",
  "certificate_id": "cert-uuid",
  "file_id": "gdrive-file-id",
  "old_name": "original_certificate.pdf",
  "new_name": "VINASHIP HARMONY_Full Term_LLC_20241127.pdf",
  "summary_renamed": true,
  "naming_convention": {
    "ship_name": "VINASHIP HARMONY",
    "cert_type": "Full Term",
    "cert_identifier": "LLC",
    "issue_date": "20241127"
  },
  "renamed_timestamp": "2024-11-27T10:30:00Z"
}
```

---

## ✅ **BEST PRACTICES:**

1. **Create User Mappings:**
   - Tạo mappings cho các certificate types phổ biến
   - Maintain consistency across company

2. **Standardize Cert Types:**
   - Luôn dùng: Full Term, Interim, Provisional
   - Tránh variations như "fullterm", "full-term"

3. **Date Consistency:**
   - Đảm bảo issue_date được điền đầy đủ
   - Format: YYYY-MM-DD trong database

4. **Ship Names:**
   - Giữ tên tàu consistent trong database
   - Tránh special characters trong ship names

---

## 🚨 **COMMON ISSUES:**

### **Issue 1: NoDate in filename**
**Cause:** issue_date is null or invalid  
**Solution:** Cập nhật issue_date cho certificate

### **Issue 2: Long filenames**
**Cause:** Ship name quá dài  
**Solution:** Shorten ship name trong database (hoặc system sẽ truncate)

### **Issue 3: Special characters in filename**
**Cause:** Ship name hoặc cert type có special chars  
**Solution:** System tự động clean up (xóa special chars)

---

**Document created:** 2024-11-27  
**Feature:** Auto Rename File for Ship Certificates  
**Version:** 1.0
