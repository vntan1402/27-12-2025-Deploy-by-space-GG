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
    
    switch (action) {
      case "passport_upload":
        return handlePassportUpload(requestData);
      case "upload_file_with_folder_creation":
        return handleUpload(requestData);
      case "test_connection":
        return handleTestConnection(requestData);
      case "create_complete_ship_structure":
        return handleCreateShipStructure(requestData);
      case "delete_complete_ship_structure":
        return handleDeleteShipStructure(requestData);
      case "rename_file":
        return handleRenameFile(requestData);
      case "move_file":
        return handleMoveFile(requestData);
      case "delete_file":
        return handleDeleteFile(requestData);
      case "get_folder_structure":
        return handleGetFolderStructure(requestData);
      case "check_ship_folder_exists":
        return handleCheckShipFolder(requestData);
      default:
        // Default handler for backend passport requests (no action specified)
        return handlePassportUpload(requestData);
    }
    
  } catch (error) {
    return createResponse(false, "Error: " + error.toString());
  }
}

function handlePassportUpload(requestData) {
  try {
    Logger.log("🔄 Processing passport upload request: " + JSON.stringify(requestData));
    
    var filename = requestData.filename;
    var fileContent = requestData.file_content;
    var folderPath = requestData.folder_path;
    var contentType = requestData.content_type || "application/pdf";
    var parentFolderId = requestData.parent_folder_id;
    
    if (!filename || !fileContent || !folderPath) {
      return createResponse(false, "Missing required parameters: filename, file_content, folder_path");
    }
    
    if (!parentFolderId) {
      return createResponse(false, "Missing parent_folder_id. Company Google Drive Folder ID must be configured in backend.");
    }
    
    Logger.log("📁 Company root folder ID: " + parentFolderId);
    Logger.log("📂 Target folder path: " + folderPath);
    
    var rootFolder = DriveApp.getFolderById(rootFolderId);
    var targetFolder = createFolderPath(rootFolder, folderPath);
    
    if (!targetFolder) {
      return createResponse(false, "Failed to create target folder: " + folderPath);
    }
    
    // Decode base64 content and create file
    Logger.log("📤 Creating file: " + filename);
    var binaryData = Utilities.base64Decode(fileContent);
    var blob = Utilities.newBlob(binaryData, contentType, filename);
    var uploadedFile = targetFolder.createFile(blob);
    
    Logger.log("✅ File uploaded successfully: " + uploadedFile.getId());
    
    return createResponse(true, "File uploaded successfully to " + folderPath, {
      file_id: uploadedFile.getId(),
      file_name: uploadedFile.getName(),
      file_url: uploadedFile.getUrl(),
      folder_path: folderPath,
      folder_id: targetFolder.getId(),
      upload_timestamp: new Date().toISOString(),
      file_size: uploadedFile.getSize()
    });
    
  } catch (error) {
    Logger.log("❌ Upload failed: " + error.toString());
    return createResponse(false, "Upload failed: " + error.toString(), {
      folder_path: requestData.folder_path,
      filename: requestData.filename,
      error_details: error.toString()
    });
  }
}

function createFolderPath(rootFolder, folderPath) {
  try {
    Logger.log("🏗️ Creating folder path: " + folderPath);
    
    // Split folder path and create nested folders
    var pathParts = folderPath.split('/').filter(function(part) {
      return part.length > 0;
    });
    
    var currentFolder = rootFolder;
    
    for (var i = 0; i < pathParts.length; i++) {
      var folderName = pathParts[i].trim();
      Logger.log("📁 Processing folder: " + folderName);
      
      var existingFolder = findFolderByName(currentFolder, folderName);
      if (existingFolder) {
        Logger.log("✅ Found existing folder: " + folderName);
        currentFolder = existingFolder;
      } else {
        Logger.log("🆕 Creating new folder: " + folderName);
        currentFolder = currentFolder.createFolder(folderName);
      }
    }
    
    Logger.log("✅ Final folder created/found: " + currentFolder.getName());
    return currentFolder;
    
  } catch (error) {
    Logger.log("❌ Error creating folder path: " + error.toString());
    return null;
  }
}

