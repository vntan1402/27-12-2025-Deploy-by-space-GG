/**
 * Crew Service
 * 
 * API calls for crew management
 * Handles CRUD operations for crew members
 */

import api from './api';
import { API_ENDPOINTS } from '../constants/api';

/**
 * Crew Service
 * All API methods for crew management
 */
export const crewService = {
  /**
   * Get all crews
   * @param {string} shipId - Optional ship ID to filter by
   * @returns {Promise} List of crews
   */
  getAll: async (shipId = null) => {
    const params = shipId ? { ship_id: shipId } : {};
    return api.get(API_ENDPOINTS.CREWS, { params });
  },

  /**
   * Get crew by ID
   * @param {string} crewId - Crew ID
   * @returns {Promise} Crew data
   */
  getById: async (crewId) => {
    return api.get(API_ENDPOINTS.CREW_BY_ID(crewId));
  },

  /**
   * Create new crew
   * @param {object} crewData - Crew data
   * @returns {Promise} Created crew
   */
  create: async (crewData) => {
    return api.post(API_ENDPOINTS.CREWS, crewData);
  },

  /**
   * Update crew
   * @param {string} crewId - Crew ID
   * @param {object} crewData - Updated crew data
   * @returns {Promise} Updated crew
   */
  update: async (crewId, crewData) => {
    return api.put(API_ENDPOINTS.CREW_BY_ID(crewId), crewData);
  },

  /**
   * Delete crew
   * @param {string} crewId - Crew ID
   * @returns {Promise} Delete result
   */
  delete: async (crewId) => {
    return api.delete(API_ENDPOINTS.CREW_BY_ID(crewId));
  },

  /**
   * Bulk delete crews
   * @param {string[]} crewIds - Array of crew IDs
   * @returns {Promise} Delete result
   */
  bulkDelete: async (crewIds) => {
    return api.delete(API_ENDPOINTS.CREW_BULK_DELETE, {
      data: {
        crew_ids: crewIds,
      }
    });
  },

  /**
   * Upload and analyze passport file
   * @param {File} passportFile - Passport file (PDF/Image)
   * @returns {Promise} Analysis result with extracted data
   */
  uploadPassport: async (passportFile) => {
    const formData = new FormData();
    formData.append('passport_file', passportFile);
    
    return api.post(API_ENDPOINTS.PASSPORT_ANALYZE, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 90000, // 90 seconds for file processing
    });
  },

  /**
   * Analyze passport with AI (V2 pattern - analysis only, no upload)
   * @param {File} file - Passport file
   * @param {string} shipName - Ship name for folder structure
   * @returns {Promise} Analysis result with extracted data and file content
   */
  analyzePassport: async (file, shipName) => {
    const formData = new FormData();
    formData.append('passport_file', file);
    formData.append('ship_name', shipName);
    
    return api.post('/api/crew/analyze-passport', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 120000 // 2 minutes for AI analysis
    });
  },
  
  /**
   * Create crew member (without files)
   * @param {object} crewData - Crew data
   * @returns {Promise} Created crew
   */
  createCrew: async (crewData) => {
    return api.post('/api/crew', crewData);
  },
  
  /**
   * Upload passport files after crew creation (background)
   * @param {string} crewId - Crew ID
   * @param {object} fileData - File data with base64 content
   * @returns {Promise} Upload result
   */
  uploadPassportFiles: async (crewId, fileData) => {
    return api.post(`/api/crew/${crewId}/upload-passport-files`, fileData, {
      timeout: 300000 // 5 minutes for file upload
    });
  },
  
  /**
   * Get all crew members with filters
   * @param {object} filters - Filter options (ship_name, status)
   * @returns {Promise} List of crew members
   */
  getCrewList: async (filters = {}) => {
    const params = new URLSearchParams();
    
    if (filters.ship_name && filters.ship_name !== 'All') {
      params.append('ship_name', filters.ship_name);
    }
    
    if (filters.status && filters.status !== 'All') {
      params.append('status', filters.status);
    }
    
    const url = params.toString() ? `/api/crew?${params.toString()}` : '/api/crew';
    return api.get(url);
  },

  /**
   * Move standby crew files to active ship folder
   * @param {string} crewId - Crew ID
   * @returns {Promise} Move result
   */
  moveStandbyFiles: async (crewId) => {
    return api.post(API_ENDPOINTS.CREW_MOVE_STANDBY_FILES, {
      crew_id: crewId,
    });
  },

  /**
   * Auto-rename passport files
   * @param {string} crewId - Crew ID
   * @returns {Promise} Rename result
   */
  renameFiles: async (crewId) => {
    return api.post(`/api/crew/${crewId}/rename-files`);
  }
};
