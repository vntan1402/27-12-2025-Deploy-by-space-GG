import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout, Sidebar, SubMenuBar, CompanyInfoPanel } from '../components';
import {
  CompanyCertTable,
  AddCompanyCertModal,
  EditCompanyCertModal,
  DeleteCompanyCertModal,
  CompanyCertNotesModal
} from '../components/CompanyCert';
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
      toast.error('Failed to load certificates');
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
    if (cert.file_id) {
      window.open(`https://drive.google.com/file/d/${cert.file_id}/view`, '_blank');
    }
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

  const handleUpdateNextSurveys = async () => {
    if (!window.confirm(language === 'vi' 
      ? 'Bạn có chắc muốn cập nhật lại tất cả ngày khảo sát tiếp theo? Thao tác này sẽ tính toán lại dựa trên quy tắc kinh doanh hiện tại.'
      : 'Are you sure you want to recalculate all next survey dates? This will update all certificates based on current business rules.'
    )) {
      return;
    }

    try {
      toast.loading(language === 'vi' ? 'Đang cập nhật...' : 'Updating...', { id: 'update-surveys' });
      
      const result = await companyCertService.recalculateAllNextSurveys();
      
      toast.success(language === 'vi' 
        ? `Đã cập nhật ${result.updated_count} chứng chỉ! (Bỏ qua: ${result.skipped_count})`
        : `Updated ${result.updated_count} certificates! (Skipped: ${result.skipped_count})`,
        { id: 'update-surveys' }
      );
      
      // Reload certificates to show updated data
      await loadCompanyCerts();
    } catch (error) {
      console.error('Update surveys error:', error);
      toast.error(language === 'vi' ? 'Cập nhật thất bại!' : 'Update failed!', { id: 'update-surveys' });
    }
  };

  const getFilteredAndSortedCerts = () => {
    let filtered = [...companyCerts];
    
    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(cert =>
        cert.cert_name?.toLowerCase().includes(query) ||
        cert.cert_no?.toLowerCase().includes(query) ||
        cert.issued_by?.toLowerCase().includes(query)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(cert => {
        if (!cert.valid_date) return statusFilter === 'Unknown';
        
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        let validDate;
        if (cert.valid_date.includes('/')) {
          const [day, month, year] = cert.valid_date.split('/');
          validDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
        } else {
          validDate = new Date(cert.valid_date);
        }
        
        if (isNaN(validDate.getTime())) return statusFilter === 'Unknown';
        validDate.setHours(0, 0, 0, 0);
        
        if (validDate < today) return statusFilter === 'Expired';
        
        const diffDays = Math.ceil((validDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
        
        if (diffDays <= 90) return statusFilter === 'Due Soon';
        return statusFilter === 'Valid';
      });
    }
    
    // Sort
    filtered.sort((a, b) => {
      const aVal = a[sortConfig.column];
      const bVal = b[sortConfig.column];
      
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
                {/* Bulk Delete Button */}
                {selectedCerts.size > 0 && (
                  <button
                    onClick={handleBulkDelete}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2 text-sm font-medium shadow-sm"
                  >
                    <span>🗑️</span>
                    {language === 'vi' ? `Xóa (${selectedCerts.size})` : `Delete (${selectedCerts.size})`}
                  </button>
                )}
                
                {/* Update Next Survey Button */}
                <button
                  onClick={handleUpdateNextSurveys}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 text-sm font-medium shadow-sm"
                  disabled={certsLoading}
                >
                  <span>🔄</span>
                  {language === 'vi' ? 'Cập nhật khảo sát' : 'Update Next Survey'}
                </button>
                
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
              handleDoubleClick(contextMenu.certificate);
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
          >
            <span>👁️</span>
            {language === 'vi' ? 'Xem file' : 'View File'}
          </button>

          <div className="border-t border-gray-200 my-1"></div>

          {/* Edit */}
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

          {/* Notes */}
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

          <div className="border-t border-gray-200 my-1"></div>

          {/* Delete */}
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
    </MainLayout>
  );
};

export default SafetyManagementSystem;
