import api from './api';

/**
 * Authentication Service
 */
export const authService = {
  /**
   * Login user
   */
  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/api/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
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
