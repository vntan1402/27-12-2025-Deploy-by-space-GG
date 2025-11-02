import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import api from '../../services/api';
import { formatDateDisplay } from '../../utils/dateHelpers';
import AddCrewCertificateModal from './AddCrewCertificateModal';
import EditCrewCertificateModal from './EditCrewCertificateModal';
import CertificateContextMenu from './CertificateContextMenu';
import DeleteCertificateModal from './DeleteCertificateModal';
import { BatchProcessingModal } from './BatchProcessingModal';
import { BatchResultsModal } from './BatchResultsModal';

const CrewCertificateTable = ({ selectedShip, ships, onShipFilterChange, onShipSelect }) => {
  const { language, user } = useAuth();
  
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
  const [showBatchResults, setShowBatchResults] = useState(false);
  const [batchResults, setBatchResults] = useState([]);
  
  // Filters
  const [filters, setFilters] = useState({
    shipSignOn: 'all',
    status: 'all',
    crewName: 'all'
  });
  
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
    setContextMenu({
      certificate: cert,
      position: { x: e.clientX, y: e.clientY }
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
      
      // Delete each certificate
      for (const cert of certsArray) {
        await api.delete(`/api/crew-certificates/${cert.id}`);
      }
      
      toast.success(language === 'vi' 
        ? `✅ Đã xóa ${certsArray.length} chứng chỉ` 
        : `✅ Deleted ${certsArray.length} certificate(s)`);
      
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
    Array.from(files).forEach(file => {
      initialStatusMap[file.name] = 'waiting';
      initialProgressMap[file.name] = 0;
      initialSubStatusMap[file.name] = '';
    });
    setFileStatusMap(initialStatusMap);
    setFileProgressMap(initialProgressMap);
    setFileSubStatusMap(initialSubStatusMap);

    const results = [];

    // Process files with staggered delay (300ms)
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      try {
        // Update status to processing
        setFileStatusMap(prev => ({ ...prev, [file.name]: 'processing' }));
        setFileSubStatusMap(prev => ({ ...prev, [file.name]: language === 'vi' ? 'Đang phân tích AI...' : 'AI analyzing...' }));
        setFileProgressMap(prev => ({ ...prev, [file.name]: 10 }));

        // Step 1: AI Analysis
        const formData = new FormData();
        formData.append('cert_file', file);
        if (selectedShip && selectedShip.id) {
          formData.append('ship_id', selectedShip.id);
        }
        if (preSelectedCrewId) {
          formData.append('crew_id', preSelectedCrewId);
        }

        setFileProgressMap(prev => ({ ...prev, [file.name]: 30 }));
        const analysisResponse = await api.post('/api/crew-certificates/analyze-file', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        setFileProgressMap(prev => ({ ...prev, [file.name]: 50 }));
        setFileSubStatusMap(prev => ({ ...prev, [file.name]: language === 'vi' ? 'Tạo chứng chỉ...' : 'Creating certificate...' }));

        const analysisData = analysisResponse.data;

        // Step 2: Create certificate record
        const createData = {
          crew_id: analysisData.crew_id,
          cert_name: analysisData.cert_name,
          cert_no: analysisData.cert_no,
          issued_by: analysisData.issued_by,
          issued_date: analysisData.issued_date,
          cert_expiry: analysisData.cert_expiry,
          note: analysisData.note || '',
          _file_content: analysisData._file_content,
          _summary_text: analysisData._summary_text
        };

        setFileProgressMap(prev => ({ ...prev, [file.name]: 70 }));
        const createResponse = await api.post('/api/crew-certificates/manual', createData);

        setFileProgressMap(prev => ({ ...prev, [file.name]: 85 }));
        setFileSubStatusMap(prev => ({ ...prev, [file.name]: language === 'vi' ? 'Upload file lên Drive...' : 'Uploading to Drive...' }));

        // Step 3: Upload file
        const certId = createResponse.data.id;
        const uploadFormData = new FormData();
        uploadFormData.append('files', file);

        await api.post(`/api/crew-certificates/${certId}/upload-files`, uploadFormData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        setFileProgressMap(prev => ({ ...prev, [file.name]: 100 }));
        setFileStatusMap(prev => ({ ...prev, [file.name]: 'completed' }));
        setFileSubStatusMap(prev => ({ ...prev, [file.name]: '' }));

        results.push({
          success: true,
          filename: file.name,
          crew_name: analysisData.crew_name,
          cert_name: analysisData.cert_name,
          cert_no: analysisData.cert_no,
          certCreated: true,
          fileUploaded: true
        });

      } catch (error) {
        console.error(`Batch upload error for ${file.name}:`, error);
        setFileStatusMap(prev => ({ ...prev, [file.name]: 'error' }));
        setFileSubStatusMap(prev => ({ ...prev, [file.name]: '' }));
        
        results.push({
          success: false,
          filename: file.name,
          error: error.response?.data?.detail || error.message || 'Unknown error'
        });
      }

      // Update progress
      setBatchProgress({ current: i + 1, total: files.length });

      // Staggered delay (300ms) between files (except after last file)
      if (i < files.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 300));
      }
    }

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
  const getAbbreviation = (fullName) => {
    if (!fullName || fullName === '-') return '-';
    
    const words = fullName.trim().split(/\s+/);
    const abbreviation = words
      .map(word => word.charAt(0).toUpperCase())
      .join('');
    
    return abbreviation;
  };

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
      .map(crew => ({
        value: crew.full_name,
        displayName: language === 'en' && crew.full_name_en ? crew.full_name_en : crew.full_name
      }))
      .sort((a, b) => a.displayName.localeCompare(b.displayName));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-1">
            {language === 'vi' ? 'Chứng chỉ thuyền viên' : 'Crew Certificates'}
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
                setFilters({...filters, shipSignOn: e.target.value, crewName: 'all'});
                onShipFilterChange?.(e.target.value);
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
                {/* Checkbox */}
                <th className="px-3 py-3 text-center border-r border-gray-200">
                  <input
                    type="checkbox"
                    checked={sortedCertificates.length > 0 && sortedCertificates.every(cert => selectedCertificates.has(cert.id))}
                    onChange={(e) => handleSelectAll(e.target.checked, sortedCertificates)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                  />
                </th>
                <th className="px-3 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200">
                  {language === 'vi' ? 'STT' : 'No.'}
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
                  onClick={() => handleSort('cert_name')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'}
                  {getSortIcon('cert_name')}
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
                  <td colSpan="12" className="px-6 py-8 text-center">
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
                    <td className="px-3 py-4 whitespace-nowrap text-center border-r border-gray-200">
                      <input
                        type="checkbox"
                        checked={selectedCertificates.has(cert.id)}
                        onChange={() => handleSelectCertificate(cert.id)}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                      />
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {index + 1}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900 border-r border-gray-200 uppercase">
                      {language === 'en' && cert.crew_name_en ? cert.crew_name_en : cert.crew_name}
                    </td>
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
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {cert.rank || '-'}
                    </td>
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
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {cert.cert_no}
                    </td>
                    <td 
                      className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 cursor-help"
                      title={cert.issued_by || ''}
                    >
                      <span className="font-medium">
                        {getAbbreviation(cert.issued_by)}
                      </span>
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
                    <td className="px-4 py-4 text-sm text-gray-900 border-r border-gray-200">
                      <div className="max-w-xs truncate" title={cert.note}>
                        {cert.note || '-'}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="12" className="px-6 py-12 text-center">
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
            setCertificatesToDelete(contextMenu.certificate);
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
    </div>
  );
};

export default CrewCertificateTable;
