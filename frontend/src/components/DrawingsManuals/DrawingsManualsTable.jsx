/**
 * Drawings & Manuals Table Component
 * Full-featured table with all V1 functionality
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import drawingManualService from '../../services/drawingManualService';
import { formatDateDisplay } from '../../utils/dateHelpers';
import { calculateTooltipPosition, calculateContextMenuPosition } from '../../utils/positionHelpers';
import { 
  estimateFileProcessingTime, 
  startSmoothProgressForFile 
} from '../../utils/progressHelpers';
import { AddDrawingManualModal } from './AddDrawingManualModal';
import { EditDrawingManualModal } from './EditDrawingManualModal';
import { DrawingManualNotesModal } from './DrawingManualNotesModal';
import { BatchProcessingModal } from './BatchProcessingModal';
import { BatchResultsModal } from './BatchResultsModal';

export const DrawingsManualsTable = ({ selectedShip }) => {
  const { language } = useAuth();

  // State
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingDocument, setEditingDocument] = useState(null);
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [notesDocument, setNotesDocument] = useState(null);

  // Batch processing states
  const [isBatchProcessing, setIsBatchProcessing] = useState(false);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });
  const [batchResults, setBatchResults] = useState([]);
  const [showBatchResults, setShowBatchResults] = useState(false);
  const [fileProgressMap, setFileProgressMap] = useState({});
  const [fileStatusMap, setFileStatusMap] = useState({});
  const [fileSubStatusMap, setFileSubStatusMap] = useState({});
  const [isBatchMinimized, setIsBatchMinimized] = useState(false);

  // Selection state
  const [selectedDocuments, setSelectedDocuments] = useState(new Set());

  // Sort state
  const [sort, setSort] = useState({
    column: null,
    direction: 'asc'
  });

  // Filter state
  const [filters, setFilters] = useState({
    status: 'all',
    search: ''
  });

  // Context menu state
  const [contextMenu, setContextMenu] = useState({
    show: false,
    x: 0,
    y: 0,
    document: null
  });

  const [showStatusSubmenu, setShowStatusSubmenu] = useState(false);

  // Note tooltip state
  const [noteTooltip, setNoteTooltip] = useState({
    show: false,
    x: 0,
    y: 0,
    content: '',
    showBelow: false,
    width: 300
  });

  // Fetch documents when ship changes
  useEffect(() => {
    if (selectedShip) {
      fetchDocuments();
    } else {
      setDocuments([]);
    }
  }, [selectedShip]);

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setContextMenu({ show: false, x: 0, y: 0, document: null });
      setShowStatusSubmenu(false);
    };

    if (contextMenu.show) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [contextMenu.show]);

  const fetchDocuments = async () => {
    if (!selectedShip) return;

    try {
      setLoading(true);
      const response = await drawingManualService.getAll(selectedShip.id);
      setDocuments(response.data || []);
    } catch (error) {
      console.error('Failed to fetch drawings & manuals:', error);
      toast.error(language === 'vi' ? 'Không thể tải danh sách tài liệu' : 'Failed to load documents');
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetchDocuments();
      toast.success(language === 'vi' ? '✅ Đã cập nhật danh sách!' : '✅ List updated!');
    } catch (error) {
      toast.error(language === 'vi' ? '❌ Không thể làm mới' : '❌ Failed to refresh');
    } finally {
      setRefreshing(false);
    }
  };

  // Filter and sort documents
  const getFilteredDocuments = () => {
    let filtered = [...documents];

    // Filter by status
    if (filters.status !== 'all') {
      filtered = filtered.filter(doc => 
        doc.status?.toLowerCase() === filters.status.toLowerCase()
      );
    }

    // Filter by search (across multiple columns)
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(doc => 
        doc.document_name?.toLowerCase().includes(searchLower) ||
        doc.document_no?.toLowerCase().includes(searchLower) ||
        doc.approved_by?.toLowerCase().includes(searchLower)
      );
    }

    // Sort
    if (sort.column) {
      filtered.sort((a, b) => {
        let aVal = a[sort.column] || '';
        let bVal = b[sort.column] || '';

        if (sort.column === 'approved_date') {
          aVal = aVal ? new Date(aVal) : new Date(0);
          bVal = bVal ? new Date(bVal) : new Date(0);
        } else {
          aVal = aVal.toString().toLowerCase();
          bVal = bVal.toString().toLowerCase();
        }

        if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  };

  const handleSort = (column) => {
    setSort(prev => ({
      column: column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  // Selection handlers
  const handleSelectDocument = (documentId) => {
    setSelectedDocuments(prev => {
      const newSet = new Set(prev);
      if (newSet.has(documentId)) {
        newSet.delete(documentId);
      } else {
        newSet.add(documentId);
      }
      return newSet;
    });
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      const allIds = new Set(getFilteredDocuments().map(doc => doc.id));
      setSelectedDocuments(allIds);
    } else {
      setSelectedDocuments(new Set());
    }
  };

  const isAllSelected = () => {
    const filtered = getFilteredDocuments();
    return filtered.length > 0 && filtered.every(doc => selectedDocuments.has(doc.id));
  };

  const isIndeterminate = () => {
    const filtered = getFilteredDocuments();
    const selectedCount = filtered.filter(doc => selectedDocuments.has(doc.id)).length;
    return selectedCount > 0 && selectedCount < filtered.length;
  };

  // Note tooltip handlers
  const handleNoteMouseEnter = (e, note) => {
    if (!note) return;

    const rect = e.target.getBoundingClientRect();
    const TOOLTIP_WIDTH = 300;
    const TOOLTIP_MAX_HEIGHT = 200;
    
    const { x, y } = calculateTooltipPosition(rect, TOOLTIP_WIDTH, TOOLTIP_MAX_HEIGHT);

    setNoteTooltip({
      show: true,
      x: x,
      y: y,
      content: note,
      showBelow: false,
      width: TOOLTIP_WIDTH
    });
  };

  const handleNoteMouseLeave = () => {
    setNoteTooltip({
      show: false,
      x: 0,
      y: 0,
      content: '',
      showBelow: false,
      width: 300
    });
  };

  // Context menu handlers
  const handleContextMenu = (e, document) => {
    e.preventDefault();

    const { x, y } = calculateContextMenuPosition(e, 220, 400);

    setContextMenu({
      show: true,
      x: x,
      y: y,
      document: document
    });
  };

  const handleViewFile = (document) => {
    if (document.file_id) {
      window.open(`https://drive.google.com/file/d/${document.file_id}/view`, '_blank');
      toast.success(language === 'vi' ? '📄 Đã mở file' : '📄 File opened');
    } else {
      toast.warning(language === 'vi' ? '⚠️ File chưa được upload' : '⚠️ File not uploaded yet');
    }
    setContextMenu({ show: false, x: 0, y: 0, document: null });
  };

  const handleCopyLink = (document) => {
    if (document.file_id) {
      const link = `https://drive.google.com/file/d/${document.file_id}/view`;
      navigator.clipboard.writeText(link);
      toast.success(language === 'vi' ? '🔗 Đã copy link' : '🔗 Link copied');
    } else {
      toast.warning(language === 'vi' ? '⚠️ File chưa được upload' : '⚠️ File not uploaded yet');
    }
    setContextMenu({ show: false, x: 0, y: 0, document: null });
  };

  const handleDownload = (document) => {
    if (document.file_id) {
      window.open(`https://drive.google.com/uc?export=download&id=${document.file_id}`, '_blank');
      toast.success(language === 'vi' ? '⬇️ Đang tải xuống...' : '⬇️ Downloading...');
    } else {
      toast.warning(language === 'vi' ? '⚠️ File chưa được upload' : '⚠️ File not uploaded yet');
    }
    setContextMenu({ show: false, x: 0, y: 0, document: null });
  };

  const handleChangeStatus = async (document, newStatus) => {
    try {
      await drawingManualService.update(document.id, { status: newStatus });
      toast.success(language === 'vi' ? `✅ Đã đổi trạng thái thành ${newStatus}` : `✅ Status changed to ${newStatus}`);
      await fetchDocuments();
    } catch (error) {
      console.error('Failed to change status:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to change status';
      toast.error(language === 'vi' ? `❌ Không thể đổi trạng thái: ${errorMsg}` : `❌ ${errorMsg}`);
    }
    setContextMenu({ show: false, x: 0, y: 0, document: null });
  };

  const handleDelete = async (document) => {
    if (window.confirm(language === 'vi' 
      ? `Bạn có chắc muốn xóa "${document.document_name}"?`
      : `Are you sure you want to delete "${document.document_name}"?`
    )) {
      try {
        await drawingManualService.delete(document.id, true);

        setSelectedDocuments(prev => {
          const newSet = new Set(prev);
          newSet.delete(document.id);
          return newSet;
        });

        toast.success(language === 'vi' ? '✅ Đã xóa tài liệu' : '✅ Document deleted');
        await fetchDocuments();
      } catch (error) {
        console.error('Failed to delete document:', error);
        const errorMsg = error.response?.data?.detail || 'Failed to delete document';
        toast.error(language === 'vi' ? `❌ Không thể xóa tài liệu: ${errorMsg}` : `❌ ${errorMsg}`);
      }
    }
    setContextMenu({ show: false, x: 0, y: 0, document: null });
  };

  // Bulk actions
  const handleBulkView = () => {
    const selectedDocs = documents.filter(doc => selectedDocuments.has(doc.id));
    const docsWithFiles = selectedDocs.filter(doc => doc.file_id);

    if (docsWithFiles.length === 0) {
      toast.warning(language === 'vi' ? '⚠️ Không có file nào để xem' : '⚠️ No files to view');
    } else {
      docsWithFiles.forEach(doc => {
        window.open(`https://drive.google.com/file/d/${doc.file_id}/view`, '_blank');
      });
      toast.success(language === 'vi' ? `📄 Đã mở ${docsWithFiles.length} file` : `📄 Opened ${docsWithFiles.length} files`);
    }
    setContextMenu({ show: false, x: 0, y: 0, document: null });
  };

  const handleBulkCopyLinks = () => {
    const selectedDocs = documents.filter(doc => selectedDocuments.has(doc.id));
    const docsWithFiles = selectedDocs.filter(doc => doc.file_id);

    if (docsWithFiles.length === 0) {
      toast.warning(language === 'vi' ? '⚠️ Không có file nào để copy link' : '⚠️ No files to copy links');
    } else {
      const links = docsWithFiles.map(doc => `https://drive.google.com/file/d/${doc.file_id}/view`).join('\n');
      navigator.clipboard.writeText(links);
      toast.success(language === 'vi' ? `🔗 Đã copy ${docsWithFiles.length} link` : `🔗 Copied ${docsWithFiles.length} links`);
    }
    setContextMenu({ show: false, x: 0, y: 0, document: null });
  };

  const handleBulkDownload = () => {
    const selectedDocs = documents.filter(doc => selectedDocuments.has(doc.id));
    const docsWithFiles = selectedDocs.filter(doc => doc.file_id);

    if (docsWithFiles.length === 0) {
      toast.warning(language === 'vi' ? '⚠️ Không có file nào để tải' : '⚠️ No files to download');
    } else {
      docsWithFiles.forEach(doc => {
        window.open(`https://drive.google.com/uc?export=download&id=${doc.file_id}`, '_blank');
      });
      toast.success(language === 'vi' ? `⬇️ Đang tải ${docsWithFiles.length} file...` : `⬇️ Downloading ${docsWithFiles.length} files...`);
    }
    setContextMenu({ show: false, x: 0, y: 0, document: null });
  };

  const handleBulkDelete = async () => {
    if (window.confirm(language === 'vi'
      ? `Bạn có chắc muốn xóa ${selectedDocuments.size} tài liệu đã chọn?`
      : `Are you sure you want to delete ${selectedDocuments.size} selected documents?`
    )) {
      try {
        const documentIds = Array.from(selectedDocuments);
        const response = await drawingManualService.bulkDelete(documentIds, true);

        toast.success(language === 'vi' 
          ? `✅ Đã xóa ${response.data.deleted_count} tài liệu` 
          : `✅ Deleted ${response.data.deleted_count} documents`
        );

        setSelectedDocuments(new Set());
        await fetchDocuments();
      } catch (error) {
        console.error('Failed to bulk delete:', error);
        const errorMsg = error.response?.data?.detail || 'Failed to delete documents';
        toast.error(language === 'vi' ? `❌ Không thể xóa tài liệu: ${errorMsg}` : `❌ ${errorMsg}`);
      }
    }
    setContextMenu({ show: false, x: 0, y: 0, document: null });
  };

  // Batch processing handlers
  const handleStartBatchProcessing = async (files) => {
    if (!selectedShip) return;

    setIsBatchProcessing(true);
    setBatchProgress({ current: 0, total: files.length });
    setBatchResults([]);

    // Initialize progress maps
    const initialProgressMap = {};
    const initialStatusMap = {};
    const initialSubStatusMap = {};
    files.forEach(file => {
      initialProgressMap[file.name] = 0;
      initialStatusMap[file.name] = 'waiting';
      initialSubStatusMap[file.name] = null;
    });
    setFileProgressMap(initialProgressMap);
    setFileStatusMap(initialStatusMap);
    setFileSubStatusMap(initialSubStatusMap);

    const results = [];
    const STAGGER_DELAY = 5000; // 5 seconds between file starts

    // Process files with staggered start
    const promises = files.map((file, index) => {
      return new Promise((resolve) => {
        setTimeout(async () => {
          try {
            const result = await processSingleFileInBatch(file);
            results.push(result);
            setBatchProgress({ current: results.length, total: files.length });
            resolve(result);
          } catch (error) {
            const errorResult = {
              filename: file.name,
              success: false,
              error: error.message || 'Processing failed',
              documentCreated: false
            };
            results.push(errorResult);
            setBatchProgress({ current: results.length, total: files.length });
            resolve(errorResult);
          }
        }, index * STAGGER_DELAY);
      });
    });

    // Wait for all files to complete
    await Promise.all(promises);

    // Close batch processing modal
    setIsBatchProcessing(false);

    // Show results modal
    setBatchResults(results);
    setShowBatchResults(true);

    // Refresh list
    await fetchDocuments();

    // Show summary toast
    const successCount = results.filter(r => r.success).length;
    const failCount = results.length - successCount;
    toast.success(
      `${language === 'vi' ? 'Đã xử lý' : 'Processed'} ${results.length} ${language === 'vi' ? 'file' : 'files'}: ` +
      `${successCount} ${language === 'vi' ? 'thành công' : 'success'}, ${failCount} ${language === 'vi' ? 'thất bại' : 'failed'}`
    );
  };

  const processSingleFileInBatch = async (file) => {
    const result = {
      filename: file.name,
      success: false,
      documentCreated: false,
      documentName: '',
      documentNo: '',
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
      // Step 1: Analyze file
      const formData = new FormData();
      formData.append('document_file', file);
      formData.append('ship_id', selectedShip.id);
      formData.append('bypass_validation', 'true');

      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
      const analyzeResponse = await fetch(`${BACKEND_URL}/api/drawings-manuals/analyze-file`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (!analyzeResponse.ok) {
        throw new Error('Analysis failed');
      }

      const data = await analyzeResponse.json();
      
      // Backend returns wrapped response: { success: true/false, analysis: {...} }
      if (!data.success || !data.analysis) {
        throw new Error(data.message || 'Analysis failed');
      }
      
      const analysis = data.analysis;
      result.documentName = analysis.document_name || file.name;
      result.documentNo = analysis.document_no || '';

      // Step 2: Create document record
      const documentData = {
        ship_id: selectedShip.id,
        document_name: analysis.document_name || file.name,
        document_no: analysis.document_no || null,
        approved_by: analysis.approved_by || null,
        approved_date: analysis.approved_date || null,
        status: 'Unknown',
        note: analysis.note || null
      };

      const createResponse = await fetch(`${BACKEND_URL}/api/drawings-manuals`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(documentData)
      });

      if (!createResponse.ok) {
        throw new Error('Failed to create document record');
      }

      const createdDocument = await createResponse.json();
      const documentId = createdDocument.id;
      result.documentCreated = true;
      result.documentId = documentId;

      // Step 3: Upload files to Google Drive
      if (analysis._file_content && analysis._filename) {
        try {
          const uploadData = {
            file_content: analysis._file_content,
            filename: analysis._filename,
            content_type: analysis._content_type || 'application/pdf',
            summary_text: analysis._summary_text || ''
          };

          const uploadResponse = await fetch(`${BACKEND_URL}/api/drawings-manuals/${documentId}/upload-files`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(uploadData)
          });

          if (uploadResponse.ok) {
            result.fileUploaded = true;
            result.success = true;
          } else {
            result.success = true; // Document created but file upload failed (non-critical)
          }
        } catch (uploadError) {
          console.error(`File upload error for document ${documentId}:`, uploadError);
          result.success = true; // Document created successfully, file upload is non-critical
          result.fileUploadError = uploadError.message;
        }
      } else {
        result.success = true; // Document created without file content
      }

      // Success!
      result.success = true;
      progressController.complete(); // Jump to 100%
      setFileStatusMap(prev => ({ ...prev, [file.name]: 'completed' }));

    } catch (error) {
      console.error(`Failed to process ${file.name}:`, error);
      result.error = error.message || 'Processing failed';
      result.success = false;
      progressController.stop();
      setFileStatusMap(prev => ({ ...prev, [file.name]: 'error' }));
    }
    
    // Brief pause before returning
    await new Promise(resolve => setTimeout(resolve, 500));

    return result;
  };

  // Edit handlers
  const handleEditDocument = (document) => {
    setEditingDocument(document);
    setShowEditModal(true);
    setContextMenu({ show: false, x: 0, y: 0, document: null });
  };

  const filteredDocuments = getFilteredDocuments();

  if (!selectedShip) {
    return null;
  }

  return (
    <div>
      {/* Header with title and buttons */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          {language === 'vi' 
            ? `Danh sách Bản vẽ & Sổ tay cho ${selectedShip.name}` 
            : `Drawings & Manuals List for ${selectedShip.name}`}
        </h3>

        <div className="flex gap-3">
          <button
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-green-600 hover:bg-green-700 text-white cursor-pointer transition-all"
            onClick={() => setShowAddModal(true)}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {language === 'vi' ? 'Thêm Bản vẽ/Sổ tay' : 'Add Drawings & Manuals'}
          </button>

          <button
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              refreshing
                ? 'bg-gray-400 cursor-not-allowed text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer'
            }`}
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? (
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            {language === 'vi' ? 'Làm mới' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* ========== FILTERS SECTION ========== */}
      <div className="mb-4 p-4 bg-gray-50 rounded-lg border">
        <div className="flex gap-4 items-center flex-wrap">
          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">
              {language === 'vi' ? 'Trạng thái:' : 'Status:'}
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="border border-gray-300 rounded px-3 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
              <option value="valid">{language === 'vi' ? 'Hợp lệ' : 'Valid'}</option>
              <option value="approved">{language === 'vi' ? 'Đã phê duyệt' : 'Approved'}</option>
              <option value="expired">{language === 'vi' ? 'Hết hạn' : 'Expired'}</option>
              <option value="unknown">{language === 'vi' ? 'Chưa rõ' : 'Unknown'}</option>
            </select>
          </div>

          {/* Search Filter (searches across Document Name, Document No., Approved By) */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">
              {language === 'vi' ? 'Tìm kiếm:' : 'Search:'}
            </label>
            <div className="relative">
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                placeholder={language === 'vi' ? 'Tìm theo tên, số, người phê duyệt...' : 'Search by name, no., approver...'}
                className="border border-gray-300 rounded px-3 py-1 pl-8 text-sm w-64 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <svg 
                className="w-4 h-4 text-gray-400 absolute left-2 top-1/2 transform -translate-y-1/2" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              {filters.search && (
                <button
                  onClick={() => setFilters(prev => ({ ...prev, search: '' }))}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* Results Count - Right Aligned */}
          <div className="ml-auto text-sm text-gray-600">
            {language === 'vi' 
              ? `Hiển thị ${filteredDocuments.length} / ${documents.length} tài liệu`
              : `Showing ${filteredDocuments.length} / ${documents.length} document${documents.length !== 1 ? 's' : ''}`
            }
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={isAllSelected()}
                      ref={el => {
                        if (el) {
                          el.indeterminate = isIndeterminate();
                        }
                      }}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="w-4 h-4 mr-2"
                    />
                    <span>{language === 'vi' ? 'Số TT' : 'No.'}</span>
                  </div>
                </th>
                <th 
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('document_name')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Tên Tài liệu' : 'Document Name'}</span>
                    {sort.column === 'document_name' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>
                <th 
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('document_no')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Số Tài liệu' : 'Document No.'}</span>
                    {sort.column === 'document_no' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>
                <th 
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('approved_by')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Phê duyệt bởi' : 'Approved By'}</span>
                    {sort.column === 'approved_by' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>
                <th 
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('approved_date')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Ngày phê duyệt' : 'Approved Date'}</span>
                    {sort.column === 'approved_date' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>
                <th 
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('status')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Trạng thái' : 'Status'}</span>
                    {sort.column === 'status' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sort.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>
                <th className="border border-gray-300 px-4 py-2 text-center">
                  {language === 'vi' ? 'Ghi chú' : 'Note'}
                </th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <p className="mt-2">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</p>
                  </td>
                </tr>
              ) : filteredDocuments.length === 0 ? (
                <tr>
                  <td colSpan="7" className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                    {documents.length === 0 
                      ? (language === 'vi' ? 'Chưa có tài liệu nào' : 'No documents available')
                      : (language === 'vi' ? 'Không có tài liệu nào phù hợp với bộ lọc' : 'No documents match the current filters')
                    }
                  </td>
                </tr>
              ) : (
                filteredDocuments.map((document, index) => (
                  <tr 
                    key={document.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onContextMenu={(e) => handleContextMenu(e, document)}
                    title={language === 'vi' ? 'Right-click để xem menu' : 'Right-click for menu'}
                  >
                    <td className="border border-gray-300 px-4 py-2">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedDocuments.has(document.id)}
                          onChange={() => handleSelectDocument(document.id)}
                          className="w-4 h-4 mr-3"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <span>{index + 1}</span>
                      </div>
                    </td>
                    <td className="border border-gray-300 px-4 py-2">
                      <div className="flex items-center gap-2">
                        <span>{document.document_name}</span>
                        {document.file_id && (
                          <span 
                            className="text-green-500 text-xs cursor-pointer hover:text-green-600" 
                            title={`${language === 'vi' ? 'File gốc' : 'Original file'}\n📁 ${selectedShip?.name || 'Unknown'}/Class & Flag Cert/Drawings & Manuals`}
                            onClick={(e) => {
                              e.stopPropagation();
                              if (document.file_id) {
                                window.open(`https://drive.google.com/file/d/${document.file_id}/view`, '_blank');
                              }
                            }}
                          >
                            📄
                          </span>
                        )}
                        {document.summary_file_id && (
                          <span 
                            className="text-blue-500 text-xs cursor-pointer hover:text-blue-600" 
                            title={`${language === 'vi' ? 'File tóm tắt' : 'Summary file'}\n📁 ${selectedShip?.name || 'Unknown'}/Class & Flag Cert/Drawings & Manuals`}
                            onClick={(e) => {
                              e.stopPropagation();
                              if (document.summary_file_id) {
                                window.open(`https://drive.google.com/file/d/${document.summary_file_id}/view`, '_blank');
                              }
                            }}
                          >
                            📋
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="border border-gray-300 px-4 py-2 font-mono">{document.document_no || '-'}</td>
                    <td className="border border-gray-300 px-4 py-2">{document.approved_by || '-'}</td>
                    <td className="border border-gray-300 px-4 py-2">{document.approved_date ? formatDateDisplay(document.approved_date) : '-'}</td>
                    <td className="border border-gray-300 px-4 py-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        document.status === 'Valid' ? 'bg-green-100 text-green-800' :
                        document.status === 'Approved' ? 'bg-blue-100 text-blue-800' :
                        document.status === 'Expired' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {document.status}
                      </span>
                    </td>
                    <td className="border border-gray-300 px-4 py-2 text-center">
                      {document.note ? (
                        <span 
                          className="text-red-600 cursor-pointer text-lg font-bold hover:text-red-700 transition-colors"
                          onClick={() => {
                            setNotesDocument(document);
                            setShowNotesModal(true);
                          }}
                          onMouseEnter={(e) => handleNoteMouseEnter(e, document.note)}
                          onMouseLeave={handleNoteMouseLeave}
                          title={language === 'vi' ? 'Click để xem/sửa ghi chú' : 'Click to view/edit note'}
                        >
                          *
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Note Tooltip */}
      {noteTooltip.show && (
        <div
          className="fixed bg-gray-800 text-white p-3 rounded-lg shadow-2xl z-50 border border-gray-600"
          style={{
            left: `${noteTooltip.x}px`,
            top: `${noteTooltip.y}px`,
            width: `${noteTooltip.width}px`,
            maxHeight: '200px',
            overflowY: 'auto',
            fontSize: '14px',
            lineHeight: '1.5'
          }}
        >
          {noteTooltip.content}
        </div>
      )}

      {/* Context Menu */}
      {contextMenu.show && (
        <>
          <div 
            className="fixed inset-0 z-40"
            onClick={() => {
              setContextMenu({ show: false, x: 0, y: 0, document: null });
              setShowStatusSubmenu(false);
            }}
          />
          <div
            className="fixed bg-white shadow-xl rounded-lg border border-gray-200 py-2 z-50"
            style={{ 
              left: `${contextMenu.x}px`,
              top: `${contextMenu.y}px`,
              minWidth: '200px'
            }}
          >
            {/* Multiple selection menu */}
            {selectedDocuments.size > 1 ? (
              <>
                <button
                  onClick={handleBulkView}
                  className="w-full px-4 py-2 text-left hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  {language === 'vi' ? 'Xem Files' : 'View Files'}
                </button>
                <button
                  onClick={handleBulkCopyLinks}
                  className="w-full px-4 py-2 text-left hover:bg-green-50 text-gray-700 hover:text-green-600 transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  {language === 'vi' ? 'Copy Links' : 'Copy Links'}
                </button>
                <button
                  onClick={handleBulkDownload}
                  className="w-full px-4 py-2 text-left hover:bg-purple-50 text-gray-700 hover:text-purple-600 transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  {language === 'vi' ? 'Download Files' : 'Download Files'}
                </button>
                <div className="border-t border-gray-200 my-1"></div>
                <button
                  onClick={handleBulkDelete}
                  className="w-full px-4 py-2 text-left hover:bg-red-50 text-gray-700 hover:text-red-600 transition-all flex items-center gap-2 font-medium"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  {language === 'vi' ? `Xóa ${selectedDocuments.size} mục đã chọn` : `Delete ${selectedDocuments.size} Selected`}
                </button>
              </>
            ) : (
              <>
                {/* Single selection menu */}
                <button
                  onClick={() => handleViewFile(contextMenu.document)}
                  className="w-full px-4 py-2 text-left hover:bg-green-50 text-gray-700 hover:text-green-600 transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  {language === 'vi' ? 'Xem File' : 'View File'}
                </button>
                <button
                  onClick={() => handleCopyLink(contextMenu.document)}
                  className="w-full px-4 py-2 text-left hover:bg-purple-50 text-gray-700 hover:text-purple-600 transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  {language === 'vi' ? 'Copy Link' : 'Copy Link'}
                </button>
                <button
                  onClick={() => handleDownload(contextMenu.document)}
                  className="w-full px-4 py-2 text-left hover:bg-indigo-50 text-gray-700 hover:text-indigo-600 transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  {language === 'vi' ? 'Download' : 'Download'}
                </button>
                
                {/* Change Status with Submenu */}
                <div className="relative">
                  <button
                    onMouseEnter={() => setShowStatusSubmenu(true)}
                    onMouseLeave={() => setShowStatusSubmenu(false)}
                    className="w-full px-4 py-2 text-left hover:bg-orange-50 text-gray-700 hover:text-orange-600 transition-all flex items-center justify-between gap-2"
                  >
                    <div className="flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      {language === 'vi' ? 'Đổi Trạng thái' : 'Change Status'}
                    </div>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                  
                  {/* Status Submenu */}
                  {showStatusSubmenu && (
                    <div
                      className="absolute top-0 bg-white shadow-xl rounded-lg border border-gray-200 py-2 z-50"
                      style={{ 
                        minWidth: '150px',
                        ...(contextMenu.x > window.innerWidth - 400 
                          ? { right: '100%', marginRight: '4px' }
                          : { left: '100%', marginLeft: '4px' })
                      }}
                      onMouseEnter={() => setShowStatusSubmenu(true)}
                      onMouseLeave={() => setShowStatusSubmenu(false)}
                    >
                      <button
                        onClick={() => handleChangeStatus(contextMenu.document, 'Valid')}
                        className="w-full px-4 py-2 text-left hover:bg-green-50 text-gray-700 hover:text-green-600 transition-all flex items-center gap-2"
                      >
                        <span className="w-2 h-2 rounded-full bg-green-500"></span>
                        {language === 'vi' ? 'Hợp lệ' : 'Valid'}
                      </button>
                      <button
                        onClick={() => handleChangeStatus(contextMenu.document, 'Approved')}
                        className="w-full px-4 py-2 text-left hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-all flex items-center gap-2"
                      >
                        <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                        {language === 'vi' ? 'Đã phê duyệt' : 'Approved'}
                      </button>
                      <button
                        onClick={() => handleChangeStatus(contextMenu.document, 'Expired')}
                        className="w-full px-4 py-2 text-left hover:bg-red-50 text-gray-700 hover:text-red-600 transition-all flex items-center gap-2"
                      >
                        <span className="w-2 h-2 rounded-full bg-red-500"></span>
                        {language === 'vi' ? 'Hết hạn' : 'Expired'}
                      </button>
                      <button
                        onClick={() => handleChangeStatus(contextMenu.document, 'Unknown')}
                        className="w-full px-4 py-2 text-left hover:bg-gray-50 text-gray-700 hover:text-gray-600 transition-all flex items-center gap-2"
                      >
                        <span className="w-2 h-2 rounded-full bg-gray-500"></span>
                        {language === 'vi' ? 'Chưa rõ' : 'Unknown'}
                      </button>
                    </div>
                  )}
                </div>
                
                <div className="border-t border-gray-200 my-1"></div>
                
                {/* Edit option - moved above Delete */}
                <button
                  onClick={() => handleEditDocument(contextMenu.document)}
                  className="w-full px-4 py-2 text-left hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  {language === 'vi' ? 'Chỉnh sửa' : 'Edit'}
                </button>
                
                <button
                  onClick={() => handleDelete(contextMenu.document)}
                  className="w-full px-4 py-2 text-left hover:bg-red-50 text-gray-700 hover:text-red-600 transition-all flex items-center gap-2 font-medium"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  {language === 'vi' ? 'Xóa' : 'Delete'}
                </button>
              </>
            )}
          </div>
        </>
      )}

      {/* Modals */}
      <AddDrawingManualModal 
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        selectedShip={selectedShip}
        onDocumentAdded={fetchDocuments}
        onStartBatchProcessing={handleStartBatchProcessing}
      />

      <EditDrawingManualModal 
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setEditingDocument(null);
        }}
        document={editingDocument}
        onDocumentUpdated={fetchDocuments}
      />

      <DrawingManualNotesModal 
        isOpen={showNotesModal}
        onClose={() => {
          setShowNotesModal(false);
          setNotesDocument(null);
        }}
        document={notesDocument}
        onNoteUpdated={fetchDocuments}
      />

      <BatchProcessingModal 
        isOpen={isBatchProcessing}
        progress={batchProgress}
        fileProgressMap={fileProgressMap}
        fileStatusMap={fileStatusMap}
        fileSubStatusMap={fileSubStatusMap}
        isMinimized={isBatchMinimized}
        onToggleMinimize={() => setIsBatchMinimized(!isBatchMinimized)}
      />

      <BatchResultsModal 
        isOpen={showBatchResults}
        onClose={() => setShowBatchResults(false)}
        results={batchResults}
      />
    </div>
  );
};
