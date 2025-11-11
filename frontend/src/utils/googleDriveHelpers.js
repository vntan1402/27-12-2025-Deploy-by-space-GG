/**
 * Google Drive Helper Functions
 * Utilities for handling Google Drive URLs and conversions
 */

/**
 * Convert Google Drive view link to thumbnail/direct image link
 * @param {string} url - Google Drive URL
 * @param {string} size - Thumbnail size (default: 'w1000')
 * @returns {string} - Direct image URL
 * 
 * @example
 * Input:  https://drive.google.com/file/d/FILE_ID/view?usp=drive_link
 * Output: https://drive.google.com/thumbnail?id=FILE_ID&sz=w1000
 * 
 * Note: Using thumbnail API instead of uc?export=view for better CORS support
 */
export const convertGoogleDriveUrl = (url, size = 'w1000') => {
  if (!url || typeof url !== 'string') return url;
  
  // Check if it's a Google Drive link
  if (url.includes('drive.google.com/file/d/')) {
    // Extract file ID from URL
    const fileIdMatch = url.match(/\/d\/([^\/\?]+)/);
    if (fileIdMatch && fileIdMatch[1]) {
      const fileId = fileIdMatch[1];
      // Use thumbnail API for better CORS support and faster loading
      return `https://drive.google.com/thumbnail?id=${fileId}&sz=${size}`;
    }
  }
  
  // Return original URL if not a Google Drive link
  return url;
};

/**
 * Check if URL is a Google Drive link
 * @param {string} url - URL to check
 * @returns {boolean} - True if Google Drive link
 */
export const isGoogleDriveUrl = (url) => {
  if (!url || typeof url !== 'string') return false;
  return url.includes('drive.google.com');
};

/**
 * Extract file ID from Google Drive URL
 * @param {string} url - Google Drive URL
 * @returns {string|null} - File ID or null if not found
 */
export const extractGoogleDriveFileId = (url) => {
  if (!url || typeof url !== 'string') return null;
  
  const fileIdMatch = url.match(/\/d\/([^\/\?]+)/);
  return fileIdMatch ? fileIdMatch[1] : null;
};

/**
 * Get embeddable Google Drive URL
 * @param {string} url - Google Drive URL
 * @returns {string} - Embeddable URL
 */
export const getGoogleDriveEmbedUrl = (url) => {
  const fileId = extractGoogleDriveFileId(url);
  if (fileId) {
    return `https://drive.google.com/file/d/${fileId}/preview`;
  }
  return url;
};

/**
 * Get downloadable Google Drive URL
 * @param {string} url - Google Drive URL
 * @returns {string} - Downloadable URL
 */
export const getGoogleDriveDownloadUrl = (url) => {
  const fileId = extractGoogleDriveFileId(url);
  if (fileId) {
    return `https://drive.google.com/uc?export=download&id=${fileId}`;
  }
  return url;
};
