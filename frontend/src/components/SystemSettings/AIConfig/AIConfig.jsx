import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { aiConfigService } from '../../../services';
import AIConfigModal from './AIConfigModal';

const AIConfig = ({ user }) => {
  const [aiConfig, setAiConfig] = useState({
    provider: 'google',
    model: 'gemini-2.0-flash',
    api_key: '',
    use_emergent_key: true,
    document_ai: {
      enabled: false,
      project_id: '',
      location: 'us',
      processor_id: '',
      apps_script_url: ''
    }
  });
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAIConfig();
  }, []);

  const fetchAIConfig = async () => {
    try {
      const data = await aiConfigService.getConfig();
      setAiConfig({
        provider: data.provider || 'google',
        model: data.model || 'gemini-2.0-flash',
        api_key: data.api_key || '',
        use_emergent_key: data.use_emergent_key !== false,
        document_ai: data.document_ai || {
          enabled: false,
          project_id: '',
          location: 'us',
          processor_id: '',
          apps_script_url: ''
        }
      });
    } catch (error) {
      console.error('Failed to fetch AI config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (config) => {
    try {
      await aiConfigService.updateConfig(config);
      toast.success('AI configuration updated successfully!');
      setShowModal(false);
      fetchAIConfig();
    } catch (error) {
      console.error('Failed to update AI config:', error);
      toast.error(`Failed to update AI configuration: ${error.response?.data?.detail || error.message}`);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">AI Configuration</h2>
          <p className="text-sm text-gray-600">Configure AI provider and model settings</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
        >
          Configure AI
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600 mb-1">Current Provider:</p>
          <p className="text-lg font-semibold text-gray-800">{aiConfig.provider.toUpperCase()}</p>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600 mb-1">Model:</p>
          <p className="text-lg font-semibold text-gray-800">{aiConfig.model}</p>
        </div>
      </div>

      {showModal && (
        <AIConfigModal
          config={aiConfig}
          onClose={() => setShowModal(false)}
          onSave={handleSave}
        />
      )}
    </div>
  );
};

export default AIConfig;
