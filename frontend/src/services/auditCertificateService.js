/**
 * Audit Certificate Service
 * 
 * API calls for AUDIT certificate management (ISM-ISPS-MLC)
 * Handles CRUD operations for audit certificates
 */

import api from './api';

/**
 * Audit Certificate Service
 * All API methods for audit certificate management
 */
export const auditCertificateService = {
  /**
   * Get all audit certificates
   * @param {string} shipId - Ship ID to filter by
   * @returns {Promise} List of audit certificates
   */
  getAll: async (shipId) => {
    const params = { ship_id: shipId };
    return api.get('/api/audit-certificates', { params });
  },

  /**
   * Get audit certificate by ID
   * @param {string} certId - Audit certificate ID
   * @returns {Promise} Audit certificate data
   */
  getById: async (certId) => {
    return api.get(`/api/audit-certificates/${certId}`);
  },

  /**
   * Create new audit certificate
   * @param {object} certData - Audit certificate data
   * @returns {Promise} Created audit certificate
   */
  create: async (certData) => {
    return api.post('/api/audit-certificates', certData);
  },

  /**
   * Update audit certificate
   * @param {string} certId - Audit certificate ID
   * @param {object} certData - Updated audit certificate data
   * @returns {Promise} Updated audit certificate
   */
  update: async (certId, certData) => {
    return api.put(`/api/audit-certificates/${certId}`, certData);
  },

  /**
   * Delete audit certificate
   * @param {string} certId - Audit certificate ID
   * @returns {Promise} Delete result
   */
  delete: async (certId) => {
    return api.delete(`/api/audit-certificates/${certId}`);
  },

  /**
   * Bulk delete audit certificates
   * @param {string[]} certIds - Array of audit certificate IDs
   * @returns {Promise} Delete result
   */
  bulkDelete: async (certIds) => {
    return api.post('/api/audit-certificates/bulk-delete', {
      cert_ids: certIds,
    });
  },

  /**
   * Bulk update audit certificates
   * @param {string[]} certIds - Array of audit certificate IDs
   * @param {object} updateData - Data to update
   * @returns {Promise} Update result
   */
  bulkUpdate: async (certIds, updateData) => {
    return api.post('/api/audit-certificates/bulk-update', {
      cert_ids: certIds,
      update_data: updateData,
    });
  },

  /**
   * Bulk update survey types
   * @param {string[]} certIds - Array of audit certificate IDs
   * @param {string} surveyType - New survey type
   * @returns {Promise} Update result
   */
  bulkUpdateSurveyTypes: async (certIds, surveyType) => {
    return api.post('/api/audit-certificates/bulk-update', {
      cert_ids: certIds,
      update_data: { next_survey_type: surveyType },
    });
  },

  /**
   * Upload audit certificate file to Google Drive
   * @param {string} certId - Audit certificate ID
   * @param {object} fileData - File data with file_id, folder_id, file_name
   * @returns {Promise} Upload result
   */
  uploadFile: async (certId, fileData) => {
    return api.post(`/api/audit-certificates/${certId}/upload-file`, fileData);
  },

  /**
   * Get audit certificate file link
   * @param {string} certId - Audit certificate ID
   * @returns {Promise} File link
   */
  getFileLink: async (certId) => {
    return api.get(`/api/audit-certificates/${certId}/file-link`);
  },

  /**
   * Batch get links for multiple certificates
   * @param {string[]} certIds - Array of audit certificate IDs
   * @returns {Promise} Array of file links
   */
  batchGetLinks: async (certIds) => {
    // For now, fetch links one by one
    const promises = certIds.map(id => auditCertificateService.getFileLink(id).catch(() => null));
    return Promise.all(promises);
  },

  /**
   * Analyze audit certificate file with AI
   * @param {File} certFile - Audit certificate file (PDF)
   * @param {string} shipId - Ship ID
   * @returns {Promise} Analysis result with extracted data
   */
  analyzeFile: async (certFile, shipId) => {
    const formData = new FormData();
    formData.append('certificate_file', certFile);
    formData.append('ship_id', shipId);
    
    return api.post('/api/audit-certificates/analyze-file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 90000, // 90 seconds for AI processing
    });
  },

  /**
   * Get upcoming audit surveys
   * @param {number} days - Number of days to check ahead
   * @param {string} company - Company name to filter
   * @returns {Promise} List of upcoming surveys
   */
  getUpcomingSurveys: async (days = 30, company = null) => {
    const params = { days };
    if (company) {
      params.company = company;
    }
    return api.get('/api/audit-certificates/upcoming-surveys', { params });
  },

  /**
   * Auto-rename audit certificate files on Google Drive
   * @param {string[]} certIds - Array of audit certificate IDs
   * @returns {Promise} Rename result
   */
  autoRename: async (certIds) => {
    // This would be implemented similar to ship certificates
    // For now, return placeholder
    return Promise.resolve({
      data: {
        success: true,
        message: 'Auto-rename feature will be implemented',
        renamed_count: 0
      }
    });
  },

  /**
   * Check for duplicate audit certificate
   * @param {string} shipId - Ship ID
   * @param {string} certName - Audit certificate name
   * @param {string} certNo - Audit certificate number
   * @returns {Promise} Duplicate check result
   */
  checkDuplicate: async (shipId, certName, certNo) => {
    // This would check if certificate already exists
    // For now, return no duplicate
    return Promise.resolve({
      data: {
        is_duplicate: false,
        existing_certificate: null
      }
    });
  },
};

export default auditCertificateService;
