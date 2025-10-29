/**
 * EditUserModal Component
 * Modal for editing existing users with role-based validation
 */
import React, { useState, useEffect } from 'react';

const EditUserModal = ({
  user,
  onClose,
  onSubmit,
  language,
  companies,
  ships,
  availableRoles,
  loading,
  currentUser
}) => {
  const [userData, setUserData] = useState({
    username: '',
    email: '',
    password: '',  // Optional - only if changing
    full_name: '',
    role: 'viewer',
    department: [],  // Changed to array
    company: '',
    ship: '',
    zalo: ''
  });

  // Initialize form data when user prop changes
  useEffect(() => {
    if (user) {
      setUserData({
        username: user.username || '',
        email: user.email || '',
        password: '',  // Keep empty, only fill if user wants to change
        full_name: user.full_name || '',
        role: user.role || 'viewer',
        department: Array.isArray(user.department) ? user.department : (user.department ? [user.department] : []),  // Convert to array if needed
        company: user.company || '',
        ship: user.ship || '',
        zalo: user.zalo || '',
        gmail: user.gmail || ''
      });
    }
  }, [user]);

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate at least one department is selected
    if (!userData.department || userData.department.length === 0) {
      alert(language === 'vi' ? 'Vui lòng chọn ít nhất một phòng ban' : 'Please select at least one department');
      return;
    }
    
    // Pass userId and userData to parent
    onSubmit(user.id, userData);
  };

  /**
   * Get department options with DPA and Supply
   */
  const departmentOptions = [
    { value: 'technical', label: language === 'vi' ? 'Kỹ thuật' : 'Technical' },
    { value: 'operations', label: language === 'vi' ? 'Vận hành' : 'Operations' },
    { value: 'safety', label: language === 'vi' ? 'An toàn' : 'Safety' },
    { value: 'commercial', label: language === 'vi' ? 'Thương mại' : 'Commercial' },
    { value: 'crewing', label: language === 'vi' ? 'Thuyền viên' : 'Crewing' },
    { value: 'ship_crew', label: language === 'vi' ? 'Thuyền viên tàu' : 'Ship Crew' },
    { value: 'dpa', label: 'DPA' },
    { value: 'supply', label: language === 'vi' ? 'Vật tư' : 'Supply' }
  ];

  /**
   * Handle department checkbox change
   */
  const handleDepartmentChange = (deptValue) => {
    const currentDepts = userData.department || [];
    const isChecked = currentDepts.includes(deptValue);
    
    let newDepts;
    if (isChecked) {
      // Remove department
      newDepts = currentDepts.filter(d => d !== deptValue);
    } else {
      // Add department
      newDepts = [...currentDepts, deptValue];
    }
    
    setUserData(prev => ({ ...prev, department: newDepts }));
  };

  // Check if ship_crew is selected in department
  const isShipCrewSelected = userData.department && Array.isArray(userData.department) && userData.department.includes('ship_crew');

  // Filter ships by user's company
  const getFilteredShips = () => {
    if (!userData.company) return [];
    
    // Find the selected company
    const selectedCompany = companies.find(c => 
      c.id === userData.company ||
      c.name_en === userData.company ||
      c.name_vn === userData.company ||
      c.name === userData.company
    );
    
    if (!selectedCompany) return [];
    
    // Filter ships by company
    return ships.filter(ship => 
      ship.company === userData.company || 
      ship.company === selectedCompany.id ||
      ship.company === selectedCompany.name_en || 
      ship.company === selectedCompany.name_vn ||
      ship.company === selectedCompany.name
    );
  };

  const filteredShips = getFilteredShips();

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

  // Check if editing own role (should be disabled)
  const isEditingOwnRole = user && currentUser && user.id === currentUser.id;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200 sticky top-0 bg-white">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? 'Chỉnh sửa người dùng' : 'Edit User'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            disabled={loading}
          >
            ×
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Username (Read-only) and Email - 2 fields per row */}
          <div className="grid grid-cols-2 gap-4">
            {/* Username (Read-only) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên đăng nhập' : 'Username'}
              </label>
              <input
                type="text"
                value={userData.username}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed"
                disabled
                readOnly
              />
              <p className="text-xs text-gray-500 mt-1">
                {language === 'vi' ? 'Không thể thay đổi' : 'Cannot be changed'}
              </p>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                value={userData.email}
                onChange={(e) => setUserData(prev => ({ ...prev, email: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="user@example.com"
                disabled={loading}
              />
            </div>
          </div>

          {/* Password and Full Name - 2 fields per row */}
          <div className="grid grid-cols-2 gap-4">
            {/* Password (Optional) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Mật khẩu mới' : 'New Password'}
              </label>
              <input
                type="password"
                value={userData.password}
                onChange={(e) => setUserData(prev => ({ ...prev, password: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Để trống nếu giữ nguyên' : 'Leave empty to keep current'}
                minLength={6}
                disabled={loading}
              />
              <p className="text-xs text-gray-500 mt-1">
                {language === 'vi' ? 'Chỉ điền để đổi' : 'Fill only to change'}
              </p>
            </div>

            {/* Full Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Họ và tên' : 'Full Name'} *
              </label>
              <input
                type="text"
                required
                value={userData.full_name}
                onChange={(e) => setUserData(prev => ({ ...prev, full_name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Nhập họ và tên' : 'Enter full name'}
                disabled={loading}
              />
            </div>
          </div>

          {/* Role - Full width or with Ship based on department */}
          <div className={isShipCrewSelected ? "grid grid-cols-2 gap-4" : ""}>
            {/* Role */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Vai trò' : 'Role'} *
              </label>
              <select
                required
                value={userData.role}
                onChange={(e) => setUserData(prev => ({ ...prev, role: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                disabled={loading || isEditingOwnRole}
              >
                {availableRoles.map(role => (
                  <option key={role} value={role}>
                    {getRoleDisplayName(role)}
                  </option>
                ))}
                {/* Show current role even if not in available roles */}
                {!availableRoles.includes(userData.role) && (
                  <option value={userData.role}>
                    {getRoleDisplayName(userData.role)}
                  </option>
                )}
              </select>
              {isEditingOwnRole && (
                <p className="text-xs text-amber-600 mt-1">
                  {language === 'vi' ? 'Không thể thay đổi vai trò của chính mình' : 'Cannot change your own role'}
                </p>
              )}
            </div>

            {/* Ship - Only show if ship_crew is selected in department */}
            {isShipCrewSelected && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tàu' : 'Ship'}
                </label>
                <select
                  value={userData.ship}
                  onChange={(e) => setUserData(prev => ({ ...prev, ship: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={loading || !userData.company}
                >
                  <option value="">{language === 'vi' ? 'Chọn tàu' : 'Select ship'}</option>
                  {filteredShips.map(ship => (
                    <option key={ship.id} value={ship.name}>
                      {ship.name}
                    </option>
                  ))}
                </select>
                {!userData.company && (
                  <p className="text-xs text-amber-600 mt-1">
                    {language === 'vi' ? 'Chọn công ty trước' : 'Select company first'}
                  </p>
                )}
                {userData.company && filteredShips.length === 0 && (
                  <p className="text-xs text-gray-500 mt-1">
                    {language === 'vi' ? 'Không có tàu nào' : 'No ships available'}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Department - Full width with checkboxes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Phòng ban' : 'Department'} *
            </label>
            <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
              <div className="grid grid-cols-2 gap-3">
                {departmentOptions.map(dept => {
                  const isChecked = (userData.department || []).includes(dept.value);
                  return (
                    <label 
                      key={dept.value}
                      className="flex items-center space-x-2 cursor-pointer hover:bg-gray-100 p-2 rounded transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleDepartmentChange(dept.value)}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                        disabled={loading}
                      />
                      <span className="text-sm text-gray-700">{dept.label}</span>
                    </label>
                  );
                })}
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {language === 'vi' ? '* Chọn ít nhất một phòng ban. Có thể chọn nhiều phòng ban.' : '* Select at least one department. Multiple selections allowed.'}
            </p>
          </div>

          {/* Company and Zalo - 2 fields per row */}
          <div className="grid grid-cols-2 gap-4">
            {/* Company - Editable for Super Admin, Disabled for others */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Công ty' : 'Company'}
              </label>
              <select
                value={userData.company}
                onChange={(e) => setUserData(prev => ({ ...prev, company: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                disabled={loading || currentUser?.role !== 'super_admin'}
              >
                <option value="">{language === 'vi' ? 'Chọn công ty' : 'Select company'}</option>
                {companies.map(company => (
                  <option key={company.id} value={company.id}>
                    {language === 'vi' ? (company.name_vn || company.name_en) : (company.name_en || company.name_vn)}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {currentUser?.role === 'super_admin' 
                  ? (language === 'vi' ? '👑 Super Admin có thể đổi công ty' : '👑 Super Admin can change company')
                  : (language === 'vi' ? '🔒 Không thể đổi công ty' : '🔒 Cannot change company')
                }
              </p>
            </div>

            {/* Zalo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Zalo *
              </label>
              <input
                type="text"
                required
                value={userData.zalo}
                onChange={(e) => setUserData(prev => ({ ...prev, zalo: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Số điện thoại Zalo' : 'Zalo phone number'}
                disabled={loading}
              />
            </div>
          </div>

          {/* Gmail - Single field */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Gmail
            </label>
            <input
              type="email"
              value={userData.gmail}
              onChange={(e) => setUserData(prev => ({ ...prev, gmail: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="user@gmail.com"
              disabled={loading}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all font-medium"
              disabled={loading}
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-all font-medium"
              disabled={loading}
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {language === 'vi' ? 'Đang cập nhật...' : 'Updating...'}
                </div>
              ) : (
                language === 'vi' ? 'Cập nhật' : 'Update'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditUserModal;
