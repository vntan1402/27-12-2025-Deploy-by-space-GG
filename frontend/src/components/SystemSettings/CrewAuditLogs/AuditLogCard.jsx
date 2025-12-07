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
    <div className={`border-2 ${config.borderColor} ${config.bgColor} rounded-lg p-4 hover:shadow-md transition-all`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          {/* Header */}
          <div className="flex items-center gap-3 mb-2">
            <span className="text-2xl">{config.icon}</span>
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`font-bold ${config.textColor} text-lg`}>
                  {getActionLabel(log.action)}
                </span>
                <span className="text-gray-400">•</span>
                <span className="text-sm text-gray-600 font-medium">{time}</span>
              </div>
            </div>
          </div>

          {/* Crew Info */}
          <div className="mb-3">
            <div className="flex items-center gap-2 text-gray-900">
              <span className="font-semibold">{language === 'vi' ? 'Crew:' : 'Crew:'}</span>
              <span className="font-bold text-lg">{log.entity_name}</span>
            </div>
            {log.ship_name && log.ship_name !== '-' && (
              <div className="flex items-center gap-2 text-gray-700 mt-1">
                <span className="text-sm">{language === 'vi' ? 'Tàu:' : 'Ship:'}</span>
                <span className="text-sm font-medium">{log.ship_name}</span>
              </div>
            )}
          </div>

          {/* User Info */}
          <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
            <span>{language === 'vi' ? 'Thực hiện bởi:' : 'By:'}</span>
            <span className="font-medium">{log.performed_by_name}</span>
            <span className="text-gray-400">({log.performed_by})</span>
          </div>

          {/* Changes Summary */}
          {visibleChanges.length > 0 && (
            <div className="space-y-1 mb-3">
              <div className="text-sm font-semibold text-gray-700 mb-1">
                {language === 'vi' ? 'Thay đổi:' : 'Changes:'}
              </div>
              {visibleChanges.map((change, index) => (
                <div key={index} className="text-sm text-gray-700 pl-3">
                  • <span className="font-medium">{change.field_label}:</span>{' '}
                  <span className="text-gray-500">"{change.old_value || '-'}"</span>
                  {' → '}
                  <span className="text-gray-900 font-semibold">"{change.new_value || '-'}"</span>
                </div>
              ))}
              {hiddenCount > 0 && (
                <div className="text-sm text-gray-500 italic pl-3">
                  {language === 'vi' 
                    ? `+ ${hiddenCount} thay đổi khác...`
                    : `+ ${hiddenCount} more change${hiddenCount > 1 ? 's' : ''}...`}
                </div>
              )}
            </div>
          )}

          {/* Notes */}
          {log.notes && (
            <div className="bg-white bg-opacity-50 border border-gray-200 rounded px-3 py-2 text-sm text-gray-700 mb-3">
              <span className="font-medium">📝 </span>
              {log.notes}
            </div>
          )}
        </div>

        {/* View Details Button */}
        <button
          onClick={() => onViewDetails(log)}
          className="bg-white hover:bg-gray-50 border-2 border-gray-300 hover:border-gray-400 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap flex items-center gap-2"
        >
          <span>{language === 'vi' ? 'Chi tiết' : 'Details'}</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
};
