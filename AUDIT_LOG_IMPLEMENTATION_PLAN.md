# 📋 Audit Log Implementation Plan

## ✅ Đã hoàn thành
- **Crew** (CREATE/UPDATE/DELETE/SIGN_ON/SIGN_OFF/TRANSFER)
- **Crew Certificates** (CREATE/UPDATE/DELETE)

---

## 🎯 Kế hoạch triển khai theo thứ tự ưu tiên

### **PHASE 1: Core Entities (Priority: HIGH) 🔴**

#### 1.1 Ships (Tàu)
**Service:** `ship_service.py`
**Collections:** `ships`
**Operations to log:**
- ✅ CREATE_SHIP - Thêm tàu mới
- ✅ UPDATE_SHIP - Cập nhật thông tin tàu
- ✅ DELETE_SHIP - Xóa tàu

**Key fields to track:**
```python
fields = [
    'name',           # Tên tàu
    'imo',            # IMO number
    'flag',           # Cờ tàu
    'ship_type',      # Loại tàu
    'class_society',  # Hội đăng kiểm
    'gross_tonnage',  # Trọng tải
    'built_year',     # Năm đóng
    'delivery_date',  # Ngày nhận tàu
    'status'          # Trạng thái
]
```

**Estimated effort:** 2-3 hours
**Impact:** HIGH - Ships là core entity

---

#### 1.2 Ship Certificates (Chứng chỉ tàu)
**Service:** `certificate_service.py`
**Collections:** `audit_certificates`
**Operations to log:**
- ✅ CREATE_CERTIFICATE - Thêm chứng chỉ tàu
- ✅ UPDATE_CERTIFICATE - Cập nhật chứng chỉ tàu
- ✅ DELETE_CERTIFICATE - Xóa chứng chỉ tàu
- ✅ BULK_DELETE_CERTIFICATES - Xóa hàng loạt

**Key fields to track:**
```python
fields = [
    'cert_name',        # Tên chứng chỉ
    'cert_no',          # Số chứng chỉ
    'issue_date',       # Ngày cấp
    'valid_date',       # Ngày hết hạn
    'last_endorse',     # Lần xác nhận cuối
    'status',           # Trạng thái
    'cert_type'         # Loại chứng chỉ
]
```

**Estimated effort:** 2-3 hours
**Impact:** HIGH - Important compliance documents

---

#### 1.3 Companies (Công ty)
**Service:** `company_service.py`
**Collections:** `companies`
**Operations to log:**
- ✅ CREATE_COMPANY - Tạo công ty mới
- ✅ UPDATE_COMPANY - Cập nhật thông tin công ty
- ✅ DELETE_COMPANY - Xóa công ty

**Key fields to track:**
```python
fields = [
    'name_vn',      # Tên công ty (VN)
    'name_en',      # Tên công ty (EN)
    'code',         # Mã công ty
    'tax_id',       # Mã số thuế
    'email',        # Email
    'phone',        # Điện thoại
    'address_vn',   # Địa chỉ (VN)
    'address_en',   # Địa chỉ (EN)
    'status'        # Trạng thái
]
```

**Estimated effort:** 2 hours
**Impact:** MEDIUM - Admin only, infrequent changes

---

#### 1.4 Users (Người dùng)
**Service:** `user_service.py`
**Collections:** `users`
**Operations to log:**
- ✅ CREATE_USER - Tạo người dùng mới
- ✅ UPDATE_USER - Cập nhật thông tin người dùng
- ✅ DELETE_USER - Xóa người dùng
- ✅ CHANGE_ROLE - Thay đổi quyền
- ✅ ACTIVATE/DEACTIVATE - Kích hoạt/vô hiệu hóa

**Key fields to track:**
```python
fields = [
    'username',     # Tên đăng nhập
    'email',        # Email
    'full_name',    # Họ tên
    'role',         # Vai trò (admin/user)
    'company',      # Công ty
    'department',   # Phòng ban
    'is_active'     # Trạng thái active
]
```

**Special notes:**
- ⚠️ KHÔNG log `password_hash`
- ✅ Log role changes separately

**Estimated effort:** 2-3 hours
**Impact:** HIGH - Security sensitive

---

### **PHASE 2: Ship Documents (Priority: MEDIUM) 🟡**

#### 2.1 Approval Documents (Văn bản phê duyệt)
**Service:** `approval_document_service.py`
**Collections:** `approval_documents`

**Key fields:**
```python
fields = [
    'approval_document_name',
    'approval_document_no',
    'approved_by',
    'approved_date',
    'status',
    'note'
]
```

**Estimated effort:** 2 hours

---

#### 2.2 Survey Reports (Báo cáo kiểm tra)
**Service:** `survey_report_service.py`
**Collections:** `survey_reports`

**Key fields:**
```python
fields = [
    'survey_report_name',
    'survey_report_no',
    'report_form',
    'issued_date',
    'issued_by',
    'surveyor_name',
    'status',
    'note'
]
```

**Estimated effort:** 2 hours

---

#### 2.3 Test Reports (Báo cáo thử nghiệm)
**Service:** `test_report_service.py`
**Collections:** `test_reports`

**Key fields:**
```python
fields = [
    'test_report_name',
    'test_report_no',
    'report_form',
    'issued_date',
    'issued_by',
    'valid_date',
    'status',
    'note'
]
```

**Estimated effort:** 2 hours

---

