/**
 * Header Component
 * Extracted from App.js (lines 12886-12926)
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export const Header = () => {
  const { user, logout, language, toggleLanguage } = useAuth();
  const navigate = useNavigate();

  // Get role display name
  const getRoleDisplayName = (role) => {
    if (language === 'vi') {
      const roleMap = {
        'super_admin': 'Siêu quản trị',
        'admin': 'Quản trị viên',
        'manager': 'Cán bộ công ty',
        'editor': 'Sĩ quan',
        'viewer': 'Thuyền viên'
      };
      return roleMap[role] || role;
    }
    return role;
  };

  return (
    <header className="bg-white shadow-lg border-b border-blue-200">
      {/* V2 Indicator Badge - Top right corner */}
      <div className="absolute top-2 right-2 z-50">
        <span className="bg-gradient-to-r from-green-500 to-blue-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg animate-pulse">
          🚀 V2 MODULAR
        </span>
      </div>
      
      <div className="w-full px-4 py-4">
        <div className="flex justify-between items-center">
          {/* Left side - Logo & Title */}
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-gray-800">
              {language === 'vi' ? 'Hệ thống quản lí tàu biển' : 'Ship Management System'}
            </h1>
            <span className="text-blue-600 text-sm">
              {language === 'vi' ? 'Với sự hỗ trợ AI' : 'With AI Support'}
            </span>
            {/* V2 Badge */}
            <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-semibold border border-green-300">
              V2
            </span>
          </div>
          
          {/* Right side - Actions */}
          <div className="flex items-center space-x-4">
            {/* Language Toggle */}
            <button
              onClick={toggleLanguage}
              className="px-3 py-1 text-sm border border-gray-300 rounded-full hover:bg-gray-50 transition-all"
            >
              {language === 'en' ? 'VI' : 'EN'}
            </button>
            
            {/* User Info */}
            <span className="text-sm text-gray-600">
              {user?.full_name} ({getRoleDisplayName(user?.role)})
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
