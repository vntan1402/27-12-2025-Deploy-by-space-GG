import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { useAuth } from '../../../contexts/AuthContext';
import api from '../../../services/api';
import { convertGoogleDriveUrl } from '../../../utils/googleDriveHelpers';

const CompanyDetailModal = ({ company, onClose, language = 'en' }) => {
  const { user: currentUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [statistics, setStatistics] = useState({
    totalShips: 0,
    totalUsers: 0,
    activeUsers: 0,
    totalCrew: 0
  });
  const [baseFee, setBaseFee] = useState(0);
  const [monthlyFee, setMonthlyFee] = useState(null);
  const [calculatingFee, setCalculatingFee] = useState(false);

  useEffect(() => {
    if (company) {
      fetchCompanyStatistics();
      fetchBaseFee();
    }
  }, [company]);

  const fetchBaseFee = async () => {
    try {
      const response = await api.get('/api/system-settings/base-fee');
      if (response.data && response.data.base_fee !== undefined) {
        setBaseFee(response.data.base_fee);
        console.log('💰 Base fee loaded:', response.data.base_fee);
      }
    } catch (error) {
      console.error('Error fetching base fee:', error);
      // Default to 0 if error
      setBaseFee(0);
    }
  };

  const calculateMonthlyFee = () => {
    setCalculatingFee(true);
    try {
      // Monthly Fee = (Total Ships x Base Fee) + (Office Staff x 2 USD) + (Crew Members x 0.5 USD)
      const shipsFee = statistics.totalShips * baseFee;
      const staffFee = statistics.totalUsers * 2;
      const crewFee = statistics.totalCrew * 0.5;
      const total = shipsFee + staffFee + crewFee;
      
      setMonthlyFee(total);
      console.log('💵 Monthly Fee Calculation:', {
        totalShips: statistics.totalShips,
        baseFee: baseFee,
        shipsFee: shipsFee,
        officeStaff: statistics.totalUsers,
        staffFee: staffFee,
        crewMembers: statistics.totalCrew,
        crewFee: crewFee,
        totalMonthlyFee: total
      });
      
      toast.success(
        language === 'vi' 
          ? `Phí hàng tháng: $${total.toFixed(2)}` 
          : `Monthly Fee: $${total.toFixed(2)}`,
        { autoClose: 2000 }
      );
    } catch (error) {
      console.error('Error calculating monthly fee:', error);
      toast.error(language === 'vi' ? 'Lỗi khi tính phí' : 'Error calculating fee');
    } finally {
      setCalculatingFee(false);
    }
  };

  const fetchCompanyStatistics = async () => {
    setLoading(true);
    try {
      console.log('🔍 Fetching company statistics for:', company);
      
      // Fetch ships
      const shipsResponse = await api.get('/api/ships');
      console.log('📊 All ships:', shipsResponse.data?.length);
      
      const companyShips = shipsResponse.data.filter(ship => 
        ship.company === company.id || 
        ship.company === company.name_en || 
        ship.company === company.name_vn
      );
      console.log('🚢 Company ships (before certificate filter):', companyShips.length);
      console.log('🔑 Company identifiers - ID:', company.id, 'Name EN:', company.name_en, 'Name VN:', company.name_vn);

      // Fetch ship certificates - using correct endpoint
      const shipCertificatesResponse = await api.get('/api/certificates');
      const shipCertificates = shipCertificatesResponse.data || [];
      console.log('📄 Total ship certificates:', shipCertificates.length);

      // Fetch audit certificates (now supports fetching all without ship_id)
      const auditCertificatesResponse = await api.get('/api/audit-certificates');
      const auditCertificates = auditCertificatesResponse.data || [];
      console.log('📋 Total audit certificates:', auditCertificates.length);

      // Get unique ship IDs that have at least one certificate
      const shipIdsWithCertificates = new Set();
      
      // Add ships from ship certificates
      shipCertificates.forEach(cert => {
        if (cert.ship_id) {
          shipIdsWithCertificates.add(cert.ship_id);
        }
      });
      
      // Add ships from audit certificates
      auditCertificates.forEach(cert => {
        if (cert.ship_id) {
          shipIdsWithCertificates.add(cert.ship_id);
        }
      });
      
      console.log('🎯 Unique ship IDs with certificates:', Array.from(shipIdsWithCertificates));

      // Count only ships that have at least one certificate
      const shipsWithCertificates = companyShips.filter(ship => 
        shipIdsWithCertificates.has(ship.id)
      );
      console.log('✅ Ships with certificates:', shipsWithCertificates.length);

      console.log('✅ Ships with certificates:', shipsWithCertificates.length);

      // Fetch users count (office staff only - exclude ship_crew department)
      const usersResponse = await api.get('/api/users');
      console.log('👥 Total users:', usersResponse.data?.length);
      
      const companyUsers = usersResponse.data.filter(user => 
        user.company === company.id || 
        user.company === company.name_en || 
        user.company === company.name_vn
      );
      console.log('🏢 Company users:', companyUsers.length);

      // Exclude users with ship_crew department from total users count
      const nonCrewUsers = companyUsers.filter(user => {
        if (!user.department) return true;
        const departments = Array.isArray(user.department) ? user.department : [user.department];
        return !departments.includes('ship_crew');
      });
      console.log('💼 Non-crew users (office staff):', nonCrewUsers.length);

      const activeUsers = nonCrewUsers.filter(user => user.is_active);
      console.log('✅ Active users:', activeUsers.length);
      
      // Fetch crew list (backend already filters by company_id from current_user)
      const crewResponse = await api.get('/api/crew');
      const totalCrewCount = crewResponse.data?.length || 0;
      console.log('⚓ Total crew members (backend filtered by company):', totalCrewCount);

      const finalStats = {
        totalShips: shipsWithCertificates.length, // Only count ships with at least one certificate
        totalUsers: nonCrewUsers.length, // Office staff only (exclude ship_crew)
        activeUsers: activeUsers.length, // Active office staff only
        totalCrew: totalCrewCount // Crew from backend (already filtered by company_id)
      };
      
      console.log('📊 Final statistics:', finalStats);
      setStatistics(finalStats);
    } catch (error) {
      console.error('❌ Error fetching company statistics:', error);
      toast.error(language === 'vi' ? 'Lỗi khi tải thống kê công ty' : 'Error loading company statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString(language === 'vi' ? 'vi-VN' : 'en-US');
    } catch {
      return dateString;
    }
  };

  const getSystemExpiryBadge = (expiryDate) => {
    if (!expiryDate) return null;

    const today = new Date();
    const expiry = new Date(expiryDate);
    const daysUntilExpiry = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));

    if (daysUntilExpiry < 0) {
      return (
        <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">
          🔴 {language === 'vi' ? 'Đã hết hạn' : 'Expired'}
        </span>
      );
    } else if (daysUntilExpiry <= 30) {
      return (
        <span className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm font-medium">
          🟡 {language === 'vi' ? `Còn ${daysUntilExpiry} ngày` : `${daysUntilExpiry} days left`}
        </span>
      );
    } else {
      return (
        <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
          🟢 {language === 'vi' ? `Còn ${daysUntilExpiry} ngày` : `${daysUntilExpiry} days left`}
        </span>
      );
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4 rounded-t-xl flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="bg-white bg-opacity-20 p-2 rounded-lg">
              🏢
            </div>
            <h2 className="text-2xl font-bold">
              {language === 'vi' ? 'Thông tin công ty' : 'Company Details'}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={calculateMonthlyFee}
              disabled={calculatingFee || loading}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {calculatingFee 
                ? (language === 'vi' ? 'Đang tính...' : 'Calculating...') 
                : (language === 'vi' ? 'Tính Phí' : 'Calculate Fee')
              }
            </button>
            <button
              onClick={onClose}
              className="text-white hover:bg-white hover:bg-opacity-20 p-2 rounded-lg transition-all"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Company Logo & Name */}
          <div className="flex items-center gap-4 border-b pb-4">
            {company.logo_url ? (
              <img 
                src={company.logo_url} 
                alt={company.name_en}
                className="w-20 h-20 object-contain rounded-lg border-2 border-gray-200"
              />
            ) : (
              <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-blue-200 rounded-lg flex items-center justify-center text-3xl">
                🏢
              </div>
            )}
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-2xl font-bold text-gray-800">
                    {language === 'vi' ? company.name_vn : company.name_en}
                  </h3>
                  <p className="text-gray-500 text-sm">
                    {language === 'vi' ? company.name_en : company.name_vn}
                  </p>
                </div>
                {monthlyFee !== null && (
                  <div className="bg-gradient-to-r from-green-500 to-green-600 text-white px-4 py-2 rounded-lg shadow-lg">
                    <p className="text-xs font-medium">
                      {language === 'vi' ? 'Phí hàng tháng' : 'Monthly Fee'}
                    </p>
                    <p className="text-2xl font-bold">
                      ${monthlyFee.toFixed(2)}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Ships Count */}
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
              <div>
                <p className="text-sm text-gray-600">
                  {language === 'vi' ? 'Tổng số tàu' : 'Total Ships'}
                </p>
                {loading ? (
                  <div className="h-8 w-16 bg-gray-200 animate-pulse rounded"></div>
                ) : (
                  <p className="text-3xl font-bold text-blue-700">{statistics.totalShips}</p>
                )}
              </div>
            </div>

            {/* Total Users */}
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
              <div>
                <p className="text-sm text-gray-600">
                  {language === 'vi' ? 'Nhân viên văn phòng' : 'Office Staff'}
                </p>
                {loading ? (
                  <div className="h-8 w-16 bg-gray-200 animate-pulse rounded"></div>
                ) : (
                  <p className="text-3xl font-bold text-green-700">{statistics.totalUsers}</p>
                )}
              </div>
            </div>

            {/* Total Crew */}
            <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4 border border-orange-200">
              <div>
                <p className="text-sm text-gray-600">
                  {language === 'vi' ? 'Thuyền viên' : 'Crew Members'}
                </p>
                {loading ? (
                  <div className="h-8 w-16 bg-gray-200 animate-pulse rounded"></div>
                ) : (
                  <p className="text-3xl font-bold text-orange-700">{statistics.totalCrew}</p>
                )}
              </div>
            </div>

            {/* Active Users */}
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
              <div>
                <p className="text-sm text-gray-600">
                  {language === 'vi' ? 'Đang hoạt động' : 'Active Users'}
                </p>
                {loading ? (
                  <div className="h-8 w-16 bg-gray-200 animate-pulse rounded"></div>
                ) : (
                  <p className="text-3xl font-bold text-purple-700">{statistics.activeUsers}</p>
                )}
              </div>
            </div>
          </div>

          {/* Company Information */}
          <div className="bg-gray-50 rounded-lg p-5 space-y-4">
            <h4 className="text-lg font-semibold text-gray-800 border-b pb-2">
              📋 {language === 'vi' ? 'Thông tin chi tiết' : 'Detailed Information'}
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Vietnamese Name */}
              <div>
                <label className="text-sm font-medium text-gray-600">
                  {language === 'vi' ? 'Tên tiếng Việt' : 'Vietnamese Name'}
                </label>
                <p className="text-gray-800 font-medium mt-1">{company.name_vn || 'N/A'}</p>
              </div>

              {/* English Name */}
              <div>
                <label className="text-sm font-medium text-gray-600">
                  {language === 'vi' ? 'Tên tiếng Anh' : 'English Name'}
                </label>
                <p className="text-gray-800 font-medium mt-1">{company.name_en || 'N/A'}</p>
              </div>

              {/* Tax ID */}
              <div>
                <label className="text-sm font-medium text-gray-600">
                  {language === 'vi' ? 'Mã số thuế' : 'Tax ID'}
                </label>
                <p className="text-gray-800 font-medium mt-1">{company.tax_id || 'N/A'}</p>
              </div>

              {/* Gmail */}
              <div>
                <label className="text-sm font-medium text-gray-600">Gmail</label>
                <p className="text-gray-800 font-medium mt-1">{company.gmail || 'N/A'}</p>
              </div>

              {/* Zalo */}
              <div>
                <label className="text-sm font-medium text-gray-600">Zalo</label>
                <p className="text-gray-800 font-medium mt-1">{company.zalo || 'N/A'}</p>
              </div>

              {/* Software Expiry - Only for System Admin & Super Admin */}
              {currentUser && (currentUser.role === 'system_admin' || currentUser.role === 'super_admin') && (
                <div>
                  <label className="text-sm font-medium text-gray-600">
                    {language === 'vi' ? 'Hạn sử dụng phần mềm' : 'Software Expiry'}
                  </label>
                  <div className="mt-1">
                    {company.software_expiry ? (
                      <div className="flex items-center gap-2">
                        <span className="text-gray-800">{formatDate(company.software_expiry)}</span>
                        {getSystemExpiryBadge(company.software_expiry)}
                      </div>
                    ) : (
                      <p className="text-gray-800">N/A</p>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Vietnamese Address */}
            <div>
              <label className="text-sm font-medium text-gray-600">
                {language === 'vi' ? 'Địa chỉ tiếng Việt' : 'Vietnamese Address'}
              </label>
              <p className="text-gray-800 mt-1 leading-relaxed">{company.address_vn || 'N/A'}</p>
            </div>

            {/* English Address */}
            <div>
              <label className="text-sm font-medium text-gray-600">
                {language === 'vi' ? 'Địa chỉ tiếng Anh' : 'English Address'}
              </label>
              <p className="text-gray-800 mt-1 leading-relaxed">{company.address_en || 'N/A'}</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 px-6 py-4 border-t flex justify-end rounded-b-xl">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-all font-medium"
          >
            {language === 'vi' ? 'Đóng' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CompanyDetailModal;
