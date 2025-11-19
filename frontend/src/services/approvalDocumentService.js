/**
 * Approval Document Service
 * Handles all API calls related to approval documents (ISM-ISPS-MLC)
 */
import api from './api';

const approvalDocumentService = {
  // Get all approval documents for a ship
  getAll: async (shipId) => {
    const response = await api.get(`/api/approval-documents?ship_id=${shipId}`);
    return response;
  },

  // Analyze file with AI
  analyzeFile: async (formData) => {
    const response = await api.post('/api/approval-documents/analyze-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response;
  },

  // Create new document
  create: async (data) => {
    const response = await api.post('/api/approval-documents', data);
    return response;
  },

  // Update document
  update: async (id, data) => {
    const response = await api.put(`/api/approval-documents/${id}`, data);
    return response;
  },

  // Delete single document
  delete: async (id, background = true) => {
    const response = await api.delete(`/api/approval-documents/${id}?background=${background}`);
    return response;
  },

  // Bulk delete documents
  bulkDelete: async (documentIds, background = true) => {
    const response = await api.post(`/api/approval-documents/bulk-delete?background=${background}`, {
      document_ids: documentIds
    });
    return response;
  },

  // Upload files to Google Drive
  uploadFiles: async (documentId, data) => {
    const response = await api.post(`/api/approval-documents/${documentId}/upload-files`, data);
    return response;
  },

  // Check for duplicate
  checkDuplicate: async (shipId, documentNo, documentName) => {
    const response = await api.post('/api/approval-documents/check-duplicate', {
      ship_id: shipId,
      approval_document_no: documentNo,
      approval_document_name: documentName
    });
    return response;
  }
};

export default approvalDocumentService;
