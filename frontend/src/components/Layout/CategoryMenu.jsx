import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

// Main categories configuration
const MAIN_CATEGORIES = [
  {
    key: 'crew',
    name_vi: 'Thông tin Thuyền viên',
    name_en: 'Crew Information',
    icon: '👥'
  },
  {
    key: 'ship_certificates',
    name_vi: 'Chứng chỉ Tàu',
    name_en: 'Ship Certificates',
    icon: '📜'
  },
  {
    key: 'crew_certificates',
    name_vi: 'Chứng chỉ Thuyền viên',
    name_en: 'Crew Certificates',
    icon: '🎓'
  },
  {
    key: 'survey_reports',
    name_vi: 'Báo cáo Khảo sát',
    name_en: 'Survey Reports',
    icon: '📋'
  },
  {
    key: 'test_reports',
    name_vi: 'Báo cáo Thử nghiệm',
    name_en: 'Test Reports',
    icon: '🧪'
  },
  {
    key: 'drawings',
    name_vi: 'Bản vẽ & Hướng dẫn',
    name_en: 'Drawings & Manuals',
    icon: '📊'
  },
  {
    key: 'other_docs',
    name_vi: 'Tài liệu khác',
    name_en: 'Other Documents',
    icon: '📄'
  },
  {
    key: 'mlc',
    name_vi: 'MLC',
    name_en: 'MLC Documents',
    icon: '⚓'
  }
];

/**
 * CategoryMenu Component
 * Displays main categories with ship selection on hover
 * 
 * @param {Object} props
 * @param {string} props.selectedCategory - Currently selected category
 * @param {Function} props.onCategoryChange - Callback when category changes
 * @param {Array} props.ships - List of ships
 * @param {Function} props.onShipSelect - Callback when ship is selected
 * @param {Function} props.onAddRecord - Callback for add record action
 */
export const CategoryMenu = ({
  selectedCategory,
  onCategoryChange,
  ships = [],
  onShipSelect,
  onAddRecord
}) => {
  const { language } = useAuth();
  const [hoveredCategory, setHoveredCategory] = useState(null);

  const handleCategoryMouseEnter = (categoryKey) => {
    setHoveredCategory(categoryKey);
  };

  const handleCategoryMouseLeave = () => {
    setHoveredCategory(null);
  };

  const handleCategoryClick = (categoryKey) => {
    onCategoryChange(categoryKey);
    setHoveredCategory(null);
  };

  const handleShipClick = (ship, categoryKey) => {
    onShipSelect(ship);
    onCategoryChange(categoryKey);
    setHoveredCategory(null);
  };

  // Get category display name
  const getCategoryName = (category) => {
    return language === 'vi' ? category.name_vi : category.name_en;
  };

  return (
    <div className="space-y-2">
      {/* Categories */}
      {MAIN_CATEGORIES.map((category) => (
        <div
          key={category.key}
          className="relative"
          onMouseEnter={() => handleCategoryMouseEnter(category.key)}
          onMouseLeave={handleCategoryMouseLeave}
        >
          <button
            onClick={() => handleCategoryClick(category.key)}
            className={`w-full text-left p-3 rounded-lg transition-all border-2 text-white font-medium hover:scale-102 ${
              selectedCategory === category.key
                ? 'bg-gradient-to-r from-blue-400 to-indigo-500 border-blue-300 ring-2 ring-blue-200 shadow-lg'
                : 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-400 hover:to-indigo-500 border-blue-400 shadow-md'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">{category.icon}</span>
                <span className="text-sm">{getCategoryName(category)}</span>
              </div>
              {selectedCategory === category.key && (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </div>
          </button>

          {/* Ships list - inline expansion on hover */}
          {hoveredCategory === category.key && ships.length > 0 && (
            <div className="absolute left-0 right-0 mt-2 bg-white border-2 border-blue-200 rounded-lg shadow-2xl p-3 text-gray-800 z-50">
              <h4 className="font-semibold text-gray-700 mb-2 text-sm flex items-center gap-2">
                <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
                </svg>
                {language === 'vi' ? 'Danh sách tàu' : 'Ships List'}
              </h4>

              <div className="space-y-2 max-h-64 overflow-y-auto">
                {ships.slice(0, 8).map((ship) => (
                  <button
                    key={ship.id}
                    onClick={() => handleShipClick(ship, category.key)}
                    className="block w-full text-left p-2 rounded-md hover:bg-blue-50 transition-all text-sm border border-gray-100 hover:border-blue-300 hover:shadow-md"
                  >
                    <div className="font-medium text-gray-800 flex items-center gap-2">
                      <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {ship.name}
                    </div>
                    <div className="text-xs text-gray-500 ml-6 mt-1">
                      {ship.flag} • {ship.class_society || 'N/A'}
                    </div>
                  </button>
                ))}
              </div>

              {ships.length > 8 && (
                <div className="text-center pt-2 border-t border-gray-200 mt-2">
                  <span className="text-xs text-gray-500 font-medium">
                    {language === 'vi'
                      ? `+${ships.length - 8} tàu khác`
                      : `+${ships.length - 8} more ships`
                    }
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      ))}

      {/* Action Buttons */}
      <div className="mt-6 space-y-2">
        <button
          onClick={onAddRecord}
          className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white py-3 px-4 rounded-lg transition-all shadow-md hover:shadow-lg font-semibold flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          {language === 'vi' ? 'THÊM TÀU MỚI' : 'ADD NEW SHIP'}
        </button>
      </div>
    </div>
  );
};
