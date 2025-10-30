import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { shipService, companyService } from '../../services';
import { toast } from 'react-toastify';

const EditShipModal = ({ isOpen, onClose, ship, onShipUpdated }) => {
  const { language, user } = useAuth();
  const navigate = useNavigate();
  
  // State for ship data
  const [shipData, setShipData] = useState({
    name: '',
    imo_number: '',
    ship_type: '',
    class_society: '',
    flag: '',
    gross_tonnage: '',
    deadweight: '',
    built_year: '',
    delivery_date: '',
    keel_laid: '',
    ship_owner: '',
    company: user?.company || '',
    // Docking information
    last_docking: '',
    last_docking_2: '',
    next_docking: '',
    // Survey information
    last_special_survey: '',
    last_intermediate_survey: '',
    special_survey_from_date: '',
    special_survey_to_date: '',
    // Anniversary date
    anniversary_date_day: '',
    anniversary_date_month: '',
  });
  
  // State for companies list (for ship_owner dropdown)
  const [availableCompanies, setAvailableCompanies] = useState([]);
  const [isLoadingCompanies, setIsLoadingCompanies] = useState(false);
  const [userCompanyName, setUserCompanyName] = useState('');
  
  // State for form submission
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load ship data when modal opens
  useEffect(() => {
    if (isOpen && ship) {
      // Format dates from backend (ISO datetime or MM/YYYY) to input format (YYYY-MM-DD or MM/YYYY)
      setShipData({
        name: ship.name || '',
        imo_number: ship.imo || '',
        ship_type: ship.ship_type || '',
        class_society: ship.class_society || '',
        flag: ship.flag || '',
        gross_tonnage: ship.gross_tonnage ? String(ship.gross_tonnage) : '',
        deadweight: ship.deadweight ? String(ship.deadweight) : '',
        built_year: ship.built_year ? String(ship.built_year) : '',
        delivery_date: formatDateFromBackend(ship.delivery_date) || '',
        keel_laid: formatDateFromBackend(ship.keel_laid) || '',
        ship_owner: ship.ship_owner || '',
        company: ship.company || user?.company || '',
        // Docking information
        last_docking: formatLastDockingFromBackend(ship.last_docking) || '',
        last_docking_2: formatLastDockingFromBackend(ship.last_docking_2) || '',
        next_docking: formatDateFromBackend(ship.next_docking) || '',
        // Survey information
        last_special_survey: formatDateFromBackend(ship.last_special_survey) || '',
        last_intermediate_survey: formatDateFromBackend(ship.last_intermediate_survey) || '',
        special_survey_from_date: formatDateFromBackend(ship.special_survey_cycle?.from_date) || '',
        special_survey_to_date: formatDateFromBackend(ship.special_survey_cycle?.to_date) || '',
        // Anniversary date
        anniversary_date_day: ship.anniversary_date?.day ? String(ship.anniversary_date.day) : '',
        anniversary_date_month: ship.anniversary_date?.month ? String(ship.anniversary_date.month) : '',
      });
      
      fetchCompanies();
    }
  }, [isOpen, ship]);

  const fetchCompanies = async () => {
    try {
      setIsLoadingCompanies(true);
      const response = await companyService.getAll();
      // Response is axios response object, get data from it
      const companies = response.data || [];
      setAvailableCompanies(companies);
      
      // Find and set user's company name
      if (user && user.company && companies.length > 0) {
        const userCompany = companies.find(c => 
          c.id === user.company || 
          c.name_vn === user.company || 
          c.name_en === user.company ||
          c.name === user.company
        );
        
        if (userCompany) {
          const companyName = language === 'vi' ? userCompany.name_vn : userCompany.name_en;
          setUserCompanyName(companyName);
        } else {
          setUserCompanyName(user.company);
        }
      }
    } catch (error) {
      console.error('Failed to fetch companies:', error);
      toast.error(language === 'vi' 
        ? '❌ Không thể tải danh sách công ty'
        : '❌ Failed to load companies list'
      );
      setAvailableCompanies([]);
      if (user && user.company) {
        setUserCompanyName(user.company);
      }
    } finally {
      setIsLoadingCompanies(false);
    }
  };

  // Helper function to format date from backend (ISO datetime) to input (YYYY-MM-DD)
  const formatDateFromBackend = (dateStr) => {
    if (!dateStr || dateStr === 'null' || dateStr === 'N/A') return '';
    
    try {
      // If ISO datetime, extract date part
      if (typeof dateStr === 'string' && (dateStr.includes('T') || dateStr.includes('Z'))) {
        return dateStr.split('T')[0];
      }
      
      // If already YYYY-MM-DD
      if (typeof dateStr === 'string' && dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
        return dateStr;
      }
      
      return '';
    } catch (error) {
      console.error('Date format error:', error);
      return '';
    }
  };

  // Helper function to format last docking from backend (ISO datetime) to display (MM/YYYY)
  const formatLastDockingFromBackend = (dockingStr) => {
    if (!dockingStr || dockingStr === 'null' || dockingStr === 'N/A') return '';
    
    try {
      // If ISO datetime (YYYY-MM-DDTHH:MM:SSZ), convert to MM/YYYY
      if (typeof dockingStr === 'string' && (dockingStr.includes('T') || dockingStr.includes('Z'))) {
        const datePart = dockingStr.split('T')[0]; // YYYY-MM-DD
        const [year, month] = datePart.split('-');
        return `${month}/${year}`;
      }
      
      // If already in MM/YYYY format
      if (typeof dockingStr === 'string' && dockingStr.match(/^\d{1,2}\/\d{4}$/)) {
        return dockingStr;
      }
      
      return dockingStr;
    } catch (error) {
      console.error('Docking format error:', error);
      return dockingStr;
    }
  };

  // Helper function to convert date input (YYYY-MM-DD) to UTC datetime for backend
  const convertDateInputToUTC = (dateStr) => {
    if (!dateStr || dateStr.trim() === '') return null;
    
    try {
      // If already in ISO datetime format, return as is
      if (dateStr.includes('T') || dateStr.includes('Z')) {
        return dateStr;
      }
      
      // Convert YYYY-MM-DD to ISO datetime (UTC)
      if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
        return `${dateStr}T00:00:00Z`;
      }
      
      return null;
    } catch (error) {
      console.error('Date conversion error:', error);
      return null;
    }
  };

  // Helper function to convert last docking MM/YYYY to datetime for backend
  const formatLastDockingForBackend = (dockingStr) => {
    if (!dockingStr || dockingStr.trim() === '') return null;
    
    try {
      // If in MM/YYYY format, convert to ISO datetime (YYYY-MM-01T00:00:00Z)
      const mmYyyyPattern = /^\d{1,2}\/\d{4}$/;
      if (typeof dockingStr === 'string' && mmYyyyPattern.test(dockingStr.trim())) {
        const [month, year] = dockingStr.trim().split('/');
        const paddedMonth = month.padStart(2, '0');
        return `${year}-${paddedMonth}-01T00:00:00Z`;
      }
      
      // If already in YYYY-MM-DD format, convert to ISO datetime
      if (typeof dockingStr === 'string' && dockingStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
        return `${dockingStr}T00:00:00Z`;
      }
      
      // If already in ISO datetime format, return as is
      if (typeof dockingStr === 'string' && (dockingStr.includes('T') || dockingStr.includes('Z'))) {
        return dockingStr;
      }
      
      return null;
    } catch (error) {
      console.error('Last docking format error:', error);
      return null;
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate required fields (Ship Type is optional)
    if (!shipData.name || !shipData.imo_number || !shipData.class_society || 
        !shipData.flag || !shipData.company || !shipData.ship_owner) {
      toast.error(language === 'vi' 
        ? '❌ Vui lòng điền đầy đủ các trường bắt buộc'
        : '❌ Please fill in all required fields'
      );
      return;
    }

    setIsSubmitting(true);
    try {
      // Prepare ship data for API
      const apiData = {
        name: shipData.name.trim(),
        imo: shipData.imo_number.trim(),
        ship_type: shipData.ship_type.trim() || null,
        class_society: shipData.class_society.trim(),
        flag: shipData.flag.trim(),
        gross_tonnage: shipData.gross_tonnage ? parseFloat(shipData.gross_tonnage) : null,
        deadweight: shipData.deadweight ? parseFloat(shipData.deadweight) : null,
        built_year: shipData.built_year ? parseInt(shipData.built_year) : null,
        delivery_date: convertDateInputToUTC(shipData.delivery_date),
        keel_laid: convertDateInputToUTC(shipData.keel_laid),
        ship_owner: shipData.ship_owner.trim(),
        company: shipData.company.trim(),
        // Docking information - convert MM/YYYY format to ISO datetime
        last_docking: formatLastDockingForBackend(shipData.last_docking),
        last_docking_2: formatLastDockingForBackend(shipData.last_docking_2),
        next_docking: convertDateInputToUTC(shipData.next_docking),
        // Survey information - convert to ISO datetime
        last_special_survey: convertDateInputToUTC(shipData.last_special_survey),
        last_intermediate_survey: convertDateInputToUTC(shipData.last_intermediate_survey),
        special_survey_from_date: convertDateInputToUTC(shipData.special_survey_from_date),
        special_survey_to_date: convertDateInputToUTC(shipData.special_survey_to_date),
        // Anniversary date
        anniversary_date_day: shipData.anniversary_date_day ? parseInt(shipData.anniversary_date_day) : null,
        anniversary_date_month: shipData.anniversary_date_month ? parseInt(shipData.anniversary_date_month) : null,
      };

      console.log('Updating ship with data:', apiData);
      
      const response = await shipService.update(ship.id, apiData);
      
      console.log('Ship update response:', response);
      
      if (response && response.data) {
        toast.success(language === 'vi' 
          ? `✅ Cập nhật tàu ${shipData.name} thành công!`
          : `✅ Ship ${shipData.name} updated successfully!`
        );
        
        // Call callback to refresh ship data
        if (onShipUpdated) {
          onShipUpdated(response.data);
        }
        
        // Close modal
        onClose();
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Failed to update ship:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);
      
      const errorMessage = error.response?.data?.detail || error.message;
      toast.error(language === 'vi' 
        ? `❌ Lỗi cập nhật tàu: ${errorMessage}`
        : `❌ Failed to update ship: ${errorMessage}`
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle close
  const handleClose = () => {
    if (isSubmitting) {
      return; // Prevent closing during operations
    }
    
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        {/* Modal Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between z-10">
          <h2 className="text-2xl font-bold text-gray-800">
            🚢 {language === 'vi' ? 'Chỉnh sửa thông tin tàu' : 'Edit Ship Information'}
          </h2>
          <button
            onClick={handleClose}
            disabled={isSubmitting}
            className="text-gray-500 hover:text-gray-700 text-2xl font-bold disabled:opacity-50"
          >
            ×
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="p-6">
          {/* Basic Information Section */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b">
              {language === 'vi' ? 'Thông tin cơ bản' : 'Basic Information'}
            </h3>
            
            <div className="grid grid-cols-12 gap-4">
              {/* Company - locked to user's company */}
              <div className="col-span-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Công ty' : 'Company'} *
                </label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    disabled
                    value={userCompanyName || shipData.company}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed"
                    placeholder={isLoadingCompanies ? (language === 'vi' ? 'Đang tải...' : 'Loading...') : ''}
                  />
                  <div className="absolute right-3 top-2 text-gray-400">
                    🔒
                  </div>
                </div>
              </div>

              {/* Ship Owner */}
              <div className="col-span-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Chủ tàu' : 'Ship Owner'} *
                </label>
                <select
                  required
                  value={shipData.ship_owner}
                  onChange={(e) => setShipData(prev => ({ ...prev, ship_owner: e.target.value }))}
                  disabled={isLoadingCompanies}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">{language === 'vi' ? 'Chọn chủ tàu' : 'Select ship owner'}</option>
                  {availableCompanies.map(company => (
                    <option key={company.id} value={language === 'vi' ? company.name_vn : company.name_en}>
                      {language === 'vi' ? company.name_vn : company.name_en}
                    </option>
                  ))}
                </select>
              </div>

              {/* Ship Name */}
              <div className="col-span-12">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tên tàu' : 'Ship Name'} *
                </label>
                <input
                  type="text"
                  required
                  value={shipData.name}
                  onChange={(e) => setShipData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'Nhập tên tàu' : 'Enter ship name'}
                />
              </div>

              {/* IMO Number, Flag, Class Society, Ship Type - all in one row */}
              <div className="col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Số IMO' : 'IMO Number'} *
                </label>
                <input
                  type="text"
                  required
                  value={shipData.imo_number}
                  onChange={(e) => setShipData(prev => ({ ...prev, imo_number: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="1234567"
                />
              </div>

              {/* Flag */}
              <div className="col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Cờ' : 'Flag'} *
                </label>
                <input
                  type="text"
                  required
                  value={shipData.flag}
                  onChange={(e) => setShipData(prev => ({ ...prev, flag: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'Việt Nam, Singapore...' : 'Vietnam, Singapore...'}
                />
              </div>

              {/* Class Society */}
              <div className="col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Đăng kiểm' : 'Class Society'} *
                </label>
                <input
                  type="text"
                  required
                  value={shipData.class_society}
                  onChange={(e) => setShipData(prev => ({ ...prev, class_society: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="DNV GL, ABS, LR..."
                />
              </div>

              {/* Ship Type - Optional */}
              <div className="col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Loại tàu' : 'Ship Type'}
                </label>
                <input
                  type="text"
                  value={shipData.ship_type}
                  onChange={(e) => setShipData(prev => ({ ...prev, ship_type: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'Container, Bulk Carrier, Tanker...' : 'Container, Bulk Carrier, Tanker...'}
                />
              </div>
            </div>
          </div>

          {/* Technical Details Section */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b">
              {language === 'vi' ? 'Thông tin kỹ thuật' : 'Technical Details'}
            </h3>
            
            <div className="grid grid-cols-12 gap-4">
              {/* Gross Tonnage */}
              <div className="col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'GT (Tổng Dung Tích)' : 'GT (Gross Tonnage)'}
                </label>
                <input
                  type="number"
                  value={shipData.gross_tonnage}
                  onChange={(e) => setShipData(prev => ({ ...prev, gross_tonnage: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0"
                />
              </div>

              {/* Deadweight */}
              <div className="col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'DWT (Trọng tải)' : 'DWT (Deadweight)'}
                </label>
                <input
                  type="number"
                  value={shipData.deadweight}
                  onChange={(e) => setShipData(prev => ({ ...prev, deadweight: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0"
                />
              </div>

              {/* Built Year */}
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Năm đóng' : 'Built Year'}
                </label>
                <input
                  type="number"
                  value={shipData.built_year}
                  onChange={(e) => setShipData(prev => ({ ...prev, built_year: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="2020"
                />
              </div>

              {/* Delivery Date */}
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày giao' : 'Delivery Date'}
                </label>
                <input
                  type="date"
                  value={shipData.delivery_date}
                  onChange={(e) => setShipData(prev => ({ ...prev, delivery_date: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Keel Laid */}
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Keel Laid' : 'Keel Laid'}
                </label>
                <input
                  type="date"
                  value={shipData.keel_laid}
                  onChange={(e) => setShipData(prev => ({ ...prev, keel_laid: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Anniversary Date - Day */}
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Anniversary (Ngày)' : 'Anniversary (Day)'}
                </label>
                <input
                  type="number"
                  min="1"
                  max="31"
                  value={shipData.anniversary_date_day}
                  onChange={(e) => setShipData(prev => ({ ...prev, anniversary_date_day: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="15"
                />
              </div>

              {/* Anniversary Date - Month */}
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Anniversary (Tháng)' : 'Anniversary (Month)'}
                </label>
                <input
                  type="number"
                  min="1"
                  max="12"
                  value={shipData.anniversary_date_month}
                  onChange={(e) => setShipData(prev => ({ ...prev, anniversary_date_month: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="6"
                />
              </div>
            </div>
          </div>

          {/* Survey Dates Section */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b">
              {language === 'vi' ? 'Thông tin khảo sát' : 'Survey Dates'}
            </h3>
            
            <div className="grid grid-cols-12 gap-4">
              {/* Last Special Survey */}
              <div className="col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Last Special Survey' : 'Last Special Survey'}
                </label>
                <input
                  type="date"
                  value={shipData.last_special_survey}
                  onChange={(e) => setShipData(prev => ({ ...prev, last_special_survey: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Last Intermediate Survey */}
              <div className="col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Last Intermediate Survey' : 'Last Intermediate Survey'}
                </label>
                <input
                  type="date"
                  value={shipData.last_intermediate_survey}
                  onChange={(e) => setShipData(prev => ({ ...prev, last_intermediate_survey: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Special Survey From Date */}
              <div className="col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Special Survey From' : 'Special Survey From'}
                </label>
                <input
                  type="date"
                  value={shipData.special_survey_from_date}
                  onChange={(e) => setShipData(prev => ({ ...prev, special_survey_from_date: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Special Survey To Date */}
              <div className="col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Special Survey To' : 'Special Survey To'}
                </label>
                <input
                  type="date"
                  value={shipData.special_survey_to_date}
                  onChange={(e) => setShipData(prev => ({ ...prev, special_survey_to_date: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Last Docking Section */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b">
              {language === 'vi' ? 'Thông tin Docking' : 'Docking Information'}
            </h3>
            
            <div className="grid grid-cols-12 gap-4">
              {/* Last Docking */}
              <div className="col-span-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Last Docking 1' : 'Last Docking 1'}
                </label>
                <input
                  type="text"
                  value={shipData.last_docking}
                  onChange={(e) => setShipData(prev => ({ ...prev, last_docking: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="11/2020"
                />
              </div>

              {/* Last Docking 2 */}
              <div className="col-span-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Last Docking 2' : 'Last Docking 2'}
                </label>
                <input
                  type="text"
                  value={shipData.last_docking_2}
                  onChange={(e) => setShipData(prev => ({ ...prev, last_docking_2: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="08/2021"
                />
              </div>

              {/* Next Docking */}
              <div className="col-span-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Next Docking' : 'Next Docking'}
                </label>
                <input
                  type="date"
                  value={shipData.next_docking}
                  onChange={(e) => setShipData(prev => ({ ...prev, next_docking: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-4 pt-4 border-t">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSubmitting && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              )}
              {isSubmitting 
                ? (language === 'vi' ? 'Đang cập nhật...' : 'Updating...') 
                : (language === 'vi' ? 'Cập nhật tàu' : 'Update Ship')
              }
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditShipModal;
