function doPost(e) {
  return handleRequest(e);
}

function doGet(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  try {
    var requestData = {};
    
    if (e && e.postData && e.postData.contents) {
      requestData = JSON.parse(e.postData.contents);
    } else if (e && e.parameter) {
      requestData = e.parameter;
    }
    
    var action = requestData.action || "passport_upload";
    
    Logger.log("🔄 Request action: " + action);
    
    switch (action) {
      case "passport_upload":
        return handlePassportUpload(requestData);
      case "upload_file_with_folder_creation":
        return handleUploadFixed(requestData);
      case "test_connection":
        return handleTestConnection(requestData);
      case "debug_folder_structure":
        return debugFolderStructure(requestData);
      default:
        return handleUploadFixed(requestData);
    }
    
  } catch (error) {
    Logger.log("❌ Request handling error: " + error.toString());
    return createResponse(false, "Error: " + error.toString());
  }
}

/**
 * FIXED version of handleUpload with enhanced debugging and folder lookup
 */
function handleUploadFixed(requestData) {
  try {
    Logger.log("🔄 FIXED: Starting file upload with debugging...");
    
    var shipName = requestData.ship_name;
    var parentCategory = requestData.parent_category;
    var category = requestData.category;
    var filename = requestData.filename;
    var fileContent = requestData.file_content;
    var parentFolderId = requestData.parent_folder_id;
    
    Logger.log("📋 Upload parameters:");
    Logger.log("   Ship Name: " + shipName);
    Logger.log("   Parent Category: " + parentCategory);
    Logger.log("   Category: " + category);
    Logger.log("   Filename: " + filename);
    Logger.log("   Parent Folder ID: " + parentFolderId);
    Logger.log("   Content Length: " + (fileContent ? fileContent.length : 0));
    
    if (!shipName || !filename || !fileContent || !parentFolderId) {
      return createResponse(false, "Missing required parameters");
    }
    
    // Step 1: Get parent folder
    var parentFolder;
    try {
      parentFolder = DriveApp.getFolderById(parentFolderId);
      Logger.log("✅ Parent folder accessed: " + parentFolder.getName());
    } catch (e) {
      Logger.log("❌ Parent folder error: " + e.toString());
      return createResponse(false, "Parent folder not accessible: " + e.toString());
    }
    
    // Step 2: Find or create ship folder
    var shipFolder = findOrCreateFolderSafe(parentFolder, shipName);
    if (!shipFolder) {
      Logger.log("❌ Ship folder creation failed: " + shipName);
      return createResponse(false, "Ship folder not found/created: " + shipName);
    }
    Logger.log("✅ Ship folder ready: " + shipFolder.getName());
    
    // Step 3: Determine target folder based on category structure
    var targetFolder;
    var folderPath;
    
    if (parentCategory && category) {
      // Nested structure: Ship/ParentCategory/Category
      Logger.log("📁 Creating nested structure: " + shipName + "/" + parentCategory + "/" + category);
      targetFolder = createFolderPathSafe(shipFolder, [parentCategory, category]);
      folderPath = shipName + "/" + parentCategory + "/" + category;
    } else if (category) {
      // Single level: Ship/Category
      Logger.log("📁 Creating single level: " + shipName + "/" + category);
      targetFolder = createFolderPathSafe(shipFolder, [category]);
      folderPath = shipName + "/" + category;
    } else {
      // Direct to ship folder
      Logger.log("📁 Using ship folder directly: " + shipName);
      targetFolder = shipFolder;
      folderPath = shipName;
    }
    
    if (!targetFolder) {
      Logger.log("❌ Target folder creation failed");
      return createResponse(false, "Failed to create target folder structure");
    }
    
    Logger.log("✅ Target folder ready: " + targetFolder.getName());
    Logger.log("📂 Final folder path: " + folderPath);
    
    // Step 4: Create file
    try {
      var binaryData = Utilities.base64Decode(fileContent);
      var blob = Utilities.newBlob(binaryData, "application/pdf", filename);
      var uploadedFile = targetFolder.createFile(blob);
      
      Logger.log("✅ File created successfully!");
      Logger.log("🆔 File ID: " + uploadedFile.getId());
      Logger.log("📝 File name: " + uploadedFile.getName());
      
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
    
  } catch (error) {
    Logger.log("❌ Upload handler error: " + error.toString());
    return createResponse(false, "Upload failed: " + error.toString());
  }
}

/**
 * Safe folder creation with enhanced debugging
 */
function createFolderPathSafe(parentFolder, folderNames) {
  try {
    Logger.log("🏗️ Creating folder path: " + JSON.stringify(folderNames));
    
    var currentFolder = parentFolder;
    
    for (var i = 0; i < folderNames.length; i++) {
      var folderName = folderNames[i];
      Logger.log("📁 Processing folder: " + folderName);
      
      // First, try to find existing folder
      var existingFolder = findFolderByNameSafe(currentFolder, folderName);
      
      if (existingFolder) {
        Logger.log("   ✅ Found existing: " + folderName);
        currentFolder = existingFolder;
      } else {
        Logger.log("   🆕 Creating new: " + folderName);
        try {
          currentFolder = currentFolder.createFolder(folderName);
          Logger.log("   ✅ Created: " + folderName + " (ID: " + currentFolder.getId() + ")");
        } catch (createError) {
          Logger.log("   ❌ Creation failed: " + folderName + " - " + createError.toString());
          return null;
        }
      }
    }
    
    Logger.log("✅ Folder path created successfully: " + currentFolder.getName());
    return currentFolder;
    
  } catch (error) {
    Logger.log("❌ Folder path creation error: " + error.toString());
    return null;
  }
}

/**
 * Safe folder finder with enhanced debugging
 */
function findFolderByNameSafe(parentFolder, folderName) {
  try {
    Logger.log("🔍 Looking for folder: '" + folderName + "' in '" + parentFolder.getName() + "'");
    
    // Get all folders in parent
    var allFolders = parentFolder.getFolders();
    var foundFolders = [];
    
    while (allFolders.hasNext()) {
      var folder = allFolders.next();
      var currentName = folder.getName();
      foundFolders.push(currentName);
      
      // Exact match
      if (currentName === folderName) {
        Logger.log("   ✅ Found exact match: " + currentName);
        return folder;
      }
    }
    
    Logger.log("   📋 Available folders: " + JSON.stringify(foundFolders));
    Logger.log("   ❌ Folder '" + folderName + "' not found");
    return null;
    
  } catch (error) {
    Logger.log("   ❌ Error searching for folder: " + error.toString());
    return null;
  }
}

/**
 * Safe folder finder or creator
 */
function findOrCreateFolderSafe(parentFolder, folderName) {
  var existingFolder = findFolderByNameSafe(parentFolder, folderName);
  if (existingFolder) {
    return existingFolder;
  }
  
  try {
    Logger.log("🆕 Creating folder: " + folderName);
    var newFolder = parentFolder.createFolder(folderName);
    Logger.log("✅ Created folder: " + folderName + " (ID: " + newFolder.getId() + ")");
    return newFolder;
  } catch (error) {
    Logger.log("❌ Failed to create folder: " + folderName + " - " + error.toString());
    return null;
  }
}

/**
 * Debug folder structure
 */
function debugFolderStructure(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    
    if (!parentFolderId) {
      return createResponse(false, "Missing parent_folder_id for debug");
    }
    
    Logger.log("🔍 Debugging folder structure...");
    Logger.log("   Parent Folder ID: " + parentFolderId);
    Logger.log("   Ship Name: " + shipName);
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    Logger.log("   Parent folder name: " + parentFolder.getName());
    
    // List all folders in parent
    var folders = parentFolder.getFolders();
    var folderList = [];
    
    while (folders.hasNext()) {
      var folder = folders.next();
      folderList.push({
        name: folder.getName(),
        id: folder.getId()
      });
    }
    
    Logger.log("   Found " + folderList.length + " folders in parent");
    
    var result = {
      parent_folder_name: parentFolder.getName(),
      parent_folder_id: parentFolderId,
      total_folders: folderList.length,
      folders: folderList
    };
    
    // If ship name provided, check ship folder
    if (shipName) {
      var shipFolder = findFolderByNameSafe(parentFolder, shipName);
      if (shipFolder) {
        result.ship_folder_found = true;
        result.ship_folder_id = shipFolder.getId();
        
        // Check subfolders in ship folder
        var subFolders = shipFolder.getFolders();
        var subFolderList = [];
        
        while (subFolders.hasNext()) {
          var subFolder = subFolders.next();
          subFolderList.push({
            name: subFolder.getName(),
            id: subFolder.getId()
          });
        }
        
        result.ship_subfolders = subFolderList;
      } else {
        result.ship_folder_found = false;
      }
    }
    
    return createResponse(true, "Folder structure debug completed", result);
    
  } catch (error) {
    return createResponse(false, "Debug failed: " + error.toString());
  }
}

function createResponse(success, message, data) {
  var response = {
    success: success,
    message: message,
    timestamp: new Date().toISOString(),
    service: "Company Apps Script - Fixed Upload",
    version: "v4.1-upload-bug-fix"
  };
  
  if (data) {
    for (var key in data) {
      response[key] = data[key];
    }
  }
  
  Logger.log("📤 Response: " + JSON.stringify(response, null, 2));
  
  return ContentService
    .createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}

// Legacy support functions
function handleTestConnection(requestData) {
  try {
    var folderId = requestData.folder_id || requestData.parent_folder_id;
    if (!folderId) {
      return createResponse(false, "Missing folder_id or parent_folder_id");
    }
    
    var folder = DriveApp.getFolderById(folderId);
    return createResponse(true, "Connection successful", {
      folder_name: folder.getName(),
      folder_id: folderId,
      test_result: "PASSED"
    });
    
  } catch (error) {
    return createResponse(false, "Connection failed: " + error.toString());
  }
}