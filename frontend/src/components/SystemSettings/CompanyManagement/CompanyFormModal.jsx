/**
 * CompanyFormModal Component
 * Modal for adding/editing companies with logo upload and Google Drive config
 */
import React, { useState, useEffect } from 'react';

const CompanyFormModal = ({
  company, // For edit mode
  onClose,
  onSubmit,
  language,
  loading,
  mode, // 'add' or 'edit'
  currentUser,
  onConfigureGoogleDrive
}) => {
  const [companyData, setCompanyData] = useState({
    name_vn: '',
    name_en: '',
    address_vn: '',
    address_en: '',
    tax_id: '',
    gmail: '',
    zalo: '',
    logo_url: '',
    system_expiry: ''
  });

  const [logoFile, setLogoFile] = useState(null);
  const [logoPreview, setLogoPreview] = useState('');

  // Initialize form data for edit mode
  useEffect(() => {
    if (mode === 'edit' && company) {
      setCompanyData({
        name_vn: company.name_vn || '',
        name_en: company.name_en || '',
        address_vn: company.address_vn || '',
        address_en: company.address_en || '',
        tax_id: company.tax_id || '',
        gmail: company.gmail || '',
        zalo: company.zalo || '',
        logo_url: company.logo_url || '',
        system_expiry: company.system_expiry ? new Date(company.system_expiry).toISOString().split('T')[0] : ''
      });
      
      if (company.logo_url) {
        setLogoPreview(company.logo_url);
      }
    }
  }, [mode, company]);

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert(language === 'vi' ? 'Vui lòng chọn file ảnh!' : 'Please select an image file!');
        return;
      }
      
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert(language === 'vi' ? 'Kích thước file không được vượt quá 5MB!' : 'File size should not exceed 5MB!');
        return;
      }
      
      setLogoFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setLogoPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (mode === 'edit' && company) {
      await onSubmit(company.id, companyData, logoFile);
    } else {
      await onSubmit(companyData, logoFile);
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200 sticky top-0 bg-white">
          <h2 className="text-2xl font-bold text-gray-800">
            {mode === 'edit' 
              ? (language === 'vi' ? 'Chỉnh sửa công ty' : 'Edit Company')
              : (language === 'vi' ? 'Thêm công ty mới' : 'Add New Company')
            }
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            disabled={loading}
          >
            ×
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Company Names */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên công ty (Tiếng Việt)' : 'Company Name (Vietnamese)'} *
              </label>
              <input
                type="text"
                required
                value={companyData.name_vn}
                onChange={(e) => setCompanyData(prev => ({ ...prev, name_vn: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder={language === 'vi' ? 'Nhập tên công ty bằng tiếng Việt' : 'Enter company name in Vietnamese'}
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên công ty (Tiếng Anh)' : 'Company Name (English)'} *
              </label>
              <input
                type="text"
                required
                value={companyData.name_en}
                onChange={(e) => setCompanyData(prev => ({ ...prev, name_en: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder={language === 'vi' ? 'Nhập tên công ty bằng tiếng Anh' : 'Enter company name in English'}
                disabled={loading}
              />
            </div>
          </div>

          {/* Addresses */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Địa chỉ (Tiếng Việt)' : 'Address (Vietnamese)'} *
              </label>
              <textarea
                required
                value={companyData.address_vn}
                onChange={(e) => setCompanyData(prev => ({ ...prev, address_vn: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none"
                rows="3"
                placeholder={language === 'vi' ? 'Nhập địa chỉ bằng tiếng Việt' : 'Enter address in Vietnamese'}
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Địa chỉ (Tiếng Anh)' : 'Address (English)'} *
              </label>
              <textarea
                required
                value={companyData.address_en}
                onChange={(e) => setCompanyData(prev => ({ ...prev, address_en: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none"
                rows="3"
                placeholder={language === 'vi' ? 'Nhập địa chỉ bằng tiếng Anh' : 'Enter address in English'}
                disabled={loading}
              />
            </div>
          </div>

          {/* Tax ID */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Mã số thuế' : 'Tax ID'} *
            </label>
            <input
              type="text"
              required
              value={companyData.tax_id}
              onChange={(e) => setCompanyData(prev => ({ ...prev, tax_id: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder={language === 'vi' ? 'Nhập mã số thuế' : 'Enter tax ID'}
              disabled={loading}
            />
          </div>

          {/* Gmail & Zalo */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Gmail</label>
              <input
                type="email"
                value={companyData.gmail}
                onChange={(e) => setCompanyData(prev => ({ ...prev, gmail: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="company@gmail.com"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Zalo</label>
              <input
                type="text"
                value={companyData.zalo}
                onChange={(e) => setCompanyData(prev => ({ ...prev, zalo: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder={language === 'vi' ? 'Số điện thoại Zalo' : 'Zalo phone number'}
                disabled={loading}
              />
            </div>
          </div>

          {/* Logo Upload Section */}
          <div className="border-t pt-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">
              {language === 'vi' ? 'Logo công ty' : 'Company Logo'}
            </h3>
            
            {/* Logo URL */}
            <div className="mb-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'URL Logo (Ưu tiên)' : 'Logo URL (Priority)'}
              </label>
              <input
                type="url"
                value={companyData.logo_url}
                onChange={(e) => {
                  setCompanyData(prev => ({ ...prev, logo_url: e.target.value }));
                  if (e.target.value) {
                    setLogoPreview(e.target.value);
                    setLogoFile(null);
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="https://example.com/logo.png"
                disabled={loading}
              />
              <p className="text-xs text-gray-500 mt-1">
                {language === 'vi' 
                  ? '* Nếu có URL, file upload sẽ bị bỏ qua'
                  : '* If URL is provided, file upload will be ignored'}
              </p>
            </div>

            {/* File Upload */}
            {!companyData.logo_url && (
              <div className="mb-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Hoặc tải lên file' : 'Or Upload File'}
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  disabled={loading}
                />
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi' 
                    ? 'JPG, PNG, GIF (tối đa 5MB)'
                    : 'JPG, PNG, GIF (max 5MB)'}
                </p>
              </div>
            )}

            {/* Logo Preview */}
            {logoPreview && (
              <div className="mt-3">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Xem trước' : 'Preview'}
                </label>
                <img 
                  src={logoPreview} 
                  alt="Logo preview" 
                  className="w-32 h-32 object-contain border border-gray-300 rounded-lg p-2"
                />
              </div>
            )}
          </div>

          {/* System Expiry */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Ngày hết hạn hệ thống' : 'System Expiry Date'}
            </label>
            <input
              type="date"
              value={companyData.system_expiry}
              onChange={(e) => setCompanyData(prev => ({ ...prev, system_expiry: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
          </div>

          {/* Company Google Drive Configuration (Edit mode only) */}
          {mode === 'edit' && company && onConfigureGoogleDrive && (
            <div className="border-t pt-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">
                ☁️ {language === 'vi' ? 'Google Drive của công ty' : 'Company Google Drive'}
              </h3>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-3">
                <p className="text-sm text-blue-700 mb-3">
                  {language === 'vi' 
                    ? 'Cấu hình Google Drive riêng cho công ty này để lưu trữ tài liệu. Hỗ trợ Apps Script, OAuth 2.0 và Service Account.'
                    : 'Configure dedicated Google Drive for this company to store documents. Supports Apps Script, OAuth 2.0, and Service Account.'
                  }
                </p>
                <button
                  type="button"
                  onClick={() => onConfigureGoogleDrive(company)}
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg transition-all font-medium flex items-center gap-2"
                >
                  ⚙️ {language === 'vi' ? 'Cấu hình Google Drive' : 'Configure Google Drive'}
                </button>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all font-medium"
              disabled={loading}
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white rounded-lg transition-all font-medium"
              disabled={loading}
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {language === 'vi' ? 'Đang xử lý...' : 'Processing...'}
                </div>
              ) : (
                mode === 'edit'
                  ? (language === 'vi' ? 'Cập nhật' : 'Update')
                  : (language === 'vi' ? 'Thêm công ty' : 'Add Company')
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CompanyFormModal;
