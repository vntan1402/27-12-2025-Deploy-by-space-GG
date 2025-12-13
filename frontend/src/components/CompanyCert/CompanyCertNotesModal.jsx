/**
 * Company Certificate Notes Modal
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import api from '../../services/api';

export const CompanyCertNotesModal = ({
  isOpen,
  onClose,
  onSuccess,
  certificate,
  language
}) => {
  const [notes, setNotes] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (certificate) {
      setNotes(certificate.notes || '');
    }
  }, [certificate]);

  if (!isOpen || !certificate) return null;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await api.put(`/api/company-certs/${certificate.id}`, {
        notes: notes,
        has_notes: Boolean(notes && notes.trim().length > 0)
      });
      toast.success(language === 'vi' ? 'Cập nhật ghi chú thành công!' : 'Notes updated successfully!');
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Save notes error:', error);
      
      // Handle validation errors
      let errorMessage = 'Failed to save notes';
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (Array.isArray(detail)) {
          errorMessage = detail.map(err => err.msg || JSON.stringify(err)).join(', ');
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        } else {
          errorMessage = JSON.stringify(detail);
        }
      }
      
      toast.error(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-bold text-gray-800">
            {language === 'vi' ? 'Ghi chú' : 'Notes'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">
            ×
          </button>
        </div>

        <div className="p-6">
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              <strong>{language === 'vi' ? 'Chứng chỉ:' : 'Certificate:'}</strong> {certificate.cert_name}
            </p>
            <p className="text-sm text-gray-600">
              <strong>{language === 'vi' ? 'Số:' : 'No:'}</strong> {certificate.cert_no}
            </p>
          </div>

          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            rows="8"
            placeholder={language === 'vi' ? 'Nhập ghi chú...' : 'Enter notes...'}
          />

          <div className="flex gap-3 mt-4">
            <button
              onClick={onClose}
              disabled={isSaving}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
            >
              {isSaving ? (language === 'vi' ? 'Đang lưu...' : 'Saving...') : (language === 'vi' ? 'Lưu' : 'Save')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanyCertNotesModal;