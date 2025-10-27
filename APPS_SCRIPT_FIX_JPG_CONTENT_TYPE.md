# Fix JPG Files Being Saved as PDF in Apps Script

## 🐛 Vấn đề

Files JPG khi upload đang bị thêm đuôi .pdf hoặc được lưu sai content type.

**Nguyên nhân:** Apps Script hardcode content_type thành "application/pdf"

## ✅ Giải pháp

### Tìm code này trong Apps Script (function `handleUploadFixed`):

Khoảng dòng 167-170:

```javascript
// Step 4: Create file
try {
  var binaryData = Utilities.base64Decode(fileContent);
  var blob = Utilities.newBlob(binaryData, "application/pdf", filename);  // ❌ Hardcoded!
  var uploadedFile = targetFolder.createFile(blob);
```

### Sửa thành:

```javascript
// Step 4: Create file
try {
  var binaryData = Utilities.base64Decode(fileContent);
  
  // ✅ Use content_type from request, fallback to application/pdf
  var contentType = requestData.content_type || "application/pdf";
  var blob = Utilities.newBlob(binaryData, contentType, filename);
  
  var uploadedFile = targetFolder.createFile(blob);
```

## 📝 Complete Fixed Section

```javascript
// Step 4: Create file
try {
  Logger.log("📄 Creating file in target folder...");
  Logger.log("   Filename: " + filename);
  Logger.log("   Content type: " + (requestData.content_type || "application/pdf"));
  
  var binaryData = Utilities.base64Decode(fileContent);
  
  // ✅ FIXED: Use content_type from request
  var contentType = requestData.content_type || "application/pdf";
  var blob = Utilities.newBlob(binaryData, contentType, filename);
  
  var uploadedFile = targetFolder.createFile(blob);
  
  Logger.log("✅ File created successfully!");
  Logger.log("🆔 File ID: " + uploadedFile.getId());
  Logger.log("📝 File name: " + uploadedFile.getName());
  Logger.log("📦 MIME type: " + uploadedFile.getMimeType());
  
  return createResponse(true, "File uploaded successfully", {
    file_id: uploadedFile.getId(),
    file_name: uploadedFile.getName(),
    file_url: uploadedFile.getUrl(),
    folder_path: folderPath,
    folder_id: targetFolder.getId(),
    upload_timestamp: new Date().toISOString()
  });
  
} catch (createError) {
  Logger.log("❌ File creation error: " + createError.toString());
  return createResponse(false, "File creation failed: " + createError.toString());
}
```

## 🔍 Verification

Sau khi update, Apps Script execution logs sẽ show:

**For PDF:**
```
📄 Creating file in target folder...
   Filename: document.pdf
   Content type: application/pdf
   MIME type: application/pdf
```

**For JPG:**
```
📄 Creating file in target folder...
   Filename: photo.jpg
   Content type: image/jpeg
   MIME type: image/jpeg
```

## 🧪 Testing

### Test với file JPG:
1. Upload folder có file JPG
2. Check Apps Script execution logs
3. Should see: `Content type: image/jpeg`
4. Check Google Drive
5. File nên có icon image, không phải PDF icon
6. Mở file trên Drive nên hiển thị ảnh, không phải PDF

### Test với file PDF:
1. Upload folder có file PDF
2. Should still work như cũ
3. Content type: `application/pdf`

## 📊 Backend Request Format

Backend đang gửi đúng:

```javascript
{
  "action": "upload_file_with_folder_creation",
  "parent_folder_id": "...",
  "ship_name": "BROTHER 36",
  "parent_category": "Class & Flag Cert/Other Documents",
  "category": "Radio Report",
  "filename": "photo.jpg",
  "file_content": "base64...",
  "content_type": "image/jpeg"  // ✅ Backend sends correct type
}
```

Apps Script chỉ cần dùng `content_type` này!

## 🚀 Deployment

1. **Update Apps Script**
   - Sửa dòng `Utilities.newBlob(...)` 
   - Add `var contentType = requestData.content_type || "application/pdf";`

2. **Test trong Apps Script**
   ```javascript
   function testJpgUpload() {
     var testData = {
       parent_folder_id: "YOUR_FOLDER_ID",
       ship_name: "BROTHER 36",
       parent_category: "Class & Flag Cert/Other Documents",
       category: "Test",
       filename: "test.jpg",
       file_content: Utilities.base64Encode("fake image data"),
       content_type: "image/jpeg"  // Test with JPG
     };
     
     var result = handleUploadFixed(testData);
     Logger.log(result);
   }
   ```

3. **Deploy new version**
   - Deploy → Manage deployments → Edit → New version
   - Description: "Fix JPG content type handling"

4. **Test from Ship Management System**
   - Upload folder with mixed PDF and JPG files
   - Verify all files have correct type

## ✅ Expected Results

**Before fix:**
```
Google Drive:
- document.pdf (PDF icon) ✅
- photo.jpg (PDF icon) ❌ Wrong!
```

**After fix:**
```
Google Drive:
- document.pdf (PDF icon) ✅
- photo.jpg (Image icon) ✅ Correct!
```

## 🎯 Summary

**Change location:** Apps Script `handleUploadFixed` function, Step 4

**Change:**
```javascript
// OLD
var blob = Utilities.newBlob(binaryData, "application/pdf", filename);

// NEW
var contentType = requestData.content_type || "application/pdf";
var blob = Utilities.newBlob(binaryData, contentType, filename);
```

**Impact:** Files will be saved with correct MIME type matching their extension.
