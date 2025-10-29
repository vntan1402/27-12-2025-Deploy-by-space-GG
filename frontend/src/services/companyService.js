/**
 * Company Service
 * 
 * API calls for company management
 * Handles CRUD operations for companies
 */

import api from './api';
import { API_ENDPOINTS } from '../constants/api';

/**
 * Company Service
 * All API methods for company management
 */
export const companyService = {
  /**
   * Get all companies
   * @returns {Promise} List of companies
   */
  getAll: async () => {
    return api.get(API_ENDPOINTS.COMPANIES);
  },

  /**
   * Get company by ID
   * @param {string} companyId - Company ID
   * @returns {Promise} Company data
   */
  getById: async (companyId) => {
    return api.get(API_ENDPOINTS.COMPANY_BY_ID(companyId));
  },

  /**
   * Create new company
   * @param {object} companyData - Company data
   * @returns {Promise} Created company
   */
  create: async (companyData) => {
    return api.post(API_ENDPOINTS.COMPANIES, companyData);
  },

  /**
   * Update company
   * @param {string} companyId - Company ID
   * @param {object} companyData - Updated company data
   * @returns {Promise} Updated company
   */
  update: async (companyId, companyData) => {
    return api.put(API_ENDPOINTS.COMPANY_BY_ID(companyId), companyData);
  },

  /**
   * Delete company
   * @param {string} companyId - Company ID
   * @returns {Promise} Delete result
   */
  delete: async (companyId) => {
    return api.delete(API_ENDPOINTS.COMPANY_BY_ID(companyId));
  },

  /**
   * Get company logo
   * @param {string} companyId - Company ID
   * @returns {Promise} Logo data
   */
  getLogo: async (companyId) => {
    return api.get(API_ENDPOINTS.COMPANY_LOGO(companyId));
  },

  /**
   * Upload company logo
   * @param {string} companyId - Company ID
   * @param {File} logoFile - Logo file
   * @returns {Promise} Upload result
   */
  uploadLogo: async (companyId, logoFile) => {
    const formData = new FormData();
    formData.append('logo', logoFile);
    
    return api.post(API_ENDPOINTS.COMPANY_LOGO(companyId), formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};
