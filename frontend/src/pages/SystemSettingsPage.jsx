/**
 * System Settings Page
 * Main page for system configuration and management
 * Includes: User Management, Company Management, Google Drive Config, AI Config, Admin Tools
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout } from '../components/Layout';
import { UserManagement } from '../components/SystemSettings/UserManagement';
import { CompanyManagement } from '../components/SystemSettings/CompanyManagement';
import AIConfig from '../components/SystemSettings/AIConfig';
import SystemGoogleDrive from '../components/SystemSettings/SystemGoogleDrive';

// Import components (will be created)
// import { AdminTools } from '../components/SystemSettings/AdminTools';

const SystemSettingsPage = () => {
  const { user, language } = useAuth();
  const navigate = useNavigate();

  // Check permissions
  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    // Allow viewer, manager, admin, super_admin, and system_admin to access settings
    // Viewer and manager can only see their own profile in user list
    const allowedRoles = ['viewer', 'editor', 'manager', 'admin', 'super_admin', 'system_admin'];
    if (!allowedRoles.includes(user.role)) {
      toast.error(language === 'vi' ? 'Bạn không có quyền truy cập trang này' : 'You do not have permission to access this page');
      navigate('/');
    }
  }, [user, navigate, language]);

  if (!user) {
    return null;
  }

  return (
    <MainLayout>
      {/* Page Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-800">
            {language === 'vi' ? 'Cài đặt hệ thống' : 'System Settings'}
          </h1>
          <button
            onClick={() => navigate('/')}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-all"
          >
            {language === 'vi' ? 'Quay lại' : 'Back'}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="space-y-8">
        {/* User Management - All roles can access (viewer and editor see only themselves) */}
        {(user.role === 'viewer' || user.role === 'editor' || user.role === 'manager' || user.role === 'admin' || user.role === 'super_admin' || user.role === 'system_admin') && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-6 text-gray-800 border-b pb-3">
              👥 {language === 'vi' 
                ? (user.role === 'viewer' || user.role === 'editor' ? 'Thông tin cá nhân' : 'Quản lý người dùng')
                : (user.role === 'viewer' || user.role === 'editor' ? 'My Profile' : 'User Management')
              }
            </h2>
            <UserManagement />
          </div>
        )}

        {/* Company Management - Admin, Super Admin, System Admin */}
        {(user.role === 'admin' || user.role === 'super_admin' || user.role === 'system_admin') && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-6 text-gray-800 border-b pb-3">
              🏢 {language === 'vi' ? 'Quản lý công ty' : 'Company Management'}
            </h2>
            <CompanyManagement />
          </div>
        )}

        {/* System Google Drive - Super Admin, System Admin */}
        {(user.role === 'super_admin' || user.role === 'system_admin') && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-6 text-gray-800 border-b pb-3">
              📁 {language === 'vi' ? 'Cấu hình Google Drive hệ thống' : 'System Google Drive Configuration'}
            </h2>
            <SystemGoogleDrive user={user} />
          </div>
        )}

        {/* AI Configuration - Super Admin, System Admin only */}
        {(user.role === 'super_admin' || user.role === 'system_admin') && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-6 text-gray-800 border-b pb-3">
              🤖 {language === 'vi' ? 'Cấu hình AI' : 'AI Configuration'}
            </h2>
            <AIConfig user={user} />
          </div>
        )}

        {/* Admin Tools - Admin, Super Admin, System Admin */}
        {(user.role === 'admin' || user.role === 'super_admin' || user.role === 'system_admin') && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">
              🛠️ {language === 'vi' ? 'Công cụ Admin' : 'Admin Tools'}
            </h2>
            <p className="text-gray-600">Admin Tools module will be implemented here</p>
            {/* <AdminTools /> */}
          </div>
        )}
      </div>
    </MainLayout>
  );
};

export default SystemSettingsPage;
