/**
 * Sidebar Component
 * Container for category menu and ship selection
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { CategoryMenu } from './CategoryMenu';
import UserGuideModal from '../UserGuideModal';

export const Sidebar = ({
  selectedCategory,
  onCategoryChange,
  onAddRecord,
  showAddShipButton = false  // Default false - only show on Home and Class & Flag Cert pages
}) => {
  const { language, user, logout } = useAuth();
  const navigate = useNavigate();
  const [showUserGuide, setShowUserGuide] = useState(false);

  const t = {
    categoryTitle: language === 'vi' ? 'Management Categories' : 'Management Categories',
    userGuide: language === 'vi' ? 'Hướng dẫn' : 'User Guide',
    systemSettings: language === 'vi' ? 'System Settings' : 'System Settings',
    logout: language === 'vi' ? 'LOG OUT' : 'LOG OUT'
  };

  const handleSystemSettings = () => {
    navigate('/settings');
  };

  const handleLogout = () => {
    if (window.confirm(language === 'vi' ? 'Bạn có chắc muốn đăng xuất?' : 'Are you sure you want to logout?')) {
      logout();
      navigate('/login');
    }
  };

  // Check if user has access to System Settings
  const canAccessSettings = user?.role && ['manager', 'admin', 'super_admin', 'system_admin'].includes(user.role);

  return (
    <div className="bg-blue-600 rounded-xl shadow-lg p-4 text-white flex flex-col" style={{ height: 'calc(100vh - 120px)', overflow: 'visible' }}>
      <h3 className="text-lg font-semibold mb-6">
        {t.categoryTitle}
      </h3>

      <div className="flex-1" style={{ overflowY: 'auto', overflowX: 'visible' }}>
        <CategoryMenu
          selectedCategory={selectedCategory}
          onCategoryChange={onCategoryChange}
          onAddRecord={onAddRecord}
          showAddShipButton={showAddShipButton}
        />
      </div>

      {/* User Guide Button */}
      <div className="mt-4">
        <button
          onClick={() => setShowUserGuide(true)}
          className="w-full bg-green-600 hover:bg-green-700 text-white py-3 px-4 rounded-lg transition-all font-semibold flex items-center justify-center shadow-md"
        >
          <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
          </svg>
          {t.userGuide}
        </button>
      </div>

      {/* Home Button */}
      <div className="mt-2">
        <button
          onClick={() => navigate('/')}
          className="w-full bg-blue-700 hover:bg-blue-800 text-white py-3 px-4 rounded-lg transition-all font-semibold flex items-center justify-center shadow-md"
        >
          <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
          </svg>
          {language === 'vi' ? 'Trang chủ' : 'Home'}
        </button>
      </div>

      {/* Bottom Actions */}
      <div className="mt-6 pt-4 border-t border-blue-500 space-y-2">
        {canAccessSettings && (
          <button
            onClick={handleSystemSettings}
            className="w-full bg-blue-700 hover:bg-blue-800 text-white py-2 px-4 rounded-lg transition-all text-sm font-medium flex items-center justify-center"
          >
            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
            </svg>
            {t.systemSettings}
          </button>
        )}
        <button
          onClick={handleLogout}
          className="w-full bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg transition-all text-sm font-medium flex items-center justify-center"
        >
          <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clipRule="evenodd" />
          </svg>
          {t.logout}
        </button>
      </div>

      {/* User Guide Modal */}
      {showUserGuide && (
        <UserGuideModal onClose={() => setShowUserGuide(false)} />
      )}
    </div>
  );
};