#### 2.4 Drawings & Manuals (Bản vẽ & Hướng dẫn)
**Service:** `drawing_manual_service.py`
**Collections:** `drawings_manuals`

**Key fields:**
```python
fields = [
    'document_name',
    'document_no',
    'approved_by',
    'approved_date',
    'status',
    'note'
]
```

**Estimated effort:** 2 hours

---

### **PHASE 3: System Config (Priority: LOW) 🔵**

#### 3.1 AI Configuration
**Service:** `ai_config_service.py`
**Collections:** `ai_config`

**Key fields:**
```python
fields = [
    'provider',     # OpenAI/Anthropic/Google
    'model',        # Model name
    'enabled',      # Bật/tắt
    'api_key'       # API key (MASKED in logs)
]
```

**Special notes:**
- ⚠️ MASK sensitive data (API keys)

**Estimated effort:** 1-2 hours

---

## 🛠️ Implementation Checklist per Entity

### For each entity, follow these steps:

#### Backend (3-4 hours per entity)
1. ✅ **Add audit functions to `crew_audit_log_service.py`:**
   - `log_[entity]_create()`
   - `log_[entity]_update()`
   - `log_[entity]_delete()`

2. ✅ **Verify DB field names:**
   - Query actual collection
   - Document field mappings
   - Handle date/datetime fields

3. ✅ **Integrate into service:**
   - Add `get_audit_log_service()` helper
   - Hook into create/update/delete methods
   - Add try-catch with proper error logging

4. ✅ **Test manually:**
   - Create entity
   - Update entity
   - Delete entity
   - Verify logs in DB

#### Frontend (1 hour per entity)
1. ✅ **Add action configs in `AuditLogCard.jsx`:**
   - Icons
   - Colors
   - Labels (VI/EN)

2. ✅ **Test display:**
   - Check icon rendering
   - Verify labels
   - Test filters

---

## 📊 Total Effort Estimation

| Phase | Entities | Backend | Frontend | Testing | Total |
|-------|----------|---------|----------|---------|-------|
| **Phase 1** | 4 entities | 10h | 3h | 3h | **16h** |
| **Phase 2** | 4 entities | 8h | 2h | 2h | **12h** |
| **Phase 3** | 1 entity | 2h | 0.5h | 0.5h | **3h** |
| **TOTAL** | 9 entities | 20h | 5.5h | 5.5h | **31h** |

---

## 🎯 Recommended Approach

### Option A: Complete Phase 1 First (Recommended)
- Triển khai đầy đủ Phase 1 (Ships, Ship Certs, Companies, Users)
- Test kỹ lưỡng
- Deploy và gather feedback
- Sau đó mới làm Phase 2 & 3

### Option B: One Entity at a Time
- Triển khai từng entity một
- Test và deploy incrementally
- Ít rủi ro hơn nhưng mất nhiều thời gian deploy

---

## ⚠️ Important Notes

### 1. Field Name Verification
**CRITICAL:** Always verify DB field names first!
```python
# Check actual field names in DB
doc = await db[collection].find_one({})
print(doc.keys())
```

### 2. Date Field Handling
Common patterns:
- `issued_date` vs `issue_date`
- `cert_expiry` vs `expiry_date`
- `valid_date` vs `validity_date`

### 3. Action Naming Convention
```python
# Standard format
CREATE_[ENTITY]     # e.g., CREATE_SHIP, CREATE_CERTIFICATE
UPDATE_[ENTITY]     # e.g., UPDATE_SHIP, UPDATE_CERTIFICATE
DELETE_[ENTITY]     # e.g., DELETE_SHIP, DELETE_CERTIFICATE
```

### 4. Sensitive Data
**Never log:**
- Passwords or password hashes
- Full API keys (only last 4 chars)
- Personal identification numbers (unless required)

### 5. Testing Checklist
For each entity:
- [ ] Create operation logs correctly
- [ ] Update operation logs field changes
- [ ] Delete operation logs correctly
- [ ] Bulk operations log correctly
- [ ] Filters work (by user, action, date)
- [ ] Export works (CSV/Excel)
- [ ] No performance impact
- [ ] No duplicate logs

---

## 🚀 Next Steps

1. **Confirm priorities** with stakeholders
2. **Start with Ships** (highest impact, most used)
3. **Implement incrementally**
4. **Test thoroughly** after each entity
5. **Document field mappings** as you go

---

## 📝 Progress Tracking

| Entity | Status | Started | Completed | Tested | Notes |
|--------|--------|---------|-----------|--------|-------|
| Crew | ✅ DONE | - | - | ✅ | All operations |
| Crew Certificates | ✅ DONE | - | - | ✅ | All operations |
| Ships | ⏳ PENDING | - | - | - | Phase 1 |
| Ship Certificates | ⏳ PENDING | - | - | - | Phase 1 |
| Companies | ⏳ PENDING | - | - | - | Phase 1 |
| Users | ⏳ PENDING | - | - | - | Phase 1 |
| Approval Docs | ⏳ PENDING | - | - | - | Phase 2 |
| Survey Reports | ⏳ PENDING | - | - | - | Phase 2 |
| Test Reports | ⏳ PENDING | - | - | - | Phase 2 |
| Drawings/Manuals | ⏳ PENDING | - | - | - | Phase 2 |
| AI Config | ⏳ PENDING | - | - | - | Phase 3 |

---

**Last Updated:** 2025-12-09
**Total Entities:** 11 (2 done, 9 pending)
**Estimated Completion:** ~31 hours of development
