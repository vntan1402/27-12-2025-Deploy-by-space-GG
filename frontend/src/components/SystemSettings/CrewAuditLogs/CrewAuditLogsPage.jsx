/**
 * Crew Audit Logs Page
 * Displays comprehensive audit trail for all crew operations
 */
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import { MainLayout } from '../../Layout';
import { AuditLogFilters } from './AuditLogFilters';
import { AuditLogList } from './AuditLogList';
import { AuditLogDetailModal } from './AuditLogDetailModal';
import crewAuditLogService from '../../../services/crewAuditLogService';

const CrewAuditLogsPage = () => {
  const navigate = useNavigate();
  const { user, language } = useAuth();

  // State
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  // Filter states
  const [filters, setFilters] = useState({
    dateRange: 'last_30_days',
    customStartDate: null,
    customEndDate: null,
    action: 'all',
    user: 'all',
    ship: 'all',
    search: ''
  });

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const logsPerPage = 20;

  // Load logs from API
  useEffect(() => {
    const loadLogs = async () => {
      setLoading(true);
      try {
        // Calculate date range
        let startDate = null;
        let endDate = null;
        
        const now = new Date();
        
        switch (filters.dateRange) {
          case 'today':
            startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString();
            break;
          case 'yesterday':
            const yesterday = new Date(now);
            yesterday.setDate(yesterday.getDate() - 1);
            startDate = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate()).toISOString();
            endDate = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate(), 23, 59, 59).toISOString();
            break;
          case 'last_7_days':
            startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
            break;
          case 'last_30_days':
            startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString();
            break;
          case 'last_3_months':
            startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000).toISOString();
            break;
          case 'custom':
            startDate = filters.customStartDate ? new Date(filters.customStartDate).toISOString() : null;
            endDate = filters.customEndDate ? new Date(filters.customEndDate + 'T23:59:59').toISOString() : null;
            break;
        }
        
        const response = await crewAuditLogService.getAuditLogs({
          startDate,
          endDate,
          action: filters.action,
          performedBy: filters.user,
          shipName: filters.ship,
          search: filters.search,
          skip: (currentPage - 1) * logsPerPage,
          limit: logsPerPage
        });
        
        setLogs(response.logs || []);
      } catch (error) {
        console.error('Error loading audit logs:', error);
        setLogs([]);
      } finally {
        setLoading(false);
      }
    };

    loadLogs();
  }, [filters, currentPage, logsPerPage]);

  // Logs are already filtered by API, just use them directly
  const totalPages = Math.ceil(logs.length / logsPerPage);

  // Load unique users and ships from API
  const [uniqueUsers, setUniqueUsers] = useState([]);
  const [uniqueShips, setUniqueShips] = useState([]);

  useEffect(() => {
    const loadFilterData = async () => {
      try {
        const [usersData, shipsData] = await Promise.all([
          crewAuditLogService.getUniqueUsers(),
          crewAuditLogService.getUniqueShips()
        ]);
        setUniqueUsers(usersData || []);
        setUniqueShips(shipsData || []);
      } catch (error) {
        console.error('Error loading filter data:', error);
      }
    };

    loadFilterData();
  }, []);

  // Handle filter change
  const handleFilterChange = (newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setCurrentPage(1); // Reset to first page
  };

  // Handle view details
  const handleViewDetails = (log) => {
    setSelectedLog(log);
    setShowDetailModal(true);
  };

  // Handle export CSV
  const handleExportCSV = () => {
    // Prepare CSV data
    const headers = [
      'Date',
      'Time',
      'Action',
      'Crew Name',
      'Ship',
      'User',
      'Changes',
      'Notes'
    ];

    const rows = logs.map(log => {
      const date = new Date(log.performed_at);
      const dateStr = date.toLocaleDateString(language === 'vi' ? 'vi-VN' : 'en-US');
      const timeStr = date.toLocaleTimeString(language === 'vi' ? 'vi-VN' : 'en-US');
      const changesStr = log.changes.map(c => 
        `${c.field_label}: "${c.old_value}" → "${c.new_value}"`
      ).join('; ');

      return [
        dateStr,
        timeStr,
        log.action,
        log.entity_name,
        log.ship_name || '-',
        log.performed_by_name,
        changesStr,
        log.notes || ''
      ];
    });

    // Create CSV content
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    // Download
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    link.setAttribute('href', url);
    link.setAttribute('download', `crew_audit_logs_${timestamp}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Handle export Excel
  const handleExportExcel = async () => {
    try {
      // Dynamic import of xlsx library
      const XLSX = await import('xlsx');

      // Prepare data for Excel
      const data = logs.map(log => {
        const date = new Date(log.performed_at);
        const changesStr = log.changes.map(c => 
          `${c.field_label}: "${c.old_value}" → "${c.new_value}"`
        ).join('\n');

        return {
          'Date': date.toLocaleDateString(language === 'vi' ? 'vi-VN' : 'en-US'),
          'Time': date.toLocaleTimeString(language === 'vi' ? 'vi-VN' : 'en-US'),
          'Action': log.action,
          'Crew Name': log.entity_name,
          'Ship': log.ship_name || '-',
          'User': log.performed_by_name,
          'Changes': changesStr,
          'Notes': log.notes || ''
        };
      });

      // Create worksheet
      const ws = XLSX.utils.json_to_sheet(data);

      // Set column widths
      ws['!cols'] = [
        { wch: 12 },  // Date
        { wch: 10 },  // Time
        { wch: 15 },  // Action
        { wch: 20 },  // Crew Name
        { wch: 15 },  // Ship
        { wch: 20 },  // User
        { wch: 50 },  // Changes
        { wch: 30 }   // Notes
      ];

      // Create workbook
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Crew Audit Logs');

      // Download
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      XLSX.writeFile(wb, `crew_audit_logs_${timestamp}.xlsx`);
    } catch (error) {
      console.error('Export Excel error:', error);
      alert(language === 'vi' 
        ? 'Lỗi khi export Excel. Vui lòng thử lại.' 
        : 'Error exporting Excel. Please try again.');
    }
  };

  // Handle export menu
  const [showExportMenu, setShowExportMenu] = useState(false);

  // Permission check
  useEffect(() => {
    if (!user || !['admin', 'super_admin', 'system_admin'].includes(user.role)) {
      navigate('/system-settings');
    }
  }, [user, navigate]);

  if (!user) return null;

  return (
    <MainLayout>
      {/* Page Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
              📋 {language === 'vi' ? 'Crew Audit Logs' : 'Crew Audit Logs'}
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              {language === 'vi' 
                ? 'Lịch sử thay đổi và hoạt động của tất cả crew records'
                : 'Change history and activity logs for all crew records'}
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Export Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-all flex items-center gap-2"
              >
                <span>📥</span>
                <span>{language === 'vi' ? 'Export' : 'Export'}</span>
                <svg className={`w-4 h-4 transition-transform ${showExportMenu ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showExportMenu && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setShowExportMenu(false)}></div>
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl z-20 border border-gray-200 overflow-hidden">
                    <button
                      onClick={() => {
                        handleExportCSV();
                        setShowExportMenu(false);
                      }}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50 transition-all flex items-center gap-3"
                    >
                      <span className="text-xl">📄</span>
                      <div>
                        <div className="font-medium text-gray-900">CSV</div>
                        <div className="text-xs text-gray-500">Comma-separated values</div>
                      </div>
                    </button>
                    
                    <button
                      onClick={() => {
                        handleExportExcel();
                        setShowExportMenu(false);
                      }}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50 transition-all flex items-center gap-3 border-t border-gray-100"
                    >
                      <span className="text-xl">📊</span>
                      <div>
                        <div className="font-medium text-gray-900">Excel</div>
                        <div className="text-xs text-gray-500">Microsoft Excel format</div>
                      </div>
                    </button>
                  </div>
                </>
              )}
            </div>
            
            <button
              onClick={() => navigate('/system-settings')}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-all"
            >
              {language === 'vi' ? 'Quay lại' : 'Back'}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="bg-white rounded-xl shadow-lg">
        {/* Filters */}
        <div className="p-6 border-b border-gray-200">
          <AuditLogFilters
            filters={filters}
            onFilterChange={handleFilterChange}
            uniqueUsers={uniqueUsers}
            uniqueShips={uniqueShips}
            language={language}
          />
        </div>

        {/* Summary */}
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <p className="text-sm text-gray-700">
            {language === 'vi' ? 'Tóm tắt: ' : 'Summary: '}
            <span className="font-bold">{logs.length}</span>
            {language === 'vi' ? ' logs được tìm thấy' : ' logs found'}
          </p>
        </div>

        {/* Logs List */}
        <div className="p-6">
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">
                {language === 'vi' ? 'Đang tải...' : 'Loading...'}
              </p>
            </div>
          ) : paginatedLogs.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📋</div>
              <p className="text-gray-600 text-lg">
                {language === 'vi' ? 'Không tìm thấy logs' : 'No logs found'}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                {language === 'vi' 
                  ? 'Thử thay đổi bộ lọc để xem kết quả khác'
                  : 'Try changing filters to see different results'}
              </p>
            </div>
          ) : (
            <AuditLogList
              logs={paginatedLogs}
              onViewDetails={handleViewDetails}
              language={language}
            />
          )}
        </div>

        {/* Pagination */}
        {!loading && paginatedLogs.length > 0 && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className={`
                px-4 py-2 rounded-lg font-medium transition-all
                ${currentPage === 1
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'}
              `}
            >
              ◄ {language === 'vi' ? 'Trước' : 'Previous'}
            </button>

            <span className="text-sm text-gray-700">
              {language === 'vi' ? 'Trang' : 'Page'} {currentPage} {language === 'vi' ? 'của' : 'of'} {totalPages}
            </span>

            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className={`
                px-4 py-2 rounded-lg font-medium transition-all
                ${currentPage === totalPages
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'}
              `}
            >
              {language === 'vi' ? 'Sau' : 'Next'} ►
            </button>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {showDetailModal && selectedLog && (
        <AuditLogDetailModal
          log={selectedLog}
          onClose={() => {
            setShowDetailModal(false);
            setSelectedLog(null);
          }}
          language={language}
        />
      )}
    </MainLayout>
  );
};

export default CrewAuditLogsPage;
