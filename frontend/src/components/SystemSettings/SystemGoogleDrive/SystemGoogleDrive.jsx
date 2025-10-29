import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { gdriveService } from '../../../services';
import SystemGoogleDriveModal from './SystemGoogleDriveModal';

const SystemGoogleDrive = ({ user }) => {
  const [showModal, setShowModal] = useState(false);
  const [gdriveStatus, setGdriveStatus] = useState(null);
  const [gdriveConfig, setGdriveConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncLoading, setSyncLoading] = useState(false);

  useEffect(() => {
    fetchGoogleDriveStatus();
    fetchGoogleDriveConfig();
  }, []);

  const fetchGoogleDriveStatus = async () => {
    try {
      const data = await gdriveService.getStatus();
      setGdriveStatus(data);
    } catch (error) {
      console.error('Failed to fetch Google Drive status:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchGoogleDriveConfig = async () => {
    try {
      const data = await gdriveService.getConfig();
      setGdriveConfig(data);
    } catch (error) {
      console.error('Failed to fetch Google Drive config:', error);
    }
  };

  const handleSyncToDrive = async () => {
    setSyncLoading(true);
    try {
      const result = await gdriveService.syncToDrive();
      toast.success(`Backup thành công! ${result.files_uploaded} files đã được upload.`);
      fetchGoogleDriveStatus();
    } catch (error) {
      console.error('Sync to Drive error:', error);
      toast.error(`Backup thất bại: ${error.response?.data?.detail || error.message}`);
    } finally {
      setSyncLoading(false);
    }
  };

  const handleSyncFromDrive = async () => {
    setSyncLoading(true);
    try {
      const result = await gdriveService.syncFromDrive();
      toast.success(`Restore thành công! ${result.files_restored || 0} files đã được khôi phục.`);
      fetchGoogleDriveStatus();
    } catch (error) {
      console.error('Sync from Drive error:', error);
      toast.error(`Restore thất bại: ${error.response?.data?.detail || error.message}`);
    } finally {
      setSyncLoading(false);
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

  const isConfigured = gdriveStatus?.configured || gdriveConfig?.configured;

  return (
    <div className="space-y-4">
      {/* Configuration Status */}
      <div className="p-4 rounded-lg bg-gray-50 border">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-medium text-gray-800">Trạng thái cấu hình</h4>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
            isConfigured ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {isConfigured ? '✓ Đã cấu hình' : '✗ Chưa cấu hình'}
          </span>
        </div>
        
        {isConfigured ? (
          <div className="text-sm text-gray-600 space-y-1">
            <div className="flex justify-between">
              <span>Auth Method:</span>
              <span className="font-mono text-xs">
                {gdriveConfig?.auth_method === 'apps_script' 
                  ? 'Apps Script' 
                  : gdriveConfig?.auth_method === 'oauth' 
                    ? 'OAuth 2.0' 
                    : 'Service Account'}
              </span>
            </div>
            {gdriveConfig?.service_account_email && (
              <div className="flex justify-between">
                <span>Account Email:</span>
                <span className="font-mono text-xs">{gdriveConfig.service_account_email}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span>Folder ID:</span>
              <span className="font-mono text-xs">{gdriveConfig?.folder_id}</span>
            </div>
            {gdriveConfig?.last_sync && (
              <div className="flex justify-between">
                <span>Đồng bộ cuối:</span>
                <span className="text-xs">{new Date(gdriveConfig.last_sync).toLocaleString('vi-VN')}</span>
              </div>
            )}
            {gdriveConfig?.next_auto_sync && (
              <div className="flex justify-between">
                <span>Auto-sync tiếp theo:</span>
                <span className="text-xs text-blue-600 font-medium">
                  ⏰ {new Date(gdriveConfig.next_auto_sync).toLocaleString('vi-VN')} (21:00 hàng ngày)
                </span>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-500">
            Chưa có cấu hình Google Drive. Nhấn "Cấu hình Google Drive" để bắt đầu.
          </p>
        )}
      </div>

      {/* Sync Status */}
      {isConfigured && (
        <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
          <h4 className="font-medium text-blue-800 mb-3">Trạng thái đồng bộ</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="text-center p-3 bg-white rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{gdriveStatus?.local_files || 0}</div>
              <div className="text-gray-600 text-xs mt-1">Collections trong DB</div>
            </div>
            <div className="text-center p-3 bg-white rounded-lg">
              <div className="text-2xl font-bold text-green-600">{gdriveStatus?.drive_files || 0}</div>
              <div className="text-gray-600 text-xs mt-1">Backup folders trên Drive</div>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="space-y-2">
        <button
          onClick={() => setShowModal(true)}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg transition-all font-medium"
        >
          ⚙️ Cấu hình Google Drive hệ thống
        </button>
        
        {isConfigured && (
          <>
            <button
              onClick={handleSyncToDrive}
              disabled={syncLoading}
              className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white py-2.5 rounded-lg transition-all font-medium flex items-center justify-center"
            >
              {syncLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                  Đang backup...
                </>
              ) : (
                <>☁️↑ Backup lên Drive (Sync to Drive)</>
              )}
            </button>
            
            <button
              onClick={handleSyncFromDrive}
              disabled={syncLoading}
              className="w-full bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white py-2.5 rounded-lg transition-all font-medium flex items-center justify-center"
            >
              {syncLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                  Đang restore...
                </>
              ) : (
                <>☁️↓ Restore từ Drive (Sync from Drive)</>
              )}
            </button>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-xs text-yellow-800">
              <strong>💡 Lưu ý:</strong>
              <ul className="list-disc list-inside mt-1 space-y-0.5">
                <li>Backup tự động chạy lúc <strong>21:00 mỗi ngày</strong></li>
                <li>Mỗi bản backup lưu vào folder riêng theo ngày (VD: 2025-01-29/)</li>
                <li>Backup bao gồm <strong>TẤT CẢ</strong> collections trong database</li>
              </ul>
            </div>
          </>
        )}
      </div>

      {showModal && (
        <SystemGoogleDriveModal
          onClose={() => {
            setShowModal(false);
            fetchGoogleDriveStatus();
            fetchGoogleDriveConfig();
          }}
        />
      )}
    </div>
  );
};

export default SystemGoogleDrive;
