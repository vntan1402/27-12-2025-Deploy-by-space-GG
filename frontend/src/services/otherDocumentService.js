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
   */
  uploadFileForDocument: async (documentId, shipId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('ship_id', shipId);
    
    console.log('📤 Uploading file for document:', documentId, 'file:', file.name);
    
    try {
      const response = await api.post('/api/other-documents/upload-file-only', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes timeout
      });
      
      console.log('📦 Upload response:', response.data);
      
      if (response.data.success && response.data.file_id) {
        console.log('🔄 Updating document with file_id:', response.data.file_id);
        
        // Update document with file_id
        const updateResponse = await api.put(`/api/other-documents/${documentId}`, {
          file_ids: [response.data.file_id]
        });
        
        console.log('✅ Update response:', updateResponse.data);
        console.log('✅ Document updated with file_id:', response.data.file_id);
        
        return {
          success: true,
          file_id: response.data.file_id,
          filename: response.data.filename
        };
      }
      
      console.error('❌ Upload failed - no file_id in response:', response.data);
      throw new Error('File upload failed - no file_id returned');
    } catch (error) {
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
  },

  /**
   * Upload a folder with multiple files
   */
  uploadFolder: async (shipId, files, folderName, metadata) => {
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
    
    const response = await api.post('/api/other-documents/upload-folder', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 300000, // 5 minutes timeout for folder upload
    });
    
    return response.data;
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
