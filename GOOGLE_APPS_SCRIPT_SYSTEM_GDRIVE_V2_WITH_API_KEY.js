// =========================================================
// 🚢 GOOGLE DRIVE BACKUP PROXY
// Author: Vu Ngoc Tan + GPT-5
// Version: v2.0 (Enhanced Security & Stability)
// Date: 2025-10-29
// =========================================================

// =================== 🔧 CONFIG ===================
const ROOT_FOLDER_ID = '1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB'; // 👈 Replace with your folder ID
const API_KEY = 'Vntan1402sms'; // 👈 Add secret key for authentication
const TIMEZONE = 'GMT+7';
const DATE_FORMAT = 'yyyy-MM-dd HH:mm:ss';

// =================== 🧩 UTILITIES ===================
function log(message, data) {
  const time = Utilities.formatDate(new Date(), TIMEZONE, DATE_FORMAT);
  Logger.log(`[${time}] ${message}${data ? ' | ' + JSON.stringify(data) : ''}`);
}

function successResponse(message, data = null) {
  return ContentService
    .createTextOutput(JSON.stringify({ success: true, message, data }))
    .setMimeType(ContentService.MimeType.JSON);
}

function errorResponse(message, error = null) {
  const details = error ? (error.stack || error.message || String(error)) : '';
  log(`❌ ERROR: ${message}`, details);
  return ContentService
    .createTextOutput(JSON.stringify({ success: false, message, error: details }))
    .setMimeType(ContentService.MimeType.JSON);
}

// =================== 🔐 AUTHENTICATION ===================
function validateApiKey(payload) {
  if (!payload.api_key || payload.api_key !== API_KEY) {
    throw new Error('Invalid or missing API key.');
  }
}

// =================== 📂 DRIVE ACTIONS ===================

// Create folder (if not exists)
function createFolder({ folder_name, parent_id }) {
  const parentFolder = parent_id ? DriveApp.getFolderById(parent_id) : DriveApp.getFolderById(ROOT_FOLDER_ID);
  const existingFolders = parentFolder.getFoldersByName(folder_name);
  if (existingFolders.hasNext()) {
    const folder = existingFolders.next();
    log('📁 Folder already exists', { name: folder_name, id: folder.getId() });
    return folder;
  }
  const folder = parentFolder.createFolder(folder_name);
  log('📁 Created new folder', { name: folder_name, id: folder.getId() });
  return folder;
}

// Upload file (JSON/Text)
function uploadFile({ folder_id, filename, content, mimeType = 'application/json' }) {
  const folder = DriveApp.getFolderById(folder_id || ROOT_FOLDER_ID);
  const blob = Utilities.newBlob(content, mimeType, filename);
  const file = folder.createFile(blob);
  log('⬆️ Uploaded file', { name: filename, id: file.getId(), mimeType });
  return file;
}

// List all folders inside parent
function listFolders({ parent_id }) {
  const folder = DriveApp.getFolderById(parent_id || ROOT_FOLDER_ID);
  const subfolders = folder.getFolders();
  const list = [];
  while (subfolders.hasNext()) {
    const f = subfolders.next();
    list.push({ id: f.getId(), name: f.getName(), created: f.getDateCreated() });
  }
  log('📂 Listed subfolders', { count: list.length });
  return list;
}

// List files inside folder
function listFiles({ folder_id }) {
  const folder = DriveApp.getFolderById(folder_id || ROOT_FOLDER_ID);
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
  log('📑 Listed files', { count: list.length });
  return list;
}

// Download file content
function downloadFile({ file_id }) {
  const file = DriveApp.getFileById(file_id);
  const content = file.getBlob().getDataAsString();
  log('⬇️ Downloaded file', { name: file.getName(), id: file_id });
  return { name: file.getName(), content, mimeType: file.getMimeType() };
}

// Delete file (move to trash)
function deleteFile({ file_id }) {
  const file = DriveApp.getFileById(file_id);
  file.setTrashed(true);
  log('🗑️ Trashed file', { id: file_id, name: file.getName() });
  return { id: file_id, trashed: true };
}

// Test connection
function testConnection() {
  try {
    const folder = DriveApp.getFolderById(ROOT_FOLDER_ID);
    return {
      status: 'Connected',
      folder_name: folder.getName(),
      folder_id: folder.getId()
    };
  } catch (err) {
    throw new Error('Drive connection failed. Check ROOT_FOLDER_ID or permissions.');
  }
}

// =================== 🕹️ MAIN HANDLER ===================
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    validateApiKey(payload);

    const { action } = payload;
    log(`📨 Incoming action: ${action}`);

    switch (action) {
      case 'test_connection':
        return successResponse('Connection successful', testConnection());

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
          name: file.getName()
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
    return errorResponse('Request failed', error);
  }
}

// =================== 🌐 SIMPLE UI ===================
function doGet() {
  return HtmlService.createHtmlOutput(`
    <h2>🚀 Google Drive Backup Proxy - v2.0</h2>
    <p>Status: <b>Active</b></p>
    <p>Root Folder ID: ${ROOT_FOLDER_ID}</p>
    <p>Timezone: ${TIMEZONE}</p>
    <p>API Key Enabled ✅</p>
    <hr/>
    <p><i>Use POST requests with JSON payload to interact with the API.</i></p>
  `);
}
