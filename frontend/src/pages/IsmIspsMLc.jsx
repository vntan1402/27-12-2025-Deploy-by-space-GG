import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout, Sidebar, SubMenuBar, CompanyInfoPanel } from '../components';
import { ShipDetailPanel } from '../components/ShipDetailPanel';
import { AddShipModal } from '../components/Ships';
import { 
  AuditCertificateTable, 
  AuditCertificateFilters, 
  AuditCertificateActionButtons,
  AddAuditCertificateModal,
  EditAuditCertificateModal,
  DeleteAuditCertificateModal,
  AuditCertificateNotesModal,
  AuditUpcomingSurveyModal
} from '../components/AuditCertificate';
import {
  AuditReportList,
  AddAuditReportModal,
  EditAuditReportModal,
  AuditReportNotesModal
} from '../components/AuditReport';
import { BatchProcessingModal, BatchResultsModal } from '../components/ClassSurveyReport';
import { ApprovalDocumentTable } from '../components/ApprovalDocument';
import { OtherAuditDocumentTable } from '../components/OtherAuditDocument';
import { shipService, companyService, auditCertificateService, auditReportService } from '../services';
import api from '../services/api';
import { toast } from 'sonner';
import { RateLimiter } from '../utils/retryHelper';

// Create a global rate limiter for GDrive uploads to prevent 429 errors
// Max 2 concurrent uploads, 2 seconds between requests
const gdriveUploadLimiter = new RateLimiter(2, 2000);

