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
      const data = await shipService.getAllShips();
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

      {/* Ship Selector Dropdown */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {language === 'vi' ? 'Chọn tàu:' : 'Select Ship:'}
        </label>
        <select
          value={selectedShip?.id || ''}
          onChange={(e) => {
            const ship = ships.find(s => s.id === e.target.value);
            setSelectedShip(ship);
          }}
          className="w-full md:w-96 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="">{language === 'vi' ? 'Chọn tàu...' : 'Select a ship...'}</option>
          {ships.map(ship => (
            <option key={ship.id} value={ship.id}>
              {ship.name} {ship.imo ? `(IMO: ${ship.imo})` : ''}
            </option>
          ))}
        </select>
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
