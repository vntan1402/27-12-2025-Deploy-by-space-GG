/**
 * Upload Manager Singleton
 * Manages file uploads independently from React lifecycle
 * Preserves state and RESUMES uploads across module re-evaluations
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
    // Check if there's existing state in window to preserve
    const existing = window.__uploadManagerState;
    
    if (existing && existing.activeUploads && existing.activeUploads.size > 0) {
      // Restore state from previous instance
      console.log('📦 [UploadManager] Restoring existing state from window');
      this.activeUploads = existing.activeUploads;
      this.fileDataQueues = existing.fileDataQueues || new Map();
      this.cancelledTasks = existing.cancelledTasks || new Set();
      this.scheduledUploads = new Map(); // Don't restore - will re-schedule
      this.uploadedIndices = existing.uploadedIndices || new Map(); // Track which files were uploaded
      
      // CRITICAL: Resume any in-progress uploads
      this._resumeUploads();
    } else {
      // Fresh initialization
      console.log('📦 [UploadManager] Fresh initialization');
      this.activeUploads = new Map();
      this.fileDataQueues = new Map();
      this.cancelledTasks = new Set();
      this.scheduledUploads = new Map();
      this.uploadedIndices = new Map();
    }
    
    this._saveState();
  }
  
  // Resume uploads that were interrupted by page navigation
  _resumeUploads() {
    const api = getApi();
    
    this.activeUploads.forEach((uploadState, taskId) => {
      if (uploadState.inProgress && !this.cancelledTasks.has(taskId)) {
        const fileDataArray = this.fileDataQueues.get(taskId);
        if (!fileDataArray) {
          console.log(`⚠️ [UploadManager] No file data for task ${taskId}, cannot resume`);
          return;
        }
        
        const uploadedSet = this.uploadedIndices.get(taskId) || new Set();
        const remainingFiles = fileDataArray
          .map((fd, idx) => ({ fileData: fd, index: idx }))
          .filter(item => !uploadedSet.has(item.index));
        
        if (remainingFiles.length === 0) {
          console.log(`✅ [UploadManager] Task ${taskId} already completed`);
          return;
        }
        
        console.log(`🔄 [UploadManager] RESUMING task ${taskId}: ${remainingFiles.length} files remaining`);
        
        // Re-schedule remaining uploads with stagger
        const staggerDelayMs = 2000;
        remainingFiles.forEach((item, idx) => {
          const delay = idx * staggerDelayMs;
          
          window.setTimeout(() => {
            const manager = window.__uploadManager;
            if (manager && !manager.cancelledTasks.has(taskId)) {
              manager._uploadSingleFileData(
                taskId, 
                item.fileData, 
                item.index, 
                uploadState.apiEndpoint, 
                api, 
                null
              );
            }
          }, delay);
        });
        
        console.log(`📤 [UploadManager] Re-scheduled ${remainingFiles.length} uploads`);
      }
    });
  }
  
  _saveState() {
    window.__uploadManagerState = {
      activeUploads: this.activeUploads,
      fileDataQueues: this.fileDataQueues,
      cancelledTasks: this.cancelledTasks,
      uploadedIndices: this.uploadedIndices
      // Don't save scheduledUploads - timeout IDs are not transferable
    };
  }
  
  async startUpload({ taskId, files, apiEndpoint, staggerDelayMs = 2000, onProgress }) {
    const api = getApi();
    
    console.log(`📤 [UploadManager] Starting upload for task ${taskId} with ${files.length} files`);
    console.log(`📤 [UploadManager] Reading file contents into memory...`);
    
    const fileArray = Array.from(files);
    
    // Read ALL file contents into memory
    const fileDataArray = [];
    for (let i = 0; i < fileArray.length; i++) {
      const file = fileArray[i];
      try {
        const arrayBuffer = await readFileAsArrayBuffer(file);
        fileDataArray.push({
          name: file.name,
          type: file.type || 'application/octet-stream',
          size: file.size,
          data: arrayBuffer
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
    
    // Store file DATA
    this.fileDataQueues.set(taskId, fileDataArray);
    this.cancelledTasks.delete(taskId);
    this.uploadedIndices.set(taskId, new Set()); // Track uploaded file indices
    
    // Track upload state
    const uploadState = {
      taskId,
      apiEndpoint,
      totalFiles: fileDataArray.length,
      completedFiles: 0,
      failedFiles: 0,
      inProgress: true,
      startTime: Date.now()
    };
    this.activeUploads.set(taskId, uploadState);
    
    this._saveState();
    
    // Schedule uploads
    fileDataArray.forEach((fileData, index) => {
      const delay = index * staggerDelayMs;
      
      window.setTimeout(() => {
        const manager = window.__uploadManager;
        if (manager) {
          manager._uploadSingleFileData(taskId, fileData, index, apiEndpoint, api, onProgress);
        }
      }, delay);
    });
    
    console.log(`📤 [UploadManager] Scheduled ${fileDataArray.length} uploads with ${staggerDelayMs}ms stagger`);
  }
  
  async _uploadSingleFileData(taskId, fileData, index, apiEndpoint, api, onProgress) {
    const currentApi = api || getApi();
    
    // Check if already uploaded (for resume scenarios)
    const uploadedSet = this.uploadedIndices.get(taskId);
    if (uploadedSet && uploadedSet.has(index)) {
      console.log(`⏭️ [UploadManager] File ${index + 1} already uploaded, skipping`);
      return;
    }
    
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
    
    if (!fileData.data) {
      console.error(`❌ [UploadManager] No data for file ${filename}, skipping`);
      uploadState.failedFiles++;
      this._checkCompletion(taskId, uploadState, onProgress);
      return;
    }
    
    try {
      // Check task status from server
      try {
        const statusCheck = await currentApi.get(`${apiEndpoint}${taskId}`);
        if (statusCheck.data?.status === 'cancelled') {
          console.log(`🚫 [UploadManager] Task ${taskId} cancelled on server. Skipping.`);
          this.cancelledTasks.add(taskId);
          this._saveState();
          return;
        }
      } catch (e) {
        // Ignore status check errors
      }
      
      console.log(`📤 [UploadManager] Uploading ${index + 1}/${uploadState.totalFiles}: ${filename}`);
      
      const blob = new Blob([fileData.data], { type: fileData.type });
      const formData = new FormData();
      formData.append('file', blob, filename);
      
      const response = await currentApi.post(
        `${apiEndpoint}${taskId}/upload-file`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 300000
        }
      );
      
      // Mark as uploaded
      if (!this.uploadedIndices.has(taskId)) {
        this.uploadedIndices.set(taskId, new Set());
      }
      this.uploadedIndices.get(taskId).add(index);
      
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
        this._saveState();
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
      
      // Cleanup
      this.fileDataQueues.delete(taskId);
      this.uploadedIndices.delete(taskId);
    }
    
    this._saveState();
    
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
    
    this.fileDataQueues.delete(taskId);
    this.uploadedIndices.delete(taskId);
    
    const uploadState = this.activeUploads.get(taskId);
    if (uploadState) {
      uploadState.inProgress = false;
    }
    
    this._saveState();
  }
  
  getStatus(taskId) {
    return this.activeUploads.get(taskId);
  }
  
  isCancelled(taskId) {
    return this.cancelledTasks.has(taskId);
  }
}

// Always create new instance but it will restore state from window
window.__uploadManager = new UploadManager();
export default window.__uploadManager;
