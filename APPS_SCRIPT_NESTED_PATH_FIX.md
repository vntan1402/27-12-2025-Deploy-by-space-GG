# Apps Script Update Required - Support Nested Parent Category

## Current Problem

Apps Script is creating a folder with name `"Class & Flag Cert/Other Documents"` instead of navigating through existing folders.

**What's happening:**
```
BROTHER 36
└── Class & Flag Cert/Other Documents  ❌ (One folder with "/" in name)
    └── Radio Report
```

**What we need:**
```
BROTHER 36
└── Class & Flag Cert (existing)
    └── Other Documents (existing)
        └── Radio Report ✅ (new subfolder)
```

## Root Cause

Your Apps Script's `handleUploadFileWithFolderCreation` function does NOT split `parent_category` by `/`.

Current logic (in your Apps Script):
```javascript
var parentCategoryFolder = findOrCreateFolder(shipFolder, parentCategory);
```

This treats `"Class & Flag Cert/Other Documents"` as ONE folder name, not a path.

## Required Apps Script Fix

### Update `handleUploadFileWithFolderCreation` function:

**FIND THIS CODE IN YOUR APPS SCRIPT:**
```javascript
function handleUploadFileWithFolderCreation(data) {
  // ... existing code ...
  
  var shipFolder = findOrCreateFolder(rootFolder, shipName);
  
  // ❌ OLD CODE (treats parent_category as single folder name):
  var parentCategoryFolder = findOrCreateFolder(shipFolder, parentCategory);
  
  var categoryFolder = findOrCreateFolder(parentCategoryFolder, category);
  
  // ... rest of code ...
}
```

**REPLACE WITH:**
```javascript
function handleUploadFileWithFolderCreation(data) {
  // ... existing code ...
  
  var shipFolder = findOrCreateFolder(rootFolder, shipName);
  
  // ✅ NEW CODE (handles nested path in parent_category):
  var parentCategoryFolder = shipFolder;
  if (parentCategory) {
    var parentCategoryPath = parentCategory.split('/');
    for (var i = 0; i < parentCategoryPath.length; i++) {
      var folderName = parentCategoryPath[i].trim();
      if (folderName) {
        parentCategoryFolder = findOrCreateFolder(parentCategoryFolder, folderName);
      }
    }
  }
  
  var categoryFolder = findOrCreateFolder(parentCategoryFolder, category);
  
  // ... rest of code ...
}
```

## Complete Updated Function Example

