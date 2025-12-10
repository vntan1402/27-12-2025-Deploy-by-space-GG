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

  // Filter out dismissed announcements
  const visibleAnnouncements = announcements.filter(
    announcement => !dismissedIds.includes(announcement.id)
  );

  if (visibleAnnouncements.length === 0) {
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
    <div className="space-y-3 mb-6 animate-slideDown">
      {visibleAnnouncements.map((announcement) => {
        const style = getAnnouncementStyle(announcement.type);
        const title = language === 'vi' ? announcement.title_vn : announcement.title_en;
        const content = language === 'vi' ? announcement.content_vn : announcement.content_en;

        return (
          <div
            key={announcement.id}
            className={`${style.bg} ${style.border} border-2 rounded-lg p-4 shadow-md`}
          >
            <div className="flex items-start gap-3">
              {/* Icon */}
              <div className="text-2xl flex-shrink-0 mt-0.5">
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
  );
};

export default AnnouncementBanner;
