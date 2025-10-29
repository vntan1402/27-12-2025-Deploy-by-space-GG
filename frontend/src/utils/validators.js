/**
 * Validation Utilities
 * 
 * Form validation functions
 */

/**
 * Validate email format
 * 
 * @param {string} email - Email address
 * @returns {boolean} True if valid email
 */
export const isValidEmail = (email) => {
  if (!email) return false;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate required field
 * 
 * @param {any} value - Field value
 * @param {string} fieldName - Field name for error message
 * @returns {string|null} Error message or null if valid
 */
export const validateRequired = (value, fieldName) => {
  if (value === null || value === undefined || value === '') {
    return `${fieldName} is required`;
  }
  if (typeof value === 'string' && value.trim() === '') {
    return `${fieldName} is required`;
  }
  return null;
};

/**
 * Validate date format (DD/MM/YYYY or YYYY-MM-DD)
 * 
 * @param {string} dateStr - Date string
 * @returns {boolean} True if valid format
 */
export const isValidDateFormat = (dateStr) => {
  if (!dateStr) return false;
  
  // DD/MM/YYYY format
  const ddmmyyyyRegex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
  if (ddmmyyyyRegex.test(dateStr)) return true;
  
  // YYYY-MM-DD format
  const yyyymmddRegex = /^(\d{4})-(\d{2})-(\d{2})$/;
  if (yyyymmddRegex.test(dateStr)) return true;
  
  return false;
};

/**
 * Validate phone number (Vietnamese format)
 * 
 * @param {string} phone - Phone number
 * @returns {boolean} True if valid phone
 */
export const isValidPhoneNumber = (phone) => {
  if (!phone) return false;
  
  // Remove all non-digit characters
  const cleaned = phone.replace(/\D/g, '');
  
  // Vietnamese phone: 10 digits starting with 0
  return /^0\d{9}$/.test(cleaned);
};

/**
 * Validate passport number format
 * 
 * @param {string} passport - Passport number
 * @returns {boolean} True if valid format
 */
export const isValidPassportNumber = (passport) => {
  if (!passport) return false;
  
  // Most passports: 6-9 alphanumeric characters
  return /^[A-Z0-9]{6,9}$/i.test(passport.trim());
};

/**
 * Validate IMO number
 * 
 * @param {string} imo - IMO number
 * @returns {boolean} True if valid IMO
 */
export const isValidIMO = (imo) => {
  if (!imo) return false;
  
  // IMO number: 7 digits
  const cleaned = imo.replace(/\D/g, '');
  return /^\d{7}$/.test(cleaned);
};

/**
 * Validate crew data
 * 
 * @param {object} data - Crew data object
 * @returns {object} { isValid: boolean, errors: object }
 */
export const validateCrewData = (data) => {
  const errors = {};
  
  // Required fields
  if (!data.full_name?.trim()) {
    errors.full_name = 'Full name is required';
  }
  
  if (!data.date_of_birth) {
    errors.date_of_birth = 'Date of birth is required';
  }
  
  if (!data.passport?.trim()) {
    errors.passport = 'Passport number is required';
  }
  
  if (!data.place_of_birth?.trim()) {
    errors.place_of_birth = 'Place of birth is required';
  }
  
  // Optional but validate if provided
  if (data.date_of_birth && !isValidDateFormat(data.date_of_birth)) {
    errors.date_of_birth = 'Invalid date format';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
};

/**
 * Validate certificate data
 * 
 * @param {object} data - Certificate data object
 * @returns {object} { isValid: boolean, errors: object }
 */
export const validateCertificateData = (data) => {
  const errors = {};
  
  // Required fields
  if (!data.cert_name?.trim()) {
    errors.cert_name = 'Certificate name is required';
  }
  
  if (!data.cert_no?.trim()) {
    errors.cert_no = 'Certificate number is required';
  }
  
  if (!data.issued_date) {
    errors.issued_date = 'Issued date is required';
  }
  
  // Validate dates if provided
  if (data.issued_date && !isValidDateFormat(data.issued_date)) {
    errors.issued_date = 'Invalid date format';
  }
  
  if (data.cert_expiry && !isValidDateFormat(data.cert_expiry)) {
    errors.cert_expiry = 'Invalid date format';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
};

/**
 * Validate ship data
 * 
 * @param {object} data - Ship data object
 * @returns {object} { isValid: boolean, errors: object }
 */
export const validateShipData = (data) => {
  const errors = {};
  
  // Required fields
  if (!data.name?.trim()) {
    errors.name = 'Ship name is required';
  }
  
  if (!data.imo_number?.trim()) {
    errors.imo_number = 'IMO number is required';
  } else if (!isValidIMO(data.imo_number)) {
    errors.imo_number = 'Invalid IMO number (must be 7 digits)';
  }
  
  // Optional but validate if provided
  if (data.built_date && !isValidDateFormat(data.built_date)) {
    errors.built_date = 'Invalid date format';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
};

/**
 * Validate survey report data
 * 
 * @param {object} data - Survey report data object
 * @returns {object} { isValid: boolean, errors: object }
 */
export const validateSurveyReportData = (data) => {
  const errors = {};
  
  // Required fields
  if (!data.survey_report_name?.trim()) {
    errors.survey_report_name = 'Survey report name is required';
  }
  
  // Validate dates if provided
  if (data.issued_date && !isValidDateFormat(data.issued_date)) {
    errors.issued_date = 'Invalid date format';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
};

/**
 * Validate test report data
 * 
 * @param {object} data - Test report data object
 * @returns {object} { isValid: boolean, errors: object }
 */
export const validateTestReportData = (data) => {
  const errors = {};
  
  // Required fields
  if (!data.test_report_name?.trim()) {
    errors.test_report_name = 'Test report name is required';
  }
  
  // Validate dates if provided
  if (data.issued_date && !isValidDateFormat(data.issued_date)) {
    errors.issued_date = 'Invalid date format';
  }
  
  if (data.valid_date && !isValidDateFormat(data.valid_date)) {
    errors.valid_date = 'Invalid date format';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
};

/**
 * Validate file size
 * 
 * @param {File} file - File object
 * @param {number} maxSizeMB - Maximum size in MB
 * @returns {boolean} True if file size is valid
 */
export const isValidFileSize = (file, maxSizeMB = 10) => {
  if (!file) return false;
  const maxBytes = maxSizeMB * 1024 * 1024;
  return file.size <= maxBytes;
};

/**
 * Validate file type
 * 
 * @param {File} file - File object
 * @param {string[]} allowedTypes - Array of allowed MIME types
 * @returns {boolean} True if file type is valid
 */
export const isValidFileType = (file, allowedTypes) => {
  if (!file || !allowedTypes) return false;
  return allowedTypes.includes(file.type);
};

/**
 * Validate PDF file
 * 
 * @param {File} file - File object
 * @returns {object} { isValid: boolean, error: string|null }
 */
export const validatePDFFile = (file) => {
  if (!file) {
    return { isValid: false, error: 'No file selected' };
  }
  
  if (file.type !== 'application/pdf') {
    return { isValid: false, error: 'Only PDF files are allowed' };
  }
  
  if (!isValidFileSize(file, 10)) {
    return { isValid: false, error: 'File size must be less than 10MB' };
  }
  
  return { isValid: true, error: null };
};

/**
 * Validate image file
 * 
 * @param {File} file - File object
 * @returns {object} { isValid: boolean, error: string|null }
 */
export const validateImageFile = (file) => {
  if (!file) {
    return { isValid: false, error: 'No file selected' };
  }
  
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
  if (!isValidFileType(file, allowedTypes)) {
    return { isValid: false, error: 'Only JPEG and PNG images are allowed' };
  }
  
  if (!isValidFileSize(file, 5)) {
    return { isValid: false, error: 'Image size must be less than 5MB' };
  }
  
  return { isValid: true, error: null };
};

/**
 * Validate username
 * 
 * @param {string} username - Username
 * @returns {object} { isValid: boolean, error: string|null }
 */
export const validateUsername = (username) => {
  if (!username || username.trim() === '') {
    return { isValid: false, error: 'Username is required' };
  }
  
  if (username.length < 3) {
    return { isValid: false, error: 'Username must be at least 3 characters' };
  }
  
  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    return { isValid: false, error: 'Username can only contain letters, numbers, and underscores' };
  }
  
  return { isValid: true, error: null };
};

/**
 * Validate password
 * 
 * @param {string} password - Password
 * @returns {object} { isValid: boolean, error: string|null }
 */
export const validatePassword = (password) => {
  if (!password || password.trim() === '') {
    return { isValid: false, error: 'Password is required' };
  }
  
  if (password.length < 6) {
    return { isValid: false, error: 'Password must be at least 6 characters' };
  }
  
  return { isValid: true, error: null };
};
