# 🔧 HƯỚNG DẪN RE-DEPLOY APPS SCRIPT (Chi tiết từng bước)

## ⚠️ Vấn đề hiện tại:
- Code Apps Script: ✅ ĐÚNG
- POST requests: ❌ Trả về HTML thay vì JSON
- **Nguyên nhân:** Deployment settings chưa đúng

---

## 📋 Các bước RE-DEPLOY (Quan trọng!)

### Bước 1: Mở Apps Script Editor

1. Truy cập: https://script.google.com
2. Đăng nhập với Google Account của bạn
3. Tìm project có tên như: "Ship Management" hoặc tương tự
4. Click vào project để mở editor

---

### Bước 2: Verify Code

Kiểm tra xem code có đúng không:

✅ **Check function doPost():**
```javascript
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    validateApiKey(payload);
    // ... rest
  }
}
```

✅ **Check API_KEY:**
```javascript
const API_KEY = 'Vntan1402sms';
```

✅ **Check ROOT_FOLDER_ID:**
```javascript
const ROOT_FOLDER_ID = '1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB';
```

---

### Bước 3: QUAN TRỌNG - Deploy với Settings Đúng

#### 3.1. Click "Deploy" button (góc trên bên phải)

- Nếu chưa deploy bao giờ: Click **"New deployment"**
- Nếu đã deploy rồi: Click **"Manage deployments"**

#### 3.2. Nếu đã có deployment (Manage deployments):

1. Bạn sẽ thấy list các deployments
2. Click **⚙️ icon** (Settings) bên cạnh deployment đang active
3. Click **"Edit"**
4. Hoặc click **"New deployment"** để tạo deployment mới

#### 3.3. Configuration Settings (CỰC KỲ QUAN TRỌNG):

**Mô tả (Description):**
```
Ship Management GDrive Proxy v2.0 - POST enabled
```

**Select type:**
- Click biểu tượng ⚙️ (gear/settings)
- Chọn: **Web app** ✅

**Execute as (Thực thi với quyền của):**
```
┌─────────────────────────────────────┐
│ Execute as:                         │
│ ┌─────────────────────────────────┐ │
│ │ ● Me (your-email@gmail.com)    │←── ✅ CHỌN CÁI NÀY
│ │ ○ User accessing the web app   │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```
⚠️ **PHẢI CHỌN: "Me"**

**Who has access (Ai có quyền truy cập):**
```
┌─────────────────────────────────────┐
│ Who has access:                     │
│ ┌─────────────────────────────────┐ │
│ │ ○ Only myself                  │ │
│ │ ● Anyone                       │←── ✅ CHỌN CÁI NÀY
│ │ ○ Anyone with Google account   │←── ❌ KHÔNG CHỌN
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```
⚠️ **PHẢI CHỌN: "Anyone"** (KHÔNG phải "Anyone with Google account")

---

### Bước 4: Deploy & Authorize

1. Click **"Deploy"** button
2. Một popup sẽ xuất hiện với 2 options:
   - **"Authorize access"** ← Click vào đây
3. Chọn Google Account của bạn
4. Có thể thấy warning: "This app isn't verified"
   - Click **"Advanced"** (Nâng cao)
   - Click **"Go to [Project name] (unsafe)"**
5. Review permissions:
   - ✅ "See, edit, create, and delete all of your Google Drive files"
   - Click **"Allow"**

---

### Bước 5: Copy URL

Sau khi deploy thành công:

1. Popup hiển thị thông tin deployment
2. Tìm dòng **"Web app URL"**:
   ```
   https://script.google.com/macros/s/AKfycby.../exec
   ```
3. **Copy toàn bộ URL**
4. Click **"Done"**

---

### Bước 6: TEST với curl

```bash
WEB_APP_URL="PASTE_YOUR_NEW_URL_HERE"
API_KEY="Vntan1402sms"

curl -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d "{\"action\": \"test_connection\", \"api_key\": \"$API_KEY\"}"
```

