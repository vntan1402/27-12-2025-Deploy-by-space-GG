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
  
  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [editingCert, setEditingCert] = useState(null);
  const [deletingCert, setDeletingCert] = useState(null);
  const [notesCert, setNotesCert] = useState(null);
  
  // Sort & Filter
  const [sortConfig, setSortConfig] = useState({
    column: 'cert_name',
    direction: 'asc'
  });

  // Load company data
  useEffect(() => {
    loadCompanyData();
    if (selectedSubMenu === 'company_cert') {
      loadCompanyCerts();
    }
  }, [selectedSubMenu]);

  const loadCompanyData = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/company`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setCompanyData(data);
      }
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
      setSelectedCerts(new Set(companyCerts.map(cert => cert.id)));
    } else {
      setSelectedCerts(new Set());
    }
  };

  const handleDoubleClick = (cert) => {
    if (cert.file_id) {
      window.open(`https://drive.google.com/file/d/${cert.file_id}/view`, '_blank');
    }
  };

  const getFilteredAndSortedCerts = () => {
    let filtered = [...companyCerts];
    
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

  // Sub-menu items
  const subMenuItems = [
    {
      id: 'company_cert',
      label: language === 'vi' ? 'Chứng chỉ công ty' : 'Company Cert.',
      icon: '📄'
    },
    {
      id: 'sms_procedures',
      label: language === 'vi' ? 'Quy trình SMS' : 'SMS Procedures',
      icon: '📋'
    },
    {
      id: 'record_template',
      label: language === 'vi' ? 'Mẫu biên bản' : 'Record Template',
      icon: '📝'
    },
    {
      id: 'ship_record',
      label: language === 'vi' ? 'Biên bản tàu' : 'Ship Record',
      icon: '🚢'
    }
  ];

  return (
    <MainLayout>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Company Info Panel */}
          {companyData && (
            <CompanyInfoPanel 
              company={companyData}
              language={language}
            />
          )}

          {/* Sub Menu */}
          <SubMenuBar
            items={subMenuItems}
            selectedItem={selectedSubMenu}
            onSelectItem={setSelectedSubMenu}
            language={language}
          />

          {/* Main Content */}
          <div className="flex-1 overflow-auto p-6 bg-gray-50">
            <div className="max-w-7xl mx-auto">
              <div className="mb-6">
                <h1 className="text-3xl font-bold text-gray-800">
                  {language === 'vi' ? 'Hệ thống quản lý an toàn' : 'Safety Management System'}
                </h1>
              </div>

              {/* Company Cert Content */}
              {selectedSubMenu === 'company_cert' && (
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-semibold">
                      {language === 'vi' ? 'Chứng chỉ công ty' : 'Company Certificates'}
                    </h2>
                    <button
                      onClick={() => setShowAddModal(true)}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                    >
                      <span>➕</span>
                      {language === 'vi' ? 'Thêm chứng chỉ' : 'Add Certificate'}
                    </button>
                  </div>

                  {certsLoading ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    </div>
                  ) : (
                    <CompanyCertTable
                      certificates={getFilteredAndSortedCerts()}
                      selectedCertificates={selectedCerts}
                      onSelectCertificate={handleSelectCert}
                      onSelectAllCertificates={handleSelectAllCerts}
                      onSort={handleSort}
                      sortConfig={sortConfig}
                      onDoubleClick={handleDoubleClick}
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
                  )}
                </div>
              )}

              {/* Other sub-menus (placeholder) */}
              {selectedSubMenu === 'sms_procedures' && (
                <div className="bg-white rounded-lg shadow p-6 text-center">
                  <p className="text-gray-600">
                    {language === 'vi' ? 'SMS Procedures - Đang phát triển' : 'SMS Procedures - Coming Soon'}
                  </p>
                </div>
              )}

              {selectedSubMenu === 'record_template' && (
                <div className="bg-white rounded-lg shadow p-6 text-center">
                  <p className="text-gray-600">
                    {language === 'vi' ? 'Record Template - Đang phát triển' : 'Record Template - Coming Soon'}
                  </p>
                </div>
              )}

              {selectedSubMenu === 'ship_record' && (
                <div className="bg-white rounded-lg shadow p-6 text-center">
                  <p className="text-gray-600">
                    {language === 'vi' ? 'Ship Record - Đang phát triển' : 'Ship Record - Coming Soon'}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      <AddCompanyCertModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={loadCompanyCerts}
        language={language}
      />

      <EditCompanyCertModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        onSuccess={loadCompanyCerts}
        certificate={editingCert}
        language={language}
      />

      <DeleteCompanyCertModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onSuccess={loadCompanyCerts}
        certificate={deletingCert}
        language={language}
      />

      <CompanyCertNotesModal
        isOpen={showNotesModal}
        onClose={() => setShowNotesModal(false)}
        onSuccess={loadCompanyCerts}
        certificate={notesCert}
        language={language}
      />
    </MainLayout>
  );
};

export default SafetyManagementSystem;
