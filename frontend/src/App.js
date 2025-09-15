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
    const initializeAuth = async () => {
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        // Only verify token if we don't already have user data
        if (!user) {
          await verifyToken();
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, [token, user]);

  const verifyToken = async () => {
    try {
      // Try to decode token to get user info
      const tokenData = token.split('.')[1];
      const decoded = JSON.parse(atob(tokenData));
      
      // Check if token is expired
      const currentTime = Math.floor(Date.now() / 1000);
      if (decoded.exp && decoded.exp < currentTime) {
        console.warn('Token expired - logging out');
        logout();
        return;
      }
      
      // Create user object from token data
      const userData = {
        id: decoded.sub,
        username: decoded.username,
        role: decoded.role,
        company: decoded.company,
        full_name: decoded.full_name || decoded.username // fallback
      };
      setUser(userData);
    } catch (error) {
      console.warn('Token verification failed:', error.message);
      logout();
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
    viewer: "Crew",
    editor: "Ship Officer", 
    manager: "Company Officer",
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
    grossTonnage: "Tổng Dung Tích",
    deadweight: "Trọng Tải",
    certName: "Tên chứng chỉ",
    certNo: "Số chứng chỉ", 
    issueDate: "Ngày cấp",
    validDate: "Ngày hết hạn",
    lastEndorse: "Xác nhận cuối",
    nextSurvey: "Khảo sát tiếp theo",
    
    // Permissions
    viewer: "Thuyền viên",
    editor: "Sĩ quan",
    manager: "Cán bộ công ty",
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
                <p>{language === 'vi' ? 'Hệ thống có 5 cấp độ quyền từ Thuyền viên đến Super Admin' : 'System has 5 permission levels from Crew to Super Admin'}</p>
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
        <AppContent />
        <Toaster position="top-right" />
      </BrowserRouter>
    </AuthProvider>
  );
};

// App Content Component (inside AuthProvider)
const AppContent = () => {
  const { language } = useAuth();
  const [gdriveConfig, setGdriveConfig] = useState({
    folder_id: ''
  });

  // Handle OAuth 2.0 callback
  useEffect(() => {
    const handleOAuthCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const storedState = sessionStorage.getItem('oauth_state');

      if (window.location.pathname === '/oauth2callback' && code && state && state === storedState) {
        try {
          const response = await axios.post(`${API}/gdrive/oauth/callback`, {
            authorization_code: code,
            state: state,
            folder_id: gdriveConfig.folder_id
          });

          if (response.data.success) {
            toast.success(language === 'vi' ? 'OAuth xác thực thành công!' : 'OAuth authorization successful!');
            
            // Clean up
            sessionStorage.removeItem('oauth_state');
            
            // Redirect back to settings page
            window.location.href = '/';
          } else {
            toast.error(language === 'vi' ? 'OAuth xác thực thất bại' : 'OAuth authorization failed');
          }
        } catch (error) {
          console.error('OAuth callback error:', error);
          toast.error(language === 'vi' ? 'Lỗi xử lý OAuth callback' : 'OAuth callback processing error');
        }
      }
    };

    handleOAuthCallback();
  }, []);

  // OAuth callback route handling
  if (window.location.pathname === '/oauth2callback') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">
            {language === 'vi' ? 'Đang xử lý xác thực OAuth...' : 'Processing OAuth authorization...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/home" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
      <Route path="/account-control" element={<ProtectedRoute><AccountControlPage /></ProtectedRoute>} />
      <Route path="/ships" element={<ProtectedRoute><ShipsPage /></ProtectedRoute>} />
      <Route path="/ships/:shipId" element={<ProtectedRoute><ShipDetailPage /></ProtectedRoute>} />
      <Route path="/oauth2callback" element={<div>Processing OAuth...</div>} />
      <Route path="/" element={<Navigate to="/login" />} />
    </Routes>
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
  const [availableCompanies, setAvailableCompanies] = useState([]);
  const [showFullShipInfo, setShowFullShipInfo] = useState(false);
  const [showShipListModal, setShowShipListModal] = useState(false);
  const [showEditShipModal, setShowEditShipModal] = useState(false);
  const [editingShipData, setEditingShipData] = useState(null);
  const navigate = useNavigate();
  
  const t = translations[language];

  useEffect(() => {
    fetchShips();
    fetchSettings();
    fetchAvailableCompanies();
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

  const fetchAvailableCompanies = async () => {
    try {
      const response = await axios.get(`${API}/companies`);
      setAvailableCompanies(response.data);
    } catch (error) {
      console.error('Failed to fetch companies:', error);
      setAvailableCompanies([]);
    }
  };

  // Filter ships by user's company
  const getUserCompanyShips = () => {
    if (!user?.company) return ships;
    return ships.filter(ship => ship.company === user.company);
  };

  const handleEditShip = async (updatedShipData) => {
    try {
      // Prepare ship payload similar to create ship
      const shipPayload = {
        name: updatedShipData.name?.trim() || '',
        imo: updatedShipData.imo?.trim() || null,
        flag: updatedShipData.flag?.trim() || '',
        ship_type: updatedShipData.ship_type?.trim() || '',
        gross_tonnage: updatedShipData.gross_tonnage ? parseFloat(updatedShipData.gross_tonnage) : null,
        year_built: updatedShipData.year_built ? parseInt(updatedShipData.year_built) : null,
        ship_owner: updatedShipData.ship_owner?.trim() || '',
        company: user?.company || '' // Always use user's company
      };
      
      // Remove null/empty values
      Object.keys(shipPayload).forEach(key => {
        if (shipPayload[key] === null || shipPayload[key] === '') {
          if (key === 'imo') {
            delete shipPayload[key];
          } else if (['gross_tonnage', 'year_built'].includes(key)) {
            delete shipPayload[key];
          }
        }
      });
      
      await axios.put(`${API}/ships/${updatedShipData.id}`, shipPayload);
      
      // Update local state
      setShips(ships.map(ship => 
        ship.id === updatedShipData.id 
          ? { ...ship, ...shipPayload, id: updatedShipData.id } 
          : ship
      ));
      
      // Update selected ship
      setSelectedShip({ ...selectedShip, ...shipPayload });
      
      toast.success(language === 'vi' ? 'Cập nhật tàu thành công!' : 'Ship updated successfully!');
      setShowEditShipModal(false);
      setEditingShipData(null);
    } catch (error) {
      console.error('Ship update error:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      toast.error(language === 'vi' ? `Không thể cập nhật tàu: ${errorMessage}` : `Failed to update ship: ${errorMessage}`);
    }
  };

  const handleDeleteShip = async (shipId) => {
    if (!window.confirm(language === 'vi' ? 'Bạn có chắc chắn muốn xóa tàu này?' : 'Are you sure you want to delete this ship?')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/ships/${shipId}`);
      
      // Update local state
      setShips(ships.filter(ship => ship.id !== shipId));
      
      // Clear selected ship if it was deleted
      if (selectedShip?.id === shipId) {
        setSelectedShip(null);
      }
      
      toast.success(language === 'vi' ? 'Xóa tàu thành công!' : 'Ship deleted successfully!');
      setShowEditShipModal(false);
      setEditingShipData(null);
    } catch (error) {
      console.error('Ship delete error:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      toast.error(language === 'vi' ? `Không thể xóa tàu: ${errorMessage}` : `Failed to delete ship: ${errorMessage}`);
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
                  language === 'vi' && user?.role === 'manager' ? 'Cán bộ công ty' :
                  language === 'vi' && user?.role === 'editor' ? 'Sĩ quan' :
                  language === 'vi' && user?.role === 'viewer' ? 'Thuyền viên' : user?.role})
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
                      <div className="flex justify-between items-center mb-3">
                        <h4 className="font-medium text-gray-700">{language === 'vi' ? 'Danh sách tàu' : 'Ships List'}</h4>
                        <button
                          onClick={() => setShowShipListModal(true)}
                          className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-all"
                        >
                          {language === 'vi' ? 'Xem danh mục' : 'See All List'}
                        </button>
                      </div>
                      {(() => {
                        const userCompanyShips = getUserCompanyShips();
                        return userCompanyShips.length === 0 ? (
                          <p className="text-gray-500 text-sm">
                            {language === 'vi' ? 'Chưa có tàu nào trong công ty' : 'No ships in your company'}
                          </p>
                        ) : (
                          <>
                            <div className="space-y-2">
                              {userCompanyShips.slice(0, 5).map((ship) => (
                                <button
                                  key={ship.id}
                                  onClick={() => handleShipClick(ship, category.key)}
                                  className="block w-full text-left p-2 rounded hover:bg-blue-50 transition-all text-sm border border-gray-100 hover:border-blue-200"
                                >
                                  <div className="font-medium text-gray-800">{ship.name}</div>
                                  <div className="text-xs text-gray-500">{ship.flag} • {ship.class_society}</div>
                                </button>
                              ))}
                            </div>
                            {userCompanyShips.length > 5 && (
                              <div className="text-center pt-2 border-t border-gray-100 mt-2">
                                <span className="text-xs text-gray-500">
                                  {language === 'vi' ? `+${userCompanyShips.length - 5} tàu khác` : `+${userCompanyShips.length - 5} more ships`}
                                </span>
                              </div>
                            )}
                          </>
                        );
                      })()}
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
                        <div className="flex items-center gap-4">
                          <h2 className="text-2xl font-bold text-gray-800">
                            {language === 'vi' ? 'Hồ sơ tài liệu' : 'Document Portfolio'}
                          </h2>
                          <div className="flex items-center gap-2">
                            {/* Ship Particular Button */}
                            <button
                              onClick={() => setShowFullShipInfo(!showFullShipInfo)}
                              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-all flex items-center"
                            >
                              <span className="mr-1">🚢</span>
                              {language === 'vi' ? 'Thông số kỹ thuật' : 'Ship Particular'}
                              <span className="ml-1 text-xs">
                                {showFullShipInfo ? '▲' : '▼'}
                              </span>
                            </button>
                            {/* Edit Ship Button */}
                            <button
                              onClick={() => {
                                setEditingShipData({...selectedShip});
                                setShowEditShipModal(true);
                              }}
                              className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium transition-all flex items-center"
                            >
                              <span className="mr-1">✏️</span>
                              {language === 'vi' ? 'Sửa tàu' : 'Edit Ship'}
                            </button>
                          </div>
                        </div>
                        <button
                          onClick={() => setSelectedShip(null)}
                          className="text-gray-400 hover:text-gray-600 text-xl px-2 py-1"
                          title={language === 'vi' ? 'Đóng chi tiết tàu' : 'Close ship details'}
                        >
                          ✕
                        </button>
                      </div>
                      
                      {/* Ship Information */}
                      <div className="mb-6">
                        {/* Basic Ship Info (Always visible) */}
                        <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                          <div>
                            <span className="font-semibold">{language === 'vi' ? 'Tên tàu:' : 'Ship Name:'}</span>
                            <span className="ml-2">{selectedShip.name}</span>
                          </div>
                          <div>
                            <span className="font-semibold">{language === 'vi' ? 'Tổ chức Phân cấp:' : 'Class Society:'}</span>
                            <span className="ml-2">{selectedShip.ship_type || selectedShip.class_society || '-'}</span>
                          </div>
                          <div>
                            <span className="font-semibold">{language === 'vi' ? 'Cờ:' : 'Flag:'}</span>
                            <span className="ml-2">{selectedShip.flag}</span>
                          </div>
                          <div>
                            <span className="font-semibold">{language === 'vi' ? 'Tổng Dung Tích:' : 'Gross Tonnage:'}</span>
                            <span className="ml-2">{selectedShip.gross_tonnage?.toLocaleString()}</span>
                          </div>
                        </div>

                        {/* Full Ship Info (Toggle visibility) */}
                        {showFullShipInfo && (
                          <div className="grid grid-cols-2 gap-4 text-sm p-4 bg-gray-50 rounded-lg border">
                            <div className="col-span-2">
                              <h4 className="font-semibold text-gray-700 mb-3 border-b pb-2">
                                {language === 'vi' ? 'Thông tin chi tiết tàu' : 'Detailed Ship Information'}
                              </h4>
                            </div>
                            <div>
                              <span className="font-semibold">{language === 'vi' ? 'Tên tàu:' : 'Ship Name:'}</span>
                              <span className="ml-2">{selectedShip.name}</span>
                            </div>
                            <div>
                              <span className="font-semibold">{language === 'vi' ? 'Tổ chức Phân cấp:' : 'Class Society:'}</span>
                              <span className="ml-2">{selectedShip.ship_type || selectedShip.class_society || '-'}</span>
                            </div>
                            <div>
                              <span className="font-semibold">{language === 'vi' ? 'Cờ:' : 'Flag:'}</span>
                              <span className="ml-2">{selectedShip.flag}</span>
                            </div>
                            <div>
                              <span className="font-semibold">{language === 'vi' ? 'Tổng Dung Tích:' : 'Gross Tonnage:'}</span>
                              <span className="ml-2">{selectedShip.gross_tonnage?.toLocaleString()}</span>
                            </div>
                            <div>
                              <span className="font-semibold">{language === 'vi' ? 'Trọng Tải:' : 'Deadweight:'}</span>
                              <span className="ml-2">{selectedShip.deadweight?.toLocaleString()}</span>
                            </div>
                            <div>
                              <span className="font-semibold">{language === 'vi' ? 'Năm đóng:' : 'Built Year:'}</span>
                              <span className="ml-2">{selectedShip.built_year}</span>
                            </div>
                            <div>
                              <span className="font-semibold">{language === 'vi' ? 'Chủ tàu:' : 'Ship Owner:'}</span>
                              <span className="ml-2">{selectedShip.ship_owner || '-'}</span>
                            </div>
                            <div>
                              <span className="font-semibold">{language === 'vi' ? 'Công ty quản lý:' : 'Company:'}</span>
                              <span className="ml-2">{selectedShip.company || '-'}</span>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Sub Menu */}
                      <div className="mb-6">
                        <div className="grid grid-cols-5 gap-1 w-full">
                          {subMenuItems[selectedCategory] && subMenuItems[selectedCategory].map((item) => (
                            <button
                              key={item.key}
                              onClick={() => setSelectedSubMenu(item.key)}
                              className={`px-2 py-3 rounded-lg text-sm font-medium transition-all text-center whitespace-nowrap flex-1 ${
                                selectedSubMenu === item.key 
                                  ? 'bg-blue-600 text-white shadow-lg transform scale-105' 
                                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700 hover:shadow-md hover:transform hover:scale-102'
                              }`}
                              style={{ minHeight: '48px' }}
                            >
                              <span className="text-xs leading-tight">{item.name}</span>
                            </button>
                          ))}
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
          availableCompanies={availableCompanies}
        />
      )}

      {/* Ship List Modal */}
      {showShipListModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[80vh] overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <h3 className="text-xl font-bold text-gray-800">
                {language === 'vi' ? 'Danh mục tàu công ty' : 'Company Ship List'}
              </h3>
              <button
                onClick={() => setShowShipListModal(false)}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
              >
                ×
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
              {(() => {
                const userCompanyShips = getUserCompanyShips();
                return (
                  <>
                    <div className="mb-4 flex justify-between items-center">
                      <p className="text-sm text-gray-600">
                        {language === 'vi' 
                          ? `Hiển thị ${userCompanyShips.length} tàu thuộc công ty: ${user?.company || 'N/A'}`
                          : `Showing ${userCompanyShips.length} ships from company: ${user?.company || 'N/A'}`
                        }
                      </p>
                    </div>
                    
                    {userCompanyShips.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-6xl mb-4">🚢</div>
                        <h4 className="text-lg font-semibold text-gray-700 mb-2">
                          {language === 'vi' ? 'Chưa có tàu nào' : 'No ships available'}
                        </h4>
                        <p className="text-gray-500">
                          {language === 'vi' ? 'Chưa có tàu nào thuộc công ty của bạn' : 'No ships belong to your company yet'}
                        </p>
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse border border-gray-300 rounded-lg">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-300 px-4 py-3 text-left font-semibold">
                                {language === 'vi' ? 'Tên tàu' : 'Ship Name'}
                              </th>
                              <th className="border border-gray-300 px-4 py-3 text-left font-semibold">
                                {language === 'vi' ? 'IMO' : 'IMO'}
                              </th>
                              <th className="border border-gray-300 px-4 py-3 text-left font-semibold">
                                {language === 'vi' ? 'Cờ' : 'Flag'}
                              </th>
                              <th className="border border-gray-300 px-4 py-3 text-left font-semibold">
                                {language === 'vi' ? 'Hạng' : 'Class'}
                              </th>
                              <th className="border border-gray-300 px-4 py-3 text-left font-semibold">
                                {language === 'vi' ? 'Tổng Dung Tích' : 'Gross Tonnage'}
                              </th>
                              <th className="border border-gray-300 px-4 py-3 text-left font-semibold">
                                {language === 'vi' ? 'Chủ tàu' : 'Ship Owner'}
                              </th>
                              <th className="border border-gray-300 px-4 py-3 text-center font-semibold">
                                {language === 'vi' ? 'Thao tác' : 'Actions'}
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {userCompanyShips.map((ship) => (
                              <tr key={ship.id} className="hover:bg-gray-50">
                                <td className="border border-gray-300 px-4 py-3 font-medium text-gray-800">
                                  {ship.name}
                                </td>
                                <td className="border border-gray-300 px-4 py-3 text-gray-600">
                                  {ship.imo_number || '-'}
                                </td>
                                <td className="border border-gray-300 px-4 py-3">
                                  {ship.flag || '-'}
                                </td>
                                <td className="border border-gray-300 px-4 py-3">
                                  {ship.class_society || '-'}
                                </td>
                                <td className="border border-gray-300 px-4 py-3">
                                  {ship.gross_tonnage?.toLocaleString() || '-'}
                                </td>
                                <td className="border border-gray-300 px-4 py-3">
                                  {ship.ship_owner || '-'}
                                </td>
                                <td className="border border-gray-300 px-4 py-3 text-center">
                                  <button
                                    onClick={() => {
                                      setSelectedShip(ship);
                                      setSelectedCategory('documents');
                                      setShowShipListModal(false);
                                    }}
                                    className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-all"
                                  >
                                    {language === 'vi' ? 'Xem chi tiết' : 'View Details'}
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </>
                );
              })()}
            </div>
          </div>
        </div>
      )}

      {/* Edit Ship Modal */}
      {showEditShipModal && editingShipData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <h3 className="text-xl font-bold text-gray-800">
                {language === 'vi' ? 'Chỉnh sửa thông tin tàu' : 'Edit Ship Information'}
              </h3>
              <button
                onClick={() => {
                  setShowEditShipModal(false);
                  setEditingShipData(null);
                }}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
              >
                ×
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              <form onSubmit={(e) => {
                e.preventDefault();
                handleEditShip(editingShipData);
              }}>
                {/* Ship Name */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Tên tàu' : 'Ship Name'} *
                  </label>
                  <input
                    type="text"
                    required
                    value={editingShipData.name || ''}
                    onChange={(e) => setEditingShipData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* IMO and Flag */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Số IMO' : 'IMO Number'}
                    </label>
                    <input
                      type="text"
                      value={editingShipData.imo || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, imo: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="1234567"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Cờ' : 'Flag'} *
                    </label>
                    <input
                      type="text"
                      required
                      value={editingShipData.flag || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, flag: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Class Society */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Tổ chức Phân cấp' : 'Class Society'} *
                  </label>
                  <input
                    type="text"
                    required
                    value={editingShipData.ship_type || ''}
                    onChange={(e) => setEditingShipData(prev => ({ ...prev, ship_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Gross Tonnage, Year Built */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Tổng Dung Tích (GT)' : 'Gross Tonnage (GT)'}
                    </label>
                    <input
                      type="number"
                      value={editingShipData.gross_tonnage || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, gross_tonnage: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="0"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Năm đóng' : 'Built Year'}
                    </label>
                    <input
                      type="number"
                      value={editingShipData.year_built || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, year_built: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="2020"
                    />
                  </div>
                </div>

                {/* Ship Owner */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Chủ tàu' : 'Ship Owner'} *
                  </label>
                  <input
                    type="text"
                    required
                    value={editingShipData.ship_owner || ''}
                    onChange={(e) => setEditingShipData(prev => ({ ...prev, ship_owner: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Company (Read-only) */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Công ty quản lý' : 'Company'} *
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      disabled
                      value={user?.company || 'N/A'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed"
                    />
                    <div className="absolute right-2 top-2 text-gray-400">🔒</div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {language === 'vi' ? 'Không thể thay đổi công ty' : 'Company cannot be changed'}
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-between items-center">
                  <button
                    type="button"
                    onClick={() => handleDeleteShip(editingShipData.id)}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all flex items-center"
                  >
                    <span className="mr-2">🗑️</span>
                    {language === 'vi' ? 'Xóa tàu' : 'Delete Ship'}
                  </button>
                  
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        setShowEditShipModal(false);
                        setEditingShipData(null);
                      }}
                      className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all"
                    >
                      {language === 'vi' ? 'Hủy' : 'Cancel'}
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all"
                    >
                      {language === 'vi' ? 'Cập nhật' : 'Update'}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Account Control Page Component  
const AccountControlPage = () => {
  const { user, language } = useAuth();
  const [users, setUsers] = useState([]);
  const [showAddUser, setShowAddUser] = useState(false);
  const [showEditUser, setShowEditUser] = useState(false);
  const [showUserList, setShowUserList] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [newUserData, setNewUserData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'viewer',
    department: 'technical',
    company: '',
    ship: '',
    zalo: '',
    gmail: ''
  });
  // User filtering and sorting state
  const [userFilters, setUserFilters] = useState({
    company: '',
    department: '',
    ship: ''
  });
  const [userSorting, setUserSorting] = useState({
    sortBy: 'full_name',
    sortOrder: 'asc'
  });
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [showPermissions, setShowPermissions] = useState(false);
  const [showGoogleDrive, setShowGoogleDrive] = useState(false);
  const [showAIConfig, setShowAIConfig] = useState(false);
  const [showCompanyForm, setShowCompanyForm] = useState(false);
  const [showEditCompany, setShowEditCompany] = useState(false);
  const [editingCompany, setEditingCompany] = useState(null);
  // PDF Analysis state
  const [showPdfAnalysis, setShowPdfAnalysis] = useState(false);
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfAnalyzing, setPdfAnalyzing] = useState(false);
  const [availableCompanies, setAvailableCompanies] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [gdriveConfig, setGdriveConfig] = useState({
    auth_method: 'apps_script', // 'apps_script', 'oauth', or 'service_account' 
    // Apps Script fields
    web_app_url: '',
    // OAuth fields
    client_id: '',
    client_secret: '',
    folder_id: '',
    // Service Account fields (legacy)
    service_account_json: ''
  });
  const [gdriveStatus, setGdriveStatus] = useState(null);
  const [gdriveCurrentConfig, setGdriveCurrentConfig] = useState(null);
  const [syncLoading, setSyncLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  // Company Google Drive state
  const [showCompanyGoogleDrive, setShowCompanyGoogleDrive] = useState(false);
  const [companyGdriveConfig, setCompanyGdriveConfig] = useState({
    auth_method: 'apps_script',
    web_app_url: '',
    client_id: '',
    client_secret: '',
    folder_id: '',
    service_account_json: ''
  });
  const [companyGdriveStatus, setCompanyGdriveStatus] = useState(null);
  const [companyGdriveCurrentConfig, setCompanyGdriveCurrentConfig] = useState(null);
  const [companyGdriveTestLoading, setCompanyGdriveTestLoading] = useState(false);
  const [aiConfig, setAiConfig] = useState({
    provider: 'openai',
    model: 'gpt-4o'
  });
  const [companies, setCompanies] = useState([]);
  const [ships, setShips] = useState([]);
  const [companyData, setCompanyData] = useState({
    name_vn: '',
    name_en: '',
    address_vn: '',
    address_en: '',
    tax_id: '',
    gmail: '',
    zalo: '',
    system_expiry: '',
    gdrive_config: {
      service_account_email: '',
      project_id: '',
      private_key: '',
      client_email: '',
      client_id: '',
      folder_id: ''
    }
  });
  const [usageStats, setUsageStats] = useState(null);
  const [usageLoading, setUsageLoading] = useState(false);
  const navigate = useNavigate();
  
  const t = translations[language];

  // Role hierarchy helper functions
  const roleHierarchy = {
    'viewer': 1,
    'editor': 2,
    'manager': 3,
    'admin': 4,
    'super_admin': 5
  };

  const canEditUser = (targetUser) => {
    // Self-edit prevention
    if (targetUser.id === user.id) return false;
    
    const currentLevel = roleHierarchy[user.role] || 0;
    const targetLevel = roleHierarchy[targetUser.role] || 0;
    
    // Super Admin can edit anyone
    if (user.role === 'super_admin') return true;
    
    // Admin can edit anyone except Super Admin  
    if (user.role === 'admin') {
      return targetLevel < roleHierarchy['super_admin'];
    }
    
    // Manager can only edit users in same company with lower or equal role
    if (user.role === 'manager') {
      if (targetUser.company !== user.company) return false;
      return targetLevel <= currentLevel;
    }
    
    // Lower roles cannot edit anyone
    return false;
  };

  const canDeleteUser = (targetUser) => {
    // Self-delete prevention  
    if (targetUser.id === user.id) return false;
    
    // Super Admin protection - only Super Admin can delete Super Admin
    if (targetUser.role === 'super_admin' && user.role !== 'super_admin') return false;
    
    // Use same logic as edit for other cases
    return canEditUser(targetUser);
  };

  const canEditCompany = (company) => {
    // Super Admin can edit any company
    if (user.role === 'super_admin') return true;
    
    // Admin can only edit their own company
    if (user.role === 'admin') {
      return company.name_vn === user.company || company.name_en === user.company;
    }
    
    // Lower roles cannot edit companies
    return false;
  };

  const canDeleteCompany = (company) => {
    // Only Super Admin can delete companies
    return user.role === 'super_admin';
  };

  useEffect(() => {
    if (user?.role === 'manager' || user?.role === 'admin' || user?.role === 'super_admin') {
      fetchUsers();
    }
    if (user?.role === 'admin' || user?.role === 'super_admin') {
      fetchGoogleDriveStatus();
      fetchGoogleDriveConfig();
    }
    if (user?.role === 'super_admin') {
      fetchAIConfig();
    }
    if (user?.role === 'admin' || user?.role === 'super_admin') {
      fetchCompanies();
    }
    if (user?.role === 'manager' || user?.role === 'admin' || user?.role === 'super_admin') {
      fetchShips();
    }
    if (user?.role === 'admin' || user?.role === 'super_admin') {
      fetchUsageStats();
    }
  }, [user]);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
      setFilteredUsers(response.data);
    } catch (error) {
      toast.error('Failed to fetch users');
    }
  };

  const fetchFilteredUsers = async (filters = userFilters, sorting = userSorting) => {
    try {
      const params = new URLSearchParams();
      if (filters.company) params.append('company', filters.company);
      if (filters.department) params.append('department', filters.department);
      if (filters.ship) params.append('ship', filters.ship);
      params.append('sort_by', sorting.sortBy);
      params.append('sort_order', sorting.sortOrder);
      
      const response = await axios.get(`${API}/users/filtered?${params.toString()}`);
      setFilteredUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch filtered users:', error);
      toast.error('Failed to fetch filtered users');
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

  const fetchGoogleDriveConfig = async () => {
    try {
      const response = await axios.get(`${API}/gdrive/config`);
      setGdriveCurrentConfig(response.data);
    } catch (error) {
      console.error('Failed to fetch Google Drive config:', error);
    }
  };

  const handleTestGoogleDriveConnection = async () => {
    if (!gdriveConfig.service_account_json || !gdriveConfig.folder_id) {
      toast.error(language === 'vi' ? 'Vui lòng điền đầy đủ thông tin!' : 'Please fill in all required information!');
      return;
    }

    // Clean and validate folder ID
    const cleanFolderId = gdriveConfig.folder_id.trim();
    if (cleanFolderId.length < 20 || cleanFolderId.length > 100 || cleanFolderId.includes(' ')) {
      toast.error(language === 'vi' ? 
        `Folder ID không hợp lệ (độ dài: ${cleanFolderId.length}). Vui lòng kiểm tra lại!` :
        `Invalid Folder ID (length: ${cleanFolderId.length}). Please check again!`
      );
      return;
    }

    setTestLoading(true);
    try {
      const testConfig = {
        ...gdriveConfig,
        folder_id: cleanFolderId
      };
      
      const response = await axios.post(`${API}/gdrive/test`, testConfig);
      if (response.data.success) {
        toast.success(language === 'vi' ? 
          `Kết nối thành công! Folder: ${response.data.folder_name}` : 
          `Connection successful! Folder: ${response.data.folder_name}`
        );
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message;
      toast.error(language === 'vi' ? 
        `Test kết nối thất bại: ${errorMessage}` : 
        `Connection test failed: ${errorMessage}`
      );
    } finally {
      setTestLoading(false);
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

  const fetchShips = async () => {
    try {
      const response = await axios.get(`${API}/ships`);
      setShips(response.data);
    } catch (error) {
      console.error('Failed to fetch ships:', error);
    }
  };

  // Make fetchCompanies available globally for logo upload
  useEffect(() => {
    window.fetchCompanies = fetchCompanies;
    return () => {
      delete window.fetchCompanies;
    };
  }, []);

  const fetchUsageStats = async () => {
    try {
      const response = await axios.get(`${API}/usage-stats?days=30`);
      setUsageStats(response.data);
    } catch (error) {
      console.error('Failed to fetch usage stats:', error);
    }
  };

  const handleGoogleDriveConfig = async () => {
    // Validate required fields based on auth method
    const authMethod = gdriveConfig.auth_method || 'apps_script';
    
    let missingFields = false;
    if (authMethod === 'apps_script') {
      if (!gdriveConfig.web_app_url || !gdriveConfig.folder_id) {
        missingFields = true;
      }
    } else if (authMethod === 'oauth') {
      if (!gdriveConfig.client_id || !gdriveConfig.client_secret || !gdriveConfig.folder_id) {
        missingFields = true;
      }
    } else if (authMethod === 'service_account') {
      if (!gdriveConfig.service_account_json || !gdriveConfig.folder_id) {
        missingFields = true;
      }
    }
    
    if (missingFields) {
      toast.error(language === 'vi' ? 'Vui lòng điền đầy đủ thông tin' : 'Please fill all required fields');
      return;
    }

    try {
      let endpoint;
      let payload;
      
      if (authMethod === 'apps_script') {
        endpoint = '/gdrive/configure-proxy';
        payload = {
          web_app_url: gdriveConfig.web_app_url,
          folder_id: gdriveConfig.folder_id
        };
      } else if (authMethod === 'oauth') {
        endpoint = '/gdrive/oauth/authorize';
        payload = {
          client_id: gdriveConfig.client_id,
          client_secret: gdriveConfig.client_secret,
          redirect_uri: 'https://vessel-docs-1.preview.emergentagent.com/oauth2callback',
          folder_id: gdriveConfig.folder_id
        };
      } else {
        endpoint = '/gdrive/configure';
        payload = {
          service_account_json: gdriveConfig.service_account_json,
          folder_id: gdriveConfig.folder_id
        };
      }
      
      const response = await axios.post(`${API}${endpoint}`, payload);
      
      if (authMethod === 'oauth' && response.data.authorization_url) {
        // For OAuth, redirect to authorization URL
        sessionStorage.setItem('oauth_state', response.data.state);
        window.location.href = response.data.authorization_url;
      } else {
        // For Apps Script and Service Account, show success
        toast.success(language === 'vi' ? 'Cấu hình Google Drive thành công!' : 'Google Drive configured successfully!');
        setShowGoogleDrive(false);
        // Reset config based on auth method
        if (authMethod === 'apps_script') {
          setGdriveConfig(prev => ({ ...prev, web_app_url: '', folder_id: '' }));
        } else if (authMethod === 'oauth') {
          setGdriveConfig(prev => ({ ...prev, client_id: '', client_secret: '', folder_id: '' }));
        } else {
          setGdriveConfig(prev => ({ ...prev, service_account_json: '', folder_id: '' }));
        }
        fetchGoogleDriveStatus();
        fetchGoogleDriveConfig();
      }
    } catch (error) {
      console.error('Google Drive configuration error:', error);
      toast.error(language === 'vi' ? 'Cấu hình Google Drive thất bại!' : 'Failed to configure Google Drive!');
    }
  };

  const handleSyncToGoogleDrive = async () => {
    setSyncLoading(true);
    try {
      // Check current auth method from config
      const currentConfig = await axios.get(`${API}/gdrive/config`);
      const authMethod = currentConfig.data?.auth_method || 'service_account';
      
      let endpoint;
      if (authMethod === 'apps_script') {
        endpoint = '/gdrive/sync-to-drive-proxy';
      } else {
        endpoint = '/gdrive/sync-to-drive';
      }
      
      await axios.post(`${API}${endpoint}`);
      toast.success(language === 'vi' ? 'Đồng bộ lên Google Drive thành công!' : 'Synced to Google Drive successfully!');
      fetchGoogleDriveStatus();
    } catch (error) {
      console.error('Sync to Google Drive error:', error);
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

  const handlePdfAnalysis = async () => {
    if (!pdfFile) {
      toast.error(language === 'vi' ? 'Vui lòng chọn file PDF!' : 'Please select a PDF file!');
      return;
    }

    setPdfAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('file', pdfFile);

      const response = await axios.post(`${API}/analyze-pdf`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });

      if (response.data.success) {
        toast.success(language === 'vi' ? 'Phân tích PDF thành công!' : 'PDF analysis completed!');
        // You can handle the analysis results here
        console.log('PDF Analysis Results:', response.data.analysis);
      } else {
        toast.error(language === 'vi' ? 'Phân tích PDF thất bại!' : 'PDF analysis failed!');
      }
    } catch (error) {
      console.error('PDF analysis error:', error);
      const errorMessage = error.response?.data?.message || error.message;
      toast.error(language === 'vi' ? `Lỗi phân tích PDF: ${errorMessage}` : `PDF analysis error: ${errorMessage}`);
    } finally {
      setPdfAnalyzing(false);
      setShowPdfAnalysis(false);
      setPdfFile(null);
    }
  };

  // Company Google Drive Configuration Functions
  const fetchCompanyGoogleDriveStatus = async (companyId) => {
    try {
      const response = await axios.get(`${API}/companies/${companyId}/gdrive/status`);
      setCompanyGdriveStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch company Google Drive status:', error);
    }
  };

  const fetchCompanyGoogleDriveConfig = async (companyId) => {
    try {
      const response = await axios.get(`${API}/companies/${companyId}/gdrive/config`);
      setCompanyGdriveCurrentConfig(response.data);
    } catch (error) {
      console.error('Failed to fetch company Google Drive config:', error);
    }
  };

  const handleCompanyGoogleDriveConfig = async (companyId) => {
    // Validate required fields based on auth method
    const authMethod = companyGdriveConfig.auth_method || 'apps_script';
    
    let missingFields = false;
    if (authMethod === 'apps_script') {
      if (!companyGdriveConfig.web_app_url || !companyGdriveConfig.folder_id) {
        missingFields = true;
      }
    } else if (authMethod === 'oauth') {
      if (!companyGdriveConfig.client_id || !companyGdriveConfig.client_secret || !companyGdriveConfig.folder_id) {
        missingFields = true;
      }
    } else if (authMethod === 'service_account') {
      if (!companyGdriveConfig.service_account_json || !companyGdriveConfig.folder_id) {
        missingFields = true;
      }
    }
    
    if (missingFields) {
      toast.error(language === 'vi' ? 'Vui lòng điền đầy đủ thông tin' : 'Please fill all required fields');
      return;
    }

    try {
      let endpoint;
      let payload;
      
      if (authMethod === 'apps_script') {
        endpoint = `/companies/${companyId}/gdrive/configure-proxy`;
        payload = {
          web_app_url: companyGdriveConfig.web_app_url,
          folder_id: companyGdriveConfig.folder_id
        };
      } else if (authMethod === 'oauth') {
        endpoint = `/companies/${companyId}/gdrive/oauth/authorize`;
        payload = {
          client_id: companyGdriveConfig.client_id,
          client_secret: companyGdriveConfig.client_secret,
          redirect_uri: 'https://vessel-docs-1.preview.emergentagent.com/oauth2callback',
          folder_id: companyGdriveConfig.folder_id
        };
      } else {
        endpoint = `/companies/${companyId}/gdrive/configure`;
        payload = {
          service_account_json: companyGdriveConfig.service_account_json,
          folder_id: companyGdriveConfig.folder_id
        };
      }
      
      const response = await axios.post(`${API}${endpoint}`, payload);
      
      if (authMethod === 'oauth' && response.data.authorization_url) {
        // For OAuth, redirect to authorization URL
        sessionStorage.setItem('oauth_state', response.data.state);
        window.location.href = response.data.authorization_url;
      } else {
        // For Apps Script and Service Account, show success
        toast.success(language === 'vi' ? 'Cấu hình Google Drive công ty thành công!' : 'Company Google Drive configured successfully!');
        setShowCompanyGoogleDrive(false);
        // Reset config based on auth method
        if (authMethod === 'apps_script') {
          setCompanyGdriveConfig(prev => ({ ...prev, web_app_url: '', folder_id: '' }));
        } else if (authMethod === 'oauth') {
          setCompanyGdriveConfig(prev => ({ ...prev, client_id: '', client_secret: '', folder_id: '' }));
        } else {
          setCompanyGdriveConfig(prev => ({ ...prev, service_account_json: '', folder_id: '' }));
        }
        fetchCompanyGoogleDriveStatus(companyId);
        fetchCompanyGoogleDriveConfig(companyId);
      }
    } catch (error) {
      console.error('Company Google Drive configuration error:', error);
      toast.error(language === 'vi' ? 'Cấu hình Google Drive công ty thất bại!' : 'Failed to configure company Google Drive!');
    }
  };

  const handleTestCompanyGoogleDriveConnection = async (companyId) => {
    if (!companyGdriveConfig.service_account_json || !companyGdriveConfig.folder_id) {
      toast.error(language === 'vi' ? 'Vui lòng điền đầy đủ thông tin!' : 'Please fill in all required information!');
      return;
    }

    setCompanyGdriveTestLoading(true);
    try {
      const testConfig = {
        service_account_json: companyGdriveConfig.service_account_json,
        folder_id: companyGdriveConfig.folder_id
      };
      
      const response = await axios.post(`${API}/companies/${companyId}/gdrive/test`, testConfig);
      if (response.data.success) {
        toast.success(language === 'vi' ? 
          `Kết nối thành công! Folder: ${response.data.folder_name}` : 
          `Connection successful! Folder: ${response.data.folder_name}`
        );
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message;
      toast.error(language === 'vi' ? 
        `Test kết nối thất bại: ${errorMessage}` : 
        `Connection test failed: ${errorMessage}`
      );
    } finally {
      setCompanyGdriveTestLoading(false);
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
      
      const response = await axios.post(`${API}/companies`, payload);
      const newCompany = response.data;
      
      // Store the company ID for logo upload
      setCompanyData(prev => ({ ...prev, id: newCompany.id }));
      
      toast.success(language === 'vi' ? 'Công ty đã được tạo thành công!' : 'Company created successfully!');
      setShowCompanyForm(false);
      
      // Reset form data
      setCompanyData({
        name_vn: '',
        name_en: '',
        address_vn: '',
        address_en: '',
        tax_id: '',
        gmail: '',
        zalo: '',
        system_expiry: '',
        gdrive_config: {
          service_account_email: '',
          project_id: '',
          private_key: '',
          client_email: '',
          client_id: '',
          folder_id: ''
        }
      });
      
      fetchCompanies();
      
      return newCompany;
    } catch (error) {
      toast.error(language === 'vi' ? 'Không thể tạo công ty!' : 'Failed to create company!');
      throw error;
    }
  };

  const handleEditCompany = async () => {
    if (!editingCompany) return;
    
    try {
      const payload = {
        ...editingCompany,
        system_expiry: editingCompany.system_expiry ? new Date(editingCompany.system_expiry).toISOString() : null
      };
      
      await axios.put(`${API}/companies/${editingCompany.id}`, payload);
      toast.success(language === 'vi' ? 'Công ty đã được cập nhật thành công!' : 'Company updated successfully!');
      setShowEditCompany(false);
      setEditingCompany(null);
      fetchCompanies();
      
      return editingCompany;
    } catch (error) {
      toast.error(language === 'vi' ? 'Không thể cập nhật công ty!' : 'Failed to update company!');
      throw error;
    }
  };

  const handleDeleteCompany = async (company) => {
    if (!window.confirm(language === 'vi' ? 
      `Bạn có chắc muốn xóa công ty "${company.name_vn}"?` : 
      `Are you sure you want to delete company "${company.name_en}"?`)) {
      return;
    }

    try {
      await axios.delete(`${API}/companies/${company.id}`);
      toast.success(language === 'vi' ? 'Công ty đã được xóa thành công!' : 'Company deleted successfully!');
      fetchCompanies();
    } catch (error) {
      toast.error(language === 'vi' ? 'Không thể xóa công ty!' : 'Failed to delete company!');
    }
  };

  const openEditUser = (user) => {
    setEditingUser({
      ...user,
      password: '' // Don't populate password for security
    });
    setShowEditUser(true);
  };

  const handleEditUser = async () => {
    if (!editingUser) return;
    
    try {
      await axios.put(`${API}/users/${editingUser.id}`, editingUser);
      toast.success(language === 'vi' ? 'Người dùng đã được cập nhật thành công!' : 'User updated successfully!');
      setShowEditUser(false);
      setEditingUser(null);
      fetchUsers();
    } catch (error) {
      toast.error(language === 'vi' ? 'Không thể cập nhật người dùng!' : 'Failed to update user!');
      console.error('User update error:', error);
    }
  };

  const handleAddUser = async () => {
    if (!newUserData.username || !newUserData.password || !newUserData.full_name || !newUserData.zalo) {
      toast.error(language === 'vi' ? 'Vui lòng điền đầy đủ thông tin bắt buộc (Tên đăng nhập, Mật khẩu, Họ tên, Zalo)!' : 'Please fill in all required fields (Username, Password, Full Name, Zalo)!');
      return;
    }
    
    try {
      await axios.post(`${API}/auth/register`, newUserData);
      toast.success(language === 'vi' ? 'Người dùng đã được tạo thành công!' : 'User created successfully!');
      setShowAddUser(false);
      setNewUserData({
        username: '',
        email: '',
        password: '',
        full_name: '',
        role: 'viewer',
        department: 'technical',
        company: '',
        ship: '',
        zalo: '',
        gmail: ''
      });
      fetchUsers();
    } catch (error) {
      toast.error(language === 'vi' ? 'Không thể tạo người dùng!' : 'Failed to create user!');
      console.error('User creation error:', error);
    }
  };

  const handleDeleteUser = async (user) => {
    if (!window.confirm(language === 'vi' ? 
      `Bạn có chắc muốn xóa người dùng "${user.full_name}"?` : 
      `Are you sure you want to delete user "${user.full_name}"?`)) {
      return;
    }

    try {
      await axios.delete(`${API}/users/${user.id}`);
      toast.success(language === 'vi' ? 'Người dùng đã được xóa thành công!' : 'User deleted successfully!');
      fetchUsers();
    } catch (error) {
      toast.error(language === 'vi' ? 'Không thể xóa người dùng!' : 'Failed to delete user!');
      console.error('User delete error:', error);
    }
  };

  const openEditCompany = (company) => {
    setEditingCompany({
      ...company,
      system_expiry: company.system_expiry ? new Date(company.system_expiry).toISOString().split('T')[0] : '',
      gdrive_config: company.gdrive_config || {
        service_account_email: '',
        project_id: '',
        private_key: '',
        client_email: '',
        client_id: '',
        folder_id: ''
      }
    });
    
    // Fetch company Google Drive configuration
    if (company.id) {
      fetchCompanyGoogleDriveConfig(company.id);
      fetchCompanyGoogleDriveStatus(company.id);
    }
    
    setShowEditCompany(true);
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
          {/* User Management */}
          {(user?.role === 'manager' || user?.role === 'admin' || user?.role === 'super_admin') && (
            <div className="bg-white rounded-xl shadow-lg p-6 lg:col-span-full">
              <h3 className="text-lg font-semibold mb-6 text-gray-800">
                {language === 'vi' ? 'Quản lý người dùng' : 'User Management'}
              </h3>
              
              {/* Action Buttons */}
              <div className="mb-6 flex space-x-4">
                <button
                  onClick={() => setShowAddUser(true)}
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg transition-all"
                >
                  {t.addUser}
                </button>
                <button
                  onClick={() => setShowUserList(!showUserList)}
                  className={`px-6 py-2 rounded-lg transition-all ${
                    showUserList 
                      ? 'bg-red-600 hover:bg-red-700 text-white' 
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  {showUserList 
                    ? (language === 'vi' ? 'Ẩn danh sách' : 'Hide List')
                    : (language === 'vi' ? 'Danh sách người dùng' : 'User List')
                  }
                </button>
              </div>
              
              {/* Filtering and Sorting Controls */}
              {showUserList && (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
                  <h4 className="font-medium mb-3 text-gray-800">
                    {language === 'vi' ? 'Bộ lọc và sắp xếp' : 'Filter and Sort'}
                  </h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                    {/* Company Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {language === 'vi' ? 'Công ty' : 'Company'}
                      </label>
                      <select
                        value={userFilters.company}
                        onChange={(e) => {
                          const newFilters = { ...userFilters, company: e.target.value };
                          setUserFilters(newFilters);
                          fetchFilteredUsers(newFilters, userSorting);
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">{language === 'vi' ? 'Tất cả công ty' : 'All Companies'}</option>
                        {[...new Set(users.map(u => u.company).filter(Boolean))].map(company => (
                          <option key={company} value={company}>{company}</option>
                        ))}
                      </select>
                    </div>
                    
                    {/* Department Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {language === 'vi' ? 'Phòng ban' : 'Department'}
                      </label>
                      <select
                        value={userFilters.department}
                        onChange={(e) => {
                          const newFilters = { ...userFilters, department: e.target.value };
                          setUserFilters(newFilters);
                          fetchFilteredUsers(newFilters, userSorting);
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">{language === 'vi' ? 'Tất cả phòng ban' : 'All Departments'}</option>
                        <option value="technical">{language === 'vi' ? 'Kỹ thuật' : 'Technical'}</option>
                        <option value="operations">{language === 'vi' ? 'Vận hành' : 'Operations'}</option>
                        <option value="safety">{language === 'vi' ? 'An toàn' : 'Safety'}</option>
                        <option value="commercial">{language === 'vi' ? 'Thương mại' : 'Commercial'}</option>
                        <option value="crewing">{language === 'vi' ? 'Thuyền viên' : 'Crewing'}</option>
                        <option value="ship_crew">{language === 'vi' ? 'Thuyền viên tàu' : 'Ship Crew'}</option>
                      </select>
                    </div>
                    
                    {/* Ship Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {language === 'vi' ? 'Tàu' : 'Ship'}
                      </label>
                      <select
                        value={userFilters.ship}
                        onChange={(e) => {
                          const newFilters = { ...userFilters, ship: e.target.value };
                          setUserFilters(newFilters);
                          fetchFilteredUsers(newFilters, userSorting);
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">{language === 'vi' ? 'Tất cả tàu' : 'All Ships'}</option>
                        {[...new Set(users.map(u => u.ship).filter(Boolean))].map(ship => (
                          <option key={ship} value={ship}>{ship}</option>
                        ))}
                      </select>
                    </div>
                    
                    {/* Sort By */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {language === 'vi' ? 'Sắp xếp theo' : 'Sort By'}
                      </label>
                      <select
                        value={userSorting.sortBy}
                        onChange={(e) => {
                          const newSorting = { ...userSorting, sortBy: e.target.value };
                          setUserSorting(newSorting);
                          fetchFilteredUsers(userFilters, newSorting);
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="full_name">{language === 'vi' ? 'Tên' : 'Name'}</option>
                        <option value="company">{language === 'vi' ? 'Công ty' : 'Company'}</option>
                        <option value="department">{language === 'vi' ? 'Phòng ban' : 'Department'}</option>
                        <option value="role">{language === 'vi' ? 'Vai trò' : 'Role'}</option>
                        <option value="ship">{language === 'vi' ? 'Tàu' : 'Ship'}</option>
                        <option value="created_at">{language === 'vi' ? 'Ngày tạo' : 'Created Date'}</option>
                      </select>
                    </div>
                    
                    {/* Sort Order */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {language === 'vi' ? 'Thứ tự' : 'Order'}
                      </label>
                      <select
                        value={userSorting.sortOrder}
                        onChange={(e) => {
                          const newSorting = { ...userSorting, sortOrder: e.target.value };
                          setUserSorting(newSorting);
                          fetchFilteredUsers(userFilters, newSorting);
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="asc">{language === 'vi' ? 'Tăng dần' : 'Ascending'}</option>
                        <option value="desc">{language === 'vi' ? 'Giảm dần' : 'Descending'}</option>
                      </select>
                    </div>
                  </div>
                  
                  {/* Clear Filters Button */}
                  <div className="mt-3 flex justify-end">
                    <button
                      onClick={() => {
                        setUserFilters({ company: '', department: '', ship: '' });
                        setUserSorting({ sortBy: 'full_name', sortOrder: 'asc' });
                        fetchUsers();
                      }}
                      className="px-4 py-2 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-all"
                    >
                      {language === 'vi' ? 'Xóa bộ lọc' : 'Clear Filters'}
                    </button>
                  </div>
                </div>
              )}
              
              {/* Users Table */}
              {showUserList && users.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse border border-gray-300 text-sm">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="border border-gray-300 px-4 py-3 text-left">
                          {language === 'vi' ? 'Tên người dùng' : 'User Name'}
                        </th>
                        <th className="border border-gray-300 px-4 py-3 text-left">
                          {language === 'vi' ? 'Công ty' : 'Company'}
                        </th>
                        <th className="border border-gray-300 px-4 py-3 text-left">
                          {language === 'vi' ? 'Phòng ban' : 'Department'}
                        </th>
                        <th className="border border-gray-300 px-4 py-3 text-left">
                          {language === 'vi' ? 'Vai trò' : 'Role'}
                        </th>
                        <th className="border border-gray-300 px-4 py-3 text-left">
                          {language === 'vi' ? 'Tàu' : 'Ship'}
                        </th>
                        <th className="border border-gray-300 px-4 py-3 text-left">Zalo</th>
                        <th className="border border-gray-300 px-4 py-3 text-left">Gmail</th>
                        <th className="border border-gray-300 px-4 py-3 text-center">
                          {language === 'vi' ? 'Thao tác' : 'Actions'}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredUsers.map((userItem) => (
                        <tr key={userItem.id} className="hover:bg-gray-50">
                          <td className="border border-gray-300 px-4 py-3 font-medium">
                            {userItem.full_name}
                            <div className="text-xs text-gray-500">{userItem.username}</div>
                          </td>
                          <td className="border border-gray-300 px-4 py-3">
                            {userItem.company || '-'}
                          </td>
                          <td className="border border-gray-300 px-4 py-3">
                            {userItem.department || '-'}
                          </td>
                          <td className="border border-gray-300 px-4 py-3">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              userItem.role === 'super_admin' ? 'bg-red-100 text-red-800' :
                              userItem.role === 'admin' ? 'bg-orange-100 text-orange-800' :
                              userItem.role === 'manager' ? 'bg-blue-100 text-blue-800' :
                              userItem.role === 'editor' ? 'bg-green-100 text-green-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {userItem.role === 'super_admin' ? (language === 'vi' ? 'Siêu quản trị' : 'Super Admin') :
                               userItem.role === 'admin' ? (language === 'vi' ? 'Quản trị' : 'Admin') :
                               userItem.role === 'manager' ? (language === 'vi' ? 'Cán bộ công ty' : 'Company Officer') :
                               userItem.role === 'editor' ? (language === 'vi' ? 'Sĩ quan' : 'Ship Officer') :
                               (language === 'vi' ? 'Thuyền viên' : 'Crew')}
                            </span>
                          </td>
                          <td className="border border-gray-300 px-4 py-3">
                            {userItem.ship || '-'}
                          </td>
                          <td className="border border-gray-300 px-4 py-3">
                            {userItem.zalo || '-'}
                          </td>
                          <td className="border border-gray-300 px-4 py-3">
                            {userItem.gmail || '-'}
                          </td>
                          <td className="border border-gray-300 px-4 py-3 text-center">
                            <div className="flex justify-center space-x-2">
                              <button
                                onClick={() => openEditUser(userItem)}
                                disabled={!canEditUser(userItem)}
                                className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-3 py-1 rounded text-xs transition-all"
                                title={
                                  !canEditUser(userItem) 
                                    ? (language === 'vi' 
                                        ? 'Không có quyền chỉnh sửa người dùng này' 
                                        : 'No permission to edit this user')
                                    : (language === 'vi' ? 'Sửa' : 'Edit')
                                }
                              >
                                {language === 'vi' ? 'Sửa' : 'Edit'}
                              </button>
                              <button
                                onClick={() => handleDeleteUser(userItem)}
                                disabled={!canDeleteUser(userItem)}
                                className="bg-red-500 hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-3 py-1 rounded text-xs transition-all"
                                title={
                                  !canDeleteUser(userItem) 
                                    ? (language === 'vi' 
                                        ? 'Không có quyền xóa người dùng này' 
                                        : 'No permission to delete this user')
                                    : (language === 'vi' ? 'Xóa' : 'Delete')
                                }
                              >
                                {language === 'vi' ? 'Xóa' : 'Delete'}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">👥</div>
                  <p>{language === 'vi' ? 'Chưa có người dùng nào' : 'No users yet'}</p>
                  <p className="text-sm mt-2">
                    {language === 'vi' ? 'Nhấn "Thêm người dùng" để bắt đầu' : 'Click "Add User" to get started'}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* System Google Drive Configuration - Super Admin Only */}
          {user?.role === 'super_admin' && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">
                {language === 'vi' ? 'Cấu hình Google Drive hệ thống' : 'System Google Drive Configuration'}
              </h3>
              
              {/* Google Drive Status */}
              <div className="mb-4 space-y-3">
                {/* Configuration Status */}
                <div className="p-4 rounded-lg bg-gray-50 border">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-800">
                      {language === 'vi' ? 'Trạng thái cấu hình' : 'Configuration Status'}
                    </h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      gdriveStatus?.configured ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {gdriveStatus?.configured ? 
                        (language === 'vi' ? 'Đã cấu hình' : 'Configured') : 
                        (language === 'vi' ? 'Chưa cấu hình' : 'Not configured')}
                    </span>
                  </div>
                  
                  {gdriveCurrentConfig?.configured ? (
                    <div className="text-sm text-gray-600 space-y-1">
                      <div className="flex justify-between">
                        <span>{language === 'vi' ? 'Method:' : 'Auth Method:'}</span>
                        <span className="font-mono text-xs">
                          {gdriveCurrentConfig.auth_method === 'apps_script' 
                            ? 'Apps Script' 
                            : gdriveCurrentConfig.auth_method === 'oauth' 
                              ? 'OAuth 2.0' 
                              : 'Service Account'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>
                          {gdriveCurrentConfig.auth_method === 'apps_script' 
                            ? (language === 'vi' ? 'Email Account:' : 'Account Email:')
                            : (language === 'vi' ? 'Service Account:' : 'Service Account:')}
                        </span>
                        <span className="font-mono text-xs">{gdriveCurrentConfig.service_account_email}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>{language === 'vi' ? 'Folder ID:' : 'Folder ID:'}</span>
                        <span className="font-mono text-xs">{gdriveCurrentConfig.folder_id}</span>
                      </div>
                      {gdriveCurrentConfig.last_sync && (
                        <div className="flex justify-between">
                          <span>{language === 'vi' ? 'Đồng bộ cuối:' : 'Last Sync:'}</span>
                          <span className="text-xs">{gdriveCurrentConfig.last_sync ? new Date(gdriveCurrentConfig.last_sync).toLocaleString() : 'Never'}</span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">
                      {language === 'vi' ? 
                        'Chưa có cấu hình Google Drive. Nhấn "Cấu hình Google Drive" để bắt đầu.' : 
                        'No Google Drive configuration yet. Click "Configure Google Drive" to get started.'}
                    </p>
                  )}
                </div>

                {/* Sync Status */}
                {gdriveStatus?.configured && (
                  <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
                    <h4 className="font-medium text-blue-800 mb-2">
                      {language === 'vi' ? 'Trạng thái đồng bộ' : 'Sync Status'}
                    </h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">{gdriveStatus.local_files || 0}</div>
                        <div className="text-gray-600">{language === 'vi' ? 'Files local' : 'Local files'}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">{gdriveStatus.drive_files || 0}</div>
                        <div className="text-gray-600">{language === 'vi' ? 'Files Drive' : 'Drive files'}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
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
                <button
                  onClick={() => setShowPdfAnalysis(true)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg transition-all"
                >
                  {language === 'vi' ? 'Phân tích PDF' : 'PDF Analysis'}
                </button>
              </div>
            </div>
          )}

          {/* Usage Tracking - Admin+ Only */}
          {(user?.role === 'admin' || user?.role === 'super_admin') && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">
                {language === 'vi' ? 'Theo dõi sử dụng AI' : 'AI Usage Tracking'}
              </h3>
              
              {/* Usage Statistics */}
              {usageStats && (
                <div className="space-y-4">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <div className="text-sm text-blue-600 font-medium">
                        {language === 'vi' ? 'Tổng yêu cầu' : 'Total Requests'}
                      </div>
                      <div className="text-lg font-bold text-blue-800">
                        {usageStats.total_requests ? usageStats.total_requests.toLocaleString() : '0'}
                      </div>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg">
                      <div className="text-sm text-green-600 font-medium">
                        {language === 'vi' ? 'Chi phí ước tính' : 'Estimated Cost'}
                      </div>
                      <div className="text-lg font-bold text-green-800">
                        ${usageStats.total_estimated_cost ? usageStats.total_estimated_cost.toFixed(4) : '0.0000'}
                      </div>
                    </div>
                  </div>

                  {/* Token Usage */}
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-sm text-gray-600 mb-2">
                      {language === 'vi' ? 'Sử dụng token (30 ngày):' : 'Token Usage (30 days):'}
                    </div>
                    <div className="text-xs space-y-1">
                      <div>
                        <span className="font-medium">Input:</span> {usageStats.total_input_tokens ? usageStats.total_input_tokens.toLocaleString() : '0'} tokens
                      </div>
                      <div>
                        <span className="font-medium">Output:</span> {usageStats.total_output_tokens ? usageStats.total_output_tokens.toLocaleString() : '0'} tokens
                      </div>
                    </div>
                  </div>

                  {/* Provider Distribution */}
                  {usageStats.requests_by_provider && Object.keys(usageStats.requests_by_provider).length > 0 && (
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <div className="text-sm text-gray-600 mb-2">
                        {language === 'vi' ? 'Phân bố nhà cung cấp:' : 'Provider Distribution:'}
                      </div>
                      <div className="space-y-1">
                        {Object.entries(usageStats.requests_by_provider || {}).map(([provider, count]) => (
                          <div key={provider} className="flex justify-between text-xs">
                            <span className="capitalize">{provider}</span>
                            <span className="font-medium">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              <div className="mt-4 space-y-2">
                <button
                  onClick={() => {
                    setUsageLoading(true);
                    fetchUsageStats().finally(() => setUsageLoading(false));
                  }}
                  disabled={usageLoading}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white py-2 rounded-lg transition-all text-sm"
                >
                  {usageLoading ? '⏳' : '🔄'} {language === 'vi' ? 'Làm mới thống kê' : 'Refresh Stats'}
                </button>
              </div>
            </div>
          )}

          {/* Company Management - Admin+ Only */}
          {(user?.role === 'admin' || user?.role === 'super_admin') && (
            <div className="bg-white rounded-xl shadow-lg p-6 lg:col-span-full">
              <h3 className="text-lg font-semibold mb-6 text-gray-800">
                {language === 'vi' ? 'Quản lý công ty' : 'Company Management'}
              </h3>
              
              {/* Action Buttons - Only Super Admin can add new companies */}
              {user?.role === 'super_admin' && (
                <div className="mb-6">
                  <button
                    onClick={() => setShowCompanyForm(true)}
                    className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-2 rounded-lg transition-all"
                  >
                    {language === 'vi' ? 'Thêm công ty mới' : 'Add New Company'}
                  </button>
                </div>
              )}
              
              {/* Companies Table */}
              {companies.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse border border-gray-300 text-sm">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="border border-gray-300 px-4 py-3 text-left">
                          {language === 'vi' ? 'Logo' : 'Logo'}
                        </th>
                        <th className="border border-gray-300 px-4 py-3 text-left">
                          {language === 'vi' ? 'Tên công ty (VN)' : 'Company Name (VN)'}
                        </th>
                        <th className="border border-gray-300 px-4 py-3 text-left">
                          {language === 'vi' ? 'Tên công ty (EN)' : 'Company Name (EN)'}
                        </th>
                        <th className="border border-gray-300 px-4 py-3 text-left">Zalo</th>
                        <th className="border border-gray-300 px-4 py-3 text-left">
                          {language === 'vi' ? 'Hết hạn' : 'Expiry'}
                        </th>
                        <th className="border border-gray-300 px-4 py-3 text-center">
                          {language === 'vi' ? 'Thao tác' : 'Actions'}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {companies.map((company) => (
                        <tr key={company.id} className="hover:bg-gray-50">
                          <td className="border border-gray-300 px-4 py-3 text-center">
                            {company.logo_url ? (
                              <img 
                                src={`${API}${company.logo_url}`} 
                                alt={company.name_en} 
                                className="w-12 h-12 object-contain mx-auto rounded"
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                  e.target.nextSibling.style.display = 'flex';
                                }}
                              />
                            ) : null}
                            <div 
                              className={`w-12 h-12 bg-gray-200 rounded flex items-center justify-center mx-auto text-gray-500 text-xs ${company.logo_url ? 'hidden' : 'flex'}`}
                            >
                              {language === 'vi' ? 'Chưa có' : 'No Logo'}
                            </div>
                          </td>
                          <td className="border border-gray-300 px-4 py-3 font-medium">
                            {company.name_vn}
                          </td>
                          <td className="border border-gray-300 px-4 py-3">
                            {company.name_en}
                          </td>
                          <td className="border border-gray-300 px-4 py-3">
                            {company.zalo || '-'}
                          </td>
                          <td className="border border-gray-300 px-4 py-3">
                            {company.system_expiry ? 
                              new Date(company.system_expiry).toLocaleDateString() : 
                              (language === 'vi' ? 'Không giới hạn' : 'Unlimited')
                            }
                          </td>
                          <td className="border border-gray-300 px-4 py-3 text-center">
                            <div className="flex justify-center space-x-2">
                              <button
                                onClick={() => openEditCompany(company)}
                                disabled={!canEditCompany(company)}
                                className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-3 py-1 rounded text-xs transition-all"
                                title={
                                  !canEditCompany(company) 
                                    ? (language === 'vi' 
                                        ? 'Chỉ có thể sửa công ty của bạn' 
                                        : 'You can only edit your own company')
                                    : (language === 'vi' ? 'Sửa' : 'Edit')
                                }
                              >
                                {language === 'vi' ? 'Sửa' : 'Edit'}
                              </button>
                              {user?.role === 'super_admin' && (
                                <button
                                  onClick={() => handleDeleteCompany(company)}
                                  disabled={!canDeleteCompany(company)}
                                  className="bg-red-500 hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-3 py-1 rounded text-xs transition-all"
                                  title={
                                    !canDeleteCompany(company) 
                                      ? (language === 'vi' 
                                          ? 'Chỉ Super Admin mới có thể xóa công ty' 
                                          : 'Only Super Admin can delete companies')
                                      : (language === 'vi' ? 'Xóa' : 'Delete')
                                  }
                                >
                                  {language === 'vi' ? 'Xóa' : 'Delete'}
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">🏢</div>
                  <p>{language === 'vi' ? 'Chưa có công ty nào' : 'No companies yet'}</p>
                  <p className="text-sm mt-2">
                    {language === 'vi' ? 'Nhấn "Thêm công ty mới" để bắt đầu' : 'Click "Add New Company" to get started'}
                  </p>
                </div>
              )}
            </div>
          )}

        </div>

        {/* Google Drive Configuration Modal */}
        {showGoogleDrive && (
          <GoogleDriveModal
            config={gdriveConfig}
            setConfig={setGdriveConfig}
            currentConfig={gdriveCurrentConfig}
            onClose={() => setShowGoogleDrive(false)}
            onSave={handleGoogleDriveConfig}
            onTest={handleTestGoogleDriveConnection}
            testLoading={testLoading}
            language={language}
          />
        )}

        {/* Company Google Drive Configuration Modal */}
        {showCompanyGoogleDrive && editingCompany && (
          <CompanyGoogleDriveModal
            companyId={editingCompany.id}
            config={companyGdriveConfig}
            setConfig={setCompanyGdriveConfig}
            currentConfig={companyGdriveCurrentConfig}
            onClose={() => {
              console.log('🔍 Debug - Closing Company Google Drive modal');
              setShowCompanyGoogleDrive(false);
            }}
            onSave={() => {
              console.log('🔍 Debug - Company Google Drive Save clicked');
              console.log('   editingCompany.id:', editingCompany.id);
              
              if (editingCompany.id) {
                handleCompanyGoogleDriveConfig(editingCompany.id);
              } else {
                toast.error(language === 'vi' ? 'Lỗi: Không có Company ID để lưu' : 'Error: No Company ID to save');
              }
            }}
            onTest={() => {
              console.log('🔍 Debug - Company Google Drive Test clicked (onTest prop)');
              console.log('   editingCompany.id:', editingCompany.id);
              
              if (editingCompany.id) {
                handleTestCompanyGoogleDriveConnection(editingCompany.id);
              } else {
                toast.error(language === 'vi' ? 'Lỗi: Không có Company ID để test' : 'Error: No Company ID to test');
              }
            }}
            testLoading={companyGdriveTestLoading}
            language={language}
          />
        )}

        {/* AI Configuration Modal */}
        {showAIConfig && (
          <AIConfigModal
            config={aiConfig}
            setConfig={setAiConfig}
            onClose={() => setShowAIConfig(false)}
            onSave={handleAIConfigUpdate}
            language={language}
          />
        )}

        {/* Company Form Modal */}
        {showCompanyForm && (
          <CompanyFormModal
            companyData={companyData}
            setCompanyData={setCompanyData}
            onClose={() => setShowCompanyForm(false)}
            onSubmit={handleCreateCompany}
            language={language}
            isEdit={false}
            companyGdriveCurrentConfig={companyGdriveCurrentConfig}
            fetchCompanyGoogleDriveConfig={fetchCompanyGoogleDriveConfig}
            fetchCompanyGoogleDriveStatus={fetchCompanyGoogleDriveStatus}
            setShowCompanyGoogleDrive={setShowCompanyGoogleDrive}
          />
        )}

        {/* Edit Company Modal */}
        {showEditCompany && editingCompany && (
          <CompanyFormModal
            companyData={editingCompany}
            setCompanyData={setEditingCompany}
            onClose={() => {
              setShowEditCompany(false);
              setEditingCompany(null);
            }}
            onSubmit={handleEditCompany}
            language={language}
            isEdit={true}
            companyGdriveCurrentConfig={companyGdriveCurrentConfig}
            fetchCompanyGoogleDriveConfig={fetchCompanyGoogleDriveConfig}
            fetchCompanyGoogleDriveStatus={fetchCompanyGoogleDriveStatus}
            setShowCompanyGoogleDrive={setShowCompanyGoogleDrive}
          />
        )}

        {/* Add User Modal */}
        {showAddUser && (
          <AddUserModal
            userData={newUserData}
            setUserData={setNewUserData}
            onClose={() => {
              setShowAddUser(false);
              setNewUserData({
                username: '',
                email: '',
                password: '',
                full_name: '',
                role: 'viewer',
                department: 'technical',
                company: '',
                ship: '',
                zalo: '',
                gmail: ''
              });
            }}
            onSubmit={handleAddUser}
            language={language}
            companies={companies}
            ships={ships}
          />
        )}

        {/* Edit User Modal */}
        {showEditUser && editingUser && (
          <EditUserModal
            userData={editingUser}
            setUserData={setEditingUser}
            onClose={() => {
              setShowEditUser(false);
              setEditingUser(null);
            }}
            onSubmit={handleEditUser}
            language={language}
            companies={companies}
            ships={ships}
          />
        )}
        
        {/* PDF Analysis Modal */}
        {showPdfAnalysis && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
              <div className="flex justify-between items-center p-6 border-b border-gray-200">
                <h3 className="text-xl font-bold text-gray-800">
                  {language === 'vi' ? 'Phân tích Giấy chứng nhận' : 'Certificate Analysis'}
                </h3>
                <button
                  onClick={() => {
                    setShowPdfAnalysis(false);
                    setPdfFile(null);
                  }}
                  className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
                >
                  ×
                </button>
              </div>
              
              <div className="p-6">
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {language === 'vi' ? 'Chọn file PDF (tối đa 5MB)' : 'Select PDF file (max 5MB)'}
                  </label>
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => {
                      const file = e.target.files[0];
                      if (file && file.size > 5 * 1024 * 1024) {
                        toast.error(language === 'vi' ? 'File quá lớn! Tối đa 5MB' : 'File too large! Max 5MB');
                        return;
                      }
                      setPdfFile(file);
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                {pdfFile && (
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm text-blue-800">
                      📄 {pdfFile.name} ({(pdfFile.size / 1024 / 1024).toFixed(2)}MB)
                    </p>
                  </div>
                )}
                
                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setShowPdfAnalysis(false);
                      setPdfFile(null);
                    }}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all"
                    disabled={pdfAnalyzing}
                  >
                    {language === 'vi' ? 'Hủy' : 'Cancel'}
                  </button>
                  <button
                    onClick={handlePdfAnalysis}
                    disabled={pdfAnalyzing || !pdfFile}
                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center justify-center"
                  >
                    {pdfAnalyzing ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        {language === 'vi' ? 'Đang phân tích...' : 'Analyzing...'}
                      </>
                    ) : (
                      language === 'vi' ? 'Phân tích PDF' : 'Analyze PDF'
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Google Drive Configuration Modal Component
const GoogleDriveModal = ({ config, setConfig, currentConfig, onClose, onSave, onTest, testLoading, language }) => {
  const [authMethod, setAuthMethod] = useState(config.auth_method || 'apps_script');
  const [oauthLoading, setOauthLoading] = useState(false);
  
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleAuthMethodChange = (method) => {
    setAuthMethod(method);
    setConfig(prev => ({ ...prev, auth_method: method }));
  };

  const handleAppsScriptTest = async () => {
    try {
      setOauthLoading(true);
      
      const response = await axios.post(`${API}/gdrive/configure-proxy`, {
        web_app_url: config.web_app_url,
        folder_id: config.folder_id
      });
      
      if (response.data.success) {
        toast.success(language === 'vi' ? 'Apps Script proxy hoạt động!' : 'Apps Script proxy working!');
      } else {
        toast.error(language === 'vi' ? 'Apps Script proxy lỗi' : 'Apps Script proxy error');
      }
    } catch (error) {
      console.error('Apps Script test error:', error);
      toast.error(language === 'vi' ? 'Lỗi test Apps Script' : 'Apps Script test error');
    } finally {
      setOauthLoading(false);
    }
  };

  const handleOAuthAuthorize = async () => {
    try {
      setOauthLoading(true);
      
      const oauthConfig = {
        client_id: config.client_id,
        client_secret: config.client_secret,
        redirect_uri: 'https://vessel-docs-1.preview.emergentagent.com/oauth2callback',
        folder_id: config.folder_id
      };

      const response = await axios.post(`${API}/gdrive/oauth/authorize`, oauthConfig);
      
      if (response.data.success && response.data.authorization_url) {
        // Store state for later use
        sessionStorage.setItem('oauth_state', response.data.state);
        
        // Redirect to Google OAuth
        window.location.href = response.data.authorization_url;
      } else {
        toast.error(language === 'vi' ? 'Không thể tạo URL xác thực' : 'Failed to generate authorization URL');
      }
    } catch (error) {
      console.error('OAuth authorization error:', error);
      toast.error(language === 'vi' ? 'Lỗi xác thực OAuth' : 'OAuth authorization error');
    } finally {
      setOauthLoading(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]" 
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto mx-4">
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

        {/* Current Configuration Display */}
        {currentConfig?.configured && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h4 className="font-medium text-green-800 mb-2">
              {language === 'vi' ? 'Cấu hình hiện tại:' : 'Current Configuration:'}
            </h4>
            <div className="text-sm text-green-700 space-y-1">
              <div><strong>{language === 'vi' ? 'Method:' : 'Auth Method:'}</strong> {
                currentConfig.auth_method === 'apps_script' 
                  ? 'Apps Script' 
                  : currentConfig.auth_method === 'oauth' 
                    ? 'OAuth 2.0' 
                    : 'Service Account'
              }</div>
              <div><strong>{language === 'vi' ? 'Folder ID:' : 'Folder ID:'}</strong> {currentConfig.folder_id}</div>
              {currentConfig.last_sync && (
                <div><strong>{language === 'vi' ? 'Đồng bộ cuối:' : 'Last Sync:'}</strong> {currentConfig.last_sync ? new Date(currentConfig.last_sync).toLocaleString() : 'Never'}</div>
              )}
            </div>
          </div>
        )}

        {/* Authentication Method Selector */}
        <div className="mb-6">
          <h4 className="font-medium text-gray-800 mb-3">
            {language === 'vi' ? 'Phương thức xác thực' : 'Authentication Method'}
          </h4>
          <div className="flex space-x-2 mb-4 flex-wrap">
            <button
              type="button"
              onClick={() => handleAuthMethodChange('apps_script')}
              className={`px-3 py-2 rounded-lg transition-all text-sm ${
                authMethod === 'apps_script'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Apps Script ({language === 'vi' ? 'Đơn giản nhất' : 'Easiest'})
            </button>
            <button
              type="button"
              onClick={() => handleAuthMethodChange('oauth')}
              className={`px-3 py-2 rounded-lg transition-all text-sm ${
                authMethod === 'oauth'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              OAuth 2.0 ({language === 'vi' ? 'Khuyên dùng' : 'Recommended'})
            </button>
            <button
              type="button"
              onClick={() => handleAuthMethodChange('service_account')}
              className={`px-3 py-2 rounded-lg transition-all text-sm ${
                authMethod === 'service_account'
                  ? 'bg-yellow-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Service Account ({language === 'vi' ? 'Cũ' : 'Legacy'})
            </button>
          </div>
        </div>
        
        <div className="space-y-6">
          {/* Apps Script Configuration */}
          {authMethod === 'apps_script' && (
            <>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <h5 className="font-medium text-green-800 mb-2">
                  ✨ {language === 'vi' ? 'Google Apps Script (Đơn giản nhất)' : 'Google Apps Script (Easiest)'}
                </h5>
                <p className="text-sm text-green-700">
                  {language === 'vi' 
                    ? 'Sử dụng Google Apps Script làm proxy để bypass vấn đề OAuth consent screen. Không cần verification từ Google!'
                    : 'Use Google Apps Script as a proxy to bypass OAuth consent screen issues. No Google verification needed!'
                  }
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Google Apps Script Web App URL' : 'Google Apps Script Web App URL'}
                </label>
                <input
                  type="url"
                  value={config.web_app_url}
                  onChange={(e) => setConfig(prev => ({ ...prev, web_app_url: e.target.value }))}
                  placeholder="https://script.google.com/macros/s/AKfycby.../exec"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi' 
                    ? 'Ví dụ: https://script.google.com/macros/s/AKfycbzi8DdyZ85Oi9H6s-HH5CTp28HFquCWB-CquduS7MT1SBytLB_awx1UqASBVvL51SE/exec'
                    : 'Example: https://script.google.com/macros/s/AKfycbzi8DdyZ85Oi9H6s-HH5CTp28HFquCWB-CquduS7MT1SBytLB_awx1UqASBVvL51SE/exec'
                  }
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
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi' ? 'Folder ID từ URL Google Drive: drive.google.com/drive/folders/[FOLDER_ID]' : 'Folder ID from Google Drive URL: drive.google.com/drive/folders/[FOLDER_ID]'}
                </p>
              </div>

              {/* Apps Script Test Connection */}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-800">
                    {language === 'vi' ? 'Test kết nối Apps Script' : 'Test Apps Script Connection'}
                  </h4>
                  <button
                    onClick={handleAppsScriptTest}
                    disabled={oauthLoading || !config.web_app_url || !config.folder_id}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center gap-2"
                  >
                    {oauthLoading && <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>}
                    {language === 'vi' ? 'Test kết nối' : 'Test Connection'}
                  </button>
                </div>
                <p className="text-xs text-gray-500">
                  {language === 'vi' ? 'Test kết nối Apps Script trước khi lưu' : 'Test Apps Script connection before saving'}
                </p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-green-800 mb-2">
                  📋 {language === 'vi' ? 'Hướng dẫn setup Apps Script:' : 'Apps Script Setup Instructions:'}
                </h4>
                <ol className="text-sm text-green-700 space-y-1">
                  <li>1. {language === 'vi' ? 'Truy cập' : 'Go to'} <a href="https://script.google.com" target="_blank" className="underline">script.google.com</a></li>
                  <li>2. {language === 'vi' ? 'Tạo New project: "Ship Management Drive Proxy"' : 'Create New project: "Ship Management Drive Proxy"'}</li>
                  <li>3. {language === 'vi' ? 'Copy code từ file GOOGLE_APPS_SCRIPT_PROXY.js' : 'Copy code from GOOGLE_APPS_SCRIPT_PROXY.js file'}</li>
                  <li>4. {language === 'vi' ? 'Sửa FOLDER_ID với folder ID thực tế' : 'Update FOLDER_ID with your actual folder ID'}</li>
                  <li>5. {language === 'vi' ? 'Deploy as Web app → Execute as: Me → Who has access: Anyone' : 'Deploy as Web app → Execute as: Me → Who has access: Anyone'}</li>
                  <li>6. {language === 'vi' ? 'Copy Web app URL và paste vào trên' : 'Copy Web app URL and paste above'}</li>
                </ol>
              </div>
            </>
          )}

          {/* OAuth Configuration */}
          {authMethod === 'oauth' && (
            <>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <h5 className="font-medium text-blue-800 mb-2">
                  {language === 'vi' ? 'OAuth 2.0 Configuration' : 'OAuth 2.0 Configuration'}
                </h5>
                <p className="text-sm text-blue-700">
                  {language === 'vi' 
                    ? 'OAuth 2.0 cho phép ứng dụng truy cập Google Drive của bạn một cách an toàn mà không cần chia sẻ mật khẩu.'
                    : 'OAuth 2.0 allows the application to securely access your Google Drive without sharing passwords.'
                  }
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Client ID' : 'Client ID'}
                </label>
                <input
                  type="text"
                  value={config.client_id}
                  onChange={(e) => setConfig(prev => ({ ...prev, client_id: e.target.value }))}
                  placeholder="123456789012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Client Secret' : 'Client Secret'}
                </label>
                <input
                  type="password"
                  value={config.client_secret}
                  onChange={(e) => setConfig(prev => ({ ...prev, client_secret: e.target.value }))}
                  placeholder="GOCSPX-abcdefghijklmnopqrstuvwxyz123456"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
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

              {/* OAuth Authorization Button */}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-800">
                    {language === 'vi' ? 'Xác thực OAuth' : 'OAuth Authorization'}
                  </h4>
                  <button
                    onClick={handleOAuthAuthorize}
                    disabled={oauthLoading || !config.client_id || !config.client_secret || !config.folder_id}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center gap-2"
                  >
                    {oauthLoading && <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>}
                    {language === 'vi' ? 'Xác thực với Google' : 'Authorize with Google'}
                  </button>
                </div>
                <p className="text-xs text-gray-500">
                  {language === 'vi' ? 'Nhấn để xác thực ứng dụng với Google Drive' : 'Click to authorize the application with Google Drive'}
                </p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-green-800 mb-2">
                  {language === 'vi' ? 'Hướng dẫn thiết lập OAuth:' : 'OAuth Setup Instructions:'}
                </h4>
                <ol className="text-sm text-green-700 space-y-1">
                  <li>1. {language === 'vi' ? 'Truy cập Google Cloud Console' : 'Go to Google Cloud Console'}</li>
                  <li>2. {language === 'vi' ? 'Tạo OAuth 2.0 Client IDs' : 'Create OAuth 2.0 Client IDs'}</li>
                  <li>3. {language === 'vi' ? 'Thêm Authorized redirect URI:' : 'Add Authorized redirect URI:'} <code>https://vessel-docs-1.preview.emergentagent.com/oauth2callback</code></li>
                  <li>4. {language === 'vi' ? 'Copy Client ID và Client Secret' : 'Copy Client ID and Client Secret'}</li>
                  <li>5. {language === 'vi' ? 'Tạo folder trong Google Drive và copy Folder ID' : 'Create folder in Google Drive and copy Folder ID'}</li>
                  <li>6. {language === 'vi' ? 'Nhấn "Xác thực với Google" để kết nối' : 'Click "Authorize with Google" to connect'}</li>
                </ol>
              </div>
            </>
          )}

          {/* Service Account Configuration (Legacy) */}
          {authMethod === 'service_account' && (
            <>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                <h5 className="font-medium text-yellow-800 mb-2">
                  {language === 'vi' ? 'Service Account (Cũ)' : 'Service Account (Legacy)'}
                </h5>
                <p className="text-sm text-yellow-700">
                  {language === 'vi' 
                    ? 'Service Account có giới hạn storage quota. Khuyên dùng OAuth 2.0 thay thế.'
                    : 'Service Account has storage quota limitations. OAuth 2.0 is recommended instead.'
                  }
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Service Account JSON' : 'Service Account JSON'}
                </label>
                <textarea
                  value={config.service_account_json}
                  onChange={(e) => setConfig(prev => ({ ...prev, service_account_json: e.target.value }))}
                  placeholder={language === 'vi' ? 'Paste service account JSON key tại đây...' : 'Paste service account JSON key here...'}
                  className="w-full h-40 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm"
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
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi' ? 'Folder ID từ URL Google Drive: drive.google.com/drive/folders/[FOLDER_ID]' : 'Folder ID from Google Drive URL: drive.google.com/drive/folders/[FOLDER_ID]'}
                </p>
              </div>

              {/* Test Connection Section for Service Account */}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-800">
                    {language === 'vi' ? 'Test kết nối' : 'Test Connection'}
                  </h4>
                  <button
                    onClick={onTest}
                    disabled={testLoading || !config.service_account_json || !config.folder_id}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center gap-2"
                  >
                    {testLoading && <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>}
                    {language === 'vi' ? 'Test kết nối' : 'Test Connection'}
                  </button>
                </div>
                <p className="text-xs text-gray-500">
                  {language === 'vi' ? 'Kiểm tra kết nối trước khi lưu cấu hình' : 'Test connection before saving configuration'}
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
                  <li>6. {language === 'vi' ? 'Test kết nối trước khi lưu' : 'Test connection before saving'}</li>
                </ol>
              </div>
            </>
          )}
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
            disabled={
              authMethod === 'apps_script'
                ? (!config.web_app_url || !config.folder_id)
                : authMethod === 'oauth' 
                  ? (!config.client_id || !config.client_secret || !config.folder_id)
                  : (!config.service_account_json || !config.folder_id)
            }
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-all"
          >
            {language === 'vi' ? 'Lưu cấu hình' : 'Save Configuration'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Company Google Drive Configuration Modal Component
const CompanyGoogleDriveModal = ({ companyId, config, setConfig, currentConfig, onClose, onSave, onTest, testLoading, language }) => {
  const [authMethod, setAuthMethod] = useState(config.auth_method || 'apps_script');
  const [oauthLoading, setOauthLoading] = useState(false);
  
  // Debug logging on modal render
  console.log('🔍 CompanyGoogleDriveModal rendered with:');
  console.log('   companyId:', companyId);
  console.log('   config:', config);
  console.log('   authMethod:', authMethod);
  
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleAuthMethodChange = (method) => {
    setAuthMethod(method);
    setConfig(prev => ({ ...prev, auth_method: method }));
  };

  const handleAppsScriptTest = async () => {
    console.log('🔍 Debug - handleAppsScriptTest called');
    console.log('   CompanyId:', companyId);
    console.log('   Config:', config);
    
    if (!companyId) {
      console.error('❌ No Company ID available in handleAppsScriptTest');
      toast.error(language === 'vi' ? 'Lỗi: Không có Company ID' : 'Error: No Company ID');
      return;
    }
    
    try {
      setOauthLoading(true);
      
      // Use the test configuration endpoint instead of configure endpoint for testing
      const response = await axios.post(`${API}/companies/${companyId}/gdrive/configure-proxy`, {
        web_app_url: config.web_app_url,
        folder_id: config.folder_id
      });
      
      if (response.data.success) {
        toast.success(language === 'vi' ? 'Apps Script proxy hoạt động!' : 'Apps Script proxy working!');
      } else {
        toast.error(language === 'vi' ? 'Apps Script proxy lỗi' : 'Apps Script proxy error');
      }
    } catch (error) {
      console.error('Apps Script test error:', error);
      const errorMessage = error.response?.data?.message || error.message;
      toast.error(language === 'vi' ? `Lỗi test Apps Script: ${errorMessage}` : `Apps Script test error: ${errorMessage}`);
    } finally {
      setOauthLoading(false);
    }
  };

  const handleOAuthAuthorize = async () => {
    try {
      setOauthLoading(true);
      
      const oauthConfig = {
        client_id: config.client_id,
        client_secret: config.client_secret,
        redirect_uri: 'https://vessel-docs-1.preview.emergentagent.com/oauth2callback',
        folder_id: config.folder_id
      };

      const response = await axios.post(`${API}/companies/${companyId}/gdrive/oauth/authorize`, oauthConfig);
      
      if (response.data.success && response.data.authorization_url) {
        // Store state for later use
        sessionStorage.setItem('oauth_state', response.data.state);
        
        // Redirect to Google OAuth
        window.location.href = response.data.authorization_url;
      } else {
        toast.error(language === 'vi' ? 'Không thể tạo URL xác thực' : 'Failed to generate authorization URL');
      }
    } catch (error) {
      console.error('OAuth authorization error:', error);
      toast.error(language === 'vi' ? 'Lỗi xác thực OAuth' : 'OAuth authorization error');
    } finally {
      setOauthLoading(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]" 
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? 'Cấu hình Google Drive công ty' : 'Company Google Drive Configuration'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Current Configuration Display */}
        {currentConfig?.configured && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h4 className="font-medium text-green-800 mb-2">
              {language === 'vi' ? 'Cấu hình hiện tại:' : 'Current Configuration:'}
            </h4>
            <div className="text-sm text-green-700 space-y-1">
              <div><strong>{language === 'vi' ? 'Method:' : 'Auth Method:'}</strong> {
                currentConfig.auth_method === 'apps_script' 
                  ? 'Apps Script' 
                  : currentConfig.auth_method === 'oauth' 
                    ? 'OAuth 2.0' 
                    : 'Service Account'
              }</div>
              <div><strong>{language === 'vi' ? 'Folder ID:' : 'Folder ID:'}</strong> {currentConfig.folder_id}</div>
              {currentConfig.last_sync && (
                <div><strong>{language === 'vi' ? 'Đồng bộ cuối:' : 'Last Sync:'}</strong> {currentConfig.last_sync ? new Date(currentConfig.last_sync).toLocaleString() : 'Never'}</div>
              )}
            </div>
          </div>
        )}

        {/* Authentication Method Selector */}
        <div className="mb-6">
          <h4 className="font-medium text-gray-800 mb-3">
            {language === 'vi' ? 'Phương thức xác thực' : 'Authentication Method'}
          </h4>
          <div className="flex space-x-2 mb-4 flex-wrap">
            <button
              type="button"
              onClick={() => handleAuthMethodChange('apps_script')}
              className={`px-3 py-2 rounded-lg transition-all text-sm ${
                authMethod === 'apps_script'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Apps Script ({language === 'vi' ? 'Đơn giản nhất' : 'Easiest'})
            </button>
            <button
              type="button"
              onClick={() => handleAuthMethodChange('oauth')}
              className={`px-3 py-2 rounded-lg transition-all text-sm ${
                authMethod === 'oauth'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              OAuth 2.0 ({language === 'vi' ? 'Khuyên dùng' : 'Recommended'})
            </button>
            <button
              type="button"
              onClick={() => handleAuthMethodChange('service_account')}
              className={`px-3 py-2 rounded-lg transition-all text-sm ${
                authMethod === 'service_account'
                  ? 'bg-yellow-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Service Account ({language === 'vi' ? 'Cũ' : 'Legacy'})
            </button>
          </div>
        </div>
        
        <div className="space-y-6">
          {/* Apps Script Configuration */}
          {authMethod === 'apps_script' && (
            <>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <h5 className="font-medium text-green-800 mb-2">
                  ✨ {language === 'vi' ? 'Google Apps Script (Đơn giản nhất)' : 'Google Apps Script (Easiest)'}
                </h5>
                <p className="text-sm text-green-700">
                  {language === 'vi' 
                    ? 'Sử dụng Google Apps Script cho công ty này. Không cần verification từ Google!'
                    : 'Use Google Apps Script for this company. No Google verification needed!'
                  }
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Google Apps Script Web App URL' : 'Google Apps Script Web App URL'}
                </label>
                <input
                  type="url"
                  value={config.web_app_url}
                  onChange={(e) => setConfig(prev => ({ ...prev, web_app_url: e.target.value }))}
                  placeholder="https://script.google.com/macros/s/AKfycby.../exec"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi' 
                    ? 'Ví dụ: https://script.google.com/macros/s/AKfycbzi8DdyZ85Oi9H6s-HH5CTp28HFquCWB-CquduS7MT1SBytLB_awx1UqASBVvL51SE/exec'
                    : 'Example: https://script.google.com/macros/s/AKfycbzi8DdyZ85Oi9H6s-HH5CTp28HFquCWB-CquduS7MT1SBytLB_awx1UqASBVvL51SE/exec'
                  }
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
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi' ? 'Folder ID từ URL Google Drive: drive.google.com/drive/folders/[FOLDER_ID]' : 'Folder ID from Google Drive URL: drive.google.com/drive/folders/[FOLDER_ID]'}
                </p>
              </div>

              {/* Apps Script Test Connection */}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-800">
                    {language === 'vi' ? 'Test kết nối Apps Script' : 'Test Apps Script Connection'}
                  </h4>
                  <button
                    onClick={handleAppsScriptTest}
                    disabled={oauthLoading || !config.web_app_url || !config.folder_id}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center gap-2"
                  >
                    {oauthLoading && <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>}
                    {language === 'vi' ? 'Test kết nối' : 'Test Connection'}
                  </button>
                </div>
                <p className="text-xs text-gray-500">
                  {language === 'vi' ? 'Test kết nối Apps Script trước khi lưu' : 'Test Apps Script connection before saving'}
                </p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-green-800 mb-2">
                  📋 {language === 'vi' ? 'Hướng dẫn setup Apps Script:' : 'Apps Script Setup Instructions:'}
                </h4>
                <ol className="text-sm text-green-700 space-y-1">
                  <li>1. {language === 'vi' ? 'Truy cập' : 'Go to'} <a href="https://script.google.com" target="_blank" className="underline">script.google.com</a></li>
                  <li>2. {language === 'vi' ? 'Tạo New project cho công ty này' : 'Create New project for this company'}</li>
                  <li>3. {language === 'vi' ? 'Copy code từ APPS_SCRIPT_FIXED_CODE.js' : 'Copy code from APPS_SCRIPT_FIXED_CODE.js'}</li>
                  <li>4. {language === 'vi' ? 'Sửa FOLDER_ID với folder ID riêng của công ty' : 'Update FOLDER_ID with company-specific folder ID'}</li>
                  <li>5. {language === 'vi' ? 'Deploy as Web app → Execute as: Me → Who has access: Anyone' : 'Deploy as Web app → Execute as: Me → Who has access: Anyone'}</li>
                  <li>6. {language === 'vi' ? 'Copy Web app URL và paste vào trên' : 'Copy Web app URL and paste above'}</li>
                </ol>
              </div>
            </>
          )}

          {/* OAuth Configuration */}
          {authMethod === 'oauth' && (
            <>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <h5 className="font-medium text-blue-800 mb-2">
                  {language === 'vi' ? 'OAuth 2.0 Configuration cho Công ty' : 'OAuth 2.0 Configuration for Company'}
                </h5>
                <p className="text-sm text-blue-700">
                  {language === 'vi' 
                    ? 'OAuth 2.0 cho phép công ty truy cập Google Drive riêng một cách an toàn.'
                    : 'OAuth 2.0 allows the company to securely access its dedicated Google Drive.'
                  }
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Client ID' : 'Client ID'}
                </label>
                <input
                  type="text"
                  value={config.client_id}
                  onChange={(e) => setConfig(prev => ({ ...prev, client_id: e.target.value }))}
                  placeholder="123456789012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Client Secret' : 'Client Secret'}
                </label>
                <input
                  type="password"
                  value={config.client_secret}
                  onChange={(e) => setConfig(prev => ({ ...prev, client_secret: e.target.value }))}
                  placeholder="GOCSPX-abcdefghijklmnopqrstuvwxyz123456"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
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
                  {language === 'vi' ? 'Folder ID riêng cho công ty này' : 'Dedicated folder ID for this company'}
                </p>
              </div>

              {/* OAuth Authorization Button */}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-800">
                    {language === 'vi' ? 'Xác thực OAuth' : 'OAuth Authorization'}
                  </h4>
                  <button
                    onClick={handleOAuthAuthorize}
                    disabled={oauthLoading || !config.client_id || !config.client_secret || !config.folder_id}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center gap-2"
                  >
                    {oauthLoading && <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>}
                    {language === 'vi' ? 'Xác thực với Google' : 'Authorize with Google'}
                  </button>
                </div>
                <p className="text-xs text-gray-500">
                  {language === 'vi' ? 'Nhấn để xác thực công ty với Google Drive' : 'Click to authorize company with Google Drive'}
                </p>
              </div>
            </>
          )}

          {/* Service Account Configuration (Legacy) */}
          {authMethod === 'service_account' && (
            <>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                <h5 className="font-medium text-yellow-800 mb-2">
                  {language === 'vi' ? 'Service Account cho Công ty (Cũ)' : 'Service Account for Company (Legacy)'}
                </h5>
                <p className="text-sm text-yellow-700">
                  {language === 'vi' 
                    ? 'Service Account có giới hạn storage quota. Khuyên dùng Apps Script thay thế.'
                    : 'Service Account has storage quota limitations. Apps Script is recommended instead.'
                  }
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Service Account JSON' : 'Service Account JSON'}
                </label>
                <textarea
                  value={config.service_account_json}
                  onChange={(e) => setConfig(prev => ({ ...prev, service_account_json: e.target.value }))}
                  placeholder={language === 'vi' ? 'Paste service account JSON key cho công ty này...' : 'Paste service account JSON key for this company...'}
                  className="w-full h-40 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi' ? 'Tạo Service Account riêng cho công ty này' : 'Create dedicated Service Account for this company'}
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
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi' ? 'Folder ID riêng cho công ty này' : 'Dedicated folder ID for this company'}
                </p>
              </div>

              {/* Test Connection Section for Service Account */}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-800">
                    {language === 'vi' ? 'Test kết nối' : 'Test Connection'}
                  </h4>
                  <button
                    onClick={onTest}
                    disabled={testLoading || !config.service_account_json || !config.folder_id}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center gap-2"
                  >
                    {testLoading && <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>}
                    {language === 'vi' ? 'Test kết nối' : 'Test Connection'}
                  </button>
                </div>
                <p className="text-xs text-gray-500">
                  {language === 'vi' ? 'Kiểm tra kết nối trước khi lưu cấu hình' : 'Test connection before saving configuration'}
                </p>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="font-medium text-yellow-800 mb-2">
                  {language === 'vi' ? 'Hướng dẫn thiết lập:' : 'Setup Instructions:'}
                </h4>
                <ol className="text-sm text-yellow-700 space-y-1">
                  <li>1. {language === 'vi' ? 'Tạo project riêng cho công ty trong Google Cloud Console' : 'Create dedicated project for company in Google Cloud Console'}</li>
                  <li>2. {language === 'vi' ? 'Enable Google Drive API' : 'Enable Google Drive API'}</li>
                  <li>3. {language === 'vi' ? 'Tạo Service Account và download JSON key' : 'Create Service Account and download JSON key'}</li>
                  <li>4. {language === 'vi' ? 'Tạo folder riêng và share với service account email' : 'Create dedicated folder and share with service account email'}</li>
                  <li>5. {language === 'vi' ? 'Copy Folder ID từ URL' : 'Copy Folder ID from URL'}</li>
                  <li>6. {language === 'vi' ? 'Test kết nối trước khi lưu' : 'Test connection before saving'}</li>
                </ol>
              </div>
            </>
          )}
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
            disabled={
              authMethod === 'apps_script'
                ? (!config.web_app_url || !config.folder_id)
                : authMethod === 'oauth' 
                  ? (!config.client_id || !config.client_secret || !config.folder_id)
                  : (!config.service_account_json || !config.folder_id)
            }
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-all"
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
  const departments = ['technical', 'operations', 'safety', 'commercial', 'crewing', 'ship_crew'];
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

// AI Configuration Modal Component
const AIConfigModal = ({ config, setConfig, onClose, onSave, language }) => {
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const providers = [
    { value: 'openai', label: 'OpenAI', models: ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo'] },
    { value: 'anthropic', label: 'Anthropic', models: ['claude-3-sonnet', 'claude-3-haiku'] },
    { value: 'google', label: 'Google', models: ['gemini-pro', 'gemini-pro-vision'] }
  ];

  const selectedProvider = providers.find(p => p.value === config.provider);

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" 
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? 'Cấu hình AI' : 'AI Configuration'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Nhà cung cấp AI' : 'AI Provider'}
            </label>
            <select
              value={config.provider}
              onChange={(e) => {
                const provider = providers.find(p => p.value === e.target.value);
                setConfig(prev => ({
                  ...prev,
                  provider: e.target.value,
                  model: provider?.models[0] || 'gpt-4o'
                }));
              }}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {providers.map(provider => (
                <option key={provider.value} value={provider.value}>
                  {provider.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Mô hình AI' : 'AI Model'}
            </label>
            <select
              value={config.model}
              onChange={(e) => setConfig(prev => ({ ...prev, model: e.target.value }))}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {selectedProvider?.models.map(model => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              {language === 'vi' ? 
                'Chú ý: Thay đổi cấu hình AI sẽ ảnh hưởng đến tất cả tính năng phân tích tài liệu và tìm kiếm thông minh.' : 
                'Note: Changing AI configuration will affect all document analysis and smart search features.'
              }
            </p>
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
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-all"
          >
            {language === 'vi' ? 'Lưu cấu hình' : 'Save Configuration'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Company Form Modal Component
const CompanyFormModal = ({ 
  companyData, 
  setCompanyData, 
  onClose, 
  onSubmit, 
  language, 
  isEdit = false,
  companyGdriveCurrentConfig,
  fetchCompanyGoogleDriveConfig,
  fetchCompanyGoogleDriveStatus,
  setShowCompanyGoogleDrive
}) => {
  const [logoFile, setLogoFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleSubmitWithLogo = async () => {
    try {
      // First submit the company data
      await onSubmit();
      
      // If we have a logo file and the company was created/updated successfully, upload the logo
      if (logoFile && companyData.id) {
        await handleLogoUpload(companyData.id);
      }
    } catch (error) {
      console.error('Error submitting company:', error);
    }
  };

  const handleLogoUpload = async (companyId) => {
    if (!logoFile) return;
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', logoFile);
      
      const response = await axios.post(`${API}/companies/${companyId}/upload-logo`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });
      
      toast.success(language === 'vi' ? 'Logo đã được tải lên thành công!' : 'Logo uploaded successfully!');
      
      // Refresh companies list to show the new logo
      if (window.fetchCompanies) {
        window.fetchCompanies();
      }
      
    } catch (error) {
      toast.error(language === 'vi' ? 'Không thể tải lên logo!' : 'Failed to upload logo!');
      console.error('Logo upload error:', error);
    } finally {
      setUploading(false);
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
            {isEdit ? 
              (language === 'vi' ? 'Chỉnh sửa công ty' : 'Edit Company') :
              (language === 'vi' ? 'Thêm công ty mới' : 'Add New Company')
            }
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên công ty (Tiếng Việt)' : 'Company Name (Vietnamese)'} *
              </label>
              <input
                type="text"
                required
                value={companyData.name_vn}
                onChange={(e) => setCompanyData(prev => ({ ...prev, name_vn: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Nhập tên công ty bằng tiếng Việt' : 'Enter company name in Vietnamese'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên công ty (Tiếng Anh)' : 'Company Name (English)'} *
              </label>
              <input
                type="text"
                required
                value={companyData.name_en}
                onChange={(e) => setCompanyData(prev => ({ ...prev, name_en: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Nhập tên công ty bằng tiếng Anh' : 'Enter company name in English'}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Địa chỉ (Tiếng Việt)' : 'Address (Vietnamese)'} *
              </label>
              <textarea
                required
                value={companyData.address_vn}
                onChange={(e) => setCompanyData(prev => ({ ...prev, address_vn: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows="3"
                placeholder={language === 'vi' ? 'Nhập địa chỉ bằng tiếng Việt' : 'Enter address in Vietnamese'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Địa chỉ (Tiếng Anh)' : 'Address (English)'} *
              </label>
              <textarea
                required
                value={companyData.address_en}
                onChange={(e) => setCompanyData(prev => ({ ...prev, address_en: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows="3"
                placeholder={language === 'vi' ? 'Nhập địa chỉ bằng tiếng Anh' : 'Enter address in English'}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Mã số thuế' : 'Tax ID'} *
            </label>
            <input
              type="text"
              required
              value={companyData.tax_id}
              onChange={(e) => setCompanyData(prev => ({ ...prev, tax_id: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={language === 'vi' ? 'Nhập mã số thuế' : 'Enter tax ID'}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Gmail</label>
              <input
                type="email"
                value={companyData.gmail}
                onChange={(e) => setCompanyData(prev => ({ ...prev, gmail: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="company@gmail.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Zalo</label>
              <input
                type="text"
                value={companyData.zalo}
                onChange={(e) => setCompanyData(prev => ({ ...prev, zalo: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Số điện thoại Zalo' : 'Zalo phone number'}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Thời hạn sử dụng hệ thống' : 'System Usage Expiry'}
            </label>
            <input
              type="date"
              value={companyData.system_expiry}
              onChange={(e) => setCompanyData(prev => ({ ...prev, system_expiry: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Company Google Drive Configuration */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-800 flex items-center">
              <svg className="w-5 h-5 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/>
                <path d="M8 6h4v2H8V6zM8 10h4v2H8v-2z"/>
              </svg>
              {language === 'vi' ? 'Cấu hình Google Drive công ty' : 'Company Google Drive Configuration'}
            </h3>
            
            {/* Current Configuration Status */}
            {companyGdriveCurrentConfig && companyGdriveCurrentConfig.configured && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <h4 className="font-medium text-green-800 mb-2">
                  {language === 'vi' ? 'Cấu hình hiện tại:' : 'Current Configuration:'}
                </h4>
                <div className="text-sm text-green-700 space-y-1">
                  <div><strong>{language === 'vi' ? 'Phương thức:' : 'Auth Method:'}</strong> {
                    companyGdriveCurrentConfig.auth_method === 'apps_script' 
                      ? 'Apps Script' 
                      : companyGdriveCurrentConfig.auth_method === 'oauth' 
                        ? 'OAuth 2.0' 
                        : 'Service Account'
                  }</div>
                  <div><strong>{language === 'vi' ? 'Folder ID:' : 'Folder ID:'}</strong> {companyGdriveCurrentConfig.folder_id}</div>
                  {companyGdriveCurrentConfig.service_account_email && (
                    <div><strong>{language === 'vi' ? 'Account Email:' : 'Account Email:'}</strong> {companyGdriveCurrentConfig.service_account_email}</div>
                  )}
                  {companyGdriveCurrentConfig.last_sync && (
                    <div><strong>{language === 'vi' ? 'Đồng bộ cuối:' : 'Last Sync:'}</strong> {new Date(companyGdriveCurrentConfig.last_sync).toLocaleString()}</div>
                  )}
                </div>
              </div>
            )}

            {/* Configuration Status Badge */}
            <div className="mb-4 flex items-center space-x-3">
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                companyGdriveCurrentConfig?.configured 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {companyGdriveCurrentConfig?.configured 
                  ? (language === 'vi' ? 'Đã cấu hình' : 'Configured')
                  : (language === 'vi' ? 'Chưa cấu hình' : 'Not configured')
                }
              </div>
              
              {companyGdriveCurrentConfig?.configured && (
                <button
                  onClick={() => {
                    if (companyData.id) {
                      fetchCompanyGoogleDriveConfig(companyData.id);
                      fetchCompanyGoogleDriveStatus(companyData.id);
                      setShowCompanyGoogleDrive(true);
                    }
                  }}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-all"
                >
                  {language === 'vi' ? 'Đồng bộ ngay' : 'Sync Now'}
                </button>
              )}
            </div>

            {/* Configure Button */}
            <button
              onClick={() => {
                console.log('🔍 Debug - Configure Company Google Drive clicked');
                console.log('   companyData:', companyData);
                console.log('   companyData.id:', companyData.id);
                
                if (companyData.id) {
                  console.log('✅ Using companyData.id:', companyData.id);
                  fetchCompanyGoogleDriveConfig(companyData.id);
                  fetchCompanyGoogleDriveStatus(companyData.id);
                  setShowCompanyGoogleDrive(true);
                } else {
                  console.log('❌ No company ID found');
                  toast.warning(language === 'vi' ? 'Vui lòng lưu công ty trước khi cấu hình Google Drive' : 'Please save company before configuring Google Drive');
                }
              }}
              className="w-full px-4 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-all font-medium"
            >
              {language === 'vi' ? 'Cấu hình Google Drive công ty' : 'Configure Company Google Drive'}
            </button>

            <div className="mt-3 bg-purple-50 border border-purple-200 rounded-lg p-3">
              <p className="text-sm text-purple-700">
                {language === 'vi' 
                  ? 'Cấu hình Google Drive riêng cho công ty này. Hỗ trợ 3 phương thức: Apps Script (đơn giản), OAuth 2.0 (khuyên dùng), Service Account (cũ).'
                  : 'Configure dedicated Google Drive for this company. Supports 3 methods: Apps Script (easiest), OAuth 2.0 (recommended), Service Account (legacy).'
                }
              </p>
            </div>
          </div>

          {/* Company Logo Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Logo công ty' : 'Company Logo'}
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setLogoFile(e.target.files[0])}
              className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <p className="text-xs text-gray-500 mt-1">
              {language === 'vi' ? 'Hỗ trợ: JPG, PNG, GIF (tối đa 5MB)' : 'Supported: JPG, PNG, GIF (max 5MB)'}
            </p>
            {isEdit && companyData.logo_url && (
              <div className="mt-2">
                <img 
                  src={`${API}${companyData.logo_url}`} 
                  alt="Current logo" 
                  className="w-16 h-16 object-contain border border-gray-200 rounded"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi' ? 'Logo hiện tại' : 'Current logo'}
                </p>
              </div>
            )}
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-medium text-yellow-800 mb-2">
              {language === 'vi' ? 'Lưu ý:' : 'Note:'}
            </h4>
            <ul className="text-sm text-yellow-700 space-y-1">
              <li>• {language === 'vi' ? 'Thông tin công ty sẽ được lưu trên Google Drive' : 'Company data will be stored on Google Drive'}</li>
              <li>• {language === 'vi' ? 'Logo sẽ được tải lên sau khi tạo/cập nhật công ty' : 'Logo will be uploaded after creating/updating company'}</li>
              <li>• {language === 'vi' ? 'Chỉ Super Admin mới có quyền truy cập tính năng này' : 'Only Super Admin can access this feature'}</li>
            </ul>
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
            onClick={handleSubmitWithLogo}
            disabled={uploading}
            className="px-6 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center"
          >
            {uploading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>}
            {isEdit ?
              (language === 'vi' ? 'Cập nhật công ty' : 'Update Company') :
              (language === 'vi' ? 'Tạo công ty' : 'Create Company')
            }
          </button>
        </div>
      </div>
    </div>
  );
};

// Edit User Modal Component
const EditUserModal = ({ userData, setUserData, onClose, onSubmit, language, companies, ships }) => {
  const [permissions, setPermissions] = useState({
    categories: [],
    departments: [],
    sensitivity_levels: [],
    permissions: []
  });

  // Update permissions when userData changes
  useEffect(() => {
    if (userData && userData.permissions) {
      setPermissions({
        categories: userData.permissions.categories || [],
        departments: userData.permissions.departments || [],
        sensitivity_levels: userData.permissions.sensitivity_levels || [],
        permissions: userData.permissions.permissions || []
      });
    } else {
      setPermissions({
        categories: [],
        departments: [],
        sensitivity_levels: [],
        permissions: []
      });
    }
  }, [userData]);

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const roleOptions = [
    { value: 'viewer', label: language === 'vi' ? 'Thuyền viên' : 'Crew' },
    { value: 'editor', label: language === 'vi' ? 'Sĩ quan' : 'Ship Officer' },
    { value: 'manager', label: language === 'vi' ? 'Cán bộ công ty' : 'Company Officer' },
    { value: 'admin', label: language === 'vi' ? 'Quản trị viên' : 'Admin' },
    { value: 'super_admin', label: language === 'vi' ? 'Siêu quản trị' : 'Super Admin' }
  ];

  const categories = ['certificates', 'inspection_records', 'survey_reports', 'drawings_manuals', 'other_documents'];
  const departments = ['technical', 'operations', 'safety', 'commercial', 'crewing', 'ship_crew'];
  const sensitivityLevels = ['public', 'internal', 'confidential', 'restricted'];
  const permissionTypes = ['read', 'write', 'delete', 'manage_users', 'system_control'];

  const categoryNames = {
    certificates: language === 'vi' ? 'Chứng chỉ' : 'Certificates',
    inspection_records: language === 'vi' ? 'Hồ sơ kiểm tra' : 'Inspection Records',
    survey_reports: language === 'vi' ? 'Báo cáo khảo sát' : 'Survey Reports',
    drawings_manuals: language === 'vi' ? 'Bản vẽ & Hướng dẫn' : 'Drawings & Manuals',
    other_documents: language === 'vi' ? 'Tài liệu khác' : 'Other Documents'
  };

  const departmentNames = {
    technical: language === 'vi' ? 'Kỹ thuật' : 'Technical',
    operations: language === 'vi' ? 'Vận hành' : 'Operations',
    safety: language === 'vi' ? 'An toàn' : 'Safety',
    commercial: language === 'vi' ? 'Thương mại' : 'Commercial',
    crewing: language === 'vi' ? 'Thuyền viên' : 'Crewing',
    ship_crew: language === 'vi' ? 'Thuyền bộ' : 'Ship Crew'
  };

  const sensitivityNames = {
    public: language === 'vi' ? 'Công khai' : 'Public',
    internal: language === 'vi' ? 'Nội bộ' : 'Internal',
    confidential: language === 'vi' ? 'Bí mật' : 'Confidential',
    restricted: language === 'vi' ? 'Hạn chế' : 'Restricted'
  };

  const permissionNames = {
    read: language === 'vi' ? 'Xem' : 'Read',
    write: language === 'vi' ? 'Ghi' : 'Write',
    delete: language === 'vi' ? 'Xóa' : 'Delete',
    manage_users: language === 'vi' ? 'Quản lý người dùng' : 'Manage Users',
    system_control: language === 'vi' ? 'Điều khiển hệ thống' : 'System Control'
  };

  // Check if user is ship crew to show/enable ship dropdown
  const isShipCrew = userData?.department === 'ship_crew';

  // Update user data with permissions when saving
  const handleSubmitWithPermissions = () => {
    setUserData(prev => ({ ...prev, permissions }));
    onSubmit();
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" 
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? 'Chỉnh sửa người dùng' : 'Edit User'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên đăng nhập' : 'Username'} *
              </label>
              <input
                type="text"
                required
                value={userData.username}
                onChange={(e) => setUserData(prev => ({ ...prev, username: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Nhập tên đăng nhập' : 'Enter username'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Họ và tên' : 'Full Name'} *
              </label>
              <input
                type="text"
                required
                value={userData.full_name}
                onChange={(e) => setUserData(prev => ({ ...prev, full_name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Nhập họ và tên' : 'Enter full name'}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={userData.email}
              onChange={(e) => setUserData(prev => ({ ...prev, email: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={language === 'vi' ? 'Nhập email (không bắt buộc)' : 'Enter email (optional)'}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Công ty' : 'Company'} *
              </label>
              <select
                required
                value={userData.company || ''}
                onChange={(e) => setUserData(prev => ({ ...prev, company: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">
                  {language === 'vi' ? 'Chọn công ty' : 'Select company'}
                </option>
                {companies.map(company => (
                  <option key={company.id} value={company.name_vn}>
                    {language === 'vi' ? company.name_vn : company.name_en}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tàu' : 'Ship'}
                {isShipCrew && <span className="text-red-500"> *</span>}
              </label>
              <select
                required={isShipCrew}
                disabled={!isShipCrew}
                value={isShipCrew ? (userData.ship || '') : ''}
                onChange={(e) => setUserData(prev => ({ ...prev, ship: e.target.value }))}
                className={`w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  !isShipCrew ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : ''
                }`}
              >
                <option value="">
                  {isShipCrew 
                    ? (language === 'vi' ? 'Chọn tàu' : 'Select ship')
                    : (language === 'vi' ? 'Chỉ dành cho Thuyền bộ' : 'Ship Crew only')
                  }
                </option>
                {isShipCrew && ships.map(ship => (
                  <option key={ship.id} value={ship.name}>
                    {ship.name}
                  </option>
                ))}
              </select>
              {!isShipCrew && (
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi' 
                    ? 'Chỉ hiển thị khi chọn phòng ban "Thuyền bộ"' 
                    : 'Only available for "Ship Crew" department'}
                </p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Phòng ban' : 'Department'} *
            </label>
            <select
              required
              value={userData.department || ''}
              onChange={(e) => setUserData(prev => ({ ...prev, department: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {departments.map(dept => (
                <option key={dept} value={dept}>
                  {departmentNames[dept]}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Vai trò' : 'Role'} *
            </label>
            <select
              required
              value={userData.role}
              onChange={(e) => setUserData(prev => ({ ...prev, role: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {roleOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Zalo *
              </label>
              <input
                type="text"
                required
                value={userData.zalo || ''}
                onChange={(e) => setUserData(prev => ({ ...prev, zalo: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Số điện thoại Zalo (bắt buộc)' : 'Zalo phone number (required)'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Gmail</label>
              <input
                type="email"
                value={userData.gmail || ''}
                onChange={(e) => setUserData(prev => ({ ...prev, gmail: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Địa chỉ Gmail (không bắt buộc)' : 'Gmail address (optional)'}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Mật khẩu mới' : 'New Password'}
            </label>
            <input
              type="password"
              value={userData.password || ''}
              onChange={(e) => setUserData(prev => ({ ...prev, password: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={language === 'vi' ? 'Để trống nếu không thay đổi' : 'Leave blank if no change'}
            />
            <p className="text-xs text-gray-500 mt-1">
              {language === 'vi' ? 'Chỉ nhập nếu muốn thay đổi mật khẩu' : 'Only enter if you want to change password'}
            </p>
          </div>

          {/* Permissions Section */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">
              {language === 'vi' ? 'Phân quyền chi tiết' : 'Detailed Permissions'}
            </h3>
            
            {/* Current Permissions Summary */}
            <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
              <h4 className="font-medium mb-3 text-gray-700">
                {language === 'vi' ? 'Trạng thái phân quyền hiện tại:' : 'Current Permission Status:'}
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium text-blue-600">
                    {language === 'vi' ? 'Loại tài liệu:' : 'Categories:'}
                  </span>
                  <div className="text-gray-600">
                    {permissions.categories.length > 0 
                      ? permissions.categories.map(cat => categoryNames[cat]).join(', ')
                      : (language === 'vi' ? 'Chưa có' : 'None')
                    }
                  </div>
                </div>
                <div>
                  <span className="font-medium text-green-600">
                    {language === 'vi' ? 'Phòng ban:' : 'Departments:'}
                  </span>
                  <div className="text-gray-600">
                    {permissions.departments.length > 0 
                      ? permissions.departments.map(dept => departmentNames[dept]).join(', ')
                      : (language === 'vi' ? 'Chưa có' : 'None')
                    }
                  </div>
                </div>
                <div>
                  <span className="font-medium text-orange-600">
                    {language === 'vi' ? 'Mức bảo mật:' : 'Security:'}
                  </span>
                  <div className="text-gray-600">
                    {permissions.sensitivity_levels.length > 0 
                      ? permissions.sensitivity_levels.map(level => sensitivityNames[level]).join(', ')
                      : (language === 'vi' ? 'Chưa có' : 'None')
                    }
                  </div>
                </div>
                <div>
                  <span className="font-medium text-purple-600">
                    {language === 'vi' ? 'Quyền hạn:' : 'Permissions:'}
                  </span>
                  <div className="text-gray-600">
                    {permissions.permissions.length > 0 
                      ? permissions.permissions.map(perm => permissionNames[perm]).join(', ')
                      : (language === 'vi' ? 'Chưa có' : 'None')
                    }
                  </div>
                </div>
              </div>
            </div>
            
            <div className="grid md:grid-cols-2 gap-6">
              {/* Document Categories */}
              <div>
                <h4 className="font-medium mb-3 text-gray-700 flex items-center justify-between">
                  <span>{language === 'vi' ? 'Loại tài liệu' : 'Document Categories'}</span>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                    {permissions.categories.length}/{categories.length}
                  </span>
                </h4>
                <div className="space-y-2 max-h-32 overflow-y-auto">
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
                      <span className="text-sm">{categoryNames[cat]}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Departments */}
              <div>
                <h4 className="font-medium mb-3 text-gray-700 flex items-center justify-between">
                  <span>{language === 'vi' ? 'Phòng ban' : 'Departments'}</span>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                    {permissions.departments.length}/{departments.length}
                  </span>
                </h4>
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
                      <span className="text-sm">{departmentNames[dept]}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Sensitivity Levels */}
              <div>
                <h4 className="font-medium mb-3 text-gray-700 flex items-center justify-between">
                  <span>{language === 'vi' ? 'Mức độ bảo mật' : 'Sensitivity Levels'}</span>
                  <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded-full">
                    {permissions.sensitivity_levels.length}/{sensitivityLevels.length}
                  </span>
                </h4>
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
                      <span className="text-sm">{sensitivityNames[level]}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Permission Types */}
              <div>
                <h4 className="font-medium mb-3 text-gray-700 flex items-center justify-between">
                  <span>{language === 'vi' ? 'Loại quyền' : 'Permission Types'}</span>
                  <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                    {permissions.permissions.length}/{permissionTypes.length}
                  </span>
                </h4>
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
                      <span className="text-sm">{permissionNames[perm]}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mt-4">
              <p className="text-sm text-yellow-700">
                {language === 'vi' 
                  ? '💡 Quyền chi tiết này sẽ được áp dụng ngoài quyền cơ bản của vai trò được chọn.' 
                  : '💡 These detailed permissions will be applied in addition to the basic role permissions.'}
              </p>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-800 mb-2">
              {language === 'vi' ? 'Lưu ý:' : 'Note:'}
            </h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• {language === 'vi' ? 'Các trường có dấu (*) là bắt buộc' : 'Fields marked with (*) are required'}</li>
              <li>• {language === 'vi' ? 'Thay đổi vai trò sẽ ảnh hưởng đến quyền truy cập' : 'Role changes will affect access permissions'}</li>
              <li>• {language === 'vi' ? 'Để trống mật khẩu nếu không muốn thay đổi' : 'Leave password blank if no change needed'}</li>
              <li>• {language === 'vi' ? 'Phân quyền chi tiết sẽ bổ sung cho quyền vai trò cơ bản' : 'Detailed permissions supplement basic role permissions'}</li>
            </ul>
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
            onClick={handleSubmitWithPermissions}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all"
          >
            {language === 'vi' ? 'Cập nhật' : 'Update'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Add User Modal Component
const AddUserModal = ({ userData, setUserData, onClose, onSubmit, language, companies, ships }) => {
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const roleOptions = [
    { value: 'viewer', label: language === 'vi' ? 'Thuyền viên' : 'Crew' },
    { value: 'editor', label: language === 'vi' ? 'Sĩ quan' : 'Ship Officer' },
    { value: 'manager', label: language === 'vi' ? 'Cán bộ công ty' : 'Company Officer' },
    { value: 'admin', label: language === 'vi' ? 'Quản trị viên' : 'Admin' },
    { value: 'super_admin', label: language === 'vi' ? 'Siêu quản trị' : 'Super Admin' }
  ];

  const departmentOptions = [
    { value: 'technical', label: language === 'vi' ? 'Kỹ thuật' : 'Technical' },
    { value: 'operations', label: language === 'vi' ? 'Vận hành' : 'Operations' },
    { value: 'safety', label: language === 'vi' ? 'An toàn' : 'Safety' },
    { value: 'commercial', label: language === 'vi' ? 'Thương mại' : 'Commercial' },
    { value: 'crewing', label: language === 'vi' ? 'Thuyền viên' : 'Crewing' },
    { value: 'ship_crew', label: language === 'vi' ? 'Thuyền bộ' : 'Ship Crew' }
  ];

  // Check if user is ship crew to show/enable ship dropdown
  const isShipCrew = userData.department === 'ship_crew';

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" 
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">
            {language === 'vi' ? 'Thêm người dùng mới' : 'Add New User'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên đăng nhập' : 'Username'} *
              </label>
              <input
                type="text"
                required
                value={userData.username}
                onChange={(e) => setUserData(prev => ({ ...prev, username: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Nhập tên đăng nhập' : 'Enter username'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Họ và tên' : 'Full Name'} *
              </label>
              <input
                type="text"
                required
                value={userData.full_name}
                onChange={(e) => setUserData(prev => ({ ...prev, full_name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Nhập họ và tên' : 'Enter full name'}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={userData.email}
              onChange={(e) => setUserData(prev => ({ ...prev, email: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={language === 'vi' ? 'Nhập email (không bắt buộc)' : 'Enter email (optional)'}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Mật khẩu' : 'Password'} *
            </label>
            <input
              type="password"
              required
              value={userData.password}
              onChange={(e) => setUserData(prev => ({ ...prev, password: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={language === 'vi' ? 'Nhập mật khẩu' : 'Enter password'}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Công ty' : 'Company'} *
              </label>
              <select
                required
                value={userData.company || ''}
                onChange={(e) => setUserData(prev => ({ ...prev, company: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">
                  {language === 'vi' ? 'Chọn công ty' : 'Select company'}
                </option>
                {companies.map(company => (
                  <option key={company.id} value={company.name_vn}>
                    {language === 'vi' ? company.name_vn : company.name_en}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tàu' : 'Ship'}
                {isShipCrew && <span className="text-red-500"> *</span>}
              </label>
              <select
                required={isShipCrew}
                disabled={!isShipCrew}
                value={isShipCrew ? (userData.ship || '') : ''}
                onChange={(e) => setUserData(prev => ({ ...prev, ship: e.target.value }))}
                className={`w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  !isShipCrew ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : ''
                }`}
              >
                <option value="">
                  {isShipCrew 
                    ? (language === 'vi' ? 'Chọn tàu' : 'Select ship')
                    : (language === 'vi' ? 'Chỉ dành cho Thuyền bộ' : 'Ship Crew only')
                  }
                </option>
                {isShipCrew && ships.map(ship => (
                  <option key={ship.id} value={ship.name}>
                    {ship.name}
                  </option>
                ))}
              </select>
              {!isShipCrew && (
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi' 
                    ? 'Chỉ hiển thị khi chọn phòng ban "Thuyền bộ"' 
                    : 'Only available for "Ship Crew" department'}
                </p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Phòng ban' : 'Department'} *
            </label>
            <select
              required
              value={userData.department}
              onChange={(e) => setUserData(prev => ({ ...prev, department: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {departmentOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Vai trò' : 'Role'} *
            </label>
            <select
              required
              value={userData.role}
              onChange={(e) => setUserData(prev => ({ ...prev, role: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {roleOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Zalo *
              </label>
              <input
                type="text"
                required
                value={userData.zalo || ''}
                onChange={(e) => setUserData(prev => ({ ...prev, zalo: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Số điện thoại Zalo (bắt buộc)' : 'Zalo phone number (required)'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Gmail</label>
              <input
                type="email"
                value={userData.gmail || ''}
                onChange={(e) => setUserData(prev => ({ ...prev, gmail: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={language === 'vi' ? 'Địa chỉ Gmail (không bắt buộc)' : 'Gmail address (optional)'}
              />
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-800 mb-2">
              {language === 'vi' ? 'Lưu ý:' : 'Note:'}
            </h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• {language === 'vi' ? 'Tất cả trường có dấu (*) là bắt buộc' : 'All fields with (*) are required'}</li>
              <li>• {language === 'vi' ? 'Người dùng mới sẽ nhận được thông tin đăng nhập qua email' : 'New user will receive login credentials via email'}</li>
            </ul>
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
            onClick={onSubmit}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all"
          >
            {language === 'vi' ? 'Tạo người dùng' : 'Create User'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Add Record Modal Component
const AddRecordModal = ({ onClose, onSuccess, language, selectedShip, availableCompanies }) => {
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
  const { user } = useAuth();
  const [recordType, setRecordType] = useState(() => {
    // Default to 'certificate' if user can't create ships
    const allowedRoles = ['manager', 'admin', 'super_admin'];
    return allowedRoles.includes(user?.role) ? 'ship' : 'certificate';
  });
  // PDF Analysis state
  const [showPdfAnalysis, setShowPdfAnalysis] = useState(false);
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfAnalyzing, setPdfAnalyzing] = useState(false);
  const [shipData, setShipData] = useState({
    name: '',
    imo_number: '',
    class_society: '',
    flag: '',
    gross_tonnage: '',
    deadweight: '',
    built_year: '',
    ship_owner: '',
    company: user?.company || '' // Auto-fill with user's company
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
  const [certificateFile, setCertificateFile] = useState(null);
  const [documentData, setDocumentData] = useState({
    title: '',
    category: 'other_documents',
    description: '',
    file: null
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Check if user can create ships (Company Officer role and above)
  const canCreateShip = () => {
    const allowedRoles = ['manager', 'admin', 'super_admin'];
    return allowedRoles.includes(user?.role);
  };

  const handlePdfAnalysis = async () => {
    if (!pdfFile) {
      toast.error(language === 'vi' ? 'Vui lòng chọn file PDF!' : 'Please select a PDF file!');
      return;
    }

    setPdfAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('file', pdfFile);

      const response = await axios.post(`${API}/analyze-ship-certificate`, formData, {
        headers: {
          // Content-Type is automatically set by axios for FormData with proper boundary
        }
      });

      if (response.data.success) {
        // Auto-fill ship data with extracted information (excluding company)
        const extractedData = response.data.analysis;
        setShipData(prev => ({
          ...prev,
          name: extractedData.ship_name || prev.name,
          imo_number: extractedData.imo_number || prev.imo_number,
          class_society: extractedData.class_society || prev.class_society,
          flag: extractedData.flag || prev.flag,
          gross_tonnage: extractedData.gross_tonnage || prev.gross_tonnage,
          deadweight: extractedData.deadweight || prev.deadweight,
          built_year: extractedData.built_year || prev.built_year,
          ship_owner: extractedData.ship_owner || prev.ship_owner
          // company field intentionally NOT updated - keeps user's company
        }));
        
        toast.success(language === 'vi' ? 'Phân tích PDF thành công! Đã tự động điền thông tin tàu.' : 'PDF analysis completed! Ship information auto-filled.');
        setShowPdfAnalysis(false);
        setPdfFile(null);
      } else {
        toast.error(language === 'vi' ? 'Phân tích PDF thất bại!' : 'PDF analysis failed!');
      }
    } catch (error) {
      console.error('PDF analysis error:', error);
      const errorMessage = error.response?.data?.message || error.message;
      toast.error(language === 'vi' ? `Lỗi phân tích PDF: ${errorMessage}` : `PDF analysis error: ${errorMessage}`);
    } finally {
      setPdfAnalyzing(false);
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleSubmitShip = async () => {
    try {
      setIsSubmitting(true);
      
      // Prepare ship payload with proper data cleaning
      const shipPayload = {
        name: shipData.name?.trim() || '',
        imo: shipData.imo_number?.trim() || null, // Frontend uses imo_number, backend expects imo
        flag: shipData.flag?.trim() || '',
        ship_type: shipData.class_society?.trim() || '', // Frontend uses class_society, backend expects ship_type
        gross_tonnage: shipData.gross_tonnage ? parseFloat(shipData.gross_tonnage) : null,
        year_built: shipData.built_year ? parseInt(shipData.built_year) : null,
        ship_owner: shipData.ship_owner?.trim() || '',
        company: shipData.company?.trim() || user?.company || ''
      };
      
      // Remove null values to avoid database constraint issues
      Object.keys(shipPayload).forEach(key => {
        if (shipPayload[key] === null || shipPayload[key] === '') {
          if (key === 'imo') {
            delete shipPayload[key]; // Remove IMO entirely if empty
          } else if (['gross_tonnage', 'year_built'].includes(key)) {
            delete shipPayload[key]; // Remove optional numeric fields if empty
          }
        }
      });
      
      console.log('Ship payload:', shipPayload); // Debug log
      
      const response = await axios.post(`${API}/ships`, shipPayload);
      onSuccess('ship');
      toast.success(language === 'vi' ? 'Tàu đã được thêm thành công!' : 'Ship added successfully!');
    } catch (error) {
      console.error('Ship creation error:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      toast.error(language === 'vi' ? `Không thể thêm tàu: ${errorMessage}` : `Failed to add ship: ${errorMessage}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitCertificate = async () => {
    try {
      setIsSubmitting(true);
      
      if (certificateFile) {
        // Submit certificate with file upload to Company Google Drive
        const formData = new FormData();
        formData.append('file', certificateFile);
        formData.append('ship_id', selectedShip?.id || '');
        formData.append('cert_name', certificateData.cert_name);
        formData.append('cert_no', certificateData.cert_no);
        formData.append('issue_date', new Date(certificateData.issue_date).toISOString());
        formData.append('valid_date', new Date(certificateData.valid_date).toISOString());
        if (certificateData.last_endorse) {
          formData.append('last_endorse', new Date(certificateData.last_endorse).toISOString());
        }
        if (certificateData.next_survey) {
          formData.append('next_survey', new Date(certificateData.next_survey).toISOString());
        }
        formData.append('category', certificateData.category);
        formData.append('sensitivity_level', certificateData.sensitivity_level);
        
        const response = await axios.post(`${API}/certificates/upload-with-file`, formData, {
          headers: {
            // Content-Type is automatically set by axios for FormData with proper boundary
          }
        });
        
        toast.success(language === 'vi' ? 'Chứng chỉ và tập tin đã được tải lên thành công!' : 'Certificate and file uploaded successfully!');
      } else {
        // Submit certificate metadata only (existing functionality)
        const certPayload = {
          ...certificateData,
          issue_date: new Date(certificateData.issue_date).toISOString(),
          valid_date: new Date(certificateData.valid_date).toISOString(),
          last_endorse: certificateData.last_endorse ? new Date(certificateData.last_endorse).toISOString() : null,
          next_survey: certificateData.next_survey ? new Date(certificateData.next_survey).toISOString() : null
        };
        
        const response = await axios.post(`${API}/certificates`, certPayload);
        toast.success(language === 'vi' ? 'Chứng chỉ đã được thêm thành công!' : 'Certificate added successfully!');
      }
      
      onSuccess('certificate');
    } catch (error) {
      console.error('Certificate creation error:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      
      // Handle specific Google Drive configuration errors
      if (errorMessage.includes('Google Drive not configured')) {
        toast.error(language === 'vi' 
          ? 'Google Drive chưa được cấu hình cho công ty của bạn. Vui lòng liên hệ quản trị viên để cấu hình Google Drive.' 
          : 'Google Drive not configured for your company. Please contact administrator to configure Google Drive.');
      } else if (errorMessage.includes('File size exceeds')) {
        toast.error(language === 'vi' 
          ? 'Kích thước tập tin vượt quá giới hạn 150MB' 
          : 'File size exceeds 150MB limit');
      } else {
        toast.error(language === 'vi' 
          ? `Không thể tải lên chứng chỉ: ${errorMessage}` 
          : `Failed to upload certificate: ${errorMessage}`);
      }
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
            {/* Ship option - only for Company Officer and above */}
            {canCreateShip() && (
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
            )}
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
                value="survey_report"
                checked={recordType === 'survey_report'}
                onChange={(e) => setRecordType(e.target.value)}
                className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500"
              />
              <span>{language === 'vi' ? 'Báo cáo khảo sát' : 'Survey Report'}</span>
            </label>
          </div>
          
          {/* Permission message for non-eligible users */}
          {!canCreateShip() && (
            <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                <span className="font-medium">ℹ️ {language === 'vi' ? 'Lưu ý:' : 'Note:'}</span>
                {' '}
                {language === 'vi' 
                  ? 'Chỉ có Company Officer trở lên mới có thể tạo hồ sơ tàu mới.'
                  : 'Only Company Officer and above can create new ship records.'
                }
              </p>
            </div>
          )}
        </div>

        {/* PDF Analysis Section for Ship */}
        {recordType === 'ship' && (
          <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-blue-800 mb-1">
                  {language === 'vi' ? 'Thêm tàu mới từ Giấy chứng nhận' : 'Add Ship from Certificate'}
                </h4>
                <p className="text-sm text-blue-600">
                  {language === 'vi' ? 'Upload file PDF và AI sẽ tự động điền thông tin tàu' : 'Upload PDF file and AI will auto-fill ship information'}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowPdfAnalysis(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-all flex items-center"
              >
                <span className="mr-2">📄</span>
                {language === 'vi' ? 'Upload PDF' : 'Upload PDF'}
              </button>
            </div>
          </div>
        )}

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
                  {language === 'vi' ? 'Tổ chức Phân cấp' : 'Class Society'} *
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
                  {language === 'vi' ? 'Tổng Dung Tích (GT)' : 'Gross Tonnage (GT)'}
                </label>
                <input
                  type="number"
                  value={shipData.gross_tonnage}
                  onChange={(e) => setShipData(prev => ({ ...prev, gross_tonnage: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Trọng Tải (DWT)' : 'Deadweight (DWT)'}
                </label>
                <input
                  type="number"
                  value={shipData.deadweight}
                  onChange={(e) => setShipData(prev => ({ ...prev, deadweight: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Năm đóng' : 'Built Year'}
                </label>
                <input
                  type="number"
                  value={shipData.built_year}
                  onChange={(e) => setShipData(prev => ({ ...prev, built_year: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="2020"
                />
              </div>
            </div>

            {/* Ship Owner and Company Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Chủ tàu' : 'Ship Owner'} *
                </label>
                <select
                  required
                  value={shipData.ship_owner}
                  onChange={(e) => setShipData(prev => ({ ...prev, ship_owner: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">{language === 'vi' ? 'Chọn chủ tàu' : 'Select ship owner'}</option>
                  {availableCompanies.map(company => (
                    <option key={company.id} value={language === 'vi' ? company.name_vn : company.name_en}>
                      {language === 'vi' ? company.name_vn : company.name_en}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Công ty quản lý' : 'Company'} *
                </label>
                <div className="relative">
                  <select
                    required
                    disabled
                    value={shipData.company}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed"
                  >
                    <option value={shipData.company}>
                      {shipData.company || (language === 'vi' ? 'Công ty của bạn' : 'Your company')}
                    </option>
                  </select>
                  <div className="absolute right-2 top-2 text-gray-400">
                    🔒
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'vi' 
                    ? 'Tự động điền từ công ty của bạn' 
                    : 'Auto-filled from your company'
                  }
                </p>
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
            
            {/* Multi-File Upload Section */}
            <div className="border-2 border-dashed border-blue-300 rounded-lg p-6 bg-blue-50">
              <div className="text-center">
                <svg
                  className="mx-auto h-12 w-12 text-blue-400 mb-4"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                  aria-hidden="true"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <h3 className="text-lg font-medium text-blue-900 mb-2">
                  {language === 'vi' ? 'Tải lên và phân loại tự động bằng AI' : 'Upload & Auto-Classify with AI'}
                </h3>
                <p className="text-blue-700 mb-4">
                  {language === 'vi' 
                    ? 'Tải lên nhiều file chứng chỉ cùng lúc. AI sẽ tự động phân loại và tạo record.' 
                    : 'Upload multiple certificate files at once. AI will automatically classify and create records.'}
                </p>
                
                <label
                  htmlFor="multi-file-upload"
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer transition-colors"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  {language === 'vi' ? 'Chọn nhiều file' : 'Select Multiple Files'}
                  <input
                    id="multi-file-upload"
                    name="multi-file-upload"
                    type="file"
                    multiple
                    className="sr-only"
                    onChange={(e) => handleMultiFileUpload(e.target.files)}
                    accept="*/*"
                  />
                </label>
                
                <p className="text-xs text-blue-600 mt-2">
                  {language === 'vi' ? 'Tối đa 150MB mỗi file • Tất cả định dạng được hỗ trợ' : 'Max 150MB per file • All formats supported'}
                </p>
              </div>
              
              {/* Multi-file upload progress */}
              {multiFileUploads && multiFileUploads.length > 0 && (
                <div className="mt-6 space-y-3">
                  <h4 className="font-medium text-gray-900">
                    {language === 'vi' ? 'Tiến trình xử lý' : 'Processing Progress'}
                  </h4>
                  {multiFileUploads.map((fileUpload, index) => (
                    <div key={index} className="bg-white p-3 rounded-lg border">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div className={`w-3 h-3 rounded-full mr-3 ${
                            fileUpload.status === 'completed' ? 'bg-green-500' :
                            fileUpload.status === 'processing' ? 'bg-yellow-500 animate-pulse' :
                            fileUpload.status === 'failed' ? 'bg-red-500' : 'bg-gray-300'
                          }`}></div>
                          <span className="font-medium text-sm">{fileUpload.filename}</span>
                        </div>
                        <div className="text-xs text-gray-500">
                          {(fileUpload.size / 1024 / 1024).toFixed(2)} MB
                        </div>
                      </div>
                      
                      {fileUpload.category && (
                        <div className="mt-2 text-sm">
                          <span className="text-blue-600">
                            {language === 'vi' ? 'Phân loại' : 'Category'}: {fileUpload.category}
                          </span>
                          {fileUpload.ship_name && (
                            <span className="text-green-600 ml-4">
                              {language === 'vi' ? 'Tàu' : 'Ship'}: {fileUpload.ship_name}
                            </span>
                          )}
                        </div>
                      )}
                      
                      {fileUpload.errors && fileUpload.errors.length > 0 && (
                        <div className="mt-2 text-xs text-red-600">
                          {fileUpload.errors.join(', ')}
                        </div>
                      )}
                      
                      {fileUpload.certificate_created && (
                        <div className="mt-2 text-xs text-green-600">
                          ✅ {language === 'vi' ? 'Đã tạo certificate record' : 'Certificate record created'}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            {/* OR Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">
                  {language === 'vi' ? 'HOẶC tạo thủ công' : 'OR create manually'}
                </span>
              </div>
            </div>
            
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

            {/* File Upload Section */}
            <div className="border-t border-gray-200 pt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Tập tin chứng chỉ' : 'Certificate File'}
                  <span className="text-sm text-gray-500 ml-2">
                    ({language === 'vi' ? 'Tùy chọn, tối đa 150MB' : 'Optional, max 150MB'})
                  </span>
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                  <div className="space-y-1 text-center">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                      aria-hidden="true"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="certificate-file-upload"
                        className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                      >
                        <span>{language === 'vi' ? 'Tải lên tập tin' : 'Upload a file'}</span>
                        <input
                          id="certificate-file-upload"
                          name="certificate-file-upload"
                          type="file"
                          className="sr-only"
                          onChange={(e) => setCertificateFile(e.target.files[0])}
                          accept="*/*"
                        />
                      </label>
                      <p className="pl-1">{language === 'vi' ? 'hoặc kéo và thả' : 'or drag and drop'}</p>
                    </div>
                    <p className="text-xs text-gray-500">
                      {language === 'vi' ? 'Tất cả các định dạng tập tin được hỗ trợ' : 'All file formats supported'}
                    </p>
                  </div>
                </div>
                
                {certificateFile && (
                  <div className="mt-2 flex items-center justify-between p-2 bg-blue-50 border border-blue-200 rounded-md">
                    <div className="flex items-center">
                      <svg className="h-5 w-5 text-blue-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1v-2zM3 7a1 1 0 011-1h12a1 1 0 011 1v7a1 1 0 01-1 1H4a1 1 0 01-1-1V7z" clipRule="evenodd" />
                      </svg>
                      <span className="text-sm text-blue-700 font-medium">{certificateFile.name}</span>
                      <span className="text-xs text-blue-600 ml-2">
                        ({(certificateFile.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setCertificateFile(null)}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      {language === 'vi' ? 'Xóa' : 'Remove'}
                    </button>
                  </div>
                )}
                
                {certificateFile && (
                  <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-md">
                    <div className="flex items-center">
                      <svg className="h-5 w-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span className="text-sm text-green-700">
                        {language === 'vi' 
                          ? 'Tập tin sẽ được tải lên thư mục "DATA INPUT" trong Google Drive của công ty, được sắp xếp theo ngày.' 
                          : 'File will be uploaded to company Google Drive "DATA INPUT" folder, organized by date.'}
                      </span>
                    </div>
                  </div>
                )}
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
      
      {/* PDF Analysis Modal */}
      {showPdfAnalysis && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <h3 className="text-xl font-bold text-gray-800">
                {language === 'vi' ? 'Phân tích Giấy chứng nhận' : 'Certificate Analysis'}
              </h3>
              <button
                onClick={() => {
                  setShowPdfAnalysis(false);
                  setPdfFile(null);
                }}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
              >
                ×
              </button>
            </div>
            
            <div className="p-6">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'vi' ? 'Chọn file PDF (tối đa 5MB)' : 'Select PDF file (max 5MB)'}
                </label>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => {
                    const file = e.target.files[0];
                    if (file && file.size > 5 * 1024 * 1024) {
                      toast.error(language === 'vi' ? 'File quá lớn! Tối đa 5MB' : 'File too large! Max 5MB');
                      return;
                    }
                    setPdfFile(file);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              {pdfFile && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-800">
                    📄 {pdfFile.name} ({(pdfFile.size / 1024 / 1024).toFixed(2)}MB)
                  </p>
                </div>
              )}
              
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowPdfAnalysis(false);
                    setPdfFile(null);
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all"
                  disabled={pdfAnalyzing}
                >
                  {language === 'vi' ? 'Hủy' : 'Cancel'}
                </button>
                <button
                  onClick={handlePdfAnalysis}
                  disabled={pdfAnalyzing || !pdfFile}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-all flex items-center justify-center"
                >
                  {pdfAnalyzing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      {language === 'vi' ? 'Đang phân tích...' : 'Analyzing...'}
                    </>
                  ) : (
                    language === 'vi' ? 'Phân tích PDF' : 'Analyze PDF'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Additional components for Ships Page and Ship Detail Page would go here
const ShipsPage = () => <div>Ships Page - To be implemented</div>;
const ShipDetailPage = () => <div>Ship Detail Page - To be implemented</div>;

export default App;