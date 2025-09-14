/**
 * Google Apps Script Code for Certificate Upload with Company Google Drive Integration
 * 
 * This script provides the backend functionality for uploading certificate files
 * to company-specific Google Drive folders organized by date.
 * 
 * Supported Actions:
 * - test_connection: Test Google Drive connection
 * - create_folder_structure: Create nested folder structure (DATA INPUT/YYYY-MM-DD)
 * - upload_file: Upload individual files to specified folders
 * - sync_to_drive: Bulk data sync (existing functionality)
 * - list_files: List files in folders (existing functionality)
 */

function doPost(e) {
  try {
    // Parse the incoming request
    let requestData;
    
    if (e.postData && e.postData.contents) {
      requestData = JSON.parse(e.postData.contents);
    } else {
      throw new Error("No request data received");
    }
    
    const action = requestData.action;
    
    // Route to appropriate handler based on action
    switch (action) {
      case 'test_connection':
        return handleTestConnection(requestData);
        
      case 'create_folder_structure':
        return handleCreateFolderStructure(requestData);
        
      case 'upload_file':
        return handleUploadFile(requestData);
        
      case 'sync_to_drive':
        return handleSyncToDrive(requestData);
        
      case 'list_files':
        return handleListFiles(requestData);
        
      default:
        throw new Error(`Unsupported action: ${action}`);
    }
    
  } catch (error) {
    console.error('doPost error:', error);
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        message: error.toString(),
        timestamp: new Date().toISOString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Test Google Drive connection
 */
function handleTestConnection(requestData) {
  try {
    const folderId = requestData.folder_id;
    
    if (!folderId) {
      throw new Error("folder_id is required");
    }
    
    // Test access to the specified folder
    const folder = DriveApp.getFolderById(folderId);
    const folderName = folder.getName();
    
    return ContentService
      .createTextOutput(JSON.stringify({
        success: true,
        message: "Connection successful",
        folder_name: folderName,
        folder_id: folderId,
        timestamp: new Date().toISOString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        message: `Connection test failed: ${error.toString()}`,
        timestamp: new Date().toISOString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Create nested folder structure: ROOT_FOLDER/DATA INPUT/YYYY-MM-DD/
 */
function handleCreateFolderStructure(requestData) {
  try {
    const parentFolderId = requestData.parent_folder_id;
    const folderPath = requestData.folder_path; // e.g., "DATA INPUT/2024-09-14"
    
    if (!parentFolderId || !folderPath) {
      throw new Error("parent_folder_id and folder_path are required");
    }
    
    const parentFolder = DriveApp.getFolderById(parentFolderId);
    const pathParts = folderPath.split('/');
    
    let currentFolder = parentFolder;
    let currentPath = '';
    
    // Create each folder in the path if it doesn't exist
    for (const folderName of pathParts) {
      if (!folderName.trim()) continue;
      
      currentPath += (currentPath ? '/' : '') + folderName;
      
      // Check if folder already exists
      const subFolders = currentFolder.getFoldersByName(folderName);
      
      if (subFolders.hasNext()) {
        // Folder exists, use it
        currentFolder = subFolders.next();
      } else {
        // Create new folder
        currentFolder = currentFolder.createFolder(folderName);
      }
    }
    
    return ContentService
      .createTextOutput(JSON.stringify({
        success: true,
        message: `Folder structure created: ${folderPath}`,
        folder_id: currentFolder.getId(),
        folder_name: currentFolder.getName(),
        folder_path: folderPath,
        timestamp: new Date().toISOString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        message: `Failed to create folder structure: ${error.toString()}`,
        timestamp: new Date().toISOString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Upload individual file to specified folder
 */
function handleUploadFile(requestData) {
  try {
    const folderId = requestData.folder_id;
    const fileName = requestData.file_name;
    const fileContent = requestData.file_content; // base64 encoded
    const mimeType = requestData.mime_type || 'application/octet-stream';
    
    if (!folderId || !fileName || !fileContent) {
      throw new Error("folder_id, file_name, and file_content are required");
    }
    
    // Get the target folder
    const folder = DriveApp.getFolderById(folderId);
    
    // Decode base64 content to bytes
    const bytes = Utilities.base64Decode(fileContent);
    
    // Create blob from bytes
    const blob = Utilities.newBlob(bytes, mimeType, fileName);
    
    // Check if file already exists and handle duplicates
    let finalFileName = fileName;
    const existingFiles = folder.getFilesByName(fileName);
    
    if (existingFiles.hasNext()) {
      // Create unique filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const nameParts = fileName.split('.');
      if (nameParts.length > 1) {
        const extension = nameParts.pop();
        finalFileName = `${nameParts.join('.')}_${timestamp}.${extension}`;
      } else {
        finalFileName = `${fileName}_${timestamp}`;
      }
      blob.setName(finalFileName);
    }
    
    // Create file in the folder
    const file = folder.createFile(blob);
    
    return ContentService
      .createTextOutput(JSON.stringify({
        success: true,
        message: `File uploaded successfully: ${finalFileName}`,
        file_id: file.getId(),
        file_name: finalFileName,
        file_url: file.getUrl(),
        file_size: bytes.length,
        folder_id: folderId,
        timestamp: new Date().toISOString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        message: `File upload failed: ${error.toString()}`,
        timestamp: new Date().toISOString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Bulk data sync (existing functionality)
 */
function handleSyncToDrive(requestData) {
  try {
    const folderId = requestData.folder_id;
    const fileName = requestData.file_name;
    const fileContent = requestData.file_content;
    
    if (!folderId || !fileName || !fileContent) {
      throw new Error("folder_id, file_name, and file_content are required");
    }
    
    const folder = DriveApp.getFolderById(folderId);
    
    // For sync operation, we create/update JSON files
    const existingFiles = folder.getFilesByName(fileName);
    
    if (existingFiles.hasNext()) {
      // Update existing file
      const file = existingFiles.next();
      file.setContent(fileContent);
      
      return ContentService
        .createTextOutput(JSON.stringify({
          success: true,
          message: `File updated: ${fileName}`,
          file_id: file.getId(),
          action: 'updated',
          timestamp: new Date().toISOString()
        }))
        .setMimeType(ContentService.MimeType.JSON);
    } else {
      // Create new file
      const file = folder.createFile(fileName, fileContent, 'application/json');
      
      return ContentService
        .createTextOutput(JSON.stringify({
          success: true,
          message: `File created: ${fileName}`,
          file_id: file.getId(),
          action: 'created',
          timestamp: new Date().toISOString()
        }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        message: `Sync failed: ${error.toString()}`,
        timestamp: new Date().toISOString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * List files in specified folder
 */
function handleListFiles(requestData) {
  try {
    const folderId = requestData.folder_id;
    
    if (!folderId) {
      throw new Error("folder_id is required");
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
    
    return ContentService
      .createTextOutput(JSON.stringify({
        success: true,
        message: `Found ${fileList.length} files`,
        files: fileList,
        folder_id: folderId,
        timestamp: new Date().toISOString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        message: `List files failed: ${error.toString()}`,
        timestamp: new Date().toISOString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Handle GET requests (for testing)
 */
function doGet(e) {
  return ContentService
    .createTextOutput(JSON.stringify({
      success: true,
      message: "Certificate Upload Google Apps Script API is running",
      timestamp: new Date().toISOString(),
      supported_actions: [
        'test_connection',
        'create_folder_structure', 
        'upload_file',
        'sync_to_drive',
        'list_files'
      ]
    }))
    .setMimeType(ContentService.MimeType.JSON);
}