/**
 * Audit Report Service
 * API calls for audit report management
 */
import api from './api';
import { API_TIMEOUT } from '../constants/api';

export const auditReportService = {
  /**
   * Get all audit reports for a ship
   */
  getAll: async (shipId) => {
    return await api.get(`/api/audit-reports?ship_id=${shipId}`);
  },

  /**
   * Create new audit report
   */
  create: async (reportData) => {
    return await api.post('/api/audit-reports', reportData);
  },

  /**
   * Update existing audit report
   */
  update: async (reportId, reportData) => {
    return await api.put(`/api/audit-reports/${reportId}`, reportData);
  },

  /**
   * Delete single audit report
   */
  delete: async (reportId) => {
    return await api.delete(`/api/audit-reports/${reportId}`);
  },

  /**
   * Bulk delete audit reports
   */
  bulkDelete: async (reportIds) => {
    return await api.post('/api/audit-reports/bulk-delete', { 
      report_ids: reportIds 
    });
  },

  /**
   * Analyze audit report file using AI
   */
  analyzeFile: async (shipId, file, bypassValidation = false) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('ship_id', shipId);
    formData.append('bypass_validation', bypassValidation ? 'true' : 'false'); // Convert boolean to string like Survey Report
    
    return await api.post('/api/audit-reports/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: API_TIMEOUT.AI_ANALYSIS, // 90 seconds for AI processing (same as Survey Report)
    });
  },

  /**
   * Upload audit report files to Google Drive
   */
  uploadFiles: async (reportId, fileContent, filename, contentType, summaryText = null) => {
    return await api.post(`/api/audit-reports/${reportId}/upload-files`, {
      file_content: fileContent,
      filename: filename,
      content_type: contentType,
      summary_text: summaryText
    }, {
      timeout: API_TIMEOUT.FILE_UPLOAD, // 60 seconds for file upload (same as Survey Report)
    });
  }
};
