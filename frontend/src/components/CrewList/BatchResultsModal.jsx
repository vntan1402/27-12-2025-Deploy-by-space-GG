import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const BatchResultsModal = ({ 
  results,
  onClose
}) => {
  const { language } = useAuth();
  
  const successCount = results.filter(r => r.success).length;
  const failedCount = results.filter(r => !r.success).length;
  const totalCount = results.length;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold text-gray-800">
                {language === 'vi' ? 'Kết quả xử lý hàng loạt' : 'Batch Processing Results'}
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                {language === 'vi' 
                  ? `Đã xử lý ${totalCount} file hộ chiếu`
                  : `Processed ${totalCount} passport files`}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
            >
              ×
            </button>
          </div>
        </div>
        
        {/* Summary Stats */}
        <div className="p-6 bg-gradient-to-r from-blue-50 to-green-50 border-b border-gray-200">
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-lg p-4 text-center shadow-sm">
              <div className="text-3xl font-bold text-gray-800">{totalCount}</div>
              <div className="text-sm text-gray-600 mt-1">
                {language === 'vi' ? 'Tổng số' : 'Total'}
              </div>
            </div>
            <div className="bg-white rounded-lg p-4 text-center shadow-sm">
              <div className="text-3xl font-bold text-green-600">{successCount}</div>
              <div className="text-sm text-gray-600 mt-1">
                {language === 'vi' ? 'Thành công' : 'Success'}
              </div>
            </div>
            <div className="bg-white rounded-lg p-4 text-center shadow-sm">
              <div className="text-3xl font-bold text-red-600">{failedCount}</div>
              <div className="text-sm text-gray-600 mt-1">
                {language === 'vi' ? 'Thất bại' : 'Failed'}
              </div>
            </div>
          </div>
        </div>
        
        {/* Results List */}
        <div className="p-6 overflow-y-auto max-h-[50vh]">
          <div className="space-y-3">
            {results.map((result, index) => (
              <div 
                key={index}
                className={`border-2 rounded-lg p-4 ${
                  result.success 
                    ? 'border-green-200 bg-green-50' 
                    : 'border-red-200 bg-red-50'
                }`}
              >
                <div className="flex items-start space-x-3">
                  {/* Status Icon */}
                  <div className="flex-shrink-0 mt-1">
                    <span className="text-2xl">
                      {result.success ? '✅' : '❌'}
                    </span>
                  </div>
                  
                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className={`font-semibold truncate ${
                          result.success ? 'text-green-800' : 'text-red-800'
                        }`} title={result.filename}>
                          {result.filename}
                        </p>
                        {result.success && result.crew_name && (
                          <p className="text-sm text-green-700 mt-1">
                            <span className="font-medium">
                              {language === 'vi' ? 'Thuyền viên:' : 'Crew:'} 
                            </span>{' '}
                            {result.crew_name}
                          </p>
                        )}
                        {result.passport_number && (
                          <p className="text-sm text-gray-600 mt-1">
                            <span className="font-medium">
                              {language === 'vi' ? 'Hộ chiếu:' : 'Passport:'} 
                            </span>{' '}
                            {result.passport_number}
                          </p>
                        )}
                      </div>
                      <div className="ml-3 flex-shrink-0">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          result.success 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {result.success 
                            ? (language === 'vi' ? 'Thành công' : 'Success')
                            : (language === 'vi' ? 'Thất bại' : 'Failed')
                          }
                        </span>
                      </div>
                    </div>
                    
                    {/* Error Message */}
                    {!result.success && result.error && (
                      <div className="mt-2 bg-red-100 border border-red-200 rounded p-2">
                        <p className="text-xs text-red-700">
                          <span className="font-semibold">
                            {language === 'vi' ? 'Lỗi:' : 'Error:'} 
                          </span>{' '}
                          {result.error}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
          >
            {language === 'vi' ? 'Đóng' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );
};
