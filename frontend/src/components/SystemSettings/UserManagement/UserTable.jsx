/**
 * UserTable Component
 * Displays list of users in table format with actions
 */
import React from 'react';

const UserTable = ({
  users,
  loading,
  currentUser,
  language,
  canEditUser,
  canDeleteUser,
  onEditUser,
  onDeleteUser
}) => {
  /**
   * Get role badge color
   */
  const getRoleBadgeClass = (role) => {
    switch (role) {
      case 'super_admin':
        return 'bg-red-100 text-red-800';
      case 'admin':
        return 'bg-orange-100 text-orange-800';
      case 'manager':
        return 'bg-blue-100 text-blue-800';
      case 'editor':
        return 'bg-green-100 text-green-800';
      case 'viewer':
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  /**
   * Get role display name
   */
  const getRoleDisplayName = (role) => {
    const roleNames = {
      super_admin: language === 'vi' ? 'Siêu quản trị' : 'Super Admin',
      admin: language === 'vi' ? 'Quản trị' : 'Admin',
      manager: language === 'vi' ? 'Cán bộ công ty' : 'Company Officer',
      editor: language === 'vi' ? 'Sĩ quan' : 'Ship Officer',
      viewer: language === 'vi' ? 'Thuyền viên' : 'Crew'
    };
    return roleNames[role] || role;
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
      </div>
    );
  }

  if (users.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 bg-gray-50 rounded-lg">
        <div className="text-5xl mb-4">👥</div>
        <p className="text-lg">{language === 'vi' ? 'Chưa có người dùng nào' : 'No users yet'}</p>
        <p className="text-sm mt-2">
          {language === 'vi' ? 'Nhấn "Thêm người dùng" để bắt đầu' : 'Click "Add User" to get started'}
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-gray-300 text-sm">
        <thead>
          <tr className="bg-gray-50">
            <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-700">
              {language === 'vi' ? 'Tên người dùng' : 'User Name'}
            </th>
            <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-700">
              {language === 'vi' ? 'Công ty' : 'Company'}
            </th>
            <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-700">
              {language === 'vi' ? 'Phòng ban' : 'Department'}
            </th>
            <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-700">
              {language === 'vi' ? 'Vai trò' : 'Role'}
            </th>
            <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-700">
              {language === 'vi' ? 'Tàu' : 'Ship'}
            </th>
            <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-700">
              Zalo
            </th>
            <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-700">
              Gmail
            </th>
            <th className="border border-gray-300 px-4 py-3 text-center font-semibold text-gray-700">
              {language === 'vi' ? 'Thao tác' : 'Actions'}
            </th>
          </tr>
        </thead>
        <tbody>
          {users.map((userItem) => (
            <tr key={userItem.id} className="hover:bg-gray-50 transition-colors">
              <td className="border border-gray-300 px-4 py-3">
                <div className="font-medium text-gray-800">{userItem.full_name}</div>
                <div className="text-xs text-gray-500">{userItem.username}</div>
              </td>
              <td className="border border-gray-300 px-4 py-3 text-gray-700">
                {userItem.company || '-'}
              </td>
              <td className="border border-gray-300 px-4 py-3 text-gray-700">
                {Array.isArray(userItem.department) && userItem.department.length > 0
                  ? userItem.department.map(dept => {
                      const deptLabels = {
                        technical: language === 'vi' ? 'Kỹ thuật' : 'Technical',
                        operations: language === 'vi' ? 'Vận hành' : 'Operations',
                        safety: language === 'vi' ? 'An toàn' : 'Safety',
                        commercial: language === 'vi' ? 'Thương mại' : 'Commercial',
                        crewing: language === 'vi' ? 'Thuyền viên' : 'Crewing',
                        ship_crew: language === 'vi' ? 'Thuyền viên tàu' : 'Ship Crew',
                        dpa: 'DPA',
                        supply: language === 'vi' ? 'Vật tư' : 'Supply'
                      };
                      return deptLabels[dept] || dept;
                    }).join(', ')
                  : (userItem.department || '-')
                }
              </td>
              <td className="border border-gray-300 px-4 py-3">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRoleBadgeClass(userItem.role)}`}>
                  {getRoleDisplayName(userItem.role)}
                </span>
              </td>
              <td className="border border-gray-300 px-4 py-3 text-gray-700">
                {userItem.ship || '-'}
              </td>
              <td className="border border-gray-300 px-4 py-3 text-gray-700">
                {userItem.zalo || '-'}
              </td>
              <td className="border border-gray-300 px-4 py-3 text-gray-700">
                {userItem.gmail || '-'}
              </td>
              <td className="border border-gray-300 px-4 py-3">
                <div className="flex justify-center space-x-2">
                  <button
                    onClick={() => onEditUser && onEditUser(userItem)}
                    disabled={!canEditUser(userItem)}
                    className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-3 py-1 rounded text-xs transition-all font-medium"
                    title={
                      !canEditUser(userItem) 
                        ? (language === 'vi' 
                            ? 'Không có quyền chỉnh sửa người dùng này' 
                            : 'No permission to edit this user')
                        : (language === 'vi' ? 'Sửa' : 'Edit')
                    }
                  >
                    {language === 'vi' ? 'Sửa' : 'Edit'}
                  </button>
                  <button
                    onClick={() => onDeleteUser(userItem)}
                    disabled={!canDeleteUser(userItem)}
                    className="bg-red-500 hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-3 py-1 rounded text-xs transition-all font-medium"
                    title={
                      !canDeleteUser(userItem) 
                        ? (language === 'vi' 
                            ? 'Không có quyền xóa người dùng này' 
                            : 'No permission to delete this user')
                        : (language === 'vi' ? 'Xóa' : 'Delete')
                    }
                  >
                    {language === 'vi' ? 'Xóa' : 'Delete'}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default UserTable;
