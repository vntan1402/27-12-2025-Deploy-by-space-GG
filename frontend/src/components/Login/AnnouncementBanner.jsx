import React, { useState, useEffect } from 'react';
import systemAnnouncementService from '../../services/systemAnnouncementService';

const AnnouncementBanner = ({ language }) => {
  const [announcements, setAnnouncements] = useState([]);
  const [dismissedIds, setDismissedIds] = useState([]);

  useEffect(() => {
    loadAnnouncements();
    loadDismissedIds();
  }, []);

  const loadAnnouncements = async () => {
    try {
      const data = await systemAnnouncementService.getActiveAnnouncements();
      setAnnouncements(data);
    } catch (error) {
      console.error('Error loading announcements:', error);
      // Fail silently - don't block login page if announcements fail to load
    }
  };

  const loadDismissedIds = () => {
    try {
      const dismissed = localStorage.getItem('dismissed_announcements');
      if (dismissed) {
        setDismissedIds(JSON.parse(dismissed));
      }
    } catch (error) {
      console.error('Error loading dismissed announcements:', error);
    }
  };

  const handleDismiss = (announcementId) => {
    const newDismissed = [...dismissedIds, announcementId];
    setDismissedIds(newDismissed);
    try {
      localStorage.setItem('dismissed_announcements', JSON.stringify(newDismissed));
    } catch (error) {
      console.error('Error saving dismissed announcement:', error);
    }
  };

  const handleRestoreAll = () => {
    setDismissedIds([]);
    try {
      localStorage.removeItem('dismissed_announcements');
    } catch (error) {
      console.error('Error restoring announcements:', error);
    }
  };

  // Filter out dismissed announcements
  const visibleAnnouncements = announcements.filter(
    announcement => !dismissedIds.includes(announcement.id)
  );

  // Count dismissed announcements
  const dismissedCount = announcements.length - visibleAnnouncements.length;

  // Show toggle button if there are dismissed announcements
  if (visibleAnnouncements.length === 0 && dismissedCount === 0) {
    return null;
  }

  const getAnnouncementStyle = (type) => {
    const styles = {
      info: {
        bg: 'bg-blue-50',
        border: 'border-blue-200',
        text: 'text-blue-800',
        icon: 'ℹ️',
        closeHover: 'hover:bg-blue-100'
      },
      warning: {
        bg: 'bg-yellow-50',
        border: 'border-yellow-200',
        text: 'text-yellow-800',
        icon: '⚠️',
        closeHover: 'hover:bg-yellow-100'
      },
      success: {
        bg: 'bg-green-50',
        border: 'border-green-200',
        text: 'text-green-800',
        icon: '✅',
        closeHover: 'hover:bg-green-100'
      },
      error: {
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-red-800',
        icon: '❌',
        closeHover: 'hover:bg-red-100'
      }
    };
    return styles[type] || styles.info;
  };

  return (
    <>
      <style jsx>{`
        @keyframes pulse-border {
          0%, 100% {
            border-color: currentColor;
            box-shadow: 0 0 0 0 currentColor;
          }
          50% {
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3);
          }
        }
        .animate-pulse-border {
          animation: pulse-border 2s ease-in-out infinite;
        }
        @keyframes bounce-bell {
          0%, 100% {
            transform: rotate(0deg);
          }
          10%, 30% {
            transform: rotate(-10deg);
          }
          20%, 40% {
            transform: rotate(10deg);
          }
        }
        .animate-bounce-bell:hover {
          animation: bounce-bell 0.5s ease-in-out;
        }
        @keyframes blink-icon {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.4;
            transform: scale(1.1);
          }
        }
        .animate-blink-icon {
          animation: blink-icon 1.5s ease-in-out infinite;
        }
      `}</style>
      
      <div className="space-y-3 mb-6 relative">
        {/* Toggle Button - Show when there are dismissed announcements */}
        {dismissedCount > 0 && (
          <button
            onClick={handleRestoreAll}
            className="absolute -top-2 -right-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-2 shadow-lg transition-all duration-200 transform hover:scale-110 animate-bounce-bell z-10"
            title={language === 'vi' ? `Hiển thị ${dismissedCount} thông báo đã ẩn` : `Show ${dismissedCount} hidden announcement(s)`}
          >
            <div className="relative">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {/* Badge with count */}
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-bold">
                {dismissedCount}
              </span>
            </div>
          </button>
        )}
        
        <div className="animate-slideDown">
        {visibleAnnouncements.map((announcement) => {
          const style = getAnnouncementStyle(announcement.type);
          const title = language === 'vi' ? announcement.title_vn : announcement.title_en;
          const content = language === 'vi' ? announcement.content_vn : announcement.content_en;

          return (
            <div
              key={announcement.id}
              className={`${style.bg} ${style.border} border-2 rounded-lg p-4 shadow-md animate-pulse-border`}
            >
            <div className="flex items-start gap-3">
              {/* Icon */}
              <div className="text-2xl flex-shrink-0 mt-0.5 animate-blink-icon">
                {style.icon}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <h3 className={`font-semibold ${style.text} text-base mb-1`}>
                  {title}
                </h3>
                <p className={`${style.text} text-sm leading-relaxed whitespace-pre-wrap`}>
                  {content}
                </p>
              </div>

              {/* Close Button */}
              <button
                onClick={() => handleDismiss(announcement.id)}
                className={`flex-shrink-0 ${style.text} ${style.closeHover} rounded-full p-1 transition-colors`}
                aria-label="Close"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          );
        })}
        </div>
      </div>
    </>
  );
};

export default AnnouncementBanner;
