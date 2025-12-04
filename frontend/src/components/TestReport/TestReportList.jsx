/**
 * Test Report List Component
 * Full-featured test report management with table, filters, CRUD operations
 * Migrated from V1 with 100% feature parity (minus Valid Date From/To filters)
 */
import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { testReportService } from '../../services';
import { toast } from 'sonner';
import { formatDateDisplay } from '../../utils/dateHelpers';
import { calculateTooltipPosition, calculateContextMenuPosition } from '../../utils/positionHelpers';

export const TestReportList = ({ 
  selectedShip, 
  onAddReport, 
  onEditReport, 
  onViewNotes,
  refreshKey,
  onStartBatchProcessing
}) => {
  const { language } = useAuth();

  // ========== DATA STATE ==========
  const [testReports, setTestReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // ========== FILTERS STATE (MODIFIED - NO DATE FILTERS) ==========
  const [filters, setFilters] = useState({
    status: 'all',
    search: ''
  });

  // ========== SORTING STATE ==========
  const [sort, setSort] = useState({
    column: null,
    direction: 'asc'
  });

  // ========== SELECTION STATE ==========
  const [selectedReports, setSelectedReports] = useState(new Set());

  // ========== CONTEXT MENU STATE ==========
  const [contextMenu, setContextMenu] = useState({
    show: false,
    x: 0,
    y: 0,
    report: null
  });

  // ========== NOTE TOOLTIP STATE ==========
  const [noteTooltip, setNoteTooltip] = useState({
    show: false,
    x: 0,
    y: 0,
    width: 300,
    content: ''
  });

  // ========== REFS ==========
  const contextMenuRef = useRef(null);

  // ========== FETCH TEST REPORTS ==========
  useEffect(() => {
    if (selectedShip) {
      fetchTestReports();
    } else {
      setTestReports([]);
    }
  }, [selectedShip, refreshKey]);

  const fetchTestReports = async () => {
    if (!selectedShip) return;

    try {
      setLoading(true);
      const data = await testReportService.getAll(selectedShip.id);
      setTestReports(data);
    } catch (error) {
      console.error('Failed to fetch test reports:', error);
      toast.error(
        language === 'vi' 
          ? 'Không thể tải danh sách báo cáo test' 
          : 'Failed to load test reports'
      );
    } finally {
      setLoading(false);
    }
  };

  // ========== REFRESH HANDLER ==========
  const handleRefresh = async () => {
    if (!selectedShip || isRefreshing) return;

    try {
      setIsRefreshing(true);
      await fetchTestReports();
      toast.success(
        language === 'vi' 
          ? '✅ Đã cập nhật danh sách Test Reports!' 
          : '✅ Test Reports list updated!'
      );
    } catch (error) {
      console.error('Failed to refresh test reports:', error);
      toast.error(
        language === 'vi' 
          ? '❌ Không thể làm mới danh sách' 
          : '❌ Failed to refresh list'
      );
    } finally {
      setIsRefreshing(false);
    }
  };

  // ========== FILTER LOGIC (MODIFIED - NO DATE FILTERS) ==========
  const getFilteredReports = () => {
    let filtered = [...testReports];

    // Status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(report => {
        const status = report.status?.toLowerCase();
        return status === filters.status.toLowerCase();
      });
    }

    // Search filter (searches: name, form, number, issued_by)
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(report =>
        report.test_report_name?.toLowerCase().includes(searchLower) ||
        report.report_form?.toLowerCase().includes(searchLower) ||
        report.test_report_no?.toLowerCase().includes(searchLower) ||
        report.issued_by?.toLowerCase().includes(searchLower)
      );
    }

    return getSortedReports(filtered);
  };

  // ========== SORT LOGIC ==========
  const handleSort = (column) => {
    setSort(prev => ({
      column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const getSortedReports = (reports) => {
    if (!sort.column) return reports;

    return [...reports].sort((a, b) => {
      let aVal = a[sort.column];
      let bVal = b[sort.column];

      // Handle null/undefined
      if (!aVal) return 1;
      if (!bVal) return -1;

      // Date comparison
      if (sort.column.includes('date')) {
        aVal = new Date(aVal);
        bVal = new Date(bVal);
      }

      // String comparison (case-insensitive)
      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }

      if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1;
      return 0;
    });
  };

  // ========== SELECTION LOGIC ==========
  const handleReportSelect = (reportId) => {
    setSelectedReports(prev => {
      const newSet = new Set(prev);
      if (newSet.has(reportId)) {
        newSet.delete(reportId);
      } else {
        newSet.add(reportId);
      }
      return newSet;
    });
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      const allIds = getFilteredReports().map(r => r.id);
      setSelectedReports(new Set(allIds));
    } else {
      setSelectedReports(new Set());
    }
  };

  const isAllSelected = () => {
    const filtered = getFilteredReports();
    return filtered.length > 0 && filtered.every(r => selectedReports.has(r.id));
  };

  const isIndeterminate = () => {
    const filtered = getFilteredReports();
    const selectedCount = filtered.filter(r => selectedReports.has(r.id)).length;
    return selectedCount > 0 && selectedCount < filtered.length;
  };

  // ========== CONTEXT MENU HANDLERS ==========
  const handleContextMenu = (e, report) => {
    e.preventDefault();
    
    // Auto-select the right-clicked report if not already selected
    if (!selectedReports.has(report.id)) {
      setSelectedReports(new Set([report.id]));
    }
    
    const { x, y } = calculateContextMenuPosition(e, 200, 250);
    
    setContextMenu({
      show: true,
      x: x,
      y: y,
      report
    });
  };

  const handleEdit = (report) => {
    setContextMenu({ show: false, x: 0, y: 0, report: null });
    onEditReport(report);
  };

  const handleDelete = async (report) => {
    setContextMenu({ show: false, x: 0, y: 0, report: null });

    const confirmMsg = language === 'vi'
      ? 'Bạn có chắc muốn xóa báo cáo test này?'
      : 'Are you sure you want to delete this test report?';

    if (!window.confirm(confirmMsg)) return;

    try {
      await testReportService.delete(report.id);
      toast.success(
        language === 'vi' 
          ? 'Đã xóa báo cáo test' 
          : 'Test report deleted successfully'
      );
      fetchTestReports();
      setSelectedReports(new Set());
    } catch (error) {
      console.error('Failed to delete test report:', error);
      toast.error(
        language === 'vi' 
          ? 'Không thể xóa báo cáo test' 
          : 'Failed to delete test report'
      );
    }
  };

  // View File handler
  const handleViewFile = (report) => {
    setContextMenu({ show: false, x: 0, y: 0, report: null });
    
    if (report.test_report_file_id) {
      handleOpenFile(null, report.test_report_file_id);
    } else {
      toast.error(
        language === 'vi' 
          ? 'Không có file để xem' 
          : 'No file to view'
      );
    }
  };

  // Copy Link handler
  const handleCopyLink = (report) => {
    setContextMenu({ show: false, x: 0, y: 0, report: null });
    
    if (report.test_report_file_id) {
      const link = `https://drive.google.com/file/d/${report.test_report_file_id}/view`;
      navigator.clipboard.writeText(link);
      toast.success(
        language === 'vi' 
          ? 'Đã copy link vào clipboard' 
          : 'Link copied to clipboard'
      );
    } else {
      toast.error(
        language === 'vi' 
          ? 'Không có file link để copy' 
          : 'No file link to copy'
      );
    }
  };

  // Bulk view files - open multiple files in new tabs
  const handleBulkView = () => {
    setContextMenu({ show: false, x: 0, y: 0, report: null });
    
    const selectedReportsList = testReports.filter(r => selectedReports.has(r.id));
    const filesWithId = selectedReportsList.filter(r => r.test_report_file_id);
    
    if (filesWithId.length === 0) {
      toast.error(
        language === 'vi' 
          ? 'Không có file nào để xem' 
          : 'No files to view'
      );
      return;
    }

    filesWithId.forEach(report => {
      const url = `https://drive.google.com/file/d/${report.test_report_file_id}/view`;
      window.open(url, '_blank');
    });

    toast.success(
      language === 'vi' 
        ? `Đã mở ${filesWithId.length} file(s)` 
        : `Opened ${filesWithId.length} file(s)`
    );
  };

  // Bulk download files
  const handleBulkDownload = () => {
    setContextMenu({ show: false, x: 0, y: 0, report: null });
    
    const selectedReportsList = testReports.filter(r => selectedReports.has(r.id));
    const filesWithId = selectedReportsList.filter(r => r.test_report_file_id);
    
    if (filesWithId.length === 0) {
      toast.error(
        language === 'vi' 
          ? 'Không có file nào để tải' 
          : 'No files to download'
      );
      return;
    }

    filesWithId.forEach(report => {
      const url = `https://drive.google.com/uc?export=download&id=${report.test_report_file_id}`;
      const link = document.createElement('a');
      link.href = url;
      link.download = report.test_report_name || 'test_report.pdf';
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });

    toast.success(
      language === 'vi' 
        ? `Đang tải ${filesWithId.length} file(s)` 
        : `Downloading ${filesWithId.length} file(s)`
    );
  };

  // Bulk copy links
  const handleBulkCopyLinks = () => {
    setContextMenu({ show: false, x: 0, y: 0, report: null });
    
    const selectedReportsList = testReports.filter(r => selectedReports.has(r.id));
    const filesWithId = selectedReportsList.filter(r => r.test_report_file_id);
    
    if (filesWithId.length === 0) {
      toast.error(
        language === 'vi' 
          ? 'Không có file link nào để copy' 
          : 'No file links to copy'
      );
      return;
    }

    const links = filesWithId.map(report => {
      const link = `https://drive.google.com/file/d/${report.test_report_file_id}/view`;
      return `${report.test_report_name}: ${link}`;
    }).join('\n');

    navigator.clipboard.writeText(links);
    toast.success(
      language === 'vi' 
        ? `Đã copy ${filesWithId.length} link(s) vào clipboard` 
        : `Copied ${filesWithId.length} link(s) to clipboard`
    );
  };

  const handleBulkDelete = async () => {
    setContextMenu({ show: false, x: 0, y: 0, report: null });

    const reportCount = selectedReports.size;
    const confirmMsg = language === 'vi'
      ? `Bạn có chắc muốn xóa ${reportCount} báo cáo test đã chọn? Thao tác này cũng sẽ xóa các file liên quan trên Google Drive.`
      : `Are you sure you want to delete ${reportCount} test report(s)? This will also delete associated files from Google Drive.`;

    if (!window.confirm(confirmMsg)) return;

    const toastMsg = language === 'vi'
      ? `🗑️ Đang xóa ${reportCount} báo cáo test và file...`
      : `🗑️ Deleting ${reportCount} test report(s) and files...`;

    const toastId = toast.loading(toastMsg);

    try {
      const reportIds = Array.from(selectedReports);
      const result = await testReportService.bulkDelete(reportIds);

      toast.dismiss(toastId);

      if (result.errors && result.errors.length > 0) {
        toast.warning(
          language === 'vi'
            ? `⚠️ Đã xóa ${result.deleted_count} báo cáo test, ${result.errors.length} lỗi`
            : `⚠️ Deleted ${result.deleted_count} test report(s), ${result.errors.length} error(s)`
        );
      } else {
        toast.success(
          language === 'vi'
            ? `✅ Đã xóa ${result.deleted_count} báo cáo test thành công`
            : `✅ Successfully deleted ${result.deleted_count} test report(s)`
        );
      }

      fetchTestReports();
      setSelectedReports(new Set());
    } catch (error) {
      console.error('Failed to bulk delete:', error);
      toast.dismiss(toastId);
      toast.error(
        language === 'vi' 
          ? '❌ Lỗi khi xóa báo cáo test' 
          : '❌ Failed to delete test reports'
      );
    }
  };

  // ========== FILE HANDLERS ==========
  const handleOpenFile = async (e, fileId) => {
    e.stopPropagation();
    if (!fileId) return;
    
    // Open Google Drive file in new tab
    window.open(`https://drive.google.com/file/d/${fileId}/view`, '_blank');
  };

  // ========== NOTE TOOLTIP HANDLERS ==========
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

  const handleNoteClick = (e, report) => {
    e.stopPropagation();
    handleNoteMouseLeave();
    onViewNotes(report);
  };

  // ========== RENDER ==========
  const filteredReports = getFilteredReports();

  return (
    <div className="space-y-4">
      {/* ========== HEADER SECTION ========== */}
      <div className="flex justify-between items-center mb-4">
        {/* Left: Title */}
        <h3 className="text-lg font-semibold text-gray-800">
          {selectedShip 
            ? (language === 'vi' 
                ? `Danh sách Báo cáo Test cho ${selectedShip.name}` 
                : `Test Report List for ${selectedShip.name}`)
            : (language === 'vi' ? 'Vui lòng chọn tàu' : 'Please select a ship')
          }
        </h3>

        {/* Right: Action Buttons */}
        <div className="flex gap-3">
          {/* Add Button (Green) */}
          <button
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              selectedShip
                ? 'bg-green-600 hover:bg-green-700 text-white cursor-pointer'
                : 'bg-gray-400 cursor-not-allowed text-white'
            }`}
            onClick={() => selectedShip && onAddReport()}
            disabled={!selectedShip}
            title={
              selectedShip
                ? (language === 'vi' ? 'Thêm báo cáo test mới' : 'Add new test report')
                : (language === 'vi' ? 'Vui lòng chọn tàu trước' : 'Please select a ship first')
            }
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {language === 'vi' ? 'Thêm Báo cáo Test' : 'Add Test Report'}
          </button>

          {/* Refresh Button (Blue) */}
          <button
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              selectedShip && !isRefreshing
                ? 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer'
                : 'bg-gray-400 cursor-not-allowed text-white'
            }`}
            onClick={handleRefresh}
            disabled={!selectedShip || isRefreshing}
            title={
              selectedShip
                ? (language === 'vi' ? 'Làm mới danh sách' : 'Refresh list')
                : (language === 'vi' ? 'Vui lòng chọn tàu trước' : 'Please select a ship first')
            }
          >
            {isRefreshing ? (
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            {language === 'vi' ? 'Làm mới' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* ========== FILTERS SECTION ========== */}
      <div className="mb-4 p-4 bg-gray-50 rounded-lg border">
        <div className="flex gap-4 items-center flex-wrap">
          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">
              {language === 'vi' ? 'Tình trạng:' : 'Status:'}
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="border border-gray-300 rounded px-3 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
              <option value="valid">{language === 'vi' ? 'Còn hạn' : 'Valid'}</option>
              <option value="expired soon">{language === 'vi' ? 'Sắp hết hạn' : 'Expired soon'}</option>
              <option value="critical">{language === 'vi' ? 'Khẩn cấp' : 'Critical'}</option>
              <option value="expired">{language === 'vi' ? 'Hết hạn' : 'Expired'}</option>
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
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
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
                  onClick={() => setFilters(prev => ({ ...prev, search: '' }))}
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
              ? `Hiển thị ${filteredReports.length} / ${testReports.length} báo cáo`
              : `Showing ${filteredReports.length} / ${testReports.length} report${testReports.length !== 1 ? 's' : ''}`
            }
          </div>
        </div>
      </div>

      {/* ========== TABLE ========== */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            {/* Table Head */}
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {/* Column 1: Checkbox + No. */}
                <th className="border border-gray-300 px-4 py-2 text-left">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={isAllSelected()}
                      ref={el => {
                        if (el) {
                          el.indeterminate = isIndeterminate();
                        }
                      }}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="w-4 h-4 mr-2"
                    />
                    <span>{language === 'vi' ? 'Số TT' : 'No.'}</span>
                  </div>
                </th>

                {/* Column 2: Test Report Name (sortable) */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('test_report_name')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Tên Báo cáo Test' : 'Test Report Name'}</span>
                    {sort.column === 'test_report_name' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 3: Report Form (sortable) */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('report_form')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Mẫu Báo cáo' : 'Report Form'}</span>
                    {sort.column === 'report_form' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 4: Test Report No. (sortable) */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('test_report_no')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Số Báo cáo' : 'Test Report No.'}</span>
                    {sort.column === 'test_report_no' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 5: Issued By (sortable) */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('issued_by')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Cấp bởi' : 'Issued By'}</span>
                    {sort.column === 'issued_by' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 6: Issued Date (sortable) */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('issued_date')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Ngày cấp' : 'Issued Date'}</span>
                    {sort.column === 'issued_date' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 7: Valid Date (sortable) with info icon */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('valid_date')}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1">
                      <span>{language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}</span>
                      <span
                        className="text-blue-500 cursor-help text-sm"
                        title={
                          language === 'vi'
                            ? 'Thông tin hạn bảo dưỡng được tính bởi AI có thể gặp sai sót. Vui lòng kiểm tra và sửa lại nếu cần'
                            : 'Valid Date calculated by AI may contain errors. Please verify and correct if needed'
                        }
                        onClick={(e) => e.stopPropagation()}
                      >
                        ⓘ
                      </span>
                    </div>
                    {sort.column === 'valid_date' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 8: Status (sortable) */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('status')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Trạng thái' : 'Status'}</span>
                    {sort.column === 'status' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Column 9: Note (not sortable) */}
                <th className="border border-gray-300 px-4 py-2 text-center">
                  {language === 'vi' ? 'Ghi chú' : 'Note'}
                </th>
              </tr>
            </thead>

            {/* Table Body */}
            <tbody>
              {filteredReports.length === 0 ? (
                // Empty State
                <tr>
                  <td colSpan="9" className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                    {testReports.length === 0
                      ? (language === 'vi' ? 'Chưa có báo cáo test nào' : 'No test reports available')
                      : (language === 'vi' ? 'Không có báo cáo test nào phù hợp với bộ lọc' : 'No test reports match the current filters')
                    }
                  </td>
                </tr>
              ) : (
                // Render Rows
                filteredReports.map((report, index) => (
                  <tr
                    key={report.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onContextMenu={(e) => handleContextMenu(e, report)}
                  >
                    {/* Cell 1: Checkbox + No. */}
                    <td className="border border-gray-300 px-4 py-2">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedReports.has(report.id)}
                          onChange={() => handleReportSelect(report.id)}
                          className="w-4 h-4 mr-3"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <span>{index + 1}</span>
                      </div>
                    </td>

                    {/* Cell 2: Test Report Name + File Icons */}
                    <td className="border border-gray-300 px-4 py-2">
                      <div className="flex items-center gap-2">
                        <span>{report.test_report_name}</span>

                        {/* Original File Icon (📄 green) */}
                        {report.test_report_file_id && (
                          <span
                            className="text-green-500 text-xs cursor-pointer hover:text-green-600"
                            title={`${language === 'vi' ? 'File gốc' : 'Original file'}\n📁 ${selectedShip?.name || 'Unknown'}/Class & Flag Cert/Test Report`}
                            onClick={(e) => handleOpenFile(e, report.test_report_file_id)}
                          >
                            📄
                          </span>
                        )}

                        {/* Summary File Icon (📋 blue) */}
                        {report.test_report_summary_file_id && (
                          <span
                            className="text-blue-500 text-xs cursor-pointer hover:text-blue-600"
                            title={`${language === 'vi' ? 'File tóm tắt' : 'Summary file'}\n📁 ${selectedShip?.name || 'Unknown'}/Class & Flag Cert/Test Report`}
                            onClick={(e) => handleOpenFile(e, report.test_report_summary_file_id)}
                          >
                            📋
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Cell 3: Report Form */}
                    <td className="border border-gray-300 px-4 py-2">
                      {report.report_form || '-'}
                    </td>

                    {/* Cell 4: Test Report No. (monospace font) */}
                    <td className="border border-gray-300 px-4 py-2 font-mono">
                      {report.test_report_no}
                    </td>

                    {/* Cell 5: Issued By */}
                    <td className="border border-gray-300 px-4 py-2">
                      {report.issued_by || '-'}
                    </td>

                    {/* Cell 6: Issued Date */}
                    <td className="border border-gray-300 px-4 py-2">
                      {report.issued_date ? formatDateDisplay(report.issued_date) : '-'}
                    </td>

                    {/* Cell 7: Valid Date (with tooltip) */}
                    <td
                      className="border border-gray-300 px-4 py-2 cursor-help"
                      title={
                        language === 'vi'
                          ? 'Thông tin hạn bảo dưỡng được tính bởi AI có thể gặp sai sót. Vui lòng kiểm tra và sửa lại nếu cần'
                          : 'Valid Date calculated by AI may contain errors. Please verify and correct if needed'
                      }
                    >
                      {report.valid_date ? formatDateDisplay(report.valid_date) : '-'}
                    </td>

                    {/* Cell 8: Status Badge */}
                    <td className="border border-gray-300 px-4 py-2">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          report.status === 'Valid' ? 'bg-green-100 text-green-800' :
                          report.status === 'Expired soon' ? 'bg-yellow-100 text-yellow-800' :
                          report.status === 'Critical' ? 'bg-orange-100 text-orange-800' :
                          report.status === 'Expired' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {report.status}
                      </span>
                    </td>

                    {/* Cell 9: Note (red asterisk *) */}
                    <td className="border border-gray-300 px-4 py-2 text-center">
                      {report.note ? (
                        <span
                          className="text-red-600 cursor-help text-lg font-bold"
                          onMouseEnter={(e) => handleNoteMouseEnter(e, report.note)}
                          onMouseLeave={handleNoteMouseLeave}
                          onClick={(e) => handleNoteClick(e, report)}
                        >
                          *
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ========== CONTEXT MENU ========== */}
      {contextMenu.show && (
        <>
          {/* Overlay to close menu */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setContextMenu({ show: false, x: 0, y: 0, report: null })}
          />

          {/* Menu */}
          <div
            ref={contextMenuRef}
            className="fixed bg-white shadow-xl rounded-lg border border-gray-200 py-2 z-50"
            style={{
              left: `${contextMenu.x}px`,
              top: `${contextMenu.y}px`,
              minWidth: '180px'
            }}
          >
            {/* Single item actions */}
            {selectedReports.size <= 1 ? (
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
                  onClick={() => handleEdit(contextMenu.report)}
                  className="w-full px-4 py-2 text-left hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  {language === 'vi' ? 'Chỉnh sửa' : 'Edit'}
                </button>

                <button
                  onClick={() => handleDelete(contextMenu.report)}
                  className="w-full px-4 py-2 text-left hover:bg-red-50 text-gray-700 hover:text-red-600 transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  {language === 'vi' ? 'Xóa' : 'Delete'}
                </button>
              </>
            ) : (
              // Bulk actions when multiple selected
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
                    ? `Xem file (${selectedReports.size} báo cáo)` 
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
                  className="w-full px-4 py-2 text-left hover:bg-red-50 text-gray-700 hover:text-red-600 transition-all flex items-center gap-2 font-medium"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  {language === 'vi' 
                    ? `Xóa ${selectedReports.size} báo cáo đã chọn` 
                    : `Delete ${selectedReports.size} selected report(s)`
                  }
                </button>
              </>
            )}
          </div>
        </>
      )}

      {/* ========== NOTE TOOLTIP ========== */}
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
