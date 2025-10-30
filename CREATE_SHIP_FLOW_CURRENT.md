# Flow Hiện Tại Sau Khi Click "Create Ship"

## Tổng Quan Flow

```
User điền form → Click "Create Ship" → Các bước sau diễn ra tuần tự
```

---

## Chi Tiết Từng Bước

### **Bước 1: Tạo Ship Trong Database** (2-3 giây)
```
🔄 API Call: POST /api/ships
📊 Backend: Tạo ship record trong MongoDB
📦 Backend: Start background task tạo Google Drive folder
✅ Backend: Return ship data (id, name, etc.)
```

**Thời gian**: ~2-3 giây
**Blocking**: ✅ User phải đợi bước này

---

### **Bước 2: Hiện Thông Báo Thành Công**
```
✅ Toast: "Tạo tàu [TÊN TÀU] thành công!"
```

**Thời gian**: Ngay lập tức sau Bước 1
**UI Update**: Toast notification xuất hiện

---

### **Bước 3: Đóng Modal và Reset Form**
```
🚪 Modal đóng
🔄 Form reset về trạng thái ban đầu
🗑️ PDF file được xóa (nếu có)
```

**Thời gian**: Ngay lập tức
**User Experience**: Modal biến mất, user có thể làm việc khác

---

### **Bước 4: Navigate và Refresh Ship List**
```
🧭 Navigate to: /certificates (Class & Flag Cert page)
🔄 Trigger: location.state = { refresh: true, newShipId, newShipName }
📊 ClassAndFlagCert: Nhận state → fetchShips()
🔃 GET /api/ships → Load tất cả ships
📋 Ship List: Refresh và hiện ship mới
```

**Thời gian**: ~1-2 giây
**UI Update**: 
- Chuyển trang sang Class & Flag Cert
- Ship list refresh
- **Ship mới xuất hiện trong list ngay lập tức**

---

### **Bước 5: Thông Báo Google Drive (Background)**
```
📁 Toast: "Đang tạo folder Google Drive..."
```

**Thời gian**: Ngay sau navigate
**Non-Blocking**: ✅ Chạy background, không block UI

---

### **Bước 6: Polling Google Drive Status** (Background)
```
⏱️ Wait 3 giây trước khi bắt đầu check
🔄 Poll mỗi 3 giây, tối đa 20 lần (60 giây total)
📡 API Call: GET /api/ships/{shipId}
🔍 Check field: gdrive_folder_status
```

**Các trường hợp:**

#### **Case A: Thành Công** (thường 10-60 giây)
```
✅ Status = "completed"
✅ Toast: "Folder Google Drive cho tàu [TÊN] đã được tạo thành công"
🛑 Stop polling
```

#### **Case B: Thất Bại**
```
❌ Status = "failed" / "timeout" / "error"
⚠️ Toast: "Không thể tạo folder Google Drive: [error message]"
🛑 Stop polling
```

#### **Case C: Timeout (sau 60 giây)**
```
⏰ Hết 20 attempts mà vẫn chưa có status
📁 Toast: "Folder Google Drive đang được tạo trong nền. Bạn có thể tiếp tục làm việc."
🛑 Stop polling
ℹ️ Backend vẫn tiếp tục tạo folder (có thể mất tới 180 giây)
```

---

## Timeline Visualization

```
Thời gian   | User Action                  | UI State                      | Backend Action
------------|------------------------------|-------------------------------|------------------
0s          | Click "Create Ship"          | Loading...                    | Creating ship record
2s          | -                            | ✅ Toast: "Tạo tàu thành công!"| Start GDrive task
2s          | -                            | Modal closes                  | -
2s          | -                            | Navigate to /certificates     | -
3s          | -                            | Ship list shows new ship      | -
3s          | -                            | 📁 Toast: "Đang tạo folder..."| Creating GDrive folder
6s          | User can work normally       | -                             | Creating GDrive folder
9s          | User can work normally       | Poll #1 (check status)        | Creating GDrive folder
12s         | User can work normally       | Poll #2                       | Creating GDrive folder
...         | ...                          | ...                           | ...
30s         | User can work normally       | Poll #10                      | GDrive folder done!
30s         | -                            | ✅ Toast: "Folder tạo xong!"  | -
```

---

## Điểm Quan Trọng

### ✅ **Ưu Điểm:**
1. **Không block user**: Ship xuất hiện trong list ngay (~3 giây)
2. **Không phải đợi Google Drive**: User tiếp tục làm việc
3. **Feedback rõ ràng**: Toast riêng cho từng operation
4. **Graceful degradation**: Ship data được lưu ngay cả khi Google Drive fail

