# 🐛 Debugging Guide - "Not Authenticated" Error với Apps Script API Key

## ❌ Lỗi: "Apps Script test error: Not authenticated"

### 🔍 Nguyên nhân có thể xảy ra:

1. **API Key không được gửi từ frontend**
2. **API Key sai hoặc không khớp**
3. **Apps Script chưa được deploy lại sau khi update code**
4. **Payload structure không đúng**
5. **API Key bị lost trong quá trình gửi request**

---

## 🧪 Step-by-Step Debugging

### Step 1: Kiểm tra Apps Script Code

**✅ Đảm bảo API_KEY được set đúng:**

Mở Apps Script và kiểm tra dòng 10:
```javascript
const API_KEY = 'Vntan1402sms'; // ✅ Must match exactly
```

**✅ Đảm bảo validateApiKey được gọi đúng:**

Tìm function `doPost()` (dòng 145):
```javascript
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    
    // ⚠️ Check this line exists
    validateApiKey(payload);
    
    // ... rest of code
  }
}
```

**✅ Deploy lại Apps Script:**
1. Click **Deploy** > **Manage deployments**
2. Click ⚙️ icon > **New Version**
3. Add description: "Added API key validation v2.1"
4. Click **Deploy**

⚠️ **QUAN TRỌNG**: Web App URL không đổi, nhưng phải deploy version mới thì code mới có hiệu lực!

---

### Step 2: Test Apps Script Trực Tiếp (Bypass Backend)

**Test 1: Test với curl (No API Key)**

```bash
curl -X POST "YOUR_WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "test_connection"
  }'
```

**Expected Response:**
```json
{
  "success": false,
  "message": "Authentication failed: Invalid or missing API key.",
  "error": "Error: Invalid or missing API key."
}
```

---

**Test 2: Test với curl (Wrong API Key)**

```bash
curl -X POST "YOUR_WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "test_connection",
    "api_key": "wrong_key_123"
  }'
```

**Expected Response:**
```json
{
  "success": false,
  "message": "Authentication failed: Invalid or missing API key.",
  "error": "Error: Invalid or missing API key."
}
```

---

**Test 3: Test với curl (Correct API Key)**

```bash
curl -X POST "YOUR_WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "test_connection",
    "api_key": "Vntan1402sms"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Connection successful",
  "data": {
    "status": "Connected",
    "folder_name": "Ship Management System Backups",
    "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
  }
}
```

✅ **Nếu Test 3 thành công** → Apps Script hoạt động đúng, vấn đề ở frontend/backend

❌ **Nếu Test 3 thất bại** → Apps Script chưa được deploy đúng hoặc API_KEY sai

---

### Step 3: Kiểm tra Backend Request

**Check backend logs khi test connection:**

```bash
tail -f /var/log/supervisor/backend.*.log | grep -i "gdrive\|apps script"
```

**Tìm dòng log request payload:**
```
INFO: Request to Apps Script: {"action": "test_connection", "folder_id": "...", "api_key": "Vntan1402sms"}
```

✅ **Nếu thấy api_key trong log** → Backend gửi đúng

❌ **Nếu KHÔNG thấy api_key** → Frontend không gửi hoặc backend không nhận

---

### Step 4: Kiểm tra Frontend

**Mở DevTools Console (F12) > Network Tab:**

1. Mở System Settings > Google Drive Configuration
2. Nhập:
   - Web App URL: `https://script.google.com/macros/s/.../exec`
   - Folder ID: `1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB`
   - API Key: `Vntan1402sms` ✅ **Nhập chính xác**
3. Click "Test Connection"
4. Trong Network tab, tìm request `configure-proxy`
5. Click vào request đó > **Payload tab**

**Check Request Payload:**
```json
{
  "web_app_url": "https://script.google.com/macros/s/.../exec",
  "folder_id": "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB",
  "api_key": "Vntan1402sms"  // ✅ Must be present
}
```

✅ **Nếu có api_key** → Frontend gửi đúng

❌ **Nếu KHÔNG có api_key** → Frontend input field không hoạt động

---

### Step 5: Debug Frontend Code

**Check SystemGoogleDriveModal.jsx:**

Mở file và tìm function `handleSave()` (dòng ~107):

```javascript
if (authMethod === 'apps_script') {
  // ... validation code ...
  
  payload = {
    web_app_url: config.web_app_url,
    folder_id: config.folder_id
  };
  
  // ✅ MUST HAVE THIS
  if (config.api_key) {
    payload.api_key = config.api_key;
  }
}
```

**Check config state initialization (dòng ~10):**
```javascript
const [config, setConfig] = useState({
  auth_method: 'apps_script',
  web_app_url: '',
  api_key: '',  // ✅ MUST HAVE THIS
  // ... other fields
});
```

---

### Step 6: Test từng bước (Manual)

**Test A: Console log trong frontend**

Thêm console.log vào `handleSave()`:
```javascript
const handleSave = async () => {
  console.log('💡 Config state:', config);
  console.log('💡 API Key:', config.api_key);
  console.log('💡 Payload:', payload);
  // ... rest of code
}
```

**Test B: Network inspection**

Dùng Chrome DevTools:
1. Network tab > Filter: `configure-proxy`
2. Click request > Payload tab
3. Verify `api_key` field exists và có giá trị `Vntan1402sms`

---

## 🔧 Fix Solutions

### Fix 1: Apps Script chưa deploy version mới

**Problem:** Code đã update nhưng vẫn chạy version cũ

**Solution:**
1. Trong Apps Script Editor, click **Deploy** > **Manage deployments**
2. Click ⚙️ icon bên cạnh deployment
3. Click **New version**
4. Add description: "API key validation v2.1"
5. Click **Deploy**

