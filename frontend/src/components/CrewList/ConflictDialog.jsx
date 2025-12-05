import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const ConflictDialog = ({ 
  conflict, 
  onKeepCurrent, 
  onUseMyValue, 
  onCancel 
}) => {
  const { language } = useAuth();
  
  if (!conflict) return null;
  
  const { 
    current_ship, 
    current_status,
    updated_by,
    current_updated_at,
    your_values 
  } = conflict;
  
  const formatTime = (isoString) => {
    if (!isoString) return '-';
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
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-orange-200 bg-orange-50">
          <div className="flex items-start gap-4">
            <div className="text-5xl">⚠️</div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-orange-800">
                {language === 'vi' ? 'Phát hiện xung đột!' : 'Conflict Detected!'}
              </h2>
              <p className="text-sm text-orange-700 mt-1">
                {language === 'vi' 
                  ? 'Thuyền viên này đã được sửa bởi người khác trong khi bạn đang chỉnh sửa.' 
                  : 'This crew member was modified by another user while you were editing.'}
              </p>
            </div>
          </div>
        </div>
        
        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Modified Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-blue-800 font-semibold">ℹ️</span>
              <span className="text-sm font-bold text-blue-900">
                {language === 'vi' ? 'Thông tin cập nhật' : 'Update Information'}
              </span>
            </div>
            <div className="text-sm text-blue-800 space-y-1">
              <div>
                <span className="font-semibold">{language === 'vi' ? 'Người sửa:' : 'Modified by:'}</span> {updated_by || '-'}
              </div>
              <div>
                <span className="font-semibold">{language === 'vi' ? 'Thời gian:' : 'At:'}</span> {formatTime(current_updated_at)}
              </div>
            </div>
          </div>
          
          {/* Comparison Table */}
          <div className="border border-gray-300 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 border-r">
                    {language === 'vi' ? 'Trường' : 'Field'}
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 border-r bg-green-50">
                    {language === 'vi' ? 'Giá trị hiện tại (DB)' : 'Current Value (DB)'}
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 bg-yellow-50">
                    {language === 'vi' ? 'Giá trị của bạn' : 'Your Value'}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {your_values.ship_sign_on !== undefined && (
                  <tr>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 border-r">
                      {language === 'vi' ? 'Tàu đăng ký' : 'Ship Sign On'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 border-r bg-green-50 font-semibold">
                      {current_ship || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 bg-yellow-50 font-semibold">
                      {your_values.ship_sign_on || '-'}
                    </td>
                  </tr>
                )}
                
                {your_values.status !== undefined && (
                  <tr>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 border-r">
                      Status
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 border-r bg-green-50 font-semibold">
                      {current_status || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 bg-yellow-50 font-semibold">
                      {your_values.status || '-'}
                    </td>
                  </tr>
                )}
                
                {your_values.date_sign_on !== undefined && (
                  <tr>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 border-r">
                      {language === 'vi' ? 'Ngày xuống tàu' : 'Date Sign On'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 border-r bg-green-50">
                      -
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 bg-yellow-50">
                      {your_values.date_sign_on || '-'}
                    </td>
                  </tr>
                )}
                
                {your_values.date_sign_off !== undefined && (
                  <tr>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 border-r">
                      {language === 'vi' ? 'Ngày rời tàu' : 'Date Sign Off'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 border-r bg-green-50">
                      -
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 bg-yellow-50">
                      {your_values.date_sign_off || '-'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          {/* Warning */}
          <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-4">
            <p className="text-sm text-yellow-800">
              <span className="font-bold">⚡ {language === 'vi' ? 'Lưu ý:' : 'Note:'}</span>{' '}
              {language === 'vi' 
                ? 'Nếu bạn chọn "Dùng giá trị của tôi", bạn sẽ ghi đè những thay đổi của người khác.'
                : 'If you choose "Use My Value", you will overwrite the other user\'s changes.'}
            </p>
          </div>
        </div>
        
        {/* Actions */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 flex flex-wrap gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-5 py-2.5 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-medium transition-all"
          >
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          
          <button
            onClick={onKeepCurrent}
            className="px-5 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-all flex items-center gap-2"
          >
            <span>✓</span>
            <span>{language === 'vi' ? 'Giữ giá trị hiện tại' : 'Keep Current Value'}</span>
          </button>
          
          <button
            onClick={onUseMyValue}
            className="px-5 py-2.5 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition-all flex items-center gap-2"
          >
            <span>⚠️</span>
            <span>{language === 'vi' ? 'Dùng giá trị của tôi' : 'Use My Value'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