### 📊 **Ship Data Được Lưu Ở Đâu:**
- **MongoDB**: Ngay lập tức sau 2-3 giây
- **Google Drive Folder**: Sau 10-180 giây (background)

### 🔄 **Refresh Mechanism:**
- **Database**: Refresh ngay khi navigate to /certificates
- **Google Drive**: Không cần refresh, backend tự update status

### 🎯 **User Experience:**
```
Điền form (30s) → Create (2s) → ✅ Ship trong list (1s) → Làm việc bình thường
                                   ↓
                              Background: Tạo folder (10-60s)
                                   ↓
                              ✅ Notification khi xong
```

---

## Backend Flow (Tham Khảo)

### **Backend: Create Ship API**
```python
@api_router.post("/ships")
async def create_ship(ship_data):
    # 1. Tạo ship record trong MongoDB
    ship_dict["id"] = str(uuid.uuid4())
    await mongo_db.create("ships", ship_dict)
    
    # 2. Start background task (non-blocking)
    asyncio.create_task(
        create_google_drive_folder_background(ship_dict, current_user)
    )
    
    # 3. Return ngay lập tức
    return ShipResponse(**ship_dict)
```

### **Backend: Background Task**
```python
async def create_google_drive_folder_background(ship_dict, user):
    # Timeout 180 giây
    await asyncio.wait_for(
        create_google_drive_folder_for_new_ship(...),
        timeout=180.0
    )
    
    # Update ship status trong MongoDB
    await mongo_db.update("ships", {"id": ship_id}, {
        "gdrive_folder_status": "completed",  # hoặc "failed"
        "gdrive_folder_created_at": datetime.now(),
        "gdrive_folder_error": error_msg if failed
    })
```

---

## Các Trường Hợp Đặc Biệt

### **Nếu User Navigate Đi Trước Khi Google Drive Xong:**
✅ **OK**: Polling vẫn chạy background
✅ **OK**: Notification vẫn hiện khi xong
✅ **OK**: Status được lưu trong database

### **Nếu User Logout Trước Khi Google Drive Xong:**
✅ **OK**: Backend vẫn tạo folder
✅ **OK**: Status được lưu trong database
❌ **Không**: User không thấy notification (đã logout)
✅ **OK**: Lần login sau, data vẫn đúng

### **Nếu Browser Crash Trong Lúc Tạo:**
✅ **OK**: Ship data đã được lưu trong database
✅ **OK**: Backend vẫn tạo folder
❌ **Không**: Polling bị stop (browser crash)
✅ **OK**: Status được lưu trong database

---

## So Sánh Flow Cũ vs Mới

### **Flow Cũ (Blocking):**
```
Create → Đợi database (2s) → Đợi Google Drive (60s) → Done (62s)
        └─ User phải đợi 62 giây!
```

### **Flow Mới (Non-Blocking):**
```
Create → Đợi database (2s) → Done! User làm việc
                               └─ Background: Google Drive (60s)
        └─ User chỉ đợi 2-3 giây!
```

**Cải thiện**: 62s → 3s = **20x nhanh hơn** (từ góc nhìn user)

---

## Testing Flow

### **Test Normal Case:**
1. Click "Create Ship"
2. ✅ Expect (~2s): Toast "Tạo tàu thành công!"
3. ✅ Expect (~3s): Modal đóng, chuyển sang /certificates
4. ✅ Expect (~3s): Ship xuất hiện trong list
5. ✅ Expect (~3s): Toast "Đang tạo folder Google Drive..."
6. ✅ Expect (~30s): Toast "Folder Google Drive đã được tạo thành công"

### **Test Google Drive Fail:**
1. Disable Google Drive config
2. Click "Create Ship"
3. ✅ Expect: Ship vẫn tạo thành công trong database
4. ✅ Expect: Ship xuất hiện trong list
5. ⚠️ Expect: Toast warning về Google Drive error
6. ✅ Verify: Ship data vẫn intact

---

## Kết Luận

**Flow hiện tại** đảm bảo:
- ✅ **Fast**: User thấy ship trong 3 giây
- ✅ **Non-blocking**: Không phải đợi Google Drive
- ✅ **Reliable**: Ship data luôn được lưu
- ✅ **Informative**: Toast notifications rõ ràng
- ✅ **Resilient**: Hoạt động ngay cả khi Google Drive fail
