/**
 * Class Audit Report List Component
 * Full-featured audit report management with table, filters, CRUD operations
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { auditReportService } from '../../services';
import { toast } from 'sonner';
import { AddAuditReportModal } from './AddAuditReportModal';
import { EditAuditReportModal } from './EditAuditReportModal';
import { AuditReportNotesModal } from './AuditReportNotesModal';
import { formatDateDisplay } from '../../utils/dateHelpers';

export const AuditReportList = ({ 
  selectedShip, 
  reports,
  loading,
  selectedReports,
  onSelectReport,
  onSelectAll,
  filters,
  onFiltersChange,
  sort,
  onSortChange,
  onRefresh,
  isRefreshing,
  onStartBatchProcessing,
  onAddReport,
  onEditReport,
  onNotesClick,
  language 
}) => {

  // Context Menu
  const [contextMenu, setContextMenu] = useState({
    show: false,
    x: 0,
    y: 0,
    report: null
  });

  // Note Tooltip
  const [noteTooltip, setNoteTooltip] = useState({
    show: false,
    x: 0,
    y: 0,
    content: ''
  });

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClick = () => {
      if (contextMenu.show) {
        setContextMenu({ show: false, x: 0, y: 0, report: null });
      }
    };
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, [contextMenu.show]);

  // Handle refresh (call parent handler)
  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    }
  };

  // Handle sort
  const handleSort = (column) => {
    if (onSortChange) {
      const direction = sort.column === column && sort.direction === 'asc' ? 'desc' : 'asc';
      onSortChange({ column, direction });
    }
  };

  // Get sort icon
  const getSortIcon = (column) => {
    if (sort.column !== column) return null;
    return (
      <span className="ml-1 text-blue-600 text-sm font-bold">
        {sort.direction === 'asc' ? '▲' : '▼'}
      </span>
    );
  };

  // Get abbreviation from full name
  const getAbbreviation = (fullName) => {
    if (!fullName) return '';
    const words = fullName.trim().split(/\s+/);
    if (words.length === 1) return words[0].substring(0, 3).toUpperCase();
    return words.slice(0, 4).map(word => word[0]).join('').toUpperCase();
  };

  // Original refresh handler kept for compatibility
  const handleRefreshOld = async () => {
    if (!selectedShip) return;
    
    try {
      setIsRefreshing(true);
      if (onRefresh) onRefresh();
      toast.success(language === 'vi' ? '✅ Đã cập nhật danh sách!' : '✅ List refreshed!');
    } catch (error) {
      console.error('Failed to refresh:', error);
      toast.error(language === 'vi' ? '❌ Không thể làm mới danh sách' : '❌ Failed to refresh');
    } finally {
      setIsRefreshing(false);
    }
  };

  // Filter and sort reports
  const getFilteredReports = () => {
    let filtered = [...reports];

    // Apply status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(report => 
        report.status && report.status.toLowerCase() === filters.status.toLowerCase()
      );
    }

    // Apply search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(report =>
        (report.audit_report_name && report.audit_report_name.toLowerCase().includes(searchLower)) ||
        (report.audit_report_no && report.audit_report_no.toLowerCase().includes(searchLower)) ||
        (report.audited_by && report.audited_by.toLowerCase().includes(searchLower)) ||
        (report.note && report.note.toLowerCase().includes(searchLower))
      );
    }

    // Apply sorting
    if (sort.column) {
      filtered.sort((a, b) => {
        let aValue = a[sort.column] || '';
        let bValue = b[sort.column] || '';

        // Handle date sorting
        if (sort.column === 'audit_date') {
          aValue = a.audit_date ? new Date(a.audit_date).getTime() : 0;
          bValue = b.audit_date ? new Date(b.audit_date).getTime() : 0;
        } else {
          // String comparison
          aValue = String(aValue).toLowerCase();
          bValue = String(bValue).toLowerCase();
        }

        if (aValue < bValue) return sort.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return sort.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  };

  // Checkbox selection handlers
  const handleSelectAll = (checked) => {
    if (onSelectAll) {
      onSelectAll(checked);
    }
  };

  const handleSelectReport = (reportId) => {
    if (onSelectReport) {
      onSelectReport(reportId);
    }
  };

  const isAllSelected = () => {
    const filtered = getFilteredReports();
    return filtered.length > 0 && filtered.every(r => selectedReports.has(r.id));
  };

  const isIndeterminate = () => {
    const filtered = getFilteredReports();
    const selected = filtered.filter(r => selectedReports.has(r.id));
    return selected.length > 0 && selected.length < filtered.length;
  };

  // Context menu handlers
  const handleContextMenu = (e, report) => {
    e.preventDefault();
    setContextMenu({
      show: true,
      x: e.clientX,
      y: e.clientY,
      report
    });
  };

  const handleViewFile = async (report) => {
    if (!report.audit_report_file_id) {
      toast.warning(language === 'vi' ? 'Không có file' : 'No file available');
      setContextMenu({ show: false, x: 0, y: 0, report: null });
      return;
    }

    try {
      // Use backend endpoint to get proper view URL (handles company/system gdrive config)
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/gdrive/file/${report.audit_report_file_id}/view`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.view_url) {
          window.open(data.view_url, '_blank');
        } else {
          // Fallback to direct Google Drive link
          window.open(`https://drive.google.com/file/d/${report.audit_report_file_id}/view`, '_blank');
        }
      } else {
        // Fallback to direct Google Drive link
        window.open(`https://drive.google.com/file/d/${report.audit_report_file_id}/view`, '_blank');
      }
    } catch (error) {
      console.error('Error getting view URL:', error);
      // Fallback to direct Google Drive link
      window.open(`https://drive.google.com/file/d/${report.audit_report_file_id}/view`, '_blank');
    }

    setContextMenu({ show: false, x: 0, y: 0, report: null });
  };

  const handleCopyLink = async (report) => {
    if (!report.audit_report_file_id) {
      toast.warning(language === 'vi' ? 'Không có file' : 'No file available');
      setContextMenu({ show: false, x: 0, y: 0, report: null });
      return;
    }

    try {
      // Use backend endpoint to get proper view URL
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/gdrive/file/${report.audit_report_file_id}/view`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      let linkToCopy;
      if (response.ok) {
        const data = await response.json();
        linkToCopy = data.view_url || `https://drive.google.com/file/d/${report.audit_report_file_id}/view`;
      } else {
        // Fallback to direct Google Drive link
        linkToCopy = `https://drive.google.com/file/d/${report.audit_report_file_id}/view`;
      }

      await navigator.clipboard.writeText(linkToCopy);
      toast.success(language === 'vi' ? 'Đã copy link' : 'Link copied');
    } catch (error) {
      console.error('Error copying link:', error);
      // Fallback: copy direct Google Drive link
      const fallbackLink = `https://drive.google.com/file/d/${report.audit_report_file_id}/view`;
      await navigator.clipboard.writeText(fallbackLink);
      toast.success(language === 'vi' ? 'Đã copy link' : 'Link copied');
    }

    setContextMenu({ show: false, x: 0, y: 0, report: null });
  };

  const handleEditReport = (report) => {
    if (onEditReport) {
      onEditReport(report);
    }
    setContextMenu({ show: false, x: 0, y: 0, report: null });
  };

  const handleDeleteReport = async (report) => {
    if (!window.confirm(
      language === 'vi' 
        ? `Bạn có chắc chắn muốn xóa báo cáo audit "${report.audit_report_name}"?`
        : `Are you sure you want to delete report "${report.audit_report_name}"?`
    )) {
      return;
    }

    try {
      const response = await auditReportService.bulkDelete([report.id]);
      const result = response.data;
      
      // First notification: Record deleted
      if (result.deleted_count > 0) {
        toast.success(
          language === 'vi' 
            ? '✅ Đã xóa báo cáo audit khỏi hệ thống' 
            : '✅ Report deleted from database'
        );
      }
      
      // Second notification: Files deleted from Google Drive
      if (result.files_deleted > 0) {
        setTimeout(() => {
          toast.success(
            language === 'vi' 
              ? `🗑️ Đã xóa ${result.files_deleted} file từ Google Drive` 
              : `🗑️ Deleted ${result.files_deleted} file(s) from Google Drive`
          );
        }, 1000);
      }
      
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Failed to delete report:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to delete report';
      toast.error(
        language === 'vi' 
          ? `❌ Không thể xóa báo cáo audit: ${errorMsg}` 
          : `❌ ${errorMsg}`
      );
    }
    setContextMenu({ show: false, x: 0, y: 0, report: null });
  };

  const handleBulkDelete = async () => {
    if (selectedReports.size === 0) return;

    if (!window.confirm(
      language === 'vi' 
        ? `Bạn có chắc chắn muốn xóa ${selectedReports.size} báo cáo audit đã chọn?`
        : `Are you sure you want to delete ${selectedReports.size} selected report(s)?`
    )) {
      return;
    }

    try {
      const reportIds = Array.from(selectedReports);
      const response = await auditReportService.bulkDelete(reportIds);
      const result = response.data;
      
      // First notification: Records deleted
      if (result.deleted_count > 0) {
        toast.success(
          language === 'vi' 
            ? `✅ Đã xóa ${result.deleted_count} báo cáo audit khỏi hệ thống` 
            : `✅ Deleted ${result.deleted_count} report(s) from database`
        );
      }
      
      // Second notification: Files deleted from Google Drive
      if (result.files_deleted > 0) {
        setTimeout(() => {
          toast.success(
            language === 'vi' 
              ? `🗑️ Đã xóa ${result.files_deleted} file từ Google Drive` 
              : `🗑️ Deleted ${result.files_deleted} file(s) from Google Drive`
          );
        }, 1000);
      }
      
      // Show errors if any
      if (result.errors && result.errors.length > 0) {
        setTimeout(() => {
          toast.warning(
            language === 'vi' 
              ? `⚠️ Có ${result.errors.length} lỗi khi xóa` 
              : `⚠️ ${result.errors.length} error(s) occurred`
          );
        }, 2000);
      }
      
      // Clear selection after successful deletion
      if (onSelectAll) {
        onSelectAll(false);
      }
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Failed to bulk delete:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to delete reports';
      toast.error(
        language === 'vi' 
          ? `❌ Không thể xóa báo cáo audit: ${errorMsg}` 
          : `❌ ${errorMsg}`
      );
    }
    setContextMenu({ show: false, x: 0, y: 0, report: null });
  };

  // Bulk view files - open multiple files in new tabs
  const handleBulkView = async () => {
    const selectedReportsList = reports.filter(r => selectedReports.has(r.id));
    const reportsWithFiles = selectedReportsList.filter(r => r.audit_report_file_id);

    if (reportsWithFiles.length === 0) {
      toast.warning(language === 'vi' ? 'Không có báo cáo audit nào có file đính kèm' : 'No reports have attached files');
      return;
    }

    try {
      // Open files (limit to 10 to avoid browser blocking)
      const limit = Math.min(reportsWithFiles.length, 10);
      for (let i = 0; i < limit; i++) {
        const report = reportsWithFiles[i];
        
        try {
          const response = await fetch(
            `${process.env.REACT_APP_BACKEND_URL}/api/gdrive/file/${report.audit_report_file_id}/view`,
            { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }}
          );

          let viewUrl;
          if (response.ok) {
            const data = await response.json();
            viewUrl = data.view_url || `https://drive.google.com/file/d/${report.audit_report_file_id}/view`;
          } else {
            viewUrl = `https://drive.google.com/file/d/${report.audit_report_file_id}/view`;
          }

          window.open(viewUrl, '_blank', 'noopener,noreferrer');
        } catch (error) {
          console.error(`Error opening file for report ${report.audit_report_no}:`, error);
        }
        
        // Small delay between opens
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      if (reportsWithFiles.length > 10) {
        toast.info(language === 'vi' ? `📄 Đã mở ${limit} file đầu tiên (giới hạn trình duyệt)` : `📄 Opened first ${limit} files (browser limit)`);
      } else {
        toast.success(language === 'vi' ? `📄 Đã mở ${limit} file` : `📄 Opened ${limit} files`);
      }
    } catch (error) {
      console.error('Bulk view error:', error);
      toast.error(language === 'vi' ? '❌ Lỗi khi mở file' : '❌ Error opening files');
    }

    setContextMenu({ show: false, x: 0, y: 0, report: null });
  };

  // Bulk download files
  const handleBulkDownload = async () => {
    const selectedReportsList = reports.filter(r => selectedReports.has(r.id));
    const reportsWithFiles = selectedReportsList.filter(r => r.audit_report_file_id);

    if (reportsWithFiles.length === 0) {
      toast.warning(language === 'vi' ? 'Không có báo cáo audit nào có file đính kèm' : 'No reports have attached files');
      return;
    }

    try {
      toast.info(language === 'vi' ? `📥 Đang tải xuống ${reportsWithFiles.length} file...` : `📥 Downloading ${reportsWithFiles.length} files...`);

      let downloadedCount = 0;

      for (const report of reportsWithFiles) {
        try {
          const response = await fetch(
            `${process.env.REACT_APP_BACKEND_URL}/api/gdrive/file/${report.audit_report_file_id}/download`,
            {
              headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            }
          );

          if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${report.audit_report_name || report.audit_report_no || 'survey_report'}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            
            downloadedCount++;
          }
          
          // Small delay between downloads
          await new Promise(resolve => setTimeout(resolve, 300));
        } catch (error) {
          console.error(`Download error for ${report.audit_report_no}:`, error);
        }
      }

      toast.success(language === 'vi' ? `✅ Đã tải xuống ${downloadedCount}/${reportsWithFiles.length} file` : `✅ Downloaded ${downloadedCount}/${reportsWithFiles.length} files`);
    } catch (error) {
      console.error('Bulk download error:', error);
      toast.error(language === 'vi' ? '❌ Lỗi khi tải xuống file' : '❌ Error downloading files');
    }

    setContextMenu({ show: false, x: 0, y: 0, report: null });
  };

  // Bulk copy links
  const handleBulkCopyLinks = async () => {
    const selectedReportsList = reports.filter(r => selectedReports.has(r.id));
    const reportsWithFiles = selectedReportsList.filter(r => r.audit_report_file_id);

    if (reportsWithFiles.length === 0) {
      toast.warning(language === 'vi' ? 'Không có báo cáo audit nào có file đính kèm' : 'No reports have attached files');
      return;
    }

    try {
      const links = [];

      for (const report of reportsWithFiles) {
        try {
          const response = await fetch(
            `${process.env.REACT_APP_BACKEND_URL}/api/gdrive/file/${report.audit_report_file_id}/view`,
            { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }}
          );

          let viewUrl;
          if (response.ok) {
            const data = await response.json();
            viewUrl = data.view_url || `https://drive.google.com/file/d/${report.audit_report_file_id}/view`;
          } else {
            viewUrl = `https://drive.google.com/file/d/${report.audit_report_file_id}/view`;
          }

          links.push(`${report.audit_report_name || report.audit_report_no}: ${viewUrl}`);
        } catch (error) {
          console.error(`Error getting link for ${report.audit_report_no}:`, error);
        }
      }

      if (links.length > 0) {
        await navigator.clipboard.writeText(links.join('\n'));
        toast.success(language === 'vi' ? `🔗 Đã sao chép ${links.length} link` : `🔗 Copied ${links.length} links`);
      } else {
        toast.error(language === 'vi' ? '❌ Không thể lấy link nào' : '❌ Could not get any links');
      }
    } catch (error) {
      console.error('Bulk copy links error:', error);
      toast.error(language === 'vi' ? '❌ Lỗi khi sao chép link' : '❌ Error copying links');
    }

    setContextMenu({ show: false, x: 0, y: 0, report: null });
  };

  // Note tooltip handlers
  const handleNoteMouseEnter = (e, note) => {
    if (!note) return;
    
    const rect = e.target.getBoundingClientRect();
    const tooltipWidth = 320; // max-w-xs is approximately 320px (20rem)
    const tooltipHeight = 150; // approximate height for padding
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const padding = 10; // minimum distance from edge
    
    // Calculate initial position (using viewport coordinates for position: fixed)
    let x = rect.left;
    let y = rect.bottom + 5;
    
    // Check if tooltip would overflow on the right
    if (x + tooltipWidth > viewportWidth - padding) {
      // Align to right edge of viewport with padding
      x = viewportWidth - tooltipWidth - padding;
    }
    
    // Ensure it doesn't go off left edge
    if (x < padding) {
      x = padding;
    }
    
    // Check if tooltip would overflow on the bottom
    if (y + tooltipHeight > viewportHeight - padding) {
      // Position above the element instead
      y = rect.top - tooltipHeight - 5;
      // If still overflows top, position within viewport
      if (y < padding) {
        y = padding;
      }
    }
    
    setNoteTooltip({
      show: true,
      x: x,
      y: y,
      content: note
    });
  };

  const handleNoteMouseLeave = () => {
    setNoteTooltip({ show: false, x: 0, y: 0, content: '' });
  };

  // Notes modal handlers
  const handleNoteClick = (report) => {
    if (onNotesClick) {
      onNotesClick(report, report.note || '');
    }
    // Hide tooltip when modal opens
    setNoteTooltip({ show: false, x: 0, y: 0, content: '' });
  };

  const handleSaveNotes = async () => {
    if (!notesReport) return;

    try {
      await auditReportService.update(notesReport.id, {
        ...notesReport,
        note: notesValue
      });

      toast.success(
        language === 'vi' 
          ? 'Đã lưu ghi chú' 
          : 'Notes saved successfully'
      );

      // Refresh list to show updated notes
      if (onRefresh) onRefresh();
      
      // Close modal
      setShowNotesModal(false);
      setNotesReport(null);
      setNotesValue('');
    } catch (error) {
      console.error('Failed to save notes:', error);
      toast.error(
        language === 'vi' 
          ? 'Không thể lưu ghi chú' 
          : 'Failed to save notes'
      );
    }
  };

  // Render empty state
  if (!selectedShip) {
    return (
      <div className="text-center py-12 text-gray-500">
        <div className="text-6xl mb-4">🚢</div>
        <p className="text-lg">
          {language === 'vi' ? 'Vui lòng chọn tàu để xem Class Audit Report' : 'Please select a ship to view Class Audit Report'}
        </p>
      </div>
    );
  }

  // Render loading state
  if (loading && reports.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p className="mt-4 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
      </div>
    );
  }

  const filteredReports = getFilteredReports();

  return (
    <div className="space-y-4">
      {/* Action Buttons Row */}
      <div className="flex items-center justify-between gap-4">
        {/* Report List Title with Ship Name - Left Side */}
        <h3 className="text-lg font-semibold text-gray-800">
          {language === 'vi' ? 'Danh sách Báo cáo Audit cho' : 'Class Audit Report List for'}{' '}
          {selectedShip ? `"${selectedShip.name}"` : (language === 'vi' ? '"Chọn tàu"' : '"Select a ship"')}
        </h3>

        {/* Add & Refresh Buttons - Right Side */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => onAddReport && onAddReport()}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-all"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {language === 'vi' ? 'Thêm Audit Report' : 'Add Audit Report'}
          </button>

          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              isRefreshing
                ? 'bg-gray-400 cursor-not-allowed text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer'
            }`}
          >
            <svg 
              className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {language === 'vi' ? 'Làm mới' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Filters Row */}
      <div className="mb-4 p-4 bg-gray-50 rounded-lg border">
        <div className="flex gap-4 items-center flex-wrap">
          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">
              {language === 'vi' ? 'Tình trạng:' : 'Status:'}
            </label>
            <select
              value={filters.status}
              onChange={(e) => onFiltersChange && onFiltersChange({ ...filters, status: e.target.value })}
              className="border border-gray-300 rounded px-3 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
              <option value="valid">Valid</option>
              <option value="expired">Expired</option>
              <option value="pending">Pending</option>
            </select>
          </div>

          {/* Search Filter */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">
              {language === 'vi' ? 'Tìm kiếm:' : 'Search:'}
            </label>
            <div className="relative">
              <input
                type="text"
                value={filters.search}
                onChange={(e) => onFiltersChange && onFiltersChange({ ...filters, search: e.target.value })}
                placeholder={language === 'vi' ? 'Tìm theo tên, số...' : 'Search by name, number...'}
                className="border border-gray-300 rounded px-3 py-1 pl-8 text-sm w-64 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <svg 
                className="w-4 h-4 text-gray-400 absolute left-2 top-1/2 transform -translate-y-1/2" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              {filters.search && (
                <button
                  onClick={() => onFiltersChange && onFiltersChange({ ...filters, search: '' })}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* Results Count - Right Aligned */}
          <div className="ml-auto text-sm text-gray-600">
            {language === 'vi' 
              ? `Hiển thị ${filteredReports.length} / ${reports.length} báo cáo audit`
              : `Showing ${filteredReports.length} / ${reports.length} report${reports.length !== 1 ? 's' : ''}`
            }
          </div>
        </div>
      </div>

      {/* Audit Reports Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-200 rounded-lg">
          <thead className="bg-gray-50">
            <tr>
              {/* Checkbox Column */}
              <th className="border border-gray-300 px-4 py-2 text-center">
                <div className="flex items-center justify-center">
                  <input
                    type="checkbox"
                    checked={isAllSelected()}
                    ref={(el) => {
                      if (el) el.indeterminate = isIndeterminate();
                    }}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                  />
                </div>
              </th>

              {/* Audit Report Name */}
              <th 
                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('audit_report_name')}
              >
                <div className="flex items-center justify-between">
                  <span>{language === 'vi' ? 'Tên Báo cáo Audit' : 'Audit Report Name'}</span>
                  {getSortIcon('audit_report_name')}
                </div>
              </th>

              {/* Audit Type */}
              <th 
                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('audit_type')}
              >
                <div className="flex items-center justify-between">
                  <span>{language === 'vi' ? 'Loại Audit' : 'Audit Type'}</span>
                  {getSortIcon('audit_type')}
                </div>
              </th>

              {/* Audit Report No */}
              <th 
                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('audit_report_no')}
              >
                <div className="flex items-center justify-between">
                  <span>{language === 'vi' ? 'Số Báo cáo Audit' : 'Audit Report No.'}</span>
                  {getSortIcon('audit_report_no')}
                </div>
              </th>

              {/* Audit Date */}
              <th 
                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('audit_date')}
              >
                <div className="flex items-center justify-between">
                  <span>{language === 'vi' ? 'Ngày Audit' : 'Audit Date'}</span>
                  {getSortIcon('audit_date')}
                </div>
              </th>

              {/* Audited By */}
              <th 
                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('audited_by')}
              >
                <div className="flex items-center justify-between">
                  <span>{language === 'vi' ? 'Audit bởi' : 'Audited By'}</span>
                  {getSortIcon('audited_by')}
                </div>
              </th>

              {/* Status */}
              <th 
                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('status')}
              >
                <div className="flex items-center justify-between">
                  <span>{language === 'vi' ? 'Tình trạng' : 'Status'}</span>
                  {getSortIcon('status')}
                </div>
              </th>

              {/* Note */}
              <th 
                className="border border-gray-300 px-4 py-2 text-center cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('note')}
              >
                <div className="flex items-center justify-center">
                  <span>{language === 'vi' ? 'Ghi chú' : 'Note'}</span>
                  {getSortIcon('note')}
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredReports.length === 0 ? (
              <tr>
                <td colSpan="8" className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                  {reports.length === 0 
                    ? (language === 'vi' ? 'Chưa có audit report nào' : 'No audit reports available')
                    : (language === 'vi' ? 'Không có audit report nào phù hợp với bộ lọc' : 'No audit reports match the current filters')
                  }
                </td>
              </tr>
            ) : (
              filteredReports.map((report, index) => (
                <tr 
                  key={report.id} 
                  className="hover:bg-gray-50 cursor-context-menu"
                  onContextMenu={(e) => handleContextMenu(e, report)}
                >
                  {/* Checkbox + Index */}
                  <td className="border border-gray-300 px-4 py-2 text-center">
                    <div className="flex items-center justify-center space-x-2">
                      <input
                        type="checkbox"
                        checked={selectedReports.has(report.id)}
                        onChange={() => handleSelectReport(report.id)}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                        onClick={(e) => e.stopPropagation()}
                      />
                      <span className="font-bold">{index + 1}</span>
                    </div>
                  </td>

                  {/* Audit Report Name with File Icons */}
                  <td className="border border-gray-300 px-4 py-2">
                    <div className="flex items-center gap-2">
                      <span>{report.audit_report_name}</span>
                      {report.audit_report_file_id && (
                        <span 
                          className="text-green-500 text-xs cursor-pointer hover:text-green-600" 
                          title={language === 'vi' 
                            ? `📄 File gốc\n📁 Đường dẫn: ${selectedShip?.name}/Class & Flag Cert/Class Audit Report/` 
                            : `📄 Original file\n📁 Path: ${selectedShip?.name}/Class & Flag Cert/Class Audit Report/`
                          }
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(`https://drive.google.com/file/d/${report.audit_report_file_id}/view`, '_blank');
                          }}
                        >
                          📄
                        </span>
                      )}
                      {report.audit_report_summary_file_id && (
                        <span 
                          className="text-blue-500 text-xs cursor-pointer hover:text-blue-600" 
                          title={language === 'vi' 
                            ? `📋 File tóm tắt (Summary)\n📁 Đường dẫn: ${selectedShip?.name}/Class & Flag Cert/Class Audit Report/` 
                            : `📋 Summary file\n📁 Path: ${selectedShip?.name}/Class & Flag Cert/Class Audit Report/`
                          }
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(`https://drive.google.com/file/d/${report.audit_report_summary_file_id}/view`, '_blank');
                          }}
                        >
                          📋
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Audit Type */}
                  <td className="border border-gray-300 px-4 py-2">{report.audit_type || '-'}</td>

                  {/* Audit Report No (Monospace Font) */}
                  <td className="border border-gray-300 px-4 py-2 font-mono">{report.audit_report_no || '-'}</td>

                  {/* Audit Date */}
                  <td className="border border-gray-300 px-4 py-2">
                    {report.audit_date ? formatDateDisplay(report.audit_date) : '-'}
                  </td>

                  {/* Audited By (Abbreviation with Tooltip) */}
                  <td 
                    className="border border-gray-300 px-4 py-2 text-sm font-semibold text-blue-700" 
                    title={report.audited_by || '-'}
                  >
                    {getAbbreviation(report.audited_by)}
                  </td>

                  {/* Status Badge */}
                  <td className="border border-gray-300 px-4 py-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      report.status?.toLowerCase() === 'valid' ? 'bg-green-100 text-green-800' :
                      report.status?.toLowerCase() === 'expired' ? 'bg-red-100 text-red-800' :
                      report.status?.toLowerCase() === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {report.status || 'Unknown'}
                    </span>
                  </td>

                  {/* Note (Asterisk with Tooltip) */}
                  {/* Note */}
                  <td 
                    className="border border-gray-300 px-4 py-2 text-center cursor-pointer hover:bg-gray-50 transition-colors"
                    onClick={() => handleNoteClick(report)}
                    title={language === 'vi' ? 'Click để xem/sửa ghi chú' : 'Click to view/edit notes'}
                  >
                    {report.note ? (
                      <span 
                        className="text-red-600 text-lg font-bold relative"
                        onMouseEnter={(e) => handleNoteMouseEnter(e, report.note)}
                        onMouseLeave={handleNoteMouseLeave}
                      >
                        *
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Context Menu */}
      {contextMenu.show && (
        <div 
          className="fixed bg-white border-2 border-gray-300 rounded-lg shadow-2xl z-[9999]"
          style={{
            position: 'fixed',
            top: `${contextMenu.y}px`,
            left: `${contextMenu.x}px`,
            minWidth: '180px',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2)'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="py-1">
            {/* Single item actions */}
            {selectedReports.size <= 1 && (
              <>
                <button
                  onClick={() => handleViewFile(contextMenu.report)}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                >
                  <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  {language === 'vi' ? 'Mở File' : 'View File'}
                </button>
                
                <button
                  onClick={() => handleCopyLink(contextMenu.report)}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                >
                  <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  {language === 'vi' ? 'Copy Link' : 'Copy Link'}
                </button>
                
                <div className="border-t border-gray-200 my-1"></div>
                
                <button
                  onClick={() => handleEditReport(contextMenu.report)}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                >
                  <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  {language === 'vi' ? 'Chỉnh sửa' : 'Edit'}
                </button>
                
                <button
                  onClick={() => handleDeleteReport(contextMenu.report)}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center"
                >
                  <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  {language === 'vi' ? 'Xóa' : 'Delete'}
                </button>
              </>
            )}
            
            {/* Bulk actions when multiple selected */}
            {selectedReports.size > 1 && (
              <>
                <button
                  onClick={handleBulkView}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                >
                  <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  {language === 'vi' 
                    ? `Xem file (${selectedReports.size} báo cáo audit)` 
                    : `View Files (${selectedReports.size} reports)`}
                </button>

                <button
                  onClick={handleBulkDownload}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                >
                  <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  {language === 'vi' 
                    ? `Tải xuống (${selectedReports.size} file)` 
                    : `Download (${selectedReports.size} files)`}
                </button>

                <button
                  onClick={handleBulkCopyLinks}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                >
                  <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                  </svg>
                  {language === 'vi' 
                    ? `Sao chép link (${selectedReports.size} file)` 
                    : `Copy Links (${selectedReports.size} files)`}
                </button>

                <div className="border-t border-gray-200 my-1"></div>

                <button
                  onClick={handleBulkDelete}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center"
                >
                  <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  {language === 'vi' 
                    ? `Xóa ${selectedReports.size} báo cáo audit đã chọn` 
                    : `Delete ${selectedReports.size} selected report(s)`
                  }
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Note Tooltip */}
      {noteTooltip.show && (
        <div 
          className="fixed bg-gray-800 text-white text-sm p-3 rounded-lg shadow-lg z-[100] max-w-xs"
          style={{
            position: 'fixed',
            top: `${noteTooltip.y}px`,
            left: `${noteTooltip.x}px`
          }}
        >
          {noteTooltip.content}
        </div>
      )}

    </div>
  );
};

