/**
 * Add Company Certificate Modal
 * With AI analysis and file upload - Full flow like Audit Certificate
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

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
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
    }
  };

  const handleAnalyze = async () => {
    if (!certificateFile) {
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
          filename: certificateFile.name,
          content_type: certificateFile.type
        });

        if (response.data.success) {
          const info = response.data.extracted_info;
          
          // Auto-fill form
          setFormData(prev => ({
            ...prev,
            cert_name: info.cert_name || prev.cert_name,
            cert_no: info.cert_no || prev.cert_no,
            issue_date: info.issue_date || prev.issue_date,
            valid_date: info.valid_date || prev.valid_date,
            issued_by: info.issued_by || prev.issued_by
          }));
          
          // Store summary text
          setSummaryText(response.data.summary_text || '');
          
          // Check for duplicate warning
          if (response.data.duplicate_warning) {
            setDuplicateWarning(response.data.duplicate_warning);
          }
          
          setAnalyzed(true);
          toast.success(language === 'vi' ? 'Phân tích thành công!' : 'Analysis successful!');
        }
      };
      reader.readAsDataURL(certificateFile);
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
    
    if (!formData.cert_name || !formData.cert_no) {
      toast.error(language === 'vi' 
        ? 'Vui lòng nhập tên và số chứng chỉ!'
        : 'Please enter certificate name and number!');
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? 'Thêm chứng chỉ công ty' : 'Add Company Certificate'}
          </h2>
          <button 
            onClick={handleClose} 
            className="text-gray-400 hover:text-gray-600 text-2xl"
            disabled={isSubmitting}
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Tải lên file *' : 'Upload File *'}
            </label>
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileChange}
              className="w-full px-3 py-2 border rounded-lg"
              disabled={isSubmitting}
            />
            <p className="text-xs text-gray-500 mt-1">
              {language === 'vi' 
                ? 'PDF, JPG, PNG (tối đa 50MB)'
                : 'PDF, JPG, PNG (max 50MB)'}
            </p>
            
            {certificateFile && (
              <div className="mt-3 flex items-center gap-3">
                <span className="text-sm text-gray-600">
                  📄 {certificateFile.name}
                </span>
                {!analyzed && (
                  <button
                    type="button"
                    onClick={handleAnalyze}
                    disabled={isAnalyzing}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 text-sm font-medium"
                  >
                    {isAnalyzing 
                      ? (language === 'vi' ? '🔄 Đang phân tích...' : '🔄 Analyzing...') 
                      : (language === 'vi' ? '🤖 Phân tích với AI' : '🤖 Analyze with AI')
                    }
                  </button>
                )}
                {analyzed && (
                  <span className="text-green-600 text-sm font-medium">
                    ✅ {language === 'vi' ? 'Đã phân tích' : 'Analyzed'}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Duplicate Warning */}
          {duplicateWarning && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
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

          {/* Certificate Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Tên chứng chỉ *' : 'Certificate Name *'}
            </label>
            <input
              type="text"
              required
              value={formData.cert_name}
              onChange={(e) => setFormData({ ...formData, cert_name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              disabled={isSubmitting}
            />
          </div>

          {/* Certificate Number */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Số chứng chỉ *' : 'Certificate No *'}
            </label>
            <input
              type="text"
              required
              value={formData.cert_no}
              onChange={(e) => setFormData({ ...formData, cert_no: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              disabled={isSubmitting}
            />
          </div>

          {/* Issue Date & Valid Date */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ngày cấp' : 'Issue Date'}
              </label>
              <input
                type="date"
                value={formData.issue_date}
                onChange={(e) => setFormData({ ...formData, issue_date: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
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
                onChange={(e) => setFormData({ ...formData, valid_date: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* Issued By */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Cơ quan cấp' : 'Issued By'}
            </label>
            <input
              type="text"
              value={formData.issued_by}
              onChange={(e) => setFormData({ ...formData, issued_by: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              disabled={isSubmitting}
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Ghi chú' : 'Notes'}
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              rows="3"
              disabled={isSubmitting}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
              disabled={isSubmitting}
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !certificateFile}
              className="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-400"
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
