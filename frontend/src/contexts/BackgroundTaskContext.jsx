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

  const value = {
    activeTasks,
    addTask,
    updateTask,
    removeTask,
    getTask,
    startRenameTask,
    startUploadTask,
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
