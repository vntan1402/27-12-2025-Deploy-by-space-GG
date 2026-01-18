import React, { useState, useEffect } from 'react';
import { X, Minimize2, Maximize2, CheckCircle, XCircle, Loader2, FileText } from 'lucide-react';

/**
 * Floating Progress Component for Background Tasks
 * Shows progress in a floating card that doesn't block UI
 */
const FloatingProgress = ({
  isVisible,
  title,
  completed,
  total,
  currentFile,
  errors = [],
  status, // 'processing', 'completed', 'completed_with_errors', 'failed'
  onClose,
  onMinimize,
  language = 'vi'
}) => {
  const [isMinimized, setIsMinimized] = useState(false);
  const [position, setPosition] = useState({ x: 20, y: 20 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  // Calculate progress percentage
  const progressPercent = total > 0 ? Math.round((completed / total) * 100) : 0;
  
  // Determine if task is done
  const isDone = status === 'completed' || status === 'completed_with_errors' || status === 'failed';

  // Handle drag start
  const handleMouseDown = (e) => {
    if (e.target.closest('.drag-handle')) {
      setIsDragging(true);
      setDragOffset({
        x: e.clientX - position.x,
        y: e.clientY - position.y
      });
    }
  };

  // Handle drag move
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isDragging) {
        setPosition({
          x: Math.max(0, Math.min(window.innerWidth - 320, e.clientX - dragOffset.x)),
          y: Math.max(0, Math.min(window.innerHeight - 200, e.clientY - dragOffset.y))
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragOffset]);

  // Auto-close after completion (optional - can be disabled)
  useEffect(() => {
    if (isDone && completed > 0 && errors.length === 0) {
      const timer = setTimeout(() => {
        onClose?.();
      }, 5000); // Auto close after 5 seconds if all successful
      return () => clearTimeout(timer);
    }
  }, [isDone, completed, errors.length, onClose]);

  if (!isVisible) return null;

  // Status icon and color
  const getStatusInfo = () => {
    if (status === 'completed') {
      return { icon: CheckCircle, color: 'text-green-500', bgColor: 'bg-green-50' };
    } else if (status === 'completed_with_errors') {
      return { icon: CheckCircle, color: 'text-yellow-500', bgColor: 'bg-yellow-50' };
    } else if (status === 'failed') {
      return { icon: XCircle, color: 'text-red-500', bgColor: 'bg-red-50' };
    }
    return { icon: Loader2, color: 'text-blue-500', bgColor: 'bg-blue-50' };
  };

  const statusInfo = getStatusInfo();
  const StatusIcon = statusInfo.icon;

  // Minimized view
  if (isMinimized) {
    return (
      <div
        className="fixed z-50 cursor-move"
        style={{ right: '20px', bottom: '20px' }}
      >
        <div 
          className={`flex items-center gap-2 px-4 py-2 rounded-full shadow-lg ${statusInfo.bgColor} border border-gray-200`}
          onClick={() => setIsMinimized(false)}
        >
          <StatusIcon className={`w-5 h-5 ${statusInfo.color} ${!isDone ? 'animate-spin' : ''}`} />
          <span className="text-sm font-medium">
            {isDone 
              ? `${completed}/${total} ${language === 'vi' ? 'hoàn thành' : 'done'}`
              : `${completed}/${total}`
            }
          </span>
          <Maximize2 className="w-4 h-4 text-gray-500 hover:text-gray-700 cursor-pointer" />
        </div>
      </div>
    );
  }

  // Full view
  return (
    <div
      className="fixed z-50"
      style={{ 
        right: '20px',
        bottom: '20px',
        width: '320px'
      }}
      onMouseDown={handleMouseDown}
    >
      <div className={`rounded-lg shadow-xl border ${statusInfo.bgColor} border-gray-200 overflow-hidden`}>
        {/* Header - Draggable */}
        <div className="drag-handle flex items-center justify-between px-4 py-2 bg-white border-b cursor-move">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-gray-600" />
            <span className="font-medium text-sm text-gray-800">{title}</span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsMinimized(true)}
              className="p-1 hover:bg-gray-100 rounded"
              title={language === 'vi' ? 'Thu nhỏ' : 'Minimize'}
            >
              <Minimize2 className="w-4 h-4 text-gray-500" />
            </button>
            {isDone && (
              <button
                onClick={onClose}
                className="p-1 hover:bg-gray-100 rounded"
                title={language === 'vi' ? 'Đóng' : 'Close'}
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="p-4 bg-white">
          {/* Progress bar */}
          <div className="mb-3">
            <div className="flex justify-between text-xs text-gray-600 mb-1">
              <span>{language === 'vi' ? 'Tiến độ' : 'Progress'}</span>
              <span>{completed}/{total} ({progressPercent}%)</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  status === 'failed' ? 'bg-red-500' :
                  status === 'completed_with_errors' ? 'bg-yellow-500' :
                  status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
                }`}
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Current file / Status */}
          <div className="flex items-center gap-2 text-sm">
            <StatusIcon className={`w-4 h-4 ${statusInfo.color} ${!isDone ? 'animate-spin' : ''}`} />
            <span className="text-gray-600 truncate">
              {isDone ? (
                status === 'completed' ? (
                  language === 'vi' ? '✅ Hoàn thành!' : '✅ Completed!'
                ) : status === 'completed_with_errors' ? (
                  language === 'vi' ? `⚠️ Hoàn thành với ${errors.length} lỗi` : `⚠️ Completed with ${errors.length} errors`
                ) : (
                  language === 'vi' ? '❌ Thất bại' : '❌ Failed'
                )
              ) : (
                currentFile || (language === 'vi' ? 'Đang xử lý...' : 'Processing...')
              )}
            </span>
          </div>

          {/* Errors list (if any) */}
          {errors.length > 0 && isDone && (
            <div className="mt-3 max-h-24 overflow-y-auto">
              <p className="text-xs font-medium text-red-600 mb-1">
                {language === 'vi' ? 'Lỗi:' : 'Errors:'}
              </p>
              <ul className="text-xs text-red-500 space-y-1">
                {errors.slice(0, 5).map((error, index) => (
                  <li key={index} className="truncate">• {error}</li>
                ))}
                {errors.length > 5 && (
                  <li className="text-gray-500">
                    {language === 'vi' ? `...và ${errors.length - 5} lỗi khác` : `...and ${errors.length - 5} more`}
                  </li>
                )}
              </ul>
            </div>
          )}

          {/* Auto-close message */}
          {isDone && completed > 0 && errors.length === 0 && (
            <p className="text-xs text-gray-400 mt-2 text-center">
              {language === 'vi' ? 'Tự động đóng sau 5 giây...' : 'Auto closing in 5 seconds...'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default FloatingProgress;
