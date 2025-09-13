# Google Drive Integration - Troubleshooting Guide

## Lỗi phổ biến và cách khắc phục

### 1. Lỗi "Folder not found" hoặc "404 Error"

**Lỗi này xảy ra khi:**
- Folder ID không đúng
- Folder đã bị xóa
- Service account chưa có quyền truy cập

**Cách kiểm tra Folder ID đúng:**

1. **Truy cập folder trong Google Drive**
2. **Copy URL đầy đủ**, ví dụ:
   ```
   https://drive.google.com/drive/folders/1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB?usp=sharing
   ```

3. **Chỉ lấy phần Folder ID** (sau `/folders/` và trước `?`):
   ```
   1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB
   ```

**❌ SAI:**
- Copy cả URL: `https://drive.google.com/drive/folders/1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB`
- Copy thiếu hoặc thừa ký tự
- Copy lặp lại: `1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB`

**✅ ĐÚNG:**
- Chỉ ID: `1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB`
- Độ dài thường từ 25-45 ký tự
- Không có khoảng trắng

### 2. Lỗi "Access Denied" hoặc "403 Forbidden"

**Nguyên nhân:**
- Service account chưa được share quyền truy cập folder

**Cách khắc phục:**

1. **Tìm Service Account Email:**
   - Trong file JSON, tìm field `"client_email"`
   - Ví dụ: `"ship-management@my-project.iam.gserviceaccount.com"`

2. **Share folder với Service Account:**
   - Right-click vào folder trong Google Drive
   - Chọn **Share**
   - Nhập Service Account Email
   - Chọn permission: **Editor** (không phải Viewer)
   - Click **Send**

3. **Kiểm tra lại:**
   - Refresh trang Google Drive
   - Kiểm tra folder có hiển thị Service Account trong danh sách share

### 3. Lỗi "Invalid Service Account JSON"

**Nguyên nhân:**
- File JSON bị lỗi format
- Copy thiếu hoặc thừa ký tự

**Cách khắc phục:**

1. **Download lại Service Account Key:**
   - Vào Google Cloud Console
   - IAM & Admin > Service Accounts
   - Chọn service account
   - Tab Keys > Add Key > Create new key
   - Chọn JSON format

2. **Copy đúng cách:**
   - Mở file JSON bằng text editor (Notepad, VS Code)
   - Select All (Ctrl+A)
   - Copy (Ctrl+C)
   - Paste vào textarea trong Ship Management System

3. **Kiểm tra format JSON:**
   - File phải bắt đầu bằng `{`
   - Kết thúc bằng `}`
   - Có các field: `type`, `project_id`, `private_key`, `client_email`

### 4. Lỗi "Folder ID format appears invalid"

**Nguyên nhân:**
- Folder ID quá ngắn hoặc quá dài
- Chứa khoảng trắng
- Copy sai format

**Cách khắc phục:**

1. **Kiểm tra độ dài:**
   - Folder ID hợp lệ: 25-45 ký tự
   - Không có khoảng trắng
   - Chỉ chứa chữ, số, dấu gạch

2. **Copy lại từ URL:**
   - Vào folder trong Google Drive
   - Copy URL từ address bar
   - Chỉ lấy phần sau `/folders/`

### 5. Test Steps chi tiết

**Để test connection thành công:**

1. **Kiểm tra trước khi test:**
   ```
   ✅ Service Account JSON đã copy đầy đủ
   ✅ Folder ID đúng format (25-45 ký tự)
   ✅ Folder đã share với service account email
   ✅ Permission là Editor (không phải Viewer)
   ```

2. **Click Test Connection**

3. **Nếu thành công:** Sẽ hiển thị tên folder
4. **Nếu thất bại:** Đọc message lỗi và làm theo hướng dẫn

### 6. Các bước kiểm tra từng bước

**Bước 1: Kiểm tra Google Drive Folder**
- Folder có tồn tại không?
- Bạn có quyền truy cập không?
- Copy đúng Folder ID chưa?

**Bước 2: Kiểm tra Service Account**
- File JSON có đầy đủ không?
- Client email có đúng không?
- Service account có active không?

**Bước 3: Kiểm tra Share Permission**
- Folder đã share với service account email chưa?
- Permission có phải Editor không?
- Share có bị reject không?

**Bước 4: Kiểm tra Google Cloud Console**
- Google Drive API đã enable chưa?
- Service account key còn hiệu lực không?
- Project có đúng không?

### 7. Tools để debug

**Kiểm tra JSON format:**
```bash
# Paste JSON vào file test.json
cat test.json | python -m json.tool
# Nếu có lỗi thì JSON không hợp lệ
```

**Kiểm tra Folder ID:**
- Độ dài: thường 25-45 ký tự
- Chỉ chứa: a-z, A-Z, 0-9, -, _
- Không có khoảng trắng

### 8. Khi nào liên hệ support

Nếu vẫn không được sau khi làm theo tất cả các bước trên, vui lòng cung cấp:

1. **Screenshot lỗi** (che private key)
2. **Folder ID** đang sử dụng
3. **Service account email**
4. **Các bước đã thực hiện**

**LỚI KHUYÊN:**
- Test với folder mới trước
- Sử dụng service account mới nếu cần
- Đảm bảo Google Drive API đã enable
- Kiểm tra quota usage trong Google Cloud Console

---

*Cập nhật: 13/09/2025*