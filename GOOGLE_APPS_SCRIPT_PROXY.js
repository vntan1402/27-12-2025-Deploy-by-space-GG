/**
 * Ship Management Google Drive Proxy
 * Bypass OAuth consent screen issues by using Google Apps Script
 */

// Configuration
const FOLDER_ID = '1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB'; // Replace with your folder ID
const ALLOWED_ORIGINS = [
  'https://certmaster-ship.preview.emergentagent.com',
  'http://localhost:3000'
];

/**
 * Handle all HTTP requests
 */
function doPost(e) {
  return handleRequest(e);
}

function doGet(e) {
  return handleRequest(e);
}

/**
 * Main request handler
 */
function handleRequest(e) {
  try {
    // Set CORS headers
    const response = {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
      }
    };
    
    // Handle OPTIONS request (CORS preflight)
    if (e.parameter.method === 'OPTIONS') {
      return ContentService.createTextOutput('')
        .setMimeType(ContentService.MimeType.JSON)
        .setHeaders(response.headers);
    }
    
    const action = e.parameter.action || e.postData?.contents ? JSON.parse(e.postData.contents).action : null;
    
    switch (action) {
      case 'test_connection':
        return handleTestConnection();
      case 'list_files':
        return handleListFiles();
      case 'upload_file':
        return handleUploadFile(e);
      case 'sync_to_drive':
        return handleSyncToDrive(e);
      default:
        return createErrorResponse('Invalid action');
    }
    
  } catch (error) {
    console.error('Error:', error);
    return createErrorResponse(error.toString());
  }
}

/**
 * Test Google Drive connection
 */
function handleTestConnection() {
  try {
    const folder = DriveApp.getFolderById(FOLDER_ID);
    const folderName = folder.getName();
    
    return createSuccessResponse({
      success: true,
      message: 'Google Drive connection successful',
      folder_name: folderName,
      folder_id: FOLDER_ID,
      service_account_email: Session.getActiveUser().getEmail()
    });
  } catch (error) {
    return createErrorResponse('Failed to access Google Drive folder: ' + error.toString());
  }
}

/**
 * List files in the folder
 */
function handleListFiles() {
  try {
    const folder = DriveApp.getFolderById(FOLDER_ID);
    const files = folder.getFiles();
    const fileList = [];
    
    while (files.hasNext()) {
      const file = files.next();
      fileList.push({
        id: file.getId(),
        name: file.getName(),
        size: file.getSize(),
        lastModified: file.getLastUpdated().toISOString(),
        mimeType: file.getBlob().getContentType()
      });
    }
    
    return createSuccessResponse({
      success: true,
      files: fileList,
      count: fileList.length
    });
  } catch (error) {
    return createErrorResponse('Failed to list files: ' + error.toString());
  }
}

/**
 * Upload file to Google Drive
 */
function handleUploadFile(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const fileName = data.fileName;
    const fileContent = data.fileContent;
    const mimeType = data.mimeType || 'application/json';
    
    const folder = DriveApp.getFolderById(FOLDER_ID);
    const blob = Utilities.newBlob(fileContent, mimeType, fileName);
    
    // Check if file exists and update or create
    const existingFiles = folder.getFilesByName(fileName);
    let file;
    
    if (existingFiles.hasNext()) {
      // Update existing file
      file = existingFiles.next();
      file.setContent(fileContent);
    } else {
      // Create new file
      file = folder.createFile(blob);
    }
    
    return createSuccessResponse({
      success: true,
      message: 'File uploaded successfully',
      file_id: file.getId(),
      file_name: fileName,
      file_url: file.getUrl()
    });
  } catch (error) {
    return createErrorResponse('Failed to upload file: ' + error.toString());
  }
}

/**
 * Sync multiple files to Google Drive
 */
function handleSyncToDrive(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const files = data.files || [];
    
    const folder = DriveApp.getFolderById(FOLDER_ID);
    const uploadedFiles = [];
    
    for (const fileData of files) {
      try {
        const blob = Utilities.newBlob(fileData.content, 'application/json', fileData.name);
        
        // Check if file exists
        const existingFiles = folder.getFilesByName(fileData.name);
        let file;
        
        if (existingFiles.hasNext()) {
          file = existingFiles.next();
          file.setContent(fileData.content);
        } else {
          file = folder.createFile(blob);
        }
        
        uploadedFiles.push({
          name: fileData.name,
          id: file.getId(),
          url: file.getUrl()
        });
      } catch (fileError) {
        console.error(`Error uploading ${fileData.name}:`, fileError);
      }
    }
    
    return createSuccessResponse({
      success: true,
      message: `Successfully synced ${uploadedFiles.length} files to Google Drive`,
      uploaded_files: uploadedFiles,
      total_files: files.length
    });
  } catch (error) {
    return createErrorResponse('Failed to sync files: ' + error.toString());
  }
}

/**
 * Create success response
 */
function createSuccessResponse(data) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON)
    .setHeaders({
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    });
}

/**
 * Create error response
 */
function createErrorResponse(message) {
  return ContentService.createTextOutput(JSON.stringify({
    success: false,
    error: message
  }))
    .setMimeType(ContentService.MimeType.JSON)
    .setHeaders({
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    });
}