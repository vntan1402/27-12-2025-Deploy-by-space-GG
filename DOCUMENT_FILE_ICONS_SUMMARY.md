# 📄 Tổng hợp Icons cho File Gốc và File Tóm tắt

## 🎯 Tổng quan

Trong hệ thống, mỗi document có thể có **2 loại file**:
1. **File gốc** (Original File) - File chứng chỉ/tài liệu đầy đủ
2. **File tóm tắt** (Summary File) - File tóm tắt nội dung chính

---

## 🏷️ Icons được sử dụng

| Icon | Loại File | Màu | Mục đích |
|------|-----------|-----|----------|
| 📄 | File gốc (Original) | **🟢 Green** | File chứng chỉ/tài liệu đầy đủ |
| 📋 | File tóm tắt (Summary) | **🔵 Blue** | File tóm tắt nội dung (AI-generated hoặc manual) |
| 📄 | File gốc | **🔴 Red** | Trong một số trường hợp đặc biệt (Audit Certificates) |

---

## 📊 Các Document Types hỗ trợ File Summary

### 1. 🚢 **Ship Certificates** (Chứng chỉ tàu)

**File:** `shipCertificateService.js`

```javascript
// Hỗ trợ upload 2 files
uploadFiles: async (certId, certFile, summaryFile = null)
```

**Icons:**
- 📄 **File gốc** (Green) - `google_drive_file_id`
- 📋 **File summary** (Blue) - `summary_file_id` (nếu có)

**Loại certificates:**
- IOPP, ISPP
- Class Certificate
- Safety Equipment Certificate
- Load Line Certificate
- Tonnage Certificate
- Cargo Ship Safety Certificate
- Và tất cả ship certificates khác

---

### 2. 👥 **Crew Certificates** (Chứng chỉ thuyền viên)

**File:** `crewCertificateService.js`

```javascript
// Hỗ trợ upload 2 files
uploadFiles: async (certId, certFile, summaryFile = null)
```

**Icons:**
- 📄 **File gốc** (Green) - `google_drive_file_id`
- 📋 **File summary** (Blue) - `summary_file_id` (nếu có)

**Loại certificates:**
- COC (Certificate of Competency)
- COP (Certificate of Proficiency)
- STCW Certificates
- Medical Certificate
- Seafarer's Book
- Passport

---

### 3. 📋 **Test Reports** (Báo cáo thử nghiệm)

**File:** `testReportService.js`

```javascript
// Hỗ trợ AI tạo summary tự động
uploadFiles: async (reportId, fileContent, filename, contentType, summaryText)
```

**Icons:**
- 📄 **File gốc** (Green) - `test_report_file_id`
- 📋 **File summary** (Blue) - `test_report_summary_file_id`

**Đặc biệt:**
- AI tự động tạo summary từ file gốc
- Hỗ trợ split file lớn thành nhiều chunks để xử lý
- Hiển thị thông tin: `📄 File có X trang, đã chia thành Y phần`

---

### 4. 📋 **Class Survey Reports** (Báo cáo khảo sát đăng kiểm)

**File:** `surveyReportService.js`

```javascript
// Hỗ trợ AI tạo summary
uploadFiles: async (reportId, fileContent, filename, contentType, summaryText)
```

**Icons:**
- 📄 **File gốc** (Green) - `survey_report_file_id`
- 📋 **File summary** (Blue) - `survey_report_summary_file_id`

---

### 5. 📋 **Audit Reports** (Báo cáo kiểm tra)

**File:** `auditReportService.js`

```javascript
// Hỗ trợ AI tạo summary
uploadFiles: async (reportId, fileContent, filename, contentType, summaryText = null)
```

**Icons:**
- 📄 **File gốc** (Green/Red) - `audit_report_file_id`
- 📋 **File summary** (Blue) - `audit_report_summary_file_id`

---

### 6. 📄 **Audit Certificates** (Chứng chỉ kiểm tra)

**Loại:**
- ISM Certificate
- ISPS Certificate
- MLC Certificate

**Icons:**
- 📄 **File gốc** (**🔴 Red** - đặc biệt) - `certificate_file_id`
- Không có file summary riêng

---

## 🔍 Chi tiết Icon trong Code

### Ship Certificates (CertificateTable.jsx)

```jsx
{/* File gốc - Green */}
{cert.google_drive_file_id && (
  <span className="text-green-500 text-xs cursor-pointer">
    📄
  </span>
)}

{/* File summary - Blue (nếu có) */}
{cert.summary_file_id && (
  <span className="text-blue-500 text-xs cursor-pointer">
    📋
  </span>
)}
```

### Test Reports (TestReportList.jsx)

```jsx
{/* File gốc - Green */}
{report.test_report_file_id && (
  <span className="text-green-500 text-xs">
    📄
  </span>
)}

{/* File summary - Blue */}
{report.test_report_summary_file_id && (
  <span className="text-blue-500 text-xs">
    📋
  </span>
)}
```

### Audit Certificates (AuditCertificateTable.jsx)

```jsx
{/* File gốc - Red (đặc biệt) */}
{cert.certificate_file_id && (
  <span className="text-red-500 text-xs">
    📄
  </span>
)}
```

---

## 🎉 Tooltips và Hover Text

| Icon | Tooltip (Tiếng Việt) | Tooltip (English) |
|------|------------------------|-------------------|
| 📄 | File gốc | Original file |
| 📋 | File tóm tắt | Summary file |

**Ví dụ tooltip chi tiết:**
```
File tóm tắt
📁 [Ship Name]/Class & Flag Cert/Test Report
```

---

## 💡 Tính năng AI Summary

Các document types hỗ trợ **AI tự động tạo summary**:

1. ✅ **Test Reports** - AI trích xuất thông tin chính
2. ✅ **Class Survey Reports** - AI tóm tắt nội dung
3. ✅ **Audit Reports** - AI tạo summary

**Quy trình:**
1. Upload file gốc
2. AI phân tích và trích xuất thông tin
3. Tạo file summary tự động
4. Lưu cả 2 files vào Google Drive
5. Hiển thị 2 icons trong table

---

## 📊 Tổng kết

**Tổng số document types hỗ trợ file summary:** 5 loại

1. ✅ Ship Certificates (Manual upload)
2. ✅ Crew Certificates (Manual upload)
3. ✅ Test Reports (AI auto-generate)
4. ✅ Class Survey Reports (AI auto-generate)
5. ✅ Audit Reports (AI auto-generate)

**Icons sử dụng:**
- 📄 Green: File gốc (phổ biến nhất)
- 📋 Blue: File summary (chuẩn)
- 📄 Red: File gốc Audit Certificates (đặc biệt)

**Components chính:**
- `CertificateTable.jsx` - Ship & Crew Certificates
- `TestReportList.jsx` - Test Reports
- `AuditCertificateTable.jsx` - Audit Certificates
- `AuditReportList.jsx` - Audit Reports

---

**Cập nhật:** Tháng 12, 2025
