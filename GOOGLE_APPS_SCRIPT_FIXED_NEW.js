/**
 * Ship Management System - Google Apps Script for Multi-File Upload
 * Version: 2.0 - Fixed and Compatible
 * 
 * This script handles:
 * - Multi-file upload with AI classification
 * - Ship folder structure creation: Ship Name -> 5 category subfolders
 * - File organization by categories
 * - Proper error handling and JSON responses
 * 
 * Supported Actions:
 * - test_connection: Test Google Drive access
 * - create_folder_structure: Create ship folder + 5 category subfolders
 * - upload_file: Upload files to specific category folders
 * - list_files: List files in folders
 * - sync_to_drive: Legacy sync support
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
    let requestData;
    
    if (e && e.postData && e.postData.contents) {
      try {
        requestData = JSON.parse(e.postData.contents);
      } catch (parseError) {
        return createJsonResponse(false, `Invalid JSON: ${parseError.toString()}`);
      }
    } else if (e && e.parameter) {
      requestData = e.parameter;
    } else {
      return createJsonResponse(true, "Ship Management Google Apps Script API is running", {
        supported_actions: [
          'test_connection',
          'create_folder_structure', 
          'upload_file',
          'list_files',
          'sync_to_drive'
        ],
        version: '2.0'
      });
    }
    
    const action = requestData.action;
    
    // Route to appropriate handler
    switch (action) {
      case 'test_connection':
        return handleTestConnection(requestData);
        
      case 'create_folder_structure':
        return handleCreateFolderStructure(requestData);
        
      case 'upload_file':
        return handleUploadFile(requestData);
        
      case 'list_files':
        return handleListFiles(requestData);
        
      case 'get_file_view_url':
        return handleGetFileViewUrl(requestData);
        
      case 'sync_to_drive':
        return handleSyncToDrive(requestData);
        
      default:
        return createJsonResponse(false, `Unsupported action: ${action}`);
    }
    
  } catch (error) {
    console.error('Main handler error:', error);
    return createJsonResponse(false, `Server error: ${error.toString()}`);
  }
}

/**
 * Create proper JSON response
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
    
    return createJsonResponse(true, "Connection successful", {
      folder_name: folderName,
      folder_id: folderId,
      drive_access: true
    });
    
  } catch (error) {
    return createJsonResponse(false, `Connection test failed: ${error.toString()}`);
  }
}

/**
 * Create ship folder structure: Ship Name -> 5 category subfolders
 */
function handleCreateFolderStructure(requestData) {
  try {
    const parentFolderId = requestData.parent_folder_id || requestData.folder_id;
    const folderPath = requestData.folder_path;
    const shipName = requestData.ship_name;
    
    if (!parentFolderId) {
      return createJsonResponse(false, "parent_folder_id or folder_id is required");
    }
    
    // Use ship_name or folder_path
    const targetFolderName = shipName || folderPath;
    
    if (!targetFolderName) {
      return createJsonResponse(false, "ship_name or folder_path is required");
    }
    
    const parentFolder = DriveApp.getFolderById(parentFolderId);
    
    // Create main ship folder if it doesn't exist
    let shipFolder = findOrCreateFolder(parentFolder, targetFolderName);
    
    // Create 5 category subfolders
    const categories = [
      "Certificates",
      "Test Reports", 
      "Survey Reports",
      "Drawings & Manuals",
      "Other Documents"
    ];
    
    const subfolderIds = {};
    
    for (const category of categories) {
      try {
        const subfolder = findOrCreateFolder(shipFolder, category);
        subfolderIds[category] = subfolder.getId();
      } catch (e) {
        console.error(`Error creating category folder ${category}:`, e);
        // Continue with other folders even if one fails
      }
    }
    
    return createJsonResponse(true, `Ship folder structure created: ${targetFolderName}`, {
      ship_folder_id: shipFolder.getId(),
      ship_folder_name: shipFolder.getName(),
      subfolder_ids: subfolderIds,
      categories_created: Object.keys(subfolderIds).length
    });
    
  } catch (error) {
    return createJsonResponse(false, `Failed to create folder structure: ${error.toString()}`);
  }
}

/**
 * Upload file to specific category folder
 */
