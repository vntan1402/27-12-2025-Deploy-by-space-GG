# Other Documents Folder Upload - Simplified Implementation

## ✅ Giải pháp tốt hơn: Dùng `upload_file_with_folder_creation` đã có sẵn!

Thay vì tạo 2 actions mới (`create_subfolder` và `upload_to_folder`), chúng ta **tận dụng action đã có sẵn** với **nested category path**.

## Cách hoạt động

### Backend gửi request với nested path:

```javascript
{
  "action": "upload_file_with_folder_creation",  // ✅ Action đã có sẵn
  "parent_folder_id": "ROOT_FOLDER_ID",
  "ship_name": "BROTHER 36",
  "parent_category": "Class & Flag Cert",
  "category": "Other Documents/Radio Report",  // ✅ Nested path!
  "filename": "file.pdf",
  "file_content": "base64...",
  "content_type": "application/pdf"
}
```

### Apps Script tạo folder structure:

```
ROOT
└── BROTHER 36
    └── Class & Flag Cert
        └── Other Documents
            └── Radio Report  ← Subfolder được tạo tự động!
                ├── file1.pdf
                ├── file2.pdf
                └── file3.pdf
```

## Yêu cầu Apps Script

### Apps Script cần hỗ trợ nested path trong `category`

**Nếu Apps Script chưa hỗ trợ**, cần sửa đổi nhỏ trong function `findOrCreateFolder`:

```javascript
function handleUploadFileWithFolderCreation(data) {
  try {
    var parentFolderId = data.parent_folder_id;
    var shipName = data.ship_name;
    var parentCategory = data.parent_category;
    var category = data.category;  // Có thể là "Other Documents/Radio Report"
    var filename = data.filename;
    var fileContent = data.file_content;
    var contentType = data.content_type;
    
    // Navigate to root folder
    var rootFolder = DriveApp.getFolderById(parentFolderId);
    
    // Find or create ship folder
    var shipFolder = findOrCreateFolder(rootFolder, shipName);
    
    // Find or create parent category folder
    var parentCategoryFolder = findOrCreateFolder(shipFolder, parentCategory);
    
    // ✅ HANDLE NESTED PATH: Split category by "/" and create nested folders
    var categoryPath = category.split('/');
    var currentFolder = parentCategoryFolder;
    
    for (var i = 0; i < categoryPath.length; i++) {
      currentFolder = findOrCreateFolder(currentFolder, categoryPath[i]);
    }
    
    // Upload file to final folder
    var decodedContent = Utilities.base64Decode(fileContent);
    var blob = Utilities.newBlob(decodedContent, contentType, filename);
    var file = currentFolder.createFile(blob);
    
    return {
      success: true,
      file_id: file.getId(),
      folder_id: currentFolder.getId(),  // ✅ Return folder ID
      folder_path: category,
      message: "File uploaded successfully"
    };
    
  } catch (error) {
    return {
      success: false,
      message: "Upload failed: " + error.toString()
    };
  }
}

function findOrCreateFolder(parentFolder, folderName) {
  var folders = parentFolder.getFoldersByName(folderName);
  if (folders.hasNext()) {
    return folders.next();
  } else {
    return parentFolder.createFolder(folderName);
  }
}
```

## Benefits của approach này

✅ **Không cần thêm actions mới** - Tận dụng code đã có
✅ **Đơn giản hơn** - Chỉ cần modify logic handle nested path
✅ **Backward compatible** - Không ảnh hưởng existing uploads
✅ **Flexible** - Có thể tạo nhiều levels: `A/B/C/D`

## Testing

### Test với curl:

```bash
curl -X POST "YOUR_APPS_SCRIPT_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "upload_file_with_folder_creation",
    "parent_folder_id": "YOUR_ROOT_FOLDER_ID",
    "ship_name": "BROTHER 36",
    "parent_category": "Class & Flag Cert",
    "category": "Other Documents/Radio Report",
    "filename": "test.pdf",
    "file_content": "BASE64_ENCODED_CONTENT",
    "content_type": "application/pdf"
  }'
```

