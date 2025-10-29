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
    <MainLayout>
      <div className="flex h-full">
        <Sidebar 
          selectedCategory={selectedCategory}
          onCategoryChange={handleCategoryChange}
          ships={ships}
          selectedShip={selectedShip}
          onShipSelect={handleShipSelect}
          onAddRecord={handleAddRecord}
        />
        
        <div className="flex-1 flex flex-col">
          <SubMenuBar 
            selectedCategory={selectedCategory}
            selectedSubMenu={selectedSubMenu}
            onSubMenuChange={setSelectedSubMenu}
          />
          
          <main className="flex-1 p-6 bg-gray-50">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">
                {language === 'vi' ? 'Chào mừng đến hệ thống quản lý tàu' : 'Welcome to Ship Management System'}
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-semibold text-blue-900 mb-2">
                    👥 {language === 'vi' ? 'Quản lý thuyền viên' : 'Crew Management'}
                  </h3>
                  <p className="text-sm text-blue-800">
                    {language === 'vi' ? 'Quản lý thông tin thuyền viên, hợp đồng và chứng chỉ' : 'Manage crew information, contracts and certificates'}
                  </p>
                </div>
                
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h3 className="font-semibold text-green-900 mb-2">
                    🚢 {language === 'vi' ? 'Quản lý tàu' : 'Ship Management'}
                  </h3>
                  <p className="text-sm text-green-800">
                    {language === 'vi' ? 'Thông tin tàu, bảo trì và kiểm định' : 'Ship information, maintenance and inspections'}
                  </p>
                </div>
                
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <h3 className="font-semibold text-purple-900 mb-2">
                    📊 {language === 'vi' ? 'Báo cáo' : 'Reports'}
                  </h3>
                  <p className="text-sm text-purple-800">
                    {language === 'vi' ? 'Báo cáo và thống kê hệ thống' : 'System reports and analytics'}
                  </p>
                </div>
              </div>
              
              {selectedShip && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-semibold text-gray-800 mb-2">
                    {language === 'vi' ? 'Tàu được chọn:' : 'Selected Ship:'}
                  </h3>
                  <div className="text-sm text-gray-600">
                    <p><strong>{language === 'vi' ? 'Tên:' : 'Name:'}</strong> {selectedShip.name}</p>
                    <p><strong>{language === 'vi' ? 'Cờ:' : 'Flag:'}</strong> {selectedShip.flag}</p>
                    <p><strong>{language === 'vi' ? 'Hội đăng kiểm:' : 'Class Society:'}</strong> {selectedShip.class_society}</p>
                  </div>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>
    </MainLayout>
  );
};

export default HomePage;
