/**
 * Approval Document Notes Modal
 * Features:
 * - View full note content
 * - Edit note
 * - Save changes
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import approvalDocumentService from '../../services/approvalDocumentService';
import { toast } from 'sonner';

export const ApprovalDocumentNotesModal = ({ isOpen, onClose, document, onNoteUpdated }) => {
  const { language } = useAuth();
  const [isSaving, setIsSaving] = useState(false);
  const [note, setNote] = useState('');

  // Load note when modal opens
  useEffect(() => {
    if (document) {
      setNote(document.note || '');
    }
  }, [document]);

  // ========== SAVE NOTE ==========
  const handleSave = async () => {
    try {
      setIsSaving(true);

      // Update only the note field
      await approvalDocumentService.update(document.id, {
        note: note.trim() || null
      });

      toast.success(
        language === 'vi' 
          ? '✅ Đã cập nhật ghi chú' 
          : '✅ Note updated'
      );

      // Close modal and refresh
      onNoteUpdated();
      onClose();

    } catch (error) {
      console.error('Failed to update note:', error);
      toast.error(
        language === 'vi' 
          ? '❌ Không thể cập nhật ghi chú' 
          : '❌ Failed to update note'
      );
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen || !document) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-2xl font-bold text-gray-800">
              {language === 'vi' ? '📝 Ghi chú' : '📝 Note'}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {document.approval_document_name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title={language === 'vi' ? 'Đóng' : 'Close'}
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Note Content */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {language === 'vi' ? 'Nội dung ghi chú' : 'Note Content'}
          </label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows="10"
            placeholder={language === 'vi' ? 'Nhập ghi chú...' : 'Enter note...'}
          />
          <p className="text-xs text-gray-500 mt-1">
            {language === 'vi' 
              ? 'Ghi chú này sẽ hiển thị trong bảng với dấu * màu đỏ' 
              : 'This note will be displayed in the table with a red asterisk *'}
          </p>
        </div>

        {/* Footer Buttons */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all font-medium"
            disabled={isSaving}
          >
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              isSaving
                ? 'bg-gray-400 cursor-not-allowed text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {isSaving ? (
              <span className="flex items-center">
                <svg className="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {language === 'vi' ? 'Đang lưu...' : 'Saving...'}
              </span>
            ) : (
              language === 'vi' ? 'Lưu' : 'Save'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
