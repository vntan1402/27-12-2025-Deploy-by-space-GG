import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { authService } from '../services/authService';
import api from '../services/api';
import { companyCacheService } from '../services/companyCacheService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [language, setLanguage] = useState(
    localStorage.getItem('language') || 'vi'
  );
  const [softwareExpiry, setSoftwareExpiry] = useState(
    localStorage.getItem('software_expiry') || null
  );
  const [isSoftwareExpired, setIsSoftwareExpired] = useState(
    localStorage.getItem('is_software_expired') === 'true'
  );
  
  // Flag to ensure verify-token only runs ONCE per session
  const hasVerifiedToken = useRef(false);
  const isVerifying = useRef(false);

  useEffect(() => {
    // Skip if already verified or currently verifying
    if (hasVerifiedToken.current || isVerifying.current) {
      console.log('🔄 [AuthContext] Skipping - already verified or verifying');
      if (loading) setLoading(false);
      return;
    }
    
    if (token) {
      // First, try to restore user from localStorage for instant UI
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser);
          setUser(parsedUser);
          console.log('✅ [AuthContext] Restored user from localStorage:', parsedUser.username);
          
          // Restore company expiry from localStorage (instant)
          const storedExpiry = localStorage.getItem('software_expiry');
          const storedIsExpired = localStorage.getItem('is_software_expired');
          if (storedExpiry) {
            setSoftwareExpiry(storedExpiry);
            setIsSoftwareExpired(storedIsExpired === 'true');
          }
          
          // Set loading to false immediately for faster page render
          setLoading(false);
          
          // Mark as verified - NO need to call API again
          hasVerifiedToken.current = true;
          
          // Only verify token in background on FIRST app load (not on navigation)
          // Check if this is a fresh page load by checking sessionStorage
          const sessionVerified = sessionStorage.getItem('token_verified');
          if (!sessionVerified) {
            console.log('🔐 [AuthContext] First load - verifying token in background');
            sessionStorage.setItem('token_verified', 'true');
            verifyTokenBackground();
          } else {
            console.log('✅ [AuthContext] Already verified this session - skipping API call');
          }
        } catch (e) {
          console.error('❌ [AuthContext] Failed to parse stored user:', e);
          verifyToken();
        }
      } else {
        // No stored user, must verify token
        verifyToken();
      }
    } else {
      setLoading(false);
    }
  }, [token]);

  // Background token verification (non-blocking) - runs only ONCE per session
  const verifyTokenBackground = async () => {
    if (isVerifying.current) {
      console.log('⏳ [AuthContext] Already verifying - skipping');
      return;
    }
    
    isVerifying.current = true;
    
    try {
      console.log('🔐 [AuthContext] Starting background token verification...');
      const response = await authService.verifyToken();
      const userData = response.data?.user || response.data;
      
      // Update user if data changed
      const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
      if (JSON.stringify(userData) !== JSON.stringify(storedUser)) {
        console.log('🔄 [AuthContext] User data updated from server');
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
      }
      
      // Refresh company expiry only if needed
      if (userData?.company) {
        await fetchCompanyExpiry(userData.company);
      }
      
      console.log('✅ [AuthContext] Background verification completed');
    } catch (error) {
      console.warn('⚠️ [AuthContext] Background token verification failed:', error.message);
      // Token might be invalid - logout only if 401
      if (error.response?.status === 401) {
        console.log('🔐 [AuthContext] Token expired, logging out');
        sessionStorage.removeItem('token_verified');
        logout();
      }
    } finally {
      isVerifying.current = false;
    }
  };

  const fetchCompanyExpiry = async (companyIdOrName) => {
    try {
      // Skip company expiry check if no company (e.g., system_admin)
      if (!companyIdOrName) {
        console.log('ℹ️ [AuthContext] No company assigned - skipping expiry check');
        return;
      }
      
      console.log('🔍 [AuthContext] Fetching company expiry for:', companyIdOrName);
      
      // Fetch companies to get software_expiry
      const response = await api.get('/api/companies');
      const companies = response.data;
      
      console.log('📦 [AuthContext] Total companies fetched:', companies.length);
      
      // Find user's company by ID (UUID) or name
      const userCompany = companies.find(c => 
        c.id === companyIdOrName ||
        c.name_en === companyIdOrName || 
        c.name_vn === companyIdOrName ||
        c.name === companyIdOrName
      );
      
      console.log('🏢 [AuthContext] Found user company:', userCompany?.name_en || userCompany?.name_vn || 'NOT FOUND');
      
      if (userCompany && userCompany.software_expiry) {
        const expiryDate = new Date(userCompany.software_expiry);
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Reset to start of day for accurate comparison
        const isExpired = expiryDate < today;
        
        console.log('📅 [AuthContext] Expiry Date:', expiryDate);
        console.log('📅 [AuthContext] Today:', today);
        console.log('🔴 [AuthContext] Is Expired:', isExpired);
        
        setSoftwareExpiry(userCompany.software_expiry);
        setIsSoftwareExpired(isExpired);
        
        localStorage.setItem('software_expiry', userCompany.software_expiry);
        localStorage.setItem('is_software_expired', isExpired.toString());
        
        console.log(`✅ [AuthContext] Software Expiry Status Set: ${isExpired ? 'EXPIRED' : 'ACTIVE'}`);
      } else {
        console.warn('⚠️ [AuthContext] No company found or no software_expiry field');
      }
    } catch (error) {
      console.error('❌ [AuthContext] Error fetching company expiry:', error);
    }
  };

  const verifyToken = async () => {
    try {
      const response = await authService.verifyToken();
      // Handle both formats: direct user object or wrapped in response
      const userData = response.data?.user || response.data;
      setUser(userData);
      
      // Fetch company expiry after verifying token
      if (userData && userData.company) {
        await fetchCompanyExpiry(userData.company);
      }
    } catch (error) {
      console.error('Token verification failed:', error);
      // Don't logout immediately - just log the error
      // The token might still be valid even if verify endpoint doesn't exist
      // User data should already be in localStorage from login
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
        // Also fetch company expiry
        if (parsedUser && parsedUser.company) {
          await fetchCompanyExpiry(parsedUser.company);
        }
      } else {
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await authService.login(username, password);
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      
      setToken(access_token);
      setUser(userData);
      
      // Fetch company expiry after login
      if (userData && userData.company) {
        await fetchCompanyExpiry(userData.company);
      }
      
      return response;
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    authService.logout();
    setToken(null);
    setUser(null);
    setSoftwareExpiry(null);
    setIsSoftwareExpired(false);
    localStorage.removeItem('software_expiry');
    localStorage.removeItem('is_software_expired');
    sessionStorage.removeItem('token_verified');
    hasVerifiedToken.current = false;
  };

  const toggleLanguage = () => {
    const newLanguage = language === 'vi' ? 'en' : 'vi';
    setLanguage(newLanguage);
    localStorage.setItem('language', newLanguage);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        language,
        softwareExpiry,
        isSoftwareExpired,
        login,
        logout,
        toggleLanguage,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
