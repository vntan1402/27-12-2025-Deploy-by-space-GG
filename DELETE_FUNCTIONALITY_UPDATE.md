# Certificate Delete with Google Drive File Removal

## ✅ ĐÃ HOÀN THÀNH

### 🎯 **Chức năng đã thêm:**
1. **Google Apps Script Action**: Thêm `delete_file` action để xóa file trên Google Drive
2. **Backend API**: Thêm endpoint `/companies/{company_id}/gdrive/delete-file` để xóa file
3. **Certificate Delete**: Cập nhật endpoint DELETE certificate để tự động xóa file Google Drive
4. **Multi Delete**: Hỗ trợ xóa nhiều certificate cùng lúc và xóa tất cả file tương ứng

---

## 📝 **HƯỚNG DẪN CẬP NHẬT GOOGLE APPS SCRIPT**

### Bước 1: Mở Google Apps Script
1. Truy cập [Google Apps Script](https://script.google.com/)
2. Mở project Apps Script hiện tại của bạn
3. Mở file `Code.gs`

### Bước 2: Thay thế toàn bộ code
Copy toàn bộ nội dung từ file `/app/FINAL_GOOGLE_APPS_SCRIPT.js` và thay thế vào Apps Script của bạn.

**Các action mới đã thêm:**
- `delete_file`: Xóa file khỏi Google Drive
- `get_folder_structure`: Lấy cấu trúc thư mục (cho Move functionality)
- `move_file`: Di chuyển file giữa các thư mục

### Bước 3: Deploy lại Apps Script
1. Nhấn **Deploy** → **New deployment**
2. Chọn **Web app**
3. Set **Execute as**: Me (email của bạn)
4. Set **Who has access**: Anyone
5. Nhấn **Deploy**
6. Copy URL mới (nếu có)

### Bước 4: Cập nhật URL (nếu cần)
Nếu URL Apps Script thay đổi:
1. Đăng nhập vào Ship Management System
2. Vào **System Settings** → **Company Management**
3. Edit Google Drive configuration của company
4. Cập nhật **Apps Script URL** với URL mới
5. Test connection

---

## 🔧 **TÁC DỤNG CỦA CHỨC NĂNG MỚI**

### Khi xóa Certificate đơn lẻ:
1. ✅ Xóa certificate khỏi database
2. ✅ Tự động xóa file tương ứng trên Google Drive
3. ✅ Hiển thị thông báo thành công

### Khi xóa nhiều Certificate:
1. ✅ Xóa từng certificate khỏi database  
2. ✅ Xóa từng file tương ứng trên Google Drive
3. ✅ Hiển thị số lượng certificate đã xóa

### Xử lý lỗi thông minh:
- ✅ Nếu file không tồn tại trên Google Drive → Tiếp tục xóa certificate
- ✅ Nếu không có quyền xóa file → Cảnh báo nhưng vẫn xóa certificate
- ✅ Ghi log chi tiết để theo dõi

---

## 📊 **THÔNG TIN KỸ THUẬT**

### Delete File Action Parameters:
```javascript
{
  "action": "delete_file",
  "file_id": "1ABC123...",
  "permanent_delete": false  // true = xóa vĩnh viễn, false = vào thùng rác
}
```

### Response từ Apps Script:
```javascript
{
  "success": true,
  "message": "File deleted successfully",
  "file_id": "1ABC123...",
  "file_name": "certificate.pdf",
  "delete_method": "moved_to_trash",  // hoặc "permanently_deleted"
  "deleted_timestamp": "2025-01-20T10:30:00Z"
}
```

### Backend Endpoint:
```
POST /api/companies/{company_id}/gdrive/delete-file
{
  "file_id": "1ABC123...",
  "permanent_delete": false
}
```

---

## 🧪 **KIỂM TRA CHỨC NĂNG**

### Test Case 1: Xóa Certificate đơn lẻ
1. Đăng nhập với admin1/123456
2. Chọn ship bất kỳ
3. Vào Documents → Certificates
4. Right-click certificate và chọn **Delete**
5. Xác nhận xóa
6. **Kết quả mong đợi**: 
   - Certificate biến mất khỏi list
   - File trên Google Drive cũng bị xóa
   - Thông báo thành công

### Test Case 2: Xóa nhiều Certificate
1. Check multiple certificates bằng checkbox
2. Right-click và chọn **Delete**
3. Xác nhận xóa
4. **Kết quả mong đợi**:
   - Tất cả certificate đã chọn biến mất
   - Tất cả file tương ứng trên Google Drive bị xóa
   - Thông báo số lượng đã xóa

### Test Case 3: Certificate không có file
1. Xóa certificate không có `gdrive_file_id`
2. **Kết quả mong đợi**:
   - Certificate vẫn bị xóa thành công
   - Không có lỗi xảy ra

---

## ⚠️ **LƯU Ý QUAN TRỌNG**

### Chế độ xóa file:
- **Mặc định**: File được chuyển vào **Thùng rác** Google Drive (có thể khôi phục)
- **Permanent Delete**: Có thể cấu hình để xóa vĩnh viễn (không khôi phục được)

### Tương thích ngược:
- ✅ Certificate cũ không có `gdrive_file_id` vẫn xóa được bình thường
- ✅ Không ảnh hưởng đến certificate đã tồn tại
- ✅ Apps Script cũ vẫn hoạt động (chỉ thêm action mới)

### Quyền truy cập:
- Apps Script cần quyền **Editor** hoặc **Owner** với Google Drive
- Nếu không có quyền xóa file → Chỉ cảnh báo, không fail

---

## 🎉 **HOÀN THÀNH**

Chức năng đã được triển khai hoàn chỉnh:

1. ✅ **Google Apps Script**: Đã thêm `delete_file` action
2. ✅ **Backend**: Đã cập nhật DELETE certificate endpoint  
3. ✅ **Frontend**: Không cần thay đổi (tự động hoạt động)
4. ✅ **Error Handling**: Xử lý lỗi thông minh và an toàn
5. ✅ **Logging**: Ghi log chi tiết cho việc debug

**Bây giờ khi xóa certificate, file trên Google Drive sẽ tự động được xóa theo! 🚀**