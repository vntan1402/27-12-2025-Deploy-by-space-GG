/**
 * Ship Management System - Complete Apps Script v3.3
 * With Move and Delete Functionality
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
      try {
        requestData = JSON.parse(e.postData.contents);
      } catch (parseError) {
        return createJsonResponse(false, "Invalid JSON: " + parseError.toString());
      }
    } else if (e && e.parameter) {
      requestData = e.parameter;
    } else {
      return createJsonResponse(true, "Ship Management Apps Script v3.3 is WORKING!", {
        version: "3.3-complete-with-delete",
        timestamp: new Date().toISOString(),
        supported_actions: [
          "test_connection", 
          "create_complete_ship_structure", 
          "upload_file_with_folder_creation",
          "check_ship_folder_exists",
          "get_folder_structure",
          "move_file",
          "delete_file"
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
        
      default:
        return createJsonResponse(true, "Apps Script working - no action specified", {
          received_action: action,
          available_actions: [
            "test_connection", 
            "create_complete_ship_structure", 
            "upload_file_with_folder_creation",
            "check_ship_folder_exists",
            "get_folder_structure",
            "move_file",
            "delete_file"
          ]
        });
    }
    
  } catch (error) {
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
    
    var folder = DriveApp.getFolderById(folderId);
    var folderName = folder.getName();
    
    return createJsonResponse(true, "Connection successful", {
      folder_name: folderName,
      folder_id: folderId,
      test_result: "PASSED"
    });
    
  } catch (error) {
    return createJsonResponse(false, "Connection test failed: " + error.toString());
  }
}

function handleCreateCompleteShipStructure(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    var companyId = requestData.company_id;
    
    if (!parentFolderId || !shipName) {
      return createJsonResponse(false, "Missing required parameters: parent_folder_id, ship_name");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findOrCreateFolder(parentFolder, shipName);
    
    // CORRECT folder structure matching Homepage Sidebar
    var folderStructure = {
      "Document Portfolio": [
        "Certificates",
        "Inspection Records",
        "Survey Reports", 
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
      ],
      "ISPS Records": [
        "ISPS Certificate",
        "Security Plan",
        "Security Assessments"
      ],
      "MLC Records": [
        "MLC Certificate",
        "Labor Conditions",
        "Accommodation Reports"
      ],
      "Supplies": [
        "Inventory",
        "Purchase Orders",
        "Spare Parts"
      ]
    };
    
    var subfolderIds = {};
    var totalSubfoldersCreated = 0;
    
    for (var mainCategory in folderStructure) {
      var mainFolder = findOrCreateFolder(shipFolder, mainCategory);
      subfolderIds[mainCategory] = mainFolder.getId();
      
      var subCategories = folderStructure[mainCategory];
      var subcategoryIds = {};
      
      for (var i = 0; i < subCategories.length; i++) {
        var subCategory = subCategories[i];
        var subFolder = findOrCreateFolder(mainFolder, subCategory);
        subcategoryIds[subCategory] = subFolder.getId();
        totalSubfoldersCreated++;
      }
      
      subfolderIds[mainCategory + "_subcategories"] = subcategoryIds;
    }
    
    return createJsonResponse(true, "Complete folder structure created: " + shipName, {
      ship_folder_id: shipFolder.getId(),
      ship_folder_name: shipFolder.getName(),
      subfolder_ids: subfolderIds,
      categories_created: Object.keys(folderStructure).length,
      total_subfolders_created: totalSubfoldersCreated,
      structure_type: "homepage_sidebar_compliant",
      company_id: companyId
    });
    
  } catch (error) {
    return createJsonResponse(false, "Folder creation failed: " + error.toString());
  }
}

function handleUploadFileWithFolderCreation(requestData) {
  try {
    var shipName = requestData.ship_name;
    var category = requestData.category;
    var filename = requestData.filename;
    var fileContent = requestData.file_content;
    var contentType = requestData.content_type || 'application/pdf';
    var parentFolderId = requestData.parent_folder_id;
    
    if (!shipName || !category || !filename || !fileContent) {
      return createJsonResponse(false, "Missing required parameters: ship_name, category, filename, file_content");
    }
    
    if (!parentFolderId) {
      return createJsonResponse(false, "Parent folder ID not available");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findFolderByName(parentFolder, shipName);
    
    if (!shipFolder) {
      return createJsonResponse(false, "Ship folder '" + shipName + "' not found. Please create ship first.");
    }
    
    // Categories under Document Portfolio
    var documentPortfolioCategories = [
      "Certificates", "Inspection Records", "Survey Reports", 
      "Drawings & Manuals", "Other Documents"
    ];
    
    var parentCategoryFolder;
    var folderPath;
    
    if (documentPortfolioCategories.indexOf(category) !== -1) {
      // Find Document Portfolio folder
      parentCategoryFolder = findFolderByName(shipFolder, "Document Portfolio");
      if (!parentCategoryFolder) {
        return createJsonResponse(false, "Document Portfolio folder not found in ship '" + shipName + "'");
      }
      folderPath = shipName + "/Document Portfolio/" + category;
    } else {
      // Direct under ship folder
      parentCategoryFolder = shipFolder;
      folderPath = shipName + "/" + category;
    }
    
    // Find target category folder
    var categoryFolder = findFolderByName(parentCategoryFolder, category);
    if (!categoryFolder) {
      return createJsonResponse(false, "Category folder '" + category + "' not found");
    }
    
    // Decode and upload
    var binaryData = Utilities.base64Decode(fileContent);
    var blob = Utilities.newBlob(binaryData, contentType, filename);
    var uploadedFile = categoryFolder.createFile(blob);
    
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
        folder_exists: false,
        ship_name: shipName
      });
    }
    
    var categories = [];
    var subfolders = shipFolder.getFolders();
    while (subfolders.hasNext()) {
      var subfolder = subfolders.next();
      categories.push(subfolder.getName());
    }
    
    return createJsonResponse(true, "Ship folder structure found", {
      folder_exists: true,
      ship_folder_id: shipFolder.getId(),
      ship_name: shipName,
      available_categories: categories,
      subfolder_count: categories.length
    });
    
  } catch (error) {
    return createJsonResponse(false, "Folder check failed: " + error.toString());
  }
}

// Get folder structure for Move functionality
function handleGetFolderStructure(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name || '';
    
    if (!parentFolderId) {
      return createJsonResponse(false, "Missing parent_folder_id parameter");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var folders = [];
    
    if (shipName) {
      // Get specific ship folder structure
      var shipFolder = findFolderByName(parentFolder, shipName);
      
      if (!shipFolder) {
        return createJsonResponse(false, "Ship folder '" + shipName + "' not found", {
          folders: []
        });
      }
      
      // Get all subfolders in the ship folder (main categories)
      var mainFolders = shipFolder.getFolders();
      while (mainFolders.hasNext()) {
        var mainFolder = mainFolders.next();
        var mainFolderName = mainFolder.getName();
        
        // Add main folder
        folders.push({
          folder_id: mainFolder.getId(),
          folder_name: mainFolderName,
          folder_path: shipName + "/" + mainFolderName,
          parent_id: shipFolder.getId(),
          level: 1
        });
        
        // Get subfolders (subcategories)
        var subFolders = mainFolder.getFolders();
        while (subFolders.hasNext()) {
          var subFolder = subFolders.next();
          folders.push({
            folder_id: subFolder.getId(),
            folder_name: subFolder.getName(),
            folder_path: shipName + "/" + mainFolderName + "/" + subFolder.getName(),
            parent_id: mainFolder.getId(),
            parent_category: mainFolderName,
            level: 2
          });
        }
      }
      
      // Also add the main ship folder as an option
      folders.unshift({
        folder_id: shipFolder.getId(),
        folder_name: shipName + " (Main)",
        folder_path: shipName,
        parent_id: parentFolderId,
        level: 0
      });
      
    } else {
      // Get all ship folders
      var allShipFolders = parentFolder.getFolders();
      while (allShipFolders.hasNext()) {
        var shipFolder = allShipFolders.next();
        var shipFolderName = shipFolder.getName();
        
        folders.push({
          folder_id: shipFolder.getId(),
          folder_name: shipFolderName,
          folder_path: shipFolderName,
          parent_id: parentFolderId,
          level: 0
        });
      }
    }
    
    return createJsonResponse(true, "Folder structure retrieved successfully", {
      folders: folders,
      total_count: folders.length,
      ship_name: shipName
    });
    
  } catch (error) {
    return createJsonResponse(false, "Error getting folder structure: " + error.toString(), {
      folders: []
    });
  }
}

// Move file between folders
function handleMoveFile(requestData) {
  try {
    var fileId = requestData.file_id;
    var targetFolderId = requestData.target_folder_id;
    
    if (!fileId || !targetFolderId) {
      return createJsonResponse(false, "Missing required parameters: file_id and target_folder_id");
    }
    
    // Get the file and target folder
    var file = DriveApp.getFileById(fileId);
    var targetFolder = DriveApp.getFolderById(targetFolderId);
    
    // Get current parent folders
    var currentParents = file.getParents();
    var originalFolderNames = [];
    
    // Remove file from all current parent folders
    while (currentParents.hasNext()) {
      var currentParent = currentParents.next();
      originalFolderNames.push(currentParent.getName());
      currentParent.removeFile(file);
    }
    
    // Add file to target folder
    targetFolder.addFile(file);
    
    return createJsonResponse(true, "File moved successfully", {
      file_id: fileId,
      file_name: file.getName(),
      target_folder_id: targetFolderId,
      target_folder_name: targetFolder.getName(),
      original_folders: originalFolderNames,
      moved_timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    return createJsonResponse(false, "Error moving file: " + error.toString(), {
      file_id: fileId,
      target_folder_id: targetFolderId
    });
  }
}

// NEW FUNCTION: Delete file from Google Drive
function handleDeleteFile(requestData) {
  try {
    var fileId = requestData.file_id;
    var permanentDelete = requestData.permanent_delete || false; // Default to moving to trash
    
    if (!fileId) {
      return createJsonResponse(false, "Missing required parameter: file_id");
    }
    
    // Get the file
    var file = DriveApp.getFileById(fileId);
    var fileName = file.getName();
    var fileSize = file.getSize();
    
    // Get parent folder information before deletion
    var parentFolders = [];
    var parents = file.getParents();
    while (parents.hasNext()) {
      var parent = parents.next();
      parentFolders.push({
        folder_id: parent.getId(),
        folder_name: parent.getName()
      });
    }
    
    if (permanentDelete) {
      // Permanently delete the file
      DriveApp.removeFile(file);
      var deleteMethod = "permanently_deleted";
    } else {
      // Move to trash (default behavior)
      file.setTrashed(true);
      var deleteMethod = "moved_to_trash";
    }
    
    return createJsonResponse(true, "File deleted successfully: " + fileName, {
      file_id: fileId,
      file_name: fileName,
      file_size: fileSize,
      delete_method: deleteMethod,
      parent_folders: parentFolders,
      deleted_timestamp: new Date().toISOString(),
      note: permanentDelete ? "File permanently deleted" : "File moved to trash (can be restored)"
    });
    
  } catch (error) {
    // Handle specific error cases
    if (error.toString().indexOf("File not found") !== -1) {
      return createJsonResponse(false, "File not found: " + fileId + " (may already be deleted)", {
        file_id: fileId,
        error_type: "file_not_found"
      });
    } else if (error.toString().indexOf("Permission denied") !== -1) {
      return createJsonResponse(false, "Permission denied: Cannot delete file " + fileId, {
        file_id: fileId,
        error_type: "permission_denied"
      });
    } else {
      return createJsonResponse(false, "Error deleting file: " + error.toString(), {
        file_id: fileId,
        error_type: "general_error"
      });
    }
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