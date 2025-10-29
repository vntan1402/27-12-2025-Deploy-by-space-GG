import api from './api';

export const aiConfigService = {
  // Get AI configuration
  getConfig: async () => {
    const response = await api.get('/api/ai-config');
    return response.data;
  },

  // Update AI configuration
  updateConfig: async (config) => {
    const response = await api.post('/api/ai-config', config);
    return response.data;
  }
};
