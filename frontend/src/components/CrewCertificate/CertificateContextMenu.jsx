import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

const CertificateContextMenu = ({ 
  certificate, 
  position, 
  onClose, 
  onEdit,
  onDelete,
  onViewOriginal,
  onViewSummary,
  onCopyLink,
  onDownload,
  onAutoRename,
  selectedCount = 0
}) => {
  const { language, user } = useAuth();

  const handleAction = (action) => {
    action();
    onClose();
  };

  const canEdit = user && ['manager', 'admin', 'super_admin'].includes(user.role);
  const canDelete = user && ['admin', 'super_admin'].includes(user.role);
  
  // Show bulk delete when multiple certificates are selected
  const showBulkDelete = selectedCount > 1;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 z-40" 
        onClick={onClose}
      />
      
      {/* Context Menu */}
      <div
        className="fixed bg-white rounded-lg shadow-2xl border border-gray-200 py-2 z-50 min-w-[220px]"
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
        }}
      >
        {/* Show selection count header when multiple selected */}
        {showBulkDelete && (
          <div className="px-4 py-2 text-sm font-semibold text-gray-700 border-b border-gray-200">
            {selectedCount} {language === 'vi' ? 'chứng chỉ đã chọn' : 'certificates selected'}
          </div>
        )}

        {/* Edit - Only show for single certificate */}
        {canEdit && !showBulkDelete && (
          <button
            onClick={() => handleAction(onEdit)}
            className="w-full px-4 py-2 text-left hover:bg-blue-50 flex items-center space-x-3 text-gray-700 hover:text-blue-600 transition-colors"
          >
            <span className="text-lg">✏️</span>
            <span className="font-medium">{language === 'vi' ? 'Chỉnh sửa' : 'Edit Certificate'}</span>
          </button>
        )}

        {/* Delete - Show different text for bulk vs single */}
        {canDelete && (
          <button
            onClick={() => handleAction(onDelete)}
            className="w-full px-4 py-2 text-left hover:bg-red-50 flex items-center space-x-3 text-gray-700 hover:text-red-600 transition-colors"
          >
            <span className="text-lg">🗑️</span>
            <span className="font-medium">
              {showBulkDelete 
                ? (language === 'vi' ? `Xóa ${selectedCount} chứng chỉ` : `Delete ${selectedCount} Certificates`)
                : (language === 'vi' ? 'Xóa chứng chỉ' : 'Delete Certificate')}
            </span>
          </button>
        )}

        {/* Divider - Only show if we have file actions */}
        {!showBulkDelete && (certificate.crew_cert_file_id || certificate.crew_cert_summary_file_id) && (
          <div className="border-t border-gray-200 my-2"></div>
        )}

        {/* File actions - Only show for single certificate */}
        {!showBulkDelete && (
          <>
            {/* View Original File */}
            {certificate.crew_cert_file_id && (
              <button
                onClick={() => handleAction(onViewOriginal)}
                className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-3 text-gray-700 transition-colors"
              >
                <span className="text-lg">👁️</span>
                <span>{language === 'vi' ? 'Xem file gốc' : 'View Original File'}</span>
              </button>
            )}

            {/* View Summary File */}
            {certificate.crew_cert_summary_file_id && (
              <button
                onClick={() => handleAction(onViewSummary)}
                className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-3 text-gray-700 transition-colors"
              >
                <span className="text-lg">📋</span>
                <span>{language === 'vi' ? 'Xem file tóm tắt' : 'View Summary File'}</span>
              </button>
            )}

            {/* Copy File Link */}
            {certificate.crew_cert_file_id && (
              <button
                onClick={() => handleAction(onCopyLink)}
                className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-3 text-gray-700 transition-colors"
              >
                <span className="text-lg">🔗</span>
                <span>{language === 'vi' ? 'Sao chép link' : 'Copy File Link'}</span>
              </button>
            )}

            {/* Download File */}
            {certificate.crew_cert_file_id && (
              <button
                onClick={() => handleAction(onDownload)}
                className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-3 text-gray-700 transition-colors"
              >
                <span className="text-lg">📥</span>
                <span>{language === 'vi' ? 'Tải xuống' : 'Download File'}</span>
              </button>
            )}

            <div className="border-t border-gray-200 my-2"></div>

            {/* Auto Rename File */}
            {certificate.crew_cert_file_id && (
              <button
                onClick={() => handleAction(onAutoRename)}
                className="w-full px-4 py-2 text-left hover:bg-purple-50 flex items-center space-x-3 text-gray-700 hover:text-purple-600 transition-colors"
              >
                <span className="text-lg">⚡</span>
                <div className="flex-1">
                  <div className="font-medium">
                    {language === 'vi' ? 'Đổi tên file tự động' : 'Auto Rename File'}
                  </div>
                  {selectedCount > 1 && (
                    <div className="text-xs text-gray-500">
                      {language === 'vi' 
                        ? `${selectedCount} file được chọn` 
                        : `${selectedCount} files selected`}
                    </div>
                  )}
                </div>
              </button>
            )}
          </>
        )}
      </div>
    </>
  );
};

export default CertificateContextMenu;
