/**
 * Upcoming Survey Modal Component
 * Shows certificates with upcoming survey dates
 * Based on V1 Upcoming Survey Notification (lines 22608-22717)
 */
import React, { useState, useMemo } from 'react';
import { FileText, FileSpreadsheet } from 'lucide-react';
import { formatDateDisplay } from '../../utils/dateHelpers';
import { exportUpcomingSurveysToPDF, exportUpcomingSurveysToXLSX } from '../../utils/exportHelpers';
import { toast } from 'react-hot-toast';

export const UpcomingSurveyModal = ({
  isOpen,
  onClose,
  surveys = [],
  totalCount = 0,
  company = '',
  companyName = '',
  checkDate = '',
  language
}) => {
  const [shipFilter, setShipFilter] = useState('');

  // Use company name if available, fallback to company ID
  const displayCompany = companyName || company;

  // Get unique ship names for filter dropdown
  // Must be called before any conditional return to follow React hooks rules
  const shipNames = useMemo(() => {
    if (!surveys || surveys.length === 0) return [];
    const names = [...new Set(surveys.map(s => s.ship_name).filter(Boolean))];
    return names.sort();
  }, [surveys]);

  // Filter surveys by ship name
  // Must be called before any conditional return to follow React hooks rules
  const filteredSurveys = useMemo(() => {
    if (!surveys || surveys.length === 0) return [];
    if (!shipFilter) return surveys;
    return surveys.filter(s => s.ship_name === shipFilter);
  }, [surveys, shipFilter]);

  // Early return AFTER all hooks are called
  if (!isOpen) return null;

  // Export handlers
  const handleExportPDF = () => {
    try {
      exportUpcomingSurveysToPDF(filteredSurveys, {
        language,
        companyName: displayCompany,
        totalCount: filteredSurveys.length
      });
      toast.success(language === 'vi' ? 'Xuất PDF thành công!' : 'PDF exported successfully!');
    } catch (error) {
      console.error('Export PDF error:', error);
      toast.error(language === 'vi' ? 'Lỗi khi xuất PDF' : 'Failed to export PDF');
    }
  };

  const handleExportXLSX = () => {
    try {
      exportUpcomingSurveysToXLSX(filteredSurveys, {
        language,
        companyName: displayCompany,
        totalCount: filteredSurveys.length
      });
      toast.success(language === 'vi' ? 'Xuất Excel thành công!' : 'Excel exported successfully!');
    } catch (error) {
      console.error('Export XLSX error:', error);
      toast.error(language === 'vi' ? 'Lỗi khi xuất Excel' : 'Failed to export Excel');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[70] p-4">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xl font-bold text-orange-600 flex items-center">
              ⚠️ {language === 'vi' ? 'Thông báo Survey sắp đến hạn' : 'Upcoming Survey Notification'}
            </h3>
            {/* Export Buttons */}
            {surveys.length > 0 && (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleExportPDF}
                  className="flex items-center gap-1 px-3 py-1.5 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 transition duration-200"
                  title={language === 'vi' ? 'Xuất PDF' : 'Export PDF'}
                >
                  <FileText size={16} />
                  <span>PDF</span>
                </button>
                <button
                  onClick={handleExportXLSX}
                  className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition duration-200"
                  title={language === 'vi' ? 'Xuất Excel' : 'Export Excel'}
                >
                  <FileSpreadsheet size={16} />
                  <span>Excel</span>
                </button>
              </div>
            )}
          </div>
          <p className="text-gray-700 mb-4">
            {language === 'vi' 
              ? 'Các Giấy chứng nhận sau sắp đến hạn kiểm tra, hãy bố trí kiểm tra trong thời gian sớm nhất:'
              : 'The following certificates are approaching their survey dates. Please arrange inspections as soon as possible:'}
          </p>
          <div className="text-sm text-gray-600 mb-4">
            {language === 'vi' 
              ? `Tổng cộng: ${totalCount} chứng chỉ | Công ty: ${displayCompany}`
              : `Total: ${totalCount} certificates | Company: ${displayCompany}`}
          </div>
          {checkDate && (
            <div className="text-xs text-gray-500">
              {language === 'vi' ? 'Ngày kiểm tra: ' : 'Check date: '}
              {new Date(checkDate).toLocaleDateString()}
            </div>
          )}
          
          {/* Ship Name Filter - Always show if there are ships */}
          {shipNames.length > 0 && (
            <div className="mt-4 flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">
                {language === 'vi' ? 'Lọc theo tàu:' : 'Filter by Ship:'}
              </label>
              <select
                value={shipFilter}
                onChange={(e) => setShipFilter(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">{language === 'vi' ? '-- Tất cả tàu --' : '-- All Ships --'}</option>
                {shipNames.map(name => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
              {shipFilter && (
                <span className="text-sm text-gray-500">
                  ({filteredSurveys.length} {language === 'vi' ? 'kết quả' : 'results'})
                </span>
              )}
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
                  {language === 'vi' ? 'Tình trạng' : 'Status'}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredSurveys.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                    {language === 'vi' 
                      ? '✅ Không có survey sắp đến hạn'
                      : '✅ No upcoming surveys'}
                  </td>
                </tr>
              ) : (
                filteredSurveys.map((survey, index) => (
                  <tr 
                    key={index} 
                    className={`hover:bg-gray-50 ${
                      survey.is_overdue ? 'bg-red-50' : 
                      survey.is_critical ? 'bg-orange-50' :
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
                      <div className="font-medium">{formatDateDisplay(survey.next_survey_date)}</div>
                      <div className="text-xs text-gray-500">
                        {survey.days_until_window_close >= 0 
                          ? (language === 'vi' ? `Còn ${survey.days_until_window_close} ngày tới window close` : `${survey.days_until_window_close} days to window close`)
                          : (language === 'vi' ? `Quá window close ${Math.abs(survey.days_until_window_close)} ngày` : `${Math.abs(survey.days_until_window_close)} days past window close`)
                        }
                      </div>
                      {survey.window_type && (
                        <div className="text-xs text-blue-600 font-medium">
                          Window: {survey.window_type}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 border-b">
                      {survey.next_survey_type || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm border-b">
                      {survey.is_overdue ? (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                          {language === 'vi' ? 'Quá hạn' : 'Overdue'}
                        </span>
                      ) : survey.is_critical ? (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800">
                          {language === 'vi' ? 'Khẩn cấp' : 'Critical'}
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
