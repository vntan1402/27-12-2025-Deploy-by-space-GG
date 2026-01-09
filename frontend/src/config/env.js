/**
 * Runtime Environment Configuration
 * 
 * This module provides access to environment variables that can be configured
 * at runtime (container startup) rather than build time.
 * 
 * Priority:
 * 1. window._env_ (runtime config from env-config.js)
 * 2. process.env (build-time config)
 * 3. Default values
 */

const getEnvVar = (key, defaultValue = '') => {
  // Check runtime config first (set by env-config.js at container startup)
  if (typeof window !== 'undefined' && window._env_ && window._env_[key]) {
    return window._env_[key];
  }
  
  // Fall back to build-time environment variables
  if (process.env[key]) {
    return process.env[key];
  }
  
  // Return default value
  return defaultValue;
};

const env = {
  // Backend API URL - can be configured at runtime via REACT_APP_BACKEND_URL
  BACKEND_URL: getEnvVar('REACT_APP_BACKEND_URL', 'http://localhost:8001'),
  
  // App version
  VERSION: getEnvVar('REACT_APP_VERSION', '2.0.0'),
};

export default env;
