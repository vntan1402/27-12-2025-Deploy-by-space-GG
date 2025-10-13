/**
 * COMPLETE GOOGLE APPS SCRIPT v4.2 - MERGED VERSION
 * Combines all functionalities from both scripts:
 * - Ship management and file operations
 * - Enhanced upload with debugging
 * - Passport upload handling
 * - File operations (rename, move, delete)
 * - Folder structure management
 */

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
    
    var action = requestData.action || "default";
    
    Logger.log("🔄 Request action: " + action);
    Logger.log("📋 Request data keys: " + Object.keys(requestData));
    
    switch (action) {
      // File upload actions
      case "passport_upload":
        return handlePassportUpload(requestData);
      case "upload_file_with_folder_creation":
        return handleUploadFixed(requestData);
      case "upload_crew_certificate":
        return handleCrewCertificateUpload(requestData);
      
      // File management actions
      case "rename_file":
        return handleRenameFile(requestData);
      case "move_file":
        return handleMoveFile(requestData);
      case "delete_file":
        return handleDeleteFile(requestData);
      
      // Ship structure actions
      case "create_complete_ship_structure":
        return handleCreateShipStructure(requestData);
      case "delete_complete_ship_structure":
        return handleDeleteShipStructure(requestData);
      case "get_folder_structure":
        return handleGetFolderStructure(requestData);
      case "check_ship_folder_exists":
        return handleCheckShipFolder(requestData);
      
      // Debug and testing actions
      case "test_connection":
        return handleTestConnection(requestData);
      case "debug_folder_structure":
        return debugFolderStructure(requestData);
      
      default:
        return createResponse(true, "Complete Ship Management Apps Script v4.3 MERGED", {
          version: "4.3-complete-merged-crew-certificates",
          supported_actions: [
            "passport_upload",
            "upload_file_with_folder_creation",
            "upload_crew_certificate",
            "rename_file",
            "move_file", 
            "delete_file",
            "create_complete_ship_structure",
            "delete_complete_ship_structure",
            "get_folder_structure",
            "check_ship_folder_exists",
            "test_connection",
            "debug_folder_structure"
          ],
          available_actions: [
            "passport_upload",
            "upload_file_with_folder_creation", 
            "rename_file",
            "move_file",
            "delete_file",
            "create_complete_ship_structure",
            "delete_complete_ship_structure",
            "get_folder_structure",
            "check_ship_folder_exists",
            "test_connection",
            "debug_folder_structure"
          ],
          action_received: action,
          service: "Complete Ship Management System",
          features: [
            "Enhanced file upload with debugging",
            "Passport document processing",
            "Ship folder structure management",
            "File operations (rename, move, delete)",
            "Advanced folder debugging",
            "Connection testing"
          ]
        });
    }
    
  } catch (error) {
    Logger.log("❌ Request handling error: " + error.toString());
    return createResponse(false, "Error: " + error.toString());
  }
}

/**
 * Handle passport upload (from second script)
 */
function handlePassportUpload(requestData) {
  Logger.log("📄 Processing passport upload...");
  // Use the enhanced upload function for passport files
  return handleUploadFixed(requestData);
}

/**
 * ENHANCED FILE UPLOAD with debugging (from second script)
 */
