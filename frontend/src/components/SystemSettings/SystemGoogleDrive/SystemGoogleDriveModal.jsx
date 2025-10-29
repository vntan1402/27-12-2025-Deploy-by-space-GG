import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { gdriveService } from '../../../services';
import api from '../../../services/api';

const API_PREFIX = '/api';

const SystemGoogleDriveModal = ({ onClose }) => {
  const [authMethod, setAuthMethod] = useState('apps_script');
  const [config, setConfig] = useState({
    auth_method: 'apps_script',
    web_app_url: '',
    api_key: '',
    client_id: '',
    client_secret: '',
    folder_id: '',
    service_account_json: ''
  });
  const [currentConfig, setCurrentConfig] = useState(null);
  const [testLoading, setTestLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(false);

  useEffect(() => {
    fetchCurrentConfig();
  }, []);

  const fetchCurrentConfig = async () => {
    try {
      const data = await gdriveService.getConfig();
      setCurrentConfig(data);
      if (data.auth_method) {
        setAuthMethod(data.auth_method);
      }
    } catch (error) {
      console.error('Failed to fetch current config:', error);
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleAuthMethodChange = (method) => {
    setAuthMethod(method);
    setConfig(prev => ({ ...prev, auth_method: method }));
  };

  const handleAppsScriptTest = async () => {
    if (!config.web_app_url || !config.folder_id) {
      toast.error('Please fill in Web App URL and Folder ID');
      return;
    }

    try {
      setTestLoading(true);
      
      const response = await gdriveService.configureProxy(config.web_app_url, config.folder_id);

      if (response.success) {
        toast.success('Apps Script proxy working!');
      } else {
        toast.error('Apps Script proxy error');
      }
    } catch (error) {
      console.error('Apps Script test error:', error);
      toast.error(`Apps Script test error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setTestLoading(false);
    }
  };

  const handleOAuthAuthorize = async () => {
    if (!config.client_id || !config.client_secret || !config.folder_id) {
      toast.error('Please fill in all OAuth fields');
      return;
    }

    try {
      setOauthLoading(true);
      const oauthConfig = {
        client_id: config.client_id,
        client_secret: config.client_secret,
        redirect_uri: `${window.location.origin}/oauth2callback`,
        folder_id: config.folder_id
      };

      const response = await axios.post(`${API}/gdrive/oauth/authorize`, oauthConfig);

      if (response.data.success && response.data.authorization_url) {
        sessionStorage.setItem('oauth_state', response.data.state);
        window.location.href = response.data.authorization_url;
      } else {
        toast.error('Failed to generate authorization URL');
      }
    } catch (error) {
      console.error('OAuth authorization error:', error);
      toast.error(`OAuth authorization error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setOauthLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      let endpoint;
      let payload;

      if (authMethod === 'apps_script') {
        if (!config.web_app_url || !config.folder_id) {
          toast.error('Please fill in all required fields');
          return;
        }
        endpoint = '/gdrive/configure-proxy';
        payload = {
          web_app_url: config.web_app_url,
          folder_id: config.folder_id
        };
        
        // Add API key if provided
        if (config.api_key) {
          payload.api_key = config.api_key;
        }
      } else if (authMethod === 'oauth') {
        if (!config.client_id || !config.client_secret || !config.folder_id) {
          toast.error('Please fill in all required fields');
          return;
        }
        // For OAuth, we use the authorize flow
        handleOAuthAuthorize();
        return;
      } else {
        // Service Account
        if (!config.service_account_json || !config.folder_id) {
          toast.error('Please fill in all required fields');
          return;
        }
        endpoint = '/gdrive/configure';
        payload = {
          service_account_json: config.service_account_json,
          folder_id: config.folder_id
        };
      }

      const response = await axios.post(`${API}${endpoint}`, payload);
      
      toast.success('Google Drive configured successfully!');
      onClose();
    } catch (error) {
      console.error('Google Drive configuration error:', error);
      toast.error(`Failed to configure Google Drive: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleTestServiceAccount = async () => {
    if (!config.service_account_json || !config.folder_id) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      setTestLoading(true);
      const response = await axios.post(`${API}/gdrive/test`, {
        service_account_json: config.service_account_json,
        folder_id: config.folder_id
      });

      if (response.data.success) {
        toast.success(`Connection successful! Folder: ${response.data.folder_name}`);
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message;
      toast.error(`Connection test failed: ${errorMessage}`);
    } finally {
      setTestLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[99999]"
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">System Google Drive Configuration</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Current Configuration Display */}
        {currentConfig?.configured && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h4 className="font-medium text-green-800 mb-2">Current Configuration:</h4>
            <div className="text-sm text-green-700 space-y-1">
              <div>
                <strong>Method:</strong>{' '}
                {currentConfig.auth_method === 'apps_script'
                  ? 'Apps Script'
                  : currentConfig.auth_method === 'oauth'
                  ? 'OAuth 2.0'
                  : 'Service Account'}
              </div>
              <div><strong>Folder ID:</strong> {currentConfig.folder_id}</div>
              {currentConfig.last_sync && (
                <div>
                  <strong>Last Sync:</strong> {new Date(currentConfig.last_sync).toLocaleString()}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Authentication Method Selector */}
        <div className="mb-6">
          <h4 className="font-medium text-gray-800 mb-3">Authentication Method</h4>
          <div className="flex space-x-2 mb-4 flex-wrap">
            <button
              type="button"
              onClick={() => handleAuthMethodChange('apps_script')}
              className={`px-3 py-2 rounded-lg transition-all text-sm ${
                authMethod === 'apps_script'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Apps Script (Easiest)
            </button>
            <button
              type="button"
              onClick={() => handleAuthMethodChange('oauth')}
              className={`px-3 py-2 rounded-lg transition-all text-sm ${
                authMethod === 'oauth'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              OAuth 2.0 (Recommended)
            </button>
            <button
              type="button"
              onClick={() => handleAuthMethodChange('service_account')}
              className={`px-3 py-2 rounded-lg transition-all text-sm ${
                authMethod === 'service_account'
                  ? 'bg-yellow-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Service Account (Legacy)
            </button>
          </div>
        </div>

        <div className="space-y-6">
          {/* Apps Script Configuration */}
          {authMethod === 'apps_script' && (
            <>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <h5 className="font-medium text-green-800 mb-2">
                  ✨ Google Apps Script (Easiest)
                </h5>
                <p className="text-sm text-green-700">
                  Use Google Apps Script as a proxy to bypass OAuth consent screen issues. No Google verification needed!
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Google Apps Script Web App URL
                </label>
                <input
                  type="url"
                  value={config.web_app_url}
                  onChange={(e) => setConfig(prev => ({ ...prev, web_app_url: e.target.value }))}
                  placeholder="https://script.google.com/macros/s/AKfycby.../exec"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Example: https://script.google.com/macros/s/AKfycbzi8DdyZ85Oi9H6s-HH5CTp28HFquCWB-CquduS7MT1SBytLB_awx1UqASBVvL51SE/exec
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Google Drive Folder ID
                </label>
                <input
                  type="text"
                  value={config.folder_id}
                  onChange={(e) => setConfig(prev => ({ ...prev, folder_id: e.target.value }))}
                  placeholder="1abcDEFghiJKLmnopQRStuv2wxYZ"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Folder ID from Google Drive URL: drive.google.com/drive/folders/[FOLDER_ID]
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  🔐 API Key (Optional - Recommended for Security)
                </label>
                <input
                  type="password"
                  value={config.api_key}
                  onChange={(e) => setConfig(prev => ({ ...prev, api_key: e.target.value }))}
                  placeholder="Enter API Key from Apps Script (e.g., Vntan1402sms)"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  💡 Set API_KEY in Apps Script code for enhanced security. Leave empty if not using API key authentication.
                </p>
              </div>

              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-800">Test Apps Script Connection</h4>
                  <button
                    onClick={handleAppsScriptTest}
                    disabled={testLoading || !config.web_app_url || !config.folder_id}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center gap-2"
                  >
                    {testLoading && <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>}
                    Test Connection
                  </button>
                </div>
                <p className="text-xs text-gray-500">
                  Test Apps Script connection before saving
                </p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-green-800 mb-2">
                  📋 Apps Script Setup Instructions:
                </h4>
                <ol className="text-sm text-green-700 space-y-1 list-decimal list-inside">
                  <li>Go to <a href="https://script.google.com" target="_blank" rel="noopener noreferrer" className="underline">script.google.com</a></li>
                  <li>Create New project: "Ship Management Drive Proxy"</li>
                  <li>Copy code from GOOGLE_APPS_SCRIPT_PROXY.js file</li>
                  <li>Update FOLDER_ID with your actual folder ID</li>
                  <li>Deploy as Web app → Execute as: Me → Who has access: Anyone</li>
                  <li>Copy Web app URL and paste above</li>
                </ol>
              </div>
            </>
          )}

          {/* OAuth Configuration */}
          {authMethod === 'oauth' && (
            <>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <h5 className="font-medium text-blue-800 mb-2">OAuth 2.0 Configuration</h5>
                <p className="text-sm text-blue-700">
                  OAuth 2.0 allows the application to securely access your Google Drive without sharing passwords.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Client ID</label>
                <input
                  type="text"
                  value={config.client_id}
                  onChange={(e) => setConfig(prev => ({ ...prev, client_id: e.target.value }))}
                  placeholder="123456789012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Client Secret</label>
                <input
                  type="password"
                  value={config.client_secret}
                  onChange={(e) => setConfig(prev => ({ ...prev, client_secret: e.target.value }))}
                  placeholder="GOCSPX-abcdefghijklmnopqrstuvwxyz123456"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Google Drive Folder ID
                </label>
                <input
                  type="text"
                  value={config.folder_id}
                  onChange={(e) => setConfig(prev => ({ ...prev, folder_id: e.target.value }))}
                  placeholder="1abcDEFghiJKLmnopQRStuv2wxYZ"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Folder ID from Google Drive URL: drive.google.com/drive/folders/[FOLDER_ID]
                </p>
              </div>

              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-800">OAuth Authorization</h4>
                  <button
                    onClick={handleOAuthAuthorize}
                    disabled={oauthLoading || !config.client_id || !config.client_secret || !config.folder_id}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center gap-2"
                  >
                    {oauthLoading && <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>}
                    Authorize with Google
                  </button>
                </div>
                <p className="text-xs text-gray-500">
                  Click to authorize the application with Google Drive
                </p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-green-800 mb-2">OAuth Setup Instructions:</h4>
                <ol className="text-sm text-green-700 space-y-1 list-decimal list-inside">
                  <li>Go to Google Cloud Console</li>
                  <li>Create OAuth 2.0 Client IDs</li>
                  <li>Add Authorized redirect URI: <code>{window.location.origin}/oauth2callback</code></li>
                  <li>Copy Client ID and Client Secret</li>
                  <li>Create folder in Google Drive and copy Folder ID</li>
                  <li>Click "Authorize with Google" to connect</li>
                </ol>
              </div>
            </>
          )}

          {/* Service Account Configuration */}
          {authMethod === 'service_account' && (
            <>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                <h5 className="font-medium text-yellow-800 mb-2">Service Account (Legacy)</h5>
                <p className="text-sm text-yellow-700">
                  Service Account has storage quota limitations. OAuth 2.0 is recommended instead.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Service Account JSON
                </label>
                <textarea
                  value={config.service_account_json}
                  onChange={(e) => setConfig(prev => ({ ...prev, service_account_json: e.target.value }))}
                  placeholder="Paste service account JSON key here..."
                  className="w-full h-40 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Create Service Account in Google Cloud Console and download JSON key
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Google Drive Folder ID
                </label>
                <input
                  type="text"
                  value={config.folder_id}
                  onChange={(e) => setConfig(prev => ({ ...prev, folder_id: e.target.value }))}
                  placeholder="1abcDEFghiJKLmnopQRStuv2wxYZ"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Folder ID from Google Drive URL: drive.google.com/drive/folders/[FOLDER_ID]
                </p>
              </div>

              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-800">Test Connection</h4>
                  <button
                    onClick={handleTestServiceAccount}
                    disabled={testLoading || !config.service_account_json || !config.folder_id}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center gap-2"
                  >
                    {testLoading && <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>}
                    Test Connection
                  </button>
                </div>
                <p className="text-xs text-gray-500">
                  Test connection before saving configuration
                </p>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="font-medium text-yellow-800 mb-2">Setup Instructions:</h4>
                <ol className="text-sm text-yellow-700 space-y-1 list-decimal list-inside">
                  <li>Create project in Google Cloud Console</li>
                  <li>Enable Google Drive API</li>
                  <li>Create Service Account and download JSON key</li>
                  <li>Create folder in Google Drive and share with service account email</li>
                  <li>Copy Folder ID from URL</li>
                  <li>Test connection before saving</li>
                </ol>
              </div>
            </>
          )}
        </div>

        <div className="flex justify-end space-x-4 mt-8">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={
              authMethod === 'apps_script'
                ? (!config.web_app_url || !config.folder_id)
                : authMethod === 'oauth'
                ? (!config.client_id || !config.client_secret || !config.folder_id)
                : (!config.service_account_json || !config.folder_id)
            }
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-all"
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};

export default SystemGoogleDriveModal;
