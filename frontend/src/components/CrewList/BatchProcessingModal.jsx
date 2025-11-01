import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const BatchProcessingModal = ({ 
  progress,
  currentFile,
  onClose
}) => {
  const { language } = useAuth();
  
  const percentage = progress.total > 0 ? Math.round((progress.current / progress.total) * 100) : 0;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-xl font-bold text-gray-800">
            {language === 'vi' ? 'Đang xử lý hàng loạt' : 'Batch Processing'}
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {language === 'vi' 
              ? 'Vui lòng đợi trong khi hệ thống xử lý các file hộ chiếu...'
              : 'Please wait while the system processes passport files...'}
          </p>
        </div>
        
        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Progress Stats */}
          <div className="flex items-center justify-between">
            <div className="text-center flex-1">
              <div className="text-3xl font-bold text-blue-600">{progress.current}</div>
              <div className="text-sm text-gray-600 mt-1">
                {language === 'vi' ? 'Đang xử lý' : 'Processing'}
              </div>
            </div>
            <div className="text-gray-400 text-2xl">/</div>
            <div className="text-center flex-1">
              <div className="text-3xl font-bold text-gray-800">{progress.total}</div>
              <div className="text-sm text-gray-600 mt-1">
                {language === 'vi' ? 'Tổng số' : 'Total'}
              </div>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm font-medium text-gray-700">
              <span>{percentage}% {language === 'vi' ? 'Hoàn thành' : 'Complete'}</span>
              <span>{progress.success} {language === 'vi' ? 'Thành công' : 'Success'} • {progress.failed} {language === 'vi' ? 'Thất bại' : 'Failed'}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500 ease-out flex items-center justify-end"
                style={{ width: `${percentage}%` }}
              >
                {percentage > 10 && (
                  <span className="text-xs text-white font-bold mr-2">{percentage}%</span>
                )}
              </div>
            </div>
          </div>
          
          {/* Current File */}
          {currentFile && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-200 border-t-blue-600"></div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-blue-800">
                    {language === 'vi' ? 'Đang xử lý:' : 'Processing:'}
                  </p>
                  <p className="text-sm text-blue-700 truncate" title={currentFile}>
                    {currentFile}
                  </p>
                </div>
              </div>
            </div>
          )}
          
          {/* Status Message */}
          <div className="text-center">
            <p className="text-sm text-gray-600">
              {language === 'vi' 
                ? 'Quá trình này có thể mất vài phút. Vui lòng không đóng cửa sổ này.'
                : 'This process may take a few minutes. Please do not close this window.'}
            </p>
          </div>
        </div>
        
        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 rounded-b-xl">
          <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
            <div className="animate-pulse">⚡</div>
            <span>
              {language === 'vi' 
                ? 'Đang sử dụng AI để phân tích hộ chiếu...'
                : 'Using AI to analyze passports...'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
