import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import api from '../../services/api';

// Common certificate names (28+ options)
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

const AddCrewCertificateModal = ({ 
  onClose, 
  onSuccess,
  onBatchUpload,
  selectedShip, 
  ships, 
  preSelectedCrew = null,
  preSelectedCrewName = null,
  allCrewList = []
}) => {
  const { language, user } = useAuth();
  const fileInputRef = useRef(null);
  
  // State
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzedData, setAnalyzedData] = useState(null);
  const [crewList, setCrewList] = useState([]);
  const [isLoadingCrew, setIsLoadingCrew] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [customCertNames, setCustomCertNames] = useState([]);
  const [customCertInput, setCustomCertInput] = useState('');
  const [showWarningModal, setShowWarningModal] = useState(false);
  const [warningMessage, setWarningMessage] = useState('');
  const [highlightCrewSection, setHighlightCrewSection] = useState(false);
  
  // Form data
  const [formData, setFormData] = useState({
    crew_id: preSelectedCrew?.id || '',
    crew_name: preSelectedCrew?.full_name || '',
    crew_name_en: preSelectedCrew?.full_name_en || '',
    passport: preSelectedCrew?.passport || '',
    rank: preSelectedCrew?.rank || '',
    date_of_birth: preSelectedCrew?.date_of_birth || '',
    cert_name: '',
    cert_no: '',
    issued_by: '',
    issued_date: '',
    cert_expiry: '',
    note: ''
  });

  // Fetch crew list on mount
  useEffect(() => {
    if (allCrewList && allCrewList.length > 0) {
      // Use passed crew list
      console.log('Setting crew list from props:', allCrewList.length, 'crew members');
      setCrewList(allCrewList);
    } else {
      // Fetch crew list if not provided
      fetchCrewList();
    }
    loadCustomCertNames();
  }, [allCrewList]);

  // Pre-select crew after crew list is loaded
  useEffect(() => {
    if (preSelectedCrewName && crewList.length > 0 && !formData.crew_id) {
      console.log('Attempting to pre-select crew:', preSelectedCrewName);
      const crew = crewList.find(c => c.full_name === preSelectedCrewName);
      if (crew) {
        console.log('Found crew to pre-select:', crew);
        setFormData(prev => ({
          ...prev,
          crew_id: crew.id,
          crew_name: crew.full_name,
          crew_name_en: crew.full_name_en || '',
          passport: crew.passport,
          rank: crew.rank || '',
          date_of_birth: crew.date_of_birth || ''
        }));
      } else {
        console.log('Crew not found in list');
      }
    }
  }, [preSelectedCrewName, crewList]);

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

  const fetchCrewList = async () => {
    try {
      setIsLoadingCrew(true);
      const response = await api.get('/api/crew');
      setCrewList(response.data || []);
    } catch (error) {
      console.error('Failed to fetch crew list:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách thuyền viên' : 'Failed to load crew list');
    } finally {
      setIsLoadingCrew(false);
    }
  };

  // Handle file drop/select
  const handleFileChange = async (e) => {
    const files = Array.from(e.target.files || []);
    
    if (files.length === 0) return;
    
    // Multiple files - trigger batch upload
    if (files.length > 1) {
      // Check if crew is selected (required for batch upload)
      if (!formData.crew_id) {
        setWarningMessage(language === 'vi' 
          ? 'Vui lòng chọn thuyền viên trước khi upload nhiều file' 
          : 'Please select crew member before batch upload');
        setShowWarningModal(true);
        setHighlightCrewSection(true);
        // Clear file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        return;
      }
      
      if (onBatchUpload) {
        // Pass the pre-selected crew ID if available
        const preSelectedCrewId = formData.crew_id || null;
        onBatchUpload(files, preSelectedCrewId);
      }
    } else {
      // Single file - normal flow
      const file = files[0];
      await handleFileUpload(file);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files || []);
    
    if (files.length === 0) return;
    
    // Multiple files - trigger batch upload
    if (files.length > 1) {
      // Check if crew is selected (required for batch upload)
      if (!formData.crew_id) {
        setWarningMessage(language === 'vi' 
          ? 'Vui lòng chọn thuyền viên trước khi upload nhiều file' 
          : 'Please select crew member before batch upload');
        setShowWarningModal(true);
        setHighlightCrewSection(true);
        return;
      }
      
      if (onBatchUpload) {
        // Pass the pre-selected crew ID if available
        const preSelectedCrewId = formData.crew_id || null;
        onBatchUpload(files, preSelectedCrewId);
      }
    } else {
      // Single file - normal flow
      const file = files[0];
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
    
    // Auto-analyze if crew is selected
    if (formData.crew_id) {
      await analyzeFile(file);
    } else {
      // Show modal warning instead of toast
      setWarningMessage(language === 'vi' 
        ? 'Vui lòng chọn thuyền viên trước khi phân tích file' 
        : 'Please select crew member before analyzing file');
      setShowWarningModal(true);
    }
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setAnalyzedData(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const analyzeFile = async (file) => {
    if (!formData.crew_id) {
      setWarningMessage(language === 'vi' 
        ? 'Vui lòng chọn thuyền viên trước khi phân tích file' 
        : 'Please select crew member before analyzing file');
      setShowWarningModal(true);
      return;
    }

    if (!selectedShip) {
      setWarningMessage(language === 'vi' 
        ? 'Vui lòng chọn tàu trước khi phân tích file' 
        : 'Please select ship before analyzing file');
      setShowWarningModal(true);
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
        timeout: 120000 // 2 minutes
      });

      const data = response.data || response;
      
      console.log('=== API Response from analyze-file ===');
      console.log('Full response:', data);
      console.log('data.success:', data.success);
      console.log('data.analysis:', data.analysis);
      console.log('JSON.stringify(data.analysis):', JSON.stringify(data.analysis, null, 2));
      console.log('=====================================');

      // Check if analysis succeeded
      if (data.success && data.analysis) {
        processAnalysisSuccess(data.analysis);
      } else {
        console.log('⚠️ Analysis failed or no analysis data');
        toast.warning(language === 'vi' 
          ? '⚠️ Không thể phân tích file. Vui lòng nhập thủ công.'
          : '⚠️ Cannot analyze file. Please enter manually.');
      }

    } catch (error) {
      console.error('AI analysis error:', error);
      
      // Handle name mismatch error
      const errorDetail = error.response?.data?.detail;
      const errorStatus = error.response?.status;
      
      if (errorStatus === 400 && errorDetail) {
        const detailStr = typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail);
        
        if (detailStr.includes('Certificate holder name')) {
          toast.error(
            <div>
              <p className="font-bold">{language === 'vi' ? '⚠️ Tên không khớp' : '⚠️ Name Mismatch'}</p>
              <p className="text-sm">{detailStr}</p>
            </div>,
            { duration: 6000 }
          );
        } else {
          toast.error(language === 'vi' 
            ? `❌ Lỗi phân tích file: ${detailStr}` 
            : `❌ Analysis failed: ${detailStr}`);
        }
      } else {
        toast.error(language === 'vi' 
          ? '❌ Lỗi phân tích file. Vui lòng nhập thủ công.'
          : '❌ Analysis failed. Please enter manually.');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const processAnalysisSuccess = (analysis) => {
    // Store complete analysis data
    setAnalyzedData(analysis);
    
    console.log('=== Certificate AI Analysis Result ===');
    console.log('Full analysis object:', analysis);
    console.log('cert_name:', analysis.cert_name);
    console.log('cert_no:', analysis.cert_no);
    console.log('issued_by:', analysis.issued_by);
    console.log('issued_date:', analysis.issued_date);
    console.log('expiry_date:', analysis.expiry_date);
    console.log('cert_expiry:', analysis.cert_expiry);
    console.log('rank:', analysis.rank);
    console.log('note:', analysis.note);
    console.log('======================================');

    // Auto-populate form fields
    setFormData(prev => {
      const newData = {
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
        rank: analysis.rank || prev.rank,
        note: analysis.note || prev.note  // ✅ ADDED: Auto-fill note field
      };
      
      console.log('=== Form Data After Update ===');
      console.log('New form data:', newData);
      console.log('==============================');
      
      return newData;
    });

    toast.success(language === 'vi' 
      ? '✅ Phân tích AI thành công!' 
      : '✅ AI analysis successful!');
  };

  // Handle crew selection
  const handleCrewSelect = (crewId) => {
    const crew = crewList.find(c => c.id === crewId);
    if (crew) {
      setFormData(prev => ({
        ...prev,
        crew_id: crew.id,
        crew_name: crew.full_name,
        crew_name_en: crew.full_name_en || '',
        passport: crew.passport,
        rank: crew.rank || '',
        date_of_birth: crew.date_of_birth || ''
      }));

      // Auto-analyze if file is already uploaded
      if (uploadedFile) {
        analyzeFile(uploadedFile);
      }
    }
  };

  // Handle form input change
  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Check duplicate
  const checkDuplicate = async () => {
    if (!formData.crew_id || !formData.cert_no) return null;

    try {
      const response = await api.post('/api/crew-certificates/check-duplicate', {
        crew_id: formData.crew_id,
        cert_no: formData.cert_no
      });

      return response.data;
    } catch (error) {
      console.error('Duplicate check error:', error);
      return null;
    }
  };

  // Handle submit
  const handleSubmit = async () => {
    // Validate required fields
    if (!formData.crew_id || !formData.crew_name || !formData.passport || 
        !formData.cert_name || !formData.cert_no) {
      toast.error(language === 'vi' 
        ? '❌ Vui lòng điền đầy đủ thông tin bắt buộc (*)' 
        : '❌ Please fill in all required fields (*)');
      return;
    }

    if (!selectedShip) {
      toast.error(language === 'vi' 
        ? '❌ Vui lòng chọn tàu' 
        : '❌ Please select a ship');
      return;
    }

    // Check duplicate
    const duplicateCheck = await checkDuplicate();
    if (duplicateCheck?.exists) {
      toast.error(language === 'vi' 
        ? `❌ Chứng chỉ đã tồn tại: ${duplicateCheck.existing_cert?.cert_name}` 
        : `❌ Certificate already exists: ${duplicateCheck.existing_cert?.cert_name}`);
      return;
    }

    try {
      setIsSubmitting(true);

      // Save custom cert name if new
      saveCustomCertName(formData.cert_name);

      // Create certificate
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

      const response = await api.post(`/api/crew-certificates/manual?ship_id=${selectedShip.id}`, certData);
      
      const createdCert = response.data;

      // Upload files if available (background)
      if (analyzedData?._file_content && createdCert?.id) {
        uploadFilesInBackground(createdCert.id);
      }

      toast.success(language === 'vi' 
        ? '✅ Thêm chứng chỉ thành công!' 
        : '✅ Certificate added successfully!');

      onSuccess?.();
      onClose();

    } catch (error) {
      console.error('Submit error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      toast.error(language === 'vi' 
        ? `❌ Không thể thêm chứng chỉ: ${errorMessage}` 
        : `❌ Failed to add certificate: ${errorMessage}`);
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
        ? '⚠️ Chứng chỉ đã tạo nhưng lỗi khi upload files' 
        : '⚠️ Certificate created but file upload failed');
    }
  };

  // Handle close warning modal with highlight effect
  const handleCloseWarningModal = () => {
    setShowWarningModal(false);
    
    // Highlight crew section if warning was about crew selection
    if (warningMessage.includes('thuyền viên') || warningMessage.includes('crew member')) {
      setHighlightCrewSection(true);
      
      // Auto-remove highlight after 5 seconds
      setTimeout(() => {
        setHighlightCrewSection(false);
      }, 5000);
    }
  };

  // Filter crew list based on selected ship
  const getFilteredCrewList = () => {
    console.log('getFilteredCrewList - selectedShip:', selectedShip?.name);
    console.log('Total crew list:', crewList.length);
    
    if (!selectedShip) {
      // If no ship selected, return all crew
      console.log('No ship selected, showing all crew');
      return crewList;
    }

    // Filter crew by selected ship ONLY (không bao gồm Standby)
    const filtered = crewList.filter(crew => {
      const crewShip = crew.ship_sign_on || '-';
      return crewShip === selectedShip.name;
    });
    
    console.log(`Filtered crew for ship ${selectedShip.name}:`, filtered.length);
    console.log('Filtered crew:', filtered.map(c => ({ name: c.full_name, ship: c.ship_sign_on })));
    
    return filtered;
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
          <div className="flex-1 mr-4">
            {/* Title on single line with crew info */}
            {(preSelectedCrew || formData.crew_id) ? (
              <h2 className="text-xl font-bold text-gray-800 flex items-center flex-wrap">
                <span className="mr-2">📜</span>
                {language === 'vi' ? 'Thêm chứng chỉ cho' : 'Add Crew Certificate for'}
                <span className="ml-2 text-blue-700 uppercase">
                  {formData.rank && `${formData.rank} `}
                  {formData.crew_name}
                </span>
                {selectedShip && (
                  <span className="ml-2 text-green-700">
                    - {selectedShip.name}
                  </span>
                )}
              </h2>
            ) : (
              <h2 className="text-2xl font-bold text-gray-800 flex items-center">
                <span className="mr-2">📜</span>
                {language === 'vi' ? 'Thêm chứng chỉ thuyền viên' : 'Add Crew Certificate'}
              </h2>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1">
          <div className="space-y-6">
            {/* Section 1: AI Certificate Analysis */}
            <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-blue-800 mb-3 flex items-center">
                <span className="mr-2">📄</span>
                {language === 'vi' ? 'Phân tích từ chứng chỉ (AI)' : 'From Certificate File (AI Analysis)'}
              </h3>
              
              {/* Drag and drop area */}
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
                  uploadedFile 
                    ? 'border-green-400 bg-green-50' 
                    : 'border-blue-300 bg-white hover:border-blue-500 hover:bg-blue-50'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  multiple
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
                        ? 'Kéo thả file hoặc click để chọn' 
                        : 'Drag & drop file or click to select'}
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      {language === 'vi' 
                        ? 'Hỗ trợ: PDF, JPG, PNG (tối đa 10MB/file)' 
                        : 'Supports: PDF, JPG, PNG (max 10MB/file)'}
                    </p>
                    <p className="text-blue-500 text-xs mt-1">
                      {language === 'vi' 
                        ? '💡 1 file: Xem trước | Nhiều files: Xử lý hàng loạt (tối đa 10 files)' 
                        : '💡 1 file: Preview | Multiple files: Batch process (max 10 files)'}
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
                    {language === 'vi' ? 'AI phân tích thành công! Thông tin đã được tự động điền.' : 'AI analysis successful! Information auto-filled.'}
                  </p>
                </div>
              )}
            </div>

            {/* Section 2: Crew Selection (if not pre-selected from filter or props) */}
            {!preSelectedCrew && !preSelectedCrewName && !formData.crew_id && (
              <div className={`rounded-lg p-4 transition-all duration-300 ${
                highlightCrewSection 
                  ? 'border-4 border-orange-500 bg-orange-50 animate-pulse' 
                  : 'border border-gray-200'
              }`}>
                <h3 className={`text-lg font-semibold mb-3 flex items-center ${
                  highlightCrewSection ? 'text-orange-600' : 'text-gray-800'
                }`}>
                  <span className="mr-2">👤</span>
                  {language === 'vi' ? 'Chọn thuyền viên' : 'Select Crew Member'}
                  <span className="text-red-500 ml-1">*</span>
                </h3>
                
                <select
                  value={formData.crew_id}
                  onChange={(e) => {
                    handleCrewSelect(e.target.value);
                    // Remove highlight when crew is selected
                    if (e.target.value) {
                      setHighlightCrewSection(false);
                    }
                  }}
                  className={`w-full px-3 py-2 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    highlightCrewSection 
                      ? 'border-2 border-orange-500' 
                      : 'border border-gray-300'
                  }`}
                  disabled={isLoadingCrew}
                >
                  <option value="">{language === 'vi' ? '-- Chọn thuyền viên --' : '-- Select crew member --'}</option>
                  {getFilteredCrewList().map(crew => (
                    <option key={crew.id} value={crew.id}>
                      {crew.full_name.toUpperCase()} - {crew.passport} - {crew.rank || 'N/A'}
                    </option>
                  ))}
                </select>

                {/* Ship filter info */}
                {selectedShip && (
                  <p className="mt-2 text-xs text-gray-500">
                    {language === 'vi' 
                      ? `Hiển thị thuyền viên trên tàu: ${selectedShip.name}` 
                      : `Showing crew on ship: ${selectedShip.name}`}
                  </p>
                )}

                {formData.crew_id && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-md">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-600">{language === 'vi' ? 'Tên:' : 'Name:'}</span>
                        <span className="ml-2 font-medium">{formData.crew_name}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">{language === 'vi' ? 'Hộ chiếu:' : 'Passport:'}</span>
                        <span className="ml-2 font-medium">{formData.passport}</span>
                      </div>
                      {formData.rank && (
                        <div>
                          <span className="text-gray-600">{language === 'vi' ? 'Chức danh:' : 'Rank:'}</span>
                          <span className="ml-2 font-medium">{formData.rank}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Section 3: Certificate Details */}
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
                    placeholder={language === 'vi' ? 'Nhập ghi chú (tùy chọn)' : 'Enter note (optional)'}
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
            disabled={isSubmitting || !formData.crew_id || !formData.cert_name || !formData.cert_no}
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
                {language === 'vi' ? 'Thêm chứng chỉ' : 'Add Certificate'}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Warning Modal */}
      {showWarningModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            {/* Header */}
            <div className="p-6 border-b border-gray-200 bg-yellow-50">
              <h3 className="text-xl font-bold text-gray-800 flex items-center">
                <span className="text-2xl mr-2">⚠️</span>
                {language === 'vi' ? 'Cảnh báo' : 'Warning'}
              </h3>
            </div>

            {/* Content */}
            <div className="p-6">
              <p className="text-gray-700 text-center text-lg">
                {warningMessage}
              </p>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-gray-200 bg-gray-50 flex justify-center">
              <button
                onClick={handleCloseWarningModal}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
              >
                {language === 'vi' ? 'Đã hiểu' : 'OK'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AddCrewCertificateModal;
