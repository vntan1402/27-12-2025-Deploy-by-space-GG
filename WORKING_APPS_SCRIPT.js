/**
 * Ship Management System - Working Google Apps Script
 * Deploy this as Web App with "Execute as: Me" and "Anyone" access
 */

function doPost(e) {
  return handleRequest(e);
}

function doGet(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  try {
    // Parse request data
    let requestData = {};
    
    if (e && e.postData && e.postData.contents) {
      try {
        requestData = JSON.parse(e.postData.contents);
      } catch (parseError) {
        return createJsonResponse(false, `Invalid JSON: ${parseError.toString()}`);
      }
    } else if (e && e.parameter) {
      requestData = e.parameter;
    } else {
      // Default response - this proves the script is working
      return createJsonResponse(true, "Ship Management Apps Script is WORKING!", {
        version: "2.0-dynamic-only",
        timestamp: new Date().toISOString(),
        supported_actions: ["test_connection", "create_complete_ship_structure", "upload_file_with_folder_creation"]
      });
    }
    
    const action = requestData.action || "default";
    
    // Handle different actions
    switch (action) {
      case 'test_connection':
        return handleTestConnection(requestData);
        
      case 'create_complete_ship_structure':
        return handleCreateCompleteShipStructure(requestData);
        
      case 'upload_file_with_folder_creation':
        return handleUploadFileWithFolderCreation(requestData);
        
      default:
        return createJsonResponse(true, "Apps Script working - no action specified", {
          received_action: action,
          available_actions: ["test_connection", "create_complete_ship_structure", "upload_file_with_folder_creation"]
        });
    }
    
  } catch (error) {
    return createJsonResponse(false, `Error: ${error.toString()}`);
  }
}

/**
 * Create JSON response
 */
function createJsonResponse(success, message, data = null) {
  const response = {
    success: success,
    message: message,
    timestamp: new Date().toISOString()
  };
  
  if (data) {
    Object.assign(response, data);
  }
  
  return ContentService
    .createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Test Google Drive connection
 */
function handleTestConnection(requestData) {
  try {
    const folderId = requestData.folder_id;
    
    if (!folderId) {
      return createJsonResponse(false, "folder_id is required for test_connection");
    }
    
    // Test access to the folder
    const folder = DriveApp.getFolderById(folderId);
    const folderName = folder.getName();
    
    return createJsonResponse(true, "Google Drive connection successful!", {
      folder_name: folderName,
      folder_id: folderId,
      drive_access: true,
      test_result: "PASSED"
    });
    
  } catch (error) {
    return createJsonResponse(false, `Connection test failed: ${error.toString()}`);
  }
}

/**
 * Create complete dynamic ship folder structure
 */
function handleCreateCompleteShipStructure(requestData) {
  try {
    const parentFolderId = requestData.parent_folder_id || requestData.folder_id;
    const shipName = requestData.ship_name || requestData.folder_path;
    const companyId = requestData.company_id;
    
    if (!parentFolderId) {
      return createJsonResponse(false, "parent_folder_id is required");
    }
    
    if (!shipName) {
      return createJsonResponse(false, "ship_name is required");
    }
    
    const parentFolder = DriveApp.getFolderById(parentFolderId);
    
    // Create ship folder
    let shipFolder = findOrCreateFolder(parentFolder, shipName);
    
    // Dynamic folder structure from homepage sidebar
    const folderStructure = {
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
    
    const subfolderIds = {};
    let totalSubfoldersCreated = 0;
    
    // Create main categories and their subfolders
    for (const [categoryName, subfolders] of Object.entries(folderStructure)) {
      try {
        // Create main category folder
        const categoryFolder = findOrCreateFolder(shipFolder, categoryName);
        subfolderIds[categoryName] = categoryFolder.getId();
        
        // Create subfolders within category
        const categorySubfolders = {};
        for (const subfolderName of subfolders) {
          try {
            const subfolder = findOrCreateFolder(categoryFolder, subfolderName);
            categorySubfolders[subfolderName] = subfolder.getId();
            totalSubfoldersCreated++;
          } catch (e) {
            console.error(`Error creating subfolder ${subfolderName} in ${categoryName}:`, e);
          }
        }
        
        // Store subfolder structure
        subfolderIds[`${categoryName}_subfolders`] = categorySubfolders;
        
      } catch (e) {
        console.error(`Error creating category ${categoryName}:`, e);
      }
    }
    
    return createJsonResponse(true, `Complete folder structure created: ${shipName}`, {
      ship_folder_id: shipFolder.getId(),
      ship_folder_name: shipFolder.getName(),
      subfolder_ids: subfolderIds,
      categories_created: Object.keys(folderStructure).length,
      total_subfolders_created: totalSubfoldersCreated,
      structure_type: "dynamic",
      company_id: companyId
    });
    
  } catch (error) {
    return createJsonResponse(false, `Dynamic folder creation failed: ${error.toString()}`);
  }
}

/**
 * Upload file
 */
function handleUploadFile(requestData) {
  try {
    const folderId = requestData.folder_id;
    const fileName = requestData.file_name;
    const fileContent = requestData.file_content; // base64
    const mimeType = requestData.mime_type || 'application/octet-stream';
    
    if (!folderId || !fileName || !fileContent) {
      return createJsonResponse(false, "folder_id, file_name, and file_content are required");
    }
    
    const folder = DriveApp.getFolderById(folderId);
    
    // Decode base64 and create file
    const bytes = Utilities.base64Decode(fileContent);
    const blob = Utilities.newBlob(bytes, mimeType, fileName);
    
    // Handle duplicates by adding timestamp
    let finalFileName = fileName;
    const existingFiles = folder.getFilesByName(fileName);
    
    if (existingFiles.hasNext()) {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const nameParts = fileName.split('.');
      
      if (nameParts.length > 1) {
        const extension = nameParts.pop();
        finalFileName = `${nameParts.join('.')}_${timestamp}.${extension}`;
      } else {
        finalFileName = `${fileName}_${timestamp}`;
      }
      
      blob.setName(finalFileName);
    }
    
    const file = folder.createFile(blob);
    
    return createJsonResponse(true, `File uploaded: ${finalFileName}`, {
      file_id: file.getId(),
      file_name: finalFileName,
      file_url: file.getUrl(),
      file_size: bytes.length,
      folder_id: folderId
    });
    
  } catch (error) {
    return createJsonResponse(false, `File upload failed: ${error.toString()}`);
  }
}

/**
 * Helper: Find or create folder
 */
function findOrCreateFolder(parentFolder, folderName) {
  const existingFolders = parentFolder.getFoldersByName(folderName);
  
  if (existingFolders.hasNext()) {
    return existingFolders.next();
  } else {
    return parentFolder.createFolder(folderName);
  }
}