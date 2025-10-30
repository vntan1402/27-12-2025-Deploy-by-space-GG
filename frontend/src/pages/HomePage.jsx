import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout, Sidebar } from '../components/Layout';

const HomePage = () => {
  const { language } = useAuth();
  
  // State management
  const [selectedCategory, setSelectedCategory] = useState('ship_certificates');

  const handleCategoryChange = (category) => {
    setSelectedCategory(category);
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
          onAddRecord={handleAddRecord}
        />
      }
    >
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
