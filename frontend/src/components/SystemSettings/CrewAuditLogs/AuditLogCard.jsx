/**
 * Audit Log Card Component
 * Individual log entry display
 */
import React from 'react';

export const AuditLogCard = ({ log, onViewDetails, language }) => {
  // Get action icon and color
  const getActionConfig = (action) => {
    const configs = {
      CREATE: { icon: '➕', color: 'green', bgColor: 'bg-green-50', borderColor: 'border-green-200', textColor: 'text-green-800' },
      UPDATE: { icon: '🔄', color: 'blue', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', textColor: 'text-blue-800' },
      DELETE: { icon: '🗑️', color: 'red', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-800' },
      SIGN_ON: { icon: '🚢', color: 'purple', bgColor: 'bg-purple-50', borderColor: 'border-purple-200', textColor: 'text-purple-800' },
      SIGN_OFF: { icon: '🏝️', color: 'orange', bgColor: 'bg-orange-50', borderColor: 'border-orange-200', textColor: 'text-orange-800' },
      SHIP_TRANSFER: { icon: '🔀', color: 'indigo', bgColor: 'bg-indigo-50', borderColor: 'border-indigo-200', textColor: 'text-indigo-800' },
      BULK_UPDATE: { icon: '📋', color: 'teal', bgColor: 'bg-teal-50', borderColor: 'border-teal-200', textColor: 'text-teal-800' },
      CREATE_CERTIFICATE: { icon: '📜', color: 'green', bgColor: 'bg-green-50', borderColor: 'border-green-200', textColor: 'text-green-800' },
      UPDATE_CERTIFICATE: { icon: '📝', color: 'blue', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', textColor: 'text-blue-800' },
      DELETE_CERTIFICATE: { icon: '🗑️', color: 'red', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-800' },
      // Ships
      CREATE_SHIP: { icon: '⚓', color: 'green', bgColor: 'bg-green-50', borderColor: 'border-green-200', textColor: 'text-green-800' },
      UPDATE_SHIP: { icon: '🚢', color: 'blue', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', textColor: 'text-blue-800' },
      DELETE_SHIP: { icon: '🗑️', color: 'red', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-800' },
      // Ship Certificates
      CREATE_SHIP_CERTIFICATE: { icon: '📋', color: 'green', bgColor: 'bg-green-50', borderColor: 'border-green-200', textColor: 'text-green-800' },
      UPDATE_SHIP_CERTIFICATE: { icon: '📝', color: 'blue', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', textColor: 'text-blue-800' },
      DELETE_SHIP_CERTIFICATE: { icon: '🗑️', color: 'red', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-800' },
      // Companies
      CREATE_COMPANY: { icon: '🏢', color: 'green', bgColor: 'bg-green-50', borderColor: 'border-green-200', textColor: 'text-green-800' },
      UPDATE_COMPANY: { icon: '✏️', color: 'blue', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', textColor: 'text-blue-800' },
      DELETE_COMPANY: { icon: '🗑️', color: 'red', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-800' },
      // Users
      CREATE_USER: { icon: '👤', color: 'green', bgColor: 'bg-green-50', borderColor: 'border-green-200', textColor: 'text-green-800' },
      UPDATE_USER: { icon: '👥', color: 'blue', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', textColor: 'text-blue-800' },
      DELETE_USER: { icon: '🗑️', color: 'red', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-800' }
    };
    return configs[action] || configs.UPDATE;
  };

  // Get action label
  const getActionLabel = (action) => {
    const labels = {
      CREATE: language === 'vi' ? 'Tạo mới' : 'Create',
      UPDATE: language === 'vi' ? 'Cập nhật' : 'Update',
      DELETE: language === 'vi' ? 'Xóa' : 'Delete',
      SIGN_ON: language === 'vi' ? 'Xuống tàu' : 'Sign On',
      SIGN_OFF: language === 'vi' ? 'Rời tàu' : 'Sign Off',
      SHIP_TRANSFER: language === 'vi' ? 'Chuyển tàu' : 'Ship Transfer',
      BULK_UPDATE: language === 'vi' ? 'Cập nhật hàng loạt' : 'Bulk Update',
      CREATE_CERTIFICATE: language === 'vi' ? 'Thêm chứng chỉ' : 'Add Certificate',
      UPDATE_CERTIFICATE: language === 'vi' ? 'Sửa chứng chỉ' : 'Update Certificate',
      DELETE_CERTIFICATE: language === 'vi' ? 'Xóa chứng chỉ' : 'Delete Certificate'
    };
    return labels[action] || action;
  };

  const config = getActionConfig(log.action);
  
  // Format time in local timezone
  const logDate = new Date(log.performed_at);
  const time = logDate.toLocaleTimeString(language === 'vi' ? 'vi-VN' : 'en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
  
  // Check if log is from today
  const today = new Date();
  const isToday = logDate.toDateString() === today.toDateString();
  
  // If not today, include date
  const displayTime = isToday ? time : logDate.toLocaleDateString(language === 'vi' ? 'vi-VN' : 'en-US', {
    month: '2-digit',
    day: '2-digit'
  }) + ' ' + time;

  // Show max 3 changes in summary
  const visibleChanges = log.changes.slice(0, 3);
  const hiddenCount = log.changes.length - visibleChanges.length;

  return (
    <div className={`border ${config.borderColor} ${config.bgColor} rounded-lg p-2 hover:shadow-md transition-all`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {/* Header - Single compact line */}
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="text-base">{config.icon}</span>
            <span className={`font-bold text-sm ${config.textColor}`}>
              {getActionLabel(log.action)}
            </span>
            <span className="text-gray-400 text-xs">//</span>
            <span className="text-xs text-gray-600">{displayTime}</span>
            <span className="text-gray-400 text-xs">//</span>
            <span className="text-xs text-gray-600">{log.performed_by_name}</span>
          </div>

          {/* All Info in Single Line */}
          <div className="text-xs text-gray-700 leading-tight">
            {/* Crew & Ship */}
            <span className="font-semibold">{log.entity_name}</span>
            {log.ship_name && log.ship_name !== '-' && (
              <span className="text-gray-600"> // 🚢 {log.ship_name}</span>
            )}
            
            {/* Changes */}
            {visibleChanges.length > 0 && (
              <>
                <span className="text-gray-400 mx-1">//</span>
                {visibleChanges.map((change, index) => (
                  <span key={index}>
                    <span className="font-medium">{change.field_label}:</span>{' '}
                    <span className="text-gray-500">"{change.old_value || '-'}"</span>
                    {' → '}
                    <span className="text-gray-900 font-semibold">"{change.new_value || '-'}"</span>
                    {index < visibleChanges.length - 1 && <span className="text-gray-400 mx-1">//</span>}
                  </span>
                ))}
                {hiddenCount > 0 && (
                  <span className="text-gray-500 italic ml-1">
                    {language === 'vi' 
                      ? `+${hiddenCount} thay đổi khác...`
                      : `+${hiddenCount} more...`}
                  </span>
                )}
              </>
            )}
            
            {/* Notes */}
            {log.notes && (
              <>
                <span className="text-gray-400 mx-1">//</span>
                <span className="text-gray-600 italic">📝 {log.notes}</span>
              </>
            )}
          </div>
        </div>

        {/* View Details Button - Compact */}
        <button
          onClick={() => onViewDetails(log)}
          className="bg-white hover:bg-gray-50 border border-gray-300 hover:border-gray-400 px-1.5 py-0.5 rounded text-xs font-medium transition-all whitespace-nowrap flex items-center gap-1 flex-shrink-0"
        >
          <span>{language === 'vi' ? 'Chi tiết' : 'Details'}</span>
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
};
