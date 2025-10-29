/**
 * Text/String Utilities
 * 
 * Extracted from Frontend V1
 * Text manipulation, Vietnamese diacritics handling, and formatting
 */

/**
 * Vietnamese diacritics removal map
 */
const vietnameseMap = {
  'à': 'a', 'á': 'a', 'ạ': 'a', 'ả': 'a', 'ã': 'a',
  'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ậ': 'a', 'ẩ': 'a', 'ẫ': 'a',
  'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ặ': 'a', 'ẳ': 'a', 'ẵ': 'a',
  'è': 'e', 'é': 'e', 'ẹ': 'e', 'ẻ': 'e', 'ẽ': 'e',
  'ê': 'e', 'ề': 'e', 'ế': 'e', 'ệ': 'e', 'ể': 'e', 'ễ': 'e',
  'ì': 'i', 'í': 'i', 'ị': 'i', 'ỉ': 'i', 'ĩ': 'i',
  'ò': 'o', 'ó': 'o', 'ọ': 'o', 'ỏ': 'o', 'õ': 'o',
  'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ộ': 'o', 'ổ': 'o', 'ỗ': 'o',
  'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ợ': 'o', 'ở': 'o', 'ỡ': 'o',
  'ù': 'u', 'ú': 'u', 'ụ': 'u', 'ủ': 'u', 'ũ': 'u',
  'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ự': 'u', 'ử': 'u', 'ữ': 'u',
  'ỳ': 'y', 'ý': 'y', 'ỵ': 'y', 'ỷ': 'y', 'ỹ': 'y',
  'đ': 'd',
  // Uppercase versions
  'À': 'A', 'Á': 'A', 'Ạ': 'A', 'Ả': 'A', 'Ã': 'A',
  'Â': 'A', 'Ầ': 'A', 'Ấ': 'A', 'Ậ': 'A', 'Ẩ': 'A', 'Ẫ': 'A',
  'Ă': 'A', 'Ằ': 'A', 'Ắ': 'A', 'Ặ': 'A', 'Ẳ': 'A', 'Ẵ': 'A',
  'È': 'E', 'É': 'E', 'Ẹ': 'E', 'Ẻ': 'E', 'Ẽ': 'E',
  'Ê': 'E', 'Ề': 'E', 'Ế': 'E', 'Ệ': 'E', 'Ể': 'E', 'Ễ': 'E',
  'Ì': 'I', 'Í': 'I', 'Ị': 'I', 'Ỉ': 'I', 'Ĩ': 'I',
  'Ò': 'O', 'Ó': 'O', 'Ọ': 'O', 'Ỏ': 'O', 'Õ': 'O',
  'Ô': 'O', 'Ồ': 'O', 'Ố': 'O', 'Ộ': 'O', 'Ổ': 'O', 'Ỗ': 'O',
  'Ơ': 'O', 'Ờ': 'O', 'Ớ': 'O', 'Ợ': 'O', 'Ở': 'O', 'Ỡ': 'O',
  'Ù': 'U', 'Ú': 'U', 'Ụ': 'U', 'Ủ': 'U', 'Ũ': 'U',
  'Ư': 'U', 'Ừ': 'U', 'Ứ': 'U', 'Ự': 'U', 'Ử': 'U', 'Ữ': 'U',
  'Ỳ': 'Y', 'Ý': 'Y', 'Ỵ': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y',
  'Đ': 'D'
};

/**
 * Remove Vietnamese diacritics from string
 * Converts Vietnamese characters to their ASCII equivalents
 * 
 * @param {string} str - String with Vietnamese diacritics
 * @returns {string} String with diacritics removed
 */
export const removeVietnameseDiacritics = (str) => {
  if (!str) return '';
  return str.replace(/./g, char => vietnameseMap[char] || char);
};

/**
 * Auto-fill English field from Vietnamese field
 * Removes diacritics and trims whitespace
 * 
 * @param {string} vietnameseText - Vietnamese text
 * @returns {string} English text (ASCII only)
 */
export const autoFillEnglishField = (vietnameseText) => {
  if (!vietnameseText || vietnameseText.trim() === '') return '';
  return removeVietnameseDiacritics(vietnameseText.trim());
};

/**
 * Get abbreviation from full organization name
 * Takes first letter of each word
 * 
 * @param {string} fullName - Full organization name
 * @returns {string} Abbreviation (e.g., "Maritime Authority" → "MA")
 */
export const getAbbreviation = (fullName) => {
  if (!fullName || fullName === '-') return '-';
  
  // Split by spaces and get first letter of each word
  const words = fullName.trim().split(/\s+/);
  
  // Get first letter of each word (uppercase)
  const abbreviation = words
    .map(word => word.charAt(0).toUpperCase())
    .join('');
  
  return abbreviation;
};

