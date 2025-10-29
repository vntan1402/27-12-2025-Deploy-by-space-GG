// =========================================================
// 🚢 GOOGLE DRIVE BACKUP PROXY - v3.1 (GET Support)
// Version: v3.1 (Dynamic Folder ID + Safe Logging + GET Support)
// =========================================================

// =================== 🔧 CONFIG ===================
const TIMEZONE = 'GMT+7';
const DATE_FORMAT = 'yyyy-MM-dd HH:mm:ss';
const LOG_MASK_LENGTH = 6;

// =================== 🧩 UTILITIES (Same as v3.0) ===================
function maskSensitiveData(value, showLength = LOG_MASK_LENGTH) {
  if (!value || typeof value !== 'string') return '***';
  if (value.length <= showLength) return '***';
  return value.substring(0, showLength) + '***';
}

function log(message, data) {
  const time = Utilities.formatDate(new Date(), TIMEZONE, DATE_FORMAT);
  
  if (data && typeof data === 'object') {
    const safeData = JSON.parse(JSON.stringify(data));
    
    if (safeData.folder_id) safeData.folder_id = maskSensitiveData(safeData.folder_id);
    if (safeData.parent_id) safeData.parent_id = maskSensitiveData(safeData.parent_id);
    if (safeData.file_id) safeData.file_id = maskSensitiveData(safeData.file_id);
    if (safeData.api_key) safeData.api_key = '***HIDDEN***';
    if (safeData.content) safeData.content = `<${safeData.content.length} bytes>`;
    
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
function validateFolderId(folderId) {
  if (!folderId || typeof folderId !== 'string') {
    throw new Error('folder_id is required and must be a string');
  }
  
  try {
    const folder = DriveApp.getFolderById(folderId);
    return folder;
  } catch (e) {
    throw new Error('Invalid folder_id or no access permission: ' + maskSensitiveData(folderId));
  }
}

// =================== 📂 DRIVE ACTIONS ===================
function createFolder({ folder_name, parent_id }) {
  if (!folder_name) throw new Error('folder_name is required');
  
  const parentFolder = validateFolderId(parent_id);
  const existingFolders = parentFolder.getFoldersByName(folder_name);
  
  if (existingFolders.hasNext()) {
    const folder = existingFolders.next();
    log('📁 Folder already exists', { name: folder_name, id: maskSensitiveData(folder.getId()) });
    return folder;
  }
  
  const folder = parentFolder.createFolder(folder_name);
  log('📁 Created new folder', { name: folder_name, id: maskSensitiveData(folder.getId()) });
  return folder;
}

function uploadFile({ folder_id, filename, content, mimeType = 'application/json' }) {
  if (!filename) throw new Error('filename is required');
  if (!content) throw new Error('content is required');
  
  const folder = validateFolderId(folder_id);
  const blob = Utilities.newBlob(content, mimeType, filename);
  const file = folder.createFile(blob);
  
  log('⬆️ Uploaded file', { name: filename, id: maskSensitiveData(file.getId()), size: content.length, mimeType });
  return file;
}

function listFolders({ parent_id }) {
  const folder = validateFolderId(parent_id);
  const subfolders = folder.getFolders();
  const list = [];
  
  while (subfolders.hasNext()) {
    const f = subfolders.next();
    list.push({ id: f.getId(), name: f.getName(), created: f.getDateCreated() });
  }
  
  log('📂 Listed subfolders', { parent_id: maskSensitiveData(parent_id), count: list.length });
  return list;
}

function listFiles({ folder_id, parent_folder_id, folder_name }) {
  let folder;
  
  if (folder_id) {
    folder = validateFolderId(folder_id);
  } else if (parent_folder_id && folder_name) {
    const parentFolder = validateFolderId(parent_folder_id);
    const subfolders = parentFolder.getFoldersByName(folder_name);
    
    if (!subfolders.hasNext()) {
      throw new Error(`Subfolder '${folder_name}' not found in parent folder`);
    }
    
    folder = subfolders.next();
  } else {
    throw new Error('Either folder_id or (parent_folder_id + folder_name) is required');
  }
  
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
    folder_id: folder_id ? maskSensitiveData(folder_id) : undefined,
    parent_folder_id: parent_folder_id ? maskSensitiveData(parent_folder_id) : undefined,
    folder_name,
    count: list.length 
  });
  
  return list;
}

function downloadFile({ file_id }) {
  if (!file_id) throw new Error('file_id is required');
  
  try {
    const file = DriveApp.getFileById(file_id);
    const content = file.getBlob().getDataAsString();
    
    log('⬇️ Downloaded file', { name: file.getName(), id: maskSensitiveData(file_id), size: content.length });
    return { name: file.getName(), content, mimeType: file.getMimeType() };
  } catch (e) {
    throw new Error('Invalid file_id or no access permission: ' + maskSensitiveData(file_id));
  }
}

function deleteFile({ file_id }) {
  if (!file_id) throw new Error('file_id is required');
  
  try {
    const file = DriveApp.getFileById(file_id);
    const fileName = file.getName();
    file.setTrashed(true);
    
    log('🗑️ Trashed file', { id: maskSensitiveData(file_id), name: fileName });
    return { id: file_id, trashed: true };
  } catch (e) {
    throw new Error('Invalid file_id or no access permission: ' + maskSensitiveData(file_id));
  }
}

function testConnection({ folder_id }) {
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

// =================== 🕹️ MAIN HANDLERS ===================

// ✨ NEW: doGet handler for GET requests (test_connection only)
function doGet(e) {
  try {
    const params = e.parameter;
    const action = params.action;
    
    log(`📨 Incoming GET request`, { action });
    
    // Only allow test_connection via GET for security
    if (action === 'test_connection') {
      const folder_id = params.folder_id;
      
      if (!folder_id) {
        return errorResponse('folder_id parameter is required');
      }
      
      return successResponse('Connection successful', testConnection({ folder_id }));
    }
    
    // For other actions, show UI
    return HtmlService.createHtmlOutput(`
      <h2>🚀 Google Drive Backup Proxy - v3.1 (Secure + GET Support)</h2>
      <p>Status: <b>Active</b></p>
      <p>✅ Dynamic Folder ID (no hardcoded values)</p>
      <p>✅ Safe Logging (sensitive data masked)</p>
      <p>✅ GET support for test_connection</p>
      <p>🔒 Security: folder_id required in each request</p>
      <p>Timezone: ${TIMEZONE}</p>
      <hr/>
      <h3>Usage:</h3>
      <p><b>Test Connection (GET):</b></p>
      <code>?action=test_connection&folder_id=YOUR_FOLDER_ID</code>
      <p><b>Other Actions (POST):</b></p>
      <code>{"action": "upload_file", "folder_id": "...", ...}</code>
    `);
    
  } catch (error) {
    return errorResponse('GET request failed: ' + error.message, error);
  }
}

// POST handler (same as v3.0)
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const { action } = payload;
    
    if (!action) throw new Error('action is required in request payload');
    
    log(`📨 Incoming POST request`, { action });

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
