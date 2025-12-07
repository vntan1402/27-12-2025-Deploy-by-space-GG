/**
 * Audit Log Filters Component
 * Provides filtering options for audit logs
 */
import React from 'react';

export const AuditLogFilters = ({ filters, onFilterChange, uniqueUsers, uniqueShips, language }) => {
  const handleDateRangeChange = (e) => {
    onFilterChange({ dateRange: e.target.value });
  };

  const handleActionChange = (e) => {
    onFilterChange({ action: e.target.value });
  };

  const handleUserChange = (e) => {
    onFilterChange({ user: e.target.value });
  };

  const handleSearchChange = (e) => {
    onFilterChange({ search: e.target.value });
  };

  const handleShipChange = (e) => {
    onFilterChange({ ship: e.target.value });
  };

  const handleCustomDateChange = (field, value) => {
    onFilterChange({ [field]: value });
  };

  return (
    <div className="space-y-4">
      {/* Row 1: Date Range and Action */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Date Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {language === 'vi' ? 'Khoảng thời gian' : 'Date Range'}
          </label>
          <select
            value={filters.dateRange}
            onChange={handleDateRangeChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
          >
            <option value="today">{language === 'vi' ? 'Hôm nay' : 'Today'}</option>
            <option value="yesterday">{language === 'vi' ? 'Hôm qua' : 'Yesterday'}</option>
            <option value="last_7_days">{language === 'vi' ? '7 ngày qua' : 'Last 7 days'}</option>
            <option value="last_30_days">{language === 'vi' ? '30 ngày qua' : 'Last 30 days'}</option>
            <option value="last_3_months">{language === 'vi' ? '3 tháng qua' : 'Last 3 months'}</option>
            <option value="custom">{language === 'vi' ? 'Tùy chỉnh' : 'Custom'}</option>
          </select>
        </div>

        {/* Action Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {language === 'vi' ? 'Loại thao tác' : 'Action Type'}
          </label>
          <select
            value={filters.action}
            onChange={handleActionChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
          >
            <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
            <option value="CREATE">{language === 'vi' ? 'Tạo mới' : 'Create'}</option>
            <option value="UPDATE">{language === 'vi' ? 'Cập nhật' : 'Update'}</option>
            <option value="DELETE">{language === 'vi' ? 'Xóa' : 'Delete'}</option>
            <option value="SIGN_ON">{language === 'vi' ? 'Xuống tàu' : 'Sign On'}</option>
            <option value="SIGN_OFF">{language === 'vi' ? 'Rời tàu' : 'Sign Off'}</option>
            <option value="SHIP_TRANSFER">{language === 'vi' ? 'Chuyển tàu' : 'Ship Transfer'}</option>
            <option value="BULK_UPDATE">{language === 'vi' ? 'Cập nhật hàng loạt' : 'Bulk Update'}</option>
          </select>
        </div>

        {/* User */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {language === 'vi' ? 'Người thực hiện' : 'User'}
          </label>
          <select
            value={filters.user}
            onChange={handleUserChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
          >
            <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
            {uniqueUsers.map(user => (
              <option key={user.username} value={user.username}>
                {user.name} ({user.username})
              </option>
            ))}
          </select>
        </div>

        {/* Search */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {language === 'vi' ? 'Tìm kiếm crew' : 'Search Crew'}
          </label>
          <input
            type="text"
            value={filters.search}
            onChange={handleSearchChange}
            placeholder={language === 'vi' ? 'Nhập tên crew...' : 'Enter crew name...'}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
          />
        </div>
      </div>

      {/* Row 2: Custom Date Range (if selected) */}
      {filters.dateRange === 'custom' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Từ ngày' : 'From Date'}
            </label>
            <input
              type="date"
              value={filters.customStartDate || ''}
              onChange={(e) => handleCustomDateChange('customStartDate', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Đến ngày' : 'To Date'}
            </label>
            <input
              type="date"
              value={filters.customEndDate || ''}
              onChange={(e) => handleCustomDateChange('customEndDate', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
            />
          </div>
        </div>
      )}
    </div>
  );
};
