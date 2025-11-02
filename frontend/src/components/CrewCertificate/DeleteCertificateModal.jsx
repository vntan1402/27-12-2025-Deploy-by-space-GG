import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

const DeleteCertificateModal = ({ certificates, onConfirm, onCancel, isDeleting }) => {
  const { language } = useAuth();
  const isBulk = Array.isArray(certificates) && certificates.length > 1;
  const certToDelete = isBulk ? certificates : [certificates];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-xl font-bold text-gray-800 flex items-center">
            <span className="mr-2">⚠️</span>
            {language === 'vi' ? 'Xác nhận xóa' : 'Confirm Delete'}
          </h3>
        </div>

        {/* Content */}
        <div className="p-6">
          {isBulk ? (
            <div>
              <p className="text-gray-700 mb-4">
                {language === 'vi' 
                  ? `Bạn có chắc chắn muốn xóa ${certToDelete.length} chứng chỉ đã chọn?`
                  : `Are you sure you want to delete ${certToDelete.length} selected certificates?`}
              </p>
              <div className="bg-gray-50 rounded-lg p-3 max-h-40 overflow-y-auto">
                <ul className="space-y-1 text-sm">
                  {certToDelete.map((cert, idx) => (
                    <li key={cert.id || idx} className="text-gray-600">
                      • {cert.crew_name} - {cert.cert_name}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div>
              <p className="text-gray-700 mb-2">
                {language === 'vi' 
                  ? 'Bạn có chắc chắn muốn xóa chứng chỉ này?'
                  : 'Are you sure you want to delete this certificate?'}
              </p>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-sm text-gray-600">
                  <span className="font-medium">{language === 'vi' ? 'Thuyền viên:' : 'Crew:'}</span> {certToDelete[0].crew_name}
                </p>
                <p className="text-sm text-gray-600">
                  <span className="font-medium">{language === 'vi' ? 'Chứng chỉ:' : 'Certificate:'}</span> {certToDelete[0].cert_name}
                </p>
                <p className="text-sm text-gray-600">
                  <span className="font-medium">{language === 'vi' ? 'Số:' : 'No.:'}</span> {certToDelete[0].cert_no}
                </p>
              </div>
            </div>
          )}

          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700 flex items-center">
              <span className="mr-2">⚠️</span>
              {language === 'vi' 
                ? 'Hành động này không thể hoàn tác. Files trên Google Drive cũng sẽ bị xóa.'
                : 'This action cannot be undone. Files on Google Drive will also be deleted.'}
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 flex justify-end space-x-3">
          <button
            onClick={onCancel}
            disabled={isDeleting}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
          >
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:bg-gray-300 flex items-center"
          >
            {isDeleting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                {language === 'vi' ? 'Đang xóa...' : 'Deleting...'}
              </>
            ) : (
              <>
                <span className="mr-2">🗑️</span>
                {language === 'vi' ? 'Xóa' : 'Delete'}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteCertificateModal;
