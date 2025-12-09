# Phase 1 Audit Log Integration Guide

## ✅ Completed
1. Created audit log extension mixins in `/app/backend/app/services/audit_log_extensions.py`
2. Added mixins to CrewAuditLogService
3. Verified DB field names for all 4 entities

## 🔧 Integration Steps

### 1. Ships (ship_service.py)

**File:** `/app/backend/app/services/ship_service.py`

**Add helper method:**
```python
@staticmethod
def get_audit_log_service():
    """Get audit log service instance"""
    from app.db.mongodb import mongo_db
    from app.services.crew_audit_log_service import CrewAuditLogService
    from app.repositories.crew_audit_log_repository import CrewAuditLogRepository
    return CrewAuditLogService(CrewAuditLogRepository(mongo_db.database))
```

**Line 49 - After create_ship (after ShipRepository.create):**
```python
# Log audit
try:
    audit_service = ShipService.get_audit_log_service()
    user_dict = {
        'id': current_user.id,
        'username': current_user.username,
        'full_name': current_user.full_name,
        'company': current_user.company
    }
    await audit_service.log_ship_create(
        ship_data=ship_dict,
        user=user_dict
    )
except Exception as e:
    logger.error(f"Failed to create audit log: {e}")
```

**Line 76 - In update_ship (before return):**
```python
# Log audit
try:
    audit_service = ShipService.get_audit_log_service()
    user_dict = {
        'id': current_user.id,
        'username': current_user.username,
        'full_name': current_user.full_name,
        'company': current_user.company
    }
    old_ship = await ShipRepository.find_by_id(ship_id)
    updated_ship = await ShipRepository.find_by_id(ship_id)
    
    await audit_service.log_ship_update(
        old_ship=old_ship,
        new_ship=updated_ship,
        user=user_dict
    )
except Exception as e:
    logger.error(f"Failed to create audit log: {e}")
```

**Line 102 - In delete_ship (before return):**
```python
# Log audit
try:
    audit_service = ShipService.get_audit_log_service()
    user_dict = {
        'id': current_user.id,
        'username': current_user.username,
        'full_name': current_user.full_name,
        'company': current_user.company
    }
    await audit_service.log_ship_delete(
        ship_data=ship,
        user=user_dict
    )
except Exception as e:
    logger.error(f"Failed to create audit log: {e}")
```

---

### 2. Ship Certificates (certificate_service.py or audit_certificate_service.py)

**File:** Search for the service that handles audit_certificates CRUD

**Similar pattern as above, but use:**
- `log_ship_certificate_create(ship_name, cert_data, user)`
- `log_ship_certificate_update(ship_name, old_cert, new_cert, user)`
- `log_ship_certificate_delete(ship_name, cert_data, user)`

---

### 3. Companies (company_service.py)

**File:** `/app/backend/app/services/company_service.py`

**Similar pattern:**
- `log_company_create(company_data, user)`
- `log_company_update(old_company, new_company, user)`
- `log_company_delete(company_data, user)`

---

### 4. Users (user_service.py)

**File:** `/app/backend/app/services/user_service.py`

**⚠️ IMPORTANT: Never log password_hash!**

**Similar pattern:**
- `log_user_create(user_data, performed_by_user)`
- `log_user_update(old_user, new_user, performed_by_user)`
- `log_user_delete(user_data, performed_by_user)`

**Special note:** For user operations, `performed_by_user` is the admin/user performing the action (current_user), NOT the user being modified.

---

## 🎨 Frontend Updates

**File:** `/app/frontend/src/components/SystemSettings/CrewAuditLogs/AuditLogCard.jsx`

### Update getActionConfig (around line 15):
```javascript
const configs = {
  // ... existing configs ...
  
  // Ships
  CREATE_SHIP: { icon: '🚢', color: 'green', bgColor: 'bg-green-50', borderColor: 'border-green-200', textColor: 'text-green-800' },
  UPDATE_SHIP: { icon: '⚓', color: 'blue', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', textColor: 'text-blue-800' },
  DELETE_SHIP: { icon: '🗑️', color: 'red', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-800' },
  
  // Ship Certificates
  CREATE_SHIP_CERTIFICATE: { icon: '📜', color: 'green', bgColor: 'bg-green-50', borderColor: 'border-green-200', textColor: 'text-green-800' },
  UPDATE_SHIP_CERTIFICATE: { icon: '📝', color: 'blue', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', textColor: 'text-blue-800' },
  DELETE_SHIP_CERTIFICATE: { icon: '🗑️', color: 'red', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-800' },
  
  // Companies
  CREATE_COMPANY: { icon: '🏢', color: 'green', bgColor: 'bg-green-50', borderColor: 'border-green-200', textColor: 'text-green-800' },
  UPDATE_COMPANY: { icon: '✏️', color: 'blue', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', textColor: 'text-blue-800' },
  DELETE_COMPANY: { icon: '🗑️', color: 'red', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-800' },
  
  // Users
  CREATE_USER: { icon: '👤', color: 'green', bgColor: 'bg-green-50', borderColor: 'border-green-200', textColor: 'text-green-800' },
  UPDATE_USER: { icon: '👥', color: 'blue', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', textColor: 'text-blue-800' },
  DELETE_USER: { icon: '🗑️', color: 'red', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-800' },
};
```

