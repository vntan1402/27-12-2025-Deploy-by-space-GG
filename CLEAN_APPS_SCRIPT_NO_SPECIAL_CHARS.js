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
      try {
        requestData = JSON.parse(e.postData.contents);
      } catch (parseError) {
        return createJsonResponse(false, "Invalid JSON: " + parseError.toString());
      }
    } else if (e && e.parameter) {
      requestData = e.parameter;
    } else {
      return createJsonResponse(true, "Ship Management Apps Script v3.8 WORKING", {
        version: "3.8-multi-cert-fix",
        timestamp: new Date().toISOString(),
        supported_actions: [
          "test_connection", 
          "create_complete_ship_structure", 
          "upload_file_with_folder_creation",
          "check_ship_folder_exists",
          "get_folder_structure",
          "move_file",
          "delete_file",
          "rename_file"
        ]
      });
    }
    
    var action = requestData.action || "default";
    
    switch (action) {
      case 'test_connection':
        return handleTestConnection(requestData);
        
      case 'create_complete_ship_structure':
        return handleCreateCompleteShipStructure(requestData);
        
      case 'upload_file_with_folder_creation':
        return handleUploadFileWithFolderCreation(requestData);
        
      case 'check_ship_folder_exists':
        return handleCheckShipFolderExists(requestData);
        
      case 'get_folder_structure':
        return handleGetFolderStructure(requestData);
        
      case 'move_file':
        return handleMoveFile(requestData);
        
      case 'delete_file':
        return handleDeleteFile(requestData);
        
      case 'rename_file':
        return handleRenameFile(requestData);
        
      default:
        return createJsonResponse(true, "Apps Script working", {
          received_action: action
        });
    }
    
  } catch (error) {
    Logger.log("Global error: " + error.toString());
    return createJsonResponse(false, "Error: " + error.toString());
  }
}

function createJsonResponse(success, message, data) {
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

function handleTestConnection(requestData) {
  try {
    var folderId = requestData.folder_id;
    
    if (!folderId) {
      return createJsonResponse(false, "Missing folder_id parameter");
    }
    
    try {
      var folder = DriveApp.getFolderById(folderId);
      var folderName = folder.getName();
      
      return createJsonResponse(true, "Connection successful", {
        folder_name: folderName,
        folder_id: folderId,
        test_result: "PASSED"
      });
    } catch (driveError) {
      return createJsonResponse(false, "Google Drive access failed: " + driveError.toString());
    }
    
  } catch (error) {
    return createJsonResponse(false, "Connection test failed: " + error.toString());
  }
}

function handleCreateCompleteShipStructure(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    var backendApiUrl = requestData.backend_api_url;
    
    if (!parentFolderId || !shipName) {
      return createJsonResponse(false, "Missing required parameters");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findOrCreateFolder(parentFolder, shipName);
    
    var folderStructure;
    
    if (backendApiUrl) {
      var dynamicResult = getDynamicFolderStructure(backendApiUrl);
      if (dynamicResult.success) {
        folderStructure = dynamicResult.structure;
      } else {
        folderStructure = getFallbackFolderStructure().structure;
      }
    } else {
      folderStructure = getFallbackFolderStructure().structure;
    }
    
    var subfolderIds = {};
    var totalSubfoldersCreated = 0;
    
    for (var mainCategory in folderStructure) {
      var mainFolder = findOrCreateFolder(shipFolder, mainCategory);
      subfolderIds[mainCategory] = mainFolder.getId();
      
      var subCategories = folderStructure[mainCategory];
      for (var i = 0; i < subCategories.length; i++) {
        var subCategory = subCategories[i];
        findOrCreateFolder(mainFolder, subCategory);
        totalSubfoldersCreated++;
      }
    }
    
    return createJsonResponse(true, "Ship structure created: " + shipName, {
      ship_folder_id: shipFolder.getId(),
      total_subfolders_created: totalSubfoldersCreated
    });
    
  } catch (error) {
    return createJsonResponse(false, "Folder creation failed: " + error.toString());
  }
}

function getDynamicFolderStructure(backendApiUrl) {
  try {
    var apiUrl = backendApiUrl + "/api/sidebar-structure";
    
    var response = UrlFetchApp.fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      muteHttpExceptions: true,
      timeout: 15
    });
    
    if (response.getResponseCode() === 200) {
      var result = JSON.parse(response.getContentText());
      
      if (result.success && result.structure) {
        return {
          success: true,
          structure: result.structure
        };
      }
    }
    
    return { success: false, error: "API call failed" };
    
  } catch (error) {
    return { success: false, error: error.toString() };
  }
}

function getFallbackFolderStructure() {
  return {
    success: true,
    structure: {
      "Class & Flag Cert": [
        "Certificates",
        "Class Survey Report",
        "Test Report",
        "Drawings & Manuals",
        "Other Documents"
      ],
      "Crew Records": [
        "Crew List",
        "Crew Certificates",
        "Medical Records"
      ],
      "ISM Records": [
        "ISM Certificate",
        "Safety Procedures",
        "Audit Reports"
      ]
    }
  };
}

