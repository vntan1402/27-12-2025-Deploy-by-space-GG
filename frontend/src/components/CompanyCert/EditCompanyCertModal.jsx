/**
 * Edit Company Certificate Modal
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import api from '../../services/api';

export const EditCompanyCertModal = ({
  isOpen,
  onClose,
  onSuccess,
  certificate,
  language
}) => {
  const [formData, setFormData] = useState({
    cert_name: '',
    cert_no: '',
    issue_date: '',
    valid_date: '',
    issued_by: '',
    notes: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (certificate) {
      setFormData({
        cert_name: certificate.cert_name || '',
        cert_no: certificate.cert_no || '',
        issue_date: certificate.issue_date || '',
        valid_date: certificate.valid_date || '',
        issued_by: certificate.issued_by || '',
        notes: certificate.notes || ''
      });
    }
  }, [certificate]);

  if (!isOpen || !certificate) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    setIsSubmitting(true);
    try {
      await api.put(`/company-certs/${certificate.id}`, formData);
      toast.success(language === 'vi' ? 'Cập nhật thành công!' : 'Updated successfully!');
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Update error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? 'Sửa chứng chỉ' : 'Edit Certificate'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'} *
            </label>
            <input
              type="text"
              required
              value={formData.cert_name}
              onChange={(e) => setFormData({ ...formData, cert_name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Số chứng chỉ' : 'Certificate No'} *
            </label>
            <input
              type="text"
              required
              value={formData.cert_no}
              onChange={(e) => setFormData({ ...formData, cert_no: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ngày cấp' : 'Issue Date'}
              </label>
              <input
                type="date"
                value={formData.issue_date}
                onChange={(e) => setFormData({ ...formData, issue_date: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}
              </label>
              <input
                type="date"
                value={formData.valid_date}
                onChange={(e) => setFormData({ ...formData, valid_date: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Cơ quan cấp' : 'Issued By'}
            </label>
            <input
              type="text"
              value={formData.issued_by}
              onChange={(e) => setFormData({ ...formData, issued_by: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Ghi chú' : 'Notes'}
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              rows="3"
            />
          </div>

          <div className="flex gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
              disabled={isSubmitting}
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-400"
            >
              {isSubmitting ? (language === 'vi' ? 'Đang lưu...' : 'Saving...') : (language === 'vi' ? 'Cập nhật' : 'Update')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditCompanyCertModal;