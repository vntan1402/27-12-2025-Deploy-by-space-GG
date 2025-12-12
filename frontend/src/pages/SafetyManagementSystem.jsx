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
    try {
      const response = await api.get('/company');
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

  const subMenuItems = [
    {
      key: 'company_cert',
      name_vi: 'Chứng chỉ công ty',
      name_en: 'Company Cert.'
    },
    {
      key: 'sms_procedures',
      name_vi: 'Quy trình SMS',
      name_en: 'SMS Procedures'
    },
    {
      key: 'record_template',
      name_vi: 'Mẫu biên bản',
      name_en: 'Record Template'
    },
    {
      key: 'ship_record',
      name_vi: 'Biên bản tàu',
      name_en: 'Ship Record'
    }
  ];

  return (
    <MainLayout
      sidebar={
        <Sidebar 
          selectedCategory="sms"
          onCategoryChange={() => {}}
        />
      }
    >
      {/* Company Info Panel */}
      {companyData && (
        <CompanyInfoPanel 
          company={companyData}
          language={language}
        />
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
            {/* Action Buttons Row */}
            <div className="flex justify-between items-center mb-4 gap-4">
              <div className="flex items-center gap-3">
                {/* Add Button */}
                <button
                  onClick={() => setShowAddModal(true)}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 font-medium transition-all shadow-sm"
                >
                  <span>➕</span>
                  {language === 'vi' ? 'Thêm' : 'Add'}
                </button>

                {/* Refresh Button */}
                <button
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center gap-2 transition-all shadow-sm"
                >
                  <span className={isRefreshing ? 'animate-spin' : ''}>🔄</span>
                  {language === 'vi' ? 'Làm mới' : 'Refresh'}
                </button>

                {/* Bulk Delete Button */}
                {selectedCerts.size > 0 && (
                  <button
                    onClick={handleBulkDelete}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2 transition-all shadow-sm"
                  >
                    <span>🗑️</span>
                    {language === 'vi' ? `Xóa (${selectedCerts.size})` : `Delete (${selectedCerts.size})`}
                  </button>
                )}
              </div>

              <div className="flex items-center gap-3">
                {/* Search */}
                <div className="relative">
                  <input
                    type="text"
                    placeholder={language === 'vi' ? 'Tìm kiếm...' : 'Search...'}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 w-64"
                  />
                  <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>

                {/* Status Filter */}
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">{language === 'vi' ? 'Tất cả' : 'All Status'}</option>
                  <option value="Valid">{language === 'vi' ? 'Còn hạn' : 'Valid'}</option>
                  <option value="Due Soon">{language === 'vi' ? 'Sắp hết hạn' : 'Due Soon'}</option>
                  <option value="Expired">{language === 'vi' ? 'Hết hạn' : 'Expired'}</option>
                </select>
              </div>
            </div>

            {/* Info Row */}
            <div className="mb-4 text-sm text-gray-600">
              {language === 'vi' 
                ? `Hiển thị ${getFilteredAndSortedCerts().length} / ${companyCerts.length} chứng chỉ`
                : `Showing ${getFilteredAndSortedCerts().length} / ${companyCerts.length} certificates`
              }
              {selectedCerts.size > 0 && (
                <span className="ml-4 text-blue-600 font-medium">
                  {language === 'vi' ? `Đã chọn: ${selectedCerts.size}` : `Selected: ${selectedCerts.size}`}
                </span>
              )}
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
                  onEditClick={(cert) => {
                    setEditingCert(cert);
                    setShowEditModal(true);
                  }}
                  onDeleteClick={(cert) => {
                    setDeletingCert(cert);
                    setShowDeleteModal(true);
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
