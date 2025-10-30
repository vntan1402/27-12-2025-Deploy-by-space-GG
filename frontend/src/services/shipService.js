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

  /**
   * Analyze ship certificate with AI
   * @param {File} certificateFile - Certificate PDF file
   * @returns {Promise} Analysis result
   */
  analyzeCertificate: async (certificateFile) => {
    const formData = new FormData();
    formData.append('file', certificateFile);
    
    return api.post(API_ENDPOINTS.SHIP_ANALYZE_CERTIFICATE, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 90000 // 90 seconds for AI analysis
    });
  },

  // Alias methods for backward compatibility
  getAllShips: async () => {
    return shipService.getAll();
  },

  getShipById: async (shipId) => {
    return shipService.getById(shipId);
  },

  createShip: async (shipData) => {
    return shipService.create(shipData);
  },

  updateShip: async (shipId, shipData) => {
    return shipService.update(shipId, shipData);
  },

  deleteShip: async (shipId, options) => {
    return shipService.delete(shipId, options);
  },
};
