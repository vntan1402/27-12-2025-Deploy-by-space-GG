# 🔐 BẢNG PHÂN QUYỀN CHI TIẾT

## ⚠️ QUY TẮC QUAN TRỌNG

**User chỉ có thể tạo users có role THẤP HƠN hoặc NGANG BẰNG (trừ ADMIN xuống)**

---

## 📊 ROLE HIERARCHY

```
Level 6: SYSTEM_ADMIN    (Cao nhất)
Level 5: SUPER_ADMIN     
Level 4: ADMIN           
Level 3: MANAGER         
Level 2: EDITOR          
Level 1: VIEWER          (Thấp nhất)
```

---

## 👥 MA TRẬN QUYỀN TẠO USER

| Current Role | Có thể tạo roles | Không thể tạo |
|--------------|------------------|---------------|
| **SYSTEM_ADMIN** (Lv 6) | ✅ system_admin<br>✅ super_admin<br>✅ admin<br>✅ manager<br>✅ editor<br>✅ viewer | ❌ Không có giới hạn |
| **SUPER_ADMIN** (Lv 5) | ✅ super_admin<br>✅ admin<br>✅ manager<br>✅ editor<br>✅ viewer | ❌ system_admin |
| **ADMIN** (Lv 4) | ✅ manager<br>✅ editor<br>✅ viewer | ❌ system_admin<br>❌ super_admin<br>❌ admin |
| **MANAGER** (Lv 3) | ✅ editor<br>✅ viewer | ❌ system_admin<br>❌ super_admin<br>❌ admin<br>❌ manager |
| **EDITOR** (Lv 2) | ❌ Không có quyền | ❌ Tất cả |
| **VIEWER** (Lv 1) | ❌ Không có quyền | ❌ Tất cả |

---

## 🎯 CHIẾN LƯỢC SETUP PRODUCTION

### ✅ CÁCH ĐÚNG (Recommended):

#### Bước 1: Tạo SYSTEM_ADMIN đầu tiên
```bash
cd /app/backend
python3 quick_create_admin.py

# File đã được update:
# Role: "system_admin" (không phải "super_admin")
```

**Kết quả:**
```
✅ Username: system_admin
✅ Role: SYSTEM_ADMIN (Level 6)
✅ Có thể tạo: TẤT CẢ ROLES
```

#### Bước 2: Login với SYSTEM_ADMIN

#### Bước 3: Tạo các roles khác qua UI
```
System Settings → User Management → Add User

Có thể tạo:
✅ SUPER_ADMIN (cho IT department)
✅ ADMIN (cho mỗi công ty)
✅ MANAGER (cho departments)
✅ EDITOR (cho ship officers)
✅ VIEWER (cho crew members)
```

---

### ❌ SAI LẦM THƯỜNG GẶP:

#### Lỗi 1: Tạo SUPER_ADMIN đầu tiên
```
❌ Nếu tạo super_admin đầu tiên:
   → Không thể tạo system_admin sau này!
   → Chỉ có thể tạo: super_admin, admin, manager, editor, viewer
   
✅ Giải pháp: Tạo SYSTEM_ADMIN từ đầu
```

#### Lỗi 2: ADMIN cố tạo SUPER_ADMIN
```
❌ Admin (Level 4) tạo super_admin (Level 5):
   → Bị chặn bởi hệ thống
   → Error: "You do not have permission to create user with this role"
   
✅ Giải pháp: Chỉ system_admin hoặc super_admin mới tạo được super_admin
```

#### Lỗi 3: Không có SYSTEM_ADMIN nào
```
❌ Nếu không có system_admin trong production:
   → Không ai có thể tạo system_admin
   → Cần chạy lại script create_first_admin.py
   
✅ Giải pháp: Luôn có ít nhất 1 SYSTEM_ADMIN
```

---

## 📋 SETUP MẪU CHO MỘT TỔ CHỨC

