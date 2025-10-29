/**
 * Category Menu Component
 * Extracted from App.js (lines 12933-13050)
 */
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
            className={`w-full text-left p-3 rounded-lg transition-all border text-white font-medium ${
              selectedCategory === category.key
                ? 'bg-blue-400 border-blue-300 ring-2 ring-blue-200'
                : 'bg-blue-500 hover:bg-blue-400 border-blue-400'
            }`}
            style={{
              background: selectedCategory === category.key
                ? 'linear-gradient(135deg, #60a5fa, #3b82f6)'
                : 'linear-gradient(135deg, #4a90e2, #357abd)',
              border: selectedCategory === category.key
                ? '2px solid #93c5fd'
                : '2px solid #2c5282'
            }}
          >
            <span className="mr-3">{category.icon}</span>
            {getCategoryName(category)}
            {selectedCategory === category.key && (
              <span className="float-right">✓</span>
            )}
          </button>

          {/* Ships list - inline expansion on hover */}
          {hoveredCategory === category.key && ships.length > 0 && (
            <div className="mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-gray-800">
              <h4 className="font-medium text-gray-700 mb-2 text-sm">
                {language === 'vi' ? 'Danh sách tàu' : 'Ships List'}
              </h4>

              <div className="space-y-2">
                {ships.slice(0, 5).map((ship) => (
                  <button
                    key={ship.id}
                    onClick={() => handleShipClick(ship, category.key)}
                    className="block w-full text-left p-2 rounded hover:bg-blue-50 transition-all text-sm border border-gray-100 hover:border-blue-200"
                  >
                    <div className="font-medium text-gray-800">{ship.name}</div>
                    <div className="text-xs text-gray-500">
                      {ship.flag} • {ship.class_society}
                    </div>
                  </button>
                ))}
              </div>

              {ships.length > 5 && (
                <div className="text-center pt-2 border-t border-gray-100 mt-2">
                  <span className="text-xs text-gray-500">
                    {language === 'vi'
                      ? `+${ships.length - 5} tàu khác`
                      : `+${ships.length - 5} more ships`
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
          className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg transition-all shadow-sm font-medium"
          style={{
            background: 'linear-gradient(135deg, #48bb78, #38a169)',
            border: '2px solid #2f855a'
          }}
        >
          {language === 'vi' ? 'THÊM TÀU MỚI' : 'ADD NEW SHIP'}
        </button>
      </div>
    </div>
  );
};
