import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import api from '../../services/api';

// Common certificate names (same as Add Modal)
const COMMON_CERT_NAMES = [
  'Certificate of Competency (COC)',
  'Certificate of Endorsement (COE)',
  'Seaman Book for COC',
  'Seaman book for GMDSS',
  'GMDSS Certificate',
  'Medical Certificate',
  'Basic Safety Training (BST)',
  'Advanced Fire Fighting (AFF)',
  'Ship Security Officer (SSO)',
  'Ship Security Awareness',
  'Proficiency in Survival Craft and Rescue Boats',
  'Crowd Management',
  'Crisis Management and Human Behavior',
  'Passenger Ship Safety',
  'ECDIS',
  'Bridge Resource Management (BRM)',
  'Engine Resource Management (ERM)',
  'High Voltage Certificate',
  'Ratings Forming Part of a Watch',
  'Ratings as Able Seafarer Deck',
  'Ratings as Able Seafarer Engine',
  'Oil Tanker Familiarization',
  'Chemical Tanker Familiarization',
  'Liquefied Gas Tanker Familiarization',
  'Oil Tanker Advanced',
  'Chemical Tanker Advanced',
  'Liquefied Gas Tanker Advanced',
  'Welding Certificate',
  'Radar Certificate'
];

const EditCrewCertificateModal = ({ certificate, onClose, onSuccess, selectedShip }) => {
  const { language, user } = useAuth();
  const fileInputRef = useRef(null);
  
  // State
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzedData, setAnalyzedData] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [customCertNames, setCustomCertNames] = useState([]);
  const [customCertInput, setCustomCertInput] = useState('');
  
  // Form data - pre-filled with certificate data
  const [formData, setFormData] = useState({
    crew_id: certificate.crew_id || '',
    crew_name: certificate.crew_name || '',
    crew_name_en: certificate.crew_name_en || '',
    passport: certificate.passport || '',
    rank: certificate.rank || '',
    date_of_birth: certificate.date_of_birth || '',
    cert_name: certificate.cert_name || '',
    cert_no: certificate.cert_no || '',
    issued_by: certificate.issued_by || '',
    issued_date: certificate.issued_date || '',
    cert_expiry: certificate.cert_expiry || '',
    note: certificate.note || ''
  });

  useEffect(() => {
    loadCustomCertNames();
  }, []);

  // Load custom certificate names from localStorage
  const loadCustomCertNames = () => {
    try {
      const saved = localStorage.getItem('customCrewCertNames');
      if (saved) {
        setCustomCertNames(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Failed to load custom cert names:', error);
    }
  };

  // Save custom certificate name to localStorage
  const saveCustomCertName = (certName) => {
    if (!certName || COMMON_CERT_NAMES.includes(certName)) return;
    
    const updated = [...new Set([...customCertNames, certName])];
    setCustomCertNames(updated);
    localStorage.setItem('customCrewCertNames', JSON.stringify(updated));
  };

  // Handle file drop/select
  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (file) {
      await handleFileUpload(file);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      await handleFileUpload(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleFileUpload = async (file) => {
    // Validate file
    const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      toast.error(language === 'vi' 
        ? '❌ Chỉ hỗ trợ file PDF, JPG, PNG' 
        : '❌ Only PDF, JPG, PNG files are supported');
      return;
    }

    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      toast.error(language === 'vi' 
        ? '❌ File quá lớn (tối đa 10MB)' 
        : '❌ File too large (max 10MB)');
      return;
    }

    setUploadedFile(file);
    
    // Auto-analyze
    await analyzeFile(file);
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setAnalyzedData(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const analyzeFile = async (file) => {
    if (!selectedShip) {
      toast.warning(language === 'vi' 
        ? 'Vui lòng chọn tàu trước' 
        : 'Please select ship first');
      return;
    }

    try {
      setIsAnalyzing(true);
      toast.info(language === 'vi' ? '🤖 Đang phân tích chứng chỉ với AI...' : '🤖 Analyzing certificate with AI...');

      const formDataToSend = new FormData();
      formDataToSend.append('cert_file', file);
      formDataToSend.append('ship_id', selectedShip.id);
      formDataToSend.append('crew_id', formData.crew_id);
      formDataToSend.append('bypass_validation', 'false');
      formDataToSend.append('bypass_dob_validation', 'false');

      const response = await api.post('/api/crew-certificates/analyze-file', formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 120000
      });

      const data = response.data || response;

      if (data.success && data.analysis) {
        processAnalysisSuccess(data.analysis);
      } else {
        toast.warning(language === 'vi' 
          ? '⚠️ Không thể phân tích file. Vui lòng nhập thủ công.'
          : '⚠️ Cannot analyze file. Please enter manually.');
      }

    } catch (error) {
      console.error('AI analysis error:', error);
      
      // Better error handling
      const errorDetail = error.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'string' 
        ? errorDetail 
        : (errorDetail ? JSON.stringify(errorDetail) : 'Unknown error');
      
      toast.error(language === 'vi' 
        ? `❌ Lỗi phân tích file: ${errorMessage}` 
        : `❌ Analysis failed: ${errorMessage}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const processAnalysisSuccess = (analysis) => {
    setAnalyzedData(analysis);
    
    setFormData(prev => ({
      ...prev,
      cert_name: analysis.cert_name || prev.cert_name,
      cert_no: analysis.cert_no || prev.cert_no,
      issued_by: analysis.issued_by || prev.issued_by,
      issued_date: analysis.issued_date ? 
        (analysis.issued_date.includes('/') ? 
          analysis.issued_date.split('/').reverse().join('-') : 
          analysis.issued_date.split('T')[0]
        ) : prev.issued_date,
      cert_expiry: analysis.expiry_date || analysis.cert_expiry ? 
        ((analysis.expiry_date || analysis.cert_expiry).includes('/') ? 
          (analysis.expiry_date || analysis.cert_expiry).split('/').reverse().join('-') : 
          (analysis.expiry_date || analysis.cert_expiry).split('T')[0]
        ) : prev.cert_expiry,
      rank: analysis.rank || prev.rank
    }));

    toast.success(language === 'vi' 
      ? '✅ Phân tích AI thành công!' 
      : '✅ AI analysis successful!');
  };

  // Handle form input change
  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Handle submit
  const handleSubmit = async () => {
    // Validate required fields
    if (!formData.cert_name || !formData.cert_no) {
      toast.error(language === 'vi' 
        ? '❌ Vui lòng điền đầy đủ thông tin bắt buộc (*)' 
        : '❌ Please fill in all required fields (*)');
      return;
    }

    try {
      setIsSubmitting(true);

      // Save custom cert name if new
      saveCustomCertName(formData.cert_name);

      // Update certificate
      const certData = {
        crew_id: formData.crew_id,
        crew_name: formData.crew_name,
        crew_name_en: formData.crew_name_en,
        passport: formData.passport,
        rank: formData.rank,
        date_of_birth: formData.date_of_birth,
        cert_name: formData.cert_name,
        cert_no: formData.cert_no,
        issued_by: formData.issued_by || '-',
        issued_date: formData.issued_date || null,
        cert_expiry: formData.cert_expiry || null,
        note: formData.note || ''
      };

      await api.put(`/api/crew-certificates/${certificate.id}`, certData);

      // Upload new files if available (background)
      if (analyzedData?._file_content && certificate.id) {
        uploadFilesInBackground(certificate.id);
      }

      toast.success(language === 'vi' 
        ? '✅ Cập nhật chứng chỉ thành công!' 
        : '✅ Certificate updated successfully!');

      onSuccess?.();
      onClose();

    } catch (error) {
      console.error('Update error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      toast.error(language === 'vi' 
        ? `❌ Không thể cập nhật chứng chỉ: ${errorMessage}` 
        : `❌ Failed to update certificate: ${errorMessage}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Upload files in background
  const uploadFilesInBackground = async (certId) => {
    try {
      const uploadData = {
        file_content: analyzedData._file_content,
        filename: analyzedData._filename,
        content_type: analyzedData._content_type,
        summary_text: analyzedData._summary_text || ''
      };

      await api.post(`/api/crew-certificates/${certId}/upload-files`, uploadData);
      
      toast.success(language === 'vi' 
        ? '✅ Đã upload files lên Google Drive' 
        : '✅ Files uploaded to Google Drive');

    } catch (error) {
      console.error('File upload error:', error);
      toast.warning(language === 'vi' 
        ? '⚠️ Đã cập nhật chứng chỉ nhưng lỗi khi upload files' 
        : '⚠️ Certificate updated but file upload failed');
    }
  };

  // Get all cert names (common + custom)
  const getAllCertNames = () => {
    return [...COMMON_CERT_NAMES, ...customCertNames].sort();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 flex justify-between items-center bg-gradient-to-r from-blue-50 to-blue-100">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 flex items-center">
              <span className="mr-2">✏️</span>
              {language === 'vi' ? 'Chỉnh sửa chứng chỉ' : 'Edit Certificate'}
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {formData.crew_name} - {formData.cert_name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1">
          <div className="space-y-6">
            {/* Section 1: Replace File (Optional) */}
            <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-blue-800 mb-3 flex items-center">
                <span className="mr-2">📄</span>
                {language === 'vi' ? 'Thay thế file chứng chỉ (Tùy chọn)' : 'Replace Certificate File (Optional)'}
              </h3>
              
              {/* Drag and drop area */}
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all ${
                  uploadedFile 
                    ? 'border-green-400 bg-green-50' 
                    : 'border-blue-300 bg-white hover:border-blue-500 hover:bg-blue-50'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={handleFileChange}
                  className="hidden"
                />
                
                {uploadedFile ? (
                  <div className="flex items-center justify-center space-x-4">
                    <div className="flex-1">
                      <p className="text-green-700 font-medium">{uploadedFile.name}</p>
                      <p className="text-sm text-gray-500 mt-1">
                        {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveFile();
                      }}
                      className="px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded-md text-sm"
                    >
                      {language === 'vi' ? 'Xóa' : 'Remove'}
                    </button>
                  </div>
                ) : (
                  <div>
                    <div className="text-4xl mb-2">📄</div>
                    <p className="text-gray-600 font-medium">
                      {language === 'vi' 
                        ? 'Kéo thả file mới hoặc click để chọn' 
                        : 'Drag & drop new file or click to select'}
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      {language === 'vi' 
                        ? 'Hỗ trợ: PDF, JPG, PNG (tối đa 10MB)' 
                        : 'Supports: PDF, JPG, PNG (max 10MB)'}
                    </p>
                  </div>
                )}
              </div>

              {/* Analysis status */}
              {isAnalyzing && (
                <div className="mt-4 p-3 bg-blue-100 border border-blue-300 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    <span className="text-blue-700">
                      {language === 'vi' ? '🤖 Đang phân tích chứng chỉ với AI...' : '🤖 Analyzing certificate with AI...'}
                    </span>
                  </div>
                </div>
              )}

              {/* Analysis success */}
              {!isAnalyzing && uploadedFile && analyzedData && (
                <div className="mt-4 p-3 bg-green-100 border border-green-300 rounded-lg">
                  <p className="text-green-700 font-medium flex items-center">
                    <span className="mr-2">✅</span>
                    {language === 'vi' ? 'AI phân tích thành công! Thông tin đã được cập nhật.' : 'AI analysis successful! Information updated.'}
                  </p>
                </div>
              )}
            </div>

            {/* Section 2: Certificate Details */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <span className="mr-2">📋</span>
                {language === 'vi' ? 'Thông tin chứng chỉ' : 'Certificate Details'}
              </h3>

              <div className="grid grid-cols-2 gap-4">
                {/* Certificate Name */}
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'}
                    <span className="text-red-500 ml-1">*</span>
                  </label>
                  <select
                    value={formData.cert_name}
                    onChange={(e) => handleInputChange('cert_name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">
                      {language === 'vi' ? '-- Chọn loại chứng chỉ --' : '-- Select certificate type --'}
                    </option>
                    {COMMON_CERT_NAMES.map((name, idx) => (
                      <option key={idx} value={name}>
                        {name}
                      </option>
                    ))}
                    {customCertNames.map((name, idx) => (
                      <option key={`custom-${idx}`} value={name}>
                        {name} (Custom)
                      </option>
                    ))}
                    <option value="__OTHER__">
                      {language === 'vi' ? '🔧 Khác (Nhập tên mới)...' : '🔧 Other (Enter new name)...'}
                    </option>
                  </select>
                  
                  {/* Custom name input (shown when "Other" is selected) */}
                  {formData.cert_name === '__OTHER__' && (
                    <div className="mt-2">
                      <input
                        type="text"
                        value={customCertInput}
                        onChange={(e) => setCustomCertInput(e.target.value)}
                        onBlur={() => {
                          if (customCertInput.trim()) {
                            saveCustomCertName(customCertInput.trim());
                            handleInputChange('cert_name', customCertInput.trim());
                            setCustomCertInput('');
                          }
                        }}
                        placeholder={language === 'vi' ? 'Nhập tên chứng chỉ mới' : 'Enter new certificate name'}
                        className="w-full px-3 py-2 border border-orange-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                        autoFocus
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        {language === 'vi' 
                          ? '💡 Nhập tên và nhấn Tab hoặc click ra ngoài để lưu' 
                          : '💡 Enter name and press Tab or click outside to save'}
                      </p>
                    </div>
                  )}
                </div>

                {/* Certificate Number */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Số chứng chỉ' : 'Certificate No.'}
                    <span className="text-red-500 ml-1">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.cert_no}
                    onChange={(e) => handleInputChange('cert_no', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Issued By */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Cơ quan cấp' : 'Issued By'}
                  </label>
                  <input
                    type="text"
                    value={formData.issued_by}
                    onChange={(e) => handleInputChange('issued_by', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Issued Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Ngày cấp' : 'Issued Date'}
                  </label>
                  <input
                    type="date"
                    value={formData.issued_date}
                    onChange={(e) => handleInputChange('issued_date', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Certificate Expiry */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Ngày hết hạn' : 'Expiry Date'}
                  </label>
                  <input
                    type="date"
                    value={formData.cert_expiry}
                    onChange={(e) => handleInputChange('cert_expiry', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Note */}
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Ghi chú' : 'Note'}
                  </label>
                  <textarea
                    value={formData.note}
                    onChange={(e) => handleInputChange('note', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
            disabled={isSubmitting}
          >
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !formData.cert_name || !formData.cert_no}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                {language === 'vi' ? 'Đang lưu...' : 'Saving...'}
              </>
            ) : (
              <>
                <span className="mr-2">✅</span>
                {language === 'vi' ? 'Lưu thay đổi' : 'Save Changes'}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EditCrewCertificateModal;
