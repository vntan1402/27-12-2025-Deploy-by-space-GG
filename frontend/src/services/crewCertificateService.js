/**
 * Crew Certificate Service
 * 
 * API calls for CREW certificate management
 * Handles CRUD operations for crew certificates (NOT ship certificates)
 * 
 * Note: This service is specifically for CREW certificates.
 * For ship certificates, use shipCertificateService.js
 */

import api from './api';
import { API_ENDPOINTS, API_TIMEOUT } from '../constants/api';

/**
 * Crew Certificate Service
 * All API methods for crew certificate management
 */
export const crewCertificateService = {
  /**
   * Get all crew certificates
   * @param {object} filters - Optional filters (crew_id, ship_id, status, etc.)
   * @returns {Promise} List of crew certificates
   */
  getAll: async (filters = {}) => {
    return api.get(API_ENDPOINTS.CREW_CERTIFICATES, { params: filters });
  },

  /**
   * Get crew certificate by ID
   * @param {string} certId - Crew certificate ID
   * @returns {Promise} Crew certificate data
   */
  getById: async (certId) => {
    return api.get(API_ENDPOINTS.CREW_CERTIFICATE_BY_ID(certId));
  },

  /**
   * Create new crew certificate
   * @param {object} certData - Crew certificate data
   * @returns {Promise} Created crew certificate
   */
  create: async (certData) => {
    return api.post(API_ENDPOINTS.CREW_CERTIFICATES, certData);
  },

  /**
   * Update crew certificate
   * @param {string} certId - Crew certificate ID
   * @param {object} certData - Updated crew certificate data
   * @returns {Promise} Updated crew certificate
   */
  update: async (certId, certData) => {
    return api.put(API_ENDPOINTS.CREW_CERTIFICATE_BY_ID(certId), certData);
  },

  /**
   * Delete crew certificate
   * @param {string} certId - Crew certificate ID
   * @returns {Promise} Delete result
   */
  delete: async (certId) => {
    return api.delete(API_ENDPOINTS.CREW_CERTIFICATE_BY_ID(certId));
  },

  /**
   * Bulk delete crew certificates
   * @param {string[]} certIds - Array of crew certificate IDs
   * @returns {Promise} Delete result
   */
  bulkDelete: async (certIds) => {
    return api.post(API_ENDPOINTS.CREW_CERTIFICATE_BULK_DELETE, {
      certificate_ids: certIds,
    });
  },

  /**
   * Analyze crew certificate file with AI
   * @param {File} certFile - Crew certificate file (PDF)
   * @param {string} crewId - Crew ID
   * @param {string} aiProvider - AI provider ('gemini' or 'openai')
   * @param {string} aiModel - AI model name
   * @param {boolean} useEmergentKey - Whether to use Emergent LLM key
   * @returns {Promise} Analysis result with extracted data
   */
  analyzeFile: async (certFile, crewId, aiProvider, aiModel, useEmergentKey) => {
    const formData = new FormData();
    formData.append('certificate_file', certFile);
    formData.append('crew_id', crewId);
    formData.append('ai_provider', aiProvider);
    formData.append('ai_model', aiModel);
    formData.append('use_emergent_key', useEmergentKey);
    
    return api.post(API_ENDPOINTS.CREW_CERTIFICATE_ANALYZE, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: API_TIMEOUT.AI_ANALYSIS,
    });
  },

  /**
   * Upload crew certificate files to Google Drive
   * @param {string} certId - Crew certificate ID
   * @param {File} certFile - Crew certificate file
   * @param {File} summaryFile - Optional summary file
   * @returns {Promise} Upload result
   */
  uploadFiles: async (certId, certFile, summaryFile = null) => {
    const formData = new FormData();
    formData.append('certificate_file', certFile);
    if (summaryFile) {
      formData.append('summary_file', summaryFile);
    }
    
    return api.post(API_ENDPOINTS.CREW_CERTIFICATE_UPLOAD_FILES(certId), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: API_TIMEOUT.FILE_UPLOAD,
    });
  },

  /**
   * Check for duplicate crew certificate
   * @param {string} crewId - Crew ID
   * @param {string} certName - Crew certificate name
   * @param {string} certNo - Crew certificate number (optional)
   * @returns {Promise} Duplicate check result
   */
  checkDuplicate: async (crewId, certName, certNo = null) => {
    return api.post(API_ENDPOINTS.CREW_CERTIFICATE_CHECK_DUPLICATE, {
      crew_id: crewId,
      cert_name: certName,
      cert_no: certNo,
    });
  },

  /**
   * Get crew certificate file link
   * @param {string} certId - Crew certificate ID
   * @param {string} fileType - File type ('certificate' or 'summary')
   * @returns {Promise} File link
   */
  getFileLink: async (certId, fileType = 'certificate') => {
    return api.get(API_ENDPOINTS.CREW_CERTIFICATE_FILE_LINK(certId), {
      params: { file_type: fileType },
    });
  },

  /**
   * Download crew certificate file
   * @param {string} certId - Crew certificate ID
   * @param {string} fileType - File type ('certificate' or 'summary')
   * @returns {Promise} File blob
   */
  downloadFile: async (certId, fileType = 'certificate') => {
    const response = await api.get(API_ENDPOINTS.CREW_CERTIFICATE_FILE_LINK(certId), {
      params: { file_type: fileType },
      responseType: 'blob',
    });
    return response;
  },

  /**
   * Get crew certificates by crew ID
   * Convenient method to get all certificates for a specific crew member
   * @param {string} crewId - Crew ID
   * @returns {Promise} List of certificates for the crew member
   */
  getByCrewId: async (crewId) => {
    return api.get(API_ENDPOINTS.CREW_CERTIFICATES, {
      params: { crew_id: crewId },
    });
  },

  /**
   * Get expiring crew certificates
   * Get certificates that expire within specified days
   * @param {number} days - Number of days to look ahead (default: 30)
   * @returns {Promise} List of expiring certificates
   */
  getExpiring: async (days = 30) => {
    return api.get(API_ENDPOINTS.CREW_CERTIFICATES, {
      params: { expiring_within_days: days },
    });
  },
};
