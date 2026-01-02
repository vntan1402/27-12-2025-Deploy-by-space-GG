import api from './api';

export const aiConfigService = {
  // Get AI configuration
  getConfig: async () => {
    const response = await api.get('/api/ai-config');
    const data = response.data;
    
    // Map backend field names to frontend field names
    return {
      ...data,
      api_key: data.custom_api_key || ''  // Map custom_api_key to api_key for frontend
    };
  },

  // Update AI configuration
  updateConfig: async (config) => {
    // Map frontend field names to backend field names
    const backendConfig = {
      ...config,
      custom_api_key: config.api_key,  // Map api_key to custom_api_key for backend
    };
    
    // Remove frontend-only field
    delete backendConfig.api_key;
    
    const response = await api.post('/api/ai-config', backendConfig);
    return response.data;
  }
};
