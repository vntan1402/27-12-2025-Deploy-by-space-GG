/**
 * Audit Certificate Notes Modal Component
 * Modal for viewing and editing audit certificate notes
 * 
 * ⭐ IMPORTANT: Parent must pass `key={certificate?.id}` to force re-render
 */
import React, { useState } from 'react';

export const AuditCertificateNotesModal = ({
  isOpen,
  onClose,
  onSave,
  certificate,
  notes,
  language
}) => {
  // ⭐ FIX: Initialize with notes prop (will reset when key changes)
  const [currentNotes, setCurrentNotes] = useState(notes || '');

  if (!isOpen) return null;

  const handleSave = () => {
    onSave(currentNotes);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full">
        {/* Header */}
        <div className="mb-4 pb-4 border-b border-gray-200">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-xl font-bold text-gray-800">
                {language === 'vi' ? '📝 Ghi chú Audit Certificate' : '📝 Audit Certificate Notes'}
              </h3>
              {certificate && (
                <p className="text-sm text-gray-600 mt-1">
                  <span className="font-medium">{certificate.cert_abbreviation || certificate.cert_name}</span>
                  {certificate.cert_no && ` - ${certificate.cert_no}`}
                </p>
              )}
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
        </div>

        {/* Notes Input */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {language === 'vi' ? 'Ghi chú' : 'Notes'}
          </label>
          <textarea
            value={currentNotes}
            onChange={(e) => setCurrentNotes(e.target.value)}
            rows={8}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            placeholder={language === 'vi' 
              ? 'Nhập ghi chú cho audit certificate này...'
              : 'Enter notes for this audit certificate...'}
          />
          <p className="text-xs text-gray-500 mt-1">
            {language === 'vi' 
              ? 'Ghi chú sẽ được lưu vào database và hiển thị dấu "*" trong bảng'
              : 'Notes will be saved to database and shown with "*" icon in table'}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg text-sm font-medium transition-all"
          >
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-all flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            {language === 'vi' ? 'Lưu ghi chú' : 'Save Notes'}
          </button>
        </div>
      </div>
    </div>
  );
};