function createResponse(success, message, data) {
  var response = {
    success: success,
    message: message,
    timestamp: new Date().toISOString()
  };
  
  if (data) {
    for (var key in data) {
      response[key] = data[key];
    }
  }
  
  return ContentService
    .createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}

// Existing functions from original script...

function handleDeleteShipStructure(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    var permanentDelete = requestData.permanent_delete || false;
    
    if (!parentFolderId || !shipName) {
      return createResponse(false, "Missing required parameters: parent_folder_id and ship_name");
    }
    
    Logger.log("Deleting ship structure: " + shipName + " (permanent: " + permanentDelete + ")");
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findFolderByName(parentFolder, shipName);
    
    if (!shipFolder) {
      return createResponse(false, "Ship folder not found: " + shipName);
    }
    
    var deletionStats = countFolderContents(shipFolder);
    var shipFolderId = shipFolder.getId();
    
    try {
      if (permanentDelete) {
        DriveApp.removeFolder(shipFolder);
        Logger.log("Ship structure permanently deleted: " + shipName);
      } else {
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

function countFolderContents(folder) {
  try {
    var stats = {
      total_folders: 0,
      total_files: 0,
      main_categories: []
    };
    
    var mainFolders = folder.getFolders();
    while (mainFolders.hasNext()) {
      var mainFolder = mainFolders.next();
      stats.total_folders++;
      stats.main_categories.push(mainFolder.getName());
      
      var subFolders = mainFolder.getFolders();
      while (subFolders.hasNext()) {
        subFolders.next();
        stats.total_folders++;
      }
      
      var files = mainFolder.getFiles();
      while (files.hasNext()) {
        files.next();
        stats.total_files++;
      }
    }
    
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

function handleUpload(requestData) {
  try {
    var shipName = requestData.ship_name;
    var parentCategory = requestData.parent_category;
    var category = requestData.category;
    var filename = requestData.filename;
    var fileContent = requestData.file_content;
    var parentFolderId = requestData.parent_folder_id;
    
    if (!shipName || !category || !filename || !fileContent || !parentFolderId) {
      return createResponse(false, "Missing required parameters");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findFolderByName(parentFolder, shipName);
    
    if (!shipFolder) {
      return createResponse(false, "Ship folder not found: " + shipName);
    }
    
    var targetFolder;
    var folderPath;
    
    if (parentCategory) {
      targetFolder = createNestedFolders(shipFolder, [parentCategory, category]);
      if (!targetFolder) {
        return createResponse(false, "Failed to create nested folders");
      }
      folderPath = shipName + "/" + parentCategory + "/" + category;
    } else {
      var parentCategoryFolder = findFolderByName(shipFolder, "Class & Flag Cert");
      if (!parentCategoryFolder) {
        return createResponse(false, "Class & Flag Cert folder not found");
      }
      targetFolder = findFolderByName(parentCategoryFolder, category);
      if (!targetFolder) {
        return createResponse(false, "Category folder not found: " + category);
      }
      folderPath = shipName + "/Class & Flag Cert/" + category;
    }
    
    var binaryData = Utilities.base64Decode(fileContent);
    var blob = Utilities.newBlob(binaryData, "application/pdf", filename);
    var uploadedFile = targetFolder.createFile(blob);
    
    return createResponse(true, "File uploaded successfully", {
      file_id: uploadedFile.getId(),
      file_name: uploadedFile.getName(),
      file_url: uploadedFile.getUrl(),
      folder_path: folderPath,
      upload_timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    return createResponse(false, "Upload failed: " + error.toString());
  }
}

function handleRenameFile(requestData) {
  try {
    var fileId = requestData.file_id;
    var newName = requestData.new_name;
    
    if (!fileId || !newName) {
      return createResponse(false, "Missing file_id or new_name");
    }
    
    var file = DriveApp.getFileById(fileId);
    var oldName = file.getName();
    file.setName(newName);
    
    return createResponse(true, "File renamed successfully", {
      file_id: fileId,
      old_name: oldName,
      new_name: newName
    });
    
  } catch (error) {
    return createResponse(false, "Rename failed: " + error.toString());
  }
}

function handleMoveFile(requestData) {
  try {
    var fileId = requestData.file_id;
    var targetFolderId = requestData.target_folder_id;
    
    if (!fileId || !targetFolderId) {
      return createResponse(false, "Missing file_id or target_folder_id");
    }
    
    var file = DriveApp.getFileById(fileId);
    var targetFolder = DriveApp.getFolderById(targetFolderId);
    
    var parents = file.getParents();
    while (parents.hasNext()) {
      parents.next().removeFile(file);
    }
    
    targetFolder.addFile(file);
    
    return createResponse(true, "File moved successfully", {
      file_id: fileId,
      file_name: file.getName(),
      target_folder_id: targetFolderId,
      target_folder_name: targetFolder.getName()
    });
    
  } catch (error) {
    return createResponse(false, "Move failed: " + error.toString());
  }
}

function handleDeleteFile(requestData) {
  try {
    var fileId = requestData.file_id;
    var permanentDelete = requestData.permanent_delete || false;
    
    if (!fileId) {
      return createResponse(false, "Missing file_id");
    }
    
    var file = DriveApp.getFileById(fileId);
    var fileName = file.getName();
    
    if (permanentDelete) {
      DriveApp.removeFile(file);
    } else {
      file.setTrashed(true);
    }
    
    return createResponse(true, "File deleted successfully", {
      file_id: fileId,
      file_name: fileName,
      delete_method: permanentDelete ? "permanent" : "trash"
    });
    
  } catch (error) {
    return createResponse(false, "Delete failed: " + error.toString());
  }
}

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
      var shipFolder = findFolderByName(parentFolder, shipName);
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

function handleCheckShipFolder(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    
    if (!parentFolderId || !shipName) {
      return createResponse(false, "Missing parameters");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findFolderByName(parentFolder, shipName);
    
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

function handleTestConnection(requestData) {
  try {
    var folderId = requestData.folder_id;
    if (!folderId) {
      return createResponse(false, "Missing folder_id");
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

function handleCreateShipStructure(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    var backendApiUrl = requestData.backend_api_url;
    
    if (!parentFolderId || !shipName) {
      return createResponse(false, "Missing parameters");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findOrCreateFolder(parentFolder, shipName);
    
    var structure = getFolderStructure(backendApiUrl);
    var totalCreated = 0;
    
    for (var mainCategory in structure) {
      var mainFolder = findOrCreateFolder(shipFolder, mainCategory);
      var subCategories = structure[mainCategory];
      
      for (var i = 0; i < subCategories.length; i++) {
        findOrCreateFolder(mainFolder, subCategories[i]);
        totalCreated++;
      }
    }
    
    return createResponse(true, "Ship structure created", {
      ship_folder_id: shipFolder.getId(),
      ship_folder_name: shipFolder.getName(),
      total_subfolders_created: totalCreated,
      structure_source: backendApiUrl ? "dynamic" : "fallback"
    });
    
  } catch (error) {
    return createResponse(false, "Structure creation failed: " + error.toString());
  }
}

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

function findFolderByName(parentFolder, folderName) {
  var folders = parentFolder.getFoldersByName(folderName);
  return folders.hasNext() ? folders.next() : null;
}

function findOrCreateFolder(parentFolder, folderName) {
  var existingFolder = findFolderByName(parentFolder, folderName);
  return existingFolder || parentFolder.createFolder(folderName);
}