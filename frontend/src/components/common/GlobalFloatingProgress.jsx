import React, { useState, useEffect, useCallback } from 'react';
import { X, Minimize2, Maximize2, CheckCircle, XCircle, Loader2, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { useBackgroundTask } from '../../contexts/BackgroundTaskContext';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';

/**
 * Global Floating Progress Component
 * Displays at App level, persists across page navigation
 * Polls backend for task status and updates automatically
 */
const GlobalFloatingProgress = () => {
  const { activeTasks, updateTask, removeTask } = useBackgroundTask();
  const { language } = useAuth();
  const [isMinimized, setIsMinimized] = useState(false);
  const [expandedTasks, setExpandedTasks] = useState(new Set());

  // Poll for task status
  useEffect(() => {
    if (activeTasks.length === 0) return;

    const pollInterval = 1000; // 1 second
    let isMounted = true;

    const pollTasks = async () => {
      for (const task of activeTasks) {
        if (!isMounted) break;
        
        // Skip completed tasks
        if (task.status === 'completed' || task.status === 'completed_with_errors' || task.status === 'failed') {
          continue;
        }

        try {
          const response = await api.get(`${task.apiEndpoint}${task.id}`);
          const status = response.data;

          updateTask(task.id, {
            completed: status.completed_files || 0,
            currentFile: status.current_file || '',
            errors: (status.results || [])
              .filter(r => !r.success)
              .map(r => r.error || 'Unknown error'),
            status: status.status
          });

          // If task completed, call onComplete callback
          if (status.status === 'completed' || status.status === 'completed_with_errors' || status.status === 'failed') {
            console.log(`✅ [GlobalFloatingProgress] Task ${task.id} completed with status: ${status.status}`);
            
            // Execute onComplete callback if exists (might be null after page refresh)
            if (typeof task.onComplete === 'function') {
              try {
                await task.onComplete();
              } catch (e) {
                console.error('onComplete callback error:', e);
              }
            }
          }
        } catch (error) {
          console.error(`❌ [GlobalFloatingProgress] Poll error for task ${task.id}:`, error);
        }
      }
    };

    // Initial poll
    pollTasks();

    // Set up interval
    const intervalId = setInterval(pollTasks, pollInterval);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, [activeTasks, updateTask]);

  // Auto-remove completed tasks after delay
  useEffect(() => {
    const completedTasks = activeTasks.filter(
      t => (t.status === 'completed' || t.status === 'completed_with_errors' || t.status === 'failed')
    );

    completedTasks.forEach(task => {
      // Auto-remove after 10 seconds for success, keep errors longer
      const delay = task.errors.length > 0 ? 30000 : 10000;
      
      const timer = setTimeout(() => {
        removeTask(task.id);
      }, delay);

      return () => clearTimeout(timer);
    });
  }, [activeTasks, removeTask]);

  // Toggle task expansion
  const toggleTaskExpand = (taskId) => {
    setExpandedTasks(prev => {
      const next = new Set(prev);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });
  };

  // Don't render if no active tasks
  if (activeTasks.length === 0) return null;

  // Get status info for a task
  const getStatusInfo = (task) => {
    if (task.status === 'completed') {
      return { icon: CheckCircle, color: 'text-green-500', bgColor: 'bg-green-50' };
    } else if (task.status === 'completed_with_errors') {
      return { icon: CheckCircle, color: 'text-yellow-500', bgColor: 'bg-yellow-50' };
    } else if (task.status === 'failed') {
      return { icon: XCircle, color: 'text-red-500', bgColor: 'bg-red-50' };
    }
    return { icon: Loader2, color: 'text-blue-500', bgColor: 'bg-blue-50' };
  };

  // Calculate total progress
  const totalCompleted = activeTasks.reduce((sum, t) => sum + t.completed, 0);
  const totalFiles = activeTasks.reduce((sum, t) => sum + t.total, 0);
  const processingCount = activeTasks.filter(t => t.status === 'processing').length;

  // Minimized view - show as badge
  if (isMinimized) {
    return (
      <div className="fixed z-[100] right-5 bottom-5">
        <div 
          className="flex items-center gap-2 px-4 py-2 rounded-full shadow-lg bg-white border border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors"
          onClick={() => setIsMinimized(false)}
        >
          {processingCount > 0 ? (
            <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
          ) : (
            <CheckCircle className="w-5 h-5 text-green-500" />
          )}
          <span className="text-sm font-medium">
            {processingCount > 0 
              ? `${totalCompleted}/${totalFiles}`
              : (language === 'vi' ? 'Hoàn thành' : 'Done')
            }
          </span>
          <span className="text-xs text-gray-500">
            ({activeTasks.length} {language === 'vi' ? 'task' : 'tasks'})
          </span>
          <Maximize2 className="w-4 h-4 text-gray-400" />
        </div>
      </div>
    );
  }

  // Full view
  return (
    <div className="fixed z-[100] right-5 bottom-5 w-80">
      <div className="rounded-lg shadow-xl border border-gray-200 bg-white overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-gray-600" />
            <span className="font-medium text-sm text-gray-800">
              {language === 'vi' ? 'Tác vụ nền' : 'Background Tasks'}
            </span>
            <span className="text-xs text-gray-500">({activeTasks.length})</span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsMinimized(true)}
              className="p-1 hover:bg-gray-200 rounded transition-colors"
              title={language === 'vi' ? 'Thu nhỏ' : 'Minimize'}
            >
              <Minimize2 className="w-4 h-4 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Tasks List */}
        <div className="max-h-80 overflow-y-auto">
          {activeTasks.map((task) => {
            const statusInfo = getStatusInfo(task);
            const StatusIcon = statusInfo.icon;
            const isDone = task.status !== 'processing';
            const isExpanded = expandedTasks.has(task.id);
            const progressPercent = task.total > 0 ? Math.round((task.completed / task.total) * 100) : 0;

            return (
              <div key={task.id} className={`border-b last:border-b-0 ${statusInfo.bgColor}`}>
                {/* Task Header */}
                <div 
                  className="p-3 cursor-pointer hover:bg-opacity-80 transition-colors"
                  onClick={() => toggleTaskExpand(task.id)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <StatusIcon className={`w-4 h-4 ${statusInfo.color} ${!isDone ? 'animate-spin' : ''}`} />
                      <span className="text-sm font-medium text-gray-800 truncate max-w-[180px]">
                        {task.title}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-600">
                        {task.completed}/{task.total}
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-gray-400" />
                      )}
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${
                        task.status === 'failed' ? 'bg-red-500' :
                        task.status === 'completed_with_errors' ? 'bg-yellow-500' :
                        task.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
                      }`}
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="px-3 pb-3 text-xs">
                    {/* Current file */}
                    {task.currentFile && !isDone && (
                      <p className="text-gray-600 truncate mb-2">
                        {language === 'vi' ? 'Đang xử lý' : 'Processing'}: {task.currentFile}
                      </p>
                    )}

                    {/* Status message */}
                    <p className={`${statusInfo.color} mb-2`}>
                      {isDone ? (
                        task.status === 'completed' ? (
                          language === 'vi' ? '✅ Hoàn thành!' : '✅ Completed!'
                        ) : task.status === 'completed_with_errors' ? (
                          language === 'vi' ? `⚠️ Hoàn thành với ${task.errors.length} lỗi` : `⚠️ Completed with ${task.errors.length} errors`
                        ) : (
                          language === 'vi' ? '❌ Thất bại' : '❌ Failed'
                        )
                      ) : (
                        language === 'vi' ? '⏳ Đang xử lý...' : '⏳ Processing...'
                      )}
                    </p>

                    {/* Errors */}
                    {task.errors.length > 0 && (
                      <div className="bg-red-50 border border-red-200 rounded p-2 max-h-20 overflow-y-auto">
                        <p className="font-medium text-red-700 mb-1">
                          {language === 'vi' ? 'Lỗi:' : 'Errors:'}
                        </p>
                        <ul className="text-red-600 space-y-0.5">
                          {task.errors.slice(0, 3).map((error, idx) => (
                            <li key={idx} className="truncate">• {error}</li>
                          ))}
                          {task.errors.length > 3 && (
                            <li className="text-gray-500">
                              ...{language === 'vi' ? `và ${task.errors.length - 3} lỗi khác` : `and ${task.errors.length - 3} more`}
                            </li>
                          )}
                        </ul>
                      </div>
                    )}

                    {/* Close button for completed tasks */}
                    {isDone && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeTask(task.id);
                        }}
                        className="mt-2 text-gray-500 hover:text-gray-700 flex items-center gap-1"
                      >
                        <X className="w-3 h-3" />
                        {language === 'vi' ? 'Đóng' : 'Close'}
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer - auto close message */}
        {activeTasks.every(t => t.status !== 'processing') && (
          <div className="px-3 py-2 bg-gray-50 border-t">
            <p className="text-xs text-gray-400 text-center">
              {language === 'vi' ? 'Tự động đóng sau 10 giây...' : 'Auto closing in 10 seconds...'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default GlobalFloatingProgress;
