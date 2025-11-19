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
   * Fixed: Changed from DELETE to POST method to match backend
   * Fixed: Changed report_ids to document_ids to match backend model
   */
  bulkDelete: async (reportIds) => {
    return await api.post('/api/audit-reports/bulk-delete', {
      document_ids: reportIds
    });
  },

  /**
   * Analyze audit report file using AI
   * Fixed: Changed endpoint from /analyze to /analyze-file to match backend
   */
  analyzeFile: async (shipId, file, bypassValidation = false) => {
    const formData = new FormData();
    formData.append('audit_report_file', file);
    formData.append('ship_id', shipId);
    formData.append('bypass_validation', bypassValidation ? 'true' : 'false');
    
    return await api.post('/api/audit-reports/analyze-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: API_TIMEOUT.AI_ANALYSIS,
      transformRequest: [(data) => data]
    });
  },

  /**
   * Upload audit report files to Google Drive
   * Using JSON body (not FormData) to match backend Form(...) signature
   */
  uploadFiles: async (reportId, fileContent, filename, contentType, summaryText = null) => {
    return await api.post(`/api/audit-reports/${reportId}/upload-files`, {
      file_content: fileContent,
      filename: filename,
      content_type: contentType,
      summary_text: summaryText
    }, {
      timeout: API_TIMEOUT.FILE_UPLOAD,
    });
  }
};
