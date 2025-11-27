/**
 * Batch Processing Modal for Audit Certificates
 * Shows progress for multiple certificate files being processed
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const BatchProcessingModal = ({
  isOpen,
  isMinimized,
  onMinimize,
  onRestore,
  uploads,
  language: propLanguage
}) => {
  const { language: contextLanguage } = useAuth();
  const language = propLanguage || contextLanguage;

  if (!isOpen) return null;

  const completed = uploads.filter(u => u.status === 'completed').length;
  const total = uploads.length;

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
                  {completed}/{total} {language === 'vi' ? 'chứng chỉ' : 'certificates'}
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[80]">
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-4xl w-full mx-4 max-h-[85vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-2xl font-bold text-gray-800">
              {language === 'vi' ? '⏳ Đang xử lý Audit Certificates' : '⏳ Processing Audit Certificates'}
            </h3>
            <p className="text-gray-600 mt-1">
              {language === 'vi' 
                ? `Tiến trình: ${completed}/${total}`
                : `Progress: ${completed}/${total}`}
            </p>
          </div>
          <button
            onClick={onMinimize}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title={language === 'vi' ? 'Thu gọn' : 'Minimize'}
          >
            <span className="text-2xl">↓</span>
          </button>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="bg-gray-200 rounded-full h-3 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-blue-500 to-cyan-500 h-full transition-all duration-500"
              style={{ width: `${(completed / total) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* File List */}
        <div className="space-y-3">
          {uploads.map((upload, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-lg border-2 transition-all ${
                upload.status === 'completed'
                  ? 'bg-green-50 border-green-300'
                  : upload.status === 'error'
                  ? 'bg-red-50 border-red-300'
                  : upload.status === 'uploading'
                  ? 'bg-blue-50 border-blue-300 animate-pulse'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="font-medium text-gray-800 truncate">
                    {upload.filename}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    {upload.stage}
                  </div>
                  {upload.error && (
                    <div className="text-sm text-red-600 mt-1">
                      ❌ {upload.error}
                    </div>
                  )}
                </div>
                <div className="ml-4">
                  {upload.status === 'completed' && (
                    <span className="text-2xl">✅</span>
                  )}
                  {upload.status === 'error' && (
                    <span className="text-2xl">❌</span>
                  )}
                  {upload.status === 'uploading' && (
                    <div className="animate-spin h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                  )}
                  {upload.status === 'pending' && (
                    <span className="text-2xl text-gray-400">⏳</span>
                  )}
                </div>
              </div>
              {/* Progress Bar for individual file */}
              {upload.status === 'uploading' && upload.progress > 0 && (
                <div className="mt-2">
                  <div className="bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div 
                      className="bg-blue-500 h-full transition-all duration-300"
                      style={{ width: `${upload.progress}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
