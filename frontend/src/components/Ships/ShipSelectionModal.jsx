/**
 * Ship Selection Modal Component
 * Reusable modal for selecting ships across multiple pages
 * 
 * Features:
 * - Search functionality (name, IMO, flag)
 * - Alphabetical sorting
 * - Responsive design
 * - Loading states
 * - Empty states
 * - Keyboard support (ESC to close)
 */

import React, { useState, useEffect } from 'react';

const ShipSelectionModal = ({
  isOpen,
  onClose,
  onSelectShip,
  ships = [],
  loading = false,
  language = 'vi',
  currentShipId = null,
  title = null,
  searchPlaceholder = null
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  // Close modal on ESC key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        handleClose();
      }
    };
    
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  // Reset search query when modal opens
  useEffect(() => {
    if (isOpen) {
      setSearchQuery('');
    }
  }, [isOpen]);

  const handleClose = () => {
    setSearchQuery('');
    onClose();
  };

  const handleSelectShip = (ship) => {
    onSelectShip(ship);
    handleClose();
  };

  // Filter and sort ships
  const filteredShips = ships
    .filter(ship => {
      if (!searchQuery.trim()) return true;
      const query = searchQuery.toLowerCase();
      return (
        ship.name?.toLowerCase().includes(query) ||
        ship.imo?.toLowerCase().includes(query) ||
        ship.flag?.toLowerCase().includes(query)
      );
    })
    .sort((a, b) => (a.name || '').localeCompare(b.name || ''));

  if (!isOpen) return null;

  const modalTitle = title || (language === 'vi' ? 'Chọn tàu' : 'Select Ship');
  const searchPlaceholderText = searchPlaceholder || (language === 'vi' ? 'Tìm kiếm tên tàu, IMO...' : 'Search ship name, IMO...');

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" 
      onClick={handleClose}
    >
      <div 
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden" 
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-800">
              {modalTitle}
            </h2>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* Search Field */}
          <div className="relative">
            <input
              type="text"
              placeholder={searchPlaceholderText}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              autoFocus
            />
            <svg
              className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>
        
        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {loading ? (
            // Loading State
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">
                {language === 'vi' ? 'Đang tải...' : 'Loading...'}
              </p>
            </div>
          ) : filteredShips.length === 0 ? (
            // Empty State
            <div className="text-center py-8 text-gray-500">
              <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <p className="text-lg font-medium">
                {language === 'vi' ? 'Không tìm thấy tàu nào' : 'No ships found'}
              </p>
              {searchQuery && (
                <p className="text-sm mt-2">
                  {language === 'vi' ? `Không có kết quả cho "${searchQuery}"` : `No results for "${searchQuery}"`}
                </p>
              )}
            </div>
          ) : (
            // Ship List
            <div className="space-y-2">
              {filteredShips.map(ship => (
                <button
                  key={ship.id}
                  onClick={() => handleSelectShip(ship)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                    currentShipId === ship.id
                      ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="font-semibold text-gray-800 flex items-center gap-2">
                        🚢 {ship.name}
                        {currentShipId === ship.id && (
                          <span className="text-xs bg-blue-500 text-white px-2 py-0.5 rounded-full">
                            {language === 'vi' ? 'Đang chọn' : 'Selected'}
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {ship.imo && `IMO: ${ship.imo}`}
                        {ship.flag && ` • ${language === 'vi' ? 'Cờ' : 'Flag'}: ${ship.flag}`}
                      </div>
                    </div>
                    <svg 
                      className="w-5 h-5 text-gray-400 flex-shrink-0 ml-2" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ShipSelectionModal;
