/**
 * Delete Company Certificate Modal
 */
import React, { useState } from 'react';
import { toast } from 'sonner';
import api from '../../services/api';

export const DeleteCompanyCertModal = ({
  isOpen,
  onClose,
  onSuccess,
  certificate,
  language
}) => {
  const [isDeleting, setIsDeleting] = useState(false);

  if (!isOpen || !certificate) return null;

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await api.delete(`/api/company-certs/${certificate.id}`);
      toast.success(language === 'vi' ? 'Xóa thành công!' : 'Deleted successfully!');
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Delete error:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">
            {language === 'vi' ? 'Xác nhận xóa' : 'Confirm Delete'}
          </h2>
          <p className="text-gray-600 mb-6">
            {language === 'vi' 
              ? `Bạn có chắc muốn xóa chứng chỉ "${certificate.cert_name}"?`
              : `Are you sure you want to delete certificate "${certificate.cert_name}"?`
            }
          </p>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={isDeleting}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400"
            >
              {isDeleting ? (language === 'vi' ? 'Đang xóa...' : 'Deleting...') : (language === 'vi' ? 'Xóa' : 'Delete')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteCompanyCertModal;