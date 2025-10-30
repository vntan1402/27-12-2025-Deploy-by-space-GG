import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

const DeleteShipConfirmationModal = ({ isOpen, onClose, ship, onConfirm, isDeleting }) => {
  const { language } = useAuth();
  const [deleteOption, setDeleteOption] = useState('database_only');

  if (!isOpen || !ship) return null;

  const handleConfirm = () => {
    onConfirm(ship.id, deleteOption);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200">
          <h3 className="text-xl font-bold text-red-600 flex items-center">
            <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            {language === 'vi' ? 'Xác nhận xóa tàu' : 'Confirm Ship Deletion'}
          </h3>
          <button
            onClick={onClose}
            disabled={isDeleting}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none disabled:opacity-50"
          >
            ×
          </button>
        </div>
        
        <div className="p-6">
          <div className="mb-6">
            {/* Warning Icon */}
            <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </div>
            
            {/* Confirmation Message */}
            <h4 className="text-lg font-semibold text-gray-900 text-center mb-2">
              {language === 'vi' 
                ? `Bạn có chắc chắn muốn xóa tàu "${ship.name}"?`
                : `Are you sure you want to delete ship "${ship.name}"?`
              }
            </h4>
            
            <p className="text-sm text-gray-600 text-center mb-6">
              {language === 'vi' 
                ? 'Hành động này không thể hoàn tác. Vui lòng chọn phương thức xóa:'
                : 'This action cannot be undone. Please choose the deletion method:'
              }
            </p>

            {/* Deletion Options */}
            <div className="space-y-4">
              {/* Option 1: Database Only */}
              <div 
                onClick={() => setDeleteOption('database_only')}
                className={`border rounded-lg p-4 cursor-pointer transition-all ${
                  deleteOption === 'database_only' 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start">
                  <input
                    type="radio"
                    name="deleteOption"
                    value="database_only"
                    checked={deleteOption === 'database_only'}
                    onChange={(e) => setDeleteOption(e.target.value)}
                    className="mt-1 mr-3"
                  />
                  <div>
                    <h5 className="font-medium text-gray-900">
                      {language === 'vi' ? 'Chỉ xóa dữ liệu trên Database' : 'Delete Database Data Only'}
                    </h5>
                    <p className="text-sm text-gray-600 mt-1">
                      {language === 'vi' 
                        ? 'Xóa thông tin tàu và tất cả chứng chỉ khỏi hệ thống. Giữ nguyên folder trên Google Drive.'
                        : 'Remove ship information and all certificates from the system. Keep Google Drive folder intact.'
                      }
                    </p>
                  </div>
                </div>
              </div>

              {/* Option 2: Database + Google Drive */}
              <div 
                onClick={() => setDeleteOption('with_gdrive')}
                className={`border rounded-lg p-4 cursor-pointer transition-all ${
                  deleteOption === 'with_gdrive' 
                    ? 'border-red-500 bg-red-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start">
                  <input
                    type="radio"
                    name="deleteOption"
                    value="with_gdrive"
                    checked={deleteOption === 'with_gdrive'}
                    onChange={(e) => setDeleteOption(e.target.value)}
                    className="mt-1 mr-3"
                  />
                  <div>
                    <h5 className="font-medium text-gray-900">
                      {language === 'vi' ? 'Xóa cả Folder trên Google Drive' : 'Delete Including Google Drive Folder'}
                    </h5>
                    <p className="text-sm text-gray-600 mt-1">
                      {language === 'vi' 
                        ? 'Xóa hoàn toàn thông tin tàu và toàn bộ folder structure trên Google Drive. KHÔNG THỂ KHÔI PHỤC!'
                        : 'Completely remove ship information and entire Google Drive folder structure. CANNOT BE RECOVERED!'
                      }
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              disabled={isDeleting}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all disabled:opacity-50"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              onClick={handleConfirm}
              disabled={isDeleting}
              className={`px-6 py-2 text-white rounded-lg transition-all font-medium flex items-center disabled:opacity-50 ${
                deleteOption === 'with_gdrive' 
                  ? 'bg-red-600 hover:bg-red-700' 
                  : 'bg-orange-600 hover:bg-orange-700'
              }`}
            >
              {isDeleting ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {language === 'vi' ? 'Đang xóa...' : 'Deleting...'}
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  {language === 'vi' ? 'Xóa tàu' : 'Delete Ship'}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteShipConfirmationModal;
