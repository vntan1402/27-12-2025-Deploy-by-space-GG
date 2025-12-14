# Permission Inconsistency Fix Plan - Option B

## 🎯 **OBJECTIVE**

Standardize permission logic: **ADMIN = Company-bound (own company only)**
- ADMIN chỉ xem/quản lý data của công ty mình
- Chỉ SUPER_ADMIN & SYSTEM_ADMIN có quyền cross-company

---

## 📊 **MODULES ANALYSIS**

### **✅ CORRECT (Already following Option B)**

| # | Module | File | Logic |
|---|--------|------|-------|
| 1 | **Ship Service** | `ship_service.py` | ✅ Line 34: Only SUPER_ADMIN & SYSTEM_ADMIN can see all companies |
| 2 | **Crew Certificate Service** | `crew_certificate_service.py` | ✅ Line 262, 291, 308: Only SUPER_ADMIN & SYSTEM_ADMIN bypass company filter |

---

### **❌ INCORRECT (Needs fixing - ADMIN has cross-company access)**

| # | Module | File | Issue | Line |
|---|--------|------|-------|------|
| 3 | **Crew Assignment** | `crew_assignment_service.py` | ADMIN in allowed list | 93, 331, 532 |
| 4 | **Crew Service** | `crew_service.py` | ADMIN in allowed list | 136, 251, 346 |
| 5 | **Crew Certificate (Update/Delete)** | `crew_certificate_service.py` | ADMIN in allowed list | 543, 617 |
| 6 | **Ship Service (Update/Delete)** | `ship_service.py` | ADMIN in allowed list | 109, 155 |
| 7 | **User Service** | `user_service.py` | ADMIN has special logic | 78 |

---

### **⚠️ MISSING (No access control implemented)**

| # | Module | File | Issue |
|---|--------|------|-------|
| 8 | **Certificate Service** | `certificate_service.py` | Line 41: `# TODO: Add access control based on user's company` |
| 9 | **Certificate Service (Get by ID)** | `certificate_service.py` | Line 66: `# TODO: Check access permission` |

---

## 🔧 **DETAILED FIX LIST**

### **1. crew_assignment_service.py** ❌

**Location:** Line 93, 331, 532

**Current (WRONG):**
```python
if current_user.role not in ["SYSTEM_ADMIN", "SUPER_ADMIN", "ADMIN"]:
    if crew.get('company_id') != current_user.company:
        raise HTTPException(status_code=403, detail="Access denied")
```

**Fix to:**
```python
if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
    if crew.get('company_id') != current_user.company:
        raise HTTPException(status_code=403, detail="Access denied")
```

**Files to update:** 3 locations

---

### **2. crew_service.py** ❌

**Location:** Line 36-39 (get_all_crew)

**Current (WRONG):**
```python
if current_user.role in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
    crew_list = await CrewRepository.find_all()
else:
    crew_list = await CrewRepository.find_all(company_id=current_user.company)
```
**Status:** ✅ CORRECT for Line 36

**Location:** Line 52-55 (get_crew_by_id)

**Current (WRONG):**
```python
if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
    if crew.get('company_id') != current_user.company:
        raise HTTPException(status_code=403, detail="Access denied")
```
**Status:** ✅ CORRECT

**Location:** Line 136, 251, 346 (update/delete/sync)

**Current (WRONG):**
```python
if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
    if crew.get('company_id') != current_user.company:
        raise HTTPException(status_code=403, detail="Access denied")
```

**Fix to:**
```python
if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
    if crew.get('company_id') != current_user.company:
        raise HTTPException(status_code=403, detail="Access denied")
```

**Files to update:** 3 locations

---

### **3. crew_certificate_service.py** ⚠️

**Location:** Line 262, 291, 308 - ✅ CORRECT (get methods)

**Location:** Line 543, 617 - ❌ WRONG (update/delete methods)

**Current (WRONG):**
```python
if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
    if cert.get('company_id') != current_user.company:
        raise HTTPException(status_code=403, detail="Access denied")
```

**Fix to:**
```python
if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
    if cert.get('company_id') != current_user.company:
        raise HTTPException(status_code=403, detail="Access denied")
```

**Files to update:** 2 locations

---

### **4. ship_service.py** ⚠️

**Location:** Line 34-37 - ✅ CORRECT (get_all_ships)

**Location:** Line 50-52 - ✅ CORRECT (get_ship_by_id)

**Location:** Line 109, 155 - ❌ WRONG (update/delete)

**Current (WRONG):**
```python
if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
    if ship.get('company') != current_user.company:
        raise HTTPException(status_code=403, detail="Access denied")
```

**Fix to:**
```python
if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
    if ship.get('company') != current_user.company:
        raise HTTPException(status_code=403, detail="Access denied")
```

**Files to update:** 2 locations

---

### **5. user_service.py** ⚠️

**Location:** Line 76-80 (get_users)

**Current (SPECIAL CASE):**
```python
if current_user.role in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
    users = await UserRepository.find_all()
elif current_user.role == UserRole.ADMIN:
    users = await UserRepository.find_all(company=current_user.company)
else:
    raise HTTPException(status_code=403, detail="Insufficient permissions")
```

