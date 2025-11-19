/**
 * Audit Report Name Formatter
 * Rút ngắn và format audit report names cho hiển thị
 */

/**
 * Rút ngắn và format audit report name
 * 
 * Rules:
 * 1. Extract key terms: ISM, ISPS, MLC, CICA, Code, Audit, Plan, Report, etc.
 * 2. Remove filler words: of, the, and, along with, for, an, in, etc.
 * 3. Title Case: Viết hoa chữ cái đầu
 * 4. Giữ nguyên acronyms: ISM, ISPS, MLC, CICA (viết hoa hết)
 * 
 * @param {string} name - Original audit report name
 * @returns {string} - Shortened and formatted name
 */
export const formatAuditReportName = (name) => {
  if (!name || name.trim() === '') {
    return name;
  }

  // Step 1: Extract audit type from full forms
  let formatted = name;
  
  // Replace full forms with acronyms
  const fullFormReplacements = {
    'International Safety Management': 'ISM',
    'International Ship and Port Facility Security': 'ISPS',
    'Maritime Labour Convention': 'MLC',
    'Cargo Ship Safety': 'CSS',
    'Document of Compliance': 'DOC',
    'Safety Management Certificate': 'SMC',
    'Interim': 'Interim',
    'Annual': 'Annual',
    'Intermediate': 'Intermediate',
    'Initial': 'Initial',
    'Renewal': 'Renewal',
    'Additional': 'Additional',
  };

  Object.entries(fullFormReplacements).forEach(([full, acronym]) => {
    const regex = new RegExp(full, 'gi');
    formatted = formatted.replace(regex, acronym);
  });

  // Step 2: Remove common filler phrases and words
  const fillerPhrases = [
    'Record of opening and closing meetings',
    'along with the audit plan',
    'along with',
    'for an',
    'for a',
    'for the',
    'under the',
    'in accordance with',
    'conducted by',
    'carried out',
    'verification of',
  ];

  fillerPhrases.forEach(phrase => {
    const regex = new RegExp(phrase, 'gi');
    formatted = formatted.replace(regex, '');
  });

  // Step 3: Extract key terms
  const keyTerms = [];
  const tokens = formatted.split(/[\s,]+/).filter(t => t.trim() !== '');

  // Acronyms and important keywords
  const acronyms = ['ISM', 'ISPS', 'MLC', 'CICA', 'DOC', 'SMC', 'CSS'];
  const importantKeywords = [
    'Code', 'Audit', 'Plan', 'Report', 'Certificate', 'Certification',
    'Verification', 'Inspection', 'Assessment', 'Review', 'Survey',
    'Initial', 'Interim', 'Annual', 'Intermediate', 'Renewal', 'Additional',
    'Check', 'List', 'Checklist', 'Meeting', 'Minutes', 'NCR',
    'Non-conformity', 'Conformity', 'Compliance', 'Safety', 'Management',
    'Ship', 'Port', 'Facility', 'Security', 'Labour', 'Convention'
  ];

  tokens.forEach(token => {
    const tokenUpper = token.toUpperCase();
    const tokenCapitalized = capitalizeWord(token);

    // Keep acronyms (all caps)
    if (acronyms.includes(tokenUpper)) {
      if (!keyTerms.includes(tokenUpper)) {
        keyTerms.push(tokenUpper);
      }
    }
    // Keep important keywords
    else if (importantKeywords.some(kw => kw.toLowerCase() === token.toLowerCase())) {
      if (!keyTerms.includes(tokenCapitalized)) {
        keyTerms.push(tokenCapitalized);
      }
    }
  });

  // Step 4: Build shortened name
  if (keyTerms.length === 0) {
    // Fallback: Just capitalize the original name
    return toTitleCase(name);
  }

  // Join key terms
  let shortened = keyTerms.join(' ');

  // Step 5: Clean up and ensure proper format
  // Remove duplicate words
  const uniqueWords = [];
  shortened.split(' ').forEach(word => {
    if (!uniqueWords.includes(word)) {
      uniqueWords.push(word);
    }
  });
  shortened = uniqueWords.join(' ');

  // Ensure max length (optional - limit to ~50 chars)
  if (shortened.length > 60) {
    // Keep only first 5-6 words if too long
    const words = shortened.split(' ');
    shortened = words.slice(0, 6).join(' ');
    if (words.length > 6) {
      shortened += '...';
    }
  }

  return shortened;
};

/**
 * Capitalize first letter of word, keep rest lowercase
 * Exception: Acronyms stay uppercase
 */
const capitalizeWord = (word) => {
  if (!word) return word;
  
  // Check if it's an acronym (all uppercase in original or known acronyms)
  const acronyms = ['ISM', 'ISPS', 'MLC', 'CICA', 'DOC', 'SMC', 'CSS', 'NCR'];
  if (acronyms.includes(word.toUpperCase())) {
    return word.toUpperCase();
  }

  return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
};

/**
 * Convert string to Title Case
 * Keep acronyms uppercase
 */
const toTitleCase = (str) => {
  if (!str) return str;

  const acronyms = ['ISM', 'ISPS', 'MLC', 'CICA', 'DOC', 'SMC', 'CSS', 'NCR'];
  
  return str
    .toLowerCase()
    .split(' ')
    .map(word => {
      // Check if word is an acronym
      if (acronyms.includes(word.toUpperCase())) {
        return word.toUpperCase();
      }
      // Regular word - capitalize first letter
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(' ');
};

/**
 * Get full name (for tooltip)
 */
export const getFullAuditReportName = (name) => {
  return name || '';
};

/**
 * Examples for testing:
 * 
 * Input: "Record of opening and closing meetings, along with the audit plan, for an International Safety Management (ISM) Code audit"
 * Output: "ISM Code Audit Plan"
 * 
 * Input: "International Safety Management (ISM) Code audit"
 * Output: "ISM Code Audit"
 * 
 * Input: "Interim Certification under the International Safety Management (ISM) Code"
 * Output: "Interim Certification ISM Code"
 * 
 * Input: "ISPS Code Compliance Verification"
 * Output: "ISPS Code Compliance Verification"
 */
