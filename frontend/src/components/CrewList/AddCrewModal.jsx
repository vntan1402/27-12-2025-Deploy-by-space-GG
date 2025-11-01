import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { crewService } from '../../services/crewService';
import { autoFillEnglishField } from '../../utils/vietnameseHelpers';

export const AddCrewModal = ({ 
  selectedShip,
  onClose, 
  onSuccess 
}) => {
  const { language, user } = useAuth();
  
  // Form state
  const [formData, setFormData] = useState({
    full_name: '',
    full_name_en: '',
    sex: 'M',
    date_of_birth: '',
    place_of_birth: '',
    place_of_birth_en: '',
    passport: '',
    nationality: '',
    passport_expiry_date: '',
    rank: '',
    seamen_book: '',
    status: selectedShip ? 'Sign on' : 'Standby',
    ship_sign_on: selectedShip?.name || '-',
    place_sign_on: '',
    date_sign_on: '',
    date_sign_off: ''
  });
  
  // File upload states
  const [uploadedFile, setUploadedFile] = useState(null);
  const [analyzedData, setAnalyzedData] = useState(null); // Store complete analysis result
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Reset form when modal closes
  useEffect(() => {
    return () => {
      handleRemoveFile();
      setFormData({
        full_name: '',
        full_name_en: '',
        sex: 'M',
        date_of_birth: '',
        place_of_birth: '',
        place_of_birth_en: '',
        passport: '',
        nationality: '',
        passport_expiry_date: '',
        rank: '',
        seamen_book: '',
        status: selectedShip ? 'Sign on' : 'Standby',
        ship_sign_on: selectedShip?.name || '-',
        place_sign_on: '',
        date_sign_on: '',
        date_sign_off: ''
      });
    };
  }, []);
  
  // Update ship_sign_on when selectedShip changes
  useEffect(() => {
    if (selectedShip && formData.status !== 'Standby') {
      setFormData(prev => ({
        ...prev,
        ship_sign_on: selectedShip.name,
        status: 'Sign on'
      }));
    }
  }, [selectedShip]);
  
  // Handle file selection
  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (file) {
      await handleFileUpload(file);
    }
  };
  
  // Handle drag and drop
  const handleDrop = async (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('border-blue-400', 'bg-blue-100');
    
    const file = e.dataTransfer.files?.[0];
    if (file) {
      await handleFileUpload(file);
    }
  };
  
  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('border-blue-400', 'bg-blue-100');
  };
  
  const handleDragLeave = (e) => {
    e.currentTarget.classList.remove('border-blue-400', 'bg-blue-100');
  };
  
  // File upload and AI analysis
  const handleFileUpload = async (file) => {
    // Validate file
    const isValidType = file.type === 'application/pdf' || file.type.startsWith('image/');
    const isValidSize = file.size <= 10 * 1024 * 1024; // 10MB
    
    if (!isValidType) {
      toast.error(language === 'vi' 
        ? 'File không đúng định dạng. Chỉ hỗ trợ PDF, JPG, PNG'
        : 'Invalid file format. Only PDF, JPG, PNG are supported');
      return;
    }
    
    if (!isValidSize) {
      toast.error(language === 'vi' 
        ? 'File quá lớn. Kích thước tối đa 10MB'
        : 'File too large. Maximum size is 10MB');
      return;
    }
    
    setUploadedFile(file);
    await analyzeFile(file);
  };
  
  // Remove file
  const handleRemoveFile = () => {
    setUploadedFile(null);
    setAnalyzedData(null);
    setIsAnalyzing(false);
    
    // Reset form to initial state
    setFormData({
      full_name: '',
      full_name_en: '',
      sex: 'M',
      date_of_birth: '',
      place_of_birth: '',
      place_of_birth_en: '',
      passport: '',
      nationality: '',
      passport_expiry_date: '',
      rank: '',
      seamen_book: '',
      status: selectedShip ? 'Sign on' : 'Standby',
      ship_sign_on: selectedShip?.name || '-',
      place_sign_on: '',
      date_sign_on: '',
      date_sign_off: ''
    });
  };
  
  // AI Analysis
  const analyzeFile = async (file) => {
    try {
      setIsAnalyzing(true);
      toast.info(language === 'vi' ? '🤖 Đang phân tích hộ chiếu với AI...' : '🤖 Analyzing passport with AI...');
      
      const shipName = formData.status === 'Standby' ? '-' : (selectedShip?.name || '-');
      
      // Call backend analyze endpoint
      const response = await crewService.analyzePassport(file, shipName);
      
      const data = response.data || response;
      
      // Check for duplicate
      if (data.duplicate) {
        toast.error(
          language === 'vi' 
            ? `❌ Hộ chiếu ${data.existing_crew?.passport} đã tồn tại cho thuyền viên: ${data.existing_crew?.full_name}`
            : `❌ Passport ${data.existing_crew?.passport} already exists for crew: ${data.existing_crew?.full_name}`
        );
        handleRemoveFile();
        return;
      }
      
      // Check if analysis succeeded
      if (data.success && data.analysis) {
        processAnalysisSuccess(data.analysis);
      } else {
        toast.warning(language === 'vi' 
          ? '⚠️ Không thể phân tích file. Vui lòng nhập thủ công.'
          : '⚠️ Cannot analyze file. Please enter manually.');
      }
      
    } catch (error) {
      console.error('AI analysis error:', error);
      toast.error(language === 'vi' 
        ? '❌ Lỗi phân tích file. Vui lòng nhập thủ công.'
        : '❌ Analysis failed. Please enter manually.');
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  // Process successful analysis
  const processAnalysisSuccess = (analysis) => {
    // Store complete analysis data (including _file_content, _summary_text)
    setAnalyzedData(analysis);
    
    console.log('Analysis result:', analysis); // Debug log
    
    // Extract Vietnamese fields
    const vietnameseFullName = analysis.full_name || '';
    const vietnamesePlaceOfBirth = analysis.place_of_birth || '';
    
    // Auto-populate form fields with correct mapping
    setFormData(prev => ({
      ...prev,
      full_name: vietnameseFullName,
      // Auto-fill English name: use AI result if available, otherwise remove diacritics from Vietnamese
      full_name_en: analysis.full_name_en || autoFillEnglishField(vietnameseFullName),
      sex: analysis.sex || prev.sex,
      date_of_birth: analysis.date_of_birth ? 
        (analysis.date_of_birth.includes('/') ? 
          // Convert DD/MM/YYYY to YYYY-MM-DD
          analysis.date_of_birth.split('/').reverse().join('-') : 
          analysis.date_of_birth.split('T')[0]
        ) : prev.date_of_birth,
      place_of_birth: vietnamesePlaceOfBirth,
      // Auto-fill English place: use AI result if available, otherwise remove diacritics from Vietnamese
      place_of_birth_en: analysis.place_of_birth_en || autoFillEnglishField(vietnamesePlaceOfBirth),
      passport: analysis.passport_number || analysis.passport || prev.passport,
      nationality: analysis.nationality || prev.nationality,
      passport_expiry_date: analysis.passport_expiry_date || analysis.expiry_date ? 
        (analysis.passport_expiry_date?.includes('/') ? 
          // Convert DD/MM/YYYY to YYYY-MM-DD
          (analysis.passport_expiry_date || analysis.expiry_date).split('/').reverse().join('-') : 
          (analysis.passport_expiry_date || analysis.expiry_date).split('T')[0]
        ) : prev.passport_expiry_date
    }));
    
    toast.success(language === 'vi' 
      ? '✅ Hộ chiếu đã được phân tích thành công!'
      : '✅ Passport analyzed successfully!');
  };
  
  // Handle form submit
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate required fields
    if (!formData.full_name || !formData.date_of_birth || !formData.place_of_birth || !formData.passport) {
      toast.error(language === 'vi' 
        ? 'Vui lòng điền đầy đủ các trường bắt buộc!'
        : 'Please fill in all required fields!');
      return;
    }
    
    try {
      setIsSubmitting(true);
      
      // Create crew member
      const createData = {
        ...formData,
        // Remove empty optional fields
        full_name_en: formData.full_name_en || undefined,
        place_of_birth_en: formData.place_of_birth_en || undefined,
        nationality: formData.nationality || undefined,
        passport_expiry_date: formData.passport_expiry_date || undefined,
        rank: formData.rank || undefined,
        seamen_book: formData.seamen_book || undefined,
        place_sign_on: formData.place_sign_on || undefined,
        date_sign_on: formData.date_sign_on || undefined,
        date_sign_off: formData.date_sign_off || undefined
      };
      
      const response = await crewService.createCrew(createData);
      const crewId = response.data.id;
      
      toast.success(language === 'vi' 
        ? 'Thuyền viên đã được thêm thành công!'
        : 'Crew member added successfully!');
      
      // Upload passport files in background (if file was analyzed)
      if (analyzedData?._file_content) {
        // Don't await - let it run in background
        crewService.uploadPassportFiles(crewId, {
          file_content: analyzedData._file_content,
          filename: analyzedData._filename,
          content_type: analyzedData._content_type,
          summary_text: analyzedData._summary_text || '',
          ship_name: formData.ship_sign_on
        }).then(() => {
          toast.success(language === 'vi' 
            ? '✅ File hộ chiếu đã được upload lên Drive'
            : '✅ Passport files uploaded to Drive');
        }).catch((error) => {
          console.error('File upload error:', error);
          toast.warning(language === 'vi' 
            ? '⚠️ Thêm thuyền viên thành công nhưng không thể upload file lên Drive'
            : '⚠️ Crew added successfully but file upload to Drive failed');
        });
      }
      
      // Close modal and refresh
      onSuccess(crewId);
      onClose();
      
    } catch (error) {
      console.error('Error adding crew member:', error);
      
      if (error.response?.status === 400 && error.response?.data?.detail?.includes('already exists')) {
        toast.error(language === 'vi' 
          ? 'Số hộ chiếu này đã tồn tại trong hệ thống!'
          : 'This passport number already exists in the system!');
      } else {
        toast.error(language === 'vi' 
          ? `Lỗi khi thêm thuyền viên: ${error.response?.data?.detail || error.message}`
          : `Error adding crew member: ${error.response?.data?.detail || error.message}`);
      }
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Handle status change
  const handleStatusChange = (newStatus) => {
    setFormData(prev => ({
      ...prev,
      status: newStatus,
      ship_sign_on: newStatus === 'Standby' ? '-' : (selectedShip?.name || '-')
    }));
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <h3 className="text-xl font-bold text-gray-800">
                {language === 'vi' ? 'Thêm thuyền viên mới' : 'Add New Crew Member'}
              </h3>
              {formData.status === 'Standby' ? (
                <span className="text-lg font-medium text-orange-600">
                  {language === 'vi' ? 'cho:' : 'for:'} <span className="font-bold">Standby Crew</span>
                </span>
              ) : selectedShip ? (
                <span className="text-lg font-medium text-gray-800">
                  {language === 'vi' ? 'cho:' : 'for:'} <span className="font-bold text-blue-600">{selectedShip.name}</span>
                </span>
              ) : null}
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Standby Mode Toggle */}
              <button
                type="button"
                onClick={() => handleStatusChange(formData.status === 'Standby' ? 'Sign on' : 'Standby')}
                className={`px-4 py-2 rounded-lg font-medium text-sm transition-all flex items-center space-x-2 border-2 ${
                  formData.status === 'Standby'
                    ? 'bg-orange-100 text-orange-800 border-orange-300 hover:bg-orange-200'
                    : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'
                }`}
                title={formData.status === 'Standby' 
                  ? (language === 'vi' ? 'Chuyển sang chế độ thường' : 'Switch to normal mode')
                  : (language === 'vi' ? 'Chuyển sang Standby Mode' : 'Switch to Standby Mode')
                }
              >
                <span>{formData.status === 'Standby' ? '🟠' : '⚪'}</span>
                <span>{language === 'vi' ? 'Standby Crew' : 'Standby Crew'}</span>
              </button>
              
              {/* Close Button */}
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
              >
                ×
              </button>
            </div>
          </div>
        </div>
        
        {/* Body */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)] space-y-6">
          
          {/* AI Passport Analysis Section */}
          <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-lg font-semibold text-blue-800 flex items-center">
                <span className="mr-2">📄</span>
                {language === 'vi' ? 'Phân tích từ hộ chiếu (AI)' : 'From Passport (AI Analysis)'}
              </h4>
              <p className="text-sm text-blue-700 ml-4">
                {language === 'vi' 
                  ? 'Tải lên file hộ chiếu để tự động phân tích và điền thông tin thuyền viên'
                  : 'Upload passport file to automatically analyze and fill crew information'
                }
              </p>
            </div>
            
            {!uploadedFile ? (
              <div className="space-y-3">
                {/* Drag & Drop Area */}
                <div 
                  className={`border-2 border-dashed border-blue-300 rounded-lg p-8 hover:border-blue-400 transition-all relative ${
                    isAnalyzing ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'
                  }`}
                  onClick={() => !isAnalyzing && document.getElementById('passport-upload').click()}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  {!isAnalyzing ? (
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="text-blue-700 font-medium text-left">
                          {language === 'vi' ? 'Kéo thả file hoặc click để chọn' : 'Drag & drop file or click to select'}
                        </p>
                        <p className="text-blue-600 text-sm text-left mt-1">
                          {language === 'vi' ? 'Hỗ trợ: PDF, JPG, PNG (tối đa 10MB)' : 'Supports: PDF, JPG, PNG (max 10MB)'}
                        </p>
                      </div>
                      <div className="flex-shrink-0 ml-4">
                        <div className="text-blue-500 text-4xl">📁</div>
                      </div>
                    </div>
                  ) : (
                    /* Analyzing Overlay with Enhanced Spinner */
                    <div className="flex flex-col items-center justify-center py-4">
                      <div className="relative">
                        {/* Outer spinning ring */}
                        <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600"></div>
                        {/* Inner pulsing circle */}
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="animate-pulse h-8 w-8 bg-blue-500 rounded-full opacity-75"></div>
                        </div>
                      </div>
                      <p className="text-blue-800 font-bold text-lg mt-4">
                        {language === 'vi' ? '🤖 Đang phân tích hộ chiếu với AI...' : '🤖 Analyzing passport with AI...'}
                      </p>
                      <p className="text-blue-600 text-sm mt-2">
                        {language === 'vi' ? 'Vui lòng đợi, quá trình này có thể mất 20-30 giây' : 'Please wait, this may take 20-30 seconds'}
                      </p>
                      <div className="flex items-center space-x-1 mt-3">
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                    </div>
                  )}
                </div>
                
                <input
                  id="passport-upload"
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={handleFileSelect}
                  className="hidden"
                  disabled={isAnalyzing}
                />
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center space-x-2 text-green-700">
                  <span>✅</span>
                  <span className="font-medium">
                    {language === 'vi' ? 'Hộ chiếu đã được phân tích thành công' : 'Passport analyzed successfully'}
                  </span>
                </div>
                <div className="bg-white p-4 rounded-lg border border-green-200">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <p><strong>{language === 'vi' ? 'File:' : 'File:'}</strong> {uploadedFile.name}</p>
                    <p><strong>{language === 'vi' ? 'Kích thước:' : 'Size:'}</strong> {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                    {analyzedData && (
                      <>
                        <p><strong>{language === 'vi' ? 'Tên:' : 'Name:'}</strong> {analyzedData.full_name || 'N/A'}</p>
                        <p><strong>{language === 'vi' ? 'Hộ chiếu:' : 'Passport:'}</strong> {analyzedData.passport_number || 'N/A'}</p>
                      </>
                    )}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleRemoveFile}
                  className="text-sm text-red-600 hover:text-red-800 flex items-center space-x-1"
                >
                  <span>🗑️</span>
                  <span>{language === 'vi' ? 'Xóa và tải lại' : 'Remove and re-upload'}</span>
                </button>
              </div>
            )}
          </div>
          
          {/* Manual Entry Form */}
          <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
            <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              <span className="mr-2">✏️</span>
              {language === 'vi' ? 'Thông tin thuyền viên (Nhập thủ công)' : 'Crew Information (Manual Entry)'}
            </h4>
            
            <p className="text-sm text-gray-600 mb-4">
              {language === 'vi' 
                ? 'Điền thông tin thuyền viên hoặc chỉnh sửa thông tin đã được phân tích từ hộ chiếu ở trên'
                : 'Fill in crew information or edit the information analyzed from passport above'
              }
            </p>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Row 1: Full Name */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Họ tên (Tiếng Việt)' : 'Full Name (Vietnamese)'} <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Họ tên (Tiếng Anh)' : 'Full Name (English)'}
                  </label>
                  <input
                    type="text"
                    value={formData.full_name_en}
                    onChange={(e) => setFormData({...formData, full_name_en: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              {/* Row 2: Sex, Date of Birth */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Giới tính' : 'Sex'}
                  </label>
                  <select
                    value={formData.sex}
                    onChange={(e) => setFormData({...formData, sex: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="M">M</option>
                    <option value="F">F</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Ngày sinh' : 'Date of Birth'} <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={formData.date_of_birth}
                    onChange={(e) => setFormData({...formData, date_of_birth: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
              </div>
              
              {/* Row 3: Place of Birth */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Nơi sinh (Tiếng Việt)' : 'Place of Birth (Vietnamese)'} <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.place_of_birth}
                    onChange={(e) => setFormData({...formData, place_of_birth: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Nơi sinh (Tiếng Anh)' : 'Place of Birth (English)'}
                  </label>
                  <input
                    type="text"
                    value={formData.place_of_birth_en}
                    onChange={(e) => setFormData({...formData, place_of_birth_en: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              {/* Row 4: Passport, Nationality */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Hộ chiếu' : 'Passport'} <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.passport}
                    onChange={(e) => setFormData({...formData, passport: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Quốc t적' : 'Nationality'}
                  </label>
                  <input
                    type="text"
                    value={formData.nationality}
                    onChange={(e) => setFormData({...formData, nationality: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              {/* Row 5: Passport Expiry Date, Rank */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Ngày hết hạn hộ chiếu' : 'Passport Expiry Date'}
                  </label>
                  <input
                    type="date"
                    value={formData.passport_expiry_date}
                    onChange={(e) => setFormData({...formData, passport_expiry_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Chức vụ' : 'Rank'}
                  </label>
                  <input
                    type="text"
                    value={formData.rank}
                    onChange={(e) => setFormData({...formData, rank: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="CE, 2/E, C/O, Master..."
                  />
                </div>
              </div>
              
              {/* Row 6: Seamen Book, Status */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Sổ thuyền viên' : 'Seamen Book'}
                  </label>
                  <input
                    type="text"
                    value={formData.seamen_book}
                    onChange={(e) => setFormData({...formData, seamen_book: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Trạng thái' : 'Status'}
                  </label>
                  <select
                    value={formData.status}
                    onChange={(e) => handleStatusChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="Sign on">{language === 'vi' ? 'Đang làm việc' : 'Sign on'}</option>
                    <option value="Standby">{language === 'vi' ? 'Chờ' : 'Standby'}</option>
                    <option value="Leave">{language === 'vi' ? 'Nghỉ phép' : 'Leave'}</option>
                  </select>
                </div>
              </div>
              
              {/* Row 7: Ship Sign On, Place Sign On */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Tàu đăng ký' : 'Ship Sign On'}
                  </label>
                  <input
                    type="text"
                    value={formData.ship_sign_on}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 cursor-not-allowed"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Nơi xuống tàu' : 'Place Sign On'}
                  </label>
                  <input
                    type="text"
                    value={formData.place_sign_on}
                    onChange={(e) => setFormData({...formData, place_sign_on: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              {/* Row 8: Date Sign On, Date Sign Off */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Ngày xuống tàu' : 'Date Sign On'}
                  </label>
                  <input
                    type="date"
                    value={formData.date_sign_on}
                    onChange={(e) => setFormData({...formData, date_sign_on: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Ngày rời tàu' : 'Date Sign Off'}
                  </label>
                  <input
                    type="date"
                    value={formData.date_sign_off}
                    onChange={(e) => setFormData({...formData, date_sign_off: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              {/* Submit Buttons */}
              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                  disabled={isSubmitting}
                >
                  {language === 'vi' ? 'Hủy' : 'Cancel'}
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>{language === 'vi' ? 'Đang xử lý...' : 'Processing...'}</span>
                    </>
                  ) : (
                    <>
                      <span>👤</span>
                      <span>{language === 'vi' ? 'Thêm thuyền viên' : 'Add Crew'}</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
