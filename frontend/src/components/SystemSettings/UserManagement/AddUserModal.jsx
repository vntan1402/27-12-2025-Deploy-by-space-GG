/**
 * AddUserModal Component
 * Modal for adding new users with role-based validation
 */
import React, { useEffect } from 'react';

const AddUserModal = ({
  userData,
  setUserData,
  onClose,
  onSubmit,
  language,
  companies,
  ships,
  availableRoles,
  loading,
  currentUser  // Added currentUser prop
}) => {
  // Lock company field to current user's company on mount
  useEffect(() => {
    if (currentUser?.company && !userData.company) {
      setUserData(prev => ({ ...prev, company: currentUser.company }));
    }
  }, [currentUser, userData.company, setUserData]);

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
    
    onSubmit();
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

  // Get current user's company name for display
  const currentUserCompanyName = companies.find(c => 
    c.name_en === currentUser?.company || c.name_vn === currentUser?.company
  );

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200 sticky top-0 bg-white">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? 'Thêm người dùng mới' : 'Add New User'}
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
          {/* Username */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Tên đăng nhập' : 'Username'} *
            </label>
            <input
              type="text"
              required
              value={userData.username}
              onChange={(e) => setUserData(prev => ({ ...prev, username: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={language === 'vi' ? 'Ví dụ: admin1 hoặc admin1@amcsc.vn' : 'Example: admin1 or admin1@company.com'}
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">
              {language === 'vi' ? '* Có thể là tên đơn giản (admin1) hoặc email' : '* Can be simple name (admin1) or email'}
            </p>
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email *
            </label>
            <input
              type="email"
              required
              value={userData.email}
              onChange={(e) => setUserData(prev => ({ ...prev, email: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="user@example.com"
              disabled={loading}
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Mật khẩu' : 'Password'} *
            </label>
            <input
              type="password"
              required
              value={userData.password}
              onChange={(e) => setUserData(prev => ({ ...prev, password: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={language === 'vi' ? 'Nhập mật khẩu (tối thiểu 6 ký tự)' : 'Enter password (min 6 characters)'}
              minLength={6}
              disabled={loading}
            />
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

          {/* Role */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Vai trò' : 'Role'} *
            </label>
            <select
              required
              value={userData.role}
              onChange={(e) => setUserData(prev => ({ ...prev, role: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            >
              {availableRoles.map(role => (
                <option key={role} value={role}>
                  {getRoleDisplayName(role)}
                </option>
              ))}
            </select>
          </div>

          {/* Department - Changed to Checkboxes */}
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

          <div className="grid grid-cols-2 gap-4">
            {/* Company - LOCKED to current user's company */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Công ty' : 'Company'} *
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={language === 'vi' 
                    ? (currentUserCompanyName?.name_vn || currentUser?.company || '')
                    : (currentUserCompanyName?.name_en || currentUser?.company || '')
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed"
                  disabled={true}
                  readOnly
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {language === 'vi' ? '🔒 Người dùng mới sẽ thuộc công ty của bạn' : '🔒 New user will belong to your company'}
              </p>
            </div>

            {/* Ship */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tàu' : 'Ship'}
              </label>
              <select
                value={userData.ship}
                onChange={(e) => setUserData(prev => ({ ...prev, ship: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              >
                <option value="">{language === 'vi' ? 'Chọn tàu' : 'Select ship'}</option>
                {ships.map(ship => (
                  <option key={ship.id} value={ship.name}>
                    {ship.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
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

            {/* Gmail */}
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
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t">
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
              className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-all font-medium"
              disabled={loading}
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {language === 'vi' ? 'Đang xử lý...' : 'Processing...'}
                </div>
              ) : (
                language === 'vi' ? 'Thêm người dùng' : 'Add User'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddUserModal;
            <input
              type="email"
              required
              value={userData.email}
              onChange={(e) => setUserData(prev => ({ ...prev, email: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="user@example.com"
              disabled={loading}
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Mật khẩu' : 'Password'} *
            </label>
            <input
              type="password"
              required
              value={userData.password}
              onChange={(e) => setUserData(prev => ({ ...prev, password: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={language === 'vi' ? 'Nhập mật khẩu (tối thiểu 6 ký tự)' : 'Enter password (min 6 characters)'}
              minLength={6}
              disabled={loading}
            />
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

          <div className="grid grid-cols-2 gap-4">
            {/* Role */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Vai trò' : 'Role'} *
              </label>
              <select
                required
                value={userData.role}
                onChange={(e) => setUserData(prev => ({ ...prev, role: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              >
                {availableRoles.map(role => (
                  <option key={role} value={role}>
                    {getRoleDisplayName(role)}
                  </option>
                ))}
              </select>
            </div>

            {/* Department */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Phòng ban' : 'Department'} *
              </label>
              <select
                required
                value={userData.department}
                onChange={(e) => setUserData(prev => ({ ...prev, department: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              >
                {departmentOptions.map(dept => (
                  <option key={dept.value} value={dept.value}>
                    {dept.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Company */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Công ty' : 'Company'}
              </label>
              <select
                value={userData.company}
                onChange={(e) => setUserData(prev => ({ ...prev, company: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              >
                <option value="">{language === 'vi' ? 'Chọn công ty' : 'Select company'}</option>
                {companies.map(company => (
                  <option key={company.id} value={company.name_en || company.name_vn}>
                    {language === 'vi' ? company.name_vn : company.name_en}
                  </option>
                ))}
              </select>
            </div>

            {/* Ship */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tàu' : 'Ship'}
              </label>
              <select
                value={userData.ship}
                onChange={(e) => setUserData(prev => ({ ...prev, ship: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              >
                <option value="">{language === 'vi' ? 'Chọn tàu' : 'Select ship'}</option>
                {ships.map(ship => (
                  <option key={ship.id} value={ship.name}>
                    {ship.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Zalo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Zalo
              </label>
              <input
                type="text"
                value={userData.zalo}
                onChange={(e) => setUserData(prev => ({ ...prev, zalo: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Số điện thoại Zalo' : 'Zalo phone number'}
                disabled={loading}
              />
            </div>

            {/* Gmail */}
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
              className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-all font-medium"
              disabled={loading}
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {language === 'vi' ? 'Đang xử lý...' : 'Processing...'}
                </div>
              ) : (
                language === 'vi' ? 'Thêm người dùng' : 'Add User'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddUserModal;
