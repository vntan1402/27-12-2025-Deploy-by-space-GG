/**
 * System Google Drive Apps Script Proxy
 * ===========================================
 * Purpose: Backend proxy for Ship Management System to interact with Google Drive
 * 
 * Features:
 * - Test connection
 * - Create daily backup folders
 * - Upload backup files (JSON)
 * - List backup folders
 * - List files in folder
 * - Download files for restore
 * 
 * Deployment:
 * 1. Go to https://script.google.com
 * 2. Create new project: "Ship Management - System GDrive Proxy"
 * 3. Paste this code
 * 4. Update ROOT_FOLDER_ID below
 * 5. Deploy as Web App:
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 6. Copy Web App URL and paste in System Settings
 * 
 * Author: Ship Management System
 * Version: 2.0.0
 */

// ==========================================
// CONFIGURATION
// ==========================================

// IMPORTANT: Update this with your Google Drive folder ID
// Get it from folder URL: https://drive.google.com/drive/folders/[FOLDER_ID]
const ROOT_FOLDER_ID = "YOUR_ROOT_FOLDER_ID_HERE";

// Logging configuration
const ENABLE_LOGGING = true;

// ==========================================
// HELPER FUNCTIONS
// ==========================================

/**
 * Log message with timestamp
 */
function log(message) {
  if (ENABLE_LOGGING) {
    Logger.log(`[${new Date().toISOString()}] ${message}`);
  }
}

/**
 * Get folder by ID
 */
function getFolderById(folderId) {
  try {
    return DriveApp.getFolderById(folderId);
  } catch (error) {
    log(`Error getting folder ${folderId}: ${error.message}`);
    return null;
  }
}

/**
 * Get file by ID
 */
function getFileById(fileId) {
  try {
    return DriveApp.getFileById(fileId);
  } catch (error) {
    log(`Error getting file ${fileId}: ${error.message}`);
    return null;
  }
}

/**
 * Find folder by name in parent folder
 */
function findFolderByName(parentFolder, folderName) {
  try {
    const folders = parentFolder.getFoldersByName(folderName);
    if (folders.hasNext()) {
      return folders.next();
    }
    return null;
  } catch (error) {
    log(`Error finding folder ${folderName}: ${error.message}`);
    return null;
  }
}

/**
 * Create success response
 */
function successResponse(data) {
  return ContentService.createTextOutput(
    JSON.stringify({
      success: true,
      ...data
    })
  ).setMimeType(ContentService.MimeType.JSON);
}

/**
 * Create error response
 */
function errorResponse(message, details = null) {
  log(`ERROR: ${message}`);
  if (details) log(`Details: ${JSON.stringify(details)}`);
  
  return ContentService.createTextOutput(
    JSON.stringify({
      success: false,
      error: message,
      details: details
    })
  ).setMimeType(ContentService.MimeType.JSON);
}

// ==========================================
// ACTION HANDLERS
// ==========================================

/**
 * Test connection to Google Drive
 */
function testConnection(payload) {
  log("Testing connection...");
  
  try {
    // Check if ROOT_FOLDER_ID is configured
    if (ROOT_FOLDER_ID === "YOUR_ROOT_FOLDER_ID_HERE") {
      return errorResponse("ROOT_FOLDER_ID not configured in script");
    }
    
    // Try to access the root folder
    const folder = getFolderById(ROOT_FOLDER_ID);
    if (!folder) {
      return errorResponse(`Cannot access root folder: ${ROOT_FOLDER_ID}`);
    }
    
    // Get folder info
    const folderName = folder.getName();
    const folderUrl = folder.getUrl();
    
    log(`✅ Connection successful to folder: ${folderName}`);
    
    return successResponse({
      message: "Connection successful",
      folder_name: folderName,
      folder_id: ROOT_FOLDER_ID,
      folder_url: folderUrl,
      access_time: new Date().toISOString()
    });
    
  } catch (error) {
    return errorResponse(`Connection test failed: ${error.message}`, {
      error_type: error.name,
      stack: error.stack
    });
  }
}

/**
 * Create a new folder (for daily backups)
 */
