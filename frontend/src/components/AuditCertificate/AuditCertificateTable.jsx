/**
 * Certificate Table Component
 * Displays ship certificates in a sortable, filterable table
 * Extracted from Frontend V1 App.js (lines 13729-14006)
 */
import React from 'react';
import { formatDateDisplay } from '../../utils/dateHelpers';

export const CertificateTable = ({
  certificates = [],
  language,
  selectedCertificates,
  onSelectCertificate,
  onSelectAllCertificates,
  onSort,
  sortConfig,
  onDoubleClick,
  onRightClick,
  onSurveyTypeRightClick,
  onNotesClick,
}) => {
  // Get sort icon for column
  const getSortIcon = (column) => {
    if (sortConfig.column !== column) {
      return null; // No icon when not sorted
    }
    return (
      <span className="ml-1 text-blue-600 text-sm font-bold">
        {sortConfig.direction === 'asc' ? '▲' : '▼'}
      </span>
    );
  };

  // Check if all certificates are selected
  const isAllSelected = () => {
    if (certificates.length === 0) return false;
    return certificates.every(cert => selectedCertificates.has(cert.id));
  };

  // Check if some (but not all) certificates are selected
  const isIndeterminate = () => {
    const selectedCount = certificates.filter(cert => selectedCertificates.has(cert.id)).length;
    return selectedCount > 0 && selectedCount < certificates.length;
  };

  // Get certificate status
  const getCertificateStatus = (cert) => {
    if (!cert.valid_date) return 'Unknown';
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const validDate = new Date(cert.valid_date);
    validDate.setHours(0, 0, 0, 0);
    
    if (validDate < today) return 'Expired';
    
    const diffTime = validDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays <= 30) return 'Over Due';
    return 'Valid';
  };

  // Format survey type for display (remove "Survey" suffix)
  const formatSurveyTypeForDisplay = (surveyType) => {
    if (!surveyType) return '-';
    return surveyType.replace(/\s+Survey$/i, '').trim() || surveyType;
  };

  // Get survey type CSS class
  const getSurveyTypeCssClass = (surveyType) => {
    if (!surveyType) return 'bg-gray-100 text-gray-800';
    
    const type = surveyType.toLowerCase();
    
    if (type === 'annual' || type === 'annual survey' || type.includes('annual')) {
      return 'bg-blue-100 text-blue-800';
    }
    if (type === 'intermediate' || type === 'intermediate survey' || type.includes('intermediate')) {
      return 'bg-yellow-100 text-yellow-800';
    }
    if (type === 'renewal' || type === 'renewal survey') {
      return 'bg-green-100 text-green-800';
    }
    if (type === 'special' || type === 'special survey') {
      return 'bg-purple-100 text-purple-800';
    }
    
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-gray-300 text-sm resizable-table">
        <thead>
          <tr className="bg-gray-50">
            <th className="border border-gray-300 px-4 py-2 text-left font-medium bg-gray-50 w-20">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={isAllSelected()}
                  ref={checkboxRef => {
                    if (checkboxRef) {
                      checkboxRef.indeterminate = isIndeterminate();
                    }
                  }}
                  onChange={(e) => onSelectAllCertificates(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                />
                <span>{language === 'vi' ? 'STT' : 'No.'}</span>
              </div>
            </th>
            <th 
              className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[120px]"
              onClick={() => onSort('cert_abbreviation')}
            >
              <div className="flex items-center justify-between">
                <span>{language === 'vi' ? 'Tên viết tắt' : 'Cert. Name'}</span>
                {getSortIcon('cert_abbreviation')}
              </div>
            </th>
            <th 
              className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[100px]"
              onClick={() => onSort('cert_type')}
            >
              <div className="flex items-center justify-between">
                <span>{language === 'vi' ? 'Loại' : 'Type'}</span>
                {getSortIcon('cert_type')}
              </div>
            </th>
            <th 
              className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[120px]"
              onClick={() => onSort('cert_no')}
            >
              <div className="flex items-center justify-between">
                <span>{language === 'vi' ? 'Số chứng chỉ' : 'Certificate No'}</span>
                {getSortIcon('cert_no')}
              </div>
            </th>
            <th 
              className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[100px]"
              onClick={() => onSort('issue_date')}
            >
              <div className="flex items-center justify-between">
                <span>{language === 'vi' ? 'Ngày cấp' : 'Issue Date'}</span>
                {getSortIcon('issue_date')}
              </div>
            </th>
            <th 
              className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[100px]"
              onClick={() => onSort('valid_date')}
            >
              <div className="flex items-center justify-between">
                <span>{language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}</span>
                {getSortIcon('valid_date')}
              </div>
            </th>
            <th 
              className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[100px]"
              onClick={() => onSort('last_endorse')}
            >
              <div className="flex items-center justify-between">
                <span>{language === 'vi' ? 'Xác nhận cuối' : 'Last Endorse'}</span>
                {getSortIcon('last_endorse')}
              </div>
            </th>
            <th 
              className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[120px]"
              onClick={() => onSort('next_survey')}
            >
              <div className="flex items-center justify-between">
                <span>{language === 'vi' ? 'Kiểm tra tới' : 'Next Survey'}</span>
                {getSortIcon('next_survey')}
              </div>
            </th>
            <th 
              className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[120px]"
              onClick={() => onSort('next_survey_type')}
            >
              <div className="flex items-center justify-between">
                <span>{language === 'vi' ? 'Loại kiểm tra tới' : 'Next Survey Type'}</span>
                {getSortIcon('next_survey_type')}
              </div>
            </th>
            <th 
              className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[120px]"
              onClick={() => onSort('issued_by')}
            >
              <div className="flex items-center justify-between">
                <span>{language === 'vi' ? 'Cấp bởi' : 'Issued By'}</span>
                {getSortIcon('issued_by')}
              </div>
            </th>
            <th 
              className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[80px]"
              onClick={() => onSort('status')}
            >
              <div className="flex items-center justify-between">
                <span>{language === 'vi' ? 'Trạng thái' : 'Status'}</span>
                {getSortIcon('status')}
              </div>
            </th>
            <th 
              className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[100px]"
              onClick={() => onSort('notes')}
            >
              <div className="flex items-center justify-between">
                <span>{language === 'vi' ? 'Ghi chú' : 'Notes'}</span>
                {getSortIcon('notes')}
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          {certificates.length === 0 ? (
            <tr>
              <td colSpan="12" className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                {language === 'vi' ? 'Chưa có chứng chỉ nào' : 'No certificates available'}
              </td>
            </tr>
          ) : (
            certificates.map((cert, index) => (
              <tr 
                key={cert.id} 
                className={`hover:bg-gray-50 cursor-pointer transition-colors ${cert.google_drive_file_id ? 'hover:bg-blue-50' : ''}`}
                onDoubleClick={() => onDoubleClick(cert)}
                onContextMenu={(e) => onRightClick(e, cert)}
                title={cert.google_drive_file_id 
                  ? (language === 'vi' ? 'Nhấn đúp để mở file | Chuột phải để Edit/Delete' : 'Double-click to open file | Right-click for Edit/Delete')
                  : (language === 'vi' ? 'Chưa có file đính kèm | Chuột phải để Edit/Delete' : 'No file attached | Right-click for Edit/Delete')
                }
              >
                <td 
                  className="border border-gray-300 px-4 py-2 text-center w-20 relative"
                  title={cert.file_name ? `File: ${cert.file_name}` : 'No file name available'}
                >
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={selectedCertificates.has(cert.id)}
                      onChange={() => onSelectCertificate(cert.id)}
                      className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                      onClick={(e) => e.stopPropagation()}
                    />
                    <span className="font-bold">{index + 1}</span>
                  </div>
                </td>
                <td 
                  className="border border-gray-300 px-4 py-2 font-mono font-bold text-blue-600"
                  title={cert.cert_name}
                  style={{ cursor: 'help' }}
                >
                  {cert.cert_abbreviation || cert.cert_name?.substring(0, 4) || 'N/A'}
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    cert.cert_type === 'Full Term' ? 'bg-green-100 text-green-800' :
                    cert.cert_type === 'Interim' ? 'bg-yellow-100 text-yellow-800' :
                    cert.cert_type === 'Provisional' ? 'bg-orange-100 text-orange-800' :
                    cert.cert_type === 'Short term' ? 'bg-red-100 text-red-800' :
                    cert.cert_type === 'Conditional' ? 'bg-blue-100 text-blue-800' :
                    cert.cert_type === 'Other' ? 'bg-purple-100 text-purple-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {cert.cert_type || 'Unknown'}
                  </span>
                </td>
                <td 
                  className="border border-gray-300 px-4 py-2 font-mono relative group cursor-help"
                  title={cert.extracted_ship_name ? `Ship Name: ${cert.extracted_ship_name}` : 'No ship name extracted'}
                >
                  {cert.cert_no}
                  {/* Tooltip for ship name */}
                  {cert.extracted_ship_name && (
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
                      <div className="font-medium">Ship Name from Certificate:</div>
                      <div className="text-blue-200">{cert.extracted_ship_name}</div>
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                    </div>
                  )}
                </td>
                <td className="border border-gray-300 px-4 py-2">{formatDateDisplay(cert.issue_date)}</td>
                <td className="border border-gray-300 px-4 py-2">{formatDateDisplay(cert.valid_date)}</td>
                <td className="border border-gray-300 px-4 py-2">
                  {cert.cert_type === 'Full Term' 
                    ? formatDateDisplay(cert.last_endorse) 
                    : (
                      <span className="text-gray-400 text-sm italic">
                        {language === 'vi' ? 'Không áp dụng' : 'N/A'}
                      </span>
                    )
                  }
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  {cert.next_survey_display || formatDateDisplay(cert.next_survey)}
                </td>
                <td 
                  className="border border-gray-300 px-4 py-2 text-center cursor-context-menu hover:bg-gray-50"
                  onContextMenu={(e) => {
                    e.stopPropagation();
                    onSurveyTypeRightClick(e, cert.id, cert.next_survey_type);
                  }}
                  title={language === 'vi' ? 'Right-click để thay đổi nhanh loại kiểm tra' : 'Right-click to quick edit survey type'}
                >
                  <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getSurveyTypeCssClass(cert.next_survey_type)}`}>
                    {formatSurveyTypeForDisplay(cert.next_survey_type)}
                  </span>
                </td>
                <td className="border border-gray-300 px-4 py-2 text-sm font-semibold text-blue-700" title={cert.issued_by}>
                  {cert.issued_by_abbreviation || (cert.issued_by ? 
                    (cert.issued_by.length > 8 ? `${cert.issued_by.substring(0, 8)}...` : cert.issued_by)
                    : '-'
                  )}
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    getCertificateStatus(cert) === 'Valid' ? 'bg-green-100 text-green-800' :
                    getCertificateStatus(cert) === 'Expired' ? 'bg-red-100 text-red-800' :
                    getCertificateStatus(cert) === 'Over Due' ? 'bg-orange-100 text-orange-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {getCertificateStatus(cert) === 'Valid' 
                      ? (language === 'vi' ? 'Còn hiệu lực' : 'Valid')
                      : getCertificateStatus(cert) === 'Expired' 
                      ? (language === 'vi' ? 'Hết hiệu lực' : 'Expired')
                      : getCertificateStatus(cert) === 'Over Due'
                      ? (language === 'vi' ? 'Quá hạn' : 'Over Due')
                      : (language === 'vi' ? 'Không rõ' : 'Unknown')
                    }
                  </span>
                </td>
                <td 
                  className="border border-gray-300 px-4 py-2 text-center" 
                  title={cert.notes || (language === 'vi' ? 'Click để thêm ghi chú' : 'Click to add notes')}
                >
                  {cert.has_notes ? (
                    <span 
                      className="text-orange-600 font-bold cursor-pointer text-lg hover:text-orange-700"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onNotesClick) onNotesClick(cert);
                      }}
                    >
                      *
                    </span>
                  ) : (
                    <span 
                      className="text-gray-400 cursor-pointer hover:text-gray-600"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onNotesClick) onNotesClick(cert);
                      }}
                    >
                      +
                    </span>
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
