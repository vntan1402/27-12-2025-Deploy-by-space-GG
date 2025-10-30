import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout, Sidebar } from '../components/Layout';
import AddShipModal from '../components/Ships/AddShipModal';
import { companyService } from '../services';

const HomePage = () => {
  const { language, user } = useAuth();
  
  // State management
  const [selectedCategory, setSelectedCategory] = useState('ship_certificates');
  const [companyLogo, setCompanyLogo] = useState(null);
  const [companyName, setCompanyName] = useState(null);
  const [showAddShipModal, setShowAddShipModal] = useState(false);
  const [modalKey, setModalKey] = useState(0); // Add key to force re-mount modal

  useEffect(() => {
    if (user && user.company) {
      fetchUserCompanyData();
    }
  }, [user, language]); // Add language dependency

  const fetchUserCompanyData = async () => {
    try {
      const companies = await companyService.getAll();
      
      // Find company by name (user.company is the company name)
      const userCompany = companies.find(c => 
        c.name_vn === user.company || 
        c.name_en === user.company || 
        c.name === user.company
      );
      
      if (userCompany) {
        // Set company logo if available
        if (userCompany.logo_url) {
          setCompanyLogo(userCompany.logo_url);
        } else {
          setCompanyLogo(null);
        }
        
        // Set company name (prefer Vietnamese name if available, fallback to English or name field)
        const displayName = language === 'vi' 
          ? (userCompany.name_vn || userCompany.name_en || userCompany.name)
          : (userCompany.name_en || userCompany.name_vn || userCompany.name);
        setCompanyName(displayName);
      } else {
        setCompanyLogo(null);
        setCompanyName(null);
      }
    } catch (error) {
      console.error('Failed to fetch user company data:', error);
      setCompanyLogo(null);
      setCompanyName(null);
    }
  };

  const handleCategoryChange = (category) => {
    setSelectedCategory(category);
  };

  const handleAddShip = () => {
    console.log('Add Ship button clicked');
    setShowAddShipModal(true);
  };

  const handleShipCreated = (shipId, shipName) => {
    // Navigate to certificates page where ship list is displayed
    navigate('/certificates', { 
      state: { 
        refresh: true, 
        newShipId: shipId,
        newShipName: shipName 
      } 
    });
  };

  const handleAddRecord = () => {
    alert(language === 'vi' ? 'Chức năng thêm record sẽ được triển khai trong Phase 4' : 'Add record feature will be implemented in Phase 4');
  };

  return (
    <MainLayout
      sidebar={
        <Sidebar
          selectedCategory={selectedCategory}
          onCategoryChange={handleCategoryChange}
          onAddRecord={handleAddShip}
        />
      }
    >
      {/* Add Ship Modal */}
      <AddShipModal 
        key={modalKey}
        isOpen={showAddShipModal}
        onClose={() => {
          console.log('Closing Add Ship modal');
          setShowAddShipModal(false);
        }}
        onShipCreated={handleShipCreated}
      />
      
      {/* Company Logo Banner */}
      {companyLogo ? (
        <div className="w-full h-96 bg-gray-50 rounded-lg flex items-center justify-center overflow-hidden relative mb-6 shadow-md">
          <img 
            src={companyLogo.startsWith('http') ? companyLogo : `${process.env.REACT_APP_BACKEND_URL}${companyLogo}`}
            alt="Company Logo"
            className="max-w-full max-h-full object-contain"
            onError={(e) => {
              console.error('Failed to load company logo:', e);
              e.target.style.display = 'none';
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-black/30 to-black/50 flex items-center justify-center">
            <div className="bg-black/50 backdrop-blur-sm text-white p-6 rounded-lg text-center">
              <h2 className="text-3xl font-bold mb-2">
                {language === 'vi' ? 'Chào mừng đến với' : 'Welcome to'}
              </h2>
              <p className="text-xl mb-3">
                {language === 'vi' ? 'Hệ thống quản lý tàu biển' : 'Ship Management System'}
              </p>
              {companyName && (
                <p className="text-2xl font-semibold text-blue-200">
                  {companyName}
                </p>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="w-full h-96 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg flex items-center justify-center mb-6 shadow-md border border-blue-100">
          <div className="text-center text-gray-600">
            <div className="text-7xl mb-4">🚢</div>
            <h2 className="text-3xl font-bold mb-3 text-gray-800">
              {language === 'vi' ? 'Hệ thống quản lý tàu biển' : 'Ship Management System'}
            </h2>
            {companyName && (
              <p className="text-2xl font-semibold mb-3 text-blue-600">
                {companyName}
              </p>
            )}
            <p className="text-lg mb-3 text-gray-700">
              {language === 'vi' ? 'Chào mừng bạn đến với hệ thống' : 'Welcome to the system'}
            </p>
            <p className="text-sm text-gray-500">
              {language === 'vi' ? 'Logo công ty sẽ hiển thị ở đây khi được tải lên' : 'Company logo will be displayed here when uploaded'}
            </p>
          </div>
        </div>
      )}
      
      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          {language === 'vi' ? 'Chào mừng đến hệ thống quản lý tàu biển' : 'Welcome to Ship Management System'}
        </h2>
        
        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
            <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
              <span className="text-2xl">📜</span>
              {language === 'vi' ? 'Class & Flag Cert' : 'Class & Flag Cert'}
            </h3>
            <p className="text-sm text-blue-800">
              {language === 'vi' ? 'Quản lý chứng chỉ tàu và tổ chức phân cấp' : 'Manage ship certificates and classification'}
            </p>
          </div>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
            <h3 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
              <span className="text-2xl">👥</span>
              {language === 'vi' ? 'Crew Records' : 'Crew Records'}
            </h3>
            <p className="text-sm text-green-800">
              {language === 'vi' ? 'Quản lý hồ sơ thuyền viên' : 'Manage crew records'}
            </p>
          </div>
          
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
            <h3 className="font-semibold text-purple-900 mb-2 flex items-center gap-2">
              <span className="text-2xl">⚓</span>
              {language === 'vi' ? 'ISM/ISPS/MLC' : 'ISM/ISPS/MLC'}
            </h3>
            <p className="text-sm text-purple-800">
              {language === 'vi' ? 'Quản lý hồ sơ ISM, ISPS và MLC' : 'Manage ISM, ISPS and MLC records'}
            </p>
          </div>
        </div>

        {/* Phase Progress Info */}
        <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg">
          <h3 className="font-semibold text-gray-800 mb-3">
            📊 {language === 'vi' ? 'Tiến độ phát triển Frontend V2' : 'Frontend V2 Development Progress'}
          </h3>
          <div className="flex flex-wrap gap-2">
            <span className="px-3 py-1 bg-green-500 text-white rounded-full text-xs font-semibold">
              ✅ Phase 0: Setup
            </span>
            <span className="px-3 py-1 bg-green-500 text-white rounded-full text-xs font-semibold">
              ✅ Phase 1: Utilities
            </span>
            <span className="px-3 py-1 bg-green-500 text-white rounded-full text-xs font-semibold">
              ✅ Phase 2: Services
            </span>
            <span className="px-3 py-1 bg-green-500 text-white rounded-full text-xs font-semibold">
              ✅ Phase 3: Hooks
            </span>
            <span className="px-3 py-1 bg-blue-500 text-white rounded-full text-xs font-semibold animate-pulse">
              🚀 Layout V1 Style Complete
            </span>
            <span className="px-3 py-1 bg-gray-300 text-gray-700 rounded-full text-xs font-semibold">
              ⏳ Phase 4: Ship Management
            </span>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default HomePage;
