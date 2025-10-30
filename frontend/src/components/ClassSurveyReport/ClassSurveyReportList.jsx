/**
 * Class Survey Report List Component
 * Placeholder component for future Class Survey Report functionality
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const ClassSurveyReportList = () => {
  const { language } = useAuth();

  return (
    <div className="bg-white rounded-lg shadow-md p-8 text-center">
      <div className="max-w-md mx-auto">
        {/* Icon */}
        <div className="text-6xl mb-4">📊</div>
        
        {/* Title */}
        <h3 className="text-2xl font-bold text-gray-800 mb-3">
          {language === 'vi' ? 'Class Survey Report' : 'Class Survey Report'}
        </h3>
        
        {/* Placeholder Message */}
        <p className="text-lg text-gray-600 mb-6">
          {language === 'vi' 
            ? 'Nội dung sẽ được bổ sung sau' 
            : 'Content will be added later'}
        </p>
        
        {/* Decorative line */}
        <div className="border-t-2 border-gray-200 pt-6 mt-6">
          <p className="text-sm text-gray-500">
            {language === 'vi' 
              ? 'Tính năng này đang trong quá trình phát triển' 
              : 'This feature is under development'}
          </p>
        </div>
      </div>
    </div>
  );
};