**Expected Response (✅ SUCCESS):**
```json
{
  "success": true,
  "message": "Connection successful",
  "data": {
    "status": "Connected",
    "folder_name": "Your Folder Name",
    "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
  }
}
```

**Wrong Response (❌ FAILED):**
```html
<HTML>
<HEAD>
<TITLE>Moved Temporarily</TITLE>
```

Nếu vẫn thấy HTML → Settings vẫn chưa đúng, quay lại Bước 3.

---

## 🎯 Common Mistakes (Sai lầm phổ biến)

### ❌ Mistake 1: Chọn "Anyone with Google account"
**Why wrong:** Requires user to login, blocks POST from external services

**Fix:** Chọn **"Anyone"** (không có "with Google account")

### ❌ Mistake 2: Chọn "User accessing the web app"
**Why wrong:** Code chạy với quyền của user (không có quyền Drive)

**Fix:** Chọn **"Me"** (code chạy với quyền của bạn)

### ❌ Mistake 3: Chỉ Save code, không Deploy
**Why wrong:** Code mới không được apply

**Fix:** Phải click **"Deploy"** (không chỉ Save)

### ❌ Mistake 4: Deploy version cũ
**Why wrong:** Version mới không được activate

**Fix:** Trong Manage deployments, đảm bảo deployment mới là "Active"

---

## 📸 Visual Guide (Text-based)

```
Apps Script Editor
┌─────────────────────────────────────────────────────────┐
│  🔨 Deploy ▼                                      Run ▶ │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Code.gs                                                │
│  ┌───────────────────────────────────────────────────┐ │
│  │ function doPost(e) {                              │ │
│  │   try {                                           │ │
│  │     const payload = JSON.parse(e.postData...     │ │
│  │     validateApiKey(payload);                     │ │
│  │     ...                                           │ │
│  │   }                                               │ │
│  │ }                                                 │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                    ↓ Click "Deploy"
                    
Deployment Configuration
┌─────────────────────────────────────────────────────────┐
│ New deployment                                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Select type:                                            │
│   [⚙️ Web app]  ← Click this gear icon                 │
│                                                         │
│ Description:                                            │
│   [Ship Management GDrive Proxy v2.0]                  │
│                                                         │
│ Execute as:                                             │
│   [● Me (your-email@gmail.com)]  ← Must select this   │
│   [○ User accessing the web app]                       │
│                                                         │
│ Who has access:                                         │
│   [○ Only myself]                                       │
│   [● Anyone]  ← Must select this (NOT "with account") │
│   [○ Anyone with Google account]  ← DON'T select      │
│                                                         │
│              [Cancel]  [Deploy]  ← Click Deploy        │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Alternative: New Deployment from Scratch

Nếu cách trên không work, thử tạo deployment hoàn toàn mới:

1. **Delete old deployment:**
   - Deploy > Manage deployments
   - Click 🗑️ (trash icon) bên cạnh deployment cũ
   - Confirm deletion

2. **Create fresh deployment:**
   - Deploy > New deployment
   - Follow Bước 3 ở trên
   - Deploy với settings đúng
   - Copy URL mới

3. **Test URL mới**

---

## ✅ Final Checklist

Trước khi test, đảm bảo:

- [ ] Code có function `doPost(e)`
- [ ] API_KEY = "Vntan1402sms"
- [ ] ROOT_FOLDER_ID = "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
- [ ] Deployment type: **Web app**
- [ ] Execute as: **Me**
- [ ] Who has access: **Anyone** (NOT "Anyone with Google account")
- [ ] Đã authorize permissions
- [ ] Đã copy URL mới
- [ ] Test với curl trả về JSON (không phải HTML)

---

## 📞 Nếu vẫn không work:

1. Screenshot deployment settings
2. Test với curl và copy full response
3. Check Apps Script execution logs:
   - Click ⏱️ (Executions) ở sidebar
   - Xem có error gì không

---

**Thời gian:** 5-10 phút để hoàn thành
**Quan trọng nhất:** Settings "Who has access: Anyone"
