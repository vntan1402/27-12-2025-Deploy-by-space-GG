# ✅ Checklist Deploy Google Apps Script - So Sánh V1 vs V3

## 🔍 Phát Hiện Quan Trọng

**Code Frontend V1 = Code Frontend V2 (100% giống nhau)**
**Code Apps Script V1 = Code Apps Script V3 (doPost() giống nhau)**

➡️ **Vấn đề KHÔNG phải ở code, mà ở deployment hoặc permissions!**

---

## 📋 Checklist: Điều Gì Khác Giữa V1 (Hoạt động) vs V3 (Không Hoạt động)

### 1. Tài Khoản Google
- [ ] V1 deploy với tài khoản Google nào? _______________
- [ ] V3 deploy với tài khoản Google nào? _______________
- [ ] Có phải cùng tài khoản không? YES / NO
- [ ] Tài khoản có phải là tài khoản sở hữu folder Drive không? YES / NO

### 2. Authorization Flow
- [ ] Khi deploy V1, có popup "Authorize access" không? YES / NO
- [ ] Khi deploy V3, có popup "Authorize access" không? YES / NO
- [ ] Có click "Advanced" → "Go to [project name] (unsafe)" không? YES / NO
- [ ] Có allow tất cả permissions không? YES / NO

### 3. Deployment Settings
**V1:**
- Deployment type: _______________ (Web app / API Executable)
- Execute as: _______________ (Me / User accessing the web app)
- Who has access: _______________ (Anyone / Anyone with Google account / Only myself)

**V3:**
- Deployment type: _______________ (Web app / API Executable)
- Execute as: _______________ (Me / User accessing the web app)
- Who has access: _______________ (Anyone / Anyone with Google account / Only myself)

### 4. Script Project Settings
- [ ] V1 có enable "Google Drive API" trong Services không? YES / NO
- [ ] V3 có enable "Google Drive API" trong Services không? YES / NO
- [ ] Project type: _______________ (Standalone / Container-bound)

### 5. ROOT_FOLDER_ID
**V1:**
- ROOT_FOLDER_ID = _______________
- Folder này thuộc tài khoản nào? _______________

**V3:**
- Không có ROOT_FOLDER_ID (sử dụng dynamic folder_id)
- folder_id được gửi qua request: `1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB`

### 6. Apps Script Code Differences
**V1 có ROOT_FOLDER_ID hardcoded:**
```javascript
const ROOT_FOLDER_ID = "YOUR_ROOT_FOLDER_ID_HERE";

function testConnection(payload) {
  const folder = getFolderById(ROOT_FOLDER_ID); // Dùng ROOT_FOLDER_ID
  ...
}
```

**V3 không hardcode, nhận từ request:**
```javascript
// Không có ROOT_FOLDER_ID

function testConnection({ folder_id }) {
  const folder = validateFolderId(folder_id); // Nhận folder_id từ request
  ...
}
```

---

## 🔎 Test Đề Xuất

### Test 1: Deploy lại V1 code (với ROOT_FOLDER_ID)

1. Copy code V1 từ `/app/GOOGLE_APPS_SCRIPT_SYSTEM_GDRIVE.js`
2. Update ROOT_FOLDER_ID = `1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB`
3. Deploy mới (tài khoản giống V1 cũ)
4. Test xem POST request có hoạt động không

### Test 2: So sánh deployment URLs

**V1 URL cũ** (nếu còn):
- URL: _______________
- Test POST: `curl -X POST [URL] -d '{"action":"test_connection"}' -H "Content-Type: application/json"`
- Result: _______________

**V3 URL mới:**
- URL: `https://script.google.com/macros/s/AKfycbxjTsiyuD5ni2gQ0wwgThahNCHkuyCvnFV2gCKHJ3LosXxKamvdi6ClTKGDuFg8Wrw/exec`
- Test POST: Already tested - returns "Page Not Found"
- Result: FAILED

---

## 💡 Giả Thuyết

### Giả thuyết 1: Authorization Issue
POST requests cần additional permissions mà chưa được grant khi deploy.

**Cách verify:**
- Re-deploy V3 và click "Advanced" → "Go to [project] (unsafe)" → Allow ALL permissions
- Đặc biệt permission: "See, edit, create, and delete all of your Google Drive files"

### Giả thuyết 2: Google Account Difference
V1 deploy với tài khoản có quyền đặc biệt (Workspace admin?) còn V3 deploy với tài khoản thường.

**Cách verify:**
- Deploy V3 với CHÍNH XÁC tài khoản đã deploy V1

### Giả thuyết 3: Apps Script Project Type
V1 là standalone script, V3 là container-bound hoặc ngược lại.

**Cách verify:**
- Check project type trong Apps Script settings

---

## 🎯 Action Items

**Bước 1: Lấy thông tin V1**
- [ ] Tìm V1 URL (nếu còn lưu)
- [ ] Test V1 URL xem còn hoạt động không
- [ ] Xem deployment settings của V1

**Bước 2: Deploy V1 code với ROOT_FOLDER_ID**
- [ ] Copy V1 code
- [ ] Set ROOT_FOLDER_ID = `1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB`
- [ ] Deploy và test

**Bước 3: So sánh chi tiết**
- [ ] So sánh tài khoản deploy
- [ ] So sánh permissions granted
- [ ] So sánh deployment settings

---

## 📞 Nếu Tất Cả Đều Giống Nhau

Nếu tất cả settings giống nhau mà vẫn không hoạt động, có thể:

1. **Google Apps Script có thay đổi API** (sau khi V1 được deploy)
2. **Browser/Network cache issue** - Thử với incognito mode hoặc máy khác
3. **Regional restrictions** - Google có thể block POST từ một số regions
4. **Rate limiting** - Quá nhiều deploy attempts

➡️ **Giải pháp cuối cùng: Chuyển sang Service Account method**

