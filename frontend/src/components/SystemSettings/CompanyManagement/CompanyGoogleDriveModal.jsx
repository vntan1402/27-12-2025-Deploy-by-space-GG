/**
 * CompanyGoogleDriveModal Component
 * Modal for configuring Google Drive for individual company
 * This is a placeholder - full implementation in later phase
 */
import React from 'react';

const CompanyGoogleDriveModal = ({
  company,
  onClose,
  language
}) => {
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4"
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? 'Cấu hình Google Drive' : 'Google Drive Configuration'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="text-center py-12">
            <div className="text-6xl mb-4">☁️</div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              {language === 'vi' 
                ? `Cấu hình Google Drive cho ${company.name_vn || company.name_en}`
                : `Configure Google Drive for ${company.name_en || company.name_vn}`
              }
            </h3>
            <p className="text-gray-600 mb-4">
              {language === 'vi' 
                ? 'Tính năng này sẽ được triển khai trong phase sau'
                : 'This feature will be implemented in a later phase'
              }
            </p>
            <button
              onClick={onClose}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-all"
            >
              {language === 'vi' ? 'Đóng' : 'Close'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanyGoogleDriveModal;