### Update getActionLabel (around line 30):
```javascript
const labels = {
  // ... existing labels ...
  
  // Ships
  CREATE_SHIP: language === 'vi' ? 'Thêm tàu' : 'Add Ship',
  UPDATE_SHIP: language === 'vi' ? 'Sửa tàu' : 'Update Ship',
  DELETE_SHIP: language === 'vi' ? 'Xóa tàu' : 'Delete Ship',
  
  // Ship Certificates
  CREATE_SHIP_CERTIFICATE: language === 'vi' ? 'Thêm chứng chỉ tàu' : 'Add Ship Certificate',
  UPDATE_SHIP_CERTIFICATE: language === 'vi' ? 'Sửa chứng chỉ tàu' : 'Update Ship Certificate',
  DELETE_SHIP_CERTIFICATE: language === 'vi' ? 'Xóa chứng chỉ tàu' : 'Delete Ship Certificate',
  
  // Companies
  CREATE_COMPANY: language === 'vi' ? 'Thêm công ty' : 'Add Company',
  UPDATE_COMPANY: language === 'vi' ? 'Sửa công ty' : 'Update Company',
  DELETE_COMPANY: language === 'vi' ? 'Xóa công ty' : 'Delete Company',
  
  // Users
  CREATE_USER: language === 'vi' ? 'Thêm người dùng' : 'Add User',
  UPDATE_USER: language === 'vi' ? 'Sửa người dùng' : 'Update User',
  DELETE_USER: language === 'vi' ? 'Xóa người dùng' : 'Delete User',
};
```

---

## 🧪 Testing Checklist

For each entity:

### Ships
- [ ] Create new ship → Check audit log
- [ ] Update ship (name, IMO, etc.) → Check audit log  
- [ ] Delete ship → Check audit log
- [ ] Filter by entity_type=ship
- [ ] Export logs

### Ship Certificates
- [ ] Create ship certificate → Check audit log
- [ ] Update certificate (expiry, issue date) → Check audit log
- [ ] Delete certificate → Check audit log
- [ ] Filter by entity_type=ship_certificate
- [ ] Export logs

### Companies
- [ ] Create company → Check audit log
- [ ] Update company info → Check audit log
- [ ] Delete/deactivate company → Check audit log
- [ ] Filter by entity_type=company
- [ ] Export logs

### Users
- [ ] Create user → Check audit log
- [ ] Update user (role, department) → Check audit log
- [ ] Delete/deactivate user → Check audit log
- [ ] Filter by entity_type=user
- [ ] Verify password NOT logged
- [ ] Export logs

---

## 📝 Implementation Order

1. ✅ Create mixins (DONE)
2. ✅ Add to CrewAuditLogService (DONE)
3. ⏳ Integrate Ships
4. ⏳ Integrate Ship Certificates
5. ⏳ Integrate Companies
6. ⏳ Integrate Users
7. ⏳ Add frontend labels/icons
8. ⏳ Test all operations
9. ⏳ Verify filters work
10. ⏳ Test export

---

## ⚠️ Common Pitfalls

1. **Field names:** Always verify actual DB field names
2. **User object:** For user logs, distinguish between target user and performing user
3. **Password:** NEVER log password_hash
4. **Dates:** Convert to string for comparison
5. **No changes:** Return None if no actual changes detected
6. **Try-catch:** Always wrap audit log calls to not break main flow
7. **Ship name:** Some entities need ship_name, use '-' if not applicable

---

## 🚀 Quick Integration Script

For fast integration, you can use this pattern:

```python
# Add after any create/update/delete operation
try:
    audit_service = YourService.get_audit_log_service()
    user_dict = {
        'id': current_user.id,
        'username': current_user.username,
        'full_name': current_user.full_name,
        'company': current_user.company
    }
    await audit_service.log_ENTITY_ACTION(...)
except Exception as e:
    logger.error(f"Failed to create audit log: {e}")
```

Replace:
- `YourService` with actual service class name
- `ENTITY_ACTION` with appropriate method (e.g., `ship_create`, `user_update`)
- `...` with required parameters

---

**Last Updated:** 2025-12-09
**Status:** Mixins created, integration pending
**Estimated Time:** 4-6 hours for full integration + testing
