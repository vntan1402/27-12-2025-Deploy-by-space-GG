/**
 * Progress Helper Utilities
 * For smooth progress animations in batch processing
 */

/**
 * Calculate estimated processing time for a file
 * @param {File} file - The file object
 * @param {number} pageCount - Optional page count
 * @returns {number} Estimated time in milliseconds
 */
export const estimateFileProcessingTime = (file, pageCount = null) => {
  const BASE_TIME = 30000; // 30 seconds base time
  const TIME_PER_MB = 5000; // 5 seconds per MB
  const TIME_PER_PAGE = 2000; // 2 seconds per page
  
  const fileSizeMB = file.size / (1024 * 1024);
  let estimatedTime = BASE_TIME + (fileSizeMB * TIME_PER_MB);
  
  if (pageCount && pageCount > 0) {
    estimatedTime += (pageCount * TIME_PER_PAGE);
  }
  
  return estimatedTime;
};

/**
 * Trigger sub-status transitions (analyzing → uploading)
 * @param {string} filename - The filename
 * @param {Function} setSubStatusMap - State setter for sub-status map
 */
export const triggerSubStatusTransitions = async (filename, setSubStatusMap) => {
  try {
    // When progress reaches 90%, start AI analysis phase
    setSubStatusMap(prev => ({ ...prev, [filename]: 'analyzing' }));

    // Wait 5 seconds for AI analysis phase
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Then switch to uploading phase
    setSubStatusMap(prev => ({ ...prev, [filename]: 'uploading' }));
  } catch (error) {
    console.error(`Error in sub-status transitions for ${filename}:`, error);
  }
};

/**
 * Start smooth progress for a specific file (parallel processing support)
 * @param {string} filename - The filename to track progress for
 * @param {Function} setProgressMap - State setter for progress map
 * @param {Function} setSubStatusMap - State setter for sub-status map
 * @param {number} duration - Duration in milliseconds
 * @param {number} maxProgress - Maximum progress to reach (default 90)
 * @returns {Object} - Object with stop and complete functions
 */
export const startSmoothProgressForFile = (
  filename,
  setProgressMap,
  setSubStatusMap,
  duration,
  maxProgress = 90
) => {
  const startTime = Date.now();
  const updateInterval = 100; // Update every 100ms
  let stopped = false;
  let subStatusTriggered = false;
  
  const intervalId = setInterval(() => {
    if (stopped) {
      clearInterval(intervalId);
      return;
    }
    
    const elapsed = Date.now() - startTime;
    const progress = (elapsed / duration) * maxProgress;
    
    if (progress >= maxProgress) {
      // Update map
      setProgressMap(prev => ({ ...prev, [filename]: maxProgress }));
      
      // Trigger sub-status transitions when reaching 90%
      if (!subStatusTriggered && maxProgress >= 90) {
        subStatusTriggered = true;
        triggerSubStatusTransitions(filename, setSubStatusMap);
      }
      
      clearInterval(intervalId);
    } else {
      // Update progress
      setProgressMap(prev => ({ ...prev, [filename]: Math.floor(progress) }));
    }
  }, updateInterval);
  
  return {
    stop: () => {
      stopped = true;
      clearInterval(intervalId);
    },
    complete: () => {
      stopped = true;
      clearInterval(intervalId);
      setProgressMap(prev => ({ ...prev, [filename]: 100 }));
      setSubStatusMap(prev => ({ ...prev, [filename]: null }));
    }
  };
};
