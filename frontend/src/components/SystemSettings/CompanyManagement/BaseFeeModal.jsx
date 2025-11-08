import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';

const BaseFeeModal = ({ onClose, language = 'en', currentBaseFee, onUpdate }) => {
  const [baseFee, setBaseFee] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentBaseFee !== null && currentBaseFee !== undefined) {
      setBaseFee(currentBaseFee.toString());
    }
  }, [currentBaseFee]);

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    const feeValue = parseFloat(baseFee);
    if (isNaN(feeValue) || feeValue < 0) {
      toast.error(language === 'vi' ? 'Vui lòng nhập số hợp lệ (≥ 0)' : 'Please enter a valid number (≥ 0)');
      return;
    }

    setLoading(true);
    try {
      await onUpdate(feeValue);
      toast.success(language === 'vi' ? 'Cập nhật Base Fee thành công!' : 'Base Fee updated successfully!');
      onClose();
    } catch (error) {
      console.error('Error updating base fee:', error);
      toast.error(language === 'vi' ? 'Lỗi khi cập nhật Base Fee' : 'Error updating Base Fee');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (!value) return '';
    return new Intl.NumberFormat('en-US').format(value);
  };

  const handleBaseFeeChange = (e) => {
    const value = e.target.value.replace(/,/g, ''); // Remove commas
    if (value === '' || /^\d*\.?\d*$/.test(value)) {
      setBaseFee(value);
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-600 to-orange-700 text-white px-6 py-4 rounded-t-xl flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="bg-white bg-opacity-20 p-2 rounded-lg">
              💰
            </div>
            <h2 className="text-xl font-bold">
              {language === 'vi' ? 'Chỉnh sửa Base Fee' : 'Edit Base Fee'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20 p-2 rounded-lg transition-all"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-blue-700">
              {language === 'vi' 
                ? 'Base Fee là phí cơ bản áp dụng cho toàn bộ hệ thống. Giá trị này sẽ được sử dụng để tính toán chi phí.'
                : 'Base Fee is the system-wide base cost. This value will be used for cost calculations.'
              }
            </p>
          </div>

          {/* Base Fee Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Base Fee (USD)' : 'Base Fee (USD)'} *
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 font-semibold">
                $
              </span>
              <input
                type="text"
                value={baseFee}
                onChange={handleBaseFeeChange}
                className="w-full pl-8 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                placeholder="0.00"
                required
                disabled={loading}
              />
            </div>
            {baseFee && !isNaN(parseFloat(baseFee)) && (
              <p className="text-xs text-gray-500 mt-1">
                {language === 'vi' ? 'Định dạng: ' : 'Formatted: '}
                <span className="font-semibold text-gray-700">
                  ${formatCurrency(parseFloat(baseFee))}
                </span>
              </p>
            )}
          </div>

          {/* Info */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-xs text-yellow-800">
              ⚠️ {language === 'vi' 
                ? 'Thay đổi Base Fee sẽ ảnh hưởng đến toàn bộ hệ thống.'
                : 'Changing Base Fee will affect the entire system.'
              }
            </p>
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
              className="flex-1 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading 
                ? (language === 'vi' ? 'Đang lưu...' : 'Saving...')
                : (language === 'vi' ? 'Lưu' : 'Save')
              }
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BaseFeeModal;
