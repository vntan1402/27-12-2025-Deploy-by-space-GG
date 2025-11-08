/**
 * Batch Results Modal for Ship Certificates
 * Shows summary of batch certificate processing results
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const BatchResultsModal = ({ isOpen, onClose, results }) => {
  const { language } = useAuth();

  if (!isOpen) return null;

  const successCount = results.filter(r => r.success).length;
  const failCount = results.length - successCount;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[80]">
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="mb-6">
          <h3 className="text-2xl font-bold text-gray-800 mb-2">
            {language === 'vi' ? '📊 Kết quả xử lý Ship Certificates' : '📊 Ship Certificate Processing Results'}
          </h3>
          <p className="text-gray-600">
            {language === 'vi' 
              ? `Đã xử lý ${results.length} chứng chỉ`
              : `Processed ${results.length} certificates`}
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
                <tr key={index} className={result.success ? 'bg-green-50' : 'bg-red-50'}>
                  <td className="border border-gray-300 px-4 py-2 text-sm">
                    {result.filename}
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-sm">
                    {result.certName || '-'}
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-sm font-mono">
                    {result.certNo || '-'}
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-center">
                    {result.success ? (
                      <div className="flex flex-col items-center gap-1">
                        <span className="text-green-600 font-semibold">
                          ✅ {language === 'vi' ? 'Thành công' : 'Success'}
                        </span>
                        {result.certificateCreated && (
                          <span className="text-xs text-green-600">
                            {language === 'vi' ? '📋 Đã tạo record' : '📋 Record created'}
                          </span>
                        )}
                        {result.fileUploaded && (
                          <span className="text-xs text-green-600">
                            {language === 'vi' ? '☁️ Đã upload Drive' : '☁️ Uploaded to Drive'}
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
                            : result.error === 'IMO_MISMATCH'
                            ? (language === 'vi' ? '⚠️ IMO không khớp' : '⚠️ IMO mismatch')
                            : result.error === 'SHIP_NAME_MISMATCH'
                            ? (language === 'vi' ? '⚠️ Tên tàu không khớp' : '⚠️ Ship name mismatch')
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
              <div className="text-3xl font-bold text-gray-800">{results.length}</div>
              <div className="text-sm text-gray-600 mt-1">
                {language === 'vi' ? 'Tổng số' : 'Total'}
              </div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600">{successCount}</div>
              <div className="text-sm text-gray-600 mt-1">
                {language === 'vi' ? 'Thành công' : 'Success'}
              </div>
            </div>
            <div>
              <div className="text-3xl font-bold text-red-600">{failCount}</div>
              <div className="text-sm text-gray-600 mt-1">
                {language === 'vi' ? 'Thất bại' : 'Failed'}
              </div>
            </div>
          </div>
        </div>

        {/* Close Button */}
        <div className="flex justify-end">
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
