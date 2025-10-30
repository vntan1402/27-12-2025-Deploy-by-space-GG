/**
 * Add Ship Modal Component
 * Full form for creating new ship with all fields
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { shipService, companyService } from '../../services';

const AddShipModal = ({ isOpen, onClose }) => {
  const { language, user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [companies, setCompanies] = useState([]);
  
  // Form data state
  const [formData, setFormData] = useState({
    // Basic Info
    name: '',
    imo: '',
    flag: '',
    ship_type: '',
    class_society: '',
    company: '',
    ship_owner: '',
    
    // Technical Details
    gross_tonnage: '',
    deadweight: '',
    built_year: '',
    delivery_date: '',
    keel_laid: '',
    
    // Survey Dates
    last_docking: '',
    last_docking_2: '',
    next_docking: '',
    last_special_survey: '',
    last_intermediate_survey: '',
  });

  useEffect(() => {
    if (isOpen) {
      fetchUserCompany();
    }
  }, [isOpen, user]);

  const fetchUserCompany = async () => {
    try {
      const response = await companyService.getAll();
      const allCompanies = response.data || response;
      
      // Find user's company by matching name
      const userCompany = allCompanies.find(c => {
        const companyNames = [
          c.name,
          c.name_en,
          c.name_vn
        ].filter(Boolean);
        
        return companyNames.some(name => 
          name === user.company || 
          name.toLowerCase() === user.company?.toLowerCase()
        );
      });
      
      if (userCompany) {
        setCompanies([userCompany]);
        // Set company name (prefer name_en, then name_vn, then name)
        const companyName = userCompany.name_en || userCompany.name_vn || userCompany.name;
        setFormData(prev => ({
          ...prev,
          company: companyName
        }));
      } else {
        // If no match found, use user.company as fallback
        setCompanies([]);
        setFormData(prev => ({
          ...prev,
          company: user.company || ''
        }));
      }
    } catch (error) {
      console.error('Failed to fetch company:', error);
      // On error, fallback to user.company
      setFormData(prev => ({
        ...prev,
        company: user.company || ''
      }));
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate required fields
    if (!formData.name || !formData.flag || !formData.ship_type || !formData.company) {
      toast.error(language === 'vi' 
        ? 'Vui lòng điền đầy đủ thông tin bắt buộc (Name, Flag, Ship Type, Company)' 
        : 'Please fill in all required fields (Name, Flag, Ship Type, Company)'
      );
      return;
    }

    try {
      setLoading(true);
      
      // Prepare data - convert numeric fields
      const shipData = {
        ...formData,
        gross_tonnage: formData.gross_tonnage ? parseFloat(formData.gross_tonnage) : null,
        deadweight: formData.deadweight ? parseFloat(formData.deadweight) : null,
        built_year: formData.built_year ? parseInt(formData.built_year) : null,
        // Convert date strings to ISO format if provided
        delivery_date: formData.delivery_date || null,
        keel_laid: formData.keel_laid || null,
        last_docking: formData.last_docking || null,
        last_docking_2: formData.last_docking_2 || null,
        next_docking: formData.next_docking || null,
        last_special_survey: formData.last_special_survey || null,
        last_intermediate_survey: formData.last_intermediate_survey || null,
      };

      // Remove empty strings
      Object.keys(shipData).forEach(key => {
        if (shipData[key] === '') {
          shipData[key] = null;
        }
      });

      const response = await shipService.create(shipData);
      
      toast.success(language === 'vi' 
        ? `Tàu "${formData.name}" đã được tạo thành công! Đang tạo folder structure...` 
        : `Ship "${formData.name}" created successfully! Creating folder structure...`
      );
      
      onClose();
      
      // Navigate to ship detail page
      if (response.id) {
        navigate(`/ships/${response.id}`);
      }
      
    } catch (error) {
      console.error('Failed to create ship:', error);
      const errorMsg = error.response?.data?.detail || error.message;
      toast.error(language === 'vi' 
        ? `Không thể tạo tàu: ${errorMsg}` 
        : `Failed to create ship: ${errorMsg}`
      );
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const t = {
    title: language === 'vi' ? 'Thêm Tàu Mới' : 'Add New Ship',
    basicInfo: language === 'vi' ? 'Thông Tin Cơ Bản' : 'Basic Information',
    technicalDetails: language === 'vi' ? 'Chi Tiết Kỹ Thuật' : 'Technical Details',
    surveyDates: language === 'vi' ? 'Ngày Đăng Kiểm' : 'Survey Dates',
    ownerInfo: language === 'vi' ? 'Thông Tin Chủ Sở Hữu' : 'Owner Information',
    
    // Fields
    shipName: language === 'vi' ? 'Tên Tàu' : 'Ship Name',
    imoNumber: language === 'vi' ? 'Số IMO' : 'IMO Number',
    flag: language === 'vi' ? 'Cờ' : 'Flag',
    shipType: language === 'vi' ? 'Loại Tàu / Class Society' : 'Ship Type / Class Society',
    company: language === 'vi' ? 'Công Ty' : 'Company',
    grossTonnage: language === 'vi' ? 'Gross Tonnage' : 'Gross Tonnage',
    deadweight: language === 'vi' ? 'Deadweight (DWT)' : 'Deadweight (DWT)',
    builtYear: language === 'vi' ? 'Năm Đóng' : 'Built Year',
    deliveryDate: language === 'vi' ? 'Ngày Giao Tàu' : 'Delivery Date',
    keelLaid: language === 'vi' ? 'Ngày Đặt Sống' : 'Keel Laid Date',
    lastDocking: language === 'vi' ? 'Docking Gần Nhất' : 'Last Docking',
    lastDocking2: language === 'vi' ? 'Docking Gần Nhất 2' : 'Last Docking 2',
    nextDocking: language === 'vi' ? 'Docking Tiếp Theo' : 'Next Docking',
    lastSpecialSurvey: language === 'vi' ? 'Special Survey Gần Nhất' : 'Last Special Survey',
    lastIntermediateSurvey: language === 'vi' ? 'Intermediate Survey Gần Nhất' : 'Last Intermediate Survey',
    shipOwner: language === 'vi' ? 'Chủ Tàu' : 'Ship Owner',
    
    // Buttons
    cancel: language === 'vi' ? 'Hủy' : 'Cancel',
    create: language === 'vi' ? 'Tạo Tàu' : 'Create Ship',
    creating: language === 'vi' ? 'Đang tạo...' : 'Creating...',
    
    // Placeholders
    required: language === 'vi' ? '(Bắt buộc)' : '(Required)',
    optional: language === 'vi' ? '(Tùy chọn)' : '(Optional)',
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 flex justify-between items-center">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <span>🚢</span>
            {t.title}
          </h2>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 text-3xl font-bold leading-none"
            disabled={loading}
          >
            ×
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 140px)' }}>
          
          {/* Basic Information Section */}
          <div className="mb-8">
            <h3 className="text-lg font-bold text-gray-800 mb-4 pb-2 border-b-2 border-blue-500">
              📋 {t.basicInfo}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Ship Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.shipName} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., MV PACIFIC HARMONY"
                />
              </div>

              {/* IMO Number */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.imoNumber} {t.optional}
                </label>
                <input
                  type="text"
                  name="imo"
                  value={formData.imo}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 9876543"
                />
              </div>

              {/* Flag */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.flag} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="flag"
                  value={formData.flag}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Panama, Singapore, Marshall Islands"
                />
              </div>

              {/* Ship Type / Class Society */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.shipType} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="ship_type"
                  value={formData.ship_type}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., DNV GL, ABS, Lloyd's Register, BV"
                />
              </div>

              {/* Company */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.company} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="company"
                  value={formData.company}
                  readOnly
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi' ? 'Tàu sẽ được gán cho công ty của bạn' : 'Ship will be assigned to your company'}
                </p>
              </div>
            </div>
          </div>

          {/* Technical Details Section */}
          <div className="mb-8">
            <h3 className="text-lg font-bold text-gray-800 mb-4 pb-2 border-b-2 border-blue-500">
              ⚙️ {t.technicalDetails}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Gross Tonnage */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.grossTonnage} {t.optional}
                </label>
                <input
                  type="number"
                  step="0.01"
                  name="gross_tonnage"
                  value={formData.gross_tonnage}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 75000"
                />
              </div>

              {/* Deadweight */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.deadweight} {t.optional}
                </label>
                <input
                  type="number"
                  step="0.01"
                  name="deadweight"
                  value={formData.deadweight}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 150000"
                />
              </div>

              {/* Built Year */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.builtYear} {t.optional}
                </label>
                <input
                  type="number"
                  name="built_year"
                  value={formData.built_year}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 2010"
                  min="1900"
                  max={new Date().getFullYear() + 5}
                />
              </div>

              {/* Delivery Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.deliveryDate} {t.optional}
                </label>
                <input
                  type="date"
                  name="delivery_date"
                  value={formData.delivery_date}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Keel Laid */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.keelLaid} {t.optional}
                </label>
                <input
                  type="date"
                  name="keel_laid"
                  value={formData.keel_laid}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Survey Dates Section */}
          <div className="mb-8">
            <h3 className="text-lg font-bold text-gray-800 mb-4 pb-2 border-b-2 border-blue-500">
              📅 {t.surveyDates}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Last Docking */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.lastDocking} {t.optional}
                </label>
                <input
                  type="date"
                  name="last_docking"
                  value={formData.last_docking}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Last Docking 2 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.lastDocking2} {t.optional}
                </label>
                <input
                  type="date"
                  name="last_docking_2"
                  value={formData.last_docking_2}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Next Docking */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.nextDocking} {t.optional}
                </label>
                <input
                  type="date"
                  name="next_docking"
                  value={formData.next_docking}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Last Special Survey */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.lastSpecialSurvey} {t.optional}
                </label>
                <input
                  type="date"
                  name="last_special_survey"
                  value={formData.last_special_survey}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Last Intermediate Survey */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.lastIntermediateSurvey} {t.optional}
                </label>
                <input
                  type="date"
                  name="last_intermediate_survey"
                  value={formData.last_intermediate_survey}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Owner Information Section */}
          <div className="mb-8">
            <h3 className="text-lg font-bold text-gray-800 mb-4 pb-2 border-b-2 border-blue-500">
              👤 {t.ownerInfo}
            </h3>
            <div className="grid grid-cols-1 gap-4">
              {/* Ship Owner */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.shipOwner} {t.optional}
                </label>
                <input
                  type="text"
                  name="ship_owner"
                  value={formData.ship_owner}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Pacific Shipping Company Ltd."
                />
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {t.cancel}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>}
              {loading ? t.creating : t.create}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddShipModal;
