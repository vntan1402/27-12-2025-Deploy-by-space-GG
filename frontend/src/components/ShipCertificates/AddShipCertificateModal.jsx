/**
 * Add Ship Certificate Modal Component
 * Full-featured modal for adding ship certificates with AI analysis
 * Extracted from V1 AddRecordModal (Certificate section)
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import { DuplicateShipCertificateModal } from './DuplicateShipCertificateModal';
import { ShipNameMismatchModal } from './ShipNameMismatchModal';

export const AddShipCertificateModal = ({ 
  isOpen, 
  onClose, 
  onSuccess,
  selectedShip,
  allShips = [],
  onShipChange,
  aiConfig
}) => {
  const { user, language } = useAuth();

  // Ship selection state
  const [showShipDropdown, setShowShipDropdown] = useState(false);

  // Certificate form state
  const [certificateData, setCertificateData] = useState({
    ship_id: selectedShip?.id || '',
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
    notes: '',
    category: 'certificates',
    sensitivity_level: 'internal'
  });

  // Multi cert upload states
  const [isMultiCertProcessing, setIsMultiCertProcessing] = useState(false);
  const [multiCertUploads, setMultiCertUploads] = useState([]);
  const [uploadSummary, setUploadSummary] = useState({ success: 0, failed: 0, total: 0 });

  // Single file upload state for form
  const [certificateFile, setCertificateFile] = useState(null);
  const [isCertificateAnalyzing, setIsCertificateAnalyzing] = useState(false);

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Duplicate modal state
  const [duplicateModal, setDuplicateModal] = useState({
    show: false,
    duplicates: [],
    currentFile: null,
    analysisResult: null,
    uploadResult: null
  });

  // Mismatch modal state
  const [mismatchModal, setMismatchModal] = useState({
    show: false,
    extractedShipName: '',
    currentFile: null,
    analysisResult: null,
    uploadResult: null
  });

  // Update ship_id when selectedShip changes
  useEffect(() => {
    if (selectedShip?.id) {
      setCertificateData(prev => ({ ...prev, ship_id: selectedShip.id }));
    }
  }, [selectedShip?.id]);

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
    setMultiCertUploads([]);
    setUploadSummary({ success: 0, failed: 0, total: files.length });

    const formData = new FormData();
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await api.post(
        `/api/ships/${selectedShip.id}/certificates/multi-upload`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );

      if (response.data && response.data.results) {
        const results = response.data.results;
        setMultiCertUploads(results);

        // Count success/failed
        const successCount = results.filter(r => r.status === 'success').length;
        const failedCount = results.filter(r => r.status === 'error').length;
        
        setUploadSummary({
          success: successCount,
          failed: failedCount,
          total: results.length
        });

        // Auto-fill form with first successful result
        const firstSuccess = results.find(r => r.status === 'success' && r.analysis);
        if (firstSuccess && firstSuccess.analysis) {
          const analysisData = firstSuccess.analysis;
          const autoFillData = {
            cert_name: analysisData.cert_name || analysisData.certificate_name || '',
            cert_no: analysisData.cert_no || analysisData.certificate_number || '',
            issue_date: formatCertDate(analysisData.issue_date),
            valid_date: formatCertDate(analysisData.valid_date || analysisData.expiry_date),
            issued_by: analysisData.issued_by || '',
            ship_id: selectedShip.id
          };

          // Count filled fields
          const filledFields = Object.keys(autoFillData).filter(key => 
            autoFillData[key] && String(autoFillData[key]).trim()
          ).length;

          setCertificateData(prev => ({
            ...prev,
            ...autoFillData
          }));

          toast.success(language === 'vi' 
            ? `✅ Phân tích certificate thành công! Đã điền ${filledFields} trường thông tin.`
            : `✅ Certificate analysis successful! Auto-filled ${filledFields} fields.`
          );
        }

        toast.success(language === 'vi'
          ? `✅ Upload hoàn tất: ${successCount} thành công, ${failedCount} thất bại`
          : `✅ Upload complete: ${successCount} success, ${failedCount} failed`
        );
      }
    } catch (error) {
      console.error('Multi cert upload error:', error);
      toast.error(language === 'vi' 
        ? `❌ Lỗi upload: ${error.response?.data?.detail || error.message}`
        : `❌ Upload error: ${error.response?.data?.detail || error.message}`
      );
    } finally {
      setIsMultiCertProcessing(false);
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedShip?.id) {
      toast.error(language === 'vi' ? 'Vui lòng chọn tàu' : 'Please select a ship');
      return;
    }

    if (!certificateData.cert_name) {
      toast.error(language === 'vi' ? 'Vui lòng nhập tên chứng chỉ' : 'Please enter certificate name');
      return;
    }

    try {
      setIsSubmitting(true);

      // Prepare certificate payload with UTC-safe date conversion
      const certPayload = {
        ...certificateData,
        ship_id: selectedShip.id,
        issue_date: convertDateInputToUTC(certificateData.issue_date),
        valid_date: convertDateInputToUTC(certificateData.valid_date),
        last_endorse: certificateData.last_endorse ? convertDateInputToUTC(certificateData.last_endorse) : null,
        next_survey: certificateData.next_survey ? convertDateInputToUTC(certificateData.next_survey) : null
      };

      const response = await api.post('/api/ships/certificates', certPayload);
      
      toast.success(language === 'vi' 
        ? '✅ Chứng chỉ đã được thêm thành công!' 
        : '✅ Certificate added successfully!'
      );

      // Reset form
      setCertificateData({
        ship_id: selectedShip?.id || '',
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
        notes: '',
        category: 'certificates',
        sensitivity_level: 'internal'
      });
      setCertificateFile(null);
      setMultiCertUploads([]);
      setUploadSummary({ success: 0, failed: 0, total: 0 });

      onSuccess();
      onClose();
    } catch (error) {
      console.error('Certificate creation error:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      
      toast.error(language === 'vi' 
        ? `❌ Không thể tạo chứng chỉ: ${errorMessage}` 
        : `❌ Failed to create certificate: ${errorMessage}`
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle close
  const handleClose = () => {
    setCertificateData({
      ship_id: selectedShip?.id || '',
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
      notes: '',
      category: 'certificates',
      sensitivity_level: 'internal'
    });
    setCertificateFile(null);
    setMultiCertUploads([]);
    setUploadSummary({ success: 0, failed: 0, total: 0 });
    setIsMultiCertProcessing(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-800">
            📋 {language === 'vi' ? 'Thêm Ship Certificate' : 'Add Ship Certificate'}
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Ship Selection Warning */}
          {!selectedShip && (
            <div className="relative">
              <div 
                className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 cursor-pointer hover:bg-yellow-100 transition-colors"
                onMouseEnter={() => setShowShipDropdown(true)}
                onMouseLeave={() => setShowShipDropdown(false)}
              >
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-yellow-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="text-yellow-800 text-sm font-medium">
                        {language === 'vi' ? '⚠️ Chưa chọn tàu' : '⚠️ No Ship Selected'}
                      </p>
                      <div className="text-yellow-600">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </div>
                    <p className="text-yellow-700 text-xs mt-1">
                      {language === 'vi' 
                        ? 'Hover để chọn tàu. Certificate sẽ được gán vào tàu đã chọn.'
                        : 'Hover to select a ship. Certificates will be assigned to the selected ship.'
                      }
                    </p>
                  </div>
                </div>
              </div>

              {/* Ship Selection Dropdown */}
              {showShipDropdown && (
                <div 
                  className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto"
                  onMouseEnter={() => setShowShipDropdown(true)}
                  onMouseLeave={() => setShowShipDropdown(false)}
                >
                  <div className="p-2">
                    <div className="text-xs font-medium text-gray-500 px-3 py-2 border-b">
                      {language === 'vi' ? 'Chọn tàu:' : 'Select Ship:'}
                    </div>
                    {allShips && allShips.length > 0 ? (
                      <div className="max-h-48 overflow-y-auto">
                        {allShips.map((ship) => (
                          <button
                            key={ship.id}
                            type="button"
                            onClick={() => {
                              onShipChange(ship);
                              setShowShipDropdown(false);
                              toast.success(language === 'vi' 
                                ? `✅ Đã chọn tàu: ${ship.name}`
                                : `✅ Selected ship: ${ship.name}`);
                            }}
                            className="w-full text-left px-3 py-2 hover:bg-blue-50 rounded transition-colors flex items-center justify-between group"
                          >
                            <div>
                              <div className="font-medium text-gray-900 text-sm">{ship.name}</div>
                              <div className="text-xs text-gray-500">
                                IMO: {ship.imo_number} • {ship.flag}
                              </div>
                            </div>
                            <div className="text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                            </div>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="px-3 py-4 text-center text-gray-500 text-sm">
                        {language === 'vi' 
                          ? 'Không có tàu nào. Hãy thêm tàu mới trước.'
                          : 'No ships available. Please add a new ship first.'}
                      </div>
                    )}
                  </div>
                </div>
              )}
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
                {aiConfig && (
                  <div className="flex items-center mb-2">
                    <span className="text-sm text-blue-700 mr-2">
                      {language === 'vi' ? 'Model AI đang sử dụng:' : 'AI Model in use:'}
                    </span>
                    <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z" />
                      </svg>
                      {aiConfig.provider === 'emergent' ? 'Emergent LLM' : aiConfig.provider.charAt(0).toUpperCase() + aiConfig.provider.slice(1)} - {aiConfig.model}
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
                <div className="text-sm font-medium text-gray-700">
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
                    <span className="text-gray-600 font-bold">{uploadSummary.total}</span>
                    <span className="text-gray-600 text-sm ml-1">{language === 'vi' ? 'tổng' : 'total'}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Warning message for no ship selected */}
            {!selectedShip && (
              <div className="text-center mt-2">
                <p className="text-yellow-700 text-sm">
                  {language === 'vi' 
                    ? '⚠️ Vui lòng chọn tàu trước khi upload certificate'
                    : '⚠️ Please select a ship before uploading certificate'
                  }
                </p>
              </div>
            )}
          </div>

          {/* Certificate Form Fields */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">
              {language === 'vi' ? 'Thông tin chứng chỉ (Nhập thủ công)' : 'Certificate Information (Manual Entry)'}
            </h3>
            <p className="text-sm text-gray-600">
              {language === 'vi' 
                ? 'Điền hoặc chỉnh sửa thông tin chứng chỉ được trích xuất từ file'
                : 'Fill in or edit the certificate information extracted from file'
              }
            </p>

            {/* Row 1: Certificate Name & Abbreviation */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={certificateData.cert_name}
                  onChange={(e) => setCertificateData({ ...certificateData, cert_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                  value={certificateData.cert_abbreviation}
                  onChange={(e) => setCertificateData({ ...certificateData, cert_abbreviation: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'Tên viết tắt' : 'Abbreviation'}
                />
              </div>
            </div>

            {/* Row 2: Certificate Number & Type */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Số chứng chỉ' : 'Certificate Number'}
                </label>
                <input
                  type="text"
                  value={certificateData.cert_no}
                  onChange={(e) => setCertificateData({ ...certificateData, cert_no: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                  placeholder={language === 'vi' ? 'Nhập số chứng chỉ' : 'Enter certificate number'}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Loại chứng chỉ' : 'Certificate Type'}
                </label>
                <select
                  value={certificateData.cert_type}
                  onChange={(e) => setCertificateData({ ...certificateData, cert_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="Full Term">Full Term</option>
                  <option value="Interim">Interim</option>
                  <option value="Provisional">Provisional</option>
                  <option value="Short term">Short term</option>
                  <option value="Conditional">Conditional</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            {/* Row 3: Issue Date & Valid Date */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày cấp' : 'Issue Date'}
                </label>
                <input
                  type="date"
                  value={certificateData.issue_date}
                  onChange={(e) => setCertificateData({ ...certificateData, issue_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}
                </label>
                <input
                  type="date"
                  value={certificateData.valid_date}
                  onChange={(e) => setCertificateData({ ...certificateData, valid_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Row 4: Last Endorse & Next Survey (conditional) */}
            {certificateData.cert_type === 'Full Term' && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Xác nhận cuối' : 'Last Endorse'}
                  </label>
                  <input
                    type="date"
                    value={certificateData.last_endorse}
                    onChange={(e) => setCertificateData({ ...certificateData, last_endorse: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Kiểm tra tới' : 'Next Survey'}
                  </label>
                  <input
                    type="date"
                    value={certificateData.next_survey}
                    onChange={(e) => setCertificateData({ ...certificateData, next_survey: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            )}

            {/* Row 5: Next Survey Type (if next_survey is set) */}
            {certificateData.next_survey && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Loại kiểm tra tới' : 'Next Survey Type'}
                  </label>
                  <select
                    value={certificateData.next_survey_type}
                    onChange={(e) => setCertificateData({ ...certificateData, next_survey_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">{language === 'vi' ? '-- Chọn loại --' : '-- Select Type --'}</option>
                    <option value="Annual">Annual</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Renewal">Renewal</option>
                    <option value="Special">Special</option>
                  </select>
                </div>
              </div>
            )}

            {/* Row 6: Issued By & Abbreviation */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Cấp bởi' : 'Issued By'}
                </label>
                <input
                  type="text"
                  value={certificateData.issued_by}
                  onChange={(e) => setCertificateData({ ...certificateData, issued_by: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'Tên tổ chức cấp' : 'Issuing organization'}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tên viết tắt (Issued By)' : 'Issued By Abbreviation'}
                </label>
                <input
                  type="text"
                  value={certificateData.issued_by_abbreviation}
                  onChange={(e) => setCertificateData({ ...certificateData, issued_by_abbreviation: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'Viết tắt' : 'Abbreviation'}
                />
              </div>
            </div>

            {/* Row 7: Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ghi chú' : 'Notes'}
              </label>
              <textarea
                value={certificateData.notes}
                onChange={(e) => setCertificateData({ ...certificateData, notes: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Thêm ghi chú...' : 'Add notes...'}
              />
            </div>
          </div>

          {/* Footer Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              disabled={isSubmitting}
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !selectedShip || !certificateData.cert_name}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                isSubmitting || !selectedShip || !certificateData.cert_name
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isSubmitting 
                ? (language === 'vi' ? '⏳ Đang lưu...' : '⏳ Saving...') 
                : (language === 'vi' ? '✅ Lưu Certificate' : '✅ Save Certificate')
              }
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

