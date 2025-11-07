/**
 * Other Audit Document Notes Modal
 * Modal for viewing and editing document notes
 * Similar to TestReportNotesModal
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import otherAuditDocumentService from '../../services/otherAuditDocumentService';

const OtherAuditDocumentNotesModal = ({ show, onClose, document, onUpdate }) => {
  const { language } = useAuth();
  const [note, setNote] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Initialize note when document changes
  useEffect(() => {
    if (document) {
      setNote(document.note || '');
    }
  }, [document]);

  const handleSave = async () => {
    if (!document) return;

    try {
      setIsSaving(true);
      await otherAuditDocumentService.update(document.id, { note });
      
      toast.success(language === 'vi' 
        ? '✅ Đã lưu ghi chú!' 
        : '✅ Note saved!');
      
      onUpdate();
      onClose();
    } catch (error) {
      console.error('Failed to save note:', error);
      toast.error(language === 'vi' 
        ? '❌ Không thể lưu ghi chú' 
        : '❌ Failed to save note');
    } finally {
      setIsSaving(false);
    }
  };

  if (!show || !document) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full mx-4">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-gray-800">
            {language === 'vi' ? '📝 Ghi chú' : '📝 Notes'}
          </h3>
          <button
            onClick={onClose}
            disabled={isSaving}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Document Info */}
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">
            {language === 'vi' ? 'Tài liệu:' : 'Document:'}
            <span className="ml-2 font-semibold text-gray-800">{document.document_name}</span>
          </p>
        </div>

        {/* Note Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {language === 'vi' ? 'Nội dung ghi chú:' : 'Note content:'}
          </label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={language === 'vi' ? 'Nhập ghi chú...' : 'Enter note...'}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows="6"
            disabled={isSaving}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={isSaving}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all disabled:opacity-50"
          >
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all disabled:opacity-50 flex items-center gap-2"
          >
            {isSaving ? (
              <>
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {language === 'vi' ? 'Đang lưu...' : 'Saving...'}
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {language === 'vi' ? 'Lưu' : 'Save'}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default OtherAuditDocumentNotesModal;
