import api from './api';

export const gdriveService = {
  // Get Google Drive status
  getStatus: async () => {
    const response = await api.get('/gdrive/status');
    return response.data;
  },

  // Get Google Drive configuration
  getConfig: async () => {
    const response = await api.get('/gdrive/config');
    return response.data;
  },

  // Configure with Apps Script
  configureProxy: async (webAppUrl, folderId) => {
    const response = await api.post('/gdrive/configure-proxy', {
      web_app_url: webAppUrl,
      folder_id: folderId
    });
    return response.data;
  },

  // Configure with OAuth
  authorizeOAuth: async (clientId, clientSecret, redirectUri, folderId) => {
    const response = await api.post('/gdrive/oauth/authorize', {
      client_id: clientId,
      client_secret: clientSecret,
      redirect_uri: redirectUri,
      folder_id: folderId
    });
    return response.data;
  },

  // Configure with Service Account
  configure: async (serviceAccountJson, folderId) => {
    const response = await api.post('/gdrive/configure', {
      service_account_json: serviceAccountJson,
      folder_id: folderId
    });
    return response.data;
  },

  // Test connection
  test: async (serviceAccountJson, folderId) => {
    const response = await api.post('/gdrive/test', {
      service_account_json: serviceAccountJson,
      folder_id: folderId
    });
    return response.data;
  }
};
