/**
 * Company Info Panel
 * Displays company information when no ship is selected (filter = All)
 */
import React from 'react';
import { useAuth } from '../contexts/AuthContext';

export const CompanyInfoPanel = ({ companyName, onClose }) => {
  const { language } = useAuth();

  return (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-6 mb-6">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-3">
            <div className="bg-white/20 p-3 rounded-lg">
              <span className="text-3xl">🏢</span>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">
                {companyName || (language === 'vi' ? 'Công ty' : 'Company')}
              </h2>
              <p className="text-blue-100 text-sm">
                {language === 'vi' ? 'Quản lý toàn công ty' : 'Company-wide Management'}
              </p>
            </div>
          </div>
          
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <p className="text-blue-100 text-xs mb-1">
                  {language === 'vi' ? 'Chế độ xem' : 'View Mode'}
                </p>
                <p className="text-white font-semibold flex items-center">
                  <span className="mr-2">👁️</span>
                  {language === 'vi' ? 'Tất cả thuyền viên' : 'All Crew Members'}
                </p>
              </div>
              
              <div>
                <p className="text-blue-100 text-xs mb-1">
                  {language === 'vi' ? 'Phạm vi' : 'Scope'}
                </p>
                <p className="text-white font-semibold flex items-center">
                  <span className="mr-2">🌐</span>
                  {language === 'vi' ? 'Toàn bộ đội tàu' : 'All Fleet'}
                </p>
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
