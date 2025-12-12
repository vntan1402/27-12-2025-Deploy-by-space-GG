/**
 * Add Company Certificate Modal
 * Layout giống Add Audit Certificate
 */
import React, { useState } from 'react';
import { toast } from 'sonner';
import api from '../../services/api';

export const AddCompanyCertModal = ({
  isOpen,
  onClose,
  onSuccess,
  language
}) => {
  const [formData, setFormData] = useState({
    cert_name: '',
    cert_no: '',
    issue_date: '',
    valid_date: '',
    last_endorse: '',
    next_survey: '',
    next_survey_type: '',
    issued_by: '',
    notes: ''
  });

  const [certificateFile, setCertificateFile] = useState(null);
  const [summaryText, setSummaryText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState(null);

  if (!isOpen) return null;

  const handleFileChange = (files) => {
    const file = files[0];
    if (!file) return;
    
    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      toast.error(language === 'vi' ? 'Kích thước file vượt quá 50MB!' : 'File size exceeds 50MB!');
      return;
    }
    
    // Validate file type
    const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    if (!validTypes.includes(file.type)) {
      toast.error(language === 'vi' ? 'Chỉ chấp nhận file PDF, JPG, PNG!' : 'Only PDF, JPG, PNG files accepted!');
      return;
    }
    
    setCertificateFile(file);
    setAnalyzed(false);
    
    // Auto analyze
    handleAnalyze(file);
  };

  const handleAnalyze = async (file) => {
    const fileToAnalyze = file || certificateFile;
    if (!fileToAnalyze) {
      toast.error(language === 'vi' ? 'Vui lòng chọn file!' : 'Please select a file!');
      return;
    }

    setIsAnalyzing(true);
    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64Content = e.target.result.split(',')[1];
        
        const response = await api.post('/api/company-certs/analyze-file', {
          file_content: base64Content,
          filename: fileToAnalyze.name,
          content_type: fileToAnalyze.type
        });

        if (response.data.success) {
          const info = response.data.extracted_info;
          
          // Helper function to convert DD/MM/YYYY to YYYY-MM-DD
          const convertDateFormat = (dateStr) => {
            if (!dateStr) return '';
            // If already in YYYY-MM-DD format, return as is
            if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) return dateStr;
            // Convert DD/MM/YYYY to YYYY-MM-DD
            const parts = dateStr.split('/');
            if (parts.length === 3) {
              const [day, month, year] = parts;
              return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
            }
            return dateStr;
          };
          
          // Auto-fill form with date conversion
          setFormData(prev => ({
            ...prev,
            cert_name: info.cert_name || prev.cert_name,
            cert_no: info.cert_no || prev.cert_no,
            issue_date: convertDateFormat(info.issue_date) || prev.issue_date,
            valid_date: convertDateFormat(info.valid_date) || prev.valid_date,
            last_endorse: convertDateFormat(info.last_endorse) || prev.last_endorse,
            next_survey: convertDateFormat(info.next_survey) || prev.next_survey,
            issued_by: info.issued_by || prev.issued_by
          }));
          
          // Store summary text
          setSummaryText(response.data.summary_text || '');
          
          // Check for duplicate warning
          if (response.data.duplicate_warning) {
            setDuplicateWarning(response.data.duplicate_warning);
          }
          
          setAnalyzed(true);
          toast.success(language === 'vi' ? '✅ Phân tích thành công!' : '✅ Analysis successful!');
        }
      };
      reader.readAsDataURL(fileToAnalyze);
    } catch (error) {
      console.error('Analysis error:', error);
      toast.error(language === 'vi' 
        ? 'Phân tích thất bại. Vui lòng nhập thủ công.'
        : 'Analysis failed. Please enter manually.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.cert_name) {
      toast.error(language === 'vi' ? 'Vui lòng nhập tên chứng chỉ!' : 'Please enter certificate name!');
      return;
    }

    if (!certificateFile) {
      toast.error(language === 'vi' ? 'Vui lòng chọn file!' : 'Please select a file!');
      return;
    }

    // Show duplicate warning if exists
    if (duplicateWarning) {
      const confirmed = window.confirm(
        language === 'vi'
          ? `⚠️ Cảnh báo trùng lặp!\n\nChứng chỉ số "${formData.cert_no}" đã tồn tại.\n\nBạn có chắc muốn tiếp tục?`
          : `⚠️ Duplicate Warning!\n\nCertificate "${formData.cert_no}" already exists.\n\nDo you want to continue?`
      );
      if (!confirmed) return;
    }

    setIsSubmitting(true);
    try {
      // Prepare FormData
      const uploadData = new FormData();
      uploadData.append('file', certificateFile);
      
      // Add cert_data as JSON string
      const certData = {
        ...formData,
        summary_text: summaryText
      };
      uploadData.append('cert_data', JSON.stringify(certData));

      // Upload
      await api.post('/api/company-certs/upload-with-file', uploadData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      toast.success(language === 'vi' 
        ? 'Thêm chứng chỉ thành công!'
        : 'Certificate added successfully!');
      onSuccess();
      handleClose();
    } catch (error) {
      console.error('Submit error:', error);
      toast.error(error.response?.data?.detail || 'Failed to add certificate');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setFormData({
      cert_name: '',
      cert_no: '',
      issue_date: '',
      valid_date: '',
      last_endorse: '',
      next_survey: '',
      next_survey_type: '',
      issued_by: '',
      notes: ''
    });
    setCertificateFile(null);
    setSummaryText('');
    setAnalyzed(false);
    setDuplicateWarning(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center z-10">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? '📋 Thêm Company Certificate' : '📋 Add Company Certificate'}
          </h2>
          <button 
            onClick={handleClose} 
            className="text-gray-400 hover:text-gray-600"
            disabled={isSubmitting}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* File Upload Section with Guidelines */}
          <div className="border-2 border-dashed border-blue-300 rounded-lg p-6 bg-blue-50">
            <div className="flex items-start justify-between mb-3">
              {/* Title */}
              <div className="flex-1 pr-4">
                <h3 className="text-lg font-semibold text-blue-900 mb-2">
                  📋 {language === 'vi' ? 'Upload Certificate' : 'Upload Certificate'}
                </h3>
              </div>

              {/* Upload Guidelines */}
              <div className="w-72 mx-4 bg-blue-100 rounded-lg p-3">
                <h4 className="text-sm font-medium text-blue-800 mb-2 flex items-center">
                  📝 {language === 'vi' ? 'Hướng dẫn Upload:' : 'Upload Guidelines:'}
                </h4>
                <ul className="text-xs text-blue-700 space-y-1">
                  <li>• {language === 'vi' ? 'PDF, JPG, PNG' : 'PDF, JPG, PNG files'}</li>
                  <li>• {language === 'vi' ? 'Max 50MB/file' : 'Max 50MB per file'}</li>
                  <li>• {language === 'vi' ? 'AI tự động phân tích' : 'AI auto-analysis'}</li>
                  <li>• {language === 'vi' ? 'Tự động điền thông tin' : 'Auto-fill info'}</li>
                </ul>
              </div>

              {/* Upload Button */}
              <div className="flex-shrink-0">
                <label
                  htmlFor="cert-upload"
                  className="inline-flex items-center px-4 py-3 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 shadow-md cursor-pointer transition-colors"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {language === 'vi' ? '📋 Upload Cert' : '📋 Upload Cert'}
                  <input
                    id="cert-upload"
                    type="file"
                    className="sr-only"
                    onChange={(e) => handleFileChange(e.target.files)}
                    accept=".pdf,.jpg,.jpeg,.png"
                    disabled={isSubmitting}
                  />
                </label>
              </div>
            </div>

            {/* Analyzing Indicator */}
            {isAnalyzing && (
              <div className="mt-4 p-3 bg-white rounded-lg border border-blue-200">
                <div className="flex items-center gap-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                  <span className="text-sm text-blue-700 font-medium">
                    {language === 'vi' ? '🤖 Đang phân tích với AI...' : '🤖 Analyzing with AI...'}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Manual Form */}
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-md font-semibold text-gray-700">
                ✍️ {language === 'vi' ? 'Hoặc nhập thủ công:' : 'Or Enter Manually:'}
              </h3>
              
              {/* File attached indicator */}
              {certificateFile && (
                <div className="flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8 4a3 3 0 00-3 3v4a5 5 0 0010 0V7a1 1 0 112 0v4a7 7 0 11-14 0V7a5 5 0 0110 0v4a3 3 0 11-6 0V7a1 1 0 012 0v4a1 1 0 102 0V7a3 3 0 00-3-3z" clipRule="evenodd" />
                  </svg>
                  <span className="font-medium">{certificateFile.name}</span>
                  <button
                    type="button"
                    onClick={() => {
                      setCertificateFile(null);
                      toast.info(language === 'vi' ? 'Đã xóa file đính kèm' : 'Removed attached file');
                    }}
                    className="ml-1 hover:text-blue-900"
                  >
                    ✕
                  </button>
                </div>
              )}
            </div>

            {/* Duplicate Warning */}
            {duplicateWarning && (
              <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <span className="text-yellow-600 text-xl">⚠️</span>
                  <div>
                    <p className="font-medium text-yellow-800">
                      {language === 'vi' ? 'Cảnh báo trùng lặp' : 'Duplicate Warning'}
                    </p>
                    <p className="text-sm text-yellow-700 mt-1">
                      {duplicateWarning.message}
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Row 1: Certificate Name & Number */}
            <div className="grid grid-cols-2 gap-4">
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
            </div>

            {/* Row 2: Issue Date & Valid Date */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày cấp' : 'Issue Date'}
                </label>
                <input
                  type="date"
                  value={formData.issue_date}
                  onChange={(e) => setFormData({...formData, issue_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  disabled={isSubmitting}
                />
              </div>
            </div>

            {/* Row 3: Last Endorse, Next Survey & Next Survey Type */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Xác nhận cuối' : 'Last Endorse'}
                </label>
                <input
                  type="date"
                  value={formData.last_endorse}
                  onChange={(e) => setFormData({...formData, last_endorse: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  disabled={isSubmitting}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Loại kiểm tra tới' : 'Next Survey Type'}
                </label>
                <select
                  value={formData.next_survey_type}
                  onChange={(e) => setFormData({...formData, next_survey_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  disabled={isSubmitting}
                >
                  <option value="">{language === 'vi' ? '-- Chọn loại --' : '-- Select Type --'}</option>
                  <option value="Initial">Initial</option>
                  <option value="Intermediate">Intermediate</option>
                  <option value="Renewal">Renewal</option>
                </select>
              </div>
            </div>

            {/* Row 4: Issued By (full width) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Cấp bởi' : 'Issued By'}
              </label>
              <input
                type="text"
                value={formData.issued_by}
                onChange={(e) => setFormData({...formData, issued_by: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                placeholder={language === 'vi' ? 'Tên tổ chức cấp' : 'Issuing organization'}
                disabled={isSubmitting}
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
              disabled={isSubmitting}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-medium"
              disabled={isSubmitting}
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !certificateFile}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white rounded-lg font-medium"
            >
              {isSubmitting 
                ? (language === 'vi' ? 'Đang lưu...' : 'Saving...') 
                : (language === 'vi' ? 'Lưu' : 'Save')
              }
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddCompanyCertModal;
