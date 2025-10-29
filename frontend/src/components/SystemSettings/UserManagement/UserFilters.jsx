/**
 * UserFilters Component
 * Provides filtering and sorting controls for user list
 */
import React from 'react';

const UserFilters = ({
  filters,
  setFilters,
  sorting,
  setSorting,
  companies,
  ships,
  language,
  onClearFilters
}) => {
  /**
   * Department options
   */
  const departmentOptions = [
    { value: '', label: language === 'vi' ? 'Tất cả phòng ban' : 'All Departments' },
    { value: 'technical', label: language === 'vi' ? 'Kỹ thuật' : 'Technical' },
    { value: 'operations', label: language === 'vi' ? 'Vận hành' : 'Operations' },
    { value: 'safety', label: language === 'vi' ? 'An toàn' : 'Safety' },
    { value: 'commercial', label: language === 'vi' ? 'Thương mại' : 'Commercial' },
    { value: 'crewing', label: language === 'vi' ? 'Thuyền viên' : 'Crewing' },
    { value: 'ship_crew', label: language === 'vi' ? 'Thuyền viên tàu' : 'Ship Crew' }
  ];

  /**
   * Sort by options
   */
  const sortByOptions = [
    { value: 'full_name', label: language === 'vi' ? 'Tên' : 'Name' },
    { value: 'company', label: language === 'vi' ? 'Công ty' : 'Company' },
    { value: 'department', label: language === 'vi' ? 'Phòng ban' : 'Department' },
    { value: 'role', label: language === 'vi' ? 'Vai trò' : 'Role' },
    { value: 'ship', label: language === 'vi' ? 'Tàu' : 'Ship' },
    { value: 'created_at', label: language === 'vi' ? 'Ngày tạo' : 'Created Date' }
  ];

  /**
   * Sort order options
   */
  const sortOrderOptions = [
    { value: 'asc', label: language === 'vi' ? 'Tăng dần (A-Z)' : 'Ascending (A-Z)' },
    { value: 'desc', label: language === 'vi' ? 'Giảm dần (Z-A)' : 'Descending (Z-A)' }
  ];

  return (
    <div className="mb-6 bg-gray-50 p-4 rounded-lg border border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          {language === 'vi' ? 'Bộ lọc & Sắp xếp' : 'Filters & Sorting'}
        </h3>
        <button
          onClick={onClearFilters}
          className="text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-1 rounded transition-all"
        >
          {language === 'vi' ? 'Xóa bộ lọc' : 'Clear Filters'}
        </button>
      </div>

      {/* Filters Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {/* Company Filter */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            {language === 'vi' ? 'Công ty' : 'Company'}
          </label>
          <select
            value={filters.company}
            onChange={(e) => setFilters(prev => ({ ...prev, company: e.target.value }))}
            className="w-full px-2 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">{language === 'vi' ? 'Tất cả công ty' : 'All Companies'}</option>
            {companies.map((company, idx) => (
              <option key={idx} value={company.name_en || company.name_vn}>
                {language === 'vi' ? company.name_vn : company.name_en}
              </option>
            ))}
          </select>
        </div>

        {/* Department Filter */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            {language === 'vi' ? 'Phòng ban' : 'Department'}
          </label>
          <select
            value={filters.department}
            onChange={(e) => setFilters(prev => ({ ...prev, department: e.target.value }))}
            className="w-full px-2 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {departmentOptions.map(dept => (
              <option key={dept.value} value={dept.value}>{dept.label}</option>
            ))}
          </select>
        </div>

        {/* Ship Filter */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            {language === 'vi' ? 'Tàu' : 'Ship'}
          </label>
          <select
            value={filters.ship}
            onChange={(e) => setFilters(prev => ({ ...prev, ship: e.target.value }))}
            className="w-full px-2 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">{language === 'vi' ? 'Tất cả tàu' : 'All Ships'}</option>
            {ships.map((ship, idx) => (
              <option key={idx} value={ship.name}>{ship.name}</option>
            ))}
          </select>
        </div>

        {/* Sort By */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            {language === 'vi' ? 'Sắp xếp theo' : 'Sort By'}
          </label>
          <select
            value={sorting.sortBy}
            onChange={(e) => setSorting(prev => ({ ...prev, sortBy: e.target.value }))}
            className="w-full px-2 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {sortByOptions.map(option => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        {/* Sort Order */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            {language === 'vi' ? 'Thứ tự' : 'Order'}
          </label>
          <select
            value={sorting.sortOrder}
            onChange={(e) => setSorting(prev => ({ ...prev, sortOrder: e.target.value }))}
            className="w-full px-2 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {sortOrderOptions.map(option => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};

export default UserFilters;
