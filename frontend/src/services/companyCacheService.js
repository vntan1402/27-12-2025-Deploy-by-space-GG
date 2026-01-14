/**
 * Company Cache Service
 * 
 * Centralized cache for company data to avoid repeated API calls
 * - Stores company info in localStorage with session tracking
 * - Only fetches from API once per session
 * - Invalidates cache when company data changes
 */

import api from './api';

const COMPANY_INFO_CACHE_KEY = 'company_info_cache';
const COMPANIES_LIST_CACHE_KEY = 'companies_list_cache';
const SESSION_KEY = 'company_session_id';

// Get or create session ID (shared with ship cache)
const getSessionId = () => {
  let sessionId = sessionStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem(SESSION_KEY, sessionId);
  }
  return sessionId;
};

export const companyCacheService = {
  /**
   * Get current user's company info from cache or API
   * @param {boolean} forceRefresh - Force refresh from API
   * @returns {Promise<Object>} Company info
   */
  getCompanyInfo: async (forceRefresh = false) => {
    const currentSessionId = getSessionId();
    
    // Try to get from cache first
    if (!forceRefresh) {
      try {
        const cached = localStorage.getItem(COMPANY_INFO_CACHE_KEY);
        if (cached) {
          const { sessionId, companyInfo, timestamp } = JSON.parse(cached);
          
          if (sessionId === currentSessionId) {
            console.log('✅ [CompanyCache] Using cached company info');
            return companyInfo;
          } else {
            console.log('🔄 [CompanyCache] New session detected, will refresh');
          }
        }
      } catch (e) {
        console.warn('[CompanyCache] Failed to read cache:', e);
      }
    }
    
    // Fetch from API
    console.log('🌐 [CompanyCache] Fetching company info from API...');
    try {
      const response = await api.get('/api/company');
      const companyInfo = response.data;
      
      // Save to cache
      const cacheData = {
        sessionId: currentSessionId,
        companyInfo: companyInfo,
        timestamp: Date.now()
      };
      localStorage.setItem(COMPANY_INFO_CACHE_KEY, JSON.stringify(cacheData));
      console.log('✅ [CompanyCache] Cached company info:', companyInfo?.name_en || companyInfo?.name_vn);
      
      return companyInfo;
    } catch (error) {
      console.error('[CompanyCache] Failed to fetch company info:', error);
      
      // Try to return stale cache if API fails
      try {
        const cached = localStorage.getItem(COMPANY_INFO_CACHE_KEY);
        if (cached) {
          const { companyInfo } = JSON.parse(cached);
          console.warn('[CompanyCache] Using stale cache due to API error');
          return companyInfo;
        }
      } catch (e) {
        // Ignore
      }
      
      throw error;
    }
  },

  /**
   * Get all companies list from cache or API
   * @param {boolean} forceRefresh - Force refresh from API
   * @returns {Promise<Array>} List of companies
   */
  getCompaniesList: async (forceRefresh = false) => {
    const currentSessionId = getSessionId();
    
    // Try to get from cache first
    if (!forceRefresh) {
      try {
        const cached = localStorage.getItem(COMPANIES_LIST_CACHE_KEY);
        if (cached) {
          const { sessionId, companies, timestamp } = JSON.parse(cached);
          
          if (sessionId === currentSessionId) {
            console.log('✅ [CompanyCache] Using cached companies list:', companies.length);
            return companies;
          } else {
            console.log('🔄 [CompanyCache] New session detected, will refresh');
          }
        }
      } catch (e) {
        console.warn('[CompanyCache] Failed to read cache:', e);
      }
    }
    
    // Fetch from API
    console.log('🌐 [CompanyCache] Fetching companies list from API...');
    try {
      const response = await api.get('/api/companies');
      const companies = response.data || [];
      
      // Save to cache
      const cacheData = {
        sessionId: currentSessionId,
        companies: companies,
        timestamp: Date.now()
      };
      localStorage.setItem(COMPANIES_LIST_CACHE_KEY, JSON.stringify(cacheData));
      console.log('✅ [CompanyCache] Cached', companies.length, 'companies');
      
      return companies;
    } catch (error) {
      console.error('[CompanyCache] Failed to fetch companies:', error);
      
      // Try to return stale cache if API fails
      try {
        const cached = localStorage.getItem(COMPANIES_LIST_CACHE_KEY);
        if (cached) {
          const { companies } = JSON.parse(cached);
          console.warn('[CompanyCache] Using stale cache due to API error');
          return companies;
        }
      } catch (e) {
        // Ignore
      }
      
      throw error;
    }
  },

  /**
   * Invalidate all company caches
   */
  invalidateCache: () => {
    console.log('🗑️ [CompanyCache] Cache invalidated');
    localStorage.removeItem(COMPANY_INFO_CACHE_KEY);
    localStorage.removeItem(COMPANIES_LIST_CACHE_KEY);
  },

  /**
   * Invalidate only company info cache
   */
  invalidateCompanyInfoCache: () => {
    console.log('🗑️ [CompanyCache] Company info cache invalidated');
    localStorage.removeItem(COMPANY_INFO_CACHE_KEY);
  },

  /**
   * Invalidate only companies list cache
   */
  invalidateCompaniesListCache: () => {
    console.log('🗑️ [CompanyCache] Companies list cache invalidated');
    localStorage.removeItem(COMPANIES_LIST_CACHE_KEY);
  },

  /**
   * Update company in cache
   * @param {Object} updatedCompany - Updated company data
   */
  updateCompanyInCache: (updatedCompany) => {
    try {
      // Update company info cache if it matches
      const infoCache = localStorage.getItem(COMPANY_INFO_CACHE_KEY);
      if (infoCache) {
        const cacheData = JSON.parse(infoCache);
        if (cacheData.companyInfo?.id === updatedCompany.id) {
          cacheData.companyInfo = { ...cacheData.companyInfo, ...updatedCompany };
          cacheData.timestamp = Date.now();
          localStorage.setItem(COMPANY_INFO_CACHE_KEY, JSON.stringify(cacheData));
          console.log('✅ [CompanyCache] Updated company info in cache');
        }
      }
      
      // Update companies list cache
      const listCache = localStorage.getItem(COMPANIES_LIST_CACHE_KEY);
      if (listCache) {
        const cacheData = JSON.parse(listCache);
        const index = cacheData.companies.findIndex(c => c.id === updatedCompany.id);
        if (index !== -1) {
          cacheData.companies[index] = { ...cacheData.companies[index], ...updatedCompany };
          cacheData.timestamp = Date.now();
          localStorage.setItem(COMPANIES_LIST_CACHE_KEY, JSON.stringify(cacheData));
          console.log('✅ [CompanyCache] Updated company in list cache');
        }
      }
    } catch (e) {
      console.warn('[CompanyCache] Failed to update cache:', e);
    }
  },

  /**
   * Get cached company info synchronously (if available)
   * Returns null if no cache
   */
  getCachedCompanyInfoSync: () => {
    try {
      const currentSessionId = getSessionId();
      const cached = localStorage.getItem(COMPANY_INFO_CACHE_KEY);
      if (cached) {
        const { sessionId, companyInfo } = JSON.parse(cached);
        if (sessionId === currentSessionId) {
          return companyInfo;
        }
      }
    } catch (e) {
      // Ignore
    }
    return null;
  },

  /**
   * Get cached companies list synchronously (if available)
   * Returns null if no cache
   */
  getCachedCompaniesListSync: () => {
    try {
      const currentSessionId = getSessionId();
      const cached = localStorage.getItem(COMPANIES_LIST_CACHE_KEY);
      if (cached) {
        const { sessionId, companies } = JSON.parse(cached);
        if (sessionId === currentSessionId) {
          return companies;
        }
      }
    } catch (e) {
      // Ignore
    }
    return null;
  }
};

export default companyCacheService;
