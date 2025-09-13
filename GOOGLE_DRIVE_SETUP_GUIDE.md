# Hướng dẫn Thiết lập Google Drive Integration

## Tổng quan
Ship Management System đã được tích hợp với Google Drive để đồng bộ dữ liệu tự động. Tính năng này chỉ dành cho **Super Admin**.

## Các bước thiết lập

### 1. Tạo Google Cloud Project
1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project hiện có
3. Ghi nhớ **Project ID**

### 2. Enable Google Drive API
1. Trong Google Cloud Console, vào **APIs & Services** > **Library**
2. Tìm kiếm "Google Drive API"
3. Click **Enable** để kích hoạt API

### 3. Tạo Service Account
1. Vào **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **Service Account**
3. Nhập thông tin:
   - Service account name: `ship-management-service`
   - Service account ID: `ship-management-service`
   - Description: `Service account for Ship Management System`
4. Click **Create and Continue**
5. Skip roles (để trống) và click **Done**

### 4. Tạo Service Account Key
1. Trong danh sách Service Accounts, click vào service account vừa tạo
2. Vào tab **Keys**
3. Click **Add Key** > **Create new key**
4. Chọn **JSON** format
5. Click **Create** - file JSON sẽ được download tự động
6. **Quan trọng**: Lưu file JSON này an toàn, đây là credential để truy cập Google Drive

### 5. Tạo Google Drive Folder
1. Truy cập [Google Drive](https://drive.google.com)
2. Tạo folder mới với tên: `Ship Management Data`
3. Copy **Folder ID** từ URL:
   ```
   https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                     Đây là Folder ID
   ```

### 6. Chia sẻ Folder với Service Account
1. Right-click vào folder vừa tạo
2. Chọn **Share**
3. Trong ô **Add people and groups**, nhập email của service account 
   (có trong file JSON, field `client_email`)
4. Chọn permission: **Editor**
5. Click **Send**

### 7. Cấu hình trong Ship Management System
1. Login với tài khoản **Super Admin**
2. Vào **System Settings** (CÀI ĐẶT HỆ THỐNG)
3. Tìm section **System Google Drive Configuration**
4. Click **Configure System Google Drive**
5. Trong modal:
   - **Service Account JSON**: Copy toàn bộ nội dung file JSON vào đây
   - **Google Drive Folder ID**: Paste Folder ID từ bước 5
6. Click **Test Connection** để kiểm tra kết nối
7. Nếu test thành công, click **Save Configuration**

## Sử dụng Google Drive Integration

### Đồng bộ dữ liệu
Sau khi cấu hình thành công, bạn sẽ thấy 2 nút:

1. **☁️↑ Sync to Drive**: Đồng bộ dữ liệu từ hệ thống lên Google Drive
2. **☁️↓ Sync from Drive**: Đồng bộ dữ liệu từ Google Drive về hệ thống

### Tự động đồng bộ
Hệ thống sẽ tự động sync lên Google Drive khi:
- Tạo mới user
- Cập nhật user  
- Tạo mới company
- Cập nhật company
- Các thay đổi quan trọng khác

## File được đồng bộ

Các file sau sẽ được đồng bộ:
- `users.json` - Dữ liệu người dùng
- `companies.json` - Dữ liệu công ty
- `ships.json` - Dữ liệu tàu
- `certificates.json` - Dữ liệu chứng chỉ
- `ai_config.json` - Cấu hình AI
- `usage_tracking.json` - Theo dõi sử dụng

## Khắc phục sự cố

### Lỗi "Invalid Service Account JSON"
- Kiểm tra format JSON có đúng không
- Đảm bảo copy toàn bộ nội dung file JSON

### Lỗi "Cannot access folder"
- Kiểm tra Folder ID có đúng không
- Đảm bảo đã share folder với service account email
- Kiểm tra permission là **Editor**

### Lỗi "Failed to configure Google Drive"
- Kiểm tra Google Drive API đã được enable chưa
- Kiểm tra service account key còn hiệu lực
- Kiểm tra network connection

### Test Connection thất bại
- Đảm bảo tất cả bước setup đã thực hiện đúng
- Kiểm tra service account JSON và folder ID
- Thử tạo folder mới và share lại

## Bảo mật

**Quan trọng**: 
- Service Account JSON chứa private key, cần bảo mật tuyệt đối
- Không share hoặc commit file JSON vào source code
- Chỉ Super Admin mới có quyền cấu hình Google Drive
- Định kỳ rotate service account key (khuyến nghị 90 ngày)

## Support

Nếu gặp vấn đề, vui lòng cung cấp thông tin:
1. Screenshot màn hình lỗi
2. Message lỗi chi tiết
3. Các bước đã thực hiện
4. Log file (nếu có)

---

*Tài liệu này được tạo cho Ship Management System v1.0*