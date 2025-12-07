/**
 * Audit Log Detail Modal
 * Shows comprehensive details of a single audit log entry
 */
import React from 'react';

export const AuditLogDetailModal = ({ log, onClose, language }) => {
  // Get action icon
  const getActionIcon = (action) => {
    const icons = {
      CREATE: '➕',
      UPDATE: '🔄',
      DELETE: '🗑️',
      SIGN_ON: '🚢',
      SIGN_OFF: '🏝️',
      SHIP_TRANSFER: '🔀',
      BULK_UPDATE: '📋'
    };
    return icons[action] || '📝';
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

  const formatDateTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString(language === 'vi' ? 'vi-VN' : 'en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[9999] p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl my-8">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className="text-5xl">{getActionIcon(log.action)}</div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  {getActionLabel(log.action)} - {language === 'vi' ? 'Chi tiết Log' : 'Log Detail'}
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  {language === 'vi' ? 'Thông tin chi tiết về thao tác này' : 'Comprehensive details about this operation'}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-all text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
          {/* Basic Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">📋</span>
              <span className="text-sm font-bold text-blue-900 uppercase">
                {language === 'vi' ? 'Thông tin cơ bản' : 'Basic Information'}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-semibold text-gray-700">{language === 'vi' ? 'Log ID:' : 'Log ID:'}</span>
                <div className="text-gray-900 font-mono bg-white px-2 py-1 rounded mt-1">{log.id}</div>
              </div>
              <div>
                <span className="font-semibold text-gray-700">{language === 'vi' ? 'Crew ID:' : 'Crew ID:'}</span>
                <div className="text-gray-900 font-mono bg-white px-2 py-1 rounded mt-1">{log.entity_id}</div>
              </div>
              <div>
                <span className="font-semibold text-gray-700">{language === 'vi' ? 'Tên Crew:' : 'Crew Name:'}</span>
                <div className="text-gray-900 font-bold bg-white px-2 py-1 rounded mt-1">{log.entity_name}</div>
              </div>
              <div>
                <span className="font-semibold text-gray-700">{language === 'vi' ? 'Thao tác:' : 'Action:'}</span>
                <div className="text-gray-900 font-bold bg-white px-2 py-1 rounded mt-1">{getActionLabel(log.action)}</div>
              </div>
              {log.ship_name && (
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Tàu:' : 'Ship:'}</span>
                  <div className="text-gray-900 font-medium bg-white px-2 py-1 rounded mt-1">{log.ship_name}</div>
                </div>
              )}
              <div>
                <span className="font-semibold text-gray-700">{language === 'vi' ? 'Người thực hiện:' : 'Performed by:'}</span>
                <div className="text-gray-900 bg-white px-2 py-1 rounded mt-1">
                  {log.performed_by_name} <span className="text-gray-500">({log.performed_by})</span>
                </div>
              </div>
              <div>
                <span className="font-semibold text-gray-700">{language === 'vi' ? 'Thời gian:' : 'Timestamp:'}</span>
                <div className="text-gray-900 bg-white px-2 py-1 rounded mt-1">{formatDateTime(log.performed_at)}</div>
              </div>
              <div>
                <span className="font-semibold text-gray-700">{language === 'vi' ? 'Nguồn:' : 'Source:'}</span>
                <div className="text-gray-900 bg-white px-2 py-1 rounded mt-1">{log.source}</div>
              </div>
            </div>
          </div>

          {/* Changes */}
          {log.changes && log.changes.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">🔄</span>
                <span className="text-sm font-bold text-yellow-900 uppercase">
                  {language === 'vi' ? `Thay đổi (${log.changes.length})` : `Changes (${log.changes.length})`}
                </span>
              </div>
              <div className="space-y-3">
                {log.changes.map((change, index) => (
                  <div key={index} className="bg-white border border-gray-200 rounded-lg p-3">
                    <div className="font-semibold text-gray-900 mb-2">
                      {index + 1}. {change.field_label}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <div className="text-xs text-gray-500 mb-1">
                          {language === 'vi' ? 'Trước:' : 'Before:'}
                        </div>
                        <div className="bg-red-50 border border-red-200 px-3 py-2 rounded text-gray-900">
                          {change.old_value === null || change.old_value === '' ? '-' : String(change.old_value)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 mb-1">
                          {language === 'vi' ? 'Sau:' : 'After:'}
                        </div>
                        <div className="bg-green-50 border border-green-200 px-3 py-2 rounded text-gray-900 font-semibold">
                          {change.new_value === null || change.new_value === '' ? '-' : String(change.new_value)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          {log.notes && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xl">📝</span>
                <span className="text-sm font-bold text-gray-900 uppercase">
                  {language === 'vi' ? 'Ghi chú' : 'Notes'}
                </span>
              </div>
              <p className="text-gray-700 leading-relaxed">{log.notes}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium transition-all"
          >
            {language === 'vi' ? 'Đóng' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );
};
