import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout, Sidebar, SubMenuBar, CertificateTable, CertificateFilters, CertificateActionButtons, AddShipCertificateModal, UpcomingSurveyModal, CertificateNotesModal } from '../components';
import { EditShipCertificateModal, DeleteShipCertificateModal } from '../components/ShipCertificates';
import { ShipDetailPanel } from '../components/ShipDetailPanel';
import { EditShipModal, DeleteShipConfirmationModal, AddShipModal } from '../components/Ships';
import { shipService, shipCertificateService } from '../services';
import api from '../services/api';
import { toast } from 'sonner';
import { shortenClassSociety } from '../utils/shipHelpers';
import { compareDates } from '../utils/dateHelpers';

const ClassAndFlagCert = () => {
  const { language, user } = useAuth();
  const location = useLocation();
  
  // State
  const [selectedCategory] = useState('ship_certificates');
  const [selectedSubMenu, setSelectedSubMenu] = useState('certificates');
  const [showShipModal, setShowShipModal] = useState(false);
  const [showAddShipModal, setShowAddShipModal] = useState(false);
  const [showEditShipModal, setShowEditShipModal] = useState(false);
  const [showDeleteShipModal, setShowDeleteShipModal] = useState(false);
  const [ships, setShips] = useState([]);
  const [selectedShip, setSelectedShip] = useState(null);
  const [deleteShipData, setDeleteShipData] = useState(null);
  const [isDeletingShip, setIsDeletingShip] = useState(false);
  const [loading, setLoading] = useState(false);

  // Certificate states
  const [certificates, setCertificates] = useState([]);
  const [certificatesLoading, setCertificatesLoading] = useState(false);
  const [selectedCertificates, setSelectedCertificates] = useState(new Set());
  const [showAddShipCertificateModal, setShowAddShipCertificateModal] = useState(false);
  const [showEditShipCertificateModal, setShowEditShipCertificateModal] = useState(false);
  const [showDeleteShipCertificateModal, setShowDeleteShipCertificateModal] = useState(false);
  const [editingCertificate, setEditingCertificate] = useState(null);
  const [deletingCertificate, setDeletingCertificate] = useState(null);
  
  // Filter states
  const [certificateFilters, setCertificateFilters] = useState({
    certificateType: 'all',
    status: 'all',
    search: '',
  });
  
  // Sort state
  const [certificateSort, setCertificateSort] = useState({
    column: 'cert_abbreviation',
    direction: 'asc',
  });
  
  // Action states
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isUpdatingSurveyTypes, setIsUpdatingSurveyTypes] = useState(false);
  const [isMultiCertProcessing, setIsMultiCertProcessing] = useState(false);
  
  // AI Config state
  const [aiConfig, setAiConfig] = useState(null);
  
  // Context menu state (for right-click actions)
  const [contextMenu, setContextMenu] = useState(null);
  const [surveyTypeContextMenu, setSurveyTypeContextMenu] = useState(null);
  
  // Upcoming survey modal state
  const [upcomingSurveyModal, setUpcomingSurveyModal] = useState({
    show: false,
    surveys: [],
    totalCount: 0,
    company: '',
    companyName: '',
    checkDate: ''
  });

  // Link caching state for certificate files
  const [certificateLinksCache, setCertificateLinksCache] = useState({});
  const [linksFetching, setLinksFetching] = useState(false);
  const [linksFetchProgress, setLinksFetchProgress] = useState({ ready: 0, total: 0 });

  // Notes modal state
  const [notesModal, setNotesModal] = useState({
    show: false,
    certificate: null,
    notes: ''
  });

  // Auto rename state
  const [showAutoRenameDialog, setShowAutoRenameDialog] = useState(false);
  const [batchRenameProgress, setBatchRenameProgress] = useState({
    isRunning: false,
    completed: 0,
    total: 0,
    current: '',
    errors: []
  });

  // Fetch ships on mount
  useEffect(() => {
    fetchShips();
    fetchAiConfig();
  }, []);

  // Fetch AI Config
  const fetchAiConfig = async () => {
    try {
      const response = await api.get('/api/ai-config');
      if (response.data && response.data.length > 0) {
        // Use first active config
        const activeConfig = response.data.find(config => config.is_active) || response.data[0];
        setAiConfig(activeConfig);
      }
    } catch (error) {
      console.error('Error fetching AI config:', error);
      // Don't show error toast, just log it
    }
  };

  // Handle navigation from Add Ship - refresh when new ship is created
  useEffect(() => {
    if (location.state?.refresh) {
      console.log('Refreshing ship list after new ship creation:', location.state);
      fetchShips();
      
      // Clear the location state to prevent re-triggering on subsequent renders
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const fetchShips = async () => {
    try {
      console.log('Fetching ships...');
      setLoading(true);
      const response = await shipService.getAllShips();
      console.log('Ships fetched successfully:', response);
      const data = response.data || response || []; // Handle different response formats
      
      // Ensure data is array
      if (!Array.isArray(data)) {
        console.error('Ships response is not an array:', data);
        setShips([]);
      } else {
        setShips(data);
      }
      
      // Don't auto-select, let user choose via Ship Select button
      // If no ship selected and ships available, could optionally show modal
      // setShowShipModal(true); // Uncomment to auto-show modal
    } catch (error) {
      console.error('Failed to fetch ships:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách tàu' : 'Failed to load ships');
      setShips([]); // Set empty array on error
    } finally {
      console.log('Setting loading to false');
      setLoading(false);
    }
  };

  // ===== CERTIFICATE FUNCTIONS =====
  
  // Fetch certificates for selected ship
  const fetchCertificates = async (shipId) => {
    if (!shipId) {
      setCertificates([]);
      return;
    }
    
    try {
      setCertificatesLoading(true);
      const response = await api.get(`/api/ships/${shipId}/certificates`);
      const data = response.data || [];
      setCertificates(Array.isArray(data) ? data : []);
      
      // Pre-fetch Google Drive links in background
      prefetchCertificateLinks(data);
    } catch (error) {
      console.error('Failed to fetch certificates:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách chứng chỉ' : 'Failed to load certificates');
      setCertificates([]);
    } finally {
      setCertificatesLoading(false);
    }
  };

  // Pre-fetch Google Drive links for certificates
  const prefetchCertificateLinks = async (certs) => {
    if (!certs || certs.length === 0) return;

    // Filter certificates that have file IDs and are not already cached
    const certsWithFiles = certs.filter(cert => 
      cert.google_drive_file_id && !certificateLinksCache[cert.google_drive_file_id]
    );

    if (certsWithFiles.length === 0) {
      setLinksFetchProgress({ ready: certs.filter(c => c.google_drive_file_id).length, total: certs.filter(c => c.google_drive_file_id).length });
      return;
    }

    setLinksFetching(true);
    setLinksFetchProgress({ ready: 0, total: certsWithFiles.length });

    let fetchedCount = 0;
    const newCache = { ...certificateLinksCache };

    // Fetch links in batches to avoid overwhelming the server
    const batchSize = 5;
    for (let i = 0; i < certsWithFiles.length; i += batchSize) {
      const batch = certsWithFiles.slice(i, i + batchSize);
      
      await Promise.allSettled(
        batch.map(async (cert) => {
          try {
            const response = await api.get(`/api/gdrive/file/${cert.google_drive_file_id}/view`);
            if (response.data?.success && response.data?.view_url) {
              newCache[cert.google_drive_file_id] = response.data.view_url;
              fetchedCount++;
              setLinksFetchProgress({ ready: fetchedCount, total: certsWithFiles.length });
            }
          } catch (error) {
            console.warn(`Failed to fetch link for certificate ${cert.cert_abbreviation}:`, error);
          }
        })
      );

      // Small delay between batches
      if (i + batchSize < certsWithFiles.length) {
        await new Promise(resolve => setTimeout(resolve, 200));
      }
    }

    setCertificateLinksCache(newCache);
    setLinksFetching(false);
  };

  // Fetch certificates when ship is selected
  useEffect(() => {
    if (selectedShip?.id) {
      fetchCertificates(selectedShip.id);
    } else {
      setCertificates([]);
    }
  }, [selectedShip?.id]);

  // Get unique certificate types for filter dropdown
  const getUniqueCertificateTypes = () => {
    const types = new Set();
    certificates.forEach(cert => {
      if (cert.cert_type) types.add(cert.cert_type);
    });
    return Array.from(types).sort();
  };

  // Get certificate status
  const getCertificateStatus = (cert) => {
    if (!cert.valid_date) return 'Unknown';
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const validDate = new Date(cert.valid_date);
    validDate.setHours(0, 0, 0, 0);
    
    if (validDate < today) return 'Expired';
    
    const diffTime = validDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays <= 30) return 'Over Due';
    return 'Valid';
  };

  // Apply filters and sort to certificates
  const getFilteredCertificates = () => {
    let filtered = [...certificates];

    // Apply certificate type filter
    if (certificateFilters.certificateType !== 'all') {
      filtered = filtered.filter(cert => cert.cert_type === certificateFilters.certificateType);
    }

    // Apply status filter
    if (certificateFilters.status !== 'all') {
      filtered = filtered.filter(cert => getCertificateStatus(cert) === certificateFilters.status);
    }

    // Apply search filter
    if (certificateFilters.search) {
      const searchLower = certificateFilters.search.toLowerCase();
      filtered = filtered.filter(cert => 
        (cert.cert_name && cert.cert_name.toLowerCase().includes(searchLower)) ||
        (cert.cert_abbreviation && cert.cert_abbreviation.toLowerCase().includes(searchLower)) ||
        (cert.cert_no && cert.cert_no.toLowerCase().includes(searchLower))
      );
    }

    // Apply sorting
    if (certificateSort.column) {
      filtered.sort((a, b) => {
        let aVal = a[certificateSort.column];
        let bVal = b[certificateSort.column];

        // Handle date sorting
        if (['issue_date', 'valid_date', 'last_endorse', 'next_survey'].includes(certificateSort.column)) {
          return compareDates(aVal, bVal) * (certificateSort.direction === 'asc' ? 1 : -1);
        }

        // Handle string sorting
        if (typeof aVal === 'string') aVal = aVal.toLowerCase();
        if (typeof bVal === 'string') bVal = bVal.toLowerCase();

        if (aVal < bVal) return certificateSort.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return certificateSort.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  };

  // Handle certificate sort
  const handleCertificateSort = (column) => {
    setCertificateSort(prev => ({
      column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  // Handle certificate selection
  const handleSelectCertificate = (certId) => {
    setSelectedCertificates(prev => {
      const newSet = new Set(prev);
      if (newSet.has(certId)) {
        newSet.delete(certId);
      } else {
        newSet.add(certId);
      }
      return newSet;
    });
  };

  // Handle select all certificates
  const handleSelectAllCertificates = (checked) => {
    if (checked) {
      const allIds = getFilteredCertificates().map(cert => cert.id);
      setSelectedCertificates(new Set(allIds));
    } else {
      setSelectedCertificates(new Set());
    }
  };

  // Handle certificate double click - open PDF
  const handleCertificateDoubleClick = async (cert) => {
    if (!cert.google_drive_file_id) {
      toast.warning(language === 'vi' ? 'Chứng chỉ chưa có file đính kèm' : 'Certificate has no attached file');
      return;
    }

    try {
      // Check cache first
      if (certificateLinksCache[cert.google_drive_file_id]) {
        window.open(certificateLinksCache[cert.google_drive_file_id], '_blank', 'noopener,noreferrer');
        toast.success(language === 'vi' ? 'Đang mở file chứng chỉ...' : 'Opening certificate file...');
        return;
      }

      // Fetch from API if not cached
      const response = await api.get(`/api/gdrive/file/${cert.google_drive_file_id}/view`);
      if (response.data?.success && response.data?.view_url) {
        // Cache the link
        setCertificateLinksCache(prev => ({
          ...prev,
          [cert.google_drive_file_id]: response.data.view_url
        }));
        
        window.open(response.data.view_url, '_blank', 'noopener,noreferrer');
        toast.success(language === 'vi' ? 'Đang mở file chứng chỉ...' : 'Opening certificate file...');
      } else {
        toast.error(language === 'vi' ? 'Không thể mở file chứng chỉ' : 'Cannot open certificate file');
      }
    } catch (error) {
      console.error('Error opening certificate file:', error);
      toast.error(language === 'vi' ? 'Lỗi khi mở file chứng chỉ' : 'Error opening certificate file');
    }
  };

  // Handle certificate right click - context menu
  const handleCertificateRightClick = (e, cert) => {
    e.preventDefault();
    
    // Calculate position with boundary check
    const menuWidth = 250; // Approximate menu width
    const menuHeight = 400; // Approximate menu height
    
    let x = e.clientX;
    let y = e.clientY;
    
    // Check if menu would overflow right edge
    if (x + menuWidth > window.innerWidth) {
      x = window.innerWidth - menuWidth - 10; // 10px padding
    }
    
    // Check if menu would overflow bottom edge
    if (y + menuHeight > window.innerHeight) {
      y = window.innerHeight - menuHeight - 10; // 10px padding
    }
    
    // Ensure menu doesn't go off left or top edge
    if (x < 10) x = 10;
    if (y < 10) y = 10;
    
    setContextMenu({
      x: x,
      y: y,
      certificate: cert,
    });
  };

  // Handle survey type right click - quick edit
  const handleSurveyTypeRightClick = (e, certId, currentType) => {
    e.preventDefault();
    e.stopPropagation();
    setSurveyTypeContextMenu({
      x: e.clientX,
      y: e.clientY,
      certId,
      currentType,
    });
  };

  // Close context menus on click outside
  useEffect(() => {
    const handleClick = () => {
      setContextMenu(null);
      setSurveyTypeContextMenu(null);
    };
    
    if (contextMenu || surveyTypeContextMenu) {
      document.addEventListener('click', handleClick);
      return () => document.removeEventListener('click', handleClick);
    }
  }, [contextMenu, surveyTypeContextMenu]);

  // Handle refresh certificates
  const handleRefreshCertificates = async () => {
    if (!selectedShip?.id) return;
    
    setIsRefreshing(true);
    try {
      await fetchCertificates(selectedShip.id);
      toast.success(language === 'vi' ? 'Đã cập nhật danh sách chứng chỉ!' : 'Certificate list refreshed!');
    } catch (error) {
      console.error('Error refreshing certificates:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Handle update survey types (placeholder)
  const handleUpdateSurveyTypes = async () => {
    if (!selectedShip?.id) {
      toast.warning(language === 'vi' ? 'Vui lòng chọn tàu trước' : 'Please select a ship first');
      return;
    }
    
    try {
      setIsUpdatingSurveyTypes(true);
      
      toast.info(language === 'vi' 
        ? 'Đang cập nhật Next Survey dựa trên quy định IMO và chu kỳ 5 năm...'
        : 'Updating Next Survey based on IMO regulations and 5-year cycle...'
      );

      // Call backend API to update next survey types
      const response = await api.post(`/api/ships/${selectedShip.id}/update-next-survey`);
      
      const result = response.data;
      
      if (result.success) {
        // Show detailed success message
        toast.success(language === 'vi' 
          ? `✅ Đã cập nhật Next Survey cho ${result.updated_count}/${result.total_certificates} chứng chỉ của tàu ${result.ship_name}`
          : `✅ Updated Next Survey for ${result.updated_count}/${result.total_certificates} certificates of ship ${result.ship_name}`
        );
        
        // Show sample changes
        if (result.results && result.results.length > 0) {
          const sampleChanges = result.results.slice(0, 2);
          const changesSummary = sampleChanges.map(cert => 
            `${cert.cert_name}: ${cert.new_next_survey_type}`
          ).join('; ');
          
          if (changesSummary) {
            setTimeout(() => {
              toast.info(language === 'vi' 
                ? `Ví dụ cập nhật: ${changesSummary}`
                : `Sample updates: ${changesSummary}`, 
                { duration: 8000 }
              );
            }, 2000);
          }
        }
        
        // Refresh certificates list
        await fetchCertificates(selectedShip.id);
      } else {
        toast.warning(result.message || (language === 'vi' 
          ? 'Không thể cập nhật Next Survey'
          : 'Could not update Next Survey'
        ));
      }
    } catch (error) {
      console.error('Next Survey update error:', error);
      toast.error(language === 'vi' 
        ? `❌ Lỗi khi cập nhật Next Survey: ${error.response?.data?.detail || error.message}`
        : `❌ Error updating Next Survey: ${error.response?.data?.detail || error.message}`
      );
    } finally {
      setIsUpdatingSurveyTypes(false);
    }
  };

  // Handle upcoming survey check (placeholder)
  const handleUpcomingSurvey = async () => {
    try {
      console.log('🔍 Checking upcoming surveys...');
      
      // First check server current date
      try {
        const dateResponse = await api.get('/api/system/current-datetime');
        console.log('📅 Server current date/time:', dateResponse.data);
        console.log(`Server date: ${dateResponse.data.formatted}`);
        console.log(`Timezone: ${dateResponse.data.timezone} (${dateResponse.data.timezone_offset})`);
      } catch (dateError) {
        console.warn('Could not fetch server datetime:', dateError);
      }
      
      const response = await api.get('/api/certificates/upcoming-surveys');
      const data = response.data;
      
      console.log('📊 Upcoming surveys response:', data);
      console.log(`Total certificates checked: ${data.total_count || 0}`);
      console.log(`Surveys in window: ${data.upcoming_surveys?.length || 0}`);
      
      if (data.upcoming_surveys && data.upcoming_surveys.length > 0) {
        setUpcomingSurveyModal({
          show: true,
          surveys: data.upcoming_surveys,
          totalCount: data.total_count,
          company: data.company,
          companyName: data.company_name,
          checkDate: data.check_date
        });
        
        toast.info(language === 'vi' 
          ? `⚠️ Có ${data.upcoming_surveys.length} chứng chỉ trong survey window (±3 tháng)`
          : `⚠️ ${data.upcoming_surveys.length} certificates in survey window (±3 months)`
        );
      } else {
        console.log('✅ No surveys in current window (±3 months from today)');
        toast.success(language === 'vi' 
          ? '✅ Không có survey trong window hiện tại (±3 tháng)\n💡 Surveys xa hơn sẽ không hiển thị'
          : '✅ No surveys in current window (±3 months)\n💡 Future surveys beyond window won\'t show'
        );
      }
    } catch (error) {
      console.error('❌ Error checking upcoming surveys:', error);
      console.error('Error details:', error.response?.data);
      toast.error(language === 'vi' 
        ? '❌ Lỗi kiểm tra upcoming surveys'
        : '❌ Error checking upcoming surveys'
      );
    }
  };

  // Handle add certificate (placeholder)
  const handleAddShipCertificate = () => {
    if (!selectedShip) {
      toast.warning(language === 'vi' ? 'Vui lòng chọn tàu trước' : 'Please select a ship first');
      return;
    }
    setShowAddShipCertificateModal(true);
  };

  // Handle ship certificate success
  const handleShipCertificateSuccess = async () => {
    // Refresh certificate list with loading indicator
    if (selectedShip?.id) {
      setCertificatesLoading(true);
      try {
        await fetchCertificates(selectedShip.id);
        toast.success(language === 'vi' ? '✅ Đã cập nhật danh sách certificate!' : '✅ Certificate list updated!');
      } catch (error) {
        console.error('Error refreshing certificates:', error);
      } finally {
        setCertificatesLoading(false);
      }
    }
  };

  // Handle bulk delete certificates
  const handleBulkDelete = async () => {
    if (selectedCertificates.size === 0) {
      toast.warning(language === 'vi' ? 'Vui lòng chọn chứng chỉ cần xóa' : 'Please select certificates to delete');
      return;
    }

    const confirmed = window.confirm(
      language === 'vi' 
        ? `Bạn có chắc chắn muốn xóa ${selectedCertificates.size} chứng chỉ đã chọn?`
        : `Are you sure you want to delete ${selectedCertificates.size} selected certificates?`
    );

    if (!confirmed) return;

    try {
      const certIds = Array.from(selectedCertificates);
      
      // Call backend bulk delete API
      const response = await api.post('/api/certificates/bulk-delete', {
        certificate_ids: certIds
      });

      if (response.data.success) {
        toast.success(
          language === 'vi'
            ? `✅ Đã xóa ${response.data.deleted_count} chứng chỉ`
            : `✅ Deleted ${response.data.deleted_count} certificates`
        );
        
        // Clear selection
        setSelectedCertificates(new Set());
        
        // Refresh certificate list
        if (selectedShip?.id) {
          await fetchCertificates(selectedShip.id);
        }
      }
    } catch (error) {
      console.error('Bulk delete error:', error);
      toast.error(
        language === 'vi'
          ? '❌ Lỗi khi xóa chứng chỉ'
          : '❌ Error deleting certificates'
      );
    }
  };

  // Handle bulk view files - open multiple files in new tabs
  const handleBulkView = async () => {
    if (selectedCertificates.size === 0) {
      toast.warning(language === 'vi' ? 'Vui lòng chọn chứng chỉ' : 'Please select certificates');
      return;
    }

    try {
      const selectedCerts = certificates.filter(cert => selectedCertificates.has(cert.id));
      const certsWithFiles = selectedCerts.filter(cert => cert.google_drive_file_id);

      if (certsWithFiles.length === 0) {
        toast.warning(
          language === 'vi'
            ? 'Không có chứng chỉ nào có file đính kèm'
            : 'No certificates have attached files'
        );
        return;
      }

      // Open files in new tabs (limit to 10 to avoid browser blocking)
      const limit = Math.min(certsWithFiles.length, 10);
      for (let i = 0; i < limit; i++) {
        const cert = certsWithFiles[i];
        
        // Check cache first
        let viewUrl = certificateLinksCache[cert.google_drive_file_id];
        
        if (!viewUrl) {
          // Fetch from API if not cached
          const response = await api.get(`/api/gdrive/file/${cert.google_drive_file_id}/view`);
          if (response.data?.success && response.data?.view_url) {
            viewUrl = response.data.view_url;
            // Update cache
            setCertificateLinksCache(prev => ({
              ...prev,
              [cert.google_drive_file_id]: viewUrl
            }));
          }
        }
        
        if (viewUrl) {
          window.open(viewUrl, '_blank', 'noopener,noreferrer');
        }
      }

      if (certsWithFiles.length > 10) {
        toast.info(
          language === 'vi'
            ? `📄 Đã mở ${limit} file đầu tiên (giới hạn trình duyệt)`
            : `📄 Opened first ${limit} files (browser limit)`
        );
      } else {
        toast.success(
          language === 'vi'
            ? `📄 Đã mở ${limit} file`
            : `📄 Opened ${limit} files`
        );
      }
    } catch (error) {
      console.error('Bulk view error:', error);
      toast.error(
        language === 'vi'
          ? '❌ Lỗi khi mở file'
          : '❌ Error opening files'
      );
    }
  };

  // Handle bulk download files
  const handleBulkDownload = async () => {
    if (selectedCertificates.size === 0) {
      toast.warning(language === 'vi' ? 'Vui lòng chọn chứng chỉ' : 'Please select certificates');
      return;
    }

    try {
      const selectedCerts = certificates.filter(cert => selectedCertificates.has(cert.id));
      const certsWithFiles = selectedCerts.filter(cert => cert.google_drive_file_id);

      if (certsWithFiles.length === 0) {
        toast.warning(
          language === 'vi'
            ? 'Không có chứng chỉ nào có file đính kèm'
            : 'No certificates have attached files'
        );
        return;
      }

      toast.info(
        language === 'vi'
          ? `📥 Đang tải xuống ${certsWithFiles.length} file...`
          : `📥 Downloading ${certsWithFiles.length} files...`
      );

      let downloadedCount = 0;

      for (const cert of certsWithFiles) {
        try {
          const response = await api.get(`/api/gdrive/file/${cert.google_drive_file_id}/download`, {
            responseType: 'blob'
          });
          
          // Create download link
          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', `${cert.cert_abbreviation || cert.cert_name}.pdf`);
          document.body.appendChild(link);
          link.click();
          link.remove();
          window.URL.revokeObjectURL(url);
          
          downloadedCount++;
          
          // Small delay between downloads
          await new Promise(resolve => setTimeout(resolve, 300));
        } catch (error) {
          console.error(`Download error for ${cert.cert_abbreviation}:`, error);
        }
      }

      toast.success(
        language === 'vi'
          ? `✅ Đã tải xuống ${downloadedCount}/${certsWithFiles.length} file`
          : `✅ Downloaded ${downloadedCount}/${certsWithFiles.length} files`
      );
    } catch (error) {
      console.error('Bulk download error:', error);
      toast.error(
        language === 'vi'
          ? '❌ Lỗi khi tải xuống file'
          : '❌ Error downloading files'
      );
    }
  };

  // Handle bulk copy links
  const handleBulkCopyLinks = async () => {
    if (selectedCertificates.size === 0) {
      toast.warning(language === 'vi' ? 'Vui lòng chọn chứng chỉ' : 'Please select certificates');
      return;
    }

    try {
      const selectedCerts = certificates.filter(cert => selectedCertificates.has(cert.id));
      const certsWithFiles = selectedCerts.filter(cert => cert.google_drive_file_id);

      if (certsWithFiles.length === 0) {
        toast.warning(
          language === 'vi'
            ? 'Không có chứng chỉ nào có file đính kèm'
            : 'No certificates have attached files'
        );
        return;
      }

      const links = [];

      for (const cert of certsWithFiles) {
        // Check cache first
        let viewUrl = certificateLinksCache[cert.google_drive_file_id];
        
        if (!viewUrl) {
          // Fetch from API if not cached
          try {
            const response = await api.get(`/api/gdrive/file/${cert.google_drive_file_id}/view`);
            if (response.data?.success && response.data?.view_url) {
              viewUrl = response.data.view_url;
              // Update cache
              setCertificateLinksCache(prev => ({
                ...prev,
                [cert.google_drive_file_id]: viewUrl
              }));
            }
          } catch (error) {
            console.error(`Error getting link for ${cert.cert_abbreviation}:`, error);
          }
        }
        
        if (viewUrl) {
          links.push(`${cert.cert_abbreviation || cert.cert_name}: ${viewUrl}`);
        }
      }

      if (links.length > 0) {
        // Copy to clipboard
        await navigator.clipboard.writeText(links.join('\n'));
        toast.success(
          language === 'vi'
            ? `🔗 Đã sao chép ${links.length} link`
            : `🔗 Copied ${links.length} links`
        );
      } else {
        toast.error(
          language === 'vi'
            ? '❌ Không thể lấy link nào'
            : '❌ Could not get any links'
        );
      }
    } catch (error) {
      console.error('Bulk copy links error:', error);
      toast.error(
        language === 'vi'
          ? '❌ Lỗi khi sao chép link'
          : '❌ Error copying links'
      );
    }
  };

  // Handle notes click
  const handleNotesClick = (cert) => {
    setNotesModal({
      show: true,
      certificate: cert,
      notes: cert.notes || ''
    });
  };

  // Handle save notes
  const handleSaveNotes = async () => {
    if (!notesModal.certificate) return;

    try {
      await api.put(`/api/certificates/${notesModal.certificate.id}`, {
        notes: notesModal.notes
      });

      toast.success(
        language === 'vi'
          ? '✅ Đã lưu ghi chú'
          : '✅ Notes saved'
      );

      // Close modal
      setNotesModal({ show: false, certificate: null, notes: '' });

      // Refresh certificates
      if (selectedShip?.id) {
        await fetchCertificates(selectedShip.id);
      }
    } catch (error) {
      console.error('Save notes error:', error);
      toast.error(
        language === 'vi'
          ? '❌ Lỗi khi lưu ghi chú'
          : '❌ Error saving notes'
      );
    }
  };

  // Handle show auto rename dialog
  const handleShowAutoRenameDialog = () => {
    setShowAutoRenameDialog(true);
    setContextMenu(null);
  };

  // Execute batch auto rename
  const handleExecuteBatchAutoRename = async () => {
    try {
      // Get certificates to rename
      let certificatesToRename = [];
      
      if (selectedCertificates.size > 0) {
        // Use selected certificates if any are checked
        certificatesToRename = Array.from(selectedCertificates);
      } else if (contextMenu.certificate?.id) {
        // Use the right-clicked certificate if no checkboxes are selected
        certificatesToRename = [contextMenu.certificate.id];
      }

      if (certificatesToRename.length === 0) {
        toast.error(language === 'vi' ? 'Không có chứng chỉ nào được chọn!' : 'No certificates selected!');
        return;
      }

      // Filter certificates that have Google Drive file IDs
      const allCertificates = getFilteredCertificates();
      const validCertificates = certificatesToRename.map(certId => {
        const cert = allCertificates.find(c => c.id === certId);
        return cert;
      }).filter(cert => cert && cert.google_drive_file_id);

      if (validCertificates.length === 0) {
        toast.error(
          language === 'vi' 
            ? 'Không có chứng chỉ nào có file trên Google Drive!' 
            : 'No certificates have Google Drive files!'
        );
        return;
      }

      // Initialize progress
      setBatchRenameProgress({
        isRunning: true,
        completed: 0,
        total: validCertificates.length,
        current: '',
        errors: []
      });

      const errors = [];
      let completed = 0;

      // Process each certificate sequentially
      for (const certificate of validCertificates) {
        try {
          // Update progress
          setBatchRenameProgress(prev => ({
            ...prev,
            current: `${certificate.cert_name || certificate.cert_abbreviation || 'Unknown'} (${certificate.cert_no || 'No Number'})`
          }));

          // Make the auto-rename API call
          const response = await api.post(`/api/certificates/${certificate.id}/auto-rename-file`);
          
          if (response.data?.success) {
            completed++;
            setBatchRenameProgress(prev => ({
              ...prev,
              completed: completed
            }));
          } else {
            throw new Error(response.data?.message || 'Unknown error');
          }
          
          // Small delay between requests
          await new Promise(resolve => setTimeout(resolve, 500));
          
        } catch (error) {
          console.error(`❌ Failed to rename ${certificate.cert_name}:`, error);
          
          let errorMessage = certificate.cert_name || certificate.cert_abbreviation || 'Unknown Certificate';
          if (error.response?.status === 501) {
            const detail = error.response.data?.detail || '';
            const suggestedMatch = detail.match(/Suggested filename: (.+)/);
            if (suggestedMatch) {
              errorMessage += ` (${language === 'vi' ? 'Gợi ý' : 'Suggested'}: ${suggestedMatch[1]})`;
            }
          } else {
            errorMessage += ` (${error.message || 'Unknown error'})`;
          }
          
          errors.push(errorMessage);
          setBatchRenameProgress(prev => ({
            ...prev,
            errors: [...prev.errors, errorMessage]
          }));
        }
      }

      // Show completion message
      const successCount = completed;
      const errorCount = errors.length;

      if (successCount > 0) {
        toast.success(
          language === 'vi' 
            ? `Đã đổi tên ${successCount}/${validCertificates.length} files thành công!` 
            : `Successfully renamed ${successCount}/${validCertificates.length} files!`
        );
      }
      
      if (errorCount > 0) {
        toast.error(
          language === 'vi' 
            ? `${errorCount} files không thể đổi tên. Xem chi tiết trong dialog.` 
            : `${errorCount} files could not be renamed. Check details in dialog.`
        );
      }

      // Refresh certificate list
      if (successCount > 0 && selectedShip?.id) {
        await fetchCertificates(selectedShip.id);
      }

      // Close dialog after completion
      setTimeout(() => {
        setShowAutoRenameDialog(false);
        setBatchRenameProgress({ isRunning: false, completed: 0, total: 0, current: '', errors: [] });
        setSelectedCertificates(new Set());
      }, 2000);

    } catch (error) {
      console.error('❌ Batch auto rename error:', error);
      toast.error(
        language === 'vi' 
          ? 'Lỗi khi thực hiện batch auto rename!' 
          : 'Error during batch auto rename!'
      );
      
      // Reset progress on error
      setBatchRenameProgress({ isRunning: false, completed: 0, total: 0, current: '', errors: [] });
    }
  };

  const handleAddRecord = () => {
    console.log('Add Ship button clicked from ClassAndFlagCert');
    setShowAddShipModal(true);
  };

  const handleShipCreated = async (shipId, shipName) => {
    console.log('Ship created callback triggered:', shipId, shipName);
    // Close modal
    setShowAddShipModal(false);
    // Refresh ship list to show new ship
    await fetchShips();
    console.log('Ship list refreshed after creation');
    // Don't need to navigate - already on this page!
  };

  const handleEditShip = (ship) => {
    setShowEditShipModal(true);
  };

  const handleShipUpdated = (updatedShip) => {
    // Update ships list
    setShips(ships.map(s => s.id === updatedShip.id ? updatedShip : s));
    // Update selected ship
    setSelectedShip(updatedShip);
    // Refresh ships list
    fetchShips();
    toast.success(language === 'vi' ? 'Cập nhật tàu thành công!' : 'Ship updated successfully!');
  };

  // Handle ship update after recalculation
  const handleShipUpdate = async (shipId) => {
    try {
      const response = await api.get(`/api/ships/${shipId}`);
      const updatedShip = response.data;
      
      // Update ships list
      setShips(ships.map(s => s.id === updatedShip.id ? updatedShip : s));
      // Update selected ship
      setSelectedShip(updatedShip);
    } catch (error) {
      console.error('Error refreshing ship data:', error);
      toast.error(language === 'vi' ? 'Không thể làm mới dữ liệu tàu' : 'Failed to refresh ship data');
    }
  };

  const handleDeleteShipClick = (ship) => {
    setDeleteShipData(ship);
    setShowDeleteShipModal(true);
  };

  const handleDeleteShip = async (shipId, deleteOption) => {
    try {
      setIsDeletingShip(true);
      
      // Show initial loading message
      toast.info(language === 'vi' 
        ? `Đang xóa tàu ${deleteShipData?.name}...`
        : `Deleting ship ${deleteShipData?.name}...`
      );

      // Step 1: Delete ship from database only (quick operation)
      const response = await shipService.delete(shipId);

      // Step 2: If user chose to delete Google Drive folder, do it in background
      if (deleteOption === 'with_gdrive') {
        // Don't await - let it run in background
        (async () => {
          try {
            // Get user's company ID for Google Drive operations
            const userCompanyId = user?.company || user?.company_id;
            
            if (userCompanyId && deleteShipData?.name) {
              toast.info(language === 'vi' 
                ? 'Đang xóa folder Google Drive...'
                : 'Deleting Google Drive folder...'
              );

              const gdriveResponse = await api.post(`/api/companies/${userCompanyId}/gdrive/delete-ship-folder`, {
                ship_name: deleteShipData.name
              });

              if (gdriveResponse && gdriveResponse.data) {
                if (gdriveResponse.data.success) {
                  toast.success(language === 'vi' 
                    ? 'Đã xóa folder Google Drive thành công'
                    : 'Google Drive folder deleted successfully'
                  );
                } else if (gdriveResponse.data.warning) {
                  toast.warning(language === 'vi' 
                    ? 'Folder Google Drive không tìm thấy (có thể đã được xóa trước đó)'
                    : 'Google Drive folder not found (may have been deleted previously)'
                  );
                }
              }
            }
          } catch (gdriveError) {
            console.error('Google Drive deletion error:', gdriveError);
            toast.warning(language === 'vi' 
              ? 'Đã xóa dữ liệu tàu nhưng có lỗi khi xóa folder Google Drive'
              : 'Ship data deleted but Google Drive folder deletion failed'
            );
          }
        })();
      }

      // Success message for database deletion (immediate)
      toast.success(language === 'vi' 
        ? `Đã xóa tàu "${deleteShipData?.name}" thành công`
        : `Ship "${deleteShipData?.name}" deleted successfully`
      );

      // Refresh ships list
      await fetchShips();

      // Close modals and reset states
      setShowDeleteShipModal(false);
      setShowEditShipModal(false);
      setDeleteShipData(null);
      
      // Navigate back to ship list if current ship was deleted
      if (selectedShip && selectedShip.id === shipId) {
        setSelectedShip(null);
      }

    } catch (error) {
      console.error('Ship deletion error:', error);
      
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred';
      
      toast.error(language === 'vi' 
        ? `Không thể xóa tàu: ${errorMessage}`
        : `Failed to delete ship: ${errorMessage}`
      );
    } finally {
      setIsDeletingShip(false);
    }
  };

  return (
    <MainLayout
      sidebar={
        <Sidebar 
          selectedCategory={selectedCategory}
          onCategoryChange={(cat) => {
            // Navigate to different pages based on category
            const routes = {
              'ship_certificates': '/certificates',
              'crew': '/crew',
              'ism': '/ism',
              'isps': '/isps',
              'mlc': '/mlc',
              'supplies': '/supplies'
            };
            if (routes[cat]) {
              window.location.href = routes[cat];
            }
          }}
          onAddRecord={handleAddRecord}
        />
      }
    >
      {/* Page Title with Ship Select Button */}
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-800">
          {language === 'vi' ? 'CLASS & FLAG CERT' : 'CLASS & FLAG CERT'}
        </h1>
        
        {!selectedShip && (
          <div className="flex items-center gap-4">
            <p className="text-gray-600">
              {language === 'vi' ? 'Vui lòng chọn tàu để xem thông tin' : 'Please select a ship to view information'}
            </p>
            <button
              onClick={() => setShowShipModal(true)}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-all flex items-center gap-2 whitespace-nowrap"
            >
              <span>🚢</span>
              {language === 'vi' ? 'Chọn tàu' : 'Ship Select'}
            </button>
          </div>
        )}
      </div>

      {/* Ship Detail Panel */}
      {selectedShip && (
        <ShipDetailPanel
          ship={selectedShip}
          onClose={() => setSelectedShip(null)}
          onEditShip={handleEditShip}
          showShipParticular={true}
          onShipSelect={() => setShowShipModal(true)}
          onShipUpdate={handleShipUpdate}
        />
      )}

      {/* Ship Selection Modal */}
      {showShipModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowShipModal(false)}>
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-800">
                  {language === 'vi' ? 'Chọn tàu' : 'Select Ship'}
                </h2>
                <button
                  onClick={() => setShowShipModal(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {loading ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <p className="mt-2 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
                </div>
              ) : ships.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>{language === 'vi' ? 'Không có tàu nào' : 'No ships available'}</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {ships.map(ship => (
                    <button
                      key={ship.id}
                      onClick={() => {
                        setSelectedShip(ship);
                        setShowShipModal(false);
                      }}
                      className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                        selectedShip?.id === ship.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="font-semibold text-gray-800">{ship.name}</div>
                      <div className="text-sm text-gray-600 mt-1">
                        {ship.imo && `IMO: ${ship.imo}`}
                        {ship.flag && ` • ${language === 'vi' ? 'Cờ' : 'Flag'}: ${ship.flag}`}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* SubMenu Bar */}
      <SubMenuBar 
        selectedCategory={selectedCategory}
        selectedSubMenu={selectedSubMenu}
        onSubMenuChange={setSelectedSubMenu}
      />
      
      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-md p-6">
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
          </div>
        ) : !selectedShip ? (
          /* Ship Cards Grid - Show all ships for selection */
          <div>
            <h3 className="text-xl font-semibold mb-6 text-gray-800">
              {language === 'vi' ? 'Chọn tàu để xem thông tin chứng chỉ' : 'Select a ship to view certificate information'}
            </h3>
            
            {ships.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-6xl mb-4">🚢</div>
                <p className="text-lg">{language === 'vi' ? 'Không có tàu nào' : 'No ships available'}</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                {ships.map(ship => (
                  <div
                    key={ship.id}
                    onClick={() => setSelectedShip(ship)}
                    className="border-2 border-gray-200 rounded-lg p-4 hover:border-purple-500 hover:shadow-lg transition-all cursor-pointer bg-gradient-to-br from-white to-gray-50"
                  >
                    {/* Ship Icon */}
                    <div className="text-center mb-3">
                      <div className="text-3xl">🚢</div>
                    </div>
                    
                    {/* Ship Name */}
                    <h4 className="text-base font-bold text-gray-800 text-center mb-3 line-clamp-2 min-h-[3rem]">
                      {ship.name}
                    </h4>
                    
                    {/* Ship Details */}
                    <div className="space-y-1.5 text-sm">
                      {ship.imo && (
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600 text-xs">IMO:</span>
                          <span className="font-semibold text-gray-800 text-xs">{ship.imo}</span>
                        </div>
                      )}
                      {ship.flag && (
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600 text-xs">{language === 'vi' ? 'Cờ:' : 'Flag:'}</span>
                          <span className="font-semibold text-gray-800 text-xs truncate ml-1">{ship.flag}</span>
                        </div>
                      )}
                      {ship.class_society && (
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600 text-xs">{language === 'vi' ? 'Đăng kiểm:' : 'Class Society:'}</span>
                          <span className="font-semibold text-gray-800 text-xs truncate ml-1">{shortenClassSociety(ship.class_society)}</span>
                        </div>
                      )}
                      {ship.built_year && (
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600 text-xs">{language === 'vi' ? 'Năm:' : 'Year:'}</span>
                          <span className="font-semibold text-gray-800 text-xs">{ship.built_year}</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Select Button */}
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <button
                        className="w-full py-1.5 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded font-medium transition-all"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedShip(ship);
                        }}
                      >
                        {language === 'vi' ? 'Chọn' : 'Select'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          /* Certificate List Section */
          <div>
            {/* Action Buttons */}
            <CertificateActionButtons
              language={language}
              selectedShip={selectedShip}
              selectedCertificatesCount={selectedCertificates.size}
              isUpdatingSurveyTypes={isUpdatingSurveyTypes}
              isMultiCertProcessing={isMultiCertProcessing}
              isRefreshing={isRefreshing}
              linksFetching={linksFetching}
              linksFetchProgress={linksFetchProgress}
              onUpdateSurveyTypes={handleUpdateSurveyTypes}
              onUpcomingSurvey={handleUpcomingSurvey}
              onAddCertificate={handleAddShipCertificate}
              onRefresh={handleRefreshCertificates}
            />

            {/* Certificate Filters */}
            <CertificateFilters
              filters={certificateFilters}
              onFilterChange={setCertificateFilters}
              certificateTypes={getUniqueCertificateTypes()}
              totalCount={certificates.length}
              filteredCount={getFilteredCertificates().length}
              language={language}
              linksFetching={false}
              linksReady={0}
            />

            {/* Certificate Table */}
            {certificatesLoading ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-2 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
              </div>
            ) : (
              <CertificateTable
                certificates={getFilteredCertificates()}
                language={language}
                selectedCertificates={selectedCertificates}
                onSelectCertificate={handleSelectCertificate}
                onSelectAllCertificates={handleSelectAllCertificates}
                onSort={handleCertificateSort}
                sortConfig={certificateSort}
                onDoubleClick={handleCertificateDoubleClick}
                onRightClick={handleCertificateRightClick}
                onSurveyTypeRightClick={handleSurveyTypeRightClick}
                onNotesClick={handleNotesClick}
              />
            )}
          </div>
        )}
      </div>

      {/* Context Menu for Certificate Actions */}
      {contextMenu && (
        <div
          className="fixed bg-white shadow-lg rounded-lg py-2 z-[9999] border border-gray-200 min-w-[200px]"
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
          {/* Header showing selection count */}
          {selectedCertificates.size > 1 ? (
            <div className="px-4 py-2 text-xs font-semibold text-gray-500 border-b border-gray-200">
              {selectedCertificates.size} {language === 'vi' ? 'chứng chỉ đã chọn' : 'certificates selected'}
            </div>
          ) : (
            <div className="px-4 py-2 text-xs font-semibold text-gray-500 border-b border-gray-200">
              {contextMenu.certificate?.cert_abbreviation || contextMenu.certificate?.cert_name}
            </div>
          )}
          
          {/* View File - works for single and multiple */}
          <button
            onClick={() => {
              if (selectedCertificates.size > 1) {
                handleBulkView();
              } else if (contextMenu.certificate) {
                handleCertificateDoubleClick(contextMenu.certificate);
              }
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left hover:bg-gray-100 text-gray-700 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            {selectedCertificates.size > 1 
              ? (language === 'vi' ? `Xem file (${selectedCertificates.size} chứng chỉ)` : `View Files (${selectedCertificates.size} certificates)`)
              : (language === 'vi' ? 'Xem file' : 'View File')
            }
            {contextMenu.certificate?.google_drive_file_id && selectedCertificates.size === 1 && (
              <span className="ml-auto text-xs bg-green-100 text-green-600 px-1 rounded">📄</span>
            )}
          </button>

          {/* Download - works for single and multiple */}
          <button
            onClick={() => {
              handleBulkDownload();
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left hover:bg-gray-100 text-gray-700 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {selectedCertificates.size > 1 
              ? (language === 'vi' ? `Tải xuống (${selectedCertificates.size} file)` : `Download (${selectedCertificates.size} files)`)
              : (language === 'vi' ? 'Tải xuống file' : 'Download File')
            }
            {contextMenu.certificate?.google_drive_file_id && selectedCertificates.size === 1 && (
              <span className="ml-auto text-xs bg-blue-100 text-blue-600 px-1 rounded">📥</span>
            )}
          </button>

          {/* Copy Link - works for single and multiple */}
          <button
            onClick={() => {
              handleBulkCopyLinks();
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left hover:bg-gray-100 text-gray-700 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
            </svg>
            {selectedCertificates.size > 1 
              ? (language === 'vi' ? `Sao chép link (${selectedCertificates.size} file)` : `Copy Links (${selectedCertificates.size} files)`)
              : (language === 'vi' ? 'Sao chép link' : 'Copy Link')
            }
            {contextMenu.certificate?.google_drive_file_id && selectedCertificates.size === 1 && (
              <span className="ml-auto text-xs bg-gray-100 text-gray-600 px-1 rounded">🔗</span>
            )}
          </button>

          {/* Auto Rename File */}
          <button
            onClick={handleShowAutoRenameDialog}
            className="w-full px-4 py-2 text-left hover:bg-orange-50 text-orange-600 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
            Auto Rename File
          </button>

          <div className="border-t border-gray-200 my-1"></div>

          {/* Edit - only show for single selection */}
          {contextMenu.certificate && selectedCertificates.size <= 1 && (
            <button
              onClick={() => {
                setEditingCertificate(contextMenu.certificate);
                setShowEditShipCertificateModal(true);
                setContextMenu(null);
              }}
              className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2 text-blue-600"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              {language === 'vi' ? 'Chỉnh sửa chứng chỉ' : 'Edit Certificate'}
            </button>
          )}
          
          {/* Delete - works for single and multiple */}
          <button
            onClick={() => {
              if (selectedCertificates.size > 1) {
                handleBulkDelete();
              } else {
                setDeletingCertificate(contextMenu.certificate);
                setShowDeleteShipCertificateModal(true);
              }
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left hover:bg-red-50 text-red-600 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            {selectedCertificates.size > 1 
              ? (language === 'vi' ? `Xóa ${selectedCertificates.size} chứng chỉ` : `Delete ${selectedCertificates.size} certificates`)
              : (language === 'vi' ? 'Xóa chứng chỉ' : 'Delete Certificate')
            }
          </button>
        </div>
      )}

      {/* Survey Type Context Menu */}
      {surveyTypeContextMenu && (
        <div
          className="fixed bg-white shadow-lg rounded-lg py-2 z-50 border border-gray-200"
          style={{ top: surveyTypeContextMenu.y, left: surveyTypeContextMenu.x }}
        >
          {['Annual', 'Intermediate', 'Renewal', 'Special'].map(type => (
            <button
              key={type}
              onClick={async () => {
                try {
                  // Quick update survey type
                  await api.put(`/api/certificates/${surveyTypeContextMenu.certId}`, {
                    next_survey_type: type
                  });

                  toast.success(language === 'vi' 
                    ? `✅ Đã cập nhật loại kiểm tra thành "${type}"`
                    : `✅ Survey type updated to "${type}"`
                  );

                  // Refresh certificate list
                  if (selectedShip?.id) {
                    await fetchCertificates(selectedShip.id);
                  }
                } catch (error) {
                  console.error('Error updating survey type:', error);
                  toast.error(language === 'vi' 
                    ? '❌ Lỗi cập nhật loại kiểm tra'
                    : '❌ Failed to update survey type'
                  );
                }
                
                setSurveyTypeContextMenu(null);
              }}
              className={`w-full px-4 py-2 text-left hover:bg-gray-100 ${
                surveyTypeContextMenu.currentType === type ? 'bg-blue-50 font-semibold text-blue-700' : ''
              }`}
            >
              {surveyTypeContextMenu.currentType === type && '✓ '}
              {type}
            </button>
          ))}
          
          {/* Clear option */}
          <div className="border-t my-1"></div>
          <button
            onClick={async () => {
              try {
                await api.put(`/api/certificates/${surveyTypeContextMenu.certId}`, {
                  next_survey_type: null
                });

                toast.success(language === 'vi' 
                  ? '✅ Đã xóa loại kiểm tra'
                  : '✅ Survey type cleared'
                );

                if (selectedShip?.id) {
                  await fetchCertificates(selectedShip.id);
                }
              } catch (error) {
                console.error('Error clearing survey type:', error);
                toast.error(language === 'vi' 
                  ? '❌ Lỗi xóa loại kiểm tra'
                  : '❌ Failed to clear survey type'
                );
              }
              
              setSurveyTypeContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left hover:bg-gray-100 text-gray-600 italic"
          >
            {language === 'vi' ? '— Không có —' : '— None —'}
          </button>
        </div>
      )}

      {/* Add Ship Modal */}
      <AddShipModal 
        isOpen={showAddShipModal}
        onClose={() => {
          console.log('Closing Add Ship modal');
          setShowAddShipModal(false);
        }}
        onShipCreated={handleShipCreated}
      />

      {/* Edit Ship Modal */}
      {showEditShipModal && selectedShip && (
        <EditShipModal
          isOpen={showEditShipModal}
          onClose={() => setShowEditShipModal(false)}
          ship={selectedShip}
          onShipUpdated={handleShipUpdated}
          onDeleteShip={handleDeleteShipClick}
        />
      )}

      {/* Delete Ship Confirmation Modal */}
      {showDeleteShipModal && deleteShipData && (
        <DeleteShipConfirmationModal
          isOpen={showDeleteShipModal}
          onClose={() => {
            setShowDeleteShipModal(false);
            setDeleteShipData(null);
          }}
          ship={deleteShipData}
          onConfirm={handleDeleteShip}
          isDeleting={isDeletingShip}
        />
      )}

      {/* Add Ship Certificate Modal */}
      <AddShipCertificateModal
        isOpen={showAddShipCertificateModal}
        onClose={() => setShowAddShipCertificateModal(false)}
        onSuccess={handleShipCertificateSuccess}
        selectedShip={selectedShip}
        allShips={ships}
        onShipChange={setSelectedShip}
        aiConfig={aiConfig}
      />

      {/* Edit Ship Certificate Modal */}
      <EditShipCertificateModal
        isOpen={showEditShipCertificateModal}
        onClose={() => {
          setShowEditShipCertificateModal(false);
          setEditingCertificate(null);
        }}
        onSuccess={handleShipCertificateSuccess}
        certificate={editingCertificate}
      />

      {/* Delete Ship Certificate Modal */}
      <DeleteShipCertificateModal
        isOpen={showDeleteShipCertificateModal}
        onClose={() => {
          setShowDeleteShipCertificateModal(false);
          setDeletingCertificate(null);
        }}
        onSuccess={handleShipCertificateSuccess}
        certificate={deletingCertificate}
      />

      {/* Upcoming Survey Modal */}
      <UpcomingSurveyModal
        isOpen={upcomingSurveyModal.show}
        onClose={() => setUpcomingSurveyModal({ show: false, surveys: [], totalCount: 0, company: '', companyName: '', checkDate: '' })}
        surveys={upcomingSurveyModal.surveys}
        totalCount={upcomingSurveyModal.totalCount}
        company={upcomingSurveyModal.company}
        companyName={upcomingSurveyModal.companyName}
        checkDate={upcomingSurveyModal.checkDate}
        language={language}
      />

      {/* Certificate Notes Modal */}
      <CertificateNotesModal
        isOpen={notesModal.show}
        onClose={() => setNotesModal({ show: false, certificate: null, notes: '' })}
        certificate={notesModal.certificate}
        notes={notesModal.notes}
        onNotesChange={(newNotes) => setNotesModal(prev => ({ ...prev, notes: newNotes }))}
        onSave={handleSaveNotes}
        language={language}
      />

      {/* Auto Rename Progress Dialog */}
      {showAutoRenameDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[70] p-4">
          <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full">
            {/* Header */}
            <div className="mb-6">
              <h3 className="text-xl font-bold text-orange-600 mb-2">
                🔄 {language === 'vi' ? 'Đổi tên tự động' : 'Auto Rename Files'}
              </h3>
              {!batchRenameProgress.isRunning && (
                <p className="text-sm text-gray-600">
                  {language === 'vi' 
                    ? `Đổi tên ${selectedCertificates.size > 0 ? selectedCertificates.size : 1} file(s) theo định dạng chuẩn trên Google Drive`
                    : `Rename ${selectedCertificates.size > 0 ? selectedCertificates.size : 1} file(s) to standard format on Google Drive`}
                </p>
              )}
            </div>

            {/* Progress Bar */}
            {batchRenameProgress.isRunning && (
              <div className="mb-6">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>{language === 'vi' ? 'Tiến độ' : 'Progress'}</span>
                  <span className="font-medium">
                    {batchRenameProgress.completed}/{batchRenameProgress.total}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <div 
                    className="bg-orange-600 h-full transition-all duration-300 ease-out"
                    style={{ width: `${(batchRenameProgress.completed / batchRenameProgress.total) * 100}%` }}
                  ></div>
                </div>
                {batchRenameProgress.current && (
                  <p className="text-xs text-gray-500 mt-2">
                    {language === 'vi' ? 'Đang xử lý' : 'Processing'}: {batchRenameProgress.current}
                  </p>
                )}
              </div>
            )}

            {/* Errors */}
            {batchRenameProgress.errors.length > 0 && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg max-h-40 overflow-y-auto">
                <h4 className="text-sm font-semibold text-red-800 mb-2">
                  ⚠️ {language === 'vi' ? 'Lỗi' : 'Errors'} ({batchRenameProgress.errors.length})
                </h4>
                <ul className="text-xs text-red-700 space-y-1">
                  {batchRenameProgress.errors.map((error, index) => (
                    <li key={index}>• {error}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end gap-3">
              {!batchRenameProgress.isRunning && (
                <>
                  <button
                    onClick={() => {
                      setShowAutoRenameDialog(false);
                      setBatchRenameProgress({ isRunning: false, completed: 0, total: 0, current: '', errors: [] });
                    }}
                    className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg text-sm font-medium transition-all"
                  >
                    {language === 'vi' ? 'Hủy' : 'Cancel'}
                  </button>
                  <button
                    onClick={handleExecuteBatchAutoRename}
                    className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm font-medium transition-all flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {language === 'vi' ? 'Bắt đầu' : 'Start'}
                  </button>
                </>
              )}
              {batchRenameProgress.isRunning && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {language === 'vi' ? 'Đang xử lý...' : 'Processing...'}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
};

export default ClassAndFlagCert;
