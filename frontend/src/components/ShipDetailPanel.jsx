/**
 * Ship Detail Panel Component
 * Displays ship photo, basic info, and detailed information
 * Extracted from V1 App.js (lines 13060-13400)
 */
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { formatDateDisplay } from '../utils/dateHelpers';

export const ShipDetailPanel = ({ 
  ship, 
  onClose,
  showEditButton = true,
  onEditShip,
  showShipParticular = true 
}) => {
  const { language } = useAuth();
  const [showFullShipInfo, setShowFullShipInfo] = useState(false);

  if (!ship) return null;

  return (
    <div className="grid md:grid-cols-3 gap-6 mb-6">
      {/* Ship Photo - 1/3 width */}
      <div className="md:col-span-1">
        <div className="bg-gray-200 rounded-lg p-4 h-48 flex items-center justify-center">
          <div className="text-center">
            <div className="text-4xl mb-2">🚢</div>
            <p className="font-semibold">SHIP PHOTO</p>
          </div>
        </div>
      </div>
      
      {/* Ship Info - 2/3 width */}
      <div className="md:col-span-2">
        {/* Header with buttons */}
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold text-gray-800">
              {ship.name}
            </h2>
            <div className="flex items-center gap-2">
              {/* Ship Particular Button */}
              {showShipParticular && (
                <button
                  onClick={() => setShowFullShipInfo(!showFullShipInfo)}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-all flex items-center"
                >
                  <span className="mr-1">🚢</span>
                  {language === 'vi' ? 'Thông số kỹ thuật' : 'Ship Particular'}
                  <span className="ml-1 text-xs">
                    {showFullShipInfo ? '▲' : '▼'}
                  </span>
                </button>
              )}
              
              {/* Edit Ship Button */}
              {showEditButton && onEditShip && (
                <button
                  onClick={() => onEditShip(ship)}
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium transition-all flex items-center"
                >
                  <span className="mr-1">✏️</span>
                  {language === 'vi' ? 'Sửa tàu' : 'Edit Ship'}
                </button>
              )}
            </div>
          </div>
          
          {/* Close Button */}
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl px-2 py-1"
              title={language === 'vi' ? 'Đóng chi tiết tàu' : 'Close ship details'}
            >
              ✕
            </button>
          )}
        </div>
        
        {/* Basic Ship Info - 3x3 Grid */}
        <div className="grid grid-cols-3 gap-4 text-sm mb-4">
          <div className="text-base font-bold">
            <span className="font-bold">{language === 'vi' ? 'Tên tàu:' : 'Ship Name:'}</span>
            <span className="ml-2 font-bold">{ship.name}</span>
          </div>
          <div>
            <span className="font-semibold">{language === 'vi' ? 'Tổ chức Phân cấp:' : 'Class Society:'}</span>
            <span className="ml-2">{ship.class_society || '-'}</span>
          </div>
          <div>
            <span className="font-semibold">{language === 'vi' ? 'Cơ:' : 'Flag:'}</span>
            <span className="ml-2">{ship.flag || '-'}</span>
          </div>
          <div>
            <span className="font-semibold">{language === 'vi' ? 'IMO:' : 'IMO:'}</span>
            <span className="ml-2">{ship.imo || '-'}</span>
          </div>
          <div>
            <span className="font-semibold">{language === 'vi' ? 'Năm đóng:' : 'Built Year:'}</span>
            <span className="ml-2">{ship.built_year || '-'}</span>
          </div>
          <div className={`${(ship.ship_owner || '').length > 25 ? 'row-span-2' : ''}`}>
            <span className="font-semibold">{language === 'vi' ? 'Chủ tàu:' : 'Ship Owner:'}</span>
            <span className="ml-2 break-words">{ship.ship_owner || '-'}</span>
          </div>
          <div>
            <span className="font-semibold">{language === 'vi' ? 'Tổng Dung Tích:' : 'Gross Tonnage:'}</span>
            <span className="ml-2">{ship.gross_tonnage?.toLocaleString() || '-'}</span>
          </div>
          <div>
            <span className="font-semibold">{language === 'vi' ? 'Trọng Tải:' : 'Deadweight:'}</span>
            <span className="ml-2">{ship.deadweight?.toLocaleString() || '-'}</span>
          </div>
        </div>

        {/* Detailed Ship Info (Toggle visibility) */}
        {showFullShipInfo && (
          <div className="p-4 bg-gray-50 rounded-lg border">
            <div className="mb-3">
              <h4 className="font-semibold text-gray-700 border-b pb-2">
                {language === 'vi' ? 'Thông tin chi tiết tàu' : 'Detailed Ship Information'}
              </h4>
            </div>
            
            <div className="grid grid-cols-3 gap-6 text-sm">
              {/* Column 1 - Docking Data */}
              <div className="space-y-3">
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Last Docking 1:' : 'Last Docking 1:'}</span>
                  <div className="mt-1">{formatDate(ship.last_docking) || '-'}</div>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Last Docking 2:' : 'Last Docking 2:'}</span>
                  <div className="mt-1">{formatDate(ship.last_docking_2) || '-'}</div>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Next Docking:' : 'Next Docking:'}</span>
                  <div className="mt-1">{formatDate(ship.next_docking) || '-'}</div>
                </div>
              </div>
              
              {/* Column 2 - Special Survey */}
              <div className="space-y-3">
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Chu kỳ Special Survey:' : 'Special Survey Cycle:'}</span>
                  <div className="mt-1">-</div>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Last Special Survey:' : 'Last Special Survey:'}</span>
                  <div className="mt-1">{formatDate(ship.last_special_survey) || '-'}</div>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Last Intermediate:' : 'Last Intermediate:'}</span>
                  <div className="mt-1">{formatDate(ship.last_intermediate_survey) || '-'}</div>
                </div>
              </div>
              
              {/* Column 3 - Anniversary & Compliance */}
              <div className="space-y-3">
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Anniversary Date:' : 'Anniversary Date:'}</span>
                  <div className="mt-1">-</div>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Keel Laid:' : 'Keel Laid:'}</span>
                  <div className="mt-1">{formatDate(ship.keel_laid) || '-'}</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
