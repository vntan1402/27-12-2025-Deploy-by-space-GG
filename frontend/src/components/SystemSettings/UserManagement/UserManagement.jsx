/**
 * User Management Container
 * Main component for managing users with role-based permissions
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useAuth } from '../../../contexts/AuthContext';
import userService from '../../../services/userService';
import shipService from '../../../services/shipService';
import companyService from '../../../services/companyService';
import AddUserModal from './AddUserModal';
import UserTable from './UserTable';

/**
 * Role hierarchy (from highest to lowest)
 * super_admin > admin > manager > editor > viewer
 */
const ROLE_HIERARCHY = {
  super_admin: 5,
  admin: 4,
  manager: 3,
  editor: 2,
  viewer: 1,
};

const UserManagement = () => {
  const { user: currentUser, language } = useAuth();
  
  // State
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [ships, setShips] = useState([]);
  const [showUserList, setShowUserList] = useState(false);
  const [showAddUser, setShowAddUser] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // New user data
  const [newUserData, setNewUserData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'viewer',
    department: 'technical',
    company: '',
    ship: '',
    zalo: '',
    gmail: ''
  });

  // Fetch data on mount
  useEffect(() => {
    fetchCompanies();
    fetchShips();
  }, []);

  // Fetch users when list is shown
  useEffect(() => {
    if (showUserList) {
      fetchUsers();
    }
  }, [showUserList]);

  /**
   * Fetch all users
   */
  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await userService.getAll();
      const data = response.data;
      setUsers(data);
      setFilteredUsers(data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách người dùng' : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Fetch companies
   */
  const fetchCompanies = async () => {
    try {
      const response = await companyService.getAll();
      setCompanies(response.data || []);
    } catch (error) {
      console.error('Failed to fetch companies:', error);
    }
  };

  /**
   * Fetch ships
   */
  const fetchShips = async () => {
    try {
      const response = await shipService.getAllShips();
      setShips(response.data || []);
    } catch (error) {
      console.error('Failed to fetch ships:', error);
    }
  };

  /**
   * Check if current user can create a user with specific role
   * @param {string} targetRole - Role to be assigned
   * @returns {boolean}
   */
  const canCreateUserWithRole = (targetRole) => {
    // Super admin can create any role
    if (currentUser.role === 'super_admin') {
      return true;
    }
    
    // Users can only create roles lower than their own
    const currentRoleLevel = ROLE_HIERARCHY[currentUser.role] || 0;
    const targetRoleLevel = ROLE_HIERARCHY[targetRole] || 0;
    
    return currentRoleLevel > targetRoleLevel;
  };

  /**
   * Get available roles for current user to assign
   * @returns {Array} List of available roles
   */
  const getAvailableRoles = () => {
    if (currentUser.role === 'super_admin') {
      return ['super_admin', 'admin', 'manager', 'editor', 'viewer'];
    }
    
    const currentRoleLevel = ROLE_HIERARCHY[currentUser.role] || 0;
    return Object.entries(ROLE_HIERARCHY)
      .filter(([role, level]) => level < currentRoleLevel)
      .map(([role]) => role)
      .reverse(); // Show from highest to lowest
  };

  /**
   * Handle add user
   */
  const handleAddUser = async () => {
    try {
      // Validate required fields
      if (!newUserData.username || !newUserData.email || !newUserData.password || !newUserData.full_name) {
        toast.error(language === 'vi' ? 'Vui lòng điền đầy đủ thông tin bắt buộc' : 'Please fill in all required fields');
        return;
      }

      // Check permission to create user with selected role
      if (!canCreateUserWithRole(newUserData.role)) {
        toast.error(language === 'vi' ? 'Bạn không có quyền tạo người dùng với vai trò này' : 'You do not have permission to create user with this role');
        return;
      }

      setLoading(true);
      await userService.create(newUserData);
      
      toast.success(language === 'vi' ? 'Thêm người dùng thành công!' : 'User added successfully!');
      
      // Reset form
      setNewUserData({
        username: '',
        email: '',
        password: '',
        full_name: '',
        role: 'viewer',
        department: 'technical',
        company: '',
        ship: '',
        zalo: '',
        gmail: ''
      });
      
      setShowAddUser(false);
      
      // Refresh user list
      if (showUserList) {
        fetchUsers();
      }
    } catch (error) {
      console.error('Failed to add user:', error);
      const errorMessage = error.response?.data?.detail || (language === 'vi' ? 'Không thể thêm người dùng' : 'Failed to add user');
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Check if user can edit another user
   * @param {Object} targetUser - User to be edited
   * @returns {boolean}
   */
  const canEditUser = (targetUser) => {
    // Cannot edit self
    if (targetUser.id === currentUser.id) {
      return false;
    }

    // Super admin can edit all
    if (currentUser.role === 'super_admin') {
      return true;
    }

    // Can only edit users with lower role level
    const currentRoleLevel = ROLE_HIERARCHY[currentUser.role] || 0;
    const targetRoleLevel = ROLE_HIERARCHY[targetUser.role] || 0;
    
    return currentRoleLevel > targetRoleLevel;
  };

  /**
   * Check if user can delete another user
   * @param {Object} targetUser - User to be deleted
   * @returns {boolean}
   */
  const canDeleteUser = (targetUser) => {
    // Cannot delete self
    if (targetUser.id === currentUser.id) {
      return false;
    }

    // Super admin can delete all (except self)
    if (currentUser.role === 'super_admin') {
      return true;
    }

    // Can only delete users with lower role level
    const currentRoleLevel = ROLE_HIERARCHY[currentUser.role] || 0;
    const targetRoleLevel = ROLE_HIERARCHY[targetUser.role] || 0;
    
    return currentRoleLevel > targetRoleLevel;
  };

  /**
   * Handle delete user
   */
  const handleDeleteUser = async (targetUser) => {
    if (!canDeleteUser(targetUser)) {
      toast.error(language === 'vi' ? 'Bạn không có quyền xóa người dùng này' : 'You do not have permission to delete this user');
      return;
    }

    const confirmMessage = language === 'vi' 
      ? `Bạn có chắc muốn xóa người dùng "${targetUser.full_name}"?`
      : `Are you sure you want to delete user "${targetUser.full_name}"?`;
    
    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      setLoading(true);
      await userService.delete(targetUser.id);
      toast.success(language === 'vi' ? 'Xóa người dùng thành công!' : 'User deleted successfully!');
      fetchUsers();
    } catch (error) {
      console.error('Failed to delete user:', error);
      toast.error(language === 'vi' ? 'Không thể xóa người dùng' : 'Failed to delete user');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Action Buttons */}
      <div className="mb-6 flex space-x-4">
        <button
          onClick={() => setShowAddUser(true)}
          className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg transition-all font-medium"
        >
          {language === 'vi' ? 'Thêm người dùng' : 'Add User'}
        </button>
        <button
          onClick={() => setShowUserList(!showUserList)}
          className={`px-6 py-2 rounded-lg transition-all font-medium ${
            showUserList 
              ? 'bg-red-600 hover:bg-red-700 text-white' 
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {showUserList 
            ? (language === 'vi' ? 'Ẩn danh sách' : 'Hide List')
            : (language === 'vi' ? 'Danh sách người dùng' : 'User List')
          }
        </button>
      </div>

      {/* Users Table */}
      {showUserList && (
        <UserTable
          users={filteredUsers}
          loading={loading}
          currentUser={currentUser}
          language={language}
          canEditUser={canEditUser}
          canDeleteUser={canDeleteUser}
          onDeleteUser={handleDeleteUser}
        />
      )}

      {/* Add User Modal */}
      {showAddUser && (
        <AddUserModal
          userData={newUserData}
          setUserData={setNewUserData}
          onClose={() => {
            setShowAddUser(false);
            setNewUserData({
              username: '',
              email: '',
              password: '',
              full_name: '',
              role: 'viewer',
              department: 'technical',
              company: '',
              ship: '',
              zalo: '',
              gmail: ''
            });
          }}
          onSubmit={handleAddUser}
          language={language}
          companies={companies}
          ships={ships}
          availableRoles={getAvailableRoles()}
          loading={loading}
        />
      )}
    </div>
  );
};

export default UserManagement;
