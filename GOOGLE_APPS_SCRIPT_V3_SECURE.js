// =========================================================
// 🚢 GOOGLE DRIVE BACKUP PROXY - SECURE VERSION
// Version: v3.0 (Dynamic Folder ID + Safe Logging)
// Author: Vu Ngoc Tan + GPT-5
// Date: 2025-10-29
// =========================================================

// =================== 🔧 CONFIG ===================
const TIMEZONE = 'GMT+7';
const DATE_FORMAT = 'yyyy-MM-dd HH:mm:ss';
const LOG_MASK_LENGTH = 6; // Show first 6 chars, mask the rest

// =================== 🧩 UTILITIES ===================

/**
 * Mask sensitive data for safe logging
 * Examples:
 *   - "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB" → "1UeKVB***"
 *   - "my-secret-api-key" → "my-sec***"
 */
function maskSensitiveData(value, showLength = LOG_MASK_LENGTH) {
  if (!value || typeof value !== 'string') return '***';
  if (value.length <= showLength) return '***';
  return value.substring(0, showLength) + '***';
}

/**
 * Safe logger that masks sensitive data
 */
function log(message, data) {
  const time = Utilities.formatDate(new Date(), TIMEZONE, DATE_FORMAT);
  
  if (data && typeof data === 'object') {
    // Create a copy to avoid modifying original
    const safeData = JSON.parse(JSON.stringify(data));
    
    // Mask sensitive fields
    if (safeData.folder_id) {
      safeData.folder_id = maskSensitiveData(safeData.folder_id);
    }
    if (safeData.parent_id) {
      safeData.parent_id = maskSensitiveData(safeData.parent_id);
    }
    if (safeData.file_id) {
      safeData.file_id = maskSensitiveData(safeData.file_id);
    }
    if (safeData.api_key) {
      safeData.api_key = '***HIDDEN***';
    }
    // Don't log file content
    if (safeData.content) {
      safeData.content = `<${safeData.content.length} bytes>`;
    }
    
    Logger.log(`[${time}] ${message} | ${JSON.stringify(safeData)}`);
  } else {
    Logger.log(`[${time}] ${message}${data ? ' | ' + data : ''}`);
  }
}

function successResponse(message, data = null) {
  log(`✅ SUCCESS: ${message}`, data);
  return ContentService
    .createTextOutput(JSON.stringify({ success: true, message, data }))
    .setMimeType(ContentService.MimeType.JSON);
}

function errorResponse(message, error = null) {
  const details = error ? (error.stack || error.message || String(error)) : '';
  log(`❌ ERROR: ${message}`, { error: details });
  return ContentService
    .createTextOutput(JSON.stringify({ success: false, message, error: details }))
    .setMimeType(ContentService.MimeType.JSON);
}

// =================== 🔒 VALIDATION ===================

/**
 * Validate that required folder_id is provided in payload
 */
function validateFolderId(folderId) {
  if (!folderId || typeof folderId !== 'string') {
    throw new Error('folder_id is required and must be a string');
  }
  
  // Try to access the folder to ensure it exists and user has permission
  try {
    const folder = DriveApp.getFolderById(folderId);
    return folder;
  } catch (e) {
    throw new Error('Invalid folder_id or no access permission: ' + maskSensitiveData(folderId));
  }
}

// =================== 📂 DRIVE ACTIONS ===================

/**
 * Create folder (if not exists) inside parent folder
 */
function createFolder({ folder_name, parent_id }) {
  if (!folder_name) {
    throw new Error('folder_name is required');
  }
  
  // Validate parent folder
  const parentFolder = validateFolderId(parent_id);
  
  // Check if folder already exists
  const existingFolders = parentFolder.getFoldersByName(folder_name);
  if (existingFolders.hasNext()) {
    const folder = existingFolders.next();
    log('📁 Folder already exists', { 
      name: folder_name, 
      id: maskSensitiveData(folder.getId())
    });
    return folder;
  }
  
  // Create new folder
  const folder = parentFolder.createFolder(folder_name);
  log('📁 Created new folder', { 
    name: folder_name, 
    id: maskSensitiveData(folder.getId())
  });
  return folder;
}

/**
 * Upload file (JSON/Text) to specified folder
 */
function uploadFile({ folder_id, filename, content, mimeType = 'application/json' }) {
  if (!filename) {
    throw new Error('filename is required');
  }
  if (!content) {
    throw new Error('content is required');
  }
  
  // Validate folder
  const folder = validateFolderId(folder_id);
  
  // Create blob and upload
  const blob = Utilities.newBlob(content, mimeType, filename);
  const file = folder.createFile(blob);
  
  log('⬆️ Uploaded file', { 
    name: filename, 
    id: maskSensitiveData(file.getId()),
    size: content.length,
    mimeType: mimeType
  });
  
  return file;
}

