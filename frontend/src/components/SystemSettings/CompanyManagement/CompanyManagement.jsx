/**
 * Company Management Container
 * Main component for managing companies with role-based permissions
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useAuth } from '../../../contexts/AuthContext';
import { companyService } from '../../../services/companyService';
import api from '../../../services/api';
import CompanyTable from './CompanyTable';
import CompanyFormModal from './CompanyFormModal';
import CompanyGoogleDriveModal from './CompanyGoogleDriveModal';
import CompanyDetailModal from './CompanyDetailModal';
import BaseFeeModal from './BaseFeeModal';

const CompanyManagement = () => {
  const { user: currentUser, language } = useAuth();
  
  // State
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddCompany, setShowAddCompany] = useState(false);
  const [showEditCompany, setShowEditCompany] = useState(false);
  const [editingCompany, setEditingCompany] = useState(null);
  const [showGoogleDriveModal, setShowGoogleDriveModal] = useState(false);
  const [selectedCompanyForGDrive, setSelectedCompanyForGDrive] = useState(null);
  const [showCompanyDetail, setShowCompanyDetail] = useState(false);
  const [selectedCompanyForDetail, setSelectedCompanyForDetail] = useState(null);
  const [showBaseFeeModal, setShowBaseFeeModal] = useState(false);
  const [baseFee, setBaseFee] = useState(0);

  // Fetch companies and base fee on mount
  useEffect(() => {
    fetchCompanies();
    fetchBaseFee();
  }, []);

  /**
   * Fetch base fee
   */
  const fetchBaseFee = async () => {
    try {
      const response = await api.get('/api/system-settings/base-fee');
      if (response.data && response.data.success) {
        setBaseFee(response.data.base_fee || 0);
      }
    } catch (error) {
      console.error('Failed to fetch base fee:', error);
    }
  };

  /**
   * Handle update base fee
   */
  const handleUpdateBaseFee = async (newBaseFee) => {
    try {
      const response = await api.put(`/api/system-settings/base-fee?base_fee=${newBaseFee}`);
      if (response.data && response.data.success) {
        setBaseFee(newBaseFee);
        await fetchBaseFee(); // Refresh
      }
    } catch (error) {
      console.error('Failed to update base fee:', error);
      throw error;
    }
  };

  /**
   * Fetch all companies
   */
  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const response = await companyService.getAll();
      let companiesList = response.data || [];
      
      // Filter companies based on user role
      // Only super_admin can see all companies
      // Other users can only see their own company
      if (currentUser.role !== 'super_admin') {
        companiesList = companiesList.filter(company => 
          company.id === currentUser.company || 
          company.name_en === currentUser.company || 
          company.name_vn === currentUser.company
        );
      }
      
      setCompanies(companiesList);
    } catch (error) {
      console.error('Failed to fetch companies:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách công ty' : 'Failed to load companies');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Check if user can add company (Super Admin only)
   * Other users can only see their own company, not add new ones
   */
  const canAddCompany = () => {
    return currentUser.role === 'super_admin';
  };

  /**
   * Check if user can edit company
   * - System Admin & Super Admin: Can edit all companies
   * - Admin: Can only edit own company
   */
  const canEditCompany = (company) => {
    if (currentUser.role === 'system_admin' || currentUser.role === 'super_admin') {
      return true;
    }
    
    if (currentUser.role === 'admin') {
      // Admin can only edit their own company
      return company.id === currentUser.company || 
             company.name_en === currentUser.company || 
             company.name_vn === currentUser.company;
    }
    
    return false;
  };

  /**
   * Check if user can delete company (System Admin & Super Admin only)
   */
  const canDeleteCompany = (company) => {
    return currentUser.role === 'system_admin' || currentUser.role === 'super_admin';
  };

  /**
   * Check if user can configure Google Drive (System Admin & Super Admin only)
   */
  const canConfigureGoogleDrive = () => {
    return currentUser.role === 'system_admin' || currentUser.role === 'super_admin';
  };

  /**
   * Handle add company
   */
  const handleAddCompany = async (companyData, logoFile) => {
    try {
      setLoading(true);
      
      // Create company first
      const response = await companyService.create(companyData);
      const newCompany = response.data;
      
      toast.success(language === 'vi' ? 'Thêm công ty thành công!' : 'Company added successfully!');
      
      // Upload logo if provided
      if (logoFile && newCompany.id) {
        try {
          await companyService.uploadLogo(newCompany.id, logoFile);
          toast.success(language === 'vi' ? 'Logo đã được tải lên!' : 'Logo uploaded successfully!');
        } catch (logoError) {
          console.error('Failed to upload logo:', logoError);
          toast.warning(language === 'vi' ? 'Công ty đã được tạo nhưng không thể tải logo' : 'Company created but logo upload failed');
        }
      }
      
      setShowAddCompany(false);
      fetchCompanies();
    } catch (error) {
      console.error('Failed to add company:', error);
      const errorMessage = error.response?.data?.detail || (language === 'vi' ? 'Không thể thêm công ty' : 'Failed to add company');
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle edit company
   */
  const handleEditCompany = async (companyId, companyData, logoFile) => {
    try {
      setLoading(true);
      
      // Update company
      await companyService.update(companyId, companyData);
      
      toast.success(language === 'vi' ? 'Cập nhật công ty thành công!' : 'Company updated successfully!');
      
      // Upload logo if provided
      if (logoFile) {
        try {
          await companyService.uploadLogo(companyId, logoFile);
          toast.success(language === 'vi' ? 'Logo đã được cập nhật!' : 'Logo updated successfully!');
        } catch (logoError) {
          console.error('Failed to upload logo:', logoError);
          toast.warning(language === 'vi' ? 'Công ty đã được cập nhật nhưng không thể tải logo' : 'Company updated but logo upload failed');
        }
      }
      
      setShowEditCompany(false);
      setEditingCompany(null);
      fetchCompanies();
    } catch (error) {
      console.error('Failed to update company:', error);
      const errorMessage = error.response?.data?.detail || (language === 'vi' ? 'Không thể cập nhật công ty' : 'Failed to update company');
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle delete company
   */
  const handleDeleteCompany = async (company) => {
    if (!canDeleteCompany(company)) {
      toast.error(language === 'vi' ? 'Bạn không có quyền xóa công ty này' : 'You do not have permission to delete this company');
      return;
    }

    const confirmMessage = language === 'vi' 
      ? `Bạn có chắc muốn xóa công ty "${company.name_vn || company.name_en}"?\n\nLưu ý: Công ty này sẽ bị xóa vĩnh viễn.`
      : `Are you sure you want to delete company "${company.name_en || company.name_vn}"?\n\nNote: This company will be permanently deleted.`;
    
    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      setLoading(true);
      await companyService.delete(company.id);
      toast.success(language === 'vi' ? '✅ Xóa công ty thành công!' : '✅ Company deleted successfully!');
      fetchCompanies();
    } catch (error) {
      console.error('Failed to delete company:', error);
      
      // Handle specific error cases
      const errorDetail = error.response?.data?.detail || '';
      
      if (error.response?.status === 400) {
        // Check if error is about ships
        if (errorDetail.includes('ships') || errorDetail.includes('ship')) {
          const shipCount = errorDetail.match(/(\d+)\s+ships?/i);
          const count = shipCount ? shipCount[1] : '';
          
          if (language === 'vi') {
            toast.error(
              `❌ Không thể xóa công ty!\n\n` +
              `Công ty này còn ${count} tàu đang hoạt động.\n\n` +
              `⚠️ Vui lòng xóa hoặc chuyển nhượng tất cả các tàu trước khi xóa công ty.`,
              { duration: 6000 }
            );
          } else {
            toast.error(
              `❌ Cannot delete company!\n\n` +
              `This company has ${count} ships.\n\n` +
              `⚠️ Please delete or reassign all ships before deleting the company.`,
              { duration: 6000 }
            );
          }
        } 
        // Check if error is about users
        else if (errorDetail.includes('users') || errorDetail.includes('user')) {
          if (language === 'vi') {
            toast.error(
              `❌ Không thể xóa công ty!\n\n` +
              `Công ty này còn người dùng đang hoạt động.\n\n` +
              `⚠️ Vui lòng xóa hoặc chuyển nhượng tất cả người dùng trước khi xóa công ty.`,
              { duration: 6000 }
            );
          } else {
            toast.error(
              `❌ Cannot delete company!\n\n` +
              `This company has active users.\n\n` +
              `⚠️ Please delete or reassign all users before deleting the company.`,
              { duration: 6000 }
            );
          }
        } else {
          // Generic 400 error
          toast.error(errorDetail || (language === 'vi' ? '❌ Không thể xóa công ty' : '❌ Failed to delete company'));
        }
      } else {
        // Other errors
        const errorMessage = errorDetail || (language === 'vi' ? '❌ Không thể xóa công ty' : '❌ Failed to delete company');
        toast.error(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle open edit modal
   */
  const openEditModal = (company) => {
    setEditingCompany(company);
    setShowEditCompany(true);
  };

  /**
   * Handle open Google Drive config modal
   */
  const openGoogleDriveModal = (company) => {
    setSelectedCompanyForGDrive(company);
    setShowGoogleDriveModal(true);
  };

  /**
   * Handle open company detail modal
   */
  const openCompanyDetailModal = (company) => {
    setSelectedCompanyForDetail(company);
    setShowCompanyDetail(true);
  };

  return (
    <div>
      {/* Action Buttons */}
      {canAddCompany() && (
        <div className="mb-6 flex items-center justify-between">
          <div className="flex gap-3">
            <button
              onClick={() => setShowAddCompany(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-all font-medium"
            >
              {language === 'vi' ? 'Thêm công ty mới' : 'Add New Company'}
            </button>
            
            {(currentUser?.role === 'system_admin' || currentUser?.role === 'super_admin') && (
              <button
                onClick={() => setShowBaseFeeModal(true)}
                className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-2 rounded-lg transition-all font-medium flex items-center gap-2"
              >
                💰 {language === 'vi' ? 'Sửa Base Fee' : 'Edit Base Fee'}
              </button>
            )}
          </div>

          {/* Display Current Base Fee */}
          <div className="bg-gray-50 border border-gray-300 rounded-lg px-4 py-2">
            <span className="text-sm text-gray-600 mr-2">
              {language === 'vi' ? 'Base Fee hiện tại:' : 'Current Base Fee:'}
            </span>
            <span className="text-lg font-bold text-orange-600">
              ${baseFee.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      )}

      {/* Companies Table */}
      <CompanyTable
        companies={companies}
        loading={loading}
        currentUser={currentUser}
        language={language}
        canEditCompany={canEditCompany}
        canDeleteCompany={canDeleteCompany}
        onEditCompany={openEditModal}
        onDeleteCompany={handleDeleteCompany}
        onConfigureGoogleDrive={openGoogleDriveModal}
        onViewCompanyDetail={openCompanyDetailModal}
      />

      {/* Add Company Modal */}
      {showAddCompany && (
        <CompanyFormModal
          onClose={() => setShowAddCompany(false)}
          onSubmit={handleAddCompany}
          language={language}
          loading={loading}
          mode="add"
        />
      )}

      {/* Edit Company Modal */}
      {showEditCompany && editingCompany && (
        <CompanyFormModal
          company={editingCompany}
          onClose={() => {
            setShowEditCompany(false);
            setEditingCompany(null);
          }}
          onSubmit={handleEditCompany}
          language={language}
          loading={loading}
          mode="edit"
          currentUser={currentUser}
          onConfigureGoogleDrive={canConfigureGoogleDrive() ? openGoogleDriveModal : null}
        />
      )}

      {/* Google Drive Configuration Modal */}
      {showGoogleDriveModal && selectedCompanyForGDrive && (
        <CompanyGoogleDriveModal
          company={selectedCompanyForGDrive}
          onClose={() => {
            setShowGoogleDriveModal(false);
            setSelectedCompanyForGDrive(null);
          }}
          language={language}
        />
      )}

      {/* Company Detail Modal */}
      {showCompanyDetail && selectedCompanyForDetail && (
        <CompanyDetailModal
          company={selectedCompanyForDetail}
          onClose={() => {
            setShowCompanyDetail(false);
            setSelectedCompanyForDetail(null);
          }}
          language={language}
        />
      )}

      {/* Base Fee Modal */}
      {showBaseFeeModal && (
        <BaseFeeModal
          currentBaseFee={baseFee}
          onClose={() => setShowBaseFeeModal(false)}
          onUpdate={handleUpdateBaseFee}
          language={language}
        />
      )}
    </div>
  );
};

export default CompanyManagement;