function createFolder(payload) {
  log("Creating folder...");
  
  try {
    const parentFolderId = payload.parent_folder_id || ROOT_FOLDER_ID;
    const folderName = payload.folder_name;
    
    if (!folderName) {
      return errorResponse("folder_name is required");
    }
    
    // Get parent folder
    const parentFolder = getFolderById(parentFolderId);
    if (!parentFolder) {
      return errorResponse(`Parent folder not found: ${parentFolderId}`);
    }
    
    // Check if folder already exists
    let folder = findFolderByName(parentFolder, folderName);
    
    if (folder) {
      log(`Folder ${folderName} already exists, returning existing folder`);
      return successResponse({
        message: "Folder already exists",
        folder_id: folder.getId(),
        folder_name: folder.getName(),
        folder_url: folder.getUrl(),
        created: false
      });
    }
    
    // Create new folder
    folder = parentFolder.createFolder(folderName);
    log(`✅ Created folder: ${folderName} (ID: ${folder.getId()})`);
    
    return successResponse({
      message: "Folder created successfully",
      folder_id: folder.getId(),
      folder_name: folder.getName(),
      folder_url: folder.getUrl(),
      created: true
    });
    
  } catch (error) {
    return errorResponse(`Failed to create folder: ${error.message}`, {
      error_type: error.name
    });
  }
}

/**
 * Upload a file to Google Drive
 */
function uploadFile(payload) {
  log("Uploading file...");
  
  try {
    const folderId = payload.folder_id || ROOT_FOLDER_ID;
    const filename = payload.filename;
    const content = payload.content;
    const mimeType = payload.mimeType || "text/plain";
    
    if (!filename) {
      return errorResponse("filename is required");
    }
    
    if (!content) {
      return errorResponse("content is required");
    }
    
    // Get folder
    const folder = getFolderById(folderId);
    if (!folder) {
      return errorResponse(`Folder not found: ${folderId}`);
    }
    
    // Check if file already exists, delete it first
    const existingFiles = folder.getFilesByName(filename);
    while (existingFiles.hasNext()) {
      const existingFile = existingFiles.next();
      log(`Deleting existing file: ${filename}`);
      existingFile.setTrashed(true);
    }
    
    // Create new file
    const blob = Utilities.newBlob(content, mimeType, filename);
    const file = folder.createFile(blob);
    
    log(`✅ Uploaded file: ${filename} (ID: ${file.getId()}, Size: ${file.getSize()} bytes)`);
    
    return successResponse({
      message: "File uploaded successfully",
      file_id: file.getId(),
      file_name: file.getName(),
      file_url: file.getUrl(),
      file_size: file.getSize(),
      mime_type: file.getMimeType()
    });
    
  } catch (error) {
    return errorResponse(`Failed to upload file: ${error.message}`, {
      error_type: error.name,
      filename: payload.filename
    });
  }
}

/**
 * List folders in a parent folder
 */
function listFolders(payload) {
  log("Listing folders...");
  
  try {
    const parentFolderId = payload.parent_folder_id || ROOT_FOLDER_ID;
    
    // Get parent folder
    const parentFolder = getFolderById(parentFolderId);
    if (!parentFolder) {
      return errorResponse(`Parent folder not found: ${parentFolderId}`);
    }
    
    // Get all subfolders
    const folders = [];
    const folderIterator = parentFolder.getFolders();
    
    while (folderIterator.hasNext()) {
      const folder = folderIterator.next();
      folders.push({
        id: folder.getId(),
        name: folder.getName(),
        url: folder.getUrl(),
        created_date: folder.getDateCreated().toISOString(),
        last_updated: folder.getLastUpdated().toISOString()
      });
    }
    
    // Sort by name (newest first, assuming YYYY-MM-DD format)
    folders.sort((a, b) => b.name.localeCompare(a.name));
    
    log(`✅ Found ${folders.length} folders`);
    
    return successResponse({
      message: `Found ${folders.length} folders`,
      folders: folders,
      parent_folder_id: parentFolderId
    });
    
  } catch (error) {
    return errorResponse(`Failed to list folders: ${error.message}`, {
      error_type: error.name
    });
  }
}

/**
 * List files in a folder
 */