---

### Fix 2: API Key field không xuất hiện trong UI

**Problem:** Frontend không có input field cho API key

**Solution:**

Kiểm tra file `/app/frontend/src/components/SystemSettings/SystemGoogleDrive/SystemGoogleDriveModal.jsx`

Tìm dòng sau Folder ID input (dòng ~300):

```jsx
<div>
  <label className="block text-sm font-medium text-gray-700 mb-2">
    🔐 API Key (Optional - Recommended for Security)
  </label>
  <input
    type="password"
    value={config.api_key}
    onChange={(e) => setConfig(prev => ({ ...prev, api_key: e.target.value }))}
    placeholder="Enter API Key from Apps Script (e.g., Vntan1402sms)"
    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
  />
</div>
```

Nếu không có → Frontend chưa update → Restart frontend:
```bash
sudo supervisorctl restart frontend
```

---

### Fix 3: Backend không gửi API key

**Problem:** Backend nhận được api_key từ frontend nhưng không forward tới Apps Script

**Solution:**

Check file `/app/backend/server.py` dòng ~13665:

```python
# Test the Apps Script URL first
test_payload = {
    "action": "test_connection",
    "folder_id": folder_id
}

# ✅ MUST HAVE THIS
if api_key:
    test_payload["api_key"] = api_key

response = requests.post(web_app_url, json=test_payload, timeout=30)
```

Nếu thiếu → Update code và restart backend:
```bash
sudo supervisorctl restart backend
```

---

### Fix 4: API Key bị trim hoặc có whitespace

**Problem:** User nhập API key có space phía trước/sau

**Solution:**

Update frontend input onChange:
```javascript
onChange={(e) => setConfig(prev => ({ 
  ...prev, 
  api_key: e.target.value.trim()  // ✅ Add .trim()
}))}
```

---

## 📋 Quick Checklist

- [ ] Apps Script có `const API_KEY = 'Vntan1402sms'`
- [ ] Apps Script đã deploy version mới (sau khi update code)
- [ ] Frontend có API Key input field (password type)
- [ ] Frontend config state có `api_key: ''` field
- [ ] Frontend handleSave() include api_key trong payload
- [ ] Backend configure-proxy endpoint check và forward api_key
- [ ] Backend sync-to-drive endpoint include api_key
- [ ] Backend auto_backup function include api_key
- [ ] Test với curl trực tiếp thành công

---

## 🎯 Test Script Tự Động

Tạo file `test_api_key.sh`:

```bash
#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

WEB_APP_URL="YOUR_WEB_APP_URL_HERE"
API_KEY="Vntan1402sms"

echo "=========================================="
echo "🧪 Testing Apps Script API Key"
echo "=========================================="

# Test 1: No API Key (Should fail)
echo ""
echo "Test 1: No API Key (Should fail)"
RESPONSE=$(curl -s -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{"action": "test_connection"}')

if echo "$RESPONSE" | grep -q '"success":false'; then
  echo -e "${GREEN}✅ PASS - Correctly rejected${NC}"
else
  echo -e "${RED}❌ FAIL - Should have been rejected${NC}"
fi

# Test 2: Wrong API Key (Should fail)
echo ""
echo "Test 2: Wrong API Key (Should fail)"
RESPONSE=$(curl -s -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{"action": "test_connection", "api_key": "wrong_key"}')

if echo "$RESPONSE" | grep -q '"success":false'; then
  echo -e "${GREEN}✅ PASS - Correctly rejected wrong key${NC}"
else
  echo -e "${RED}❌ FAIL - Should have been rejected${NC}"
fi

# Test 3: Correct API Key (Should succeed)
echo ""
echo "Test 3: Correct API Key (Should succeed)"
RESPONSE=$(curl -s -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d "{\"action\": \"test_connection\", \"api_key\": \"$API_KEY\"}")

if echo "$RESPONSE" | grep -q '"success":true'; then
  echo -e "${GREEN}✅ PASS - Connection successful${NC}"
  echo "$RESPONSE" | jq '.'
else
  echo -e "${RED}❌ FAIL - Should have succeeded${NC}"
  echo "$RESPONSE"
fi

echo ""
echo "=========================================="
echo "Tests completed!"
echo "=========================================="
```

**Chạy:**
```bash
chmod +x test_api_key.sh
./test_api_key.sh
```

---

## 💡 Common Mistakes

1. **Nhập sai API Key** - Check typo: `Vntan1402sms` (phân biệt hoa thường)
2. **Quên deploy Apps Script version mới** - Code update nhưng không deploy
3. **Frontend cache** - Ctrl+F5 để hard refresh
4. **Backend không restart** - Sau khi update code phải restart
5. **API Key có space** - Trim whitespace khi nhập

---

## ✅ Success Indicators

Khi hoạt động đúng, bạn sẽ thấy:

**Frontend:**
- Toast: "✅ Connection successful! Folder: Ship Management System Backups"

**Backend Log:**
```
INFO: Google Drive configuration successful
INFO: API key enabled: True
```

**Apps Script Log:**
```
[2025-01-29 21:00:00] ✅ API Key validated, processing action: test_connection
[2025-01-29 21:00:00] ✓ Connection successful | {"status":"Connected",...}
```

---

**Nếu sau tất cả steps trên vẫn lỗi, vui lòng cung cấp:**
1. Screenshot của Apps Script code (dòng 10: API_KEY)
2. Screenshot của Frontend API Key input field
3. Backend log khi test connection
4. Curl test result (Test 3)
