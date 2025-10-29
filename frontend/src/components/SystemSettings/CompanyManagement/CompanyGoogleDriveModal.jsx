/**
 * CompanyGoogleDriveModal Component
 * Modal for configuring Google Drive for individual company
 * Supports Apps Script, OAuth 2.0, and Service Account authentication methods
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { companyService } from '../../../services/companyService';

const CompanyGoogleDriveModal = ({
  company,
  onClose,
  language
}) => {
  const [config, setConfig] = useState({
    web_app_url: '',
    folder_id: '',
    auth_method: 'apps_script',
    client_id: '',
    client_secret: '',
    service_account_json: ''
  });
  const [currentConfig, setCurrentConfig] = useState(null);
  const [authMethod, setAuthMethod] = useState('apps_script');
  const [testLoading, setTestLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  // Load existing configuration on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        setLoading(true);
        const response = await companyService.getGDriveConfig(company.id);
        if (response.data.success && response.data.config) {
          setCurrentConfig(response.data.config);
          setConfig(response.data.config);
          setAuthMethod(response.data.config.auth_method || 'apps_script');
        }
      } catch (error) {
        console.error('Error loading Google Drive config:', error);
        // No toast for first-time config (not an error)
      } finally {
        setLoading(false);
      }
    };

    if (company?.id) {
      loadConfig();
    }
  }, [company]);

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
      toast.error(language === 'vi' ? 'Vui lòng điền Web App URL và Folder ID' : 'Please fill Web App URL and Folder ID');
      return;
    }

    try {
      setTestLoading(true);
      const response = await companyService.testGDriveConnection(company.id, {
        web_app_url: config.web_app_url,
        folder_id: config.folder_id
      });

      if (response.data.success) {
        toast.success(language === 'vi' ? '✅ Apps Script kết nối thành công!' : '✅ Apps Script connected successfully!');
      } else {
        toast.error(language === 'vi' 
          ? `❌ Apps Script lỗi: ${response.data.message}` 
          : `❌ Apps Script error: ${response.data.message}`
        );
      }
    } catch (error) {
      console.error('Apps Script test error:', error);
      const errorMessage = error.response?.data?.message || error.response?.data?.detail || error.message;
      toast.error(language === 'vi' 
        ? `❌ Lỗi test Apps Script: ${errorMessage}` 
        : `❌ Apps Script test error: ${errorMessage}`
      );
    } finally {
      setTestLoading(false);
    }
  };

  const handleSave = async () => {
    // Validate based on auth method
    if (authMethod === 'apps_script') {
      if (!config.web_app_url || !config.folder_id) {
        toast.error(language === 'vi' ? 'Vui lòng điền Web App URL và Folder ID' : 'Please fill Web App URL and Folder ID');
        return;
      }
    } else if (authMethod === 'oauth') {
      if (!config.client_id || !config.client_secret || !config.folder_id) {
        toast.error(language === 'vi' ? 'Vui lòng điền đầy đủ thông tin OAuth' : 'Please fill all OAuth information');
        return;
      }
    } else if (authMethod === 'service_account') {
      if (!config.service_account_json || !config.folder_id) {
        toast.error(language === 'vi' ? 'Vui lòng điền Service Account JSON và Folder ID' : 'Please fill Service Account JSON and Folder ID');
        return;
      }
    }

    try {
      setSaveLoading(true);
      const response = await companyService.configureGDrive(company.id, config);

      if (response.data.success) {
        toast.success(language === 'vi' 
          ? '✅ Cấu hình Google Drive đã được lưu thành công!' 
          : '✅ Google Drive configuration saved successfully!'
        );
        onClose();
      } else {
        toast.error(language === 'vi' 
          ? `❌ Lưu cấu hình thất bại: ${response.data.message}` 
          : `❌ Failed to save configuration: ${response.data.message}`
        );
      }
    } catch (error) {
      console.error('Error saving Google Drive config:', error);
      const errorMessage = error.response?.data?.message || error.response?.data?.detail || error.message;
      toast.error(language === 'vi' 
        ? `❌ Lỗi lưu cấu hình: ${errorMessage}` 
        : `❌ Error saving configuration: ${errorMessage}`
      );
    } finally {
      setSaveLoading(false);
    }
  };

  if (loading) {
    return (
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4"
        onClick={handleOverlayClick}
      >
        <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4"
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? 'Cấu hình Google Drive công ty' : 'Company Google Drive Configuration'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Current Configuration Display */}
          {currentConfig && currentConfig.web_app_url && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="font-medium text-green-800 mb-2">
                {language === 'vi' ? 'Cấu hình hiện tại:' : 'Current Configuration:'}
              </h4>
              <div className="text-sm text-green-700 space-y-1">
                <div><strong>{language === 'vi' ? 'Method:' : 'Auth Method:'}</strong> {
                  currentConfig.auth_method === 'apps_script' 
                    ? 'Apps Script' 
                    : currentConfig.auth_method === 'oauth' 
                      ? 'OAuth 2.0' 
                      : 'Service Account'
                }</div>
                <div><strong>{language === 'vi' ? 'Folder ID:' : 'Folder ID:'}</strong> {currentConfig.folder_id}</div>
                {currentConfig.last_tested && (
                  <div><strong>{language === 'vi' ? 'Test cuối:' : 'Last Tested:'}</strong> {new Date(currentConfig.last_tested).toLocaleString()}</div>
                )}
              </div>
            </div>
          )}

          {/* Authentication Method Selector */}
          <div className="mb-6">
            <h4 className="font-medium text-gray-800 mb-3">
              {language === 'vi' ? 'Phương thức xác thực' : 'Authentication Method'}
            </h4>
            <div className="flex space-x-2 mb-4 flex-wrap gap-2">
              <button
                type="button"
                onClick={() => handleAuthMethodChange('apps_script')}
                className={`px-3 py-2 rounded-lg transition-all text-sm ${
                  authMethod === 'apps_script'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Apps Script ({language === 'vi' ? 'Đơn giản nhất' : 'Easiest'})
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
                OAuth 2.0 ({language === 'vi' ? 'Khuyên dùng' : 'Recommended'})
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
                Service Account ({language === 'vi' ? 'Cũ' : 'Legacy'})
              </button>
            </div>
          </div>

          <div className="space-y-6">
            {/* Apps Script Configuration */}
            {authMethod === 'apps_script' && (
              <>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                  <h5 className="font-medium text-green-800 mb-2">
                    ✨ {language === 'vi' ? 'Google Apps Script (Đơn giản nhất)' : 'Google Apps Script (Easiest)'}
                  </h5>
                  <p className="text-sm text-green-700">
                    {language === 'vi' 
                      ? 'Sử dụng Google Apps Script cho công ty này. Không cần verification từ Google!'
                      : 'Use Google Apps Script for this company. No Google verification needed!'
                    }
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {language === 'vi' ? 'Google Apps Script Web App URL' : 'Google Apps Script Web App URL'}
                  </label>
                  <input
                    type="url"
                    value={config.web_app_url}
                    onChange={(e) => setConfig(prev => ({ ...prev, web_app_url: e.target.value }))}
                    placeholder="https://script.google.com/macros/s/AKfycby.../exec"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {language === 'vi' 
                      ? 'Ví dụ: https://script.google.com/macros/s/AKfycbzi8DdyZ85Oi9H6s-HH5CTp28HFquCWB-CquduS7MT1SBytLB_awx1UqASBVvL51SE/exec'
                      : 'Example: https://script.google.com/macros/s/AKfycbzi8DdyZ85Oi9H6s-HH5CTp28HFquCWB-CquduS7MT1SBytLB_awx1UqASBVvL51SE/exec'
                    }
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {language === 'vi' ? 'Google Drive Folder ID' : 'Google Drive Folder ID'}
                  </label>
                  <input
                    type="text"
                    value={config.folder_id}
                    onChange={(e) => setConfig(prev => ({ ...prev, folder_id: e.target.value }))}
                    placeholder="1abcDEFghiJKLmnopQRStuv2wxYZ"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {language === 'vi' ? 'Folder ID từ URL Google Drive: drive.google.com/drive/folders/[FOLDER_ID]' : 'Folder ID from Google Drive URL: drive.google.com/drive/folders/[FOLDER_ID]'}
                  </p>
                </div>

                {/* Apps Script Test Connection */}
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-gray-800">
                      {language === 'vi' ? 'Test kết nối Apps Script' : 'Test Apps Script Connection'}
                    </h4>
                    <button
                      onClick={handleAppsScriptTest}
                      disabled={testLoading || !config.web_app_url || !config.folder_id}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center gap-2"
                    >
                      {testLoading && <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>}
                      {language === 'vi' ? 'Test kết nối' : 'Test Connection'}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500">
                    {language === 'vi' ? 'Test kết nối Apps Script trước khi lưu' : 'Test Apps Script connection before saving'}
                  </p>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h4 className="font-medium text-green-800 mb-2">
                    📋 {language === 'vi' ? 'Hướng dẫn setup Apps Script:' : 'Apps Script Setup Instructions:'}
                  </h4>
                  <ol className="text-sm text-green-700 space-y-1 list-decimal list-inside">
                    <li>{language === 'vi' ? 'Truy cập' : 'Go to'} <a href="https://script.google.com" target="_blank" rel="noopener noreferrer" className="underline">script.google.com</a></li>
                    <li>{language === 'vi' ? 'Tạo New project cho công ty này' : 'Create New project for this company'}</li>
                    <li>{language === 'vi' ? 'Copy code từ APPS_SCRIPT_FIXED_CODE.js' : 'Copy code from APPS_SCRIPT_FIXED_CODE.js'}</li>
                    <li>{language === 'vi' ? 'Sửa FOLDER_ID với folder ID riêng của công ty' : 'Update FOLDER_ID with company-specific folder ID'}</li>
                    <li>{language === 'vi' ? 'Deploy as Web app → Execute as: Me → Who has access: Anyone' : 'Deploy as Web app → Execute as: Me → Who has access: Anyone'}</li>
                    <li>{language === 'vi' ? 'Copy Web app URL và paste vào trên' : 'Copy Web app URL and paste above'}</li>
                  </ol>
                </div>
              </>
            )}

            {/* OAuth Configuration */}
            {authMethod === 'oauth' && (
              <>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <h5 className="font-medium text-blue-800 mb-2">
                    {language === 'vi' ? 'OAuth 2.0 Configuration cho Công ty' : 'OAuth 2.0 Configuration for Company'}
                  </h5>
                  <p className="text-sm text-blue-700">
                    {language === 'vi' 
                      ? 'OAuth 2.0 cho phép công ty truy cập Google Drive riêng một cách an toàn.'
                      : 'OAuth 2.0 allows the company to securely access its dedicated Google Drive.'
                    }
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {language === 'vi' ? 'Client ID' : 'Client ID'}
                  </label>
                  <input
                    type="text"
                    value={config.client_id}
                    onChange={(e) => setConfig(prev => ({ ...prev, client_id: e.target.value }))}
                    placeholder="123456789012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {language === 'vi' ? 'Client Secret' : 'Client Secret'}
                  </label>
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
                    {language === 'vi' ? 'Google Drive Folder ID' : 'Google Drive Folder ID'}
                  </label>
                  <input
                    type="text"
                    value={config.folder_id}
                    onChange={(e) => setConfig(prev => ({ ...prev, folder_id: e.target.value }))}
                    placeholder="1abcDEFghiJKLmnopQRStuv2wxYZ"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {language === 'vi' ? 'Folder ID riêng cho công ty này' : 'Dedicated folder ID for this company'}
                  </p>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-700">
                    {language === 'vi' 
                      ? '⚠️ OAuth 2.0 hiện chưa được triển khai đầy đủ. Vui lòng sử dụng Apps Script.'
                      : '⚠️ OAuth 2.0 is not fully implemented yet. Please use Apps Script.'
                    }
                  </p>
                </div>
              </>
            )}

            {/* Service Account Configuration */}
            {authMethod === 'service_account' && (
              <>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                  <h5 className="font-medium text-yellow-800 mb-2">
                    {language === 'vi' ? 'Service Account cho Công ty (Cũ)' : 'Service Account for Company (Legacy)'}
                  </h5>
                  <p className="text-sm text-yellow-700">
                    {language === 'vi' 
                      ? 'Service Account có giới hạn storage quota. Khuyên dùng Apps Script thay thế.'
                      : 'Service Account has storage quota limitations. Apps Script is recommended instead.'
                    }
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {language === 'vi' ? 'Service Account JSON' : 'Service Account JSON'}
                  </label>
                  <textarea
                    value={config.service_account_json}
                    onChange={(e) => setConfig(prev => ({ ...prev, service_account_json: e.target.value }))}
                    placeholder={language === 'vi' ? 'Paste service account JSON key cho công ty này...' : 'Paste service account JSON key for this company...'}
                    className="w-full h-40 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {language === 'vi' ? 'Tạo Service Account riêng cho công ty này' : 'Create dedicated Service Account for this company'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {language === 'vi' ? 'Google Drive Folder ID' : 'Google Drive Folder ID'}
                  </label>
                  <input
                    type="text"
                    value={config.folder_id}
                    onChange={(e) => setConfig(prev => ({ ...prev, folder_id: e.target.value }))}
                    placeholder="1abcDEFghiJKLmnopQRStuv2wxYZ"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {language === 'vi' ? 'Folder ID riêng cho công ty này' : 'Dedicated folder ID for this company'}
                  </p>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-sm text-yellow-700">
                    {language === 'vi' 
                      ? '⚠️ Service Account hiện chưa được triển khai đầy đủ. Vui lòng sử dụng Apps Script.'
                      : '⚠️ Service Account is not fully implemented yet. Please use Apps Script.'
                    }
                  </p>
                </div>
              </>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4 mt-8 border-t pt-6">
            <button
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              onClick={handleSave}
              disabled={
                saveLoading || (
                  authMethod === 'apps_script'
                    ? (!config.web_app_url || !config.folder_id)
                    : authMethod === 'oauth' 
                      ? (!config.client_id || !config.client_secret || !config.folder_id)
                      : (!config.service_account_json || !config.folder_id)
                )
              }
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center gap-2"
            >
              {saveLoading && <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>}
              {language === 'vi' ? 'Lưu cấu hình' : 'Save Configuration'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanyGoogleDriveModal;
