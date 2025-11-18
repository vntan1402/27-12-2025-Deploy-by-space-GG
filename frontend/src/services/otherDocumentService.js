/**
 * Other Documents Service
 * API service for managing other documents
 * 
 * Endpoints:
 * - GET /api/other-documents?ship_id={id} - Get all other documents for a ship
 * - POST /api/other-documents - Create new document (manual entry)
 * - PUT /api/other-documents/{id} - Update document
 * - DELETE /api/other-documents/{id} - Delete document
 * - POST /api/other-documents/upload - Upload single file
 * - POST /api/other-documents/upload-folder - Upload folder
 * - POST /api/other-documents/upload-file-only - Upload file without creating record
 */

import api from './api';

const otherDocumentService = {
  /**
   * Get all other documents for a specific ship
   */
  getAll: async (shipId) => {
    const response = await api.get(`/api/other-documents?ship_id=${shipId}`);
    return response.data;
  },

  /**
   * Create a new other document (manual entry)
   */
  create: async (documentData) => {
    const response = await api.post('/api/other-documents', documentData);
    return response.data;
  },

  /**
   * Update an existing other document
   */
  update: async (documentId, documentData) => {
    const response = await api.put(`/api/other-documents/${documentId}`, documentData);
    return response.data;
  },

  /**
   * Delete an other document
   */
  delete: async (documentId) => {
    const response = await api.delete(`/api/other-documents/${documentId}?background=true`);
    return response.data;
  },

  /**
   * Upload files for other documents
   * This handles single file or multiple files
   * NO AI processing - just file upload and metadata storage
   */
  uploadFiles: async (shipId, files, metadata) => {
    // For each file, create a separate record
    const results = [];
    
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('ship_id', shipId);
      formData.append('document_name', metadata.document_name || file.name.replace(/\.[^/.]+$/, ''));
      
      if (metadata.date) formData.append('date', metadata.date);
      if (metadata.status) formData.append('status', metadata.status);
      if (metadata.note) formData.append('note', metadata.note);
      
      try {
        const response = await api.post('/api/other-documents/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5 minutes timeout for file upload
        });
        
        results.push({
          success: true,
          filename: file.name,
          data: response.data
        });
      } catch (error) {
        results.push({
          success: false,
          filename: file.name,
          error: error.response?.data?.detail || error.message
        });
      }
    }
    
    return results;
  },

  /**
   * Upload a single file and update existing document record
   * Used for background upload after record creation
   * With retry logic for rate limit errors (429)
   */
  uploadFileForDocument: async (documentId, shipId, file, retries = 3) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('ship_id', shipId);
    
    console.log('📤 Uploading file for document:', documentId, 'file:', file.name);
    
    // Retry loop for handling 429 rate limit errors
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        // Use new endpoint that handles both upload AND update
        const response = await api.post(`/api/other-documents/${documentId}/upload-file`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5 minutes timeout
        });
        
        console.log('📦 Upload response:', response.data);
        
        if (response.data.success && response.data.file_id) {
          console.log('✅ File uploaded and document updated:', response.data.file_id);
          
          return {
            success: true,
            file_id: response.data.file_id,
            filename: response.data.filename
          };
        }
        
        console.error('❌ Upload failed - no file_id in response:', response.data);
        throw new Error('File upload failed - no file_id returned');
        
      } catch (error) {
        const isRateLimit = error.response?.status === 429 || 
                           error.response?.status === 500 && 
                           error.response?.data?.detail?.includes('429');
        
        if (isRateLimit && attempt < retries - 1) {
          // Exponential backoff: 2s, 4s, 8s
          const delay = Math.pow(2, attempt + 1) * 1000;
          console.warn(`⚠️ Rate limit hit (429), retrying in ${delay/1000}s... (attempt ${attempt + 1}/${retries})`);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue; // Retry
        }
        
        // Final error after all retries or non-rate-limit error
        console.error('❌ uploadFileForDocument error:', error);
        console.error('Error details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        });
        
        return {
          success: false,
          error: error.response?.data?.detail || error.message || 'Unknown error'
        };
      }
    }
    
    // Should not reach here, but just in case
    return {
      success: false,
      error: 'Max retries exceeded'
    };
  },

  /**
   * Upload folder with multiple files
   * With optional progress callback for UI tracking
   */
  uploadFolder: async (shipId, files, folderName, metadata, progressCallback = null) => {
    const formData = new FormData();
    
    // Append all files
    files.forEach(file => {
      formData.append('files', file);
    });
    
    formData.append('ship_id', shipId);
    formData.append('folder_name', folderName);
    
    if (metadata.date) formData.append('date', metadata.date);
    if (metadata.status) formData.append('status', metadata.status);
    if (metadata.note) formData.append('note', metadata.note);
    
    // Simulate progress updates (since backend uploads in parallel, we estimate)
    if (progressCallback) {
      // Estimate: each file takes ~1.5s with staggered delay
      const estimatedTotalTime = files.length * 1500; // 1.5s per file
      const intervalTime = 500; // Update every 500ms
      const totalUpdates = Math.ceil(estimatedTotalTime / intervalTime);
      let currentUpdate = 0;
      
      const progressInterval = setInterval(() => {
        currentUpdate++;
        const estimatedCompleted = Math.floor((currentUpdate / totalUpdates) * files.length);
        const fileIndex = Math.min(estimatedCompleted, files.length - 1);
        
        progressCallback({
          completedFiles: estimatedCompleted,
          currentFile: files[fileIndex]?.name || '',
          totalFiles: files.length
        });
        
        if (currentUpdate >= totalUpdates) {
          clearInterval(progressInterval);
        }
      }, intervalTime);
      
      try {
        const response = await api.post('/api/other-documents/upload-folder', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5 minutes timeout for folder upload
        });
        
        clearInterval(progressInterval);
        
        // Final progress update
        progressCallback({
          completedFiles: files.length,
          currentFile: '',
          totalFiles: files.length
        });
        
        return response.data;
      } catch (error) {
        clearInterval(progressInterval);
        throw error;
      }
    } else {
      // No progress callback - simple upload
      const response = await api.post('/api/other-documents/upload-folder', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes timeout for folder upload
      });
      
      return response.data;
    }
  },

  /**
   * Change status of a document
   */
  changeStatus: async (documentId, newStatus) => {
    const response = await api.put(`/api/other-documents/${documentId}`, {
      status: newStatus
    });
    return response.data;
  }
};

export default otherDocumentService;
