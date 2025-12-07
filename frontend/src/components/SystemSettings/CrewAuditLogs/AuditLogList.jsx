/**
 * Audit Log List Component
 * Displays logs grouped by date in timeline format
 */
import React, { useMemo } from 'react';
import { AuditLogCard } from './AuditLogCard';

export const AuditLogList = ({ logs, onViewDetails, language }) => {
  // Group logs by date
  const groupedLogs = useMemo(() => {
    const groups = {};
    
    logs.forEach(log => {
      const date = new Date(log.performed_at);
      const dateKey = date.toDateString();
      
      if (!groups[dateKey]) {
        groups[dateKey] = {
          date: date,
          logs: []
        };
      }
      
      groups[dateKey].logs.push(log);
    });
    
    // Convert to array and sort by date (newest first)
    return Object.values(groups).sort((a, b) => b.date - a.date);
  }, [logs]);

  // Format date header
  const formatDateHeader = (date) => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    const dateStr = date.toDateString();
    const todayStr = today.toDateString();
    const yesterdayStr = yesterday.toDateString();
    
    if (dateStr === todayStr) {
      return language === 'vi' ? 'Hôm nay' : 'Today';
    } else if (dateStr === yesterdayStr) {
      return language === 'vi' ? 'Hôm qua' : 'Yesterday';
    } else {
      return date.toLocaleDateString(language === 'vi' ? 'vi-VN' : 'en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    }
  };

  return (
    <div className="space-y-3">
      {groupedLogs.map((group, index) => (
        <div key={index}>
          {/* Date Header */}
          <div className="flex items-center gap-2 mb-1.5">
            <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-lg font-semibold text-xs">
              📅 {formatDateHeader(group.date)}
            </div>
            <div className="flex-1 h-px bg-gray-200"></div>
          </div>
          
          {/* Logs for this date */}
          <div className="space-y-1.5 ml-1">
            {group.logs.map(log => (
              <AuditLogCard
                key={log.id}
                log={log}
                onViewDetails={onViewDetails}
                language={language}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
