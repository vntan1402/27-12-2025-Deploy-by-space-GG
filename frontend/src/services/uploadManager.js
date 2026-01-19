/**
 * Upload Manager - V3
 * Simply sends files to backend, backend handles everything in background
 * Similar to Auto Rename approach
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

class UploadManager {
  constructor() {
    console.log('📦 [UploadManager V3] Initialized');
  }
  
  /**
   * V3: Send all files to backend, backend processes in background
   * Frontend just needs to poll status - no more client-side scheduling
   */
  async startUpload({ taskId, files, apiEndpoint, staggerDelayMs = 100 }) {
    const api = getApi();
    
    console.log(`📤 [UploadManager V3] Sending ${files.length} files to backend for task ${taskId}`);
    
    const fileArray = Array.from(files);
    
    // Send files one by one to backend's add-file endpoint
    // Backend stores them, then processes in background
    for (let i = 0; i < fileArray.length; i++) {
      const file = fileArray[i];
      const filename = file.name || `file_${i}`;
      
      try {
        console.log(`📤 [UploadManager V3] Sending file ${i + 1}/${fileArray.length}: ${filename}`);
        
        const formData = new FormData();
        formData.append('file', file, filename);
        
        await api.post(
          `${apiEndpoint}${taskId}/add-file`,
          formData,
          {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 60000 // 1 min per file for sending
          }
        );
        
        // Small delay between sends to avoid overwhelming server
        if (i < fileArray.length - 1 && staggerDelayMs > 0) {
          await new Promise(resolve => setTimeout(resolve, staggerDelayMs));
        }
        
      } catch (error) {
        console.error(`❌ [UploadManager V3] Error sending ${filename}:`, error.message);
        // Continue with other files
      }
    }
    
    console.log(`📤 [UploadManager V3] All files sent. Starting backend processing...`);
    
    // Tell backend to start processing
    try {
      await api.post(`${apiEndpoint}${taskId}/start-processing`);
      console.log(`✅ [UploadManager V3] Backend processing started for task ${taskId}`);
    } catch (error) {
      console.error(`❌ [UploadManager V3] Error starting processing:`, error.message);
    }
  }
  
  // Legacy methods for compatibility
  cancelUpload(taskId) {
    console.log(`🚫 [UploadManager V3] Cancel request for ${taskId}`);
  }
  
  getStatus(taskId) {
    return null;
  }
  
  isCancelled(taskId) {
    return false;
  }
}

// Simple singleton
if (!window.__uploadManager) {
  window.__uploadManager = new UploadManager();
}

export default window.__uploadManager;