function listFiles(payload) {
  log("Listing files...");
  
  try {
    const parentFolderId = payload.parent_folder_id || ROOT_FOLDER_ID;
    const folderName = payload.folder_name;
    
    let folder;
    
    if (folderName) {
      // Find folder by name first
      const parentFolder = getFolderById(parentFolderId);
      if (!parentFolder) {
        return errorResponse(`Parent folder not found: ${parentFolderId}`);
      }
      
      folder = findFolderByName(parentFolder, folderName);
      if (!folder) {
        return errorResponse(`Folder not found: ${folderName}`);
      }
    } else {
      // Use parent folder directly
      folder = getFolderById(parentFolderId);
      if (!folder) {
        return errorResponse(`Folder not found: ${parentFolderId}`);
      }
    }
    
    // Get all files
    const files = [];
    const fileIterator = folder.getFiles();
    
    while (fileIterator.hasNext()) {
      const file = fileIterator.next();
      files.push({
        id: file.getId(),
        name: file.getName(),
        url: file.getUrl(),
        size: file.getSize(),
        mime_type: file.getMimeType(),
        created_date: file.getDateCreated().toISOString(),
        last_updated: file.getLastUpdated().toISOString()
      });
    }
    
    log(`✅ Found ${files.length} files in ${folder.getName()}`);
    
    return successResponse({
      message: `Found ${files.length} files`,
      files: files,
      folder_id: folder.getId(),
      folder_name: folder.getName()
    });
    
  } catch (error) {
    return errorResponse(`Failed to list files: ${error.message}`, {
      error_type: error.name
    });
  }
}

/**
 * Download a file content
 */
function downloadFile(payload) {
  log("Downloading file...");
  
  try {
    const fileId = payload.file_id;
    
    if (!fileId) {
      return errorResponse("file_id is required");
    }
    
    // Get file
    const file = getFileById(fileId);
    if (!file) {
      return errorResponse(`File not found: ${fileId}`);
    }
    
    // Get file content
    const content = file.getBlob().getDataAsString();
    
    log(`✅ Downloaded file: ${file.getName()} (Size: ${file.getSize()} bytes)`);
    
    return successResponse({
      message: "File downloaded successfully",
      file_id: file.getId(),
      file_name: file.getName(),
      content: content,
      file_size: file.getSize(),
      mime_type: file.getMimeType()
    });
    
  } catch (error) {
    return errorResponse(`Failed to download file: ${error.message}`, {
      error_type: error.name,
      file_id: payload.file_id
    });
  }
}

/**
 * Delete a file
 */
function deleteFile(payload) {
  log("Deleting file...");
  
  try {
    const fileId = payload.file_id;
    
    if (!fileId) {
      return errorResponse("file_id is required");
    }
    
    // Get file
    const file = getFileById(fileId);
    if (!file) {
      return errorResponse(`File not found: ${fileId}`);
    }
    
    const fileName = file.getName();
    
    // Move to trash
    file.setTrashed(true);
    
    log(`✅ Deleted file: ${fileName}`);
    
    return successResponse({
      message: "File deleted successfully",
      file_name: fileName
    });
    
  } catch (error) {
    return errorResponse(`Failed to delete file: ${error.message}`, {
      error_type: error.name
    });
  }
}

// ==========================================
// MAIN HANDLER
// ==========================================

/**
 * Handle POST requests (main entry point)
 */
function doPost(e) {
  log("=== Incoming POST Request ===");
  
  try {
    // Parse request payload
    let payload;
    try {
      payload = JSON.parse(e.postData.contents);
      log(`Action: ${payload.action}`);
    } catch (error) {
      return errorResponse("Invalid JSON payload");
    }
    
    // Route to appropriate handler based on action
    const action = payload.action;
    
    switch (action) {
      case "test_connection":
        return testConnection(payload);
        
      case "create_folder":
        return createFolder(payload);
        
      case "upload_file":
        return uploadFile(payload);
        
      case "list_folders":
        return listFolders(payload);
        
      case "list_files":
        return listFiles(payload);
        
      case "download_file":
        return downloadFile(payload);
        
      case "delete_file":
        return deleteFile(payload);
        
      default:
        return errorResponse(`Unknown action: ${action}`, {
          supported_actions: [
            "test_connection",
            "create_folder",
            "upload_file",
            "list_folders",
            "list_files",
            "download_file",
            "delete_file"
          ]
        });
    }
    
  } catch (error) {
    return errorResponse(`Request processing error: ${error.message}`, {
      error_type: error.name,
      stack: error.stack
    });
  }
}

