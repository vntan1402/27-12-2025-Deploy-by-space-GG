import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';
import api from '../services/api';

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

  useEffect(() => {
    if (token) {
      verifyToken();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCompanyExpiry = async (companyName) => {
    try {
      console.log('🔍 [AuthContext] Fetching company expiry for:', companyName);
      
      // Fetch companies to get software_expiry
      const response = await api.get('/api/companies');
      const companies = response.data;
      
      console.log('📦 [AuthContext] Total companies fetched:', companies.length);
      
      // Find user's company
      const userCompany = companies.find(c => 
        c.name_en === companyName || 
        c.name_vn === companyName ||
        c.name === companyName
      );
      
      console.log('🏢 [AuthContext] Found user company:', userCompany?.name_en || userCompany?.name_vn);
      
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
