/**
 * Add Audit Report Modal - V2 with All V1 Features
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
import { useUploadGuard } from '../../hooks/useUploadGuard';
import { auditReportService } from '../../services';
import { toast } from 'sonner';

export const AddAuditReportModal = ({ isOpen, onClose, selectedShip, onReportAdded, onStartBatchProcessing }) => {
  const { language } = useAuth();
  const { checkAndWarn } = useUploadGuard();
  const [isSaving, setIsSaving] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [analyzedData, setAnalyzedData] = useState(null); // Store complete analysis result
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);
  
  // Validation modal state
  const [showValidationModal, setShowValidationModal] = useState(false);
  const [validationData, setValidationData] = useState(null);

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

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // File upload handlers
  const handleFileSelect = async (files) => {
    // Convert FileList to Array
    const fileArray = Array.from(files);
    
    if (fileArray.length === 0) return;

    // Validate all files are PDFs
    const nonPdfFiles = fileArray.filter(f => !f.name.toLowerCase().endsWith('.pdf'));
    if (nonPdfFiles.length > 0) {
      toast.error(language === 'vi' ? 'Chỉ hỗ trợ file PDF' : 'Only PDF files are supported');
      return;
    }

    // Validate file sizes (max 50MB each)
    const oversizedFiles = fileArray.filter(f => f.size > 50 * 1024 * 1024);
    if (oversizedFiles.length > 0) {
      toast.error(language === 'vi' ? 'Có file quá lớn (tối đa 50MB/file)' : 'Some files are too large (max 50MB/file)');
      return;
    }

    // Detect mode: Single vs Batch
    if (fileArray.length === 1) {
      // Single file mode - existing flow
      const file = fileArray[0];
      setUploadedFile(file);
      await analyzeFile(file);
    } else {
      // Batch mode - pass to parent
      if (onStartBatchProcessing) {
        toast.info(
          language === 'vi' 
            ? `🔄 Bắt đầu xử lý ${fileArray.length} files...` 
            : `🔄 Starting batch processing of ${fileArray.length} files...`
        );
        onStartBatchProcessing(fileArray);
      } else {
        toast.error(language === 'vi' ? 'Batch processing không khả dụng' : 'Batch processing not available');
      }
    }
  };

  const handleFileInputChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files);
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
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileSelect(files);
    }
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setAnalyzedData(null);
    setFormData({
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
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // AI Analysis with Ship Validation
  const analyzeFile = async (file) => {
    // CRITICAL: Check software expiry before AI analysis
    if (!checkAndWarn()) {
      console.log('🚫 [AddAuditReport] Software expired - AI analysis blocked');
      setUploadedFile(null);
      setIsAnalyzing(false);
      return;
    }
    
    if (!selectedShip) {
      toast.error(language === 'vi' ? 'Không có tàu được chọn' : 'No ship selected');
      return;
    }

    try {
      setIsAnalyzing(true);
      toast.info(language === 'vi' ? '🤖 Đang phân tích file với AI...' : '🤖 Analyzing file with AI...');

      // Call backend analyze endpoint (bypass_validation = false initially)
      const response = await auditReportService.analyzeFile(
        selectedShip.id,
        file,
        false // Don't bypass validation initially
      );
      
      const data = response.data || response;
      
      // Check for validation error (ship mismatch)
      if (data.validation_error) {
        // Show custom validation modal instead of window.confirm
        setValidationData({
          extracted_ship_name: data.extracted_ship_name,
          extracted_ship_imo: data.extracted_ship_imo,
          expected_ship_name: data.expected_ship_name,
          expected_ship_imo: data.expected_ship_imo,
          file: file
        });
        setShowValidationModal(true);
        setIsAnalyzing(false);
        return;
      } else if (data.success && data.analysis) {
        processAnalysisSuccess(data.analysis, file);
      } else {
        processAnalysisFail();
      }
      
    } catch (error) {
      console.error('AI analysis error:', error);
      toast.error(language === 'vi' ? '❌ Lỗi phân tích file. Vui lòng nhập thủ công.' : '❌ Analysis failed. Please enter manually.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Process successful analysis
  const processAnalysisSuccess = (analysis, file) => {
    console.log('🔍 Analysis data received:', analysis);
    
    // Store complete analysis data (including _file_content, _summary_text)
    setAnalyzedData(analysis);
    
    // Auto-populate form fields
    const newFormData = {
      ...formData,
      audit_report_name: analysis.audit_report_name || formData.audit_report_name,
      audit_type: analysis.audit_type || formData.audit_type,
      report_form: analysis.report_form || formData.report_form,
      audit_report_no: analysis.audit_report_no || formData.audit_report_no,
      audit_date: analysis.audit_date ? analysis.audit_date.split('T')[0] : formData.audit_date,
      issued_by: analysis.issued_by || formData.issued_by,
      status: analysis.status || formData.status,
      note: analysis.note || formData.note,
      auditor_name: analysis.auditor_name || formData.auditor_name
    };
    
    console.log('📝 Setting form data:', newFormData);
    setFormData(newFormData);

    // Show split info if file was split
    if (analysis._split_info?.was_split) {
      toast.info(
        language === 'vi' 
          ? `📄 File có ${analysis._split_info.total_pages} trang, đã chia thành ${analysis._split_info.chunks_count} phần để xử lý.`
          : `📄 File has ${analysis._split_info.total_pages} pages, split into ${analysis._split_info.chunks_count} chunks.`
      );
    }

    // Show OCR info if OCR was used
    if (analysis._ocr_info?.ocr_success) {
      toast.success(
        language === 'vi'
          ? '✅ OCR enhancement applied - Audit Type và Report No được trích xuất chính xác hơn'
          : '✅ OCR enhancement applied - Audit Type and Report No extracted with higher accuracy'
      );
    }

    // Warn about manual review if needed
    if (analysis._ocr_info?.needs_manual_review) {
      toast.warning(
        language === 'vi'
          ? '⚠️ Vui lòng kiểm tra Audit Type và Report No'
          : '⚠️ Please verify Audit Type and Report No'
      );
    }

    toast.success(language === 'vi' ? '✅ Phân tích hoàn tất! Vui lòng kiểm tra và chỉnh sửa nếu cần.' : '✅ Analysis complete! Please review and edit if needed.');
  };

  // Process failed analysis
  const processAnalysisFail = () => {
    toast.warning(language === 'vi' ? '⚠️ Không thể phân tích file. Vui lòng nhập thủ công.' : '⚠️ Could not analyze file. Please enter manually.');
  };

  // Handle validation modal confirmation
  const handleValidationConfirm = async () => {
    setShowValidationModal(false);
    setIsAnalyzing(true);
    
    try {
      toast.info(language === 'vi' ? '🔄 Phân tích lại với xác nhận...' : '🔄 Re-analyzing with confirmation...');
      const retryResponse = await auditReportService.analyzeFile(
        selectedShip.id,
        validationData.file,
        true // Bypass validation
      );
      
      const retryData = retryResponse.data || retryResponse;
      if (retryData.success && retryData.analysis) {
        processAnalysisSuccess(retryData.analysis, validationData.file);
      } else {
        processAnalysisFail();
      }
    } catch (error) {
      console.error('Retry analysis error:', error);
      processAnalysisFail();
    } finally {
      setIsAnalyzing(false);
      setValidationData(null);
    }
  };

  // Handle validation modal cancellation
  const handleValidationCancel = () => {
    setShowValidationModal(false);
    setValidationData(null);
    handleRemoveFile();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation
    if (!formData.audit_report_name.trim()) {
      toast.error(language === 'vi' ? 'Vui lòng nhập tên báo cáo audit' : 'Please enter report name');
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
        audit_report_name: formData.audit_report_name.trim(),
        audit_type: formData.audit_type.trim() || null,
        report_form: formData.report_form.trim() || null,
        audit_report_no: formData.audit_report_no.trim() || null,
        audit_date: formData.audit_date || null,
        issued_by: formData.issued_by.trim() || null,
        status: formData.status || 'Valid',
        note: formData.note.trim() || null,
        auditor_name: formData.auditor_name.trim() || null
      };

      // Create audit report
      const createResponse = await auditReportService.create(reportData);
      const createdReport = createResponse.data || createResponse;

      toast.success(language === 'vi' ? '✅ Đã thêm audit report' : '✅ Survey report added successfully');

      // Reset form immediately
      setFormData({
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

      // Close modal
      onClose();

      // Refresh list (first time - without file icons)
      if (onReportAdded) {
        onReportAdded();
      }

      // Upload files in background if file was uploaded and analyzed
      if (uploadedFile && analyzedData && createdReport.id) {
        uploadFilesInBackground(
          createdReport.id,
          analyzedData._file_content,
          analyzedData._filename,
          analyzedData._content_type,
          analyzedData._summary_text
        );
      }

      // Reset upload state
      setUploadedFile(null);
      setAnalyzedData(null);
      
    } catch (error) {
      console.error('Failed to create audit report:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      toast.error(
        language === 'vi' 
          ? `Không thể thêm báo cáo audit: ${errorMsg}` 
          : `Failed to add report: ${errorMsg}`
      );
    } finally {
      setIsSaving(false);
    }
  };

  // Upload files in background (V1 approach)
  const uploadFilesInBackground = async (reportId, fileContent, filename, contentType, summaryText) => {
    // Small delay to ensure modal closes first
    setTimeout(async () => {
      try {
        toast.info(language === 'vi' ? '📤 Đang upload file lên Google Drive...' : '📤 Uploading files to Google Drive...');

        await auditReportService.uploadFiles(
          reportId,
          fileContent, // Base64 string
          filename,
          contentType,
          summaryText // Enhanced summary with OCR
        );

        toast.success(language === 'vi' ? '✅ Upload file hoàn tất!' : '✅ File upload complete!');
        
        // Refresh list again to show file icons
        if (onReportAdded) {
          onReportAdded();
        }
      } catch (error) {
        console.error('Failed to upload file:', error);
        toast.error(language === 'vi' ? '❌ Upload file thất bại' : '❌ File upload failed');
      }
    }, 100);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-500 to-blue-600">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-white">
              {language === 'vi' ? 'Thêm Audit Report' : 'Add Audit Report'}
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
                        : 'Drag & drop PDF files here or click to select'}
                    </p>
                    <p className="text-xs text-gray-400">
                      {language === 'vi' ? 'PDF only, max 50MB/file. Chọn nhiều files để xử lý hàng loạt.' : 'PDF only, max 50MB/file. Select multiple files for batch processing.'}
                    </p>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf"
                    multiple
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
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'Nhập tên báo cáo audit...' : 'Enter report name...'}
                />
              </div>

              {/* Audit Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Loại Audit' : 'Audit Type'}
                </label>
                <select
                  name="audit_type"
                  value={formData.audit_type}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">{language === 'vi' ? 'Chọn loại audit' : 'Select audit type'}</option>
                  <option value="ISM">ISM</option>
                  <option value="ISPS">ISPS</option>
                  <option value="MLC">MLC</option>
                  <option value="CICA">CICA</option>
                </select>
              </div>
            </div>

            {/* Row 2: Report Form */}
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

            {/* Row 3: Audit Report No + Audit Date */}
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
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
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
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Row 4: Audited By + Status */}
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

            {/* Row 5: Auditor Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên Auditor' : 'Auditor Name'}
              </label>
              <input
                type="text"
                name="auditor_name"
                value={formData.auditor_name}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Nhập tên surveyor...' : 'Enter surveyor name...'}
              />
            </div>

            {/* Row 6: Note */}
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

      {/* Ship Validation Modal */}
      {showValidationModal && validationData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-2xl mx-4 overflow-hidden">
            {/* Header */}
            <div className="bg-yellow-500 px-6 py-4 flex items-center gap-3">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <h3 className="text-xl font-bold text-white">
                {language === 'vi' 
                  ? 'audit-report-sync.preview.emergentagent.com cho biết' 
                  : 'audit-report-sync.preview.emergentagent.com says'}
              </h3>
              <button
                onClick={handleValidationCancel}
                className="ml-auto text-white hover:text-gray-200 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="px-6 py-6">
              <div className="space-y-6">
                {/* PDF Information */}
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3 text-lg">
                    {language === 'vi' ? 'Thông tin trong file PDF:' : 'Information in PDF file:'}
                  </h4>
                  <div className="bg-blue-50 rounded-lg p-4 space-y-2">
                    <div className="flex items-start gap-2">
                      <span className="text-gray-600 min-w-[80px]">
                        {language === 'vi' ? '- Tên tàu:' : '- Ship name:'}
                      </span>
                      <span className="font-medium text-gray-900 break-all">
                        {validationData.extracted_ship_name || 'N/A'}
                      </span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-gray-600 min-w-[80px]">- IMO:</span>
                      <span className="font-medium text-gray-900">
                        {validationData.extracted_ship_imo || 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Selected Ship Information */}
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3 text-lg">
                    {language === 'vi' ? 'Tàu bạn đã chọn:' : 'Your selected ship:'}
                  </h4>
                  <div className="bg-green-50 rounded-lg p-4 space-y-2">
                    <div className="flex items-start gap-2">
                      <span className="text-gray-600 min-w-[80px]">
                        {language === 'vi' ? '- Tên tàu:' : '- Ship name:'}
                      </span>
                      <span className="font-medium text-gray-900 break-all">
                        {validationData.expected_ship_name}
                      </span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-gray-600 min-w-[80px]">- IMO:</span>
                      <span className="font-medium text-gray-900">
                        {validationData.expected_ship_imo || 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Question */}
                <div className="text-center py-2">
                  <p className="text-lg text-gray-700">
                    {language === 'vi' 
                      ? `Bạn có muốn tiếp tục với tàu "${validationData.expected_ship_name}" không?`
                      : `Do you want to continue with ship "${validationData.expected_ship_name}"?`}
                  </p>
                </div>
              </div>
            </div>

            {/* Footer Buttons */}
            <div className="px-6 py-4 bg-gray-50 flex gap-3 justify-end">
              <button
                onClick={handleValidationCancel}
                className="px-6 py-2.5 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
              >
                {language === 'vi' ? 'Hủy' : 'Cancel'}
              </button>
              <button
                onClick={handleValidationConfirm}
                className="px-6 py-2.5 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg font-medium transition-colors shadow-md"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

