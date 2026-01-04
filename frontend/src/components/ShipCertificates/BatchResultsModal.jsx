/**
 * Batch Results Modal for Ship Certificates
 * Shows summary of batch certificate processing results
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const BatchResultsModal = ({ isOpen, onClose, results, onRetryFile, language: propLanguage }) => {
  const { language: contextLanguage } = useAuth();
  const language = propLanguage || contextLanguage;

  if (!isOpen) return null;

  const successCount = results.filter(r => r.success).length;
  const failCount = results.length - successCount;
  const summaryCount = results.filter(r => r.summaryGenerated).length;  // ⭐ NEW: Count summaries generated

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[80]">
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
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
          <table className="w-full bg-white border border-gray-200 rounded-lg table-auto">
            <thead className="bg-gray-50">
              <tr>
                <th className="border border-gray-300 px-3 py-2 text-left text-sm font-semibold" style={{width: '35%'}}>
                  {language === 'vi' ? 'Tên file' : 'Filename'}
                </th>
                <th className="border border-gray-300 px-3 py-2 text-left text-sm font-semibold" style={{width: '25%'}}>
                  {language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'}
                </th>
                <th className="border border-gray-300 px-3 py-2 text-left text-sm font-semibold whitespace-nowrap" style={{width: '12%'}}>
                  {language === 'vi' ? 'Số chứng chỉ' : 'Cert No.'}
                </th>
                <th className="border border-gray-300 px-3 py-2 text-center text-sm font-semibold" style={{width: '28%'}}>
                  {language === 'vi' ? 'Trạng thái' : 'Status'}
                </th>
              </tr>
            </thead>
            <tbody>
              {results.map((result, index) => (
                <tr key={index} className={result.success ? 'bg-green-50' : 'bg-red-50'}>
                  <td className="border border-gray-300 px-3 py-2 text-sm break-all">
                    {result.filename}
                  </td>
                  <td className="border border-gray-300 px-3 py-2 text-sm">
                    {result.certName || '-'}
                  </td>
                  <td className="border border-gray-300 px-3 py-2 text-sm font-mono whitespace-nowrap">
                    {result.certNo || '-'}
                  </td>
                  <td className="border border-gray-300 px-3 py-2">
                    {result.success ? (
                      <div className="flex items-center justify-center gap-2 flex-wrap">
                        <span className="text-green-600 font-semibold text-sm whitespace-nowrap">
                          ✅ {language === 'vi' ? 'Thành công' : 'Success'}
                        </span>
                        <div className="flex items-center gap-1 flex-wrap justify-center">
                          {result.certificateCreated && (
                            <span className="text-xs text-green-600 whitespace-nowrap" title={language === 'vi' ? 'Đã tạo record' : 'Record created'}>
                              📋
                            </span>
                          )}
                          {result.fileUploaded && (
                            <span className="text-xs text-green-600 whitespace-nowrap" title={language === 'vi' ? 'Đã upload Drive' : 'Uploaded to Drive'}>
                              ☁️
                            </span>
                          )}
                          {result.summaryGenerated && (
                            <span className="text-xs text-blue-600 whitespace-nowrap" title={language === 'vi' ? 'Đã tạo summary' : 'Summary generated'}>
                              📝
                            </span>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center gap-1">
                        <span className="text-red-600 font-semibold text-sm whitespace-nowrap">
                          ❌ {language === 'vi' ? 'Thất bại' : 'Failed'}
                        </span>
                        <span className="text-xs text-red-600 max-w-[200px] break-words text-center">
                          {result.error === 'DUPLICATE' 
                            ? (language === 'vi' ? '⚠️ Đã tồn tại' : '⚠️ Duplicate')
                            : result.error === 'IMO_MISMATCH'
                            ? (language === 'vi' ? '⚠️ IMO không khớp' : '⚠️ IMO mismatch')
                            : result.error === 'SHIP_NAME_MISMATCH'
                            ? (language === 'vi' ? '⚠️ Tên tàu không khớp' : '⚠️ Ship name mismatch')
                            : result.error}
                        </span>
                        {onRetryFile && (
                          <button
                            onClick={() => onRetryFile(result.filename)}
                            className="px-2 py-0.5 bg-orange-500 hover:bg-orange-600 text-white text-xs rounded transition-colors"
                          >
                            🔄 {language === 'vi' ? 'Thử lại' : 'Retry'}
                          </button>
                        )}
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
          <div className="grid grid-cols-4 gap-4 text-center">
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
            <div>
              <div className="text-3xl font-bold text-blue-600">{summaryCount}</div>
              <div className="text-sm text-gray-600 mt-1">
                {language === 'vi' ? 'AI Summary' : 'AI Summary'}
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
