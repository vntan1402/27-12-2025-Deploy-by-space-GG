/**
 * User Service
 * 
 * API calls for user management
 * Handles CRUD operations for users (account control)
 */

import api from './api';
import { API_ENDPOINTS } from '../constants/api';

/**
 * User Service
 * All API methods for user management
 */
export const userService = {
  /**
   * Get all users
   * @returns {Promise} List of users
   */
  getAll: async () => {
    return api.get(API_ENDPOINTS.USERS);
  },

  /**
   * Get filtered and sorted users
   * @param {Object} filters - Filter criteria
   * @param {Object} sorting - Sort options
   * @returns {Promise} Filtered list of users
   */
  getFiltered: async (filters = {}, sorting = {}) => {
    const params = new URLSearchParams();
    
    // Add filters
    if (filters.company) params.append('company', filters.company);
    if (filters.department) params.append('department', filters.department);
    if (filters.ship) params.append('ship', filters.ship);
    
    // Add sorting
    if (sorting.sortBy) params.append('sort_by', sorting.sortBy);
    if (sorting.sortOrder) params.append('sort_order', sorting.sortOrder);
    
    const queryString = params.toString();
    return api.get(`${API_ENDPOINTS.USERS}${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Get user by ID
   * @param {string} userId - User ID
   * @returns {Promise} User data
   */
  getById: async (userId) => {
    return api.get(API_ENDPOINTS.USER_BY_ID(userId));
  },

  /**
   * Create new user
   * @param {object} userData - User data
   * @returns {Promise} Created user
   */
  create: async (userData) => {
    return api.post(API_ENDPOINTS.USERS, userData);
  },

  /**
   * Update user
   * @param {string} userId - User ID
   * @param {object} userData - Updated user data
   * @returns {Promise} Updated user
   */
  update: async (userId, userData) => {
    return api.put(API_ENDPOINTS.USER_BY_ID(userId), userData);
  },

  /**
   * Delete user
   * @param {string} userId - User ID
   * @returns {Promise} Delete result
   */
  delete: async (userId) => {
    return api.delete(API_ENDPOINTS.USER_BY_ID(userId));
  },

  /**
   * Change user password
   * @param {string} userId - User ID
   * @param {string} newPassword - New password
   * @returns {Promise} Update result
   */
  changePassword: async (userId, newPassword) => {
    return api.post(`${API_ENDPOINTS.USER_BY_ID(userId)}/change-password`, {
      new_password: newPassword,
    });
  },

  /**
   * Update user permissions
   * @param {string} userId - User ID
   * @param {object} permissions - Permissions object
   * @returns {Promise} Update result
   */
  updatePermissions: async (userId, permissions) => {
    return api.post(`${API_ENDPOINTS.USER_BY_ID(userId)}/permissions`, permissions);
  },
};