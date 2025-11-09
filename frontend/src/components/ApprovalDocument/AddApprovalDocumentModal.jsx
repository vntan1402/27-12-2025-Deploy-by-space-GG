/**
 * Add Drawing Manual Modal
 * Features:
 * - Drag & drop PDF file upload (single & multi-file)
 * - AI Analysis with Document AI
 * - Auto-populate form fields from AI
 * - Manual edit capability
 * - Background file upload to Google Drive
 * - Split PDF support (>15 pages)
 * - Batch processing for multiple files
 */
import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useUploadGuard } from '../../hooks/useUploadGuard';
import { toast } from 'sonner';
import { formatDateForInput } from '../../utils/dateHelpers';

export const AddApprovalDocumentModal = ({ 
  isOpen, 
  onClose, 
  selectedShip, 
  onDocumentAdded, 
  onStartBatchProcessing 
}) => {
  const { language } = useAuth();
  const { isSoftwareExpired, checkAndWarn } = useUploadGuard();
  const [isSaving, setIsSaving] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [analyzedData, setAnalyzedData] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [fileError, setFileError] = useState('');
  const fileInputRef = useRef(null);

  const [formData, setFormData] = useState({
    approval_document_name: '',
    approval_document_no: '',
    approved_by: '',
    approved_date: '',
    status: 'Unknown',
    note: ''
  });

  // Reset form when modal closes or opens
  useEffect(() => {
    if (!isOpen) {
      // Reset all states when modal closes
      setFormData({
        approval_document_name: '',
        approval_document_no: '',
        approved_by: '',
        approved_date: '',
        status: 'Unknown',
        note: ''
      });
      setUploadedFile(null);
      setAnalyzedData(null);
      setIsAnalyzing(false);
      setIsSaving(false);
      setAnalysisProgress('');
      setFileError('');
      setIsDragOver(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [isOpen]);

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

    // Multi-file: Trigger batch processing
    if (fileArray.length > 1) {
      // Validate all files
      const invalidFiles = fileArray.filter(f => !f.name.toLowerCase().endsWith('.pdf'));
      if (invalidFiles.length > 0) {
        toast.error(language === 'vi' ? 'Tất cả files phải là PDF' : 'All files must be PDF');
        return;
      }

      const oversizedFiles = fileArray.filter(f => f.size > 20 * 1024 * 1024);
      if (oversizedFiles.length > 0) {
        toast.error(language === 'vi' ? 'Một số files quá lớn (tối đa 20MB/file)' : 'Some files are too large (max 20MB/file)');
        return;
      }

      // Close modal and start batch processing
      onClose();
      
      if (onStartBatchProcessing) {
        toast.info(
          language === 'vi' 
            ? `🚀 Bắt đầu xử lý ${fileArray.length} files...` 
            : `🚀 Starting batch processing for ${fileArray.length} files...`
        );
        onStartBatchProcessing(fileArray);
      }
      return;
    }

    // Single file: Continue with normal flow
    const file = fileArray[0];

    // Validate PDF
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      toast.error(language === 'vi' ? 'Chỉ hỗ trợ file PDF' : 'Only PDF files are supported');
      return;
    }

    // Validate file size (max 20MB)
    if (file.size > 20 * 1024 * 1024) {
      toast.error(language === 'vi' ? 'File quá lớn (tối đa 20MB)' : 'File too large (max 20MB)');
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
    setFileError('');
    setFormData({
      approval_document_name: '',
      approval_document_no: '',
      approved_by: '',
      approved_date: '',
      status: 'Unknown',
      note: ''
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // ========== AI ANALYSIS ==========
  const analyzeFile = async (file) => {
    // Check if software is expired before AI analysis
    if (!checkAndWarn()) {
      setUploadedFile(null);
      return;
    }

    if (!selectedShip) {
      toast.error(language === 'vi' ? 'Không có tàu được chọn' : 'No ship selected');
      return;
    }

    try {
      setIsAnalyzing(true);
      setFileError('');
      setAnalysisProgress(language === 'vi' ? '📄 Đang phân tích file...' : '📄 Analyzing file...');

      // Show progress for large files
      const fileSizeMB = file.size / (1024 * 1024);
      if (fileSizeMB > 2) {
        setAnalysisProgress(
          language === 'vi' 
            ? `📦 File lớn (${fileSizeMB.toFixed(1)}MB) - Đang xử lý với AI...` 
            : `📦 Large file (${fileSizeMB.toFixed(1)}MB) - Processing with AI...`
        );
      }

      // Create FormData for backend
      const formDataAPI = new FormData();
      formDataAPI.append('ship_id', selectedShip.id);
      formDataAPI.append('document_file', file);
      formDataAPI.append('bypass_validation', 'false');

      // Call backend API
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${BACKEND_URL}/api/approval-documents/analyze-file`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formDataAPI
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Analysis failed');
      }

      const data = await response.json();
      
      // Check split info and show appropriate warnings
      if (data._split_info) {
        const splitInfo = data._split_info;
        
        // Case 1: All chunks failed
        if (splitInfo.all_chunks_failed) {
          toast.error(
            language === 'vi'
              ? `❌ Không thể phân tích file: Tất cả ${splitInfo.processed_chunks} phần đều thất bại. Vui lòng kiểm tra file và thử lại.`
              : `❌ Analysis failed: All ${splitInfo.processed_chunks} chunks failed. Please check the file and try again.`,
            { duration: 10000 }
          );
        }
        // Case 2: Partial failure
        else if (splitInfo.has_failures && splitInfo.partial_success) {
          toast.warning(
            language === 'vi'
              ? `⚠️ Phân tích không hoàn chỉnh: ${splitInfo.successful_chunks}/${splitInfo.processed_chunks} phần thành công, ${splitInfo.failed_chunks} phần thất bại.`
              : `⚠️ Incomplete analysis: ${splitInfo.successful_chunks}/${splitInfo.processed_chunks} chunks successful, ${splitInfo.failed_chunks} chunks failed.`,
            { duration: 8000 }
          );
        }
        // Case 3: File was limited (some chunks skipped)
        else if (splitInfo.was_limited) {
          toast.warning(
            language === 'vi'
              ? `⚠️ File có ${splitInfo.total_pages} trang. Đã xử lý ${splitInfo.processed_chunks}/${splitInfo.total_chunks} phần đầu (giới hạn ${splitInfo.max_chunks_limit} phần)`
              : `⚠️ File has ${splitInfo.total_pages} pages. Processed first ${splitInfo.processed_chunks}/${splitInfo.total_chunks} chunks (limit: ${splitInfo.max_chunks_limit} chunks)`,
            { duration: 8000 }
          );
        }
      }
      
      // Store complete analysis data
      setAnalyzedData(data);
      
      // Auto-fill form with AI-extracted data
      setFormData({
        approval_document_name: data.approval_document_name || file.name.replace('.pdf', ''),
        approval_document_no: data.approval_document_no || '',
        approved_by: data.approved_by || '',
        approved_date: formatDateForInput(data.approved_date) || '',
        status: 'Unknown',
        note: data.note || ''
      });
      
      toast.success(language === 'vi' ? '✅ Phân tích file thành công!' : '✅ File analyzed successfully!');

    } catch (error) {
      console.error('AI analysis error:', error);
      const errorMsg = error.message || 'Failed to analyze file';
      setFileError(errorMsg);
      toast.error(language === 'vi' ? `❌ Không thể phân tích file: ${errorMsg}` : `❌ ${errorMsg}`);
      
      // Allow manual entry even if analysis fails
      setFormData({
        approval_document_name: file.name.replace('.pdf', ''),
        approval_document_no: '',
        approved_by: '',
        approved_date: '',
        status: 'Unknown',
        note: ''
      });
    } finally {
      setIsAnalyzing(false);
      setAnalysisProgress('');
    }
  };

  // ========== SAVE DOCUMENT ==========
  const handleSave = async () => {
    // Validate required fields
    if (!formData.approval_document_name.trim()) {
      toast.error(language === 'vi' ? 'Vui lòng nhập tên tài liệu' : 'Please enter document name');
      return;
    }

    try {
      setIsSaving(true);

      // Create document via API
      const documentData = {
        ship_id: selectedShip.id,
        approval_document_name: formData.approval_document_name.trim(),
        approval_document_no: formData.approval_document_no?.trim() || null,
        approved_by: formData.approved_by?.trim() || null,
        approved_date: formData.approved_date || null,
        status: formData.status || 'Unknown',
        note: formData.note?.trim() || null
      };

      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
      const createResponse = await fetch(`${BACKEND_URL}/api/approval-documents`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(documentData)
      });

      if (!createResponse.ok) {
        const errorData = await createResponse.json().catch(() => null);
        throw new Error(errorData?.detail || 'Failed to create document');
      }

      const createdDocument = await createResponse.json();
      const documentId = createdDocument.id;

      toast.success(language === 'vi' ? '✅ Đã thêm tài liệu' : '✅ Document added');

      // Close modal
      onClose();

      // Notify parent to refresh list
      if (onDocumentAdded) {
        onDocumentAdded();
      }

      // Background file upload (non-blocking)
      if (analyzedData?._file_content && analyzedData?._filename) {
        // Show uploading toast
        const uploadingToast = toast.info(
          language === 'vi' ? '📤 Đang upload file lên Google Drive...' : '📤 Uploading file to Google Drive...', 
          { duration: Infinity }
        );

        // Upload in background
        (async () => {
          try {
            const uploadData = {
              file_content: analyzedData._file_content,
              filename: analyzedData._filename,
              content_type: analyzedData._content_type || 'application/pdf',
              summary_text: analyzedData._summary_text || ''
            };

            const uploadResponse = await fetch(`${BACKEND_URL}/api/approval-documents/${documentId}/upload-files`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify(uploadData)
            });

            // Dismiss uploading toast
            toast.dismiss(uploadingToast);

            if (uploadResponse.ok) {
              toast.success(language === 'vi' ? '✅ File đã upload lên Google Drive!' : '✅ File uploaded to Google Drive!');
            } else {
              toast.warning(language === 'vi' ? '⚠️ Upload file thất bại' : '⚠️ File upload failed');
            }

            // Refresh list to get updated file IDs
            if (onDocumentAdded) {
              onDocumentAdded();
            }
          } catch (uploadError) {
            console.error('Background file upload failed:', uploadError);
            toast.dismiss(uploadingToast);
            toast.error(language === 'vi' ? '❌ Upload file thất bại. Tài liệu đã được lưu.' : '❌ File upload failed. Document was saved.');
          }
        })();
      }

    } catch (error) {
      console.error('Failed to add document:', error);
      const errorMsg = error.message || 'Failed to add document';
      toast.error(language === 'vi' ? `❌ Không thể thêm tài liệu: ${errorMsg}` : `❌ ${errorMsg}`);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? '📐 Thêm Tài liệu Phê duyệt' : '📐 Add Approval Document'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-all"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
            
            <div className="relative">
              <input
                type="file"
                accept=".pdf"
                multiple
                onChange={handleFileInputChange}
                className="hidden"
                id="drawing-manual-file-input"
                disabled={isAnalyzing}
                ref={fileInputRef}
              />
              <label
                htmlFor="drawing-manual-file-input"
                className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer transition-all ${
                  isDragOver
                    ? 'bg-blue-100 border-blue-500'
                    : isAnalyzing
                    ? 'bg-gray-100 border-gray-300 cursor-not-allowed'
                    : 'bg-white border-blue-300 hover:bg-blue-50 hover:border-blue-400'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <svg className="w-10 h-10 mb-3 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="mb-2 text-sm text-gray-700">
                    <span className="font-semibold">{language === 'vi' ? 'Nhấn để chọn' : 'Click to select'}</span> {language === 'vi' ? 'hoặc kéo thả file' : 'or drag and drop'}
                  </p>
                  <p className="text-xs text-gray-500">
                    PDF {language === 'vi' ? '(tối đa 20MB, nhiều file được hỗ trợ)' : '(max 20MB, multiple files supported)'}
                  </p>
                </div>
              </label>
            </div>
            
            {isAnalyzing && (
              <div className="mt-3 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg">
                <div className="flex items-center justify-center text-blue-600 mb-2">
                  <svg className="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="text-sm font-semibold">
                    {analysisProgress || (language === 'vi' ? 'Đang phân tích file...' : 'Analyzing file...')}
                  </span>
                </div>
                <div className="text-xs text-gray-600 text-center">
                  {language === 'vi' 
                    ? 'File > 15 trang sẽ được tự động chia nhỏ (tối đa 5 phần đầu)' 
                    : 'Files > 15 pages will be auto-split (max 5 chunks processed)'}
                </div>
              </div>
            )}
            
            {fileError && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700">{fileError}</p>
              </div>
            )}
          </div>
        )}
        
        {/* Success Message after Analysis */}
        {analyzedData && (
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
                    {analyzedData._filename}
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
          {/* Row 1: Document Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Tên Tài liệu' : 'Document Name'} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="approval_document_name"
              value={formData.approval_document_name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder={language === 'vi' ? 'VD: General Arrangement Plan' : 'e.g. General Arrangement Plan'}
            />
          </div>

          {/* Row 2: Document No. + Approved By */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Số Tài liệu' : 'Document No.'}
              </label>
              <input
                type="text"
                name="approval_document_no"
                value={formData.approval_document_no}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                placeholder={language === 'vi' ? 'VD: GA-001-2024' : 'e.g. GA-001-2024'}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Phê duyệt bởi' : 'Approved By'}
              </label>
              <input
                type="text"
                name="approved_by"
                value={formData.approved_by}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                placeholder={language === 'vi' ? "VD: Lloyd's Register" : "e.g. Lloyd's Register"}
              />
            </div>
          </div>

          {/* Row 3: Approved Date + Status */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ngày phê duyệt' : 'Approved Date'}
              </label>
              <input
                type="date"
                name="approved_date"
                value={formData.approved_date}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Trạng thái' : 'Status'}
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              >
                <option value="Valid">{language === 'vi' ? 'Hợp lệ' : 'Valid'}</option>
                <option value="Approved">{language === 'vi' ? 'Đã phê duyệt' : 'Approved'}</option>
                <option value="Expired">{language === 'vi' ? 'Hết hạn' : 'Expired'}</option>
                <option value="Unknown">{language === 'vi' ? 'Chưa rõ' : 'Unknown'}</option>
              </select>
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

        {/* Action Buttons */}
        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            disabled={isSaving}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all disabled:opacity-50"
          >
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || isAnalyzing}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all font-medium disabled:opacity-50 flex items-center gap-2"
          >
            {isSaving && (
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
            {language === 'vi' ? 'Lưu' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
};
