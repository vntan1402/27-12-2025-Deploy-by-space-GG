/**
 * Ship Certificate Service
 * 
 * API calls for SHIP certificate management
 * Handles CRUD operations for ship certificates (NOT crew certificates)
 * 
 * Note: This service is specifically for SHIP certificates.
 * For crew certificates, use crewCertificateService.js
 */

import api from './api';
import { API_ENDPOINTS, API_TIMEOUT } from '../constants/api';

/**
 * Ship Certificate Service
 * All API methods for ship certificate management
 */
export const shipCertificateService = {
  /**
   * Get all ship certificates
   * @param {string} shipId - Optional ship ID to filter by
   * @returns {Promise} List of ship certificates
   */
  getAll: async (shipId = null) => {
    const params = shipId ? { ship_id: shipId } : {};
    return api.get(API_ENDPOINTS.CERTIFICATES, { params });
  },

  /**
   * Get ship certificate by ID
   * @param {string} certId - Ship certificate ID
   * @returns {Promise} Ship certificate data
   */
  getById: async (certId) => {
    return api.get(API_ENDPOINTS.CERTIFICATE_BY_ID(certId));
  },

  /**
   * Create new ship certificate
   * @param {object} certData - Ship certificate data
   * @returns {Promise} Created ship certificate
   */
  create: async (certData) => {
    return api.post(API_ENDPOINTS.CERTIFICATES, certData);
  },

  /**
   * Update ship certificate
   * @param {string} certId - Ship certificate ID
   * @param {object} certData - Updated ship certificate data
   * @returns {Promise} Updated ship certificate
   */
  update: async (certId, certData) => {
    return api.put(API_ENDPOINTS.CERTIFICATE_BY_ID(certId), certData);
  },

  /**
   * Delete ship certificate
   * @param {string} certId - Ship certificate ID
   * @returns {Promise} Delete result
   */
  delete: async (certId) => {
    return api.delete(API_ENDPOINTS.CERTIFICATE_BY_ID(certId));
  },

  /**
   * Bulk delete ship certificates
   * @param {string[]} certIds - Array of ship certificate IDs
   * @returns {Promise} Delete result
   */
  bulkDelete: async (certIds) => {
    return api.post(API_ENDPOINTS.CERTIFICATE_BULK_DELETE, {
      certificate_ids: certIds,
    });
  },

  /**
   * Analyze ship certificate file with AI
   * @param {string} shipId - Ship ID
   * @param {File} certFile - Ship certificate file (PDF)
   * @param {string} aiProvider - AI provider ('gemini' or 'openai')
   * @param {string} aiModel - AI model name
   * @param {boolean} useEmergentKey - Whether to use Emergent LLM key
   * @returns {Promise} Analysis result with extracted data
   */
  analyzeFile: async (shipId, certFile, aiProvider, aiModel, useEmergentKey) => {
    const formData = new FormData();
    formData.append('ship_id', shipId);
    formData.append('certificate_file', certFile);
    formData.append('ai_provider', aiProvider);
    formData.append('ai_model', aiModel);
    formData.append('use_emergent_key', useEmergentKey);
    
    return api.post(API_ENDPOINTS.CERTIFICATE_ANALYZE, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: API_TIMEOUT.AI_ANALYSIS, // 90 seconds for AI processing
    });
  },

  /**
   * Upload ship certificate files to Google Drive
   * @param {string} certId - Ship certificate ID
   * @param {File} certFile - Ship certificate file
   * @param {File} summaryFile - Optional summary file
   * @returns {Promise} Upload result
   */
  uploadFiles: async (certId, certFile, summaryFile = null) => {
    const formData = new FormData();
    formData.append('certificate_file', certFile);
    if (summaryFile) {
      formData.append('summary_file', summaryFile);
    }
    
    return api.post(API_ENDPOINTS.CERTIFICATE_UPLOAD_FILES(certId), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: API_TIMEOUT.FILE_UPLOAD,
    });
  },

  /**
   * Check for duplicate ship certificate
   * @param {string} shipId - Ship ID
   * @param {string} certName - Ship certificate name
   * @param {string} certNo - Ship certificate number
   * @returns {Promise} Duplicate check result
   */
  checkDuplicate: async (shipId, certName, certNo) => {
    return api.post(API_ENDPOINTS.CERTIFICATE_CHECK_DUPLICATE, {
      ship_id: shipId,
      cert_name: certName,
      cert_no: certNo || null,
    });
  },

  /**
   * Get ship certificate file link
   * @param {string} certId - Ship certificate ID
   * @param {string} fileType - File type ('certificate' or 'summary')
   * @returns {Promise} File link
   */
  getFileLink: async (certId, fileType = 'certificate') => {
    return api.get(API_ENDPOINTS.CERTIFICATE_FILE_LINK(certId), {
      params: { file_type: fileType },
    });
  },

  /**
   * Download ship certificate file
   * @param {string} certId - Ship certificate ID
   * @param {string} fileType - File type ('certificate' or 'summary')
   * @returns {Promise} File blob
   */
  downloadFile: async (certId, fileType = 'certificate') => {
    const response = await api.get(API_ENDPOINTS.CERTIFICATE_FILE_LINK(certId), {
      params: { file_type: fileType },
      responseType: 'blob',
    });
    return response;
  },
};
