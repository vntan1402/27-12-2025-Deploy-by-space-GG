import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { gdriveService } from '../../../services';
import SystemGoogleDriveModal from './SystemGoogleDriveModal';

const SystemGoogleDrive = ({ user }) => {
  const [showModal, setShowModal] = useState(false);
  const [gdriveStatus, setGdriveStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGoogleDriveStatus();
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
          <h2 className="text-xl font-semibold text-gray-800 mb-2">System Google Drive Configuration</h2>
          <p className="text-sm text-gray-600">Configure Google Drive integration for document storage</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
        >
          Configure Google Drive
        </button>
      </div>

      {gdriveStatus?.configured ? (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <h4 className="font-medium text-green-800 mb-2">Current Configuration:</h4>
          <div className="text-sm text-green-700 space-y-1">
            <div>
              <strong>Auth Method:</strong>{' '}
              {gdriveStatus.auth_method === 'apps_script'
                ? 'Apps Script'
                : gdriveStatus.auth_method === 'oauth'
                ? 'OAuth 2.0'
                : 'Service Account'}
            </div>
            {gdriveStatus.folder_id && (
              <div><strong>Folder ID:</strong> {gdriveStatus.folder_id}</div>
            )}
            {gdriveStatus.last_sync && (
              <div>
                <strong>Last Sync:</strong> {new Date(gdriveStatus.last_sync).toLocaleString()}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            Google Drive is not configured yet. Click "Configure Google Drive" to set up.
          </p>
        </div>
      )}

      {showModal && (
        <SystemGoogleDriveModal
          onClose={() => {
            setShowModal(false);
            fetchGoogleDriveStatus();
          }}
        />
      )}
    </div>
  );
};

export default SystemGoogleDrive;
