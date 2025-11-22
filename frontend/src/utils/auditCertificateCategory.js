/**
 * Audit Certificate Category Detection
 * Detect ISM/ISPS/MLC/CICA category from certificate name
 */

const CATEGORY_KEYWORDS = {
  'CICA': [
    'CREW ACCOMMODATION',
    'CERTIFICATE OF INSPECTION',
    'CREW ACCOMMODATION CERTIFICATE',
    'STATEMENT OF COMPLIANCE OF CREW ACCOMMODATION',
    'CICA'
  ],
  'ISM': [
    'SAFETY MANAGEMENT CERTIFICATE',
    'INTERIM SAFETY MANAGEMENT CERTIFICATE',
    'SMC',
    'DOCUMENT OF COMPLIANCE',
    'INTERIM DOCUMENT OF COMPLIANCE',
    'DOC',
    'ISM CODE'
  ],
  'ISPS': [
    'INTERNATIONAL SHIP SECURITY CERTIFICATE',
    'INTERIM INTERNATIONAL SHIP SECURITY CERTIFICATE',
    'ISSC',
    'SHIP SECURITY PLAN',
    'SSP',
    'ISPS CODE'
  ],
  'MLC': [
    'MARITIME LABOUR CERTIFICATE',
    'INTERIM MARITIME LABOUR CERTIFICATE',
    'MLC',
    'DECLARATION OF MARITIME LABOUR COMPLIANCE',
    'DMLC'
  ]
};

/**
 * Detect certificate category from certificate name
 * Priority: CICA > ISM > ISPS > MLC
 * 
 * @param {string} certName - Certificate name
 * @returns {string} - Category: 'CICA', 'ISM', 'ISPS', 'MLC', or 'Unknown'
 */
export const detectCertificateCategory = (certName) => {
  if (!certName) return 'Unknown';
  
  const certNameUpper = certName.toUpperCase().trim();
  
  // Check in priority order: CICA first (highest priority)
  const priorities = ['CICA', 'ISM', 'ISPS', 'MLC'];
  
  for (const category of priorities) {
    const keywords = CATEGORY_KEYWORDS[category];
    for (const keyword of keywords) {
      if (certNameUpper.includes(keyword)) {
        return category;
      }
    }
  }
  
  return 'Unknown';
};

/**
 * Get category badge color (Tailwind classes)
 * 
 * @param {string} category - Category name
 * @returns {string} - Tailwind color classes
 */
export const getCategoryBadgeColor = (category) => {
  const colors = {
    'ISM': 'bg-blue-100 text-blue-800',
    'ISPS': 'bg-green-100 text-green-800',
    'MLC': 'bg-purple-100 text-purple-800',
    'CICA': 'bg-orange-100 text-orange-800', // ⭐ NEW
    'Unknown': 'bg-gray-100 text-gray-800'
  };
  
  return colors[category] || colors['Unknown'];
};

/**
 * Get all available categories
 * 
 * @returns {Array} - Array of category names
 */
export const getAvailableCategories = () => {
  return ['ISM', 'ISPS', 'MLC', 'CICA'];
};

/**
 * Get category display name (localized)
 * 
 * @param {string} category - Category name
 * @param {string} language - Language code ('vi' or 'en')
 * @returns {string} - Display name
 */
export const getCategoryDisplayName = (category, language = 'en') => {
  const names = {
    'ISM': {
      'en': 'ISM - Safety Management',
      'vi': 'ISM - Quản lý an toàn'
    },
    'ISPS': {
      'en': 'ISPS - Ship Security',
      'vi': 'ISPS - An ninh tàu biển'
    },
    'MLC': {
      'en': 'MLC - Maritime Labour',
      'vi': 'MLC - Lao động hàng hải'
    },
    'CICA': {
      'en': 'CICA - Crew Accommodation',
      'vi': 'CICA - Chỗ ở thuyền viên'
    }
  };
  
  return names[category]?.[language] || category;
};
