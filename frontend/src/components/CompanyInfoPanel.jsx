/**
 * Company Info Panel
 * Displays company information when no ship is selected (filter = All or -)
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
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-6 mb-6 min-h-[280px]">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          {/* Header with Company Logo */}
          <div className="flex items-center space-x-4 mb-4">
            <div className="bg-white/20 p-4 rounded-lg backdrop-blur-sm">
              {companyData?.logo_url ? (
                <img 
                  src={companyData.logo_url} 
                  alt="Company Logo" 
                  className="w-16 h-16 object-contain"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.parentElement.innerHTML = '<span class="text-4xl">🏢</span>';
                  }}
                />
              ) : (
                <span className="text-4xl">🏢</span>
              )}
            </div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-white mb-1">
                {companyData?.name || (language === 'vi' ? 'Công ty' : 'Company')}
              </h2>
              <p className="text-blue-100 text-sm">
                {language === 'vi' ? 'Quản lý toàn công ty' : 'Company-wide Management'}
              </p>
            </div>
          </div>
          
          {/* Company Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* Left Column */}
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
              <div className="space-y-3">
                {companyData?.address && (
                  <div>
                    <p className="text-blue-100 text-xs mb-1 flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {language === 'vi' ? 'Địa chỉ' : 'Address'}
                    </p>
                    <p className="text-white font-semibold text-sm">
                      {companyData.address}
                    </p>
                  </div>
                )}
                
                {companyData?.email && (
                  <div>
                    <p className="text-blue-100 text-xs mb-1 flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      Email
                    </p>
                    <p className="text-white font-semibold text-sm">
                      {companyData.email}
                    </p>
                  </div>
                )}
                
                {companyData?.phone && (
                  <div>
                    <p className="text-blue-100 text-xs mb-1 flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                      </svg>
                      {language === 'vi' ? 'Điện thoại' : 'Phone'}
                    </p>
                    <p className="text-white font-semibold text-sm">
                      {companyData.phone}
                    </p>
                  </div>
                )}
              </div>
            </div>
            
            {/* Right Column */}
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
              <div className="space-y-3">
                {companyData?.software_expiry && (
                  <div>
                    <p className="text-blue-100 text-xs mb-1 flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      {language === 'vi' ? 'Thời hạn phần mềm' : 'Software Expiry'}
                    </p>
                    <p className="text-white font-semibold text-sm">
                      {formatDate(companyData.software_expiry)}
                    </p>
                    {daysRemaining !== null && (
                      <div className="mt-1">
                        {daysRemaining > 30 ? (
                          <span className="text-xs text-green-200">
                            ✓ {daysRemaining} {language === 'vi' ? 'ngày còn lại' : 'days remaining'}
                          </span>
                        ) : daysRemaining > 0 ? (
                          <span className="text-xs text-yellow-200">
                            ⚠️ {daysRemaining} {language === 'vi' ? 'ngày còn lại' : 'days remaining'}
                          </span>
                        ) : (
                          <span className="text-xs text-red-200">
                            ❌ {language === 'vi' ? 'Đã hết hạn' : 'Expired'}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                )}
                
                {companyData?.total_ships !== undefined && (
                  <div>
                    <p className="text-blue-100 text-xs mb-1 flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                      {language === 'vi' ? 'Số lượng tàu' : 'Total Ships'}
                    </p>
                    <p className="text-white font-semibold text-sm">
                      {companyData.total_ships} {language === 'vi' ? 'tàu' : 'ships'}
                    </p>
                  </div>
                )}
                
                <div>
                  <p className="text-blue-100 text-xs mb-1 flex items-center">
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    {language === 'vi' ? 'Chế độ xem' : 'View Mode'}
                  </p>
                  <p className="text-white font-semibold text-sm">
                    {language === 'vi' ? 'Tất cả thuyền viên' : 'All Crew Members'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {onClose && (
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white transition-colors ml-4"
            title={language === 'vi' ? 'Đóng' : 'Close'}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
      
      <div className="mt-4 pt-4 border-t border-white/20">
        <div className="flex items-center text-white/90 text-sm">
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>
            {language === 'vi' 
              ? 'Đang hiển thị thuyền viên từ tất cả các tàu. Chọn tàu cụ thể từ dropdown để lọc.'
              : 'Showing crew from all ships. Select a specific ship from dropdown to filter.'}
          </span>
        </div>
      </div>
    </div>
  );
};
