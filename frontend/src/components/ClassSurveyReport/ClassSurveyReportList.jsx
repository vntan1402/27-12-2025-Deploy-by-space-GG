/**
 * Class Survey Report List Component
 * Full-featured survey report management with table, filters, CRUD operations
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { surveyReportService } from '../../services';
import { toast } from 'sonner';
import { AddSurveyReportModal } from './AddSurveyReportModal';
import { EditSurveyReportModal } from './EditSurveyReportModal';
import { formatDateDisplay } from '../../utils/dateHelpers';

export const ClassSurveyReportList = ({ selectedShip }) => {
  const { language } = useAuth();

  // State
  const [surveyReports, setSurveyReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Filters
  const [filters, setFilters] = useState({
    status: 'all',
    search: ''
  });

  // Sorting
  const [sort, setSort] = useState({
    column: null,
    direction: 'asc'
  });

  // Selection
  const [selectedReports, setSelectedReports] = useState(new Set());

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingReport, setEditingReport] = useState(null);

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

  // Fetch survey reports when ship is selected
  useEffect(() => {
    if (selectedShip) {
      fetchSurveyReports();
    } else {
      setSurveyReports([]);
    }
  }, [selectedShip]);

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

  // Fetch survey reports from backend
  const fetchSurveyReports = async () => {
    if (!selectedShip) return;

    try {
      setLoading(true);
      const response = await surveyReportService.getAll(selectedShip.id);
      const data = response.data || response || [];
      setSurveyReports(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch survey reports:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách báo cáo' : 'Failed to load survey reports');
      setSurveyReports([]);
    } finally {
      setLoading(false);
    }
  };

  // Refresh reports
  const handleRefresh = async () => {
    if (!selectedShip) return;
    
    try {
      setIsRefreshing(true);
      await fetchSurveyReports();
      toast.success(language === 'vi' ? '✅ Đã cập nhật danh sách!' : '✅ List refreshed!');
    } catch (error) {
      console.error('Failed to refresh:', error);
      toast.error(language === 'vi' ? '❌ Không thể làm mới danh sách' : '❌ Failed to refresh');
    } finally {
      setIsRefreshing(false);
    }
  };

  // Sort handler
  const handleSort = (column) => {
    setSort(prev => ({
      column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
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

  // Filter and sort reports
  const getFilteredReports = () => {
    let filtered = [...surveyReports];

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
        (report.survey_report_name && report.survey_report_name.toLowerCase().includes(searchLower)) ||
        (report.survey_report_no && report.survey_report_no.toLowerCase().includes(searchLower)) ||
        (report.issued_by && report.issued_by.toLowerCase().includes(searchLower)) ||
        (report.note && report.note.toLowerCase().includes(searchLower))
      );
    }

    // Apply sorting
    if (sort.column) {
      filtered.sort((a, b) => {
        let aValue = a[sort.column] || '';
        let bValue = b[sort.column] || '';

        // Handle date sorting
        if (sort.column === 'issued_date') {
          aValue = a.issued_date ? new Date(a.issued_date).getTime() : 0;
          bValue = b.issued_date ? new Date(b.issued_date).getTime() : 0;
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
    if (checked) {
      const allIds = new Set(getFilteredReports().map(r => r.id));
      setSelectedReports(allIds);
    } else {
      setSelectedReports(new Set());
    }
  };

  const handleSelectReport = (reportId) => {
    const newSelected = new Set(selectedReports);
    if (newSelected.has(reportId)) {
      newSelected.delete(reportId);
    } else {
      newSelected.add(reportId);
    }
    setSelectedReports(newSelected);
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

  const handleViewFile = (report) => {
    if (report.survey_report_file_id) {
      window.open(`https://drive.google.com/file/d/${report.survey_report_file_id}/view`, '_blank');
    } else {
      toast.warning(language === 'vi' ? 'Không có file' : 'No file available');
    }
    setContextMenu({ show: false, x: 0, y: 0, report: null });
  };

  const handleCopyLink = async (report) => {
    if (report.survey_report_file_id) {
      const link = `https://drive.google.com/file/d/${report.survey_report_file_id}/view`;
      await navigator.clipboard.writeText(link);
      toast.success(language === 'vi' ? 'Đã copy link' : 'Link copied');
    } else {
      toast.warning(language === 'vi' ? 'Không có file' : 'No file available');
    }
    setContextMenu({ show: false, x: 0, y: 0, report: null });
  };

  const handleEditReport = (report) => {
    setEditingReport(report);
    setShowEditModal(true);
    setContextMenu({ show: false, x: 0, y: 0, report: null });
  };

  const handleDeleteReport = async (report) => {
    if (!window.confirm(
      language === 'vi' 
        ? `Bạn có chắc chắn muốn xóa báo cáo "${report.survey_report_name}"?`
        : `Are you sure you want to delete report "${report.survey_report_name}"?`
    )) {
      return;
    }

    try {
      await surveyReportService.bulkDelete([report.id]);
      toast.success(language === 'vi' ? 'Đã xóa báo cáo' : 'Report deleted');
      await fetchSurveyReports();
    } catch (error) {
      console.error('Failed to delete report:', error);
      toast.error(language === 'vi' ? 'Không thể xóa báo cáo' : 'Failed to delete report');
    }
    setContextMenu({ show: false, x: 0, y: 0, report: null });
  };

  const handleBulkDelete = async () => {
    if (selectedReports.size === 0) return;

    if (!window.confirm(
      language === 'vi' 
        ? `Bạn có chắc chắn muốn xóa ${selectedReports.size} báo cáo đã chọn?`
        : `Are you sure you want to delete ${selectedReports.size} selected report(s)?`
    )) {
      return;
    }

    try {
      await surveyReportService.bulkDelete(Array.from(selectedReports));
      toast.success(
        language === 'vi' 
          ? `Đã xóa ${selectedReports.size} báo cáo` 
          : `Deleted ${selectedReports.size} report(s)`
      );
      setSelectedReports(new Set());
      await fetchSurveyReports();
    } catch (error) {
      console.error('Failed to bulk delete:', error);
      toast.error(language === 'vi' ? 'Không thể xóa báo cáo' : 'Failed to delete reports');
    }
    setContextMenu({ show: false, x: 0, y: 0, report: null });
  };

  // Note tooltip handlers
  const handleNoteMouseEnter = (e, note) => {
    if (!note) return;
    
    const rect = e.target.getBoundingClientRect();
    setNoteTooltip({
      show: true,
      x: rect.left + window.scrollX,
      y: rect.bottom + window.scrollY + 5,
      content: note
    });
  };

  const handleNoteMouseLeave = () => {
    setNoteTooltip({ show: false, x: 0, y: 0, content: '' });
  };

  // Get abbreviation from issued_by (first letters of each word, max 4 letters)
  const getAbbreviation = (issuedBy) => {
    if (!issuedBy || issuedBy === '-') return '-';
    
    const words = issuedBy.trim().split(/\s+/);
    const abbreviation = words
      .slice(0, 4) // Max 4 words
      .map(word => word.charAt(0).toUpperCase())
      .join('');
    
    return abbreviation;
  };

  // Render empty state
  if (!selectedShip) {
    return (
      <div className="text-center py-12 text-gray-500">
        <div className="text-6xl mb-4">🚢</div>
        <p className="text-lg">
          {language === 'vi' ? 'Vui lòng chọn tàu để xem Class Survey Report' : 'Please select a ship to view Class Survey Report'}
        </p>
      </div>
    );
  }

  // Render loading state
  if (loading && surveyReports.length === 0) {
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
        {/* Add & Refresh Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-all"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {language === 'vi' ? 'Thêm' : 'Add'}
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

        {/* Report Count */}
        <div className="text-sm text-gray-600">
          {language === 'vi' ? 'Tổng số:' : 'Total:'} <span className="font-bold text-gray-800">{filteredReports.length}</span>
        </div>
      </div>

      {/* Filters Row */}
      <div className="flex items-center gap-4 bg-gray-50 p-4 rounded-lg">
        {/* Status Filter */}
        <div className="w-48">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {language === 'vi' ? 'Tình trạng' : 'Status'}
          </label>
          <select
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
            <option value="valid">Valid</option>
            <option value="expired">Expired</option>
            <option value="pending">Pending</option>
          </select>
        </div>

        {/* Search Input */}
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {language === 'vi' ? 'Tìm kiếm' : 'Search'}
          </label>
          <input
            type="text"
            value={filters.search}
            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            placeholder={language === 'vi' ? 'Tìm theo tên, số, đơn vị cấp...' : 'Search by name, number, issued by...'}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Survey Reports Table */}
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

              {/* Survey Report Name */}
              <th 
                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('survey_report_name')}
              >
                <div className="flex items-center justify-between">
                  <span>{language === 'vi' ? 'Tên Báo cáo Survey' : 'Survey Report Name'}</span>
                  {getSortIcon('survey_report_name')}
                </div>
              </th>

              {/* Report Form */}
              <th 
                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('report_form')}
              >
                <div className="flex items-center justify-between">
                  <span>{language === 'vi' ? 'Mẫu Báo cáo' : 'Report Form'}</span>
                  {getSortIcon('report_form')}
                </div>
              </th>

              {/* Survey Report No */}
              <th 
                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('survey_report_no')}
              >
                <div className="flex items-center justify-between">
                  <span>{language === 'vi' ? 'Số Báo cáo Survey' : 'Survey Report No.'}</span>
                  {getSortIcon('survey_report_no')}
                </div>
              </th>

              {/* Issued Date */}
              <th 
                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('issued_date')}
              >
                <div className="flex items-center justify-between">
                  <span>{language === 'vi' ? 'Ngày cấp' : 'Issued Date'}</span>
                  {getSortIcon('issued_date')}
                </div>
              </th>

              {/* Issued By */}
              <th 
                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('issued_by')}
              >
                <div className="flex items-center justify-between">
                  <span>{language === 'vi' ? 'Cấp bởi' : 'Issued By'}</span>
                  {getSortIcon('issued_by')}
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
                  {surveyReports.length === 0 
                    ? (language === 'vi' ? 'Chưa có báo cáo survey nào' : 'No survey reports available')
                    : (language === 'vi' ? 'Không có báo cáo survey nào phù hợp với bộ lọc' : 'No survey reports match the current filters')
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

                  {/* Survey Report Name with File Icons */}
                  <td className="border border-gray-300 px-4 py-2">
                    <div className="flex items-center gap-2">
                      <span>{report.survey_report_name}</span>
                      {report.survey_report_file_id && (
                        <span 
                          className="text-green-500 text-xs cursor-pointer hover:text-green-600" 
                          title={`${language === 'vi' ? 'File gốc' : 'Original file'}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(`https://drive.google.com/file/d/${report.survey_report_file_id}/view`, '_blank');
                          }}
                        >
                          📄
                        </span>
                      )}
                      {report.survey_report_summary_file_id && (
                        <span 
                          className="text-blue-500 text-xs cursor-pointer hover:text-blue-600" 
                          title={`${language === 'vi' ? 'File tóm tắt' : 'Summary file'}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(`https://drive.google.com/file/d/${report.survey_report_summary_file_id}/view`, '_blank');
                          }}
                        >
                          📋
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Report Form */}
                  <td className="border border-gray-300 px-4 py-2">{report.report_form || '-'}</td>

                  {/* Survey Report No (Monospace Font) */}
                  <td className="border border-gray-300 px-4 py-2 font-mono">{report.survey_report_no || '-'}</td>

                  {/* Issued Date */}
                  <td className="border border-gray-300 px-4 py-2">
                    {report.issued_date ? formatDateDisplay(report.issued_date) : '-'}
                  </td>

                  {/* Issued By (Abbreviation with Tooltip) */}
                  <td 
                    className="border border-gray-300 px-4 py-2 text-sm font-semibold text-blue-700" 
                    title={report.issued_by || '-'}
                  >
                    {getAbbreviation(report.issued_by)}
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
                  <td className="border border-gray-300 px-4 py-2 text-center">
                    {report.note ? (
                      <span 
                        className="text-red-600 text-lg font-bold cursor-help relative"
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
          className="fixed bg-white border border-gray-200 rounded-lg shadow-lg z-[100]"
          style={{
            position: 'fixed',
            top: `${contextMenu.y}px`,
            left: `${contextMenu.x}px`,
            minWidth: '180px'
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
            
            {/* Bulk delete when multiple selected */}
            {selectedReports.size > 1 && (
              <button
                onClick={handleBulkDelete}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center"
              >
                <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                {language === 'vi' 
                  ? `Xóa ${selectedReports.size} báo cáo đã chọn` 
                  : `Delete ${selectedReports.size} selected report(s)`
                }
              </button>
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

      {/* Add Survey Report Modal */}
      {showAddModal && (
        <AddSurveyReportModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          selectedShip={selectedShip}
          onReportAdded={() => {
            setShowAddModal(false);
            fetchSurveyReports();
          }}
        />
      )}

      {/* Edit Survey Report Modal */}
      {showEditModal && editingReport && (
        <EditSurveyReportModal
          isOpen={showEditModal}
          onClose={() => {
            setShowEditModal(false);
            setEditingReport(null);
          }}
          report={editingReport}
          onReportUpdated={() => {
            setShowEditModal(false);
            setEditingReport(null);
            fetchSurveyReports();
          }}
        />
      )}
    </div>
  );
};
