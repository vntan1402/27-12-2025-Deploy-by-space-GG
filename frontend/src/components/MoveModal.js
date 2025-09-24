import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

// Tree node component for folder structure
const FolderTreeNode = ({ 
  folder, 
  children = [], 
  level = 0, 
  isSelected, 
  onSelect, 
  isExpanded, 
  onToggleExpand,
  hasChildren 
}) => {
  return (
    <div className="folder-tree-node">
      <div
        className={`flex items-center p-2 cursor-pointer transition-colors rounded-md ${
          isSelected 
            ? 'bg-blue-50 border border-blue-200 text-blue-800' 
            : 'hover:bg-gray-50'
        }`}
        style={{ paddingLeft: `${level * 20 + 12}px` }}
        onClick={() => onSelect(folder)}
      >
        {/* Expand/Collapse Icon */}
        {hasChildren && (
          <button
            className="flex-shrink-0 mr-2 p-1 hover:bg-gray-200 rounded"
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand(folder.folder_id);
            }}
          >
            <svg 
              className={`w-3 h-3 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </button>
        )}
        
        {/* Radio Button */}
        <div className="flex-shrink-0 mr-3">
          <div className={`w-4 h-4 rounded-full border-2 ${
            isSelected
              ? 'bg-blue-600 border-blue-600'
              : 'border-gray-300'
          }`}>
            {isSelected && (
              <div className="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
            )}
          </div>
        </div>

        {/* Folder Icon */}
        <svg className="w-4 h-4 text-yellow-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
        </svg>

        {/* Folder Name */}
        <span className={`font-medium flex-1 ${isSelected ? 'text-blue-800' : 'text-gray-900'}`}>
          {folder.folder_name}
        </span>
      </div>

      {/* Children */}
      {hasChildren && isExpanded && children.length > 0 && (
        <div className="folder-children">
          {children}
        </div>
      )}
    </div>
  );
};

const MoveModal = ({ 
  isOpen, 
  onClose, 
  selectedCertificates, 
  contextMenuCertificate, 
  selectedShip, 
  language, 
  API, 
  token,
  onMoveComplete,
  availableCompanies = []
}) => {
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [moving, setMoving] = useState(false);
  const [expandedFolders, setExpandedFolders] = useState(new Set());

  // Get certificates to move
  const certificatesToMove = selectedCertificates.size > 0 
    ? Array.from(selectedCertificates)
    : (contextMenuCertificate ? [contextMenuCertificate.id] : []);

  // Get company ID from company name
  const getCompanyId = () => {
    if (!selectedShip?.company || !availableCompanies.length) return null;
    const company = availableCompanies.find(c => 
      c.name_en === selectedShip.company || 
      c.name_vn === selectedShip.company ||
      c.name === selectedShip.company
    );
    return company?.id;
  };

  // Fetch folder structure when modal opens
  useEffect(() => {
    if (isOpen && selectedShip) {
      fetchFolders();
    }
  }, [isOpen, selectedShip]);

  // Auto-expand main categories when folders load
  useEffect(() => {
    if (folders.length > 0) {
      const mainCategories = folders
        .filter(f => f.level === 1)
        .map(f => f.folder_id);
      setExpandedFolders(new Set(mainCategories));
    }
  }, [folders]);

  const fetchFolders = async () => {
    setLoading(true);
    try {
      const companyId = getCompanyId();
      console.log('MoveModal fetchFolders called');
      console.log('selectedShip:', selectedShip);
      console.log('availableCompanies:', availableCompanies);
      console.log('computed companyId:', companyId);
      
      if (!companyId) {
        console.error('Company ID not found for ship company:', selectedShip.company);
        toast.error(language === 'vi' ? 'Không tìm thấy thông tin công ty' : 'Company information not found');
        setLoading(false);
        return;
      }

      console.log('Making API call to:', `${API}/companies/${companyId}/gdrive/folders?ship_name=${encodeURIComponent(selectedShip.name)}`);
      
      const response = await axios.get(
        `${API}/companies/${companyId}/gdrive/folders?ship_name=${encodeURIComponent(selectedShip.name)}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      console.log('API response:', response.data);

      if (response.data.success) {
        setFolders(response.data.folders);
        console.log('Folders set successfully:', response.data.folders.length, 'folders');
      } else {
        console.error('API returned success=false:', response.data);
        toast.error(language === 'vi' ? 'Không thể tải thư mục' : 'Failed to load folders');
      }
    } catch (error) {
      console.error('Error fetching folders:', error);
      toast.error(language === 'vi' ? 'Lỗi khi tải thư mục' : 'Error loading folders');
    } finally {
      setLoading(false);
    }
  };

  const toggleFolderExpand = (folderId) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folderId)) {
      newExpanded.delete(folderId);
    } else {
      newExpanded.add(folderId);
    }
    setExpandedFolders(newExpanded);
  };

  // Build tree structure from flat folder list
  const buildFolderTree = () => {
    // Group folders by level and parent
    const folderMap = new Map();
    const rootFolders = [];
    
    folders.forEach(folder => {
      folderMap.set(folder.folder_id, { ...folder, children: [] });
    });

    folders.forEach(folder => {
      if (folder.level === 0) {
        // Root ship folder
        rootFolders.push(folderMap.get(folder.folder_id));
      } else if (folder.level === 1) {
        // Main categories under ship
        const shipFolder = folders.find(f => f.level === 0);
        if (shipFolder && folderMap.has(shipFolder.folder_id)) {
          folderMap.get(shipFolder.folder_id).children.push(folderMap.get(folder.folder_id));
        }
      } else if (folder.level === 2) {
        // Subcategories
        const parentFolder = folders.find(f => f.folder_id === folder.parent_id);
        if (parentFolder && folderMap.has(parentFolder.folder_id)) {
          folderMap.get(parentFolder.folder_id).children.push(folderMap.get(folder.folder_id));
        }
      }
    });

    return rootFolders;
  };

  // Render tree recursively
  const renderFolderTree = (folderNodes, level = 0) => {
    return folderNodes.map(folder => {
      const hasChildren = folder.children && folder.children.length > 0;
      const isExpanded = expandedFolders.has(folder.folder_id);
      const isSelected = selectedFolder?.folder_id === folder.folder_id;

      return (
        <FolderTreeNode
          key={folder.folder_id}
          folder={folder}
          level={level}
          isSelected={isSelected}
          onSelect={setSelectedFolder}
          hasChildren={hasChildren}
          isExpanded={isExpanded}
          onToggleExpand={toggleFolderExpand}
          children={hasChildren ? renderFolderTree(folder.children, level + 1) : []}
        />
      );
    });
  };

  const handleMove = async () => {
    if (!selectedFolder || certificatesToMove.length === 0) {
      toast.error(language === 'vi' ? 'Vui lòng chọn thư mục đích' : 'Please select a destination folder');
      return;
    }

    const companyId = getCompanyId();
    if (!companyId) {
      toast.error(language === 'vi' ? 'Không tìm thấy thông tin công ty' : 'Company information not found');
      return;
    }

    setMoving(true);
    try {
      const movePromises = certificatesToMove.map(async (certId) => {
        // First, get the certificate details to find its Google Drive file ID
        const certResponse = await axios.get(`${API}/certificates/${certId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const certificate = certResponse.data;
        if (!certificate.google_drive_file_id) {
          throw new Error(`Certificate ${certificate.certificate_name} has no Google Drive file ID`);
        }

        // Move the file using the Google Drive API
        return axios.post(
          `${API}/companies/${companyId}/gdrive/move-file`,
          {
            file_id: certificate.google_drive_file_id,
            target_folder_id: selectedFolder.folder_id
          },
          {
            headers: { 'Authorization': `Bearer ${token}` }
          }
        );
      });

      await Promise.all(movePromises);
      
      toast.success(
        language === 'vi' 
          ? `Đã di chuyển ${certificatesToMove.length} chứng chỉ thành công!`
          : `Successfully moved ${certificatesToMove.length} certificate(s)!`
      );
      
      onMoveComplete();
    } catch (error) {
      console.error('Error moving certificates:', error);
      toast.error(
        language === 'vi' 
          ? 'Lỗi khi di chuyển chứng chỉ' 
          : 'Error moving certificates'
      );
    } finally {
      setMoving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="space-y-4">
      {/* Folder Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          {language === 'vi' ? 'Chọn thư mục đích:' : 'Select destination folder:'}
        </label>
        
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">
              {language === 'vi' ? 'Đang tải thư mục...' : 'Loading folders...'}
            </span>
          </div>
        ) : folders.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📁</div>
            <p>{language === 'vi' ? 'Không tìm thấy thư mục nào' : 'No folders found'}</p>
            <button 
              onClick={fetchFolders}
              className="mt-2 text-blue-600 hover:text-blue-800 text-sm"
            >
              {language === 'vi' ? 'Thử lại' : 'Retry'}
            </button>
          </div>
        ) : (
          <div className="max-h-80 overflow-y-auto border border-gray-300 rounded-lg p-2">
            <div className="folder-tree">
              {buildFolderTree().length > 0 ? (
                renderFolderTree(buildFolderTree())
              ) : (
                <div className="text-center py-4 text-gray-500">
                  <div className="text-2xl mb-2">📁</div>
                  <p className="text-sm">
                    {language === 'vi' 
                      ? 'Không có cấu trúc thư mục' 
                      : 'No folder structure available'
                    }
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Selected folder info */}
      {selectedFolder && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-4">
          <h4 className="font-medium text-blue-900 mb-2 flex items-center">
            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
            </svg>
            {language === 'vi' ? 'Thư mục đích:' : 'Destination folder:'}
          </h4>
          <p className="text-sm text-blue-700 font-medium">
            {selectedFolder.folder_name}
          </p>
          {selectedFolder.folder_path && (
            <p className="text-xs text-blue-600 mt-1">
              📍 {selectedFolder.folder_path}
            </p>
          )}
        </div>
      )}

      {/* Selected certificates info */}
      {certificatesToMove.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">
            {language === 'vi' ? 'Chứng chỉ được chọn:' : 'Selected certificates:'}
          </h4>
          <p className="text-sm text-gray-600">
            {certificatesToMove.length} {language === 'vi' ? 'chứng chỉ' : 'certificate(s)'}
          </p>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
        <button
          onClick={onClose}
          disabled={moving}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all disabled:opacity-50"
        >
          {language === 'vi' ? 'Hủy' : 'Cancel'}
        </button>
        <button
          onClick={handleMove}
          disabled={!selectedFolder || certificatesToMove.length === 0 || moving}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center"
        >
          {moving && (
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
          )}
          {moving 
            ? (language === 'vi' ? 'Đang di chuyển...' : 'Moving...') 
            : (language === 'vi' ? 'Di chuyển' : 'Move')
          }
        </button>
      </div>
    </div>
  );
};

export default MoveModal;