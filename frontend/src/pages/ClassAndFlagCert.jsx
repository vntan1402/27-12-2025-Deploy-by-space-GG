/**
 * Class And Flag Cert Page
 * Main page for Class & Flag Cert category
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout, Sidebar, SubMenuBar } from '../components/Layout';
import { ShipDetailPanel } from '../components/ShipDetailPanel';
import { shipService } from '../services';
import { toast } from 'sonner';

const ClassAndFlagCert = () => {
  const { language } = useAuth();
  
  // State
  const [selectedCategory] = useState('ship_certificates');
  const [selectedSubMenu, setSelectedSubMenu] = useState('certificates');
  const [showShipModal, setShowShipModal] = useState(false);
  const [ships, setShips] = useState([]);
  const [selectedShip, setSelectedShip] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch ships on mount
  useEffect(() => {
    fetchShips();
  }, []);

  const fetchShips = async () => {
    try {
      setLoading(true);
      const response = await shipService.getAllShips();
      const data = response.data; // Extract data from axios response
      setShips(data);
      
      // Auto-select first ship if available
      if (data.length > 0 && !selectedShip) {
        setSelectedShip(data[0]);
      }
    } catch (error) {
      console.error('Failed to fetch ships:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách tàu' : 'Failed to load ships');
    } finally {
      setLoading(false);
    }
  };

  const handleAddRecord = () => {
    toast.info(language === 'vi' ? 'Chức năng thêm record sẽ được triển khai trong Phase 4' : 'Add record feature will be implemented in Phase 4');
  };

  const handleEditShip = (ship) => {
    toast.info(language === 'vi' ? 'Chức năng sửa tàu sẽ được triển khai trong Phase 4' : 'Edit ship feature will be implemented in Phase 4');
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
      {/* Page Title */}
      <div className="mb-4">
        <h1 className="text-3xl font-bold text-gray-800">
          {language === 'vi' ? 'CLASS & FLAG CERT' : 'CLASS & FLAG CERT'}
        </h1>
      </div>

      {/* Ship Detail Panel */}
      {selectedShip && (
        <ShipDetailPanel
          ship={selectedShip}
          onClose={() => setSelectedShip(null)}
          onEditShip={handleEditShip}
          showShipParticular={true}
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
          <div className="text-center py-12 text-gray-500">
            <div className="text-6xl mb-4">🚢</div>
            <p className="text-lg">{language === 'vi' ? 'Vui lòng chọn tàu để xem thông tin' : 'Please select a ship to view information'}</p>
          </div>
        ) : (
          <div>
            <h3 className="text-xl font-semibold mb-4">
              {language === 'vi' ? 'Danh sách chứng chỉ' : 'Certificate List'}
            </h3>
            <p className="text-gray-600">
              {language === 'vi' 
                ? 'Nội dung danh sách chứng chỉ sẽ được triển khai trong Phase 4' 
                : 'Certificate list content will be implemented in Phase 4'
              }
            </p>
          </div>
        )}
      </div>
    </MainLayout>
  );
};

export default ClassAndFlagCert;
