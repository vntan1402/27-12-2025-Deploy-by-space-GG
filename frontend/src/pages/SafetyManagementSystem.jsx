import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useBackgroundTask } from '../contexts/BackgroundTaskContext';
import { MainLayout, Sidebar, SubMenuBar, CompanyInfoPanel } from '../components';
import {
  CompanyCertTable,
  AddCompanyCertModal,
  EditCompanyCertModal,
  DeleteCompanyCertModal,
  CompanyCertNotesModal
} from '../components/CompanyCert';
import { AuditUpcomingSurveyModal } from '../components/AuditCertificate';
import { companyCertService } from '../services';
import { toast } from 'sonner';
import api from '../services/api';

const SafetyManagementSystem = () => {
  const { language, user } = useAuth();
  
  // State
  const [selectedSubMenu, setSelectedSubMenu] = useState('company_cert');
  const [companyData, setCompanyData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Company Cert States
  const [companyCerts, setCompanyCerts] = useState([]);
  const [certsLoading, setCertsLoading] = useState(false);
  const [selectedCerts, setSelectedCerts] = useState(new Set());
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [editingCert, setEditingCert] = useState(null);
  const [deletingCert, setDeletingCert] = useState(null);
  const [notesCert, setNotesCert] = useState(null);
  
  // Upcoming Audit Modal
  const [upcomingAuditModal, setUpcomingAuditModal] = useState({
    show: false,
    surveys: [],
    totalCount: 0,
    company: '',
    companyName: '',
    checkDate: ''
  });
  const [isLoadingUpcomingAudit, setIsLoadingUpcomingAudit] = useState(false);
  
  // Context Menu
  const [contextMenu, setContextMenu] = useState(null);
  
  // Sort & Filter
  const [sortConfig, setSortConfig] = useState({
    column: 'cert_name',
    direction: 'asc'
  });

  // Filter States
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Floating Progress for Auto Rename
  const [floatingRenameProgress, setFloatingRenameProgress] = useState({
    isVisible: false,
    completed: 0,
    total: 0,
    currentFile: '',
    errors: [],
    status: 'processing'
  });

  // Load company data & certificates
  useEffect(() => {
    loadCompanyData();
    if (selectedSubMenu === 'company_cert') {
      loadCompanyCerts();
    }
    
    // Close context menu when clicking outside
    const handleClickOutside = () => setContextMenu(null);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [selectedSubMenu]);

  const loadCompanyData = async () => {
    if (!user?.company) return;
    
    try {
      // Get company info by ID (includes total_ships and total_crew)
      const response = await api.get(`/api/companies/${user.company}`);
      setCompanyData(response.data);
    } catch (error) {
      console.error('Error loading company:', error);
    }
  };

  const loadCompanyCerts = async () => {
    setCertsLoading(true);
    try {
      const certs = await companyCertService.getCompanyCerts();
      setCompanyCerts(certs);
    } catch (error) {
      console.error('Error loading company certs:', error);
      // Check if it's a permission error (403) - show user-friendly message
      if (error.response?.status === 403) {
        const message = error.response?.data?.detail || 
          (language === 'vi' 
            ? 'Bạn không có quyền xem Company Certificates' 
            : 'You do not have permission to view Company Certificates');
        toast.info(message, { duration: 5000 });
      } else {
        toast.error(language === 'vi' ? 'Không thể tải certificates' : 'Failed to load certificates');
      }
    } finally {
      setCertsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadCompanyCerts();
    setIsRefreshing(false);
    toast.success(language === 'vi' ? 'Đã làm mới!' : 'Refreshed!');
  };

  const handleSort = (column) => {
    setSortConfig(prev => ({
      column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const handleSelectCert = (certId) => {
    setSelectedCerts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(certId)) {
        newSet.delete(certId);
      } else {
        newSet.add(certId);
      }
      return newSet;
    });
  };

  const handleSelectAllCerts = (checked) => {
    if (checked) {
      const filteredCerts = getFilteredAndSortedCerts();
      setSelectedCerts(new Set(filteredCerts.map(cert => cert.id)));
    } else {
      setSelectedCerts(new Set());
    }
  };

  const handleDoubleClick = (cert) => {
    // Open Edit modal on double click
    setEditingCert(cert);
    setShowEditModal(true);
  };

  const handleViewFile = (cert) => {
    const fileId = cert?.file_id || cert?.google_drive_file_id;
    if (fileId) {
      window.open(`https://drive.google.com/file/d/${fileId}/view`, '_blank');
    } else {
      toast.warning(
        language === 'vi'
          ? 'Chứng chỉ này chưa có file đính kèm'
          : 'This certificate has no attached file'
      );
    }
  };

  const handleBulkViewFiles = () => {
    if (selectedCerts.size === 0) {
      toast.warning(language === 'vi' ? 'Vui lòng chọn chứng chỉ' : 'Please select certificates');
      return;
    }

    const selectedCertsList = companyCerts.filter(cert => selectedCerts.has(cert.id));
    const certsWithFiles = selectedCertsList.filter(cert => cert.file_id || cert.google_drive_file_id);

    if (certsWithFiles.length === 0) {
      toast.warning(
        language === 'vi'
          ? 'Không có chứng chỉ nào có file đính kèm'
          : 'No certificates have attached files'
      );
      return;
    }

    // Open each file in a new tab
    certsWithFiles.forEach(cert => {
      const fileId = cert.file_id || cert.google_drive_file_id;
      window.open(`https://drive.google.com/file/d/${fileId}/view`, '_blank');
    });

    toast.success(
      language === 'vi'
        ? `Đã mở ${certsWithFiles.length} file`
        : `Opened ${certsWithFiles.length} files`
    );
  };

  const handleRightClick = (e, cert) => {
    e.preventDefault();
    
    if (!selectedCerts.has(cert.id)) {
      setSelectedCerts(new Set([cert.id]));
    }
    
    const menuWidth = 250;
    const menuHeight = 300;
    let x = e.clientX;
    let y = e.clientY;
    
    if (x + menuWidth > window.innerWidth) {
      x = window.innerWidth - menuWidth - 10;
    }
    if (y + menuHeight > window.innerHeight) {
      y = window.innerHeight - menuHeight - 10;
    }
    
    x = Math.max(10, x);
    y = Math.max(10, y);
    
    setContextMenu({ x, y, certificate: cert });
  };

  const handleBulkDelete = async () => {
    if (selectedCerts.size === 0) {
      toast.warning(language === 'vi' ? 'Vui lòng chọn chứng chỉ' : 'Please select certificates');
      return;
    }

    if (!window.confirm(language === 'vi' 
      ? `Bạn có chắc muốn xóa ${selectedCerts.size} chứng chỉ?`
      : `Are you sure you want to delete ${selectedCerts.size} certificates?`
    )) {
      return;
    }

    try {
      await companyCertService.bulkDeleteCompanyCerts(Array.from(selectedCerts));
      toast.success(language === 'vi' 
        ? `Đã xóa ${selectedCerts.size} chứng chỉ!`
        : `Deleted ${selectedCerts.size} certificates!`
      );
      setSelectedCerts(new Set());
      await loadCompanyCerts();
    } catch (error) {
      console.error('Bulk delete error:', error);
      toast.error('Failed to delete certificates');
    }
  };

  const handleBulkDownload = async () => {
    if (selectedCerts.size === 0) {
      toast.warning(language === 'vi' ? 'Vui lòng chọn chứng chỉ' : 'Please select certificates');
      return;
    }

    try {
      const selectedCertsList = companyCerts.filter(cert => selectedCerts.has(cert.id));
      const certsWithFiles = selectedCertsList.filter(cert => cert.file_id || cert.google_drive_file_id);

      if (certsWithFiles.length === 0) {
        toast.warning(
          language === 'vi'
            ? 'Không có chứng chỉ nào có file đính kèm'
            : 'No certificates have attached files'
        );
        return;
      }

      let downloadedCount = 0;

      for (const cert of certsWithFiles) {
        try {
          const fileId = cert.file_id || cert.google_drive_file_id;
          
          // Generate filename
          const filename = `${cert.cert_abbreviation || cert.cert_name}.pdf`;
          
          // Use direct Google Drive download URL
          const downloadUrl = `https://drive.google.com/uc?export=download&id=${fileId}`;
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = filename;
          link.target = '_blank';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          downloadedCount++;
          
          // Small delay between downloads
          await new Promise(resolve => setTimeout(resolve, 200));
        } catch (error) {
          console.error(`Download error for ${cert.cert_abbreviation}:`, error);
        }
      }

      if (downloadedCount > 0) {
        toast.success(
          language === 'vi'
            ? `✅ Đang tải xuống ${downloadedCount} file`
            : `✅ Downloading ${downloadedCount} file(s)`
        );
      } else {
        toast.warning(
          language === 'vi'
            ? '⚠️ Không có file để tải xuống'
            : '⚠️ No files to download'
        );
      }
    } catch (error) {
      console.error('Bulk download error:', error);
      toast.error(
        language === 'vi'
          ? '❌ Lỗi khi tải xuống file'
          : '❌ Error downloading files'
      );
    }
  };

  const handleBulkCopyLinks = async () => {
    if (selectedCerts.size === 0) {
      toast.warning(language === 'vi' ? 'Vui lòng chọn chứng chỉ' : 'Please select certificates');
      return;
    }

    try {
      const selectedCertsList = companyCerts.filter(cert => selectedCerts.has(cert.id));
      const certsWithFiles = selectedCertsList.filter(cert => cert.file_id || cert.google_drive_file_id);

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
        const fileId = cert.file_id || cert.google_drive_file_id;
        
        try {
          const response = await api.get(`/api/gdrive/file/${fileId}/view`);
          if (response.data?.success && response.data?.view_url) {
            const viewUrl = response.data.view_url;
            links.push(`${cert.cert_abbreviation || cert.cert_name}: ${viewUrl}`);
          }
        } catch (error) {
          console.error(`Error getting link for ${cert.cert_abbreviation}:`, error);
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
            ? '❌ Không thể lấy link'
            : '❌ Could not get links'
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

  const handleAutoRenameFile = async (cert) => {
    try {
      toast.info(language === 'vi' 
        ? 'Đang đổi tên file...' 
        : 'Renaming file...'
      );
      
      const response = await api.post(`/api/company-certs/${cert.id}/auto-rename-file`);
      
      if (response.data.success) {
        toast.success(language === 'vi' 
          ? `Đã đổi tên: ${response.data.new_name}` 
          : `Renamed to: ${response.data.new_name}`
        );
        await loadCompanyCerts();
      } else {
        toast.error(response.data.message || 'Failed to rename file');
      }
    } catch (error) {
      console.error('Error renaming file:', error);
      // ⭐ FIX: Display actual backend error message (permission errors)
      const backendMessage = error.response?.data?.detail;
      const errorMessage = backendMessage || (language === 'vi' 
        ? 'Không thể đổi tên file' 
        : 'Failed to rename file');
      toast.error(errorMessage);
    }
  };

  const handleBulkAutoRenameFiles = async () => {
    const selectedCertsList = companyCerts.filter(cert => selectedCerts.has(cert.id));

    if (selectedCertsList.length === 0) {
      toast.warning(language === 'vi' 
        ? 'Vui lòng chọn chứng chỉ' 
        : 'Please select certificates'
      );
      return;
    }

    const certsWithFiles = selectedCertsList.filter(cert => 
      cert.file_id || cert.google_drive_file_id
    );

    if (certsWithFiles.length === 0) {
      toast.warning(language === 'vi' 
        ? 'Không có chứng chỉ nào có file đính kèm' 
        : 'No certificates with attached files'
      );
      return;
    }

    const confirmMsg = language === 'vi' 
      ? `Đổi tên tự động cho ${certsWithFiles.length} file?` 
      : `Auto rename ${certsWithFiles.length} files?`;
    
    if (!window.confirm(confirmMsg)) return;

    // Show floating progress
    setFloatingRenameProgress({
      isVisible: true,
      completed: 0,
      total: certsWithFiles.length,
      currentFile: language === 'vi' ? 'Đang khởi động...' : 'Starting...',
      errors: [],
      status: 'processing'
    });

    // Clear selection so user can continue working
    setSelectedCerts(new Set());

    try {
      // Get certificate IDs
      const certificateIds = certsWithFiles.map(cert => cert.id);

      // Start background bulk rename
      console.log(`🚀 Starting background bulk rename for ${certificateIds.length} company certificates`);
      const startResponse = await api.post('/api/company-certs/bulk-auto-rename', {
        certificate_ids: certificateIds
      });

      if (!startResponse.data?.success || !startResponse.data?.task_id) {
        throw new Error(startResponse.data?.message || 'Failed to start bulk rename');
      }

      const taskId = startResponse.data.task_id;
      console.log(`📋 Bulk rename task started: ${taskId}`);

      // Poll for status
      const pollInterval = 1000; // 1 second
      const maxPolls = 300; // 5 minutes max
      let pollCount = 0;

      const pollStatus = async () => {
        try {
          pollCount++;
          const statusResponse = await api.get(`/api/company-certs/bulk-auto-rename/${taskId}`);
          const status = statusResponse.data;

          // Update floating progress
          setFloatingRenameProgress(prev => ({
            ...prev,
            completed: status.completed_files || 0,
            currentFile: status.current_file || '',
            errors: (status.results || [])
              .filter(r => !r.success)
              .map(r => r.error || 'Unknown error'),
            status: status.status
          }));

          // Check if completed
          if (status.status === 'completed' || status.status === 'completed_with_errors' || status.status === 'failed') {
            // Refresh certificates list
            if ((status.completed_files || 0) > 0) {
              await loadCompanyCerts();
            }
            return; // Stop polling
          }

          // Continue polling if not completed
          if (pollCount < maxPolls) {
            setTimeout(pollStatus, pollInterval);
          } else {
            setFloatingRenameProgress(prev => ({
              ...prev,
              status: 'failed',
              errors: [...prev.errors, 'Timeout: Bulk rename took too long']
            }));
          }

        } catch (pollError) {
          console.error('❌ Poll error:', pollError);
          setFloatingRenameProgress(prev => ({
            ...prev,
            status: 'failed',
            errors: [...prev.errors, pollError.message || 'Polling error']
          }));
        }
      };

      // Start polling
      setTimeout(pollStatus, pollInterval);

    } catch (error) {
      console.error('❌ Bulk auto rename error:', error);
      setFloatingRenameProgress(prev => ({
        ...prev,
        status: 'failed',
        errors: [error.message || 'Failed to start bulk rename']
      }));
    }
  };

  // Close floating progress
  const handleCloseFloatingProgress = () => {
    setFloatingRenameProgress({
      isVisible: false,
      completed: 0,
      total: 0,
      currentFile: '',
      errors: [],
      status: 'processing'
    });
  };

  const handleUpdateNextAudits = async () => {
    if (!window.confirm(language === 'vi' 
      ? 'Bạn có chắc muốn cập nhật lại tất cả ngày kiểm tra tiếp theo? Thao tác này sẽ tính toán lại dựa trên quy tắc kinh doanh hiện tại.'
      : 'Are you sure you want to recalculate all next audit dates? This will update all certificates based on current business rules.'
    )) {
      return;
    }

    try {
      toast.loading(language === 'vi' ? 'Đang cập nhật...' : 'Updating...', { id: 'update-audits' });
      
      const result = await companyCertService.recalculateAllNextSurveys();
      
      toast.success(language === 'vi' 
        ? `Đã cập nhật ${result.updated_count} chứng chỉ! (Bỏ qua: ${result.skipped_count})`
        : `Updated ${result.updated_count} certificates! (Skipped: ${result.skipped_count})`,
        { id: 'update-audits' }
      );
      
      // Reload certificates to show updated data
      await loadCompanyCerts();
    } catch (error) {
      console.error('Update audits error:', error);
      toast.error(language === 'vi' ? 'Cập nhật thất bại!' : 'Update failed!', { id: 'update-audits' });
    }
  };

  const handleUpcomingAudit = async () => {
    setIsLoadingUpcomingAudit(true);
    try {
      // Include company parameter for System Admin to see correct data
      const companyParam = user?.company ? `&company=${user.company}` : '';
      const response = await api.get(`/api/audit-certificates/upcoming-surveys?days=30${companyParam}`);
      const data = response.data;
      
      // Always show modal, even if no audits
      setUpcomingAuditModal({
        show: true,
        surveys: data.upcoming_surveys || [],
        totalCount: data.total_count || 0,
        company: data.company,
        companyName: data.company_name,
        checkDate: data.check_date
      });
      
      // Optional: Show toast for non-empty results
      if (data.upcoming_surveys && data.upcoming_surveys.length > 0) {
        toast.info(language === 'vi' 
          ? `⚠️ Có ${data.upcoming_surveys.length} chứng chỉ trong audit window`
          : `⚠️ ${data.upcoming_surveys.length} certificates in audit window`
        );
      }
    } catch (error) {
      console.error('Error checking upcoming audits:', error);
      toast.error(language === 'vi' 
        ? '❌ Lỗi kiểm tra upcoming audits'
        : '❌ Error checking upcoming audits'
      );
    } finally {
      setIsLoadingUpcomingAudit(false);
    }
  };


  // Calculate certificate status (same logic as CompanyCertTable)
  const getCertificateStatus = (cert) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // PRIORITY 1: Check Next Audit if available
    if (cert.next_audit && cert.next_audit_type) {
      let nextAuditDate;
      if (cert.next_audit.includes('/')) {
        const [day, month, year] = cert.next_audit.split('/');
        nextAuditDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      } else {
        nextAuditDate = new Date(cert.next_audit);
      }
      
      if (!isNaN(nextAuditDate.getTime())) {
        nextAuditDate.setHours(0, 0, 0, 0);
        
        // Determine window based on audit type
        let windowOpen, windowClose;
        
        if (cert.next_audit_type.includes('Annual')) {
          // Annual: ±3M window
          windowOpen = new Date(nextAuditDate);
          windowOpen.setMonth(windowOpen.getMonth() - 3);
          windowClose = new Date(nextAuditDate);
          windowClose.setMonth(windowClose.getMonth() + 3);
        } else if (cert.next_audit_type === 'Renewal' || cert.next_audit_type === 'Initial') {
          // Renewal/Initial: -3M window
          windowOpen = new Date(nextAuditDate);
          windowOpen.setMonth(windowOpen.getMonth() - 3);
          windowClose = nextAuditDate;
        } else {
          // Default: use next_audit date as reference
          windowOpen = new Date(nextAuditDate);
          windowOpen.setMonth(windowOpen.getMonth() - 3);
          windowClose = nextAuditDate;
        }
        
        // Check status based on window
        if (today < windowOpen) {
          // Not yet in audit window
          return 'Valid';
        } else if (today > windowClose) {
          // Passed window close
          return 'Expired';
        } else {
          // Inside window: check days remaining to window close
          const diffTime = windowClose.getTime() - today.getTime();
          const daysToClose = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
          
          if (daysToClose <= 30) {
            return 'Critical';
          } else {
            return 'Due Soon';
          }
        }
      }
    }
    
    // PRIORITY 2: Fallback to Valid Date if no Next Audit
    if (!cert.valid_date) return 'Unknown';
    
    let validDate;
    if (cert.valid_date.includes('/')) {
      const [day, month, year] = cert.valid_date.split('/');
      validDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    } else {
      validDate = new Date(cert.valid_date);
    }
    
    if (isNaN(validDate.getTime())) return 'Unknown';
    validDate.setHours(0, 0, 0, 0);
    
    if (validDate < today) return 'Expired';
    
    const diffTime = validDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays <= 30) return 'Critical';
    if (diffDays <= 90) return 'Due Soon';
    return 'Valid';
  };

  const getFilteredAndSortedCerts = () => {
    let filtered = [...companyCerts];
    
    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(cert =>
        cert.cert_name?.toLowerCase().includes(query) ||
        cert.cert_no?.toLowerCase().includes(query) ||
        cert.company_name?.toLowerCase().includes(query) ||
        cert.issued_by?.toLowerCase().includes(query)
      );
    }

    // Status filter - use same logic as table display
    if (statusFilter !== 'all') {
      filtered = filtered.filter(cert => {
        const status = getCertificateStatus(cert);
        return status === statusFilter;
      });
    }
    
    // Sort
    filtered.sort((a, b) => {
      let aVal, bVal;
      
      // Special handling for status column (computed field)
      if (sortConfig.column === 'status') {
        // Define status priority order: Critical (highest urgency) -> Expired -> Due Soon -> Valid -> Unknown
        const statusPriority = {
          'Critical': 1,
          'Expired': 2,
          'Due Soon': 3,
          'Valid': 4,
          'Unknown': 5
        };
        aVal = statusPriority[getCertificateStatus(a)] || 5;
        bVal = statusPriority[getCertificateStatus(b)] || 5;
      } else {
        aVal = a[sortConfig.column];
        bVal = b[sortConfig.column];
      }
      
      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;
      
      const comparison = aVal > bVal ? 1 : -1;
      return sortConfig.direction === 'asc' ? comparison : -comparison;
    });

    return filtered;
  };

  return (
    <MainLayout
      sidebar={
        <Sidebar 
          selectedCategory="sms"
          onCategoryChange={() => {}}
        />
      }
    >
      {/* Page Title */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800">
          {language === 'vi' ? 'Hệ thống quản lý an toàn của công ty' : 'Company Safety Management System'}
        </h1>
      </div>

      {/* Company Info Panel */}
      {companyData && (
        <CompanyInfoPanel companyData={companyData} />
      )}

      {/* SubMenuBar */}
      <SubMenuBar
        selectedCategory="sms"
        selectedSubMenu={selectedSubMenu}
        onSubMenuChange={setSelectedSubMenu}
      />

      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-md p-6 mt-6">
        {/* Company Cert Content */}
        {selectedSubMenu === 'company_cert' && (
          <>
            {/* Header Row: Title (left) + Action Buttons (right) */}
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800">
                {language === 'vi' ? 'Danh sách chứng chỉ công ty' : 'Company Certificate List'}
              </h2>
              
              <div className="flex items-center gap-2">
                {/* Update Next Audit Button - Ẩn cho Viewer */}
                {user?.role !== 'viewer' && (
                  <button
                    onClick={handleUpdateNextAudits}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2 text-sm font-medium shadow-sm"
                    disabled={certsLoading}
                  >
                    <span>🔄</span>
                    {language === 'vi' ? 'Cập nhật Next Audit' : 'Update Next Audit'}
                  </button>
                )}
                
                {/* Upcoming Audit Button - Ẩn cho Viewer */}
                {user?.role !== 'viewer' && (
                  <button
                    onClick={handleUpcomingAudit}
                    disabled={isLoadingUpcomingAudit}
                    className={`px-4 py-2 text-white rounded-lg flex items-center gap-2 text-sm font-medium shadow-sm ${
                      isLoadingUpcomingAudit 
                        ? 'bg-orange-400 cursor-wait' 
                        : 'bg-orange-600 hover:bg-orange-700 cursor-pointer'
                    }`}
                  >
                    {isLoadingUpcomingAudit ? (
                      <>
                        <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        {language === 'vi' ? 'Đang kiểm tra...' : 'Checking...'}
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {language === 'vi' ? 'Upcoming Audit' : 'Upcoming Audit'}
                      </>
                    )}
                  </button>
                )}
                
                {/* Add Certificate Button */}
                <button
                  onClick={() => setShowAddModal(true)}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 text-sm font-medium shadow-sm"
                >
                  <span>➕</span>
                  {language === 'vi' ? 'Thêm chứng chỉ' : 'Add Certificate'}
                </button>

                {/* Refresh Button */}
                <button
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center gap-2 text-sm font-medium shadow-sm"
                >
                  <span className={isRefreshing ? 'animate-spin' : ''}>🔄</span>
                  {language === 'vi' ? 'Làm mới' : 'Refresh'}
                </button>
              </div>
            </div>

            {/* Filter Section - Separate Row */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-200">
              <div className="flex items-center gap-4">
                {/* Status Filter */}
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700">
                    {language === 'vi' ? 'Trạng thái:' : 'Status:'}
                  </label>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                  >
                    <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
                    <option value="Valid">{language === 'vi' ? 'Còn hạn' : 'Valid'}</option>
                    <option value="Due Soon">{language === 'vi' ? 'Sắp hết hạn' : 'Due Soon'}</option>
                    <option value="Critical">{language === 'vi' ? 'Rất gấp' : 'Critical'}</option>
                    <option value="Expired">{language === 'vi' ? 'Hết hạn' : 'Expired'}</option>
                  </select>
                </div>

                {/* Search */}
                <div className="flex items-center gap-2 flex-1">
                  <label className="text-sm font-medium text-gray-700">
                    {language === 'vi' ? 'Tìm kiếm:' : 'Search:'}
                  </label>
                  <div className="relative flex-1 max-w-md">
                    <input
                      type="text"
                      placeholder={language === 'vi' ? 'Tìm theo tên, số chứng chỉ...' : 'Search by name, cert no...'}
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                </div>

                {/* Info: Showing X / Y certificates */}
                <div className="text-sm text-gray-600 whitespace-nowrap">
                  {language === 'vi' 
                    ? `Hiển thị ${getFilteredAndSortedCerts().length} / ${companyCerts.length} chứng chỉ`
                    : `Showing ${getFilteredAndSortedCerts().length} / ${companyCerts.length} certificates`
                  }
                </div>
              </div>
            </div>

            {/* Table */}
            {certsLoading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                <p className="mt-4 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
              </div>
            ) : (
              <div onContextMenu={(e) => e.preventDefault()}>
                <CompanyCertTable
                  certificates={getFilteredAndSortedCerts()}
                  selectedCertificates={selectedCerts}
                  onSelectCertificate={handleSelectCert}
                  onSelectAllCertificates={handleSelectAllCerts}
                  onSort={handleSort}
                  sortConfig={sortConfig}
                  onDoubleClick={handleDoubleClick}
                  onRightClick={handleRightClick}
                  onNotesClick={(cert) => {
                    setNotesCert(cert);
                    setShowNotesModal(true);
                  }}
                />
              </div>
            )}
          </>
        )}

        {/* Other sub-menus (placeholder) */}
        {selectedSubMenu === 'sms_procedures' && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📋</div>
            <p className="text-xl font-medium text-gray-600">
              {language === 'vi' ? 'SMS Procedures - Đang phát triển' : 'SMS Procedures - Coming Soon'}
            </p>
          </div>
        )}

        {selectedSubMenu === 'record_template' && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📝</div>
            <p className="text-xl font-medium text-gray-600">
              {language === 'vi' ? 'Record Template - Đang phát triển' : 'Record Template - Coming Soon'}
            </p>
          </div>
        )}

        {selectedSubMenu === 'ship_record' && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🚢</div>
            <p className="text-xl font-medium text-gray-600">
              {language === 'vi' ? 'Ship Record - Đang phát triển' : 'Ship Record - Coming Soon'}
            </p>
          </div>
        )}
      </div>

      {/* Context Menu */}
      {contextMenu && (
        <div
          className="fixed bg-white shadow-lg rounded-lg py-2 z-[9999] border border-gray-200 min-w-[220px]"
          style={{ top: contextMenu.y, left: contextMenu.x }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* View */}
          <button
            onClick={() => {
              if (selectedCerts.size > 1) {
                handleBulkViewFiles();
              } else {
                handleViewFile(contextMenu.certificate);
              }
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
          >
            <span>👁️</span>
            {selectedCerts.size > 1 
              ? (language === 'vi' ? `Xem file (${selectedCerts.size} chứng chỉ)` : `View Files (${selectedCerts.size} certificates)`)
              : (language === 'vi' ? 'Xem file' : 'View File')
            }
          </button>

          {/* Download - works for single and multiple */}
          <button
            onClick={() => {
              if (selectedCerts.size > 1) {
                handleBulkDownload();
              } else {
                const fileId = contextMenu.certificate?.file_id || contextMenu.certificate?.google_drive_file_id;
                if (fileId) {
                  window.open(`https://drive.google.com/uc?export=download&id=${fileId}`, '_blank');
                }
              }
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
          >
            <span>⬇️</span>
            {selectedCerts.size > 1 
              ? (language === 'vi' ? `Tải xuống (${selectedCerts.size} file)` : `Download (${selectedCerts.size} files)`)
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
            {selectedCerts.size > 1 
              ? (language === 'vi' ? `Sao chép link (${selectedCerts.size} file)` : `Copy Links (${selectedCerts.size} files)`)
              : (language === 'vi' ? 'Sao chép link' : 'Copy Link')
            }
          </button>

          <div className="border-t border-gray-200 my-1"></div>

          {/* Auto Rename File - works for single and multiple */}
          <button
            onClick={() => {
              if (selectedCerts.size > 1) {
                handleBulkAutoRenameFiles();
              } else if (contextMenu.certificate) {
                handleAutoRenameFile(contextMenu.certificate);
              }
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left text-sm hover:bg-purple-50 hover:text-purple-600 flex items-center gap-2"
          >
            <span>⚡</span>
            {selectedCerts.size > 1 
              ? (language === 'vi' ? `Đổi tên tự động (${selectedCerts.size} file)` : `Auto Rename (${selectedCerts.size} files)`)
              : (language === 'vi' ? 'Đổi tên file tự động' : 'Auto Rename File')
            }
          </button>

          {selectedCerts.size === 1 && (
            <>
              <div className="border-t border-gray-200 my-1"></div>

              {/* Edit - single only */}
              <button
                onClick={() => {
                  setEditingCert(contextMenu.certificate);
                  setShowEditModal(true);
                  setContextMenu(null);
                }}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
              >
                <span>✏️</span>
                {language === 'vi' ? 'Chỉnh sửa' : 'Edit'}
              </button>

              {/* Notes - single only */}
              <button
                onClick={() => {
                  setNotesCert(contextMenu.certificate);
                  setShowNotesModal(true);
                  setContextMenu(null);
                }}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
              >
                <span>📝</span>
                {language === 'vi' ? 'Ghi chú' : 'Notes'}
              </button>
            </>
          )}

          <div className="border-t border-gray-200 my-1"></div>

          {/* Delete - works for single and multiple */}
          <button
            onClick={() => {
              setDeletingCert(contextMenu.certificate);
              setShowDeleteModal(true);
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2 text-red-600"
          >
            <span>🗑️</span>
            {selectedCerts.size > 1 
              ? (language === 'vi' ? `Xóa (${selectedCerts.size})` : `Delete (${selectedCerts.size})`)
              : (language === 'vi' ? 'Xóa' : 'Delete')
            }
          </button>
        </div>
      )}

      {/* Modals */}
      <AddCompanyCertModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={loadCompanyCerts}
        language={language}
      />

      <EditCompanyCertModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setEditingCert(null);
        }}
        onSuccess={loadCompanyCerts}
        certificate={editingCert}
        language={language}
      />

      <DeleteCompanyCertModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setDeletingCert(null);
        }}
        onSuccess={loadCompanyCerts}
        certificate={deletingCert}
        language={language}
      />

      <CompanyCertNotesModal
        isOpen={showNotesModal}
        onClose={() => {
          setShowNotesModal(false);
          setNotesCert(null);
        }}
        onSuccess={loadCompanyCerts}
        certificate={notesCert}
        language={language}
      />

      {/* Upcoming Audit Modal */}
      <AuditUpcomingSurveyModal
        isOpen={upcomingAuditModal.show}
        onClose={() => setUpcomingAuditModal({
          show: false,
          surveys: [],
          totalCount: 0,
          company: '',
          companyName: '',
          checkDate: ''
        })}
        surveys={upcomingAuditModal.surveys}
        totalCount={upcomingAuditModal.totalCount}
        companyName={upcomingAuditModal.companyName}
        checkDate={upcomingAuditModal.checkDate}
        language={language}
      />

      {/* Floating Progress for Auto Rename */}
      <FloatingProgress
        isVisible={floatingRenameProgress.isVisible}
        title={language === 'vi' ? 'Đổi tên tự động' : 'Auto Rename Files'}
        completed={floatingRenameProgress.completed}
        total={floatingRenameProgress.total}
        currentFile={floatingRenameProgress.currentFile}
        errors={floatingRenameProgress.errors}
        status={floatingRenameProgress.status}
        onClose={handleCloseFloatingProgress}
        language={language}
      />
    </MainLayout>
  );
};

export default SafetyManagementSystem;
