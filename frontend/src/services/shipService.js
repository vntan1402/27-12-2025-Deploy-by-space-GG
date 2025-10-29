/**
 * Ship Service
 * 
 * API calls for ship management
 * Handles CRUD operations for ships
 */

import api from './api';
import { API_ENDPOINTS } from '../constants/api';

/**
 * Ship Service
 * All API methods for ship management
 */
export const shipService = {
  /**
   * Get all ships
   * @returns {Promise} List of ships
   */
  getAll: async () => {
    return api.get(API_ENDPOINTS.SHIPS);
  },

  /**
   * Get ship by ID
   * @param {string} shipId - Ship ID
   * @returns {Promise} Ship data
   */
  getById: async (shipId) => {
    return api.get(API_ENDPOINTS.SHIP_BY_ID(shipId));
  },

  /**
   * Create new ship
   * @param {object} shipData - Ship data
   * @returns {Promise} Created ship
   */
  create: async (shipData) => {
    return api.post(API_ENDPOINTS.SHIPS, shipData);
  },

  /**
   * Update ship
   * @param {string} shipId - Ship ID
   * @param {object} shipData - Updated ship data
   * @returns {Promise} Updated ship
   */
  update: async (shipId, shipData) => {
    return api.put(API_ENDPOINTS.SHIP_BY_ID(shipId), shipData);
  },

  /**
   * Delete ship
   * @param {string} shipId - Ship ID
   * @param {object} options - Delete options
   * @param {boolean} options.delete_gdrive - Whether to delete from Google Drive
   * @returns {Promise} Delete result
   */
  delete: async (shipId, options = { delete_gdrive: false }) => {
    return api.delete(API_ENDPOINTS.SHIP_BY_ID(shipId), {
      data: options,
    });
  },

  /**
   * Get ship logo
   * @param {string} shipId - Ship ID
   * @returns {Promise} Logo data
   */
  getLogo: async (shipId) => {
    return api.get(API_ENDPOINTS.SHIP_LOGO(shipId));
  },

  /**
   * Upload ship logo
   * @param {string} shipId - Ship ID
   * @param {File} logoFile - Logo file
   * @returns {Promise} Upload result
   */
  uploadLogo: async (shipId, logoFile) => {
    const formData = new FormData();
    formData.append('logo', logoFile);
    
    return api.post(API_ENDPOINTS.SHIP_LOGO(shipId), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  /**
   * Delete ship logo
   * @param {string} shipId - Ship ID
   * @returns {Promise} Delete result
   */
  deleteLogo: async (shipId) => {
    return api.delete(API_ENDPOINTS.SHIP_LOGO(shipId));
  },
};
