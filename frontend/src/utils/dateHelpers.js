/**
 * Date Utilities
 * 
 * Extracted from Frontend V1
 * All date handling functions with timezone-safe operations
 */

/**
 * Format date for display (DD/MM/YYYY)
 * Handles various date input formats safely
 * 
 * @param {string|Date|object} dateValue - Date value in various formats
 * @returns {string} Formatted date as DD/MM/YYYY or '-' if invalid
 */
export const formatDateDisplay = (dateValue) => {
  if (!dateValue) return '-';
  
  // Handle different date formats consistently
  let dateStr = dateValue;
  if (typeof dateValue === 'object' && dateValue.toString) {
    dateStr = dateValue.toString();
  }
  
  // If it's already in DD/MM/YYYY format, return as is
  if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateStr)) {
    return dateStr;
  }
  
  // Parse ISO date string (YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss) without creating Date object
  // This avoids timezone conversion issues
  if (typeof dateStr === 'string') {
    // Extract just the date part (YYYY-MM-DD)
    const datePart = dateStr.split('T')[0]; // Remove time component if present
    const dateMatch = datePart.match(/^(\d{4})-(\d{2})-(\d{2})/);
    
    if (dateMatch) {
      const [, year, month, day] = dateMatch;
      return `${day}/${month}/${year}`;
    }
  }
  
  // Fallback: try to parse with Date (may have timezone issues)
  try {
    const date = new Date(dateStr);
    if (!isNaN(date.getTime())) {
      // Use UTC methods to avoid timezone shift for dates that might be stored as UTC
      const day = String(date.getUTCDate()).padStart(2, '0');
      const month = String(date.getUTCMonth() + 1).padStart(2, '0');
      const year = date.getUTCFullYear();
      return `${day}/${month}/${year}`;
    }
  } catch (e) {
    console.warn('Date parsing error:', e);
  }
  
  return dateStr; // Return original value if all parsing fails
};

/**
 * Convert date input to UTC ISO string for backend
 * Handles: DD/MM/YYYY, YYYY-MM-DD formats
 * 
 * @param {string} dateString - Date string to convert
 * @returns {string|null} UTC ISO string (YYYY-MM-DDTHH:mm:ssZ) or null
 */
export const convertDateInputToUTC = (dateString) => {
  if (!dateString || typeof dateString !== 'string') return null;
  
  try {
    const trimmedDate = dateString.trim();
    
    // Handle YYYY-MM-DD format from HTML date inputs
    const isoPattern = /^\d{4}-\d{2}-\d{2}$/;
    if (isoPattern.test(trimmedDate)) {
      return `${trimmedDate}T00:00:00Z`;
    }
    
    // Handle DD/MM/YYYY format from Document AI passport analysis
    const ddmmyyyyPattern = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
    const ddmmMatch = ddmmyyyyPattern.exec(trimmedDate);
    if (ddmmMatch) {
      const day = ddmmMatch[1].padStart(2, '0');
      const month = ddmmMatch[2].padStart(2, '0');
      const year = ddmmMatch[3];
      return `${year}-${month}-${day}T00:00:00Z`;
    }
    
    // Handle YYYY-MM-DD format from backend responses
    const yyyymmddPattern = /^(\d{4})-(\d{1,2})-(\d{1,2})$/;
    const yyyymmMatch = yyyymmddPattern.exec(trimmedDate);
    if (yyyymmMatch) {
      const year = yyyymmMatch[1];
      const month = yyyymmMatch[2].padStart(2, '0');
      const day = yyyymmMatch[3].padStart(2, '0');
      return `${year}-${month}-${day}T00:00:00Z`;
    }
    
    console.warn('Unsupported date format:', dateString);
    return null;
  } catch (error) {
    console.error('Error converting date input to UTC:', error);
    return null;
  }
};

/**
 * Format date for HTML date input (YYYY-MM-DD)
 * Handles: DD/MM/YYYY, YYYY-MM-DD, ISO datetime formats
 * 
 * @param {string} dateString - Date string to format
 * @returns {string} Formatted date as YYYY-MM-DD or empty string
 */
export const formatDateForInput = (dateString) => {
  if (!dateString || typeof dateString !== 'string') return '';
  
  try {
    const trimmedDate = dateString.trim();
    
    // Already in YYYY-MM-DD format
    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmedDate)) {
      return trimmedDate;
    }
    
    // Handle DD/MM/YYYY format
    const ddmmyyyyPattern = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
    const ddmmMatch = ddmmyyyyPattern.exec(trimmedDate);
    if (ddmmMatch) {
      const day = ddmmMatch[1].padStart(2, '0');
      const month = ddmmMatch[2].padStart(2, '0');
      const year = ddmmMatch[3];
      return `${year}-${month}-${day}`;
    }
    
    // Handle ISO datetime (YYYY-MM-DDTHH:mm:ss or YYYY-MM-DDTHH:mm:ssZ)
    const isoPattern = /^(\d{4})-(\d{2})-(\d{2})/;
    const isoMatch = isoPattern.exec(trimmedDate);
    if (isoMatch) {
      return `${isoMatch[1]}-${isoMatch[2]}-${isoMatch[3]}`;
    }
    
    return '';
  } catch (error) {
    console.error('Error formatting date for input:', error);
    return '';
  }
};

