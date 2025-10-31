/**
 * Add Test Report Modal
 * Features:
 * - Drag & drop PDF file upload
 * - AI Analysis with Document AI
 * - Auto-populate form fields from AI
 * - Manual edit capability
 * - Background file upload to Google Drive
 * - Split PDF support (>15 pages)
 */
import React, { useState, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { testReportService } from '../../services';
import { toast } from 'sonner';

export const AddTestReportModal = ({ isOpen, onClose, selectedShip, onReportAdded }) => {
  const { language } = useAuth();
  const [isSaving, setIsSaving] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [analyzedData, setAnalyzedData] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const [formData, setFormData] = useState({
    test_report_name: '',
    report_form: '',
    test_report_no: '',
    issued_by: '',
    issued_date: '',
    valid_date: '',
    note: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // ========== FILE UPLOAD HANDLERS ==========
  const handleFileSelect = async (files) => {
    const fileArray = Array.from(files);
    
    if (fileArray.length === 0) return;

    // Only support single file for now
    if (fileArray.length > 1) {
      toast.error(language === 'vi' ? 'Chỉ hỗ trợ 1 file tại một thời điểm' : 'Only one file supported at a time');
      return;
    }

    const file = fileArray[0];

    // Validate PDF
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
    await analyzeFile(file);
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
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // ========== AI ANALYSIS ==========
  const analyzeFile = async (file) => {
    if (!selectedShip) {
      toast.error(language === 'vi' ? 'Không có tàu được chọn' : 'No ship selected');
      return;
    }

    try {
      setIsAnalyzing(true);
      toast.info(language === 'vi' ? '🤖 Đang phân tích file với AI...' : '🤖 Analyzing file with AI...');

      // Create FormData for backend
      const formData = new FormData();
      formData.append('ship_id', selectedShip.id);
      formData.append('test_report_file', file);
      formData.append('bypass_validation', 'false');

      // Call backend API
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${BACKEND_URL}/api/test-reports/analyze-file`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Analysis failed');
      }

      const data = await response.json();
      
      // DEBUG: Log response
      console.log('=== TEST REPORT ANALYSIS RESPONSE ===');
      console.log('Full response:', data);
      console.log('====================================');
      
      // Backend returns DIRECT analysis result (not wrapped)
      // Check for validation error (ship name mismatch)
      if (data.validation_error) {
        const { extracted_ship_name, extracted_ship_imo, expected_ship_name, expected_ship_imo } = data;
        
        const warningMsg = language === 'vi'
          ? `⚠️ CẢNH BÁO: Thông tin tàu không khớp!\n\n` +
            `Thông tin trong file PDF:\n` +
            `  - Tên tàu: ${extracted_ship_name || 'N/A'}\n` +
            `  - IMO: ${extracted_ship_imo || 'N/A'}\n\n` +
            `Tàu bạn đã chọn:\n` +
            `  - Tên tàu: ${expected_ship_name}\n` +
            `  - IMO: ${expected_ship_imo || 'N/A'}\n\n` +
            `Bạn có muốn tiếp tục với tàu "${expected_ship_name}" không?`
          : `⚠️ WARNING: Ship information mismatch!\n\n` +
            `Information in PDF file:\n` +
            `  - Ship name: ${extracted_ship_name || 'N/A'}\n` +
            `  - IMO: ${extracted_ship_imo || 'N/A'}\n\n` +
            `Your selected ship:\n` +
            `  - Ship name: ${expected_ship_name}\n` +
            `  - IMO: ${expected_ship_imo || 'N/A'}\n\n` +
            `Do you want to continue with ship "${expected_ship_name}"?`;
        
        if (!window.confirm(warningMsg)) {
          setIsAnalyzing(false);
          setUploadedFile(null);
          return;
        }
        
        // User confirmed - retry with bypass
        toast.info(language === 'vi' ? '🔄 Phân tích lại với xác nhận...' : '🔄 Re-analyzing with confirmation...');
        formData.set('bypass_validation', 'true');
        
        const retryResponse = await fetch(`${BACKEND_URL}/api/test-reports/analyze-file`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: formData
        });

        if (!retryResponse.ok) {
          throw new Error('Re-analysis failed');
        }

        const retryData = await retryResponse.json();
        // Backend returns direct analysis result
        processAnalysisSuccess(retryData, file);
      } else {
        // No validation error - success
        // Backend returns direct analysis result
        processAnalysisSuccess(data, file);
      }

    } catch (error) {
      console.error('AI analysis error:', error);
      toast.error(
        language === 'vi' 
          ? `❌ Lỗi phân tích file: ${error.message}` 
          : `❌ Analysis failed: ${error.message}`
      );
      setUploadedFile(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Process successful analysis
  const processAnalysisSuccess = (analysis, file) => {
    // DEBUG: Log what we received
    console.log('=== PROCESS ANALYSIS SUCCESS ===');
    console.log('Analysis data:', analysis);
    console.log('test_report_name:', analysis.test_report_name);
    console.log('report_form:', analysis.report_form);
    console.log('test_report_no:', analysis.test_report_no);
    console.log('issued_by:', analysis.issued_by);
    console.log('issued_date:', analysis.issued_date);
    console.log('valid_date:', analysis.valid_date);
    console.log('================================');
    
    // Store complete analysis data (including _file_content, _summary_text)
    setAnalyzedData(analysis);
    
    // Auto-populate form fields
    const newFormData = {
      test_report_name: analysis.test_report_name || '',
      report_form: analysis.report_form || '',
      test_report_no: analysis.test_report_no || '',
      issued_by: analysis.issued_by || '',
      issued_date: analysis.issued_date ? analysis.issued_date.split('T')[0] : '',
      valid_date: analysis.valid_date ? analysis.valid_date.split('T')[0] : '',
      note: formData.note // Keep existing note
    };
    
    console.log('=== NEW FORM DATA ===');
    console.log('Setting formData to:', newFormData);
    console.log('=====================');
    
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
          ? '✅ OCR enhancement applied - Report Form và Report No được trích xuất chính xác hơn'
          : '✅ OCR enhancement applied - Report Form and Report No extracted with higher accuracy'
      );
    }

    // Warn about manual review if needed
    if (analysis._ocr_info?.needs_manual_review) {
      toast.warning(
        language === 'vi'
          ? '⚠️ Vui lòng kiểm tra Report Form và Report No'
          : '⚠️ Please verify Report Form and Report No'
      );
    }

    toast.success(
      language === 'vi' 
        ? '✅ File đã được phân tích!' 
        : '✅ File analyzed successfully!'
    );
  };

  // Process failed analysis
  const processAnalysisFail = () => {
    toast.error(
      language === 'vi' 
        ? '❌ Không thể phân tích file. Vui lòng nhập thủ công.' 
        : '❌ Failed to analyze file. Please enter manually.'
    );
  };

  // ========== SAVE TEST REPORT ==========
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

    if (!selectedShip) {
      toast.error(language === 'vi' ? 'Vui lòng chọn tàu' : 'Please select a ship');
      return;
    }

    try {
      setIsSaving(true);

      // Create test report in database
      const reportData = {
        ship_id: selectedShip.id,
        company_id: selectedShip.company,
        test_report_name: formData.test_report_name.trim(),
        report_form: formData.report_form?.trim() || null,
        test_report_no: formData.test_report_no.trim(),
        issued_by: formData.issued_by?.trim() || null,
        issued_date: formData.issued_date,
        valid_date: formData.valid_date || null,
        note: formData.note?.trim() || null
      };

      const createdReport = await testReportService.create(reportData);

      toast.success(
        language === 'vi' 
          ? '✅ Đã tạo báo cáo test' 
          : '✅ Test report created'
      );

      // Upload file in background if file was uploaded and analyzed
      if (uploadedFile && analyzedData && createdReport.id) {
        uploadFileInBackground(
          createdReport.id,
          analyzedData._file_content,
          analyzedData._filename,
          analyzedData._content_type,
          analyzedData._summary_text
        );
      }

      // Close modal and refresh list
      onReportAdded();
      onClose();
      resetForm();

    } catch (error) {
      console.error('Failed to create test report:', error);
      toast.error(
        language === 'vi' 
          ? '❌ Không thể tạo báo cáo test' 
          : '❌ Failed to create test report'
      );
    } finally {
      setIsSaving(false);
    }
  };

  // ========== BACKGROUND FILE UPLOAD ==========
  const uploadFileInBackground = async (reportId, fileContent, filename, contentType, summaryText) => {
    try {
      toast.info(
        language === 'vi' 
          ? '📤 Đang tải file lên Google Drive...' 
          : '📤 Uploading file to Google Drive...'
      );

      // Convert base64 to File object for upload
      const byteCharacters = atob(fileContent);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const file = new File([byteArray], filename, { type: contentType });

      await testReportService.uploadFiles(reportId, file);

      toast.success(
        language === 'vi' 
          ? '✅ Đã tải file lên thành công!' 
          : '✅ File uploaded successfully!'
      );

    } catch (error) {
      console.error('Background upload failed:', error);
      toast.error(
        language === 'vi' 
          ? '⚠️ Không thể tải file lên. Báo cáo đã được lưu.' 
          : '⚠️ Failed to upload file. Report was saved.'
      );
    }
  };

  // ========== RESET FORM ==========
  const resetForm = () => {
    setFormData({
      test_report_name: '',
      report_form: '',
      test_report_no: '',
      issued_by: '',
      issued_date: '',
      valid_date: '',
      note: ''
    });
    setUploadedFile(null);
    setAnalyzedData(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? '📋 Thêm Báo cáo Test' : '📋 Add Test Report'}
          </h3>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title={language === 'vi' ? 'Đóng' : 'Close'}
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Section 1: File Upload for AI Analysis */}
        {!analyzedData && (
          <div className="mb-6 p-4 bg-blue-50 border-2 border-blue-200 rounded-lg">
            <div className="flex items-center mb-3">
              <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <h4 className="text-lg font-semibold text-gray-800">
                {language === 'vi' ? '🤖 Phân tích File với AI' : '🤖 AI File Analysis'}
              </h4>
            </div>

            <div
              className={`relative border-2 border-dashed rounded-lg cursor-pointer transition-all ${
                isDragOver
                  ? 'border-blue-500 bg-blue-100'
                  : isAnalyzing
                  ? 'border-gray-300 bg-gray-100 cursor-not-allowed'
                  : 'border-blue-300 bg-white hover:bg-blue-50 hover:border-blue-400'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileInputChange}
                className="hidden"
                id="test-report-file-input"
                disabled={isAnalyzing}
              />
              <label
                htmlFor="test-report-file-input"
                className="flex flex-col items-center justify-center w-full h-32 cursor-pointer"
              >
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <svg className="w-10 h-10 mb-3 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="mb-2 text-sm text-gray-700">
                    <span className="font-semibold">{language === 'vi' ? 'Nhấn để chọn' : 'Click to select'}</span> {language === 'vi' ? 'hoặc kéo thả file' : 'or drag and drop'}
                  </p>
                  <p className="text-xs text-gray-500">
                    PDF {language === 'vi' ? '(tối đa 50MB)' : '(max 50MB)'}
                  </p>
                </div>
              </label>
            </div>

            {isAnalyzing && (
              <div className="mt-3 flex items-center justify-center text-blue-600">
                <svg className="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="text-sm font-medium">
                  {language === 'vi' ? 'Đang phân tích file...' : 'Analyzing file...'}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Success Message after Analysis */}
        {analyzedData && uploadedFile && (
          <div className="mb-6 p-4 bg-green-50 border-2 border-green-200 rounded-lg">
            <div className="flex items-start justify-between">
              <div className="flex items-start">
                <svg className="w-6 h-6 text-green-600 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="text-sm font-semibold text-green-800 mb-1">
                    {language === 'vi' ? '✅ File đã được phân tích thành công!' : '✅ File analyzed successfully!'}
                  </p>
                  <p className="text-xs text-green-700 font-medium">
                    {uploadedFile.name}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    {language === 'vi' ? 'Thông tin đã được tự động điền. Vui lòng kiểm tra và chỉnh sửa nếu cần.' : 'Information has been auto-filled. Please review and edit if needed.'}
                  </p>
                </div>
              </div>
              <button
                onClick={handleRemoveFile}
                className="ml-2 p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-all"
                title={language === 'vi' ? 'Xóa và chọn file khác' : 'Remove and select another file'}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Section 2: Manual Entry Form */}
        <div className="mb-4 flex items-center text-gray-700">
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          <span className="font-medium">
            {language === 'vi' ? 'Hoặc nhập thủ công' : 'Or Enter Manually'}
          </span>
        </div>

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
            onClick={handleClose}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all font-medium"
            disabled={isSaving}
          >
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || isAnalyzing}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              isSaving || isAnalyzing
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
