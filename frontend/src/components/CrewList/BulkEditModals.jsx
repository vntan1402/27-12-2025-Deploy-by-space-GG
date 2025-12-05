/**
 * Bulk Edit Modals for Crew List
 * Separate modals for editing Place Sign On, Ship Sign On, Date Sign On, Date Sign Off
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

// Bulk Edit Place Sign On Modal
export const BulkEditPlaceSignOnModal = ({ 
  isOpen, 
  onClose, 
  value, 
  onChange, 
  onSubmit, 
  selectedCount 
}) => {
  const { language } = useAuth();
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-gray-800 flex items-center">
              <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {language === 'vi' ? 'Chỉnh sửa nơi xuống tàu' : 'Edit Place Sign On'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>
        
        <div className="p-6">
          <div className="mb-4">
            <div className="text-sm text-gray-600 mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center space-x-2 mb-2">
                <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>
                  {language === 'vi' 
                    ? `Cập nhật nơi xuống tàu cho ${selectedCount} thuyền viên được chọn`
                    : `Update place sign on for ${selectedCount} selected crew members`
                  }
                </span>
              </div>
              <div className="text-xs text-blue-700 font-medium space-y-1">
                <div>
                  {language === 'vi' 
                    ? '✅ Nhập địa điểm: Cập nhật nơi xuống tàu'
                    : '✅ Enter location: Update place sign on'
                  }
                </div>
                <div>
                  {language === 'vi' 
                    ? '🗑️ Để trống: Xóa nơi xuống tàu'
                    : '🗑️ Leave empty: Clear place sign on'
                  }
                </div>
              </div>
            </div>
            
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Nơi xuống tàu' : 'Place Sign On'}
            </label>
            <input
              type="text"
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  onSubmit();
                }
              }}
              placeholder={language === 'vi' ? 'Nhập nơi xuống tàu (ví dụ: Hải Phòng, Vietnam)' : 'Enter place sign on (e.g: Ho Chi Minh City, Vietnam)'}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              onClick={onSubmit}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all flex items-center"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {language === 'vi' ? 'Cập nhật' : 'Update'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Bulk Edit Place Sign Off Modal
export const BulkEditPlaceSignOffModal = ({ 
  isOpen, 
  onClose, 
  value, 
  onChange, 
  onSubmit, 
  selectedCount 
}) => {
  const { language } = useAuth();
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-gray-800 flex items-center">
              <svg className="w-5 h-5 mr-2 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {language === 'vi' ? 'Chỉnh sửa nơi rời tàu' : 'Edit Place Sign Off'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>
        
        <div className="p-6">
          <div className="mb-4">
            <div className="text-sm text-gray-600 mb-3 p-3 bg-orange-50 rounded-lg border border-orange-200">
              <div className="flex items-center space-x-2 mb-2">
                <svg className="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>
                  {language === 'vi' 
                    ? `Cập nhật nơi rời tàu cho ${selectedCount} thuyền viên được chọn`
                    : `Update place sign off for ${selectedCount} selected crew members`
                  }
                </span>
              </div>
              <div className="text-xs text-orange-700 font-medium space-y-1">
                <div>
                  {language === 'vi' 
                    ? '✅ Nhập địa điểm: Cập nhật nơi rời tàu'
                    : '✅ Enter location: Update place sign off'
                  }
                </div>
                <div>
                  {language === 'vi' 
                    ? '🗑️ Để trống: Xóa nơi rời tàu'
                    : '🗑️ Leave empty: Clear place sign off'
                  }
                </div>
              </div>
            </div>
            
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Nơi rời tàu' : 'Place Sign Off'}
            </label>
            <input
              type="text"
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  onSubmit();
                }
              }}
              placeholder={language === 'vi' ? 'Nhập nơi rời tàu (ví dụ: Vũng Tàu, Vietnam)' : 'Enter place sign off (e.g: Vung Tau, Vietnam)'}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
              autoFocus
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              onClick={onSubmit}
              className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-all flex items-center"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {language === 'vi' ? 'Cập nhật' : 'Update'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Bulk Edit Ship Sign On Modal
export const BulkEditShipSignOnModal = ({ 
  isOpen, 
  onClose, 
  value, 
  onChange, 
  onSubmit, 
  selectedCount,
  ships,
  placeSignOn,
  onPlaceSignOnChange,
  dateSignOn,
  onDateSignOnChange
}) => {
  const { language } = useAuth();
  const [shipSearch, setShipSearch] = React.useState('');
  
  // Reset search when modal opens
  React.useEffect(() => {
    if (isOpen) {
      setShipSearch('');
    }
  }, [isOpen]);
  
  if (!isOpen) return null;
  
  // Filter ships based on search
  const filteredShips = ships && ships.length > 0 
    ? ships.filter(ship => 
        ship.name.toLowerCase().includes(shipSearch.toLowerCase())
      )
    : [];
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-gray-800 flex items-center">
              <svg className="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              {language === 'vi' ? 'Chỉnh sửa tàu đăng ký' : 'Edit Ship Sign On'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>
        
        <div className="p-6">
          <div className="mb-4">
            <div className="text-sm text-gray-600 mb-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center space-x-2 mb-2">
                <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>
                  {language === 'vi' 
                    ? `Cập nhật tàu đăng ký cho ${selectedCount} thuyền viên được chọn`
                    : `Update ship sign on for ${selectedCount} selected crew members`
                  }
                </span>
              </div>
              <div className="text-xs text-purple-700 font-medium space-y-1">
                <div>
                  {language === 'vi' 
                    ? '🚢 Chọn tàu: Sign On và di chuyển files'
                    : '🚢 Select ship: Sign On and move files'
                  }
                </div>
                <div>
                  {language === 'vi' 
                    ? '📤 Chọn "-": Sign Off và chuyển về Standby'
                    : '📤 Select "-": Sign Off and move to Standby'
                  }
                </div>
              </div>
            </div>
            
            {/* Ship Search Field */}
            {ships && ships.length > 0 && (
              <div className="mb-3">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? '🔍 Tìm kiếm tàu' : '🔍 Ship Search'}
                </label>
                <input
                  type="text"
                  value={shipSearch}
                  onChange={(e) => setShipSearch(e.target.value)}
                  placeholder={language === 'vi' ? 'Nhập tên tàu để tìm kiếm...' : 'Type ship name to search...'}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
                {shipSearch && (
                  <div className="mt-1 text-xs text-gray-600">
                    {language === 'vi' 
                      ? `Tìm thấy ${filteredShips.length} tàu` 
                      : `Found ${filteredShips.length} ship(s)`}
                  </div>
                )}
              </div>
            )}
            
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Tàu đăng ký' : 'Ship Sign On'}
            </label>
            {ships && ships.length > 0 ? (
              <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && value) {
                    e.preventDefault();
                    onSubmit();
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">{language === 'vi' ? '-- Chọn tàu --' : '-- Select Ship --'}</option>
                {filteredShips.map(ship => (
                  <option key={ship.id} value={ship.name}>{ship.name}</option>
                ))}
                <option value="-">{language === 'vi' ? '- (Sign off)' : '- (Sign off)'}</option>
              </select>
            ) : (
              <input
                type="text"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && value) {
                    e.preventDefault();
                    onSubmit();
                  }
                }}
                placeholder={language === 'vi' ? 'Nhập tên tàu hoặc "-" cho Sign off' : 'Enter ship name or "-" for Sign off'}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                autoFocus
              />
            )}
            <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-xs text-blue-800 font-medium">
                {language === 'vi' ? '📋 Cập nhật tự động:' : '📋 Auto-updates:'}
              </p>
              <ul className="text-xs text-blue-700 mt-1 space-y-1">
                <li>🚢 {language === 'vi' ? 'Chọn tàu → Sign On (files di chuyển tự động)' : 'Select ship → Sign On (files auto-move)'}</li>
                <li>📤 {language === 'vi' ? 'Chọn "-" → Sign Off, Standby (files về Standby)' : 'Select "-" → Sign Off, Standby (files to Standby)'}</li>
              </ul>
            </div>
          </div>
          
          {/* Place Sign On/Off Field - Dynamic label based on selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {value === '-' 
                ? (language === 'vi' ? 'Nơi rời tàu' : 'Place Sign Off')
                : (language === 'vi' ? 'Nơi xuống tàu' : 'Place Sign On')
              }
            </label>
            <input
              type="text"
              value={placeSignOn || ''}
              onChange={(e) => onPlaceSignOnChange(e.target.value)}
              placeholder={
                value === '-'
                  ? (language === 'vi' ? 'Nhập nơi rời tàu (tùy chọn)' : 'Enter place sign off (optional)')
                  : (language === 'vi' ? 'Nhập nơi xuống tàu (tùy chọn)' : 'Enter place sign on (optional)')
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          
          {/* Date Sign On/Off Field - Dynamic label based on selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {value === '-'
                ? (language === 'vi' ? 'Ngày rời tàu' : 'Date Sign Off')
                : (language === 'vi' ? 'Ngày xuống tàu' : 'Date Sign On')
              }
            </label>
            <input
              type="date"
              value={dateSignOn || ''}
              onChange={(e) => onDateSignOnChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              {language === 'vi' 
                ? 'Để trống sẽ sử dụng ngày hiện tại' 
                : 'Leave empty to use current date'}
            </p>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              onClick={onSubmit}
              disabled={!value}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg transition-all flex items-center"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {language === 'vi' ? 'Cập nhật' : 'Update'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Bulk Edit Date Sign On Modal
export const BulkEditDateSignOnModal = ({ 
  isOpen, 
  onClose, 
  value, 
  onChange, 
  onSubmit, 
  selectedCount 
}) => {
  const { language } = useAuth();
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-gray-800 flex items-center">
              <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {language === 'vi' ? 'Chỉnh sửa ngày xuống tàu' : 'Edit Date Sign On'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>
        
        <div className="p-6">
          <div className="mb-4">
            <div className="text-sm text-gray-600 mb-3 p-3 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center space-x-2 mb-2">
                <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>
                  {language === 'vi' 
                    ? `Cập nhật ngày xuống tàu cho ${selectedCount} thuyền viên được chọn`
                    : `Update date sign on for ${selectedCount} selected crew members`
                  }
                </span>
              </div>
              <div className="text-xs text-green-700 font-medium space-y-1">
                <div>
                  {language === 'vi' 
                    ? '✅ Nhập ngày: Cập nhật ngày xuống tàu'
                    : '✅ Enter date: Update date sign on'
                  }
                </div>
                <div>
                  {language === 'vi' 
                    ? '🗑️ Để trống: Xóa ngày xuống tàu'
                    : '🗑️ Leave empty: Clear date sign on'
                  }
                </div>
              </div>
            </div>
            
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Ngày xuống tàu' : 'Date Sign On'}
            </label>
            <input
              type="date"
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  onSubmit();
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              autoFocus
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              onClick={onSubmit}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all flex items-center"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {language === 'vi' ? 'Cập nhật' : 'Update'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Bulk Edit Date Sign Off Modal
export const BulkEditDateSignOffModal = ({ 
  isOpen, 
  onClose, 
  value, 
  onChange, 
  onSubmit, 
  selectedCount 
}) => {
  const { language } = useAuth();
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-gray-800 flex items-center">
              <svg className="w-5 h-5 mr-2 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {language === 'vi' ? 'Chỉnh sửa ngày rời tàu' : 'Edit Date Sign Off'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>
        
        <div className="p-6">
          <div className="mb-4">
            <div className="text-sm text-gray-600 mb-3 p-3 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-center space-x-2 mb-2">
                <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>
                  {language === 'vi' 
                    ? `Cập nhật ngày rời tàu cho ${selectedCount} thuyền viên được chọn`
                    : `Update date sign off for ${selectedCount} selected crew members`
                  }
                </span>
              </div>
              <div className="text-xs text-red-700 font-medium space-y-1">
                <div>
                  {language === 'vi' 
                    ? '✅ Nhập ngày: Trạng thái → "Standby", Tàu → "-"'
                    : '✅ Enter date: Status → "Standby", Ship → "-"'
                  }
                </div>
                <div>
                  {language === 'vi' 
                    ? '🗑️ Để trống: Xóa ngày rời tàu (không đổi trạng thái/tàu)'
                    : '🗑️ Leave empty: Clear date sign off (status/ship unchanged)'
                  }
                </div>
              </div>
            </div>
            
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Ngày rời tàu' : 'Date Sign Off'}
            </label>
            <input
              type="date"
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  onSubmit();
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
              autoFocus
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              onClick={onSubmit}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all flex items-center"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {language === 'vi' ? 'Cập nhật' : 'Update'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
