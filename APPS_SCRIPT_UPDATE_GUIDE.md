# Apps Script Fix - Complete Guide

## 🎯 Vấn đề

Apps Script đang tạo folder với tên `"Class & Flag Cert/Other Documents"` thay vì navigate qua folders.

**Nguyên nhân:** Dòng code này không split `parent_category`:
```javascript
targetFolder = createFolderPathSafe(shipFolder, [parentCategory, category]);
```

## ✅ Giải pháp

Split `parent_category` theo dấu `/` trước khi truyền vào array.

## 📝 Hướng dẫn Update

### Bước 1: Mở Apps Script

1. Vào https://script.google.com
2. Mở project Apps Script của bạn
3. Tìm function `handleUploadFixed`

### Bước 2: Tìm Code Cần Sửa

Tìm section "Step 3" (khoảng dòng 125-165):

```javascript
// Step 3: Determine target folder based on category structure
var targetFolder;
var folderPath;

if (parentCategory && category) {
  // Nested structure: Ship/ParentCategory/Category
  Logger.log("📁 Creating nested structure: " + shipName + "/" + parentCategory + "/" + category);
  targetFolder = createFolderPathSafe(shipFolder, [parentCategory, category]);  // ❌ Dòng này sai
  folderPath = shipName + "/" + parentCategory + "/" + category;
}
```

### Bước 3: Thay Thế Code

**XÓA** toàn bộ section từ `// Step 3:` đến hết phần `else` (khoảng 40 dòng)

**THAY BẰNG** code này:

```javascript
// Step 3: Determine target folder based on category structure
var targetFolder;
var folderPath;

if (parentCategory && category) {
  // ✅ FIXED: Split parent_category by "/" to handle nested paths
  // Example: "Class & Flag Cert/Other Documents" → ["Class & Flag Cert", "Other Documents"]
  var parentCategoryParts = parentCategory.split('/').map(function(part) {
    return part.trim();
  }).filter(function(part) {
    return part.length > 0;
  });
  
  Logger.log("📁 Creating nested structure: " + shipName + "/" + parentCategory + "/" + category);
  Logger.log("   Parent parts: " + JSON.stringify(parentCategoryParts));
  
  // Combine parent parts with category
  var allParts = parentCategoryParts.concat([category]);
  Logger.log("   All folder parts: " + JSON.stringify(allParts));
  
  targetFolder = createFolderPathSafe(shipFolder, allParts);
  folderPath = shipName + "/" + parentCategory + "/" + category;
  
} else if (category) {
  // Single level: Ship/Category
  // IMPORTANT: Crew Records should upload directly to Ship/Crew Records
  if (category === "Crew Records") {
    Logger.log("📁 Creating Crew Records: " + shipName + "/Crew Records");
    targetFolder = createFolderPathSafe(shipFolder, [category]);
    folderPath = shipName + "/Crew Records";
  } else if (category && !parentCategory) {
    // For other categories, try to find "Class & Flag Cert" parent category first
    var classFlagFolder = findFolderByNameSafe(shipFolder, "Class & Flag Cert");
    if (classFlagFolder) {
      Logger.log("📁 Using Class & Flag Cert structure: " + shipName + "/Class & Flag Cert/" + category);
      targetFolder = findOrCreateFolderSafe(classFlagFolder, category);
      folderPath = shipName + "/Class & Flag Cert/" + category;
    } else {
      Logger.log("📁 Creating single level: " + shipName + "/" + category);
      targetFolder = createFolderPathSafe(shipFolder, [category]);
      folderPath = shipName + "/" + category;
    }
  } else {
    Logger.log("📁 Creating single level: " + shipName + "/" + category);
    targetFolder = createFolderPathSafe(shipFolder, [category]);
    folderPath = shipName + "/" + category;
  }
} else {
  // Direct to ship folder
  Logger.log("📁 Using ship folder directly: " + shipName);
  targetFolder = shipFolder;
  folderPath = shipName;
}
```

### Bước 4: Verify Code Mới

**Key change:** Dòng này
```javascript
// ❌ OLD
targetFolder = createFolderPathSafe(shipFolder, [parentCategory, category]);

// ✅ NEW
var parentCategoryParts = parentCategory.split('/').map(...).filter(...);
var allParts = parentCategoryParts.concat([category]);
targetFolder = createFolderPathSafe(shipFolder, allParts);
```

**Ví dụ:**
- Input: `parent_category: "Class & Flag Cert/Other Documents"`, `category: "Radio Report"`
- OLD: `["Class & Flag Cert/Other Documents", "Radio Report"]` → Tạo folder tên có dấu `/`
- NEW: `["Class & Flag Cert", "Other Documents", "Radio Report"]` → Tạo 3 folders nested ✅

### Bước 5: Test trong Apps Script

Trước khi deploy, test code:

