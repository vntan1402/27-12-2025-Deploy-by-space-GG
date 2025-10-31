/**
 * Survey Report Service
 * 
 * API calls for survey report management
 * Handles CRUD operations for survey reports
 */

import api from './api';
import { API_ENDPOINTS, API_TIMEOUT } from '../constants/api';

/**
 * Survey Report Service
 * All API methods for survey report management
 */
export const surveyReportService = {
  /**
   * Get all survey reports
   * @param {string} shipId - Optional ship ID to filter by
   * @returns {Promise} List of survey reports
   */
  getAll: async (shipId = null) => {
    const params = shipId ? { ship_id: shipId } : {};
    return api.get(API_ENDPOINTS.SURVEY_REPORTS, { params });
  },

  /**
   * Get survey report by ID
   * @param {string} reportId - Survey report ID
   * @returns {Promise} Survey report data
   */
  getById: async (reportId) => {
    return api.get(API_ENDPOINTS.SURVEY_REPORT_BY_ID(reportId));
  },

  /**
   * Create new survey report
   * @param {object} reportData - Survey report data
   * @returns {Promise} Created survey report
   */
  create: async (reportData) => {
    return api.post(API_ENDPOINTS.SURVEY_REPORTS, reportData);
  },

  /**
   * Update survey report
   * @param {string} reportId - Survey report ID
   * @param {object} reportData - Updated survey report data
   * @returns {Promise} Updated survey report
   */
  update: async (reportId, reportData) => {
    return api.put(API_ENDPOINTS.SURVEY_REPORT_BY_ID(reportId), reportData);
  },

  /**
   * Delete survey report
   * @param {string} reportId - Survey report ID
   * @returns {Promise} Delete result
   */
  delete: async (reportId) => {
    return api.delete(API_ENDPOINTS.SURVEY_REPORT_BY_ID(reportId));
  },

  /**
   * Bulk delete survey reports
   * @param {string[]} reportIds - Array of survey report IDs
   * @returns {Promise} Delete result
   */
  bulkDelete: async (reportIds) => {
    return api.delete(API_ENDPOINTS.SURVEY_REPORT_BULK_DELETE, {
      data: { report_ids: reportIds }
    });
  },

  /**
   * Analyze survey report file with AI
   * @param {string} shipId - Ship ID
   * @param {File} reportFile - Survey report file (PDF)
   * @param {boolean} bypassValidation - Skip ship name validation (default: false)
   * @returns {Promise} Analysis result with extracted data
   */
  analyzeFile: async (shipId, reportFile, bypassValidation = false) => {
    const formData = new FormData();
    formData.append('ship_id', shipId);
    formData.append('survey_report_file', reportFile);
    formData.append('bypass_validation', bypassValidation ? 'true' : 'false');
    
    return api.post(API_ENDPOINTS.SURVEY_REPORT_ANALYZE, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: API_TIMEOUT.AI_ANALYSIS, // 90 seconds for large PDFs
    });
  },

  /**
   * Upload survey report files to Google Drive
   * @param {string} reportId - Survey report ID
   * @param {File} reportFile - Survey report file
   * @param {File} summaryFile - Optional summary file
   * @returns {Promise} Upload result
   */
  uploadFiles: async (reportId, reportFile, summaryFile = null) => {
    const formData = new FormData();
    formData.append('survey_report_file', reportFile);
    if (summaryFile) {
      formData.append('summary_file', summaryFile);
    }
    
    return api.post(API_ENDPOINTS.SURVEY_REPORT_UPLOAD_FILES(reportId), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: API_TIMEOUT.FILE_UPLOAD,
    });
  },

  /**
   * Check for duplicate survey report
   * @param {string} shipId - Ship ID
   * @param {string} reportName - Survey report name
   * @param {string} reportNo - Survey report number (optional)
   * @returns {Promise} Duplicate check result
   */
  checkDuplicate: async (shipId, reportName, reportNo = null) => {
    return api.post(API_ENDPOINTS.SURVEY_REPORT_CHECK_DUPLICATE, {
      ship_id: shipId,
      survey_report_name: reportName,
      survey_report_no: reportNo,
    });
  },

  /**
   * Get survey report file link
   * @param {string} reportId - Survey report ID
   * @param {string} fileType - File type ('survey_report' or 'summary')
   * @returns {Promise} File link
   */
  getFileLink: async (reportId, fileType = 'survey_report') => {
    return api.get(API_ENDPOINTS.SURVEY_REPORT_FILE_LINK(reportId), {
      params: { file_type: fileType },
    });
  },

  /**
   * Download survey report file
   * @param {string} reportId - Survey report ID
   * @param {string} fileType - File type ('survey_report' or 'summary')
   * @returns {Promise} File blob
   */
  downloadFile: async (reportId, fileType = 'survey_report') => {
    const response = await api.get(API_ENDPOINTS.SURVEY_REPORT_FILE_LINK(reportId), {
      params: { file_type: fileType },
      responseType: 'blob',
    });
    return response;
  },
};
