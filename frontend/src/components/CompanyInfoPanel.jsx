/**
 * Company Info Panel
 * Displays company information when no ship is selected (filter = All or -)
 * Matches ShipDetailPanel layout with logo on left, info on right
 */
import React from 'react';
import { useAuth } from '../contexts/AuthContext';

export const CompanyInfoPanel = ({ companyData, onClose }) => {
  const { language } = useAuth();

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString(language === 'vi' ? 'vi-VN' : 'en-US');
    } catch {
      return dateString;
    }
  };

  // Calculate days remaining
  const getDaysRemaining = (expiryDate) => {
    if (!expiryDate) return null;
    try {
      const today = new Date();
      const expiry = new Date(expiryDate);
      const diffTime = expiry - today;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      return diffDays;
    } catch {
      return null;
    }
  };

  const daysRemaining = companyData?.software_expiry ? getDaysRemaining(companyData.software_expiry) : null;

  return (
    <div className="grid md:grid-cols-3 gap-6 mb-6">
      {/* Company Logo - Left Side (1/3 width) */}
      <div className="md:col-span-1">
        <div className="bg-gray-200 rounded-lg p-4 h-48 flex items-center justify-center">
          {companyData?.logo_url && companyData.logo_url !== '' ? (
            <img 
              src={companyData.logo_url} 
              alt="Company Logo" 
              className="max-w-full max-h-40 object-contain"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.parentElement.innerHTML = '<div class="text-center"><div class="text-4xl mb-2">🏢</div><p class="font-semibold">COMPANY LOGO</p></div>';
              }}
            />
          ) : (
            <div className="text-center">
              <div className="text-4xl mb-2">🏢</div>
              <p className="font-semibold">COMPANY LOGO</p>
            </div>
          )}
        </div>
      </div>
        
        {/* Company Info - Right Side (2/3 width) */}
        <div className="md:col-span-2">
          {/* Header with company name and close button */}
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-800">
              {companyData?.name || (language === 'vi' ? 'Công ty' : 'Company')}
            </h2>
            
            {onClose && (
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 text-xl px-2 py-1"
                title={language === 'vi' ? 'Đóng' : 'Close'}
              >
                ✕
              </button>
            )}
          </div>
          
          {/* Company Info - 3 columns grid */}
          <div className="grid grid-cols-3 gap-4 text-sm">
            {/* Row 1 */}
            <div className="col-span-3">
              <span className="font-semibold">{language === 'vi' ? 'Tên công ty:' : 'Company Name:'}</span>
              <span className="ml-2">{companyData?.name || '-'}</span>
            </div>
            
            {companyData?.email && (
              <div>
                <span className="font-semibold">Email:</span>
                <span className="ml-2 text-blue-600">{companyData.email}</span>
              </div>
            )}
            
            {companyData?.phone && (
              <div>
                <span className="font-semibold">{language === 'vi' ? 'Điện thoại:' : 'Phone:'}</span>
                <span className="ml-2">{companyData.phone}</span>
              </div>
            )}
            
            <div>
              <span className="font-semibold">{language === 'vi' ? 'Số tàu:' : 'Total Ships:'}</span>
              <span className="ml-2">{companyData?.total_ships || 0}</span>
            </div>
            
            {/* Row 2 */}
            {companyData?.address && (
              <div className="col-span-2">
                <span className="font-semibold">{language === 'vi' ? 'Địa chỉ:' : 'Address:'}</span>
                <span className="ml-2">{companyData.address}</span>
              </div>
            )}
            
            {companyData?.software_expiry && (
              <div>
                <span className="font-semibold">{language === 'vi' ? 'Hạn PM:' : 'SW Expiry:'}</span>
                <span className="ml-2">{formatDate(companyData.software_expiry)}</span>
                {daysRemaining !== null && (
                  <span className={`ml-2 text-xs ${
                    daysRemaining > 30 ? 'text-green-600' : 
                    daysRemaining > 0 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    ({daysRemaining > 0 ? `${daysRemaining}d` : language === 'vi' ? 'Hết hạn' : 'Expired'})
                  </span>
                )}
              </div>
            )}
            
            {/* Row 3 - View mode info */}
            <div className="col-span-3 pt-2 border-t border-gray-200">
              <span className="font-semibold">{language === 'vi' ? 'Chế độ xem:' : 'View Mode:'}</span>
              <span className="ml-2 text-blue-600">
                {language === 'vi' ? 'Tất cả thuyền viên công ty' : 'All Company Crew Members'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
