/**
 * Drawing Manual Service
 * Handles all API calls related to drawings and manuals
 */
import api from './api';

const drawingManualService = {
  // Get all drawings & manuals for a ship
  getAll: async (shipId) => {
    const response = await api.get(`/api/drawings-manuals?ship_id=${shipId}`);
    return response;
  },

  // Analyze file with AI
  analyzeFile: async (formData) => {
    const response = await api.post('/api/drawings-manuals/analyze-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response;
  },

  // Create new document
  create: async (data) => {
    const response = await api.post('/api/drawings-manuals', data);
    return response;
  },

  // Update document
  update: async (id, data) => {
    const response = await api.put(`/api/drawings-manuals/${id}`, data);
    return response;
  },

  // Delete single document
  delete: async (id, background = true) => {
    const response = await api.delete(`/api/drawings-manuals/${id}?background=${background}`);
    return response;
  },

  // Bulk delete documents
  bulkDelete: async (documentIds, background = true) => {
    const response = await api.delete(`/api/drawings-manuals/bulk-delete?background=${background}`, {
      data: { document_ids: documentIds }
    });
    return response;
  },

  // Upload files to Google Drive
  uploadFiles: async (documentId, data) => {
    const response = await api.post(`/api/drawings-manuals/${documentId}/upload-files`, data);
    return response;
  },

  // Check for duplicate
  checkDuplicate: async (shipId, documentNo, documentName) => {
    const response = await api.post('/api/drawings-manuals/check-duplicate', {
      ship_id: shipId,
      document_no: documentNo,
      document_name: documentName
    });
    return response;
  }
};

export default drawingManualService;
