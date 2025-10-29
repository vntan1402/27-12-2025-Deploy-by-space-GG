import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, language } = useAuth();
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [shake, setShake] = useState(false);

  // Load saved credentials from localStorage
  useEffect(() => {
    const savedUsername = localStorage.getItem('rememberedUsername');
    if (savedUsername) {
      setUsername(savedUsername);
      setRememberMe(true);
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!username || !password) {
      toast.error(language === 'vi' ? 'Vui lòng nhập đầy đủ thông tin' : 'Please fill in all fields');
      triggerShake();
      return;
    }

    setLoading(true);
    
    try {
      await login(username, password);
      
      // Save username if remember me is checked
      if (rememberMe) {
        localStorage.setItem('rememberedUsername', username);
      } else {
        localStorage.removeItem('rememberedUsername');
      }
      
      toast.success(language === 'vi' ? 'Đăng nhập thành công!' : 'Login successful!');
      navigate('/');
    } catch (error) {
      console.error('Login error:', error);
      toast.error(
        language === 'vi' 
          ? 'Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.' 
          : 'Login failed. Please check your credentials.'
      );
      triggerShake();
    } finally {
      setLoading(false);
    }
  };

  const triggerShake = () => {
    setShake(true);
    setTimeout(() => setShake(false), 650);
  };

  const fillDemoCredentials = () => {
    setUsername('admin1');
    setPassword('123456');
    toast.info(language === 'vi' ? 'Đã điền thông tin demo' : 'Demo credentials filled');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            {language === 'vi' ? 'Hệ thống quản lý tàu' : 'Ship Management System'}
          </h1>
          <p className="text-gray-600">
            {language === 'vi' ? 'Đăng nhập để tiếp tục' : 'Login to continue'}
          </p>
          <div className="mt-4 text-xs text-gray-500">
            Frontend V2.0.0
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Tên đăng nhập' : 'Username'}
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={language === 'vi' ? 'Nhập tên đăng nhập' : 'Enter username'}
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Mật khẩu' : 'Password'}
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={language === 'vi' ? 'Nhập mật khẩu' : 'Enter password'}
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {loading
              ? (language === 'vi' ? 'Đang đăng nhập...' : 'Logging in...')
              : (language === 'vi' ? 'Đăng nhập' : 'Login')
            }
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          <p>
            {language === 'vi' ? 'Phiên bản mới' : 'New Version'}: Frontend V2 🚀
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
