import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { formatDateDisplay } from '../../utils/dateHelpers';
import { crewService } from '../../services/crewService';
import { autoFillEnglishField } from '../../utils/vietnameseHelpers';
import { estimateFileProcessingTime, startSmoothProgressForFile } from '../../utils/progressHelpers';
import { RANK_OPTIONS } from '../../utils/constants';
import { 
  AddCrewModal, 
  EditCrewModal, 
  DeleteCrewConfirmModal, 
  BatchProcessingModal, 
  BatchResultsModal,
  BulkEditPlaceSignOnModal,
  BulkEditShipSignOnModal,
  BulkEditDateSignOnModal,
  BulkEditDateSignOffModal,
  CrewAssignmentHistoryModal
} from './index';

export const CrewListTable = ({ 
  selectedShip,
  ships = [],
  onRefresh,
  onShipFilterChange,
  onShipSelect  // New prop to handle ship selection from modal
}) => {
  const { language, user } = useAuth();
  const navigate = useNavigate();
  
  // State
  const [crewList, setCrewList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCrewMembers, setSelectedCrewMembers] = useState(new Set());
  
  // Modal states
  const [showAddCrewModal, setShowAddCrewModal] = useState(false);
  const [showEditCrewModal, setShowEditCrewModal] = useState(false);
  const [showDeleteCrewModal, setShowDeleteCrewModal] = useState(false);
  const [selectedCrewForEdit, setSelectedCrewForEdit] = useState(null);
  const [crewToDelete, setCrewToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Batch processing states
  const [isBatchProcessing, setIsBatchProcessing] = useState(false);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0, success: 0, failed: 0 });
  const [currentProcessingFile, setCurrentProcessingFile] = useState('');
  const [batchResults, setBatchResults] = useState([]);
  const [showBatchProcessingModal, setShowBatchProcessingModal] = useState(false);
  const [showBatchResultsModal, setShowBatchResultsModal] = useState(false);
  
  // New states for enhanced batch processing (matching Test Report style)
  const [fileProgressMap, setFileProgressMap] = useState({});
  const [fileStatusMap, setFileStatusMap] = useState({});
  const [fileSubStatusMap, setFileSubStatusMap] = useState({});
  const [fileObjectsMap, setFileObjectsMap] = useState({}); // Store file objects for retry
  const [isBatchModalMinimized, setIsBatchModalMinimized] = useState(false);
  
  // Filter states
  const [filters, setFilters] = useState({
    ship_sign_on: 'All',
    status: 'All',
    search: ''
  });
  
  // Sort state
  const [sortConfig, setSortConfig] = useState({
    column: null,
    direction: 'asc'
  });
  
  // Context menu states
  const [crewContextMenu, setCrewContextMenu] = useState({ show: false, x: 0, y: 0, crew: null });
  const [passportContextMenu, setPassportContextMenu] = useState({ show: false, x: 0, y: 0, crew: null });
  const [rankContextMenu, setRankContextMenu] = useState({ show: false, x: 0, y: 0, crew: null });
  
  // Bulk edit modal states
  const [showBulkEditPlaceSignOn, setShowBulkEditPlaceSignOn] = useState(false);
  const [showBulkEditShipSignOn, setShowBulkEditShipSignOn] = useState(false);
  const [showBulkEditDateSignOn, setShowBulkEditDateSignOn] = useState(false);
  const [showBulkEditDateSignOff, setShowBulkEditDateSignOff] = useState(false);
  const [bulkPlaceSignOn, setBulkPlaceSignOn] = useState('');
  const [bulkShipSignOn, setBulkShipSignOn] = useState('');
  const [bulkDateSignOn, setBulkDateSignOn] = useState('');
  const [bulkDateSignOff, setBulkDateSignOff] = useState('');
  
  // Ship Sign On modal additional fields
  const [bulkShipSignOnPlace, setBulkShipSignOnPlace] = useState('');
  const [bulkShipSignOnDate, setBulkShipSignOnDate] = useState('');
  
  // Assignment history modal state
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [selectedCrewForHistory, setSelectedCrewForHistory] = useState(null);

  // Fetch crew list whenever filters change
  useEffect(() => {
    fetchCrewList();
  }, [filters.ship_sign_on, filters.status]);

  const fetchCrewList = async () => {
    setLoading(true);
    try {
      // Handle special "Standby" filter
      let queryParams = {};
      
      if (filters.ship_sign_on === 'Standby') {
        // Show only standby crew regardless of ship
        queryParams.status = 'Standby';
      } else {
        // Normal filtering
        if (filters.ship_sign_on !== 'All' && filters.ship_sign_on !== '-') {
          queryParams.ship_name = filters.ship_sign_on;
        }
        if (filters.status !== 'All') {
          queryParams.status = filters.status;
        }
      }
      
      const response = await crewService.getCrewList(queryParams);
      
      setCrewList(response.data || []);
      
    } catch (error) {
      console.error('Error fetching crew list:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách thuyền viên' : 'Failed to load crew list');
      setCrewList([]);
    } finally {
      setLoading(false);
    }
  };

  // Sync filter with selectedShip
  useEffect(() => {
    if (selectedShip) {
      // When ship is selected, update filter to match
      if (filters.ship_sign_on !== selectedShip.name) {
        setFilters(prev => ({ ...prev, ship_sign_on: selectedShip.name }));
      }
    } else {
      // When no ship selected, set filter to All (unless manually set to Standby or -)
      if (filters.ship_sign_on !== 'All' && filters.ship_sign_on !== 'Standby' && filters.ship_sign_on !== '-') {
        setFilters(prev => ({ ...prev, ship_sign_on: 'All' }));
      }
    }
  }, [selectedShip]);

  // Get filtered and sorted crew data
  const getFilteredCrewData = () => {
    let filtered = [...crewList];
    
    // Apply ship sign on filter
    if (filters.ship_sign_on && filters.ship_sign_on !== 'All') {
      if (filters.ship_sign_on === 'Standby') {
        // Show crew with ship_sign_on = "-" or status = "Standby"
        filtered = filtered.filter(crew => 
          crew.ship_sign_on === '-' || crew.status === 'Standby'
        );
      } else {
        filtered = filtered.filter(crew => crew.ship_sign_on === filters.ship_sign_on);
      }
    }
    
    // Apply status filter
    if (filters.status && filters.status !== 'All') {
      filtered = filtered.filter(crew => crew.status === filters.status);
    }
    
    // Apply search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(crew => 
        (crew.full_name && crew.full_name.toLowerCase().includes(searchLower)) ||
        (crew.full_name_en && crew.full_name_en.toLowerCase().includes(searchLower)) ||
        (crew.passport && crew.passport.toLowerCase().includes(searchLower))
      );
    }
    
    return filtered;
  };

  const getSortedCrewData = () => {
    const filtered = getFilteredCrewData();
    
    if (!sortConfig.column) return filtered;
    
    return [...filtered].sort((a, b) => {
      const aVal = a[sortConfig.column];
      const bVal = b[sortConfig.column];
      
      // Handle null/undefined
      if (!aVal && !bVal) return 0;
      if (!aVal) return 1;
      if (!bVal) return -1;
      
      // Date comparison
      if (['date_of_birth', 'date_sign_on', 'date_sign_off'].includes(sortConfig.column)) {
        const aDate = new Date(aVal);
        const bDate = new Date(bVal);
        return sortConfig.direction === 'asc' ? aDate - bDate : bDate - aDate;
      }
      
      // String comparison
      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      
      if (aStr < bStr) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aStr > bStr) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  };

  // Handle sort
  const handleSort = (column) => {
    setSortConfig(prev => ({
      column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  // Get sort icon
  const getSortIcon = (column) => {
    if (sortConfig.column !== column) {
      return null;  // Don't show any icon for unsorted columns
    }
    return (
      <span className="ml-2 text-blue-600">
        {sortConfig.direction === 'asc' ? '▲' : '▼'}
      </span>
    );
  };

  // Handle crew selection
  const handleSelectCrew = (crewId) => {
    setSelectedCrewMembers(prev => {
      const newSet = new Set(prev);
      if (newSet.has(crewId)) {
        newSet.delete(crewId);
      } else {
        newSet.add(crewId);
      }
      return newSet;
    });
  };

  // Handle select all
  const handleSelectAllCrew = (checked) => {
    if (checked) {
      const allIds = getSortedCrewData().map(crew => crew.id);
      setSelectedCrewMembers(new Set(allIds));
    } else {
      setSelectedCrewMembers(new Set());
    }
  };

  // Close context menus on click outside
  useEffect(() => {
    const handleClick = () => {
      setCrewContextMenu({ show: false, x: 0, y: 0, crew: null });
      setPassportContextMenu({ show: false, x: 0, y: 0, crew: null });
      setRankContextMenu({ show: false, x: 0, y: 0, crew: null });
    };
    
    if (crewContextMenu.show || passportContextMenu.show || rankContextMenu.show) {
      document.addEventListener('click', handleClick);
      return () => document.removeEventListener('click', handleClick);
    }
  }, [crewContextMenu.show, passportContextMenu.show, rankContextMenu.show]);
  
  // Row context menu handler
  const handleCrewRightClick = (e, crew) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Check user role
    if (!user || !['company_officer', 'manager', 'admin', 'super_admin'].includes(user.role)) {
      return;
    }
    
    // Auto-select crew if not already selected
    if (!selectedCrewMembers.has(crew.id)) {
      setSelectedCrewMembers(new Set([crew.id]));
    }
    
    // Calculate menu position (with boundary checking)
    const menuWidth = 280;
    // Estimate menu height based on number of items
    // Single selection: Edit + 4 bulk options + Delete = ~6 items * 40px + padding = ~280px
    // Multi selection: 4 bulk options + Delete = ~5 items * 40px + header + padding = ~260px
    const estimatedMenuHeight = selectedCrewMembers.size === 1 ? 320 : 280;
    let x = e.clientX;
    let y = e.clientY;
    
    // Adjust if menu would go off-screen (right side)
    if (x + menuWidth > window.innerWidth) {
      x = window.innerWidth - menuWidth - 10;
    }
    
    // Adjust if menu would go off-screen (bottom)
    if (y + estimatedMenuHeight > window.innerHeight) {
      // Try to position above cursor instead
      y = Math.max(10, y - estimatedMenuHeight);
      // If still doesn't fit, position at top with some padding
      if (y < 10) {
        y = 10;
      }
    }
    
    setCrewContextMenu({
      show: true,
      x,
      y,
      crew
    });
  };
  
  // Handle crew double click (navigate to certificates)
  const handleCrewDoubleClick = (crew) => {
    // Navigate to crew certificates page with crew name filter
    navigate('/crew-certificates', { 
      state: { 
        filterCrewName: crew.full_name,
        selectedShipId: selectedShip?.id || null,
        selectedShipName: selectedShip?.name || null
      } 
    });
  };
  
  // Handle edit crew
  const handleEditCrew = () => {
    if (crewContextMenu.crew) {
      setSelectedCrewForEdit(crewContextMenu.crew);
      setShowEditCrewModal(true);
      setCrewContextMenu({ show: false, x: 0, y: 0, crew: null });
    }
  };
  
  // Handle view assignment history
  const handleViewHistory = () => {
    if (crewContextMenu.crew) {
      setSelectedCrewForHistory(crewContextMenu.crew);
      setShowHistoryModal(true);
      setCrewContextMenu({ show: false, x: 0, y: 0, crew: null });
    }
  };
  
  // Handle delete crew
  const handleDeleteCrew = () => {
    if (selectedCrewMembers.size > 0) {
      const crewIds = Array.from(selectedCrewMembers);
      
      // If multiple crew selected, prepare bulk delete
      if (crewIds.length > 1) {
        setCrewToDelete({
          id: 'bulk',
          full_name: `${crewIds.length} ${language === 'vi' ? 'thuyền viên' : 'crew members'}`,
          isBulk: true,
          crewIds: crewIds
        });
      } else {
        // Single crew delete
        const crew = sortedCrewData.find(c => c.id === crewIds[0]);
        setCrewToDelete(crew);
      }
      
      setShowDeleteCrewModal(true);
      setCrewContextMenu({ show: false, x: 0, y: 0, crew: null });
    }
  };
  
  // Confirm delete
  const confirmDeleteCrew = async () => {
    if (!crewToDelete) return;
    
    try {
      setIsDeleting(true);
      
      // Check if bulk delete
      if (crewToDelete.isBulk) {
        // Bulk delete multiple crew
        const result = await crewService.bulkDelete(crewToDelete.crewIds);
        
        if (result.data.success) {
          const { deleted_count, files_deleted, errors } = result.data;
          
          toast.success(language === 'vi' 
            ? `Đã xóa ${deleted_count} thuyền viên${files_deleted > 0 ? ` và ${files_deleted} files` : ''}`
            : `Deleted ${deleted_count} crew member(s)${files_deleted > 0 ? ` and ${files_deleted} file(s)` : ''}`);
          
          if (errors && errors.length > 0) {
            toast.warning(language === 'vi' 
              ? `${errors.length} lỗi xảy ra: ${errors[0]}`
              : `${errors.length} error(s): ${errors[0]}`);
          }
        }
      } else {
        // Single crew delete with background flag for Drive deletion
        await crewService.delete(crewToDelete.id);
        
        toast.success(language === 'vi' 
          ? `Đã xóa thuyền viên ${crewToDelete.full_name}`
          : `Deleted crew member ${crewToDelete.full_name}`);
        
        // Show info about background Drive deletion
        if (crewToDelete.passport_file_id || crewToDelete.summary_file_id) {
          toast.info(language === 'vi' 
            ? '🗂️ Đang xóa files trên Drive...'
            : '🗂️ Deleting files on Drive...');
        }
      }
      
      // Refresh list
      fetchCrewList();
      
      // Clear selection
      setSelectedCrewMembers(new Set());
      
      // Close modal
      setShowDeleteCrewModal(false);
      setCrewToDelete(null);
      
    } catch (error) {
      console.error('Error deleting crew:', error);
      const errorMsg = error.response?.data?.detail || error.message;
      
      if (errorMsg.includes('certificates')) {
        toast.error(language === 'vi' 
          ? `Không thể xóa: ${crewToDelete.full_name} còn chứng chỉ. Vui lòng xóa chứng chỉ trước.`
          : `Cannot delete: ${crewToDelete.full_name} has certificates. Please delete certificates first.`);
      } else {
        toast.error(language === 'vi' 
          ? `Lỗi xóa thuyền viên: ${errorMsg}`
          : `Error deleting crew: ${errorMsg}`);
      }
    } finally {
      setIsDeleting(false);
    }
  };
  
  // Bulk edit handlers
  const handleBulkEditPlaceSignOn = () => {
    setBulkPlaceSignOn('');
    setShowBulkEditPlaceSignOn(true);
    setCrewContextMenu({ show: false, x: 0, y: 0, crew: null });
  };
  
  const handleBulkEditShipSignOn = () => {
    setBulkShipSignOn('');
    setShowBulkEditShipSignOn(true);
    setCrewContextMenu({ show: false, x: 0, y: 0, crew: null });
  };
  
  const handleBulkEditDateSignOn = () => {
    setBulkDateSignOn('');
    setShowBulkEditDateSignOn(true);
    setCrewContextMenu({ show: false, x: 0, y: 0, crew: null });
  };
  
  const handleBulkEditDateSignOff = () => {
    setBulkDateSignOff('');
    setShowBulkEditDateSignOff(true);
    setCrewContextMenu({ show: false, x: 0, y: 0, crew: null });
  };
  
  // Bulk update handlers
  const handleBulkUpdatePlaceSignOn = async () => {
    const crewIds = Array.from(selectedCrewMembers);
    const value = bulkPlaceSignOn.trim() === '' ? null : bulkPlaceSignOn.trim();
    await bulkUpdateField('place_sign_on', value, crewIds);
    setShowBulkEditPlaceSignOn(false);
  };
  
  const handleBulkUpdateShipSignOn = async () => {
    const crewIds = Array.from(selectedCrewMembers);
    if (!bulkShipSignOn) return;
    
    // Check if user selected "-" for Sign Off
    const isSignOff = bulkShipSignOn.trim() === '-';
    
    // Close modal immediately
    setShowBulkEditShipSignOn(false);
    
    // Show processing toast
    const processingToast = toast.loading(
      language === 'vi' 
        ? '🔄 Đang cập nhật...' 
        : '🔄 Processing...'
    );
    
    // Refresh table immediately (optimistic update)
    fetchCrewList();
    
    try {
      let successCount = 0;
      let failCount = 0;
      
      if (isSignOff) {
        // Sign Off flow: Update DB immediately, file movement in background
        for (const crewId of crewIds) {
          const crew = crewList.find(c => c.id === crewId);
          if (!crew) continue;
          
          const currentStatus = crew.status;
          
          try {
            // Update DB immediately
            await crewService.update(crewId, {
              ship_sign_on: '-',
              status: 'Standby',
              date_sign_off: crew.date_sign_off || new Date().toISOString().split('T')[0]
            });
            
            // File movement in background (only if was Sign on)
            if (currentStatus === 'Sign on') {
              crewService.signOff(crewId, {
                sign_off_date: crew.date_sign_off || new Date().toISOString().split('T')[0],
                notes: `Bulk sign off via Ship Sign On edit (selected "-")`
              }).catch(error => console.error(`Background signOff error for ${crewId}:`, error));
            }
            
            successCount++;
            
          } catch (error) {
            console.error(`Failed to sign off crew ${crewId}:`, error);
            failCount++;
          }
        }
        
      } else {
        // Normal Ship Sign On flow
        // Process each crew member
        for (const crewId of crewIds) {
          const crew = crewList.find(c => c.id === crewId);
          if (!crew) continue;
          
          const currentStatus = crew.status;
          const currentShip = crew.ship_sign_on;
          
          try {
            // Normalize ship names for comparison (trim and lowercase)
            const normalizedCurrentShip = (currentShip || '').trim().toLowerCase();
            const normalizedBulkShip = (bulkShipSignOn || '').trim().toLowerCase();
            
            // Determine action based on current status
            if (currentStatus === 'Standby') {
              // Sign On flow: Standby → Ship
              // Update DB immediately
              await crewService.update(crewId, {
                ship_sign_on: bulkShipSignOn,
                status: 'Sign on',
                date_sign_on: crew.date_sign_on || new Date().toISOString().split('T')[0],
                place_sign_on: crew.place_sign_on || null,
                date_sign_off: null
              });
              
              // File movement in background
              crewService.signOn(crewId, {
                ship_name: bulkShipSignOn,
                sign_on_date: crew.date_sign_on || new Date().toISOString().split('T')[0],
                place_sign_on: crew.place_sign_on || null,
                notes: `Bulk sign on via Ship Sign On edit to ${bulkShipSignOn}`
              }).catch(error => console.error(`Background signOn error for ${crewId}:`, error));
              
              successCount++;
              
            } else if (currentStatus === 'Sign on' && normalizedCurrentShip !== normalizedBulkShip && normalizedCurrentShip !== '' && normalizedCurrentShip !== '-') {
              // Transfer flow: Ship A → Ship B
              // Update DB immediately
              await crewService.update(crewId, {
                ship_sign_on: bulkShipSignOn,
                status: 'Sign on',
                date_sign_on: new Date().toISOString().split('T')[0]
              });
              
              // File movement in background
              crewService.transferShip(crewId, {
                to_ship_name: bulkShipSignOn,
                transfer_date: new Date().toISOString().split('T')[0],
                notes: `Bulk transfer via Ship Sign On edit from ${currentShip} to ${bulkShipSignOn}`
              }).catch(error => console.error(`Background transferShip error for ${crewId}:`, error));
              
              successCount++;
              
            } else {
              // No file movement needed:
              // - Crew already on same ship (Sign on + same ship)
              // - Just updating field for other cases
              await crewService.update(crewId, {
                ship_sign_on: bulkShipSignOn,
                status: 'Sign on',
                date_sign_off: null
              });
              successCount++;
            }
            
          } catch (error) {
            console.error(`Failed to update crew ${crewId}:`, error);
            failCount++;
          }
        }
      }
      
      // Dismiss processing toast
      toast.dismiss(processingToast);
      
      // Refresh table again to show final state
      fetchCrewList();
      
      // Show result
      if (successCount > 0) {
        const message = isSignOff
          ? (language === 'vi'
              ? `✅ Đã sign off ${successCount} thuyền viên. Files đang được di chuyển...${failCount > 0 ? ` (${failCount} thất bại)` : ''}`
              : `✅ Signed off ${successCount} crew member(s). Files are being moved in background...${failCount > 0 ? ` (${failCount} failed)` : ''}`)
          : (language === 'vi'
              ? `✅ Đã cập nhật ${successCount} thuyền viên. Files đang được di chuyển...${failCount > 0 ? ` (${failCount} thất bại)` : ''}`
              : `✅ Updated ${successCount} crew member(s). Files are being moved in background...${failCount > 0 ? ` (${failCount} failed)` : ''}`);
        
        toast.success(message, { duration: 5000 });
      } else {
        toast.error(language === 'vi' ? 'Không thể cập nhật' : 'Failed to update');
      }
      
    } catch (error) {
      toast.dismiss(processingToast);
      console.error('Bulk ship sign on error:', error);
      toast.error(language === 'vi' ? 'Lỗi cập nhật hàng loạt' : 'Bulk update error');
      fetchCrewList();
    }
  };
  
  const handleBulkUpdateDateSignOn = async () => {
    const crewIds = Array.from(selectedCrewMembers);
    const value = bulkDateSignOn === '' ? null : bulkDateSignOn;
    
    // Close modal immediately
    setShowBulkEditDateSignOn(false);
    
    // Show processing toast
    const processingToast = toast.loading(
      language === 'vi' 
        ? '🔄 Đang cập nhật...' 
        : '🔄 Processing...'
    );
    
    // Refresh table immediately (optimistic update)
    fetchCrewList();
    
    try {
      let successCount = 0;
      let failCount = 0;
      
      for (const crewId of crewIds) {
        try {
          // Update crew date_sign_on in DB immediately
          await crewService.update(crewId, { date_sign_on: value });
          
          // Update assignment history in background (if date is not null)
          if (value) {
            crewService.updateAssignmentDates(crewId, { date_sign_on: value })
              .catch(error => console.error(`Background assignment history update error for ${crewId}:`, error));
          }
          
          successCount++;
        } catch (error) {
          console.error(`Failed to update crew ${crewId}:`, error);
          failCount++;
        }
      }
      
      // Dismiss processing toast
      toast.dismiss(processingToast);
      
      // Refresh table again to show final state
      fetchCrewList();
      
      if (successCount > 0) {
        toast.success(
          language === 'vi' 
            ? `✅ Đã cập nhật ${successCount} thuyền viên${failCount > 0 ? `, ${failCount} thất bại` : ''}`
            : `✅ Updated ${successCount} crew member(s)${failCount > 0 ? `, ${failCount} failed` : ''}`
        );
      } else {
        toast.error(language === 'vi' ? 'Không thể cập nhật' : 'Failed to update');
      }
    } catch (error) {
      toast.dismiss(processingToast);
      console.error('Bulk update date sign on error:', error);
      toast.error(language === 'vi' ? 'Lỗi cập nhật hàng loạt' : 'Bulk update error');
      fetchCrewList();
    }
  };
  
  const handleBulkUpdateDateSignOff = async () => {
    const crewIds = Array.from(selectedCrewMembers);
    const isClearingDate = !bulkDateSignOff || bulkDateSignOff.trim() === '';
    
    // Close modal immediately
    setShowBulkEditDateSignOff(false);
    
    // Show processing toast
    const processingToast = toast.loading(
      language === 'vi' 
        ? '🔄 Đang cập nhật...' 
        : '🔄 Processing...'
    );
    
    // Refresh table immediately (optimistic update)
    fetchCrewList();
    
    try {
      let successCount = 0;
      let failCount = 0;
      
      if (isClearingDate) {
        // Clear Date Sign Off only (don't change status or ship)
        for (const crewId of crewIds) {
          try {
            await crewService.update(crewId, { date_sign_off: null });
            successCount++;
          } catch (error) {
            console.error(`Failed to clear date for crew ${crewId}:`, error);
            failCount++;
          }
        }
      } else {
        // Sign Off flow: Update DB immediately, file movement in background
        for (const crewId of crewIds) {
          const crew = crewList.find(c => c.id === crewId);
          if (!crew) continue;
          
          const currentStatus = crew.status;
          const currentShip = crew.ship_sign_on || '-';
          
          try {
            if (currentStatus === 'Sign on') {
              // Case 2: Real Sign Off operation (Ship → Standby)
              // Update DB immediately with status change
              await crewService.update(crewId, {
                date_sign_off: bulkDateSignOff,
                status: 'Standby',
                ship_sign_on: '-'
              });
              
              // signOff API creates new assignment history record (background)
              crewService.signOff(crewId, {
                sign_off_date: bulkDateSignOff,
                notes: `Bulk sign off via Date Sign Off edit`
              }).catch(error => console.error(`Background signOff error for ${crewId}:`, error));
              
            } else {
              // Case 1: Date correction (crew already Standby, just fixing date)
              // Update DB immediately (no status/ship change)
              await crewService.update(crewId, {
                date_sign_off: bulkDateSignOff
              });
              
              // Update existing assignment history record (background)
              crewService.updateAssignmentDates(crewId, { date_sign_off: bulkDateSignOff })
                .catch(error => console.error(`Background assignment history update error for ${crewId}:`, error));
            }
            
            successCount++;
            
          } catch (error) {
            console.error(`Failed to update crew ${crewId}:`, error);
            failCount++;
          }
        }
      }
      
      // Dismiss processing toast
      toast.dismiss(processingToast);
      
      // Refresh table again to show final state
      fetchCrewList();
      
      // Show result
      if (successCount > 0) {
        const message = isClearingDate
          ? (language === 'vi' 
              ? `✅ Đã xóa ngày xuống tàu cho ${successCount} thuyền viên${failCount > 0 ? `, ${failCount} thất bại` : ''}` 
              : `✅ Cleared date for ${successCount} crew member(s)${failCount > 0 ? `, ${failCount} failed` : ''}`)
          : (language === 'vi'
              ? `✅ Đã sign off ${successCount} thuyền viên. Files đang được di chuyển...${failCount > 0 ? ` (${failCount} thất bại)` : ''}`
              : `✅ Signed off ${successCount} crew member(s). Files are being moved in background...${failCount > 0 ? ` (${failCount} failed)` : ''}`);
        
        toast.success(message, { duration: 5000 });
      } else {
        toast.error(language === 'vi' ? 'Không thể cập nhật' : 'Failed to update');
      }
      
    } catch (error) {
      toast.dismiss(processingToast);
      console.error('Bulk date sign off error:', error);
      toast.error(language === 'vi' ? 'Lỗi cập nhật hàng loạt' : 'Bulk update error');
      fetchCrewList();
    }
  };
  
  // Bulk update field helper
  const bulkUpdateField = async (fieldName, value, crewIds) => {
    try {
      let successCount = 0;
      let failCount = 0;
      
      for (const crewId of crewIds) {
        try {
          await crewService.update(crewId, { [fieldName]: value });
          successCount++;
        } catch (error) {
          console.error(`Failed to update crew ${crewId}:`, error);
          failCount++;
        }
      }
      
      if (successCount > 0) {
        toast.success(
          language === 'vi' 
            ? `Đã cập nhật ${successCount} thuyền viên${failCount > 0 ? `, ${failCount} thất bại` : ''}`
            : `Updated ${successCount} crew member(s)${failCount > 0 ? `, ${failCount} failed` : ''}`
        );
        fetchCrewList(); // Refresh list
      } else {
        toast.error(language === 'vi' ? 'Không thể cập nhật' : 'Failed to update');
      }
    } catch (error) {
      console.error('Bulk update error:', error);
      toast.error(language === 'vi' ? 'Lỗi cập nhật hàng loạt' : 'Bulk update error');
    }
  };
  
  // Bulk update multiple fields helper
  const bulkUpdateMultipleFields = async (updates, crewIds, updateType = null) => {
    try {
      let successCount = 0;
      let failCount = 0;
      
      for (const crewId of crewIds) {
        try {
          await crewService.update(crewId, updates);
          successCount++;
        } catch (error) {
          console.error(`Failed to update crew ${crewId}:`, error);
          failCount++;
        }
      }
      
      if (successCount > 0) {
        // Custom toast message based on update type
        if (updateType === 'date_sign_off') {
          // Date Sign Off was filled (auto-update status and ship)
          toast.success(
            language === 'vi' 
              ? `✅ Đã cập nhật ${successCount} thuyền viên: Ngày rời tàu, Trạng thái "Standby", Tàu "-"${failCount > 0 ? ` (${failCount} thất bại)` : ''}`
              : `✅ Updated ${successCount} crew member(s): Date sign off, Status "Standby", Ship "-"${failCount > 0 ? ` (${failCount} failed)` : ''}`
          );
        } else if (updateType === 'clear_date_sign_off') {
          // Date Sign Off was cleared (no other changes)
          toast.success(
            language === 'vi' 
              ? `✅ Đã xóa ngày rời tàu cho ${successCount} thuyền viên${failCount > 0 ? ` (${failCount} thất bại)` : ''}`
              : `✅ Cleared date sign off for ${successCount} crew member(s)${failCount > 0 ? ` (${failCount} failed)` : ''}`
          );
        } else if (updates.ship_sign_on && updates.status && updates.hasOwnProperty('date_sign_off')) {
          // Ship Sign On update (has status and date_sign_off)
          toast.success(
            language === 'vi' 
              ? `✅ Đã cập nhật ${successCount} thuyền viên: Tàu "${updates.ship_sign_on}", Trạng thái "Sign on", Đã xóa ngày rời tàu${failCount > 0 ? ` (${failCount} thất bại)` : ''}`
              : `✅ Updated ${successCount} crew member(s): Ship "${updates.ship_sign_on}", Status "Sign on", Cleared date sign off${failCount > 0 ? ` (${failCount} failed)` : ''}`
          );
        } else {
          // Generic update
          toast.success(
            language === 'vi' 
              ? `Đã cập nhật ${successCount} thuyền viên${failCount > 0 ? `, ${failCount} thất bại` : ''}`
              : `Updated ${successCount} crew member(s)${failCount > 0 ? `, ${failCount} failed` : ''}`
          );
        }
        fetchCrewList(); // Refresh list
      } else {
        toast.error(language === 'vi' ? 'Không thể cập nhật' : 'Failed to update');
      }
    } catch (error) {
      console.error('Bulk update error:', error);
      toast.error(language === 'vi' ? 'Lỗi cập nhật hàng loạt' : 'Bulk update error');
    }
  };
  
  // Passport context menu handler
  const handlePassportRightClick = (e, crew) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!crew.passport) return;
    
    // Calculate menu position with smart positioning
    const menuWidth = 300;
    const menuHeight = 220; // 4 menu items + header + padding
    let x = e.clientX;
    let y = e.clientY;
    
    // Adjust if menu would go off-screen (right side)
    if (x + menuWidth > window.innerWidth) {
      x = window.innerWidth - menuWidth - 10;
    }
    
    // Adjust if menu would go off-screen (bottom)
    if (y + menuHeight > window.innerHeight) {
      // Try to position above cursor
      y = Math.max(10, y - menuHeight);
      if (y < 10) {
        y = 10;
      }
    }
    
    setPassportContextMenu({
      show: true,
      x,
      y,
      crew
    });
  };
  
  // View passport file
  const handleViewPassport = () => {
    if (passportContextMenu.crew?.passport_file_id) {
      window.open(`https://drive.google.com/file/d/${passportContextMenu.crew.passport_file_id}/view`, '_blank');
      toast.success(language === 'vi' ? 'Đã mở file hộ chiếu' : 'Opened passport file');
    } else {
      toast.error(language === 'vi' ? 'Không tìm thấy file hộ chiếu' : 'Passport file not found');
    }
    setPassportContextMenu({ show: false, x: 0, y: 0, crew: null });
  };
  
  // Copy passport link
  const handleCopyPassportLink = () => {
    if (passportContextMenu.crew?.passport_file_id) {
      const link = `https://drive.google.com/file/d/${passportContextMenu.crew.passport_file_id}/view`;
      navigator.clipboard.writeText(link);
      toast.success(language === 'vi' ? 'Đã sao chép link file hộ chiếu' : 'Passport file link copied');
    } else {
      toast.error(language === 'vi' ? 'Không tìm thấy file hộ chiếu' : 'Passport file not found');
    }
    setPassportContextMenu({ show: false, x: 0, y: 0, crew: null });
  };
  
  // Download passport (open in new tab for now)
  const handleDownloadPassport = () => {
    if (passportContextMenu.crew?.passport_file_id) {
      window.open(`https://drive.google.com/uc?export=download&id=${passportContextMenu.crew.passport_file_id}`, '_blank');
      toast.success(language === 'vi' ? 'Đang tải file hộ chiếu...' : 'Downloading passport file...');
    } else {
      toast.error(language === 'vi' ? 'Không tìm thấy file hộ chiếu' : 'Passport file not found');
    }
    setPassportContextMenu({ show: false, x: 0, y: 0, crew: null });
  };
  
  // Auto-rename passport files
  const handleAutoRenamePassport = async () => {
    if (!passportContextMenu.crew) return;
    
    const crew = passportContextMenu.crew;
    setPassportContextMenu({ show: false, x: 0, y: 0, crew: null });
    
    try {
      // Show loading toast
      const loadingToast = toast.loading(
        language === 'vi' 
          ? `🔄 Đang đổi tên file hộ chiếu cho ${crew.full_name}...`
          : `🔄 Renaming passport files for ${crew.full_name}...`
      );
      
      // Call auto rename API
      const result = await crewService.autoRenamePassport(crew.id);
      
      // Dismiss loading toast
      toast.dismiss(loadingToast);
      
      // Show success with new filename
      const newFilename = result.new_filename || 'files';
      toast.success(
        language === 'vi' 
          ? `✅ Đã đổi tên thành: ${newFilename}`
          : `✅ Renamed to: ${newFilename}`,
        { duration: 5000 }
      );
      
      // Refresh crew list to reflect any changes
      fetchCrewList();
      
    } catch (error) {
      console.error('Error renaming files:', error);
      const errorDetail = error.response?.data?.detail || error.message;
      
      toast.error(
        language === 'vi' 
          ? `❌ Lỗi đổi tên file: ${errorDetail}`
          : `❌ Error renaming files: ${errorDetail}`,
        { duration: 7000 }
      );
    }
  };

  // Bulk view passport files
  const handleBulkViewPassport = async () => {
    const crewIds = Array.from(selectedCrewMembers);
    if (crewIds.length === 0) return;
    
    setPassportContextMenu({ show: false, x: 0, y: 0, crew: null });
    
    let openedCount = 0;
    
    // Open each passport file in new tab
    for (const crewId of crewIds) {
      const crew = crewList.find(c => c.id === crewId);
      if (!crew || !crew.passport_file_id) continue;
      
      const fileUrl = `https://drive.google.com/file/d/${crew.passport_file_id}/view`;
      window.open(fileUrl, '_blank');
      openedCount++;
      
      // Small delay between opening tabs to avoid browser blocking
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    if (openedCount > 0) {
      toast.success(
        language === 'vi' 
          ? `✅ Đã mở ${openedCount} file hộ chiếu`
          : `✅ Opened ${openedCount} passport file(s)`,
        { duration: 3000 }
      );
    } else {
      toast.warning(
        language === 'vi' 
          ? `⚠️ Không có file hộ chiếu để mở`
          : `⚠️ No passport files to open`,
        { duration: 3000 }
      );
    }
  };

  // Bulk copy passport links
  const handleBulkCopyPassportLink = async () => {
    const crewIds = Array.from(selectedCrewMembers);
    if (crewIds.length === 0) return;
    
    setPassportContextMenu({ show: false, x: 0, y: 0, crew: null });
    
    const links = [];
    
    // Collect all passport links
    for (const crewId of crewIds) {
      const crew = crewList.find(c => c.id === crewId);
      if (!crew || !crew.passport_file_id) continue;
      
      const fileUrl = `https://drive.google.com/file/d/${crew.passport_file_id}/view`;
      links.push(`${crew.full_name}: ${fileUrl}`);
    }
    
    if (links.length > 0) {
      const allLinks = links.join('\n');
      
      try {
        await navigator.clipboard.writeText(allLinks);
        toast.success(
          language === 'vi' 
            ? `✅ Đã sao chép ${links.length} link file`
            : `✅ Copied ${links.length} file link(s)`,
          { duration: 3000 }
        );
      } catch (error) {
        toast.error(
          language === 'vi' 
            ? `❌ Không thể sao chép link`
            : `❌ Failed to copy links`,
          { duration: 3000 }
        );
      }
    } else {
      toast.warning(
        language === 'vi' 
          ? `⚠️ Không có link để sao chép`
          : `⚠️ No links to copy`,
        { duration: 3000 }
      );
    }
  };

  // Bulk download passport files
  const handleBulkDownloadPassport = async () => {
    const crewIds = Array.from(selectedCrewMembers);
    if (crewIds.length === 0) return;
    
    setPassportContextMenu({ show: false, x: 0, y: 0, crew: null });
    
    let downloadCount = 0;
    
    // Trigger download for each passport file
    for (const crewId of crewIds) {
      const crew = crewList.find(c => c.id === crewId);
      if (!crew || !crew.passport_file_id) continue;
      
      try {
        // Generate filename
        const filename = crew.passport || `${crew.full_name}_Passport.pdf`;
        
        // Trigger download
        const downloadUrl = `https://drive.google.com/uc?export=download&id=${crew.passport_file_id}`;
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        downloadCount++;
        
        // Small delay between downloads
        await new Promise(resolve => setTimeout(resolve, 200));
        
      } catch (error) {
        console.error(`Error downloading passport for ${crew.full_name}:`, error);
      }
    }
    
    if (downloadCount > 0) {
      toast.success(
        language === 'vi' 
          ? `✅ Đang tải xuống ${downloadCount} file hộ chiếu`
          : `✅ Downloading ${downloadCount} passport file(s)`,
        { duration: 3000 }
      );
    } else {
      toast.warning(
        language === 'vi' 
          ? `⚠️ Không có file để tải xuống`
          : `⚠️ No files to download`,
        { duration: 3000 }
      );
    }
  };

  // Bulk auto-rename passport files
  const handleBulkAutoRenamePassport = async () => {
    const crewIds = Array.from(selectedCrewMembers);
    if (crewIds.length === 0) return;
    
    setPassportContextMenu({ show: false, x: 0, y: 0, crew: null });
    
    try {
      // Show loading toast
      const loadingToast = toast.loading(
        language === 'vi' 
          ? `🔄 Đang đổi tên file hộ chiếu cho ${crewIds.length} thuyền viên...`
          : `🔄 Renaming passport files for ${crewIds.length} crew members...`
      );
      
      let successCount = 0;
      let failCount = 0;
      const results = [];
      
      // Process each crew member
      for (const crewId of crewIds) {
        const crew = crewList.find(c => c.id === crewId);
        if (!crew) continue;
        
        try {
          const result = await crewService.autoRenamePassport(crewId);
          successCount++;
          results.push({
            crew: crew.full_name,
            success: true,
            filename: result.new_filename || 'files'
          });
        } catch (error) {
          failCount++;
          results.push({
            crew: crew.full_name,
            success: false,
            error: error.response?.data?.detail || error.message
          });
        }
      }
      
      // Dismiss loading toast
      toast.dismiss(loadingToast);
      
      // Show results
      if (successCount > 0) {
        toast.success(
          language === 'vi' 
            ? `✅ Đã đổi tên file cho ${successCount} thuyền viên${failCount > 0 ? ` (${failCount} thất bại)` : ''}`
            : `✅ Renamed files for ${successCount} crew member(s)${failCount > 0 ? ` (${failCount} failed)` : ''}`,
          { duration: 5000 }
        );
      }
      
      if (failCount > 0) {
        const failedCrew = results.filter(r => !r.success).map(r => r.crew).join(', ');
        toast.error(
          language === 'vi' 
            ? `❌ Thất bại: ${failedCrew}`
            : `❌ Failed: ${failedCrew}`,
          { duration: 7000 }
        );
      }
      
      // Refresh crew list to reflect any changes
      fetchCrewList();
      
    } catch (error) {
      console.error('Error in bulk rename:', error);
      toast.error(
        language === 'vi' 
          ? `❌ Lỗi đổi tên file hàng loạt`
          : `❌ Bulk rename error`,
        { duration: 7000 }
      );
    }
  };
  
  // Rank context menu handler
  const handleRankRightClick = (e, crew) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Calculate menu position with smart positioning
    const menuWidth = 250;
    const menuHeight = 320; // Scrollable list + header, but cap at max-h-80
    let x = e.clientX;
    let y = e.clientY;
    
    // Adjust if menu would go off-screen (right side)
    if (x + menuWidth > window.innerWidth) {
      x = window.innerWidth - menuWidth - 10;
    }
    
    // Adjust if menu would go off-screen (bottom)
    if (y + menuHeight > window.innerHeight) {
      // Try to position above cursor
      y = Math.max(10, y - menuHeight);
      if (y < 10) {
        y = 10;
      }
    }
    
    setRankContextMenu({
      show: true,
      x,
      y,
      crew
    });
  };
  
  // Update crew rank
  const handleUpdateRank = async (rank) => {
    if (!rankContextMenu.crew) return;
    
    const crew = rankContextMenu.crew;
    setRankContextMenu({ show: false, x: 0, y: 0, crew: null });
    
    try {
      await crewService.update(crew.id, { rank });
      
      toast.success(language === 'vi' 
        ? `Đã cập nhật chức vụ cho ${crew.full_name}: ${rank}`
        : `Updated rank for ${crew.full_name}: ${rank}`);
      
      // Refresh list
      fetchCrewList();
      
    } catch (error) {
      console.error('Error updating rank:', error);
      toast.error(language === 'vi' 
        ? `Lỗi cập nhật chức vụ: ${error.response?.data?.detail || error.message}`
        : `Error updating rank: ${error.response?.data?.detail || error.message}`);
    }
  };
  
  // Batch processing handler
  const handleBatchProcessing = async (files, modalStatus = null, modalShipSignOn = null) => {
    // Validate all files first
    const validFiles = [];
    for (const file of files) {
      const isValidType = file.type === 'application/pdf' || file.type.startsWith('image/');
      const isValidSize = file.size <= 10 * 1024 * 1024; // 10MB
      
      if (!isValidType) {
        toast.error(language === 'vi' 
          ? `File ${file.name} không đúng định dạng`
          : `File ${file.name} has invalid format`);
        continue;
      }
      
      if (!isValidSize) {
        toast.error(language === 'vi' 
          ? `File ${file.name} quá lớn (>10MB)`
          : `File ${file.name} is too large (>10MB)`);
        continue;
      }
      
      validFiles.push(file);
    }
    
    if (validFiles.length === 0) {
      toast.error(language === 'vi' 
        ? 'Không có file hợp lệ nào để xử lý'
        : 'No valid files to process');
      return;
    }
    
    // Store the status and ship for batch processing
    // Use modal status if provided (from AddCrewModal), otherwise use filter
    const batchStatus = modalStatus || (filters.ship_sign_on === 'Standby' ? 'Standby' : 'Sign on');
    const batchShip = modalShipSignOn || (selectedShip?.name || '-');
    
    // Initialize batch processing with enhanced tracking
    setBatchProgress({ current: 0, total: validFiles.length, success: 0, failed: 0 });
    setBatchResults([]);
    setIsBatchProcessing(true);
    setShowBatchProcessingModal(true);
    setIsBatchModalMinimized(false);
    
    // Initialize file tracking maps
    const initialStatusMap = {};
    const initialProgressMap = {};
    const initialSubStatusMap = {};
    const initialFileObjectsMap = {};
    validFiles.forEach(file => {
      initialStatusMap[file.name] = 'waiting';
      initialProgressMap[file.name] = 0;
      initialSubStatusMap[file.name] = '';
      initialFileObjectsMap[file.name] = file; // Store file object for retry
    });
    setFileStatusMap(initialStatusMap);
    setFileProgressMap(initialProgressMap);
    setFileSubStatusMap(initialSubStatusMap);
    setFileObjectsMap(initialFileObjectsMap);
    
    // Close Add Crew modal
    setShowAddCrewModal(false);
    
    const STAGGER_DELAY = 2000; // 2 seconds between file starts
    const results = [];
    
    // Process files with staggered start (PARALLEL PROCESSING)
    const promises = validFiles.map((file, index) => {
      return new Promise((resolve) => {
        setTimeout(async () => {
          // Update status to processing
          setFileStatusMap(prev => ({ ...prev, [file.name]: 'processing' }));
          
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
            const result = await processSingleFileInBatch(file, progressController, batchStatus, batchShip);
            results.push(result);
            
            // Complete progress
            progressController.complete();
            
            // Update status to completed or error
            setFileStatusMap(prev => ({ ...prev, [file.name]: result.success ? 'completed' : 'error' }));
            
            setBatchProgress(prev => ({
              ...prev,
              current: results.length,
              success: prev.success + (result.success ? 1 : 0),
              failed: prev.failed + (result.success ? 0 : 1)
            }));
            
            resolve(result);
          } catch (error) {
            console.error(`Error processing file ${file.name}:`, error);
            progressController.stop();
            
            const errorResult = {
              success: false,
              filename: file.name,
              error: error.message || 'Unknown error'
            };
            results.push(errorResult);
            
            setFileStatusMap(prev => ({ ...prev, [file.name]: 'error' }));
            setFileProgressMap(prev => ({ ...prev, [file.name]: 0 }));
            
            setBatchProgress(prev => ({
              ...prev,
              current: results.length,
              failed: prev.failed + 1
            }));
            
            resolve(errorResult);
          }
        }, index * STAGGER_DELAY);
      });
    });
    
    // Wait for all files to complete
    await Promise.all(promises);
    
    // Show results
    setBatchResults(results);
    setShowBatchProcessingModal(false);
    setShowBatchResultsModal(true);
    setIsBatchProcessing(false);
    
    // Refresh crew list
    fetchCrewList();
  };
  
  // Process single file in batch mode
  const processSingleFileInBatch = async (file, progressController, batchStatus, batchShip) => {
    try {
      const shipName = batchShip || selectedShip?.name || '-';
      
      // Step 1: Analyze passport
      const analysisResponse = await crewService.analyzePassport(file, shipName);
      const analysisData = analysisResponse.data || analysisResponse;
      
      // Check for duplicate
      if (analysisData.duplicate) {
        return {
          success: false,
          filename: file.name,
          error: language === 'vi' 
            ? `Hộ chiếu đã tồn tại: ${analysisData.existing_crew?.full_name}`
            : `Passport already exists: ${analysisData.existing_crew?.full_name}`,
          duplicate: true
        };
      }
      
      // Check if analysis succeeded
      if (!analysisData.success || !analysisData.analysis) {
        return {
          success: false,
          filename: file.name,
          error: language === 'vi' ? 'Không thể phân tích file' : 'Cannot analyze file'
        };
      }
      
      const analysis = analysisData.analysis;
      
      // Validate required fields
      if (!analysis.full_name || !(analysis.passport_no || analysis.passport_number) || !analysis.date_of_birth) {
        return {
          success: false,
          filename: file.name,
          error: language === 'vi' 
            ? 'Thiếu thông tin bắt buộc (tên, hộ chiếu, ngày sinh)'
            : 'Missing required information (name, passport, date of birth)'
        };
      }
      
      // Step 2: Create crew member
      const vietnameseFullName = analysis.full_name || '';
      const vietnamesePlaceOfBirth = analysis.place_of_birth || '';
      
      // Use the batch status and ship passed from handleBatchProcessing
      let crewStatus = batchStatus || 'Sign on';
      let shipSignOn = batchShip || selectedShip?.name || '-';
      
      const crewData = {
        full_name: vietnameseFullName,
        full_name_en: analysis.full_name_en || autoFillEnglishField(vietnameseFullName),
        sex: analysis.sex || 'M',
        date_of_birth: analysis.date_of_birth?.includes('/') 
          ? analysis.date_of_birth.split('/').reverse().join('-')
          : analysis.date_of_birth?.split('T')[0],
        place_of_birth: vietnamesePlaceOfBirth,
        place_of_birth_en: analysis.place_of_birth_en || autoFillEnglishField(vietnamesePlaceOfBirth),
        passport: analysis.passport_no || analysis.passport_number || analysis.passport,
        nationality: analysis.nationality || '',
        passport_expiry_date: (() => {
          const expiryDate = analysis.expiry_date || analysis.passport_expiry_date;
          if (!expiryDate) return '';
          if (expiryDate.includes('/')) {
            return expiryDate.split('/').reverse().join('-');
          }
          return expiryDate.split('T')[0];
        })(),
        rank: '',
        seamen_book: '',
        status: crewStatus,
        ship_sign_on: shipSignOn,
        place_sign_on: '',
        date_sign_on: '',
        date_sign_off: ''
      };
      
      const createResponse = await crewService.createCrew(crewData);
      const crewId = createResponse.data.id;
      
      // Step 3: Upload files in background (don't wait)
      if (analysis._file_content) {
        crewService.uploadPassportFiles(crewId, {
          file_content: analysis._file_content,
          filename: analysis._filename,
          content_type: analysis._content_type,
          summary_text: analysis._summary_text || '',
          ship_name: crewData.ship_sign_on
        }).catch(error => {
          console.error(`File upload failed for ${file.name}:`, error);
        });
      }
      
      return {
        success: true,
        filename: file.name,
        crew_name: crewData.full_name,
        passport_number: crewData.passport
      };
      
    } catch (error) {
      console.error(`Error in batch processing for ${file.name}:`, error);
      return {
        success: false,
        filename: file.name,
        error: error.response?.data?.detail || error.message || 'Unknown error'
      };
    }
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
    setShowBatchProcessingModal(true);
    setIsBatchModalMinimized(true);
    setIsBatchProcessing(true);
    
    // Reset status for retry
    setFileStatusMap(prev => ({ ...prev, [failedFileName]: 'pending' }));
    setFileProgressMap(prev => ({ ...prev, [failedFileName]: 0 }));
    setFileSubStatusMap(prev => ({ 
      ...prev, 
      [failedFileName]: language === 'vi' ? '🔄 Đang thử lại...' : '🔄 Retrying...' 
    }));
    
    // Update batch progress to show we're processing 1 file
    setBatchProgress({ current: 0, total: 1, success: 0, failed: 0 });
    
    // Show retry message
    toast.info(
      language === 'vi' 
        ? `🔄 Đang xử lý lại file: ${failedFileName}` 
        : `🔄 Retrying file: ${failedFileName}`
    );
    
    try {
      // Update status to processing
      setFileStatusMap(prev => ({ ...prev, [failedFileName]: 'processing' }));
      
      // Get batch status and ship from current context
      const batchStatus = filters.ship_sign_on === 'Standby' ? 'Standby' : 'Sign on';
      const batchShip = selectedShip?.name || '-';
      
      // Create progress controller
      const estimatedTime = 15000; // 15 seconds estimate
      const progressController = {
        interval: setInterval(() => {
          setFileProgressMap(prev => {
            const currentProgress = prev[failedFileName] || 0;
            if (currentProgress < 90) {
              return { ...prev, [failedFileName]: Math.min(currentProgress + 5, 90) };
            }
            return prev;
          });
        }, estimatedTime / 18),
        complete: () => {
          clearInterval(progressController.interval);
          setFileProgressMap(prev => ({ ...prev, [failedFileName]: 100 }));
        },
        stop: () => {
          clearInterval(progressController.interval);
        }
      };
      
      // Re-process the SAME file
      const result = await processSingleFileInBatch(originalFile, progressController, batchStatus, batchShip);
      
      if (result.success) {
        progressController.complete();
        setFileStatusMap(prev => ({ ...prev, [failedFileName]: 'completed' }));
        
        toast.success(
          language === 'vi' 
            ? `✅ File đã được xử lý thành công!` 
            : `✅ File processed successfully!`
        );
        
        // Update progress to show completion
        setBatchProgress({ current: 1, total: 1, success: 1, failed: 0 });
        
        // Update the result in BatchResultsModal
        setBatchResults(prev => 
          prev.map(r => r.filename === failedFileName ? result : r)
        );
        
        // Refresh list
        fetchCrewList();
        
        // Close ProcessingModal after a short delay
        setTimeout(() => {
          setShowBatchProcessingModal(false);
          setIsBatchProcessing(false);
        }, 1500);
      } else {
        progressController.stop();
        setFileStatusMap(prev => ({ ...prev, [failedFileName]: 'error' }));
        
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
          setShowBatchProcessingModal(false);
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
      setFileStatusMap(prev => ({ ...prev, [failedFileName]: 'error' }));
      setFileSubStatusMap(prev => ({ 
        ...prev, 
        [failedFileName]: error.message || 'Unknown error' 
      }));
      
      // Close ProcessingModal after a short delay
      setTimeout(() => {
        setShowBatchProcessingModal(false);
        setIsBatchProcessing(false);
      }, 1500);
    }
  };

  const filteredCrewData = getFilteredCrewData();
  const sortedCrewData = getSortedCrewData();

  return (
    <div className="space-y-6">
      {/* Header with Add Crew Button */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-1">
            {language === 'vi' ? 'Danh sách thuyền viên công ty' : 'Company Crew List'}
          </h3>
          <p className="text-sm text-gray-600">
            {language === 'vi' 
              ? 'Quản lý tất cả thuyền viên của công ty' 
              : 'Manage all crew members of the company'}
          </p>
        </div>
        
        {/* Action Buttons */}
        <div className="flex items-center space-x-3">
          {/* Add Crew Button - role check */}
          {user && ['manager', 'admin', 'super_admin'].includes(user.role) && (
            <button 
              onClick={() => setShowAddCrewModal(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all flex items-center"
            >
              <span className="mr-2">👤</span>
              {language === 'vi' ? 'Thêm thuyền viên' : 'Add Crew'}
            </button>
          )}
          
          {/* Refresh Button */}
          <button 
            onClick={() => {
              fetchCrewList();
              toast.success(language === 'vi' ? 'Đã làm mới danh sách thuyền viên' : 'Crew list refreshed');
            }}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-all flex items-center"
            title={language === 'vi' ? 'Làm mới' : 'Refresh'}
          >
            <span className="mr-2">🔄</span>
            {language === 'vi' ? 'Làm mới' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap items-end gap-4">
          {/* Ship Sign On Filter */}
          <div className="flex items-center space-x-2 min-w-[200px]">
            <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
              {language === 'vi' ? 'Tàu đăng ký:' : 'Ship Sign On:'}
            </label>
            <select 
              value={filters.ship_sign_on}
              onChange={(e) => {
                const newShipName = e.target.value;
                setFilters({...filters, ship_sign_on: newShipName});
                
                // Clear selected ship when choosing "All" or "Standby"
                // to show Company Panel instead of Ship Info
                if ((newShipName === 'All' || newShipName === 'Standby') && onShipSelect) {
                  onShipSelect(null);
                }
                
                // Callback to parent to sync selected ship
                if (onShipFilterChange) {
                  onShipFilterChange(newShipName);
                }
              }}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            >
              <option value="All">{language === 'vi' ? 'Tất cả' : 'All'}</option>
              <option value="Standby">{language === 'vi' ? '⚓ Standby' : '⚓ Standby'}</option>
              {ships.map(ship => (
                <option key={ship.id} value={ship.name}>{ship.name}</option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-2 min-w-[160px]">
            <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
              {language === 'vi' ? 'Trạng thái:' : 'Status:'}
            </label>
            <select 
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            >
              <option value="All">{language === 'vi' ? 'Tất cả' : 'All'}</option>
              <option value="Sign on">{language === 'vi' ? 'Đang làm việc' : 'Sign on'}</option>
              <option value="Standby">{language === 'vi' ? 'Chờ' : 'Standby'}</option>
              <option value="Leave">{language === 'vi' ? 'Nghỉ phép' : 'Leave'}</option>
            </select>
          </div>

          {/* Search Field */}
          <div className="flex items-center space-x-2 min-w-[200px] max-w-[280px]">
            <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
              {language === 'vi' ? 'Tìm kiếm:' : 'Search:'}
            </label>
            <div className="relative flex-1">
              <input
                type="text"
                placeholder={language === 'vi' ? 'Tìm theo tên thuyền viên...' : 'Search by crew name...'}
                value={filters.search}
                onChange={(e) => setFilters({...filters, search: e.target.value})}
                className="w-full px-3 py-2 pl-10 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
              <span className="absolute left-3 top-2.5 text-gray-400">🔍</span>
            </div>
          </div>

          {/* Results Count */}
          <div className="flex items-center ml-auto">
            <p className="text-sm text-gray-600 whitespace-nowrap">
              {language === 'vi' ? 'Hiển thị' : 'Showing'} <span className="font-semibold">{filteredCrewData.length}/{crewList.length}</span> {language === 'vi' ? 'thuyền viên' : 'crew members'}
              <span className="ml-2 text-green-600">✓ <span className="font-semibold">{filteredCrewData.filter(crew => crew.status === 'Sign on').length}</span> {language === 'vi' ? 'đang làm việc' : 'working'}</span>
            </p>
          </div>
        </div>
      </div>

      {/* Crew List Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {/* Checkbox Column */}
                <th className="px-3 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={sortedCrewData.length > 0 && sortedCrewData.every(crew => selectedCrewMembers.has(crew.id))}
                      onChange={(e) => handleSelectAllCrew(e.target.checked)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span>{language === 'vi' ? 'STT' : 'No.'}</span>
                  </div>
                </th>
                
                {/* Full Name */}
                <th 
                  onClick={() => handleSort('full_name')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Họ tên' : 'Full Name'}
                  {getSortIcon('full_name')}
                </th>
                
                {/* Sex */}
                <th 
                  onClick={() => handleSort('sex')}
                  className="px-3 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Giới tính' : 'Sex'}
                  {getSortIcon('sex')}
                </th>
                
                {/* Rank */}
                <th 
                  onClick={() => handleSort('rank')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Chức vụ' : 'Rank'}
                  {getSortIcon('rank')}
                </th>
                
                {/* Date of Birth */}
                <th 
                  onClick={() => handleSort('date_of_birth')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Ngày sinh' : 'Date of Birth'}
                  {getSortIcon('date_of_birth')}
                </th>
                
                {/* Place of Birth */}
                <th 
                  onClick={() => handleSort('place_of_birth')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Nơi sinh' : 'Place of Birth'}
                  {getSortIcon('place_of_birth')}
                </th>
                
                {/* Passport */}
                <th 
                  onClick={() => handleSort('passport')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Hộ chiếu' : 'Passport'}
                  {getSortIcon('passport')}
                </th>
                
                {/* Status */}
                <th 
                  onClick={() => handleSort('status')}
                  className="px-3 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Trạng thái' : 'Status'}
                  {getSortIcon('status')}
                </th>
                
                {/* Ship Sign On */}
                <th 
                  onClick={() => handleSort('ship_sign_on')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Tàu đăng ký' : 'Ship Sign On'}
                  {getSortIcon('ship_sign_on')}
                </th>
                
                {/* Place Sign On */}
                <th 
                  onClick={() => handleSort('place_sign_on')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Nơi xuống tàu' : 'Place Sign On'}
                  {getSortIcon('place_sign_on')}
                </th>
                
                {/* Date Sign On */}
                <th 
                  onClick={() => handleSort('date_sign_on')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider border-r border-gray-200 cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Ngày xuống tàu' : 'Date Sign On'}
                  {getSortIcon('date_sign_on')}
                </th>
                
                {/* Date Sign Off */}
                <th 
                  onClick={() => handleSort('date_sign_off')}
                  className="px-4 py-3 text-left text-sm font-bold text-gray-700 tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  {language === 'vi' ? 'Ngày rời tàu' : 'Date Sign Off'}
                  {getSortIcon('date_sign_off')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="12" className="px-6 py-12 text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
                    <p className="text-gray-600">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
                  </td>
                </tr>
              ) : sortedCrewData.length > 0 ? (
                sortedCrewData.map((crew, index) => (
                  <tr 
                    key={crew.id} 
                    className="hover:bg-gray-50 cursor-pointer"
                    onContextMenu={(e) => handleCrewRightClick(e, crew)}
                    onDoubleClick={() => handleCrewDoubleClick(crew)}
                    title={language === 'vi' ? 'Nhấp đúp để xem chứng chỉ | Chuột phải để xem menu' : 'Double-click to view certificates | Right-click for menu'}
                  >
                    <td 
                      className="px-3 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200"
                      title={crew.passport_file_name ? `File: ${crew.passport_file_name}` : (language === 'vi' ? 'Chưa có file' : 'No file')}
                    >
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={selectedCrewMembers.has(crew.id)}
                          onChange={() => handleSelectCrew(crew.id)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <span>{index + 1}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900 border-r border-gray-200 uppercase">
                      {language === 'vi' ? crew.full_name : (crew.full_name_en || crew.full_name)}
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {crew.sex ? (crew.sex.toLowerCase().startsWith('m') ? 'M' : crew.sex.toLowerCase().startsWith('f') ? 'F' : crew.sex) : '-'}
                    </td>
                    <td 
                      className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200"
                      onContextMenu={(e) => handleRankRightClick(e, crew)}
                    >
                      {crew.rank || '-'}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {formatDateDisplay(crew.date_of_birth) || '-'}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 uppercase">
                      {language === 'vi' ? crew.place_of_birth : (crew.place_of_birth_en || crew.place_of_birth)}
                    </td>
                    <td 
                      className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200"
                      onContextMenu={(e) => handlePassportRightClick(e, crew)}
                    >
                      <div className="flex items-center space-x-2">
                        <span>{crew.passport || '-'}</span>
                        {/* File status indicators */}
                        {crew.passport_file_id && (
                          <span 
                            className="text-green-500 text-xs cursor-pointer hover:text-green-600" 
                            title={language === 'vi' ? `File gốc\n📁 ${crew.ship_sign_on}/Crew Records/Crew List` : `Original file\n📁 ${crew.ship_sign_on}/Crew Records/Crew List`}
                            onClick={(e) => {
                              e.stopPropagation();
                              if (crew.passport_file_id) {
                                window.open(`https://drive.google.com/file/d/${crew.passport_file_id}/view`, '_blank');
                              }
                            }}
                          >
                            📄
                          </span>
                        )}
                        {crew.summary_file_id && (
                          <span 
                            className="text-blue-500 text-xs cursor-pointer hover:text-blue-600" 
                            title={language === 'vi' ? `File tóm tắt\n📁 ${crew.ship_sign_on}/Crew Records/Crew List` : `Summary file\n📁 ${crew.ship_sign_on}/Crew Records/Crew List`}
                            onClick={(e) => {
                              e.stopPropagation();
                              if (crew.summary_file_id) {
                                window.open(`https://drive.google.com/file/d/${crew.summary_file_id}/view`, '_blank');
                              }
                            }}
                          >
                            📋
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-3 py-4 whitespace-nowrap border-r border-gray-200">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        crew.status === 'Sign on' ? 'bg-green-100 text-green-800' :
                        crew.status === 'Standby' ? 'bg-yellow-100 text-yellow-800' :
                        crew.status === 'Leave' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {crew.status}
                      </span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {crew.ship_sign_on}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {crew.place_sign_on || '-'}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200">
                      {formatDateDisplay(crew.date_sign_on) || '-'}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDateDisplay(crew.date_sign_off) || '-'}
                    </td>
                  </tr>
                ))
              ) : (
                // Empty State
                <tr>
                  <td colSpan="12" className="px-6 py-12 text-center">
                    <div className="text-gray-400 text-lg mb-2">👥</div>
                    <p className="text-gray-500">
                      {language === 'vi' ? 'Không tìm thấy thuyền viên phù hợp' : 'No crew members found'}
                    </p>
                    <p className="text-sm text-gray-400 mt-1">
                      {language === 'vi' ? 'Thử thay đổi bộ lọc hoặc thêm thuyền viên mới' : 'Try changing filters or add new crew members'}
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Context Menus */}
      {/* Row Context Menu */}
      {crewContextMenu.show && (
        <div
          className="fixed bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50 max-h-[80vh] overflow-y-auto"
          style={{
            top: `${crewContextMenu.y}px`,
            left: `${crewContextMenu.x}px`,
            minWidth: '280px'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {selectedCrewMembers.size > 1 && (
            <div className="px-4 py-2 text-sm font-semibold text-gray-700 border-b border-gray-200">
              {selectedCrewMembers.size} {language === 'vi' ? 'thuyền viên đã chọn' : 'crew members selected'}
            </div>
          )}
          {selectedCrewMembers.size === 1 && (
            <>
              <button
                onClick={handleEditCrew}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center space-x-2"
              >
                <span>✏️</span>
                <span>{language === 'vi' ? 'Chỉnh sửa thuyền viên' : 'Edit Crew Member'}</span>
              </button>
              
              {/* Show history menu item only for Editor+ roles */}
              {user && ['company_officer', 'manager', 'admin', 'super_admin'].includes(user.role) && (
                <button
                  onClick={handleViewHistory}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center space-x-2"
                >
                  <span>📋</span>
                  <span>{language === 'vi' ? 'Xem lịch sử' : 'View History'}</span>
                </button>
              )}
              
              <div className="border-t border-gray-200 my-1"></div>
            </>
          )}
          {/* Bulk edit options */}
          <button
            onClick={() => handleBulkEditShipSignOn()}
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center space-x-2"
          >
            <span>🚢</span>
            <span>{language === 'vi' ? 'SIGN ON' : 'SIGN ON'}</span>
          </button>
          <button
            onClick={() => handleBulkEditPlaceSignOn()}
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center space-x-2"
          >
            <span>📍</span>
            <span>{language === 'vi' ? 'Chỉnh sửa nơi xuống tàu' : 'Edit Place Sign On'}</span>
          </button>
          <button
            onClick={() => handleBulkEditDateSignOn()}
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center space-x-2"
          >
            <span>📅</span>
            <span>{language === 'vi' ? 'Chỉnh sửa ngày xuống tàu' : 'Edit Date Sign On'}</span>
          </button>
          <button
            onClick={() => handleBulkEditDateSignOff()}
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center space-x-2"
          >
            <span>📅</span>
            <span>{language === 'vi' ? 'Chỉnh sửa ngày rời tàu' : 'Edit Date Sign Off'}</span>
          </button>
          <div className="border-t border-gray-200 my-1"></div>
          <button
            onClick={handleDeleteCrew}
            className="w-full px-4 py-2 text-left text-sm hover:bg-red-50 text-red-600 flex items-center space-x-2"
          >
            <span>🗑️</span>
            <span>{language === 'vi' ? 'Xóa thuyền viên' : 'Delete Crew Member'}</span>
          </button>
        </div>
      )}
      
      {/* Passport Context Menu */}
      {passportContextMenu.show && (
        <div
          className="fixed bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50 max-h-[80vh] overflow-y-auto"
          style={{
            top: `${passportContextMenu.y}px`,
            left: `${passportContextMenu.x}px`,
            minWidth: '300px'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header - show selection count if multiple selected */}
          {selectedCrewMembers.size > 1 ? (
            <div className="px-4 py-2 text-sm font-semibold text-gray-700 border-b border-gray-200">
              {selectedCrewMembers.size} {language === 'vi' ? 'thuyền viên đã chọn' : 'crew members selected'}
            </div>
          ) : (
            <div className="px-4 py-2 text-sm font-semibold text-gray-700 border-b border-gray-200">
              {passportContextMenu.crew?.full_name} - {passportContextMenu.crew?.passport}
            </div>
          )}
          
          {/* Single crew actions */}
          {selectedCrewMembers.size === 1 && (
            <>
              <button
                onClick={handleViewPassport}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center justify-between"
                disabled={!passportContextMenu.crew?.passport_file_id}
              >
                <div className="flex items-center space-x-2">
                  <span>👁️</span>
                  <span>{language === 'vi' ? 'Xem file hộ chiếu gốc' : 'View Passport File'}</span>
                </div>
                <span>📄</span>
              </button>
              <button
                onClick={handleCopyPassportLink}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center justify-between"
                disabled={!passportContextMenu.crew?.passport_file_id}
              >
                <div className="flex items-center space-x-2">
                  <span>📋</span>
                  <span>{language === 'vi' ? 'Sao chép link file gốc' : 'Copy File Link'}</span>
                </div>
                <span>🔗</span>
              </button>
              <button
                onClick={handleDownloadPassport}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center justify-between"
                disabled={!passportContextMenu.crew?.passport_file_id}
              >
                <div className="flex items-center space-x-2">
                  <span>📥</span>
                  <span>{language === 'vi' ? 'Tải xuống file gốc' : 'Download File'}</span>
                </div>
                <span>💾</span>
              </button>
              <div className="border-t border-gray-200 my-1"></div>
              <button
                onClick={handleAutoRenamePassport}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center justify-between"
                disabled={!passportContextMenu.crew?.passport_file_id}
              >
                <div className="flex items-center space-x-2">
                  <span>⚡</span>
                  <span>{language === 'vi' ? 'Tự động đổi tên file' : 'Auto Rename File'}</span>
                </div>
                <span>⚡</span>
              </button>
            </>
          )}
          
          {/* Bulk actions - show when multiple selected */}
          {selectedCrewMembers.size > 1 && (
            <>
              <button
                onClick={handleBulkViewPassport}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center justify-between"
              >
                <div className="flex items-center space-x-2">
                  <span>👁️</span>
                  <span>{language === 'vi' ? `Xem file (${selectedCrewMembers.size})` : `View Files (${selectedCrewMembers.size})`}</span>
                </div>
                <span>📄</span>
              </button>
              <button
                onClick={handleBulkCopyPassportLink}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center justify-between"
              >
                <div className="flex items-center space-x-2">
                  <span>📋</span>
                  <span>{language === 'vi' ? `Sao chép link (${selectedCrewMembers.size})` : `Copy Links (${selectedCrewMembers.size})`}</span>
                </div>
                <span>🔗</span>
              </button>
              <button
                onClick={handleBulkDownloadPassport}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center justify-between"
              >
                <div className="flex items-center space-x-2">
                  <span>📥</span>
                  <span>{language === 'vi' ? `Tải xuống (${selectedCrewMembers.size})` : `Download Files (${selectedCrewMembers.size})`}</span>
                </div>
                <span>💾</span>
              </button>
              <div className="border-t border-gray-200 my-1"></div>
              <button
                onClick={handleBulkAutoRenamePassport}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center justify-between"
              >
                <div className="flex items-center space-x-2">
                  <span>⚡</span>
                  <span>{language === 'vi' ? `Tự động đổi tên file (${selectedCrewMembers.size})` : `Auto Rename Files (${selectedCrewMembers.size})`}</span>
                </div>
                <span>⚡</span>
              </button>
            </>
          )}
        </div>
      )}
      
      {/* Rank Context Menu */}
      {rankContextMenu.show && (
        <div
          className="fixed bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50 max-h-80 overflow-y-auto"
          style={{
            top: `${rankContextMenu.y}px`,
            left: `${rankContextMenu.x}px`,
            minWidth: '250px'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="px-4 py-2 text-sm font-semibold text-gray-700 border-b border-gray-200">
            {rankContextMenu.crew?.full_name} - {language === 'vi' ? 'Chọn Rank' : 'Select Rank'}
          </div>
          {RANK_OPTIONS.map(rank => (
            <button
              key={rank.value}
              onClick={() => handleUpdateRank(rank.value)}
              className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center justify-between ${
                rankContextMenu.crew?.rank === rank.value ? 'bg-blue-50 text-blue-700' : ''
              }`}
            >
              <span className="flex items-center space-x-2">
                <span className="font-medium">{rank.value}</span>
                <span className="text-gray-600 text-xs">{language === 'vi' ? rank.label_vi : rank.label}</span>
              </span>
              {rankContextMenu.crew?.rank === rank.value && <span>✓</span>}
            </button>
          ))}
        </div>
      )}
      
      {/* Add Crew Modal */}
      {showAddCrewModal && (
        <AddCrewModal
          selectedShip={selectedShip}
          ships={ships}
          isStandbyMode={filters.ship_sign_on === 'Standby'}
          onClose={() => setShowAddCrewModal(false)}
          onSuccess={(crewId) => {
            fetchCrewList();
            toast.success(language === 'vi' 
              ? 'Đã thêm thuyền viên thành công!'
              : 'Crew member added successfully!');
          }}
          onBatchUpload={handleBatchProcessing}
          onShipSelect={(ship) => {
            // Notify parent component to update selected ship
            if (onShipSelect) {
              onShipSelect(ship);
            }
          }}
        />
      )}
      
      {/* Batch Processing Modal */}
      {showBatchProcessingModal && (
        <BatchProcessingModal
          isOpen={showBatchProcessingModal}
          progress={batchProgress}
          fileProgressMap={fileProgressMap}
          fileStatusMap={fileStatusMap}
          fileSubStatusMap={fileSubStatusMap}
          isMinimized={isBatchModalMinimized}
          onMinimize={() => setIsBatchModalMinimized(true)}
          onRestore={() => setIsBatchModalMinimized(false)}
          onRetryFile={handleRetryFailedFile}
          language={language}
          title={language === 'vi' ? 'Đang xử lý Crew List' : 'Processing Crew List'}
        />
      )}
      
      {/* Batch Results Modal */}
      {showBatchResultsModal && (
        <BatchResultsModal
          isOpen={showBatchResultsModal}
          results={batchResults}
          onClose={() => {
            setShowBatchResultsModal(false);
            setBatchResults([]);
          }}
          onRetryFile={handleRetryFailedFile}
          language={language}
        />
      )}
      
      {/* Edit Crew Modal */}
      {showEditCrewModal && selectedCrewForEdit && (
        <EditCrewModal
          crew={selectedCrewForEdit}
          onClose={() => {
            setShowEditCrewModal(false);
            setSelectedCrewForEdit(null);
          }}
          onSuccess={() => {
            fetchCrewList();
            setShowEditCrewModal(false);
            setSelectedCrewForEdit(null);
          }}
          onDelete={(crew) => {
            setCrewToDelete(crew);
            setShowDeleteCrewModal(true);
            setShowEditCrewModal(false);
          }}
        />
      )}
      
      {/* Delete Crew Confirm Modal */}
      {showDeleteCrewModal && crewToDelete && (
        <DeleteCrewConfirmModal
          crew={crewToDelete}
          selectedCount={selectedCrewMembers.size}
          onClose={() => {
            setShowDeleteCrewModal(false);
            setCrewToDelete(null);
          }}
          onConfirm={confirmDeleteCrew}
          isDeleting={isDeleting}
        />
      )}
      
      {/* Bulk Edit Modals */}
      <BulkEditPlaceSignOnModal
        isOpen={showBulkEditPlaceSignOn}
        onClose={() => setShowBulkEditPlaceSignOn(false)}
        value={bulkPlaceSignOn}
        onChange={setBulkPlaceSignOn}
        onSubmit={handleBulkUpdatePlaceSignOn}
        selectedCount={selectedCrewMembers.size}
      />
      
      <BulkEditShipSignOnModal
        isOpen={showBulkEditShipSignOn}
        onClose={() => setShowBulkEditShipSignOn(false)}
        value={bulkShipSignOn}
        onChange={setBulkShipSignOn}
        onSubmit={handleBulkUpdateShipSignOn}
        selectedCount={selectedCrewMembers.size}
        ships={ships}
      />
      
      <BulkEditDateSignOnModal
        isOpen={showBulkEditDateSignOn}
        onClose={() => setShowBulkEditDateSignOn(false)}
        value={bulkDateSignOn}
        onChange={setBulkDateSignOn}
        onSubmit={handleBulkUpdateDateSignOn}
        selectedCount={selectedCrewMembers.size}
      />
      
      <BulkEditDateSignOffModal
        isOpen={showBulkEditDateSignOff}
        onClose={() => setShowBulkEditDateSignOff(false)}
        value={bulkDateSignOff}
        onChange={setBulkDateSignOff}
        onSubmit={handleBulkUpdateDateSignOff}
        selectedCount={selectedCrewMembers.size}
      />
      
      {/* Assignment History Modal */}
      {showHistoryModal && selectedCrewForHistory && (
        <CrewAssignmentHistoryModal
          crew={selectedCrewForHistory}
          onClose={() => {
            setShowHistoryModal(false);
            setSelectedCrewForHistory(null);
          }}
        />
      )}
    </div>
  );
};
