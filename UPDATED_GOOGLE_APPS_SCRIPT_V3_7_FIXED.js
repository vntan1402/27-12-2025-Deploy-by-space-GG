/**
 * Ship Management System - Fixed Apps Script v3.7 - FOLDER PATH FIXED VERSION
 * With Updated Fallback Structure Matching Backend + RENAME FILE Support + MULTI CERT UPLOAD FIX
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
      return createJsonResponse(true, "Ship Management Apps Script v3.7-FIXED is WORKING!", {
        version: "3.7-fixed-folder-path-multi-cert",
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
        ],
        fixes: [
          "FIXED: Multi Certificate upload folder path - now supports Class & Flag Cert structure",
          "FIXED: Added createNestedFolders function for proper hierarchy creation",  
          "FIXED: Updated fallback structure to match backend sidebar (Class & Flag Cert)",
          "FIXED: Support for parent_category parameter in upload_file_with_folder_creation",
          "Enhanced Google Drive permission error diagnosis",
          "Added rename_file action support"
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
        return createJsonResponse(true, "Apps Script working - no action specified", {
          received_action: action,
          available_actions: [
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

// NEW: Handle rename file action
function handleRenameFile(requestData) {
  try {
    var fileId = requestData.file_id;
    var newName = requestData.new_name;
    
    if (!fileId || !newName) {
      return createJsonResponse(false, "Missing required parameters: file_id and new_name");
    }
    
    Logger.log("🔄 Renaming file " + fileId + " to '" + newName + "'");
    
    // Validate and get file with proper error handling
    var file;
    try {
      file = DriveApp.getFileById(fileId);
    } catch (fileError) {
      Logger.log("❌ File access error: " + fileError.toString());
      return createJsonResponse(false, "File not found or access denied: " + fileId + ". Error: " + fileError.toString(), {
        file_id: fileId,
        error_type: "file_access_error"
      });
    }
    
    // Get original filename for logging
    var originalName = file.getName();
    
    // Perform the rename operation
    try {
      file.setName(newName);
      
      Logger.log("✅ File renamed successfully from '" + originalName + "' to '" + newName + "'");
      
      return createJsonResponse(true, "File renamed successfully", {
        file_id: fileId,
        old_name: originalName,
        new_name: newName,
        renamed_timestamp: new Date().toISOString()
      });
      
    } catch (renameError) {
      Logger.log("❌ Rename operation error: " + renameError.toString());
      return createJsonResponse(false, "Failed to rename file: " + renameError.toString(), {
        file_id: fileId,
        old_name: originalName,
        new_name: newName,
        error_type: "rename_operation_error"
      });
    }
    
  } catch (error) {
    Logger.log("❌ General rename error: " + error.toString());
    return createJsonResponse(false, "Error renaming file: " + error.toString(), {
      file_id: fileId || "unknown",
      new_name: newName || "unknown",
      error_type: "general_error"
    });
  }
}

function handleTestConnection(requestData) {
  try {
    var folderId = requestData.folder_id;
    
    if (!folderId) {
      return createJsonResponse(false, "Missing folder_id parameter");
    }
    
    // Test Google Drive access with detailed error reporting
    try {
      var folder = DriveApp.getFolderById(folderId);
      var folderName = folder.getName();
      
      return createJsonResponse(true, "Connection successful", {
        folder_name: folderName,
        folder_id: folderId,
        test_result: "PASSED",
        google_drive_access: "OK"
      });
    } catch (driveError) {
      Logger.log("Google Drive access error: " + driveError.toString());
      return createJsonResponse(false, "Google Drive access failed: " + driveError.toString(), {
        folder_id: folderId,
        error_type: "google_drive_permission",
        suggestion: "Please check Apps Script permissions for Google Drive access"
      });
    }
    
  } catch (error) {
    Logger.log("Test connection error: " + error.toString());
    return createJsonResponse(false, "Connection test failed: " + error.toString());
  }
}

function handleCreateCompleteShipStructure(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    var companyId = requestData.company_id;
    var backendApiUrl = requestData.backend_api_url;
    
    if (!parentFolderId || !shipName) {
      return createJsonResponse(false, "Missing required parameters: parent_folder_id, ship_name");
    }
    
    Logger.log("🚢 Creating ship structure for: " + shipName);
    Logger.log("📁 Parent folder ID: " + parentFolderId);
    Logger.log("🌐 Backend API URL: " + (backendApiUrl || "NOT PROVIDED"));
    
    // Test Google Drive access first
    try {
      var parentFolder = DriveApp.getFolderById(parentFolderId);
      Logger.log("✅ Google Drive access OK - Parent folder: " + parentFolder.getName());
    } catch (driveError) {
      Logger.log("❌ Google Drive access failed: " + driveError.toString());
      return createJsonResponse(false, "Google Drive permission error: " + driveError.toString(), {
        error_type: "google_drive_permission",
        suggestion: "Please check Apps Script permissions for Google Drive access",
        parent_folder_id: parentFolderId
      });
    }
    
    var shipFolder = findOrCreateFolder(parentFolder, shipName);
    
    // Get dynamic folder structure from backend if available
    var folderStructure;
    var structureSource;
    var structureMetadata = {};
    
    if (backendApiUrl) {
      Logger.log("🔄 Attempting to fetch dynamic folder structure from backend...");
      var dynamicResult = getDynamicFolderStructure(backendApiUrl);
      
      if (dynamicResult.success) {
        folderStructure = dynamicResult.structure;
        structureSource = "dynamic_from_homepage_sidebar";
        structureMetadata = dynamicResult.metadata || {};
        Logger.log("✅ Using dynamic folder structure from Homepage Sidebar");
        Logger.log("📊 Dynamic structure categories: " + Object.keys(folderStructure).join(", "));
      } else {
        Logger.log("⚠️ Dynamic structure fetch failed: " + dynamicResult.error);
        Logger.log("🔄 Falling back to updated cached structure...");
        var fallbackResult = getFallbackFolderStructure();
        folderStructure = fallbackResult.structure;
        structureSource = "fallback_updated_cached";
        structureMetadata.fallback_reason = dynamicResult.error;
        Logger.log("📊 Fallback structure categories: " + Object.keys(folderStructure).join(", "));
      }
    } else {
      Logger.log("⚠️ No backend_api_url provided, using updated fallback structure");
      var fallbackResult = getFallbackFolderStructure();
      folderStructure = fallbackResult.structure;
      structureSource = "fallback_no_api_url";
      Logger.log("📊 No API fallback structure categories: " + Object.keys(folderStructure).join(", "));
    }
    
    // Create folder structure
    var subfolderIds = {};
    var totalSubfoldersCreated = 0;
    var createdCategories = [];
    
    for (var mainCategory in folderStructure) {
      Logger.log("📁 Creating main category: " + mainCategory);
      var mainFolder = findOrCreateFolder(shipFolder, mainCategory);
      subfolderIds[mainCategory] = mainFolder.getId();
      createdCategories.push(mainCategory);
      
      var subCategories = folderStructure[mainCategory];
      var subcategoryIds = {};
      
      for (var i = 0; i < subCategories.length; i++) {
        var subCategory = subCategories[i];
        Logger.log("📂 Creating subcategory: " + mainCategory + " > " + subCategory);
        var subFolder = findOrCreateFolder(mainFolder, subCategory);
        subcategoryIds[subCategory] = subFolder.getId();
        totalSubfoldersCreated++;
      }
      
      subfolderIds[mainCategory + "_subcategories"] = subcategoryIds;
    }
    
    Logger.log("✅ Folder structure creation completed");
    Logger.log("📊 Created " + createdCategories.length + " main categories");
    Logger.log("📊 Created " + totalSubfoldersCreated + " subcategories");
    
    return createJsonResponse(true, "Complete folder structure created: " + shipName, {
      ship_folder_id: shipFolder.getId(),
      ship_folder_name: shipFolder.getName(),
      subfolder_ids: subfolderIds,
      categories_created: createdCategories,
      total_categories: createdCategories.length,
      total_subfolders_created: totalSubfoldersCreated,
      structure_source: structureSource,
      structure_metadata: structureMetadata,
      company_id: companyId,
      backend_api_used: !!backendApiUrl,
      creation_timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    Logger.log("❌ Create ship structure error: " + error.toString());
    return createJsonResponse(false, "Folder creation failed: " + error.toString());
  }
}

/**
 * Get dynamic folder structure from backend API - Enhanced with better error handling
 */
