/**
 * Certificate Action Buttons Component  
 * Top action buttons for certificate list
 * Extracted from Frontend V1 App.js (lines 13540-13626)
 */
import React from 'react';

export const CertificateActionButtons = ({
  language,
  selectedShip,
  selectedCertificatesCount = 0,
  isUpdatingSurveyTypes = false,
  isMultiCertProcessing = false,
  isRefreshing = false,
  linksFetching = false,
  linksFetchProgress = { ready: 0, total: 0 },
  onUpdateSurveyTypes,
  onUpcomingSurvey,
  onAddCertificate,
  onRefresh,
}) => {
  return (
    <div className="flex justify-between items-center mb-4">
      <div className="flex items-center gap-3">
        <h3 className="text-lg font-semibold text-gray-800">
          {language === 'vi' ? 'Danh mục Giấy chứng nhận' : 'Certificate List'}
        </h3>
        
        {/* Selection Indicator */}
        {selectedCertificatesCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {selectedCertificatesCount} {language === 'vi' ? 'đã chọn' : 'selected'}
          </div>
        )}

        {/* Links Loading Indicator */}
        {linksFetching && (
          <div className="flex items-center gap-2 px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm">
            <svg className="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {language === 'vi' ? 'Đang tải links...' : 'Loading links...'}
          </div>
        )}

        {/* Links Ready Indicator */}
        {!linksFetching && linksFetchProgress.total > 0 && (
          <div className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            {linksFetchProgress.ready}/{linksFetchProgress.total} {language === 'vi' ? 'links sẵn sàng' : 'links ready'}
          </div>
        )}
      </div>
      
      <div className="flex gap-3">
        {/* Update Next Survey Button */}
        <button
          onClick={onUpdateSurveyTypes}
          disabled={isUpdatingSurveyTypes || !selectedShip}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            selectedShip && !isUpdatingSurveyTypes
              ? 'bg-purple-600 hover:bg-purple-700 text-white cursor-pointer'
              : 'bg-gray-400 cursor-not-allowed text-white'
          }`}
          title={selectedShip 
            ? (language === 'vi' ? 'Cập nhật loại kiểm tra tới' : 'Update next survey types')
            : (language === 'vi' ? 'Vui lòng chọn tàu trước' : 'Please select a ship first')
          }
        >
          {isUpdatingSurveyTypes ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {language === 'vi' ? 'Đang cập nhật...' : 'Updating...'}
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {language === 'vi' ? 'Cập nhật Next Survey' : 'Update Next Survey'}
            </>
          )}
        </button>

        {/* Upcoming Survey Button */}
        <button
          onClick={onUpcomingSurvey}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all bg-orange-600 hover:bg-orange-700 text-white cursor-pointer"
          title={language === 'vi' ? 'Kiểm tra các chứng chỉ sắp đến hạn survey' : 'Check upcoming survey certificates'}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {language === 'vi' ? 'Upcoming Survey' : 'Upcoming Survey'}
        </button>
        
        {/* Add Certificate Button */}
        <button
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            selectedShip && !isMultiCertProcessing
              ? 'bg-green-600 hover:bg-green-700 text-white cursor-pointer'
              : 'bg-gray-400 cursor-not-allowed text-white'
          }`}
          title={selectedShip 
            ? (language === 'vi' ? 'Mở form thêm chứng chỉ' : 'Open add certificate form')
            : (language === 'vi' ? 'Vui lòng chọn tàu trước' : 'Please select a ship first')
          }
          onClick={onAddCertificate}
          disabled={!selectedShip || isMultiCertProcessing}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {isMultiCertProcessing 
            ? (language === 'vi' ? '⏳ Đang xử lý...' : '⏳ Processing...')
            : (language === 'vi' ? '📋 Thêm chứng chỉ' : '📋 Add Certificate')
          }
        </button>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg text-sm font-medium transition-all"
        >
          <span className={`${isRefreshing ? 'animate-spin' : ''}`}>🔄</span>
          {isRefreshing 
            ? (language === 'vi' ? 'Đang cập nhật...' : 'Refreshing...') 
            : (language === 'vi' ? 'Refresh' : 'Refresh')
          }
        </button>
      </div>
    </div>
  );
};
