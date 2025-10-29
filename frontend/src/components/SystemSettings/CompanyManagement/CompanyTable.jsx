/**
 * CompanyTable Component
 * Displays list of companies in table format with actions
 */
import React from 'react';

const CompanyTable = ({
  companies,
  loading,
  currentUser,
  language,
  canEditCompany,
  canDeleteCompany,
  onEditCompany,
  onDeleteCompany,
  onConfigureGoogleDrive
}) => {
  /**
   * Format expiry date
   */
  const formatExpiry = (expiryDate) => {
    if (!expiryDate) return '-';
    try {
      const date = new Date(expiryDate);
      return date.toLocaleDateString(language === 'vi' ? 'vi-VN' : 'en-US');
    } catch {
      return expiryDate;
    }
  };

  /**
   * Check if expiry is near or passed
   */
  const getExpiryStatus = (expiryDate) => {
    if (!expiryDate) return 'none';
    try {
      const date = new Date(expiryDate);
      const today = new Date();
      const daysUntilExpiry = Math.ceil((date - today) / (1000 * 60 * 60 * 24));
      
      if (daysUntilExpiry < 0) return 'expired';
      if (daysUntilExpiry <= 30) return 'warning';
      return 'ok';
    } catch {
      return 'none';
    }
  };

  /**
   * Get expiry badge class
   */
  const getExpiryBadgeClass = (status) => {
    switch (status) {
      case 'expired':
        return 'bg-red-100 text-red-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'ok':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
      </div>
    );
  }

  if (companies.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 bg-gray-50 rounded-lg">
        <div className="text-5xl mb-4">🏢</div>
        <p className="text-lg">{language === 'vi' ? 'Chưa có công ty nào' : 'No companies yet'}</p>
        <p className="text-sm mt-2">
          {language === 'vi' ? 'Nhấn "Thêm công ty mới" để bắt đầu' : 'Click "Add New Company" to get started'}
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-gray-300 text-sm">
        <thead>
          <tr className="bg-gray-50">
            <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-700 w-20">
              Logo
            </th>
            <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-700">
              {language === 'vi' ? 'Tên công ty (VN)' : 'Company Name (VN)'}
            </th>
            <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-700">
              {language === 'vi' ? 'Tên công ty (EN)' : 'Company Name (EN)'}
            </th>
            <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-700">
              Zalo
            </th>
            <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-700">
              {language === 'vi' ? 'Hạn hệ thống' : 'System Expiry'}
            </th>
            <th className="border border-gray-300 px-4 py-3 text-center font-semibold text-gray-700">
              {language === 'vi' ? 'Thao tác' : 'Actions'}
            </th>
          </tr>
        </thead>
        <tbody>
          {companies.map((company) => {
            const expiryStatus = getExpiryStatus(company.system_expiry);
            
            return (
              <tr key={company.id} className="hover:bg-gray-50 transition-colors">
                <td className="border border-gray-300 px-4 py-3">
                  {company.logo_url ? (
                    <img 
                      src={company.logo_url} 
                      alt={company.name_en || company.name_vn} 
                      className="w-12 h-12 object-contain"
                    />
                  ) : (
                    <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center text-gray-400 text-xs">
                      {language === 'vi' ? 'Không có' : 'No logo'}
                    </div>
                  )}
                </td>
                <td className="border border-gray-300 px-4 py-3 text-gray-800 font-medium">
                  {company.name_vn || '-'}
                </td>
                <td className="border border-gray-300 px-4 py-3 text-gray-800">
                  {company.name_en || '-'}
                </td>
                <td className="border border-gray-300 px-4 py-3 text-gray-700">
                  {company.zalo || '-'}
                </td>
                <td className="border border-gray-300 px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getExpiryBadgeClass(expiryStatus)}`}>
                    {formatExpiry(company.system_expiry)}
                  </span>
                </td>
                <td className="border border-gray-300 px-4 py-3">
                  <div className="flex justify-center space-x-2">
                    <button
                      onClick={() => onEditCompany(company)}
                      disabled={!canEditCompany(company)}
                      className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-3 py-1 rounded text-xs transition-all font-medium"
                      title={
                        !canEditCompany(company) 
                          ? (language === 'vi' 
                              ? 'Không có quyền chỉnh sửa công ty này' 
                              : 'No permission to edit this company')
                          : (language === 'vi' ? 'Sửa' : 'Edit')
                      }
                    >
                      {language === 'vi' ? 'Sửa' : 'Edit'}
                    </button>
                    <button
                      onClick={() => onDeleteCompany(company)}
                      disabled={!canDeleteCompany(company)}
                      className="bg-red-500 hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-3 py-1 rounded text-xs transition-all font-medium"
                      title={
                        !canDeleteCompany(company) 
                          ? (language === 'vi' 
                              ? 'Không có quyền xóa công ty này' 
                              : 'No permission to delete this company')
                          : (language === 'vi' ? 'Xóa' : 'Delete')
                      }
                    >
                      {language === 'vi' ? 'Xóa' : 'Delete'}
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default CompanyTable;
