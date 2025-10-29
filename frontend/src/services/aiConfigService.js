import api from './api';

export const aiConfigService = {
  // Get AI configuration
  getConfig: async () => {
    const response = await api.get('/ai-config');
    return response.data;
  },

  // Update AI configuration
  updateConfig: async (config) => {
    const response = await api.post('/ai-config', config);
    return response.data;
  }
};
