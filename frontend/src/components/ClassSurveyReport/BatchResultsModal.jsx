/**
 * Batch Results Modal
 * Shows summary of batch processing results
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const BatchResultsModal = ({ isOpen, onClose, results, onRetryFile }) => {
  const { language } = useAuth();

  if (!isOpen) return null;

  const successCount = results.filter(r => r.success).length;
  const failCount = results.length - successCount;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[80]">
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="mb-6">
          <h3 className="text-2xl font-bold text-gray-800 mb-2">
            {language === 'vi' ? '📊 Kết quả xử lý Survey Reports' : '📊 Survey Report Processing Results'}
          </h3>
          <p className="text-gray-600">
            {language === 'vi' 
              ? `Đã xử lý ${results.length} file`
              : `Processed ${results.length} files`}
          </p>
        </div>

        {/* Results Table */}
        <div className="overflow-x-auto mb-6">
          <table className="min-w-full bg-white border border-gray-200 rounded-lg">
            <thead className="bg-gray-50">
              <tr>
                <th className="border border-gray-300 px-4 py-2 text-left text-sm font-semibold">
                  {language === 'vi' ? 'Tên file' : 'Filename'}
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left text-sm font-semibold">
                  {language === 'vi' ? 'Tên báo cáo' : 'Report Name'}
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left text-sm font-semibold">
                  {language === 'vi' ? 'Số báo cáo' : 'Report No.'}
                </th>
                <th className="border border-gray-300 px-4 py-2 text-center text-sm font-semibold">
                  {language === 'vi' ? 'Trạng thái' : 'Status'}
                </th>
              </tr>
            </thead>
            <tbody>
              {results.map((result, index) => (
                <tr key={index} className={result.success ? 'bg-green-50' : 'bg-red-50'}>
                  <td className="border border-gray-300 px-4 py-2 text-sm">
                    <div className="flex items-center justify-between gap-2">
                      <span className="flex-1">{result.filename}</span>
                      {/* Retry button for failed files */}
                      {!result.success && onRetryFile && (
                        <button
                          onClick={() => {
                            onClose(); // Close modal first
                            onRetryFile(result.filename); // Then retry
                          }}
                          className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors"
                          title={language === 'vi' ? 'Thử lại file này' : 'Retry this file'}
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          <span>{language === 'vi' ? 'Thử lại' : 'Retry'}</span>
                        </button>
                      )}
                    </div>
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-sm">
                    {result.surveyReportName || '-'}
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-sm font-mono">
                    {result.surveyReportNo || '-'}
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-center">
                    {result.success ? (
                      <div className="flex flex-col items-center gap-1">
                        <span className="text-green-600 font-semibold">
                          ✅ {language === 'vi' ? 'Thành công' : 'Success'}
                        </span>
                        {result.surveyReportCreated && (
                          <span className="text-xs text-green-600">
                            {language === 'vi' ? '📋 Đã tạo record' : '📋 Record created'}
                          </span>
                        )}
                        {result.fileUploaded && (
                          <span className="text-xs text-green-600">
                            {language === 'vi' ? '☁️ Đã upload file' : '☁️ File uploaded'}
                          </span>
                        )}
                      </div>
                    ) : (
                      <div className="flex flex-col items-center gap-1">
                        <span className="text-red-600 font-semibold">
                          ❌ {language === 'vi' ? 'Thất bại' : 'Failed'}
                        </span>
                        <span className="text-xs text-red-600 max-w-xs break-words whitespace-pre-line">
                          {result.error === 'DUPLICATE' 
                            ? (language === 'vi' ? '⚠️ Đã tồn tại' : '⚠️ Duplicate')
                            : result.error}
                        </span>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Summary */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-gray-800">
                {results.length}
              </p>
              <p className="text-sm text-gray-600">
                {language === 'vi' ? 'Tổng số' : 'Total'}
              </p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">
                {successCount}
              </p>
              <p className="text-sm text-gray-600">
                {language === 'vi' ? 'Thành công' : 'Success'}
              </p>
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">
                {failCount}
              </p>
              <p className="text-sm text-gray-600">
                {language === 'vi' ? 'Thất bại' : 'Failed'}
              </p>
            </div>
          </div>
        </div>

        {/* Close Button */}
        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all font-medium"
          >
            {language === 'vi' ? 'Đóng' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );
};
