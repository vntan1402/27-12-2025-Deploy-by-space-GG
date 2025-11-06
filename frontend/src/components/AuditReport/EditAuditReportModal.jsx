/**
 * Edit Audit Report Modal
 * Modal for editing existing audit reports
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { auditReportService } from '../../services';
import { toast } from 'sonner';

export const EditAuditReportModal = ({ isOpen, onClose, report, onReportUpdated }) => {
  const { language } = useAuth();
  const [isSaving, setIsSaving] = useState(false);

  const [formData, setFormData] = useState({
    audit_report_name: '',
    audit_type: '',
    report_form: '',
    audit_report_no: '',
    audit_date: '',
    issued_by: '',
    status: 'Valid',
    note: '',
    auditor_name: ''
  });

  // Initialize form data when report changes
  useEffect(() => {
    if (report) {
      setFormData({
        audit_report_name: report.audit_report_name || '',
        audit_type: report.audit_type || '',
        audit_report_no: report.audit_report_no || '',
        audit_date: report.audit_date ? report.audit_date.split('T')[0] : '',
        issued_by: report.issued_by || '',
        status: report.status || 'Valid',
        note: report.note || '',
        auditor_name: report.auditor_name || ''
      });
    }
  }, [report]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation
    if (!formData.audit_report_name.trim()) {
      toast.error(language === 'vi' ? 'Vui lòng nhập tên báo cáo audit' : 'Please enter report name');
      return;
    }

    if (!report || !report.id) {
      toast.error(language === 'vi' ? 'Không tìm thấy báo cáo audit' : 'Report not found');
      return;
    }

    try {
      setIsSaving(true);

      // Prepare data for backend
      const updateData = {
        audit_report_name: formData.audit_report_name.trim(),
        audit_type: formData.audit_type.trim() || null,
        audit_report_no: formData.audit_report_no.trim() || null,
        audit_date: formData.audit_date || null,
        issued_by: formData.issued_by.trim() || null,
        status: formData.status || 'Valid',
        note: formData.note.trim() || null,
        auditor_name: formData.auditor_name.trim() || null
      };

      // Update audit report
      await auditReportService.update(report.id, updateData);

      toast.success(language === 'vi' ? '✅ Đã cập nhật báo cáo audit' : '✅ Report updated successfully');

      // Callback to refresh list
      if (onReportUpdated) {
        onReportUpdated();
      }
    } catch (error) {
      console.error('Failed to update audit report:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      toast.error(
        language === 'vi' 
          ? `Không thể cập nhật báo cáo audit: ${errorMsg}` 
          : `Failed to update report: ${errorMsg}`
      );
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-orange-500 to-orange-600">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-white">
              {language === 'vi' ? 'Chỉnh sửa Audit Report' : 'Edit Audit Report'}
            </h2>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Form Body */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Row 1: Audit Report Name + Audit Type */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Audit Report Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tên Báo cáo Audit' : 'Audit Report Name'} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="audit_report_name"
                  value={formData.audit_report_name}
                  onChange={handleChange}
                  required
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'Nhập tên báo cáo audit...' : 'Enter report name...'}
                />
              </div>

              {/* Audit Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Loại Audit' : 'Audit Type'}
                </label>
                <input
                  type="text"
                  name="audit_type"
                  value={formData.audit_type}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'VD: FL-01, FL-02...' : 'e.g., FL-01, FL-02...'}
                />
              </div>
            </div>

            {/* Row 2: Audit Report No + Audit Date */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Audit Report No */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Số Báo cáo Audit' : 'Audit Report No.'}
                </label>
                <input
                  type="text"
                  name="audit_report_no"
                  value={formData.audit_report_no}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent font-mono"
                  placeholder={language === 'vi' ? 'Nhập số báo cáo audit...' : 'Enter report number...'}
                />
              </div>

              {/* Audit Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày Audit' : 'Audit Date'}
                </label>
                <input
                  type="date"
                  name="audit_date"
                  value={formData.audit_date}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Row 3: Issued By + Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Issued By */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Cấp bởi' : 'Issued By'}
                </label>
                <input
                  type="text"
                  name="issued_by"
                  value={formData.issued_by}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'VD: Lloyd\'s Register, Bureau Veritas...' : 'e.g., Lloyd\'s Register, Bureau Veritas...'}
                />
              </div>

              {/* Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tình trạng' : 'Status'}
                </label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                >
                  <option value="Valid">Valid</option>
                  <option value="Expired">Expired</option>
                  <option value="Pending">Pending</option>
                  <option value="Unknown">Unknown</option>
                </select>
              </div>
            </div>

            {/* Row 4: Auditor Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên Auditor' : 'Auditor Name'}
              </label>
              <input
                type="text"
                name="auditor_name"
                value={formData.auditor_name}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Nhập tên surveyor...' : 'Enter surveyor name...'}
              />
            </div>

            {/* Row 5: Note */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ghi chú' : 'Note'}
              </label>
              <textarea
                name="note"
                value={formData.note}
                onChange={handleChange}
                rows="3"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Nhập ghi chú...' : 'Enter notes...'}
              />
            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-all"
            disabled={isSaving}
          >
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSaving}
            className={`px-6 py-2 rounded-lg transition-all ${
              isSaving
                ? 'bg-gray-400 cursor-not-allowed text-white'
                : 'bg-orange-600 hover:bg-orange-700 text-white'
            }`}
          >
            {isSaving 
              ? (language === 'vi' ? 'Đang lưu...' : 'Saving...') 
              : (language === 'vi' ? 'Cập nhật' : 'Update')
            }
          </button>
        </div>
      </div>
    </div>
  );
};

