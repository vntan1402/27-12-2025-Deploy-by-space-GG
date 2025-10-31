/**
 * Edit Test Report Modal
 * Features:
 * - Pre-filled form with existing data
 * - Edit all fields
 * - Show current file links
 * - Update report
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { testReportService } from '../../services';
import { toast } from 'sonner';
import { formatDateForInput } from '../../utils/dateHelpers';

export const EditTestReportModal = ({ isOpen, onClose, report, selectedShip, onReportUpdated }) => {
  const { language } = useAuth();
  const [isSaving, setIsSaving] = useState(false);

  const [formData, setFormData] = useState({
    test_report_name: '',
    report_form: '',
    test_report_no: '',
    issued_by: '',
    issued_date: '',
    valid_date: '',
    note: ''
  });

  // Load report data when modal opens
  useEffect(() => {
    if (report) {
      setFormData({
        test_report_name: report.test_report_name || '',
        report_form: report.report_form || '',
        test_report_no: report.test_report_no || '',
        issued_by: report.issued_by || '',
        issued_date: report.issued_date ? formatDateForInput(report.issued_date) : '',
        valid_date: report.valid_date ? formatDateForInput(report.valid_date) : '',
        note: report.note || ''
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

  // ========== UPDATE TEST REPORT ==========
  const handleSave = async () => {
    // Validation
    if (!formData.test_report_name || !formData.test_report_name.trim()) {
      toast.error(language === 'vi' ? 'Vui lòng nhập tên báo cáo test' : 'Please enter test report name');
      return;
    }

    if (!formData.test_report_no || !formData.test_report_no.trim()) {
      toast.error(language === 'vi' ? 'Vui lòng nhập số báo cáo' : 'Please enter test report number');
      return;
    }

    if (!formData.issued_date) {
      toast.error(language === 'vi' ? 'Vui lòng nhập ngày cấp' : 'Please enter issued date');
      return;
    }

    try {
      setIsSaving(true);

      // Update test report
      const updateData = {
        test_report_name: formData.test_report_name.trim(),
        report_form: formData.report_form?.trim() || null,
        test_report_no: formData.test_report_no.trim(),
        issued_by: formData.issued_by?.trim() || null,
        issued_date: formData.issued_date,
        valid_date: formData.valid_date || null,
        note: formData.note?.trim() || null
      };

      await testReportService.update(report.id, updateData);

      toast.success(
        language === 'vi' 
          ? '✅ Đã cập nhật báo cáo test' 
          : '✅ Test report updated'
      );

      // Close modal and refresh list
      onReportUpdated();
      onClose();

    } catch (error) {
      console.error('Failed to update test report:', error);
      toast.error(
        language === 'vi' 
          ? '❌ Không thể cập nhật báo cáo test' 
          : '❌ Failed to update test report'
      );
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen || !report) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? '✏️ Chỉnh sửa Báo cáo Test' : '✏️ Edit Test Report'}
          </h3>
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

        {/* File Links Section */}
        {(report.test_report_file_id || report.test_report_summary_file_id) && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center mb-2">
              <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <h4 className="text-sm font-semibold text-gray-800">
                {language === 'vi' ? 'Files đã tải lên' : 'Uploaded Files'}
              </h4>
            </div>
            <div className="space-y-1">
              {report.test_report_file_id && (
                <div className="flex items-center text-sm">
                  <span className="text-green-600 mr-2">📄</span>
                  <a
                    href={`https://drive.google.com/file/d/${report.test_report_file_id}/view`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {language === 'vi' ? 'File gốc' : 'Original file'}
                  </a>
                </div>
              )}
              {report.test_report_summary_file_id && (
                <div className="flex items-center text-sm">
                  <span className="text-blue-600 mr-2">📋</span>
                  <a
                    href={`https://drive.google.com/file/d/${report.test_report_summary_file_id}/view`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {language === 'vi' ? 'File tóm tắt' : 'Summary file'}
                  </a>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Form Fields */}
        <div className="space-y-3">
          {/* Row 1: Test Report Name + Report Form */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên Báo cáo Test' : 'Test Report Name'} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="test_report_name"
                value={formData.test_report_name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                placeholder={language === 'vi' ? 'VD: Fire Extinguisher Test' : 'e.g. Fire Extinguisher Test'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Mẫu Báo cáo' : 'Report Form'}
              </label>
              <input
                type="text"
                name="report_form"
                value={formData.report_form}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                placeholder={language === 'vi' ? 'VD: SOLAS Form A' : 'e.g. SOLAS Form A'}
              />
            </div>
          </div>

          {/* Row 2: Test Report No. + Issued By */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Số Báo cáo' : 'Test Report No.'} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="test_report_no"
                value={formData.test_report_no}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                placeholder={language === 'vi' ? 'VD: FE-2025-001' : 'e.g. FE-2025-001'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Cấp bởi' : 'Issued By'}
              </label>
              <input
                type="text"
                name="issued_by"
                value={formData.issued_by}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                placeholder={language === 'vi' ? 'VD: ABS' : 'e.g. ABS'}
              />
            </div>
          </div>

          {/* Row 3: Issued Date + Valid Date */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ngày cấp' : 'Issued Date'} <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                name="issued_date"
                value={formData.issued_date}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}
              </label>
              <input
                type="date"
                name="valid_date"
                value={formData.valid_date}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              />
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

        {/* Footer Buttons */}
        <div className="flex justify-end gap-3 mt-6">
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
