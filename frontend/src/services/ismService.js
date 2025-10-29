/**
 * ISM Service
 * 
 * API calls for ISM (International Safety Management) documents
 * Handles CRUD operations for ISM documents
 */

import api from './api';
import { API_ENDPOINTS, API_TIMEOUT } from '../constants/api';

/**
 * ISM Service
 * All API methods for ISM documents management
 */
export const ismService = {
  /**
   * Get all ISM documents
   * @param {string} shipId - Optional ship ID to filter by
   * @returns {Promise} List of ISM documents
   */
  getAll: async (shipId = null) => {
    const params = shipId ? { ship_id: shipId } : {};
    return api.get(API_ENDPOINTS.ISM_DOCUMENTS, { params });
  },

  /**
   * Get ISM document by ID
   * @param {string} docId - Document ID
   * @returns {Promise} Document data
   */
  getById: async (docId) => {
    return api.get(API_ENDPOINTS.ISM_DOCUMENT_BY_ID(docId));
  },

  /**
   * Create new ISM document
   * @param {object} docData - Document data
   * @returns {Promise} Created document
   */
  create: async (docData) => {
    return api.post(API_ENDPOINTS.ISM_DOCUMENTS, docData);
  },

  /**
   * Update ISM document
   * @param {string} docId - Document ID
   * @param {object} docData - Updated document data
   * @returns {Promise} Updated document
   */
  update: async (docId, docData) => {
    return api.put(API_ENDPOINTS.ISM_DOCUMENT_BY_ID(docId), docData);
  },

  /**
   * Delete ISM document
   * @param {string} docId - Document ID
   * @returns {Promise} Delete result
   */
  delete: async (docId) => {
    return api.delete(API_ENDPOINTS.ISM_DOCUMENT_BY_ID(docId));
  },

  /**
   * Bulk delete ISM documents
   * @param {string[]} docIds - Array of document IDs
   * @returns {Promise} Delete result
   */
  bulkDelete: async (docIds) => {
    return api.post(API_ENDPOINTS.ISM_DOCUMENT_BULK_DELETE, {
      document_ids: docIds,
    });
  },

  /**
   * Upload file to Google Drive
   * @param {string} docId - Document ID
   * @param {File} file - File to upload
   * @returns {Promise} Upload result
   */
  uploadFile: async (docId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return api.post(API_ENDPOINTS.ISM_DOCUMENT_UPLOAD_FILE(docId), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: API_TIMEOUT.FILE_UPLOAD,
    });
  },

  /**
   * Get file link
   * @param {string} docId - Document ID
   * @returns {Promise} File link
   */
  getFileLink: async (docId) => {
    return api.get(API_ENDPOINTS.ISM_DOCUMENT_FILE_LINK(docId));
  },

  /**
   * Download file
   * @param {string} docId - Document ID
   * @returns {Promise} File blob
   */
  downloadFile: async (docId) => {
    const response = await api.get(API_ENDPOINTS.ISM_DOCUMENT_FILE_LINK(docId), {
      responseType: 'blob',
    });
    return response;
  },
};