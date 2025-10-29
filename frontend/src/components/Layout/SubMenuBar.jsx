/**
 * SubMenuBar Component
 * Displays sub-categories for the selected main category
 * Extracted from App.js (lines 13498-13516)
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

// Sub-menu items configuration
const SUB_MENU_ITEMS = {
  crew: [
    { key: 'crew_list', name_vi: 'Danh sách', name_en: 'List' },
    { key: 'crew_passport', name_vi: 'Hộ chiếu', name_en: 'Passport' },
    { key: 'crew_summary', name_vi: 'Tổng hợp', name_en: 'Summary' }
  ],
  ship_certificates: [
    { key: 'cert_list', name_vi: 'Danh sách', name_en: 'List' },
    { key: 'cert_expiring', name_vi: 'Sắp hết hạn', name_en: 'Expiring Soon' },
    { key: 'cert_expired', name_vi: 'Đã hết hạn', name_en: 'Expired' }
  ],
  crew_certificates: [
    { key: 'crew_cert_list', name_vi: 'Danh sách', name_en: 'List' },
    { key: 'crew_cert_expiring', name_vi: 'Sắp hết hạn', name_en: 'Expiring Soon' },
    { key: 'crew_cert_expired', name_vi: 'Đã hết hạn', name_en: 'Expired' }
  ],
  survey_reports: [
    { key: 'survey_list', name_vi: 'Danh sách', name_en: 'List' },
    { key: 'survey_recent', name_vi: 'Gần đây', name_en: 'Recent' }
  ],
  test_reports: [
    { key: 'test_list', name_vi: 'Danh sách', name_en: 'List' },
    { key: 'test_recent', name_vi: 'Gần đây', name_en: 'Recent' }
  ],
  drawings: [
    { key: 'drawing_list', name_vi: 'Danh sách', name_en: 'List' },
    { key: 'manual_list', name_vi: 'Hướng dẫn', name_en: 'Manuals' }
  ],
  other_docs: [
    { key: 'other_list', name_vi: 'Danh sách', name_en: 'List' }
  ],
  mlc: [
    { key: 'mlc_list', name_vi: 'Danh sách', name_en: 'List' }
  ]
};

export const SubMenuBar = ({
  selectedCategory,
  selectedSubMenu,
  onSubMenuChange
}) => {
  const { language } = useAuth();

  // Get sub-menu items for the selected category
  const subMenuItems = SUB_MENU_ITEMS[selectedCategory] || [];

  // Don't render if there are no sub-menu items
  if (subMenuItems.length === 0) {
    return null;
  }

  return (
    <div className="mb-6">
      <div className="grid grid-cols-5 gap-1 w-full">
        {subMenuItems.map((item) => (
          <button
            key={item.key}
            onClick={() => onSubMenuChange(item.key)}
            className={`px-2 py-3 rounded-lg text-sm font-medium transition-all text-center whitespace-nowrap flex-1 ${
              selectedSubMenu === item.key
                ? 'bg-blue-600 text-white shadow-lg transform scale-105'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700 hover:shadow-md hover:transform hover:scale-102'
            }`}
            style={{ minHeight: '48px' }}
          >
            <span className="text-xs leading-tight">
              {language === 'vi' ? item.name_vi : item.name_en}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};