/**
 * Handle GET requests (for testing in browser)
 */
function doGet(e) {
  log("=== Incoming GET Request ===");
  
  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>System Google Drive Proxy - Ship Management</title>
        <style>
          body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
          }
          .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
          }
          h1 {
            color: #667eea;
            margin-top: 0;
          }
          .status {
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
          }
          .info {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
          }
          .code {
            background: #263238;
            color: #aed581;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
          }
          .action-list {
            list-style: none;
            padding: 0;
          }
          .action-list li {
            padding: 8px;
            border-bottom: 1px solid #eee;
          }
          .action-list li:last-child {
            border-bottom: none;
          }
          .badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin-right: 8px;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>🚢 System Google Drive Proxy</h1>
          <p><strong>Ship Management System - Backend API Proxy</strong></p>
          
          <div class="status">
            <strong>✅ Status:</strong> Apps Script is running and ready to receive requests
          </div>
          
          <div class="info">
            <h3>📋 Configuration</h3>
            <p><strong>Root Folder ID:</strong> <code>${ROOT_FOLDER_ID}</code></p>
            <p><strong>Version:</strong> 2.0.0</p>
            <p><strong>Last Accessed:</strong> ${new Date().toLocaleString()}</p>
          </div>
          
          <div class="info">
            <h3>🔧 Supported Actions</h3>
            <ul class="action-list">
              <li><span class="badge">POST</span><code>test_connection</code> - Test connection to Google Drive</li>
              <li><span class="badge">POST</span><code>create_folder</code> - Create daily backup folder</li>
              <li><span class="badge">POST</span><code>upload_file</code> - Upload backup file (JSON)</li>
              <li><span class="badge">POST</span><code>list_folders</code> - List backup folders</li>
              <li><span class="badge">POST</span><code>list_files</code> - List files in folder</li>
              <li><span class="badge">POST</span><code>download_file</code> - Download file for restore</li>
              <li><span class="badge">POST</span><code>delete_file</code> - Delete file from Drive</li>
            </ul>
          </div>
          
          <div class="info">
            <h3>📝 Example Request</h3>
            <div class="code">
POST ${ScriptApp.getService().getUrl()}
Content-Type: application/json

{
  "action": "test_connection"
}
            </div>
          </div>
          
          <div class="info">
            <h3>📖 Setup Instructions</h3>
            <ol>
              <li>Update <code>ROOT_FOLDER_ID</code> in the script with your Google Drive folder ID</li>
              <li>Deploy as Web App (Execute as: Me, Access: Anyone)</li>
              <li>Copy the Web App URL</li>
              <li>Paste it in System Settings > Google Drive Configuration</li>
              <li>Test connection from the app</li>
            </ol>
          </div>
          
          <p style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            Ship Management System © 2025
          </p>
        </div>
      </body>
    </html>
  `;
  
  return HtmlService.createHtmlOutput(html);
}

// ==========================================
// TESTING FUNCTIONS (Development Only)
// ==========================================

/**
 * Test function - Run from Apps Script editor
 */
function runTests() {
  Logger.clear();
  log("=== Running Tests ===");
  
  // Test 1: Connection
  log("\n--- Test 1: Connection ---");
  const testResult = testConnection({});
  log(testResult.getContent());
  
  // Test 2: Create Folder
  log("\n--- Test 2: Create Folder ---");
  const today = Utilities.formatDate(new Date(), "GMT+7", "yyyy-MM-dd");
  const createResult = createFolder({
    parent_folder_id: ROOT_FOLDER_ID,
    folder_name: `test-${today}`
  });
  log(createResult.getContent());
  
  // Test 3: List Folders
  log("\n--- Test 3: List Folders ---");
  const listResult = listFolders({
    parent_folder_id: ROOT_FOLDER_ID
  });
  log(listResult.getContent());
  
  log("\n=== Tests Complete ===");
}
