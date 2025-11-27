/**
 * Batch Results Modal for Audit Certificates
 * Shows summary of batch certificate processing results
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const BatchResultsModal = ({ 
  isOpen, 
  onClose, 
  results, 
  summary,
  language: propLanguage 
}) => {
  const { language: contextLanguage } = useAuth();
  const language = propLanguage || contextLanguage;

  if (!isOpen) return null;

  const successCount = summary?.success || 0;
  const failCount = summary?.failed || 0;
  const total = summary?.total || 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[90]">
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-5xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="mb-6">
          <h3 className="text-2xl font-bold text-gray-800 mb-2">
            {language === 'vi' ? '📊 Kết quả xử lý Audit Certificates' : '📊 Audit Certificate Processing Results'}
          </h3>
          <p className="text-gray-600">
            {language === 'vi' 
              ? `Đã xử lý ${total} chứng chỉ`
              : `Processed ${total} certificates`}
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gradient-to-br from-blue-50 to-cyan-50 p-4 rounded-lg border-2 border-blue-200">
            <div className="text-3xl font-bold text-blue-600">{total}</div>
            <div className="text-sm text-gray-600 mt-1">
              {language === 'vi' ? 'Tổng số' : 'Total'}
            </div>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-lg border-2 border-green-200">
            <div className="text-3xl font-bold text-green-600">{successCount}</div>
            <div className="text-sm text-gray-600 mt-1">
              {language === 'vi' ? 'Thành công' : 'Success'}
            </div>
          </div>
          <div className="bg-gradient-to-br from-red-50 to-rose-50 p-4 rounded-lg border-2 border-red-200">
            <div className="text-3xl font-bold text-red-600">{failCount}</div>
            <div className="text-sm text-gray-600 mt-1">
              {language === 'vi' ? 'Thất bại' : 'Failed'}
            </div>
          </div>
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
                  {language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'}
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left text-sm font-semibold">
                  {language === 'vi' ? 'Số chứng chỉ' : 'Cert No.'}
                </th>
                <th className="border border-gray-300 px-4 py-2 text-center text-sm font-semibold">
                  {language === 'vi' ? 'Trạng thái' : 'Status'}
                </th>
              </tr>
            </thead>
            <tbody>
              {results.map((result, index) => (
                <tr key={index} className={result.status === 'completed' ? 'bg-green-50' : 'bg-red-50'}>
                  <td className="border border-gray-300 px-4 py-2 text-sm">
                    {result.filename}
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-sm">
                    {result.extracted_info?.cert_name || '-'}
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-sm font-mono">
                    {result.extracted_info?.cert_no || '-'}
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-center">
                    {result.status === 'completed' ? (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                        ✅ {language === 'vi' ? 'Thành công' : 'Success'}
                      </span>
                    ) : (
                      <div>
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800">
                          ❌ {language === 'vi' ? 'Thất bại' : 'Failed'}
                        </span>
                        {result.error && (
                          <div className="text-xs text-red-600 mt-1">
                            {result.error}
                          </div>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer Actions */}
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            {language === 'vi' ? 'Đóng' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );
};
