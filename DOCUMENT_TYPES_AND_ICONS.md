# Tổng hợp các loại tài liệu và Icon trong Hệ thống Quản lý Tàu

## 📑 1. MAIN CATEGORIES (Danh mục chính)

| Icon | Tên tiếng Việt | Tên tiếng Anh | Key | Mô tả |
|------|----------------|---------------|-----|-------|
| 📜 | Class & Flag Cert | Class & Flag Cert | `ship_certificates` | Chứng chỉ đăng kiểm và cờ tàu |
| 👥 | Crew Records | Crew Records | `crew` | Hồ sơ thuyền viên |
| 📋 | ISM - ISPS - MLC | ISM - ISPS - MLC | `ism` | Chứng chỉ kiểm tra an toàn |
| 🛡️ | Safety Management System | Safety Management System | `isps` | Hệ thống quản lý an toàn |
| ⚓ | Technical Infor | Technical Infor | `mlc` | Thông tin kỹ thuật |
| 📦 | Supplies | Supplies | `supplies` | Vật tư |

---

## 📂 2. SUB-MENU ITEMS (Danh mục con)

### 2.1. Ship Certificates (📜 Class & Flag Cert)

| Tên tiếng Việt | Tên tiếng Anh | Key | Mô tả |
|----------------|---------------|-----|-------|
| Certificates | Certificates | `certificates` | Chứng chỉ tàu |
| Class Survey Report | Class Survey Report | `class_survey` | Báo cáo khảo sát đăng kiểm |
| Test Report | Test Report | `test_report` | Báo cáo thử nghiệm |
| Drawings & Manuals | Drawings & Manuals | `drawings` | Bản vẽ và sổ tay |
| Other Documents | Other Documents | `other_docs` | Tài liệu khác |

### 2.2. Crew Records (👥)

| Tên tiếng Việt | Tên tiếng Anh | Key | Mô tả |
|----------------|---------------|-----|-------|
| Crew List | Crew List | `crew_list` | Danh sách thuyền viên |
| Crew Certificates | Crew Certificates | `crew_certificates` | Chứng chỉ thuyền viên |

### 2.3. ISM - ISPS - MLC (📋)

| Tên tiếng Việt | Tên tiếng Anh | Key | Mô tả |
|----------------|---------------|-----|-------|
| Audit Certificate | Audit Certificate | `audit_certificate` | Chứng chỉ kiểm tra |
| Audit Report | Audit Report | `audit_report` | Báo cáo kiểm tra |
| Approval Document | Approval Document | `approval_document` | Tài liệu phê duyệt |
| Other Audit Document | Other Audit Document | `other_document` | Tài liệu kiểm tra khác |

### 2.4. Safety Management System (🛡️)

| Tên tiếng Việt | Tên tiếng Anh | Key |
|----------------|---------------|-----|
| ISPS Documents | ISPS Documents | `isps_list` |

### 2.5. Technical Infor (⚓)

| Tên tiếng Việt | Tên tiếng Anh | Key |
|----------------|---------------|-----|
| MLC Documents | MLC Documents | `mlc_list` |

### 2.6. Supplies (📦)

| Tên tiếng Việt | Tên tiếng Anh | Key |
|----------------|---------------|-----|
| Supplies List | Supplies List | `supplies_list` |

---

## 🎯 3. AUDIT LOG ACTION TYPES (Loại hành động trong Audit Log)

| Icon | Action Type | Màu | Mô tả |
|------|-------------|-----|-------|
| 📋 | BULK_UPDATE | Teal | Cập nhật hàng loạt |
| 📜 | CREATE_CERTIFICATE | Green | Tạo chứng chỉ thuyền viên |
| 📋 | CREATE_SHIP_CERTIFICATE | Green | Tạo chứng chỉ tàu |
| ✏️ | UPDATE | Blue | Cập nhật |
| 🗑️ | DELETE | Red | Xóa |
| ➕ | CREATE | Green | Tạo mới |

---

## 🚢 4. SHIP-RELATED ICONS (Icons liên quan đến tàu)

| Icon | Mục đích sử dụng |
|------|------------------|
| 🚢 | Ship/Tàu |
| ⚓ | Technical/Kỹ thuật |
| 🛡️ | Safety/An toàn |
| 📜 | Certificate/Chứng chỉ |
| 📋 | Report/Báo cáo |
| 📦 | Supplies/Vật tư |
| 👥 | Crew/Thuyền viên |
| 🔔 | Notification/Thông báo |
| ⚠️ | Warning/Cảnh báo |
| ℹ️ | Info/Thông tin |
| ❌ | Error/Lỗi |
| ✅ | Success/Thành công |

---

## 📊 5. SYSTEM ANNOUNCEMENT TYPES (Loại thông báo hệ thống)

| Icon | Type | Màu nền | Màu border | Mô tả |
|------|------|---------|------------|-------|
| ℹ️ | info | Blue 50 | Blue 200 | Thông tin |
| ⚠️ | warning | Yellow 50 | Yellow 200 | Cảnh báo |
| ✅ | success | Green 50 | Green 200 | Thành công |
| ❌ | error | Red 50 | Red 200 | Lỗi |

---

## 🔍 6. CERTIFICATE TYPES (Loại chứng chỉ)

### Ship Certificates (Chứng chỉ tàu)
- IOPP (International Oil Pollution Prevention)
- ISPP (International Sewage Pollution Prevention)
- Class Certificate
- Safety Equipment Certificate
- Load Line Certificate
- Tonnage Certificate
- Cargo Ship Safety Certificate

### Crew Certificates (Chứng chỉ thuyền viên)
- COC (Certificate of Competency)
- COP (Certificate of Proficiency)
- STCW Certificates
- Medical Certificate
- Seafarer's Book
- Passport

### Audit Certificates (Chứng chỉ kiểm tra)
- ISM (International Safety Management)
- ISPS (International Ship and Port Facility Security)
- MLC (Maritime Labour Convention)

---

## 💡 Ghi chú

- **File source:** `/app/frontend/src/utils/constants.js`
- **Components sử dụng icons:**
  - Sidebar navigation
  - SubMenu tabs
  - Audit log cards
  - System announcements
  - User guide modal
  - Admin tools

- **Cách thêm icon mới:**
  1. Thêm vào MAIN_CATEGORIES hoặc SUB_MENU_ITEMS trong `/app/frontend/src/utils/constants.js`
  2. Sử dụng emoji Unicode hoặc SVG icon
  3. Đảm bảo icon hiển thị đúng trên tất cả browsers

---

**Cập nhật lần cuối:** Tháng 12, 2025
**Tổng số icons được sử dụng:** 15+ emoji icons
