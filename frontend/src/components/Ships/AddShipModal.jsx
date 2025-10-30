import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { shipService, companyService } from '../../services';
import api from '../../services/api';
import { toast } from 'react-toastify';

const AddShipModal = ({ isOpen, onClose, onShipCreated }) => {
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

  // State for AI analysis
  const [pdfFile, setPdfFile] = useState(null);
  const [isPdfAnalyzing, setIsPdfAnalyzing] = useState(false);
  
  // State for companies list (for ship_owner dropdown)
  const [availableCompanies, setAvailableCompanies] = useState([]);
  const [isLoadingCompanies, setIsLoadingCompanies] = useState(false);
  const [userCompanyName, setUserCompanyName] = useState('');
  
  // State for form submission
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch companies on mount and get user's company name
  useEffect(() => {
    if (isOpen) {
      fetchCompanies();
    } else {
      // Reset form when modal closes to prevent stale state
      setShipData({
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
        last_docking: '',
        last_docking_2: '',
        next_docking: '',
        last_special_survey: '',
        last_intermediate_survey: '',
        special_survey_from_date: '',
        special_survey_to_date: '',
        anniversary_date_day: '',
        anniversary_date_month: '',
      });
      setPdfFile(null);
      setIsPdfAnalyzing(false);
      setIsSubmitting(false);
      setUserCompanyName('');
    }
  }, [isOpen, user?.company]);

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
          
          // Update shipData with company name
          setShipData(prev => ({
            ...prev,
            company: companyName
          }));
        } else {
          // Fallback to user.company if not found in list
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
      // Fallback to user.company
      if (user && user.company) {
        setUserCompanyName(user.company);
      }
    } finally {
      setIsLoadingCompanies(false);
    }
  };

  // Handle PDF file upload for AI analysis
  const handlePdfFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        toast.error(language === 'vi' 
          ? '❌ Chỉ chấp nhận file PDF'
          : '❌ Only PDF files are accepted'
        );
        return;
      }
      
      if (file.size > 10 * 1024 * 1024) {
        toast.error(language === 'vi' 
          ? '❌ File quá lớn. Tối đa 10MB'
          : '❌ File too large. Maximum 10MB'
        );
        return;
      }
      
      setPdfFile(file);
      analyzePdfWithAI(file);
    }
  };

  // Analyze PDF with AI
  const analyzePdfWithAI = async (file) => {
    if (!file) {
      toast.error(language === 'vi' 
        ? '❌ Vui lòng chọn file PDF'
        : '❌ Please select a PDF file'
      );
      return;
    }

    setIsPdfAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/api/analyze-ship-certificate', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 90000 // 90 seconds for AI analysis
      });

      if (response.data.success) {
        const analysisData = response.data.analysis || {};
        
        // Check for errors
        if (analysisData?.error) {
          toast.error(language === 'vi' 
            ? `❌ Phân tích thất bại: ${analysisData.error}`
            : `❌ Analysis failed: ${analysisData.error}`
          );
          return;
        }
        
        // Check if we have meaningful extracted data
        const validFields = Object.keys(analysisData).filter(key => {
          const value = analysisData[key];
          return value && 
                 String(value).trim() && 
                 String(value).toLowerCase() !== 'null' &&
                 String(value).toLowerCase() !== 'undefined' &&
                 !['confidence', 'processing_notes', 'error', 'processing_method', 'engine_used'].includes(key);
        });
        
        if (validFields.length === 0) {
          toast.warning(language === 'vi' 
            ? '⚠️ Không thể trích xuất thông tin từ PDF. Vui lòng nhập thủ công.'
            : '⚠️ Could not extract information from PDF. Please enter manually.'
          );
          return;
        }
        
        // Auto-fill ship data with extracted information
        const processedData = {
          // Basic Information
          name: analysisData.ship_name || '', 
          imo_number: analysisData.imo_number || '',
          ship_type: analysisData.ship_type || '',
          class_society: analysisData.class_society || '', 
          flag: analysisData.flag || '',
          gross_tonnage: analysisData.gross_tonnage ? String(analysisData.gross_tonnage) : '',
          deadweight: analysisData.deadweight ? String(analysisData.deadweight) : '',
          built_year: analysisData.built_year ? String(analysisData.built_year) : '',
          delivery_date: formatDateForInput(analysisData.delivery_date) || '',
          keel_laid: formatDateForInput(analysisData.keel_laid) || '',
          ship_owner: analysisData.ship_owner || '',
          
          // Docking Information
          last_docking: formatLastDockingForDisplay(analysisData.last_docking) || '',
          last_docking_2: formatLastDockingForDisplay(analysisData.last_docking_2) || '', 
          next_docking: formatDateForInput(analysisData.next_docking) || '',
          
          // Survey Information
          last_special_survey: formatDateForInput(analysisData.last_special_survey) || '',
          last_intermediate_survey: formatDateForInput(analysisData.last_intermediate_survey) || '',
          special_survey_from_date: formatDateForInput(analysisData.special_survey_from_date) || '',
          special_survey_to_date: formatDateForInput(analysisData.special_survey_to_date) || '',
          
          // Anniversary Date
          anniversary_date_day: analysisData.anniversary_date_day ? String(analysisData.anniversary_date_day) : '',
          anniversary_date_month: analysisData.anniversary_date_month ? String(analysisData.anniversary_date_month) : '',
        };

        // Count filled fields
        const filledFields = Object.keys(processedData).filter(key => 
          processedData[key] && processedData[key].trim()
        ).length;

        if (filledFields === 0) {
          toast.warning(language === 'vi' 
            ? '⚠️ PDF được phân tích nhưng không tìm thấy thông tin tàu phù hợp'
            : '⚠️ PDF analyzed but no suitable ship information found'
          );
          return;
        }
        
        // Update ship data
        setShipData(prev => ({
          ...prev,
          ...processedData
        }));
        
        // Show success message
        toast.success(language === 'vi' 
          ? `✅ Phân tích PDF thành công! Đã điền ${filledFields} trường thông tin tàu.`
          : `✅ PDF analysis completed! Auto-filled ${filledFields} ship information fields.`
        );
        
      } else {
        toast.error(language === 'vi' 
          ? '❌ Phân tích PDF thất bại'
          : '❌ PDF analysis failed'
        );
      }
    } catch (error) {
      console.error('PDF analysis error:', error);
      toast.error(language === 'vi' 
        ? `❌ Lỗi phân tích PDF: ${error.response?.data?.detail || error.message}`
        : `❌ PDF analysis error: ${error.response?.data?.detail || error.message}`
      );
    } finally {
      setIsPdfAnalyzing(false);
    }
  };

  // Helper function to format date for input (YYYY-MM-DD)
  const formatDateForInput = (dateStr) => {
    if (!dateStr || dateStr === 'null' || dateStr === 'N/A') return '';
    
    try {
      // Handle DD/MM/YYYY format
      if (typeof dateStr === 'string' && dateStr.includes('/')) {
        const parts = dateStr.split('/');
        if (parts.length === 3) {
          const [day, month, year] = parts;
          return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
        }
      }
      
      // Handle ISO format (YYYY-MM-DD)
      if (typeof dateStr === 'string' && dateStr.includes('-')) {
        return dateStr.split('T')[0]; // Remove time component if exists
      }
      
      return '';
    } catch (error) {
      console.error('Date format error:', error);
      return '';
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

  // Helper function to format last docking for display (MM/YYYY)
  const formatLastDockingForDisplay = (dockingStr) => {
    if (!dockingStr || dockingStr === 'null' || dockingStr === 'N/A') return '';
    
    try {
      // If already in MM/YYYY format, return as is
      if (typeof dockingStr === 'string' && dockingStr.match(/^\d{1,2}\/\d{4}$/)) {
        return dockingStr;
      }
      
      // If in YYYY-MM-DD format, convert to MM/YYYY
      if (typeof dockingStr === 'string' && dockingStr.includes('-')) {
        const parts = dockingStr.split('-');
        if (parts.length >= 2) {
          const [year, month] = parts;
          return `${month}/${year}`;
        }
      }
      
      return dockingStr;
    } catch (error) {
      console.error('Docking format error:', error);
      return dockingStr;
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
        // Convert to ISO datetime (first day of the month)
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
      
      // Otherwise return null for invalid format
      return null;
    } catch (error) {
      console.error('Last docking format error:', error);
      return null;
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate required fields (Ship Type is now optional)
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
        imo: shipData.imo_number.trim(), // Backend expects 'imo', not 'imo_number'
        ship_type: shipData.ship_type.trim() || null, // Optional field
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

      console.log('Creating ship with data:', apiData);
      
      const response = await shipService.create(apiData);
      
      console.log('Ship creation response:', response);
      
      if (response && response.data && response.data.id) {
        const shipId = response.data.id;
        const shipName = shipData.name;
        
        // Show success message for database creation
        toast.success(language === 'vi' 
          ? `✅ Tạo tàu ${shipName} thành công!`
          : `✅ Ship ${shipName} created successfully!`
        );
        
        // Wait a bit for user to see the success message before closing modal
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Close modal and reset form
        handleClose();
        
        // Notify parent component about ship creation (will navigate and refresh)
        if (onShipCreated) {
          onShipCreated(shipId, shipName);
        } else {
          // Fallback: navigate to certificates page
          navigate('/certificates');
        }
        
        // Start background monitoring IMMEDIATELY without waiting
        // Use setTimeout instead of await to avoid blocking
        setTimeout(() => {
          // Show info toast that folder creation is in progress
          toast.info(language === 'vi' 
            ? '📁 Đang tạo folder Google Drive...'
            : '📁 Creating Google Drive folder...'
          );
          
          // Poll Google Drive folder creation status in background (non-blocking)
          (async () => {
          try {
            // Wait a bit before first check (give backend time to start)
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            // Poll every 3 seconds for max 60 seconds (20 attempts)
            let attempts = 0;
            const maxAttempts = 20;
            
            while (attempts < maxAttempts) {
              try {
                const shipDetail = await shipService.getById(shipId);
                
                if (shipDetail && shipDetail.data) {
                  const status = shipDetail.data.gdrive_folder_status;
                  
                  if (status === 'completed') {
                    toast.success(language === 'vi' 
                      ? `✅ Folder Google Drive cho tàu ${shipName} đã được tạo thành công`
                      : `✅ Google Drive folder for ship ${shipName} created successfully`
                    );
                    break;
                  } else if (status === 'failed' || status === 'timeout' || status === 'error') {
                    const errorMsg = shipDetail.data.gdrive_folder_error || 'Unknown error';
                    toast.warning(language === 'vi' 
                      ? `⚠️ Không thể tạo folder Google Drive cho tàu ${shipName}: ${errorMsg}`
                      : `⚠️ Failed to create Google Drive folder for ship ${shipName}: ${errorMsg}`
                    );
                    break;
                  }
                  
                  // Status is still "pending" or not set yet, continue polling
                }
              } catch (pollError) {
                console.error('Error polling ship status:', pollError);
                // Continue polling even if one check fails
              }
              
              attempts++;
              await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds before next check
            }
            
            // If we've exhausted all attempts without success/failure
            if (attempts >= maxAttempts) {
              console.log('Google Drive folder creation status check timed out after 60 seconds');
              toast.info(language === 'vi' 
                ? `📁 Folder Google Drive cho tàu ${shipName} đang được tạo trong nền. Bạn có thể tiếp tục làm việc.`
                : `📁 Google Drive folder for ship ${shipName} is being created in background. You can continue working.`
              );
            }
          } catch (error) {
            console.error('Error monitoring Google Drive folder creation:', error);
            // Silently fail - don't show error to user as it's background operation
          }
        })();
        }, 1000); // Wait 1 second after navigation before showing Google Drive toast
        
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Failed to create ship:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);
      
      const errorMessage = error.response?.data?.detail || error.message;
      toast.error(language === 'vi' 
        ? `❌ Lỗi tạo tàu: ${errorMessage}`
        : `❌ Failed to create ship: ${errorMessage}`
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle close
  const handleClose = () => {
    if (isSubmitting || isPdfAnalyzing) {
      return; // Prevent closing during operations
    }
    
    // Reset form
    setShipData({
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
      last_docking: '',
      last_docking_2: '',
      next_docking: '',
      last_special_survey: '',
      last_intermediate_survey: '',
      special_survey_from_date: '',
      special_survey_to_date: '',
      anniversary_date_day: '',
      anniversary_date_month: '',
    });
    setPdfFile(null);
    setIsPdfAnalyzing(false);
    setUserCompanyName('');
    
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        {/* Modal Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between z-10">
          <h2 className="text-2xl font-bold text-gray-800">
            🚢 {language === 'vi' ? 'Thêm Tàu Mới' : 'Add New Ship'}
          </h2>
          <button
            onClick={handleClose}
            disabled={isSubmitting || isPdfAnalyzing}
            className="text-gray-500 hover:text-gray-700 text-2xl font-bold disabled:opacity-50"
          >
            ×
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="p-6">
          {/* AI Certificate Analysis Section */}
          <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <span>🤖</span>
              {language === 'vi' ? 'Thêm tàu từ Certificate với AI Analysis' : 'Add ship from Certificate with AI Analysis'}
            </h3>
            <p className="text-sm text-gray-600 mb-3">
              {language === 'vi' 
                ? 'Tải lên chứng chỉ tàu (PDF) để tự động điền thông tin bằng AI'
                : 'Upload ship certificate (PDF) to auto-fill information with AI'}
            </p>
            <div className="flex items-center gap-4">
              <label className="flex-1 cursor-pointer">
                <div className="flex items-center gap-3 px-4 py-3 bg-white border-2 border-blue-300 rounded-lg hover:bg-blue-50 hover:border-blue-400 transition-all">
                  <span className="text-2xl">📄</span>
                  <div className="flex-1">
                    <div className="font-medium text-blue-800">
                      {pdfFile ? pdfFile.name : (language === 'vi' ? 'Chọn file PDF' : 'Select PDF file')}
                    </div>
                    <div className="text-xs text-gray-500">
                      {language === 'vi' ? 'Tối đa 10MB' : 'Maximum 10MB'}
                    </div>
                  </div>
                </div>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handlePdfFileSelect}
                  disabled={isPdfAnalyzing || isSubmitting}
                  className="hidden"
                />
              </label>
              
              {isPdfAnalyzing && (
                <div className="flex items-center gap-2 text-blue-600">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                  <span className="text-sm font-medium">
                    {language === 'vi' ? 'Đang phân tích...' : 'Analyzing...'}
                  </span>
                </div>
              )}
            </div>
          </div>

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
              disabled={isSubmitting || isPdfAnalyzing}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={isSubmitting || isPdfAnalyzing}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSubmitting && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              )}
              {isSubmitting 
                ? (language === 'vi' ? 'Đang tạo...' : 'Creating...') 
                : (language === 'vi' ? 'Tạo Tàu' : 'Create Ship')
              }
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddShipModal;
