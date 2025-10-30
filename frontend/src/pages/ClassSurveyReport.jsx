/**
 * Class Survey Report Page
 * Similar structure to ClassAndFlagCert but without certificate list
 * Shows Class Survey Report List (placeholder) instead
 */
import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout, Sidebar, SubMenuBar } from '../components';
import { ClassSurveyReportList } from '../components/ClassSurveyReport';
import { ShipDetailPanel } from '../components/ShipDetailPanel';
import { EditShipModal, DeleteShipConfirmationModal, AddShipModal } from '../components/Ships';
import { shipService } from '../services';
import api from '../services/api';
import { toast } from 'sonner';
import { shortenClassSociety } from '../utils/shipHelpers';

const ClassSurveyReport = () => {
  const { language, user } = useAuth();
  const location = useLocation();
  
  // State
  const [selectedCategory] = useState('ship_certificates');
  const [selectedSubMenu, setSelectedSubMenu] = useState('class_survey');
  const [showShipModal, setShowShipModal] = useState(false);
  const [showAddShipModal, setShowAddShipModal] = useState(false);
  const [showEditShipModal, setShowEditShipModal] = useState(false);
  const [showDeleteShipModal, setShowDeleteShipModal] = useState(false);
  const [ships, setShips] = useState([]);
  const [selectedShip, setSelectedShip] = useState(null);
  const [deleteShipData, setDeleteShipData] = useState(null);
  const [isDeletingShip, setIsDeletingShip] = useState(false);
  const [loading, setLoading] = useState(false);

  // Fetch ships on mount
  useEffect(() => {
    fetchShips();
  }, []);

  // Handle navigation from Add Ship - refresh when new ship is created
  useEffect(() => {
    if (location.state?.refresh) {
      console.log('Refreshing ship list after new ship creation:', location.state);
      fetchShips();
      
      // Clear the location state to prevent re-triggering on subsequent renders
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
      
      // Ensure data is array
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

  const handleAddRecord = () => {
    console.log('Add Ship button clicked from ClassSurveyReport');
    setShowAddShipModal(true);
  };

  const handleShipCreated = async (shipId, shipName) => {
    console.log('Ship created callback triggered:', shipId, shipName);
    // Close modal
    setShowAddShipModal(false);
    // Refresh ship list to show new ship
    await fetchShips();
    console.log('Ship list refreshed after creation');
  };

  const handleEditShip = (ship) => {
    setShowEditShipModal(true);
  };

  const handleShipUpdated = (updatedShip) => {
    // Update ships list
    setShips(ships.map(s => s.id === updatedShip.id ? updatedShip : s));
    // Update selected ship
    setSelectedShip(updatedShip);
    // Refresh ships list
    fetchShips();
    toast.success(language === 'vi' ? 'Cập nhật tàu thành công!' : 'Ship updated successfully!');
  };

  // Handle ship update after recalculation
  const handleShipUpdate = async (shipId) => {
    try {
      const response = await api.get(`/api/ships/${shipId}`);
      const updatedShip = response.data;
      
      // Update ships list
      setShips(ships.map(s => s.id === updatedShip.id ? updatedShip : s));
      // Update selected ship
      setSelectedShip(updatedShip);
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
      
      toast.info(language === 'vi' 
        ? `Đang xóa tàu ${deleteShipData?.name}...`
        : `Deleting ship ${deleteShipData?.name}...`
      );

      // Delete ship from database
      const response = await shipService.delete(shipId);

      // If user chose to delete Google Drive folder, do it in background
      if (deleteOption === 'with_gdrive') {
        (async () => {
          try {
            const userCompanyId = user?.company || user?.company_id;
            
            if (userCompanyId && deleteShipData?.name) {
              toast.info(language === 'vi' 
                ? 'Đang xóa folder Google Drive...'
                : 'Deleting Google Drive folder...'
              );

              const gdriveResponse = await api.post(`/api/companies/${userCompanyId}/gdrive/delete-ship-folder`, {
                ship_name: deleteShipData.name
              });

              if (gdriveResponse && gdriveResponse.data) {
                if (gdriveResponse.data.success) {
                  toast.success(language === 'vi' 
                    ? 'Đã xóa folder Google Drive thành công'
                    : 'Google Drive folder deleted successfully'
                  );
                } else if (gdriveResponse.data.warning) {
                  toast.warning(language === 'vi' 
                    ? 'Folder Google Drive không tìm thấy (có thể đã được xóa trước đó)'
                    : 'Google Drive folder not found (may have been deleted previously)'
                  );
                }
              }
            }
          } catch (gdriveError) {
            console.error('Google Drive deletion error:', gdriveError);
            toast.warning(language === 'vi' 
              ? 'Đã xóa dữ liệu tàu nhưng có lỗi khi xóa folder Google Drive'
              : 'Ship data deleted but Google Drive folder deletion failed'
            );
          }
        })();
      }

      toast.success(language === 'vi' 
        ? `Đã xóa tàu "${deleteShipData?.name}" thành công`
        : `Ship "${deleteShipData?.name}" deleted successfully`
      );

      // Refresh ships list
      await fetchShips();

      // Close modals and reset states
      setShowDeleteShipModal(false);
      setShowEditShipModal(false);
      setDeleteShipData(null);
      
      // Clear selected ship if current ship was deleted
      if (selectedShip && selectedShip.id === shipId) {
        setSelectedShip(null);
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
    
    // Navigate to different pages based on submenu
    if (submenuKey === 'certificates') {
      window.location.href = '/certificates';
    }
    // Stay on this page if class_survey is selected (already here)
    // Add more routes for other submenus as needed
  };

  return (
    <MainLayout
      sidebar={
        <Sidebar 
          selectedCategory={selectedCategory}
          onCategoryChange={(cat) => {
            // Navigate to different pages based on category
            const routes = {
              'ship_certificates': '/certificates',
              'crew': '/crew',
              'ism': '/ism',
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
      {/* Page Title with Ship Select Button */}
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-800">
          {language === 'vi' ? 'CLASS SURVEY REPORT' : 'CLASS SURVEY REPORT'}
        </h1>
        
        {!selectedShip && (
          <div className="flex items-center gap-4">
            <p className="text-gray-600">
              {language === 'vi' ? 'Vui lòng chọn tàu để xem thông tin' : 'Please select a ship to view information'}
            </p>
            <button
              onClick={() => setShowShipModal(true)}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-all flex items-center gap-2 whitespace-nowrap"
            >
              <span>🚢</span>
              {language === 'vi' ? 'Chọn tàu' : 'Ship Select'}
            </button>
          </div>
        )}
      </div>

      {/* Ship Detail Panel */}
      {selectedShip && (
        <ShipDetailPanel
          ship={selectedShip}
          onClose={() => setSelectedShip(null)}
          onEditShip={handleEditShip}
          showShipParticular={true}
          onShipSelect={() => setShowShipModal(true)}
          onShipUpdate={handleShipUpdate}
        />
      )}

      {/* Ship Selection Modal */}
      {showShipModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowShipModal(false)}>
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-800">
                  {language === 'vi' ? 'Chọn tàu' : 'Select Ship'}
                </h2>
                <button
                  onClick={() => setShowShipModal(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {loading ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <p className="mt-2 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
                </div>
              ) : ships.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>{language === 'vi' ? 'Không có tàu nào' : 'No ships available'}</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {ships.map(ship => (
                    <button
                      key={ship.id}
                      onClick={() => {
                        setSelectedShip(ship);
                        setShowShipModal(false);
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
              )}
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
        ) : !selectedShip ? (
          /* Ship Cards Grid - Show all ships for selection */
          <div>
            <h3 className="text-xl font-semibold mb-6 text-gray-800">
              {language === 'vi' ? 'Chọn tàu để xem Class Survey Report' : 'Select a ship to view Class Survey Report'}
            </h3>
            
            {ships.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-6xl mb-4">🚢</div>
                <p className="text-lg">{language === 'vi' ? 'Không có tàu nào' : 'No ships available'}</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                {ships.map(ship => (
                  <div
                    key={ship.id}
                    onClick={() => setSelectedShip(ship)}
                    className="border-2 border-gray-200 rounded-lg p-4 hover:border-purple-500 hover:shadow-lg transition-all cursor-pointer bg-gradient-to-br from-white to-gray-50"
                  >
                    {/* Ship Icon */}
                    <div className="text-center mb-3">
                      <div className="text-3xl">🚢</div>
                    </div>
                    
                    {/* Ship Name */}
                    <h4 className="text-base font-bold text-gray-800 text-center mb-3 line-clamp-2 min-h-[3rem]">
                      {ship.name}
                    </h4>
                    
                    {/* Ship Details */}
                    <div className="space-y-1.5 text-sm">
                      {ship.imo && (
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600 text-xs">IMO:</span>
                          <span className="font-semibold text-gray-800 text-xs">{ship.imo}</span>
                        </div>
                      )}
                      {ship.flag && (
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600 text-xs">{language === 'vi' ? 'Cờ:' : 'Flag:'}</span>
                          <span className="font-semibold text-gray-800 text-xs truncate ml-1">{ship.flag}</span>
                        </div>
                      )}
                      {ship.class_society && (
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600 text-xs">{language === 'vi' ? 'Đăng kiểm:' : 'Class Society:'}</span>
                          <span className="font-semibold text-gray-800 text-xs truncate ml-1">{shortenClassSociety(ship.class_society)}</span>
                        </div>
                      )}
                      {ship.built_year && (
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600 text-xs">{language === 'vi' ? 'Năm:' : 'Year:'}</span>
                          <span className="font-semibold text-gray-800 text-xs">{ship.built_year}</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Select Button */}
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <button
                        className="w-full py-1.5 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded font-medium transition-all"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedShip(ship);
                        }}
                      >
                        {language === 'vi' ? 'Chọn' : 'Select'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          /* Class Survey Report List Section - Placeholder */
          <ClassSurveyReportList />
        )}
      </div>

      {/* Add Ship Modal */}
      <AddShipModal 
        isOpen={showAddShipModal}
        onClose={() => {
          console.log('Closing Add Ship modal');
          setShowAddShipModal(false);
        }}
        onShipCreated={handleShipCreated}
      />

      {/* Edit Ship Modal */}
      {showEditShipModal && selectedShip && (
        <EditShipModal
          isOpen={showEditShipModal}
          onClose={() => setShowEditShipModal(false)}
          ship={selectedShip}
          onShipUpdated={handleShipUpdated}
          onDeleteShip={handleDeleteShipClick}
        />
      )}

      {/* Delete Ship Confirmation Modal */}
      {showDeleteShipModal && deleteShipData && (
        <DeleteShipConfirmationModal
          isOpen={showDeleteShipModal}
          onClose={() => {
            setShowDeleteShipModal(false);
            setDeleteShipData(null);
          }}
          ship={deleteShipData}
          onConfirm={handleDeleteShip}
          isDeleting={isDeletingShip}
        />
      )}
    </MainLayout>
  );
};

export default ClassSurveyReport;
