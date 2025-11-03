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
      const response = await companyService.getAll();
      const companies = response.data || response || [];
      
      if (!Array.isArray(companies)) {
        console.error('Companies response is not an array:', companies);
        return;
      }
      
      // Find company by name (user.company is the company name)
      const userCompany = companies.find(c => 
        c.name_vn === user.company || 
        c.name_en === user.company || 
        c.name === user.company
      );
      
      if (userCompany) {
        setCompanyData(userCompany);
      }
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
              onClick={() => {
                // Show ship selection modal (to be implemented)
                toast.info(language === 'vi' ? 'Chức năng chọn tàu sẽ được triển khai' : 'Ship selection feature will be implemented');
              }}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-all flex items-center gap-2 whitespace-nowrap"
            >
              <span className="text-xl">🚢</span>
              {language === 'vi' ? 'Chọn tàu' : 'Select Ship'}
            </button>
          </div>
        )}
      </div>

      {/* Show CompanyInfoPanel if no ship is selected, otherwise show ShipDetailPanel */}
      {!selectedShip ? (
        <CompanyInfoPanel companyData={companyData} />
      ) : (
        <ShipDetailPanel 
          ship={selectedShip}
          onEdit={() => toast.info(language === 'vi' ? 'Chức năng chỉnh sửa tàu sẽ được triển khai' : 'Edit ship feature will be implemented')}
          onDelete={() => toast.info(language === 'vi' ? 'Chức năng xóa tàu sẽ được triển khai' : 'Delete ship feature will be implemented')}
          onShipUpdate={(updatedShip) => setSelectedShip(updatedShip)}
        />
      )}

      {/* SubMenuBar */}
      <SubMenuBar
        selectedCategory="ism"
        selectedSubMenu={selectedSubMenu}
        onSubMenuChange={handleSubMenuChange}
      />

      {/* Content Area based on selected submenu */}
      <div className="mt-6">
        <div className="bg-white rounded-lg shadow-md p-6">
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
        </div>
      </div>
    </MainLayout>
  );
};

export default IsmIspsMLc;