### Ví dụ: ABC Maritime Group (3 công ty)

#### Level 1: System Level (1 người)
```
👤 IT Administrator
   Role: SYSTEM_ADMIN
   Company: None (quản lý toàn hệ thống)
   Username: it_admin
   
   Quyền:
   ✅ Quản lý tất cả companies
   ✅ Tạo system_admin khác
   ✅ Tạo bất kỳ role nào
   ✅ System settings
```

#### Level 2: Company Level (1 người/công ty)
```
👤 Company Admin - ABC Ship Management
   Role: ADMIN
   Company: ABC Ship Management
   Username: abc_admin
   
   Quyền:
   ✅ Quản lý users của ABC Ship Management
   ✅ Tạo: manager, editor, viewer
   ❌ Không tạo: system_admin, super_admin, admin
   ❌ Không xem companies khác

👤 Company Admin - ABC Crewing
   Role: ADMIN  
   Company: ABC Crewing
   Username: abccrew_admin

👤 Company Admin - ABC Technical
   Role: ADMIN
   Company: ABC Technical  
   Username: abctech_admin
```

#### Level 3: Department Level (nhiều người)
```
👤 Operations Manager
   Role: MANAGER
   Company: ABC Ship Management
   Department: Operations
   Username: ops_manager
   
   Quyền:
   ✅ Xem tất cả data của công ty
   ✅ Tạo: editor, viewer
   ❌ Không tạo: manager, admin, super_admin, system_admin

👤 Technical Manager
   Role: MANAGER
   Company: ABC Ship Management
   Department: Technical
   Username: tech_manager
```

#### Level 4: Ship Level (nhiều người)
```
👤 Chief Officer - MV Ocean Star
   Role: EDITOR
   Ship: MV Ocean Star
   Department: Ship Crew, SSO
   Username: oceanstar_co
   
   Quyền:
   ✅ Upload/edit documents của MV Ocean Star
   ✅ Xem certificates
   ❌ Không tạo users
   ❌ Không xóa documents

👤 Chief Engineer - MV Sea Explorer  
   Role: EDITOR
   Ship: MV Sea Explorer
   Username: seaexplorer_ce
```

#### Level 5: Crew Level (nhiều người)
```
👤 Crew Member
   Role: VIEWER
   Ship: MV Ocean Star
   Username: crew_john
   
   Quyền:
   ✅ Xem documents của MV Ocean Star
   ✅ Download documents
   ❌ Không upload
   ❌ Không edit
   ❌ Không tạo users
```

---

## 🔄 WORKFLOW TẠO USERS ĐÚNG

### Scenario 1: Công ty mới join hệ thống

**Bước 1:** SYSTEM_ADMIN tạo company
```
System Settings → Company Management → Add Company
```

**Bước 2:** SYSTEM_ADMIN tạo ADMIN cho công ty đó
```
System Settings → User Management → Add User
Role: ADMIN
Company: [New Company]
```

**Bước 3:** ADMIN của công ty tạo các users khác
```
Login với company admin account
Tạo: Managers, Editors, Viewers cho công ty
```

---

### Scenario 2: Thêm Ship Officer mới

**Ai có thể làm:**
- ✅ SYSTEM_ADMIN
- ✅ SUPER_ADMIN  
- ✅ ADMIN của công ty
- ✅ MANAGER của công ty

**Không thể:**
- ❌ EDITOR khác
- ❌ VIEWER

**Cách làm:**
```
System Settings → User Management → Add User
Role: EDITOR
Ship: [Select Ship]
Department: Ship Crew
```

---

### Scenario 3: Cần tạo thêm SYSTEM_ADMIN

**Chỉ ai có thể:**
- ✅ SYSTEM_ADMIN hiện tại (duy nhất)

**Không thể:**
- ❌ SUPER_ADMIN (bị chặn)
- ❌ Tất cả roles khác

**Cách làm:**
```
Login với system_admin account
System Settings → User Management → Add User
Role: SYSTEM_ADMIN
Company: None
```

