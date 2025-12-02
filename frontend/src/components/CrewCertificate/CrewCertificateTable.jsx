import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useUploadGuard } from '../../hooks/useUploadGuard';
import { toast } from 'sonner';
import api from '../../services/api';
import { crewCertificateService } from '../../services/crewCertificateService';
import { formatDateDisplay } from '../../utils/dateHelpers';
import { estimateFileProcessingTime, startSmoothProgressForFile } from '../../utils/progressHelpers';
import { calculateTooltipPosition } from '../../utils/positionHelpers';
import AddCrewCertificateModal from './AddCrewCertificateModal';
import EditCrewCertificateModal from './EditCrewCertificateModal';
import CertificateContextMenu from './CertificateContextMenu';
import DeleteCertificateModal from './DeleteCertificateModal';
import { BatchProcessingModal } from './BatchProcessingModal';
import { BatchResultsModal } from './BatchResultsModal';

const CrewCertificateTable = ({ selectedShip, ships, onShipFilterChange, onShipSelect, initialCrewFilter }) => {
  const { language, user } = useAuth();
  const { checkAndWarn } = useUploadGuard();
  
  // State
  const [certificates, setCertificates] = useState([]);
  const [crewList, setCrewList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCertificates, setSelectedCertificates] = useState(new Set());
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [certificateToEdit, setCertificateToEdit] = useState(null);
  const [certificatesToDelete, setCertificatesToDelete] = useState(null);
  const [contextMenu, setContextMenu] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Batch processing state
  const [isBatchProcessing, setIsBatchProcessing] = useState(false);
  const [isBatchMinimized, setIsBatchMinimized] = useState(false);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });
  const [fileProgressMap, setFileProgressMap] = useState({});
  const [fileStatusMap, setFileStatusMap] = useState({});
  const [fileSubStatusMap, setFileSubStatusMap] = useState({});
  const [fileObjectsMap, setFileObjectsMap] = useState({}); // Store file objects for retry
  const [showBatchResults, setShowBatchResults] = useState(false);
  const [batchResults, setBatchResults] = useState([]);
  
  // Note tooltip state
  const [noteTooltip, setNoteTooltip] = useState({
    show: false,
    x: 0,
    y: 0,
    width: 300,
    content: ''
  });
  
  // Filters
  const [filters, setFilters] = useState({
    shipSignOn: 'all',
    status: 'all',
    crewName: 'all'
  });
  
  // Apply initial crew filter from navigation state
  useEffect(() => {
    if (initialCrewFilter) {
      setFilters(prev => ({
        ...prev,
        crewName: initialCrewFilter
      }));
    }
  }, [initialCrewFilter]);
  
  // Search
  const [searchTerm, setSearchTerm] = useState('');
  
  // Sort
  const [sort, setSort] = useState({
    column: null,
    direction: 'asc'
  });

  // Fetch crew list
  useEffect(() => {
    fetchCrewList();
  }, []);

  // Fetch certificates
  useEffect(() => {
    fetchCertificates();
  }, []);

  const fetchCrewList = async () => {
    try {
      const response = await api.get('/api/crew');
      setCrewList(response.data || []);
    } catch (error) {
      console.error('Failed to fetch crew list:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách thuyền viên' : 'Failed to load crew list');
    }
  };

  const fetchCertificates = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/crew-certificates/all');
      setCertificates(response.data || []);
    } catch (error) {
      console.error('Failed to fetch certificates:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách chứng chỉ' : 'Failed to load certificates');
      setCertificates([]);
    } finally {
      setLoading(false);
    }
  };

  // Context menu handlers
  const handleRowRightClick = (e, cert) => {
    e.preventDefault();
    
    // Calculate menu position with boundary checking
    const menuWidth = 220;
    const menuHeight = 320; // Estimate based on number of menu items
    let x = e.clientX;
    let y = e.clientY;
    
    // Adjust if menu would go off-screen (right side)
    if (x + menuWidth > window.innerWidth) {
      x = window.innerWidth - menuWidth - 10;
    }
    
    // Adjust if menu would go off-screen (bottom)
    if (y + menuHeight > window.innerHeight) {
      // Try to position above cursor
      y = Math.max(10, y - menuHeight);
      if (y < 10) {
        y = 10;
      }
    }
    
    setContextMenu({
      certificate: cert,
      position: { x, y }
    });
  };

  const handleEdit = (cert) => {
    setCertificateToEdit(cert);
    setShowEditModal(true);
  };

  const handleDelete = async () => {
    if (!certificatesToDelete) return;
    
    setIsDeleting(true);
    try {
      const certsArray = Array.isArray(certificatesToDelete) 
        ? certificatesToDelete 
        : [certificatesToDelete];
      
      // Check if bulk delete (multiple certificates)
      if (certsArray.length > 1) {
        // Bulk delete
        const certIds = certsArray.map(cert => cert.id);
        const result = await crewCertificateService.bulkDelete(certIds);
        
        if (result.data.success) {
          const { deleted_count, files_deleted, errors } = result.data;
          
          toast.success(language === 'vi' 
            ? `✅ Đã xóa ${deleted_count} chứng chỉ${files_deleted > 0 ? ` và ${files_deleted} files` : ''}` 
            : `✅ Deleted ${deleted_count} certificate(s)${files_deleted > 0 ? ` and ${files_deleted} file(s)` : ''}`);
          
          if (errors && errors.length > 0) {
            toast.warning(language === 'vi' 
              ? `${errors.length} lỗi xảy ra` 
              : `${errors.length} error(s) occurred`);
          }
        }
      } else {
        // Single delete
        await api.delete(`/api/crew-certificates/${certsArray[0].id}`);
        toast.success(language === 'vi' 
          ? `✅ Đã xóa chứng chỉ` 
          : `✅ Deleted certificate`);
      }
      
      fetchCertificates();
      setShowDeleteModal(false);
      setCertificatesToDelete(null);
      setSelectedCertificates(new Set());
    } catch (error) {
      console.error('Delete error:', error);
      toast.error(language === 'vi' ? '❌ Không thể xóa chứng chỉ' : '❌ Failed to delete certificate');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleViewOriginal = (cert) => {
    if (cert.crew_cert_file_id) {
      window.open(`https://drive.google.com/file/d/${cert.crew_cert_file_id}/view`, '_blank');
    }
  };

  const handleViewSummary = (cert) => {
    if (cert.crew_cert_summary_file_id) {
      window.open(`https://drive.google.com/file/d/${cert.crew_cert_summary_file_id}/view`, '_blank');
    }
  };

  const handleCopyLink = (cert) => {
    if (cert.crew_cert_file_id) {
      const link = `https://drive.google.com/file/d/${cert.crew_cert_file_id}/view`;
      navigator.clipboard.writeText(link);
      toast.success(language === 'vi' ? '✅ Đã sao chép link' : '✅ Link copied');
    }
  };

  const handleDownload = (cert) => {
    if (cert.crew_cert_file_id) {
      window.open(`https://drive.google.com/uc?export=download&id=${cert.crew_cert_file_id}`, '_blank');
    }
  };

  // Note tooltip handlers
  const handleNoteMouseEnter = (e, note) => {
    const rect = e.target.getBoundingClientRect();
    const tooltipWidth = 300;
    const tooltipHeight = 200;
    
    const { x, y } = calculateTooltipPosition(rect, tooltipWidth, tooltipHeight);
    
    setNoteTooltip({
      show: true,
      x: x,
      y: y,
      width: tooltipWidth,
      content: note
    });
  };

  const handleNoteMouseLeave = () => {
    setNoteTooltip({ show: false, x: 0, y: 0, width: 300, content: '' });
  };

  const handleAutoRename = async (certIds) => {
    try {
      const ids = Array.isArray(certIds) ? certIds : [certIds];
      
      await api.post('/api/crew-certificates/bulk-auto-rename', {
        certificate_ids: ids
      });
      
      toast.success(language === 'vi' 
        ? `✅ Đã đổi tên ${ids.length} file` 
        : `✅ Renamed ${ids.length} file(s)`);
      
      fetchCertificates();
    } catch (error) {
      console.error('Auto-rename error:', error);
      toast.error(language === 'vi' ? '❌ Không thể đổi tên file' : '❌ Failed to rename files');
    }
  };

  // Batch upload handler
  const handleBatchUpload = async (files, preSelectedCrewId = null) => {
    if (!files || files.length === 0) return;
    
    // CRITICAL: Check software expiry before batch upload (same as V1)
    if (!checkAndWarn()) {
      console.log('🚫 [BatchUpload] Software expired - batch upload blocked');
      return;
    }
    
    // Validate file count (max 10)
    if (files.length > 10) {
      toast.error(language === 'vi' 
        ? '❌ Tối đa 10 files. Vui lòng chọn lại.' 
        : '❌ Maximum 10 files. Please select again.');
      return;
    }

    // Validate file sizes (max 10MB each)
    const oversizedFiles = Array.from(files).filter(file => file.size > 10 * 1024 * 1024);
    if (oversizedFiles.length > 0) {
      toast.error(language === 'vi' 
        ? `❌ ${oversizedFiles.length} file(s) vượt quá 10MB` 
        : `❌ ${oversizedFiles.length} file(s) exceed 10MB`);
      return;
    }

    // Initialize batch processing
    setIsBatchProcessing(true);
    setIsBatchMinimized(false);
    setBatchProgress({ current: 0, total: files.length });
    
    const initialStatusMap = {};
    const initialProgressMap = {};
    const initialSubStatusMap = {};
    const initialFileObjectsMap = {};
    Array.from(files).forEach(file => {
      initialStatusMap[file.name] = 'waiting';
      initialProgressMap[file.name] = 0;
      initialSubStatusMap[file.name] = '';
      initialFileObjectsMap[file.name] = file; // Store file object for retry
    });
    setFileStatusMap(initialStatusMap);
    setFileProgressMap(initialProgressMap);
    setFileSubStatusMap(initialSubStatusMap);
    setFileObjectsMap(initialFileObjectsMap);

    const STAGGER_DELAY = 2000; // 2 seconds between file starts (same as crew batch upload)
    const results = [];

    // Process files with staggered start (PARALLEL PROCESSING like crew)
    const promises = Array.from(files).map((file, index) => {
      return new Promise((resolve) => {
        setTimeout(async () => {
          // Update status to processing
          setFileStatusMap(prev => ({ ...prev, [file.name]: 'processing' }));
          
          // Start smooth progress animation
          const estimatedTime = estimateFileProcessingTime(file);
          const progressController = startSmoothProgressForFile(
            file.name,
            setFileProgressMap,
            setFileSubStatusMap,
            estimatedTime,
            90 // Max 90%, then jump to 100% on complete
          );

          try {
            // Step 1: AI Analysis
            const formData = new FormData();
            formData.append('cert_file', file);
            if (selectedShip && selectedShip.id) {
              formData.append('ship_id', selectedShip.id);
            }
            if (preSelectedCrewId) {
              formData.append('crew_id', preSelectedCrewId);
            }

            const analysisResponse = await api.post('/api/crew-certificates/analyze-file', formData, {
              headers: { 'Content-Type': 'multipart/form-data' }
            });

            const responseData = analysisResponse.data;
            
            // Check if analysis succeeded
            if (!responseData.success || !responseData.analysis) {
              throw new Error('Cannot analyze file');
            }

            const analysisData = responseData.analysis;
            const crewData = {
              crew_name: responseData.crew_name,
              crew_name_en: responseData.crew_name_en,
              passport: responseData.passport,
              rank: responseData.rank,
              date_of_birth: responseData.date_of_birth
            };

            // Step 2: Create certificate record
            const createData = {
              crew_id: preSelectedCrewId,
              crew_name: crewData.crew_name,
              crew_name_en: crewData.crew_name_en || '',
              passport: crewData.passport || '',
              rank: crewData.rank || '',
              date_of_birth: crewData.date_of_birth || '',
              cert_name: analysisData.cert_name || '',
              cert_no: analysisData.cert_no || '',
              issued_by: analysisData.issued_by || '',
              issued_date: analysisData.issued_date || '',
              cert_expiry: analysisData.cert_expiry || analysisData.expiry_date || '',  // Try both field names
              note: analysisData.note || ''
            };

            const createResponse = await api.post('/api/crew-certificates/manual', createData);

            // Step 3: Upload file
            const certId = createResponse.data.id;
            
            // Convert file to base64
            const fileBase64 = await new Promise((resolve, reject) => {
              const reader = new FileReader();
              reader.onload = () => {
                const base64String = reader.result.split(',')[1];
                resolve(base64String);
              };
              reader.onerror = reject;
              reader.readAsDataURL(file);
            });

            const uploadData = {
              file_content: fileBase64,
              filename: file.name,
              content_type: file.type,
              summary_text: analysisData._summary_text || ''
            };

            await api.post(`/api/crew-certificates/${certId}/upload-files`, uploadData);

            // Complete progress
            progressController.complete();
            setFileStatusMap(prev => ({ ...prev, [file.name]: 'completed' }));

            const result = {
              success: true,
              filename: file.name,
              crew_name: crewData.crew_name,
              cert_name: analysisData.cert_name,
              cert_no: analysisData.cert_no,
              certCreated: true,
              fileUploaded: true
            };
            
            results.push(result);
            resolve(result);

          } catch (error) {
            console.error(`Batch upload error for ${file.name}:`, error);
            
            // Stop progress animation
            progressController.stop();
            setFileStatusMap(prev => ({ ...prev, [file.name]: 'error' }));
            setFileProgressMap(prev => ({ ...prev, [file.name]: 0 }));
            
            // Extract error message - handle various error formats
            let errorMessage = 'Unknown error';
            if (error.response?.data?.detail) {
              const detail = error.response.data.detail;
              if (typeof detail === 'string') {
                errorMessage = detail;
              } else if (Array.isArray(detail)) {
                // Pydantic validation errors
                errorMessage = detail.map(err => err.msg || JSON.stringify(err)).join(', ');
              } else if (typeof detail === 'object') {
                errorMessage = JSON.stringify(detail);
              }
            } else if (error.message) {
              errorMessage = error.message;
            }
            
            const errorResult = {
              success: false,
              filename: file.name,
              error: errorMessage
            };
            
            results.push(errorResult);
            resolve(errorResult);
          }
        }, index * STAGGER_DELAY);
      });
    });

    // Wait for all files to complete
    await Promise.all(promises);

    // Update overall progress
    setBatchProgress({ current: files.length, total: files.length });

    // Show results
    setBatchResults(results);
    setIsBatchProcessing(false);
    setShowBatchResults(true);
    
    // Refresh certificate list
    fetchCertificates();
    
    // Success notification
    const successCount = results.filter(r => r.success).length;
    toast.success(language === 'vi' 
      ? `✅ Hoàn tất: ${successCount}/${files.length} chứng chỉ` 
      : `✅ Completed: ${successCount}/${files.length} certificates`);
  };

  /**
   * Retry failed file from BatchResultsModal
   */
  const handleRetryFailedFile = async (failedFileName) => {
    // Get the original file object from map
    const originalFile = fileObjectsMap[failedFileName];
    
    if (!originalFile) {
      toast.error(
        language === 'vi'
          ? '❌ Không tìm thấy file gốc. Vui lòng upload lại từ đầu.'
          : '❌ Original file not found. Please upload again from scratch.'
      );
      return;
    }
    
    // Show ProcessingModal in minimized mode for this retry
    setIsBatchProcessing(true);
    setIsBatchMinimized(true);
    
    // Reset status for retry
    setFileStatusMap(prev => ({ ...prev, [failedFileName]: 'pending' }));
    setFileProgressMap(prev => ({ ...prev, [failedFileName]: 0 }));
    setFileSubStatusMap(prev => ({ 
      ...prev, 
      [failedFileName]: language === 'vi' ? '🔄 Đang thử lại...' : '🔄 Retrying...' 
    }));
    
    // Update batch progress to show we're processing 1 file
    setBatchProgress({ current: 0, total: 1 });
    
    // Show retry message
    toast.info(
      language === 'vi' 
        ? `🔄 Đang xử lý lại file: ${failedFileName}` 
        : `🔄 Retrying file: ${failedFileName}`
    );
    
    try {
      // Update status to processing
      setFileStatusMap(prev => ({ ...prev, [failedFileName]: 'processing' }));
      
      // Start smooth progress animation
      const estimatedTime = estimateFileProcessingTime(originalFile);
      const progressController = startSmoothProgressForFile(
        failedFileName,
        setFileProgressMap,
        setFileSubStatusMap,
        estimatedTime,
        90 // Max 90%, then jump to 100% on complete
      );
      
      // Create FormData
      const formData = new FormData();
      formData.append('file', originalFile);
      
      // Upload
      const response = await api.post('/api/crew-certificates/multi-upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setFileProgressMap(prev => ({ ...prev, [failedFileName]: Math.min(progress, 90) }));
        }
      });
      
      // Success!
      progressController.complete();
      setFileStatusMap(prev => ({ ...prev, [failedFileName]: 'completed' }));
      setFileProgressMap(prev => ({ ...prev, [failedFileName]: 100 }));
      
      // Update progress to show completion
      setBatchProgress({ current: 1, total: 1 });
      
      // Update the result in BatchResultsModal
      const successResult = {
        filename: failedFileName,
        success: true,
        certificateCreated: true,
        certificateName: response.data?.cert_name || '',
        certificateNo: response.data?.cert_no || '',
        error: null
      };
      
      setBatchResults(prev => 
        prev.map(r => r.filename === failedFileName ? successResult : r)
      );
      
      toast.success(
        language === 'vi' 
          ? `✅ File đã được xử lý thành công!` 
          : `✅ File processed successfully!`
      );
      
      // Refresh list
      fetchCertificates();
      
      // Close ProcessingModal after a short delay
      setTimeout(() => {
        setIsBatchProcessing(false);
      }, 1500);
      
    } catch (error) {
      console.error('Retry error:', error);
      
      const errorMessage = error.response?.data?.detail || error.message || 'Processing failed';
      
      setFileStatusMap(prev => ({ ...prev, [failedFileName]: 'error' }));
      setFileSubStatusMap(prev => ({ ...prev, [failedFileName]: errorMessage }));
      
      // Update the result in BatchResultsModal with new error
      const failedResult = {
        filename: failedFileName,
        success: false,
        certificateCreated: false,
        certificateName: '',
        certificateNo: '',
        error: errorMessage
      };
      
      setBatchResults(prev => 
        prev.map(r => r.filename === failedFileName ? failedResult : r)
      );
      
      toast.error(
        language === 'vi' 
          ? `❌ File vẫn bị lỗi: ${errorMessage}` 
          : `❌ File still failed: ${errorMessage}`
      );
      
      // Close ProcessingModal after a short delay
      setTimeout(() => {
        setIsBatchProcessing(false);
      }, 1500);
    }
  };

  // Get ship/status for certificate (based on crew's ship_sign_on)
  const getCertificateShipStatus = (cert) => {
    if (cert.crew_id && crewList.length > 0) {
      const crew = crewList.find(c => c.id === cert.crew_id);
      if (crew) {
        const shipSignOn = crew.ship_sign_on || '-';
        if (shipSignOn === '-') {
          return { ship: 'Standby', isStandby: true };
        } else {
          return { ship: shipSignOn, isStandby: false };
        }
      }
    }
    return { ship: 'Unknown', isStandby: false };
  };

  // Get abbreviation from full organization name
  // Removed getAbbreviation - now using issued_by_abbreviation from backend (like Class & Flag Cert)

  // Handle sort
  const handleSort = (column) => {
    setSort(prev => ({
      column: column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const getSortIcon = (column) => {
    // Không hiển thị icon sort
    return null;
  };

  // Handle select
  const handleSelectCertificate = (certId) => {
    const newSelected = new Set(selectedCertificates);
    if (newSelected.has(certId)) {
      newSelected.delete(certId);
    } else {
      newSelected.add(certId);
    }
    setSelectedCertificates(newSelected);
  };

  const handleSelectAll = (checked, filteredCerts) => {
    if (checked) {
      const allVisibleIds = new Set(filteredCerts.map(cert => cert.id));
      setSelectedCertificates(allVisibleIds);
    } else {
      setSelectedCertificates(new Set());
    }
  };

  // Filter certificates
  const filteredCertificates = certificates.filter(cert => {
    // Search filter - bao gồm cả rank (chức danh)
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      if (!(
        cert.crew_name?.toLowerCase().includes(search) ||
        cert.rank?.toLowerCase().includes(search) ||
        cert.cert_name?.toLowerCase().includes(search) ||
        cert.cert_no?.toLowerCase().includes(search) ||
        cert.issued_by?.toLowerCase().includes(search)
      )) return false;
    }
    
    // Ship sign on filter
    if (filters.shipSignOn !== 'all') {
      const shipStatus = getCertificateShipStatus(cert);
      const certShipSignOn = shipStatus.isStandby ? '-' : shipStatus.ship;
      if (certShipSignOn !== filters.shipSignOn) {
        return false;
      }
    }
    
    // Status filter
    if (filters.status !== 'all' && cert.status !== filters.status) {
      return false;
    }
    
    // Crew name filter
    if (filters.crewName !== 'all' && cert.crew_name !== filters.crewName) {
      return false;
    }
    
    return true;
  });

  // Sort certificates
  const sortedCertificates = [...filteredCertificates].sort((a, b) => {
    if (!sort.column) return 0;
    
    // Special handling for ship_status column
    if (sort.column === 'ship_status') {
      const aShipStatus = getCertificateShipStatus(a);
      const bShipStatus = getCertificateShipStatus(b);
      
      let comparison = 0;
      if (aShipStatus.isStandby && !bShipStatus.isStandby) {
        comparison = -1;
      } else if (!aShipStatus.isStandby && bShipStatus.isStandby) {
        comparison = 1;
      } else {
        comparison = aShipStatus.ship.localeCompare(bShipStatus.ship);
      }
      
      return sort.direction === 'asc' ? comparison : -comparison;
    }
    
    // Standard sorting
    const aVal = a[sort.column] || '';
    const bVal = b[sort.column] || '';
    const comparison = aVal.toString().localeCompare(bVal.toString());
    return sort.direction === 'asc' ? comparison : -comparison;
  });

  // Get unique ship names from certificates
  const getUniqueShips = () => {
    // Không cần nữa - sẽ dùng ships từ props
    const shipSet = new Set();
    certificates.forEach(cert => {
      const shipStatus = getCertificateShipStatus(cert);
      if (shipStatus.isStandby) {
        shipSet.add('-');
      } else {
        shipSet.add(shipStatus.ship);
      }
    });
    
    return Array.from(shipSet).sort((a, b) => {
      if (a === '-') return -1;
      if (b === '-') return 1;
      return a.localeCompare(b);
    });
  };

  // Get unique crew names based on ship filter
  const getFilteredCrewNames = () => {
    let filteredCrew = crewList;
    
    if (filters.shipSignOn !== 'all') {
      filteredCrew = crewList.filter(crew => {
        const crewShipSignOn = crew.ship_sign_on || '-';
        return crewShipSignOn === filters.shipSignOn;
      });
    }
    
    return filteredCrew
      .map(crew => {
        const displayName = language === 'en' && crew.full_name_en ? crew.full_name_en : crew.full_name;
        return {
          value: crew.full_name,
          displayName: displayName.toUpperCase() // Viết hoa toàn bộ tên
        };
      })
      .sort((a, b) => a.displayName.localeCompare(b.displayName));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-1">
            {filters.crewName && filters.crewName !== 'all' ? (
              language === 'vi' 
                ? `Chứng chỉ thuyền viên của ${filters.crewName}` 
                : `Crew Certificates for ${filters.crewName}`
            ) : (
              language === 'vi' ? 'Chứng chỉ thuyền viên' : 'Crew Certificates'
            )}
          </h3>
          <p className="text-sm text-gray-600">
            {language === 'vi' ? 'Quản lý chứng chỉ thuyền viên' : 'Manage crew certificates'}
          </p>
        </div>
        
        {/* Action Buttons */}
        <div className="flex items-center space-x-3">
          {user && ['manager', 'admin', 'super_admin'].includes(user.role) && (
            <button 
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all flex items-center"
            >
              <span className="mr-2">📜</span>
              {language === 'vi' ? 'Thêm chứng chỉ' : 'Add Certificate'}
            </button>
          )}
          
          {/* Refresh Button */}
          <button 
            onClick={() => {
              fetchCertificates();
              toast.success(language === 'vi' ? 'Đã làm mới' : 'Refreshed');
            }}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-all flex items-center"
          >
            <span className="mr-2">🔄</span>
            {language === 'vi' ? 'Làm mới' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center space-x-4 flex-wrap">
          {/* Search */}
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600 whitespace-nowrap">
              {language === 'vi' ? '🔍 Tìm kiếm:' : '🔍 Search:'}
            </label>
            <div className="relative w-64">
              <input
                type="text"
                placeholder={language === 'vi' ? 'Tên thuyền viên, chức danh...' : 'Crew name, rank...'}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-1.5 pl-10 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
              <span className="absolute left-3 top-2 text-gray-400">🔍</span>
            </div>
          </div>
          
          {/* Divider */}
          <div className="h-8 w-px bg-gray-300"></div>
          
          {/* Ship Filter */}
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600 whitespace-nowrap">
              {language === 'vi' ? 'Tàu:' : 'Ship:'}
            </label>
            <select
              value={filters.shipSignOn}
              onChange={(e) => {
                const newValue = e.target.value;
                setFilters({...filters, shipSignOn: newValue, crewName: 'all'});
                
                // Clear selected ship when choosing "all" or "Standby" ("-")
                // to show Company Panel instead of Ship Info
                if ((newValue === 'all' || newValue === '-') && onShipSelect) {
                  onShipSelect(null);
                }
                
                onShipFilterChange?.(newValue);
              }}
              className="px-3 py-1.5 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white"
            >
              <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
              {ships && ships.map(ship => (
                <option key={ship.id} value={ship.name}>
                  {ship.name}
                </option>
              ))}
              <option value="-">{language === 'vi' ? 'Standby' : 'Standby'}</option>
            </select>
          </div>
          
          {/* Crew Name Filter */}
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600 whitespace-nowrap">
              {language === 'vi' ? 'Thuyền viên:' : 'Crew:'}
            </label>
            <select
              value={filters.crewName}
              onChange={(e) => setFilters({...filters, crewName: e.target.value})}
              className="px-3 py-1.5 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white max-w-xs"
            >
              <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
              {getFilteredCrewNames().map(item => (
                <option key={item.value} value={item.value}>
                  {item.displayName}
                </option>
              ))}
            </select>
          </div>
          
          {/* Status Filter */}
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600 whitespace-nowrap">
              {language === 'vi' ? 'Trạng thái:' : 'Status:'}
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="px-3 py-1.5 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white"
            >
              <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
              <option value="Valid">✅ {language === 'vi' ? 'Còn hiệu lực' : 'Valid'}</option>
              <option value="Critical">🟠 {language === 'vi' ? 'Khẩn cấp' : 'Critical'}</option>
              <option value="Expiring Soon">⚠️ {language === 'vi' ? 'Sắp hết hạn' : 'Expiring Soon'}</option>
              <option value="Expired">❌ {language === 'vi' ? 'Hết hiệu lực' : 'Expired'}</option>
              <option value="Unknown">❓ {language === 'vi' ? 'Không xác định' : 'Unknown'}</option>
            </select>
          </div>
          
          {/* Reset Button */}
          {(filters.shipSignOn !== 'all' || filters.status !== 'all' || filters.crewName !== 'all' || searchTerm) && (
            <button
              onClick={() => {
                setFilters({ shipSignOn: 'all', status: 'all', crewName: 'all' });
                setSearchTerm('');
                onShipFilterChange?.('all');
              }}
              className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md text-sm flex items-center transition-colors"
            >
              <span className="mr-1">🔄</span>
              {language === 'vi' ? 'Xóa bộ lọc' : 'Clear'}
            </button>
          )}
          
          {/* Results Count */}
          <div className="flex items-center ml-auto">
            <p className="text-sm text-gray-600 whitespace-nowrap">
              {language === 'vi' ? 'Hiển thị' : 'Showing'} <span className="font-semibold">{sortedCertificates.length}</span> / <span className="font-semibold">{certificates.length}</span> {language === 'vi' ? 'chứng chỉ' : 'certificates'}
            </p>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {/* Checkbox + STT */}
                <th className="px-3 py-3 text-left border-r border-gray-200">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={sortedCertificates.length > 0 && sortedCertificates.every(cert => selectedCertificates.has(cert.id))}
                      onChange={(e) => handleSelectAll(e.target.checked, sortedCertificates)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                    />
                    <span className="text-sm font-bold text-gray-700 tracking-wider">
                      {language === 'vi' ? 'STT' : 'No.'}
                    </span>
                  </div>
                </th>
                <th 
                  onClick={() => handleSort('cert_name')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'}
                  {getSortIcon('cert_name')}
                </th>
                <th 
                  onClick={() => handleSort('crew_name')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Tên thuyền viên' : 'Crew Name'}
                  {getSortIcon('crew_name')}
                </th>
                <th 
                  onClick={() => handleSort('ship_status')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Tàu / Trạng thái' : 'Ship / Status'}
                  {getSortIcon('ship_status')}
                </th>
                <th 
                  onClick={() => handleSort('rank')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Chức danh' : 'Rank'}
                  {getSortIcon('rank')}
                </th>
                <th 
                  onClick={() => handleSort('cert_no')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Số chứng chỉ' : 'Certificate No.'}
                  {getSortIcon('cert_no')}
                </th>
                <th 
                  onClick={() => handleSort('issued_by')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Cơ quan cấp' : 'Issued By'}
                  {getSortIcon('issued_by')}
                </th>
                <th 
                  onClick={() => handleSort('issued_date')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Ngày cấp' : 'Issued Date'}
                  {getSortIcon('issued_date')}
                </th>
                <th 
                  onClick={() => handleSort('cert_expiry')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Ngày hết hạn' : 'Expiry Date'}
                  {getSortIcon('cert_expiry')}
                </th>
                <th 
                  onClick={() => handleSort('status')}
                  className="px-3 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Trạng thái' : 'Status'}
                  {getSortIcon('status')}
                </th>
                <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200">
                  {language === 'vi' ? 'Ghi chú' : 'Note'}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="11" className="px-6 py-8 text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <p className="mt-2 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
                  </td>
                </tr>
              ) : sortedCertificates.length > 0 ? (
                sortedCertificates.map((cert, index) => (
                  <tr 
                    key={cert.id} 
                    className={`hover:bg-gray-50 ${selectedCertificates.has(cert.id) ? 'bg-blue-50' : ''}`}
                    onContextMenu={(e) => handleRowRightClick(e, cert)}
                  >
                    {/* Checkbox + STT */}
                    <td className="px-3 py-4 whitespace-nowrap border-r border-gray-200">
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={selectedCertificates.has(cert.id)}
                          onChange={() => handleSelectCertificate(cert.id)}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                        />
                        <span className="text-sm text-gray-900">
                          {index + 1}
                        </span>
                      </div>
                    </td>
                    {/* Certificate Name */}
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      <div className="flex items-center space-x-2">
                        <span>{cert.cert_name}</span>
                        {cert.crew_cert_file_id && (
                          <span 
                            className="text-green-500 text-xs cursor-pointer hover:text-green-600" 
                            title={language === 'vi' ? 'File gốc' : 'Original file'}
                            onClick={() => window.open(`https://drive.google.com/file/d/${cert.crew_cert_file_id}/view`, '_blank')}
                          >
                            📄
                          </span>
                        )}
                        {cert.crew_cert_summary_file_id && (
                          <span 
                            className="text-blue-500 text-xs cursor-pointer hover:text-blue-600" 
                            title={language === 'vi' ? 'File tóm tắt' : 'Summary file'}
                            onClick={() => window.open(`https://drive.google.com/file/d/${cert.crew_cert_summary_file_id}/view`, '_blank')}
                          >
                            📋
                          </span>
                        )}
                      </div>
                    </td>
                    {/* Crew Name */}
                    <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900 border-r border-gray-200 uppercase">
                      {language === 'en' && cert.crew_name_en ? cert.crew_name_en : cert.crew_name}
                    </td>
                    {/* Ship/Status */}
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {(() => {
                        const shipStatus = getCertificateShipStatus(cert);
                        return (
                          <span className={shipStatus.isStandby ? 'text-orange-600 font-medium' : 'text-blue-600'}>
                            {shipStatus.ship}
                          </span>
                        );
                      })()}
                    </td>
                    {/* Rank */}
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {cert.rank || '-'}
                    </td>
                    {/* Certificate No. */}
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {cert.cert_no}
                    </td>
                    <td 
                      className="px-4 py-4 whitespace-nowrap text-sm font-semibold text-blue-700 border-r border-gray-200 cursor-help"
                      title={cert.issued_by || ''}
                    >
                      {cert.issued_by_abbreviation || (cert.issued_by ? 
                        (cert.issued_by.length > 8 ? `${cert.issued_by.substring(0, 8)}...` : cert.issued_by)
                        : '-'
                      )}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {formatDateDisplay(cert.issued_date) || '-'}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {formatDateDisplay(cert.cert_expiry) || '-'}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap border-r border-gray-200">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        cert.status === 'Valid' ? 'bg-green-100 text-green-800' :
                        cert.status === 'Critical' ? 'bg-orange-200 text-orange-900' :
                        cert.status === 'Expiring Soon' ? 'bg-yellow-100 text-yellow-800' :
                        cert.status === 'Expired' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {cert.status === 'Valid' ? (language === 'vi' ? 'Còn hạn' : 'Valid') :
                         cert.status === 'Critical' ? (language === 'vi' ? 'Khẩn cấp' : 'Critical') :
                         cert.status === 'Expiring Soon' ? (language === 'vi' ? 'Sắp hết hạn' : 'Expiring Soon') :
                         cert.status === 'Expired' ? (language === 'vi' ? 'Hết hạn' : 'Expired') :
                         cert.status || '-'}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-900 border-r border-gray-200 text-center">
                      {cert.note ? (
                        <span
                          className="text-red-600 cursor-help text-lg font-bold"
                          onMouseEnter={(e) => handleNoteMouseEnter(e, cert.note)}
                          onMouseLeave={handleNoteMouseLeave}
                        >
                          *
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="11" className="px-6 py-12 text-center">
                    <div className="text-gray-400 text-lg mb-2">📜</div>
                    <p className="text-gray-500">
                      {language === 'vi' ? 'Chưa có chứng chỉ nào' : 'No certificates found'}
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Certificate Modal */}
      {showAddModal && (
        <AddCrewCertificateModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            fetchCertificates();
          }}
          onBatchUpload={(files, preSelectedCrewId) => {
            setShowAddModal(false);
            handleBatchUpload(files, preSelectedCrewId);
          }}
          selectedShip={selectedShip}
          ships={ships}
          preSelectedCrewName={filters.crewName !== 'all' ? filters.crewName : null}
          allCrewList={crewList}
        />
      )}

      {/* Edit Certificate Modal */}
      {showEditModal && certificateToEdit && (
        <EditCrewCertificateModal
          certificate={certificateToEdit}
          ships={ships}
          allCrewList={crewList}
          onClose={() => {
            setShowEditModal(false);
            setCertificateToEdit(null);
          }}
          onSuccess={() => {
            setShowEditModal(false);
            setCertificateToEdit(null);
            fetchCertificates();
          }}
        />
      )}

      {/* Delete Certificate Modal */}
      {showDeleteModal && certificatesToDelete && (
        <DeleteCertificateModal
          certificates={Array.isArray(certificatesToDelete) ? certificatesToDelete : [certificatesToDelete]}
          onCancel={() => {
            setShowDeleteModal(false);
            setCertificatesToDelete(null);
          }}
          onConfirm={handleDelete}
          isDeleting={isDeleting}
        />
      )}

      {/* Context Menu */}
      {contextMenu && (
        <CertificateContextMenu
          certificate={contextMenu.certificate}
          position={contextMenu.position}
          onClose={() => setContextMenu(null)}
          onEdit={() => handleEdit(contextMenu.certificate)}
          onDelete={() => {
            // Check if multiple certificates are selected
            if (selectedCertificates.size > 1) {
              // Bulk delete - get all selected certificates
              const selectedCerts = sortedCertificates.filter(cert => 
                selectedCertificates.has(cert.id)
              );
              setCertificatesToDelete(selectedCerts);
            } else {
              // Single delete
              setCertificatesToDelete(contextMenu.certificate);
            }
            setShowDeleteModal(true);
            setContextMenu(null);
          }}
          onViewOriginal={() => handleViewOriginal(contextMenu.certificate)}
          onViewSummary={() => handleViewSummary(contextMenu.certificate)}
          onCopyLink={() => handleCopyLink(contextMenu.certificate)}
          onDownload={() => handleDownload(contextMenu.certificate)}
          onAutoRename={() => {
            handleAutoRename(contextMenu.certificate.id);
            setContextMenu(null);
          }}
          selectedCount={selectedCertificates.size}
        />
      )}

      {/* Batch Processing Modal */}
      <BatchProcessingModal
        isOpen={isBatchProcessing}
        progress={batchProgress}
        fileProgressMap={fileProgressMap}
        fileStatusMap={fileStatusMap}
        fileSubStatusMap={fileSubStatusMap}
        isMinimized={isBatchMinimized}
        onMinimize={() => setIsBatchMinimized(true)}
        onRestore={() => setIsBatchMinimized(false)}
        onRetryFile={handleRetryFailedFile}
        language={language}
        title={language === 'vi' ? 'Đang xử lý Crew Certificates' : 'Processing Crew Certificates'}
      />

      {/* Batch Results Modal */}
      <BatchResultsModal
        isOpen={showBatchResults}
        onClose={() => setShowBatchResults(false)}
        results={batchResults}
        onRetryFile={handleRetryFailedFile}
        language={language}
      />

      {/* Note Tooltip */}
      {noteTooltip.show && (
        <div
          className="fixed bg-gray-800 text-white p-3 rounded-lg shadow-2xl z-50 border border-gray-600"
          style={{
            left: `${noteTooltip.x}px`,
            top: `${noteTooltip.y}px`,
            width: `${noteTooltip.width}px`,
            maxHeight: '200px',
            overflowY: 'auto',
            fontSize: '14px',
            lineHeight: '1.5'
          }}
        >
          {noteTooltip.content}
        </div>
      )}
    </div>
  );
};

export default CrewCertificateTable;
