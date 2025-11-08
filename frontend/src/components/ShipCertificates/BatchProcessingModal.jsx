/**
 * Batch Processing Modal for Ship Certificates
 * Shows progress for multiple certificate files being processed
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const BatchProcessingModal = ({
  isOpen,
  isMinimized,
  onMinimize,
  onRestore,
  progress,
  fileProgressMap,
  fileStatusMap,
  fileSubStatusMap,
  title
}) => {
  const { language } = useAuth();

  if (!isOpen) return null;

  // Minimized floating widget
  if (isMinimized) {
    return (
      <div 
        onClick={onRestore}
        className="fixed bottom-6 right-6 z-[9999] cursor-pointer group"
      >
        <div className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-2xl shadow-2xl hover:shadow-3xl transition-all hover:scale-105 p-4 min-w-[280px]">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-white bg-opacity-20 rounded-full p-2">
                <div className="animate-spin h-6 w-6 border-2 border-white border-t-transparent rounded-full"></div>
              </div>
              <div>
                <div className="font-bold text-sm">
                  {language === 'vi' ? 'Đang xử lý...' : 'Processing...'}
                </div>
                <div className="text-xs text-blue-100">
                  {progress.current}/{progress.total} {language === 'vi' ? 'chứng chỉ' : 'certificates'}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="bg-white bg-opacity-20 rounded-full p-1.5 group-hover:bg-opacity-30 transition-all">
                <span className="text-sm">↑</span>
              </div>
            </div>
          </div>
          <div className="mt-2 text-xs text-blue-100">
            {language === 'vi' ? 'Click để xem tiến trình' : 'Click to view progress'}
          </div>
        </div>
      </div>
    );
  }

  // Full modal
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[80] p-4">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-xl font-bold text-gray-800">
              {title || (language === 'vi' ? '📜 Đang xử lý Ship Certificates' : '📜 Processing Ship Certificates')}
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              {language === 'vi' 
                ? `Đã hoàn thành ${progress.current}/${progress.total} chứng chỉ`
                : `Completed ${progress.current}/${progress.total} certificates`}
            </p>
          </div>
          <button
            onClick={onMinimize}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title={language === 'vi' ? 'Thu nhỏ' : 'Minimize'}
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
        </div>
        
        {/* Files List - Scrollable */}
        <div className="flex-1 overflow-y-auto space-y-3">
          {Object.keys(fileStatusMap).map((filename) => {
            const status = fileStatusMap[filename];
            const subStatus = fileSubStatusMap[filename];
            const fileProgress = fileProgressMap[filename] || 0;
            
            // Determine display status text
            let statusText = '';
            if (status === 'waiting') {
              statusText = language === 'vi' ? 'Chờ...' : 'Waiting...';
            } else if (status === 'processing') {
              if (subStatus === 'analyzing') {
                statusText = language === 'vi' ? '🤖 Phân tích với AI' : '🤖 Analyzing with AI';
              } else if (subStatus === 'uploading') {
                statusText = language === 'vi' ? '☁️ Đang tải lên Drive' : '☁️ Uploading to Drive';
              } else {
                statusText = language === 'vi' ? 'Đang xử lý...' : 'Processing...';
              }
            } else if (status === 'completed') {
              statusText = language === 'vi' ? '✅ Hoàn thành' : '✅ Completed';
            } else if (status === 'error') {
              statusText = language === 'vi' ? '❌ Lỗi' : '❌ Error';
            }
            
            return (
              <div key={filename} className="border rounded-lg p-3 bg-white shadow-sm">
                {/* Filename + Status Badge */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {status === 'waiting' && (
                      <svg className="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    )}
                    {status === 'processing' && (
                      <div className="animate-spin h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full flex-shrink-0"></div>
                    )}
                    {status === 'completed' && (
                      <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                    {status === 'error' && (
                      <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    )}
                    <span className="text-sm font-medium text-gray-700 truncate" title={filename}>
                      {filename}
                    </span>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full flex-shrink-0 ml-2 ${
                    status === 'waiting' ? 'bg-gray-200 text-gray-600' :
                    status === 'processing' ? 'bg-blue-100 text-blue-700' :
                    status === 'completed' ? 'bg-green-100 text-green-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {statusText}
                  </span>
                </div>
                
                {/* Progress Bar */}
                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-300 ${
                      status === 'completed' ? 'bg-green-500' :
                      status === 'error' ? 'bg-red-500' :
                      'bg-blue-500'
                    }`}
                    style={{ width: `${fileProgress}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
