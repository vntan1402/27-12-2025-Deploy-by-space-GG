import { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Toaster } from './components/ui/sonner';
import { toast } from 'sonner';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [language, setLanguage] = useState(localStorage.getItem('language') || 'en');

  // Check for token in both localStorage and sessionStorage
  const getStoredToken = () => {
    return localStorage.getItem('token') || sessionStorage.getItem('token');
  };

  const [token, setToken] = useState(getStoredToken());

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // Verify token validity
      verifyToken();
    }
    setLoading(false);
  }, [token]);

  const verifyToken = async () => {
    try {
      // Try to get settings to verify token is still valid
      await axios.get(`${API}/settings`);
      // Token is valid, keep it
    } catch (error) {
      if (error.response?.status === 401) {
        // Token expired or invalid, clear it
        logout();
      }
    }
  };

  const login = async (credentials) => {
    try {
      const response = await axios.post(`${API}/auth/login`, credentials);
      const { access_token, user, remember_me } = response.data;
      
      setToken(access_token);
      setUser(user);
      
      // Store token based on remember_me preference
      if (remember_me) {
        localStorage.setItem('token', access_token);
        localStorage.setItem('remember_me', 'true');
        // Clear session token
        sessionStorage.removeItem('token');
      } else {
        // Use sessionStorage for session-only login
        sessionStorage.setItem('token', access_token);
        localStorage.removeItem('remember_me');
        // Clear persistent token
        localStorage.removeItem('token');
      }
      
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      toast.success(language === 'vi' ? 'Đăng nhập thành công!' : 'Login successful!');
      return true;
    } catch (error) {
      toast.error(language === 'vi' ? 'Đăng nhập thất bại!' : 'Login failed!');
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('remember_me');
    sessionStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    toast.info(language === 'vi' ? 'Đã đăng xuất' : 'Logged out');
  };

  const toggleLanguage = () => {
    const newLang = language === 'en' ? 'vi' : 'en';
    setLanguage(newLang);
    localStorage.setItem('language', newLang);
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      language,
      login,
      logout,
      toggleLanguage,
      isAuthenticated: !!token
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return isAuthenticated ? children : <Navigate to="/login" />;
};

// Language Translations
const translations = {
  en: {
    // Navigation
    introduction: "Introduction",
    guide: "Guide", 
    contact: "Contact",
    back: "Back",
    
    // Login Page
    loginTitle: "Ship Management System",
    loginSubtitle: "With AI Support",
    loginDescription: "Maritime document management system built with AI support to help manage documents and records related to ship management and operations automatically and user-friendly. Reducing time and effort for shipping companies.",
    systemNote: "The system is being developed and improved, so we need feedback from companies. All feedback can be sent to Email:",
    username: "Username",
    password: "Password",
    loginButton: "Login",
    version: "Version V.0.0.1",
    
    // Home Page
    homeTitle: "Ship Management System",
    accountManagement: "Account Management",
    documentManagement: "Document Management",
    certificates: "Certificates",
    inspectionRecords: "Inspection Records", 
    surveyReports: "Survey Reports",
    drawingsManuals: "Drawings & Manuals",
    otherDocuments: "Other Documents",
    addNew: "Add New",
    
    // Translations
    systemSettings: "System Settings", 
    systemGoogleDrive: "System Google Drive Configuration",
    accountControl: "Account Control",
    companyLogo: "Company Logo",
    addUser: "Add User",
    permissions: "Permissions",
    uploadLogo: "Upload Logo",
    
    // Contact
    contactTitle: "Please contact us through the following methods:",
    email: "Email",
    phone: "Phone",
    
    // Ship Details
    shipName: "Ship Name",
    class: "Class",
    flag: "Flag", 
    grossTonnage: "Gross Tonnage",
    deadweight: "Deadweight",
    certName: "Certificate Name",
    certNo: "Certificate No",
    issueDate: "Issue Date",
    validDate: "Valid Date",
    lastEndorse: "Last Endorse",
    nextSurvey: "Next Survey",
    
    // Permissions
    viewer: "Viewer",
    editor: "Editor", 
    manager: "Manager",
    admin: "Admin",
    superAdmin: "Super Admin",
    
    // AI Features
    aiAnalysis: "AI Analysis",
    smartSearch: "Smart Search",
    documentSummary: "Document Summary",
    complianceCheck: "Compliance Check",
    expiryAlert: "Expiry Alert"
  },
  vi: {
    // Navigation
    introduction: "Giới thiệu",
    guide: "Hướng dẫn",
    contact: "Liên hệ", 
    back: "Quay lại",
    
    // Login Page
    loginTitle: "Hệ thống quản lí tàu biển",
    loginSubtitle: "Với sự hỗ trợ AI",
    loginDescription: "Hệ thống quản lí dữ liệu tàu biển được xây dựng với sự hỗ trợ của công nghệ trí tuệ nhân tạo (AI) giúp quản lý các tài liệu, hồ sơ liên quan đến quản lý, vận hành khai thác tàu biển một cách tự động, thân thiện với người dùng. Giảm bớt thời gian và công sức cho các công ty vận tải biển.",
    systemNote: "Hệ thống đang được phát triển và hoàn thiện nên rất cần sự đóng góp ý kiến của các công ty. Mọi ý kiến đóng góp xin gửi về Email:",
    username: "Tên đăng nhập",
    password: "Mật khẩu",
    loginButton: "Đăng nhập",
    version: "Phiên bản V.0.0.1",
    
    // Home Page
    homeTitle: "Hệ thống quản lí tàu biển",
    accountManagement: "Quản lý tài khoản",
    documentManagement: "Quản lý tài liệu",
    certificates: "Giấy chứng nhận",
    inspectionRecords: "Hồ sơ đăng kiểm",
    surveyReports: "Báo cáo kiểm tra", 
    drawingsManuals: "Bản vẽ - Sổ tay",
    otherDocuments: "Hồ sơ khác",
    addNew: "Thêm",
    
    // Translations
    systemSettings: "Cài đặt hệ thống", 
    systemGoogleDrive: "Cấu hình Google Drive hệ thống",
    accountControl: "Quản lý tài khoản",
    companyLogo: "Logo công ty",
    addUser: "Thêm người dùng",
    permissions: "Phân quyền",
    uploadLogo: "Tải lên Logo",
    
    // Contact
    contactTitle: "Vui lòng liên hệ với chúng tôi qua các hình thức sau:",
    email: "Email",
    phone: "Điện thoại",
    
    // Ship Details
    shipName: "Tên tàu",
    class: "Hạng",
    flag: "Cờ",
    grossTonnage: "Tổng trọng tải",
    deadweight: "Trọng tải chết",
    certName: "Tên chứng chỉ",
    certNo: "Số chứng chỉ", 
    issueDate: "Ngày cấp",
    validDate: "Ngày hết hạn",
    lastEndorse: "Xác nhận cuối",
    nextSurvey: "Khảo sát tiếp theo",
    
    // Permissions
    viewer: "Người xem",
    editor: "Người chỉnh sửa",
    manager: "Quản lý",
    admin: "Quản trị viên", 
    superAdmin: "Siêu quản trị",
    
    // AI Features
    aiAnalysis: "Phân tích AI",
    smartSearch: "Tìm kiếm thông minh", 
    documentSummary: "Tóm tắt tài liệu",
    complianceCheck: "Kiểm tra tuân thủ",
    expiryAlert: "Cảnh báo hết hạn"
  }
};

// Login Page Component
const LoginPage = () => {
  const [credentials, setCredentials] = useState({ 
    username: '', 
    password: '', 
    remember_me: localStorage.getItem('remember_me') === 'true' 
  });
  const [currentPage, setCurrentPage] = useState('login');
  const { login, language, toggleLanguage } = useAuth();
  const navigate = useNavigate();
  
  const t = translations[language];

  const handleLogin = async (e) => {
    e.preventDefault();
    const success = await login(credentials);
    if (success) {
      navigate('/home');
    }
  };

  const NavigationBar = ({ currentPage, onNavigate }) => (
    <nav className="flex justify-center space-x-8 mb-8">
      <button
        onClick={() => onNavigate('introduction')}
        className={`px-6 py-2 rounded-full transition-all ${
          currentPage === 'introduction' 
            ? 'bg-blue-600 text-white shadow-lg' 
            : 'bg-white text-blue-600 hover:bg-blue-50 border border-blue-200'
        }`}
      >
        {t.introduction}
      </button>
      <button
        onClick={() => onNavigate('guide')}
        className={`px-6 py-2 rounded-full transition-all ${
          currentPage === 'guide'
            ? 'bg-blue-600 text-white shadow-lg'
            : 'bg-white text-blue-600 hover:bg-blue-50 border border-blue-200'
        }`}
      >
        {t.guide}
      </button>
      <button
        onClick={() => onNavigate('contact')}
        className={`px-6 py-2 rounded-full transition-all ${
          currentPage === 'contact'
            ? 'bg-blue-600 text-white shadow-lg'
            : 'bg-white text-blue-600 hover:bg-blue-50 border border-blue-200'
        }`}
      >
        {t.contact}
      </button>
    </nav>
  );

  if (currentPage === 'introduction') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-slate-50">
        <div className="container mx-auto px-6 py-12">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">{t.loginTitle}</h1>
            <p className="text-xl text-blue-600 mb-8">{t.loginSubtitle}</p>
          </div>

          <NavigationBar currentPage={currentPage} onNavigate={setCurrentPage} />

          <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-xl p-8 backdrop-blur-sm bg-opacity-95">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">{t.introduction}</h2>
            <p className="text-gray-600 leading-relaxed mb-6">
              {t.loginDescription}
            </p>
            <p className="text-gray-600 leading-relaxed">
              {t.systemNote} <a href="mailto:AiSMS@gmail.com" className="text-blue-600 hover:underline">AiSMS@gmail.com</a>
            </p>
            
            <div className="mt-8 text-center">
              <button
                onClick={() => setCurrentPage('login')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-full transition-all shadow-lg hover:shadow-xl"
              >
                {t.back}
              </button>
            </div>
          </div>

          <div className="text-center mt-8">
            <p className="text-sm text-gray-500">{t.loginTitle}</p>
            <p className="text-sm text-gray-400">{t.version}</p>
          </div>
        </div>
      </div>
    );
  }

  if (currentPage === 'guide') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-slate-50">
        <div className="container mx-auto px-6 py-12">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">{t.loginTitle}</h1>
            <p className="text-xl text-blue-600 mb-8">{t.loginSubtitle}</p>
          </div>

          <NavigationBar currentPage={currentPage} onNavigate={setCurrentPage} />

          <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-xl p-8 backdrop-blur-sm bg-opacity-95">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">{t.guide}</h2>
            <div className="space-y-4 text-gray-600">
              <div className="p-4 bg-blue-50 rounded-lg">
                <h3 className="font-semibold mb-2">1. {language === 'vi' ? 'Đăng nhập hệ thống' : 'System Login'}</h3>
                <p>{language === 'vi' ? 'Sử dụng tài khoản được cấp để đăng nhập vào hệ thống' : 'Use your assigned credentials to login to the system'}</p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <h3 className="font-semibold mb-2">2. {language === 'vi' ? 'Quản lý tài liệu' : 'Document Management'}</h3>
                <p>{language === 'vi' ? 'Quản lý các loại chứng chỉ, hồ sơ tàu theo từng danh mục' : 'Manage certificates and ship records by categories'}</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <h3 className="font-semibold mb-2">3. {language === 'vi' ? 'Phân quyền người dùng' : 'User Permissions'}</h3>
                <p>{language === 'vi' ? 'Hệ thống có 5 cấp độ quyền từ Viewer đến Super Admin' : 'System has 5 permission levels from Viewer to Super Admin'}</p>
              </div>
              <div className="p-4 bg-yellow-50 rounded-lg">
                <h3 className="font-semibold mb-2">4. {language === 'vi' ? 'Tính năng AI' : 'AI Features'}</h3>
                <p>{language === 'vi' ? 'Sử dụng AI để phân tích tài liệu và tìm kiếm thông minh' : 'Use AI for document analysis and smart search'}</p>
              </div>
            </div>
            
            <div className="mt-8 text-center">
              <button
                onClick={() => setCurrentPage('login')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-full transition-all shadow-lg hover:shadow-xl"
              >
                {t.back}
              </button>
            </div>
          </div>

          <div className="text-center mt-8">
            <p className="text-sm text-gray-500">{t.loginTitle}</p>
            <p className="text-sm text-gray-400">{t.version}</p>
          </div>
        </div>
      </div>
    );
  }

  if (currentPage === 'contact') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-slate-50">
        <div className="container mx-auto px-6 py-12">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">{t.loginTitle}</h1>
            <p className="text-xl text-blue-600 mb-8">{t.loginSubtitle}</p>
          </div>

          <NavigationBar currentPage={currentPage} onNavigate={setCurrentPage} />

          <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-xl p-8 backdrop-blur-sm bg-opacity-95">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">{t.contact}</h2>
            <p className="text-gray-600 mb-8">{t.contactTitle}</p>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-blue-50 p-6 rounded-xl">
                <h3 className="font-semibold text-lg mb-4 text-blue-800">{t.email}</h3>
                <p className="text-blue-600">
                  <a href="mailto:AiSMS@gmail.com" className="hover:underline">AiSMS@gmail.com</a>
                </p>
              </div>
              
              <div className="bg-green-50 p-6 rounded-xl">
                <h3 className="font-semibold text-lg mb-4 text-green-800">Zalo</h3>
                <p className="text-green-600">AiSMS (0989357282)</p>
              </div>
            </div>
            
            <div className="mt-8 text-center">
              <button
                onClick={() => setCurrentPage('login')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-full transition-all shadow-lg hover:shadow-xl"
              >
                {t.back}
              </button>
            </div>
          </div>

          <div className="text-center mt-8">
            <p className="text-sm text-gray-500">{t.loginTitle}</p>
            <p className="text-sm text-gray-400">{t.version}</p>
          </div>
        </div>
      </div>
    );
  }

  // Main Login Page
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-slate-50">
      <div className="container mx-auto px-6 py-12">
        {/* Language Toggle */}
        <div className="absolute top-4 right-4">
          <button
            onClick={toggleLanguage}
            className="bg-white hover:bg-gray-50 border border-gray-200 px-4 py-2 rounded-full text-sm font-medium transition-all shadow-sm"
          >
            {language === 'en' ? 'Tiếng Việt' : 'English'}
          </button>
        </div>

        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">{t.loginTitle}</h1>
          <p className="text-xl text-blue-600 mb-8">{t.loginSubtitle}</p>
        </div>

        <NavigationBar currentPage={currentPage} onNavigate={setCurrentPage} />

        <div className="max-w-md mx-auto bg-white rounded-2xl shadow-xl p-8 backdrop-blur-sm bg-opacity-95">
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t.username}
              </label>
              <input
                type="text"
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                value={credentials.username}
                onChange={(e) => setCredentials(prev => ({ ...prev, username: e.target.value }))}
                placeholder={t.username}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t.password}
              </label>
              <input
                type="password"
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                value={credentials.password}
                onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
                placeholder={t.password}
              />
            </div>

            {/* Remember Me Checkbox */}
            <div className="flex items-center">
              <input
                id="remember-me"
                type="checkbox"
                checked={credentials.remember_me}
                onChange={(e) => setCredentials(prev => ({ ...prev, remember_me: e.target.checked }))}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700">
                {language === 'vi' ? 'Ghi nhớ đăng nhập' : 'Remember me'}
              </label>
            </div>

            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg transition-all shadow-lg hover:shadow-xl font-medium"
            >
              {t.loginButton}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-500">
            <p>{language === 'vi' ? 'Tài khoản demo: admin / admin123' : 'Demo account: admin / admin123'}</p>
            <p className="mt-2 text-xs text-gray-400">
              {language === 'vi' ? 
                '"Ghi nhớ đăng nhập" sẽ giữ bạn đăng nhập trong 30 ngày' : 
                '"Remember me" will keep you logged in for 30 days'
              }
            </p>
          </div>
        </div>

        <div className="text-center mt-8">
          <p className="text-sm text-gray-500">{t.loginTitle}</p>
          <p className="text-sm text-gray-400">{t.version}</p>
        </div>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="App">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/home" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
            <Route path="/account-control" element={<ProtectedRoute><AccountControlPage /></ProtectedRoute>} />
            <Route path="/ships" element={<ProtectedRoute><ShipsPage /></ProtectedRoute>} />
            <Route path="/ships/:shipId" element={<ProtectedRoute><ShipDetailPage /></ProtectedRoute>} />
            <Route path="/" element={<Navigate to="/login" />} />
          </Routes>
          <Toaster position="top-right" />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
};

