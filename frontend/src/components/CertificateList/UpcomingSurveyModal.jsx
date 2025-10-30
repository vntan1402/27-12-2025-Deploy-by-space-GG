/**
 * Upcoming Survey Modal Component
 * Shows certificates with upcoming survey dates
 * Based on V1 Upcoming Survey Notification (lines 22608-22717)
 */
import React from 'react';
import { formatDateDisplay } from '../../utils/dateHelpers';

export const UpcomingSurveyModal = ({
  isOpen,
  onClose,
  surveys = [],
  totalCount = 0,
  company = '',
  checkDate = '',
  language
}) => {
  if (!isOpen) return null;

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
              ? 'Các Giấy chứng nhận sau sắp đến hạn kiểm tra, hãy bố trí kiểm tra trong thời gian sớm nhất:'
              : 'The following certificates are approaching their survey dates. Please arrange inspections as soon as possible:'}
          </p>
          <div className="text-sm text-gray-600 mb-4">
            {language === 'vi' 
              ? `Tổng cộng: ${totalCount} chứng chỉ | Công ty: ${company}`
              : `Total: ${totalCount} certificates | Company: ${company}`}
          </div>
          {checkDate && (
            <div className="text-xs text-gray-500">
              {language === 'vi' ? 'Ngày kiểm tra: ' : 'Check date: '}
              {new Date(checkDate).toLocaleDateString()}
            </div>
          )}
        </div>

        {/* Certificates Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border border-gray-200 rounded-lg">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                  {language === 'vi' ? 'Tên Tàu' : 'Ship Name'}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                  {language === 'vi' ? 'Tên Chứng chỉ' : 'Cert. Name (Abbreviation)'}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                  {language === 'vi' ? 'Next Survey' : 'Next Survey'}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                  {language === 'vi' ? 'Loại Survey' : 'Next Survey Type'}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                  {language === 'vi' ? 'Last Endorse' : 'Last Endorse'}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                  {language === 'vi' ? 'Tình trạng' : 'Status'}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {surveys.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-4 py-8 text-center text-gray-500">
                    {language === 'vi' 
                      ? '✅ Không có survey sắp đến hạn'
                      : '✅ No upcoming surveys'}
                  </td>
                </tr>
              ) : (
                surveys.map((survey, index) => (
                  <tr 
                    key={index} 
                    className={`hover:bg-gray-50 ${
                      survey.is_overdue ? 'bg-red-50' : 
                      survey.is_due_soon ? 'bg-yellow-50' : 
                      ''
                    }`}
                  >
                    <td className="px-4 py-3 text-sm text-gray-900 border-b">
                      <div className="font-medium">{survey.ship_name}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 border-b">
                      <div className="font-medium">{survey.cert_name_display}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 border-b">
                      <div className="font-medium">{formatDateDisplay(survey.next_survey)}</div>
                      <div className="text-xs text-gray-500">
                        {survey.days_until_survey >= 0 
                          ? (language === 'vi' ? `Còn ${survey.days_until_survey} ngày` : `${survey.days_until_survey} days left`)
                          : (language === 'vi' ? `Quá hạn ${Math.abs(survey.days_until_survey)} ngày` : `${Math.abs(survey.days_until_survey)} days overdue`)
                        }
                      </div>
                      {survey.window_type && (
                        <div className="text-xs text-blue-600 font-medium">
                          {survey.window_type}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 border-b">
                      {survey.next_survey_type || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 border-b">
                      {formatDateDisplay(survey.last_endorse)}
                    </td>
                    <td className="px-4 py-3 text-sm border-b">
                      {survey.is_critical ? (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                          {survey.is_overdue 
                            ? (language === 'vi' ? 'Quá hạn' : 'Overdue')
                            : (language === 'vi' ? 'Khẩn cấp' : 'Critical')
                          }
                        </span>
                      ) : survey.is_due_soon ? (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                          {language === 'vi' ? 'Sắp đến hạn' : 'Due Soon'}
                        </span>
                      ) : (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                          {language === 'vi' ? 'Trong Window' : 'In Window'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Action Buttons */}
        <div className="mt-6 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition duration-200"
          >
            {language === 'vi' ? 'Đã hiểu' : 'Got it'}
          </button>
        </div>
      </div>
    </div>
  );
};
