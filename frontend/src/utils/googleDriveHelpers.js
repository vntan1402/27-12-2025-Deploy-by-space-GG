/**
 * Google Drive Helper Functions
 * Utilities for handling Google Drive URLs and conversions
 */

/**
 * Convert Google Drive view link to direct image link via googleusercontent
 * @param {string} url - Google Drive URL
 * @param {string} size - Image width (default: 'w1000')
 * @returns {string} - Direct image URL
 * 
 * @example
 * Input:  https://drive.google.com/file/d/FILE_ID/view?usp=drive_link
 * Output: https://lh3.googleusercontent.com/d/FILE_ID=w1000
 * 
 * Note: Using googleusercontent.com for best CORS support and performance
 * Sizes: w100, w200, w500, w1000, w2000, etc.
 */
export const convertGoogleDriveUrl = (url, size = 'w1000') => {
  if (!url || typeof url !== 'string') return url;
  
  // Check if it's a Google Drive link
  if (url.includes('drive.google.com/file/d/')) {
    // Extract file ID from URL
    const fileIdMatch = url.match(/\/d\/([^\/\?]+)/);
    if (fileIdMatch && fileIdMatch[1]) {
      const fileId = fileIdMatch[1];
      // Use googleusercontent.com for direct image access (best CORS support)
      return `https://lh3.googleusercontent.com/d/${fileId}=${size}`;
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
