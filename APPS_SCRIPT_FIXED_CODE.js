/**
 * Ship Management Google Drive Proxy - FIXED VERSION
 * Copy this EXACT code to your Google Apps Script
 * This fixes the "response.setHeaders is not a function" error
 */

// ⚠️ IMPORTANT: Replace with your actual folder ID
const FOLDER_ID = '1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB';

/**
 * Handle POST requests
 */
function doPost(e) {
  try {
    console.log('POST request received');
    
    // Parse the request data
    let requestData;
    if (e.postData && e.postData.contents) {
      requestData = JSON.parse(e.postData.contents);
    } else if (e.parameter) {
      requestData = e.parameter;
    } else {
      return createJsonResponse({
        success: false,
        error: 'No request data found'
      });
    }
    
    console.log('Request data:', requestData);
    
    const action = requestData.action;
    console.log('Action:', action);
    
    // Handle different actions
    switch (action) {
      case 'test_connection':
        return handleTestConnection();
      case 'sync_to_drive':
        return handleSyncToDrive(requestData);
      case 'list_files':
        return handleListFiles();
      default:
        return createJsonResponse({
          success: false,
          error: 'Unknown action: ' + action
        });
    }
    
  } catch (error) {
    console.error('doPost error:', error);
    return createJsonResponse({
      success: false,
      error: 'Server error: ' + error.toString()
    });
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
      return createJsonResponse({
        success: true,
        message: 'Ship Management Google Drive Proxy is running',
        timestamp: new Date().toISOString(),
        available_actions: ['test_connection', 'sync_to_drive', 'list_files']
      });
    }
    
  } catch (error) {
    console.error('doGet error:', error);
    return createJsonResponse({
      success: false,
      error: 'Server error: ' + error.toString()
    });
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
    
    return createJsonResponse({
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
      errorMessage = 'Folder not found. Please check the FOLDER_ID.';
    } else if (error.toString().includes('permission')) {
      errorMessage = 'Permission denied. Please ensure you have access to the folder.';
    }
    
    return createJsonResponse({
      success: false,
      error: errorMessage + ': ' + error.toString()
    });
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
        mimeType: file.getBlob().getContentType()
      });
    }
    
    console.log('Found', fileList.length, 'files');
    
    return createJsonResponse({
      success: true,
      files: fileList,
      count: fileList.length,
      folder_name: folder.getName(),
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('List files error:', error);
    return createJsonResponse({
      success: false,
      error: 'Failed to list files: ' + error.toString()
    });
  }
}

/**
 * Sync multiple files to Google Drive
 */
function handleSyncToDrive(requestData) {
  try {
    const files = requestData.files || [];
    
    if (!Array.isArray(files) || files.length === 0) {
      return createJsonResponse({
        success: false,
        error: 'No files provided for sync'
      });
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
        
        // Check if file exists
        const existingFiles = folder.getFilesByName(fileData.name);
        let file;
        
        if (existingFiles.hasNext()) {
          // Update existing file
          file = existingFiles.next();
          file.setContent(fileData.content);
          console.log('Updated existing file:', fileData.name);
        } else {
          // Create new file
          file = folder.createFile(fileData.name, fileData.content, 'application/json');
          console.log('Created new file:', fileData.name);
        }
        
        uploadedFiles.push({
          name: fileData.name,
          id: file.getId(),
          size: file.getSize()
        });
        
      } catch (fileError) {
        console.error(`Error processing ${fileData.name}:`, fileError);
        errors.push(`${fileData.name}: ${fileError.toString()}`);
      }
    }
    
    console.log('Sync completed. Uploaded:', uploadedFiles.length, 'Errors:', errors.length);
    
    return createJsonResponse({
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
    return createJsonResponse({
      success: false,
      error: 'Failed to sync files: ' + error.toString()
    });
  }
}

/**
 * Create JSON response - CORRECT WAY for Google Apps Script
 * This fixes the "response.setHeaders is not a function" error
 */
function createJsonResponse(data) {
  // ✅ CORRECT: Use ContentService (not response.setHeaders)
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Test function - run this in Apps Script editor to test locally
 */
function testScript() {
  console.log('Testing Apps Script locally...');
  
  try {
    const result = handleTestConnection();
    const content = result.getContent();
    console.log('Test result:', content);
    
    const data = JSON.parse(content);
    if (data.success) {
      console.log('✅ Test passed:', data.message);
    } else {
      console.log('❌ Test failed:', data.error);
    }
  } catch (error) {
    console.error('❌ Test error:', error);
  }
}