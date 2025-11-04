/**
 * Audit Upcoming Survey Modal Component
 * Display upcoming surveys for audit certificates
 */
import React from 'react';
import { formatDateDisplay } from '../../utils/dateHelpers';

export const AuditUpcomingSurveyModal = ({
  isOpen,
  onClose,
  surveys = [],
  totalCount = 0,
  companyName = '',
  checkDate = '',
  language
}) => {
  if (!isOpen) return null;

  // Use company name if available
  const displayCompany = companyName;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[70] p-4">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="mb-6">
          <h3 className="text-xl font-bold text-orange-600 mb-2 flex items-center">
            ⚠️ {language === 'vi' ? 'Thông báo Survey sắp đến hạn' : 'Upcoming Survey Notification'}
          </h3>
          <p className="text-gray-700 mb-4">
            {language === 'vi' 
              ? 'Các Audit Certificate sau cần đánh giá trong thời gian tới, hãy bố trí đánh giá sớm nhất:'
              : 'The following audit certificates require review in the coming period. Please arrange assessments as soon as possible:'}
              </h2>
              <p className="text-orange-100 text-sm">
                {companyName} | {language === 'vi' ? 'Ngày kiểm tra:' : 'Check date:'} {formatDateDisplay(checkDate)}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:text-orange-200 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Summary */}
        <div className="px-6 py-4 bg-orange-50 border-b border-orange-200">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-orange-800 font-semibold">
              {language === 'vi' 
                ? `Tổng cộng ${totalCount} audit certificate cần đánh giá trong những ngày tới`
                : `Total ${totalCount} audit certificates require review in the coming days`
              }
            </p>
          </div>
        </div>

        {/* Survey List */}
        <div className="overflow-y-auto max-h-[50vh] p-6">
          {surveys && surveys.length > 0 ? (
            <div className="space-y-3">
              {surveys.map((cert, index) => (
                <div key={cert.id || index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow bg-white">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg font-bold text-blue-600">{index + 1}.</span>
                        <h3 className="font-semibold text-gray-900">{cert.cert_abbreviation || cert.cert_name}</h3>
                      </div>
                      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-gray-600">
                        <p><span className="font-medium">{language === 'vi' ? 'Tàu:' : 'Ship:'}</span> {cert.ship_name}</p>
                        <p><span className="font-medium">{language === 'vi' ? 'Số:' : 'No:'}</span> {cert.cert_no}</p>
                        <p><span className="font-medium">{language === 'vi' ? 'Kiểm tra tới:' : 'Next Survey:'}</span> {formatDateDisplay(cert.next_survey)}</p>
                        <p><span className="font-medium">{language === 'vi' ? 'Loại:' : 'Type:'}</span> {cert.next_survey_type || 'N/A'}</p>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <span className="px-3 py-1 bg-orange-100 text-orange-800 text-xs font-medium rounded-full">
                        {cert.next_survey_type || 'Survey'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <svg className="w-16 h-16 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-lg font-medium">
                {language === 'vi' 
                  ? '🎉 Không có audit certificate nào cần đánh giá trong những ngày tới!'
                  : '🎉 No audit certificates require review in the coming days!'
                }
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-all"
          >
            {language === 'vi' ? 'Đóng' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );
};
