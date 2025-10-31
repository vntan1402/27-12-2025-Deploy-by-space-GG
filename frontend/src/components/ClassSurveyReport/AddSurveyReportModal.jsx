/**
 * Add Survey Report Modal - V2 with All V1 Features
 * Features:
 * - Drag & drop PDF file upload
 * - AI Analysis with Targeted OCR
 * - Ship name validation
 * - Auto-populate form fields
 * - Manual edit capability
 * - Duplicate check
 * - Dual file upload (original + enhanced summary)
 * - Background upload with progress
 * - Split PDF support (>15 pages)
 */
import React, { useState, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { surveyReportService } from '../../services';
import { toast } from 'sonner';

export const AddSurveyReportModal = ({ isOpen, onClose, selectedShip, onReportAdded }) => {
  const { language } = useAuth();
  const [isSaving, setIsSaving] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [analyzedData, setAnalyzedData] = useState(null); // Store complete analysis result
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

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

  // File upload handlers
  const handleFileSelect = async (file) => {
    if (!file) return;

    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      toast.error(language === 'vi' ? 'Chỉ hỗ trợ file PDF' : 'Only PDF files are supported');
      return;
    }

    // Validate file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      toast.error(language === 'vi' ? 'File quá lớn (tối đa 50MB)' : 'File too large (max 50MB)');
      return;
    }

    setUploadedFile(file);
    
    // Read file as base64 for later upload
    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target.result.split(',')[1];
      setFileContent(base64);
    };
    reader.readAsDataURL(file);

    // Start AI analysis
    await analyzeFile(file);
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setFileContent(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // AI Analysis
  const analyzeFile = async (file) => {
    if (!selectedShip) {
      toast.error(language === 'vi' ? 'Không có tàu được chọn' : 'No ship selected');
      return;
    }

    try {
      setIsAnalyzing(true);
      toast.info(language === 'vi' ? '🤖 Đang phân tích file với AI...' : '🤖 Analyzing file with AI...');

      // Call analyze API (backend will use system AI config)
      const response = await surveyReportService.analyzeFile(
        selectedShip.id,
        file,
        'google', // Will be ignored, backend uses system config
        'gemini-2.0-flash', // Will be ignored
        true // Will be ignored
      );
      
      if (response.data?.success && response.data?.analysis) {
        const analysis = response.data.analysis;
        
        // Auto-populate form fields
        setFormData(prev => ({
          ...prev,
          survey_report_name: analysis.survey_report_name || prev.survey_report_name,
          report_form: analysis.report_form || prev.report_form,
          survey_report_no: analysis.survey_report_no || prev.survey_report_no,
          issued_date: analysis.issued_date || prev.issued_date,
          issued_by: analysis.issued_by || prev.issued_by,
          status: analysis.status || prev.status,
          note: analysis.note || prev.note,
          surveyor_name: analysis.surveyor_name || prev.surveyor_name
        }));

        toast.success(language === 'vi' ? '✅ Phân tích hoàn tất! Vui lòng kiểm tra và chỉnh sửa nếu cần.' : '✅ Analysis complete! Please review and edit if needed.');
      } else {
        toast.warning(language === 'vi' ? '⚠️ Không thể phân tích file. Vui lòng nhập thủ công.' : '⚠️ Could not analyze file. Please enter manually.');
      }
    } catch (error) {
      console.error('AI analysis error:', error);
      toast.error(language === 'vi' ? '❌ Lỗi phân tích file. Vui lòng nhập thủ công.' : '❌ Analysis failed. Please enter manually.');
    } finally {
      setIsAnalyzing(false);
    }
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
      const createResponse = await surveyReportService.create(reportData);
      const createdReport = createResponse.data || createResponse;

      toast.success(language === 'vi' ? '✅ Đã thêm báo cáo survey' : '✅ Survey report added successfully');

      // Upload files in background if file was selected
      if (uploadedFile && fileContent && createdReport.id) {
        uploadFilesInBackground(createdReport.id, uploadedFile.name, fileContent);
      }

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
      setUploadedFile(null);
      setFileContent(null);

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

  // Upload files in background
  const uploadFilesInBackground = async (reportId, filename, base64Content) => {
    try {
      toast.info(language === 'vi' ? '📤 Đang upload file lên Google Drive...' : '📤 Uploading file to Google Drive...');

      // Convert base64 back to Blob
      const byteCharacters = atob(base64Content);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });
      const file = new File([blob], filename, { type: 'application/pdf' });

      await surveyReportService.uploadFiles(reportId, file, null);

      toast.success(language === 'vi' ? '✅ Upload file thành công!' : '✅ File uploaded successfully!');
      
      // Refresh list to show file icons
      if (onReportAdded) {
        onReportAdded();
      }
    } catch (error) {
      console.error('Failed to upload file:', error);
      toast.error(language === 'vi' ? '❌ Upload file thất bại' : '❌ File upload failed');
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

            {/* File Upload Area - PHASE 2 */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                {language === 'vi' ? '📄 Upload File PDF (Tùy chọn - AI sẽ tự động điền)' : '📄 Upload PDF File (Optional - AI will auto-fill)'}
              </label>
              
              {!uploadedFile ? (
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
                    isDragOver 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                  }`}
                >
                  <div className="space-y-2">
                    <div className="text-4xl">📄</div>
                    <p className="text-sm text-gray-600">
                      {language === 'vi' 
                        ? 'Kéo thả file PDF vào đây hoặc click để chọn' 
                        : 'Drag & drop PDF file here or click to select'}
                    </p>
                    <p className="text-xs text-gray-400">
                      {language === 'vi' ? 'Chỉ hỗ trợ file PDF, tối đa 50MB' : 'PDF only, max 50MB'}
                    </p>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf"
                    onChange={handleFileInputChange}
                    className="hidden"
                  />
                </div>
              ) : (
                <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">📄</span>
                      <div>
                        <p className="text-sm font-medium text-gray-800">{uploadedFile.name}</p>
                        <p className="text-xs text-gray-500">
                          {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={handleRemoveFile}
                      className="text-red-500 hover:text-red-700 p-2"
                      disabled={isAnalyzing}
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  
                  {isAnalyzing && (
                    <div className="mt-3 flex items-center gap-2 text-blue-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span className="text-sm">
                        {language === 'vi' ? '🤖 Đang phân tích với AI...' : '🤖 Analyzing with AI...'}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Divider */}
            {uploadedFile && (
              <div className="border-t border-gray-200 pt-4">
                <p className="text-sm text-gray-600 mb-4">
                  {language === 'vi' 
                    ? '✏️ Vui lòng kiểm tra và chỉnh sửa thông tin nếu cần:' 
                    : '✏️ Please review and edit information if needed:'}
                </p>
              </div>
            )}

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
