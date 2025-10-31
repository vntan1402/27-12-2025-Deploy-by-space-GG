/**
 * Batch Results Modal for Drawings & Manuals
 * Shows summary of batch processing results
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const BatchResultsModal = ({
  isOpen,
  results,
  onClose
}) => {
  const { language } = useAuth();

  if (!isOpen) return null;

  const successCount = results.filter(r => r.success).length;
  const failCount = results.length - successCount;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-500 to-blue-600">
          <div className="flex justify-between items-center">
            <div className="text-white">
              <h3 className="text-xl font-bold">
                {language === 'vi' ? '📊 Kết quả xử lý hàng loạt' : '📊 Batch Processing Results'}
              </h3>
              <p className="text-sm text-blue-100 mt-1">
                {language === 'vi' 
                  ? `${successCount} thành công, ${failCount} thất bại trên tổng ${results.length} files` 
                  : `${successCount} success, ${failCount} failed out of ${results.length} files`}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Summary Statistics */}
        <div className="p-6 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-lg p-4 border border-gray-200 text-center">
              <div className="text-3xl font-bold text-gray-800">{results.length}</div>
              <div className="text-sm text-gray-600 mt-1">
                {language === 'vi' ? 'Tổng files' : 'Total Files'}
              </div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-green-200 text-center">
              <div className="text-3xl font-bold text-green-600">{successCount}</div>
              <div className="text-sm text-gray-600 mt-1">
                {language === 'vi' ? 'Thành công' : 'Success'}
              </div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-red-200 text-center">
              <div className="text-3xl font-bold text-red-600">{failCount}</div>
              <div className="text-sm text-gray-600 mt-1">
                {language === 'vi' ? 'Thất bại' : 'Failed'}
              </div>
            </div>
          </div>
        </div>

        {/* Results Table */}
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(85vh - 280px)' }}>
          <table className="w-full border-collapse">
            <thead className="bg-gray-100 sticky top-0">
              <tr>
                <th className="border border-gray-300 px-4 py-2 text-left text-sm font-semibold text-gray-700">
                  {language === 'vi' ? 'Trạng thái' : 'Status'}
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left text-sm font-semibold text-gray-700">
                  {language === 'vi' ? 'Tên file' : 'Filename'}
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left text-sm font-semibold text-gray-700">
                  {language === 'vi' ? 'Tên báo cáo' : 'Report Name'}
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left text-sm font-semibold text-gray-700">
                  {language === 'vi' ? 'Số báo cáo' : 'Report No'}
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left text-sm font-semibold text-gray-700">
                  {language === 'vi' ? 'Ghi chú' : 'Note'}
                </th>
              </tr>
            </thead>
            <tbody>
              {results.map((result, index) => (
                <tr key={index} className={result.success ? 'bg-green-50' : 'bg-red-50'}>
                  <td className="border border-gray-300 px-4 py-2">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold ${
                      result.success 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {result.success ? '✅' : '❌'}
                      {result.success 
                        ? (language === 'vi' ? 'Thành công' : 'Success')
                        : (language === 'vi' ? 'Thất bại' : 'Failed')}
                    </span>
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-sm">
                    <div className="max-w-xs truncate" title={result.filename}>
                      {result.filename}
                    </div>
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-sm">
                    {result.testReportName || '-'}
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-sm font-mono">
                    {result.testReportNo || '-'}
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-sm">
                    {result.success ? (
                      <div className="space-y-1">
                        {result.testReportCreated && (
                          <div className="text-xs text-green-600">
                            {language === 'vi' ? '✓ Đã tạo record' : '✓ Record created'}
                          </div>
                        )}
                        {result.fileUploaded && (
                          <div className="text-xs text-green-600">
                            {language === 'vi' ? '✓ Đã upload file' : '✓ File uploaded'}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-xs text-red-600">
                        {result.error || (language === 'vi' ? 'Lỗi không xác định' : 'Unknown error')}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end">
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
