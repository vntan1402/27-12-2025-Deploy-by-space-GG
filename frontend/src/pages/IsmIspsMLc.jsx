import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout, Sidebar, SubMenuBar, CompanyInfoPanel } from '../components';
import { ShipDetailPanel } from '../components/ShipDetailPanel';
import { AddShipModal } from '../components/Ships';
import { shipService, companyService } from '../services';
import { toast } from 'sonner';

const IsmIspsMLc = () => {
  const { language, user } = useAuth();
  
  // State
  const [selectedCategory] = useState('ism');
  const [selectedSubMenu, setSelectedSubMenu] = useState('audit_certificate');
  const [showAddShipModal, setShowAddShipModal] = useState(false);
  const [showShipModal, setShowShipModal] = useState(false);
  const [ships, setShips] = useState([]);
  const [selectedShip, setSelectedShip] = useState(null);
  const [loading, setLoading] = useState(false);
  const [companyData, setCompanyData] = useState(null);

  // Fetch ships on mount and restore selected ship from localStorage
  useEffect(() => {
    fetchShips();
    fetchCompanyData();
    
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
          // Ship not found, clear localStorage
          localStorage.removeItem('selectedShipId');
        }
      }
    }
  }, [ships]);

  const fetchShips = async () => {
    try {
      setLoading(true);
      const response = await shipService.getAll();
      setShips(response.data || response || []);
    } catch (error) {
      console.error('Failed to fetch ships:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách tàu' : 'Failed to load ships');
    } finally {
      setLoading(false);
    }
  };

  const fetchCompanyData = async () => {
    try {
      const response = await companyService.getCompanyInfo();
      setCompanyData(response.data);
    } catch (error) {
      console.error('Failed to fetch company data:', error);
    }
  };

  const handleAddRecord = () => {
    setShowAddShipModal(true);
  };

  const handleShipCreated = (shipId, shipName) => {
    setShowAddShipModal(false);
    fetchShips();
    toast.success(language === 'vi' ? `Tàu ${shipName} đã được tạo` : `Ship ${shipName} created successfully`);
  };

  const handleShipSelect = (ship) => {
    setSelectedShip(ship);
    localStorage.setItem('selectedShipId', ship.id);
    setShowShipModal(false);
  };

  // Handle submenu navigation
  const handleSubMenuChange = (submenuKey) => {
    setSelectedSubMenu(submenuKey);
    // All submenus stay on this page for now
    console.log('Selected submenu:', submenuKey);
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
          showAddShipButton={false}
        />
      }
    >
      {/* Add Ship Modal */}
      <AddShipModal 
        isOpen={showAddShipModal}
        onClose={() => setShowAddShipModal(false)}
        onShipCreated={handleShipCreated}
      />

      {/* Page Title with Ship Select Button */}
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-800">
          {language === 'vi' ? 'ISM - ISPS - MLC' : 'ISM - ISPS - MLC'}
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
              <span className="text-xl">🚢</span>
              {language === 'vi' ? 'Chọn tàu' : 'Ship Select'}
            </button>
          </div>
        )}
      </div>

      {/* Company Info Panel - Show when no ship selected */}
      {!selectedShip && companyData && (
        <CompanyInfoPanel companyData={companyData} />
      )}

      {/* Ship Detail Panel - Show when ship is selected */}
      {selectedShip && (
        <ShipDetailPanel 
          ship={selectedShip}
          onClose={() => {
            setSelectedShip(null);
            localStorage.removeItem('selectedShipId');
          }}
          onEdit={() => toast.info(language === 'vi' ? 'Chức năng chỉnh sửa tàu sẽ được triển khai' : 'Edit ship feature will be implemented')}
          onDelete={() => toast.info(language === 'vi' ? 'Chức năng xóa tàu sẽ được triển khai' : 'Delete ship feature will be implemented')}
          onShipUpdate={(updatedShip) => setSelectedShip(updatedShip)}
          onShipSelect={() => setShowShipModal(true)}
        />
      )}

      {/* Ship Selection Modal */}
      {showShipModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowShipModal(false)}>
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-800">
                  {language === 'vi' ? 'Chọn tàu để xem thông tin chứng chỉ' : 'Select a ship to view certificate information'}
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
                <div className="grid grid-cols-2 gap-4">
                  {ships.map(ship => (
                    <div
                      key={ship.id}
                      className="border-2 border-gray-200 rounded-lg p-4 hover:border-purple-500 transition-all cursor-pointer"
                    >
                      <div className="text-center mb-4">
                        <div className="text-4xl mb-2">🚢</div>
                        <h3 className="font-bold text-lg text-gray-800">{ship.name}</h3>
                      </div>
                      <div className="space-y-1 text-sm mb-4">
                        <div className="flex justify-between">
                          <span className="text-gray-600">IMO:</span>
                          <span className="font-medium">{ship.imo || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">{language === 'vi' ? 'Cờ:' : 'Flag:' }</span>
                          <span className="font-medium">{ship.flag || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">{language === 'vi' ? 'Đẳng kiểm:' : 'Class Society:'}</span>
                          <span className="font-medium">{ship.class_society || '-'}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleShipSelect(ship)}
                        className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg font-medium transition-all"
                      >
                        {language === 'vi' ? 'Chọn' : 'Select'}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* SubMenuBar */}
      <SubMenuBar
        selectedCategory="ism"
        selectedSubMenu={selectedSubMenu}
        onSubMenuChange={handleSubMenuChange}
      />

      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-md p-6 mt-6">
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            <p className="mt-2 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
          </div>
        ) : !selectedShip ? (
          /* Ship Cards Grid - Show all ships for selection when no ship selected */
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
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {ships.map(ship => (
                  <div
                    key={ship.id}
                    className="border-2 border-gray-200 rounded-lg p-6 hover:border-purple-500 hover:shadow-lg transition-all cursor-pointer"
                    onClick={() => handleShipSelect(ship)}
                  >
                    <div className="text-center mb-4">
                      <div className="text-5xl mb-3">🚢</div>
                      <h4 className="font-bold text-xl text-gray-800">{ship.name}</h4>
                    </div>
                    <div className="space-y-2 text-sm">
                      {ship.imo && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">IMO:</span>
                          <span className="font-medium text-gray-800">{ship.imo}</span>
                        </div>
                      )}
                      {ship.flag && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">{language === 'vi' ? 'Cờ:' : 'Flag:'}</span>
                          <span className="font-medium text-gray-800">{ship.flag}</span>
                        </div>
                      )}
                      {ship.class_society && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">{language === 'vi' ? 'Đẳng kiểm:' : 'Class Society:'}</span>
                          <span className="font-medium text-gray-800">{ship.class_society}</span>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleShipSelect(ship);
                      }}
                      className="mt-4 w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg font-medium transition-all"
                    >
                      {language === 'vi' ? 'Chọn' : 'Select'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          /* Show submenu content when ship is selected */
          <div className="text-center py-12">
            <div className="text-6xl mb-4">
              {selectedSubMenu === 'audit_certificate' && '📜'}
              {selectedSubMenu === 'audit_report' && '📋'}
              {selectedSubMenu === 'approval_document' && '✅'}
              {selectedSubMenu === 'other_document' && '📄'}
            </div>
            <h3 className="text-2xl font-semibold text-gray-700 mb-2">
              {selectedSubMenu === 'audit_certificate' && (language === 'vi' ? 'Audit Certificate' : 'Audit Certificate')}
              {selectedSubMenu === 'audit_report' && (language === 'vi' ? 'Audit Report' : 'Audit Report')}
              {selectedSubMenu === 'approval_document' && (language === 'vi' ? 'Approval Document' : 'Approval Document')}
              {selectedSubMenu === 'other_document' && (language === 'vi' ? 'Other Document' : 'Other Document')}
            </h3>
            <p className="text-gray-500">
              {language === 'vi' 
                ? 'Chức năng này sẽ được triển khai trong các giai đoạn tiếp theo' 
                : 'This feature will be implemented in upcoming phases'}
            </p>
          </div>
        )}
      </div>
    </MainLayout>
  );
};

export default IsmIspsMLc;
