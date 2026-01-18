import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

/**
 * Background Task Context
 * Manages global background tasks (like Auto Rename) that persist across page navigation
 */

const BackgroundTaskContext = createContext(null);

// Local storage key for persisting active tasks
const STORAGE_KEY = 'backgroundTasks';

export const BackgroundTaskProvider = ({ children }) => {
  // Active tasks state
  const [activeTasks, setActiveTasks] = useState([]);
  
  // Load tasks from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          console.log('🔄 [BackgroundTask] Restoring tasks from localStorage:', parsed.length);
          setActiveTasks(parsed);
        }
      }
    } catch (e) {
      console.error('Failed to parse stored tasks:', e);
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  // Save tasks to localStorage whenever they change
  useEffect(() => {
    if (activeTasks.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(activeTasks));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [activeTasks]);

  // Add a new task
  const addTask = useCallback((task) => {
    const newTask = {
      id: task.taskId,
      type: task.type, // 'ship_certificate', 'audit_certificate', 'company_certificate'
      title: task.title,
      total: task.total,
      completed: 0,
      currentFile: '',
      errors: [],
      status: 'processing',
      apiEndpoint: task.apiEndpoint, // e.g., '/api/certificates/bulk-auto-rename'
      createdAt: new Date().toISOString(),
      onComplete: task.onComplete // Callback when task completes (e.g., refresh list)
    };
    
    console.log('📝 [BackgroundTask] Adding task:', newTask.id);
    setActiveTasks(prev => [...prev, newTask]);
    
    return newTask.id;
  }, []);

  // Update task progress
  const updateTask = useCallback((taskId, updates) => {
    setActiveTasks(prev => prev.map(task => 
      task.id === taskId ? { ...task, ...updates } : task
    ));
  }, []);

  // Remove task
  const removeTask = useCallback((taskId) => {
    console.log('🗑️ [BackgroundTask] Removing task:', taskId);
    setActiveTasks(prev => prev.filter(task => task.id !== taskId));
  }, []);

  // Get task by ID
  const getTask = useCallback((taskId) => {
    return activeTasks.find(task => task.id === taskId);
  }, [activeTasks]);

  // Start a new background rename task
  const startRenameTask = useCallback(async ({
    certificateIds,
    type,
    title,
    apiEndpoint,
    onComplete,
    language = 'vi'
  }) => {
    try {
      console.log(`🚀 [BackgroundTask] Starting rename task for ${certificateIds.length} certificates`);
      
      // Call API to start the task
      const startResponse = await api.post(apiEndpoint, {
        certificate_ids: certificateIds
      });

      if (!startResponse.data?.success || !startResponse.data?.task_id) {
        throw new Error(startResponse.data?.message || 'Failed to start bulk rename');
      }

      const taskId = startResponse.data.task_id;
      console.log(`📋 [BackgroundTask] Task started: ${taskId}`);

      // Add task to context
      addTask({
        taskId,
        type,
        title,
        total: certificateIds.length,
        apiEndpoint: apiEndpoint.replace('/bulk-auto-rename', '/bulk-auto-rename/'),
        onComplete
      });

      return { success: true, taskId };
    } catch (error) {
      console.error('❌ [BackgroundTask] Failed to start task:', error);
      return { success: false, error: error.message };
    }
  }, [addTask]);

  // Start a new background upload task (for folder upload)
  const startUploadTask = useCallback(async ({
    taskId,
    type,
    title,
    total,
    apiEndpoint,
    onComplete
  }) => {
    try {
      console.log(`📁 [BackgroundTask] Adding upload task: ${taskId}`);

      // Add task to context (task already started by API call)
      addTask({
        taskId,
        type,
        title,
        total,
        apiEndpoint,
        onComplete
      });

      return { success: true, taskId };
    } catch (error) {
      console.error('❌ [BackgroundTask] Failed to add upload task:', error);
      return { success: false, error: error.message };
    }
  }, [addTask]);

  // Start staggered file upload - this runs at Context level so it persists across navigation
  const startStaggeredUpload = useCallback(async ({
    taskId,
    files,
    apiEndpoint,
    staggerDelayMs = 2000,
    onFileComplete,
    onAllComplete
  }) => {
    console.log(`📤 [BackgroundTask] Starting staggered upload for task ${taskId} with ${files.length} files`);
    
    const STAGGER_DELAY = staggerDelayMs;
    let cancelledFlag = false;
    
    const uploadSingleFile = async (file, index) => {
      const filename = file.name || file.webkitRelativePath?.split('/').pop() || `file_${index}`;
      
      // Check if upload was cancelled
      if (cancelledFlag) {
        console.log(`🚫 [BackgroundTask] Upload cancelled. Skipping file ${index + 1}: ${filename}`);
        return { success: false, cancelled: true };
      }
      
      try {
        // Check task status before uploading
        try {
          const statusCheck = await api.get(`${apiEndpoint}${taskId}`);
          if (statusCheck.data?.status === 'cancelled') {
            console.log(`🚫 [BackgroundTask] Task ${taskId} cancelled. Skipping file ${index + 1}: ${filename}`);
            cancelledFlag = true;
            return { success: false, cancelled: true };
          }
        } catch (statusError) {
          console.warn('[BackgroundTask] Could not check task status:', statusError.message);
        }
        
        console.log(`📤 [BackgroundTask] Uploading ${index + 1}/${files.length}: ${filename}`);
        
        const uploadForm = new FormData();
        uploadForm.append('file', file, filename);
        
        const uploadResponse = await api.post(
          `${apiEndpoint}${taskId}/upload-file`,
          uploadForm,
          {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 300000 // 5 min timeout per file
          }
        );
        
        if (uploadResponse.data?.success) {
          console.log(`✅ [BackgroundTask] Uploaded ${index + 1}/${files.length}: ${filename}`);
          if (onFileComplete) onFileComplete(index, true, filename);
          return { success: true, filename };
        } else {
          console.warn(`⚠️ [BackgroundTask] Failed ${index + 1}/${files.length}: ${filename} - ${uploadResponse.data?.error}`);
          if (onFileComplete) onFileComplete(index, false, filename, uploadResponse.data?.error);
          return { success: false, filename, error: uploadResponse.data?.error };
        }
      } catch (uploadError) {
        // Check if error is due to task being cancelled
        const errorDetail = uploadError.response?.data?.detail || '';
        if (uploadError.response?.status === 400 && 
            (errorDetail.includes('cancelled') || errorDetail.includes('Task already'))) {
          console.log(`🚫 [BackgroundTask] Task ${taskId} cancelled. File ${index + 1}: ${filename} rejected`);
          cancelledFlag = true;
          return { success: false, cancelled: true };
        }
        console.error(`❌ [BackgroundTask] Error uploading ${filename}:`, uploadError.message);
        if (onFileComplete) onFileComplete(index, false, filename, uploadError.message);
        return { success: false, filename, error: uploadError.message };
      }
    };
    
    // Track completed uploads
    let completedCount = 0;
    const totalFiles = files.length;
    
    // Start each file upload with staggered delay
    files.forEach((file, index) => {
      setTimeout(async () => {
        const result = await uploadSingleFile(file, index);
        completedCount++;
        
        // Check if all files processed
        if (completedCount >= totalFiles && onAllComplete) {
          console.log(`✅ [BackgroundTask] All ${totalFiles} files processed for task ${taskId}`);
          onAllComplete();
        }
      }, index * STAGGER_DELAY);
    });
    
    console.log(`📤 [BackgroundTask] Scheduled ${files.length} uploads with ${STAGGER_DELAY}ms stagger`);
  }, []);

  // Cancel a running task
  const cancelTask = useCallback(async (taskId, apiEndpoint) => {
    try {
      console.log(`🚫 [BackgroundTask] Cancelling task: ${taskId}`);
      
      // Call cancel API
      const cancelUrl = apiEndpoint.endsWith('/') 
        ? `${apiEndpoint}${taskId}/cancel`
        : `${apiEndpoint}/${taskId}/cancel`;
      
      const response = await api.post(cancelUrl);
      
      if (response.data?.success) {
        // Update local task status
        updateTask(taskId, {
          status: 'cancelled',
          currentFile: ''
        });
        
        console.log(`✅ [BackgroundTask] Task ${taskId} cancelled successfully`);
        return { success: true };
      } else {
        console.error(`❌ [BackgroundTask] Cancel failed:`, response.data?.error);
        return { success: false, error: response.data?.error || 'Cancel failed' };
      }
    } catch (error) {
      console.error('❌ [BackgroundTask] Failed to cancel task:', error);
      return { success: false, error: error.message };
    }
  }, [updateTask]);

  const value = {
    activeTasks,
    addTask,
    updateTask,
    removeTask,
    getTask,
    startRenameTask,
    startUploadTask,
    startStaggeredUpload,
    cancelTask,
    hasActiveTasks: activeTasks.length > 0
  };

  return (
    <BackgroundTaskContext.Provider value={value}>
      {children}
    </BackgroundTaskContext.Provider>
  );
};

// Hook to use background task context
export const useBackgroundTask = () => {
  const context = useContext(BackgroundTaskContext);
  if (!context) {
    throw new Error('useBackgroundTask must be used within BackgroundTaskProvider');
  }
  return context;
};

export default BackgroundTaskContext;
