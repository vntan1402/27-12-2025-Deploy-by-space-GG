/**
 * Ship Cache Service
 * 
 * Centralized cache for ships data to avoid repeated API calls
 * - Stores ships in localStorage with session tracking
 * - Only fetches from API once per session
 * - Invalidates cache when new ship is added
 */

import { shipService } from './shipService';

const CACHE_KEY = 'ships_cache';
const SESSION_KEY = 'ships_session_id';

// Generate unique session ID
const generateSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Get or create session ID
const getSessionId = () => {
  let sessionId = sessionStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = generateSessionId();
    sessionStorage.setItem(SESSION_KEY, sessionId);
  }
  return sessionId;
};

export const shipCacheService = {
  /**
   * Get ships from cache or fetch from API
   * @param {boolean} forceRefresh - Force refresh from API
   * @returns {Promise<Array>} List of ships
   */
  getShips: async (forceRefresh = false) => {
    const currentSessionId = getSessionId();
    
    // Try to get from cache first
    if (!forceRefresh) {
      try {
        const cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
          const { sessionId, ships, timestamp } = JSON.parse(cached);
          
          // Check if cache is from current session
          if (sessionId === currentSessionId) {
            console.log('✅ [ShipCache] Using cached ships:', ships.length);
            return ships;
          } else {
            console.log('🔄 [ShipCache] New session detected, will refresh');
          }
        }
      } catch (e) {
        console.warn('[ShipCache] Failed to read cache:', e);
      }
    }
    
    // Fetch from API
    console.log('🌐 [ShipCache] Fetching ships from API...');
    try {
      const response = await shipService.getAllShips();
      const ships = response.data || response || [];
      
      // Ensure ships is array
      if (!Array.isArray(ships)) {
        console.error('[ShipCache] Response is not an array:', ships);
        return [];
      }
      
      // Save to cache
      const cacheData = {
        sessionId: currentSessionId,
        ships: ships,
        timestamp: Date.now()
      };
      localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
      console.log('✅ [ShipCache] Cached', ships.length, 'ships');
      
      return ships;
    } catch (error) {
      console.error('[ShipCache] Failed to fetch ships:', error);
      
      // Try to return stale cache if API fails
      try {
        const cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
          const { ships } = JSON.parse(cached);
          console.warn('[ShipCache] Using stale cache due to API error');
          return ships;
        }
      } catch (e) {
        // Ignore
      }
      
      throw error;
    }
  },

  /**
   * Invalidate cache and force refresh
   * Call this when a new ship is added
   */
  invalidateCache: () => {
    console.log('🗑️ [ShipCache] Cache invalidated');
    localStorage.removeItem(CACHE_KEY);
  },

  /**
   * Refresh cache from API
   * @returns {Promise<Array>} Updated list of ships
   */
  refreshCache: async () => {
    console.log('🔄 [ShipCache] Force refreshing cache...');
    return shipCacheService.getShips(true);
  },

  /**
   * Add a ship to cache without API call
   * Useful after creating a new ship
   * @param {Object} newShip - The newly created ship
   */
  addToCache: (newShip) => {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        const cacheData = JSON.parse(cached);
        cacheData.ships.push(newShip);
        cacheData.timestamp = Date.now();
        localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
        console.log('✅ [ShipCache] Added new ship to cache:', newShip.name);
      }
    } catch (e) {
      console.warn('[ShipCache] Failed to add to cache:', e);
      // Invalidate to force refresh next time
      shipCacheService.invalidateCache();
    }
  },

  /**
   * Update a ship in cache
   * @param {string} shipId - Ship ID to update
   * @param {Object} updatedShip - Updated ship data
   */
  updateInCache: (shipId, updatedShip) => {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        const cacheData = JSON.parse(cached);
        const index = cacheData.ships.findIndex(s => s.id === shipId);
        if (index !== -1) {
          cacheData.ships[index] = { ...cacheData.ships[index], ...updatedShip };
          cacheData.timestamp = Date.now();
          localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
          console.log('✅ [ShipCache] Updated ship in cache:', shipId);
        }
      }
    } catch (e) {
      console.warn('[ShipCache] Failed to update cache:', e);
    }
  },

  /**
   * Remove a ship from cache
   * @param {string} shipId - Ship ID to remove
   */
  removeFromCache: (shipId) => {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        const cacheData = JSON.parse(cached);
        cacheData.ships = cacheData.ships.filter(s => s.id !== shipId);
        cacheData.timestamp = Date.now();
        localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
        console.log('✅ [ShipCache] Removed ship from cache:', shipId);
      }
    } catch (e) {
      console.warn('[ShipCache] Failed to remove from cache:', e);
    }
  },

  /**
   * Get cached ships synchronously (if available)
   * Returns null if no cache
   */
  getCachedShipsSync: () => {
    try {
      const currentSessionId = getSessionId();
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        const { sessionId, ships } = JSON.parse(cached);
        if (sessionId === currentSessionId) {
          return ships;
        }
      }
    } catch (e) {
      // Ignore
    }
    return null;
  }
};

export default shipCacheService;
