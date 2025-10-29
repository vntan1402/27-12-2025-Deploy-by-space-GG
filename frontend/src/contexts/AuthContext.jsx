import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [language, setLanguage] = useState(
    localStorage.getItem('language') || 'vi'
  );

  useEffect(() => {
    if (token) {
      verifyToken();
    } else {
      setLoading(false);
    }
  }, [token]);

  const verifyToken = async () => {
    try {
      const response = await authService.verifyToken();
      setUser(response.data);
    } catch (error) {
      console.error('Token verification failed:', error);
      // Don't logout immediately - just log the error
      // The token might still be valid even if verify endpoint doesn't exist
      // User data should already be in localStorage from login
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        setUser(JSON.parse(storedUser));
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
      
      return response;
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    authService.logout();
    setToken(null);
    setUser(null);
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
