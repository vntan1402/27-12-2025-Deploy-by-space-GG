/**
 * Other Audit Documents Service
 * API service for managing other audit documents
 * 
 * Endpoints:
 * - GET /api/other-audit-documents?ship_id={id} - Get all other audit documents for a ship
 * - POST /api/other-audit-documents - Create new document (manual entry)
 * - PUT /api/other-audit-documents/{id} - Update document
 * - DELETE /api/other-audit-documents/{id} - Delete document
 * - POST /api/other-audit-documents/upload - Upload single file
 * - POST /api/other-audit-documents/upload-folder - Upload folder
 * - POST /api/other-audit-documents/upload-file-only - Upload file without creating record
 */

import api from './api';

const otherAuditDocumentService = {
  /**
   * Get all other audit documents for a specific ship
   */
  getAll: async (shipId) => {
    const response = await api.get(`/api/other-audit-documents?ship_id=${shipId}`);
    return response.data;
  },

  /**
   * Create a new other document (manual entry)
   */
  create: async (documentData) => {
    const response = await api.post('/api/other-audit-documents', documentData);
    return response.data;
  },

  /**
   * Update an existing other document
   */
  update: async (documentId, documentData) => {
    const response = await api.put(`/api/other-audit-documents/${documentId}`, documentData);
    return response.data;
  },

  /**
   * Delete an other audit document
   */
  delete: async (documentId) => {
    console.log('🗑️ Deleting other audit document:', documentId);
    try {
      const response = await api.delete(`/api/other-audit-documents/${documentId}?background=true`);
      console.log('✅ Delete response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Delete error:', error);
      throw error;
    }
  },

  /**
   * Upload files for other audit documents
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
        const response = await api.post('/api/other-audit-documents/upload', formData, {
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
    
    console.log('📤 Uploading audit file for document:', documentId, 'file:', file.name);
    
    // Retry loop for handling 429 rate limit errors
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        // Use new endpoint that handles both upload AND update
        const response = await api.post(`/api/other-audit-documents/${documentId}/upload-file`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5 minutes timeout
        });
        
        console.log('📦 Upload response:', response.data);
        
        if (response.data.success && response.data.file_id) {
          console.log('✅ Audit file uploaded and document updated:', response.data.file_id);
          
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
   * Upload folder with multiple files - CHUNKED UPLOAD
   * Uploads files one by one to avoid 413 Content Too Large error
   * With real-time progress callback for UI tracking
   * Supports cancellation via AbortController signal
   */
  uploadFolder: async (shipId, files, folderName, metadata, progressCallback = null, cancelSignal = null) => {
    const results = {
      success: true,
      folder_link: null,
      total_files: files.length,
      uploaded_files: 0,
      successful_files: 0,
      failed_files: [],
      document_id: null,
      cancelled: false
    };
    
    // Step 1: Create the document record first (without files)
    try {
      // Check if cancelled before starting
      if (cancelSignal?.aborted) {
        return { success: false, cancelled: true, message: 'Upload cancelled' };
      }
      
      const createResponse = await api.post('/api/other-audit-documents', {
        ship_id: shipId,
        document_name: folderName,  // API expects 'document_name' not 'name'
        date: metadata.date || null,
        status: metadata.status || 'Valid',
        note: metadata.note || ''
      });
      
      results.document_id = createResponse.data.id;
      console.log(`📁 Created document record: ${results.document_id}`);
    } catch (error) {
      console.error('❌ Failed to create document record:', error);
      return {
        success: false,
        error: 'Failed to create document record: ' + (error.response?.data?.detail || error.message)
      };
    }
    
    // Step 2: Upload files one by one (chunked)
    for (let i = 0; i < files.length; i++) {
      // Check if cancelled
      if (cancelSignal?.aborted) {
        console.log('🛑 Upload cancelled by user');
        results.cancelled = true;
        results.success = results.uploaded_files > 0;
        results.message = `Upload cancelled. ${results.uploaded_files}/${files.length} files uploaded.`;
        break;
      }
      
      const file = files[i];
      
      // Update progress
      if (progressCallback) {
        progressCallback({
          completedFiles: i,
          currentFile: file.name,
          totalFiles: files.length
        });
      }
      
      // Skip system files
      if (file.name === 'desktop.ini' || file.name === '.DS_Store' || file.name === 'Thumbs.db') {
        console.log(`⏭️ Skipping system file: ${file.name}`);
        results.uploaded_files++;
        continue;
      }
      
      try {
        // Upload single file to the document
        const formData = new FormData();
        formData.append('file', file);
        
        const uploadResponse = await api.post(
          `/api/other-audit-documents/${results.document_id}/upload-single-file`,
          formData,
          {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 60000 // 1 minute per file
          }
        );
        
        results.uploaded_files++;
        
        // Get folder_link from first successful upload
        if (!results.folder_link && uploadResponse.data?.folder_link) {
          results.folder_link = uploadResponse.data.folder_link;
        }
        
        console.log(`✅ [${i + 1}/${files.length}] Uploaded: ${file.name}`);
        
      } catch (error) {
        console.error(`❌ [${i + 1}/${files.length}] Failed: ${file.name}`, error.message);
        results.failed_files.push({
          name: file.name,
          error: error.response?.data?.detail || error.message
        });
        
        // Continue with next file instead of stopping
      }
    }
    
    // Final progress update
    if (progressCallback) {
      progressCallback({
        completedFiles: files.length,
        currentFile: '',
        totalFiles: files.length
      });
    }
    
    // Determine overall success
    results.success = results.uploaded_files > 0;
    results.message = results.success
      ? `Uploaded ${results.uploaded_files}/${files.length} files`
      : 'Failed to upload any files';
    
    if (results.failed_files.length > 0) {
      results.message += ` (${results.failed_files.length} failed)`;
    }
    
    return results;
  },

  /**
   * Change status of a document
   */
  changeStatus: async (documentId, newStatus) => {
    const response = await api.put(`/api/other-audit-documents/${documentId}`, {
      status: newStatus
    });
    return response.data;
  }
};

export default otherAuditDocumentService;
