/**
 * Certificate Filters Component
 * Filter controls for certificate list (type, status, search)
 * Extracted from Frontend V1 App.js (lines 13629-13727)
 */
import React from 'react';

export const CertificateFilters = ({
  filters,
  onFilterChange,
  certificateTypes,
  totalCount,
  filteredCount,
  language,
  linksFetching = false,
  linksReady = 0,
}) => {
  return (
    <div className="mb-4 p-4 bg-gray-50 rounded-lg border">
      <div className="flex gap-4 items-center flex-wrap">
        {/* Certificate Type Filter */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">
            {language === 'vi' ? 'Loại chứng chỉ:' : 'Certificate Type:'}
          </label>
          <select
            value={filters.certificateType}
            onChange={(e) => onFilterChange({ ...filters, certificateType: e.target.value })}
            className="border border-gray-300 rounded px-3 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
            {certificateTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>
        
        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">
            {language === 'vi' ? 'Trạng thái:' : 'Status:'}
          </label>
          <select
            value={filters.status}
            onChange={(e) => onFilterChange({ ...filters, status: e.target.value })}
            className="border border-gray-300 rounded px-3 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
            <option value="Valid">{language === 'vi' ? 'Còn hiệu lực' : 'Valid'}</option>
            <option value="Expired">{language === 'vi' ? 'Hết hiệu lực' : 'Expired'}</option>
            <option value="Over Due">{language === 'vi' ? 'Quá hạn' : 'Over Due'}</option>
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
              onChange={(e) => onFilterChange({ ...filters, search: e.target.value })}
              placeholder={language === 'vi' ? 'Tìm theo tên chứng chỉ...' : 'Search by certificate name...'}
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
                onClick={() => onFilterChange({ ...filters, search: '' })}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
        
        {/* Results Count with Link Status */}
        <div className="ml-auto flex items-center gap-3">
          <div className="text-sm text-gray-600">
            {language === 'vi' 
              ? `Hiển thị ${filteredCount} / ${totalCount} chứng chỉ`
              : `Showing ${filteredCount} / ${totalCount} certificates`
            }
          </div>
          
          {/* Pre-fetch Links Indicator */}
          {linksFetching && (
            <div className="flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">
              <svg className="w-3 h-3 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {language === 'vi' ? 'Đang tải links...' : 'Loading links...'}
            </div>
          )}
          
          {!linksFetching && linksReady > 0 && (
            <div className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              {linksReady} {language === 'vi' ? 'links sẵn sàng' : 'links ready'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
