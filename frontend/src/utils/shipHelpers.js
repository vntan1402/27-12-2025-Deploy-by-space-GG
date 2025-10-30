/**
 * Ship Helper Functions
 * Utility functions for ship data formatting and display
 */

/**
 * Shorten class society name for display
 * @param {string} classSociety - Full class society name
 * @returns {string} - Shortened class society name
 */
export const shortenClassSociety = (classSociety) => {
  if (!classSociety) return '';
  
  const name = classSociety.trim();
  
  // Common abbreviations mapping
  const abbreviations = {
    'American Bureau of Shipping': 'ABS',
    'Bureau Veritas': 'BV',
    'China Classification Society': 'CCS',
    'Croatian Register of Shipping': 'CRS',
    'Det Norske Veritas': 'DNV',
    'Indian Register of Shipping': 'IRS',
    'Korean Register': 'KR',
    'Nippon Kaiji Kyokai': 'NK',
    'Polish Register of Shipping': 'PRS',
    'Registro Italiano Navale': 'RINA',
    'Russian Maritime Register of Shipping': 'RS',
  };
  
  // Check for exact match in abbreviations
  for (const [full, abbr] of Object.entries(abbreviations)) {
    if (name.toLowerCase().includes(full.toLowerCase())) {
      return abbr;
    }
  }
  
  // Special handling for known patterns
  
  // DNV GL or DNV - keep as is
  if (name.match(/^DNV[\s-]?GL$/i) || name.match(/^DNV$/i)) {
    return name;
  }
  
  // Lloyd's Register variants
  if (name.toLowerCase().includes("lloyd")) {
    return 'LR';
  }
  
  // Panama Maritime Documentation Services, Inc. → Panama Maritime
  if (name.toLowerCase().includes('panama maritime')) {
    return 'Panama Maritime';
  }
  
  // For names with commas, take first part if it's reasonably short
  if (name.includes(',')) {
    const firstPart = name.split(',')[0].trim();
    if (firstPart.length <= 30) {
      return firstPart;
    }
  }
  
  // For very long names (>40 chars), try to extract meaningful abbreviation
  if (name.length > 40) {
    // Take first 2-3 words
    const words = name.split(/\s+/);
    if (words.length >= 2) {
      return words.slice(0, 2).join(' ');
    }
  }
  
  // If name is already short (<=20 chars), return as is
  if (name.length <= 20) {
    return name;
  }
  
  // Default: return first 20 chars + "..."
  return name.substring(0, 20) + '...';
};

/**
 * Get ship type display name
 * @param {string} shipType - Ship type
 * @returns {string} - Display name
 */
export const getShipTypeDisplay = (shipType) => {
  if (!shipType) return '';
  return shipType;
};
