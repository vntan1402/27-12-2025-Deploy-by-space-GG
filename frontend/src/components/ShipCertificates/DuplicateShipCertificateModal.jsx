/**
 * Duplicate Ship Certificate Modal Component
 * Shows when backend detects duplicate certificates
 * Allows user to Skip, Replace, or Keep Both
 */
import React from 'react';

export const DuplicateShipCertificateModal = ({
  isOpen,
  onClose,
  duplicates = [],
  currentFile,
  analysisResult,
  onResolution,
  language
}) => {
  if (!isOpen) return null;

  const handleResolution = (action) => {
    onResolution(action);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h2 className="text-xl font-semibold text-gray-800">
              {language === 'vi' ? '⚠️ Phát hiện Certificate trùng' : '⚠️ Duplicate Certificate Detected'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Warning Message */}
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <p className="text-orange-800 text-sm">
              {language === 'vi'
                ? 'Hệ thống phát hiện certificate có thể trùng với certificate đã tồn tại. Vui lòng xem xét thông tin bên dưới và quyết định:'
                : 'System detected a potential duplicate certificate. Please review the information below and decide:'
              }
            </p>
          </div>

          {/* Current File Info */}
          {currentFile && (
            <div className="border rounded-lg p-4 bg-blue-50">
              <h3 className="font-semibold text-blue-900 mb-2">
                {language === 'vi' ? '📄 File đang upload:' : '📄 Current File:'}
              </h3>
              <div className="text-sm text-blue-800">
                <p><span className="font-medium">{language === 'vi' ? 'Tên file:' : 'Filename:'}</span> {currentFile.name}</p>
                {analysisResult && (
                  <>
                    <p><span className="font-medium">{language === 'vi' ? 'Tên certificate:' : 'Cert Name:'}</span> {analysisResult.cert_name || '-'}</p>
                    <p><span className="font-medium">{language === 'vi' ? 'Số certificate:' : 'Cert No:'}</span> {analysisResult.cert_no || '-'}</p>
                    <p><span className="font-medium">{language === 'vi' ? 'Ngày cấp:' : 'Issue Date:'}</span> {analysisResult.issue_date || '-'}</p>
                    <p><span className="font-medium">{language === 'vi' ? 'Ngày hết hạn:' : 'Valid Date:'}</span> {analysisResult.valid_date || '-'}</p>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Existing Duplicates */}
          {duplicates.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-900">
                {language === 'vi' ? `🔍 Certificate trùng (${duplicates.length}):` : `🔍 Existing Certificates (${duplicates.length}):`}
              </h3>
              {duplicates.map((dup, index) => (
                <div key={index} className="border rounded-lg p-3 bg-gray-50">
                  <div className="text-sm text-gray-700">
                    <p><span className="font-medium">{language === 'vi' ? 'Tên:' : 'Name:'}</span> {dup.cert_name}</p>
                    <p><span className="font-medium">{language === 'vi' ? 'Số:' : 'No:'}</span> {dup.cert_no}</p>
                    <p><span className="font-medium">{language === 'vi' ? 'Loại:' : 'Type:'}</span> {dup.cert_type}</p>
                    <p><span className="font-medium">{language === 'vi' ? 'Ngày cấp:' : 'Issue Date:'}</span> {dup.issue_date || '-'}</p>
                    <p><span className="font-medium">{language === 'vi' ? 'Ngày hết hạn:' : 'Valid Date:'}</span> {dup.valid_date || '-'}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Action Buttons */}
          <div className="border-t pt-4 space-y-3">
            <h3 className="font-semibold text-gray-900">
              {language === 'vi' ? 'Chọn hành động:' : 'Choose Action:'}
            </h3>
            
            {/* Skip File */}
            <button
              onClick={() => handleResolution('skip')}
              className="w-full flex items-center gap-3 p-4 border-2 border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-left"
            >
              <div className="flex-shrink-0 w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <div className="flex-1">
                <div className="font-medium text-gray-900">
                  {language === 'vi' ? '❌ Bỏ qua file này' : '❌ Skip this file'}
                </div>
                <div className="text-sm text-gray-600">
                  {language === 'vi' ? 'Không upload file, giữ nguyên certificate cũ' : 'Don\'t upload this file, keep existing certificate'}
                </div>
              </div>
            </button>

            {/* Replace Existing */}
            <button
              onClick={() => handleResolution('replace')}
              className="w-full flex items-center gap-3 p-4 border-2 border-orange-300 rounded-lg hover:bg-orange-50 transition-colors text-left"
            >
              <div className="flex-shrink-0 w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </div>
              <div className="flex-1">
                <div className="font-medium text-gray-900">
                  {language === 'vi' ? '🔄 Thay thế certificate cũ' : '🔄 Replace existing certificate'}
                </div>
                <div className="text-sm text-gray-600">
                  {language === 'vi' ? 'Xóa certificate cũ và upload file mới' : 'Delete old certificate and upload new file'}
                </div>
              </div>
            </button>

            {/* Keep Both */}
            <button
              onClick={() => handleResolution('keep_both')}
              className="w-full flex items-center gap-3 p-4 border-2 border-green-300 rounded-lg hover:bg-green-50 transition-colors text-left"
            >
              <div className="flex-shrink-0 w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="flex-1">
                <div className="font-medium text-gray-900">
                  {language === 'vi' ? '✅ Giữ cả hai' : '✅ Keep both'}
                </div>
                <div className="text-sm text-gray-600">
                  {language === 'vi' ? 'Upload file mới và giữ certificate cũ (có 2 certificate giống nhau)' : 'Upload new file and keep old certificate (will have 2 similar certificates)'}
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
