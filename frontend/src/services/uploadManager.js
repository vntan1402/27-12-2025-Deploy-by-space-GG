/**
 * Upload Manager - V3 (Non-blocking)
 * Sends files to backend in parallel, doesn't block UI
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
    console.log('📦 [UploadManager V3] Initialized (Non-blocking)');
  }
  
  /**
   * V3: Send files to backend in parallel (non-blocking)
   * Returns immediately - upload continues in background
   */
  startUpload({ taskId, files, apiEndpoint, concurrentLimit = 5 }) {
    const api = getApi();
    const fileArray = Array.from(files);
    
    console.log(`📤 [UploadManager V3] Starting parallel upload of ${fileArray.length} files (concurrent: ${concurrentLimit})`);
    
    // Run upload in background - don't await
    this._uploadFilesParallel(taskId, fileArray, apiEndpoint, api, concurrentLimit);
    
    // Return immediately - UI is not blocked
    return Promise.resolve();
  }
  
  async _uploadFilesParallel(taskId, files, apiEndpoint, api, concurrentLimit) {
    let sentCount = 0;
    let failedCount = 0;
    const total = files.length;
    
    // Process files in batches
    for (let i = 0; i < files.length; i += concurrentLimit) {
      const batch = files.slice(i, i + concurrentLimit);
      
      // Upload batch in parallel
      const promises = batch.map(async (file, batchIndex) => {
        const globalIndex = i + batchIndex;
        const filename = file.name || `file_${globalIndex}`;
        
        try {
          const formData = new FormData();
          formData.append('file', file, filename);
          
          await api.post(
            `${apiEndpoint}${taskId}/add-file`,
            formData,
            {
              headers: { 'Content-Type': 'multipart/form-data' },
              timeout: 120000 // 2 min per file
            }
          );
          
          sentCount++;
          console.log(`📤 [V3] Sent ${sentCount}/${total}: ${filename}`);
          
        } catch (error) {
          failedCount++;
          console.error(`❌ [V3] Failed to send ${filename}:`, error.message);
        }
      });
      
      // Wait for batch to complete before starting next batch
      await Promise.all(promises);
    }
    
    console.log(`📤 [V3] All files sent. Success: ${sentCount}, Failed: ${failedCount}`);
    
    // Start backend processing
    if (sentCount > 0) {
      try {
        await api.post(`${apiEndpoint}${taskId}/start-processing`);
        console.log(`✅ [V3] Backend processing started for task ${taskId}`);
      } catch (error) {
        console.error(`❌ [V3] Error starting processing:`, error.message);
      }
    }
  }
  
  cancelUpload(taskId) {
    console.log(`🚫 [UploadManager V3] Cancel request for ${taskId}`);
  }
}

if (!window.__uploadManager) {
  window.__uploadManager = new UploadManager();
}

export default window.__uploadManager;
