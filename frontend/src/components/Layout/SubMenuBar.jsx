/**
 * SubMenuBar Component
 * Displays sub-categories for the selected main category
 * Extracted from App.js (lines 13498-13516)
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { SUB_MENU_ITEMS } from '../../utils/constants';

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
            className={`px-2 py-3 rounded-lg font-medium transition-all text-center whitespace-nowrap flex-1 ${
              selectedSubMenu === item.key
                ? 'bg-blue-600 text-white shadow-lg transform scale-105'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700 hover:shadow-md hover:transform hover:scale-102'
            }`}
            style={{ minHeight: '48px' }}
          >
            <span className="text-base leading-tight">
              {language === 'vi' ? item.name_vi : item.name_en}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};