/**
 * Parse date string safely without timezone conversion
 * 
 * @param {string} dateStr - Date string to parse
 * @returns {Date|null} Date object or null if invalid
 */
export const parseDateSafely = (dateStr) => {
  if (!dateStr) return null;
  
  try {
    // Handle DD/MM/YYYY format
    const ddmmyyyyPattern = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
    const ddmmMatch = ddmmyyyyPattern.exec(dateStr);
    if (ddmmMatch) {
      const day = parseInt(ddmmMatch[1], 10);
      const month = parseInt(ddmmMatch[2], 10) - 1; // Month is 0-indexed
      const year = parseInt(ddmmMatch[3], 10);
      return new Date(Date.UTC(year, month, day, 0, 0, 0, 0));
    }
    
    // Handle YYYY-MM-DD format
    const yyyymmddPattern = /^(\d{4})-(\d{1,2})-(\d{1,2})$/;
    const yyyymmMatch = yyyymmddPattern.exec(dateStr);
    if (yyyymmMatch) {
      const year = parseInt(yyyymmMatch[1], 10);
      const month = parseInt(yyyymmMatch[2], 10) - 1;
      const day = parseInt(yyyymmMatch[3], 10);
      return new Date(Date.UTC(year, month, day, 0, 0, 0, 0));
    }
    
    // Handle ISO datetime
    const date = new Date(dateStr);
    return isNaN(date.getTime()) ? null : date;
  } catch (e) {
    console.warn('Date parsing error:', e);
    return null;
  }
};

/**
 * Calculate days until expiry
 * 
 * @param {string} expiryDate - Expiry date string
 * @returns {number|null} Number of days until expiry (negative if expired)
 */
export const daysUntilExpiry = (expiryDate) => {
  if (!expiryDate) return null;
  
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const expiry = parseDateSafely(expiryDate);
    if (!expiry) return null;
    
    const diffTime = expiry.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays;
  } catch (e) {
    console.warn('Error calculating days until expiry:', e);
    return null;
  }
};

/**
 * Calculate certificate status based on expiry date
 * 
 * @param {string} expiryDate - Expiry date string
 * @returns {string} Status: 'Valid', 'Expiring Soon', 'Expired', or 'Unknown'
 */
export const calculateCertStatus = (expiryDate) => {
  if (!expiryDate || expiryDate === '-') return 'Unknown';
  
  const days = daysUntilExpiry(expiryDate);
  
  if (days === null) return 'Unknown';
  if (days < 0) return 'Expired';
  if (days <= 30) return 'Expiring Soon';
  return 'Valid';
};

/**
 * Get today's date in YYYY-MM-DD format
 * 
 * @returns {string} Today's date as YYYY-MM-DD
 */
export const getTodayDate = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * Check if date is in the past
 * 
 * @param {string} dateStr - Date string to check
 * @returns {boolean} True if date is in the past
 */
export const isDateInPast = (dateStr) => {
  const days = daysUntilExpiry(dateStr);
  return days !== null && days < 0;
};

/**
 * Check if date is within next N days
 * 
 * @param {string} dateStr - Date string to check
 * @param {number} days - Number of days to check within
 * @returns {boolean} True if date is within next N days
 */
export const isDateWithinDays = (dateStr, days) => {
  const daysUntil = daysUntilExpiry(dateStr);
  return daysUntil !== null && daysUntil >= 0 && daysUntil <= days;
};

/**
 * Add days to a date string
 * 
 * @param {string} dateStr - Date string (YYYY-MM-DD or DD/MM/YYYY)
 * @param {number} daysToAdd - Number of days to add
 * @returns {string} New date in YYYY-MM-DD format
 */
export const addDays = (dateStr, daysToAdd) => {
  const date = parseDateSafely(dateStr);
  if (!date) return '';
  
  date.setDate(date.getDate() + daysToAdd);
  
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  
  return `${year}-${month}-${day}`;
};

/**
 * Add months to a date string
 * 
 * @param {string} dateStr - Date string (YYYY-MM-DD or DD/MM/YYYY)
 * @param {number} monthsToAdd - Number of months to add
 * @returns {string} New date in YYYY-MM-DD format
 */
export const addMonths = (dateStr, monthsToAdd) => {
  const date = parseDateSafely(dateStr);
  if (!date) return '';
  
  date.setUTCMonth(date.getUTCMonth() + monthsToAdd);
  
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  
  return `${year}-${month}-${day}`;
};

/**
 * Compare two dates
 * 
 * @param {string} date1 - First date string
 * @param {string} date2 - Second date string
 * @returns {number} -1 if date1 < date2, 0 if equal, 1 if date1 > date2
 */
export const compareDates = (date1, date2) => {
  const d1 = parseDateSafely(date1);
  const d2 = parseDateSafely(date2);
  
  if (!d1 || !d2) return 0;
  
  if (d1 < d2) return -1;
  if (d1 > d2) return 1;
  return 0;
};