/**
 * List all folders inside parent
 */
function listFolders({ parent_id }) {
  // Validate parent folder
  const folder = validateFolderId(parent_id);
  
  const subfolders = folder.getFolders();
  const list = [];
  
  while (subfolders.hasNext()) {
    const f = subfolders.next();
    list.push({ 
      id: f.getId(), 
      name: f.getName(), 
      created: f.getDateCreated() 
    });
  }
  
  log('📂 Listed subfolders', { 
    parent_id: maskSensitiveData(parent_id),
    count: list.length 
  });
  
  return list;
}

/**
 * List files inside folder
 */
function listFiles({ folder_id }) {
  // Validate folder
  const folder = validateFolderId(folder_id);
  
  const files = folder.getFiles();
  const list = [];
  
  while (files.hasNext()) {
    const f = files.next();
    list.push({
      id: f.getId(),
      name: f.getName(),
      mimeType: f.getMimeType(),
      size: f.getSize(),
      created: f.getDateCreated(),
      modified: f.getLastUpdated()
    });
  }
  
  log('📑 Listed files', { 
    folder_id: maskSensitiveData(folder_id),
    count: list.length 
  });
  
  return list;
}

/**
 * Download file content
 */
function downloadFile({ file_id }) {
  if (!file_id) {
    throw new Error('file_id is required');
  }
  
  try {
    const file = DriveApp.getFileById(file_id);
    const content = file.getBlob().getDataAsString();
    
    log('⬇️ Downloaded file', { 
      name: file.getName(), 
      id: maskSensitiveData(file_id),
      size: content.length
    });
    
    return { 
      name: file.getName(), 
      content, 
      mimeType: file.getMimeType() 
    };
  } catch (e) {
    throw new Error('Invalid file_id or no access permission: ' + maskSensitiveData(file_id));
  }
}

/**
 * Delete file (move to trash)
 */
function deleteFile({ file_id }) {
  if (!file_id) {
    throw new Error('file_id is required');
  }
  
  try {
    const file = DriveApp.getFileById(file_id);
    const fileName = file.getName();
    file.setTrashed(true);
    
    log('🗑️ Trashed file', { 
      id: maskSensitiveData(file_id), 
      name: fileName 
    });
    
    return { id: file_id, trashed: true };
  } catch (e) {
    throw new Error('Invalid file_id or no access permission: ' + maskSensitiveData(file_id));
  }
}

/**
 * Test connection to a folder
 */
function testConnection({ folder_id }) {
  // Validate folder access
  const folder = validateFolderId(folder_id);
  
  log('🔌 Connection test successful', {
    folder_id: maskSensitiveData(folder_id),
    folder_name: folder.getName()
  });
  
  return {
    status: 'Connected',
    folder_name: folder.getName(),
    folder_id: folder_id,
    timestamp: new Date().toISOString()
  };
}

// =================== 🕹️ MAIN HANDLER ===================
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const { action } = payload;
    
    if (!action) {
      throw new Error('action is required in request payload');
    }
    
    log(`📨 Incoming request`, { action: action });

    switch (action) {
      case 'test_connection':
        return successResponse('Connection successful', testConnection(payload));

      case 'create_folder':
        const newFolder = createFolder(payload);
        return successResponse('Folder created successfully', {
          id: newFolder.getId(),
          name: newFolder.getName()
        });

      case 'upload_file':
        const file = uploadFile(payload);
        return successResponse('File uploaded successfully', {
          id: file.getId(),
          name: file.getName(),
          url: file.getUrl()
        });

      case 'list_folders':
        return successResponse('Folders retrieved', listFolders(payload));

      case 'list_files':
        return successResponse('Files retrieved', listFiles(payload));

      case 'download_file':
        return successResponse('File downloaded', downloadFile(payload));

      case 'delete_file':
        return successResponse('File deleted (trashed)', deleteFile(payload));

      default:
        throw new Error(`Unknown action: ${action}`);
    }
  } catch (error) {
    return errorResponse('Request failed: ' + error.message, error);
  }
}

// =================== 🌐 SIMPLE UI ===================
function doGet() {
  return HtmlService.createHtmlOutput(`
    <h2>🚀 Google Drive Backup Proxy - v3.0 (Secure)</h2>
    <p>Status: <b>Active</b></p>
    <p>✅ Dynamic Folder ID (no hardcoded values)</p>
    <p>✅ Safe Logging (sensitive data masked)</p>
    <p>🔒 Security: folder_id required in each request</p>
    <p>Timezone: ${TIMEZONE}</p>
    <hr/>
    <p><i>Use POST requests with JSON payload to interact with the API.</i></p>
    <p><small>Example: {"action": "test_connection", "folder_id": "YOUR_FOLDER_ID"}</small></p>
  `);
}
