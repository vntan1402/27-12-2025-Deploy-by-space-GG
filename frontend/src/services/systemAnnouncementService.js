import api from './api';

const systemAnnouncementService = {
  /**
   * Get active announcements (PUBLIC - no auth required)
   */
  getActiveAnnouncements: async () => {
    try {
      const response = await api.get('/system-announcements/active');
      return response.data;
    } catch (error) {
      console.error('Error fetching active announcements:', error);
      throw error;
    }
  },

  /**
   * Get all announcements (ADMIN only)
   */
  getAllAnnouncements: async (skip = 0, limit = 100) => {
    try {
      const response = await api.get('/system-announcements', {
        params: { skip, limit }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching all announcements:', error);
      throw error;
    }
  },

  /**
   * Get announcement by ID (ADMIN only)
   */
  getAnnouncementById: async (id) => {
    try {
      const response = await api.get(`/system-announcements/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching announcement:', error);
      throw error;
    }
  },

  /**
   * Create new announcement (ADMIN only)
   */
  createAnnouncement: async (data) => {
    try {
      const response = await api.post('/system-announcements', data);
      return response.data;
    } catch (error) {
      console.error('Error creating announcement:', error);
      throw error;
    }
  },

  /**
   * Update announcement (ADMIN only)
   */
  updateAnnouncement: async (id, data) => {
    try {
      const response = await api.put(`/system-announcements/${id}`, data);
      return response.data;
    } catch (error) {
      console.error('Error updating announcement:', error);
      throw error;
    }
  },

  /**
   * Delete announcement (ADMIN only)
   */
  deleteAnnouncement: async (id) => {
    try {
      const response = await api.delete(`/system-announcements/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting announcement:', error);
      throw error;
    }
  }
};

export default systemAnnouncementService;
