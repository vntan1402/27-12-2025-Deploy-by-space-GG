/**
 * Edit Drawing Manual Modal
 * Simple edit form for document metadata
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { formatDateForInput } from '../../utils/dateHelpers';

export const EditDrawingManualModal = ({ isOpen, onClose, document, onDocumentUpdated }) => {
  const { language } = useAuth();
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState({
    document_name: '',
    document_no: '',
    approved_by: '',
    approved_date: '',
    status: 'Unknown',
    note: ''
  });

  // Initialize form when document changes
  useEffect(() => {
    if (document) {
      setFormData({
        document_name: document.document_name || '',
        document_no: document.document_no || '',
        approved_by: document.approved_by || '',
        approved_date: formatDateForInput(document.approved_date) || '',
        status: document.status || 'Unknown',
        note: document.note || ''
      });
    }
  }, [document]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSave = async () => {
    // Validate required fields
    if (!formData.document_name.trim()) {
      toast.error(language === 'vi' ? 'Vui lòng nhập tên tài liệu' : 'Please enter document name');
      return;
    }

    try {
      setIsSaving(true);

      const updateData = {
        document_name: formData.document_name.trim(),
        document_no: formData.document_no?.trim() || null,
        approved_by: formData.approved_by?.trim() || null,
        approved_date: formData.approved_date || null,
        status: formData.status,
        note: formData.note?.trim() || null
      };

      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${BACKEND_URL}/api/drawings-manuals/${document.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Failed to update document');
      }

      toast.success(language === 'vi' ? '✅ Đã cập nhật tài liệu' : '✅ Document updated');
      
      onClose();
      
      if (onDocumentUpdated) {
        onDocumentUpdated();
      }

    } catch (error) {
      console.error('Failed to update document:', error);
      const errorMsg = error.message || 'Failed to update document';
      toast.error(language === 'vi' ? `❌ Không thể cập nhật tài liệu: ${errorMsg}` : `❌ ${errorMsg}`);
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
          <h3 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? '✏️ Chỉnh sửa Bản vẽ & Sổ tay' : '✏️ Edit Drawings & Manuals'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-all"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <div className="space-y-3">
          {/* Row 1: Document Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Tên Tài liệu' : 'Document Name'} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="document_name"
              value={formData.document_name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder={language === 'vi' ? 'VD: General Arrangement Plan' : 'e.g. General Arrangement Plan'}
            />
          </div>

          {/* Row 2: Document No. + Approved By */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Số Tài liệu' : 'Document No.'}
              </label>
              <input
                type="text"
                name="document_no"
                value={formData.document_no}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                placeholder={language === 'vi' ? 'VD: GA-001-2024' : 'e.g. GA-001-2024'}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Phê duyệt bởi' : 'Approved By'}
              </label>
              <input
                type="text"
                name="approved_by"
                value={formData.approved_by}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                placeholder={language === 'vi' ? "VD: Lloyd's Register" : "e.g. Lloyd's Register"}
              />
            </div>
          </div>

          {/* Row 3: Approved Date + Status */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ngày phê duyệt' : 'Approved Date'}
              </label>
              <input
                type="date"
                name="approved_date"
                value={formData.approved_date}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Trạng thái' : 'Status'}
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              >
                <option value="Valid">{language === 'vi' ? 'Hợp lệ' : 'Valid'}</option>
                <option value="Approved">{language === 'vi' ? 'Đã phê duyệt' : 'Approved'}</option>
                <option value="Expired">{language === 'vi' ? 'Hết hạn' : 'Expired'}</option>
                <option value="Unknown">{language === 'vi' ? 'Chưa rõ' : 'Unknown'}</option>
              </select>
            </div>
          </div>

          {/* Row 4: Note */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Ghi chú' : 'Note'}
            </label>
            <textarea
              name="note"
              value={formData.note}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              rows="2"
              placeholder={language === 'vi' ? 'Ghi chú...' : 'Notes...'}
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3 mt-6">
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
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all font-medium disabled:opacity-50 flex items-center gap-2"
          >
            {isSaving && (
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
            {language === 'vi' ? 'Lưu' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
};
