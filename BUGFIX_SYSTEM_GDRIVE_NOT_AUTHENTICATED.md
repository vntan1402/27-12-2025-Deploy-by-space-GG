# 🐛 BUG FIX: System Google Drive "Not authenticated" Error

## 🔍 Root Cause Discovered

**Vấn đề**: System Google Drive báo lỗi "Not authenticated" khi test connection, trong khi Company Google Drive hoạt động bình thường với cùng Apps Script URL.

**Nguyên nhân**: Frontend code của `SystemGoogleDriveModal.jsx` sử dụng `axios` trực tiếp thay vì `api` instance có authentication interceptor.

---

## 🔧 Files Changed

### 1. `/app/frontend/src/components/SystemSettings/SystemGoogleDrive/SystemGoogleDriveModal.jsx`

**Before (❌ Bug):**
```javascript
import axios from 'axios';
const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Direct axios calls without auth token
const response = await axios.post(`${API}/gdrive/configure-proxy`, payload);
```

**After (✅ Fixed):**
```javascript
import api from '../../../services/api';
import { gdriveService } from '../../../services';

// Using gdriveService with auth token
const response = await gdriveService.configureProxy(config.web_app_url, config.folder_id);
```

---

## 🎯 Changes Made

### 1. Import Statements
- ❌ Removed: `import axios from 'axios'`
- ✅ Added: `import api from '../../../services/api'`
- ✅ Already had: `import { gdriveService } from '../../../services'`

### 2. handleAppsScriptTest()
- Changed from `axios.post()` to `gdriveService.configureProxy()`
- Now includes JWT token automatically via api interceptor

### 3. handleOAuthAuthorize()
- Changed from `axios.post()` to `gdriveService.authorizeOAuth()`

### 4. handleSave()
- Changed from `axios.post()` to appropriate service methods
- Apps Script: `gdriveService.configureProxy()`
- Service Account: `gdriveService.configure()`

### 5. handleTestServiceAccount()
- Changed from `axios.post()` to `gdriveService.test()`

---

## ✅ Expected Result

**Before Fix:**
```
Test Connection → axios.post (no auth) → Backend rejects → "Not authenticated" ❌
```

**After Fix:**
```
Test Connection → gdriveService (with auth) → Backend accepts → Test successful ✅
```

---

## 🧪 Testing Steps

1. **Clear browser cache** (Ctrl+Shift+R or Cmd+Shift+R)
2. **Login** với `admin` / `admin123`
3. **Navigate** to Settings → System Google Drive
4. **Fill in**:
   - Web App URL: `https://script.google.com/macros/s/AKfycbz_C_dcFIlChfG6daFjABBlDjaKmHkdiTgHnhHzAR-HmDWDoHuYX1Bqz0v8KzndL4i-/exec`
   - Folder ID: `1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB`
5. **Click "Test Connection"**
6. **Expected**: ✅ "Apps Script proxy working!" toast message

---

## 🔄 Deployment Status

- ✅ Frontend code fixed
- ✅ Frontend restarted (pid 22317)
- ✅ Backend already correct (no changes needed)
- ⏳ Ready for testing

---

## 📊 Why Company Google Drive Worked

**Company Google Drive modal** may have been using the correct service methods or had proper auth setup, which is why it worked while System Google Drive didn't.

**Key Difference:**
- Company: Properly authenticated requests
- System (before fix): Direct axios calls without auth
- System (after fix): Using gdriveService with auth ✅

---

## 🎉 Bug Fixed!

The "Not authenticated" error should now be resolved. 

**Next step**: Please test in the app and confirm it works!
