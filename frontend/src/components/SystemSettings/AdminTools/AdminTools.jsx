/**
 * Admin Tools Component
 * Provides access to administrative tools and utilities
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';

const AdminTools = () => {
  const navigate = useNavigate();
  const { language } = useAuth();

  const tools = [
    {
      id: 'system-audit-logs',
      icon: '📋',
      title: language === 'vi' ? 'System Audit Logs' : 'System Audit Logs',
      description: language === 'vi' 
        ? 'Xem lịch sử thay đổi và hoạt động của tất cả entities trong hệ thống'
        : 'View change history and activity logs for all system entities',
      route: '/system-settings/crew-audit-logs',
      badge: 'Updated',
      color: 'blue'
    },
    {
      id: 'crew-logs',
      icon: '👥',
      title: language === 'vi' ? 'Crew Activity' : 'Crew Activity',
      description: language === 'vi' 
        ? 'Truy cập nhanh logs của Crew'
        : 'Quick access to crew logs',
      route: '/system-settings/crew-audit-logs?entity=crew',
      badge: null,
      color: 'purple'
    },
    {
      id: 'certificate-logs',
      icon: '📜',
      title: language === 'vi' ? 'Certificate Logs' : 'Certificate Logs',
      description: language === 'vi' 
        ? 'Truy cập nhanh logs của Chứng chỉ'
        : 'Quick access to certificate logs',
      route: '/system-settings/crew-audit-logs?entity=certificate',
      badge: 'New',
      color: 'green'
    },
  ];

  const getColorClasses = (color) => {
    const colors = {
      blue: {
        bg: 'bg-blue-50 hover:bg-blue-100',
        icon: 'text-blue-600',
        border: 'border-blue-200 hover:border-blue-300',
        text: 'text-blue-900'
      },
      green: {
        bg: 'bg-green-50 hover:bg-green-100',
        icon: 'text-green-600',
        border: 'border-green-200 hover:border-green-300',
        text: 'text-green-900'
      },
      purple: {
        bg: 'bg-purple-50 hover:bg-purple-100',
        icon: 'text-purple-600',
        border: 'border-purple-200 hover:border-purple-300',
        text: 'text-purple-900'
      },
      orange: {
        bg: 'bg-orange-50 hover:bg-orange-100',
        icon: 'text-orange-600',
        border: 'border-orange-200 hover:border-orange-300',
        text: 'text-orange-900'
      }
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="space-y-4">
      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tools.map((tool) => {
          const colorClasses = getColorClasses(tool.color);
          
          return (
            <button
              key={tool.id}
              onClick={() => navigate(tool.route)}
              className={`
                ${colorClasses.bg} ${colorClasses.border}
                border-2 rounded-xl p-5 text-left
                transition-all duration-200
                hover:shadow-md
                group relative
              `}
            >
              {/* Badge if any */}
              {tool.badge && (
                <span className="absolute top-3 right-3 bg-red-500 text-white text-xs px-2 py-1 rounded-full font-semibold">
                  {tool.badge}
                </span>
              )}

              {/* Icon */}
              <div className={`text-4xl mb-3 ${colorClasses.icon}`}>
                {tool.icon}
              </div>

              {/* Title */}
              <h3 className={`text-lg font-bold mb-2 ${colorClasses.text} group-hover:underline`}>
                {tool.title}
              </h3>

              {/* Description */}
              <p className="text-sm text-gray-600 leading-relaxed">
                {tool.description}
              </p>

              {/* Arrow indicator */}
              <div className={`mt-3 flex items-center text-sm font-semibold ${colorClasses.icon}`}>
                <span>{language === 'vi' ? 'Mở' : 'Open'}</span>
                <svg 
                  className="w-4 h-4 ml-1 transform group-hover:translate-x-1 transition-transform" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </button>
          );
        })}
      </div>

      {/* Info Note */}
      <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl">ℹ️</span>
          <div className="flex-1">
            <p className="text-sm text-gray-700">
              {language === 'vi' 
                ? 'Các công cụ admin giúp bạn quản lý và giám sát hoạt động của hệ thống. Chỉ admin và super admin mới có quyền truy cập.'
                : 'Admin tools help you manage and monitor system activities. Only admins and super admins have access.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminTools;