function handleUploadFixed(requestData) {
  try {
    Logger.log("🔄 ENHANCED: Starting file upload with debugging...");
    
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
      // IMPORTANT: Crew Records should upload directly to Ship/Crew Records, NOT Ship/Class & Flag Cert/Crew Records
      if (category === "Crew Records") {
        // Create direct path: Ship/Crew Records
        Logger.log("📁 Creating Crew Records: " + shipName + "/Crew Records");
        targetFolder = createFolderPathSafe(shipFolder, [category]);
        folderPath = shipName + "/Crew Records";
      } else if (category && !parentCategory) {
        // For other categories, try to find "Class & Flag Cert" parent category first (legacy compatibility)
        var classFlagFolder = findFolderByNameSafe(shipFolder, "Class & Flag Cert");
        if (classFlagFolder) {
          Logger.log("📁 Using Class & Flag Cert structure: " + shipName + "/Class & Flag Cert/" + category);
          targetFolder = findOrCreateFolderSafe(classFlagFolder, category);
          folderPath = shipName + "/Class & Flag Cert/" + category;
        } else {
          // Create direct single level
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
 * RENAME FILE (from first script)
 */
function handleRenameFile(requestData) {
  try {
    Logger.log("✏️ Starting file rename operation...");
    
    var fileId = requestData.file_id;
    var newName = requestData.new_name;
    
    Logger.log("📋 Rename parameters:");
    Logger.log("   File ID: " + fileId);
    Logger.log("   New Name: " + newName);
    
    if (!fileId || !newName) {
      return createResponse(false, "Missing file_id or new_name");
    }
    
    var file = DriveApp.getFileById(fileId);
    var oldName = file.getName();
    
    Logger.log("📝 Original filename: " + oldName);
    
    file.setName(newName);
    
    Logger.log("✅ File renamed successfully!");
    Logger.log("📝 New filename: " + newName);
    
    return createResponse(true, "File renamed successfully", {
      file_id: fileId,
      old_name: oldName,
      new_name: newName,
      renamed_timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    Logger.log("❌ Rename failed: " + error.toString());
    return createResponse(false, "Rename failed: " + error.toString());
  }
}

/**
 * MOVE FILE (from first script)
 */
function handleMoveFile(requestData) {
  try {
    Logger.log("📦 Starting file move operation...");
    
    var fileId = requestData.file_id;
    var targetFolderId = requestData.target_folder_id;
    
    if (!fileId || !targetFolderId) {
      return createResponse(false, "Missing file_id or target_folder_id");
    }
    
    var file = DriveApp.getFileById(fileId);
    var targetFolder = DriveApp.getFolderById(targetFolderId);
    
    // Remove from current parents
    var parents = file.getParents();
    while (parents.hasNext()) {
      parents.next().removeFile(file);
    }
    
    // Add to target folder
    targetFolder.addFile(file);
    
    Logger.log("✅ File moved successfully!");
    
    return createResponse(true, "File moved successfully", {
      file_id: fileId,
      file_name: file.getName(),
      target_folder_id: targetFolderId,
      target_folder_name: targetFolder.getName(),
      moved_timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    Logger.log("❌ Move failed: " + error.toString());
    return createResponse(false, "Move failed: " + error.toString());
  }
}

/**
 * DELETE FILE (from first script)
 */
function handleDeleteFile(requestData) {
  try {
    Logger.log("🗑️ Starting file delete operation...");
    
    var fileId = requestData.file_id;
    var permanentDelete = requestData.permanent_delete || false;
    
    if (!fileId) {
      return createResponse(false, "Missing file_id");
    }
    
    var file = DriveApp.getFileById(fileId);
    var fileName = file.getName();
    
    Logger.log("📝 Deleting file: " + fileName);
    Logger.log("🔥 Permanent delete: " + permanentDelete);
    
    if (permanentDelete) {
      DriveApp.removeFile(file);
    } else {
      file.setTrashed(true);
    }
    
    Logger.log("✅ File deleted successfully!");
    
    return createResponse(true, "File deleted successfully", {
      file_id: fileId,
      file_name: fileName,
      delete_method: permanentDelete ? "permanent" : "trash",
      deleted_timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    Logger.log("❌ Delete failed: " + error.toString());
    return createResponse(false, "Delete failed: " + error.toString());
  }
}

/**
 * CREATE SHIP STRUCTURE (from first script)
 */
function handleCreateShipStructure(requestData) {
  try {
    Logger.log("🏗️ Creating ship structure...");
    
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    var backendApiUrl = requestData.backend_api_url;
    
    if (!parentFolderId || !shipName) {
      return createResponse(false, "Missing parameters");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findOrCreateFolderSafe(parentFolder, shipName);
    
    if (!shipFolder) {
      return createResponse(false, "Failed to create ship folder");
    }
    
    var structure = getFolderStructure(backendApiUrl);
    var totalCreated = 0;
    
    for (var mainCategory in structure) {
      var mainFolder = findOrCreateFolderSafe(shipFolder, mainCategory);
      if (mainFolder) {
        var subCategories = structure[mainCategory];
        
        for (var i = 0; i < subCategories.length; i++) {
          var subFolder = findOrCreateFolderSafe(mainFolder, subCategories[i]);
          if (subFolder) {
            totalCreated++;
          }
        }
      }
    }
    
    Logger.log("✅ Ship structure created!");
    
    return createResponse(true, "Ship structure created", {
      ship_folder_id: shipFolder.getId(),
      ship_folder_name: shipFolder.getName(),
      total_subfolders_created: totalCreated,
      structure_source: backendApiUrl ? "dynamic" : "fallback"
    });
    
  } catch (error) {
    Logger.log("❌ Structure creation failed: " + error.toString());
    return createResponse(false, "Structure creation failed: " + error.toString());
  }
}

/**
 * DELETE SHIP STRUCTURE (from first script)
 */
function handleDeleteShipStructure(requestData) {
  try {
    Logger.log("🗑️ Deleting ship structure...");
    
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    var permanentDelete = requestData.permanent_delete || false;
    
    if (!parentFolderId || !shipName) {
      return createResponse(false, "Missing required parameters: parent_folder_id and ship_name");
    }
    
    Logger.log("Deleting ship structure: " + shipName + " (permanent: " + permanentDelete + ")");
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findFolderByNameSafe(parentFolder, shipName);
    
    if (!shipFolder) {
      return createResponse(false, "Ship folder not found: " + shipName);
    }
    
    // Count folders and files before deletion
    var deletionStats = countFolderContents(shipFolder);
    var shipFolderId = shipFolder.getId();
    
    try {
      if (permanentDelete) {
        // Permanent deletion: remove from Drive completely
        DriveApp.removeFolder(shipFolder);
        Logger.log("Ship structure permanently deleted: " + shipName);
      } else {
        // Move to trash (can be restored)
        shipFolder.setTrashed(true);
        Logger.log("Ship structure moved to trash: " + shipName);
      }
      
      return createResponse(true, "Ship structure deleted successfully: " + shipName, {
        ship_name: shipName,
        ship_folder_id: shipFolderId,
        delete_method: permanentDelete ? "permanent_deletion" : "moved_to_trash",
        deletion_stats: deletionStats,
        deleted_timestamp: new Date().toISOString(),
        note: permanentDelete ? "Ship structure permanently deleted" : "Ship structure moved to trash (can be restored)"
      });
      
    } catch (deleteError) {
      Logger.log("Delete operation error: " + deleteError.toString());
      return createResponse(false, "Failed to delete ship structure: " + deleteError.toString(), {
        ship_name: shipName,
        error_type: "delete_operation_error"
      });
    }
    
  } catch (error) {
    Logger.log("General delete ship structure error: " + error.toString());
    return createResponse(false, "Error deleting ship structure: " + error.toString(), {
      ship_name: requestData.ship_name || "unknown",
      error_type: "general_error"
    });
  }
}

/**
 * GET FOLDER STRUCTURE (from first script)
 */
function handleGetFolderStructure(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    
    if (!parentFolderId) {
      return createResponse(false, "Missing parent_folder_id");
    }
    
    var folders = [];
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    
    if (shipName) {
      var shipFolder = findFolderByNameSafe(parentFolder, shipName);
      if (shipFolder) {
        folders.push({
          folder_id: shipFolder.getId(),
          folder_name: shipName,
          folder_path: shipName,
          level: 0
        });
        
        var mainFolders = shipFolder.getFolders();
        while (mainFolders.hasNext()) {
          var mainFolder = mainFolders.next();
          folders.push({
            folder_id: mainFolder.getId(),
            folder_name: mainFolder.getName(),
            folder_path: shipName + "/" + mainFolder.getName(),
            level: 1
          });
        }
      }
    }
    
    return createResponse(true, "Folder structure retrieved", {
      folders: folders,
      total_count: folders.length
    });
    
  } catch (error) {
    return createResponse(false, "Get folder structure failed: " + error.toString());
  }
}

/**
 * CHECK SHIP FOLDER (from first script)
 */
function handleCheckShipFolder(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    
    if (!parentFolderId || !shipName) {
      return createResponse(false, "Missing parameters");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findFolderByNameSafe(parentFolder, shipName);
    
    if (!shipFolder) {
      return createResponse(true, "Ship folder not found", {
        folder_exists: false
      });
    }
    
    return createResponse(true, "Ship folder exists", {
      folder_exists: true,
      ship_folder_id: shipFolder.getId(),
      ship_name: shipName
    });
    
  } catch (error) {
    return createResponse(false, "Check failed: " + error.toString());
  }
}

/**
 * TEST CONNECTION (enhanced from both scripts)
 */
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

/**
 * DEBUG FOLDER STRUCTURE (from second script)
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

// ===========================================
// UTILITY FUNCTIONS (Enhanced from both scripts)
// ===========================================

/**
 * Enhanced response creator
 */
function createResponse(success, message, data) {
  var response = {
    success: success,
    message: message,
    timestamp: new Date().toISOString(),
    service: "Complete Ship Management Apps Script",
    version: "v4.2-complete-merged"
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

/**
 * Safe folder creation with enhanced debugging (from second script)
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
 * Safe folder finder with enhanced debugging (from second script)
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
 * Safe folder finder or creator (enhanced from second script)
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
 * Legacy folder finder (from first script - for compatibility)
 */
function findFolderByName(parentFolder, folderName) {
  var folders = parentFolder.getFoldersByName(folderName);
  return folders.hasNext() ? folders.next() : null;
}

/**
 * Legacy folder creator (from first script - for compatibility)
 */
function findOrCreateFolder(parentFolder, folderName) {
  var existingFolder = findFolderByName(parentFolder, folderName);
  return existingFolder || parentFolder.createFolder(folderName);
}

/**
 * Count folder contents (from first script)
 */
function countFolderContents(folder) {
  try {
    var stats = {
      total_folders: 0,
      total_files: 0,
      main_categories: []
    };
    
    // Count main category folders
    var mainFolders = folder.getFolders();
    while (mainFolders.hasNext()) {
      var mainFolder = mainFolders.next();
      stats.total_folders++;
      stats.main_categories.push(mainFolder.getName());
      
      // Count subfolders
      var subFolders = mainFolder.getFolders();
      while (subFolders.hasNext()) {
        subFolders.next();
        stats.total_folders++;
      }
      
      // Count files in main folder
      var files = mainFolder.getFiles();
      while (files.hasNext()) {
        files.next();
        stats.total_files++;
      }
    }
    
    // Count files in root ship folder
    var rootFiles = folder.getFiles();
    while (rootFiles.hasNext()) {
      rootFiles.next();
      stats.total_files++;
    }
    
    return stats;
  } catch (error) {
    return {
      total_folders: "unknown",
      total_files: "unknown",
      main_categories: [],
      count_error: error.toString()
    };
  }
}

/**
 * Get folder structure (from first script)
 */
function getFolderStructure(backendApiUrl) {
  if (backendApiUrl) {
    try {
      var response = UrlFetchApp.fetch(backendApiUrl + "/api/sidebar-structure", {
        method: 'GET',
        muteHttpExceptions: true,
        timeout: 10
      });
      
      if (response.getResponseCode() === 200) {
        var result = JSON.parse(response.getContentText());
        if (result.success && result.structure) {
          return result.structure;
        }
      }
    } catch (error) {
      // Fall through to default structure
    }
  }
  
  return {
    "Class & Flag Cert": ["Certificates", "Class Survey Report", "Test Report", "Drawings & Manuals", "Other Documents"],
    "Crew Records": ["Crew List", "Crew Certificates", "Medical Records"],
    "ISM Records": ["ISM Certificate", "Safety Procedures", "Audit Reports"],
    "ISPS Records": ["ISPS Certificate", "Security Plan", "Security Assessments"],
    "MLC Records": ["MLC Certificate", "Labor Conditions", "Accommodation Reports"],
    "Supplies": ["Inventory", "Purchase Orders", "Spare Parts"]
  };
}

/**
 * Create nested folders (from first script - for compatibility)
 */
function createNestedFolders(parentFolder, folderNames) {
  try {
    var currentFolder = parentFolder;
    
    for (var i = 0; i < folderNames.length; i++) {
      var folderName = folderNames[i];
      var folders = currentFolder.getFoldersByName(folderName);
      
      if (folders.hasNext()) {
        currentFolder = folders.next();
      } else {
        currentFolder = currentFolder.createFolder(folderName);
      }
    }
    
    return currentFolder;
  } catch (error) {
    return null;
  }
}

/**
 * CREW CERTIFICATES UPLOAD HANDLER (Step 5 - Google Drive Integration)
 * Upload crew certificate files to: ShipName > Crew Records folder
 */
function handleCrewCertificateUpload(requestData) {
  try {
    Logger.log("📋 Starting crew certificate upload...");
    
    // Validate required parameters
    if (!requestData.ship_name) {
      return createResponse(false, "Missing ship_name parameter", null);
    }
    
    if (!requestData.filename) {
      return createResponse(false, "Missing filename parameter", null);
    }
    
    if (!requestData.file_content) {
      return createResponse(false, "Missing file_content parameter", null);
    }
    
    var shipName = requestData.ship_name;
    var filename = requestData.filename;
    var crewName = requestData.crew_name || "Unknown";
    var contentType = requestData.content_type || 'application/octet-stream';
    var fileContent = requestData.file_content;
    
    Logger.log("📄 Certificate file: " + filename);
    Logger.log("🚢 Ship: " + shipName);
    Logger.log("👤 Crew: " + crewName);
    
    // Decode base64 file content
    var decodedContent = Utilities.base64Decode(fileContent);
    var blob = Utilities.newBlob(decodedContent, contentType, filename);
    
    Logger.log("✅ File decoded successfully, size: " + blob.getBytes().length + " bytes");
    
    // Get root folder
    var rootFolder = DriveApp.getRootFolder();
    
    // Find or create ship folder
    var shipFolder = null;
    var shipFolders = rootFolder.getFoldersByName(shipName);
    
    if (shipFolders.hasNext()) {
      shipFolder = shipFolders.next();
      Logger.log("📁 Found existing ship folder: " + shipName);
    } else {
      shipFolder = rootFolder.createFolder(shipName);
      Logger.log("📁 Created new ship folder: " + shipName);
    }
    
    // Find or create "Crew Records" folder inside ship folder
    var crewRecordsFolder = null;
    var crewRecordsFolders = shipFolder.getFoldersByName("Crew Records");
    
    if (crewRecordsFolders.hasNext()) {
      crewRecordsFolder = crewRecordsFolders.next();
      Logger.log("📁 Found existing Crew Records folder");
    } else {
      crewRecordsFolder = shipFolder.createFolder("Crew Records");
      Logger.log("📁 Created new Crew Records folder");
    }
    
    // Upload certificate file to Crew Records folder
    Logger.log("📤 Uploading certificate file to Crew Records folder...");
    var uploadedFile = crewRecordsFolder.createFile(blob);
    var fileId = uploadedFile.getId();
    var fileUrl = uploadedFile.getUrl();
    
    Logger.log("✅ Certificate file uploaded successfully!");
    Logger.log("   File ID: " + fileId);
    Logger.log("   File URL: " + fileUrl);
    
    return createResponse(true, "Certificate file uploaded successfully to " + shipName + " > Crew Records", {
      file_id: fileId,
      file_url: fileUrl,
      file_name: filename,
      folder_path: shipName + " > Crew Records",
      crew_name: crewName
    });
    
  } catch (error) {
    Logger.log("❌ Error uploading crew certificate: " + error.toString());
    return createResponse(false, "Failed to upload crew certificate: " + error.toString(), null);
  }

}