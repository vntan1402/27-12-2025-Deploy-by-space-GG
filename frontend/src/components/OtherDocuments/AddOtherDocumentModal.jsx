/**
 * Add Other Document Modal
 * Modal for adding new other documents
 * 
 * Features:
 * - File upload (optional): single file or multiple files
 * - Folder upload (optional)
 * - Manual entry fields: Document Name, Date, Status, Note
 * - Batch processing for multiple files (each file = 1 record)
 * - NO AI auto-fill (unlike Drawings & Manuals and Test Report)
 * 
 * Simpler than Test Report/Drawings & Manuals (no AI analysis)
 */

import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import otherDocumentService from '../../services/otherDocumentService';

const AddOtherDocumentModal = ({ show, onClose, selectedShip, onSuccess }) => {
  const { language } = useAuth();

  // Form state
  const [formData, setFormData] = useState({
    document_name: '',
    date: '',
    status: 'Unknown',
    note: ''
  });

  // File upload state
  const [files, setFiles] = useState([]);
  const [isFolder, setIsFolder] = useState(false);
  const [fileError, setFileError] = useState('');

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);

  // Handle file selection
  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    
    if (selectedFiles.length === 0) return;

    // Validate file types (PDF, JPG, JPEG)
    const invalidFiles = selectedFiles.filter(file => {
      const ext = file.name.split('.').pop().toLowerCase();
      return !['pdf', 'jpg', 'jpeg'].includes(ext);
    });

    if (invalidFiles.length > 0) {
      setFileError(language === 'vi' 
        ? `Chỉ chấp nhận file PDF và JPG. File không hợp lệ: ${invalidFiles.map(f => f.name).join(', ')}`
        : `Only PDF and JPG files are accepted. Invalid files: ${invalidFiles.map(f => f.name).join(', ')}`
      );
      return;
    }

    setFiles(selectedFiles);
    setIsFolder(false);
    setFileError('');

    // Auto-fill document name from first file if empty
    if (!formData.document_name && selectedFiles.length === 1) {
      const fileName = selectedFiles[0].name.replace(/\.[^/.]+$/, ''); // Remove extension
      setFormData(prev => ({ ...prev, document_name: fileName }));
    }
  };

  // Handle folder selection
  const handleFolderSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    
    if (selectedFiles.length === 0) return;

    setFiles(selectedFiles);
    setIsFolder(true);
    setFileError('');

    // Auto-fill document name from folder name if empty
    if (!formData.document_name && selectedFiles.length > 0) {
      const folderPath = selectedFiles[0].webkitRelativePath || '';
      const folderName = folderPath.split('/')[0];
      if (folderName) {
        setFormData(prev => ({ ...prev, document_name: folderName }));
      }
    }
  };

  // Handle form submission
  const handleSubmit = async () => {
    // Validate: must have document name OR files
    if (!formData.document_name && files.length === 0) {
      toast.error(language === 'vi' 
        ? 'Vui lòng nhập tên tài liệu hoặc chọn file' 
        : 'Please enter document name or select files');
      return;
    }

    try {
      setIsProcessing(true);

      if (files.length === 0) {
        // Manual entry without files
        await otherDocumentService.create({
          ship_id: selectedShip.id,
          document_name: formData.document_name,
          date: formData.date || null,
          status: formData.status,
          note: formData.note || null,
          file_ids: []
        });

        toast.success(language === 'vi' 
          ? '✅ Đã thêm tài liệu thành công!' 
          : '✅ Document added successfully!');
        
        onSuccess();
      } else if (isFolder) {
        // Folder upload
        const folderName = formData.document_name || files[0].webkitRelativePath.split('/')[0];
        
        toast.info(language === 'vi'
          ? `📤 Đang upload ${files.length} files lên Google Drive...`
          : `📤 Uploading ${files.length} files to Google Drive...`
        );
        
        const result = await otherDocumentService.uploadFolder(
          selectedShip.id,
          files,
          folderName,
          {
            date: formData.date || null,
            status: formData.status,
            note: formData.note || null
          }
        );

        if (result.success) {
          toast.success(language === 'vi'
            ? `✅ Đã upload folder thành công! (${result.successful_files}/${result.total_files} files)`
            : `✅ Folder uploaded successfully! (${result.successful_files}/${result.total_files} files)`
          );
          onSuccess();
        } else {
          throw new Error(result.message || 'Upload failed');
        }
      } else {
        // Multiple files upload (batch processing)
        toast.info(language === 'vi'
          ? `📤 Đang upload ${files.length} file(s) lên Google Drive...`
          : `📤 Uploading ${files.length} file(s) to Google Drive...`
        );
        
        const results = await otherDocumentService.uploadFiles(
          selectedShip.id,
          files,
          {
            document_name: files.length === 1 ? formData.document_name : null,
            date: formData.date || null,
            status: formData.status,
            note: formData.note || null
          }
        );

        const successCount = results.filter(r => r.success).length;
        const failCount = results.filter(r => !r.success).length;

        if (successCount > 0) {
          toast.success(language === 'vi'
            ? `✅ Đã upload thành công ${successCount}/${files.length} file(s)`
            : `✅ Successfully uploaded ${successCount}/${files.length} file(s)`
          );
        }

        if (failCount > 0) {
          const failedFiles = results.filter(r => !r.success).map(r => r.filename).join(', ');
          toast.error(language === 'vi'
            ? `❌ Upload thất bại cho ${failCount} file(s): ${failedFiles}`
            : `❌ Failed to upload ${failCount} file(s): ${failedFiles}`
          );
        }

        onSuccess();
      }
    } catch (error) {
      console.error('Failed to add document:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      toast.error(language === 'vi' 
        ? `❌ Lỗi: ${errorMessage}` 
        : `❌ Error: ${errorMessage}`);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!show) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto relative">
        {/* Processing Overlay */}
        {isProcessing && (
          <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center z-10 rounded-xl">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
              <p className="text-lg font-semibold text-gray-800">
                {language === 'vi' 
                  ? '📤 Đang upload file lên Google Drive...' 
                  : '📤 Uploading file to Google Drive...'}
              </p>
              <p className="text-sm text-gray-600 mt-2">
                {language === 'vi' 
                  ? 'Vui lòng đợi, quá trình này có thể mất vài phút' 
                  : 'Please wait, this may take a few minutes'}
              </p>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? '📁 Thêm Tài liệu Khác' : '📁 Add Other Document'}
          </h3>
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="text-gray-400 hover:text-gray-600 transition-all"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <div className="space-y-4">
          {/* File Upload Section */}
          <div className="p-4 bg-blue-50 border-2 border-blue-200 rounded-lg">
            <div className="flex items-center mb-3">
              <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <h4 className="text-base font-semibold text-gray-800">
                {language === 'vi' ? '📤 Chọn File để Upload (không bắt buộc)' : '📤 Select File to Upload (optional)'}
              </h4>
            </div>

            <div className="space-y-2">
              {/* File Input (hidden) */}
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg"
                multiple
                onChange={handleFileSelect}
                className="hidden"
                id="other-doc-file-input"
              />

              {/* Folder Input (hidden) */}
              <input
                type="file"
                webkitdirectory=""
                directory=""
                multiple
                onChange={handleFolderSelect}
                className="hidden"
                id="other-doc-folder-input"
              />

              {/* Upload Buttons */}
              <div className="grid grid-cols-2 gap-3">
                <label
                  htmlFor="other-doc-file-input"
                  className="flex flex-col items-center justify-center h-24 border-2 border-dashed border-blue-300 rounded-lg cursor-pointer bg-white hover:bg-blue-50 transition-all"
                >
                  <svg className="w-8 h-8 text-blue-500 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <p className="text-sm font-medium text-gray-700">
                    {language === 'vi' ? 'Chọn Files' : 'Select Files'}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {language === 'vi' ? 'PDF, JPG' : 'PDF, JPG'}
                  </p>
                </label>

                <label
                  htmlFor="other-doc-folder-input"
                  className="flex flex-col items-center justify-center h-24 border-2 border-dashed border-green-300 rounded-lg cursor-pointer bg-white hover:bg-green-50 transition-all"
                >
                  <svg className="w-8 h-8 text-green-500 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                  </svg>
                  <p className="text-sm font-medium text-gray-700">
                    {language === 'vi' ? 'Chọn Folder' : 'Select Folder'}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {language === 'vi' ? 'Toàn bộ thư mục' : 'Entire folder'}
                  </p>
                </label>
              </div>
            </div>

            {/* Selected Files Display */}
            {files.length > 0 && (
              <div className="mt-3 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-sm text-gray-700">
                    {language === 'vi' ? 'Đã chọn:' : 'Selected:'}
                  </p>
                  {files.length > 1 && (
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full">
                      {language === 'vi'
                        ? `${files.length} files → ${files.length} records`
                        : `${files.length} files → ${files.length} records`
                      }
                    </span>
                  )}
                </div>
                <ul className="list-disc list-inside max-h-24 overflow-y-auto text-sm text-gray-600 bg-white p-2 rounded border border-blue-200">
                  {files.map((file, index) => (
                    <li key={index} className="truncate">{file.name || file.webkitRelativePath}</li>
                  ))}
                </ul>
                {files.length > 1 && (
                  <p className="text-xs text-blue-600 italic">
                    {language === 'vi'
                      ? '💡 Mỗi file sẽ tạo 1 record riêng với tên từ file name'
                      : '💡 Each file will create a separate record with name from file name'
                    }
                  </p>
                )}
              </div>
            )}

            {/* Error Display */}
            {fileError && (
              <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {fileError}
              </div>
            )}
          </div>

          {/* Document Information */}
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên Tài liệu' : 'Document Name'}
                {files.length === 0 && <span className="text-red-500">*</span>}
              </label>
              <input
                type="text"
                value={formData.document_name}
                onChange={(e) => setFormData(prev => ({ ...prev, document_name: e.target.value }))}
                placeholder={
                  files.length > 1
                    ? (language === 'vi' ? 'Mỗi file sẽ dùng tên riêng' : 'Each file will use its own name')
                    : (language === 'vi' ? 'Tự động điền từ file name hoặc nhập thủ công' : 'Auto-filled from file or enter manually')
                }
                disabled={files.length > 1}
                className={`w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  files.length > 1 ? 'bg-gray-100 cursor-not-allowed text-gray-500' : ''
                }`}
              />
              {files.length > 1 && (
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi'
                    ? '📝 Document Name sẽ lấy từ file name của mỗi file'
                    : '📝 Document Name will be taken from each file name'
                  }
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày' : 'Date'}
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Trạng thái' : 'Status'}
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Valid">{language === 'vi' ? 'Hợp lệ' : 'Valid'}</option>
                  <option value="Expired">{language === 'vi' ? 'Hết hạn' : 'Expired'}</option>
                  <option value="Unknown">{language === 'vi' ? 'Chưa rõ' : 'Unknown'}</option>
                </select>
              </div>
            </div>

            {files.length > 1 && (
              <div className="p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-xs text-yellow-800">
                  {language === 'vi'
                    ? '📌 Ngày và Trạng thái sẽ được áp dụng cho tất cả files'
                    : '📌 Date and Status will be applied to all files'
                  }
                </p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ghi chú' : 'Note'}
              </label>
              <textarea
                value={formData.note}
                onChange={(e) => setFormData(prev => ({ ...prev, note: e.target.value }))}
                placeholder={language === 'vi' ? 'Nhập ghi chú...' : 'Enter note...'}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                rows="2"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 mt-4">
            <button
              onClick={onClose}
              disabled={isProcessing}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all disabled:opacity-50"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              onClick={handleSubmit}
              disabled={(!formData.document_name && files.length === 0) || isProcessing}
              className={`px-6 py-2 rounded-lg transition-all font-medium ${
                (!formData.document_name && files.length === 0) || isProcessing
                  ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {isProcessing
                ? (language === 'vi' ? '⏳ Đang xử lý...' : '⏳ Processing...')
                : (language === 'vi' ? '✅ Thêm' : '✅ Add')
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddOtherDocumentModal;
