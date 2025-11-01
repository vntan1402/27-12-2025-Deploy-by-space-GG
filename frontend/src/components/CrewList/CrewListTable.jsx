import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { formatDateDisplay } from '../../utils/dateHelpers';
import { crewService } from '../../services/crewService';
import { AddCrewModal } from './AddCrewModal';

export const CrewListTable = ({ 
  selectedShip,
  onRefresh 
}) => {
  const { language, user } = useAuth();
  
  // State
  const [crewList, setCrewList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCrewMembers, setSelectedCrewMembers] = useState(new Set());
  
  // Filter states
  const [filters, setFilters] = useState({
    ship_sign_on: 'All',
    status: 'All',
    search: ''
  });
  
  // Sort state
  const [sortConfig, setSortConfig] = useState({
    column: null,
    direction: 'asc'
  });
  
  // Context menu states
  const [crewContextMenu, setCrewContextMenu] = useState({ show: false, x: 0, y: 0, crew: null });
  const [passportContextMenu, setPassportContextMenu] = useState({ show: false, x: 0, y: 0, crew: null });
  const [rankContextMenu, setRankContextMenu] = useState({ show: false, x: 0, y: 0, crew: null });

  // Mock data for now - will be replaced with API calls
  useEffect(() => {
    if (selectedShip) {
      fetchCrewList();
    }
  }, [selectedShip, filters.ship_sign_on, filters.status]);

  const fetchCrewList = async () => {
    setLoading(true);
    try {
      // TODO: Replace with actual API call
      // const response = await crewService.getCrewList(filters);
      // setCrewList(response.data);
      
      // Mock data for now
      await new Promise(resolve => setTimeout(resolve, 500));
      setCrewList([]);
      
    } catch (error) {
      console.error('Error fetching crew list:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách thuyền viên' : 'Failed to load crew list');
    } finally {
      setLoading(false);
    }
  };

  // Get filtered and sorted crew data
  const getFilteredCrewData = () => {
    let filtered = [...crewList];
    
    // Apply search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(crew => 
        (crew.full_name && crew.full_name.toLowerCase().includes(searchLower)) ||
        (crew.full_name_en && crew.full_name_en.toLowerCase().includes(searchLower)) ||
        (crew.passport && crew.passport.toLowerCase().includes(searchLower))
      );
    }
    
    return filtered;
  };

  const getSortedCrewData = () => {
    const filtered = getFilteredCrewData();
    
    if (!sortConfig.column) return filtered;
    
    return [...filtered].sort((a, b) => {
      const aVal = a[sortConfig.column];
      const bVal = b[sortConfig.column];
      
      // Handle null/undefined
      if (!aVal && !bVal) return 0;
      if (!aVal) return 1;
      if (!bVal) return -1;
      
      // Date comparison
      if (['date_of_birth', 'date_sign_on', 'date_sign_off'].includes(sortConfig.column)) {
        const aDate = new Date(aVal);
        const bDate = new Date(bVal);
        return sortConfig.direction === 'asc' ? aDate - bDate : bDate - aDate;
      }
      
      // String comparison
      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      
      if (aStr < bStr) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aStr > bStr) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  };

  // Handle sort
  const handleSort = (column) => {
    setSortConfig(prev => ({
      column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  // Get sort icon
  const getSortIcon = (column) => {
    if (sortConfig.column !== column) {
      return <span className="text-gray-400">-</span>;
    }
    return (
      <span className="text-blue-600">
        {sortConfig.direction === 'asc' ? '▲' : '▼'}
      </span>
    );
  };

  // Handle crew selection
  const handleSelectCrew = (crewId) => {
    setSelectedCrewMembers(prev => {
      const newSet = new Set(prev);
      if (newSet.has(crewId)) {
        newSet.delete(crewId);
      } else {
        newSet.add(crewId);
      }
      return newSet;
    });
  };

  // Handle select all
  const handleSelectAllCrew = (checked) => {
    if (checked) {
      const allIds = getSortedCrewData().map(crew => crew.id);
      setSelectedCrewMembers(new Set(allIds));
    } else {
      setSelectedCrewMembers(new Set());
    }
  };

  // Close context menus on click outside
  useEffect(() => {
    const handleClick = () => {
      setCrewContextMenu({ show: false, x: 0, y: 0, crew: null });
      setPassportContextMenu({ show: false, x: 0, y: 0, crew: null });
      setRankContextMenu({ show: false, x: 0, y: 0, crew: null });
    };
    
    if (crewContextMenu.show || passportContextMenu.show || rankContextMenu.show) {
      document.addEventListener('click', handleClick);
      return () => document.removeEventListener('click', handleClick);
    }
  }, [crewContextMenu.show, passportContextMenu.show, rankContextMenu.show]);

  const filteredCrewData = getFilteredCrewData();
  const sortedCrewData = getSortedCrewData();

  return (
    <div className="space-y-6">
      {/* Header with Add Crew Button */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-1">
            {language === 'vi' ? 'Danh sách thuyền viên công ty' : 'Company Crew List'}
          </h3>
          <p className="text-sm text-gray-600">
            {language === 'vi' 
              ? 'Quản lý tất cả thuyền viên của công ty' 
              : 'Manage all crew members of the company'}
          </p>
        </div>
        
        {/* Action Buttons */}
        <div className="flex items-center space-x-3">
          {/* Add Crew Button - role check */}
          {user && ['manager', 'admin', 'super_admin'].includes(user.role) && (
            <button 
              onClick={onAddCrew}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all flex items-center"
            >
              <span className="mr-2">👤</span>
              {language === 'vi' ? 'Thêm thuyền viên' : 'Add Crew'}
            </button>
          )}
          
          {/* Refresh Button */}
          <button 
            onClick={() => {
              fetchCrewList();
              toast.success(language === 'vi' ? 'Đã làm mới danh sách thuyền viên' : 'Crew list refreshed');
            }}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-all flex items-center"
            title={language === 'vi' ? 'Làm mới' : 'Refresh'}
          >
            <span className="mr-2">🔄</span>
            {language === 'vi' ? 'Làm mới' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap items-end gap-4">
          {/* Ship Sign On Filter */}
          <div className="flex items-center space-x-2 min-w-[200px]">
            <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
              {language === 'vi' ? 'Tàu đăng ký:' : 'Ship Sign On:'}
            </label>
            <select 
              value={filters.ship_sign_on}
              onChange={(e) => setFilters({...filters, ship_sign_on: e.target.value})}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            >
              <option value="All">{language === 'vi' ? 'Tất cả' : 'All'}</option>
              {/* TODO: Add ship options */}
              <option value="-">-</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-2 min-w-[160px]">
            <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
              {language === 'vi' ? 'Trạng thái:' : 'Status:'}
            </label>
            <select 
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            >
              <option value="All">{language === 'vi' ? 'Tất cả' : 'All'}</option>
              <option value="Sign on">{language === 'vi' ? 'Đang làm việc' : 'Sign on'}</option>
              <option value="Standby">{language === 'vi' ? 'Chờ' : 'Standby'}</option>
              <option value="Leave">{language === 'vi' ? 'Nghỉ phép' : 'Leave'}</option>
            </select>
          </div>

          {/* Search Field */}
          <div className="flex items-center space-x-2 min-w-[200px] max-w-[280px]">
            <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
              {language === 'vi' ? 'Tìm kiếm:' : 'Search:'}
            </label>
            <div className="relative flex-1">
              <input
                type="text"
                placeholder={language === 'vi' ? 'Tìm theo tên thuyền viên...' : 'Search by crew name...'}
                value={filters.search}
                onChange={(e) => setFilters({...filters, search: e.target.value})}
                className="w-full px-3 py-2 pl-10 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
              <span className="absolute left-3 top-2.5 text-gray-400">🔍</span>
            </div>
          </div>

          {/* Results Count */}
          <div className="flex items-center ml-auto">
            <p className="text-sm text-gray-600 whitespace-nowrap">
              {language === 'vi' ? 'Hiển thị' : 'Showing'} <span className="font-semibold">{filteredCrewData.length}/{crewList.length}</span> {language === 'vi' ? 'thuyền viên' : 'crew members'}
              <span className="ml-2 text-green-600">✓ <span className="font-semibold">{filteredCrewData.filter(crew => crew.status === 'Sign on').length}</span> {language === 'vi' ? 'đang làm việc' : 'working'}</span>
            </p>
          </div>
        </div>
      </div>

      {/* Crew List Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {/* Checkbox Column */}
                <th className="px-3 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={sortedCrewData.length > 0 && sortedCrewData.every(crew => selectedCrewMembers.has(crew.id))}
                      onChange={(e) => handleSelectAllCrew(e.target.checked)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span>{language === 'vi' ? 'STT' : 'No.'}</span>
                  </div>
                </th>
                
                {/* Full Name */}
                <th 
                  onClick={() => handleSort('full_name')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Họ tên' : 'Full Name'}
                  {getSortIcon('full_name')}
                </th>
                
                {/* Sex */}
                <th 
                  onClick={() => handleSort('sex')}
                  className="px-3 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Giới tính' : 'Sex'}
                  {getSortIcon('sex')}
                </th>
                
                {/* Rank */}
                <th 
                  onClick={() => handleSort('rank')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Chức vụ' : 'Rank'}
                  {getSortIcon('rank')}
                </th>
                
                {/* Date of Birth */}
                <th 
                  onClick={() => handleSort('date_of_birth')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Ngày sinh' : 'Date of Birth'}
                  {getSortIcon('date_of_birth')}
                </th>
                
                {/* Place of Birth */}
                <th 
                  onClick={() => handleSort('place_of_birth')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Nơi sinh' : 'Place of Birth'}
                  {getSortIcon('place_of_birth')}
                </th>
                
                {/* Passport */}
                <th 
                  onClick={() => handleSort('passport')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Hộ chiếu' : 'Passport'}
                  {getSortIcon('passport')}
                </th>
                
                {/* Status */}
                <th 
                  onClick={() => handleSort('status')}
                  className="px-3 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Trạng thái' : 'Status'}
                  {getSortIcon('status')}
                </th>
                
                {/* Ship Sign On */}
                <th 
                  onClick={() => handleSort('ship_sign_on')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Tàu đăng ký' : 'Ship Sign On'}
                  {getSortIcon('ship_sign_on')}
                </th>
                
                {/* Place Sign On */}
                <th 
                  onClick={() => handleSort('place_sign_on')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Nơi xuống tàu' : 'Place Sign On'}
                  {getSortIcon('place_sign_on')}
                </th>
                
                {/* Date Sign On */}
                <th 
                  onClick={() => handleSort('date_sign_on')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Ngày xuống tàu' : 'Date Sign On'}
                  {getSortIcon('date_sign_on')}
                </th>
                
                {/* Date Sign Off */}
                <th 
                  onClick={() => handleSort('date_sign_off')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Ngày rời tàu' : 'Date Sign Off'}
                  {getSortIcon('date_sign_off')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="12" className="px-6 py-12 text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
                    <p className="text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
                  </td>
                </tr>
              ) : sortedCrewData.length > 0 ? (
                sortedCrewData.map((crew, index) => (
                  <tr 
                    key={crew.id} 
                    className="hover:bg-gray-50 cursor-pointer"
                    title={language === 'vi' ? 'Nhấp đúp để xem chứng chỉ | Chuột phải để xem menu' : 'Double-click to view certificates | Right-click for menu'}
                  >
                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={selectedCrewMembers.has(crew.id)}
                          onChange={() => handleSelectCrew(crew.id)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <span>{index + 1}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900 border-r border-gray-200 uppercase">
                      {language === 'vi' ? crew.full_name : (crew.full_name_en || crew.full_name)}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {crew.sex}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {crew.rank || '-'}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {formatDateDisplay(crew.date_of_birth) || '-'}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 uppercase">
                      {language === 'vi' ? crew.place_of_birth : (crew.place_of_birth_en || crew.place_of_birth)}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {crew.passport || '-'}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap border-r border-gray-200">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        crew.status === 'Sign on' ? 'bg-green-100 text-green-800' :
                        crew.status === 'Standby' ? 'bg-yellow-100 text-yellow-800' :
                        crew.status === 'Leave' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {crew.status}
                      </span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {crew.ship_sign_on}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {crew.place_sign_on || '-'}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {formatDateDisplay(crew.date_sign_on) || '-'}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDateDisplay(crew.date_sign_off) || '-'}
                    </td>
                  </tr>
                ))
              ) : (
                // Empty State
                <tr>
                  <td colSpan="12" className="px-6 py-12 text-center">
                    <div className="text-gray-400 text-lg mb-2">👥</div>
                    <p className="text-gray-500">
                      {language === 'vi' ? 'Không tìm thấy thuyền viên phù hợp' : 'No crew members found'}
                    </p>
                    <p className="text-sm text-gray-400 mt-1">
                      {language === 'vi' ? 'Thử thay đổi bộ lọc hoặc thêm thuyền viên mới' : 'Try changing filters or add new crew members'}
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