### Expected Response:

```json
{
  "success": true,
  "file_id": "1xxxxxxxxxxxxx",
  "folder_id": "1yyyyyyyyyyyyyy",
  "folder_path": "Other Documents/Radio Report",
  "message": "File uploaded successfully"
}
```

## Implementation Status

✅ **Backend**: Đã implement, đang dùng nested path
✅ **Frontend**: Đã implement, hiển thị 📁 icon
✅ **Database**: Đã có folder_id và folder_link fields
⚠️ **Apps Script**: Cần kiểm tra xem đã support nested path chưa

## Nếu Apps Script đã support nested path

**BẠN KHÔNG CẦN LÀM GÌ CẢ!** 🎉

Tính năng sẽ hoạt động ngay lập tức:
1. User upload folder "Radio Report" với 8 files
2. Backend gọi `upload_file_with_folder_creation` 8 lần với `category="Other Documents/Radio Report"`
3. Apps Script tạo subfolder và upload files
4. Database lưu folder_id
5. UI hiển thị 📁 icon

## Nếu Apps Script chưa support nested path

**CHỈ CẦN SỬA 1 CHỖ:**

Trong function `handleUploadFileWithFolderCreation`, thay:

```javascript
// OLD: Tạo folder trực tiếp
var categoryFolder = findOrCreateFolder(parentCategoryFolder, category);
```

Thành:

```javascript
// NEW: Handle nested path
var categoryPath = category.split('/');
var currentFolder = parentCategoryFolder;
for (var i = 0; i < categoryPath.length; i++) {
  currentFolder = findOrCreateFolder(currentFolder, categoryPath[i]);
}
```

## How to check if Apps Script supports nested path?

**Option 1**: Test ngay trên UI
- Upload 1 folder với vài files
- Check backend logs xem có error không
- Check Google Drive xem folder có được tạo đúng không

**Option 2**: Test với curl (như trên)

**Option 3**: Check Apps Script execution logs
- Mở Apps Script editor
- Run function với test data
- Check execution logs

## Troubleshooting

### Lỗi: Folder không được tạo

**Nguyên nhân**: Apps Script chưa hỗ trợ nested path, coi `"Other Documents/Radio Report"` là 1 folder name có dấu `/`

**Giải pháp**: Sửa Apps Script như hướng dẫn trên

### Lỗi: Files upload nhưng folder_id null

**Nguyên nhân**: Apps Script không return `folder_id` trong response

**Giải pháp**: Add `folder_id: currentFolder.getId()` vào Apps Script response

### Lỗi: 📁 icon không hiện

**Nguyên nhân**: 
- `folder_id` hoặc `folder_link` null trong database
- Apps Script không return folder_id

**Giải pháp**: 
1. Check database record xem có folder_id không
2. Check Apps Script response xem có return folder_id không
3. Nếu thiếu, có thể get folder_id từ file's parent folder

## Comparison: Old vs New Approach

### ❌ Old Approach (Phức tạp)
- Action 1: `create_subfolder` → Get folder_id
- Action 2: `upload_to_folder` với folder_id (x N files)
- Requires 2 new actions in Apps Script
- More API calls

### ✅ New Approach (Đơn giản)
- Action: `upload_file_with_folder_creation` với nested category (x N files)
- Reuse existing action
- Apps Script auto-creates nested folders
- Simpler implementation

## Conclusion

**Cách này thông minh hơn và đơn giản hơn nhiều!** 

Cảm ơn đã point out! 🙏

Bây giờ chỉ cần:
1. Test xem Apps Script đã support nested path chưa
2. Nếu chưa → Sửa 1 chỗ trong Apps Script (như hướng dẫn trên)
3. Done! ✅
