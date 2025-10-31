/**
 * Edit Other Document Modal
 * Modal for editing existing other documents
 * 
 * Features:
 * - Edit Document Name, Date, Status, Note
 * - No file upload (files are managed separately)
 * - Simple form without AI features
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import otherDocumentService from '../../services/otherDocumentService';

const EditOtherDocumentModal = ({ show, onClose, document, onSuccess }) => {
  const { language } = useAuth();

  // Form state
  const [formData, setFormData] = useState({
    document_name: '',
    date: '',
    status: 'Unknown',
    note: ''
  });

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);

  // Initialize form data when document changes
  useEffect(() => {
    if (document) {
      setFormData({
        document_name: document.document_name || '',
        date: document.date || '',
        status: document.status || 'Unknown',
        note: document.note || ''
      });
    }
  }, [document]);

  // Handle form submission
  const handleSubmit = async () => {
    // Validate document name
    if (!formData.document_name.trim()) {
      toast.error(language === 'vi' 
        ? 'Vui lòng nhập tên tài liệu' 
        : 'Please enter document name');
      return;
    }

    try {
      setIsProcessing(true);

      await otherDocumentService.update(document.id, {
        document_name: formData.document_name,
        date: formData.date || null,
        status: formData.status,
        note: formData.note || null
      });

      toast.success(language === 'vi' 
        ? '✅ Đã cập nhật tài liệu thành công!' 
        : '✅ Document updated successfully!');
      
      onSuccess();
    } catch (error) {
      console.error('Failed to update document:', error);
      toast.error(language === 'vi' 
        ? `❌ Lỗi: ${error.message}` 
        : `❌ Error: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!show) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? '✏️ Chỉnh sửa Tài liệu' : '✏️ Edit Document'}
          </h3>
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="text-gray-400 hover:text-gray-600 transition-all"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <div className="space-y-4">
          {/* Document Information */}
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên Tài liệu' : 'Document Name'}
                <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.document_name}
                onChange={(e) => setFormData(prev => ({ ...prev, document_name: e.target.value }))}
                placeholder={language === 'vi' ? 'Nhập tên tài liệu...' : 'Enter document name...'}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày' : 'Date'}
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Trạng thái' : 'Status'}
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Valid">{language === 'vi' ? 'Hợp lệ' : 'Valid'}</option>
                  <option value="Expired">{language === 'vi' ? 'Hết hạn' : 'Expired'}</option>
                  <option value="Unknown">{language === 'vi' ? 'Chưa rõ' : 'Unknown'}</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ghi chú' : 'Note'}
              </label>
              <textarea
                value={formData.note}
                onChange={(e) => setFormData(prev => ({ ...prev, note: e.target.value }))}
                placeholder={language === 'vi' ? 'Nhập ghi chú...' : 'Enter note...'}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                rows="3"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 mt-6">
            <button
              onClick={onClose}
              disabled={isProcessing}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all disabled:opacity-50"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              onClick={handleSubmit}
              disabled={!formData.document_name.trim() || isProcessing}
              className={`px-6 py-2 rounded-lg transition-all font-medium ${
                !formData.document_name.trim() || isProcessing
                  ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {isProcessing
                ? (language === 'vi' ? '⏳ Đang lưu...' : '⏳ Saving...')
                : (language === 'vi' ? '💾 Lưu' : '💾 Save')
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditOtherDocumentModal;