function getDynamicFolderStructure(backendApiUrl) {
  try {
    var apiUrl = backendApiUrl + "/api/sidebar-structure";
    Logger.log("📡 Fetching dynamic folder structure from: " + apiUrl);
    
    var response = UrlFetchApp.fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      muteHttpExceptions: true,
      timeout: 15 // Reduced timeout to fail faster
    });
    
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();
    
    Logger.log("📡 API Response Code: " + responseCode);
    
    if (responseCode === 200) {
      var result = JSON.parse(responseText);
      
      if (result.success && result.structure) {
        Logger.log("✅ Successfully fetched dynamic folder structure");
        Logger.log("📊 Received structure with " + Object.keys(result.structure).length + " categories");
        
        // Log specific folder names to verify they're updated
        if (result.structure["Class & Flag Cert"]) {
          Logger.log("📋 Class & Flag Cert subcategories: " + result.structure["Class & Flag Cert"].join(", "));
        }
        
        return {
          success: true,
          structure: result.structure,
          metadata: result.metadata,
          source: "dynamic_api"
        };
      } else {
        Logger.log("❌ API returned success=false: " + (result.message || "Unknown error"));
        return { success: false, error: result.message || "Invalid API response" };
      }
    } else {
      Logger.log("❌ API call failed with status: " + responseCode);
      Logger.log("❌ Response body: " + responseText);
      return { success: false, error: "API call failed: HTTP " + responseCode };
    }
    
  } catch (error) {
    Logger.log("❌ Error fetching dynamic structure: " + error.toString());
    return { success: false, error: error.toString() };
  }
}

