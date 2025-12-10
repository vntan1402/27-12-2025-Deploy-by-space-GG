import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout, Sidebar, SubMenuBar } from '../components';
import { ShipDetailPanel } from '../components/ShipDetailPanel';
import { CompanyInfoPanel } from '../components/CompanyInfoPanel';
import { CrewCertificateTable } from '../components/CrewCertificate';
import { EditShipModal, DeleteShipConfirmationModal, AddShipModal } from '../components/Ships';
import { shipService } from '../services';
import api from '../services/api';
import { toast } from 'sonner';

const CrewCertificate = () => {
  const { language, user } = useAuth();
  const location = useLocation();
  
  // State
  const [selectedCategory] = useState('crew');
  const [selectedSubMenu, setSelectedSubMenu] = useState('crew_certificates');
  const [showShipModal, setShowShipModal] = useState(false);
  const [shipSearchQuery, setShipSearchQuery] = useState(\'\');
  const [showAddShipModal, setShowAddShipModal] = useState(false);
  const [showEditShipModal, setShowEditShipModal] = useState(false);
  const [showDeleteShipModal, setShowDeleteShipModal] = useState(false);
  const [ships, setShips] = useState([]);
  const [selectedShip, setSelectedShip] = useState(null);
  const [deleteShipData, setDeleteShipData] = useState(null);
  const [isDeletingShip, setIsDeletingShip] = useState(false);
  const [loading, setLoading] = useState(false);
  const [companyData, setCompanyData] = useState(null);

  // Fetch company data
  useEffect(() => {
    const fetchCompanyData = async () => {
      try {
        const response = await api.get('/api/company');
        console.log('Company data fetched:', response.data);
        setCompanyData(response.data);
      } catch (error) {
        console.error('Failed to fetch company data:', error);
      }
    };
    
    if (user) {
      fetchCompanyData();
    }
  }, [user]);

  // Fetch ships on mount and restore selected ship from localStorage
  useEffect(() => {
    fetchShips();
    
    // Restore selected ship from localStorage
    const savedShipId = localStorage.getItem('selectedShipId');
    if (savedShipId) {
      console.log('Found saved ship ID:', savedShipId);
    }
  }, []);

  // Restore selected ship after ships are loaded
  useEffect(() => {
    if (ships.length > 0 && !selectedShip) {
      const savedShipId = localStorage.getItem('selectedShipId');
      if (savedShipId) {
        const savedShip = ships.find(s => s.id === savedShipId);
        if (savedShip) {
          console.log('Restoring selected ship:', savedShip.name);
          setSelectedShip(savedShip);
        } else {
          localStorage.removeItem('selectedShipId');
        }
      }
    }
  }, [ships]);

  // Handle navigation from Add Ship - refresh when new ship is created
  useEffect(() => {
    if (location.state?.refresh) {
      console.log('Refreshing ship list after new ship creation:', location.state);
      fetchShips();
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const fetchShips = async () => {
    try {
      console.log('Fetching ships...');
      setLoading(true);
      const response = await shipService.getAllShips();
      console.log('Ships fetched successfully:', response);
      const data = response.data || response || [];
      
      if (!Array.isArray(data)) {
        console.error('Ships response is not an array:', data);
        setShips([]);
      } else {
        setShips(data);
      }
    } catch (error) {
      console.error('Failed to fetch ships:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách tàu' : 'Failed to load ships');
      setShips([]);
    } finally {
      console.log('Setting loading to false');
      setLoading(false);
    }
  };

  // Helper function to update selected ship and save to localStorage
  const updateSelectedShip = (ship) => {
    setSelectedShip(ship);
    if (ship) {
      localStorage.setItem('selectedShipId', ship.id);
      console.log('Saved ship to localStorage:', ship.name, ship.id);
    } else {
      localStorage.removeItem('selectedShipId');
      console.log('Removed ship from localStorage');
    }
  };
  
  // Handle ship filter change from CrewCertificateTable
  const handleShipFilterChange = (shipName) => {
    if (shipName === 'All' || shipName === '-') {
      // Clear ship selection
      updateSelectedShip(null);
    } else {
      // Find and select ship
      const ship = ships.find(s => s.name === shipName);
      if (ship) {
        updateSelectedShip(ship);
      }
    }
  };

  const handleAddRecord = () => {
    console.log('Add Ship button clicked from CrewCertificate');
    setShowAddShipModal(true);
  };

  const handleShipCreated = async (shipId, shipName) => {
    console.log('Ship created callback triggered:', shipId, shipName);
    setShowAddShipModal(false);
    await fetchShips();
    console.log('Ship list refreshed after creation');
  };

  const handleEditShip = (ship) => {
    setShowEditShipModal(true);
  };

  const handleShipUpdated = (updatedShip) => {
    setShips(ships.map(s => s.id === updatedShip.id ? updatedShip : s));
    updateSelectedShip(updatedShip);
    fetchShips();
    toast.success(language === 'vi' ? 'Cập nhật tàu thành công!' : 'Ship updated successfully!');
  };

  const handleShipUpdate = async (shipId) => {
    try {
      const response = await api.get(`/api/ships/${shipId}`);
      const updatedShip = response.data;
      
      setShips(ships.map(s => s.id === updatedShip.id ? updatedShip : s));
      updateSelectedShip(updatedShip);
    } catch (error) {
      console.error('Error refreshing ship data:', error);
      toast.error(language === 'vi' ? 'Không thể làm mới dữ liệu tàu' : 'Failed to refresh ship data');
    }
  };

  const handleDeleteShipClick = (ship) => {
    setDeleteShipData(ship);
    setShowDeleteShipModal(true);
  };

  const handleDeleteShip = async (shipId, deleteOption) => {
    try {
      setIsDeletingShip(true);
      
      const deleteWithGDrive = deleteOption === 'with_gdrive';
      
      toast.info(language === 'vi' 
        ? `Đang xóa tàu ${deleteShipData?.name}...`
        : `Deleting ship ${deleteShipData?.name}...`
      );

      // Call backend API with delete_google_drive_folder parameter
      const response = await shipService.delete(shipId, deleteWithGDrive);

      // Handle response
      if (response && response.data) {
        const result = response.data;
        
        // Check Google Drive deletion status if it was requested
        if (deleteWithGDrive && result.google_drive_deletion) {
          const gdriveStatus = result.google_drive_deletion;
          
          if (gdriveStatus.success) {
            toast.success(language === 'vi' 
              ? '✅ Đã xóa tàu và folder Google Drive thành công'
              : '✅ Ship and Google Drive folder deleted successfully'
            );
          } else {
            // Show warning if GDrive deletion failed but ship was deleted
            toast.warning(language === 'vi' 
              ? `⚠️ Đã xóa tàu nhưng có lỗi khi xóa folder Google Drive: ${gdriveStatus.message || 'Unknown error'}`
              : `⚠️ Ship deleted but Google Drive folder deletion failed: ${gdriveStatus.message || 'Unknown error'}`
            );
          }
        } else {
          // Success message for database deletion only
          toast.success(language === 'vi' 
            ? `✅ Đã xóa tàu "${deleteShipData?.name}" thành công`
            : `✅ Ship "${deleteShipData?.name}" deleted successfully`
          );
        }
      } else {
        // Fallback success message
        toast.success(language === 'vi' 
          ? `✅ Đã xóa tàu "${deleteShipData?.name}" thành công`
          : `✅ Ship "${deleteShipData?.name}" deleted successfully`
        );
      }

      await fetchShips();

      setShowDeleteShipModal(false);
      setShowEditShipModal(false);
      setDeleteShipData(null);
      
      if (selectedShip && selectedShip.id === shipId) {
        updateSelectedShip(null);
      }

    } catch (error) {
      console.error('Ship deletion error:', error);
      
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred';
      
      toast.error(language === 'vi' 
        ? `Không thể xóa tàu: ${errorMessage}`
        : `Failed to delete ship: ${errorMessage}`
      );
    } finally {
      setIsDeletingShip(false);
    }
  };

  // Handle submenu navigation
  const handleSubMenuChange = (submenuKey) => {
    setSelectedSubMenu(submenuKey);
    // Navigate to crew list if needed
    if (submenuKey === 'crew_list') {
      window.location.href = '/crew';
    }
  };

  return (
    <MainLayout
      sidebar={
        <Sidebar 
          selectedCategory={selectedCategory}
          onCategoryChange={(cat) => {
            const routes = {
              'ship_certificates': '/certificates',
              'crew': '/crew',
              'ism': '/ism-isps-mlc',
              'isps': '/isps',
              'mlc': '/mlc',
              'supplies': '/supplies'
            };
            if (routes[cat]) {
              window.location.href = routes[cat];
            }
          }}
          onAddRecord={handleAddRecord}
        />
      }
    >
      {/* Page Title */}
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-800">
          {language === 'vi' ? 'Quản lý chứng chỉ thuyền viên' : 'Crew Certificates Management'}
        </h1>
      </div>

      {/* Ship Detail Panel or Company Info Panel */}
      {selectedShip ? (
        <ShipDetailPanel
          ship={selectedShip}
          onClose={() => updateSelectedShip(null)}
          showEditButton={false}
          showShipParticular={true}
          onShipSelect={() => setShowShipModal(true)}
          onShipUpdate={handleShipUpdate}
        />
      ) : (
        <CompanyInfoPanel
          companyData={companyData}
          onClose={null}
        />
      )}

      {/* Ship Selection Modal */}
      {showShipModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => {
          setShowShipModal(false);
          setShipSearchQuery('');
        }}>
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold text-gray-800">
                  {language === 'vi' ? 'Chọn tàu' : 'Select Ship'}
                </h2>
                <button
                  onClick={() => {
                    setShowShipModal(false);
                    setShipSearchQuery('');
                  }}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              {/* Search Field */}
              <div className="relative">
                <input
                  type="text"
                  placeholder={language === 'vi' ? 'Tìm kiếm tên tàu, IMO...' : 'Search ship name, IMO...'}
                  value={shipSearchQuery}
                  onChange={(e) => setShipSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <svg
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {loading ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <p className="mt-2 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
                </div>
              ) : (() => {
                // Filter and sort ships
                const filteredShips = ships
                  .filter(ship => {
                    if (!shipSearchQuery.trim()) return true;
                    const query = shipSearchQuery.toLowerCase();
                    return (
                      ship.name?.toLowerCase().includes(query) ||
                      ship.imo?.toLowerCase().includes(query) ||
                      ship.flag?.toLowerCase().includes(query)
                    );
                  })
                  .sort((a, b) => (a.name || '').localeCompare(b.name || ''));
                
                return filteredShips.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p>{language === 'vi' ? 'Không tìm thấy tàu nào' : 'No ships found'}</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {filteredShips.map(ship => (
                      <button
                        key={ship.id}
                        onClick={() => {
                          updateSelectedShip(ship);
                          setShowShipModal(false);
                          setShipSearchQuery('');
                        }}
                        className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                          selectedShip?.id === ship.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                        }`}
                      >
                        <div className="font-semibold text-gray-800">{ship.name}</div>
                        <div className="text-sm text-gray-600 mt-1">
                          {ship.imo && `IMO: ${ship.imo}`}
                          {ship.flag && ` • ${language === 'vi' ? 'Cờ' : 'Flag'}: ${ship.flag}`}
                        </div>
                      </button>
                    ))}
                  </div>
                );
              })()}
            </div>
          </div>
        </div>
      )}

      {/* SubMenu Bar */}
      <SubMenuBar 
        selectedCategory={selectedCategory}
        selectedSubMenu={selectedSubMenu}
        onSubMenuChange={handleSubMenuChange}
      />
      
      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-md p-6">
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
          </div>
        ) : (
          /* Crew Certificate Content Section */
          <div>
            <CrewCertificateTable 
              selectedShip={selectedShip}
              ships={ships}
              onShipFilterChange={handleShipFilterChange}
              onShipSelect={updateSelectedShip}
              initialCrewFilter={location.state?.filterCrewName || null}
            />
          </div>
        )}
      </div>

      {/* Add Ship Modal */}
      {showAddShipModal && (
        <AddShipModal
          onClose={() => setShowAddShipModal(false)}
          onSuccess={handleShipCreated}
        />
      )}

      {/* Edit Ship Modal */}
      {showEditShipModal && selectedShip && (
        <EditShipModal
          ship={selectedShip}
          onClose={() => setShowEditShipModal(false)}
          onUpdate={handleShipUpdated}
          onDelete={() => handleDeleteShipClick(selectedShip)}
        />
      )}

      {/* Delete Ship Confirmation Modal */}
      {showDeleteShipModal && deleteShipData && (
        <DeleteShipConfirmationModal
          ship={deleteShipData}
          onConfirm={(deleteOption) => handleDeleteShip(deleteShipData.id, deleteOption)}
          onCancel={() => {
            setShowDeleteShipModal(false);
            setDeleteShipData(null);
          }}
          isDeleting={isDeletingShip}
        />
      )}
    </MainLayout>
  );
};

export default CrewCertificate;
