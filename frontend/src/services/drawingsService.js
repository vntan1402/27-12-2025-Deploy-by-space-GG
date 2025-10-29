/**
 * Drawings & Manuals Service
 * 
 * API calls for drawings and manuals management
 * Handles CRUD operations for ship drawings and manuals
 */

import api from './api';
import { API_ENDPOINTS, API_TIMEOUT } from '../constants/api';

/**
 * Drawings & Manuals Service
 * All API methods for drawings and manuals management
 */
export const drawingsService = {
  /**
   * Get all drawings & manuals
   * @param {string} shipId - Ship ID (required for drawings)
   * @returns {Promise} List of drawings & manuals
   */
  getAll: async (shipId) => {
    return api.get(API_ENDPOINTS.DRAWINGS_MANUALS, {
      params: { ship_id: shipId },
    });
  },

  /**
   * Get drawing/manual by ID
   * @param {string} docId - Document ID
   * @returns {Promise} Document data
   */
  getById: async (docId) => {
    return api.get(API_ENDPOINTS.DRAWINGS_MANUALS_BY_ID(docId));
  },

  /**
   * Create new drawing/manual
   * @param {object} docData - Document data
   * @returns {Promise} Created document
   */
  create: async (docData) => {
    return api.post(API_ENDPOINTS.DRAWINGS_MANUALS, docData);
  },

  /**
   * Update drawing/manual
   * @param {string} docId - Document ID
   * @param {object} docData - Updated document data
   * @returns {Promise} Updated document
   */
  update: async (docId, docData) => {
    return api.put(API_ENDPOINTS.DRAWINGS_MANUALS_BY_ID(docId), docData);
  },

  /**
   * Delete drawing/manual
   * @param {string} docId - Document ID
   * @returns {Promise} Delete result
   */
  delete: async (docId) => {
    return api.delete(API_ENDPOINTS.DRAWINGS_MANUALS_BY_ID(docId));
  },

  /**
   * Bulk delete drawings & manuals
   * @param {string[]} docIds - Array of document IDs
   * @returns {Promise} Delete result
   */
  bulkDelete: async (docIds) => {
    return api.post(API_ENDPOINTS.DRAWINGS_MANUALS_BULK_DELETE, {
      document_ids: docIds,
    });
  },

  /**
   * Check for duplicate drawing/manual
   * @param {string} shipId - Ship ID
   * @param {string} docName - Document name
   * @param {string} docNo - Document number (optional)
   * @returns {Promise} Duplicate check result
   */
  checkDuplicate: async (shipId, docName, docNo = null) => {
    return api.post(API_ENDPOINTS.DRAWINGS_MANUALS_CHECK_DUPLICATE, {
      ship_id: shipId,
      document_name: docName,
      document_no: docNo,
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
    
    return api.post(API_ENDPOINTS.DRAWINGS_MANUALS_UPLOAD_FILE(docId), formData, {
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
    return api.get(API_ENDPOINTS.DRAWINGS_MANUALS_FILE_LINK(docId));
  },

  /**
   * Download file
   * @param {string} docId - Document ID
   * @returns {Promise} File blob
   */
  downloadFile: async (docId) => {
    const response = await api.get(API_ENDPOINTS.DRAWINGS_MANUALS_FILE_LINK(docId), {
      responseType: 'blob',
    });
    return response;
  },
};