const IsmIspsMLc = () => {
  const { language, user } = useAuth();
  
  // State
  const [selectedCategory] = useState('ism');
  const [selectedSubMenu, setSelectedSubMenu] = useState('audit_certificate');
  const [showAddShipModal, setShowAddShipModal] = useState(false);
  const [showShipModal, setShowShipModal] = useState(false);
  const [ships, setShips] = useState([]);
  const [selectedShip, setSelectedShip] = useState(null);
  const [loading, setLoading] = useState(false);
  const [companyData, setCompanyData] = useState(null);

  // Audit Certificate States
  const [auditCertificates, setAuditCertificates] = useState([]);
  const [certificatesLoading, setCertificatesLoading] = useState(false);
  const [selectedCertificates, setSelectedCertificates] = useState(new Set());
  
  // Certificate Modals
  const [showAddCertificateModal, setShowAddCertificateModal] = useState(false);
  const [showEditCertificateModal, setShowEditCertificateModal] = useState(false);
  const [showDeleteCertificateModal, setShowDeleteCertificateModal] = useState(false);
  const [editingCertificate, setEditingCertificate] = useState(null);
  const [deletingCertificate, setDeletingCertificate] = useState(null);
  
  // Filters & Sort
  const [certificateFilters, setCertificateFilters] = useState({
    certificateType: 'all',
    status: 'all',
    search: ''
  });
  const [certificateSort, setCertificateSort] = useState({
    column: 'cert_abbreviation',
    direction: 'asc'
  });
  
  // Actions
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isUpdatingNextSurvey, setIsUpdatingNextSurvey] = useState(false);
  
  // Batch links fetching
  const [linksFetching, setLinksFetching] = useState(false);
  const [linksFetchProgress, setLinksFetchProgress] = useState({ ready: 0, total: 0 });
  const [certificateLinksCache, setCertificateLinksCache] = useState({});
  
  // Notes & Survey modals
  const [notesModal, setNotesModal] = useState({ 
    show: false, certificate: null, notes: '' 
  });
  const [upcomingSurveyModal, setUpcomingSurveyModal] = useState({
    show: false, surveys: [], totalCount: 0, 
    company: '', companyName: '', checkDate: ''
  });

  // Context menus
  const [contextMenu, setContextMenu] = useState(null);
  const [surveyTypeContextMenu, setSurveyTypeContextMenu] = useState({
    show: false, x: 0, y: 0, certificate: null, currentType: ''
  });

  // AI Config
  const [aiConfig, setAiConfig] = useState(null);

  // ========== AUDIT REPORT STATES ==========
  const [auditReports, setAuditReports] = useState([]);
  const [auditReportsLoading, setAuditReportsLoading] = useState(false);
  const [selectedAuditReports, setSelectedAuditReports] = useState(new Set());
  
  // Audit Report Modals
  const [showAddAuditReportModal, setShowAddAuditReportModal] = useState(false);
  const [showEditAuditReportModal, setShowEditAuditReportModal] = useState(false);
  const [editingAuditReport, setEditingAuditReport] = useState(null);
  
  // Audit Report Filters & Sort
  const [auditReportFilters, setAuditReportFilters] = useState({
    auditType: 'all',
    status: 'all',
    search: ''
  });
  const [auditReportSort, setAuditReportSort] = useState({
    column: 'audit_date',
    direction: 'desc'
  });
  
  // Audit Report Actions
  const [isRefreshingAuditReports, setIsRefreshingAuditReports] = useState(false);
  
  // Batch Processing for Audit Reports
  const [isBatchProcessingAuditReports, setIsBatchProcessingAuditReports] = useState(false);
  const [auditReportBatchProgress, setAuditReportBatchProgress] = useState({ current: 0, total: 0 });
  const [auditReportFileProgressMap, setAuditReportFileProgressMap] = useState({});
  const [auditReportFileStatusMap, setAuditReportFileStatusMap] = useState({});
  const [auditReportFileSubStatusMap, setAuditReportFileSubStatusMap] = useState({});
  const [auditReportFileObjectsMap, setAuditReportFileObjectsMap] = useState({}); // Store file objects for retry
  const [auditReportBatchResults, setAuditReportBatchResults] = useState([]);
  const [showAuditReportBatchResults, setShowAuditReportBatchResults] = useState(false);
  const [isAuditReportBatchModalMinimized, setIsAuditReportBatchModalMinimized] = useState(false);
  
  // Notes Modal for Audit Reports
  const [auditReportNotesModal, setAuditReportNotesModal] = useState({
    show: false, report: null, notes: ''
  });


  // Fetch ships on mount and restore selected ship from localStorage
  useEffect(() => {
    fetchShips();
    fetchCompanyData();
    
    // Restore selected ship from localStorage
    const savedShipId = localStorage.getItem('selectedShipId');
    if (savedShipId) {
      console.log('Found saved ship ID:', savedShipId);
    }
  }, []);

  // Restore selected ship after ships are loaded
  useEffect(() => {
    if (ships.length > 0 && !selectedShip) {
      const savedShipId = localStorage.getItem('selectedShipId');
      if (savedShipId) {
        const savedShip = ships.find(s => s.id === savedShipId);
        if (savedShip) {
          console.log('Restoring selected ship:', savedShip.name);
          setSelectedShip(savedShip);
        } else {
          // Ship not found, clear localStorage
          localStorage.removeItem('selectedShipId');
        }
      }
    }
  }, [ships]);

  // Fetch audit certificates when ship changes
  useEffect(() => {
    if (selectedShip && selectedSubMenu === 'audit_certificate') {
      fetchAuditCertificates(selectedShip.id);
    } else {
      setAuditCertificates([]);
      setSelectedCertificates(new Set());
    }
  }, [selectedShip, selectedSubMenu]);

  // Fetch AI config on mount
  useEffect(() => {
    fetchAiConfig();
  }, []);

  // Close context menus on click outside
  useEffect(() => {
    const handleClickOutside = () => {
      if (contextMenu) setContextMenu(null);
      if (surveyTypeContextMenu?.show) {
        setSurveyTypeContextMenu({ show: false, x: 0, y: 0, certificate: null, currentType: '' });
      }
    };

    if (contextMenu || surveyTypeContextMenu?.show) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [contextMenu, surveyTypeContextMenu]);

  // Prefetch certificate links when certificates are loaded
  useEffect(() => {
    if (auditCertificates.length > 0) {
      prefetchCertificateLinks(auditCertificates);
    }
  }, [auditCertificates]);



  const fetchShips = async () => {
    try {
      setLoading(true);
      const response = await shipService.getAll();
      setShips(response.data || response || []);
    } catch (error) {
      console.error('Failed to fetch ships:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách tàu' : 'Failed to load ships');
    } finally {
      setLoading(false);
    }
  };

  const fetchCompanyData = async () => {
    try {
      const response = await companyService.getCompanyInfo();
      setCompanyData(response.data);
    } catch (error) {
      console.error('Failed to fetch company data:', error);
    }
  };

  const handleAddRecord = () => {
    setShowAddShipModal(true);
  };

  const handleShipCreated = (shipId, shipName) => {
    setShowAddShipModal(false);
    fetchShips();
    toast.success(language === 'vi' ? `Tàu ${shipName} đã được tạo` : `Ship ${shipName} created successfully`);
  };

  const handleShipSelect = (ship) => {
    setSelectedShip(ship);
    localStorage.setItem('selectedShipId', ship.id);
    setShowShipModal(false);
  };

  // Handle submenu navigation
  const handleSubMenuChange = (submenuKey) => {
    setSelectedSubMenu(submenuKey);
    // All submenus stay on this page for now
    console.log('Selected submenu:', submenuKey);
  };


  // ==================== AUDIT CERTIFICATE HANDLERS ====================
  
  const fetchAuditCertificates = async (shipId) => {
    try {
      setCertificatesLoading(true);
      const response = await auditCertificateService.getAll(shipId);
      setAuditCertificates(response.data || []);
    } catch (error) {
      console.error('Failed to fetch audit certificates:', error);
      toast.error(language === 'vi' 
        ? 'Không thể tải danh sách chứng chỉ' 
        : 'Failed to load certificates'
      );
    } finally {
      setCertificatesLoading(false);
    }
  };

  // Prefetch certificate Google Drive links in batches with progress tracking
  const prefetchCertificateLinks = async (certs) => {
    if (!certs || certs.length === 0) return;

    // Filter certificates that have file IDs and are not already cached
    const certsWithFiles = certs.filter(cert => 
      cert.google_drive_file_id && !certificateLinksCache[cert.google_drive_file_id]
    );

    if (certsWithFiles.length === 0) {
      // All links are cached, just update the progress indicator
      setLinksFetchProgress({ 
        ready: certs.filter(c => c.google_drive_file_id).length, 
        total: certs.filter(c => c.google_drive_file_id).length 
      });
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

  const handleAddCertificate = () => {
    setShowAddCertificateModal(true);
  };

  const handleClose = () => {
    setShowAddCertificateModal(false);
  };

  const handleEditCertificate = (cert) => {
    setEditingCertificate(cert);
    setShowEditCertificateModal(true);
  };

  const handleDeleteCertificate = (cert) => {
    setDeletingCertificate(cert);
    setShowDeleteCertificateModal(true);
  };

  const handleSaveCertificate = async (data) => {
    try {
      await auditCertificateService.create(data);
      toast.success(language === 'vi' 
        ? 'Đã thêm chứng chỉ' 
        : 'Certificate added successfully'
      );
      setShowAddCertificateModal(false);
      fetchAuditCertificates(selectedShip.id);
    } catch (error) {
      console.error('Failed to create certificate:', error);
      toast.error(language === 'vi' 
        ? 'Không thể thêm chứng chỉ' 
        : 'Failed to add certificate'
      );
    }
  };

  const handleUpdateCertificate = async (id, data) => {
    try {
      await auditCertificateService.update(id, data);
      toast.success(language === 'vi' 
        ? 'Đã cập nhật chứng chỉ' 
        : 'Certificate updated successfully'
      );
      setShowEditCertificateModal(false);
      setEditingCertificate(null);
      fetchAuditCertificates(selectedShip.id);
    } catch (error) {
      console.error('Failed to update certificate:', error);
      toast.error(language === 'vi' 
        ? 'Không thể cập nhật chứng chỉ' 
        : 'Failed to update certificate'
      );
    }
  };

  const handleConfirmDelete = async () => {
    try {
      if (selectedCertificates.size > 1) {
        // Bulk delete
        await auditCertificateService.bulkDelete(Array.from(selectedCertificates));
        toast.success(language === 'vi' 
          ? `Đã xóa ${selectedCertificates.size} chứng chỉ` 
          : `Deleted ${selectedCertificates.size} certificates`
        );
        setSelectedCertificates(new Set());
      } else if (deletingCertificate) {
        // Single delete
        await auditCertificateService.delete(deletingCertificate.id);
        toast.success(language === 'vi' 
          ? 'Đã xóa chứng chỉ' 
          : 'Certificate deleted successfully'
        );
      }
      setShowDeleteCertificateModal(false);
      setDeletingCertificate(null);
      fetchAuditCertificates(selectedShip.id);
    } catch (error) {
      console.error('Failed to delete certificate:', error);
      toast.error(language === 'vi' 
        ? 'Không thể xóa chứng chỉ' 
        : 'Failed to delete certificate'
      );
    }
  };

  const handleSelectCertificate = (id) => {
    const newSelected = new Set(selectedCertificates);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedCertificates(newSelected);
  };

  const handleSelectAllCertificates = (checked) => {
    if (checked) {
      const allIds = getFilteredCertificates().map(cert => cert.id);
      setSelectedCertificates(new Set(allIds));
    } else {
      setSelectedCertificates(new Set());
    }
  };

  const handleCertificateSort = (column) => {
    setCertificateSort(prev => ({
      column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const getFilteredCertificates = () => {
    let filtered = [...auditCertificates];

    // Filter by certificate type
    if (certificateFilters.certificateType !== 'all') {
      filtered = filtered.filter(cert => 
        cert.cert_type === certificateFilters.certificateType
      );
    }

    // Filter by status
    if (certificateFilters.status !== 'all') {
      filtered = filtered.filter(cert => {
        const status = getCertificateStatus(cert);
        return status === certificateFilters.status;
      });
    }

    // Filter by search
    if (certificateFilters.search) {
      const search = certificateFilters.search.toLowerCase();
      filtered = filtered.filter(cert =>
        cert.cert_name?.toLowerCase().includes(search) ||
        cert.cert_abbreviation?.toLowerCase().includes(search) ||
        cert.cert_no?.toLowerCase().includes(search) ||
        cert.issued_by?.toLowerCase().includes(search)
      );
    }

    // Sort
    filtered.sort((a, b) => {
      const aVal = a[certificateSort.column];
      const bVal = b[certificateSort.column];
      
      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;
      
      const comparison = aVal > bVal ? 1 : -1;
      return certificateSort.direction === 'asc' ? comparison : -comparison;
    });

    return filtered;
  };

  const getUniqueCertificateTypes = () => {
    const types = new Set(auditCertificates.map(cert => cert.cert_type).filter(Boolean));
    return Array.from(types);
  };

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

  const handleCertificateDoubleClick = (cert) => {
    if (cert.google_drive_file_id) {
      const link = `https://drive.google.com/file/d/${cert.google_drive_file_id}/view`;
      window.open(link, '_blank');
    } else {
      toast.warning(language === 'vi' 
        ? 'Chứng chỉ này chưa có file đính kèm' 
        : 'This certificate has no attached file'
      );
    }
  };


  const handleCertificateRightClick = (e, cert) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      certificate: cert
    });
  };

  const handleSurveyTypeRightClick = (e, certId, currentType) => {
    e.preventDefault();
    const certificate = auditCertificates.find(c => c.id === certId);
    setSurveyTypeContextMenu({
      show: true,
      x: e.clientX,
      y: e.clientY,
      certificate,
      currentType
    });
  };

  const handleSurveyTypeChange = async (newType) => {
    try {
      const cert = surveyTypeContextMenu.certificate;
      await auditCertificateService.update(cert.id, {
        next_survey_type: newType
      });
      toast.success(language === 'vi' 
        ? `Đã cập nhật thành ${newType}` 
        : `Updated to ${newType}`
      );
      fetchAuditCertificates(selectedShip.id);
      setSurveyTypeContextMenu({ show: false, x: 0, y: 0, certificate: null, currentType: '' });
    } catch (error) {
      console.error('Error updating survey type:', error);
      toast.error(language === 'vi' 
        ? 'Không thể cập nhật' 
        : 'Failed to update'
      );
    }
  };

  const fetchAiConfig = async () => {
    try {
      const response = await api.get('/api/ai-config');
      setAiConfig(response.data);
    } catch (error) {
      console.error('Failed to fetch AI config:', error);
    }
  };


  const handleNotesClick = (cert) => {
    setNotesModal({
      show: true,
      certificate: cert,
      notes: cert.notes || ''
    });
  };

  const handleSaveNotes = async (notes) => {
    try {
      await auditCertificateService.update(notesModal.certificate.id, {
        notes,
        has_notes: notes.length > 0
      });
      toast.success(language === 'vi' 
        ? 'Đã lưu ghi chú' 
        : 'Notes saved successfully'
      );
      setNotesModal({ show: false, certificate: null, notes: '' });
      fetchAuditCertificates(selectedShip.id);
    } catch (error) {
      console.error('Failed to save notes:', error);
      toast.error(language === 'vi' 
        ? 'Không thể lưu ghi chú' 
        : 'Failed to save notes'
      );
    }
  };

  const handleUpcomingSurvey = async () => {
    try {
      const response = await auditCertificateService.getUpcomingSurveys(30, user.company);
      setUpcomingSurveyModal({
        show: true,
        surveys: response.data.upcoming_surveys || [],
        totalCount: response.data.total_count || 0,
        company: user.company,
        companyName: response.data.company_name || user.company,
        checkDate: response.data.check_date || new Date().toISOString().split('T')[0]
      });
    } catch (error) {
      console.error('Failed to fetch upcoming surveys:', error);
      toast.error(language === 'vi' 
        ? 'Không thể tải thông tin kiểm tra sắp tới' 
        : 'Failed to load upcoming surveys'
      );
    }
  };

  const handleRefreshCertificates = async () => {
    setIsRefreshing(true);
    await fetchAuditCertificates(selectedShip.id);
    setIsRefreshing(false);
    toast.success(language === 'vi' 
      ? 'Đã làm mới danh sách' 
      : 'List refreshed'
    );
  };

  const handleAutoRenameFile = async (cert) => {
    try {
      toast.info(language === 'vi' 
        ? 'Đang đổi tên file...' 
        : 'Renaming file...'
      );
      
      const response = await api.post(`/api/audit-certificates/${cert.id}/auto-rename-file`);
      
      if (response.data.success) {
        toast.success(language === 'vi' 
          ? `Đã đổi tên: ${response.data.new_name}` 
          : `Renamed to: ${response.data.new_name}`
        );
        fetchAuditCertificates(selectedShip.id);
      } else {
        toast.error(response.data.message || 'Failed to rename file');
      }
    } catch (error) {
      console.error('Error renaming file:', error);
      toast.error(language === 'vi' 
        ? 'Không thể đổi tên file' 
        : 'Failed to rename file'
      );
    }
  };

  const handleUpdateSurveyTypes = async () => {
    if (!selectedShip) {
      toast.error(language === 'vi' 
        ? 'Vui lòng chọn tàu trước' 
        : 'Please select a ship first'
      );
      return;
    }

    try {
      setIsUpdatingNextSurvey(true);
      
      toast.info(language === 'vi' 
        ? '🔄 Đang tính toán Next Survey cho tất cả Audit Certificates...' 
        : '🔄 Calculating Next Survey for all Audit Certificates...'
      );

      const response = await auditCertificateService.updateShipNextSurvey(selectedShip.id);

      if (response.data.success) {
        const updatedCount = response.data.updated_count || 0;
        
        toast.success(language === 'vi' 
          ? `✅ Đã cập nhật Next Survey cho ${updatedCount} certificates!` 
          : `✅ Updated Next Survey for ${updatedCount} certificates!`
        );

        // Refresh certificates list
        await fetchAuditCertificates(selectedShip.id);
      }
    } catch (error) {
      console.error('Error updating next survey:', error);
      toast.error(language === 'vi' 
        ? '❌ Lỗi cập nhật Next Survey: ' + (error.response?.data?.detail || error.message)
        : '❌ Error updating Next Survey: ' + (error.response?.data?.detail || error.message)
      );
    } finally {
      setIsUpdatingNextSurvey(false);
    }
  };

  // Handle bulk view files - open multiple files in new tabs
  const handleBulkView = async () => {
    if (selectedCertificates.size === 0) {
      toast.warning(language === 'vi' ? 'Vui lòng chọn chứng chỉ' : 'Please select certificates');
      return;
    }

    try {
      const selectedCerts = auditCertificates.filter(cert => selectedCertificates.has(cert.id));
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
      const selectedCerts = auditCertificates.filter(cert => selectedCertificates.has(cert.id));
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
      const selectedCerts = auditCertificates.filter(cert => selectedCertificates.has(cert.id));
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

  // ========== AUDIT REPORT HANDLERS ==========
  
  // Fetch audit reports
  const fetchAuditReports = async () => {
    if (!selectedShip) return;
    
    try {
      setAuditReportsLoading(true);
      const response = await auditReportService.getAll(selectedShip.id);
      const data = response.data || response || [];
      setAuditReports(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch audit reports:', error);
      toast.error(language === 'vi' ? 'Không thể tải audit reports' : 'Failed to load audit reports');
      setAuditReports([]);
    } finally {
      setAuditReportsLoading(false);
    }
  };

  // Refresh audit reports
  const handleRefreshAuditReports = async () => {
    setIsRefreshingAuditReports(true);
    await fetchAuditReports();
    setIsRefreshingAuditReports(false);
    toast.success(language === 'vi' ? 'Đã cập nhật danh sách!' : 'List refreshed!');
  };

  // Selection handlers
  const handleSelectAuditReport = (reportId) => {
    setSelectedAuditReports(prev => {
      const newSet = new Set(prev);
      if (newSet.has(reportId)) {
        newSet.delete(reportId);
      } else {
        newSet.add(reportId);
      }
      return newSet;
    });
  };

  const handleSelectAllAuditReports = (checked) => {
    if (checked) {
      setSelectedAuditReports(new Set(auditReports.map(r => r.id)));
    } else {
      setSelectedAuditReports(new Set());
    }
  };

  // Batch processing (Match Survey Report pattern with STAGGERED processing)
  const startBatchProcessingAuditReports = async (files) => {
    if (!selectedShip) {
      toast.error(language === 'vi' ? 'Vui lòng chọn tàu' : 'Please select a ship');
      return;
    }

    setIsBatchProcessingAuditReports(true);
    setAuditReportBatchProgress({ current: 0, total: files.length });
    setIsAuditReportBatchModalMinimized(false);
    
    // Initialize progress maps (Match Survey Report pattern)
    const initialProgressMap = {};
    const initialStatusMap = {};
    const initialSubStatusMap = {};
    
    files.forEach(file => {
      initialProgressMap[file.name] = 0;
      initialStatusMap[file.name] = 'waiting';
      initialSubStatusMap[file.name] = null;
    });
    
    setAuditReportFileProgressMap(initialProgressMap);
    setAuditReportFileStatusMap(initialStatusMap);
    setAuditReportFileSubStatusMap(initialSubStatusMap);
    setAuditReportBatchResults([]);

    const STAGGER_DELAY = 5000; // 5 seconds between file starts (match Survey Report)
    const results = [];

    // Process files with staggered start (parallel processing with delays)
    const promises = files.map((file, index) => {
      return new Promise((resolve) => {
        setTimeout(async () => {
          const result = await processSingleAuditReportFile(file, file.name);
          results.push(result);
          setAuditReportBatchProgress({ current: results.length, total: files.length });
          resolve(result);
        }, index * STAGGER_DELAY);
      });
    });

    // Wait for all files to complete
    await Promise.all(promises);

    // Show results
    setIsBatchProcessingAuditReports(false);
    setAuditReportBatchResults(results);
    setShowAuditReportBatchResults(true);
    
    // Refresh list
    await fetchAuditReports();
    
    // Summary toast
    const successCount = results.filter(r => r.success).length;
    const failCount = results.length - successCount;
    toast.success(
      language === 'vi'
        ? `✅ Đã xử lý ${results.length} files: ${successCount} thành công, ${failCount} thất bại`
        : `✅ Processed ${results.length} files: ${successCount} success, ${failCount} failed`
    );
  };

  // Handle retry for failed audit report
  const handleRetryFailedAuditReport = (failedFileName) => {
    // Create a file input to allow user to select a new file
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf';
    input.onchange = async (e) => {
      const newFile = e.target.files[0];
      if (!newFile) return;
      
      // Remove the failed file from maps
      setAuditReportFileStatusMap(prev => {
        const updated = { ...prev };
        delete updated[failedFileName];
        return updated;
      });
      setAuditReportFileProgressMap(prev => {
        const updated = { ...prev };
        delete updated[failedFileName];
        return updated;
      });
      setAuditReportFileSubStatusMap(prev => {
        const updated = { ...prev };
        delete updated[failedFileName];
        return updated;
      });
      
      // Update total and reset status for new file
      setAuditReportBatchProgress(prev => ({
        ...prev,
        total: prev.total // Keep same total, replacing failed file
      }));
      
      // Reset maps for new file
      setAuditReportFileStatusMap(prev => ({ ...prev, [newFile.name]: 'pending' }));
      setAuditReportFileProgressMap(prev => ({ ...prev, [newFile.name]: 0 }));
      setAuditReportFileSubStatusMap(prev => ({ ...prev, [newFile.name]: '' }));
      
      // Process the new file
      toast.info(
        language === 'vi' 
          ? `🔄 Đang xử lý file mới: ${newFile.name}` 
          : `🔄 Processing new file: ${newFile.name}`
      );
      
      try {
        const result = await processSingleAuditReportFile(newFile, newFile.name);
        
        if (result.success) {
          toast.success(
            language === 'vi' 
              ? `✅ File mới đã được xử lý thành công!` 
              : `✅ New file processed successfully!`
          );
          // Update progress
          setAuditReportBatchProgress(prev => ({
            ...prev,
            current: prev.current + 1
          }));
          
          // Refresh list
          await fetchAuditReports();
        } else {
          toast.error(
            language === 'vi' 
              ? `❌ File mới vẫn bị lỗi: ${result.error}` 
              : `❌ New file also failed: ${result.error}`
          );
        }
      } catch (error) {
        console.error('Retry error:', error);
        toast.error(
          language === 'vi' 
            ? `❌ Lỗi khi xử lý file mới` 
            : `❌ Error processing new file`
        );
      }
    };
    
    input.click();
  };

  // Process single audit report file (Match Survey Report pattern)
  const processSingleAuditReportFile = async (file, fileName) => {
    const result = {
      filename: fileName,
      success: false,
      surveyReportCreated: false,  // Use Survey Report field names for BatchResultsModal compatibility
      fileUploaded: false,
      surveyReportName: '',  // Use Survey Report field names for BatchResultsModal compatibility
      surveyReportNo: '',    // Use Survey Report field names for BatchResultsModal compatibility
      error: null
    };
    
    try {
      // Update status to 'processing'
      setAuditReportFileStatusMap(prev => ({ ...prev, [fileName]: 'processing' }));
      setAuditReportFileProgressMap(prev => ({ ...prev, [fileName]: 5 }));
      
      // Step 1: AI Analysis with validation check
      // Use 'analyzing' to match BatchProcessingModal expectation
      setAuditReportFileSubStatusMap(prev => ({ 
        ...prev, 
        [fileName]: 'analyzing' 
      }));

      // Smooth progress updates during analysis
      setAuditReportFileProgressMap(prev => ({ ...prev, [fileName]: 15 }));
      
      // Batch mode: WITH validation check (NO auto-retry)
      let analysisResponse;
      let data;

      // Progress update: Preparing analysis
      setAuditReportFileProgressMap(prev => ({ ...prev, [fileName]: 20 }));
      
      try {
        analysisResponse = await auditReportService.analyzeFile(
          selectedShip.id,
          file,
          false // Check validation in batch mode
        );
        data = analysisResponse.data || analysisResponse;
        
        // Progress update: Analysis received
        setAuditReportFileProgressMap(prev => ({ ...prev, [fileName]: 35 }));
      } catch (apiError) {
        // API call failed - check if it's validation error in response
        console.error(`API call failed for ${fileName}:`, apiError);
        
        // Check if error response contains validation error
        if (apiError.response?.data?.validation_error) {
          const errorData = apiError.response.data;
          const extractedInfo = `${errorData.extracted_ship_name || 'N/A'} (IMO: ${errorData.extracted_ship_imo || 'N/A'})`;
          const expectedInfo = `${errorData.expected_ship_name || 'N/A'} (IMO: ${errorData.expected_ship_imo || 'N/A'})`;
          
          const errorMsg = language === 'vi' 
            ? `Thông tin tàu không khớp!\nPDF có: ${extractedInfo}\nĐã chọn: ${expectedInfo}`
            : `Ship information mismatch!\nPDF has: ${extractedInfo}\nSelected: ${expectedInfo}`;
          
          throw new Error(errorMsg);
        }
        
        // Otherwise rethrow original error
        throw apiError;
      }
      
      // If validation error detected in successful response, STOP processing
      if (data.validation_error) {
        console.log(`❌ Ship validation failed for ${fileName}:`, {
          extracted: `${data.extracted_ship_name} (IMO: ${data.extracted_ship_imo})`,
          expected: `${data.expected_ship_name} (IMO: ${data.expected_ship_imo})`
        });
        
        // Build detailed error message
        const extractedInfo = `${data.extracted_ship_name || 'N/A'} (IMO: ${data.extracted_ship_imo || 'N/A'})`;
        const expectedInfo = `${data.expected_ship_name} (IMO: ${data.expected_ship_imo || 'N/A'})`;
        
        const errorMsg = language === 'vi' 
          ? `Thông tin tàu không khớp!\nPDF có: ${extractedInfo}\nĐã chọn: ${expectedInfo}`
          : `Ship information mismatch!\nPDF has: ${extractedInfo}\nSelected: ${expectedInfo}`;
        
        // Throw error to stop processing
        throw new Error(errorMsg);
      }
      
      if (!data.success || !data.analysis) {
        throw new Error(data.message || 'AI analysis failed');
      }

      const analysis = data.analysis;
      result.surveyReportName = analysis.audit_report_name || file.name;
      result.surveyReportNo = analysis.audit_report_no || '';
      
      setAuditReportFileProgressMap(prev => ({ ...prev, [fileName]: 45 }));

      // Step 2: Create report record
      // Keep 'analyzing' during record creation (part of same phase)
      setAuditReportFileSubStatusMap(prev => ({ 
        ...prev, 
        [fileName]: 'analyzing' 
      }));
      
      // Progress: Preparing database record
      setAuditReportFileProgressMap(prev => ({ ...prev, [fileName]: 50 }));

      const reportData = {
        ship_id: selectedShip.id,
        audit_report_name: analysis.audit_report_name || file.name,
        audit_type: analysis.audit_type || null,
        report_form: analysis.report_form || null,
        audit_report_no: analysis.audit_report_no || null,
        audit_date: analysis.audit_date || null,
        issued_by: analysis.issued_by || null,
        auditor_name: analysis.auditor_name || null,
        status: analysis.status || 'Valid',
        note: analysis.note || null,
        original_filename: analysis.original_filename || file.name  // Save original filename for report_form extraction
      };

      const createResponse = await auditReportService.create(reportData);
      const createdReport = createResponse.data || createResponse;
      result.surveyReportCreated = true;
      
      setAuditReportFileProgressMap(prev => ({ ...prev, [fileName]: 60 }));

      // Step 3: Upload files to Google Drive (RATE LIMITED to prevent 429 errors)
      // Use 'uploading' to match BatchProcessingModal expectation
      setAuditReportFileSubStatusMap(prev => ({ 
        ...prev, 
        [fileName]: 'uploading' 
      }));
      
      // Progress: Starting file upload
      setAuditReportFileProgressMap(prev => ({ ...prev, [fileName]: 65 }));

      // Only upload if file content is available
      if (analysis._file_content && analysis._filename) {
        // Progress: Uploading to Google Drive
        setAuditReportFileProgressMap(prev => ({ ...prev, [fileName]: 75 }));
        
        // Use rate limiter to prevent too many concurrent uploads
        await gdriveUploadLimiter.execute(async () => {
          await auditReportService.uploadFiles(
            createdReport.id,
            analysis._file_content,
            analysis._filename,
            analysis._content_type || 'application/pdf',
            analysis._summary_text || ''
          );
        });
        result.fileUploaded = true;
        
        // Progress: Upload complete
        setAuditReportFileProgressMap(prev => ({ ...prev, [fileName]: 90 }));
      }

      // Success!
      result.success = true;
      setAuditReportFileProgressMap(prev => ({ ...prev, [fileName]: 100 }));
      setAuditReportFileStatusMap(prev => ({ ...prev, [fileName]: 'completed' }));
      setAuditReportFileSubStatusMap(prev => ({ ...prev, [fileName]: null })); // Clear sub-status on complete

    } catch (error) {
      console.error(`Error processing ${fileName}:`, error);
      
      // Provide user-friendly error messages
      let errorMessage = error.response?.data?.detail || error.message || 'Processing failed';
      
      // Special handling for specific error types
      if (error.response?.status === 429) {
        // Rate limit error
        errorMessage = language === 'vi' 
          ? 'Quá nhiều yêu cầu. Hệ thống sẽ tự động thử lại...'
          : 'Too many requests. System will retry automatically...';
      } else if (errorMessage.includes('empty summary') || errorMessage.includes('corrupted') || errorMessage.includes('unreadable')) {
        // Document AI failed to extract - make error very clear
        errorMessage = language === 'vi'
          ? `❌ Không thể đọc file: ${errorMessage}\n\n💡 Vui lòng kiểm tra:\n• File có bị hỏng không?\n• File có phải PDF hợp lệ không?\n• Chất lượng scan có đủ rõ không?\n\n🔄 Click "Re-upload" để thử lại với file khác.`
          : `❌ Cannot read file: ${errorMessage}\n\n💡 Please check:\n• Is the file corrupted?\n• Is it a valid PDF?\n• Is the scan quality clear enough?\n\n🔄 Click "Re-upload" to try again with a different file.`;
      }
      
      result.error = errorMessage;
      result.success = false;
      result.canRetry = true;  // Mark as retryable
      setAuditReportFileStatusMap(prev => ({ ...prev, [fileName]: 'error' }));
      setAuditReportFileSubStatusMap(prev => ({ ...prev, [fileName]: errorMessage }));
    }
    
    // Brief pause before returning (match Survey Report)
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return result;
  };

  // Save notes
  const handleSaveAuditReportNotes = async () => {
    try {
      const reportId = auditReportNotesModal.report?.id;
      const notes = auditReportNotesModal.notes;

      await auditReportService.update(reportId, { note: notes });
      
      toast.success(language === 'vi' ? 'Đã lưu ghi chú!' : 'Notes saved!');
      setAuditReportNotesModal({ show: false, report: null, notes: '' });
      
      // Refresh list
      await fetchAuditReports();
    } catch (error) {
      console.error('Error saving notes:', error);
      toast.error(language === 'vi' ? 'Lỗi khi lưu ghi chú' : 'Error saving notes');
    }
  };

  // Fetch audit reports when ship changes or submenu changes to audit_report
  useEffect(() => {
    if (selectedShip && selectedSubMenu === 'audit_report') {
      fetchAuditReports();
    }
  }, [selectedShip, selectedSubMenu]);


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
              'ism': '/ism-isps-mlc',
              'isps': '/isps',
              'mlc': '/mlc',
              'supplies': '/supplies'
            };
            if (routes[cat]) {
              window.location.href = routes[cat];
            }
          }}
          onAddRecord={handleAddRecord}
          showAddShipButton={false}
        />
      }
    >
      {/* Add Ship Modal */}
      <AddShipModal 
        isOpen={showAddShipModal}
        onClose={() => setShowAddShipModal(false)}
        onShipCreated={handleShipCreated}
      />

      {/* Page Title with Ship Select Button */}
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-800">
          {language === 'vi' ? 'ISM - ISPS - MLC' : 'ISM - ISPS - MLC'}
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
              <span className="text-xl">🚢</span>
              {language === 'vi' ? 'Chọn tàu' : 'Ship Select'}
            </button>
          </div>
        )}
      </div>

      {/* Company Info Panel - Show when no ship selected */}
      {!selectedShip && companyData && (
        <CompanyInfoPanel companyData={companyData} />
      )}

      {/* Ship Detail Panel - Show when ship is selected */}
      {selectedShip && (
        <ShipDetailPanel 
          ship={selectedShip}
          onClose={() => {
            setSelectedShip(null);
            localStorage.removeItem('selectedShipId');
          }}
          onEdit={() => toast.info(language === 'vi' ? 'Chức năng chỉnh sửa tàu sẽ được triển khai' : 'Edit ship feature will be implemented')}
          onDelete={() => toast.info(language === 'vi' ? 'Chức năng xóa tàu sẽ được triển khai' : 'Delete ship feature will be implemented')}
          onShipUpdate={(updatedShip) => setSelectedShip(updatedShip)}
          onShipSelect={() => setShowShipModal(true)}
        />
      )}

      {/* Ship Selection Modal */}
      {showShipModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowShipModal(false)}>
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-800">
                  {language === 'vi' ? 'Chọn tàu để xem thông tin chứng chỉ' : 'Select a ship to view certificate information'}
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
                <div className="grid grid-cols-2 gap-4">
                  {ships.map(ship => (
                    <div
                      key={ship.id}
                      className="border-2 border-gray-200 rounded-lg p-4 hover:border-purple-500 transition-all cursor-pointer"
                    >
                      <div className="text-center mb-4">
                        <div className="text-4xl mb-2">🚢</div>
                        <h3 className="font-bold text-lg text-gray-800">{ship.name}</h3>
                      </div>
                      <div className="space-y-1 text-sm mb-4">
                        <div className="flex justify-between">
                          <span className="text-gray-600">IMO:</span>
                          <span className="font-medium">{ship.imo || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">{language === 'vi' ? 'Cờ:' : 'Flag:' }</span>
                          <span className="font-medium">{ship.flag || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">{language === 'vi' ? 'Đẳng kiểm:' : 'Class Society:'}</span>
                          <span className="font-medium">{ship.class_society || '-'}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleShipSelect(ship)}
                        className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg font-medium transition-all"
                      >
                        {language === 'vi' ? 'Chọn' : 'Select'}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* SubMenuBar */}
      <SubMenuBar
        selectedCategory="ism"
        selectedSubMenu={selectedSubMenu}
        onSubMenuChange={handleSubMenuChange}
      />

      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-md p-6 mt-6">
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            <p className="mt-2 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
          </div>
        ) : !selectedShip ? (
          /* Ship Cards Grid - Show all ships for selection when no ship selected */
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
                    onClick={() => handleShipSelect(ship)}
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
                          <span className="text-gray-600 text-xs">{language === 'vi' ? 'Đẳng kiểm:' : 'Class Society:'}</span>
                          <span className="font-semibold text-gray-800 text-xs truncate ml-1">{ship.class_society}</span>
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
                        onClick={(e) => {
                          e.stopPropagation();
                          handleShipSelect(ship);
                        }}
                        className="w-full bg-purple-600 hover:bg-purple-700 text-white py-1.5 px-3 rounded-md text-sm font-medium transition-all"
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
          /* Show submenu content when ship is selected */
          selectedSubMenu === 'audit_certificate' ? (
            <div className="space-y-4">
              {/* Action Buttons */}
              <AuditCertificateActionButtons
                language={language}
                selectedShip={selectedShip}
                selectedCertificatesCount={selectedCertificates.size}
                isRefreshing={isRefreshing}
                isUpdatingSurveyTypes={isUpdatingNextSurvey}
                linksFetching={linksFetching}
                linksFetchProgress={linksFetchProgress}
                onUpdateSurveyTypes={handleUpdateSurveyTypes}
                onUpcomingSurvey={handleUpcomingSurvey}
                onAddCertificate={handleAddCertificate}
                onRefresh={handleRefreshCertificates}
              />

              {/* Filters */}
              <AuditCertificateFilters
                filters={certificateFilters}
                onFilterChange={setCertificateFilters}
                certificateTypes={getUniqueCertificateTypes()}
                totalCount={auditCertificates.length}
                filteredCount={getFilteredCertificates().length}
                language={language}
              />

              {/* Table */}
              {certificatesLoading ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <p className="mt-2 text-gray-600">
                    {language === 'vi' ? 'Đang tải...' : 'Loading...'}
                  </p>
                </div>
              ) : (
                <AuditCertificateTable
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
          ) : selectedSubMenu === 'audit_report' ? (
            /* Audit Report List */
            <AuditReportList
              selectedShip={selectedShip}
              reports={auditReports}
              loading={auditReportsLoading}
              selectedReports={selectedAuditReports}
              onSelectReport={handleSelectAuditReport}
              onSelectAll={handleSelectAllAuditReports}
              filters={auditReportFilters}
              onFiltersChange={setAuditReportFilters}
              sort={auditReportSort}
              onSortChange={setAuditReportSort}
              onRefresh={handleRefreshAuditReports}
              isRefreshing={isRefreshingAuditReports}
              onStartBatchProcessing={startBatchProcessingAuditReports}
              onAddReport={() => setShowAddAuditReportModal(true)}
              onEditReport={(report) => {
                setEditingAuditReport(report);
                setShowEditAuditReportModal(true);
              }}
              onNotesClick={(report, notes) => {
                setAuditReportNotesModal({ show: true, report, notes });
              }}
              language={language}
            />
          ) : selectedSubMenu === 'approval_document' ? (
            /* Approval Document Section */
            <ApprovalDocumentTable selectedShip={selectedShip} />
          ) : selectedSubMenu === 'other_document' ? (
            /* Other Audit Document Section */
            <OtherAuditDocumentTable selectedShip={selectedShip} />
          ) : (
            /* Placeholder for future submenus */
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📄</div>
              <h3 className="text-2xl font-semibold text-gray-700 mb-2">
                {language === 'vi' ? 'Chức năng đang phát triển' : 'Feature under development'}
              </h3>
              <p className="text-gray-500">
                {language === 'vi' 
                  ? 'Chức năng này sẽ được triển khai trong các giai đoạn tiếp theo' 
                  : 'This feature will be implemented in upcoming phases'}
              </p>
            </div>
          )
        )}
      </div>



      {/* Certificate Context Menu */}
      {contextMenu && (
        <div
          className="fixed bg-white shadow-lg rounded-lg py-2 z-[9999] border border-gray-200 min-w-[200px]"
          style={{ top: contextMenu.y, left: contextMenu.x }}
          onClick={(e) => e.stopPropagation()}
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
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
          >
            <span>👁️</span>
            {selectedCertificates.size > 1 
              ? (language === 'vi' ? `Xem file (${selectedCertificates.size} chứng chỉ)` : `View Files (${selectedCertificates.size} certificates)`)
              : (language === 'vi' ? 'Xem file' : 'View File')
            }
          </button>

          {/* Download - works for single and multiple */}
          <button
            onClick={() => {
              if (selectedCertificates.size > 1) {
                handleBulkDownload();
              } else if (contextMenu.certificate?.google_drive_file_id) {
                window.open(`https://drive.google.com/uc?export=download&id=${contextMenu.certificate.google_drive_file_id}`, '_blank');
              }
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
          >
            <span>⬇️</span>
            {selectedCertificates.size > 1 
              ? (language === 'vi' ? `Tải xuống (${selectedCertificates.size} file)` : `Download (${selectedCertificates.size} files)`)
              : (language === 'vi' ? 'Tải xuống' : 'Download')
            }
          </button>

          {/* Copy Link - works for single and multiple */}
          <button
            onClick={() => {
              handleBulkCopyLinks();
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
          >
            <span>🔗</span>
            {selectedCertificates.size > 1 
              ? (language === 'vi' ? `Sao chép link (${selectedCertificates.size} file)` : `Copy Links (${selectedCertificates.size} files)`)
              : (language === 'vi' ? 'Copy link' : 'Copy Link')
            }
          </button>

          {selectedCertificates.size === 1 && (
            <>
              <div className="border-t border-gray-200 my-1"></div>
              
              {/* Auto Rename File - single file only */}
              {contextMenu.certificate?.google_drive_file_id && (
                <button
                  onClick={() => {
                    handleAutoRenameFile(contextMenu.certificate);
                    setContextMenu(null);
                  }}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-purple-50 hover:text-purple-600 flex items-center gap-2"
                >
                  <span>⚡</span>
                  <span>{language === 'vi' ? 'Đổi tên file tự động' : 'Auto Rename File'}</span>
                </button>
              )}
              
              <div className="border-t border-gray-200 my-1"></div>
              
              {/* Edit - single only */}
              <button
                onClick={() => {
                  handleEditCertificate(contextMenu.certificate);
                  setContextMenu(null);
                }}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
              >
                <span>✏️</span>
                <span>{language === 'vi' ? 'Chỉnh sửa' : 'Edit'}</span>
              </button>
            </>
          )}

          {/* Delete - works for single and multiple */}
          <button
            onClick={() => {
              handleDeleteCertificate(contextMenu.certificate);
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2 text-red-600"
          >
            <span>🗑️</span>
            {selectedCertificates.size > 1 
              ? (language === 'vi' ? `Xóa (${selectedCertificates.size} chứng chỉ)` : `Delete (${selectedCertificates.size} certificates)`)
              : (language === 'vi' ? 'Xóa' : 'Delete')
            }
          </button>
        </div>
      )}

      {/* Survey Type Context Menu */}
      {surveyTypeContextMenu.show && (
        <div
          className="fixed bg-white shadow-lg rounded-lg py-2 z-[9999] border border-gray-200 min-w-[180px]"
          style={{ top: surveyTypeContextMenu.y, left: surveyTypeContextMenu.x }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="px-4 py-2 text-xs text-gray-500 border-b">
            {language === 'vi' ? 'Thay đổi loại survey' : 'Change survey type'}
          </div>
          {['Annual', 'Intermediate', 'Renewal', 'Special'].map(type => (
            <button
              key={type}
              onClick={() => handleSurveyTypeChange(type)}
              className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-100 ${
                surveyTypeContextMenu.currentType === type ? 'bg-blue-50 text-blue-600 font-medium' : ''
              }`}
            >
              {surveyTypeContextMenu.currentType === type && '✓ '}{type}
            </button>
          ))}
        </div>
      )}

      {/* Add Certificate Modal */}
      <AddAuditCertificateModal
        isOpen={showAddCertificateModal}
        onClose={handleClose}
        onSave={handleSaveCertificate}
        onSuccess={() => fetchAuditCertificates(selectedShip.id)}
        selectedShip={selectedShip}
        aiConfig={aiConfig}
        language={language}
      />

      {/* Edit Certificate Modal */}
      <EditAuditCertificateModal
        isOpen={showEditCertificateModal}
        onClose={() => {
          setShowEditCertificateModal(false);
          setEditingCertificate(null);
        }}
        onSave={handleUpdateCertificate}
        certificate={editingCertificate}
        language={language}
      />

      {/* Delete Certificate Modal */}
      <DeleteAuditCertificateModal
        isOpen={showDeleteCertificateModal}
        onClose={() => {
          setShowDeleteCertificateModal(false);
          setDeletingCertificate(null);
        }}
        onConfirm={handleConfirmDelete}
        certificate={deletingCertificate}
        selectedCount={selectedCertificates.size}
      />

      {/* Notes Modal */}
      <AuditCertificateNotesModal
        isOpen={notesModal.show}
        onClose={() => setNotesModal({ show: false, certificate: null, notes: '' })}
        onSave={handleSaveNotes}
        certificate={notesModal.certificate}
        notes={notesModal.notes}
        language={language}
      />

      {/* Upcoming Survey Modal */}
      <AuditUpcomingSurveyModal
        isOpen={upcomingSurveyModal.show}
        onClose={() => setUpcomingSurveyModal({
          show: false, surveys: [], totalCount: 0,
          company: '', companyName: '', checkDate: ''
        })}
        surveys={upcomingSurveyModal.surveys}
        totalCount={upcomingSurveyModal.totalCount}
        companyName={upcomingSurveyModal.companyName}
        checkDate={upcomingSurveyModal.checkDate}
        language={language}
      />

      {/* ========== AUDIT REPORT MODALS ========== */}
      
      {/* Add Audit Report Modal */}
      <AddAuditReportModal
        isOpen={showAddAuditReportModal}
        onClose={() => setShowAddAuditReportModal(false)}
        selectedShip={selectedShip}
        onReportAdded={() => {
          setShowAddAuditReportModal(false);
          fetchAuditReports();
          toast.success(language === 'vi' ? 'Đã thêm audit report!' : 'Audit report added!');
        }}
        onStartBatchProcessing={(files) => {
          setShowAddAuditReportModal(false);
          startBatchProcessingAuditReports(files);
        }}
        language={language}
      />

      {/* Edit Audit Report Modal */}
      {showEditAuditReportModal && editingAuditReport && (
        <EditAuditReportModal
          isOpen={showEditAuditReportModal}
          onClose={() => {
            setShowEditAuditReportModal(false);
            setEditingAuditReport(null);
          }}
          report={editingAuditReport}
          onReportUpdated={() => {
            setShowEditAuditReportModal(false);
            setEditingAuditReport(null);
            fetchAuditReports();
            toast.success(language === 'vi' ? 'Đã cập nhật audit report!' : 'Audit report updated!');
          }}
          language={language}
        />
      )}

      {/* Audit Report Notes Modal */}
      <AuditReportNotesModal
        isOpen={auditReportNotesModal.show}
        onClose={() => setAuditReportNotesModal({ show: false, report: null, notes: '' })}
        report={auditReportNotesModal.report}
        notes={auditReportNotesModal.notes}
        onNotesChange={(notes) => setAuditReportNotesModal(prev => ({ ...prev, notes }))}
        onSave={handleSaveAuditReportNotes}
        language={language}
      />

      {/* Batch Processing Modal for Audit Reports */}
      <BatchProcessingModal
        isOpen={isBatchProcessingAuditReports}
        isMinimized={isAuditReportBatchModalMinimized}
        onMinimize={() => setIsAuditReportBatchModalMinimized(true)}
        onRestore={() => setIsAuditReportBatchModalMinimized(false)}
        progress={auditReportBatchProgress}
        fileProgressMap={auditReportFileProgressMap}
        fileStatusMap={auditReportFileStatusMap}
        fileSubStatusMap={auditReportFileSubStatusMap}
        onRetryFile={handleRetryFailedAuditReport}
        language={language}
        title={language === 'vi' ? 'Đang xử lý Audit Reports' : 'Processing Audit Reports'}
      />

      {/* Batch Results Modal for Audit Reports */}
      <BatchResultsModal
        isOpen={showAuditReportBatchResults}
        onClose={() => {
          setShowAuditReportBatchResults(false);
          setAuditReportBatchResults([]);
        }}
        results={auditReportBatchResults}
        language={language}
      />
    </MainLayout>
  );
};

export default IsmIspsMLc;
