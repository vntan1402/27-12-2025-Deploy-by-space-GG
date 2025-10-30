/**
 * Add Survey Report Modal
 * Manual input modal for creating new survey reports
 * Phase 1: Manual input only (no AI analysis)
 */
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { surveyReportService } from '../../services';
import { toast } from 'sonner';

export const AddSurveyReportModal = ({ isOpen, onClose, selectedShip, onReportAdded }) => {
  const { language } = useAuth();
  const [isSaving, setIsSaving] = useState(false);

  const [formData, setFormData] = useState({
    survey_report_name: '',
    report_form: '',
    survey_report_no: '',
    issued_date: '',
    issued_by: '',
    status: 'Valid',
    note: '',
    surveyor_name: ''
  });

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
    if (!formData.survey_report_name.trim()) {
      toast.error(language === 'vi' ? 'Vui lòng nhập tên báo cáo' : 'Please enter report name');
      return;
    }

    if (!selectedShip) {
      toast.error(language === 'vi' ? 'Không có tàu được chọn' : 'No ship selected');
      return;
    }

    try {
      setIsSaving(true);

      // Prepare data for backend
      const reportData = {
        ship_id: selectedShip.id,
        survey_report_name: formData.survey_report_name.trim(),
        report_form: formData.report_form.trim() || null,
        survey_report_no: formData.survey_report_no.trim() || null,
        issued_date: formData.issued_date || null,
        issued_by: formData.issued_by.trim() || null,
        status: formData.status || 'Valid',
        note: formData.note.trim() || null,
        surveyor_name: formData.surveyor_name.trim() || null
      };

      // Create survey report
      await surveyReportService.create(reportData);

      toast.success(language === 'vi' ? '✅ Đã thêm báo cáo survey' : '✅ Survey report added successfully');

      // Reset form
      setFormData({
        survey_report_name: '',
        report_form: '',
        survey_report_no: '',
        issued_date: '',
        issued_by: '',
        status: 'Valid',
        note: '',
        surveyor_name: ''
      });

      // Callback to refresh list
      if (onReportAdded) {
        onReportAdded();
      }
    } catch (error) {
      console.error('Failed to create survey report:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      toast.error(
        language === 'vi' 
          ? `Không thể thêm báo cáo: ${errorMsg}` 
          : `Failed to add report: ${errorMsg}`
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
        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-500 to-blue-600">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-white">
              {language === 'vi' ? 'Thêm Survey Report' : 'Add Survey Report'}
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
            {/* Ship Info Display */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-800">
                <span className="font-semibold">{language === 'vi' ? 'Tàu:' : 'Ship:'}</span> {selectedShip?.name}
              </p>
            </div>

            {/* Row 1: Survey Report Name + Report Form */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Survey Report Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tên Báo cáo Survey' : 'Survey Report Name'} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="survey_report_name"
                  value={formData.survey_report_name}
                  onChange={handleChange}
                  required
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'Nhập tên báo cáo...' : 'Enter report name...'}
                />
              </div>

              {/* Report Form */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Mẫu Báo cáo' : 'Report Form'}
                </label>
                <input
                  type="text"
                  name="report_form"
                  value={formData.report_form}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'VD: FL-01, FL-02...' : 'e.g., FL-01, FL-02...'}
                />
              </div>
            </div>

            {/* Row 2: Survey Report No + Issued Date */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Survey Report No */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Số Báo cáo Survey' : 'Survey Report No.'}
                </label>
                <input
                  type="text"
                  name="survey_report_no"
                  value={formData.survey_report_no}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                  placeholder={language === 'vi' ? 'Nhập số báo cáo...' : 'Enter report number...'}
                />
              </div>

              {/* Issued Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày cấp' : 'Issued Date'}
                </label>
                <input
                  type="date"
                  name="issued_date"
                  value={formData.issued_date}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="Valid">Valid</option>
                  <option value="Expired">Expired</option>
                  <option value="Pending">Pending</option>
                  <option value="Unknown">Unknown</option>
                </select>
              </div>
            </div>

            {/* Row 4: Surveyor Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên Surveyor' : 'Surveyor Name'}
              </label>
              <input
                type="text"
                name="surveyor_name"
                value={formData.surveyor_name}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
          >
            {isSaving 
              ? (language === 'vi' ? 'Đang lưu...' : 'Saving...') 
              : (language === 'vi' ? 'Thêm' : 'Add')
            }
          </button>
        </div>
      </div>
    </div>
  );
};
