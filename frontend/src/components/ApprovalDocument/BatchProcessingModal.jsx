/**
 * Batch Processing Modal for Drawings & Manuals
 * Shows progress for multiple files being processed
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const BatchProcessingModal = ({
  isOpen,
  progress,
  fileProgressMap,
  fileStatusMap,
  fileSubStatusMap,
  isMinimized,
  onToggleMinimize,
  onClose
}) => {
  const { language } = useAuth();

  if (!isOpen) return null;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'waiting':
        return '⏳';
      case 'processing':
        return '🔄';
      case 'completed':
        return '✅';
      case 'error':
        return '❌';
      default:
        return '⏳';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'waiting':
        return language === 'vi' ? 'Đang chờ...' : 'Waiting...';
      case 'processing':
        return language === 'vi' ? 'Đang xử lý...' : 'Processing...';
      case 'completed':
        return language === 'vi' ? 'Hoàn tất' : 'Completed';
      case 'error':
        return language === 'vi' ? 'Lỗi' : 'Error';
      default:
        return language === 'vi' ? 'Đang chờ...' : 'Waiting...';
    }
  };

  return (
    <div className={`fixed ${isMinimized ? 'bottom-4 right-4 w-80' : 'inset-0 bg-black bg-opacity-50 flex items-center justify-center'} z-50 transition-all`}>
      <div className={`bg-white rounded-lg shadow-xl ${isMinimized ? 'w-full' : 'max-w-3xl w-full mx-4'} max-h-[80vh] overflow-hidden`}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-500 to-blue-600 flex justify-between items-center">
          <div className="text-white">
            <h3 className="text-lg font-bold">
              {language === 'vi' ? '📤 Xử lý hàng loạt Drawings & Manuals' : '📤 Batch Processing Drawings & Manuals'}
            </h3>
            <p className="text-sm text-blue-100">
              {language === 'vi' 
                ? `Đang xử lý ${progress.current}/${progress.total} files` 
                : `Processing ${progress.current}/${progress.total} files`}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onToggleMinimize}
              className="text-white hover:text-gray-200 transition-colors p-2"
              title={isMinimized ? (language === 'vi' ? 'Mở rộng' : 'Expand') : (language === 'vi' ? 'Thu nhỏ' : 'Minimize')}
            >
              {isMinimized ? '📈' : '📉'}
            </button>
          </div>
        </div>

        {/* Progress Content (hidden when minimized) */}
        {!isMinimized && (
          <div className="p-6 overflow-y-auto max-h-[60vh]">
            {/* Overall Progress Bar (Enhanced with smooth animation) */}
            <div className="mb-6">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span className="font-medium">📊 {language === 'vi' ? 'Tiến độ tổng' : 'Overall Progress'}</span>
                <span className="font-semibold text-blue-600">{Math.round((progress.current / progress.total) * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-5 overflow-hidden shadow-inner">
                <div
                  className="bg-gradient-to-r from-blue-500 via-blue-600 to-green-500 h-5 rounded-full transition-all duration-700 ease-out flex items-center justify-center text-xs text-white font-bold shadow-lg"
                  style={{ width: `${(progress.current / progress.total) * 100}%` }}
                >
                  {progress.current > 0 && (
                    <span className="drop-shadow-md">
                      {progress.current}/{progress.total}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Individual File Progress */}
            <div className="space-y-3">
              {Object.keys(fileStatusMap).map((filename) => {
                const status = fileStatusMap[filename];
                const fileProgress = fileProgressMap[filename] || 0;
                const subStatus = fileSubStatusMap[filename];

                return (
                  <div key={filename} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    {/* File name and status */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <span className="text-lg">{getStatusIcon(status)}</span>
                        <span className="text-sm font-medium text-gray-800 truncate" title={filename}>
                          {filename}
                        </span>
                      </div>
                      <span className="text-xs text-gray-600 ml-2">
                        {getStatusText(status)}
                      </span>
                    </div>

                    {/* Progress bar for processing files */}
                    {status === 'processing' && (
                      <div>
                        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${fileProgress}%` }}
                          />
                        </div>
                        {subStatus && (
                          <p className="text-xs text-gray-500 mt-1">{subStatus}</p>
                        )}
                      </div>
                    )}

                    {/* Success/Error indicators */}
                    {status === 'completed' && (
                      <div className="text-xs text-green-600 font-medium">
                        {language === 'vi' ? '✅ Đã xử lý thành công' : '✅ Successfully processed'}
                      </div>
                    )}
                    {status === 'error' && (
                      <div className="text-xs text-red-600 font-medium">
                        {language === 'vi' ? '❌ Xử lý thất bại' : '❌ Processing failed'}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Minimized View */}
        {isMinimized && (
          <div className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">
                {language === 'vi' ? 'Đang xử lý...' : 'Processing...'}
              </span>
              <span className="text-sm font-semibold text-blue-600">
                {progress.current}/{progress.total}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2 overflow-hidden">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${(progress.current / progress.total) * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
