/**
 * Company Management Container
 * Main component for managing companies with role-based permissions
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useAuth } from '../../../contexts/AuthContext';
import { companyService } from '../../../services/companyService';
import CompanyTable from './CompanyTable';
import CompanyFormModal from './CompanyFormModal';
import CompanyGoogleDriveModal from './CompanyGoogleDriveModal';

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

  // Fetch companies on mount
  useEffect(() => {
    fetchCompanies();
  }, []);

  /**
   * Fetch all companies
   */
  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const response = await companyService.getAll();
      setCompanies(response.data || []);
    } catch (error) {
      console.error('Failed to fetch companies:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách công ty' : 'Failed to load companies');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Check if user can add company (Super Admin only)
   */
  const canAddCompany = () => {
    return currentUser.role === 'super_admin';
  };

  /**
   * Check if user can edit company
   * - Super Admin: Can edit all companies
   * - Admin: Can only edit own company
   */
  const canEditCompany = (company) => {
    if (currentUser.role === 'super_admin') {
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
   * Check if user can delete company (Super Admin only)
   */
  const canDeleteCompany = (company) => {
    return currentUser.role === 'super_admin';
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

  return (
    <div>
      {/* Action Button */}
      {canAddCompany() && (
        <div className="mb-6">
          <button
            onClick={() => setShowAddCompany(true)}
            className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-2 rounded-lg transition-all font-medium"
          >
            {language === 'vi' ? 'Thêm công ty mới' : 'Add New Company'}
          </button>
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
          onConfigureGoogleDrive={openGoogleDriveModal}
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
    </div>
  );
};

export default CompanyManagement;
