# 🔧 Fix "Not authenticated" Error

## 🔍 Vấn Đề

Error "Not authenticated" xuất hiện khi test System Google Drive connection.

## ✅ Giải Pháp

### Option 1: Logout và Login lại (Recommended)

1. **Logout** khỏi ứng dụng
2. **Login lại** với: `admin` / `admin123`
3. **Thử test connection** lại

Token có thể đã expired hoặc không hợp lệ.

### Option 2: Clear Browser Cache

1. Mở DevTools (F12)
2. Application tab → Local Storage
3. Xóa `token` và `user`
4. Refresh page
5. Login lại

### Option 3: Test với Incognito Mode

1. Mở Incognito/Private window
2. Truy cập: https://navdrive.preview.emergentagent.com
3. Login: `admin` / `admin123`
4. Test connection

---

## 🐛 Debug Steps (Nếu vẫn lỗi)

### Bước 1: Kiểm tra Token trong Browser

1. Mở DevTools (F12)
2. Console tab
3. Chạy: `localStorage.getItem('token')`
4. Có token không? Copy và gửi cho tôi phần đầu (10 ký tự đầu)

### Bước 2: Kiểm tra Network Request

1. Mở DevTools (F12)
2. Network tab
3. Click "Test Connection"
4. Tìm request `/api/gdrive/configure-proxy`
5. Check:
   - Request Headers có `Authorization: Bearer xxx` không?
   - Response status code là gì? (401? 403? 500?)
6. Screenshot và gửi cho tôi

---

## 🎯 Expected vs Actual

**Expected:**
- User login → Token stored → Request includes token → Backend accepts

**Actual:**
- Request → Backend rejects với "Not authenticated"

**Possible causes:**
1. ❌ Token expired
2. ❌ Token malformed
3. ❌ Token not sent in request
4. ❌ Backend JWT validation failed

---

## 📞 Next Steps

Xin vui lòng:
1. **Thử logout/login lại** và test
2. Nếu vẫn lỗi, **share screenshot** của:
   - Network request headers
   - Console errors (if any)
   - LocalStorage token value (first 10 chars only)

Tôi sẽ giúp debug tiếp! 🚀
