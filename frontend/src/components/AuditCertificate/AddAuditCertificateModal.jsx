/**
 * Add Audit Certificate Modal - Full Featured
 * With AI analysis, file upload, duplicate detection
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useUploadGuard } from '../../hooks/useUploadGuard';
import api from '../../services/api';

export const AddAuditCertificateModal = ({
  isOpen,
  onClose,
  onSave,
  onSuccess,
  selectedShip,
  language,
  aiConfig
}) => {
  const { isSoftwareExpired, checkAndWarn } = useUploadGuard();
  const [formData, setFormData] = useState({
    ship_id: selectedShip?.id || '',
    ship_name: '',  // AI sẽ fill giá trị này
    ship_imo: '',   // AI sẽ fill giá trị này
    cert_name: '',
    cert_abbreviation: '',
    cert_no: '',
    cert_type: 'Full Term',
    issue_date: '',
    valid_date: '',
    last_endorse: '',
    next_survey: '',
    next_survey_type: '',
    issued_by: '',
    issued_by_abbreviation: '',
    notes: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Single file upload state (for review before save)
  const [certificateFile, setCertificateFile] = useState(null);
  const [validationApproved, setValidationApproved] = useState(false); // Track if user approved validation warning
  
  // Error modal state
  const [errorModal, setErrorModal] = useState({
    show: false,
    type: '', // 'error', 'warning', 'manual_input'
    title: '',
    message: '',
    details: null
  });
  
  // Validation confirmation modal state
  const [validationModal, setValidationModal] = useState({
    show: false,
    message: '',
    overrideNote: '',
    onContinue: null,
    onCancel: null
  });
  
  // Duplicate confirmation modal state
  const [duplicateModal, setDuplicateModal] = useState({
    show: false,
    message: '',
    existingCert: null,
    onContinue: null,
    onCancel: null
  });
  
  // Category warning modal state (ISM/ISPS/MLC)
  const [categoryModal, setCategoryModal] = useState({
    show: false,
    message: '',
    certName: '',
    onContinue: null,
    onCancel: null
  });
  
  // Multi cert upload states
  const [isMultiCertProcessing, setIsMultiCertProcessing] = useState(false);
  const [multiCertUploads, setMultiCertUploads] = useState([]);
  const [uploadSummary, setUploadSummary] = useState({ success: 0, failed: 0, total: 0 });
  
  // Update ship_id when selectedShip changes (nhưng KHÔNG fill ship_name và ship_imo)
  useEffect(() => {
    if (selectedShip?.id) {
      setFormData(prev => ({ 
        ...prev, 
        ship_id: selectedShip.id
        // Không fill ship_name và ship_imo - để AI fill
      }));
    }
  }, [selectedShip?.id]);

  // Format date from analysis (DD/MM/YYYY to YYYY-MM-DD)
  const formatCertDate = (dateStr) => {
    if (!dateStr || typeof dateStr !== 'string') return '';
    
    // Handle DD/MM/YYYY format
    if (dateStr.includes('/')) {
      const parts = dateStr.split('/');
      if (parts.length === 3) {
        const [day, month, year] = parts;
        if (day && month && year && year.length === 4) {
          return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
        }
      }
    }
    
    // Handle YYYY-MM-DD format
    const isoPattern = /^\d{4}-\d{2}-\d{2}$/;
    if (isoPattern.test(dateStr.trim())) {
      return dateStr.trim();
    }
    
    // Handle ISO datetime
    if (dateStr.includes('T') || dateStr.includes('Z')) {
      const date = new Date(dateStr);
      if (!isNaN(date.getTime())) {
        const year = date.getUTCFullYear();
        const month = String(date.getUTCMonth() + 1).padStart(2, '0');
        const day = String(date.getUTCDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      }
    }
    
    return '';
  };
  
  // Date conversion helper (convert YYYY-MM-DD to UTC ISO string)
  const convertDateInputToUTC = (dateInput) => {
    if (!dateInput) return null;
    
    try {
      // Handle YYYY-MM-DD format
      const parts = dateInput.split('-');
      if (parts.length === 3) {
        const [year, month, day] = parts;
        const date = new Date(Date.UTC(parseInt(year), parseInt(month) - 1, parseInt(day)));
        return date.toISOString();
      }
      
      // Fallback to direct conversion
      const date = new Date(dateInput);
      if (!isNaN(date.getTime())) {
        return date.toISOString();
      }
      
      return null;
    } catch (error) {
      console.error('Date conversion error:', error);
      return null;
    }
  };
  
  // Handle multi cert upload with AI analysis
  const handleMultiCertUpload = async (files) => {
    // Check if software is expired before upload
    if (!checkAndWarn()) {
      return;
    }

    if (!selectedShip?.id) {
      toast.error(language === 'vi' 
        ? '❌ Vui lòng chọn tàu trước khi upload certificate'
        : '❌ Please select a ship before uploading certificate'
      );
      return;
    }

    if (!files || files.length === 0) return;

    const fileArray = Array.from(files);
    const totalFiles = fileArray.length;

    // **LOGIC MỚI: Phân biệt 1 file vs multi files**
    if (totalFiles === 1) {
      // ===== SINGLE FILE: Chỉ AI analysis + Auto-fill (không create DB) =====
      await handleSingleFileAnalysis(fileArray[0]);
    } else {
      // ===== MULTI FILES: Batch processing với auto-create DB records =====
      await handleMultiFileBatchUpload(fileArray, totalFiles);
    }
  };

  // Handle validation continue - user chose to proceed with warning
  const handleValidationContinue = (extractedInfo, file, overrideNote) => {
    // Auto-fill form with extracted data
    const cert_name = extractedInfo.cert_name || extractedInfo.certificate_name || '';
    const cert_no = extractedInfo.cert_no || extractedInfo.certificate_number || '';
    
    const autoFillData = {
      cert_name: cert_name,
      cert_abbreviation: extractedInfo.cert_abbreviation || '',
      cert_no: cert_no,
      cert_type: extractedInfo.cert_type || 'Full Term',
      issue_date: formatCertDate(extractedInfo.issue_date),
      valid_date: formatCertDate(extractedInfo.valid_date || extractedInfo.expiry_date),
      last_endorse: formatCertDate(extractedInfo.last_endorse),
      next_survey: formatCertDate(extractedInfo.next_survey),
      next_survey_type: extractedInfo.next_survey_type || '',
      issued_by: extractedInfo.issued_by || '',
      issued_by_abbreviation: extractedInfo.issued_by_abbreviation || '',
      ship_id: selectedShip.id,
      ship_name: extractedInfo.ship_name || '',  // Fill từ AI extraction
      ship_imo: extractedInfo.imo_number || '',  // Fill từ AI extraction
      notes: overrideNote  // Add the override note
    };

    const filledFields = Object.keys(autoFillData).filter(key => 
      autoFillData[key] && String(autoFillData[key]).trim() && !['ship_id', 'ship_name', 'notes'].includes(key)
    ).length;

    setFormData(prev => ({
      ...prev,
      ...autoFillData
    }));

    // Store file for later upload when user clicks Save
    setCertificateFile(file);
    
    // Mark validation as approved so submit won't reject it again
    setValidationApproved(true);

    // Close validation modal
    setValidationModal({ show: false, message: '', overrideNote: '', onContinue: null, onCancel: null });

    toast.success(language === 'vi' 
      ? `✅ Đã phân tích và điền ${filledFields} trường! Ghi chú tham khảo đã được thêm. Vui lòng review và click Save.`
      : `✅ Analyzed and filled ${filledFields} fields! Reference note added. Please review and click Save.`
    );
  };

  // Handle validation cancel - user chose not to proceed
  const handleValidationCancel = () => {
    // Close validation modal
    setValidationModal({ show: false, message: '', overrideNote: '', onContinue: null, onCancel: null });
    
    // Clear file and approval flag
    setCertificateFile(null);
    setValidationApproved(false);
    
    toast.info(language === 'vi' 
      ? 'ℹ️ Upload đã bị hủy'
      : 'ℹ️ Upload cancelled'
    );
  };

  // Handle duplicate continue - user chose to proceed despite duplicate
  const handleDuplicateContinue = (extractedInfo, file) => {
    // Auto-fill form with extracted data (no special note for duplicate)
    const cert_name = extractedInfo.cert_name || extractedInfo.certificate_name || '';
    const cert_no = extractedInfo.cert_no || extractedInfo.certificate_number || '';
    
    const autoFillData = {
      cert_name: cert_name,
      cert_abbreviation: extractedInfo.cert_abbreviation || '',
      cert_no: cert_no,
      cert_type: extractedInfo.cert_type || 'Full Term',
      issue_date: formatCertDate(extractedInfo.issue_date),
      valid_date: formatCertDate(extractedInfo.valid_date || extractedInfo.expiry_date),
      last_endorse: formatCertDate(extractedInfo.last_endorse),
      next_survey: formatCertDate(extractedInfo.next_survey),
      next_survey_type: extractedInfo.next_survey_type || '',
      issued_by: extractedInfo.issued_by || '',
      issued_by_abbreviation: extractedInfo.issued_by_abbreviation || '',
      ship_id: selectedShip.id,
      ship_name: extractedInfo.ship_name || '',  // Fill từ AI extraction
      ship_imo: extractedInfo.imo_number || ''   // Fill từ AI extraction
    };

    const filledFields = Object.keys(autoFillData).filter(key => 
      autoFillData[key] && String(autoFillData[key]).trim() && !['ship_id', 'ship_name'].includes(key)
    ).length;

    setFormData(prev => ({
      ...prev,
      ...autoFillData
    }));

    // Store file for later upload when user clicks Save
    setCertificateFile(file);
    
    // Mark validation as approved (to use override endpoint)
    setValidationApproved(true);

    // Close duplicate modal
    setDuplicateModal({ show: false, message: '', existingCert: null, onContinue: null, onCancel: null });

    toast.success(language === 'vi' 
      ? `✅ Đã phân tích và điền ${filledFields} trường! Vui lòng review và click Save.`
      : `✅ Analyzed and filled ${filledFields} fields! Please review and click Save.`
    );
  };

  // Handle duplicate cancel - user chose not to proceed
  const handleDuplicateCancel = () => {
    // Close duplicate modal
    setDuplicateModal({ show: false, message: '', existingCert: null, onContinue: null, onCancel: null });
    
    // Clear file and approval flag
    setCertificateFile(null);
    setValidationApproved(false);
    
    toast.info(language === 'vi' 
      ? 'ℹ️ Upload đã bị hủy'
      : 'ℹ️ Upload cancelled'
    );
  };

  // Handle category continue - user chose to proceed despite category mismatch
  const handleCategoryContinue = (extractedInfo, file) => {
    // Auto-fill form with extracted data (no special note for category)
    const cert_name = extractedInfo.cert_name || extractedInfo.certificate_name || '';
    const cert_no = extractedInfo.cert_no || extractedInfo.certificate_number || '';
    
    const autoFillData = {
      cert_name: cert_name,
      cert_abbreviation: extractedInfo.cert_abbreviation || '',
      cert_no: cert_no,
      cert_type: extractedInfo.cert_type || 'Full Term',
      issue_date: formatCertDate(extractedInfo.issue_date),
      valid_date: formatCertDate(extractedInfo.valid_date || extractedInfo.expiry_date),
      last_endorse: formatCertDate(extractedInfo.last_endorse),
      next_survey: formatCertDate(extractedInfo.next_survey),
      next_survey_type: extractedInfo.next_survey_type || '',
      issued_by: extractedInfo.issued_by || '',
      issued_by_abbreviation: extractedInfo.issued_by_abbreviation || '',
      ship_id: selectedShip.id,
      ship_name: extractedInfo.ship_name || '',
      ship_imo: extractedInfo.imo_number || ''
    };

    const filledFields = Object.keys(autoFillData).filter(key => 
      autoFillData[key] && String(autoFillData[key]).trim() && !['ship_id', 'ship_name', 'ship_imo'].includes(key)
    ).length;

    setFormData(prev => ({
      ...prev,
      ...autoFillData
    }));

    // Store file for later upload when user clicks Save
    setCertificateFile(file);
    
    // Mark validation as approved (to use override endpoint)
    setValidationApproved(true);

    // Close category modal
    setCategoryModal({ show: false, message: '', certName: '', onContinue: null, onCancel: null });

    toast.success(language === 'vi' 
      ? `✅ Đã phân tích và điền ${filledFields} trường! Vui lòng review và click Save.`
      : `✅ Analyzed and filled ${filledFields} fields! Please review and click Save.`
    );
  };

  // Handle category cancel - user chose not to proceed
  const handleCategoryCancel = () => {
    // Close category modal
    setCategoryModal({ show: false, message: '', certName: '', onContinue: null, onCancel: null });
    
    // Clear file and approval flag
    setCertificateFile(null);
    setValidationApproved(false);
    
    toast.info(language === 'vi' 
      ? 'ℹ️ Upload đã bị hủy'
      : 'ℹ️ Upload cancelled'
    );
  };

  // Handle single file: AI analysis only + Auto-fill form
  const handleSingleFileAnalysis = async (file) => {
    try {
      setIsMultiCertProcessing(true);
      
      toast.info(language === 'vi' 
        ? '🔍 Đang phân tích file với AI...'
        : '🔍 Analyzing file with AI...'
      );

      // Read file content
      const fileContent = await file.arrayBuffer();
      const base64Content = btoa(
        new Uint8Array(fileContent).reduce((data, byte) => data + String.fromCharCode(byte), '')
      );

      // Call AI analysis endpoint with ship_id for validation
      const response = await api.post('/api/audit-certificates/analyze-file', {
        file_content: base64Content,
        filename: file.name,
        content_type: file.type,
        ship_id: selectedShip.id  // Include ship_id for backend validation
      });

      if (response.data.success && response.data.extracted_info) {
        const extractedInfo = response.data.extracted_info;
        const validationWarning = response.data.validation_warning;
        const duplicateWarning = response.data.duplicate_warning;
        const categoryWarning = response.data.category_warning;
        
        // ===== CHECK FOR CATEGORY WARNING (ISM/ISPS/MLC) - FIRST PRIORITY =====
        if (categoryWarning && categoryWarning.type === 'category_mismatch') {
          // Show category confirmation modal
          setCategoryModal({
            show: true,
            message: categoryWarning.message,
            certName: categoryWarning.cert_name,
            onContinue: () => {
              // User chose to continue - proceed with category mismatch
              handleCategoryContinue(extractedInfo, file);
            },
            onCancel: () => {
              // User chose to cancel - clear everything
              handleCategoryCancel();
            }
          });
          return; // Wait for user choice
        }
        
        // ===== CHECK FOR SHIP VALIDATION WARNING =====
        if (validationWarning && validationWarning.type === 'imo_mismatch') {
          // Show validation confirmation modal instead of toast
          setValidationModal({
            show: true,
            message: validationWarning.message,
            overrideNote: validationWarning.override_note,
            extractedInfo: extractedInfo,
            file: file,
            onContinue: () => {
              // User chose to continue - add override note and proceed
              handleValidationContinue(extractedInfo, file, validationWarning.override_note);
            },
            onCancel: () => {
              // User chose to cancel - clear everything
              handleValidationCancel();
            }
          });
          return; // Wait for user choice
        }
        
        // ===== CHECK FOR DUPLICATE WARNING =====
        if (duplicateWarning && duplicateWarning.type === 'duplicate') {
          // Show duplicate confirmation modal
          setDuplicateModal({
            show: true,
            message: duplicateWarning.message,
            existingCert: duplicateWarning.existing_certificate,
            onContinue: () => {
              // User chose to continue - proceed with duplicate
              handleDuplicateContinue(extractedInfo, file);
            },
            onCancel: () => {
              // User chose to cancel - clear everything
              handleDuplicateCancel();
            }
          });
          return; // Wait for user choice
        }
        
        // ===== VALIDATE EXTRACTED INFO (CLIENT-SIDE CHECK) =====
        const cert_name = extractedInfo.cert_name || extractedInfo.certificate_name || '';
        const cert_no = extractedInfo.cert_no || extractedInfo.certificate_number || '';
        
        // Check if critical fields are missing
        const missingFields = [];
        if (!cert_name || !cert_name.trim()) {
          missingFields.push(language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name');
        }
        if (!cert_no || !cert_no.trim()) {
          missingFields.push(language === 'vi' ? 'Số chứng chỉ' : 'Certificate Number');
        }
        
        // If critical fields are missing, show error
        if (missingFields.length > 0) {
          toast.error(language === 'vi' 
            ? `❌ AI không thể trích xuất đủ thông tin:\n• ${missingFields.join('\n• ')}\n\nVui lòng kiểm tra chất lượng file và thử lại.`
            : `❌ AI could not extract required fields:\n• ${missingFields.join('\n• ')}\n\nPlease check file quality and try again.`
          , { duration: 6000 });
          
          console.warn('⚠️ Validation failed - Missing fields:', missingFields);
          console.log('Extracted info:', extractedInfo);
          return; // Don't auto-fill or store file
        }
        
        // Auto-fill form
        const autoFillData = {
          cert_name: cert_name,
          cert_abbreviation: extractedInfo.cert_abbreviation || '',
          cert_no: cert_no,
          cert_type: extractedInfo.cert_type || 'Full Term',
          issue_date: formatCertDate(extractedInfo.issue_date),
          valid_date: formatCertDate(extractedInfo.valid_date || extractedInfo.expiry_date),
          last_endorse: formatCertDate(extractedInfo.last_endorse),
          next_survey: formatCertDate(extractedInfo.next_survey),
          next_survey_type: extractedInfo.next_survey_type || '',
          issued_by: extractedInfo.issued_by || '',
          issued_by_abbreviation: extractedInfo.issued_by_abbreviation || '',
          ship_id: selectedShip.id,
          ship_name: extractedInfo.ship_name || '',  // Fill từ AI extraction
          ship_imo: extractedInfo.imo_number || ''   // Fill từ AI extraction
        };

        const filledFields = Object.keys(autoFillData).filter(key => 
          autoFillData[key] && String(autoFillData[key]).trim() && !['ship_id', 'ship_name', 'ship_imo'].includes(key)
        ).length;

        setFormData(prev => ({
          ...prev,
          ...autoFillData
        }));

        // Store file for later upload when user clicks Save
        setCertificateFile(file);

        toast.success(language === 'vi' 
          ? `✅ Đã phân tích và điền ${filledFields} trường! Vui lòng review và click Save.`
          : `✅ Analyzed and filled ${filledFields} fields! Please review and click Save.`
        );
      } else {
        toast.error(language === 'vi' 
          ? '❌ Không thể phân tích file'
          : '❌ Failed to analyze file'
        );
      }
    } catch (error) {
      console.error('❌ Single file analysis error:', error);
      toast.error(language === 'vi' 
        ? `❌ Lỗi phân tích: ${error.response?.data?.detail || error.message}`
        : `❌ Analysis error: ${error.response?.data?.detail || error.message}`
      );
    } finally {
      setIsMultiCertProcessing(false);
    }
  };

  // Handle multi files: Batch upload with auto-create DB records (PARALLEL with stagger)
  const handleMultiFileBatchUpload = async (fileArray, totalFiles) => {
    setIsMultiCertProcessing(true);

    // Initialize upload tracking
    const initialUploads = fileArray.map((file, index) => ({
      index,
      filename: file.name,
      size: file.size,
      status: 'pending',
      progress: 0,
      stage: language === 'vi' ? 'Đang chờ...' : 'Waiting...',
      extracted_info: null,
      error: null
    }));
    
    setMultiCertUploads(initialUploads);
    setUploadSummary({ success: 0, failed: 0, total: totalFiles });

    // Show batch info
    toast.info(language === 'vi' 
      ? `🚀 Bắt đầu upload ${totalFiles} file (staggered 2s, parallel processing)...`
      : `🚀 Starting upload of ${totalFiles} files (staggered 2s, parallel processing)...`
    );

    let successCount = 0;
    let failedCount = 0;
    let firstSuccessInfo = null;

    try {
      // Create array of upload promises with staggered start
      const uploadPromises = fileArray.map(async (file, i) => {
        // Stagger start time: File 0 → 0ms, File 1 → 2000ms, File 2 → 4000ms
        const startDelay = i * 2000; // 2 seconds between starts
        
        // Wait for stagger delay
        await new Promise(resolve => setTimeout(resolve, startDelay));
        
        try {
          // Update status to uploading
          setMultiCertUploads(prev => prev.map((upload, idx) => 
            idx === i 
              ? {
                  ...upload,
                  status: 'uploading',
                  stage: language === 'vi' 
                    ? `Đang upload... (${i + 1}/${totalFiles})`
                    : `Uploading... (${i + 1}/${totalFiles})`
                }
              : upload
          ));

          // Create FormData for single file
          const formData = new FormData();
          formData.append('files', file);

          console.log(`📤 [${i + 1}/${totalFiles}] Starting upload (parallel):`, file.name);

          // Upload single file (runs in parallel with other uploads)
          const response = await api.post(
            `/api/audit-certificates/multi-upload?ship_id=${selectedShip.id}`,
            formData,
            {
              headers: { 'Content-Type': 'multipart/form-data' },
              onUploadProgress: (progressEvent) => {
                const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                setMultiCertUploads(prev => prev.map((upload, idx) => 
                  idx === i 
                    ? {
                        ...upload,
                        progress: progress,
                        stage: language === 'vi' 
                          ? `Upload ${progress}%... (${i + 1}/${totalFiles})`
                          : `Uploading ${progress}%... (${i + 1}/${totalFiles})`
                      }
                    : upload
                ));
              }
            }
          );

          console.log(`📥 [${i + 1}/${totalFiles}] Response:`, response.data);

          // Process response
          const results = response.data.results || [];
          const result = results[0]; // Single file result

          if (result && (result.status === 'success' || result.status === 'completed')) {
            successCount++;
            
            // Update status to completed
            setMultiCertUploads(prev => prev.map((upload, idx) => 
              idx === i 
                ? {
                    ...upload,
                    status: 'completed',
                    progress: 100,
                    stage: language === 'vi' ? '✅ Hoàn thành' : '✅ Completed',
                    extracted_info: result.extracted_info
                  }
                : upload
            ));

            // Store first success for auto-fill
            if (!firstSuccessInfo && result.extracted_info) {
              firstSuccessInfo = result.extracted_info;
              console.log('✅ First success with extracted_info:', firstSuccessInfo);
            }

            toast.success(language === 'vi' 
              ? `✅ ${file.name} (${i + 1}/${totalFiles})`
              : `✅ ${file.name} (${i + 1}/${totalFiles})`
            );

            return { status: 'success', index: i, result };

          } else {
            // Handle error or other status
            failedCount++;
            const errorMsg = result?.message || result?.error || 'Unknown error';
            
            setMultiCertUploads(prev => prev.map((upload, idx) => 
              idx === i 
                ? {
                    ...upload,
                    status: 'error',
                    progress: 0,
                    stage: language === 'vi' ? '❌ Thất bại' : '❌ Failed',
                    error: errorMsg
                  }
                : upload
            ));

            toast.error(language === 'vi' 
              ? `❌ ${file.name}: ${errorMsg}`
              : `❌ ${file.name}: ${errorMsg}`
            );

            return { status: 'error', index: i, error: errorMsg };
          }

        } catch (fileError) {
          failedCount++;
          console.error(`❌ [${i + 1}/${totalFiles}] Upload error:`, fileError);
          
          setMultiCertUploads(prev => prev.map((upload, idx) => 
            idx === i 
              ? {
                  ...upload,
                  status: 'error',
                  progress: 0,
                  stage: language === 'vi' ? '❌ Lỗi' : '❌ Error',
                  error: fileError.response?.data?.detail || fileError.message
                }
              : upload
          ));

          toast.error(language === 'vi' 
            ? `❌ ${file.name}: ${fileError.response?.data?.detail || fileError.message}`
            : `❌ ${file.name}: ${fileError.response?.data?.detail || fileError.message}`
          );

          return { status: 'error', index: i, error: fileError.message };
        }
      });

      // Wait for all uploads to complete (they run in parallel)
      console.log('⏳ Waiting for all parallel uploads to complete...');
      const uploadResults = await Promise.all(uploadPromises);
      
      // Count final results
      const finalSuccessCount = uploadResults.filter(r => r.status === 'success').length;
      const finalFailedCount = uploadResults.filter(r => r.status === 'error').length;

      // Update summary
      setUploadSummary({
        success: finalSuccessCount,
        failed: finalFailedCount,
        total: totalFiles
      });

      // Auto-fill form with first success
      if (firstSuccessInfo) {
        const autoFillData = {
          cert_name: firstSuccessInfo.cert_name || firstSuccessInfo.certificate_name || '',
          cert_abbreviation: firstSuccessInfo.cert_abbreviation || '',
          cert_no: firstSuccessInfo.cert_no || firstSuccessInfo.certificate_number || '',
          cert_type: firstSuccessInfo.cert_type || 'Full Term',
          issue_date: formatCertDate(firstSuccessInfo.issue_date),
          valid_date: formatCertDate(firstSuccessInfo.valid_date || firstSuccessInfo.expiry_date),
          last_endorse: formatCertDate(firstSuccessInfo.last_endorse),
          next_survey: formatCertDate(firstSuccessInfo.next_survey),
          next_survey_type: firstSuccessInfo.next_survey_type || '',
          issued_by: firstSuccessInfo.issued_by || '',
          issued_by_abbreviation: firstSuccessInfo.issued_by_abbreviation || '',
          ship_id: selectedShip.id,
          ship_name: firstSuccessInfo.ship_name || '',  // Fill từ AI extraction
          ship_imo: firstSuccessInfo.imo_number || ''   // Fill từ AI extraction
        };

        console.log('📝 Auto-filling form:', autoFillData);

        const filledFields = Object.keys(autoFillData).filter(key => 
          autoFillData[key] && String(autoFillData[key]).trim() && !['ship_id', 'ship_name', 'ship_imo'].includes(key)
        ).length;

        setFormData(prev => ({
          ...prev,
          ...autoFillData
        }));

        toast.success(language === 'vi' 
          ? `✅ Đã điền ${filledFields} trường thông tin!`
          : `✅ Auto-filled ${filledFields} fields!`
        );
      }

      // Final summary toast
      toast.success(language === 'vi'
        ? `🎉 Hoàn tất: ${finalSuccessCount} thành công, ${finalFailedCount} thất bại`
        : `🎉 Complete: ${finalSuccessCount} success, ${finalFailedCount} failed`
      );
      
      // Call onSuccess to refresh the list
      if (finalSuccessCount > 0 && onSuccess) {
        onSuccess();
      }

    } catch (error) {
      console.error('❌ Batch upload error:', error);
      toast.error(language === 'vi' 
        ? `❌ Lỗi upload: ${error.message}`
        : `❌ Upload error: ${error.message}`
      );
    } finally {
      setIsMultiCertProcessing(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.cert_name || !formData.cert_no) {
      toast.error(language === 'vi' ? 'Vui lòng điền đầy đủ thông tin bắt buộc' : 'Please fill all required fields');
      return;
    }

    setIsSubmitting(true);
    try {
      // Prepare certificate payload with UTC-safe date conversion
      const certPayload = {
        ...formData,
        ship_id: selectedShip.id,
        issue_date: convertDateInputToUTC(formData.issue_date),
        valid_date: convertDateInputToUTC(formData.valid_date),
        last_endorse: formData.last_endorse ? convertDateInputToUTC(formData.last_endorse) : null,
        next_survey: formData.next_survey ? convertDateInputToUTC(formData.next_survey) : null
      };

      // **NEW LOGIC: Nếu có certificateFile (từ single upload), upload file trước**
      if (certificateFile) {
        // Check if validation was approved (user clicked Continue on validation modal)
        if (validationApproved) {
          // User approved validation warning - create record with file using special endpoint
          console.log('✅ Validation approved - creating record with file upload');
          
          toast.info(language === 'vi' 
            ? '📤 Đang upload file và tạo certificate...'
            : '📤 Uploading file and creating certificate...'
          );
          
          // Use special endpoint that uploads file WITHOUT validation (user already approved)
          const uploadFormData = new FormData();
          uploadFormData.append('file', certificateFile);
          uploadFormData.append('cert_data', JSON.stringify(certPayload));
          
          const uploadResponse = await api.post(
            `/api/audit-certificates/create-with-file-override?ship_id=${selectedShip.id}`,
            uploadFormData,
            {
              headers: { 'Content-Type': 'multipart/form-data' }
            }
          );
          
          if (uploadResponse.data.success) {
            toast.success(language === 'vi' 
              ? '✅ Đã tạo certificate với file và ghi chú tham khảo!'
              : '✅ Certificate created with file and reference note!'
            );
            
            // Clear states
            setCertificateFile(null);
            setValidationApproved(false);
            
            // Call onSuccess to refresh list
            if (onSuccess) {
              onSuccess();
            }
            
            // Reset form
            setFormData({
              ship_id: selectedShip?.id || '',
              ship_name: selectedShip?.name || '',
              cert_name: '',
              cert_abbreviation: '',
              cert_no: '',
              cert_type: 'Full Term',
              issue_date: '',
              valid_date: '',
              last_endorse: '',
              next_survey: '',
              next_survey_type: '',
              issued_by: '',
              issued_by_abbreviation: '',
              notes: ''
            });
            
            handleClose();
          } else {
            throw new Error(uploadResponse.data.message || 'Upload failed');
          }
          
          return; // Exit after success
        }
        
        // Normal flow: upload via multi-upload endpoint (with validation)
        toast.info(language === 'vi' 
          ? '📤 Đang upload file lên Google Drive...'
          : '📤 Uploading file to Google Drive...'
        );

        // Upload file to Drive using multi-upload endpoint (sẽ tạo DB record)
        const uploadFormData = new FormData();
        uploadFormData.append('files', certificateFile);

        const uploadResponse = await api.post(
          `/api/audit-certificates/multi-upload?ship_id=${selectedShip.id}`,
          uploadFormData,
          {
            headers: { 'Content-Type': 'multipart/form-data' }
          }
        );

        console.log('📥 Upload response:', uploadResponse.data);

        // Check response status
        const results = uploadResponse.data.results || [];
        const firstResult = results[0];
        
        if (!firstResult) {
          throw new Error('No response from server');
        }

        // Handle different statuses
        if (firstResult.status === 'requires_manual_input') {
          // AI extraction insufficient
          toast.error(language === 'vi' 
            ? `❌ ${firstResult.message || 'AI không thể trích xuất đủ thông tin'}\n\n${firstResult.manual_input_reason || ''}`
            : `❌ ${firstResult.message || 'AI could not extract sufficient information'}\n\n${firstResult.manual_input_reason || ''}`
          , { duration: 8000 });
          
          console.warn('⚠️ Manual input required:', firstResult.manual_input_reason);
          
          // Don't close modal, let user manually enter data
          setCertificateFile(null); // Clear file
          return; // Stop here
        }
        
        if (firstResult.status === 'error') {
          // Hard error (IMO mismatch, etc.)
          const errorMessage = firstResult.message || firstResult.progress_message || 'Upload failed';
          toast.error(language === 'vi' 
            ? `❌ ${errorMessage}`
            : `❌ ${errorMessage}`
          , { duration: 6000 });
          
          console.error('❌ Upload error:', firstResult);
          
          // Clear file and stop
          setCertificateFile(null);
          return;
        }
        
        if (firstResult.status === 'pending_duplicate_resolution') {
          // Duplicate detected
          toast.warning(language === 'vi' 
            ? `⚠️ ${firstResult.message || 'Phát hiện chứng chỉ trùng lặp'}\n\nVui lòng xử lý duplicate từ batch upload.`
            : `⚠️ ${firstResult.message || 'Duplicate certificate detected'}\n\nPlease handle duplicate from batch upload.`
          , { duration: 8000 });
          
          console.warn('⚠️ Duplicate detected:', firstResult.duplicate_info);
          
          // Clear file and stop
          setCertificateFile(null);
          return;
        }

        // Success case
        if (uploadResponse.data.success && uploadResponse.data.summary.successfully_created > 0) {
          toast.success(language === 'vi' 
            ? '✅ Đã tạo certificate với file đính kèm!'
            : '✅ Certificate created with attached file!'
          );
          
          // Clear file state
          setCertificateFile(null);
          
          // Call onSuccess to refresh list
          if (onSuccess) {
            onSuccess();
          }
          
          // Reset form
          setFormData({
            ship_id: selectedShip?.id || '',
            ship_name: selectedShip?.name || '',
            cert_name: '',
            cert_abbreviation: '',
            cert_no: '',
            cert_type: 'Full Term',
            issue_date: '',
            valid_date: '',
            last_endorse: '',
            next_survey: '',
            next_survey_type: '',
            issued_by: '',
            issued_by_abbreviation: '',
            notes: ''
          });
          
          handleClose();
        } else {
          throw new Error(firstResult.message || 'Upload failed');
        }
      } else {
        // **ORIGINAL LOGIC: Không có file, chỉ tạo DB record**
        await onSave(certPayload);
        
        // Reset form
        setFormData({
          ship_id: selectedShip?.id || '',
          ship_name: selectedShip?.name || '',
          cert_name: '',
          cert_abbreviation: '',
          cert_no: '',
          cert_type: 'Full Term',
          issue_date: '',
          valid_date: '',
          last_endorse: '',
          next_survey: '',
          next_survey_type: '',
          issued_by: '',
          issued_by_abbreviation: '',
          notes: ''
        });
        setMultiCertUploads([]);
        setUploadSummary({ success: 0, failed: 0, total: 0 });
      }
    } catch (error) {
      // Error handled by parent
      console.error('Submit error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setFormData({
      ship_id: selectedShip?.id || '',
      ship_name: '',  // Reset để AI fill lại
      ship_imo: '',   // Reset để AI fill lại
      cert_name: '',
      cert_abbreviation: '',
      cert_no: '',
      cert_type: 'Full Term',
      issue_date: '',
      valid_date: '',
      last_endorse: '',
      next_survey: '',
      next_survey_type: '',
      issued_by: '',
      issued_by_abbreviation: '',
      notes: ''
    });
    setCertificateFile(null);
    setValidationApproved(false);
    setMultiCertUploads([]);
    setUploadSummary({ success: 0, failed: 0, total: 0 });
    setIsMultiCertProcessing(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center z-10">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? '📋 Thêm Audit Certificate' : '📋 Add Audit Certificate'}
          </h2>
          <button onClick={handleClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Software Expired Warning */}
          {isSoftwareExpired && (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
              <div className="flex items-start">
                <span className="text-yellow-600 text-2xl mr-3">⚠️</span>
                <div>
                  <h4 className="font-semibold text-yellow-800 mb-1">
                    {language === 'vi' ? 'Phần mềm hết hạn sử dụng' : 'Software Expired'}
                  </h4>
                  <p className="text-sm text-yellow-700">
                    {language === 'vi' 
                      ? 'Tính năng AI không khả dụng. Vui lòng sử dụng nhập liệu bằng tay.'
                      : 'AI features are not available. Please use manual entry.'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Multi Cert Upload Section */}
          <div className="border-2 border-dashed border-blue-300 rounded-lg p-6 bg-blue-50">
            <div className="flex items-start justify-between mb-3">
              {/* Title and AI Model */}
              <div className="flex-1 pr-4">
                <h3 className="text-lg font-semibold text-blue-900 mb-2">
                  📋 {language === 'vi' ? 'Multi Cert Upload' : 'Multi Cert Upload'}
                </h3>
                
                {/* AI Model Display */}
                {aiConfig && aiConfig.provider && (
                  <div className="flex items-center mb-2">
                    <span className="text-sm text-blue-700 mr-2">
                      {language === 'vi' ? 'Model AI đang sử dụng:' : 'AI Model in use:'}
                    </span>
                    <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z" />
                      </svg>
                      {aiConfig.provider === 'emergent' 
                        ? 'Emergent LLM' 
                        : (aiConfig.provider.charAt(0).toUpperCase() + aiConfig.provider.slice(1))
                      } - {aiConfig.model || 'Default Model'}
                    </div>
                  </div>
                )}
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
                </ul>
              </div>

              {/* Upload Button */}
              <div className="flex-shrink-0">
                <label
                  htmlFor="multi-cert-upload"
                  className={`inline-flex items-center px-4 py-3 border border-transparent text-sm font-medium rounded-md transition-colors cursor-pointer ${
                    selectedShip && !isMultiCertProcessing
                      ? 'text-white bg-blue-600 hover:bg-blue-700 shadow-md'
                      : 'text-gray-400 bg-gray-300 cursor-not-allowed'
                  }`}
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {isMultiCertProcessing 
                    ? (language === 'vi' ? '⏳ Đang xử lý...' : '⏳ Processing...')
                    : (language === 'vi' ? '📋 Cert Upload' : '📋 Cert Upload')
                  }
                  <input
                    id="multi-cert-upload"
                    type="file"
                    multiple
                    className="sr-only"
                    onChange={(e) => {
                      if (selectedShip && !isMultiCertProcessing) {
                        handleMultiCertUpload(e.target.files);
                        e.target.value = '';
                      }
                    }}
                    disabled={!selectedShip || isMultiCertProcessing}
                    accept=".pdf,.jpg,.jpeg,.png"
                  />
                </label>
              </div>
            </div>

            {/* Upload Summary */}
            {uploadSummary.total > 0 && (
              <div className="mt-4 p-3 bg-white rounded-lg border border-blue-200">
                <div className="text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Kết quả upload:' : 'Upload Results:'}
                </div>
                <div className="flex gap-4 mt-2">
                  <div className="flex items-center">
                    <span className="text-green-600 font-bold">{uploadSummary.success}</span>
                    <span className="text-gray-600 text-sm ml-1">{language === 'vi' ? 'thành công' : 'success'}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-red-600 font-bold">{uploadSummary.failed}</span>
                    <span className="text-gray-600 text-sm ml-1">{language === 'vi' ? 'thất bại' : 'failed'}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-blue-600 font-bold">{uploadSummary.total}</span>
                    <span className="text-gray-600 text-sm ml-1">{language === 'vi' ? 'tổng' : 'total'}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Upload Progress List */}
            {multiCertUploads.length > 0 && (
              <div className="mt-4 space-y-2 max-h-60 overflow-y-auto">
                {multiCertUploads.map((upload, idx) => (
                  <div 
                    key={idx}
                    className={`p-3 rounded-lg border transition-all ${
                      upload.status === 'completed' ? 'bg-green-50 border-green-300' :
                      upload.status === 'error' ? 'bg-red-50 border-red-300' :
                      upload.status === 'uploading' ? 'bg-blue-50 border-blue-300' :
                      'bg-gray-50 border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center space-x-2 flex-1 min-w-0">
                        <span className="text-xs font-mono text-gray-500">#{idx + 1}</span>
                        <span className="text-sm font-medium truncate" title={upload.filename}>
                          {upload.filename}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 ml-2">{(upload.size / 1024).toFixed(1)} KB</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className={`text-xs font-medium ${
                        upload.status === 'completed' ? 'text-green-700' :
                        upload.status === 'error' ? 'text-red-700' :
                        upload.status === 'uploading' ? 'text-blue-700' :
                        'text-gray-700'
                      }`}>
                        {upload.stage}
                      </span>
                      
                      {upload.status === 'uploading' && upload.progress > 0 && (
                        <span className="text-xs text-blue-600 font-bold">{upload.progress}%</span>
                      )}
                    </div>
                    
                    {/* Progress bar for uploading */}
                    {upload.status === 'uploading' && upload.progress > 0 && (
                      <div className="mt-2 w-full bg-blue-200 rounded-full h-1.5">
                        <div 
                          className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${upload.progress}%` }}
                        />
                      </div>
                    )}
                    
                    {/* Error message */}
                    {upload.status === 'error' && upload.error && (
                      <div className="mt-1 text-xs text-red-600">
                        {upload.error}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
          )}
          
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
            
            {/* Row 1: Ship Name & IMO (AI will fill these) */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? '🚢 Tên tàu' : '🚢 Ship Name'}
                </label>
                <input
                  type="text"
                  value={formData.ship_name}
                  onChange={(e) => setFormData({...formData, ship_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  placeholder={language === 'vi' ? 'AI sẽ tự động điền' : 'AI will auto-fill'}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? '🔢 Số IMO' : '🔢 IMO Number'}
                </label>
                <input
                  type="text"
                  value={formData.ship_imo}
                  onChange={(e) => setFormData({...formData, ship_imo: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 font-mono"
                  placeholder={language === 'vi' ? 'AI sẽ tự động điền' : 'AI will auto-fill'}
                />
              </div>
            </div>
            
            {/* Row 2: Certificate Name, Abbreviation & Number (3 columns) */}
            <div className="grid grid-cols-3 gap-4">
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
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tên viết tắt' : 'Abbreviation'}
                </label>
                <input
                  type="text"
                  value={formData.cert_abbreviation}
                  onChange={(e) => setFormData({...formData, cert_abbreviation: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  placeholder={language === 'vi' ? 'Viết tắt' : 'Abbr'}
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
                />
              </div>
            </div>

            {/* Row 3: Certificate Type, Issue Date & Valid Date (3 columns) */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Loại chứng chỉ' : 'Certificate Type'}
                </label>
                <select
                  value={formData.cert_type}
                  onChange={(e) => setFormData({...formData, cert_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Full Term">Full Term</option>
                  <option value="Interim">Interim</option>
                  <option value="Provisional">Provisional</option>
                  <option value="Short term">Short term</option>
                  <option value="Conditional">Conditional</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày cấp' : 'Issue Date'}
                </label>
                <input
                  type="date"
                  value={formData.issue_date}
                  onChange={(e) => setFormData({...formData, issue_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
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
                />
              </div>
            </div>

            {/* Row 4: Last Endorse, Next Survey & Next Survey Type (3 columns) */}
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
                  >
                    <option value="">{language === 'vi' ? '-- Chọn loại --' : '-- Select Type --'}</option>
                    <option value="Initial">Initial</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Renewal">Renewal</option>
                  </select>
                </div>
              </div>

            {/* Row 5: Issued By, Abbreviation & empty (2+1 columns) */}
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Cấp bởi' : 'Issued By'}
                </label>
                <input
                  type="text"
                  value={formData.issued_by}
                  onChange={(e) => setFormData({...formData, issued_by: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  placeholder={language === 'vi' ? 'Tên tổ chức cấp' : 'Issuing organization'}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Viết tắt' : 'Abbreviation'}
                </label>
                <input
                  type="text"
                  value={formData.issued_by_abbreviation}
                  onChange={(e) => setFormData({...formData, issued_by_abbreviation: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  placeholder={language === 'vi' ? 'Viết tắt' : 'Abbreviation'}
                />
              </div>
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
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-medium"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white rounded-lg font-medium"
            >
              {isSubmitting ? (
                language === 'vi' ? 'Đang lưu...' : 'Saving...'
              ) : (
                language === 'vi' ? 'Lưu' : 'Save'
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Validation Confirmation Modal */}
      {validationModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[70]">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4">
            {/* Header */}
            <div className="bg-red-50 border-b border-red-200 px-6 py-4 rounded-t-xl">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-lg font-semibold text-red-900">
                    {language === 'vi' ? '⚠️ Cảnh báo xác thực' : '⚠️ Validation Warning'}
                  </h3>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="px-6 py-4">
              <p className="text-gray-700 text-base mb-4">
                {validationModal.message}
              </p>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
                <p className="text-sm text-yellow-800">
                  {language === 'vi' 
                    ? '💡 Nếu bạn tiếp tục, ghi chú sau sẽ được thêm vào certificate:'
                    : '💡 If you continue, the following note will be added to the certificate:'
                  }
                </p>
                <p className="text-sm font-medium text-yellow-900 mt-2 italic">
                  "{validationModal.overrideNote}"
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="bg-gray-50 px-6 py-4 rounded-b-xl flex justify-end gap-3">
              <button
                onClick={validationModal.onCancel}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-medium transition-colors"
              >
                {language === 'vi' ? 'Hủy' : 'Cancel'}
              </button>
              <button
                onClick={validationModal.onContinue}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
              >
                {language === 'vi' ? 'Tiếp tục' : 'Continue'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Category Warning Modal (ISM/ISPS/MLC) */}
      {categoryModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[70]">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full mx-4">
            {/* Header */}
            <div className="bg-red-50 border-b border-red-200 px-6 py-4 rounded-t-xl">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-lg font-semibold text-red-900">
                    {language === 'vi' ? '⚠️ Loại giấy chứng nhận không phù hợp' : '⚠️ Certificate Category Mismatch'}
                  </h3>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="px-6 py-4">
              <p className="text-gray-700 text-base mb-4">
                {categoryModal.message}
              </p>
              
              {categoryModal.certName && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                  <p className="text-sm font-semibold text-red-900 mb-2">
                    {language === 'vi' ? '📋 Tên giấy chứng nhận:' : '📋 Certificate name:'}
                  </p>
                  <p className="text-sm text-gray-700 font-medium">
                    "{categoryModal.certName}"
                  </p>
                </div>
              )}
              
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-sm text-yellow-800">
                  {language === 'vi' 
                    ? '💡 Module ISM-ISPS-MLC chỉ dành cho các giấy chứng nhận liên quan đến ISM (International Safety Management), ISPS (International Ship and Port Facility Security), và MLC (Maritime Labour Convention).'
                    : '💡 ISM-ISPS-MLC module is only for certificates related to ISM (International Safety Management), ISPS (International Ship and Port Facility Security), and MLC (Maritime Labour Convention).'
                  }
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="bg-gray-50 px-6 py-4 rounded-b-xl flex justify-end gap-3">
              <button
                onClick={categoryModal.onCancel}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-medium transition-colors"
              >
                {language === 'vi' ? 'Hủy' : 'Cancel'}
              </button>
              <button
                onClick={categoryModal.onContinue}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
              >
                {language === 'vi' ? 'Tiếp tục tạo' : 'Continue Anyway'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Duplicate Confirmation Modal */}
      {duplicateModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[70]">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full mx-4">
            {/* Header */}
            <div className="bg-orange-50 border-b border-orange-200 px-6 py-4 rounded-t-xl">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-lg font-semibold text-orange-900">
                    {language === 'vi' ? '⚠️ Phát hiện chứng chỉ trùng lặp' : '⚠️ Duplicate Certificate Detected'}
                  </h3>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="px-6 py-4">
              <p className="text-gray-700 text-base mb-4">
                {duplicateModal.message}
              </p>
              
              {duplicateModal.existingCert && (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
                  <p className="text-sm font-semibold text-orange-900 mb-2">
                    {language === 'vi' ? '📋 Thông tin certificate đã tồn tại:' : '📋 Existing certificate info:'}
                  </p>
                  <div className="space-y-1 text-sm text-gray-700">
                    <div><span className="font-medium">{language === 'vi' ? 'Tên:' : 'Name:'}</span> {duplicateModal.existingCert.cert_name}</div>
                    <div><span className="font-medium">{language === 'vi' ? 'Số:' : 'Number:'}</span> {duplicateModal.existingCert.cert_no}</div>
                    <div><span className="font-medium">{language === 'vi' ? 'Loại:' : 'Type:'}</span> {duplicateModal.existingCert.cert_type}</div>
                    {duplicateModal.existingCert.issue_date && (
                      <div><span className="font-medium">{language === 'vi' ? 'Ngày cấp:' : 'Issue Date:'}</span> {duplicateModal.existingCert.issue_date}</div>
                    )}
                    {duplicateModal.existingCert.valid_date && (
                      <div><span className="font-medium">{language === 'vi' ? 'Ngày hết hạn:' : 'Valid Date:'}</span> {duplicateModal.existingCert.valid_date}</div>
                    )}
                  </div>
                </div>
              )}
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800">
                  {language === 'vi' 
                    ? '💡 Nếu bạn tiếp tục, một certificate mới sẽ được tạo mặc dù đã có certificate tương tự.'
                    : '💡 If you continue, a new certificate will be created despite the existing similar certificate.'
                  }
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="bg-gray-50 px-6 py-4 rounded-b-xl flex justify-end gap-3">
              <button
                onClick={duplicateModal.onCancel}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-medium transition-colors"
              >
                {language === 'vi' ? 'Hủy' : 'Cancel'}
              </button>
              <button
                onClick={duplicateModal.onContinue}
                className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition-colors"
              >
                {language === 'vi' ? 'Tiếp tục tạo mới' : 'Continue Anyway'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