function handleUploadFile(requestData) {
  try {
    const folderId = requestData.folder_id;
    const fileName = requestData.file_name;
    const fileContent = requestData.file_content; // base64 encoded
    const mimeType = requestData.mime_type || 'application/octet-stream';
    
    if (!folderId || !fileName || !fileContent) {
      return createJsonResponse(false, "folder_id, file_name, and file_content are required");
    }
    
    // Get target folder
    const folder = DriveApp.getFolderById(folderId);
    
    // Decode base64 content
    const bytes = Utilities.base64Decode(fileContent);
    const blob = Utilities.newBlob(bytes, mimeType, fileName);
    
    // Handle duplicate files by adding timestamp
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
    
    // Create file in folder
    const file = folder.createFile(blob);
    
    return createJsonResponse(true, `File uploaded successfully: ${finalFileName}`, {
      file_id: file.getId(),
      file_name: finalFileName,
      file_url: file.getUrl(),
      file_size: bytes.length,
      folder_id: folderId,
      original_name: fileName
    });
    
  } catch (error) {
    return createJsonResponse(false, `File upload failed: ${error.toString()}`);
  }
}

/**
 * List files in folder
 */
function handleListFiles(requestData) {
  try {
    const folderId = requestData.folder_id;
    
    if (!folderId) {
      return createJsonResponse(false, "folder_id is required");
    }
    
    const folder = DriveApp.getFolderById(folderId);
    const files = folder.getFiles();
    const fileList = [];
    
    while (files.hasNext()) {
      const file = files.next();
      fileList.push({
        id: file.getId(),
        name: file.getName(),
        size: file.getSize(),
        created: file.getDateCreated().toISOString(),
        modified: file.getLastUpdated().toISOString(),
        mimeType: file.getBlob().getContentType(),
        url: file.getUrl()
      });
    }
    
    return createJsonResponse(true, `Found ${fileList.length} files`, {
      files: fileList,
      folder_id: folderId,
      count: fileList.length
    });
    
  } catch (error) {
    return createJsonResponse(false, `List files failed: ${error.toString()}`);
  }
}

/**
 * Legacy sync support
 */
function handleSyncToDrive(requestData) {
  try {
    const folderId = requestData.folder_id;
    const fileName = requestData.file_name;
    const fileContent = requestData.file_content;
    
    if (!folderId || !fileName || !fileContent) {
      return createJsonResponse(false, "folder_id, file_name, and file_content are required");
    }
    
    const folder = DriveApp.getFolderById(folderId);
    
    // Check if file exists
    const existingFiles = folder.getFilesByName(fileName);
    
    if (existingFiles.hasNext()) {
      // Update existing file
      const file = existingFiles.next();
      file.setContent(fileContent);
      
      return createJsonResponse(true, `File updated: ${fileName}`, {
        file_id: file.getId(),
        action: 'updated'
      });
    } else {
      // Create new file
      const file = folder.createFile(fileName, fileContent, 'application/json');
      
      return createJsonResponse(true, `File created: ${fileName}`, {
        file_id: file.getId(),
        action: 'created'
      });
    }
    
  } catch (error) {
    return createJsonResponse(false, `Sync failed: ${error.toString()}`);
  }
}

/**
 * Handle get file view URL request
 */
function handleGetFileViewUrl(requestData) {
  debugLog('Getting file view URL');
  
  try {
    const fileId = requestData.file_id;
    
    if (!fileId) {
      return createJsonResponse(false, 'File ID is required');
    }
    
    // Try to get file by ID
    try {
      const file = DriveApp.getFileById(fileId);
      
      // Generate view URL
      const viewUrl = `https://drive.google.com/file/d/${fileId}/view`;
      
      return createJsonResponse(true, 'File view URL generated', {
        file_id: fileId,
        file_name: file.getName(),
        view_url: viewUrl,
        file_size: file.getSize()
      });
      
    } catch (fileError) {
      // File not found or no access
      return createJsonResponse(false, `File not accessible: ${fileError.toString()}`);
    }
    
  } catch (error) {
    return createJsonResponse(false, `Get file view URL failed: ${error.toString()}`);
  }
}

/**
 * Helper function to find or create folder
 */
function findOrCreateFolder(parentFolder, folderName) {
  // Check if folder already exists
  const existingFolders = parentFolder.getFoldersByName(folderName);
  
  if (existingFolders.hasNext()) {
    return existingFolders.next();
  } else {
    // Create new folder
    return parentFolder.createFolder(folderName);
  }
}

/**
 * Helper function for debugging
 */
function debugLog(message, data = null) {
  console.log(`[${new Date().toISOString()}] ${message}`);
  if (data) {
    console.log(JSON.stringify(data, null, 2));
  }
}