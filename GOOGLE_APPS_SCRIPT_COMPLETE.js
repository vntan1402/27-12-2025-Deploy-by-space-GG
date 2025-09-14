/**
 * Ship Management Google Drive Proxy - COMPLETE VERSION
 * Copy this entire code to Google Apps Script
 */

// ⚠️ IMPORTANT: Replace with your actual folder ID
const FOLDER_ID = '1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB';

/**
 * Handle POST requests
 */
function doPost(e) {
  try {
    console.log('POST request received');
    
    // Handle different content types
    let data;
    if (e.postData && e.postData.contents) {
      try {
        data = JSON.parse(e.postData.contents);
      } catch (parseError) {
        console.error('JSON parse error:', parseError);
        return createErrorResponse('Invalid JSON in request body');
      }
    } else if (e.parameter) {
      data = e.parameter;
    } else {
      return createErrorResponse('No request data found');
    }
    
    console.log('Request data:', data);
    
    const action = data.action;
    console.log('Action:', action);
    
    switch (action) {
      case 'test_connection':
        return handleTestConnection();
      case 'list_files':
        return handleListFiles();
      case 'upload_file':
        return handleUploadFile(data);
      case 'sync_to_drive':
        return handleSyncToDrive(data);
      default:
        return createErrorResponse('Invalid action: ' + action);
    }
    
  } catch (error) {
    console.error('doPost error:', error);
    return createErrorResponse('Server error: ' + error.toString());
  }
}

/**
 * Handle GET requests (for testing)
 */
function doGet(e) {
  try {
    console.log('GET request received');
    
    const action = e.parameter.action || 'test_connection';
    
    if (action === 'test_connection') {
      return handleTestConnection();
    } else {
      return createSuccessResponse({
        message: 'Ship Management Google Drive Proxy is running',
        timestamp: new Date().toISOString(),
        available_actions: ['test_connection', 'list_files', 'upload_file', 'sync_to_drive']
      });
    }
    
  } catch (error) {
    console.error('doGet error:', error);
    return createErrorResponse('Server error: ' + error.toString());
  }
}

/**
 * Test Google Drive connection
 */
function handleTestConnection() {
  try {
    console.log('Testing connection to folder:', FOLDER_ID);
    
    // Try to access the folder
    const folder = DriveApp.getFolderById(FOLDER_ID);
    const folderName = folder.getName();
    const userEmail = Session.getActiveUser().getEmail();
    
    console.log('Connection successful. Folder:', folderName, 'User:', userEmail);
    
    return createSuccessResponse({
      success: true,
      message: 'Google Drive connection successful',
      folder_name: folderName,
      folder_id: FOLDER_ID,
      service_account_email: userEmail,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Test connection error:', error);
    
    let errorMessage = 'Failed to access Google Drive folder';
    if (error.toString().includes('not found')) {
      errorMessage = 'Folder not found. Please check the FOLDER_ID in the script.';
    } else if (error.toString().includes('permission')) {
      errorMessage = 'Permission denied. Please ensure you have access to the folder.';
    }
    
    return createErrorResponse(errorMessage + ': ' + error.toString());
  }
}

/**
 * List files in the folder
 */
function handleListFiles() {
  try {
    console.log('Listing files in folder:', FOLDER_ID);
    
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
        mimeType: file.getBlob().getContentType(),
        url: file.getUrl()
      });
    }
    
    console.log('Found', fileList.length, 'files');
    
    return createSuccessResponse({
      success: true,
      files: fileList,
      count: fileList.length,
      folder_name: folder.getName(),
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('List files error:', error);
    return createErrorResponse('Failed to list files: ' + error.toString());
  }
}

/**
 * Upload single file to Google Drive
 */
function handleUploadFile(data) {
  try {
    const fileName = data.fileName;
    const fileContent = data.fileContent;
    const mimeType = data.mimeType || 'application/json';
    
    if (!fileName || !fileContent) {
      return createErrorResponse('fileName and fileContent are required');
    }
    
    console.log('Uploading file:', fileName);
    
    const folder = DriveApp.getFolderById(FOLDER_ID);
    const blob = Utilities.newBlob(fileContent, mimeType, fileName);
    
    // Check if file exists and update or create
    const existingFiles = folder.getFilesByName(fileName);
    let file;
    
    if (existingFiles.hasNext()) {
      // Update existing file
      file = existingFiles.next();
      file.setContent(fileContent);
      console.log('Updated existing file:', fileName);
    } else {
      // Create new file
      file = folder.createFile(blob);
      console.log('Created new file:', fileName);
    }
    
    return createSuccessResponse({
      success: true,
      message: 'File uploaded successfully',
      file_id: file.getId(),
      file_name: fileName,
      file_url: file.getUrl(),
      file_size: file.getSize(),
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Upload file error:', error);
    return createErrorResponse('Failed to upload file: ' + error.toString());
  }
}

/**
 * Sync multiple files to Google Drive
 */
function handleSyncToDrive(data) {
  try {
    const files = data.files || [];
    
    if (!Array.isArray(files) || files.length === 0) {
      return createErrorResponse('No files provided for sync');
    }
    
    console.log('Syncing', files.length, 'files to Google Drive');
    
    const folder = DriveApp.getFolderById(FOLDER_ID);
    const uploadedFiles = [];
    const errors = [];
    
    for (let i = 0; i < files.length; i++) {
      const fileData = files[i];
      
      try {
        if (!fileData.name || !fileData.content) {
          errors.push(`File ${i}: Missing name or content`);
          continue;
        }
        
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
          url: file.getUrl(),
          size: file.getSize()
        });
        
        console.log('Processed file:', fileData.name);
        
      } catch (fileError) {
        console.error(`Error processing ${fileData.name}:`, fileError);
        errors.push(`${fileData.name}: ${fileError.toString()}`);
      }
    }
    
    console.log('Sync completed. Uploaded:', uploadedFiles.length, 'Errors:', errors.length);
    
    return createSuccessResponse({
      success: true,
      message: `Successfully synced ${uploadedFiles.length} out of ${files.length} files`,
      uploaded_files: uploadedFiles,
      total_files: files.length,
      errors: errors,
      folder_name: folder.getName(),
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Sync files error:', error);
    return createErrorResponse('Failed to sync files: ' + error.toString());
  }
}

/**
 * Create success response
 */
function createSuccessResponse(data) {
  const response = ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
  
  // Add CORS headers
  response.setHeaders({
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
  });
  
  return response;
}

/**
 * Create error response
 */
function createErrorResponse(message) {
  const errorData = {
    success: false,
    error: message,
    timestamp: new Date().toISOString()
  };
  
  const response = ContentService.createTextOutput(JSON.stringify(errorData))
    .setMimeType(ContentService.MimeType.JSON);
  
  // Add CORS headers
  response.setHeaders({
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
  });
  
  return response;
}

/**
 * Test function - you can run this in Apps Script editor to test
 */
function testScript() {
  console.log('Testing Apps Script...');
  
  try {
    const result = handleTestConnection();
    console.log('Test result:', result.getContent());
  } catch (error) {
    console.error('Test error:', error);
  }
}