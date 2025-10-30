/**
 * Delete Ship Certificate Modal Component
 * Confirmation modal for deleting ship certificates
 * Automatically deletes from both DB and Google Drive if file exists
 */
import React, { useState } from 'react';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';

export const DeleteShipCertificateModal = ({ 
  isOpen, 
  onClose, 
  onSuccess,
  certificate
}) => {
  const { language } = useAuth();
  const [isDeleting, setIsDeleting] = useState(false);

  // Handle delete
  const handleDelete = async () => {
    if (!certificate?.id) {
      toast.error(language === 'vi' ? 'Không tìm thấy certificate' : 'Certificate not found');
      return;
    }

    try {
      setIsDeleting(true);

      // Delete certificate (backend will automatically handle Google Drive deletion if file exists)
      await api.delete(`/api/ships/certificates/${certificate.id}`);
      
      const hasFile = certificate.google_drive_file_id || certificate.gdrive_file_id;
      
      toast.success(language === 'vi' 
        ? hasFile 
          ? '✅ Đã xóa certificate và file từ Google Drive!'
          : '✅ Đã xóa certificate!'
        : hasFile
          ? '✅ Certificate and file deleted from Google Drive!'
          : '✅ Certificate deleted!'
      );

      onSuccess();
      onClose();
    } catch (error) {
      console.error('Certificate deletion error:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      
      toast.error(language === 'vi' 
        ? `❌ Không thể xóa certificate: ${errorMessage}` 
        : `❌ Failed to delete certificate: ${errorMessage}`
      );
    } finally {
      setIsDeleting(false);
    }
  };

  if (!isOpen || !certificate) return null;

  const hasFile = certificate.google_drive_file_id || certificate.gdrive_file_id;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="bg-red-50 border-b border-red-200 px-6 py-4 flex items-center gap-3">
          <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h2 className="text-xl font-semibold text-red-900">
            {language === 'vi' ? '⚠️ Xác nhận xóa Certificate' : '⚠️ Confirm Delete Certificate'}
          </h2>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Warning Message */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-800 text-sm font-medium">
              {language === 'vi'
                ? '⚠️ Hành động này không thể hoàn tác!'
                : '⚠️ This action cannot be undone!'
              }
            </p>
          </div>

          {/* Certificate Info */}
          <div className="border rounded-lg p-4 bg-gray-50">
            <h3 className="font-semibold text-gray-900 mb-2">
              {language === 'vi' ? 'Certificate sẽ bị xóa:' : 'Certificate to be deleted:'}
            </h3>
            <div className="text-sm text-gray-700 space-y-1">
              <p><span className="font-medium">{language === 'vi' ? 'Tên:' : 'Name:'}</span> {certificate.cert_name}</p>
              <p><span className="font-medium">{language === 'vi' ? 'Số:' : 'No:'}</span> {certificate.cert_no || 'N/A'}</p>
              <p><span className="font-medium">{language === 'vi' ? 'Loại:' : 'Type:'}</span> {certificate.cert_type}</p>
              {certificate.issue_date && (
                <p><span className="font-medium">{language === 'vi' ? 'Ngày cấp:' : 'Issue Date:'}</span> {new Date(certificate.issue_date).toLocaleDateString()}</p>
              )}
            </div>
          </div>

          {/* File deletion info */}
          <div className={`rounded-lg p-3 ${hasFile ? 'bg-orange-50 border border-orange-200' : 'bg-blue-50 border border-blue-200'}`}>
            <p className={`text-sm ${hasFile ? 'text-orange-800' : 'text-blue-800'}`}>
              {hasFile ? (
                <>
                  <span className="font-medium">📁 {language === 'vi' ? 'File đính kèm:' : 'Attached file:'}</span>
                  <br />
                  {language === 'vi' 
                    ? 'File này cũng sẽ bị xóa khỏi Google Drive (chuyển vào thùng rác).'
                    : 'This file will also be deleted from Google Drive (moved to trash).'
                  }
                </>
              ) : (
                <>
                  <span className="font-medium">ℹ️ {language === 'vi' ? 'Không có file:' : 'No file attached:'}</span>
                  <br />
                  {language === 'vi' 
                    ? 'Certificate này không có file đính kèm, chỉ xóa dữ liệu database.'
                    : 'This certificate has no attached file, only database record will be deleted.'
                  }
                </>
              )}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={onClose}
              disabled={isDeleting}
              className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors disabled:opacity-50"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors flex items-center justify-center gap-2 ${
                isDeleting
                  ? 'bg-red-300 text-white cursor-not-allowed'
                  : 'bg-red-600 text-white hover:bg-red-700'
              }`}
            >
              {isDeleting ? (
                <>
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {language === 'vi' ? 'Đang xóa...' : 'Deleting...'}
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  {language === 'vi' ? 'Xóa Certificate' : 'Delete Certificate'}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