```javascript
function testNestedPath() {
  // Replace with your actual folder ID
  var testData = {
    parent_folder_id: "YOUR_ROOT_FOLDER_ID",
    ship_name: "BROTHER 36",
    parent_category: "Class & Flag Cert/Other Documents",
    category: "Radio Report",
    filename: "test.txt",
    file_content: Utilities.base64Encode("Hello World"),
    content_type: "text/plain"
  };
  
  var result = handleUploadFixed(testData);
  Logger.log(JSON.stringify(result, null, 2));
  
  // Check execution logs:
  // Should see: Parent parts: ["Class & Flag Cert", "Other Documents"]
  // Should see: All folder parts: ["Class & Flag Cert", "Other Documents", "Radio Report"]
}
```

**Run function:**
1. Click "Select function" → Choose `testNestedPath`
2. Click "Run"
3. Check "Execution log" tab
4. Verify logs show correct split
5. Check Google Drive folder structure

### Bước 6: Deploy

1. Click "Deploy" → "Manage deployments"
2. Click ✏️ Edit icon next to current deployment
3. Version: "New version"
4. Description: "Fix nested parent_category path handling"
5. Click "Deploy"
6. Copy Web app URL (if changed)

### Bước 7: Update Backend (if needed)

Nếu Apps Script URL thay đổi:
1. Login vào Ship Management System
2. Go to Settings → Company Google Drive
3. Update Apps Script URL
4. Save

### Bước 8: Test từ Ship Management System

1. Chọn ship "BROTHER 36"
2. Go to "Class & Flag Cert" → "Other Documents List"
3. Click "Add Document" → "Upload Folder"
4. Chọn folder "Radio Report"
5. Upload

**Kiểm tra:**
- ✅ Backend logs: No errors
- ✅ Google Drive structure:
  ```
  BROTHER 36
  └── Class & Flag Cert (existing)
      └── Other Documents (existing)
          └── Radio Report (new)
              └── files...
  ```
- ✅ Database: có `folder_id` và `folder_link`
- ✅ UI: hiển thị 📁 icon
- ✅ Click 📁: mở đúng folder

## 🔍 Troubleshooting

### Vẫn tạo folder sai tên

**Check:**
1. Code đã được update đúng chưa?
2. Apps Script đã deploy version mới chưa?
3. Backend có gọi đúng Apps Script URL mới không?

**Debug:**
- Check Apps Script execution logs
- Tìm dòng "Parent parts:"
- Should see: `["Class & Flag Cert", "Other Documents"]`
- NOT: `["Class & Flag Cert/Other Documents"]`

### Folder không được tạo

**Check:**
- Apps Script có quyền truy cập Google Drive?
- Root folder ID có đúng không?
- Ship folder đã tồn tại chưa?

### Backend vẫn báo lỗi 500

**Check:**
- Apps Script response có return `folder_id` không?
- Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
- Look for "Folder ID from Apps Script:"

## ✅ Expected Behavior

### Before Fix
```
BROTHER 36
└── Class & Flag Cert/Other Documents  ❌ (one folder with "/" in name)
    └── Radio Report
```

### After Fix
```
BROTHER 36
└── Class & Flag Cert
    └── Other Documents
        └── Radio Report  ✅
            ├── file1.pdf
            ├── file2.pdf
            └── file3.pdf
```

## 📊 What Changed

**Code logic:**
```javascript
// Before
[parentCategory, category]
// "Class & Flag Cert/Other Documents" is treated as ONE string

// After  
parentCategory.split('/')  // Split into parts
  .map(trim)               // Remove whitespace
  .filter(not empty)       // Remove empty strings
  .concat([category])      // Add category at end
// Result: ["Class & Flag Cert", "Other Documents", "Radio Report"]
```

**Example flow:**
1. Backend sends: `parent_category: "Class & Flag Cert/Other Documents"`, `category: "Radio Report"`
2. Apps Script splits: `["Class & Flag Cert", "Other Documents"]`
3. Apps Script adds category: `["Class & Flag Cert", "Other Documents", "Radio Report"]`
4. `createFolderPathSafe` creates:
   - "Class & Flag Cert" in ship folder
   - "Other Documents" in "Class & Flag Cert"
   - "Radio Report" in "Other Documents"
5. Returns `folder_id` of "Radio Report"

## 🎉 Success Criteria

After fix, you should see:
- ✅ Correct folder structure in Google Drive
- ✅ `folder_id` returned in Apps Script response
- ✅ Database has `folder_id` and `folder_link`
- ✅ 📁 icon appears in UI
- ✅ Clicking 📁 opens correct folder on Google Drive
- ✅ All files uploaded to correct location

## 📞 Need Help?

If you encounter issues:
1. Share Apps Script execution logs
2. Share backend error logs
3. Share screenshot of Google Drive folder structure
4. I can help debug further!
