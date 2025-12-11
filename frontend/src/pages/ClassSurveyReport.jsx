/**
 * Class Survey Report Page
 * Full-featured with batch upload support
 */
import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { MainLayout, Sidebar, SubMenuBar } from '../components';
import { 
  ClassSurveyReportList, 
  BatchProcessingModal, 
  BatchResultsModal 
} from '../components/ClassSurveyReport';
import { ShipDetailPanel } from '../components/ShipDetailPanel';
import { EditShipModal, DeleteShipConfirmationModal, AddShipModal, ShipSelectionModal } from '../components/Ships';
import { shipService, surveyReportService } from '../services';
import api from '../services/api';
import { toast } from 'sonner';
import { shortenClassSociety } from '../utils/shipHelpers';
import { 
  estimateFileProcessingTime, 
  startSmoothProgressForFile 
} from '../utils/progressHelpers';

const ClassSurveyReport = () => {
  const { language, user } = useAuth();
  const location = useLocation();
  
  // State
  const [selectedCategory] = useState('ship_certificates');
  const [selectedSubMenu, setSelectedSubMenu] = useState('class_survey');
  const [showShipModal, setShowShipModal] = useState(false);
  const [showAddShipModal, setShowAddShipModal] = useState(false);
  const [showEditShipModal, setShowEditShipModal] = useState(false);
  const [showDeleteShipModal, setShowDeleteShipModal] = useState(false);
  const [ships, setShips] = useState([]);
  const [selectedShip, setSelectedShip] = useState(null);
  const [deleteShipData, setDeleteShipData] = useState(null);
  const [isDeletingShip, setIsDeletingShip] = useState(false);
  const [loading, setLoading] = useState(false);

  // Batch processing states
  const [isBatchProcessing, setIsBatchProcessing] = useState(false);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });
  const [fileProgressMap, setFileProgressMap] = useState({});
  const [fileStatusMap, setFileStatusMap] = useState({});
  const [fileSubStatusMap, setFileSubStatusMap] = useState({});
  const [fileObjectsMap, setFileObjectsMap] = useState({}); // Store file objects for retry
  const [batchResults, setBatchResults] = useState([]);
  const [showBatchResults, setShowBatchResults] = useState(false);
  const [isBatchModalMinimized, setIsBatchModalMinimized] = useState(false);
  const [listRefreshKey, setListRefreshKey] = useState(0); // Used to trigger list refresh

  // Fetch ships on mount and restore selected ship from localStorage
  useEffect(() => {
    fetchShips();
  }, []);

  // Restore selected ship after ships are loaded
  useEffect(() => {
    if (ships.length > 0 && !selectedShip) {
      const savedShipId = localStorage.getItem('selectedShipId');
      if (savedShipId) {
        const savedShip = ships.find(s => s.id === savedShipId);
        if (savedShip) {
          console.log('Restoring selected ship:', savedShip.name);
          setSelectedShip(savedShip);
        } else {
          // Ship not found, clear localStorage
          localStorage.removeItem('selectedShipId');
        }
      }
    }
  }, [ships]);

  // Handle navigation from Add Ship - refresh when new ship is created
  useEffect(() => {
    if (location.state?.refresh) {
      console.log('Refreshing ship list after new ship creation:', location.state);
      fetchShips();
      
      // Clear the location state to prevent re-triggering on subsequent renders
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const fetchShips = async () => {
    try {
      console.log('Fetching ships...');
      setLoading(true);
      const response = await shipService.getAllShips();
      console.log('Ships fetched successfully:', response);
      const data = response.data || response || [];
      
      // Ensure data is array
      if (!Array.isArray(data)) {
        console.error('Ships response is not an array:', data);
        setShips([]);
      } else {
        setShips(data);
      }
    } catch (error) {
      console.error('Failed to fetch ships:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách tàu' : 'Failed to load ships');
      setShips([]);
    } finally {
      console.log('Setting loading to false');
      setLoading(false);
    }
  };

  // Helper function to update selected ship and save to localStorage
  const updateSelectedShip = (ship) => {
    setSelectedShip(ship);
    if (ship) {
      localStorage.setItem('selectedShipId', ship.id);
      console.log('Saved ship to localStorage:', ship.name, ship.id);
    } else {
      localStorage.removeItem('selectedShipId');
      console.log('Removed ship from localStorage');
    }
  };


  // Note: handleAddRecord removed - Survey Report page manages its own Add modal
  // const handleAddRecord = () => {...};

  const handleShipCreated = async (shipId, shipName) => {
    console.log('Ship created callback triggered:', shipId, shipName);
    // Close modal
    setShowAddShipModal(false);
    // Refresh ship list to show new ship
    await fetchShips();
    console.log('Ship list refreshed after creation');
  };

  const handleEditShip = (ship) => {
    setShowEditShipModal(true);
  };

  const handleShipUpdated = (updatedShip) => {
    // Update ships list
    setShips(ships.map(s => s.id === updatedShip.id ? updatedShip : s));
    // Update selected ship
    updateSelectedShip(updatedShip);
    // Refresh ships list
    fetchShips();
    toast.success(language === 'vi' ? 'Cập nhật tàu thành công!' : 'Ship updated successfully!');
  };

  // Handle ship update after recalculation
  const handleShipUpdate = async (shipId) => {
    try {
      const response = await api.get(`/api/ships/${shipId}`);
      const updatedShip = response.data;
      
      // Update ships list
      setShips(ships.map(s => s.id === updatedShip.id ? updatedShip : s));
      // Update selected ship
      updateSelectedShip(updatedShip);
    } catch (error) {
      console.error('Error refreshing ship data:', error);
      toast.error(language === 'vi' ? 'Không thể làm mới dữ liệu tàu' : 'Failed to refresh ship data');
    }
  };

  const handleDeleteShipClick = (ship) => {
    setDeleteShipData(ship);
    setShowDeleteShipModal(true);
  };

  const handleDeleteShip = async (shipId, deleteOption) => {
    try {
      setIsDeletingShip(true);
      
      const deleteWithGDrive = deleteOption === 'with_gdrive';
      
      toast.info(language === 'vi' 
        ? `Đang xóa tàu ${deleteShipData?.name}...`
        : `Deleting ship ${deleteShipData?.name}...`
      );

      // Call backend API with delete_google_drive_folder parameter
      const response = await shipService.delete(shipId, deleteWithGDrive);

      // Handle response
      if (response && response.data) {
        const result = response.data;
        
        // Check Google Drive deletion status if it was requested
        if (deleteWithGDrive && result.google_drive_deletion) {
          const gdriveStatus = result.google_drive_deletion;
          
          if (gdriveStatus.success) {
            toast.success(language === 'vi' 
              ? '✅ Đã xóa tàu và folder Google Drive thành công'
              : '✅ Ship and Google Drive folder deleted successfully'
            );
          } else {
            // Show warning if GDrive deletion failed but ship was deleted
            toast.warning(language === 'vi' 
              ? `⚠️ Đã xóa tàu nhưng có lỗi khi xóa folder Google Drive: ${gdriveStatus.message || 'Unknown error'}`
              : `⚠️ Ship deleted but Google Drive folder deletion failed: ${gdriveStatus.message || 'Unknown error'}`
            );
          }
        } else {
          // Success message for database deletion only
          toast.success(language === 'vi' 
            ? `✅ Đã xóa tàu "${deleteShipData?.name}" thành công`
            : `✅ Ship "${deleteShipData?.name}" deleted successfully`
          );
        }
      } else {
        // Fallback success message
        toast.success(language === 'vi' 
          ? `✅ Đã xóa tàu "${deleteShipData?.name}" thành công`
          : `✅ Ship "${deleteShipData?.name}" deleted successfully`
        );
      }

      // Refresh ships list
      await fetchShips();

      // Close modals and reset states
      setShowDeleteShipModal(false);
      setShowEditShipModal(false);
      setDeleteShipData(null);
      
      // Clear selected ship if current ship was deleted
      if (selectedShip && selectedShip.id === shipId) {
        updateSelectedShip(null);
      }

    } catch (error) {
      console.error('Ship deletion error:', error);
      
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred';
      
      toast.error(language === 'vi' 
        ? `Không thể xóa tàu: ${errorMessage}`
        : `Failed to delete ship: ${errorMessage}`
      );
    } finally {
      setIsDeletingShip(false);
    }
  };

  // Handle submenu navigation
  const handleSubMenuChange = (submenuKey) => {
    setSelectedSubMenu(submenuKey);
    
    // Navigate to different pages based on submenu
    const routes = {
      'certificates': '/certificates',
      'test_report': '/test-report',
      'drawings': '/drawings-manuals',
      'other_docs': '/other-documents'
    };
    
    if (routes[submenuKey] && routes[submenuKey] !== '/class-survey-report') {
      window.location.href = routes[submenuKey];
    }
    // Stay on this page if class_survey is selected (already here)
  };

  // ==================== BATCH PROCESSING FUNCTIONS ====================
  
  /**
   * Start batch processing for multiple files
   */
  const startBatchProcessing = async (files) => {
    if (!selectedShip) {
      toast.error(language === 'vi' ? 'Vui lòng chọn tàu' : 'Please select a ship');
      return;
    }

    setIsBatchProcessing(true);
    setBatchProgress({ current: 0, total: files.length });
    setIsBatchModalMinimized(false);
    
    // Initialize progress maps
    const initialProgressMap = {};
    const initialStatusMap = {};
    const initialSubStatusMap = {};
    const initialFileObjectsMap = {};
    
    files.forEach(file => {
      initialProgressMap[file.name] = 0;
      initialStatusMap[file.name] = 'waiting';
      initialSubStatusMap[file.name] = null;
      initialFileObjectsMap[file.name] = file; // Store file object for retry
    });
    
    setFileProgressMap(initialProgressMap);
    setFileStatusMap(initialStatusMap);
    setFileSubStatusMap(initialSubStatusMap);
    setFileObjectsMap(initialFileObjectsMap);
    setBatchResults([]);
    
    const STAGGER_DELAY = 5000; // 5 seconds between file starts
    const results = [];
    
    // Process files with staggered start
    const promises = files.map((file, index) => {
      return new Promise((resolve) => {
        setTimeout(async () => {
          const result = await processSingleFile(file);
          results.push(result);
          setBatchProgress({ current: results.length, total: files.length });
          resolve(result);
        }, index * STAGGER_DELAY);
      });
    });
    
    // Wait for all files to complete
    await Promise.all(promises);
    
    // Show results
    setIsBatchProcessing(false);
    setBatchResults(results);
    setShowBatchResults(true);
    
    // Refresh ClassSurveyReportList component (will trigger via key change)
    // The component will re-fetch when selectedShip changes
    
    // Summary toast
    const successCount = results.filter(r => r.success).length;
    const failCount = results.length - successCount;
    toast.success(
      language === 'vi'
        ? `✅ Đã xử lý ${results.length} files: ${successCount} thành công, ${failCount} thất bại`
        : `✅ Processed ${results.length} files: ${successCount} success, ${failCount} failed`
    );
  };

  /**
   * Process a single file in batch mode
   */
  const processSingleFile = async (file) => {
    const result = {
      filename: file.name,
      success: false,
      surveyReportCreated: false,
      fileUploaded: false,
      surveyReportName: '',
      surveyReportNo: '',
      error: null
    };
    
    // Update status to 'processing'
    setFileStatusMap(prev => ({ ...prev, [file.name]: 'processing' }));
    setFileProgressMap(prev => ({ ...prev, [file.name]: 0 }));
    
    // Start smooth progress animation
    const estimatedTime = estimateFileProcessingTime(file);
    const progressController = startSmoothProgressForFile(
      file.name,
      setFileProgressMap,
      setFileSubStatusMap,
      estimatedTime,
      90 // Max 90%, then jump to 100% on complete
    );
    
    try {
      // Step 1: AI Analysis with validation check (NO auto-retry)
      let analyzeResponse;
      let data;
      
      try {
        analyzeResponse = await surveyReportService.analyzeFile(
          selectedShip.id,
          file,
          false // Check validation in batch mode
        );
        data = analyzeResponse.data || analyzeResponse;
      } catch (apiError) {
        // API call failed - check if it's validation error in response
        console.error(`API call failed for ${file.name}:`, apiError);
        
        // Check if error response contains validation error
        if (apiError.response?.data?.validation_error) {
          const errorData = apiError.response.data;
          const extractedInfo = `${errorData.extracted_ship_name || 'N/A'} (IMO: ${errorData.extracted_ship_imo || 'N/A'})`;
          const expectedInfo = `${errorData.expected_ship_name || 'N/A'} (IMO: ${errorData.expected_ship_imo || 'N/A'})`;
          
          const errorMsg = language === 'vi' 
            ? `Thông tin tàu không khớp!\nPDF có: ${extractedInfo}\nĐã chọn: ${expectedInfo}`
            : `Ship information mismatch!\nPDF has: ${extractedInfo}\nSelected: ${expectedInfo}`;
          
          throw new Error(errorMsg);
        }
        
        // Otherwise rethrow original error
        throw apiError;
      }
      
      // If validation error detected in successful response, STOP processing
      if (data.validation_error) {
        console.log(`❌ Ship validation failed for ${file.name}:`, {
          extracted: `${data.extracted_ship_name} (IMO: ${data.extracted_ship_imo})`,
          expected: `${data.expected_ship_name} (IMO: ${data.expected_ship_imo})`
        });
        
        // Build detailed error message
        const extractedInfo = `${data.extracted_ship_name || 'N/A'} (IMO: ${data.extracted_ship_imo || 'N/A'})`;
        const expectedInfo = `${data.expected_ship_name} (IMO: ${data.expected_ship_imo || 'N/A'})`;
        
        const errorMsg = language === 'vi' 
          ? `Thông tin tàu không khớp!\nPDF có: ${extractedInfo}\nĐã chọn: ${expectedInfo}`
          : `Ship information mismatch!\nPDF has: ${extractedInfo}\nSelected: ${expectedInfo}`;
        
        // Throw error to stop processing
        throw new Error(errorMsg);
      }
      
      if (!data.success || !data.analysis) {
        throw new Error(data.message || 'AI analysis failed');
      }
      
      const analysis = data.analysis;
      result.surveyReportName = analysis.survey_report_name || file.name;
      result.surveyReportNo = analysis.survey_report_no || '';
      
      // Step 2: Create Record
      const reportData = {
        ship_id: selectedShip.id,
        survey_report_name: analysis.survey_report_name || file.name,
        report_form: analysis.report_form || null,
        survey_report_no: analysis.survey_report_no || null,
        issued_date: analysis.issued_date || null,
        issued_by: analysis.issued_by || null,
        status: analysis.status || 'Valid',
        note: analysis.note || null,
        surveyor_name: analysis.surveyor_name || null
      };
      
      const createResponse = await surveyReportService.create(reportData);
      const createdReport = createResponse.data || createResponse;
      result.surveyReportCreated = true;
      
      // Step 3: Upload Files (SYNCHRONOUS in batch mode)
      if (analysis._file_content && analysis._filename) {
        await surveyReportService.uploadFiles(
          createdReport.id,
          analysis._file_content,
          analysis._filename,
          analysis._content_type || 'application/pdf',
          analysis._summary_text || ''
        );
        result.fileUploaded = true;
      }
      
      // Success!
      result.success = true;
      progressController.complete(); // Jump to 100%
      setFileStatusMap(prev => ({ ...prev, [file.name]: 'completed' }));
      
    } catch (error) {
      console.error(`Failed to process ${file.name}:`, error);
      result.error = error.response?.data?.detail || error.message || 'Processing failed';
      result.success = false;
      progressController.stop();
      setFileStatusMap(prev => ({ ...prev, [file.name]: 'error' }));
    }
    
    // Brief pause before returning
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return result;
  };

  /**
   * Retry failed file from BatchResultsModal
   */
  const handleRetryFailedFile = async (failedFileName) => {
    // Get the original file object from map
    const originalFile = fileObjectsMap[failedFileName];
    
    if (!originalFile) {
      toast.error(
        language === 'vi'
          ? '❌ Không tìm thấy file gốc. Vui lòng upload lại từ đầu.'
          : '❌ Original file not found. Please upload again from scratch.'
      );
      return;
    }
    
    // Show ProcessingModal in minimized mode for this retry
    setIsBatchProcessing(true);
    setIsBatchModalMinimized(true);
    
    // Reset status for retry
    setFileStatusMap(prev => ({ ...prev, [failedFileName]: 'pending' }));
    setFileProgressMap(prev => ({ ...prev, [failedFileName]: 0 }));
    setFileSubStatusMap(prev => ({ 
      ...prev, 
      [failedFileName]: language === 'vi' ? '🔄 Đang thử lại...' : '🔄 Retrying...' 
    }));
    
    // Update batch progress to show we're processing 1 file
    setBatchProgress({ current: 0, total: 1 });
    
    // Show retry message
    toast.info(
      language === 'vi' 
        ? `🔄 Đang xử lý lại file: ${failedFileName}` 
        : `🔄 Retrying file: ${failedFileName}`
    );
    
    try {
      // Re-process the SAME file
      const result = await processSingleFile(originalFile);
      
      if (result.success) {
        toast.success(
          language === 'vi' 
            ? `✅ File đã được xử lý thành công!` 
            : `✅ File processed successfully!`
        );
        
        // Update progress to show completion
        setBatchProgress({ current: 1, total: 1 });
        
        // Update the result in BatchResultsModal
        setBatchResults(prev => 
          prev.map(r => r.filename === failedFileName ? result : r)
        );
        
        // Refresh list
        setListRefreshKey(prev => prev + 1);
        
        // Close ProcessingModal after a short delay
        setTimeout(() => {
          setIsBatchProcessing(false);
        }, 1500);
      } else {
        toast.error(
          language === 'vi' 
            ? `❌ File vẫn bị lỗi: ${result.error}` 
            : `❌ File still failed: ${result.error}`
        );
        
        // Update the result in BatchResultsModal with new error
        setBatchResults(prev => 
          prev.map(r => r.filename === failedFileName ? result : r)
        );
        
        // Close ProcessingModal after a short delay
        setTimeout(() => {
          setIsBatchProcessing(false);
        }, 1500);
      }
    } catch (error) {
      console.error('Retry error:', error);
      toast.error(
        language === 'vi' 
          ? `❌ Lỗi khi xử lý lại file` 
          : `❌ Error retrying file`
      );
      
      // Mark as failed in status map
      setFileStatusMap(prev => ({ ...prev, [failedFileName]: 'failed' }));
      setFileSubStatusMap(prev => ({ 
        ...prev, 
        [failedFileName]: error.message || 'Unknown error' 
      }));
      
      // Close ProcessingModal after a short delay
      setTimeout(() => {
        setIsBatchProcessing(false);
      }, 1500);
    }
  };

  // ==================== END BATCH PROCESSING ====================

  return (
    <MainLayout
      sidebar={
        <Sidebar 
          selectedCategory={selectedCategory}
          onCategoryChange={(cat) => {
            // Navigate to different pages based on category
            const routes = {
              'ship_certificates': '/certificates',
              'crew': '/crew',
              'ism': '/ism-isps-mlc',
              'isps': '/isps',
              'mlc': '/mlc',
              'supplies': '/supplies'
            };
            if (routes[cat]) {
              window.location.href = routes[cat];
            }
          }}
          // No onAddRecord - this page doesn't add ships
        />
      }
    >
      {/* Page Title with Ship Select Button */}
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-800">
          {language === 'vi' ? 'CLASS SURVEY REPORT' : 'CLASS SURVEY REPORT'}
        </h1>
        
        {!selectedShip && (
          <div className="flex items-center gap-4">
            <p className="text-gray-600">
              {language === 'vi' ? 'Vui lòng chọn tàu để xem thông tin' : 'Please select a ship to view information'}
            </p>
            <button
              onClick={() => setShowShipModal(true)}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-all flex items-center gap-2 whitespace-nowrap"
            >
              <span>🚢</span>
              {language === 'vi' ? 'Chọn tàu' : 'Ship Select'}
            </button>
          </div>
        )}
      </div>

      {/* Ship Detail Panel */}
      {selectedShip && (
        <ShipDetailPanel
          ship={selectedShip}
          onClose={() => updateSelectedShip(null)}
          onEditShip={handleEditShip}
          showShipParticular={true}
          onShipSelect={() => setShowShipModal(true)}
          onShipUpdate={handleShipUpdate}
        />
      )}

      {/* Ship Selection Modal */}
      <ShipSelectionModal
        isOpen={showShipModal}
        onClose={() => setShowShipModal(false)}
        onSelectShip={updateSelectedShip}
        ships={ships}
        loading={loading}
        language={language}
        currentShipId={selectedShip?.id}
      />

      {/* SubMenu Bar */}
      <SubMenuBar 
        selectedCategory={selectedCategory}
        selectedSubMenu={selectedSubMenu}
        onSubMenuChange={handleSubMenuChange}
      />
      
      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-md p-6">
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
          </div>
        ) : !selectedShip ? (
          /* Ship Cards Grid - Show all ships for selection */
          <div>
            <h3 className="text-xl font-semibold mb-6 text-gray-800">
              {language === 'vi' ? 'Chọn tàu để xem Class Survey Report' : 'Select a ship to view Class Survey Report'}
            </h3>
            
            {ships.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-6xl mb-4">🚢</div>
                <p className="text-lg">{language === 'vi' ? 'Không có tàu nào' : 'No ships available'}</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                {ships.map(ship => (
                  <div
                    key={ship.id}
                    onClick={() => updateSelectedShip(ship)}
                    className="border-2 border-gray-200 rounded-lg p-4 hover:border-purple-500 hover:shadow-lg transition-all cursor-pointer bg-gradient-to-br from-white to-gray-50"
                  >
                    {/* Ship Icon */}
                    <div className="text-center mb-3">
                      <div className="text-3xl">🚢</div>
                    </div>
                    
                    {/* Ship Name */}
                    <h4 className="text-base font-bold text-gray-800 text-center mb-3 line-clamp-2 min-h-[3rem]">
                      {ship.name}
                    </h4>
                    
                    {/* Ship Details */}
                    <div className="space-y-1.5 text-sm">
                      {ship.imo && (
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600 text-xs">IMO:</span>
                          <span className="font-semibold text-gray-800 text-xs">{ship.imo}</span>
                        </div>
                      )}
                      {ship.flag && (
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600 text-xs">{language === 'vi' ? 'Cờ:' : 'Flag:'}</span>
                          <span className="font-semibold text-gray-800 text-xs truncate ml-1">{ship.flag}</span>
                        </div>
                      )}
                      {ship.class_society && (
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600 text-xs">{language === 'vi' ? 'Đăng kiểm:' : 'Class Society:'}</span>
                          <span className="font-semibold text-gray-800 text-xs truncate ml-1">{shortenClassSociety(ship.class_society)}</span>
                        </div>
                      )}
                      {ship.built_year && (
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600 text-xs">{language === 'vi' ? 'Năm:' : 'Year:'}</span>
                          <span className="font-semibold text-gray-800 text-xs">{ship.built_year}</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Select Button */}
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <button
                        className="w-full py-1.5 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded font-medium transition-all"
                        onClick={(e) => {
                          e.stopPropagation();
                          updateSelectedShip(ship);
                        }}
                      >
                        {language === 'vi' ? 'Chọn' : 'Select'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          /* Class Survey Report List Section */
          <ClassSurveyReportList 
            key={listRefreshKey} // Force re-mount and refresh when key changes
            selectedShip={selectedShip} 
            onStartBatchProcessing={startBatchProcessing}
          />
        )}
      </div>

      {/* Add Ship Modal */}
      <AddShipModal 
        isOpen={showAddShipModal}
        onClose={() => {
          console.log('Closing Add Ship modal');
          setShowAddShipModal(false);
        }}
        onShipCreated={handleShipCreated}
      />

      {/* Edit Ship Modal */}
      {showEditShipModal && selectedShip && (
        <EditShipModal
          isOpen={showEditShipModal}
          onClose={() => setShowEditShipModal(false)}
          ship={selectedShip}
          onShipUpdated={handleShipUpdated}
          onDeleteShip={handleDeleteShipClick}
        />
      )}

      {/* Delete Ship Confirmation Modal */}
      {showDeleteShipModal && deleteShipData && (
        <DeleteShipConfirmationModal
          isOpen={showDeleteShipModal}
          onClose={() => {
            setShowDeleteShipModal(false);
            setDeleteShipData(null);
          }}
          ship={deleteShipData}
          onConfirm={handleDeleteShip}
          isDeleting={isDeletingShip}
        />
      )}

      {/* Batch Processing Modal */}
      <BatchProcessingModal
        isOpen={isBatchProcessing}
        isMinimized={isBatchModalMinimized}
        onMinimize={() => setIsBatchModalMinimized(true)}
        onRestore={() => setIsBatchModalMinimized(false)}
        progress={batchProgress}
        fileProgressMap={fileProgressMap}
        fileStatusMap={fileStatusMap}
        fileSubStatusMap={fileSubStatusMap}
        onRetryFile={handleRetryFailedFile}
        language={language}
        title={language === 'vi' ? 'Đang xử lý Survey Reports' : 'Processing Survey Reports'}
      />

      {/* Batch Results Modal */}
      <BatchResultsModal
        isOpen={showBatchResults}
        onClose={() => {
          setShowBatchResults(false);
          setBatchResults([]);
          // Auto-refresh list after closing batch results modal
          setListRefreshKey(prev => prev + 1);
        }}
        results={batchResults}
        onRetryFile={handleRetryFailedFile}
        language={language}
      />
    </MainLayout>
  );
};

export default ClassSurveyReport;
