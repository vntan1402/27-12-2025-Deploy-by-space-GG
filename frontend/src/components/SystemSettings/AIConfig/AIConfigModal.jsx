import React, { useState } from 'react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AIConfigModal = ({ config: initialConfig, onClose, onSave }) => {
  const [config, setConfig] = useState(initialConfig);

  const providers = [
    { value: 'openai', label: 'OpenAI', models: ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo'] },
    { value: 'anthropic', label: 'Anthropic', models: ['claude-3-sonnet', 'claude-3-haiku'] },
    { value: 'google', label: 'Google', models: ['gemini-pro', 'gemini-pro-vision'] },
    { value: 'emergent', label: 'Emergent LLM', models: ['gemini-2.0-flash', 'gpt-4o', 'claude-3-sonnet'] }
  ];

  const selectedProvider = providers.find(p => p.value === config.provider);

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleTestDocumentAI = async () => {
    if (!config.document_ai?.project_id || !config.document_ai?.processor_id) {
      toast.error('Please fill in Project ID and Processor ID before testing');
      return;
    }

    try {
      toast.info('Testing Google Document AI connection...');
      const token = localStorage.getItem('token') || sessionStorage.getItem('token');
      
      const response = await axios.post(
        `${API}/test-document-ai`,
        {
          project_id: config.document_ai.project_id,
          location: config.document_ai.location,
          processor_id: config.document_ai.processor_id
        },
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        toast.success(`Connection successful! Processor: ${response.data.processor_name || 'N/A'}`);
      } else {
        toast.error(`Connection failed: ${response.data.message}`);
      }
    } catch (error) {
      console.error('Document AI test error:', error);
      toast.error(`Connection test error: ${error.response?.data?.detail || error.message}`);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center p-6 border-b border-gray-200 flex-shrink-0">
          <h2 className="text-2xl font-bold text-gray-800">AI Configuration</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* Provider Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">AI Provider</label>
            <select
              value={config.provider}
              onChange={(e) => {
                const provider = providers.find(p => p.value === e.target.value);
                setConfig(prev => ({
                  ...prev,
                  provider: e.target.value,
                  model: provider?.models[0] || 'gpt-4o'
                }));
              }}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {providers.map(provider => (
                <option key={provider.value} value={provider.value}>
                  {provider.label}
                </option>
              ))}
            </select>
          </div>

          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">AI Model</label>
            <select
              value={config.model}
              onChange={(e) => setConfig(prev => ({ ...prev, model: e.target.value }))}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {selectedProvider?.models.map(model => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </div>

          {/* API Key Configuration */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">API Key Configuration</label>
            <div className="space-y-3">
              {/* Use Emergent LLM Key */}
              <div className="flex items-center p-3 border border-green-200 rounded-lg bg-green-50">
                <input
                  type="radio"
                  id="use-emergent-key"
                  name="api-key-option"
                  checked={config.use_emergent_key !== false}
                  onChange={() => setConfig(prev => ({
                    ...prev,
                    use_emergent_key: true,
                    api_key: 'EMERGENT_LLM_KEY'
                  }))}
                  className="mr-3"
                />
                <div className="flex-1">
                  <label htmlFor="use-emergent-key" className="text-sm font-medium text-green-800 cursor-pointer">
                    ✨ Use Emergent LLM Key (Recommended)
                  </label>
                  <p className="text-xs text-green-600 mt-1">
                    Free to use with all models. No need to enter your own API key.
                  </p>
                </div>
              </div>

              {/* Use Custom API Key */}
              <div className="flex items-start p-3 border border-gray-200 rounded-lg">
                <input
                  type="radio"
                  id="use-custom-key"
                  name="api-key-option"
                  checked={config.use_emergent_key === false}
                  onChange={() => setConfig(prev => ({
                    ...prev,
                    use_emergent_key: false,
                    api_key: ''
                  }))}
                  className="mr-3 mt-1"
                />
                <div className="flex-1">
                  <label htmlFor="use-custom-key" className="text-sm font-medium text-gray-700 cursor-pointer">
                    🔑 Use Custom API Key
                  </label>
                  <p className="text-xs text-gray-500 mb-2">
                    Enter your API key from OpenAI, Anthropic, or Google
                  </p>
                  {config.use_emergent_key === false && (
                    <input
                      type="password"
                      value={config.api_key || ''}
                      onChange={(e) => setConfig(prev => ({ ...prev, api_key: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      placeholder="Enter your API key"
                      required
                    />
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Google Document AI Configuration */}
          <div className="border-t border-gray-200 pt-6">
            <div className="flex items-center mb-4">
              <h4 className="text-lg font-medium text-gray-800">📄 Google Document AI</h4>
            </div>

            {/* Enable/Disable Toggle */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg mb-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Enable Google Document AI</label>
                <p className="text-xs text-gray-500 mt-1">
                  Used for passport and document analysis in crew management
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.document_ai?.enabled || false}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    document_ai: {
                      ...prev.document_ai,
                      enabled: e.target.checked
                    }
                  }))}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            {/* Document AI Fields */}
            {config.document_ai?.enabled && (
              <div className="space-y-4 pl-4 border-l-2 border-blue-200">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Project ID *</label>
                  <input
                    type="text"
                    value={config.document_ai?.project_id || ''}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      document_ai: {
                        ...prev.document_ai,
                        project_id: e.target.value
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter Google Cloud Project ID"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Location *</label>
                  <select
                    value={config.document_ai?.location || 'us'}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      document_ai: {
                        ...prev.document_ai,
                        location: e.target.value
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="us">US (United States)</option>
                    <option value="eu">EU (Europe)</option>
                    <option value="asia-northeast1">Asia Northeast 1 (Tokyo)</option>
                    <option value="asia-southeast1">Asia Southeast 1 (Singapore)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Processor ID *</label>
                  <input
                    type="text"
                    value={config.document_ai?.processor_id || ''}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      document_ai: {
                        ...prev.document_ai,
                        processor_id: e.target.value
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter Document AI Processor ID"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Document AI Apps Script URL *
                  </label>
                  <input
                    type="url"
                    value={config.document_ai?.apps_script_url || ''}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      document_ai: {
                        ...prev.document_ai,
                        apps_script_url: e.target.value
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    placeholder="https://script.google.com/macros/s/..../exec"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Separate Google Apps Script URL for Document AI processing
                  </p>
                </div>

                <div>
                  <button
                    type="button"
                    onClick={handleTestDocumentAI}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm transition-all"
                  >
                    Test Connection
                  </button>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-sm text-yellow-800"><strong>Configuration Guide:</strong></p>
                  <ul className="text-xs text-yellow-700 mt-2 space-y-1 list-disc list-inside">
                    <li>Create project in Google Cloud Console</li>
                    <li>Enable Document AI API</li>
                    <li>Create Document AI processor (type: FORM_PARSER or PASSPORT_PARSER)</li>
                    <li>Deploy Apps Script for Document AI processing</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end space-x-4 p-6 border-t border-gray-200 flex-shrink-0">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
          >
            Cancel
          </button>
          <button
            onClick={() => onSave(config)}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all"
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIConfigModal;