/**
 * FIXED: Get fallback folder structure - NOW USES "Class & Flag Cert" instead of "Document Portfolio"
 */
function getFallbackFolderStructure() {
  Logger.log("📋 Using FIXED fallback folder structure (Class & Flag Cert instead of Document Portfolio)");
  
  return {
    success: true,
    structure: {
      "Class & Flag Cert": [              // FIXED: Changed from "Document Portfolio"
        "Certificates",
        "Class Survey Report",             // UPDATED: was "Inspection Records"
        "Test Report",                     // UPDATED: was "Survey Reports" 
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
    },
    source: "fallback_fixed_class_flag_cert",
    version: "v3.7_fixed_folder_path_multi_cert"
  };
}

/**
 * FIXED: Upload file with proper nested folder creation support
 * Now supports parent_category parameter for Multi Certificate uploads
 */
function handleUploadFileWithFolderCreation(requestData) {
  try {
    var shipName = requestData.ship_name;
    var parentCategory = requestData.parent_category;  // NEW: Main category (e.g., "Class & Flag Cert")
    var category = requestData.category;               // Sub-folder (e.g., "Certificates")
    var filename = requestData.filename;
    var fileContent = requestData.file_content;
    var contentType = requestData.content_type || 'application/pdf';
    var parentFolderId = requestData.parent_folder_id;
    
    Logger.log("🚢 Upload request - Ship: " + shipName + ", Parent Category: " + parentCategory + ", Category: " + category + ", File: " + filename);
    
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
    
    // FIXED: Categories under Class & Flag Cert with new names
    var classFlagCertCategories = [
      "Certificates", 
      "Class Survey Report",    // UPDATED: was "Inspection Records" 
      "Test Report",           // UPDATED: was "Survey Reports"
      "Drawings & Manuals", 
      "Other Documents"
    ];
    
    var targetFolder;
    var folderPath;
    
    // NEW: Use parent_category if provided to create nested folder structure
    if (parentCategory) {
      Logger.log("📁 Using parent_category approach: " + parentCategory + " > " + category);
      // Create nested folder path: parentCategory -> category
      var folderHierarchy = [parentCategory, category];
      targetFolder = createNestedFolders(shipFolder, folderHierarchy);
      if (!targetFolder) {
        return createJsonResponse(false, "Failed to create nested folder structure: " + parentCategory + "/" + category + " in ship '" + shipName + "'");
      }
      folderPath = shipName + "/" + parentCategory + "/" + category;
      Logger.log("✅ Created/found nested folder path: " + folderPath);
    } else if (classFlagCertCategories.indexOf(category) !== -1) {
      Logger.log("📁 Using fallback logic for Class & Flag Cert category: " + category);
      // Fallback to old logic for backward compatibility - but use "Class & Flag Cert"
      var parentCategoryFolder = findFolderByName(shipFolder, "Class & Flag Cert");
      if (!parentCategoryFolder) {
        return createJsonResponse(false, "Class & Flag Cert folder not found in ship '" + shipName + "'");
      }
      targetFolder = findFolderByName(parentCategoryFolder, category);
      if (!targetFolder) {
        return createJsonResponse(false, "Category folder '" + category + "' not found in Class & Flag Cert");
      }
      folderPath = shipName + "/Class & Flag Cert/" + category;
    } else {
      Logger.log("📁 Using direct ship folder approach for category: " + category);
      // Direct under ship folder
      targetFolder = findFolderByName(shipFolder, category);
      if (!targetFolder) {
        return createJsonResponse(false, "Category folder '" + category + "' not found");
      }
      folderPath = shipName + "/" + category;
    }
    
    // Upload file to target folder
    Logger.log("📤 Uploading file to: " + folderPath);
    var binaryData = Utilities.base64Decode(fileContent);
    var blob = Utilities.newBlob(binaryData, contentType, filename);
    var uploadedFile = targetFolder.createFile(blob);
    
    Logger.log("✅ File uploaded successfully: " + uploadedFile.getName() + " (ID: " + uploadedFile.getId() + ")");
    
    return createJsonResponse(true, "File uploaded successfully: " + filename, {
      file_id: uploadedFile.getId(),
      file_name: uploadedFile.getName(),
      file_url: uploadedFile.getUrl(),
      folder_path: folderPath,
      upload_timestamp: new Date().toISOString(),
      parent_category_used: parentCategory || null,
      nested_folder_creation: !!parentCategory
    });
    
  } catch (error) {
    Logger.log("❌ Upload file error: " + error.toString());
    return createJsonResponse(false, "File upload failed: " + error.toString());
  }
}

/**
 * NEW: Create nested folder hierarchy from array of folder names
 * This function supports the Multi Certificate upload fix
 */
function createNestedFolders(parentFolder, folderNames) {
  try {
    Logger.log("📁 Creating nested folder hierarchy: " + folderNames.join(" > "));
    var currentFolder = parentFolder;
    
    for (var i = 0; i < folderNames.length; i++) {
      var folderName = folderNames[i];
      
      // Check if folder already exists
      var folders = currentFolder.getFoldersByName(folderName);
      if (folders.hasNext()) {
        // Folder exists, use it
        currentFolder = folders.next();
        Logger.log("✅ Found existing folder: " + folderName);
      } else {
        // Create new folder
        currentFolder = currentFolder.createFolder(folderName);
        Logger.log("✅ Created new folder: " + folderName);
      }
    }
    
    Logger.log("✅ Nested folder creation completed. Final folder: " + currentFolder.getName());
    return currentFolder;
  } catch (error) {
    Logger.log("❌ Error creating nested folders: " + error.toString());
    return null;
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
    Logger.log("Check ship folder error: " + error.toString());
    return createJsonResponse(false, "Folder check failed: " + error.toString());
  }
}

// OPTIMIZED: Get folder structure for Move functionality
function handleGetFolderStructure(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name || '';
    
    if (!parentFolderId) {
      return createJsonResponse(false, "Missing parent_folder_id parameter");
    }
    
    Logger.log("📁 Getting folder structure for parent: " + parentFolderId + ", ship: " + shipName);
    
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
      
      // Add main ship folder
      folders.push({
        folder_id: shipFolder.getId(),
        folder_name: shipName + " (Main)",
        folder_path: shipName,
        parent_id: parentFolderId,
        level: 0
      });
      
      // Get main categories (limited to prevent timeout)
      var mainFolders = shipFolder.getFolders();
      var categoryCount = 0;
      var maxCategories = 10; // Limit to prevent timeout
      
      while (mainFolders.hasNext() && categoryCount < maxCategories) {
        var mainFolder = mainFolders.next();
        var mainFolderName = mainFolder.getName();
        
        folders.push({
          folder_id: mainFolder.getId(),
          folder_name: mainFolderName,
          folder_path: shipName + "/" + mainFolderName,
          parent_id: shipFolder.getId(),
          level: 1
        });
        
        // Get subcategories (limited)
        var subFolders = mainFolder.getFolders();
        var subCount = 0;
        var maxSubCategories = 5; // Limit subcategories
        
        while (subFolders.hasNext() && subCount < maxSubCategories) {
          var subFolder = subFolders.next();
          folders.push({
            folder_id: subFolder.getId(),
            folder_name: subFolder.getName(),
            folder_path: shipName + "/" + mainFolderName + "/" + subFolder.getName(),
            parent_id: mainFolder.getId(),
            parent_category: mainFolderName,
            level: 2
          });
          subCount++;
        }
        categoryCount++;
      }
    }
    
    Logger.log("✅ Found " + folders.length + " folders");
    return createJsonResponse(true, "Folder structure retrieved successfully", {
      folders: folders,
      total_count: folders.length,
      ship_name: shipName
    });
    
  } catch (error) {
    Logger.log("Get folder structure error: " + error.toString());
    return createJsonResponse(false, "Error getting folder structure: " + error.toString(), {
      folders: []
    });
  }
}