/**
 * Capitalize first letter of each word
 * 
 * @param {string} str - Input string
 * @returns {string} String with capitalized words
 */
export const capitalizeWords = (str) => {
  if (!str) return '';
  return str
    .toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Capitalize first letter only
 * 
 * @param {string} str - Input string
 * @returns {string} String with first letter capitalized
 */
export const capitalizeFirst = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

/**
 * Normalize whitespace
 * Removes extra spaces, tabs, and newlines
 * 
 * @param {string} str - Input string
 * @returns {string} String with normalized whitespace
 */
export const normalizeWhitespace = (str) => {
  if (!str) return '';
  return str.trim().replace(/\s+/g, ' ');
};

/**
 * Truncate string with ellipsis
 * 
 * @param {string} str - String to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated string with ellipsis if needed
 */
export const truncate = (str, maxLength = 50) => {
  if (!str) return '';
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength - 3) + '...';
};

/**
 * Convert string to slug (URL-friendly)
 * 
 * @param {string} str - Input string
 * @returns {string} URL-friendly slug
 */
export const slugify = (str) => {
  if (!str) return '';
  
  return removeVietnameseDiacritics(str)
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '') // Remove special characters
    .replace(/\s+/g, '-') // Replace spaces with hyphens
    .replace(/-+/g, '-'); // Replace multiple hyphens with single
};

/**
 * Format phone number
 * 
 * @param {string} phone - Phone number
 * @returns {string} Formatted phone number
 */
export const formatPhoneNumber = (phone) => {
  if (!phone) return '';
  
  // Remove all non-digit characters
  const cleaned = phone.replace(/\D/g, '');
  
  // Format based on length
  if (cleaned.length === 10) {
    // Vietnamese format: 0xxx xxx xxx
    return cleaned.replace(/(\d{4})(\d{3})(\d{3})/, '$1 $2 $3');
  }
  
  return phone; // Return as is if not matching expected format
};

/**
 * Extract numbers from string
 * 
 * @param {string} str - Input string
 * @returns {string} Numbers only
 */
export const extractNumbers = (str) => {
  if (!str) return '';
  return str.replace(/\D/g, '');
};

/**
 * Check if string contains Vietnamese characters
 * 
 * @param {string} str - String to check
 * @returns {boolean} True if contains Vietnamese characters
 */
export const containsVietnamese = (str) => {
  if (!str) return false;
  return /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i.test(str);
};

/**
 * Format crew name (Vietnamese convention: UPPERCASE)
 * 
 * @param {string} name - Crew name
 * @returns {string} Formatted name in uppercase
 */
export const formatCrewName = (name) => {
  if (!name) return '';
  return normalizeWhitespace(name).toUpperCase();
};

/**
 * Format ship name (capitalize each word)
 * 
 * @param {string} name - Ship name
 * @returns {string} Formatted ship name
 */
export const formatShipName = (name) => {
  if (!name) return '';
  return capitalizeWords(normalizeWhitespace(name));
};

/**
 * Parse certificate number
 * Extract just the number part from certificate strings
 * 
 * @param {string} certNo - Certificate number string
 * @returns {string} Cleaned certificate number
 */
export const parseCertificateNumber = (certNo) => {
  if (!certNo) return '';
  // Remove common prefixes
  return certNo
    .replace(/^(No\.|Number|#|Cert\.|Certificate)\s*/i, '')
    .trim();
};

/**
 * Compare strings for sorting (case-insensitive, Vietnamese-aware)
 * 
 * @param {string} a - First string
 * @param {string} b - Second string
 * @returns {number} -1, 0, or 1 for sorting
 */
export const compareStrings = (a, b) => {
  if (!a && !b) return 0;
  if (!a) return 1;
  if (!b) return -1;
  
  const aClean = removeVietnameseDiacritics(a).toLowerCase();
  const bClean = removeVietnameseDiacritics(b).toLowerCase();
  
  return aClean.localeCompare(bClean);
};

/**
 * Highlight search term in text
 * 
 * @param {string} text - Text to highlight in
 * @param {string} searchTerm - Term to highlight
 * @returns {string} Text with <mark> tags around matches
 */
export const highlightText = (text, searchTerm) => {
  if (!text || !searchTerm) return text;
  
  const regex = new RegExp(`(${searchTerm})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
};

/**
 * Generate initials from name
 * 
 * @param {string} name - Full name
 * @param {number} maxInitials - Maximum number of initials
 * @returns {string} Initials (e.g., "John Doe" → "JD")
 */
export const getInitials = (name, maxInitials = 2) => {
  if (!name) return '';
  
  const words = name.trim().split(/\s+/);
  const initials = words
    .slice(0, maxInitials)
    .map(word => word.charAt(0).toUpperCase())
    .join('');
  
  return initials;
};
