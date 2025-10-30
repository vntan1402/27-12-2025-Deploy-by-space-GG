/**
 * Ship Name Mismatch Modal Component
 * Shows when extracted ship name doesn't match selected ship
 * Allows user to Continue or Cancel
 */
import React from 'react';

export const ShipNameMismatchModal = ({
  isOpen,
  onClose,
  extractedShipName,
  selectedShipName,
  currentFile,
  analysisResult,
  onContinue,
  onCancel,
  language
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-xl w-full">
        {/* Header */}
        <div className="bg-yellow-50 border-b border-yellow-200 px-6 py-4 flex items-center gap-3">
          <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h2 className="text-xl font-semibold text-yellow-900">
            {language === 'vi' ? '⚠️ Tên tàu không khớp' : '⚠️ Ship Name Mismatch'}
          </h2>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Warning Message */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-800 text-sm font-medium mb-2">
              {language === 'vi'
                ? 'Tên tàu trích xuất từ certificate không khớp với tàu đã chọn!'
                : 'Ship name extracted from certificate doesn\'t match the selected ship!'
              }
            </p>
            <p className="text-yellow-700 text-xs">
              {language === 'vi'
                ? 'Vui lòng kiểm tra kỹ thông tin trước khi tiếp tục.'
                : 'Please carefully verify the information before continuing.'
              }
            </p>
          </div>

          {/* Ship Name Comparison */}
          <div className="grid grid-cols-2 gap-4">
            {/* Selected Ship */}
            <div className="border-2 border-blue-300 rounded-lg p-4 bg-blue-50">
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="font-semibold text-blue-900">
                  {language === 'vi' ? 'Tàu đã chọn' : 'Selected Ship'}
                </h3>
              </div>
              <p className="text-blue-800 font-bold text-lg">{selectedShipName}</p>
            </div>

            {/* Extracted Ship */}
            <div className="border-2 border-orange-300 rounded-lg p-4 bg-orange-50">
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <h3 className="font-semibold text-orange-900">
                  {language === 'vi' ? 'Tên từ Certificate' : 'From Certificate'}
                </h3>
              </div>
              <p className="text-orange-800 font-bold text-lg">{extractedShipName || 'N/A'}</p>
            </div>
          </div>

          {/* File Info */}
          {currentFile && (
            <div className="border rounded-lg p-3 bg-gray-50">
              <h4 className="font-medium text-gray-700 text-sm mb-2">
                {language === 'vi' ? '📄 Thông tin file:' : '📄 File Information:'}
              </h4>
              <div className="text-xs text-gray-600 space-y-1">
                <p><span className="font-medium">{language === 'vi' ? 'Tên file:' : 'Filename:'}</span> {currentFile.name}</p>
                {analysisResult && (
                  <>
                    {analysisResult.cert_name && (
                      <p><span className="font-medium">{language === 'vi' ? 'Certificate:' : 'Certificate:'}</span> {analysisResult.cert_name}</p>
                    )}
                    {analysisResult.cert_no && (
                      <p><span className="font-medium">{language === 'vi' ? 'Số:' : 'No:'}</span> {analysisResult.cert_no}</p>
                    )}
                  </>
                )}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t">
            <button
              onClick={() => {
                onCancel();
                onClose();
              }}
              className="flex-1 px-4 py-3 border-2 border-red-300 text-red-700 font-medium rounded-lg hover:bg-red-50 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              {language === 'vi' ? 'Hủy bỏ' : 'Cancel'}
            </button>
            
            <button
              onClick={() => {
                onContinue();
                onClose();
              }}
              className="flex-1 px-4 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {language === 'vi' ? 'Tiếp tục' : 'Continue Anyway'}
            </button>
          </div>

          {/* Info Message */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-blue-700 text-xs">
              <span className="font-medium">💡 {language === 'vi' ? 'Gợi ý:' : 'Tip:'}</span>{' '}
              {language === 'vi'
                ? 'Nếu certificate thuộc về tàu khác, vui lòng chọn "Hủy bỏ" và chọn đúng tàu trước khi upload lại.'
                : 'If the certificate belongs to a different ship, please select "Cancel" and choose the correct ship before uploading again.'
              }
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