// FIXED: Move file between folders with proper error handling
function handleMoveFile(requestData) {
  try {
    var fileId = requestData.file_id;
    var targetFolderId = requestData.target_folder_id;
    
    if (!fileId || !targetFolderId) {
      return createJsonResponse(false, "Missing required parameters: file_id and target_folder_id");
    }
    
    Logger.log("📁 Moving file " + fileId + " to folder " + targetFolderId);
    
    // Validate and get file with proper error handling
    var file;
    try {
      file = DriveApp.getFileById(fileId);
    } catch (fileError) {
      Logger.log("❌ File access error: " + fileError.toString());
      return createJsonResponse(false, "File not found or access denied: " + fileId + ". Error: " + fileError.toString(), {
        file_id: fileId,
        error_type: "file_access_error"
      });
    }
    
    // Validate and get target folder with proper error handling
    var targetFolder;
    try {
      targetFolder = DriveApp.getFolderById(targetFolderId);
    } catch (folderError) {
      Logger.log("❌ Target folder access error: " + folderError.toString());
      return createJsonResponse(false, "Target folder not found or access denied: " + targetFolderId + ". Error: " + folderError.toString(), {
        target_folder_id: targetFolderId,
        error_type: "folder_access_error"
      });
    }
    
    // Get current parent folders for logging
    var currentParents = file.getParents();
    var originalFolderNames = [];
    
    while (currentParents.hasNext()) {
      var currentParent = currentParents.next();
      originalFolderNames.push(currentParent.getName());
    }
    
    // Perform the move operation
    try {
      // Remove from current parents
      var parents = file.getParents();
      while (parents.hasNext()) {
        var parent = parents.next();
        parent.removeFile(file);
      }
      
      // Add to target folder
      targetFolder.addFile(file);
      
      Logger.log("✅ File moved successfully to: " + targetFolder.getName());
      
      return createJsonResponse(true, "File moved successfully", {
        file_id: fileId,
        file_name: file.getName(),
        target_folder_id: targetFolderId,
        target_folder_name: targetFolder.getName(),
        original_folders: originalFolderNames,
        moved_timestamp: new Date().toISOString()
      });
      
    } catch (moveError) {
      Logger.log("❌ Move operation error: " + moveError.toString());
      return createJsonResponse(false, "Failed to move file: " + moveError.toString(), {
        file_id: fileId,
        target_folder_id: targetFolderId,
        error_type: "move_operation_error"
      });
    }
    
  } catch (error) {
    Logger.log("❌ General move error: " + error.toString());
    return createJsonResponse(false, "Error moving file: " + error.toString(), {
      file_id: fileId || "unknown",
      target_folder_id: targetFolderId || "unknown",
      error_type: "general_error"
    });
  }
}