**Fix to:**
```python
if current_user.role in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
    users = await UserRepository.find_all()
elif current_user.role in [UserRole.ADMIN, UserRole.MANAGER]:
    users = await UserRepository.find_all(company=current_user.company)
else:
    raise HTTPException(status_code=403, detail="Insufficient permissions")
```

**Note:** Admin có thể xem users của company mình (để quản lý team)

**Files to update:** 1 location

---

### **6. certificate_service.py** ⚠️

**Location:** Line 37-42 (get_certificates)

**Current (MISSING):**
```python
async def get_certificates(ship_id: Optional[str], current_user: UserResponse) -> List[CertificateResponse]:
    """Get certificates, optionally filtered by ship"""
    certificates = await CertificateRepository.find_all(ship_id=ship_id)
    
    # TODO: Add access control based on user's company  # ← ⚠️ MISSING
```

**Fix to:**
```python
async def get_certificates(ship_id: Optional[str], current_user: UserResponse) -> List[CertificateResponse]:
    """Get certificates, optionally filtered by ship"""
    
    # Add company filtering
    if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
        # Get ships for user's company
        from app.repositories.ship_repository import ShipRepository
        company_ships = await ShipRepository.find_all(company=current_user.company)
        company_ship_ids = [ship['id'] for ship in company_ships]
        
        if ship_id:
            # Verify ship belongs to user's company
            if ship_id not in company_ship_ids:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Filter certificates by company's ships
        certificates = await CertificateRepository.find_all(ship_id=ship_id)
        certificates = [cert for cert in certificates if cert.get('ship_id') in company_ship_ids]
    else:
        certificates = await CertificateRepository.find_all(ship_id=ship_id)
```

**Files to update:** 1 location

---

**Location:** Line 59-66 (get_certificate_by_id)

**Current (MISSING):**
```python
async def get_certificate_by_id(cert_id: str, current_user: UserResponse) -> CertificateResponse:
    """Get certificate by ID"""
    cert = await CertificateRepository.find_by_id(cert_id)
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    # TODO: Check access permission  # ← ⚠️ MISSING
```

**Fix to:**
```python
async def get_certificate_by_id(cert_id: str, current_user: UserResponse) -> CertificateResponse:
    """Get certificate by ID"""
    cert = await CertificateRepository.find_by_id(cert_id)
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    # Check access permission
    if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
        from app.repositories.ship_repository import ShipRepository
        ship = await ShipRepository.find_by_id(cert.get('ship_id'))
        if not ship or ship.get('company') != current_user.company:
            raise HTTPException(status_code=403, detail="Access denied")
```

**Files to update:** 1 location

---

## 📝 **SUMMARY**

### **Files to modify:**

| # | File | Locations | Total Changes |
|---|------|-----------|---------------|
| 1 | `crew_assignment_service.py` | 93, 331, 532 | 3 |
| 2 | `crew_service.py` | 136, 251, 346 | 3 |
| 3 | `crew_certificate_service.py` | 543, 617 | 2 |
| 4 | `ship_service.py` | 109, 155 | 2 |
| 5 | `user_service.py` | 78 | 1 |
| 6 | `certificate_service.py` | 37-42, 59-66 | 2 |

**Total:** 6 files, 13 changes

---

## 🎯 **STANDARDIZED PATTERN**

### **For GET ALL (List)**
```python
if current_user.role in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
    items = await Repository.find_all()  # All companies
else:
    items = await Repository.find_all(company=current_user.company)  # Own company
```

### **For GET BY ID (Single)**
```python
item = await Repository.find_by_id(item_id)

if not item:
    raise HTTPException(status_code=404, detail="Not found")

# Check access
if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
    if item.get('company') != current_user.company:
        raise HTTPException(status_code=403, detail="Access denied")
```

### **For UPDATE/DELETE**
```python
item = await Repository.find_by_id(item_id)

if not item:
    raise HTTPException(status_code=404, detail="Not found")

# Check access (same as GET BY ID)
if current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
    if item.get('company') != current_user.company:
        raise HTTPException(status_code=403, detail="Access denied")

# Proceed with update/delete
```

---

## ✅ **TESTING CHECKLIST**

After fixing, test with different roles:

### **Test Case 1: ADMIN of Company A**
- ✅ Can view Company A ships
- ❌ Cannot view Company B ships
- ✅ Can create/update/delete Company A ships
- ❌ Cannot modify Company B ships

### **Test Case 2: SUPER_ADMIN**
- ✅ Can view all companies
- ✅ Can modify all companies

### **Test Case 3: MANAGER of Company A**
- ✅ Can view Company A data
- ❌ Cannot view Company B data

---

## 🚀 **EXECUTION PLAN**

1. ✅ Create this analysis document
2. 🔧 Fix crew_assignment_service.py (3 changes)
3. 🔧 Fix crew_service.py (3 changes)
4. 🔧 Fix crew_certificate_service.py (2 changes)
5. 🔧 Fix ship_service.py (2 changes)
6. 🔧 Fix user_service.py (1 change)
7. 🔧 Fix certificate_service.py (2 changes)
8. 🧪 Run linter
9. 🧪 Test with different roles
10. ✅ Verify all modules consistent

**Estimated time:** 30-45 minutes
