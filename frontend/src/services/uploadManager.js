/**
 * Upload Manager Singleton
 * Manages file uploads independently from React lifecycle
 * Attached to window object to persist across page navigation and hot reload
 */

import api from './api';

class UploadManager {
  constructor() {
    // Store active uploads by taskId
    this.activeUploads = new Map();
    // Store file queues by taskId  
    this.fileQueues = new Map();
    // Cancelled tasks
    this.cancelledTasks = new Set();
    // Active timeouts (to track scheduled uploads)
    this.scheduledUploads = new Map();
    
    console.log('📦 [UploadManager] Initialized');
  }
  
  /**
   * Start staggered file upload
   * @param {Object} config Upload configuration
   * @param {string} config.taskId Task ID
   * @param {File[]} config.files Array of File objects
   * @param {string} config.apiEndpoint API endpoint base
   * @param {number} config.staggerDelayMs Delay between file uploads (default 2000ms)
   * @param {Function} config.onProgress Callback for progress updates
   */
  startUpload({ taskId, files, apiEndpoint, staggerDelayMs = 2000, onProgress }) {
    console.log(`📤 [UploadManager] Starting upload for task ${taskId} with ${files.length} files`);
    
    // Store files in queue (convert FileList to Array if needed)
    const fileArray = Array.from(files);
    this.fileQueues.set(taskId, fileArray);
    this.cancelledTasks.delete(taskId);
    
    // Track upload state
    const uploadState = {
      taskId,
      totalFiles: fileArray.length,
      completedFiles: 0,
      failedFiles: 0,
      inProgress: true,
      startTime: Date.now()
    };
    this.activeUploads.set(taskId, uploadState);
    
    // Store scheduled timeouts
    const timeoutIds = [];
    
    // Schedule each file upload with staggered delay
    fileArray.forEach((file, index) => {
      const delay = index * staggerDelayMs;
      
      const timeoutId = setTimeout(() => {
        this._uploadSingleFile(taskId, file, index, apiEndpoint, onProgress);
      }, delay);
      
      timeoutIds.push(timeoutId);
    });
    
    this.scheduledUploads.set(taskId, timeoutIds);
    
    console.log(`📤 [UploadManager] Scheduled ${fileArray.length} uploads with ${staggerDelayMs}ms stagger`);
  }
  
  /**
   * Upload a single file
   */
  async _uploadSingleFile(taskId, file, index, apiEndpoint, onProgress) {
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
    
    const filename = file.name || `file_${index}`;
    
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
      
      const formData = new FormData();
      formData.append('file', file, filename);
      
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
      // Check if cancelled
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
    
    // Check if all files processed
    const processed = uploadState.completedFiles + uploadState.failedFiles;
    if (processed >= uploadState.totalFiles) {
      uploadState.inProgress = false;
      console.log(`✅ [UploadManager] Task ${taskId} complete. Success: ${uploadState.completedFiles}, Failed: ${uploadState.failedFiles}`);
      
      // Cleanup
      this.fileQueues.delete(taskId);
      this.scheduledUploads.delete(taskId);
    }
    
    // Notify progress if callback provided
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
  
  /**
   * Cancel an upload
   */
  cancelUpload(taskId) {
    console.log(`🚫 [UploadManager] Cancelling task ${taskId}`);
    this.cancelledTasks.add(taskId);
    
    // Clear scheduled timeouts
    const timeoutIds = this.scheduledUploads.get(taskId);
    if (timeoutIds) {
      timeoutIds.forEach(id => clearTimeout(id));
      this.scheduledUploads.delete(taskId);
    }
    
    const uploadState = this.activeUploads.get(taskId);
    if (uploadState) {
      uploadState.inProgress = false;
    }
  }
  
  /**
   * Get upload status
   */
  getStatus(taskId) {
    return this.activeUploads.get(taskId);
  }
  
  /**
   * Check if task is cancelled
   */
  isCancelled(taskId) {
    return this.cancelledTasks.has(taskId);
  }
}

// Create or reuse singleton instance attached to window
// This ensures it persists across hot reload and page navigation
if (!window.__uploadManager) {
  window.__uploadManager = new UploadManager();
}

const uploadManager = window.__uploadManager;
export default uploadManager;
