import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const DeleteCrewConfirmModal = ({ 
  crew,
  selectedCount = 1,
  onClose, 
  onConfirm,
  isDeleting = false
}) => {
  const { language } = useAuth();
  
  const isBulk = selectedCount > 1;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0 w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">⚠️</span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-800">
                {language === 'vi' ? 'Xác nhận xóa' : 'Confirm Delete'}
              </h3>
              <p className="text-sm text-gray-600">
                {language === 'vi' ? 'Hành động này không thể hoàn tác' : 'This action cannot be undone'}
              </p>
            </div>
          </div>
        </div>
        
        {/* Body */}
        <div className="p-6">
          {isBulk ? (
            <div>
              <p className="text-gray-700 mb-4">
                {language === 'vi' 
                  ? `Bạn có chắc chắn muốn xóa ${selectedCount} thuyền viên đã chọn?`
                  : `Are you sure you want to delete ${selectedCount} selected crew members?`
                }
              </p>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-sm text-yellow-800">
                  <span className="font-semibold">⚠️ {language === 'vi' ? 'Lưu ý:' : 'Note:'}</span>
                  {' '}
                  {language === 'vi' 
                    ? 'Thuyền viên có chứng chỉ sẽ không thể xóa. Vui lòng xóa chứng chỉ trước.'
                    : 'Crew members with certificates cannot be deleted. Please delete certificates first.'
                  }
                </p>
              </div>
            </div>
          ) : (
            <div>
              <p className="text-gray-700 mb-2">
                {language === 'vi' 
                  ? 'Bạn có chắc chắn muốn xóa thuyền viên này?'
                  : 'Are you sure you want to delete this crew member?'
                }
              </p>
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <div className="space-y-2">
                  <p className="text-sm">
                    <span className="font-semibold text-gray-700">{language === 'vi' ? 'Họ tên:' : 'Name:'}</span>
                    {' '}
                    <span className="text-gray-900">{crew?.full_name}</span>
                  </p>
                  <p className="text-sm">
                    <span className="font-semibold text-gray-700">{language === 'vi' ? 'Hộ chiếu:' : 'Passport:'}</span>
                    {' '}
                    <span className="text-gray-900">{crew?.passport}</span>
                  </p>
                  <p className="text-sm">
                    <span className="font-semibold text-gray-700">{language === 'vi' ? 'Tàu:' : 'Ship:'}</span>
                    {' '}
                    <span className="text-gray-900">{crew?.ship_sign_on}</span>
                  </p>
                </div>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-sm text-yellow-800">
                  <span className="font-semibold">⚠️ {language === 'vi' ? 'Lưu ý:' : 'Note:'}</span>
                  {' '}
                  {language === 'vi' 
                    ? 'Nếu thuyền viên có chứng chỉ, bạn cần xóa tất cả chứng chỉ trước.'
                    : 'If crew member has certificates, you need to delete all certificates first.'
                  }
                </p>
              </div>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-white transition-colors"
            disabled={isDeleting}
          >
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          <button
            onClick={onConfirm}
            className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
            disabled={isDeleting}
          >
            {isDeleting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>{language === 'vi' ? 'Đang xóa...' : 'Deleting...'}</span>
              </>
            ) : (
              <>
                <span>🗑️</span>
                <span>{language === 'vi' ? 'Xóa' : 'Delete'}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
