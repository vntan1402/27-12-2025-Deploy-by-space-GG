/**
 * Edit Audit Certificate Modal - Simplified Version
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';

export const EditAuditCertificateModal = ({
  isOpen,
  onClose,
  onSave,
  certificate,
  language
}) => {
  const [formData, setFormData] = useState({
    ship_name: '',
    ship_imo: '',
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
    notes: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (certificate) {
      setFormData({
        cert_name: certificate.cert_name || '',
        cert_abbreviation: certificate.cert_abbreviation || '',
        cert_no: certificate.cert_no || '',
        cert_type: certificate.cert_type || 'Full Term',
        issue_date: certificate.issue_date?.split('T')[0] || '',
        valid_date: certificate.valid_date?.split('T')[0] || '',
        last_endorse: certificate.last_endorse?.split('T')[0] || '',
        next_survey: certificate.next_survey?.split('T')[0] || '',
        next_survey_type: certificate.next_survey_type || '',
        issued_by: certificate.issued_by || '',
        issued_by_abbreviation: certificate.issued_by_abbreviation || '',
        notes: certificate.notes || ''
      });
    }
  }, [certificate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.cert_name || !formData.cert_no) {
      toast.error(language === 'vi' ? 'Vui lòng điền đầy đủ thông tin bắt buộc' : 'Please fill all required fields');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSave(certificate.id, formData);
    } catch (error) {
      // Error handled by parent
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen || !certificate) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center z-10">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? '✏️ Chỉnh sửa Audit Certificate' : '✏️ Edit Audit Certificate'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {/* Certificate Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.cert_name}
                onChange={(e) => setFormData({...formData, cert_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            {/* Certificate No */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Số chứng chỉ' : 'Certificate No'} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.cert_no}
                onChange={(e) => setFormData({...formData, cert_no: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            {/* Cert Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Loại' : 'Type'}
              </label>
              <select
                value={formData.cert_type}
                onChange={(e) => setFormData({...formData, cert_type: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="Full Term">Full Term</option>
                <option value="Interim">Interim</option>
                <option value="Provisional">Provisional</option>
                <option value="Short term">Short term</option>
              </select>
            </div>

            {/* Issue Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ngày cấp' : 'Issue Date'}
              </label>
              <input
                type="date"
                value={formData.issue_date}
                onChange={(e) => setFormData({...formData, issue_date: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Valid Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}
              </label>
              <input
                type="date"
                value={formData.valid_date}
                onChange={(e) => setFormData({...formData, valid_date: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Next Survey */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Next Survey' : 'Next Survey'}
              </label>
              <input
                type="date"
                value={formData.next_survey}
                onChange={(e) => setFormData({...formData, next_survey: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Issued By */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Cơ quan cấp' : 'Issued By'}
              </label>
              <input
                type="text"
                value={formData.issued_by}
                onChange={(e) => setFormData({...formData, issued_by: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Ghi chú' : 'Notes'}
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-medium"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg font-medium"
            >
              {isSubmitting ? (
                language === 'vi' ? 'Đang cập nhật...' : 'Updating...'
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