// HomePage Component (Main Dashboard)
const HomePage = () => {
  const { user, logout, language, toggleLanguage } = useAuth();
  const [ships, setShips] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('documents');
  const [hoveredCategory, setHoveredCategory] = useState(null);
  const [selectedShip, setSelectedShip] = useState(null);
  const [selectedSubMenu, setSelectedSubMenu] = useState('certificates');
  const [certificates, setCertificates] = useState([]);
  const [companyLogo, setCompanyLogo] = useState(null);
  const [hoverTimeout, setHoverTimeout] = useState(null);
  const [showAddRecord, setShowAddRecord] = useState(false);
  const navigate = useNavigate();
  
  const t = translations[language];

  useEffect(() => {
    fetchShips();
    fetchSettings();
  }, []);

  useEffect(() => {
    if (selectedShip && selectedSubMenu === 'certificates') {
      fetchCertificates(selectedShip.id);
    }
  }, [selectedShip, selectedSubMenu]);

  const fetchShips = async () => {
    try {
      const response = await axios.get(`${API}/ships`);
      setShips(response.data);
    } catch (error) {
      console.error('Failed to fetch ships:', error);
    }
  };

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      if (response.data.logo_url) {
        setCompanyLogo(response.data.logo_url);
      }
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    }
  };

  const fetchCertificates = async (shipId) => {
    try {
      const response = await axios.get(`${API}/ships/${shipId}/certificates`);
      setCertificates(response.data);
    } catch (error) {
      console.error('Failed to fetch certificates:', error);
      setCertificates([]);
    }
  };

  const handleCategoryMouseEnter = (categoryKey) => {
    if (hoverTimeout) {
      clearTimeout(hoverTimeout);
      setHoverTimeout(null);
    }
    setHoveredCategory(categoryKey);
  };

  const handleCategoryMouseLeave = () => {
    const timeout = setTimeout(() => {
      setHoveredCategory(null);
    }, 1000); // 1 second delay
    setHoverTimeout(timeout);
  };

  const handleShipClick = (ship, categoryKey = 'documents') => {
    // Clear any hover timeout
    if (hoverTimeout) {
      clearTimeout(hoverTimeout);
      setHoverTimeout(null);
    }
    
    // Set ship details persistently
    setSelectedShip(ship);
    setSelectedCategory(categoryKey);
    setHoveredCategory(null); // Hide dropdown after selection
    
    // Set default submenu based on category
    if (categoryKey === 'documents') {
      setSelectedSubMenu('certificates');
    } else {
      const categorySubMenus = subMenuItems[categoryKey];
      if (categorySubMenus && categorySubMenus.length > 0) {
        setSelectedSubMenu(categorySubMenus[0].key);
      }
    }
  };

  const categories = [
    { key: 'documents', name: language === 'vi' ? 'Hồ sơ tài liệu' : 'Document Portfolio', icon: '📁' },
    { key: 'crew', name: language === 'vi' ? 'Thuyền viên' : 'Crew Records', icon: '👥' },
    { key: 'ism', name: language === 'vi' ? 'Hồ sơ ISM' : 'ISM Records', icon: '📋' },
    { key: 'isps', name: language === 'vi' ? 'Hồ sơ ISPS' : 'ISPS Records', icon: '🛡️' },
    { key: 'mlc', name: language === 'vi' ? 'Hồ sơ MLC' : 'MLC Records', icon: '⚖️' },
    { key: 'supplies', name: language === 'vi' ? 'Vật tư' : 'Supplies', icon: '📦' },
  ];

  const subMenuItems = {
    documents: [
      { key: 'certificates', name: language === 'vi' ? 'Giấy chứng nhận' : 'Certificates' },
      { key: 'inspection_records', name: language === 'vi' ? 'Hồ sơ đăng kiểm' : 'Inspection Records' },
      { key: 'survey_reports', name: language === 'vi' ? 'Báo cáo kiểm tra' : 'Survey Reports' },
      { key: 'drawings_manuals', name: language === 'vi' ? 'Bản vẽ - Sổ tay' : 'Drawings & Manuals' },
      { key: 'other_documents', name: language === 'vi' ? 'Hồ sơ khác' : 'Other Documents' },
    ],
    crew: [
      { key: 'crew_list', name: language === 'vi' ? 'Danh sách thuyền viên' : 'Crew List' },
      { key: 'crew_certificates', name: language === 'vi' ? 'Chứng chỉ thuyền viên' : 'Crew Certificates' },
      { key: 'medical_records', name: language === 'vi' ? 'Hồ sơ y tế' : 'Medical Records' },
    ],
    ism: [
      { key: 'ism_certificate', name: language === 'vi' ? 'Chứng chỉ ISM' : 'ISM Certificate' },
      { key: 'safety_procedures', name: language === 'vi' ? 'Quy trình an toàn' : 'Safety Procedures' },
      { key: 'audit_reports', name: language === 'vi' ? 'Báo cáo kiểm toán' : 'Audit Reports' },
    ],
    isps: [
      { key: 'isps_certificate', name: language === 'vi' ? 'Chứng chỉ ISPS' : 'ISPS Certificate' },
      { key: 'security_plan', name: language === 'vi' ? 'Kế hoạch bảo mật' : 'Security Plan' },
      { key: 'security_assessments', name: language === 'vi' ? 'Đánh giá bảo mật' : 'Security Assessments' },
    ],
    mlc: [
      { key: 'mlc_certificate', name: language === 'vi' ? 'Chứng chỉ MLC' : 'MLC Certificate' },
      { key: 'labor_conditions', name: language === 'vi' ? 'Điều kiện lao động' : 'Labor Conditions' },
      { key: 'accommodation_reports', name: language === 'vi' ? 'Báo cáo nơi ở' : 'Accommodation Reports' },
    ],
    supplies: [
      { key: 'inventory', name: language === 'vi' ? 'Tồn kho' : 'Inventory' },
      { key: 'purchase_orders', name: language === 'vi' ? 'Đơn đặt hàng' : 'Purchase Orders' },
      { key: 'spare_parts', name: language === 'vi' ? 'Phụ tùng thay thế' : 'Spare Parts' },
    ],
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      return new Date(dateString).toLocaleDateString('vi-VN');
    } catch (error) {
      return '-';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-lg border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-800">{language === 'vi' ? 'Hệ thống quản lí tàu biển' : 'Ship Management System'}</h1>
              <span className="text-blue-600 text-sm">{language === 'vi' ? 'Với sự hỗ trợ AI' : 'With AI Support'}</span>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleLanguage}
                className="px-3 py-1 text-sm border border-gray-300 rounded-full hover:bg-gray-50 transition-all"
              >
                {language === 'en' ? 'VI' : 'EN'}
              </button>
              
              <button
                onClick={() => navigate('/account-control')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-all shadow-sm"
              >
                {language === 'vi' ? 'Cài đặt hệ thống' : 'System Settings'}
              </button>
              
              <span className="text-sm text-gray-600">
                {user?.full_name} ({language === 'vi' && user?.role === 'super_admin' ? 'Siêu quản trị' : 
                  language === 'vi' && user?.role === 'admin' ? 'Quản trị viên' :
                  language === 'vi' && user?.role === 'manager' ? 'Quản lý' :
                  language === 'vi' && user?.role === 'editor' ? 'Người chỉnh sửa' :
                  language === 'vi' && user?.role === 'viewer' ? 'Người xem' : user?.role})
              </span>
              
              <button
                onClick={logout}
                className="text-red-600 hover:text-red-700 px-3 py-1 rounded transition-all"
              >
                {language === 'vi' ? 'Đăng xuất' : 'Logout'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-4 gap-8">
          {/* Left Sidebar - Categories and Ships */}
          <div className="bg-blue-600 rounded-xl shadow-lg p-4 text-white">
            <h3 className="text-lg font-semibold mb-6">{language === 'vi' ? 'Danh mục quản lý' : 'Management Categories'}</h3>
            <div className="space-y-2">
              {categories.map((category) => (
                <div
                  key={category.key}
                  className="relative"
                  onMouseEnter={() => handleCategoryMouseEnter(category.key)}
                  onMouseLeave={handleCategoryMouseLeave}
                >
                  <button 
                    className="w-full text-left p-3 rounded-lg bg-blue-500 hover:bg-blue-400 transition-all border border-blue-400 text-white font-medium"
                    style={{
                      background: 'linear-gradient(135deg, #4a90e2, #357abd)',
                      border: '2px solid #2c5282'
                    }}
                  >
                    <span className="mr-3">{category.icon}</span>
                    {category.name}
                  </button>
                  
                  {/* Ships dropdown - now uses hoveredCategory instead of selectedCategory */}
                  {hoveredCategory === category.key && (
                    <div className="absolute left-full top-0 ml-2 bg-white border border-gray-200 rounded-lg shadow-xl p-4 w-64 z-10 text-gray-800">
                      <h4 className="font-medium mb-3 text-gray-700">{language === 'vi' ? 'Danh sách tàu' : 'Ships List'}</h4>
                      {ships.length === 0 ? (
                        <p className="text-gray-500 text-sm">{language === 'vi' ? 'Chưa có tàu nào' : 'No ships available'}</p>
                      ) : (
                        <div className="space-y-2">
                          {ships.map((ship) => (
                            <button
                              key={ship.id}
                              onClick={() => handleShipClick(ship, category.key)}
                              className="block w-full text-left p-2 rounded hover:bg-blue-50 transition-all text-sm border border-gray-100 hover:border-blue-200"
                            >
                              <div className="font-medium">{ship.name}</div>
                              <div className="text-xs text-gray-500">
                                IMO: {ship.imo_number}
                              </div>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            {/* Additional Management Buttons */}
            <div className="mt-6 space-y-2">
              <button 
                onClick={() => setShowAddRecord(true)}
                className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg transition-all shadow-sm font-medium"
                style={{
                  background: 'linear-gradient(135deg, #48bb78, #38a169)',
                  border: '2px solid #2f855a'
                }}
              >
                {language === 'vi' ? 'THÊM HỒ SƠ MỚI' : 'ADD NEW RECORD'}
              </button>
              
              <button
                onClick={() => navigate('/account-control')}
                className="w-full bg-blue-500 hover:bg-blue-600 text-white py-3 rounded-lg transition-all shadow-sm font-medium"
                style={{
                  background: 'linear-gradient(135deg, #4299e1, #3182ce)',
                  border: '2px solid #2b6cb0'
                }}
              >
                {language === 'vi' ? 'Cài đặt hệ thống' : 'System Settings'}
              </button>
              
              <button
                onClick={logout}
                className="w-full bg-red-600 hover:bg-red-700 text-white py-3 rounded-lg transition-all shadow-sm font-medium"
                style={{
                  background: 'linear-gradient(135deg, #f56565, #e53e3e)',
                  border: '2px solid #c53030'
                }}
              >
                LOG OUT
              </button>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-xl shadow-lg p-8 min-h-96">
              {/* Ship Details - now persists after click */}
              {selectedShip ? (
                <div>
                  {/* Ship Header with Photo */}
                  <div className="grid md:grid-cols-3 gap-6 mb-6">
                    <div className="md:col-span-1">
                      <div className="bg-gray-200 rounded-lg p-4 h-48 flex items-center justify-center">
                        <div className="text-center">
                          <div className="text-4xl mb-2">🚢</div>
                          <p className="font-semibold">SHIP PHOTO</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="md:col-span-2">
                      <div className="flex justify-between items-center mb-4">
                        <h2 className="text-2xl font-bold text-gray-800">
                          {language === 'vi' ? 'Hồ sơ tài liệu' : 'Document Portfolio'}
                        </h2>
                        <button
                          onClick={() => setSelectedShip(null)}
                          className="text-gray-400 hover:text-gray-600 text-xl px-2 py-1"
                          title={language === 'vi' ? 'Đóng chi tiết tàu' : 'Close ship details'}
                        >
                          ✕
                        </button>
                      </div>
                      
                      {/* Sub Menu */}
                      <div className="mb-4">
                        <div className="flex flex-wrap gap-2">
                          {subMenuItems[selectedCategory] && subMenuItems[selectedCategory].map((item) => (
                            <button
                              key={item.key}
                              onClick={() => setSelectedSubMenu(item.key)}
                              className={`px-4 py-2 rounded-lg text-sm transition-all ${
                                selectedSubMenu === item.key 
                                  ? 'bg-blue-600 text-white' 
                                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                              }`}
                            >
                              {item.name}
                            </button>
                          ))}
                        </div>
                      </div>
                      
                      {/* Ship Information */}
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-semibold">{language === 'vi' ? 'Tên tàu:' : 'Ship Name:'}</span>
                          <span className="ml-2">{selectedShip.name}</span>
                        </div>
                        <div>
                          <span className="font-semibold">{language === 'vi' ? 'Hạng:' : 'Class:'}</span>
                          <span className="ml-2">{selectedShip.class_society}</span>
                        </div>
                        <div>
                          <span className="font-semibold">{language === 'vi' ? 'Cờ:' : 'Flag:'}</span>
                          <span className="ml-2">{selectedShip.flag}</span>
                        </div>
                        <div>
                          <span className="font-semibold">{language === 'vi' ? 'Tổng trọng tải:' : 'Gross Tonnage:'}</span>
                          <span className="ml-2">{selectedShip.gross_tonnage?.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="font-semibold">{language === 'vi' ? 'Trọng tải chết:' : 'Deadweight:'}</span>
                          <span className="ml-2">{selectedShip.deadweight?.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="font-semibold">{language === 'vi' ? 'Năm đóng:' : 'Built Year:'}</span>
                          <span className="ml-2">{selectedShip.built_year}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Content based on selected category and submenu */}
                  {selectedCategory === 'documents' && selectedSubMenu === 'certificates' && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4 text-gray-800">
                        {language === 'vi' ? 'Danh mục Giấy chứng nhận' : 'Certificate List'}
                      </h3>
                      
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse border border-gray-300 text-sm">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-300 px-4 py-2 text-left">No.</th>
                              <th className="border border-gray-300 px-4 py-2 text-left">{language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'}</th>
                              <th className="border border-gray-300 px-4 py-2 text-left">{language === 'vi' ? 'Số chứng chỉ' : 'Certificate No'}</th>
                              <th className="border border-gray-300 px-4 py-2 text-left">{language === 'vi' ? 'Ngày cấp' : 'Issue Date'}</th>
                              <th className="border border-gray-300 px-4 py-2 text-left">{language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}</th>
                              <th className="border border-gray-300 px-4 py-2 text-left">{language === 'vi' ? 'Xác nhận cuối' : 'Last Endorse'}</th>
                              <th className="border border-gray-300 px-4 py-2 text-left">{language === 'vi' ? 'Khảo sát tiếp theo' : 'Next Survey'}</th>
                            </tr>
                          </thead>
                          <tbody>
                            {certificates.length === 0 ? (
                              <tr>
                                <td colSpan="7" className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                                  {language === 'vi' ? 'Chưa có chứng chỉ nào' : 'No certificates available'}
                                </td>
                              </tr>
                            ) : (
                              certificates.map((cert, index) => (
                                <tr 
                                  key={cert.id} 
                                  className="hover:bg-gray-50 cursor-pointer"
                                  onDoubleClick={() => {
                                    toast.info(language === 'vi' ? `Mở chứng chỉ: ${cert.cert_name}` : `Open certificate: ${cert.cert_name}`);
                                  }}
                                >
                                  <td className="border border-gray-300 px-4 py-2">{index + 1}</td>
                                  <td className="border border-gray-300 px-4 py-2">{cert.cert_name}</td>
                                  <td className="border border-gray-300 px-4 py-2">{cert.cert_no}</td>
                                  <td className="border border-gray-300 px-4 py-2">{formatDate(cert.issue_date)}</td>
                                  <td className="border border-gray-300 px-4 py-2">{formatDate(cert.valid_date)}</td>
                                  <td className="border border-gray-300 px-4 py-2">{formatDate(cert.last_endorse)}</td>
                                  <td className="border border-gray-300 px-4 py-2">{formatDate(cert.next_survey)}</td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                  
                  {/* Other categories content */}
                  {selectedCategory !== 'documents' || selectedSubMenu !== 'certificates' ? (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">
                        {selectedCategory === 'crew' ? '👥' : 
                         selectedCategory === 'ism' ? '📋' :
                         selectedCategory === 'isps' ? '🛡️' :
                         selectedCategory === 'mlc' ? '⚖️' :
                         selectedCategory === 'supplies' ? '📦' : '📋'}
                      </div>
                      <h3 className="text-xl font-semibold mb-2">
                        {subMenuItems[selectedCategory]?.find(item => item.key === selectedSubMenu)?.name || 
                         categories.find(cat => cat.key === selectedCategory)?.name}
                      </h3>
                      <p className="text-gray-600">
                        {language === 'vi' ? 'Danh mục này đang được phát triển' : 'This section is under development'}
                      </p>
                    </div>
                  ) : null}
                </div>
              ) : (
                // Default view when no ship is selected
                <div>
                  {companyLogo ? (
                    <div
                      className="w-full h-96 bg-cover bg-center rounded-lg flex items-center justify-center"
                      style={{ backgroundImage: `url(${BACKEND_URL}${companyLogo})` }}
                    >
                      <div className="bg-black bg-opacity-50 text-white p-6 rounded-lg text-center">
                        <h2 className="text-2xl font-bold mb-2">{language === 'vi' ? 'Chào mừng đến với' : 'Welcome to'}</h2>
                        <p className="text-lg">{language === 'vi' ? 'Hệ thống quản lí tàu biển' : 'Ship Management System'}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="w-full h-96 bg-gray-100 rounded-lg flex items-center justify-center">
                      <div className="text-center text-gray-500">
                        <div className="text-6xl mb-4">🚢</div>
                        <h2 className="text-2xl font-bold mb-2">{language === 'vi' ? 'Hệ thống quản lí tàu biển' : 'Ship Management System'}</h2>
                        <p className="mb-4">{language === 'vi' ? 'Chọn tàu từ danh mục bên trái để xem thông tin' : 'Select a ship from the left categories to view details'}</p>
                        <p className="text-sm">
                          {language === 'vi' ? 'Logo công ty sẽ hiển thị ở đây khi được tải lên' : 'Company logo will be displayed here when uploaded'}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* AI Features Section */}
                  <div className="mt-8 grid md:grid-cols-3 gap-4">
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
                      <h4 className="font-semibold text-blue-800 mb-2">{language === 'vi' ? 'Phân tích AI' : 'AI Analysis'}</h4>
                      <p className="text-sm text-blue-600">{language === 'vi' ? 'Phân tích tài liệu tự động' : 'Automated document analysis'}</p>
                    </div>
                    
                    <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-lg border border-green-200">
                      <h4 className="font-semibold text-green-800 mb-2">{language === 'vi' ? 'Tìm kiếm thông minh' : 'Smart Search'}</h4>
                      <p className="text-sm text-green-600">{language === 'vi' ? 'Tìm kiếm thông minh' : 'AI-powered search'}</p>
                    </div>
                    
                    <div className="bg-gradient-to-r from-purple-50 to-violet-50 p-4 rounded-lg border border-purple-200">
                      <h4 className="font-semibold text-purple-800 mb-2">{language === 'vi' ? 'Kiểm tra tuân thủ' : 'Compliance Check'}</h4>
                      <p className="text-sm text-purple-600">{language === 'vi' ? 'Kiểm tra tuân thủ' : 'Compliance monitoring'}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Add Record Modal */}
      {showAddRecord && (
        <AddRecordModal
          onClose={() => setShowAddRecord(false)}
          onSuccess={(type) => {
            setShowAddRecord(false);
            if (type === 'ship') {
              fetchShips();
            } else if (type === 'certificate' && selectedShip) {
              fetchCertificates(selectedShip.id);
            }
            toast.success(language === 'vi' ? 'Thêm hồ sơ thành công!' : 'Record added successfully!');
          }}
          language={language}
          selectedShip={selectedShip}
        />
      )}
    </div>
  );
};

// Account Control Page Component  
const AccountControlPage = () => {
  const { user, language } = useAuth();
  const [users, setUsers] = useState([]);
  const [showAddUser, setShowAddUser] = useState(false);
  const [showPermissions, setShowPermissions] = useState(false);
  const [showGoogleDrive, setShowGoogleDrive] = useState(false);
  const [showAIConfig, setShowAIConfig] = useState(false);
  const [showCompanyForm, setShowCompanyForm] = useState(false);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [logoFile, setLogoFile] = useState(null);
  const [gdriveConfig, setGdriveConfig] = useState({
    service_account_json: '',
    folder_id: ''
  });
  const [gdriveStatus, setGdriveStatus] = useState(null);
  const [syncLoading, setSyncLoading] = useState(false);
  const [aiConfig, setAiConfig] = useState({
    provider: 'openai',
    model: 'gpt-4o'
  });
  const [companies, setCompanies] = useState([]);
  const [companyData, setCompanyData] = useState({
    name_vn: '',
    name_en: '',
    address_vn: '',
    address_en: '',
    tax_id: '',
    gmail: '',
    zalo: '',
    system_expiry: '',
    gdrive_config: null
  });
  const navigate = useNavigate();
  
  const t = translations[language];

  useEffect(() => {
    if (user?.role === 'manager' || user?.role === 'admin' || user?.role === 'super_admin') {
      fetchUsers();
    }
    if (user?.role === 'admin' || user?.role === 'super_admin') {
      fetchGoogleDriveStatus();
    }
    if (user?.role === 'super_admin') {
      fetchAIConfig();
      fetchCompanies();
    }
  }, [user]);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      toast.error('Failed to fetch users');
    }
  };

  const fetchGoogleDriveStatus = async () => {
    try {
      const response = await axios.get(`${API}/gdrive/status`);
      setGdriveStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch Google Drive status:', error);
    }
  };

  const fetchAIConfig = async () => {
    try {
      const response = await axios.get(`${API}/ai-config`);
      setAiConfig(response.data);
    } catch (error) {
      console.error('Failed to fetch AI config:', error);
    }
  };

  const fetchCompanies = async () => {
    try {
      const response = await axios.get(`${API}/companies`);
      setCompanies(response.data);
    } catch (error) {
      console.error('Failed to fetch companies:', error);
    }
  };

  const handleLogoUpload = async () => {
    if (!logoFile) return;
    
    const formData = new FormData();
    formData.append('file', logoFile);
    
    try {
      const response = await axios.post(`${API}/upload/logo`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success(language === 'vi' ? 'Logo đã được cập nhật!' : 'Logo updated successfully!');
      setLogoFile(null);
    } catch (error) {
      toast.error(language === 'vi' ? 'Không thể tải lên logo' : 'Failed to upload logo');
    }
  };

  const handleGoogleDriveConfig = async () => {
    if (!gdriveConfig.service_account_json || !gdriveConfig.folder_id) {
      toast.error(language === 'vi' ? 'Vui lòng điền đầy đủ thông tin' : 'Please fill all required fields');
      return;
    }

    try {
      await axios.post(`${API}/gdrive/configure`, gdriveConfig);
      toast.success(language === 'vi' ? 'Cấu hình Google Drive thành công!' : 'Google Drive configured successfully!');
      setShowGoogleDrive(false);
      setGdriveConfig({ service_account_json: '', folder_id: '' });
      fetchGoogleDriveStatus();
    } catch (error) {
      toast.error(language === 'vi' ? 'Cấu hình Google Drive thất bại!' : 'Failed to configure Google Drive!');
    }
  };

  const handleSyncToGoogleDrive = async () => {
    setSyncLoading(true);
    try {
      await axios.post(`${API}/gdrive/sync-to-drive`);
      toast.success(language === 'vi' ? 'Đồng bộ lên Google Drive thành công!' : 'Synced to Google Drive successfully!');
      fetchGoogleDriveStatus();
    } catch (error) {
      toast.error(language === 'vi' ? 'Đồng bộ thất bại!' : 'Sync failed!');
    } finally {
      setSyncLoading(false);
    }
  };

  const handleSyncFromGoogleDrive = async () => {
    setSyncLoading(true);
    try {
      await axios.post(`${API}/gdrive/sync-from-drive`);
      toast.success(language === 'vi' ? 'Đồng bộ từ Google Drive thành công!' : 'Synced from Google Drive successfully!');
      fetchGoogleDriveStatus();
    } catch (error) {
      toast.error(language === 'vi' ? 'Đồng bộ thất bại!' : 'Sync failed!');
    } finally {
      setSyncLoading(false);
    }
  };

  const handleAIConfigUpdate = async () => {
    try {
      await axios.post(`${API}/ai-config`, aiConfig);
      toast.success(language === 'vi' ? 'Cấu hình AI thành công!' : 'AI configuration updated successfully!');
      setShowAIConfig(false);
      fetchAIConfig();
    } catch (error) {
      toast.error(language === 'vi' ? 'Cấu hình AI thất bại!' : 'Failed to update AI configuration!');
    }
  };

  const handleCreateCompany = async () => {
    if (!companyData.name_vn || !companyData.name_en || !companyData.tax_id) {
      toast.error(language === 'vi' ? 'Vui lòng điền đầy đủ thông tin bắt buộc' : 'Please fill all required fields');
      return;
    }

    try {
      const payload = {
        ...companyData,
        system_expiry: companyData.system_expiry ? new Date(companyData.system_expiry).toISOString() : null
      };
      
      await axios.post(`${API}/companies`, payload);
      toast.success(language === 'vi' ? 'Công ty đã được tạo thành công!' : 'Company created successfully!');
      setShowCompanyForm(false);
      setCompanyData({
        name_vn: '',
        name_en: '',
        address_vn: '',
        address_en: '',
        tax_id: '',
        gmail: '',
        zalo: '',
        system_expiry: '',
        gdrive_config: null
      });
      fetchCompanies();
    } catch (error) {
      toast.error(language === 'vi' ? 'Không thể tạo công ty!' : 'Failed to create company!');
    }
  };

  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-lg border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-800">{language === 'vi' ? 'Cài đặt hệ thống' : 'System Settings'}</h1>
            <button
              onClick={() => navigate('/home')}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-all"
            >
              {t.back}
            </button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Company Logo Section */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">{t.companyLogo}</h3>
            <div className="space-y-4">
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setLogoFile(e.target.files[0])}
                className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              <button
                onClick={handleLogoUpload}
                disabled={!logoFile}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white py-2 rounded-lg transition-all"
              >
                {t.uploadLogo}
              </button>
            </div>
          </div>

          {/* User Management */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">{language === 'vi' ? 'Quản lý người dùng' : 'User Management'}</h3>
            <div className="space-y-4">
              <button
                onClick={() => setShowAddUser(true)}
                className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg transition-all"
              >
                {t.addUser}
              </button>
              
              <button
                onClick={() => setShowPermissions(true)}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg transition-all"
              >
                {t.permissions}
              </button>
            </div>
          </div>

          {/* System Google Drive Configuration - Admin Only */}
          {isAdmin && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">
                {language === 'vi' ? 'Cấu hình Google Drive hệ thống' : 'System Google Drive Configuration'}
              </h3>
              
              {/* Google Drive Status */}
              {gdriveStatus && (
                <div className="mb-4 p-3 rounded-lg bg-gray-50">
                  <div className="text-sm space-y-1">
                    <div className={`font-medium ${gdriveStatus.configured ? 'text-green-600' : 'text-red-600'}`}>
                      {language === 'vi' ? 'Trạng thái:' : 'Status:'} {gdriveStatus.configured ? 
                        (language === 'vi' ? 'Đã cấu hình' : 'Configured') : 
                        (language === 'vi' ? 'Chưa cấu hình' : 'Not configured')}
                    </div>
                    {gdriveStatus.configured && (
                      <>
                        <div className="text-gray-600">
                          {language === 'vi' ? 'Files local:' : 'Local files:'} {gdriveStatus.local_files}
                        </div>
                        <div className="text-gray-600">
                          {language === 'vi' ? 'Files Google Drive:' : 'Drive files:'} {gdriveStatus.drive_files}
                        </div>
                        {gdriveStatus.last_sync && (
                          <div className="text-gray-600">
                            {language === 'vi' ? 'Đồng bộ cuối:' : 'Last sync:'} {new Date(gdriveStatus.last_sync).toLocaleString()}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}
              
              <div className="space-y-3">
                <button
                  onClick={() => setShowGoogleDrive(true)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg transition-all"
                >
                  {language === 'vi' ? 'Cấu hình Google Drive hệ thống' : 'Configure System Google Drive'}
                </button>
                
                {gdriveStatus?.configured && (
                  <>
                    <button
                      onClick={handleSyncToGoogleDrive}
                      disabled={syncLoading}
                      className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white py-2 rounded-lg transition-all"
                    >
                      {syncLoading ? '⏳' : '☁️↑'} {language === 'vi' ? 'Đồng bộ lên Drive' : 'Sync to Drive'}
                    </button>
                    
                    <button
                      onClick={handleSyncFromGoogleDrive}
                      disabled={syncLoading}
                      className="w-full bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white py-2 rounded-lg transition-all"
                    >
                      {syncLoading ? '⏳' : '☁️↓'} {language === 'vi' ? 'Đồng bộ từ Drive' : 'Sync from Drive'}
                    </button>
                  </>
                )}
              </div>
            </div>
          )}

          {/* AI Provider Configuration - Super Admin Only */}
          {user?.role === 'super_admin' && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">
                {language === 'vi' ? 'Cấu hình AI' : 'AI Configuration'}
              </h3>
              
              {/* Current AI Config Status */}
              <div className="mb-4 p-3 rounded-lg bg-gray-50">
                <div className="text-sm space-y-1">
                  <div className="font-medium text-blue-600">
                    {language === 'vi' ? 'Nhà cung cấp hiện tại:' : 'Current Provider:'} {aiConfig.provider.toUpperCase()}
                  </div>
                  <div className="text-gray-600">
                    {language === 'vi' ? 'Mô hình:' : 'Model:'} {aiConfig.model}
                  </div>
                </div>
              </div>
              
              <div className="space-y-3">
                <button
                  onClick={() => setShowAIConfig(true)}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg transition-all"
                >
                  {language === 'vi' ? 'Cấu hình AI' : 'Configure AI'}
                </button>
              </div>
            </div>
          )}

          {/* Company Management - Super Admin Only */}
          {user?.role === 'super_admin' && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">
                {language === 'vi' ? 'Quản lý công ty' : 'Company Management'}
              </h3>
              
              {/* Companies List */}
              {companies.length > 0 && (
                <div className="mb-4 p-3 rounded-lg bg-gray-50">
                  <div className="text-sm font-medium text-gray-700 mb-2">
                    {language === 'vi' ? 'Công ty hiện có:' : 'Existing Companies:'}
                  </div>
                  <div className="space-y-1">
                    {companies.slice(0, 3).map((company) => (
                      <div key={company.id} className="text-xs text-gray-600">
                        {company.name_vn} - {company.tax_id}
                      </div>
                    ))}
                    {companies.length > 3 && (
                      <div className="text-xs text-gray-500">
                        {language === 'vi' ? `+${companies.length - 3} công ty khác` : `+${companies.length - 3} more companies`}
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              <div className="space-y-3">
                <button
                  onClick={() => setShowCompanyForm(true)}
                  className="w-full bg-orange-600 hover:bg-orange-700 text-white py-2 rounded-lg transition-all"
                >
                  {language === 'vi' ? 'Thêm công ty mới' : 'Add New Company'}
                </button>
              </div>
            </div>
          )}

          {/* Users List */}
          <div className="bg-white rounded-xl shadow-lg p-6 lg:col-span-full">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">{language === 'vi' ? 'Danh sách người dùng' : 'Users List'}</h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {users.map((userItem) => (
                <div key={userItem.id} className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-all">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-800">{userItem.full_name}</p>
                      <p className="text-sm text-gray-600">{userItem.username}</p>
                      <p className="text-xs text-blue-600">{userItem.role === 'super_admin' ? (language === 'vi' ? 'Siêu quản trị' : 'Super Admin') :
                        userItem.role === 'admin' ? (language === 'vi' ? 'Quản trị viên' : 'Admin') :
                        userItem.role === 'manager' ? (language === 'vi' ? 'Quản lý' : 'Manager') :
                        userItem.role === 'editor' ? (language === 'vi' ? 'Người chỉnh sửa' : 'Editor') :
                        (language === 'vi' ? 'Người xem' : 'Viewer')}</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={selectedUsers.includes(userItem.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedUsers([...selectedUsers, userItem.id]);
                        } else {
                          setSelectedUsers(selectedUsers.filter(id => id !== userItem.id));
                        }
                      }}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Google Drive Configuration Modal */}
        {showGoogleDrive && (
          <GoogleDriveModal
            config={gdriveConfig}
            setConfig={setGdriveConfig}
            onClose={() => setShowGoogleDrive(false)}
            onSave={handleGoogleDriveConfig}
            language={language}
          />
        )}

        {/* Permission Assignment Modal */}
        {showPermissions && (
          <PermissionModal
            selectedUsers={selectedUsers}
            onClose={() => setShowPermissions(false)}
            onSuccess={() => {
              setShowPermissions(false);
              setSelectedUsers([]);
              fetchUsers();
            }}
          />
        )}
      </div>
    </div>
  );
};

// Google Drive Configuration Modal Component
const GoogleDriveModal = ({ config, setConfig, onClose, onSave, language }) => {
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" 
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? 'Cấu hình Google Drive hệ thống' : 'System Google Drive Configuration'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Service Account JSON' : 'Service Account JSON'}
            </label>
            <textarea
              value={config.service_account_json}
              onChange={(e) => setConfig(prev => ({ ...prev, service_account_json: e.target.value }))}
              placeholder={language === 'vi' ? 'Paste service account JSON key tại đây...' : 'Paste service account JSON key here...'}
              className="w-full h-40 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
            <p className="text-xs text-gray-500 mt-1">
              {language === 'vi' ? 'Tạo Service Account trong Google Cloud Console và download JSON key' : 'Create Service Account in Google Cloud Console and download JSON key'}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Google Drive Folder ID' : 'Google Drive Folder ID'}
            </label>
            <input
              type="text"
              value={config.folder_id}
              onChange={(e) => setConfig(prev => ({ ...prev, folder_id: e.target.value }))}
              placeholder="1abcDEFghiJKLmnopQRStuv2wxYZ"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              {language === 'vi' ? 'Folder ID từ URL Google Drive: drive.google.com/drive/folders/[FOLDER_ID]' : 'Folder ID from Google Drive URL: drive.google.com/drive/folders/[FOLDER_ID]'}
            </p>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-medium text-yellow-800 mb-2">
              {language === 'vi' ? 'Hướng dẫn thiết lập:' : 'Setup Instructions:'}
            </h4>
            <ol className="text-sm text-yellow-700 space-y-1">
              <li>1. {language === 'vi' ? 'Tạo project trong Google Cloud Console' : 'Create project in Google Cloud Console'}</li>
              <li>2. {language === 'vi' ? 'Enable Google Drive API' : 'Enable Google Drive API'}</li>
              <li>3. {language === 'vi' ? 'Tạo Service Account và download JSON key' : 'Create Service Account and download JSON key'}</li>
              <li>4. {language === 'vi' ? 'Tạo folder trong Google Drive và share với service account email' : 'Create folder in Google Drive and share with service account email'}</li>
              <li>5. {language === 'vi' ? 'Copy Folder ID từ URL' : 'Copy Folder ID from URL'}</li>
            </ol>
          </div>
        </div>

        <div className="flex justify-end space-x-4 mt-8">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
          >
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          <button
            onClick={onSave}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all"
          >
            {language === 'vi' ? 'Lưu cấu hình' : 'Save Configuration'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Permission Modal Component
const PermissionModal = ({ selectedUsers, onClose, onSuccess }) => {
  const { language } = useAuth();
  const [permissions, setPermissions] = useState({
    categories: [],
    departments: [],
    sensitivity_levels: [],
    permissions: []
  });

  const t = translations[language];

  const categories = ['certificates', 'inspection_records', 'survey_reports', 'drawings_manuals', 'other_documents'];
  const departments = ['technical', 'operations', 'safety', 'commercial', 'crewing'];
  const sensitivityLevels = ['public', 'internal', 'confidential', 'restricted'];
  const permissionTypes = ['read', 'write', 'delete', 'manage_users', 'system_control'];

  const handleSubmit = async () => {
    try {
      await axios.post(`${API}/permissions/assign`, {
        user_ids: selectedUsers,
        ...permissions
      });
      toast.success(language === 'vi' ? 'Phân quyền thành công!' : 'Permissions assigned successfully!');
      onSuccess();
    } catch (error) {
      toast.error(language === 'vi' ? 'Phân quyền thất bại!' : 'Failed to assign permissions!');
    }
  };

  // Handle clicking outside the modal content
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" 
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">{t.permissions}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>
        
        <div className="grid md:grid-cols-2 gap-8">
          {/* Categories */}
          <div>
            <h3 className="font-semibold mb-3">{language === 'vi' ? 'Loại tài liệu' : 'Document Categories'}</h3>
            <div className="space-y-2">
              {categories.map(cat => (
                <label key={cat} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={permissions.categories.includes(cat)}
                    onChange={(e) => {
                      const newCats = e.target.checked
                        ? [...permissions.categories, cat]
                        : permissions.categories.filter(c => c !== cat);
                      setPermissions(prev => ({ ...prev, categories: newCats }));
                    }}
                    className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="capitalize">{cat.replace('_', ' ')}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Departments */}
          <div>
            <h3 className="font-semibold mb-3">{language === 'vi' ? 'Phòng ban' : 'Departments'}</h3>
            <div className="space-y-2">
              {departments.map(dept => (
                <label key={dept} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={permissions.departments.includes(dept)}
                    onChange={(e) => {
                      const newDepts = e.target.checked
                        ? [...permissions.departments, dept]
                        : permissions.departments.filter(d => d !== dept);
                      setPermissions(prev => ({ ...prev, departments: newDepts }));
                    }}
                    className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="capitalize">{dept}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Sensitivity Levels */}
          <div>
            <h3 className="font-semibold mb-3">{language === 'vi' ? 'Mức độ bảo mật' : 'Sensitivity Levels'}</h3>
            <div className="space-y-2">
              {sensitivityLevels.map(level => (
                <label key={level} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={permissions.sensitivity_levels.includes(level)}
                    onChange={(e) => {
                      const newLevels = e.target.checked
                        ? [...permissions.sensitivity_levels, level]
                        : permissions.sensitivity_levels.filter(l => l !== level);
                      setPermissions(prev => ({ ...prev, sensitivity_levels: newLevels }));
                    }}
                    className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="capitalize">{level}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Permission Types */}
          <div>
            <h3 className="font-semibold mb-3">{language === 'vi' ? 'Quyền hạn' : 'Permissions'}</h3>
            <div className="space-y-2">
              {permissionTypes.map(perm => (
                <label key={perm} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={permissions.permissions.includes(perm)}
                    onChange={(e) => {
                      const newPerms = e.target.checked
                        ? [...permissions.permissions, perm]
                        : permissions.permissions.filter(p => p !== perm);
                      setPermissions(prev => ({ ...prev, permissions: newPerms }));
                    }}
                    className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="capitalize">{perm.replace('_', ' ')}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-4 mt-8">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
          >
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          <button
            onClick={handleSubmit}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all"
          >
            {language === 'vi' ? 'Áp dụng' : 'Apply'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Add Record Modal Component
const AddRecordModal = ({ onClose, onSuccess, language, selectedShip }) => {
  const [recordType, setRecordType] = useState('ship');
  const [shipData, setShipData] = useState({
    name: '',
    imo_number: '',
    class_society: '',
    flag: '',
    gross_tonnage: '',
    deadweight: '',
    built_year: ''
  });
  const [certificateData, setCertificateData] = useState({
    ship_id: selectedShip?.id || '',
    cert_name: '',
    cert_no: '',
    issue_date: '',
    valid_date: '',
    last_endorse: '',
    next_survey: '',
    category: 'certificates',
    sensitivity_level: 'internal'
  });
  const [documentData, setDocumentData] = useState({
    title: '',
    category: 'other_documents',
    description: '',
    file: null
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleSubmitShip = async () => {
    try {
      setIsSubmitting(true);
      const shipPayload = {
        ...shipData,
        gross_tonnage: parseFloat(shipData.gross_tonnage),
        deadweight: parseFloat(shipData.deadweight),
        built_year: parseInt(shipData.built_year)
      };
      
      const response = await axios.post(`${API}/ships`, shipPayload);
      onSuccess('ship');
      toast.success(language === 'vi' ? 'Tàu đã được thêm thành công!' : 'Ship added successfully!');
    } catch (error) {
      toast.error(language === 'vi' ? 'Không thể thêm tàu!' : 'Failed to add ship!');
      console.error('Ship creation error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitCertificate = async () => {
    try {
      setIsSubmitting(true);
      const certPayload = {
        ...certificateData,
        issue_date: new Date(certificateData.issue_date).toISOString(),
        valid_date: new Date(certificateData.valid_date).toISOString(),
        last_endorse: certificateData.last_endorse ? new Date(certificateData.last_endorse).toISOString() : null,
        next_survey: certificateData.next_survey ? new Date(certificateData.next_survey).toISOString() : null
      };
      
      const response = await axios.post(`${API}/certificates`, certPayload);
      onSuccess('certificate');
      toast.success(language === 'vi' ? 'Chứng chỉ đã được thêm thành công!' : 'Certificate added successfully!');
    } catch (error) {
      toast.error(language === 'vi' ? 'Không thể thêm chứng chỉ!' : 'Failed to add certificate!');
      console.error('Certificate creation error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitDocument = async () => {
    try {
      setIsSubmitting(true);
      // For now, create a basic document record (file upload can be enhanced later)
      const docPayload = {
        title: documentData.title,
        category: documentData.category,
        description: documentData.description,
        ship_id: selectedShip?.id || null
      };
      
      // This would need a separate endpoint for documents in the backend
      toast.info(language === 'vi' ? 'Tính năng tải lên tài liệu đang được phát triển' : 'Document upload feature is under development');
      onSuccess('document');
    } catch (error) {
      toast.error(language === 'vi' ? 'Không thể thêm tài liệu!' : 'Failed to add document!');
      console.error('Document creation error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = () => {
    if (recordType === 'ship') {
      handleSubmitShip();
    } else if (recordType === 'certificate') {
      handleSubmitCertificate();
    } else if (recordType === 'document') {
      handleSubmitDocument();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" 
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? 'Thêm hồ sơ mới' : 'Add New Record'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Record Type Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            {language === 'vi' ? 'Loại hồ sơ' : 'Record Type'}
          </label>
          <div className="flex space-x-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="ship"
                checked={recordType === 'ship'}
                onChange={(e) => setRecordType(e.target.value)}
                className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500"
              />
              <span>{language === 'vi' ? 'Tàu' : 'Ship'}</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="certificate"
                checked={recordType === 'certificate'}
                onChange={(e) => setRecordType(e.target.value)}
                className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500"
              />
              <span>{language === 'vi' ? 'Chứng chỉ' : 'Certificate'}</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="document"
                checked={recordType === 'document'}
                onChange={(e) => setRecordType(e.target.value)}
                className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500"
              />
              <span>{language === 'vi' ? 'Tài liệu' : 'Document'}</span>
            </label>
          </div>
        </div>

        {/* Ship Form */}
        {recordType === 'ship' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tên tàu' : 'Ship Name'} *
                </label>
                <input
                  type="text"
                  required
                  value={shipData.name}
                  onChange={(e) => setShipData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'Nhập tên tàu' : 'Enter ship name'}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Số IMO' : 'IMO Number'} *
                </label>
                <input
                  type="text"
                  required
                  value={shipData.imo_number}
                  onChange={(e) => setShipData(prev => ({ ...prev, imo_number: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="1234567"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Hãng đăng kiểm' : 'Class Society'} *
                </label>
                <input
                  type="text"
                  required
                  value={shipData.class_society}
                  onChange={(e) => setShipData(prev => ({ ...prev, class_society: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="DNV GL, ABS, LR..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Cờ' : 'Flag'} *
                </label>
                <input
                  type="text"
                  required
                  value={shipData.flag}
                  onChange={(e) => setShipData(prev => ({ ...prev, flag: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'Việt Nam, Singapore...' : 'Vietnam, Singapore...'}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tổng trọng tải (GT)' : 'Gross Tonnage (GT)'} *
                </label>
                <input
                  type="number"
                  required
                  value={shipData.gross_tonnage}
                  onChange={(e) => setShipData(prev => ({ ...prev, gross_tonnage: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Trọng tải chết (DWT)' : 'Deadweight (DWT)'} *
                </label>
                <input
                  type="number"
                  required
                  value={shipData.deadweight}
                  onChange={(e) => setShipData(prev => ({ ...prev, deadweight: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Năm đóng' : 'Built Year'} *
                </label>
                <input
                  type="number"
                  required
                  value={shipData.built_year}
                  onChange={(e) => setShipData(prev => ({ ...prev, built_year: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="2020"
                />
              </div>
            </div>
          </div>
        )}

        {/* Certificate Form */}
        {recordType === 'certificate' && (
          <div className="space-y-4">
            {!selectedShip && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800 text-sm">
                  {language === 'vi' ? 'Vui lòng chọn tàu trước khi thêm chứng chỉ' : 'Please select a ship before adding certificates'}
                </p>
              </div>
            )}
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'} *
                </label>
                <input
                  type="text"
                  required
                  value={certificateData.cert_name}
                  onChange={(e) => setCertificateData(prev => ({ ...prev, cert_name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'Nhập tên chứng chỉ' : 'Enter certificate name'}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Số chứng chỉ' : 'Certificate Number'} *
                </label>
                <input
                  type="text"
                  required
                  value={certificateData.cert_no}
                  onChange={(e) => setCertificateData(prev => ({ ...prev, cert_no: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={language === 'vi' ? 'Nhập số chứng chỉ' : 'Enter certificate number'}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày cấp' : 'Issue Date'} *
                </label>
                <input
                  type="date"
                  required
                  value={certificateData.issue_date}
                  onChange={(e) => setCertificateData(prev => ({ ...prev, issue_date: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'} *
                </label>
                <input
                  type="date"
                  required
                  value={certificateData.valid_date}
                  onChange={(e) => setCertificateData(prev => ({ ...prev, valid_date: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Xác nhận cuối' : 'Last Endorse'}
                </label>
                <input
                  type="date"
                  value={certificateData.last_endorse}
                  onChange={(e) => setCertificateData(prev => ({ ...prev, last_endorse: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Khảo sát tiếp theo' : 'Next Survey'}
                </label>
                <input
                  type="date"
                  value={certificateData.next_survey}
                  onChange={(e) => setCertificateData(prev => ({ ...prev, next_survey: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Danh mục' : 'Category'} *
                </label>
                <select
                  required
                  value={certificateData.category}
                  onChange={(e) => setCertificateData(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="certificates">{language === 'vi' ? 'Giấy chứng nhận' : 'Certificates'}</option>
                  <option value="inspection_records">{language === 'vi' ? 'Hồ sơ đăng kiểm' : 'Inspection Records'}</option>
                  <option value="survey_reports">{language === 'vi' ? 'Báo cáo kiểm tra' : 'Survey Reports'}</option>
                  <option value="drawings_manuals">{language === 'vi' ? 'Bản vẽ - Sổ tay' : 'Drawings & Manuals'}</option>
                  <option value="other_documents">{language === 'vi' ? 'Hồ sơ khác' : 'Other Documents'}</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Mức độ bảo mật' : 'Sensitivity Level'} *
                </label>
                <select
                  required
                  value={certificateData.sensitivity_level}
                  onChange={(e) => setCertificateData(prev => ({ ...prev, sensitivity_level: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="public">{language === 'vi' ? 'Công khai' : 'Public'}</option>
                  <option value="internal">{language === 'vi' ? 'Nội bộ' : 'Internal'}</option>
                  <option value="confidential">{language === 'vi' ? 'Bí mật' : 'Confidential'}</option>
                  <option value="restricted">{language === 'vi' ? 'Hạn chế' : 'Restricted'}</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Document Form */}
        {recordType === 'document' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tiêu đề tài liệu' : 'Document Title'} *
              </label>
              <input
                type="text"
                required
                value={documentData.title}
                onChange={(e) => setDocumentData(prev => ({ ...prev, title: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Nhập tiêu đề tài liệu' : 'Enter document title'}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Danh mục' : 'Category'} *
              </label>
              <select
                required
                value={documentData.category}
                onChange={(e) => setDocumentData(prev => ({ ...prev, category: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="other_documents">{language === 'vi' ? 'Hồ sơ khác' : 'Other Documents'}</option>
                <option value="drawings_manuals">{language === 'vi' ? 'Bản vẽ - Sổ tay' : 'Drawings & Manuals'}</option>
                <option value="inspection_records">{language === 'vi' ? 'Hồ sơ đăng kiểm' : 'Inspection Records'}</option>
                <option value="survey_reports">{language === 'vi' ? 'Báo cáo kiểm tra' : 'Survey Reports'}</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Mô tả' : 'Description'}
              </label>
              <textarea
                value={documentData.description}
                onChange={(e) => setDocumentData(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows="3"
                placeholder={language === 'vi' ? 'Nhập mô tả tài liệu (tùy chọn)' : 'Enter document description (optional)'}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tệp tài liệu' : 'Document File'}
              </label>
              <input
                type="file"
                onChange={(e) => setDocumentData(prev => ({ ...prev, file: e.target.files[0] }))}
                className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
              />
              <p className="text-xs text-gray-500 mt-1">
                {language === 'vi' ? 'Hỗ trợ: PDF, DOC, DOCX, JPG, PNG' : 'Supported: PDF, DOC, DOCX, JPG, PNG'}
              </p>
            </div>
          </div>
        )}

        <div className="flex justify-end space-x-4 mt-8">
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all disabled:opacity-50"
          >
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || (recordType === 'certificate' && !selectedShip)}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center"
          >
            {isSubmitting && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>}
            {language === 'vi' ? 'Thêm hồ sơ' : 'Add Record'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Additional components for Ships Page and Ship Detail Page would go here
const ShipsPage = () => <div>Ships Page - To be implemented</div>;
const ShipDetailPage = () => <div>Ship Detail Page - To be implemented</div>;

export default App;