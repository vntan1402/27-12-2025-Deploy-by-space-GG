/**
 * Edit Ship Certificate Modal Component
 * Modal for editing existing ship certificates
 * Based on V1 Edit Certificate Modal (lines 14635-15090)
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';

export const EditShipCertificateModal = ({ 
  isOpen, 
  onClose, 
  onSuccess,
  certificate
}) => {
  const { language } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Edit form state
  const [editData, setEditData] = useState({
    cert_name: '',
    cert_abbreviation: '',
    cert_no: '',
    cert_type: 'Full Term',
    issue_date: '',
    valid_date: '',
    last_endorse: '',
    next_survey: '',
    next_survey_type: '',
    issued_by: '',
    issued_by_abbreviation: '',
    notes: '',
    exclude_from_auto_update: false
  });

  // Load certificate data when modal opens
  useEffect(() => {
    if (certificate) {
      setEditData({
        cert_name: certificate.cert_name || '',
        cert_abbreviation: certificate.cert_abbreviation || '',
        cert_no: certificate.cert_no || '',
        cert_type: certificate.cert_type || 'Full Term',
        issue_date: certificate.issue_date ? certificate.issue_date.split('T')[0] : '',
        valid_date: certificate.valid_date ? certificate.valid_date.split('T')[0] : '',
        last_endorse: certificate.last_endorse ? certificate.last_endorse.split('T')[0] : '',
        next_survey: certificate.next_survey ? certificate.next_survey.split('T')[0] : '',
        next_survey_type: certificate.next_survey_type || '',
        issued_by: certificate.issued_by || '',
        issued_by_abbreviation: certificate.issued_by_abbreviation || '',
        notes: certificate.notes || '',
        exclude_from_auto_update: certificate.exclude_from_auto_update || false
      });
    }
  }, [certificate]);

  // Date conversion helper (convert YYYY-MM-DD to UTC ISO string)
  const convertDateInputToUTC = (dateInput) => {
    if (!dateInput) return null;
    
    try {
      const parts = dateInput.split('-');
      if (parts.length === 3) {
        const [year, month, day] = parts;
        const date = new Date(Date.UTC(parseInt(year), parseInt(month) - 1, parseInt(day)));
        return date.toISOString();
      }
      
      const date = new Date(dateInput);
      if (!isNaN(date.getTime())) {
        return date.toISOString();
      }
      
      return null;
    } catch (error) {
      console.error('Date conversion error:', error);
      return null;
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!certificate?.id) {
      toast.error(language === 'vi' ? 'Không tìm thấy certificate' : 'Certificate not found');
      return;
    }

    if (!editData.cert_name) {
      toast.error(language === 'vi' ? 'Vui lòng nhập tên chứng chỉ' : 'Please enter certificate name');
      return;
    }

    try {
      setIsSubmitting(true);

      // Prepare update payload with UTC-safe date conversion
      const updatePayload = {
        cert_name: editData.cert_name,
        cert_abbreviation: editData.cert_abbreviation || null,
        cert_no: editData.cert_no || null,
        cert_type: editData.cert_type,
        issue_date: convertDateInputToUTC(editData.issue_date),
        valid_date: convertDateInputToUTC(editData.valid_date),
        last_endorse: editData.last_endorse ? convertDateInputToUTC(editData.last_endorse) : null,
        next_survey: editData.next_survey ? convertDateInputToUTC(editData.next_survey) : null,
        next_survey_type: editData.next_survey_type || null,
        issued_by: editData.issued_by || null,
        issued_by_abbreviation: editData.issued_by_abbreviation || null,
        notes: editData.notes || null,
        exclude_from_auto_update: editData.exclude_from_auto_update || false
      };

      await api.put(`/api/certificates/${certificate.id}`, updatePayload);
      
      toast.success(language === 'vi' 
        ? '✅ Chứng chỉ đã được cập nhật thành công!' 
        : '✅ Certificate updated successfully!'
      );

      onSuccess();
      onClose();
    } catch (error) {
      console.error('Certificate update error:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      
      toast.error(language === 'vi' 
        ? `❌ Không thể cập nhật chứng chỉ: ${errorMessage}` 
        : `❌ Failed to update certificate: ${errorMessage}`
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen || !certificate) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-800">
            ✏️ {language === 'vi' ? 'Chỉnh sửa Ship Certificate' : 'Edit Ship Certificate'}
          </h2>
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
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Row 1: Certificate Name (col-span-3) + Abbreviation + Number + Type */}
          <div className="grid grid-cols-6 gap-4">
            <div className="col-span-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={editData.cert_name}
                onChange={(e) => setEditData({ ...editData, cert_name: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'VD: Safety Management Certificate' : 'e.g. Safety Management Certificate'}
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Viết tắt' : 'Abbreviation'}
              </label>
              <input
                type="text"
                value={editData.cert_abbreviation}
                onChange={(e) => setEditData({ ...editData, cert_abbreviation: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="SMC"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Số chứng chỉ' : 'Certificate No'}
              </label>
              <input
                type="text"
                value={editData.cert_no}
                onChange={(e) => setEditData({ ...editData, cert_no: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                placeholder={language === 'vi' ? 'Nhập số' : 'Enter no'}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Loại' : 'Type'} <span className="text-red-500">*</span>
              </label>
              <select
                value={editData.cert_type}
                onChange={(e) => setEditData({ ...editData, cert_type: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="Full Term">Full Term</option>
                <option value="Interim">Interim</option>
                <option value="Provisional">Provisional</option>
                <option value="Short term">Short term</option>
                <option value="Conditional">Conditional</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          {/* Row 2: Issue Date + Valid Date + Issued By + Abbreviation */}
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ngày cấp' : 'Issue Date'}
              </label>
              <input
                type="date"
                value={editData.issue_date}
                onChange={(e) => setEditData({ ...editData, issue_date: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}
              </label>
              <input
                type="date"
                value={editData.valid_date}
                onChange={(e) => setEditData({ ...editData, valid_date: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Cấp bởi' : 'Issued By'}
              </label>
              <input
                type="text"
                value={editData.issued_by}
                onChange={(e) => setEditData({ ...editData, issued_by: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Tên tổ chức' : 'Organization'}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Viết tắt (Issued By)' : 'Abbreviation'}
              </label>
              <input
                type="text"
                value={editData.issued_by_abbreviation}
                onChange={(e) => setEditData({ ...editData, issued_by_abbreviation: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="ABS"
              />
            </div>
          </div>

          {/* Row 3: Last Endorse + Next Survey + Next Survey Type (conditional on Full Term) */}
          {editData.cert_type === 'Full Term' && (
            <>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Xác nhận cuối' : 'Last Endorse'}
                  </label>
                  <input
                    type="date"
                    value={editData.last_endorse}
                    onChange={(e) => setEditData({ ...editData, last_endorse: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Kiểm tra tới' : 'Next Survey'}
                  </label>
                  <input
                    type="date"
                    value={editData.next_survey}
                    onChange={(e) => setEditData({ ...editData, next_survey: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {editData.next_survey && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Loại kiểm tra tới' : 'Next Survey Type'}
                    </label>
                    <select
                      value={editData.next_survey_type}
                      onChange={(e) => setEditData({ ...editData, next_survey_type: e.target.value })}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">{language === 'vi' ? '-- Chọn --' : '-- Select --'}</option>
                      <option value="Annual">Annual</option>
                      <option value="Intermediate">Intermediate</option>
                      <option value="Renewal">Renewal</option>
                      <option value="Special">Special</option>
                    </select>
                  </div>
                )}
              </div>

              {/* Checkbox: Exclude from Auto Update */}
              <div className="mt-3">
                <label className="flex items-start space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editData.exclude_from_auto_update}
                    onChange={(e) => setEditData({ ...editData, exclude_from_auto_update: e.target.checked })}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="text-sm text-gray-700">
                    {language === 'vi' 
                      ? 'Không tự động cập nhật Next Survey và Next Survey Type cho Giấy chứng nhận này'
                      : 'Do not automatically update Next Survey and Next Survey Type for this certificate'}
                  </span>
                </label>
                {editData.exclude_from_auto_update && (
                  <p className="text-xs text-gray-500 ml-6 mt-1">
                    {language === 'vi' 
                      ? '⚠️ Khi chọn, hệ thống sẽ không tự động cập nhật Next Survey khi click nút "Update Next Survey"'
                      : '⚠️ When checked, system will not automatically update Next Survey when clicking "Update Next Survey" button'}
                  </p>
                )}
              </div>
            </>
          )}

          {/* Row 4: Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Ghi chú' : 'Notes'}
            </label>
            <textarea
              value={editData.notes}
              onChange={(e) => setEditData({ ...editData, notes: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={language === 'vi' ? 'Thêm ghi chú...' : 'Add notes...'}
            />
          </div>

          {/* Footer Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              disabled={isSubmitting}
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !editData.cert_name}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                isSubmitting || !editData.cert_name
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isSubmitting 
                ? (language === 'vi' ? '⏳ Đang lưu...' : '⏳ Saving...') 
                : (language === 'vi' ? '✅ Cập nhật Certificate' : '✅ Update Certificate')
              }
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