// FIXED: Delete file from Google Drive with proper error handling
function handleDeleteFile(requestData) {
  try {
    var fileId = requestData.file_id;
    var permanentDelete = requestData.permanent_delete || false;
    
    if (!fileId) {
      return createJsonResponse(false, "Missing required parameter: file_id");
    }
    
    Logger.log("🗑️ Deleting file " + fileId + " (permanent: " + permanentDelete + ")");
    
    // Validate and get file with proper error handling
    var file;
    try {
      file = DriveApp.getFileById(fileId);
    } catch (fileError) {
      Logger.log("❌ File access error: " + fileError.toString());
      // Check if this is a "not found" error
      if (fileError.toString().indexOf("not found") !== -1 || 
          fileError.toString().indexOf("does not exist") !== -1) {
        return createJsonResponse(false, "File not found: " + fileId + " (may already be deleted)", {
          file_id: fileId,
          error_type: "file_not_found"
        });
      } else {
        return createJsonResponse(false, "Permission denied: Cannot access file " + fileId + ". Error: " + fileError.toString(), {
          file_id: fileId,
          error_type: "permission_denied"
        });
      }
    }
    
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
    
    // Perform deletion
    var deleteMethod;
    try {
      if (permanentDelete) {
        DriveApp.removeFile(file);
        deleteMethod = "permanently_deleted";
      } else {
        file.setTrashed(true);
        deleteMethod = "moved_to_trash";
      }
      
      Logger.log("✅ File deleted successfully: " + fileName);
      
      return createJsonResponse(true, "File deleted successfully: " + fileName, {
        file_id: fileId,
        file_name: fileName,
        file_size: fileSize,
        delete_method: deleteMethod,
        parent_folders: parentFolders,
        deleted_timestamp: new Date().toISOString(),
        note: permanentDelete ? "File permanently deleted" : "File moved to trash (can be restored)"
      });
      
    } catch (deleteError) {
      Logger.log("❌ Delete operation error: " + deleteError.toString());
      return createJsonResponse(false, "Failed to delete file: " + deleteError.toString(), {
        file_id: fileId,
        error_type: "delete_operation_error"
      });
    }
    
  } catch (error) {
    Logger.log("❌ General delete error: " + error.toString());
    return createJsonResponse(false, "Error deleting file: " + error.toString(), {
      file_id: fileId || "unknown",
      error_type: "general_error"
    });
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