---

## 🚨 BẢO MẬT & BEST PRACTICES

### 1. **Số lượng SYSTEM_ADMIN**
```
✅ Recommended: 1-2 người
⚠️  Lý do:
   - Quyền cao nhất
   - Có thể tạo system_admin khác
   - Quản lý toàn hệ thống
   
💡 Tip: Chỉ gán cho IT Administrator thực sự tin cậy
```

### 2. **Số lượng ADMIN mỗi công ty**
```
✅ Recommended: 1-3 người/công ty
💡 Tip: 
   - 1 Technical Superintendent (primary)
   - 1 Operations Manager (backup)
   - 1 IT Support (nếu cần)
```

### 3. **Tránh Role Inflation**
```
❌ Không nên:
   - Tạo quá nhiều ADMIN
   - Cho EDITOR quyền MANAGER khi không cần
   - Tạo SUPER_ADMIN cho mọi người

✅ Nên:
   - Gán role tối thiểu cần thiết
   - Review permissions định kỳ
   - Downgrade role khi không còn cần
```

### 4. **Audit Trail**
```
📊 Định kỳ review:
   - Ai có SYSTEM_ADMIN access?
   - Ai có ADMIN access?
   - Users không active → deactivate
   - Permissions có đúng không?
```

---

## 📊 QUICK REFERENCE TABLE

| Cần tạo role | Cần đăng nhập với | Có thể? |
|--------------|-------------------|---------|
| SYSTEM_ADMIN | SYSTEM_ADMIN | ✅ Yes |
| SYSTEM_ADMIN | SUPER_ADMIN | ❌ No |
| SUPER_ADMIN | SYSTEM_ADMIN | ✅ Yes |
| SUPER_ADMIN | SUPER_ADMIN | ✅ Yes |
| SUPER_ADMIN | ADMIN | ❌ No |
| ADMIN | SYSTEM_ADMIN | ✅ Yes |
| ADMIN | SUPER_ADMIN | ✅ Yes |
| ADMIN | ADMIN | ❌ No |
| MANAGER | ADMIN | ✅ Yes |
| MANAGER | MANAGER | ❌ No |
| EDITOR | ADMIN | ✅ Yes |
| EDITOR | MANAGER | ✅ Yes |
| VIEWER | ADMIN | ✅ Yes |
| VIEWER | MANAGER | ✅ Yes |
| VIEWER | EDITOR | ❌ No |

---

## ✅ CHECKLIST DEPLOYMENT

```
□ ✅ Chạy quick_create_admin.py (đã update thành system_admin)
□ ✅ Verify role = "system_admin" (không phải super_admin)
□ ✅ Login thành công
□ ✅ Test tạo super_admin qua UI → thành công
□ ✅ Test tạo admin qua UI → thành công
□ ✅ Logout, login với admin
□ ✅ Test admin không tạo được super_admin → đúng
□ ✅ Test admin tạo được manager → thành công
```

---

## 🎯 TÓM TẮT

### QUY TẮC VÀNG:
1. **Luôn tạo SYSTEM_ADMIN đầu tiên** ✅
2. **User chỉ tạo role thấp hơn mình** (trừ super_admin tạo được super_admin)
3. **Không có role nào tự nâng cấp được** ❌
4. **Cần system_admin để tạo system_admin** ✅

### SCRIPTS ĐÃ ĐƯỢC UPDATE:
```
✅ quick_create_admin.py → Role: "system_admin"
✅ create_first_admin.py → Role: "system_admin"
```

### SAU KHI DEPLOY:
```
1. Run: python3 quick_create_admin.py
2. Login với system_admin
3. Tạo các roles khác qua UI theo hierarchy
4. Done! ✅
```

---

**Cảm ơn bạn đã chỉ ra lỗi! Giờ đây tài liệu đã CHÍNH XÁC 100%** 🎯
