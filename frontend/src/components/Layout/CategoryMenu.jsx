/**
 * Category Menu Component
 * Extracted from App.js - Simplified version with navigation
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { MAIN_CATEGORIES } from '../../utils/constants';

export const CategoryMenu = ({
  selectedCategory,
  onCategoryChange,
  onAddRecord
}) => {
  const { language } = useAuth();
  const navigate = useNavigate();

  const handleCategoryClick = (categoryKey) => {
    onCategoryChange(categoryKey);
    
    // Navigate to corresponding page
    const routes = {
      'ship_certificates': '/certificates',
      'crew': '/crew',
      'ism': '/ism',
      'isps': '/isps',
      'mlc': '/mlc',
      'supplies': '/supplies'
    };
    
    if (routes[categoryKey]) {
      navigate(routes[categoryKey]);
    }
  };

  // Get category display name
  const getCategoryName = (category) => {
    return language === 'vi' ? category.name_vi : category.name_en;
  };

  return (
    <div className="space-y-2">
      {/* Categories - Simple buttons */}
      {MAIN_CATEGORIES.map((category) => (
        <button
          key={category.key}
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
      ))}

      {/* Action Button */}
      <div className="mt-6">
        <button
          onClick={onAddRecord}
          className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg transition-all shadow-sm font-medium flex items-center justify-center gap-2"
          style={{
            background: 'linear-gradient(135deg, #48bb78, #38a169)',
            border: '2px solid #2f855a'
          }}
        >
          <span className="text-xl">🚢</span>
          {language === 'vi' ? 'THÊM TÀU MỚI' : 'ADD NEW SHIP'}
        </button>
      </div>
    </div>
  );
};
