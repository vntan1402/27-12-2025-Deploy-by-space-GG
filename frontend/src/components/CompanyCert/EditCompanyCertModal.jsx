/**
 * Edit Company Certificate Modal
 * Layout matches Add Company Certificate Modal
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
    company_name: '',
    issue_date: '',
    valid_date: '',
    last_endorse: '',
    next_survey: '',
    next_survey_type: '',
    issued_by: '',
    notes: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (certificate) {
      setFormData({
        cert_name: certificate.cert_name || '',
        cert_no: certificate.cert_no || '',
        company_name: certificate.company_name || '',
        issue_date: certificate.issue_date || '',
        valid_date: certificate.valid_date || '',
        last_endorse: certificate.last_endorse || '',
        next_survey: certificate.next_survey || '',
        next_survey_type: certificate.next_survey_type || '',
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
      // Add has_notes flag based on notes content
      const updateData = {
        ...formData,
        has_notes: formData.notes && formData.notes.trim().length > 0
      };
      
      await api.put(`/api/company-certs/${certificate.id}`, updateData);
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
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 flex justify-between items-center z-10">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            📝 {language === 'vi' ? 'Sửa Company Certificate' : 'Edit Company Certificate'}
          </h2>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 transition-colors"
            disabled={isSubmitting}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Form Fields */}
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-md font-semibold text-gray-700">
                ✍️ {language === 'vi' ? 'Thông tin chứng chỉ:' : 'Certificate Information:'}
              </h3>
            </div>

            {/* Row 1: Certificate Name, Number & Company Name */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.cert_name}
                  onChange={(e) => setFormData({...formData, cert_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  placeholder={language === 'vi' ? 'Nhập tên chứng chỉ' : 'Enter certificate name'}
                  required
                  disabled={isSubmitting}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Số chứng chỉ' : 'Certificate Number'}
                </label>
                <input
                  type="text"
                  value={formData.cert_no}
                  onChange={(e) => setFormData({...formData, cert_no: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 font-mono"
                  placeholder={language === 'vi' ? 'Số chứng chỉ' : 'Cert No'}
                  disabled={isSubmitting}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tên công ty' : 'Company Name'}
                </label>
                <input
                  type="text"
                  value={formData.company_name}
                  onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  placeholder={language === 'vi' ? 'Tên công ty trên chứng chỉ' : 'Company name on certificate'}
                  disabled={isSubmitting}
                />
              </div>
            </div>

            {/* Row 2: All Dates in One Row - 4 columns */}
            <div className="grid grid-cols-4 gap-3 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày cấp' : 'Issue Date'}
                </label>
                <input
                  type="date"
                  value={formData.issue_date}
                  onChange={(e) => setFormData({...formData, issue_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                  disabled={isSubmitting}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}
                </label>
                <input
                  type="date"
                  value={formData.valid_date}
                  onChange={(e) => setFormData({...formData, valid_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                  disabled={isSubmitting}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Xác nhận cuối' : 'Last Endorse'}
                </label>
                <input
                  type="date"
                  value={formData.last_endorse}
                  onChange={(e) => setFormData({...formData, last_endorse: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                  disabled={isSubmitting}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Kiểm tra tới' : 'Next Survey'}
                </label>
                <input
                  type="date"
                  value={formData.next_survey}
                  onChange={(e) => setFormData({...formData, next_survey: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                  disabled={isSubmitting}
                />
              </div>
            </div>

            {/* Row 3: Survey Type & Issued By */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Loại kiểm tra' : 'Survey Type'}
                </label>
                <select
                  value={formData.next_survey_type}
                  onChange={(e) => setFormData({...formData, next_survey_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  disabled={isSubmitting}
                >
                  <option value="">{language === 'vi' ? '-- Chọn loại --' : '-- Select Type --'}</option>
                  <option value="Initial">Initial</option>
                  <option value="Annual">Annual</option>
                  <option value="Intermediate">Intermediate</option>
                  <option value="Renewal">Renewal</option>
                  <option value="Special">Special</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Cơ quan cấp' : 'Issued By'}
                </label>
                <input
                  type="text"
                  value={formData.issued_by}
                  onChange={(e) => setFormData({...formData, issued_by: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  placeholder={language === 'vi' ? 'Tên cơ quan cấp' : 'Issuing authority'}
                  disabled={isSubmitting}
                />
              </div>
            </div>

            {/* Row 4: Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ghi chú' : 'Notes'}
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({...formData, notes: e.target.value})}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 resize-none"
                placeholder={language === 'vi' ? 'Nhập ghi chú (nếu có)' : 'Enter notes (optional)'}
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
              disabled={isSubmitting}
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`px-6 py-2 rounded-lg text-white font-medium transition-all ${
                isSubmitting
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg'
              }`}
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  {language === 'vi' ? 'Đang cập nhật...' : 'Updating...'}
                </span>
              ) : (
                language === 'vi' ? 'Cập nhật' : 'Update'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
