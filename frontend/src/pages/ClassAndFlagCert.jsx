import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout, Sidebar, SubMenuBar, CertificateTable, CertificateFilters, CertificateActionButtons, AddShipCertificateModal } from '../components';
import { EditShipCertificateModal, DeleteShipCertificateModal } from '../components/ShipCertificates';
import { ShipDetailPanel } from '../components/ShipDetailPanel';
import { EditShipModal, DeleteShipConfirmationModal, AddShipModal } from '../components/Ships';
import { shipService, shipCertificateService } from '../services';
import api from '../services/api';
import { toast } from 'sonner';
import { shortenClassSociety } from '../utils/shipHelpers';
import { compareDates } from '../utils/dateHelpers';

const ClassAndFlagCert = () => {
  const { language, user } = useAuth();
  const location = useLocation();
  
  // State
  const [selectedCategory] = useState('ship_certificates');
  const [selectedSubMenu, setSelectedSubMenu] = useState('certificates');
  const [showShipModal, setShowShipModal] = useState(false);
  const [showAddShipModal, setShowAddShipModal] = useState(false);
  const [showEditShipModal, setShowEditShipModal] = useState(false);
  const [showDeleteShipModal, setShowDeleteShipModal] = useState(false);
  const [ships, setShips] = useState([]);
  const [selectedShip, setSelectedShip] = useState(null);
  const [deleteShipData, setDeleteShipData] = useState(null);
  const [isDeletingShip, setIsDeletingShip] = useState(false);
  const [loading, setLoading] = useState(false);

  // Certificate states
  const [certificates, setCertificates] = useState([]);
  const [certificatesLoading, setCertificatesLoading] = useState(false);
  const [selectedCertificates, setSelectedCertificates] = useState(new Set());
  const [showAddShipCertificateModal, setShowAddShipCertificateModal] = useState(false);
  const [showEditShipCertificateModal, setShowEditShipCertificateModal] = useState(false);
  const [showDeleteShipCertificateModal, setShowDeleteShipCertificateModal] = useState(false);
  const [editingCertificate, setEditingCertificate] = useState(null);
  const [deletingCertificate, setDeletingCertificate] = useState(null);
  
  // Filter states
  const [certificateFilters, setCertificateFilters] = useState({
    certificateType: 'all',
    status: 'all',
    search: '',
  });
  
  // Sort state
  const [certificateSort, setCertificateSort] = useState({
    column: 'cert_abbreviation',
    direction: 'asc',
  });
  
  // Action states
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isUpdatingSurveyTypes, setIsUpdatingSurveyTypes] = useState(false);
  const [isMultiCertProcessing, setIsMultiCertProcessing] = useState(false);
  
  // AI Config state
  const [aiConfig, setAiConfig] = useState(null);
  
  // Context menu state (for right-click actions)
  const [contextMenu, setContextMenu] = useState(null);
  const [surveyTypeContextMenu, setSurveyTypeContextMenu] = useState(null);

  // Fetch ships on mount
  useEffect(() => {
    fetchShips();
    fetchAiConfig();
  }, []);

  // Fetch AI Config
  const fetchAiConfig = async () => {
    try {
      const response = await api.get('/api/ai-config');
      if (response.data && response.data.length > 0) {
        // Use first active config
        const activeConfig = response.data.find(config => config.is_active) || response.data[0];
        setAiConfig(activeConfig);
      }
    } catch (error) {
      console.error('Error fetching AI config:', error);
      // Don't show error toast, just log it
    }
  };

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
      const data = response.data || response || []; // Handle different response formats
      
      // Ensure data is array
      if (!Array.isArray(data)) {
        console.error('Ships response is not an array:', data);
        setShips([]);
      } else {
        setShips(data);
      }
      
      // Don't auto-select, let user choose via Ship Select button
      // If no ship selected and ships available, could optionally show modal
      // setShowShipModal(true); // Uncomment to auto-show modal
    } catch (error) {
      console.error('Failed to fetch ships:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách tàu' : 'Failed to load ships');
      setShips([]); // Set empty array on error
    } finally {
      console.log('Setting loading to false');
      setLoading(false);
    }
  };

  // ===== CERTIFICATE FUNCTIONS =====
  
  // Fetch certificates for selected ship
  const fetchCertificates = async (shipId) => {
    if (!shipId) {
      setCertificates([]);
      return;
    }
    
    try {
      setCertificatesLoading(true);
      const response = await api.get(`/api/ships/${shipId}/certificates`);
      const data = response.data || [];
      setCertificates(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch certificates:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách chứng chỉ' : 'Failed to load certificates');
      setCertificates([]);
    } finally {
      setCertificatesLoading(false);
    }
  };

  // Fetch certificates when ship is selected
  useEffect(() => {
    if (selectedShip?.id) {
      fetchCertificates(selectedShip.id);
    } else {
      setCertificates([]);
    }
  }, [selectedShip?.id]);

  // Get unique certificate types for filter dropdown
  const getUniqueCertificateTypes = () => {
    const types = new Set();
    certificates.forEach(cert => {
      if (cert.cert_type) types.add(cert.cert_type);
    });
    return Array.from(types).sort();
  };

  // Get certificate status
  const getCertificateStatus = (cert) => {
    if (!cert.valid_date) return 'Unknown';
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const validDate = new Date(cert.valid_date);
    validDate.setHours(0, 0, 0, 0);
    
    if (validDate < today) return 'Expired';
    
    const diffTime = validDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays <= 30) return 'Over Due';
    return 'Valid';
  };

  // Apply filters and sort to certificates
  const getFilteredCertificates = () => {
    let filtered = [...certificates];

    // Apply certificate type filter
    if (certificateFilters.certificateType !== 'all') {
      filtered = filtered.filter(cert => cert.cert_type === certificateFilters.certificateType);
    }

    // Apply status filter
    if (certificateFilters.status !== 'all') {
      filtered = filtered.filter(cert => getCertificateStatus(cert) === certificateFilters.status);
    }

    // Apply search filter
    if (certificateFilters.search) {
      const searchLower = certificateFilters.search.toLowerCase();
      filtered = filtered.filter(cert => 
        (cert.cert_name && cert.cert_name.toLowerCase().includes(searchLower)) ||
        (cert.cert_abbreviation && cert.cert_abbreviation.toLowerCase().includes(searchLower)) ||
        (cert.cert_no && cert.cert_no.toLowerCase().includes(searchLower))
      );
    }

    // Apply sorting
    if (certificateSort.column) {
      filtered.sort((a, b) => {
        let aVal = a[certificateSort.column];
        let bVal = b[certificateSort.column];

        // Handle date sorting
        if (['issue_date', 'valid_date', 'last_endorse', 'next_survey'].includes(certificateSort.column)) {
          return compareDates(aVal, bVal) * (certificateSort.direction === 'asc' ? 1 : -1);
        }

        // Handle string sorting
        if (typeof aVal === 'string') aVal = aVal.toLowerCase();
        if (typeof bVal === 'string') bVal = bVal.toLowerCase();

        if (aVal < bVal) return certificateSort.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return certificateSort.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  };

  // Handle certificate sort
  const handleCertificateSort = (column) => {
    setCertificateSort(prev => ({
      column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  // Handle certificate selection
  const handleSelectCertificate = (certId) => {
    setSelectedCertificates(prev => {
      const newSet = new Set(prev);
      if (newSet.has(certId)) {
        newSet.delete(certId);
      } else {
        newSet.add(certId);
      }
      return newSet;
    });
  };

  // Handle select all certificates
  const handleSelectAllCertificates = (checked) => {
    if (checked) {
      const allIds = getFilteredCertificates().map(cert => cert.id);
      setSelectedCertificates(new Set(allIds));
    } else {
      setSelectedCertificates(new Set());
    }
  };

  // Handle certificate double click - open PDF
  const handleCertificateDoubleClick = async (cert) => {
    if (!cert.google_drive_file_id) {
      toast.warning(language === 'vi' ? 'Chứng chỉ chưa có file đính kèm' : 'Certificate has no attached file');
      return;
    }

    try {
      const response = await api.get(`/api/certificates/${cert.id}/file-link`);
      if (response.data?.file_link) {
        window.open(response.data.file_link, '_blank');
      } else {
        toast.error(language === 'vi' ? 'Không thể lấy link file' : 'Failed to get file link');
      }
    } catch (error) {
      console.error('Error opening certificate file:', error);
      toast.error(language === 'vi' ? 'Không thể mở file' : 'Failed to open file');
    }
  };

  // Handle certificate right click - context menu
  const handleCertificateRightClick = (e, cert) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      certificate: cert,
    });
  };

  // Handle survey type right click - quick edit
  const handleSurveyTypeRightClick = (e, certId, currentType) => {
    e.preventDefault();
    e.stopPropagation();
    setSurveyTypeContextMenu({
      x: e.clientX,
      y: e.clientY,
      certId,
      currentType,
    });
  };

  // Close context menus on click outside
  useEffect(() => {
    const handleClick = () => {
      setContextMenu(null);
      setSurveyTypeContextMenu(null);
    };
    
    if (contextMenu || surveyTypeContextMenu) {
      document.addEventListener('click', handleClick);
      return () => document.removeEventListener('click', handleClick);
    }
  }, [contextMenu, surveyTypeContextMenu]);

  // Handle refresh certificates
  const handleRefreshCertificates = async () => {
    if (!selectedShip?.id) return;
    
    setIsRefreshing(true);
    try {
      await fetchCertificates(selectedShip.id);
      toast.success(language === 'vi' ? 'Đã cập nhật danh sách chứng chỉ!' : 'Certificate list refreshed!');
    } catch (error) {
      console.error('Error refreshing certificates:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Handle update survey types (placeholder - implement based on V1 logic)
  const handleUpdateSurveyTypes = async () => {
    if (!selectedShip?.id) return;
    
    setIsUpdatingSurveyTypes(true);
    try {
      // TODO: Implement update survey types logic from V1
      toast.info(language === 'vi' ? 'Chức năng đang phát triển' : 'Feature under development');
    } catch (error) {
      console.error('Error updating survey types:', error);
      toast.error(language === 'vi' ? 'Không thể cập nhật' : 'Failed to update');
    } finally {
      setIsUpdatingSurveyTypes(false);
    }
  };

  // Handle upcoming survey check (placeholder)
  const handleUpcomingSurvey = () => {
    // TODO: Implement upcoming survey check from V1
    toast.info(language === 'vi' ? 'Chức năng đang phát triển' : 'Feature under development');
  };

  // Handle add certificate (placeholder)
  const handleAddShipCertificate = () => {
    if (!selectedShip) {
      toast.warning(language === 'vi' ? 'Vui lòng chọn tàu trước' : 'Please select a ship first');
      return;
    }
    setShowAddShipCertificateModal(true);
  };

  // Handle ship certificate success
  const handleShipCertificateSuccess = async () => {
    // Refresh certificate list
    if (selectedShip?.id) {
      await fetchCertificates(selectedShip.id);
    }
    toast.success(language === 'vi' ? '✅ Đã thêm certificate thành công!' : '✅ Certificate added successfully!');
  };

  const handleAddRecord = () => {
    console.log('Add Ship button clicked from ClassAndFlagCert');
    setShowAddShipModal(true);
  };

  const handleShipCreated = async (shipId, shipName) => {
    console.log('Ship created callback triggered:', shipId, shipName);
    // Close modal
    setShowAddShipModal(false);
    // Refresh ship list to show new ship
    await fetchShips();
    console.log('Ship list refreshed after creation');
    // Don't need to navigate - already on this page!
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
      
      // Show initial loading message
      toast.info(language === 'vi' 
        ? `Đang xóa tàu ${deleteShipData?.name}...`
        : `Deleting ship ${deleteShipData?.name}...`
      );

      // Step 1: Delete ship from database only (quick operation)
      const response = await shipService.delete(shipId);

      // Step 2: If user chose to delete Google Drive folder, do it in background
      if (deleteOption === 'with_gdrive') {
        // Don't await - let it run in background
        (async () => {
          try {
            // Get user's company ID for Google Drive operations
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

      // Success message for database deletion (immediate)
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
      
      // Navigate back to ship list if current ship was deleted
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
          {language === 'vi' ? 'CLASS & FLAG CERT' : 'CLASS & FLAG CERT'}
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
        onSubMenuChange={setSelectedSubMenu}
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
              {language === 'vi' ? 'Chọn tàu để xem thông tin chứng chỉ' : 'Select a ship to view certificate information'}
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
          /* Certificate List Section */
          <div>
            {/* Action Buttons */}
            <CertificateActionButtons
              language={language}
              selectedShip={selectedShip}
              selectedCertificatesCount={selectedCertificates.size}
              isUpdatingSurveyTypes={isUpdatingSurveyTypes}
              isMultiCertProcessing={isMultiCertProcessing}
              isRefreshing={isRefreshing}
              onUpdateSurveyTypes={handleUpdateSurveyTypes}
              onUpcomingSurvey={handleUpcomingSurvey}
              onAddCertificate={handleAddShipCertificate}
              onRefresh={handleRefreshCertificates}
            />

            {/* Certificate Filters */}
            <CertificateFilters
              filters={certificateFilters}
              onFilterChange={setCertificateFilters}
              certificateTypes={getUniqueCertificateTypes()}
              totalCount={certificates.length}
              filteredCount={getFilteredCertificates().length}
              language={language}
              linksFetching={false}
              linksReady={0}
            />

            {/* Certificate Table */}
            {certificatesLoading ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-2 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
              </div>
            ) : (
              <CertificateTable
                certificates={getFilteredCertificates()}
                language={language}
                selectedCertificates={selectedCertificates}
                onSelectCertificate={handleSelectCertificate}
                onSelectAllCertificates={handleSelectAllCertificates}
                onSort={handleCertificateSort}
                sortConfig={certificateSort}
                onDoubleClick={handleCertificateDoubleClick}
                onRightClick={handleCertificateRightClick}
                onSurveyTypeRightClick={handleSurveyTypeRightClick}
              />
            )}
          </div>
        )}
      </div>

      {/* Context Menu for Certificate Actions */}
      {contextMenu && (
        <div
          className="fixed bg-white shadow-lg rounded-lg py-2 z-50 border border-gray-200"
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
          <button
            onClick={() => {
              // TODO: Implement edit certificate
              toast.info(language === 'vi' ? 'Chức năng đang phát triển' : 'Feature under development');
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            {language === 'vi' ? 'Sửa' : 'Edit'}
          </button>
          <button
            onClick={() => {
              // TODO: Implement delete certificate
              toast.info(language === 'vi' ? 'Chức năng đang phát triển' : 'Feature under development');
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left hover:bg-gray-100 text-red-600 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            {language === 'vi' ? 'Xóa' : 'Delete'}
          </button>
        </div>
      )}

      {/* Survey Type Context Menu */}
      {surveyTypeContextMenu && (
        <div
          className="fixed bg-white shadow-lg rounded-lg py-2 z-50 border border-gray-200"
          style={{ top: surveyTypeContextMenu.y, left: surveyTypeContextMenu.x }}
        >
          {['Annual', 'Intermediate', 'Renewal', 'Special'].map(type => (
            <button
              key={type}
              onClick={() => {
                // TODO: Implement quick survey type edit
                toast.info(language === 'vi' ? 'Chức năng đang phát triển' : 'Feature under development');
                setSurveyTypeContextMenu(null);
              }}
              className="w-full px-4 py-2 text-left hover:bg-gray-100"
            >
              {type}
            </button>
          ))}
        </div>
      )}

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

      {/* Add Ship Certificate Modal */}
      <AddShipCertificateModal
        isOpen={showAddShipCertificateModal}
        onClose={() => setShowAddShipCertificateModal(false)}
        onSuccess={handleShipCertificateSuccess}
        selectedShip={selectedShip}
        allShips={ships}
        onShipChange={setSelectedShip}
        aiConfig={aiConfig}
      />
    </MainLayout>
  );
};

export default ClassAndFlagCert;
