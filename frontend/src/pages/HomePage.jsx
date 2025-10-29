import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout, Sidebar, SubMenuBar } from '../components/Layout';

const HomePage = () => {
  const { language } = useAuth();
  
  // State management
  const [selectedCategory, setSelectedCategory] = useState('ship_certificates');
  const [selectedSubMenu, setSelectedSubMenu] = useState('certificates');

  const handleCategoryChange = (category) => {
    setSelectedCategory(category);
    // Reset sub-menu when category changes
    setSelectedSubMenu(null);
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
          ships={ships}
          onShipSelect={handleShipSelect}
          onAddRecord={handleAddRecord}
        />
      }
    >
      {/* SubMenu Bar */}
      <SubMenuBar 
        selectedCategory={selectedCategory}
        selectedSubMenu={selectedSubMenu}
        onSubMenuChange={setSelectedSubMenu}
      />
      
      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          {language === 'vi' ? 'Chào mừng đến hệ thống quản lý tàu biển' : 'Welcome to Ship Management System'}
        </h2>
        
        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
            <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
              <span className="text-2xl">👥</span>
              {language === 'vi' ? 'Quản lý thuyền viên' : 'Crew Management'}
            </h3>
            <p className="text-sm text-blue-800">
              {language === 'vi' ? 'Quản lý thông tin thuyền viên, hợp đồng và chứng chỉ' : 'Manage crew information, contracts and certificates'}
            </p>
          </div>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
            <h3 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
              <span className="text-2xl">🚢</span>
              {language === 'vi' ? 'Quản lý tàu' : 'Ship Management'}
            </h3>
            <p className="text-sm text-green-800">
              {language === 'vi' ? 'Thông tin tàu, bảo trì và kiểm định' : 'Ship information, maintenance and inspections'}
            </p>
          </div>
          
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
            <h3 className="font-semibold text-purple-900 mb-2 flex items-center gap-2">
              <span className="text-2xl">📊</span>
              {language === 'vi' ? 'Báo cáo' : 'Reports'}
            </h3>
            <p className="text-sm text-purple-800">
              {language === 'vi' ? 'Báo cáo và thống kê hệ thống' : 'System reports and analytics'}
            </p>
          </div>
        </div>
        
        {/* Selected Ship Info */}
        {selectedShip && (
          <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
            <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
              </svg>
              {language === 'vi' ? 'Tàu được chọn' : 'Selected Ship'}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-600">{language === 'vi' ? 'Tên tàu:' : 'Ship Name:'}</span>
                <p className="font-semibold text-gray-800">{selectedShip.name}</p>
              </div>
              <div>
                <span className="text-gray-600">{language === 'vi' ? 'Quốc kỳ:' : 'Flag:'}</span>
                <p className="font-semibold text-gray-800">{selectedShip.flag}</p>
              </div>
              <div>
                <span className="text-gray-600">{language === 'vi' ? 'Hội đăng kiểm:' : 'Class Society:'}</span>
                <p className="font-semibold text-gray-800">{selectedShip.class_society}</p>
              </div>
            </div>
          </div>
        )}

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
              🚀 Layout Complete
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
