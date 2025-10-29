import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout, Sidebar, SubMenuBar } from '../components/Layout';

const HomePage = () => {
  const { language } = useAuth();
  
  // State management
  const [selectedCategory, setSelectedCategory] = useState('crew');
  const [selectedSubMenu, setSelectedSubMenu] = useState('crew_list');
  const [ships, setShips] = useState([
    // Mock data for demonstration
    { id: '1', name: 'PACIFIC OCEAN', flag: 'Panama', class_society: 'BV' },
    { id: '2', name: 'ATLANTIC STAR', flag: 'Liberia', class_society: 'DNV' },
    { id: '3', name: 'INDIAN PEARL', flag: 'Marshall Islands', class_society: 'ABS' },
  ]);
  const [selectedShip, setSelectedShip] = useState(null);

  const handleCategoryChange = (category) => {
    setSelectedCategory(category);
    // Reset sub-menu when category changes
    setSelectedSubMenu(null);
  };

  const handleShipSelect = (ship) => {
    setSelectedShip(ship);
  };

  const handleAddRecord = () => {
    alert(language === 'vi' ? 'Chức năng thêm tàu sẽ được triển khai trong Phase 4' : 'Add ship feature will be implemented in Phase 4');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              {language === 'vi' ? 'Hệ thống quản lý tàu' : 'Ship Management System'}
            </h1>
            <p className="text-sm text-gray-600">Frontend V2.0.0</p>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={toggleLanguage}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              {language === 'vi' ? '🇬🇧 English' : '🇻🇳 Tiếng Việt'}
            </button>

            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">
                {user?.username || 'User'}
              </span>
              <button
                onClick={logout}
                className="px-4 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600"
              >
                {language === 'vi' ? 'Đăng xuất' : 'Logout'}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-md p-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-800 mb-4">
              {language === 'vi' ? '🎉 Chào mừng đến Frontend V2!' : '🎉 Welcome to Frontend V2!'}
            </h2>
            
            <div className="space-y-4 text-left max-w-2xl mx-auto mt-8">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">
                  ✅ {language === 'vi' ? 'Hoàn thành Phase 0' : 'Phase 0 Complete'}
                </h3>
                <ul className="text-sm text-blue-800 space-y-1 ml-4">
                  <li>• {language === 'vi' ? 'Frontend V1 đã backup' : 'Frontend V1 backed up'}</li>
                  <li>• {language === 'vi' ? 'Frontend V2 với cấu trúc mới' : 'Frontend V2 with new architecture'}</li>
                  <li>• {language === 'vi' ? 'Auth system hoạt động' : 'Auth system working'}</li>
                  <li>• {language === 'vi' ? 'TailwindCSS đã setup' : 'TailwindCSS configured'}</li>
                  <li>• {language === 'vi' ? 'API service layer sẵn sàng' : 'API service layer ready'}</li>
                </ul>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="font-semibold text-yellow-900 mb-2">
                  🚧 {language === 'vi' ? 'Tiếp theo' : 'Next Steps'}
                </h3>
                <ul className="text-sm text-yellow-800 space-y-1 ml-4">
                  <li>• Phase 1: {language === 'vi' ? 'Extract utilities từ V1' : 'Extract utilities from V1'}</li>
                  <li>• Phase 2: {language === 'vi' ? 'Tạo API service layer' : 'Create API service layer'}</li>
                  <li>• Phase 3: {language === 'vi' ? 'Tạo custom hooks' : 'Create custom hooks'}</li>
                  <li>• Phase 4-7: {language === 'vi' ? 'Migrate từng feature' : 'Migrate features'}</li>
                </ul>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-semibold text-green-900 mb-2">
                  📂 {language === 'vi' ? 'Cấu trúc mới' : 'New Structure'}
                </h3>
                <div className="text-sm text-green-800 font-mono">
                  <div>/src</div>
                  <div className="ml-4">├── components/ (UI components)</div>
                  <div className="ml-4">├── features/ (Feature modules)</div>
                  <div className="ml-4">├── hooks/ (Custom hooks)</div>
                  <div className="ml-4">├── services/ (API services)</div>
                  <div className="ml-4">├── utils/ (Utilities)</div>
                  <div className="ml-4">├── contexts/ (React contexts)</div>
                  <div className="ml-4">└── pages/ (Page components)</div>
                </div>
              </div>

              <div className="text-center mt-8">
                <p className="text-gray-600">
                  {language === 'vi' 
                    ? 'Features sẽ được migrate từ V1 sang V2 dần dần...' 
                    : 'Features will be migrated from V1 to V2 gradually...'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default HomePage;