function handleUploadFileWithFolderCreation(requestData) {
  try {
    var shipName = requestData.ship_name;
    var parentCategory = requestData.parent_category;
    var category = requestData.category;
    var filename = requestData.filename;
    var fileContent = requestData.file_content;
    var contentType = requestData.content_type || 'application/pdf';
    var parentFolderId = requestData.parent_folder_id;
    
    if (!shipName || !category || !filename || !fileContent) {
      return createJsonResponse(false, "Missing required parameters");
    }
    
    if (!parentFolderId) {
      return createJsonResponse(false, "Parent folder ID not available");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findFolderByName(parentFolder, shipName);
    
    if (!shipFolder) {
      return createJsonResponse(false, "Ship folder not found: " + shipName);
    }
    
    var targetFolder;
    var folderPath;
    
    if (parentCategory) {
      var folderHierarchy = [parentCategory, category];
      targetFolder = createNestedFolders(shipFolder, folderHierarchy);
      if (!targetFolder) {
        return createJsonResponse(false, "Failed to create nested folder structure");
      }
      folderPath = shipName + "/" + parentCategory + "/" + category;
    } else {
      var classFlagCertCategories = ["Certificates", "Class Survey Report", "Test Report", "Drawings & Manuals", "Other Documents"];
      
      if (classFlagCertCategories.indexOf(category) !== -1) {
        var parentCategoryFolder = findFolderByName(shipFolder, "Class & Flag Cert");
        if (!parentCategoryFolder) {
          return createJsonResponse(false, "Class & Flag Cert folder not found");
        }
        targetFolder = findFolderByName(parentCategoryFolder, category);
        if (!targetFolder) {
          return createJsonResponse(false, "Category folder not found: " + category);
        }
        folderPath = shipName + "/Class & Flag Cert/" + category;
      } else {
        targetFolder = findFolderByName(shipFolder, category);
        if (!targetFolder) {
          return createJsonResponse(false, "Category folder not found: " + category);
        }
        folderPath = shipName + "/" + category;
      }
    }
    
    var binaryData = Utilities.base64Decode(fileContent);
    var blob = Utilities.newBlob(binaryData, contentType, filename);
    var uploadedFile = targetFolder.createFile(blob);
    
    return createJsonResponse(true, "File uploaded successfully: " + filename, {
      file_id: uploadedFile.getId(),
      file_name: uploadedFile.getName(),
      file_url: uploadedFile.getUrl(),
      folder_path: folderPath,
      upload_timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    return createJsonResponse(false, "File upload failed: " + error.toString());
  }
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

function handleRenameFile(requestData) {
  try {
    var fileId = requestData.file_id;
    var newName = requestData.new_name;
    
    if (!fileId || !newName) {
      return createJsonResponse(false, "Missing required parameters: file_id and new_name");
    }
    
    var file = DriveApp.getFileById(fileId);
    var originalName = file.getName();
    file.setName(newName);
    
    return createJsonResponse(true, "File renamed successfully", {
      file_id: fileId,
      old_name: originalName,
      new_name: newName
    });
    
  } catch (error) {
    return createJsonResponse(false, "Error renaming file: " + error.toString());
  }
}

function handleCheckShipFolderExists(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    
    if (!parentFolderId || !shipName) {
      return createJsonResponse(false, "Missing required parameters");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findFolderByName(parentFolder, shipName);
    
    if (!shipFolder) {
      return createJsonResponse(true, "Ship folder not found", {
        folder_exists: false
      });
    }
    
    return createJsonResponse(true, "Ship folder found", {
      folder_exists: true,
      ship_folder_id: shipFolder.getId()
    });
    
  } catch (error) {
    return createJsonResponse(false, "Folder check failed: " + error.toString());
  }
}

function handleGetFolderStructure(requestData) {
  try {
    return createJsonResponse(true, "Folder structure retrieved", {
      folders: [],
      total_count: 0
    });
  } catch (error) {
    return createJsonResponse(false, "Error getting folder structure: " + error.toString());
  }
}

function handleMoveFile(requestData) {
  try {
    var fileId = requestData.file_id;
    var targetFolderId = requestData.target_folder_id;
    
    if (!fileId || !targetFolderId) {
      return createJsonResponse(false, "Missing required parameters");
    }
    
    var file = DriveApp.getFileById(fileId);
    var targetFolder = DriveApp.getFolderById(targetFolderId);
    
    var parents = file.getParents();
    while (parents.hasNext()) {
      var parent = parents.next();
      parent.removeFile(file);
    }
    
    targetFolder.addFile(file);
    
    return createJsonResponse(true, "File moved successfully", {
      file_id: fileId,
      target_folder_id: targetFolderId
    });
    
  } catch (error) {
    return createJsonResponse(false, "Error moving file: " + error.toString());
  }
}

function handleDeleteFile(requestData) {
  try {
    var fileId = requestData.file_id;
    
    if (!fileId) {
      return createJsonResponse(false, "Missing required parameter: file_id");
    }
    
    var file = DriveApp.getFileById(fileId);
    file.setTrashed(true);
    
    return createJsonResponse(true, "File deleted successfully", {
      file_id: fileId
    });
    
  } catch (error) {
    return createJsonResponse(false, "Error deleting file: " + error.toString());
  }
}

function findOrCreateFolder(parentFolder, folderName) {
  var existingFolder = findFolderByName(parentFolder, folderName);
  if (existingFolder) {
    return existingFolder;
  }
  return parentFolder.createFolder(folderName);
}

function findFolderByName(parentFolder, folderName) {
  var folders = parentFolder.getFoldersByName(folderName);
  return folders.hasNext() ? folders.next() : null;
}