import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export const Header = () => {
  const { user, logout, language, toggleLanguage } = useAuth();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const menuRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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
    return role?.replace('_', ' ').toUpperCase() || 'USER';
  };

  const handleLogout = () => {
    if (window.confirm(language === 'vi' ? 'Bạn có chắc muốn đăng xuất?' : 'Are you sure you want to logout?')) {
      logout();
      navigate('/login');
    }
  };

  // Get user initials for avatar
  const getUserInitials = () => {
    if (user?.full_name) {
      return user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    }
    return user?.username?.slice(0, 2).toUpperCase() || 'U';
  };

  return (
    <header className="bg-white shadow-lg border-b border-blue-200 sticky top-0 z-50">
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
            {/* Logo */}
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
              </svg>
            </div>

            {/* Title */}
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                {language === 'vi' ? 'Hệ thống quản lý tàu biển' : 'Ship Management System'}
              </h1>
              <p className="text-xs text-blue-600 flex items-center gap-2">
                <span>{language === 'vi' ? 'Với sự hỗ trợ AI' : 'With AI Support'}</span>
                <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded text-xs font-semibold border border-green-300">
                  V2
                </span>
              </p>
            </div>
          </div>

          {/* Right side - Actions */}
          <div className="flex items-center space-x-4">
            {/* Language Toggle */}
            <button
              onClick={toggleLanguage}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-all flex items-center gap-2"
              title={language === 'vi' ? 'Chuyển sang English' : 'Switch to Vietnamese'}
            >
              <span className="text-lg">{language === 'vi' ? '🇬🇧' : '🇻🇳'}</span>
              <span className="font-medium">{language === 'en' ? 'VI' : 'EN'}</span>
            </button>

            {/* User Menu Dropdown */}
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all border border-gray-200"
              >
                {/* User Avatar */}
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                  {getUserInitials()}
                </div>
                
                {/* User Info */}
                <div className="text-left hidden md:block">
                  <p className="text-sm font-medium text-gray-800">{user?.full_name || user?.username}</p>
                  <p className="text-xs text-gray-500">{getRoleDisplayName(user?.role)}</p>
                </div>

                {/* Dropdown Arrow */}
                <svg
                  className={`w-4 h-4 text-gray-500 transition-transform ${showUserMenu ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Dropdown Menu */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                  {/* User Info Section */}
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="font-semibold text-gray-800">{user?.full_name || user?.username}</p>
                    <p className="text-sm text-gray-500">{user?.email || 'No email'}</p>
                    <p className="text-xs text-gray-400 mt-1">{getRoleDisplayName(user?.role)}</p>
                  </div>

                  {/* Menu Items */}
                  <div className="py-2">
                    {/* Profile */}
                    <button
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3"
                      onClick={() => {
                        setShowUserMenu(false);
                        navigate('/profile');
                      }}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      {language === 'vi' ? 'Thông tin cá nhân' : 'Profile'}
                    </button>

                    {/* Settings (role-based) */}
                    {user?.role && ['manager', 'admin', 'super_admin'].includes(user.role) && (
                      <button
                        className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3"
                        onClick={() => {
                          setShowUserMenu(false);
                          navigate('/settings');
                        }}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        {language === 'vi' ? 'Cài đặt hệ thống' : 'System Settings'}
                      </button>
                    )}
                  </div>

                  {/* Logout */}
                  <div className="border-t border-gray-100 pt-2">
                    <button
                      onClick={handleLogout}
                      className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-3"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      {language === 'vi' ? 'Đăng xuất' : 'Logout'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
