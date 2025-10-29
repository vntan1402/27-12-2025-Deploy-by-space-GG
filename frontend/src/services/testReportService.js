/**
 * Test Report Service
 * 
 * API calls for test report management
 * Handles CRUD operations for test reports (fire extinguisher, life raft, etc.)
 */

import api from './api';
import { API_ENDPOINTS, API_TIMEOUT } from '../constants/api';

/**
 * Test Report Service
 * All API methods for test report management
 */
export const testReportService = {
  /**
   * Get all test reports
   * @param {string} shipId - Optional ship ID to filter by
   * @returns {Promise} List of test reports
   */
  getAll: async (shipId = null) => {
    const params = shipId ? { ship_id: shipId } : {};
    return api.get(API_ENDPOINTS.TEST_REPORTS, { params });
  },

  /**
   * Get test report by ID
   * @param {string} reportId - Test report ID
   * @returns {Promise} Test report data
   */
  getById: async (reportId) => {
    return api.get(API_ENDPOINTS.TEST_REPORT_BY_ID(reportId));
  },

  /**
   * Create new test report
   * @param {object} reportData - Test report data
   * @returns {Promise} Created test report
   */
  create: async (reportData) => {
    return api.post(API_ENDPOINTS.TEST_REPORTS, reportData);
  },

  /**
   * Update test report
   * @param {string} reportId - Test report ID
   * @param {object} reportData - Updated test report data
   * @returns {Promise} Updated test report
   */
  update: async (reportId, reportData) => {
    return api.put(API_ENDPOINTS.TEST_REPORT_BY_ID(reportId), reportData);
  },

  /**
   * Delete test report
   * @param {string} reportId - Test report ID
   * @returns {Promise} Delete result
   */
  delete: async (reportId) => {
    return api.delete(API_ENDPOINTS.TEST_REPORT_BY_ID(reportId));
  },

  /**
   * Bulk delete test reports
   * @param {string[]} reportIds - Array of test report IDs
   * @returns {Promise} Delete result
   */
  bulkDelete: async (reportIds) => {
    return api.post(API_ENDPOINTS.TEST_REPORT_BULK_DELETE, {
      report_ids: reportIds,
    });
  },

  /**
   * Analyze test report file with AI
   * @param {string} shipId - Ship ID
   * @param {File} reportFile - Test report file (PDF)
   * @param {string} aiProvider - AI provider ('gemini' or 'openai')
   * @param {string} aiModel - AI model name
   * @param {boolean} useEmergentKey - Whether to use Emergent LLM key
   * @returns {Promise} Analysis result with extracted data
   */
  analyzeFile: async (shipId, reportFile, aiProvider, aiModel, useEmergentKey) => {
    const formData = new FormData();
    formData.append('ship_id', shipId);
    formData.append('test_report_file', reportFile);
    formData.append('ai_provider', aiProvider);
    formData.append('ai_model', aiModel);
    formData.append('use_emergent_key', useEmergentKey);
    
    return api.post(API_ENDPOINTS.TEST_REPORT_ANALYZE, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: API_TIMEOUT.AI_ANALYSIS,
    });
  },

  /**
   * Upload test report files to Google Drive
   * @param {string} reportId - Test report ID
   * @param {File} reportFile - Test report file
   * @param {File} summaryFile - Optional summary file
   * @returns {Promise} Upload result
   */
  uploadFiles: async (reportId, reportFile, summaryFile = null) => {
    const formData = new FormData();
    formData.append('test_report_file', reportFile);
    if (summaryFile) {
      formData.append('summary_file', summaryFile);
    }
    
    return api.post(API_ENDPOINTS.TEST_REPORT_UPLOAD_FILES(reportId), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: API_TIMEOUT.FILE_UPLOAD,
    });
  },

  /**
   * Check for duplicate test report
   * @param {string} shipId - Ship ID
   * @param {string} reportName - Test report name
   * @param {string} reportNo - Test report number (optional)
   * @returns {Promise} Duplicate check result
   */
  checkDuplicate: async (shipId, reportName, reportNo = null) => {
    return api.post(API_ENDPOINTS.TEST_REPORT_CHECK_DUPLICATE, {
      ship_id: shipId,
      test_report_name: reportName,
      test_report_no: reportNo,
    });
  },

  /**
   * Get test report file link
   * @param {string} reportId - Test report ID
   * @param {string} fileType - File type ('test_report' or 'summary')
   * @returns {Promise} File link
   */
  getFileLink: async (reportId, fileType = 'test_report') => {
    return api.get(API_ENDPOINTS.TEST_REPORT_FILE_LINK(reportId), {
      params: { file_type: fileType },
    });
  },

  /**
   * Download test report file
   * @param {string} reportId - Test report ID
   * @param {string} fileType - File type ('test_report' or 'summary')
   * @returns {Promise} File blob
   */
  downloadFile: async (reportId, fileType = 'test_report') => {
    const response = await api.get(API_ENDPOINTS.TEST_REPORT_FILE_LINK(reportId), {
      params: { file_type: fileType },
      responseType: 'blob',
    });
    return response;
  },
};