```javascript
function handleUploadFileWithFolderCreation(data) {
  try {
    var parentFolderId = data.parent_folder_id;
    var shipName = data.ship_name;
    var parentCategory = data.parent_category;  // Can be "Class & Flag Cert/Other Documents"
    var category = data.category;  // "Radio Report"
    var filename = data.filename;
    var fileContent = data.file_content;
    var contentType = data.content_type;
    
    // Get root folder
    var rootFolder = DriveApp.getFolderById(parentFolderId);
    
    // Find or create ship folder
    var shipFolder = findOrCreateFolder(rootFolder, shipName);
    
    // ✅ HANDLE NESTED PARENT CATEGORY PATH
    var parentCategoryFolder = shipFolder;
    if (parentCategory) {
      // Split by "/" to handle nested paths like "Class & Flag Cert/Other Documents"
      var parentCategoryPath = parentCategory.split('/');
      for (var i = 0; i < parentCategoryPath.length; i++) {
        var folderName = parentCategoryPath[i].trim();
        if (folderName) {
          parentCategoryFolder = findOrCreateFolder(parentCategoryFolder, folderName);
        }
      }
    }
    
    // Find or create category folder (e.g., "Radio Report")
    var categoryFolder = findOrCreateFolder(parentCategoryFolder, category);
    
    // Decode and upload file
    var decodedContent = Utilities.base64Decode(fileContent);
    var blob = Utilities.newBlob(decodedContent, contentType, filename);
    var file = categoryFolder.createFile(blob);
    
    return {
      success: true,
      file_id: file.getId(),
      folder_id: categoryFolder.getId(),  // Return folder ID of category folder
      folder_path: parentCategory + '/' + category,
      message: "File uploaded successfully"
    };
    
  } catch (error) {
    return {
      success: false,
      message: "Upload failed: " + error.toString(),
      error: error.toString()
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

## Testing the Fix

### Before deploying to production, test in Apps Script:

**Test Case 1: Nested path**
```javascript
function testNestedPath() {
  var testData = {
    parent_folder_id: "YOUR_ROOT_FOLDER_ID",
    ship_name: "BROTHER 36",
    parent_category: "Class & Flag Cert/Other Documents",
    category: "Radio Report",
    filename: "test.txt",
    file_content: Utilities.base64Encode("Hello World"),
    content_type: "text/plain"
  };
  
  var result = handleUploadFileWithFolderCreation(testData);
  Logger.log(result);
  
  // Expected result:
  // - Folder structure: BROTHER 36 / Class & Flag Cert / Other Documents / Radio Report / test.txt
  // - result.success = true
  // - result.folder_id = ID of "Radio Report" folder
}
```

**Test Case 2: Single level (backward compatibility)**
```javascript
function testSingleLevel() {
  var testData = {
    parent_folder_id: "YOUR_ROOT_FOLDER_ID",
    ship_name: "BROTHER 36",
    parent_category: "Class & Flag Cert",
    category: "Test Report",
    filename: "test.pdf",
    file_content: Utilities.base64Encode("Test"),
    content_type: "application/pdf"
  };
  
  var result = handleUploadFileWithFolderCreation(testData);
  Logger.log(result);
  
  // Expected result:
  // - Folder structure: BROTHER 36 / Class & Flag Cert / Test Report / test.pdf
  // - result.success = true
}
```

## Deployment Steps

1. **Open your Apps Script project**
   - URL: `https://script.google.com`
   - Open your existing Company Apps Script

2. **Update the code**
   - Find `handleUploadFileWithFolderCreation` function
   - Replace the parent category handling code as shown above

3. **Test in Apps Script**
   - Run `testNestedPath()` function
   - Check execution logs
   - Verify folder structure in Google Drive

4. **Deploy new version**
   - Click "Deploy" → "New deployment"
   - OR "Deploy" → "Manage deployments" → "Edit" → "Version: New version"
   - Description: "Support nested parent_category path"
   - Click "Deploy"

5. **Update URL in backend (if changed)**
   - If deployment URL changed, update in Ship Management System settings

6. **Test from Ship Management System**
   - Upload a folder in "Other Documents"
   - Verify folder structure is correct

## Benefits of This Fix

✅ **Supports nested paths** - `"Class & Flag Cert/Other Documents"` works correctly
✅ **Backward compatible** - Single-level paths still work: `"Class & Flag Cert"`
✅ **No breaking changes** - Existing uploads continue to work
✅ **Reusable** - Works for any nested folder structure
✅ **Returns folder_id** - Backend can store folder link

## Alternative: Quick Backend Workaround (Not Recommended)

If you cannot update Apps Script immediately, backend can use a workaround:

**Upload in 2 steps:**
1. Upload 1 dummy file to "Other Documents" to ensure folder exists
2. Upload files to "Radio Report" subfolder

But this is NOT recommended because:
- Slower (extra API call)
- Leaves dummy files
- Doesn't solve root cause

## Verification

After updating Apps Script, verify with backend logs:

```
✅ Should see:
INFO:server:   Folder ID: 1abc123xyz
INFO:server:   Folder Link: https://drive.google.com/drive/folders/1abc123xyz

❌ Should NOT see:
- Folders with "/" in name
- Nested folders in wrong location
```

## Support

If you need help updating Apps Script:
1. Share your current Apps Script code
2. I can provide exact line-by-line changes
3. Or I can provide the complete updated function

**Ready to update Apps Script?** Let me know if you need any clarification!
