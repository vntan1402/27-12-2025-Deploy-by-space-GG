/**
 * Crew Audit Logs Page
 * Displays comprehensive audit trail for all crew operations
 */
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import { MainLayout } from '../../Layout';
import { allMockLogs } from './mockData';
import { AuditLogFilters } from './AuditLogFilters';
import { AuditLogList } from './AuditLogList';
import { AuditLogDetailModal } from './AuditLogDetailModal';

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

  // Load mock data (will be replaced with API call)
  useEffect(() => {
    const loadLogs = async () => {
      setLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      setLogs(allMockLogs);
      setLoading(false);
    };

    loadLogs();
  }, []);

  // Filter logs
  const filteredLogs = useMemo(() => {
    let result = [...logs];

    // Date range filter
    const now = new Date();
    let startDate = null;

    switch (filters.dateRange) {
      case 'today':
        startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        break;
      case 'yesterday':
        startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
        break;
      case 'last_7_days':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case 'last_30_days':
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case 'last_3_months':
        startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        break;
      case 'custom':
        startDate = filters.customStartDate ? new Date(filters.customStartDate) : null;
        break;
      default:
        startDate = null;
    }

    if (startDate) {
      result = result.filter(log => new Date(log.performed_at) >= startDate);
    }

    if (filters.dateRange === 'custom' && filters.customEndDate) {
      const endDate = new Date(filters.customEndDate);
      endDate.setHours(23, 59, 59, 999);
      result = result.filter(log => new Date(log.performed_at) <= endDate);
    }

    // Action filter
    if (filters.action !== 'all') {
      result = result.filter(log => log.action === filters.action);
    }

    // User filter
    if (filters.user !== 'all') {
      result = result.filter(log => log.performed_by === filters.user);
    }

    // Ship filter
    if (filters.ship !== 'all') {
      result = result.filter(log => log.ship_name === filters.ship);
    }

    // Search filter (crew name)
    if (filters.search.trim()) {
      const searchTerm = filters.search.toLowerCase().trim();
      result = result.filter(log => 
        log.entity_name.toLowerCase().includes(searchTerm)
      );
    }

    // Sort by date (newest first)
    result.sort((a, b) => new Date(b.performed_at) - new Date(a.performed_at));

    return result;
  }, [logs, filters]);

  // Pagination
  const totalPages = Math.ceil(filteredLogs.length / logsPerPage);
  const paginatedLogs = useMemo(() => {
    const startIndex = (currentPage - 1) * logsPerPage;
    return filteredLogs.slice(startIndex, startIndex + logsPerPage);
  }, [filteredLogs, currentPage, logsPerPage]);

  // Get unique users for filter dropdown
  const uniqueUsers = useMemo(() => {
    const users = logs.map(log => ({
      username: log.performed_by,
      name: log.performed_by_name
    }));
    
    // Remove duplicates
    const unique = users.filter((user, index, self) => 
      index === self.findIndex(u => u.username === user.username)
    );
    
    return unique;
  }, [logs]);

  // Get unique ships for filter dropdown
  const uniqueShips = useMemo(() => {
    const ships = logs.map(log => log.ship_name);
    
    // Remove duplicates and sort
    const unique = [...new Set(ships)].filter(ship => ship && ship !== '-');
    unique.sort();
    
    return unique;
  }, [logs]);

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

  // Handle export
  const handleExport = () => {
    // TODO: Implement export functionality
    alert(language === 'vi' 
      ? 'Tính năng export đang được phát triển' 
      : 'Export feature under development');
  };

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
            <button
              onClick={handleExport}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-all flex items-center gap-2"
            >
              <span>📥</span>
              <span>{language === 'vi' ? 'Export' : 'Export'}</span>
            </button>
            
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
            language={language}
          />
        </div>

        {/* Summary */}
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <p className="text-sm text-gray-700">
            {language === 'vi' ? 'Tóm tắt: ' : 'Summary: '}
            <span className="font-bold">{filteredLogs.length}</span>
            {language === 'vi' ? ' logs được tìm thấy' : ' logs found'}
            {filteredLogs.length !== logs.length && (
              <span className="text-gray-500">
                {' '}({language === 'vi' ? 'từ tổng' : 'out of'} {logs.length})
              </span>
            )}
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
