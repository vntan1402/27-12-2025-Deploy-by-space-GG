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
    return api.post(API_ENDPOINTS.CREW_BULK_DELETE, {
      crew_ids: crewIds,
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
      timeout: 60000, // 60 seconds for file processing
    });
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
};
