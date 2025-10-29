import api from './api';

/**
 * Authentication Service
 */
export const authService = {
  /**
   * Login user
   */
  login: async (username, password) => {
    const response = await api.post('/api/auth/login', {
      username,
      password
    });
    
    return response;
  },

  /**
   * Verify token
   */
  verifyToken: async () => {
    return api.get('/api/verify-token');
  },

  /**
   * Logout (client-side only)
   */
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
};
