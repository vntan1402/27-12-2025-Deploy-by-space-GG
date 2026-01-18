/**
 * Upload Manager Singleton
 * Manages file uploads independently from React lifecycle
 * Reads file content into memory immediately to survive page navigation
 */

// Get axios instance
const getApi = () => {
  if (window.__apiInstance) {
    return window.__apiInstance;
  }
  const api = require('./api').default;
  window.__apiInstance = api;
  return api;
};

// Read file as ArrayBuffer
const readFileAsArrayBuffer = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsArrayBuffer(file);
  });
};

class UploadManager {
  constructor() {
    this.activeUploads = new Map();
    this.fileDataQueues = new Map(); // Store file DATA (not File objects)
    this.cancelledTasks = new Set();
    this.scheduledUploads = new Map();
    
    console.log('📦 [UploadManager] Initialized (with file data caching)');
  }
  
  /**
   * Start staggered file upload
   * Reads all files into memory first, then schedules uploads
   */
  async startUpload({ taskId, files, apiEndpoint, staggerDelayMs = 2000, onProgress }) {
    const api = getApi();
    
    console.log(`📤 [UploadManager] Starting upload for task ${taskId} with ${files.length} files`);
    console.log(`📤 [UploadManager] Reading file contents into memory...`);
    
    // Convert FileList to Array
    const fileArray = Array.from(files);
    
    // Read ALL file contents into memory IMMEDIATELY
    // This ensures data survives page navigation
    const fileDataArray = [];
    for (let i = 0; i < fileArray.length; i++) {
      const file = fileArray[i];
      try {
        const arrayBuffer = await readFileAsArrayBuffer(file);
        fileDataArray.push({
          name: file.name,
          type: file.type || 'application/octet-stream',
          size: file.size,
          data: arrayBuffer // Raw binary data in memory
        });
      } catch (err) {
        console.error(`❌ [UploadManager] Failed to read file ${file.name}:`, err);
        fileDataArray.push({
          name: file.name,
          type: file.type,
          size: file.size,
          data: null,
          error: err.message
        });
      }
    }
    
    console.log(`📤 [UploadManager] Read ${fileDataArray.length} files into memory`);
    
    // Store file DATA (not File objects)
    this.fileDataQueues.set(taskId, fileDataArray);
    this.cancelledTasks.delete(taskId);
    
    // Track upload state
    const uploadState = {
      taskId,
      totalFiles: fileDataArray.length,
      completedFiles: 0,
      failedFiles: 0,
      inProgress: true,
      startTime: Date.now()
    };
    this.activeUploads.set(taskId, uploadState);
    
    // Store scheduled timeouts
    const timeoutIds = [];
    
    // Schedule each file upload with staggered delay
    fileDataArray.forEach((fileData, index) => {
      const delay = index * staggerDelayMs;
      
      const timeoutId = window.setTimeout(() => {
        this._uploadSingleFileData(taskId, fileData, index, apiEndpoint, api, onProgress);
      }, delay);
      
      timeoutIds.push(timeoutId);
    });
    
    this.scheduledUploads.set(taskId, timeoutIds);
    
    console.log(`📤 [UploadManager] Scheduled ${fileDataArray.length} uploads with ${staggerDelayMs}ms stagger`);
  }
  
  /**
   * Upload a single file from cached data
   */
  async _uploadSingleFileData(taskId, fileData, index, apiEndpoint, api, onProgress) {
    // Check if cancelled
    if (this.cancelledTasks.has(taskId)) {
      console.log(`🚫 [UploadManager] Task ${taskId} cancelled. Skipping file ${index + 1}`);
      return;
    }
    
    const uploadState = this.activeUploads.get(taskId);
    if (!uploadState) {
      console.log(`⚠️ [UploadManager] No upload state for task ${taskId}`);
      return;
    }
    
    const filename = fileData.name || `file_${index}`;
    
    // Skip if file read failed
    if (!fileData.data) {
      console.error(`❌ [UploadManager] No data for file ${filename}, skipping`);
      uploadState.failedFiles++;
      this._checkCompletion(taskId, uploadState, onProgress);
      return;
    }
    
    try {
      // Check task status from server
      try {
        const statusCheck = await api.get(`${apiEndpoint}${taskId}`);
        if (statusCheck.data?.status === 'cancelled') {
          console.log(`🚫 [UploadManager] Task ${taskId} cancelled on server. Skipping.`);
          this.cancelledTasks.add(taskId);
          return;
        }
      } catch (e) {
        // Ignore status check errors
      }
      
      console.log(`📤 [UploadManager] Uploading ${index + 1}/${uploadState.totalFiles}: ${filename}`);
      
      // Create Blob from ArrayBuffer
      const blob = new Blob([fileData.data], { type: fileData.type });
      
      const formData = new FormData();
      formData.append('file', blob, filename);
      
      const response = await api.post(
        `${apiEndpoint}${taskId}/upload-file`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 300000
        }
      );
      
      if (response.data?.success) {
        uploadState.completedFiles++;
        console.log(`✅ [UploadManager] Uploaded ${index + 1}/${uploadState.totalFiles}: ${filename}`);
      } else {
        uploadState.failedFiles++;
        console.warn(`⚠️ [UploadManager] Failed ${index + 1}/${uploadState.totalFiles}: ${filename}`);
      }
      
    } catch (error) {
      const errorDetail = error.response?.data?.detail || '';
      if (error.response?.status === 400 && 
          (errorDetail.includes('cancelled') || errorDetail.includes('Task already'))) {
        console.log(`🚫 [UploadManager] Task ${taskId} cancelled. Stopping.`);
        this.cancelledTasks.add(taskId);
        return;
      }
      
      uploadState.failedFiles++;
      console.error(`❌ [UploadManager] Error uploading ${filename}:`, error.message);
    }
    
    this._checkCompletion(taskId, uploadState, onProgress);
  }
  
  _checkCompletion(taskId, uploadState, onProgress) {
    const processed = uploadState.completedFiles + uploadState.failedFiles;
    if (processed >= uploadState.totalFiles) {
      uploadState.inProgress = false;
      console.log(`✅ [UploadManager] Task ${taskId} complete. Success: ${uploadState.completedFiles}, Failed: ${uploadState.failedFiles}`);
      
      // Cleanup - free memory
      this.fileDataQueues.delete(taskId);
      this.scheduledUploads.delete(taskId);
    }
    
    if (onProgress) {
      onProgress({
        taskId,
        completed: uploadState.completedFiles,
        failed: uploadState.failedFiles,
        total: uploadState.totalFiles,
        inProgress: uploadState.inProgress
      });
    }
  }
  
  cancelUpload(taskId) {
    console.log(`🚫 [UploadManager] Cancelling task ${taskId}`);
    this.cancelledTasks.add(taskId);
    
    const timeoutIds = this.scheduledUploads.get(taskId);
    if (timeoutIds) {
      timeoutIds.forEach(id => window.clearTimeout(id));
      this.scheduledUploads.delete(taskId);
    }
    
    // Free memory
    this.fileDataQueues.delete(taskId);
    
    const uploadState = this.activeUploads.get(taskId);
    if (uploadState) {
      uploadState.inProgress = false;
    }
  }
  
  getStatus(taskId) {
    return this.activeUploads.get(taskId);
  }
  
  isCancelled(taskId) {
    return this.cancelledTasks.has(taskId);
  }
}

// Singleton attached to window
if (!window.__uploadManager) {
  window.__uploadManager = new UploadManager();
}

export default window.__uploadManager;
