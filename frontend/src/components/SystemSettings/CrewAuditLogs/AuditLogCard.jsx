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
      BULK_UPDATE: { icon: '📋', color: 'teal', bgColor: 'bg-teal-50', borderColor: 'border-teal-200', textColor: 'text-teal-800' }
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
      BULK_UPDATE: language === 'vi' ? 'Cập nhật hàng loạt' : 'Bulk Update'
    };
    return labels[action] || action;
  };

  const config = getActionConfig(log.action);
  const time = new Date(log.performed_at).toLocaleTimeString(language === 'vi' ? 'vi-VN' : 'en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });

  // Show max 3 changes in summary
  const visibleChanges = log.changes.slice(0, 3);
  const hiddenCount = log.changes.length - visibleChanges.length;

  return (
    <div className={`border ${config.borderColor} ${config.bgColor} rounded-lg p-3 hover:shadow-md transition-all`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {/* Header - Single compact line */}
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xl">{config.icon}</span>
            <span className={`font-bold ${config.textColor}`}>
              {getActionLabel(log.action)}
            </span>
            <span className="text-gray-400 text-xs">•</span>
            <span className="text-xs text-gray-600">{time}</span>
            <span className="text-gray-400 text-xs">•</span>
            <span className="text-xs text-gray-600">{log.performed_by_name}</span>
          </div>

          {/* Crew & Ship Info - Compact */}
          <div className="mb-1.5">
            <span className="text-sm text-gray-700">
              <span className="font-semibold">{log.entity_name}</span>
              {log.ship_name && log.ship_name !== '-' && (
                <span className="text-gray-600"> • 🚢 {log.ship_name}</span>
              )}
            </span>
          </div>

          {/* Changes Summary - Compact */}
          {visibleChanges.length > 0 && (
            <div className="space-y-0.5">
              {visibleChanges.map((change, index) => (
                <div key={index} className="text-xs text-gray-700">
                  <span className="font-medium">{change.field_label}:</span>{' '}
                  <span className="text-gray-500">"{change.old_value || '-'}"</span>
                  {' → '}
                  <span className="text-gray-900 font-semibold">"{change.new_value || '-'}"</span>
                </div>
              ))}
              {hiddenCount > 0 && (
                <div className="text-xs text-gray-500 italic">
                  {language === 'vi' 
                    ? `+${hiddenCount} thay đổi khác...`
                    : `+${hiddenCount} more...`}
                </div>
              )}
            </div>
          )}

          {/* Notes - Compact */}
          {log.notes && (
            <div className="mt-1.5 text-xs text-gray-600 italic">
              📝 {log.notes}
            </div>
          )}
        </div>

        {/* View Details Button - Compact */}
        <button
          onClick={() => onViewDetails(log)}
          className="bg-white hover:bg-gray-50 border border-gray-300 hover:border-gray-400 px-2 py-1 rounded text-xs font-medium transition-all whitespace-nowrap flex items-center gap-1 flex-shrink-0"
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
