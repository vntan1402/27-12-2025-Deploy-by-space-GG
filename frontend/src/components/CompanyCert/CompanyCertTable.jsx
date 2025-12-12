/**
 * Company Certificate Table Component
 * Displays company certificates in a sortable table
 */
import React, { useState } from 'react';
import { formatDateDisplay } from '../../utils/dateHelpers';
import { useAuth } from '../../contexts/AuthContext';

export const CompanyCertTable = ({
  certificates = [],
  selectedCertificates,
  onSelectCertificate,
  onSelectAllCertificates,
  onSort,
  sortConfig,
  onDoubleClick,
  onNotesClick,
  onEditClick,
  onDeleteClick
}) => {
  const { language, user } = useAuth();
  const [noteTooltip, setNoteTooltip] = useState({
    show: false,
    x: 0,
    y: 0,
    width: 300,
    content: ''
  });

  const handleNoteMouseEnter = (e, note) => {
    if (!note) return;
    
    const rect = e.target.getBoundingClientRect();
    const tooltipWidth = 300;
    const tooltipHeight = 200;
    
    let x = rect.left;
    let y = rect.bottom + 5;
    
    if (x + tooltipWidth > window.innerWidth) {
      x = window.innerWidth - tooltipWidth - 10;
    }
    
    if (y + tooltipHeight > window.innerHeight) {
      y = rect.top - tooltipHeight - 5;
    }
    
    setNoteTooltip({
      show: true,
      x: x,
      y: y,
      width: tooltipWidth,
      content: note
    });
  };

  const handleNoteMouseLeave = () => {
    setNoteTooltip({ show: false, x: 0, y: 0, width: 300, content: '' });
  };

  const getSortIcon = (column) => {
    if (sortConfig.column !== column) return null;
    return (
      <span className="ml-1 text-blue-600 text-sm font-bold">
        {sortConfig.direction === 'asc' ? '▲' : '▼'}
      </span>
    );
  };

  const isAllSelected = () => {
    if (certificates.length === 0) return false;
    return certificates.every(cert => selectedCertificates.has(cert.id));
  };

  const isIndeterminate = () => {
    const selectedCount = certificates.filter(cert => selectedCertificates.has(cert.id)).length;
    return selectedCount > 0 && selectedCount < certificates.length;
  };

  const getCertificateStatus = (cert) => {
    if (!cert.valid_date) return 'Unknown';
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    let validDate;
    if (cert.valid_date.includes('/')) {
      const [day, month, year] = cert.valid_date.split('/');
      validDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    } else {
      validDate = new Date(cert.valid_date);
    }
    
    if (isNaN(validDate.getTime())) return 'Unknown';
    validDate.setHours(0, 0, 0, 0);
    
    if (validDate < today) return 'Expired';
    
    const diffTime = validDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays <= 90) return 'Due Soon';
    return 'Valid';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Valid':
        return 'bg-green-100 text-green-800';
      case 'Due Soon':
        return 'bg-yellow-100 text-yellow-800';
      case 'Expired':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Check if user can edit/delete (Admin or DPA Manager)
  const canEditDelete = () => {
    if (!user) return false;
    if (['admin', 'super_admin', 'system_admin'].includes(user.role)) return true;
    if (user.role === 'manager' && user.department === 'DPA') return true;
    return false;
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 border-b text-left w-12">
              <input
                type="checkbox"
                checked={isAllSelected()}
                ref={el => {
                  if (el) el.indeterminate = isIndeterminate();
                }}
                onChange={(e) => onSelectAllCertificates(e.target.checked)}
                className="rounded border-gray-300"
              />
            </th>
            <th className="px-4 py-3 border-b text-left w-12">
              {language === 'vi' ? 'STT' : 'No.'}
            </th>
            <th 
              className="px-4 py-3 border-b text-left cursor-pointer hover:bg-gray-100"
              onClick={() => onSort('cert_name')}
            >
              {language === 'vi' ? 'Tên chứng chỉ' : 'Cert Name'}
              {getSortIcon('cert_name')}
            </th>
            <th className="px-4 py-3 border-b text-left">
              {language === 'vi' ? 'Số chứng chỉ' : 'Certificate No'}
            </th>
            <th className="px-4 py-3 border-b text-left">
              {language === 'vi' ? 'Ngày cấp' : 'Issue Date'}
            </th>
            <th className="px-4 py-3 border-b text-left">
              {language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}
            </th>
            <th className="px-4 py-3 border-b text-left">
              {language === 'vi' ? 'Cơ quan cấp' : 'Issued By'}
            </th>
            <th className="px-4 py-3 border-b text-center">
              {language === 'vi' ? 'Trạng thái' : 'Status'}
            </th>
            <th className="px-4 py-3 border-b text-center">
              {language === 'vi' ? 'Ghi chú' : 'Notes'}
            </th>
            {canEditDelete() && (
              <th className="px-4 py-3 border-b text-center">
                {language === 'vi' ? 'Thao tác' : 'Actions'}
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {certificates.map((cert, index) => {
            const status = getCertificateStatus(cert);
            return (
              <tr
                key={cert.id}
                className={`hover:bg-gray-50 ${
                  selectedCertificates.has(cert.id) ? 'bg-blue-50' : ''
                }`}
                onDoubleClick={() => onDoubleClick(cert)}
              >
                <td className="px-4 py-2 border-b">
                  <input
                    type="checkbox"
                    checked={selectedCertificates.has(cert.id)}
                    onChange={(e) => {
                      e.stopPropagation();
                      onSelectCertificate(cert.id);
                    }}
                    className="rounded border-gray-300"
                  />
                </td>
                <td className="px-4 py-2 border-b text-sm">{index + 1}</td>
                <td className="px-4 py-2 border-b">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{cert.cert_name || '-'}</span>
                    {cert.file_id && (
                      <span className="text-blue-600" title="Has file">📄</span>
                    )}
                    {cert.summary_file_id && ['admin', 'super_admin', 'system_admin'].includes(user?.role) && (
                      <span className="text-green-600 cursor-pointer" title="Summary file">📝</span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-2 border-b text-sm">{cert.cert_no || '-'}</td>
                <td className="px-4 py-2 border-b text-sm">{formatDateDisplay(cert.issue_date) || '-'}</td>
                <td className="px-4 py-2 border-b text-sm">{formatDateDisplay(cert.valid_date) || '-'}</td>
                <td className="px-4 py-2 border-b text-sm">{cert.issued_by || '-'}</td>
                <td className="px-4 py-2 border-b text-center">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(status)}`}>
                    {status}
                  </span>
                </td>
                <td className="px-4 py-2 border-b text-center">
                  {cert.notes ? (
                    <button
                      className="text-blue-600 hover:text-blue-800 text-lg"
                      onClick={(e) => {
                        e.stopPropagation();
                        onNotesClick(cert);
                      }}
                      onMouseEnter={(e) => handleNoteMouseEnter(e, cert.notes)}
                      onMouseLeave={handleNoteMouseLeave}
                      title="View notes"
                    >
                      📝
                    </button>
                  ) : (
                    <button
                      className="text-gray-400 hover:text-gray-600 text-lg"
                      onClick={(e) => {
                        e.stopPropagation();
                        onNotesClick(cert);
                      }}
                      title="Add notes"
                    >
                      📝
                    </button>
                  )}
                </td>
                {canEditDelete() && (
                  <td className="px-4 py-2 border-b text-center">
                    <div className="flex gap-2 justify-center">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onEditClick(cert);
                        }}
                        className="text-blue-600 hover:text-blue-800 text-sm"
                        title="Edit"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteClick(cert);
                        }}
                        className="text-red-600 hover:text-red-800 text-sm"
                        title="Delete"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>

      {certificates.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          {language === 'vi' ? 'Chưa có chứng chỉ nào' : 'No certificates yet'}
        </div>
      )}

      {noteTooltip.show && (
        <div
          className="fixed z-50 bg-white border border-gray-300 rounded-lg shadow-lg p-3 max-h-48 overflow-y-auto"
          style={{
            left: `${noteTooltip.x}px`,
            top: `${noteTooltip.y}px`,
            width: `${noteTooltip.width}px`
          }}
        >
          <div className="text-sm text-gray-700 whitespace-pre-wrap">
            {noteTooltip.content}
          </div>
        </div>
      )}
    </div>
  );
};

export default CompanyCertTable;