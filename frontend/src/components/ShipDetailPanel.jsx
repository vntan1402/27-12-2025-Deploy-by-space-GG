/**
 * Ship Detail Panel Component
 * Displays ship photo, basic info, and detailed information
 * Extracted from V1 App.js (lines 13060-13400)
 */
import React, { useState } from 'react';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { formatDateDisplay } from '../utils/dateHelpers';
import { shortenClassSociety } from '../utils/shipHelpers';
import { shipService } from '../services';

export const ShipDetailPanel = ({ 
  ship, 
  onClose,
  showEditButton = true,
  onEditShip,
  showShipParticular = true,
  onShipSelect, // New prop for ship selection
  onShipUpdate // Callback to refresh ship data after recalculation
}) => {
  const { language } = useAuth();
  const [showFullShipInfo, setShowFullShipInfo] = useState(false);
  const [isRecalculating, setIsRecalculating] = useState(false);

  if (!ship) return null;

  // Format anniversary date (day + month)
  const formatAnniversaryDate = (anniversaryDate) => {
    if (!anniversaryDate) return '-';
    
    // Handle enhanced anniversary date format
    if (anniversaryDate.day && anniversaryDate.month) {
      const monthNames = [
        '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
      ];
      return `${anniversaryDate.day} ${monthNames[anniversaryDate.month]}`;
    }
    
    // Handle legacy datetime format
    if (typeof anniversaryDate === 'string') {
      try {
        const date = new Date(anniversaryDate);
        const monthNames = [
          '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ];
        return `${date.getDate()} ${monthNames[date.getMonth() + 1]}`;
      } catch {
        return '-';
      }
    }
    
    return '-';
  };

  // Format special survey cycle (date range)
  const formatSpecialSurveyCycle = (specialSurveyCycle) => {
    if (!specialSurveyCycle) return '-';
    
    // Handle enhanced special survey cycle format with dd/MM/yyyy format
    if (specialSurveyCycle.from_date && specialSurveyCycle.to_date) {
      try {
        const fromDate = new Date(specialSurveyCycle.from_date);
        const toDate = new Date(specialSurveyCycle.to_date);
        
        // Format as dd/MM/yyyy
        const formatDate = (date) => {
          const day = String(date.getDate()).padStart(2, '0');
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const year = date.getFullYear();
          return `${day}/${month}/${year}`;
        };
        
        const fromStr = formatDate(fromDate);
        const toStr = formatDate(toDate);
        
        return `${fromStr} - ${toStr}`;
      } catch {
        return '-';
      }
    }
    
    // Handle legacy months format  
    if (typeof specialSurveyCycle === 'number') {
      return `${specialSurveyCycle} ${language === 'vi' ? 'tháng' : 'months'}`;
    }
    
    return '-';
  };

  // Recalculate Next Docking
  const handleRecalculateNextDocking = async () => {
    if (!ship?.id || isRecalculating) return;
    
    setIsRecalculating(true);
    try {
      const result = await shipService.calculateNextDocking(ship.id);
      
      if (result.success) {
        let message = `Next docking calculated: ${result.next_docking.date}`;
        
        if (result.next_docking.last_docking_date) {
          message += `\nBased on last docking: ${result.next_docking.last_docking_date}`;
        }
        
        if (result.next_docking.calculation_method) {
          message += `\nMethod: ${result.next_docking.calculation_method}`;
        }
        
        if (result.next_docking.interval_months) {
          message += `\nInterval: ${result.next_docking.interval_months} months`;
        }
        
        toast.success(message);
        
        // Refresh ship data
        if (onShipUpdate) {
          await onShipUpdate(ship.id);
        }
      } else {
        toast.warning(result.message || 'Unable to calculate next docking date. Last docking date required.');
      }
    } catch (error) {
      console.error('Error recalculating next docking:', error);
      toast.error('Failed to recalculate next docking date');
    } finally {
      setIsRecalculating(false);
    }
  };

  // Recalculate Special Survey Cycle
  const handleRecalculateSpecialSurveyCycle = async () => {
    if (!ship?.id || isRecalculating) return;
    
    setIsRecalculating(true);
    try {
      const result = await shipService.calculateSpecialSurveyCycle(ship.id);
      
      if (result.success) {
        let message = `Special Survey cycle calculated: ${result.special_survey_cycle.display}`;
        message += `\nCycle Type: ${result.special_survey_cycle.cycle_type}`;
        message += `\nIntermediate Survey Required: ${result.special_survey_cycle.intermediate_required ? 'Yes' : 'No'}`;
        
        toast.success(message);
        
        // Refresh ship data
        if (onShipUpdate) {
          await onShipUpdate(ship.id);
        }
      } else {
        toast.warning(result.message || 'Unable to calculate Special Survey cycle from certificates');
      }
    } catch (error) {
      console.error('Error recalculating special survey cycle:', error);
      toast.error('Failed to recalculate special survey cycle');
    } finally {
      setIsRecalculating(false);
    }
  };

  // Recalculate Anniversary Date
  const handleRecalculateAnniversaryDate = async () => {
    if (!ship?.id || isRecalculating) return;
    
    setIsRecalculating(true);
    try {
      const result = await shipService.calculateAnniversaryDate(ship.id);
      
      if (result.success) {
        const message = `Anniversary date calculated: ${result.anniversary_date.display}\nSource: ${result.anniversary_date.source}`;
        toast.success(message);
        
        // Refresh ship data
        if (onShipUpdate) {
          await onShipUpdate(ship.id);
        }
      } else {
        toast.warning(result.message || 'Unable to calculate anniversary date from certificates');
      }
    } catch (error) {
      console.error('Error recalculating anniversary date:', error);
      toast.error('Failed to recalculate anniversary date');
    } finally {
      setIsRecalculating(false);
    }
  };

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
              {/* Ship Select Button */}
              {onShipSelect && (
                <button
                  onClick={onShipSelect}
                  className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-md text-sm font-medium transition-all flex items-center"
                >
                  <span className="mr-1">🚢</span>
                  {language === 'vi' ? 'Chọn tàu' : 'Ship Select'}
                </button>
              )}
              
              {/* Ship Particular Button */}
              {showShipParticular && (
                <button
                  onClick={() => setShowFullShipInfo(!showFullShipInfo)}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-all flex items-center"
                >
                  <span className="mr-1">📋</span>
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
            <span className="font-semibold">{language === 'vi' ? 'Đăng kiểm:' : 'Class Society:'}</span>
            <span className="ml-2">{shortenClassSociety(ship.class_society) || '-'}</span>
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
                  <div className="mt-1">{formatDateDisplay(ship.last_docking) || '-'}</div>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Last Docking 2:' : 'Last Docking 2:'}</span>
                  <div className="mt-1">{formatDateDisplay(ship.last_docking_2) || '-'}</div>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Next Docking:' : 'Next Docking:'}</span>
                  <div className="mt-1 flex items-center space-x-2">
                    <span>{formatDateDisplay(ship.next_docking) || '-'}</span>
                    <button
                      onClick={handleRecalculateNextDocking}
                      disabled={isRecalculating}
                      className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Recalculate based on IMO requirements"
                    >
                      ↻
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Column 2 - Special Survey */}
              <div className="space-y-3">
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Chu kỳ Special Survey:' : 'Special Survey Cycle:'}</span>
                  <div className="mt-1 flex items-center space-x-2">
                    <span>{formatSpecialSurveyCycle(ship.special_survey_cycle) || '-'}</span>
                    <button
                      onClick={handleRecalculateSpecialSurveyCycle}
                      disabled={isRecalculating}
                      className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Recalculate from Full Term certificates"
                    >
                      ↻
                    </button>
                  </div>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Last Special Survey:' : 'Last Special Survey:'}</span>
                  <div className="mt-1">{formatDateDisplay(ship.last_special_survey) || '-'}</div>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Last Intermediate:' : 'Last Intermediate:'}</span>
                  <div className="mt-1">{formatDateDisplay(ship.last_intermediate_survey) || '-'}</div>
                </div>
              </div>
              
              {/* Column 3 - Anniversary & Compliance */}
              <div className="space-y-3">
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Anniversary Date:' : 'Anniversary Date:'}</span>
                  <div className="mt-1 flex items-center space-x-2">
                    <span>{formatAnniversaryDate(ship.anniversary_date) || '-'}</span>
                    {ship.anniversary_date?.manual_override && (
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">Manual</span>
                    )}
                    {ship.anniversary_date?.auto_calculated && (
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">Auto</span>
                    )}
                    <button
                      onClick={handleRecalculateAnniversaryDate}
                      disabled={isRecalculating}
                      className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Recalculate from certificates"
                    >
                      ↻
                    </button>
                  </div>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Keel Laid:' : 'Keel Laid:'}</span>
                  <div className="mt-1">{formatDateDisplay(ship.keel_laid) || '-'}</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
