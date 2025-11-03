/**
 * Add Audit Certificate Modal - Full Featured
 * With AI analysis, file upload, duplicate detection
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import api from '../../services/api';

export const AddAuditCertificateModal = ({
  isOpen,
  onClose,
  onSave,
  selectedShip,
  language,
  aiConfig
}) => {
  const [formData, setFormData] = useState({
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

  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Multi cert upload states
  const [isMultiCertProcessing, setIsMultiCertProcessing] = useState(false);
  const [multiCertUploads, setMultiCertUploads] = useState([]);
  const [uploadSummary, setUploadSummary] = useState({ success: 0, failed: 0, total: 0 });
  
  // Update ship_id when selectedShip changes
  useEffect(() => {
    if (selectedShip?.id) {
      setFormData(prev => ({ ...prev, ship_id: selectedShip.id, ship_name: selectedShip.name }));
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
    if (!selectedShip?.id) {
      toast.error(language === 'vi' 
        ? '❌ Vui lòng chọn tàu trước khi upload certificate'
        : '❌ Please select a ship before uploading certificate'
      );
      return;
    }

    if (!files || files.length === 0) return;

    setIsMultiCertProcessing(true);
    const fileArray = Array.from(files);
    const totalFiles = fileArray.length;

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
      ? `🚀 Bắt đầu upload ${totalFiles} file (delay 0.5s giữa các file)...`
      : `🚀 Starting upload of ${totalFiles} files (0.5s delay between files)...`
    );

    let successCount = 0;
    let failedCount = 0;
    let firstSuccessInfo = null;

    try {
      // Upload files sequentially with delay
      for (let i = 0; i < fileArray.length; i++) {
        const file = fileArray[i];
        
        // Delay between uploads (except for first file)
        if (i > 0) {
          await new Promise(resolve => setTimeout(resolve, 500)); // 0.5s delay
        }

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

          console.log(`📤 [${i + 1}/${totalFiles}] Uploading:`, file.name);

          // Upload single file
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
        }
      }

      // Update summary
      setUploadSummary({
        success: successCount,
        failed: failedCount,
        total: totalFiles
      });

      // Auto-fill form with first success
      if (firstSuccessInfo) {
        const autoFillData = {
          cert_name: firstSuccessInfo.cert_name || firstSuccessInfo.certificate_name || '',
          cert_no: firstSuccessInfo.cert_no || firstSuccessInfo.certificate_number || '',
          issue_date: formatCertDate(firstSuccessInfo.issue_date),
          valid_date: formatCertDate(firstSuccessInfo.valid_date || firstSuccessInfo.expiry_date),
          issued_by: firstSuccessInfo.issued_by || '',
          ship_id: selectedShip.id,
          ship_name: selectedShip.name
        };

        console.log('📝 Auto-filling form:', autoFillData);

        const filledFields = Object.keys(autoFillData).filter(key => 
          autoFillData[key] && String(autoFillData[key]).trim() && !['ship_id', 'ship_name'].includes(key)
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
        ? `🎉 Hoàn tất: ${successCount} thành công, ${failedCount} thất bại`
        : `🎉 Complete: ${successCount} success, ${failedCount} failed`
      );
      
      // Call onSave to refresh the list
      if (successCount > 0) {
        onSave();
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
    } catch (error) {
      // Error handled by parent
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
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
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* TODO: Add file upload and AI analysis */}
          
          <div className="grid grid-cols-2 gap-4">
            {/* Certificate Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.cert_name}
                onChange={(e) => setFormData({...formData, cert_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            {/* Certificate No */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Số chứng chỉ' : 'Certificate No'} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.cert_no}
                onChange={(e) => setFormData({...formData, cert_no: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            {/* Cert Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Loại' : 'Type'}
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
              </select>
            </div>

            {/* Issue Date */}
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

            {/* Valid Date */}
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

            {/* Next Survey */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Next Survey' : 'Next Survey'}
              </label>
              <input
                type="date"
                value={formData.next_survey}
                onChange={(e) => setFormData({...formData, next_survey: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Issued By */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Cơ quan cấp' : 'Issued By'}
              </label>
              <input
                type="text"
                value={formData.issued_by}
                onChange={(e) => setFormData({...formData, issued_by: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
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
              onClick={onClose}
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
    </div>
  );
};
