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
        <div className="grid grid-cols-3 gap-6 text-sm">
          {/* Column 1: Company Name, Email, Phone */}
          <div className="space-y-3">
            <div>
              <div className="text-xs text-gray-500 mb-1">{language === 'vi' ? 'Tên công ty' : 'Company Name'}</div>
              <div className="font-bold text-base text-gray-800">{companyData?.name || '-'}</div>
            </div>
            
            {companyData?.email && (
              <div>
                <div className="text-xs text-gray-500 mb-1">Email</div>
                <div className="text-blue-600">{companyData.email}</div>
              </div>
            )}
            
            {companyData?.phone && (
              <div>
                <div className="text-xs text-gray-500 mb-1">{language === 'vi' ? 'Điện thoại' : 'Phone'}</div>
                <div>{companyData.phone}</div>
              </div>
            )}
          </div>
          
          {/* Column 2: Total Ships, Total Crew */}
          <div className="space-y-3">
            <div>
              <div className="text-xs text-gray-500 mb-1">{language === 'vi' ? 'Số tàu' : 'Total Ships'}</div>
              <div className="font-bold text-2xl text-blue-600">{companyData?.total_ships || 0}</div>
            </div>
            
            <div>
              <div className="text-xs text-gray-500 mb-1">{language === 'vi' ? 'Tổng thuyền viên' : 'Total Crew'}</div>
              <div className="font-bold text-2xl text-green-600">{companyData?.total_crew || 0}</div>
            </div>
          </div>
          
          {/* Column 3: Software Expiry and Notice (uses both rows if notice needed) */}
          <div className="space-y-3">
            <div>
              <div className="text-xs text-gray-500 mb-1">{language === 'vi' ? 'Hạn phần mềm' : 'Software Expiry'}</div>
              <div className="font-semibold">
                {companyData?.software_expiry ? formatDate(companyData.software_expiry) : '-'}
                {daysRemaining !== null && (
                  <span className={`ml-2 text-xs ${
                    daysRemaining > 30 ? 'text-green-600' : 
                    daysRemaining > 0 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    ({daysRemaining > 0 ? `${daysRemaining}d` : language === 'vi' ? 'Hết hạn' : 'Expired'})
                  </span>
                )}
              </div>
            </div>
            
            {/* Notice - Only show if less than 30 days remaining */}
            {daysRemaining !== null && daysRemaining < 30 && daysRemaining >= 0 && (
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded">
                <div className="flex items-start">
                  <span className="text-yellow-600 mr-2 text-lg">⚠️</span>
                  <div>
                    <div className="font-semibold text-yellow-800 text-xs mb-1">
                      {language === 'vi' ? 'Lưu ý' : 'Notice'}
                    </div>
                    <div className="text-xs text-yellow-700 leading-relaxed">
                      {language === 'vi' 
                        ? 'Phần mềm sắp hết hạn, hãy gia hạn phần mềm để tiếp tục sử dụng.'
                        : 'Software is about to expire, please renew to continue using.'
                      }
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Expired Notice */}
            {daysRemaining !== null && daysRemaining < 0 && (
              <div className="bg-red-50 border-l-4 border-red-400 p-3 rounded">
                <div className="flex items-start">
                  <span className="text-red-600 mr-2 text-lg">🚫</span>
                  <div>
                    <div className="font-semibold text-red-800 text-xs mb-1">
                      {language === 'vi' ? 'Cảnh báo' : 'Warning'}
                    </div>
                    <div className="text-xs text-red-700 leading-relaxed">
                      {language === 'vi' 
                        ? 'Phần mềm đã hết hạn! Vui lòng liên hệ để gia hạn ngay.'
                        : 'Software has expired! Please contact us to renew immediately.'
                      }
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
