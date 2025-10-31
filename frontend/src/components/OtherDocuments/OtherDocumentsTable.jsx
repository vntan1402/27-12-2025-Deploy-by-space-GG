/**
 * Other Documents Table Component
 * Displays list of other documents with filtering, sorting, and context menu
 * 
 * Features:
 * - 5 columns: No., Document Name, Date, Status, Note
 * - Filter by status
 * - Search by document name and note
 * - Sort by Document Name, Date, Status
 * - Context menu: Edit, Change Status (no bulk actions, no AI)
 * - Note tooltip on hover
 * 
 * Simpler than Drawings & Manuals (no AI, no bulk actions, no file management features)
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import otherDocumentService from '../../services/otherDocumentService';
import { formatDateDisplay } from '../../utils/dateHelpers';
import AddOtherDocumentModal from './AddOtherDocumentModal';
import EditOtherDocumentModal from './EditOtherDocumentModal';
import OtherDocumentNotesModal from './OtherDocumentNotesModal';

const OtherDocumentsTable = ({ selectedShip }) => {
  const { language } = useAuth();

  // State
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDocuments, setSelectedDocuments] = useState(new Set());
  
  // Sorting
  const [sortConfig, setSortConfig] = useState({
    column: null,
    direction: 'asc'
  });
  
  // Filtering
  const [filters, setFilters] = useState({
    status: 'all',
    search: ''
  });
  
  // Context Menu
  const [contextMenu, setContextMenu] = useState({
    show: false,
    x: 0,
    y: 0,
    document: null
  });
  const [showStatusSubmenu, setShowStatusSubmenu] = useState(false);
  
  // Note Tooltip
  const [noteTooltip, setNoteTooltip] = useState({
    show: false,
    x: 0,
    y: 0,
    content: ''
  });
  
  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingDocument, setEditingDocument] = useState(null);
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [notesDocument, setNotesDocument] = useState(null);
  
  // Refresh state
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch documents when ship changes
  useEffect(() => {
    if (selectedShip) {
      fetchDocuments();
    } else {
      setDocuments([]);
    }
  }, [selectedShip]);

  // Close context menu on click outside
  useEffect(() => {
    const handleClickOutside = () => {
      if (contextMenu.show) {
        setContextMenu({ show: false, x: 0, y: 0, document: null });
        setShowStatusSubmenu(false);
      }
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
      const data = await otherDocumentService.getAll(selectedShip.id);
      setDocuments(data);
    } catch (error) {
      console.error('Failed to fetch other documents:', error);
      toast.error(language === 'vi' 
        ? 'Không thể tải danh sách tài liệu' 
        : 'Failed to load documents');
    } finally {
      setLoading(false);
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

    // Search in document_name and note
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(doc =>
        doc.document_name?.toLowerCase().includes(searchLower) ||
        doc.note?.toLowerCase().includes(searchLower)
      );
    }

    // Sort
    if (sortConfig.column) {
      filtered.sort((a, b) => {
        let aVal = a[sortConfig.column] || '';
        let bVal = b[sortConfig.column] || '';

        if (sortConfig.column === 'date') {
          aVal = aVal ? new Date(aVal) : new Date(0);
          bVal = bVal ? new Date(bVal) : new Date(0);
        } else {
          aVal = aVal.toString().toLowerCase();
          bVal = bVal.toString().toLowerCase();
        }

        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  };

  // Handle sort
  const handleSort = (column) => {
    setSortConfig(prev => ({
      column: column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  // Handle selection
  const handleSelectDocument = (documentId, checked) => {
    setSelectedDocuments(prev => {
      const newSet = new Set(prev);
      if (checked) {
        newSet.add(documentId);
      } else {
        newSet.delete(documentId);
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

  const handleRowClick = (documentId) => {
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

  const isAllSelected = () => {
    const filtered = getFilteredDocuments();
    return filtered.length > 0 && filtered.every(doc => selectedDocuments.has(doc.id));
  };

  const isIndeterminate = () => {
    const filtered = getFilteredDocuments();
    const selectedCount = filtered.filter(doc => selectedDocuments.has(doc.id)).length;
    return selectedCount > 0 && selectedCount < filtered.length;
  };

  // Handle note click - open modal instead of tooltip
  const handleNoteClick = (document) => {
    setNotesDocument(document);
    setShowNotesModal(true);
  };

  // Handle context menu
  const handleContextMenu = (e, document) => {
    e.preventDefault();
    setContextMenu({
      show: true,
      x: e.clientX,
      y: e.clientY,
      document: document
    });
    setShowStatusSubmenu(true);
  };

  // Handle edit
  const handleEdit = (document) => {
    setEditingDocument(document);
    setShowEditModal(true);
    setContextMenu({ show: false, x: 0, y: 0, document: null });
  };

  // Handle change status
  const handleChangeStatus = async (document, newStatus) => {
    try {
      await otherDocumentService.changeStatus(document.id, newStatus);
      toast.success(language === 'vi' 
        ? 'Đã cập nhật trạng thái' 
        : 'Status updated successfully');
      fetchDocuments();
      setContextMenu({ show: false, x: 0, y: 0, document: null });
      setShowStatusSubmenu(false);
    } catch (error) {
      console.error('Failed to change status:', error);
      toast.error(language === 'vi' 
        ? 'Không thể cập nhật trạng thái' 
        : 'Failed to update status');
    }
  };

  // Handle delete
  const handleDelete = async () => {
    if (selectedDocuments.size === 0) return;

    const confirmMessage = language === 'vi'
      ? `Bạn có chắc muốn xóa ${selectedDocuments.size} tài liệu đã chọn?`
      : `Are you sure you want to delete ${selectedDocuments.size} selected document(s)?`;

    if (!window.confirm(confirmMessage)) return;

    try {
      const deletePromises = Array.from(selectedDocuments).map(id =>
        otherDocumentService.delete(id)
      );

      await Promise.all(deletePromises);

      toast.success(language === 'vi'
        ? `Đã xóa ${selectedDocuments.size} tài liệu`
        : `Deleted ${selectedDocuments.size} document(s)`
      );

      setSelectedDocuments(new Set());
      fetchDocuments();
    } catch (error) {
      console.error('Failed to delete documents:', error);
      toast.error(language === 'vi'
        ? 'Không thể xóa tài liệu'
        : 'Failed to delete documents'
      );
    }
  };

  // Handle refresh
  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      await fetchDocuments();
      toast.success(language === 'vi' 
        ? '✅ Đã cập nhật danh sách!' 
        : '✅ List updated!');
    } catch (error) {
      console.error('Failed to refresh:', error);
      toast.error(language === 'vi' 
        ? '❌ Không thể làm mới danh sách' 
        : '❌ Failed to refresh list');
    } finally {
      setIsRefreshing(false);
    }
  };

  const filteredDocuments = getFilteredDocuments();

  if (!selectedShip) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>{language === 'vi' ? 'Vui lòng chọn tàu' : 'Please select a ship'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with title and action buttons */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800">
          {language === 'vi' ? 'Danh sách Tài liệu Khác' : 'Other Documents List'}
        </h3>

        <div className="flex gap-3">
          {/* Add Button */}
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-green-600 hover:bg-green-700 text-white transition-all"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {language === 'vi' ? 'Thêm Tài liệu' : 'Add Document'}
          </button>

          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white transition-all disabled:bg-gray-400"
          >
            {isRefreshing ? (
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

          {/* Delete Button - Show when items selected */}
          {selectedDocuments.size > 0 && (
            <button
              onClick={handleDelete}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 text-white transition-all"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              {language === 'vi' ? `Xóa (${selectedDocuments.size})` : `Delete (${selectedDocuments.size})`}
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Trạng thái' : 'Status'}
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
              <option value="valid">{language === 'vi' ? 'Hợp lệ' : 'Valid'}</option>
              <option value="expired">{language === 'vi' ? 'Hết hạn' : 'Expired'}</option>
              <option value="unknown">{language === 'vi' ? 'Chưa rõ' : 'Unknown'}</option>
            </select>
          </div>

          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Tìm kiếm' : 'Search'}
            </label>
            <input
              type="text"
              placeholder={language === 'vi' ? 'Tìm theo tên tài liệu...' : 'Search by document name...'}
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Clear Filters Button */}
        {(filters.status !== 'all' || filters.search) && (
          <div className="mt-3 flex justify-end">
            <button
              onClick={() => setFilters({ status: 'all', search: '' })}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-all"
            >
              {language === 'vi' ? 'Xóa bộ lọc' : 'Clear filters'}
            </button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {/* Checkbox Column */}
                <th className="border border-gray-300 px-4 py-2 text-left">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={isAllSelected()}
                      ref={el => {
                        if (el) el.indeterminate = isIndeterminate();
                      }}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="w-4 h-4 mr-2"
                    />
                    <span>{language === 'vi' ? 'Số TT' : 'No.'}</span>
                  </div>
                </th>

                {/* Document Name Column - Sortable */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('document_name')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Tên Tài liệu' : 'Document Name'}</span>
                    {sortConfig.column === 'document_name' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sortConfig.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Date Column - Sortable */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('date')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Ngày' : 'Date'}</span>
                    {sortConfig.column === 'date' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sortConfig.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Status Column - Sortable */}
                <th
                  className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('status')}
                >
                  <div className="flex items-center justify-between">
                    <span>{language === 'vi' ? 'Trạng thái' : 'Status'}</span>
                    {sortConfig.column === 'status' && (
                      <span className="ml-1 text-blue-600 text-sm font-bold">
                        {sortConfig.direction === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                  </div>
                </th>

                {/* Note Column */}
                <th className="border border-gray-300 px-4 py-2 text-center">
                  {language === 'vi' ? 'Ghi chú' : 'Note'}
                </th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="5" className="border border-gray-300 px-4 py-8 text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </td>
                </tr>
              ) : filteredDocuments.length === 0 ? (
                <tr>
                  <td colSpan="5" className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                    {language === 'vi' ? 'Không có tài liệu nào' : 'No documents found'}
                  </td>
                </tr>
              ) : (
                filteredDocuments.map((document, index) => (
                  <tr
                    key={document.id}
                    className={`hover:bg-blue-50 transition-colors ${
                      selectedDocuments.has(document.id) ? 'bg-blue-100' : ''
                    }`}
                    onClick={() => handleRowClick(document.id)}
                  >
                    {/* Checkbox + Row Number */}
                    <td className="border border-gray-300 px-4 py-2">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedDocuments.has(document.id)}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleSelectDocument(document.id, e.target.checked);
                          }}
                          className="w-4 h-4 mr-2"
                        />
                        <span>{index + 1}</span>
                      </div>
                    </td>

                    {/* Document Name with icons */}
                    <td className="border border-gray-300 px-4 py-2">
                      <div className="flex items-center gap-2">
                        {document.document_name}
                        {/* Folder Icon */}
                        {document.folder_link && document.folder_id && (
                          <span
                            className="text-yellow-600 text-sm cursor-pointer hover:text-yellow-700 transition-colors"
                            title={language === 'vi' ? 'Mở folder trên Drive' : 'Open folder on Drive'}
                            onClick={(e) => {
                              e.stopPropagation();
                              window.open(document.folder_link, '_blank');
                            }}
                          >
                            📁
                          </span>
                        )}
                        {/* File Icon */}
                        {!document.folder_link && document.file_ids && document.file_ids.length > 0 && (
                          <span
                            className="text-blue-500 text-xs cursor-pointer hover:text-blue-600"
                            title={language === 'vi' ? 'Xem file' : 'View file'}
                            onClick={(e) => {
                              e.stopPropagation();
                              if (document.file_ids && document.file_ids[0]) {
                                window.open(`https://drive.google.com/file/d/${document.file_ids[0]}/view`, '_blank');
                              }
                            }}
                          >
                            📄
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Date */}
                    <td className="border border-gray-300 px-4 py-2">
                      {document.date ? formatDateDisplay(document.date) : '-'}
                    </td>

                    {/* Status - Right-click for context menu */}
                    <td
                      className="border border-gray-300 px-4 py-2 cursor-context-menu"
                      onContextMenu={(e) => handleContextMenu(e, document)}
                    >
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        document.status === 'Valid' ? 'bg-green-100 text-green-800' :
                        document.status === 'Expired' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {document.status}
                      </span>
                    </td>

                    {/* Note */}
                    <td className="border border-gray-300 px-4 py-2 text-center">
                      {document.note ? (
                        <span
                          className="text-red-600 cursor-help text-lg font-bold"
                          onMouseEnter={(e) => handleNoteMouseEnter(e, document.note)}
                          onMouseLeave={handleNoteMouseLeave}
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
            width: '300px',
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
            {/* Edit Button */}
            <button
              onClick={() => handleEdit(contextMenu.document)}
              className="w-full px-4 py-2 text-left hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-all flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              {language === 'vi' ? 'Chỉnh sửa' : 'Edit'}
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
          </div>
        </>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <AddOtherDocumentModal
          show={showAddModal}
          onClose={() => setShowAddModal(false)}
          selectedShip={selectedShip}
          onSuccess={() => {
            setShowAddModal(false);
            fetchDocuments();
          }}
        />
      )}

      {/* Edit Modal */}
      {showEditModal && editingDocument && (
        <EditOtherDocumentModal
          show={showEditModal}
          onClose={() => {
            setShowEditModal(false);
            setEditingDocument(null);
          }}
          document={editingDocument}
          onSuccess={() => {
            setShowEditModal(false);
            setEditingDocument(null);
            fetchDocuments();
          }}
        />
      )}
    </div>
  );
};

export default OtherDocumentsTable;
