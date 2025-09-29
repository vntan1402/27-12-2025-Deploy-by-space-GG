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
    inspectionRecords: "Class Survey Report", 
    surveyReports: "Test Report",
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
    inspectionRecords: "Hồ sơ Đăng kiểm",
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
  const { user, token, logout, language, toggleLanguage } = useAuth();
  const [ships, setShips] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('documents');
  const [hoveredCategory, setHoveredCategory] = useState(null);
  const [selectedShip, setSelectedShip] = useState(null);
  const [selectedSubMenu, setSelectedSubMenu] = useState('certificates');
  const [certificates, setCertificates] = useState([]);
  const [certificateLinksCache, setCertificateLinksCache] = useState({}); // Per-ship cache: {shipId: {certId: {link, url}}}
  const [linksFetching, setLinksFetching] = useState(false); // Loading state for links
  const [companyLogo, setCompanyLogo] = useState(null);
  const [hoverTimeout, setHoverTimeout] = useState(null);
  const [showAddRecord, setShowAddRecord] = useState(false);
  const [addRecordDefaultTab, setAddRecordDefaultTab] = useState(null);
  const [availableCompanies, setAvailableCompanies] = useState([]);
  const [showFullShipInfo, setShowFullShipInfo] = useState(false);
  const [showShipListModal, setShowShipListModal] = useState(false);
  const [showEditShipModal, setShowEditShipModal] = useState(false);
  const [editingShipData, setEditingShipData] = useState(null);
  const [showDeleteShipModal, setShowDeleteShipModal] = useState(false);
  const [deleteShipData, setDeleteShipData] = useState(null);
  const [deleteShipOption, setDeleteShipOption] = useState('database_only'); // 'database_only' or 'with_gdrive'
  const [isDeletingShip, setIsDeletingShip] = useState(false);
  const [isUpdatingSurveyTypes, setIsUpdatingSurveyTypes] = useState(false);
  const [pendingManualReviews, setPendingManualReviews] = useState([]); // Files requiring manual review
  const [showFileViewer, setShowFileViewer] = useState(false);
  const [fileViewerData, setFileViewerData] = useState(null);
  const [aiConfig, setAiConfig] = useState({ provider: 'Unknown', model: 'Unknown' });
  
  // Certificate List filters and sorting
  const [certificateFilters, setCertificateFilters] = useState({
    certificateType: 'all',
    status: 'all',
    search: '' // Add search field
  });
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Certificate table sorting state
  const [certificateSort, setCertificateSort] = useState({
    column: null,
    direction: 'asc' // 'asc' or 'desc'
  });
  
  // Certificate table sorting functions
  const handleCertificateSort = (column) => {
    setCertificateSort(prev => ({
      column: column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const getSortIcon = (column) => {
    if (certificateSort.column !== column) {
      return null; // No icon when not sorted
    }
    return (
      <span className="ml-1 text-blue-600 text-sm font-bold">
        {certificateSort.direction === 'asc' ? '▲' : '▼'}
      </span>
    );
  };

  const getCertificateStatus = (certificate) => {
    // Rule 4: Certificates without Valid Date always have Valid status
    if (!certificate.valid_date) {
      return 'Valid';
    }
    
    const validDate = new Date(certificate.valid_date);
    const currentDate = new Date();
    currentDate.setHours(0, 0, 0, 0); // Reset time for date-only comparison
    
    return validDate >= currentDate ? 'Valid' : 'Expired';
  };

  // Certificate selection functions
  const handleSelectCertificate = (certificateId) => {
    const newSelected = new Set(selectedCertificates);
    if (newSelected.has(certificateId)) {
      newSelected.delete(certificateId);
    } else {
      newSelected.add(certificateId);
    }
    setSelectedCertificates(newSelected);
  };

  const handleSelectAllCertificates = (checked) => {
    if (checked) {
      const allVisibleIds = new Set(getFilteredCertificates().map(cert => cert.id));
      setSelectedCertificates(allVisibleIds);
    } else {
      setSelectedCertificates(new Set());
    }
  };

  const isAllSelected = () => {
    const visibleCerts = getFilteredCertificates();
    return visibleCerts.length > 0 && visibleCerts.every(cert => selectedCertificates.has(cert.id));
  };

  const isIndeterminate = () => {
    const visibleCerts = getFilteredCertificates();
    const selectedVisible = visibleCerts.filter(cert => selectedCertificates.has(cert.id));
    return selectedVisible.length > 0 && selectedVisible.length < visibleCerts.length;
  };

  // Column resize functionality
  useEffect(() => {
    let activeColumn = null;
    let startX = 0;
    let startWidth = 0;
    
    const handleMouseMove = (e) => {
      if (!activeColumn) return;
      
      const newWidth = startWidth + (e.clientX - startX);
      
      if (newWidth > 50) { // Minimum width
        activeColumn.style.width = newWidth + 'px';
      }
    };
    
    const handleMouseUp = () => {
      if (activeColumn) {
        activeColumn.removeAttribute('data-resizing');
        activeColumn = null;
      }
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
    
    const initResizeHandlers = () => {
      document.querySelectorAll('.resize-handle').forEach(th => {
        // Remove existing listeners
        th.removeEventListener('mousedown', th._resizeHandler);
        
        th._resizeHandler = (e) => {
          const rect = th.getBoundingClientRect();
          const isNearRightEdge = e.clientX > rect.right - 8;
          
          if (isNearRightEdge) {
            e.preventDefault();
            e.stopPropagation();
            
            activeColumn = th;
            startX = e.clientX;
            startWidth = parseInt(window.getComputedStyle(th).width, 10);
            
            th.setAttribute('data-resizing', 'true');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
          }
        };
        
        th.addEventListener('mousedown', th._resizeHandler);
      });
    };
    
    // Initialize after DOM is ready
    const timer = setTimeout(initResizeHandlers, 200);
    
    return () => {
      clearTimeout(timer);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [certificates]); // Re-initialize when certificates change

  const sortCertificates = (certificates) => {
    if (!certificateSort.column) return certificates;
    
    return [...certificates].sort((a, b) => {
      let aValue, bValue;
      
      switch (certificateSort.column) {
        case 'cert_abbreviation':
          aValue = (a.cert_abbreviation || '').toLowerCase();
          bValue = (b.cert_abbreviation || '').toLowerCase();
          break;
        case 'cert_type':
          aValue = (a.cert_type || '').toLowerCase();
          bValue = (b.cert_type || '').toLowerCase();
          break;
        case 'cert_no':
          aValue = (a.cert_no || '').toLowerCase();
          bValue = (b.cert_no || '').toLowerCase();
          break;
        case 'issued_by':
          aValue = (a.issued_by || '').toLowerCase();
          bValue = (b.issued_by || '').toLowerCase();
          break;
        case 'issue_date':
          aValue = a.issue_date ? new Date(a.issue_date) : new Date(0);
          bValue = b.issue_date ? new Date(b.issue_date) : new Date(0);
          break;
        case 'valid_date':
          aValue = a.valid_date ? new Date(a.valid_date) : new Date(0);
          bValue = b.valid_date ? new Date(b.valid_date) : new Date(0);
          break;
        case 'status':
          aValue = getCertificateStatus(a);
          bValue = getCertificateStatus(b);
          break;
        case 'last_endorse':
          aValue = a.last_endorse ? new Date(a.last_endorse) : new Date(0);
          bValue = b.last_endorse ? new Date(b.last_endorse) : new Date(0);
          break;
        case 'next_survey':
          aValue = a.next_survey ? new Date(a.next_survey) : new Date(0);
          bValue = b.next_survey ? new Date(b.next_survey) : new Date(0);
          break;
        case 'next_survey_type':
          aValue = (a.next_survey_type || '').toLowerCase();
          bValue = (b.next_survey_type || '').toLowerCase();
          break;
        case 'notes':
          aValue = (a.notes || '').toLowerCase();
          bValue = (b.notes || '').toLowerCase();
          break;
        default:
          return 0;
      }
      
      if (aValue < bValue) return certificateSort.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return certificateSort.direction === 'asc' ? 1 : -1;
      return 0;
    });
  };

  // Context Menu for Certificate List
  const [contextMenu, setContextMenu] = useState({
    show: false,
    x: 0,
    y: 0,
    certificate: null
  });
  const [selectedCertificates, setSelectedCertificates] = useState(new Set());
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [showEditCertModal, setShowEditCertModal] = useState(false);
  const [editingCertificate, setEditingCertificate] = useState(null);
  
  // Multi Cert Upload States
  const [multiCertUploads, setMultiCertUploads] = useState([]);
  const [isMultiCertProcessing, setIsMultiCertProcessing] = useState(false);
  const [uploadSummary, setUploadSummary] = useState(null);
  const [duplicateModal, setDuplicateModal] = useState({
    show: false,
    currentFile: '',
    duplicates: [],
    fileIndex: -1,
    resolution: null
  });
  
  // Duplicate resolution modal for multi-cert upload
  const [duplicateResolutionModal, setDuplicateResolutionModal] = useState({
    show: false,
    fileData: null,
    analysisResult: null,
    duplicateInfo: null,
    shipId: null,
    fileIndex: -1,
    fileName: ''
  });
  const navigate = useNavigate();
  
  const t = translations[language];

  useEffect(() => {
    fetchShips();
    fetchSettings();
    fetchAvailableCompanies();
    fetchAiConfig(); // Fetch AI config when component mounts
  }, []);

  useEffect(() => {
    if (selectedShip && selectedSubMenu === 'certificates') {
      fetchCertificates(selectedShip.id);
    }
  }, [selectedShip, selectedSubMenu]);

  const fetchAiConfig = async () => {
    try {
      const response = await axios.get(`${API}/ai-config`);
      setAiConfig(response.data);
    } catch (error) {
      console.error('Failed to fetch AI config:', error);
      // Set default if can't fetch
      setAiConfig({ provider: 'Unknown', model: 'Unknown', api_key: '' });
    }
  };

  const fetchShips = async () => {
    if (!token) {
      console.log('No token available, skipping ships fetch');
      return;
    }
    
    try {
      const response = await axios.get(`${API}/ships`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setShips(response.data);
      console.log('Ships fetched successfully:', response.data.length, 'ships');
    } catch (error) {
      console.error('Failed to fetch ships:', error);
      if (error.response?.status === 401) {
        console.log('Unauthorized - token may be invalid');
      }
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
    console.log('getUserCompanyShips called');
    console.log('User:', user);
    console.log('User company:', user?.company);
    console.log('Ships:', ships);
    console.log('Ships length:', ships.length);
    
    if (!user?.company) {
      console.log('No user company found, returning all ships');
      return ships;
    }
    
    const filtered = ships.filter(ship => {
      console.log(`Comparing ship "${ship.name}" company "${ship.company}" with user company "${user.company}"`);
      return ship.company === user.company;
    });
    
    console.log('Filtered ships:', filtered);
    console.log('Filtered ships length:', filtered.length);
    
    return filtered;
  };

  const handleEditShip = async (updatedShipData) => {
    try {
      // Prepare ship payload similar to create ship
      const shipPayload = {
        name: updatedShipData.name?.trim() || '',
        imo: updatedShipData.imo?.trim() || null,
        flag: updatedShipData.flag?.trim() || '',
        ship_type: updatedShipData.ship_type?.trim() || '',
        class_society: updatedShipData.class_society?.trim() || '',
        gross_tonnage: updatedShipData.gross_tonnage ? parseFloat(updatedShipData.gross_tonnage) : null,
        deadweight: updatedShipData.deadweight ? parseFloat(updatedShipData.deadweight) : null,
        year_built: updatedShipData.year_built ? parseInt(updatedShipData.year_built) : null,
        delivery_date: updatedShipData.delivery_date || null,
        keel_laid: updatedShipData.keel_laid || null,
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

  const handleDeleteShip = async (shipId, deleteOption) => {
    try {
      setIsDeletingShip(true);
      
      // Show initial loading message
      toast.info(language === 'vi' 
        ? `Đang xóa tàu ${deleteShipData?.name}...`
        : `Deleting ship ${deleteShipData?.name}...`
      );

      // Delete ship from database
      const deleteResponse = await fetch(`${API}/ships/${shipId}`, {
        method: 'DELETE',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!deleteResponse.ok) {
        const errorData = await deleteResponse.json();
        throw new Error(errorData.detail || 'Failed to delete ship from database');
      }

      // If user chose to delete Google Drive folder as well
      if (deleteOption === 'with_gdrive') {
        try {
          // Get user's company ID for Google Drive operations
          const userCompanyId = user?.company_id || user?.company;
          
          if (userCompanyId && deleteShipData?.name) {
            toast.info(language === 'vi' 
              ? 'Đang xóa folder Google Drive...'
              : 'Deleting Google Drive folder...'
            );

            const gdriveDeleteResponse = await fetch(`${API}/companies/${userCompanyId}/gdrive/delete-ship-folder`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                ship_name: deleteShipData.name
              })
            });

            if (!gdriveDeleteResponse.ok) {
              console.warn('Failed to delete Google Drive folder, but ship data was deleted from database');
              toast.warning(language === 'vi' 
                ? 'Đã xóa dữ liệu tàu nhưng không thể xóa folder Google Drive'
                : 'Ship data deleted but failed to delete Google Drive folder'
              );
            } else {
              toast.success(language === 'vi' 
                ? 'Đã xóa folder Google Drive thành công'
                : 'Google Drive folder deleted successfully'
              );
            }
          }
        } catch (gdriveError) {
          console.error('Google Drive deletion error:', gdriveError);
          toast.warning(language === 'vi' 
            ? 'Đã xóa dữ liệu tàu nhưng có lỗi khi xóa folder Google Drive'
            : 'Ship data deleted but Google Drive folder deletion failed'
          );
        }
      }

      // Success message
      toast.success(language === 'vi' 
        ? `Đã xóa tàu "${deleteShipData?.name}" thành công`
        : `Ship "${deleteShipData?.name}" deleted successfully`
      );

      // Refresh ships list
      await fetchShips();

      // Close modals and reset states
      setShowDeleteShipModal(false);
      setShowEditShipModal(false);
      setDeleteShipData(null);
      setEditingShipData(null);
      setDeleteShipOption('database_only');
      
      // Navigate back to ship list if current ship was deleted
      if (selectedShip && selectedShip.id === shipId) {
        setSelectedShip(null);
        setCertificates([]);
      }

    } catch (error) {
      console.error('Ship deletion error:', error);
      
      let errorMessage = 'Unknown error occurred';
      if (error.response?.data) {
        const errorData = error.response.data;
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map(err => err.msg || err).join(', ');
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(language === 'vi' 
        ? `Không thể xóa tàu: ${errorMessage}`
        : `Failed to delete ship: ${errorMessage}`
      );
    } finally {
      setIsDeletingShip(false);
    }
  };

  // Handle updating Next Survey and Next Survey Type for all certificates of current ship
  const handleUpdateSurveyTypes = async () => {
    if (!selectedShip) {
      toast.warning(language === 'vi' ? 'Vui lòng chọn tàu trước' : 'Please select a ship first');
      return;
    }
    
    try {
      setIsUpdatingSurveyTypes(true);
      
      toast.info(language === 'vi' 
        ? 'Đang cập nhật Next Survey dựa trên quy định IMO và chu kỳ 5 năm...'
        : 'Updating Next Survey based on IMO regulations and 5-year cycle...'
      );

      // Call the new API endpoint to update next survey for the ship
      const response = await fetch(`${API}/ships/${selectedShip.id}/update-next-survey`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        
        if (result.success) {
          // Show detailed success message
          toast.success(language === 'vi' 
            ? `Đã cập nhật Next Survey cho ${result.updated_count}/${result.total_certificates} chứng chỉ của tàu ${result.ship_name}`
            : `Updated Next Survey for ${result.updated_count}/${result.total_certificates} certificates of ship ${result.ship_name}`
          );
          
          // Show detailed results if available
          if (result.results && result.results.length > 0) {
            console.log('Next Survey Update Results:', result.results);
            
            // Show first few updated certificates in console for debugging
            result.results.slice(0, 3).forEach((cert, index) => {
              console.log(`Certificate ${index + 1}: ${cert.cert_name}`);
              console.log(`  Next Survey: ${cert.old_next_survey} → ${cert.new_next_survey}`);
              console.log(`  Next Survey Type: ${cert.old_next_survey_type} → ${cert.new_next_survey_type}`);
              console.log(`  Reasoning: ${cert.reasoning}`);
            });
            
            // Show summary toast with first few changes
            const sampleChanges = result.results.slice(0, 2);
            const changesSummary = sampleChanges.map(cert => 
              `${cert.cert_name}: ${cert.new_next_survey_type}`
            ).join('; ');
            
            if (changesSummary) {
              setTimeout(() => {
                toast.info(language === 'vi' 
                  ? `Ví dụ cập nhật: ${changesSummary}`
                  : `Sample updates: ${changesSummary}`, 
                  { autoClose: 8000 }
                );
              }, 2000);
            }
          }
          
          // Refresh certificates list to show updated next survey info
          await fetchCertificates(selectedShip.id);
          
        } else {
          toast.warning(result.message || (language === 'vi' 
            ? 'Không thể cập nhật Next Survey'
            : 'Could not update Next Survey'
          ));
        }
      } else {
        const errorData = await response.json().catch(() => ({}));
        toast.error(language === 'vi' 
          ? `Lỗi khi cập nhật Next Survey: ${errorData.detail || response.statusText}`
          : `Error updating Next Survey: ${errorData.detail || response.statusText}`
        );
      }

    } catch (error) {
      console.error('Next Survey update error:', error);
      toast.error(language === 'vi' 
        ? 'Lỗi khi cập nhật Next Survey'
        : 'Error updating Next Survey'
      );
    } finally {
      setIsUpdatingSurveyTypes(false);
    }
  };

  // Handle manual review actions for files not auto-classified as marine certificates
  const handleManualReviewAction = async (action, reviewData) => {
    try {
      const actionData = {
        action: action, // "view", "skip", "confirm_marine"
        temp_file_id: reviewData.temp_file_id,
        filename: reviewData.filename,
        file_content_b64: reviewData.file_content_b64,
        ship_id: selectedShip?.id,
        analysis_result: reviewData.analysis,
        original_category: reviewData.detected_category
      };

      if (action === 'view') {
        // Show file viewer modal with complete analysis data
        setFileViewerData({
          filename: reviewData.filename,
          content_b64: reviewData.file_content_b64,
          content_type: reviewData.content_type,
          detected_category: reviewData.detected_category,
          confidence: reviewData.confidence,
          analysis: reviewData.analysis || {} // Include full analysis data
        });
        setShowFileViewer(true);
        return;
      }

      // For skip and confirm_marine actions, call backend
      const response = await fetch(`${API}/certificates/manual-review-action`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(actionData)
      });

      if (response.ok) {
        const result = await response.json();
        
        if (action === 'skip') {
          toast.info(language === 'vi' 
            ? `⏭️ Đã bỏ qua file: ${reviewData.filename}`
            : `⏭️ Skipped file: ${reviewData.filename}`
          );
          
          // Remove from pending manual reviews
          setPendingManualReviews(prev => 
            prev.filter(item => item.temp_file_id !== reviewData.temp_file_id)
          );
          
          // Update multiCertUploads status
          setMultiCertUploads(prev => prev.map(upload => 
            upload.filename === reviewData.filename
              ? {
                  ...upload,
                  status: 'skipped',
                  progress: 100,
                  stage: language === 'vi' ? 'Đã bỏ qua' : 'Skipped'
                }
              : upload
          ));
          
        } else if (action === 'confirm_marine') {
          toast.success(language === 'vi' 
            ? `✅ Đã xác nhận và thêm chứng chỉ: ${reviewData.filename}`
            : `✅ Confirmed and added certificate: ${reviewData.filename}`
          );
          
          // Remove from pending manual reviews
          setPendingManualReviews(prev => 
            prev.filter(item => item.temp_file_id !== reviewData.temp_file_id)
          );
          
          // Update multiCertUploads status
          setMultiCertUploads(prev => prev.map(upload => 
            upload.filename === reviewData.filename
              ? {
                  ...upload,
                  status: 'completed',
                  progress: 100,
                  stage: language === 'vi' ? 'Hoàn thành (Đã xác nhận)' : 'Completed (User Confirmed)',
                  certificate: { id: result.certificate_id },
                  survey_type: result.survey_type,
                  user_confirmed: true
                }
              : upload
          ));
          
          // Refresh certificates list
          await fetchCertificates(selectedShip.id);
        }
        
      } else {
        throw new Error(`Action failed: ${response.statusText}`);
      }

    } catch (error) {
      console.error('Manual review action error:', error);
      toast.error(language === 'vi' 
        ? `Lỗi khi thực hiện hành động: ${error.message}`
        : `Error performing action: ${error.message}`
      );
    }
  };

  // Load cache from sessionStorage on component mount
  useEffect(() => {
    try {
      const savedCache = sessionStorage.getItem('certificateLinksCache');
      if (savedCache) {
        setCertificateLinksCache(JSON.parse(savedCache));
        console.log('✅ Loaded certificate links cache from sessionStorage');
      }
    } catch (error) {
      console.warn('Failed to load cache from sessionStorage:', error);
    }
  }, []);

  // Save cache to sessionStorage whenever it changes
  useEffect(() => {
    try {
      if (Object.keys(certificateLinksCache).length > 0) {
        sessionStorage.setItem('certificateLinksCache', JSON.stringify(certificateLinksCache));
      }
    } catch (error) {
      console.warn('Failed to save cache to sessionStorage:', error);
    }
  }, [certificateLinksCache]);

  // Get cached links for current ship
  const getCurrentShipLinks = () => {
    return selectedShip?.id ? (certificateLinksCache[selectedShip.id] || {}) : {};
  };

  // Pre-fetch certificate links for faster multi-copy functionality
  const preFetchCertificateLinks = async (certificateList, shipId) => {
    if (!certificateList || certificateList.length === 0 || !shipId) return;
    
    // Check if we already have cached links for this ship
    const existingCache = certificateLinksCache[shipId] || {};
    const uncachedCertificates = certificateList.filter(cert => !existingCache[cert.id]);
    
    if (uncachedCertificates.length === 0) {
      console.log(`✅ All links already cached for ship ${shipId} (${certificateList.length} certificates)`);
      return;
    }
    
    console.log(`🔄 Pre-fetching ${uncachedCertificates.length}/${certificateList.length} links for ship ${shipId}`);
    setLinksFetching(true);
    const linkCache = { ...existingCache }; // Start with existing cache
    
    try {
      // Fetch links in parallel with rate limiting (5 concurrent requests)
      const batchSize = 5;
      const batches = [];
      
      for (let i = 0; i < uncachedCertificates.length; i += batchSize) {
        const batch = uncachedCertificates.slice(i, i + batchSize);
        batches.push(batch);
      }
      
      for (const batch of batches) {
        const promises = batch.map(async (cert) => {
          if (!cert.google_drive_file_id) return null;
          
          try {
            const response = await fetch(`${API}/gdrive/file/${cert.google_drive_file_id}/view`, {
              headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            
            if (data.view_url) {
              const certName = cert.cert_name || 'Certificate';
              const certAbbr = cert.cert_abbreviation || cert.cert_name?.substring(0, 4) || 'N/A';
              const formattedLink = `${certName} (${certAbbr}): ${data.view_url}`;
              
              return {
                id: cert.id,
                link: formattedLink,
                url: data.view_url
              };
            }
            return null;
          } catch (error) {
            console.warn(`Failed to pre-fetch link for certificate ${cert.id}:`, error);
            return null;
          }
        });
        
        const batchResults = await Promise.all(promises);
        batchResults.forEach(result => {
          if (result) {
            linkCache[result.id] = result;
          }
        });
        
        // Small delay between batches to avoid overwhelming the server
        if (batches.indexOf(batch) < batches.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }
      
      // Update the cache for this specific ship
      setCertificateLinksCache(prev => ({
        ...prev,
        [shipId]: linkCache
      }));
      
      const newCachedCount = Object.keys(linkCache).length - Object.keys(existingCache).length;
      console.log(`✅ Pre-fetched ${newCachedCount} new links for ship ${shipId}. Total cached: ${Object.keys(linkCache).length}/${certificateList.length}`);
      
    } catch (error) {
      console.error('Error pre-fetching certificate links:', error);
    } finally {
      setLinksFetching(false);
    }
  };

  const fetchCertificates = async (shipId) => {
    console.log('fetchCertificates called with shipId:', shipId);
    try {
      setIsRefreshing(true);
      const response = await axios.get(`${API}/ships/${shipId}/certificates`);
      console.log('Certificates fetched successfully:', response.data.length, 'certificates');
      setCertificates(response.data);
      
      // Pre-fetch certificate links for faster multi-copy functionality
      if (response.data && response.data.length > 0 && shipId) {
        // Don't await this to avoid blocking UI
        preFetchCertificateLinks(response.data, shipId).catch(error => {
          console.warn('Pre-fetch links failed:', error);
        });
      }
    } catch (error) {
      console.error('Failed to fetch certificates:', error);
      setCertificates([]);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleRefreshCertificates = async () => {
    if (selectedShip) {
      await fetchCertificates(selectedShip.id);
      toast.success(language === 'vi' ? 'Đã cập nhật danh sách chứng chỉ!' : 'Certificate list refreshed!');
    }
  };

  // Context Menu Functions
  const handleCertificateRightClick = (e, certificate) => {
    e.preventDefault();
    
    // Check if user has Company Officer role or higher
    const allowedRoles = ['company_officer', 'manager', 'admin', 'super_admin'];
    if (!allowedRoles.includes(user?.role)) {
      return; // Don't show context menu for unauthorized users
    }
    
    // If certificate is not selected, add it to current selection (don't clear others)
    if (!selectedCertificates.has(certificate.id)) {
      const newSelected = new Set(selectedCertificates);
      newSelected.add(certificate.id);
      setSelectedCertificates(newSelected);
    }
    
    // Calculate context menu position with viewport boundary checking
    const contextMenuWidth = 200; // Estimated width of context menu
    const contextMenuHeight = 180; // Estimated height of context menu
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    let x = e.clientX;
    let y = e.clientY;
    
    // Adjust X position if menu would overflow right edge
    if (x + contextMenuWidth > viewportWidth) {
      x = viewportWidth - contextMenuWidth - 10; // 10px margin from edge
    }
    
    // Adjust Y position if menu would overflow bottom edge
    if (y + contextMenuHeight > viewportHeight) {
      y = y - contextMenuHeight; // Show above cursor instead of below
      // If still overflows (near top of screen), position at bottom of viewport
      if (y < 0) {
        y = viewportHeight - contextMenuHeight - 10; // 10px margin from bottom
      }
    }
    
    // Ensure menu doesn't go off left or top edges
    if (x < 0) x = 10;
    if (y < 0) y = 10;
    
    setContextMenu({
      show: true,
      x: x,
      y: y,
      certificate: certificate
    });
  };

  const handleDownloadSelectedCertificates = async () => {
    try {
      if (selectedCertificates.size === 0) return;
      
      // Show loading toast for multiple files
      if (selectedCertificates.size > 1) {
        toast.info(language === 'vi' 
          ? `Đang tải xuống ${selectedCertificates.size} chứng chỉ...` 
          : `Downloading ${selectedCertificates.size} certificates...`);
      }
      
      // Get selected certificate data
      const selectedCertificatesData = getFilteredCertificates().filter(cert => 
        selectedCertificates.has(cert.id)
      );
      
      // Download each certificate
      for (const certificate of selectedCertificatesData) {
        try {
          await downloadSingleCertificate(certificate);
          // Small delay between downloads to avoid overwhelming the browser
          if (selectedCertificates.size > 1) {
            await new Promise(resolve => setTimeout(resolve, 500));
          }
        } catch (error) {
          console.error(`Failed to download certificate: ${certificate.certificate_name}`, error);
          toast.error(language === 'vi' 
            ? `Không thể tải: ${certificate.certificate_name}` 
            : `Failed to download: ${certificate.certificate_name}`);
        }
      }
      
      // Success message
      if (selectedCertificates.size > 1) {
        toast.success(language === 'vi' 
          ? `Đã tải xuống ${selectedCertificates.size} chứng chỉ` 
          : `Downloaded ${selectedCertificates.size} certificates`);
      }
      
    } catch (error) {
      console.error('Download error:', error);
      toast.error(language === 'vi' ? 'Lỗi khi tải xuống' : 'Download error');
    }
    setContextMenu({ show: false, x: 0, y: 0, certificate: null });
  };

  const downloadSingleCertificate = async (certificate) => {
    try {
      // Get download URL from backend
      const response = await fetch(`${API}/gdrive/file/${certificate.google_drive_file_id}/download`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) {
        throw new Error('Failed to get download URL');
      }
      
      const data = await response.json();
      
      if (data.download_url) {
        // Create temporary link and trigger download
        const link = document.createElement('a');
        link.href = data.download_url;
        
        // Generate filename: Certificate Name + Extension
        const filename = certificate.certificate_name 
          ? `${certificate.certificate_name}.pdf`
          : `Certificate_${certificate.id}.pdf`;
        
        link.download = filename;
        link.target = '_blank';
        
        // Append to document, click, and remove
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log(`Downloaded: ${filename}`);
      } else {
        throw new Error('No download URL provided');
      }
    } catch (error) {
      console.error('Single certificate download error:', error);
      throw error;
    }
  };

  const handleDownloadCertificate = async (certificate) => {
    try {
      await downloadSingleCertificate(certificate);
      toast.success(language === 'vi' 
        ? `Đã tải xuống: ${certificate.certificate_name}` 
        : `Downloaded: ${certificate.certificate_name}`);
    } catch (error) {
      toast.error(language === 'vi' ? 'Không thể tải xuống file' : 'Cannot download file');
    }
    setContextMenu({ show: false, x: 0, y: 0, certificate: null });
  };

  const handleOpenCertificate = async (certificate) => {
    try {
      const response = await fetch(`${API}/gdrive/file/${certificate.google_drive_file_id}/view`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (data.view_url) {
        window.open(data.view_url, '_blank');
      } else {
        toast.error(language === 'vi' ? 'Không thể mở file' : 'Cannot open file');
      }
    } catch (error) {
      toast.error(language === 'vi' ? 'Lỗi khi mở file' : 'Error opening file');
    }
    setContextMenu({ show: false, x: 0, y: 0, certificate: null });
  };

  const handleOpenSelectedCertificates = async () => {
    try {
      if (selectedCertificates.size === 0) return;
      
      // Warn if opening too many files
      if (selectedCertificates.size > 10) {
        const confirmed = window.confirm(
          language === 'vi' 
            ? `Bạn đang mở ${selectedCertificates.size} files. Điều này có thể làm chậm trình duyệt. Bạn có muốn tiếp tục?`
            : `You are opening ${selectedCertificates.size} files. This may slow down your browser. Do you want to continue?`
        );
        if (!confirmed) return;
      }

      const allCertificates = getFilteredCertificates();
      const certificatesToOpen = allCertificates.filter(cert => selectedCertificates.has(cert.id));
      
      // Show initial info toast
      toast.info(
        language === 'vi' 
          ? `Đang tải ${certificatesToOpen.length} files, sẽ mở từng file với độ trễ 1 giây...`
          : `Loading ${certificatesToOpen.length} files, will open each file with 1 second delay...`
      );
      
      let openedCount = 0;
      let errorCount = 0;
      
      // First, fetch all URLs in parallel for faster loading
      const urlPromises = certificatesToOpen.map(async (cert) => {
        try {
          const response = await fetch(`${API}/gdrive/file/${cert.google_drive_file_id}/view`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          const data = await response.json();
          return { cert, url: data.view_url, success: !!data.view_url };
        } catch (error) {
          console.error(`Error fetching URL for ${cert.cert_name}:`, error);
          return { cert, url: null, success: false };
        }
      });
      
      const urlResults = await Promise.all(urlPromises);
      
      // Then open tabs with delays, using direct window.open for better browser support
      urlResults.forEach((result, index) => {
        setTimeout(() => {
          if (result.success && result.url) {
            try {
              // Use direct window.open with minimal features for better compatibility
              const newTab = window.open(result.url, '_blank');
              if (newTab) {
                openedCount++;
                console.log(`✅ Opened tab ${index + 1}/${urlResults.length}: ${result.cert.cert_name}`);
              } else {
                errorCount++;
                console.warn(`❌ Failed to open tab for: ${result.cert.cert_name} (popup blocked)`);
              }
            } catch (error) {
              errorCount++;
              console.error(`❌ Error opening tab for ${result.cert.cert_name}:`, error);
            }
          } else {
            errorCount++;
            console.warn(`❌ No URL available for: ${result.cert.cert_name}`);
          }
          
          // Show final toast on last iteration
          if (index === urlResults.length - 1) {
            setTimeout(() => {
              if (openedCount > 0) {
                toast.success(
                  language === 'vi' 
                    ? `✅ Đã mở ${openedCount}/${urlResults.length} files${errorCount > 0 ? ` (${errorCount} lỗi)` : ''}`
                    : `✅ Opened ${openedCount}/${urlResults.length} files${errorCount > 0 ? ` (${errorCount} errors)` : ''}`
                );
              } else {
                toast.error(
                  language === 'vi' 
                    ? '❌ Không thể mở files (có thể bị chặn popup)' 
                    : '❌ Cannot open files (may be blocked by popup blocker)'
                );
              }
            }, 100);
          }
        }, index * 1000); // 1 second delay between each open
      });
      
      handleCloseContextMenu();
    } catch (error) {
      console.error('Error in handleOpenSelectedCertificates:', error);
      toast.error(language === 'vi' ? 'Lỗi khi mở files' : 'Error opening files');
    }
  };

  const handleCopySelectedLinks = async () => {
    try {
      if (selectedCertificates.size === 0) return;

      const allCertificates = getFilteredCertificates();
      const certificatesToCopy = allCertificates.filter(cert => selectedCertificates.has(cert.id));
      
      let copiedLinks = [];
      let errorCount = 0;
      let cachedCount = 0;
      let fetchedCount = 0;
      
      // Get current ship's cached links
      const currentShipLinks = getCurrentShipLinks();
      
      // First, try to use cached links
      for (const cert of certificatesToCopy) {
        const cachedLink = currentShipLinks[cert.id];
        if (cachedLink && cachedLink.link) {
          copiedLinks.push(cachedLink.link);
          cachedCount++;
        } else {
          // Fallback: fetch link if not cached
          try {
            const response = await fetch(`${API}/gdrive/file/${cert.google_drive_file_id}/view`, {
              headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            
            if (data.view_url) {
              // Format: "Certificate Name (Certificate Abbreviation): URL"
              const certName = cert.cert_name || 'Certificate';
              const certAbbr = cert.cert_abbreviation || cert.cert_name?.substring(0, 4) || 'N/A';
              const formattedLink = `${certName} (${certAbbr}): ${data.view_url}`;
              copiedLinks.push(formattedLink);
              fetchedCount++;
              
              // Cache this link for future use
              if (selectedShip?.id) {
                setCertificateLinksCache(prev => ({
                  ...prev,
                  [selectedShip.id]: {
                    ...getCurrentShipLinks(),
                    [cert.id]: {
                      link: formattedLink,
                      url: data.view_url
                    }
                  }
                }));
              }
            } else {
              errorCount++;
            }
          } catch (error) {
            errorCount++;
          }
        }
      }
      
      if (copiedLinks.length > 0) {
        // Copy all links to clipboard, separated by newlines
        const linksText = copiedLinks.join('\n');
        await navigator.clipboard.writeText(linksText);
        
        // Enhanced success message showing cache performance
        const performanceInfo = cachedCount > 0 ? 
          (language === 'vi' 
            ? ` (${cachedCount} từ cache, ${fetchedCount} tải mới)` 
            : ` (${cachedCount} cached, ${fetchedCount} fetched)`) : '';
        
        toast.success(
          language === 'vi' 
            ? `✅ Đã copy ${copiedLinks.length} link${errorCount > 0 ? `, ${errorCount} link lỗi` : ''}${performanceInfo}`
            : `✅ Copied ${copiedLinks.length} link${copiedLinks.length > 1 ? 's' : ''}${errorCount > 0 ? `, ${errorCount} error${errorCount > 1 ? 's' : ''}` : ''}${performanceInfo}`
        );
      } else {
        toast.error(language === 'vi' ? 'Không thể lấy links' : 'Cannot get links');
      }
      
      handleCloseContextMenu();
    } catch (error) {
      console.error('Error in handleCopySelectedLinks:', error);
      toast.error(language === 'vi' ? 'Lỗi khi copy links' : 'Error copying links');
    }
  };

  const handleCopyLink = async (certificate) => {
    try {
      const response = await fetch(`${API}/gdrive/file/${certificate.google_drive_file_id}/view`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      
      if (data.view_url) {
        await navigator.clipboard.writeText(data.view_url);
        toast.success(language === 'vi' ? 'Đã copy link' : 'Link copied');
      } else {
        toast.error(language === 'vi' ? 'Không thể lấy link' : 'Cannot get link');
      }
    } catch (error) {
      toast.error(language === 'vi' ? 'Lỗi khi copy link' : 'Error copying link');
    }
    setContextMenu({ show: false, x: 0, y: 0, certificate: null });
  };

  const handleDeleteCertificateFromContext = () => {
    setShowDeleteConfirmation(true);
    setContextMenu({ show: false, x: 0, y: 0, certificate: null });
  };

  const handleCloseContextMenu = () => {
    setContextMenu({ show: false, x: 0, y: 0, certificate: null });
  };

  const handleEditCertificate = () => {
    setEditingCertificate(contextMenu.certificate);
    setShowEditCertModal(true);
    handleCloseContextMenu();
  };

  const handleDeleteCertificate = async () => {
    if (!contextMenu.certificate) return;
    
    const confirmMessage = language === 'vi' 
      ? `Bạn có chắc chắn muốn xóa chứng chỉ "${contextMenu.certificate.cert_name}"?`
      : `Are you sure you want to delete certificate "${contextMenu.certificate.cert_name}"?`;
    
    if (window.confirm(confirmMessage)) {
      try {
        await axios.delete(`${API}/certificates/${contextMenu.certificate.id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        toast.success(language === 'vi' ? 'Đã xóa chứng chỉ!' : 'Certificate deleted!');
        await fetchCertificates(selectedShip.id); // Refresh list
      } catch (error) {
        console.error('Error deleting certificate:', error);
        toast.error(language === 'vi' ? 'Lỗi khi xóa chứng chỉ!' : 'Error deleting certificate!');
      }
    }
    
    setContextMenu({ show: false, x: 0, y: 0, certificate: null });
  };

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      if (contextMenu.show) {
        handleCloseContextMenu();
      }
    };
    
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [contextMenu.show]);

  // Handle duplicate resolution
  const handleDuplicateResolution = async (action, resetAnalyzingState) => {
    const { fileData, analysisResult, duplicateInfo, shipId, fileIndex, fileName } = duplicateResolutionModal;
    
    try {
      // Call resolve duplicate API
      const response = await fetch(`${API}/certificates/resolve-duplicate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action: action, // "skip" or "continue"
          file_data: fileData,
          analysis_result: analysisResult,
          ship_id: shipId,
          duplicate_info: duplicateInfo
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        
        if (action === 'skip') {
          // Update upload status to skipped
          setMultiCertUploads(prev => prev.map((upload, idx) => 
            idx === fileIndex 
              ? {
                  ...upload,
                  status: 'skipped',
                  progress: 100,
                  stage: language === 'vi' ? 'Đã bỏ qua' : 'Skipped'
                }
              : upload
          ));
          
          toast.info(language === 'vi' 
            ? `⏩ Đã bỏ qua: ${fileName} (trùng lặp)`
            : `⏩ Skipped: ${fileName} (duplicate)`
          );
          
        } else if (action === 'continue') {
          // Update upload status to completed
          setMultiCertUploads(prev => prev.map((upload, idx) => 
            idx === fileIndex 
              ? {
                  ...upload,
                  status: 'completed',
                  progress: 100,
                  stage: language === 'vi' ? 'Hoàn thành' : 'Completed',
                  certificate: result.certificate
                }
              : upload
          ));
          
          toast.success(language === 'vi' 
            ? `✅ Đã tạo: ${fileName} (bất chấp trùng lặp)`
            : `✅ Created: ${fileName} (despite duplicate)`
          );
        }
        
        // Close modal
        setDuplicateResolutionModal({
          show: false,
          fileData: null,
          analysisResult: null,
          duplicateInfo: null,
          shipId: null,
          fileIndex: -1,
          fileName: ''
        });
        
        // Refresh certificates list
        if (selectedShip) {
          await fetchCertificates(selectedShip.id);
        }
        
        // Reset certificate analyzing state to unlock the Add Certificate button
        if (typeof resetAnalyzingState === 'function') {
          resetAnalyzingState(false);
        }
        
      } else {
        const errorData = await response.json().catch(() => ({}));
        toast.error(language === 'vi' 
          ? `Lỗi xử lý trùng lặp: ${errorData.detail || response.statusText}`
          : `Error resolving duplicate: ${errorData.detail || response.statusText}`
        );
        
        // Reset certificate analyzing state on error
        if (typeof resetAnalyzingState === 'function') {
          resetAnalyzingState(false);
        }
      }
      
    } catch (error) {
      console.error('Duplicate resolution error:', error);
      toast.error(language === 'vi' 
        ? 'Lỗi khi xử lý trùng lặp'
        : 'Error resolving duplicate'
      );
      
      // Reset certificate analyzing state on error
      if (typeof resetAnalyzingState === 'function') {
        resetAnalyzingState(false);
      }
    }
  };

  // Update resolution for a specific file
  const updateFileResolution = (filename, resolution) => {
    setDuplicateResolutionModal(prev => ({
      ...prev,
      files: prev.files.map(file => 
        file.filename === filename 
          ? { ...file, resolution }
          : file
      )
    }));
  };

  // Process duplicate resolutions
  const processDuplicateResolutions = async () => {
    try {
      const { files, shipId } = duplicateResolutionModal;
      let processedCount = 0;
      let cancelledCount = 0;
      
      for (const file of files) {
        if (file.resolution === 'cancel') {
          cancelledCount++;
          continue;
        }
        
        const resolutionData = {
          analysis_result: file.analysis,
          ship_id: shipId,
          duplicate_resolution: file.resolution,
          duplicate_target_id: file.duplicate_certificate?.id
        };
        
        const response = await axios.post(`${API}/certificates/process-with-resolution`, resolutionData, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.data.status === 'success') {
          processedCount++;
        }
      }
      
      // Close modal
      setDuplicateResolutionModal({
        show: false,
        files: [],
        shipId: null
      });
      
      // Show results
      if (processedCount > 0) {
        toast.success(
          language === 'vi' 
            ? `✅ Đã xử lý thành công ${processedCount} certificates`
            : `✅ Successfully processed ${processedCount} certificates`
        );
        
        // Refresh certificate list
        if (selectedShip) {
          await fetchCertificates(selectedShip.id);
        }
      }
      
      if (cancelledCount > 0) {
        toast.info(
          language === 'vi'
            ? `ℹ️ Đã hủy ${cancelledCount} certificates`
            : `ℹ️ Cancelled ${cancelledCount} certificates`
        );
      }
      
    } catch (error) {
      console.error('Error processing duplicate resolutions:', error);
      toast.error(
        language === 'vi'
          ? `❌ Lỗi xử lý: ${error.response?.data?.detail || error.message}`
          : `❌ Processing error: ${error.response?.data?.detail || error.message}`
      );
    }
  };

  const handleMismatchResolution = (action) => {
    toast.info(language === 'vi' ? 'Chức năng đang được xây dựng lại' : 'Feature is being rebuilt');
  };

  // Multi Cert Upload Functions
  const handleMultiCertUpload = async (files, autoFillCallback = null) => {
    if (!files || files.length === 0) return;
    
    if (!selectedShip) {
      toast.error(language === 'vi' 
        ? 'Vui lòng chọn tàu trước khi upload certificates'
        : 'Please select a ship before uploading certificates'
      );
      return;
    }
    
    // Initialize upload states
    setIsMultiCertProcessing(true);
    setUploadSummary(null);
    
    const fileArray = Array.from(files);
    const initialUploads = fileArray.map((file, index) => ({
      index,
      filename: file.name,
      name: file.name, // Add name field for display
      size: file.size,
      status: 'pending', // pending, uploading, analyzing, processing, completed, error
      progress: 0,
      stage: language === 'vi' ? 'Đang chờ xử lý...' : 'Waiting to process...', // Add stage field
      analysis: null,
      upload: null,
      certificate: null,
      error: null,
      isMarine: null
    }));
    
    setMultiCertUploads(initialUploads);
    
    try {
      let successCount = 0;
      let errorCount = 0;
      let totalFiles = fileArray.length;
      
      // Show initial info about batch processing with delay
      toast.info(language === 'vi' 
        ? `Bắt đầu upload ${totalFiles} files với delay 0.5s giữa các file...`
        : `Starting upload of ${totalFiles} files with 0.5s delay between files...`
      );
      
      // Start all uploads concurrently with 0.5s delay between each
      const uploadPromises = [];
      
      for (let i = 0; i < fileArray.length; i++) {
        const file = fileArray[i];
        
        // Create promise for each file upload with delay
        const uploadPromise = new Promise(async (resolve) => {
          try {
            // Wait for staggered start (0.5s * index)
            await new Promise(delayResolve => setTimeout(delayResolve, i * 500));
            
            // Update status to uploading for current file
            setMultiCertUploads(prev => prev.map((upload, idx) => 
              idx === i 
                ? {
                    ...upload,
                    status: 'uploading',
                    stage: language === 'vi' 
                      ? `Đang upload ${file.name}... (${i + 1}/${totalFiles})`
                      : `Uploading ${file.name}... (${i + 1}/${totalFiles})`
                  }
                : upload
            ));
            
            // Create FormData for single file
            const formData = new FormData();
            formData.append('files', file);
            
            // Upload single file
            const response = await axios.post(`${API}/certificates/multi-upload?ship_id=${selectedShip.id}`, formData, {
              headers: {
                'Content-Type': 'multipart/form-data',
                'Authorization': `Bearer ${token}`
              },
              onUploadProgress: (progressEvent) => {
                const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                setMultiCertUploads(prev => prev.map((upload, idx) => 
                  idx === i 
                    ? {
                        ...upload,
                        progress: progress,
                        stage: language === 'vi' 
                          ? `Đang upload ${file.name}... ${progress}% (${i + 1}/${totalFiles})`
                          : `Uploading ${file.name}... ${progress}% (${i + 1}/${totalFiles})`
                      }
                    : upload
                ));
              }
            });
            
            // Process the response for this file
            const results = response.data.results || [];
            const result = results[0]; // Should be only one result
            
            if (result && (result.status === 'completed' || result.status === 'success' || result.status === 'duplicate')) {
              setMultiCertUploads(prev => prev.map((upload, idx) => 
                idx === i 
                  ? {
                      ...upload,
                      status: 'completed',
                      progress: 100,
                      stage: language === 'vi' ? 'Hoàn thành' : 'Completed',
                      analysis: result.analysis,
                      upload: result.upload,
                      certificate: result.certificate,
                      isMarine: result.is_marine
                    }
                  : upload
              ));
              
              // Show individual success message for each file with status context
              const statusMessage = result.status === 'duplicate' 
                ? (language === 'vi' ? ' (Đã tồn tại)' : ' (Already exists)')
                : '';
              
              toast.success(language === 'vi' 
                ? `✅ Upload thành công: ${file.name}${statusMessage} (${i + 1}/${totalFiles})`
                : `✅ Upload successful: ${file.name}${statusMessage} (${i + 1}/${totalFiles})`
              );
              
              resolve({ status: 'success', file: file.name });
              
            } else if (result && result.status === 'pending_duplicate_resolution') {
              // File requires duplicate resolution - pause and show dialog
              setMultiCertUploads(prev => prev.map((upload, idx) => 
                idx === i 
                  ? {
                      ...upload,
                      status: 'pending_duplicate',
                      progress: 90,
                      stage: language === 'vi' ? 'Chờ quyết định trùng lặp' : 'Awaiting duplicate resolution',
                      duplicateInfo: result.duplicate_info
                    }
                  : upload
              ));
              
              // Show duplicate resolution modal
              setDuplicateResolutionModal({
                show: true,
                fileData: file,
                analysisResult: result.analysis,
                duplicateInfo: result.duplicate_info,
                shipId: selectedShip?.id,
                fileIndex: i,
                fileName: file.name
              });
              
              // Pause the upload process - don't resolve the promise yet
              return; // Don't resolve, wait for user decision
              
            } else if (result && result.status === 'requires_manual_review') {
              // File requires manual review - add to pending reviews
              const reviewData = {
                temp_file_id: result.temp_file_id,
                filename: result.filename,
                file_content_b64: result.file_content_b64,
                content_type: result.content_type,
                detected_category: result.detected_category,
                confidence: result.confidence,
                analysis: result.analysis,
                file_size: result.file_size,
                manual_override_options: result.manual_override_options,
                upload_index: i
              };
              
              setPendingManualReviews(prev => [...prev, reviewData]);
              
              setMultiCertUploads(prev => prev.map((upload, idx) => 
                idx === i 
                  ? {
                      ...upload,
                      status: 'requires_manual_review',
                      progress: 100,
                      stage: language === 'vi' ? 'Cần xem xét thủ công' : 'Requires Manual Review',
                      analysis: result.analysis,
                      detected_category: result.detected_category,
                      confidence: result.confidence,
                      requires_user_action: true,
                      manual_override_options: result.manual_override_options
                    }
                  : upload
              ));
              
              // Show manual review notification
              toast.warning(language === 'vi' 
                ? `⚠️ Cần xem xét: ${file.name} - Hệ thống phân loại: ${result.detected_category}`
                : `⚠️ Manual review needed: ${file.name} - System classified as: ${result.detected_category}`
              );
              
              resolve({ status: 'manual_review', file: file.name });
              
            } else {
              const errorMsg = result?.error || result?.message || 'Unknown error';
              setMultiCertUploads(prev => prev.map((upload, idx) => 
                idx === i 
                  ? {
                      ...upload,
                      status: 'error',
                      progress: 100,
                      stage: language === 'vi' ? 'Lỗi xử lý' : 'Processing error',
                      error: errorMsg
                    }
                  : upload
              ));
              
              // Show individual error message
              toast.error(language === 'vi' 
                ? `❌ Lỗi upload: ${file.name} - ${errorMsg}`
                : `❌ Upload error: ${file.name} - ${errorMsg}`
              );
              
              resolve({ status: 'error', file: file.name, error: errorMsg });
            }
            
          } catch (fileError) {
            console.error(`Error uploading file ${file.name}:`, fileError);
            
            setMultiCertUploads(prev => prev.map((upload, idx) => 
              idx === i 
                ? {
                    ...upload,
                    status: 'error',
                    progress: 100,
                    stage: language === 'vi' ? 'Lỗi upload' : 'Upload error',
                    error: fileError.response?.data?.detail || fileError.message
                  }
                : upload
            ));
            
            toast.error(language === 'vi' 
              ? `❌ Lỗi upload: ${file.name}`
              : `❌ Upload error: ${file.name}`
            );
            
            resolve({ status: 'error', file: file.name, error: fileError.message });
          }
        });
        
        uploadPromises.push(uploadPromise);
      }
      
      // Wait for all uploads to complete
      const results = await Promise.all(uploadPromises);
      
      // Count results
      successCount = results.filter(r => r.status === 'success').length;
      errorCount = results.filter(r => r.status === 'error').length;
      const manualReviewCount = results.filter(r => r.status === 'manual_review').length;
      
      // Show final summary
      const finalSummary = {
        total_files: totalFiles,
        successful_uploads: successCount,
        failed_uploads: errorCount,
        manual_review_count: manualReviewCount,
        processing_time: `${totalFiles} files uploaded concurrently with 0.5s staggered start`
      };
      
      setUploadSummary(finalSummary);
      
      // Final success/error toast
      if (successCount > 0 && errorCount === 0 && manualReviewCount === 0) {
        toast.success(language === 'vi' 
          ? `🎉 Tất cả ${successCount} files đã được upload thành công!`
          : `🎉 All ${successCount} files uploaded successfully!`
        );
      } else if (successCount > 0 && (errorCount > 0 || manualReviewCount > 0)) {
        const reviewText = manualReviewCount > 0 ? 
          (language === 'vi' ? `, ${manualReviewCount} cần xem xét` : `, ${manualReviewCount} need review`) : '';
        toast.warning(language === 'vi' 
          ? `⚠️ Upload hoàn thành: ${successCount} thành công, ${errorCount} lỗi${reviewText}`
          : `⚠️ Upload completed: ${successCount} successful, ${errorCount} errors${reviewText}`
        );
      } else {
        toast.error(language === 'vi' 
          ? `❌ Upload thất bại: ${errorCount} files lỗi`
          : `❌ Upload failed: ${errorCount} files with errors`
        );
      }
      
      // Refresh certificates if any were successfully uploaded
      if (successCount > 0) {
        await fetchCertificates(selectedShip.id);
      }
      
    } catch (error) {
      console.error('Multi cert upload error:', error);
      toast.error(
        language === 'vi'
          ? `❌ Lỗi xử lý: ${error.response?.data?.detail || error.message}`
          : `❌ Processing error: ${error.response?.data?.detail || error.message}`
      );
      
      // Update all pending/uploading files to error status
      setMultiCertUploads(prev => prev.map(upload => 
        upload.status === 'pending' || upload.status === 'uploading'
          ? {
              ...upload,
              status: 'error',
              progress: 100,
              stage: language === 'vi' ? 'Lỗi xử lý batch' : 'Batch processing error',
              error: error.response?.data?.detail || error.message
            }
          : upload
      ));
    } finally {
      setIsMultiCertProcessing(false);
    }
  };

  // Handle upload file to specific folder (for non-certificate files)
  const handleUploadToFolder = async (filename, folderCategory) => {
    if (!selectedShip?.id) {
      toast.error('No ship selected');
      return;
    }
    
    try {
      // Find the original file from multiCertUploads
      const fileUpload = multiCertUploads.find(upload => upload.filename === filename);
      if (!fileUpload) {
        toast.error('File not found');
        return;
      }
      
      // Find the original file from the files array (we need to store this)
      toast.info(
        language === 'vi' 
          ? `Đang upload ${filename} vào folder ${folderCategory}...`
          : `Uploading ${filename} to ${folderCategory} folder...`
      );
      
      // For now, just mark as completed since we don't have the original file reference
      // This would need to be implemented with proper file storage
      setMultiCertUploads(prev => prev.map(upload => 
        upload.filename === filename 
          ? { ...upload, status: 'completed', message: `Uploaded to ${folderCategory}` }
          : upload
      ));
      
      toast.success(
        language === 'vi'
          ? `✅ Đã upload ${filename} vào folder ${folderCategory}`
          : `✅ Successfully uploaded ${filename} to ${folderCategory} folder`
      );
    } catch (error) {
      console.error('Upload to folder error:', error);
      toast.error('Upload failed');
    }
  };
  
  // Handle skip file (for non-certificate files)
  const handleSkipFile = (filename) => {
    setMultiCertUploads(prev => prev.map(upload => 
      upload.filename === filename 
        ? { ...upload, status: 'skipped', message: 'Skipped by user' }
        : upload
    ));
    
    toast.info(
      language === 'vi'
        ? `File ${filename} đã được bỏ qua`
        : `File ${filename} has been skipped`
    );
  };

  const getFilteredCertificates = () => {
    // First filter by category/submenu
    const categoryMap = {
      'certificates': 'certificates',
      'inspection_records': 'inspection_records',
      'survey_reports': 'survey_reports', 
      'test_reports': 'test_reports',
      'drawings_manuals': 'drawings_manuals',
      'other_documents': 'other_documents'
    };
    
    const targetCategory = categoryMap[selectedSubMenu] || 'certificates';
    
    const categoryFiltered = certificates.filter(cert => {
      const certCategory = cert.category || 'certificates'; // Default to certificates if no category
      return certCategory === targetCategory;
    });
    
    // Then apply existing filters (type, status, and search)
    const filtered = categoryFiltered.filter(cert => {
      const typeMatch = certificateFilters.certificateType === 'all' || 
                       cert.cert_type === certificateFilters.certificateType;
      
      // Use new status logic for filtering
      const certStatus = getCertificateStatus(cert);
      const statusMatch = certificateFilters.status === 'all' || 
                         certStatus === certificateFilters.status;
      
      // Search filter for cert_name and cert_abbreviation
      const searchTerm = certificateFilters.search.toLowerCase().trim();
      const searchMatch = !searchTerm || 
                         (cert.cert_name && cert.cert_name.toLowerCase().includes(searchTerm)) ||
                         (cert.cert_abbreviation && cert.cert_abbreviation.toLowerCase().includes(searchTerm));
      
      return typeMatch && statusMatch && searchMatch;
    });
    
    console.log(`Certificate filtering: ${certificates.length} total → ${categoryFiltered.length} in category '${targetCategory}' → ${filtered.length} after filters`);
    
    // Apply sorting
    return sortCertificates(filtered);
  };

  const getUniqueValues = (field) => {
    const values = certificates.map(cert => cert[field]).filter(Boolean);
    return [...new Set(values)];
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
      { key: 'inspection_records', name: language === 'vi' ? 'Hồ sơ Đăng kiểm' : 'Class Survey Report' },
      { key: 'survey_reports', name: language === 'vi' ? 'Báo cáo kiểm tra' : 'Test Report' },
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

  const handleCertificateDoubleClick = async (cert) => {
    try {
      if (!cert.google_drive_file_id) {
        toast.error(language === 'vi' 
          ? 'Chứng chỉ này chưa có file đính kèm' 
          : 'No file attached to this certificate'
        );
        return;
      }

      // Get Google Drive file view URL
      const response = await axios.get(`${API}/gdrive/file/${cert.google_drive_file_id}/view`);
      
      if (response.data.success && response.data.view_url) {
        // Open file in new window
        window.open(response.data.view_url, '_blank', 'noopener,noreferrer');
        toast.success(language === 'vi' 
          ? 'Đang mở file chứng chỉ...' 
          : 'Opening certificate file...'
        );
      } else {
        toast.error(language === 'vi' 
          ? 'Không thể mở file chứng chỉ' 
          : 'Cannot open certificate file'
        );
      }
    } catch (error) {
      console.error('Error opening certificate file:', error);
      toast.error(language === 'vi' 
        ? 'Lỗi khi mở file chứng chỉ' 
        : 'Error opening certificate file'
      );
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      return new Date(dateString).toLocaleDateString('vi-VN');
    } catch (error) {
      return '-';
    }
  };
  // Enhanced formatting functions for Anniversary Date and Dry Dock Cycle
  const formatAnniversaryDate = (anniversaryDate) => {
    if (!anniversaryDate) return '-';
    
    // Handle enhanced anniversary date format
    if (anniversaryDate.day && anniversaryDate.month) {
      const monthNames = [
        '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
      ];
      return `${anniversaryDate.day} ${monthNames[anniversaryDate.month]}`;
    }
    
    // Handle legacy datetime format
    if (typeof anniversaryDate === 'string') {
      try {
        const date = new Date(anniversaryDate);
        const monthNames = [
          '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ];
        return `${date.getDate()} ${monthNames[date.getMonth() + 1]}`;
      } catch {
        return '-';
      }
    }
    
    return '-';
  };
  
  const formatDryDockCycle = (dryDockCycle) => {
    if (!dryDockCycle) return '-';
    
    // Handle enhanced dry dock cycle format with dd/MM/yyyy format
    if (dryDockCycle.from_date && dryDockCycle.to_date) {
      try {
        const fromDate = new Date(dryDockCycle.from_date);
        const toDate = new Date(dryDockCycle.to_date);
        
        // Format as dd/MM/yyyy
        const formatDate = (date) => {
          const day = String(date.getDate()).padStart(2, '0');
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const year = date.getFullYear();
          return `${day}/${month}/${year}`;
        };
        
        const fromStr = formatDate(fromDate);
        const toStr = formatDate(toDate);
        
        return `${fromStr} - ${toStr}`;
      } catch {
        return '-';
      }
    }
    
    // Handle legacy months format
    if (typeof dryDockCycle === 'number') {
      return `${dryDockCycle} ${language === 'vi' ? 'tháng' : 'months'}`;
    }
    
    return '-';
  };
  
  
  const formatSpecialSurveyCycle = (specialSurveyCycle) => {
    if (!specialSurveyCycle) return '-';
    
    // Handle enhanced special survey cycle format with dd/MM/yyyy format
    if (specialSurveyCycle.from_date && specialSurveyCycle.to_date) {
      try {
        const fromDate = new Date(specialSurveyCycle.from_date);
        const toDate = new Date(specialSurveyCycle.to_date);
        
        // Format as dd/MM/yyyy
        const formatDate = (date) => {
          const day = String(date.getDate()).padStart(2, '0');
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const year = date.getFullYear();
          return `${day}/${month}/${year}`;
        };
        
        const fromStr = formatDate(fromDate);
        const toStr = formatDate(toDate);
        
        return `${fromStr} - ${toStr}`;
      } catch {
        return '-';
      }
    }
    
    // Handle legacy months format  
    if (typeof specialSurveyCycle === 'number') {
      return `${specialSurveyCycle} ${language === 'vi' ? 'tháng' : 'months'}`;
    }
    
    return '-';
  };
  
  // Anniversary date management functions
  const handleRecalculateAnniversaryDate = async (shipId) => {
    if (!shipId) return;
    
    try {
      const currentToken = localStorage.getItem('token') || sessionStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/ships/${shipId}/calculate-anniversary-date`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Show success message with calculated date
        alert(`Anniversary date calculated: ${result.anniversary_date.display}\nSource: ${result.anniversary_date.source}`);
        
        // Refresh the ship data
        if (selectedShip?.id === shipId) {
          fetchShips(); // Refresh the ship list
          // Optionally refresh ship details if in detail view
        }
      } else {
        alert(result.message || 'Unable to calculate anniversary date from certificates');
      }
    } catch (error) {
      console.error('Error recalculating anniversary date:', error);
      alert('Failed to recalculate anniversary date');
    }
  };

  // Special Survey Cycle management functions
  const handleRecalculateSpecialSurveyCycle = async (shipId) => {
    if (!shipId) return;
    
    try {
      const currentToken = localStorage.getItem('token') || sessionStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/ships/${shipId}/calculate-special-survey-cycle`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Show success message with calculated cycle
        alert(`Special Survey cycle calculated: ${result.special_survey_cycle.display}\nCycle Type: ${result.special_survey_cycle.cycle_type}\nIntermediate Survey Required: ${result.special_survey_cycle.intermediate_required ? 'Yes' : 'No'}`);
        
        // Refresh the ship data
        if (selectedShip?.id === shipId) {
          fetchShips(); // Refresh the ship list
        }
      } else {
        alert(result.message || 'Unable to calculate Special Survey cycle from certificates');
      }
    } catch (error) {
      console.error('Error recalculating special survey cycle:', error);
      alert('Failed to recalculate special survey cycle');
    }
  };

  // Last Docking dates management functions
  const handleRecalculateDockingDates = async (shipId) => {
    if (!shipId) return;
    
    try {
      const currentToken = localStorage.getItem('token') || sessionStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/ships/${shipId}/calculate-docking-dates`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Show success message with calculated dates
        let message = 'Docking dates extracted from CSSC/DD certificates:\n';
        if (result.docking_dates.last_docking) {
          message += `Last Docking 1: ${result.docking_dates.last_docking}\n`;
        }
        if (result.docking_dates.last_docking_2) {
          message += `Last Docking 2: ${result.docking_dates.last_docking_2}`;
        }
        alert(message);
        
        // Refresh the ship data
        if (selectedShip?.id === shipId) {
          fetchShips(); // Refresh the ship list
        }
      } else {
        alert(result.message || 'Unable to extract docking dates from CSSC/DD certificates');
      }
    } catch (error) {
      console.error('Error recalculating docking dates:', error);
      alert('Failed to recalculate docking dates');
    }
  };

  // Next Docking calculation functions
  const handleRecalculateNextDocking = async (shipId) => {
    if (!shipId) return;
    
    try {
      const currentToken = localStorage.getItem('token') || sessionStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/ships/${shipId}/calculate-next-docking`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Show success message with calculated date
        let message = `Next docking calculated: ${result.next_docking.date}\n`;
        message += `Interval: ${result.next_docking.interval_months} months (${result.next_docking.compliance})\n`;
        message += `Class Society: ${result.next_docking.class_society}\n`;
        if (result.next_docking.ship_age) {
          message += `Ship Age: ${result.next_docking.ship_age} years\n`;
        }
        message += `Notes: ${result.next_docking.notes}`;
        
        alert(message);
        
        // Refresh the ship data
        if (selectedShip?.id === shipId) {
          fetchShips(); // Refresh the ship list
        }
      } else {
        alert(result.message || 'Unable to calculate next docking date. Last docking date required.');
      }
    } catch (error) {
      console.error('Error recalculating next docking date:', error);
      alert('Failed to recalculate next docking date');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-lg border-b">
        <div className="w-full px-4 py-4">
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

      <div className="w-full px-4 py-8">
        <div className="grid lg:grid-cols-5 gap-4">
          {/* Left Sidebar - Categories and Ships (Reduced width: 1/5 instead of 1/4) */}
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
                onClick={() => {
                  setAddRecordDefaultTab(null); // No default tab when clicked from main button
                  setShowAddRecord(true);
                }}
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

          {/* Main Content Area (Expanded width: 4/5 instead of 3/4) */}
          <div className="lg:col-span-4">
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
                                // Initialize enhanced fields for editing
                                const initData = {
                                  ...selectedShip,
                                  // Ensure enhanced anniversary date structure
                                  anniversary_date: selectedShip.anniversary_date && typeof selectedShip.anniversary_date === 'object' 
                                    ? selectedShip.anniversary_date 
                                    : selectedShip.anniversary_date 
                                      ? { day: null, month: null, auto_calculated: false, manual_override: true, source_certificate_type: "Legacy" }
                                      : { day: null, month: null, auto_calculated: false, manual_override: false, source_certificate_type: null },
                                  // Ensure enhanced dry dock cycle structure
                                  dry_dock_cycle: selectedShip.dry_dock_cycle && typeof selectedShip.dry_dock_cycle === 'object'
                                    ? selectedShip.dry_dock_cycle
                                    : selectedShip.dry_dock_cycle && typeof selectedShip.dry_dock_cycle === 'number'
                                      ? { from_date: null, to_date: null, intermediate_docking_required: true, last_intermediate_docking: null }
                                      : { from_date: null, to_date: null, intermediate_docking_required: true, last_intermediate_docking: null },
                                  // Ensure enhanced special survey cycle structure
                                  special_survey_cycle: selectedShip.special_survey_cycle && typeof selectedShip.special_survey_cycle === 'object'
                                    ? selectedShip.special_survey_cycle
                                    : { from_date: null, to_date: null, intermediate_required: false, cycle_type: null }
                                };
                                setEditingShipData(initData);
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
                        {/* Basic Ship Info (Always visible) - Enhanced 3x3 Grid Layout */}
                        <div className="grid grid-cols-3 gap-4 text-sm mb-4">
                          <div className="text-base font-bold">
                            <span className="font-bold">{language === 'vi' ? 'Tên tàu:' : 'Ship Name:'}</span>
                            <span className="ml-2 font-bold">{selectedShip.name}</span>
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
                            <span className="font-semibold">{language === 'vi' ? 'IMO:' : 'IMO:'}</span>
                            <span className="ml-2">{selectedShip.imo || '-'}</span>
                          </div>
                          <div>
                            <span className="font-semibold">{language === 'vi' ? 'Năm đóng:' : 'Built Year:'}</span>
                            <span className="ml-2">{selectedShip.built_year || '-'}</span>
                          </div>
                          <div className={`${(selectedShip.ship_owner || '').length > 25 ? 'row-span-2' : ''}`}>
                            <span className="font-semibold">{language === 'vi' ? 'Chủ tàu:' : 'Ship Owner:'}</span>
                            <span className="ml-2 break-words">{selectedShip.ship_owner || '-'}</span>
                          </div>
                          <div>
                            <span className="font-semibold">{language === 'vi' ? 'Tổng Dung Tích:' : 'Gross Tonnage:'}</span>
                            <span className="ml-2">{selectedShip.gross_tonnage?.toLocaleString() || '-'}</span>
                          </div>
                          <div>
                            <span className="font-semibold">{language === 'vi' ? 'Trọng Tải:' : 'Deadweight:'}</span>
                            <span className="ml-2">{selectedShip.deadweight?.toLocaleString() || '-'}</span>
                          </div>
                          {/* Empty slot - will be occupied by Ship Owner if text is long */}
                          <div className={`${(selectedShip.ship_owner || '').length > 25 ? 'hidden' : ''}`}></div>
                        </div>

                        {/* Full Ship Info (Toggle visibility) - 3 columns layout */}
                        {showFullShipInfo && (
                          <div className="p-4 bg-gray-50 rounded-lg border">
                            <div className="mb-3">
                              <h4 className="font-semibold text-gray-700 border-b pb-2">
                                {language === 'vi' ? 'Thông tin chi tiết tàu' : 'Detailed Ship Information'}
                              </h4>
                            </div>
                            
                            <div className="grid grid-cols-3 gap-6 text-sm">
                              {/* Column 1 - Docking Data (Vertical) */}
                              <div className="space-y-3">
                                <div>
                                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Last Docking 1:' : 'Last Docking 1:'}</span>
                                  <div className="mt-1 flex items-center space-x-2">
                                    <span>{formatDate(selectedShip.last_docking) || '-'}</span>
                                    <button
                                      onClick={() => handleRecalculateDockingDates(selectedShip.id)}
                                      className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                                      title="Recalculate from CSSC/DD certificates"
                                    >
                                      ↻
                                    </button>
                                  </div>
                                </div>
                                <div>
                                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Last Docking 2:' : 'Last Docking 2:'}</span>
                                  <div className="mt-1">{formatDate(selectedShip.last_docking_2) || '-'}</div>
                                </div>
                                <div>
                                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Next Docking:' : 'Next Docking:'}</span>
                                  <div className="mt-1 flex items-center space-x-2">
                                    <span>{formatDate(selectedShip.next_docking) || '-'}</span>
                                    {selectedShip.next_docking && (
                                      <span className="px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded" title="IMO SOLAS 30-month requirement">
                                        IMO
                                      </span>
                                    )}
                                    <button
                                      onClick={() => handleRecalculateNextDocking(selectedShip.id)}
                                      className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                                      title="Recalculate based on IMO requirements"
                                    >
                                      ↻
                                    </button>
                                  </div>
                                </div>
                              </div>
                              
                              {/* Column 2 - Special Survey Management (Vertical) */}
                              <div className="space-y-3">
                                <div>
                                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Chu kỳ Special Survey:' : 'Special Survey Cycle:'}</span>
                                  <div className="mt-1 flex items-center space-x-2">
                                    <span>{formatSpecialSurveyCycle(selectedShip.special_survey_cycle) || '-'}</span>
                                    {selectedShip.special_survey_cycle?.cycle_type && (
                                      <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded" title={selectedShip.special_survey_cycle.cycle_type}>
                                        IMO
                                      </span>
                                    )}
                                    <button
                                      onClick={() => handleRecalculateSpecialSurveyCycle(selectedShip.id)}
                                      className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                                      title="Recalculate from Full Term certificates"
                                    >
                                      ↻
                                    </button>
                                  </div>
                                </div>
                                <div>
                                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Last Special Survey:' : 'Last Special Survey:'}</span>
                                  <div className="mt-1">{formatDate(selectedShip.last_special_survey) || '-'}</div>
                                </div>
                                <div>
                                  <span className="font-semibold text-gray-700 flex items-center">
                                    {language === 'vi' ? 'Last Intermediate:' : 'Last Intermediate:'}
                                    <div className="group relative ml-1">
                                      <svg className="w-3 h-3 text-gray-400 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                      </svg>
                                      <div className="absolute bottom-full left-0 mb-2 w-48 p-2 text-xs text-white bg-gray-800 rounded opacity-0 group-hover:opacity-100 transition-opacity z-10">
                                        {language === 'vi' 
                                          ? 'Kiểm tra trung gian giữa 2 Special Survey (2.5-3 năm)'
                                          : 'Mid-cycle inspection between Special Surveys (2.5-3 years)'}
                                      </div>
                                    </div>
                                  </span>
                                  <div className="mt-1">{formatDate(selectedShip.last_intermediate_survey) || '-'}</div>
                                </div>
                              </div>
                              
                              {/* Column 3 - Anniversary & Compliance (Vertical) */}
                              <div className="space-y-3">
                                <div>
                                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Anniversary Date:' : 'Anniversary Date:'}</span>
                                  <div className="mt-1 flex items-center space-x-2">
                                    <span>{formatAnniversaryDate(selectedShip.anniversary_date) || '-'}</span>
                                    {selectedShip.anniversary_date?.manual_override && (
                                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">Manual</span>
                                    )}
                                    {selectedShip.anniversary_date?.auto_calculated && (
                                      <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">Auto</span>
                                    )}
                                    <button
                                      onClick={() => handleRecalculateAnniversaryDate(selectedShip.id)}
                                      className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                                      title="Recalculate from certificates"
                                    >
                                      ↻
                                    </button>
                                  </div>
                                </div>
                                <div>
                                  <span className="font-semibold text-gray-700">{language === 'vi' ? 'Keel Laid:' : 'Keel Laid:'}</span>
                                  <div className="mt-1">{formatDate(selectedShip.keel_laid) || '-'}</div>
                                </div>
                              </div>
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
                      <div className="flex justify-between items-center mb-4">
                        <div className="flex items-center gap-3">
                          <h3 className="text-lg font-semibold text-gray-800">
                            {language === 'vi' ? 'Danh mục Giấy chứng nhận' : 'Certificate List'}
                          </h3>
                          
                          {/* Selection Indicator */}
                          {selectedCertificates.size > 0 && (
                            <div className="flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              {selectedCertificates.size} {language === 'vi' ? 'đã chọn' : 'selected'}
                            </div>
                          )}
                        </div>
                        
                        <div className="flex gap-3">
                          {/* Update Next Survey Button */}
                          <button
                            onClick={handleUpdateSurveyTypes}
                            disabled={isUpdatingSurveyTypes || !selectedShip}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                              selectedShip && !isUpdatingSurveyTypes
                                ? 'bg-purple-600 hover:bg-purple-700 text-white cursor-pointer'
                                : 'bg-gray-400 cursor-not-allowed text-white'
                            }`}
                            title={selectedShip 
                              ? (language === 'vi' ? 'Cập nhật loại khảo sát tiếp theo' : 'Update next survey types')
                              : (language === 'vi' ? 'Vui lòng chọn tàu trước' : 'Please select a ship first')
                            }
                          >
                            {isUpdatingSurveyTypes ? (
                              <>
                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                {language === 'vi' ? 'Đang cập nhật...' : 'Updating...'}
                              </>
                            ) : (
                              <>
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                {language === 'vi' ? 'Cập nhật Next Survey' : 'Update Next Survey'}
                              </>
                            )}
                          </button>
                          
                          {/* Cert Upload Button */}
                          <button
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                              selectedShip && !isMultiCertProcessing
                                ? 'bg-green-600 hover:bg-green-700 text-white cursor-pointer'
                                : 'bg-gray-400 cursor-not-allowed text-white'
                            }`}
                            title={selectedShip 
                              ? (language === 'vi' ? 'Mở form thêm chứng chỉ' : 'Open add certificate form')
                              : (language === 'vi' ? 'Vui lòng chọn tàu trước' : 'Please select a ship first')
                            }
                            onClick={() => {
                              if (selectedShip && !isMultiCertProcessing) {
                                setAddRecordDefaultTab('certificate'); // Force certificate tab
                                setShowAddRecord(true);
                              }
                            }}
                            disabled={!selectedShip || isMultiCertProcessing}
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            {isMultiCertProcessing 
                              ? (language === 'vi' ? '⏳ Đang xử lý...' : '⏳ Processing...')
                              : (language === 'vi' ? '📋 Thêm chứng chỉ' : '📋 Add Certificate')
                            }
                          </button>

                          {/* Refresh Button */}
                          <button
                            onClick={handleRefreshCertificates}
                            disabled={isRefreshing}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg text-sm font-medium transition-all"
                          >
                            <span className={`${isRefreshing ? 'animate-spin' : ''}`}>🔄</span>
                            {isRefreshing 
                              ? (language === 'vi' ? 'Đang cập nhật...' : 'Refreshing...') 
                              : (language === 'vi' ? 'Refresh' : 'Refresh')
                            }
                          </button>
                        </div>
                      </div>

                      {/* Filter Controls */}
                      <div className="mb-4 p-4 bg-gray-50 rounded-lg border">
                        <div className="flex gap-4 items-center flex-wrap">
                          <div className="flex items-center gap-2">
                            <label className="text-sm font-medium text-gray-700">
                              {language === 'vi' ? 'Loại chứng chỉ:' : 'Certificate Type:'}
                            </label>
                            <select
                              value={certificateFilters.certificateType}
                              onChange={(e) => setCertificateFilters(prev => ({...prev, certificateType: e.target.value}))}
                              className="border border-gray-300 rounded px-3 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                              <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
                              {getUniqueValues('cert_type').map(type => (
                                <option key={type} value={type}>{type}</option>
                              ))}
                            </select>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <label className="text-sm font-medium text-gray-700">
                              {language === 'vi' ? 'Trạng thái:' : 'Status:'}
                            </label>
                            <select
                              value={certificateFilters.status}
                              onChange={(e) => setCertificateFilters(prev => ({...prev, status: e.target.value}))}
                              className="border border-gray-300 rounded px-3 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                              <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
                              <option value="Valid">{language === 'vi' ? 'Còn hiệu lực' : 'Valid'}</option>
                              <option value="Expired">{language === 'vi' ? 'Hết hiệu lực' : 'Expired'}</option>
                            </select>
                          </div>
                          
                          {/* Search Filter */}
                          <div className="flex items-center gap-2">
                            <label className="text-sm font-medium text-gray-700">
                              {language === 'vi' ? 'Tìm kiếm:' : 'Search:'}
                            </label>
                            <div className="relative">
                              <input
                                type="text"
                                value={certificateFilters.search}
                                onChange={(e) => setCertificateFilters(prev => ({...prev, search: e.target.value}))}
                                placeholder={language === 'vi' ? 'Tìm theo tên chứng chỉ...' : 'Search by certificate name...'}
                                className="border border-gray-300 rounded px-3 py-1 pl-8 text-sm w-64 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              />
                              <svg 
                                className="w-4 h-4 text-gray-400 absolute left-2 top-1/2 transform -translate-y-1/2" 
                                fill="none" 
                                stroke="currentColor" 
                                viewBox="0 0 24 24"
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                              </svg>
                              {certificateFilters.search && (
                                <button
                                  onClick={() => setCertificateFilters(prev => ({...prev, search: ''}))}
                                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                  </svg>
                                </button>
                              )}
                            </div>
                          </div>
                          
                          {/* Results Count with Link Status */}
                          <div className="ml-auto flex items-center gap-3">
                            <div className="text-sm text-gray-600">
                              {language === 'vi' 
                                ? `Hiển thị ${getFilteredCertificates().length} / ${certificates.length} chứng chỉ`
                                : `Showing ${getFilteredCertificates().length} / ${certificates.length} certificates`
                              }
                            </div>
                            
                            {/* Pre-fetch Links Indicator */}
                            {linksFetching && (
                              <div className="flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">
                                <svg className="w-3 h-3 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                {language === 'vi' ? 'Đang tải links...' : 'Loading links...'}
                              </div>
                            )}
                            
                            {!linksFetching && Object.keys(getCurrentShipLinks()).length > 0 && (
                              <div className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                                {Object.keys(getCurrentShipLinks()).length} {language === 'vi' ? 'links sẵn sàng' : 'links ready'}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse border border-gray-300 text-sm resizable-table">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="border border-gray-300 px-4 py-2 text-left font-medium bg-gray-50 w-20">
                                <div className="flex items-center space-x-2">
                                  <input
                                    type="checkbox"
                                    checked={isAllSelected()}
                                    ref={headerCheckboxRef => {
                                      if (headerCheckboxRef) {
                                        headerCheckboxRef.indeterminate = isIndeterminate();
                                      }
                                    }}
                                    onChange={(e) => handleSelectAllCertificates(e.target.checked)}
                                    className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                                  />
                                  <span>{language === 'vi' ? 'STT' : 'No.'}</span>
                                </div>
                              </th>
                              <th 
                                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[120px] resize-handle"
                                onClick={() => handleCertificateSort('cert_abbreviation')}
                                style={{overflow: 'hidden'}}
                              >
                                <div className="flex items-center justify-between">
                                  <span>{language === 'vi' ? 'Tên viết tắt' : 'Cert. Name'}</span>
                                  {getSortIcon('cert_abbreviation')}
                                </div>
                              </th>
                              <th 
                                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[100px] resize-handle"
                                onClick={() => handleCertificateSort('cert_type')}
                                style={{overflow: 'hidden'}}
                              >
                                <div className="flex items-center justify-between">
                                  <span>{language === 'vi' ? 'Loại' : 'Type'}</span>
                                  {getSortIcon('cert_type')}
                                </div>
                              </th>
                              <th 
                                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[120px] resize-handle"
                                onClick={() => handleCertificateSort('cert_no')}
                                style={{overflow: 'hidden'}}
                              >
                                <div className="flex items-center justify-between">
                                  <span>{language === 'vi' ? 'Số chứng chỉ' : 'Certificate No'}</span>
                                  {getSortIcon('cert_no')}
                                </div>
                              </th>
                              <th 
                                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[100px] resize-handle"
                                onClick={() => handleCertificateSort('issue_date')}
                                style={{overflow: 'hidden'}}
                              >
                                <div className="flex items-center justify-between">
                                  <span>{language === 'vi' ? 'Ngày cấp' : 'Issue Date'}</span>
                                  {getSortIcon('issue_date')}
                                </div>
                              </th>
                              <th 
                                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[100px] resize-handle"
                                onClick={() => handleCertificateSort('valid_date')}
                                style={{overflow: 'hidden'}}
                              >
                                <div className="flex items-center justify-between">
                                  <span>{language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}</span>
                                  {getSortIcon('valid_date')}
                                </div>
                              </th>
                              <th 
                                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[100px] resize-handle"
                                onClick={() => handleCertificateSort('last_endorse')}
                                style={{overflow: 'hidden'}}
                              >
                                <div className="flex items-center justify-between">
                                  <span>{language === 'vi' ? 'Xác nhận cuối' : 'Last Endorse'}</span>
                                  {getSortIcon('last_endorse')}
                                </div>
                              </th>
                              <th 
                                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[120px] resize-handle"
                                onClick={() => handleCertificateSort('next_survey')}
                                style={{overflow: 'hidden'}}
                              >
                                <div className="flex items-center justify-between">
                                  <span>{language === 'vi' ? 'Khảo sát tiếp theo' : 'Next Survey'}</span>
                                  {getSortIcon('next_survey')}
                                </div>
                              </th>
                              
                              {/* Next Survey Type Column */}
                              <th 
                                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[120px] resize-handle"
                                onClick={() => handleCertificateSort('next_survey_type')}
                                style={{overflow: 'hidden'}}
                              >
                                <div className="flex items-center justify-between">
                                  <span>{language === 'vi' ? 'Loại khảo sát tiếp theo' : 'Next Survey Type'}</span>
                                  {getSortIcon('next_survey_type')}
                                </div>
                              </th>
                              <th 
                                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[120px] resize-handle"
                                onClick={() => handleCertificateSort('issued_by')}
                                style={{overflow: 'hidden'}}
                              >
                                <div className="flex items-center justify-between">
                                  <span>{language === 'vi' ? 'Cấp bởi' : 'Issued By'}</span>
                                  {getSortIcon('issued_by')}
                                </div>
                              </th>
                              <th 
                                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[80px] resize-handle"
                                onClick={() => handleCertificateSort('status')}
                                style={{overflow: 'hidden'}}
                              >
                                <div className="flex items-center justify-between">
                                  <span>{language === 'vi' ? 'Trạng thái' : 'Status'}</span>
                                  {getSortIcon('status')}
                                </div>
                              </th>
                              <th 
                                className="border border-gray-300 px-4 py-2 text-left cursor-pointer hover:bg-gray-100 min-w-[100px] resize-handle"
                                onClick={() => handleCertificateSort('notes')}
                                style={{overflow: 'hidden'}}
                              >
                                <div className="flex items-center justify-between">
                                  <span>{language === 'vi' ? 'Ghi chú' : 'Notes'}</span>
                                  {getSortIcon('notes')}
                                </div>
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {getFilteredCertificates().length === 0 ? (
                              <tr>
                                <td colSpan="12" className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                                  {certificates.length === 0 
                                    ? (language === 'vi' ? 'Chưa có chứng chỉ nào' : 'No certificates available')
                                    : (language === 'vi' ? 'Không có chứng chỉ nào phù hợp với bộ lọc' : 'No certificates match the current filters')
                                  }
                                </td>
                              </tr>
                            ) : (
                              getFilteredCertificates().map((cert, index) => (
                                <tr 
                                  key={cert.id} 
                                  className={`hover:bg-gray-50 cursor-pointer transition-colors ${cert.google_drive_file_id ? 'hover:bg-blue-50' : ''}`}
                                  onDoubleClick={() => handleCertificateDoubleClick(cert)}
                                  onContextMenu={(e) => handleCertificateRightClick(e, cert)}
                                  title={cert.google_drive_file_id 
                                    ? (language === 'vi' ? 'Nhấn đúp để mở file | Chuột phải để Edit/Delete' : 'Double-click to open file | Right-click for Edit/Delete')
                                    : (language === 'vi' ? 'Chưa có file đính kèm | Chuột phải để Edit/Delete' : 'No file attached | Right-click for Edit/Delete')
                                  }
                                >
                                  <td className="border border-gray-300 px-4 py-2 text-center w-20">
                                    <div className="flex items-center space-x-2">
                                      <input
                                        type="checkbox"
                                        checked={selectedCertificates.has(cert.id)}
                                        onChange={() => handleSelectCertificate(cert.id)}
                                        className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                                        onClick={(e) => e.stopPropagation()}
                                      />
                                      <span className="font-bold">{index + 1}</span>
                                    </div>
                                  </td>
                                  <td 
                                    className="border border-gray-300 px-4 py-2 font-mono font-bold text-blue-600"
                                    title={cert.cert_name}
                                    style={{ cursor: 'help' }}
                                  >
                                    {cert.cert_abbreviation || cert.cert_name?.substring(0, 4) || 'N/A'}
                                  </td>
                                  <td className="border border-gray-300 px-4 py-2">
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                                      cert.cert_type === 'Full Term' ? 'bg-green-100 text-green-800' :
                                      cert.cert_type === 'Interim' ? 'bg-yellow-100 text-yellow-800' :
                                      cert.cert_type === 'Provisional' ? 'bg-orange-100 text-orange-800' :
                                      cert.cert_type === 'Short term' ? 'bg-red-100 text-red-800' :
                                      cert.cert_type === 'Conditional' ? 'bg-blue-100 text-blue-800' :
                                      cert.cert_type === 'Other' ? 'bg-purple-100 text-purple-800' :
                                      'bg-gray-100 text-gray-800'
                                    }`}>
                                      {cert.cert_type || 'Unknown'}
                                    </span>
                                  </td>
                                  <td className="border border-gray-300 px-4 py-2 font-mono">{cert.cert_no}</td>
                                  <td className="border border-gray-300 px-4 py-2">{formatDate(cert.issue_date)}</td>
                                  <td className="border border-gray-300 px-4 py-2">{formatDate(cert.valid_date)}</td>
                                  <td className="border border-gray-300 px-4 py-2">
                                    {cert.cert_type === 'Full Term' 
                                      ? formatDate(cert.last_endorse) 
                                      : (
                                        <span className="text-gray-400 text-sm italic">
                                          {language === 'vi' ? 'Không áp dụng' : 'N/A'}
                                        </span>
                                      )
                                    }
                                  </td>
                                  <td className="border border-gray-300 px-4 py-2">
                                    {cert.next_survey_display || formatDate(cert.next_survey)}
                                  </td>
                                  <td className="border border-gray-300 px-4 py-2">
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                                      cert.next_survey_type === 'Annual' ? 'bg-blue-100 text-blue-800' :
                                      cert.next_survey_type === 'Intermediate' ? 'bg-yellow-100 text-yellow-800' :
                                      cert.next_survey_type === 'Renewal' ? 'bg-green-100 text-green-800' :
                                      cert.next_survey_type === 'Special' ? 'bg-purple-100 text-purple-800' :
                                      cert.next_survey_type === 'Dry Dock' ? 'bg-orange-100 text-orange-800' :
                                      cert.next_survey_type === '1st Annual Survey' ? 'bg-blue-100 text-blue-800' :
                                      cert.next_survey_type === '2nd Annual Survey/Intermediate Survey' ? 'bg-yellow-100 text-yellow-800' :
                                      cert.next_survey_type === '3rd Annual Survey' ? 'bg-blue-100 text-blue-800' :
                                      cert.next_survey_type === '4th Annual Survey' ? 'bg-blue-100 text-blue-800' :
                                      cert.next_survey_type === 'Special Survey' ? 'bg-purple-100 text-purple-800' :
                                      cert.next_survey_type === 'Condition Certificate Expiry' ? 'bg-red-100 text-red-800' :
                                      cert.next_survey_type?.includes('Annual Survey') ? 'bg-blue-100 text-blue-800' :
                                      cert.next_survey_type?.includes('Intermediate') ? 'bg-yellow-100 text-yellow-800' :
                                      'bg-gray-100 text-gray-800'
                                    }`}>
                                      {cert.next_survey_type || '-'}
                                    </span>
                                  </td>
                                  <td className="border border-gray-300 px-4 py-2 text-sm font-semibold text-blue-700" title={cert.issued_by}>
                                    {cert.issued_by_abbreviation || (cert.issued_by ? 
                                      (cert.issued_by.length > 8 ? `${cert.issued_by.substring(0, 8)}...` : cert.issued_by)
                                      : '-'
                                    )}
                                  </td>
                                  <td className="border border-gray-300 px-4 py-2">
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                                      getCertificateStatus(cert) === 'Valid' ? 'bg-green-100 text-green-800' :
                                      getCertificateStatus(cert) === 'Expired' ? 'bg-red-100 text-red-800' :
                                      'bg-gray-100 text-gray-800'
                                    }`}>
                                      {getCertificateStatus(cert) === 'Valid' 
                                        ? (language === 'vi' ? 'Còn hiệu lực' : 'Valid')
                                        : getCertificateStatus(cert) === 'Expired' 
                                        ? (language === 'vi' ? 'Hết hiệu lực' : 'Expired')
                                        : (language === 'vi' ? 'Không rõ' : 'Unknown')
                                      }
                                    </span>
                                  </td>
                                  <td className="border border-gray-300 px-4 py-2 text-center" title={cert.notes}>
                                    {cert.has_notes ? (
                                      <span className="text-orange-600 font-bold cursor-help text-lg">*</span>
                                    ) : (
                                      <span className="text-gray-400">-</span>
                                    )}
                                  </td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Certificate Context Menu */}
                  {contextMenu.show && (
                    <div 
                      className="fixed bg-white border border-gray-200 rounded-lg shadow-lg z-[100]"
                      style={{
                        position: 'fixed',
                        top: `${contextMenu.y}px`,
                        left: `${contextMenu.x}px`,
                        minWidth: '180px'
                      }}
                    >
                      <div className="py-1">
                        {selectedCertificates.size > 1 && (
                          <div className="px-4 py-2 text-xs font-semibold text-gray-500 border-b border-gray-200">
                            {selectedCertificates.size} {language === 'vi' ? 'chứng chỉ đã chọn' : 'certificates selected'}
                          </div>
                        )}
                        
                        <button
                          onClick={() => {
                            if (selectedCertificates.size > 1) {
                              handleOpenSelectedCertificates();
                            } else {
                              handleOpenCertificate(contextMenu.certificate);
                            }
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                        >
                          <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                          {selectedCertificates.size > 1 
                            ? (language === 'vi' ? `Mở ${selectedCertificates.size} files` : `Open ${selectedCertificates.size} files`)
                            : (language === 'vi' ? 'Mở' : 'Open')
                          }
                        </button>
                        
                        <button
                          onClick={() => {
                            if (selectedCertificates.size > 1) {
                              handleCopySelectedLinks();
                            } else {
                              handleCopyLink(contextMenu.certificate);
                            }
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                        >
                          <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                          </svg>
                          {selectedCertificates.size > 1 
                            ? (language === 'vi' ? `Copy ${selectedCertificates.size} links` : `Copy ${selectedCertificates.size} links`)
                            : (language === 'vi' ? 'Copy Link' : 'Copy Link')
                          }
                        </button>
                        
                        <button
                          onClick={() => {
                            if (selectedCertificates.size > 1) {
                              handleDownloadSelectedCertificates();
                            } else {
                              handleDownloadCertificate(contextMenu.certificate);
                            }
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                        >
                          <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          {selectedCertificates.size > 1 
                            ? (language === 'vi' ? `Tải xuống ${selectedCertificates.size} files` : `Download ${selectedCertificates.size} files`)
                            : (language === 'vi' ? 'Tải xuống' : 'Download')
                          }
                        </button>
                        
                        <div className="border-t border-gray-200 my-1"></div>
                        
                        <button
                          onClick={handleEditCertificate}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                        >
                          <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                          {language === 'vi' ? 'Chỉnh sửa' : 'Edit'}
                        </button>
                        
                        <button
                          onClick={handleDeleteCertificateFromContext}
                          className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center"
                        >
                          <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                          {language === 'vi' ? 'Xóa' : 'Delete'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Delete Confirmation Modal */}
                  {showDeleteConfirmation && (
                    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                        <div className="mt-3 text-center">
                          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                            <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                            </svg>
                          </div>
                          <h3 className="text-lg leading-6 font-medium text-gray-900 mt-2">
                            {language === 'vi' ? 'Xác nhận xóa' : 'Confirm Delete'}
                          </h3>
                          <div className="mt-2 px-7 py-3">
                            <p className="text-sm text-gray-500">
                              {selectedCertificates.size > 1 
                                ? (language === 'vi' 
                                    ? `Bạn có chắc chắn muốn xóa ${selectedCertificates.size} chứng chỉ đã chọn?`
                                    : `Are you sure you want to delete ${selectedCertificates.size} selected certificates?`)
                                : (language === 'vi' 
                                    ? 'Bạn có chắc chắn muốn xóa chứng chỉ này?'
                                    : 'Are you sure you want to delete this certificate?')
                              }
                            </p>
                            <p className="text-xs text-gray-400 mt-2">
                              {language === 'vi' ? 'Hành động này không thể hoàn tác.' : 'This action cannot be undone.'}
                            </p>
                          </div>
                          <div className="flex justify-center space-x-4 mt-4">
                            <button
                              onClick={() => setShowDeleteConfirmation(false)}
                              className="px-4 py-2 bg-gray-300 text-gray-700 text-base font-medium rounded-md shadow-sm hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
                            >
                              {language === 'vi' ? 'Hủy' : 'Cancel'}
                            </button>
                            <button
                              onClick={async () => {
                                try {
                                  if (selectedCertificates.size > 1) {
                                    // Delete multiple certificates
                                    for (const certId of selectedCertificates) {
                                      await fetch(`${API}/certificates/${certId}`, {
                                        method: 'DELETE',
                                        headers: { 'Authorization': `Bearer ${token}` }
                                      });
                                    }
                                    toast.success(language === 'vi' 
                                      ? `Đã xóa ${selectedCertificates.size} chứng chỉ`
                                      : `Deleted ${selectedCertificates.size} certificates`);
                                  } else {
                                    // Delete single certificate
                                    const certId = contextMenu.certificate?.id || Array.from(selectedCertificates)[0];
                                    await fetch(`${API}/certificates/${certId}`, {
                                      method: 'DELETE',
                                      headers: { 'Authorization': `Bearer ${token}` }
                                    });
                                    toast.success(language === 'vi' ? 'Đã xóa chứng chỉ' : 'Certificate deleted');
                                  }
                                  
                                  setSelectedCertificates(new Set());
                                  setShowDeleteConfirmation(false);
                                  fetchCertificates(selectedShip.id); // Fix: add selectedShip.id
                                } catch (error) {
                                  toast.error(language === 'vi' ? 'Lỗi khi xóa' : 'Error deleting');
                                }
                              }}
                              className="px-4 py-2 bg-red-600 text-white text-base font-medium rounded-md shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                            >
                              {language === 'vi' ? 'Xóa' : 'Delete'}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Edit Certificate Modal */}
                  {showEditCertModal && editingCertificate && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[70]">
                      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-md w-full mx-4">
                        <div className="mb-6">
                          <h3 className="text-xl font-bold text-gray-800 mb-2">
                            {language === 'vi' ? 'Chỉnh sửa chứng chỉ' : 'Edit Certificate'}
                          </h3>
                          <p className="text-gray-600 text-sm">
                            {language === 'vi' ? 'Cập nhật thông tin chứng chỉ' : 'Update certificate information'}
                          </p>
                        </div>

                        <form className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              {language === 'vi' ? 'Tên chứng chỉ' : 'Certificate Name'} *
                            </label>
                            <input
                              type="text"
                              value={editingCertificate.cert_name || ''}
                              onChange={(e) => setEditingCertificate(prev => ({ ...prev, cert_name: e.target.value }))}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              required
                            />
                          </div>
                          
                          {/* Certificate Abbreviation Field */}
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              {language === 'vi' ? 'Tên viết tắt' : 'Cert. Name (Abbreviation)'}
                            </label>
                            <input
                              type="text"
                              value={editingCertificate.cert_abbreviation || ''}
                              onChange={(e) => setEditingCertificate(prev => ({ ...prev, cert_abbreviation: e.target.value }))}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              placeholder={language === 'vi' ? 'VD: CSSE, IAPP, ISM...' : 'e.g.: CSSE, IAPP, ISM...'}
                            />
                          </div>
                          
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              {language === 'vi' ? 'Số chứng chỉ' : 'Certificate Number'} *
                            </label>
                            <input
                              type="text"
                              value={editingCertificate.cert_no || ''}
                              onChange={(e) => setEditingCertificate(prev => ({ ...prev, cert_no: e.target.value }))}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              required
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              {language === 'vi' ? 'Loại chứng chỉ' : 'Certificate Type'}
                            </label>
                            <input
                              type="text"
                              value={editingCertificate.cert_type || ''}
                              onChange={(e) => setEditingCertificate(prev => ({ ...prev, cert_type: e.target.value }))}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                {language === 'vi' ? 'Ngày cấp' : 'Issue Date'}
                              </label>
                              <input
                                type="date"
                                value={editingCertificate.issue_date?.split('T')[0] || ''}
                                onChange={(e) => setEditingCertificate(prev => ({ ...prev, issue_date: e.target.value }))}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              />
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                {language === 'vi' ? 'Ngày hết hạn' : 'Valid Date'}
                              </label>
                              <input
                                type="date"
                                value={editingCertificate.valid_date?.split('T')[0] || ''}
                                onChange={(e) => setEditingCertificate(prev => ({ ...prev, valid_date: e.target.value }))}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              />
                            </div>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              {language === 'vi' ? 'Cơ quan cấp' : 'Issued By'}
                            </label>
                            <input
                              type="text"
                              value={editingCertificate.issued_by || ''}
                              onChange={(e) => setEditingCertificate(prev => ({ ...prev, issued_by: e.target.value }))}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                          </div>
                        </form>

                        <div className="flex justify-end space-x-3 mt-6">
                          <button
                            onClick={() => {
                              setShowEditCertModal(false);
                              setEditingCertificate(null);
                            }}
                            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
                          >
                            {language === 'vi' ? 'Hủy' : 'Cancel'}
                          </button>
                          <button
                            onClick={async () => {
                              try {
                                await axios.put(`${API}/certificates/${editingCertificate.id}`, editingCertificate, {
                                  headers: { 'Authorization': `Bearer ${token}` }
                                });
                                
                                toast.success(language === 'vi' ? 'Cập nhật chứng chỉ thành công!' : 'Certificate updated successfully!');
                                setShowEditCertModal(false);
                                setEditingCertificate(null);
                                await fetchCertificates(selectedShip.id); // Refresh list
                              } catch (error) {
                                console.error('Error updating certificate:', error);
                                toast.error(language === 'vi' ? 'Lỗi khi cập nhật chứng chỉ!' : 'Error updating certificate!');
                              }
                            }}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all"
                          >
                            {language === 'vi' ? 'Lưu' : 'Save'}
                          </button>
                        </div>
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
          onClose={() => {
            setShowAddRecord(false);
            setAddRecordDefaultTab(null); // Reset default tab
          }}
          onSuccess={(type) => {
            setShowAddRecord(false);
            setAddRecordDefaultTab(null); // Reset default tab
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
          ships={ships}
          parentAiConfig={aiConfig}
          isMultiCertProcessing={isMultiCertProcessing}
          multiCertUploads={multiCertUploads}
          handleMultiCertUpload={handleMultiCertUpload}
          uploadSummary={uploadSummary}
          setMultiCertUploads={setMultiCertUploads}
          setUploadSummary={setUploadSummary}
          handleUploadToFolder={handleUploadToFolder}
          handleSkipFile={handleSkipFile}
          defaultTab={addRecordDefaultTab}
          // File Viewer Modal props
          showFileViewer={showFileViewer}
          setShowFileViewer={setShowFileViewer}
          fileViewerData={fileViewerData}
          setFileViewerData={setFileViewerData}
          pendingManualReviews={pendingManualReviews}
          handleManualReviewAction={handleManualReviewAction}
          duplicateResolutionModal={duplicateResolutionModal}
          handleDuplicateResolution={handleDuplicateResolution}
          setIsMultiCertProcessing={setIsMultiCertProcessing}
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
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-[95vh] overflow-hidden">
            <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200">
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
            
            <div className="p-6">
              <form onSubmit={(e) => {
                e.preventDefault();
                handleEditShip(editingShipData);
              }}>
                <div className="grid grid-cols-12 gap-4">
                  
                  {/* Basic Ship Information Section */}
                  <div className="col-span-12">
                    <h4 className="text-lg font-semibold text-gray-700 mb-3 pb-2 border-b">
                      {language === 'vi' ? 'Thông tin cơ bản' : 'Basic Information'}
                    </h4>
                  </div>
                  
                  {/* Ship Name - Full width */}
                  <div className="col-span-6">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Tên tàu' : 'Ship Name'} *
                    </label>
                    <input
                      type="text"
                      required
                      value={editingShipData.name || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>

                  {/* IMO - Short width */}
                  <div className="col-span-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Số IMO' : 'IMO Number'}
                    </label>
                    <input
                      type="text"
                      value={editingShipData.imo || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, imo: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      placeholder="1234567"
                    />
                  </div>

                  {/* Flag - Medium width */}
                  <div className="col-span-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Cờ' : 'Flag'} *
                    </label>
                    <input
                      type="text"
                      required
                      value={editingShipData.flag || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, flag: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>

                  {/* Class Society - Medium width */}
                  <div className="col-span-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Tổ chức Phân cấp' : 'Class Society'} *
                    </label>
                    <input
                      type="text"
                      required
                      value={editingShipData.class_society || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, class_society: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>

                  {/* Ship Owner - Medium width */}
                  <div className="col-span-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Chủ tàu' : 'Ship Owner'} *
                    </label>
                    <input
                      type="text"
                      required
                      value={editingShipData.ship_owner || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, ship_owner: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>

                  {/* Gross Tonnage - Short width */}
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'GT' : 'GT'}
                    </label>
                    <input
                      type="number"
                      value={editingShipData.gross_tonnage || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, gross_tonnage: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      placeholder="0"
                    />
                  </div>

                  {/* Deadweight - Short width */}
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'DWT' : 'DWT'}
                    </label>
                    <input
                      type="number"
                      value={editingShipData.deadweight || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, deadweight: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      placeholder="0"
                    />
                  </div>

                  {/* Built Year - Short width */}
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Năm đóng' : 'Built Year'}
                    </label>
                    <input
                      type="number"
                      value={editingShipData.year_built || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, year_built: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      placeholder="2020"
                    />
                  </div>

                  {/* Delivery Date - Short width */}
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Ngày giao' : 'Delivery Date'}
                    </label>
                    <input
                      type="date"
                      value={editingShipData.delivery_date ? new Date(editingShipData.delivery_date).toISOString().split('T')[0] : ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, delivery_date: e.target.value ? e.target.value : null }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>

                  {/* Keel Laid - Short width */}
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Keel Laid' : 'Keel Laid'}
                    </label>
                    <input
                      type="date"
                      value={editingShipData.keel_laid ? new Date(editingShipData.keel_laid).toISOString().split('T')[0] : ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, keel_laid: e.target.value ? e.target.value : null }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>

                  {/* Survey & Maintenance Section */}
                  <div className="col-span-12 mt-4">
                    <h4 className="text-lg font-semibold text-gray-700 mb-3 pb-2 border-b">
                      {language === 'vi' ? 'Thông tin Khảo sát & Bảo dưỡng' : 'Survey & Maintenance Information'}
                    </h4>
                  </div>

                  {/* Docking Dates Row */}
                  <div className="col-span-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Last Docking 1' : 'Last Docking 1'}
                    </label>
                    <input
                      type="date"
                      value={editingShipData.last_docking || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, last_docking: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>

                  <div className="col-span-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Last Docking 2' : 'Last Docking 2'}
                    </label>
                    <input
                      type="date"
                      value={editingShipData.last_docking_2 || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, last_docking_2: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>

                  <div className="col-span-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Next Docking' : 'Next Docking'}
                    </label>
                    <div className="flex space-x-1">
                      <input
                        type="date"
                        value={editingShipData.next_docking || ''}
                        onChange={(e) => setEditingShipData(prev => ({ ...prev, next_docking: e.target.value }))}
                        className="flex-1 px-2 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      />
                      <button
                        type="button"
                        onClick={() => handleRecalculateNextDocking(editingShipData.id)}
                        className="px-2 py-2 bg-orange-100 hover:bg-orange-200 text-orange-800 text-xs rounded-lg transition-colors"
                        title="Auto-calculate"
                      >
                        IMO
                      </button>
                    </div>
                  </div>

                  <div className="col-span-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Last Special Survey' : 'Last Special Survey'}
                    </label>
                    <input
                      type="date"
                      value={editingShipData.last_special_survey || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, last_special_survey: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>

                  <div className="col-span-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <span className="flex items-center">
                        {language === 'vi' ? 'Last Intermediate Survey' : 'Last Intermediate Survey'}
                        <div className="group relative ml-1">
                          <svg className="w-3 h-3 text-gray-400 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <div className="absolute bottom-full left-0 mb-2 w-64 p-2 text-xs text-white bg-gray-800 rounded opacity-0 group-hover:opacity-100 transition-opacity z-10">
                            {language === 'vi' 
                              ? 'Kiểm tra trung gian thực hiện giữa 2 Special Survey (thường 2.5-3 năm). Theo quy định IMO, Class Society như DNV GL, Lloyd\'s Register, ABS, Bureau Veritas.'
                              : 'Intermediate inspection between Special Surveys (typically 2.5-3 years). Required by IMO, Class Societies like DNV GL, Lloyd\'s Register, ABS, Bureau Veritas.'}
                          </div>
                        </div>
                      </span>
                    </label>
                    <input
                      type="date"
                      value={editingShipData.last_intermediate_survey || ''}
                      onChange={(e) => setEditingShipData(prev => ({ ...prev, last_intermediate_survey: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>

                  {/* Anniversary Date Section */}
                  <div className="col-span-6 mt-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Anniversary Date' : 'Anniversary Date'}
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <input
                          type="number"
                          min="1"
                          max="31"
                          value={editingShipData.anniversary_date?.day || ''}
                          onChange={(e) => setEditingShipData(prev => ({ 
                            ...prev, 
                            anniversary_date: {
                              ...prev.anniversary_date,
                              day: parseInt(e.target.value) || null,
                              manual_override: true,
                              auto_calculated: false,
                              source_certificate_type: "Manual Entry"
                            }
                          }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          placeholder="Day"
                        />
                      </div>
                      <div>
                        <select
                          value={editingShipData.anniversary_date?.month || ''}
                          onChange={(e) => setEditingShipData(prev => ({ 
                            ...prev, 
                            anniversary_date: {
                              ...prev.anniversary_date,
                              month: parseInt(e.target.value) || null,
                              manual_override: true,
                              auto_calculated: false,
                              source_certificate_type: "Manual Entry"
                            }
                          }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                        >
                          <option value="">Month</option>
                          <option value="1">Jan</option>
                          <option value="2">Feb</option>
                          <option value="3">Mar</option>
                          <option value="4">Apr</option>
                          <option value="5">May</option>
                          <option value="6">Jun</option>
                          <option value="7">Jul</option>
                          <option value="8">Aug</option>
                          <option value="9">Sep</option>
                          <option value="10">Oct</option>
                          <option value="11">Nov</option>
                          <option value="12">Dec</option>
                        </select>
                      </div>
                      <div>
                        <button
                          type="button"
                          onClick={() => handleRecalculateAnniversaryDate(editingShipData.id)}
                          className="w-full px-3 py-2 bg-blue-100 hover:bg-blue-200 text-blue-800 text-sm rounded-lg transition-colors"
                        >
                          Auto
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Special Survey Cycle Section */}
                  <div className="col-span-6 mt-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'vi' ? 'Special Survey Cycle (IMO 5-year)' : 'Special Survey Cycle (IMO 5-year)'}
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <input
                          type="date"
                          value={editingShipData.special_survey_cycle?.from_date || ''}
                          onChange={(e) => setEditingShipData(prev => ({ 
                            ...prev, 
                            special_survey_cycle: {
                              ...prev.special_survey_cycle,
                              from_date: e.target.value,
                              cycle_type: "IMO 5-year Standard",
                              manual_override: true,
                              auto_calculated: false
                            }
                          }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          placeholder="From Date"
                        />
                      </div>
                      <div>
                        <input
                          type="date"
                          value={editingShipData.special_survey_cycle?.to_date || ''}
                          onChange={(e) => setEditingShipData(prev => ({ 
                            ...prev, 
                            special_survey_cycle: {
                              ...prev.special_survey_cycle,
                              to_date: e.target.value,
                              cycle_type: "IMO 5-year Standard",
                              manual_override: true,
                              auto_calculated: false
                            }
                          }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          placeholder="To Date"
                        />
                      </div>
                      <div>
                        <button
                          type="button"
                          onClick={() => handleRecalculateSpecialSurveyCycle(editingShipData.id)}
                          className="w-full px-3 py-2 bg-purple-100 hover:bg-purple-200 text-purple-800 text-sm rounded-lg transition-colors"
                        >
                          Auto
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-between mt-6 pt-4 border-t border-gray-200">
                  {/* Delete Button - Left side */}
                  <button
                    type="button"
                    onClick={() => {
                      setDeleteShipData(editingShipData);
                      setShowDeleteShipModal(true);
                    }}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all font-medium flex items-center"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    {language === 'vi' ? 'Xóa tàu' : 'Delete Ship'}
                  </button>

                  {/* Cancel and Save Buttons - Right side */}
                  <div className="flex space-x-3">
                    <button
                      type="button"
                      onClick={() => {
                        setShowEditShipModal(false);
                        setEditingShipData(null);
                      }}
                      className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
                    >
                      {language === 'vi' ? 'Hủy' : 'Cancel'}
                    </button>
                    <button
                      type="submit"
                      className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all font-medium"
                    >
                      {language === 'vi' ? 'Lưu thay đổi' : 'Save Changes'}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Ship Confirmation Modal */}
      {showDeleteShipModal && deleteShipData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl">
            <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200">
              <h3 className="text-xl font-bold text-red-600 flex items-center">
                <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                {language === 'vi' ? 'Xác nhận xóa tàu' : 'Confirm Ship Deletion'}
              </h3>
              <button
                onClick={() => {
                  setShowDeleteShipModal(false);
                  setDeleteShipData(null);
                  setDeleteShipOption('database_only');
                }}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
              >
                ×
              </button>
            </div>
            
            <div className="p-6">
              <div className="mb-6">
                <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full">
                  <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </div>
                
                <h4 className="text-lg font-semibold text-gray-900 text-center mb-2">
                  {language === 'vi' 
                    ? `Bạn có chắc chắn muốn xóa tàu "${deleteShipData.name}"?`
                    : `Are you sure you want to delete ship "${deleteShipData.name}"?`
                  }
                </h4>
                
                <p className="text-sm text-gray-600 text-center mb-6">
                  {language === 'vi' 
                    ? 'Hành động này không thể hoàn tác. Vui lòng chọn phương thức xóa:'
                    : 'This action cannot be undone. Please choose the deletion method:'
                  }
                </p>

                {/* Deletion Options */}
                <div className="space-y-4">
                  {/* Option 1: Database Only */}
                  <div 
                    onClick={() => setDeleteShipOption('database_only')}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      deleteShipOption === 'database_only' 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start">
                      <input
                        type="radio"
                        name="deleteOption"
                        value="database_only"
                        checked={deleteShipOption === 'database_only'}
                        onChange={(e) => setDeleteShipOption(e.target.value)}
                        className="mt-1 mr-3"
                      />
                      <div>
                        <h5 className="font-medium text-gray-900">
                          {language === 'vi' ? 'Chỉ xóa dữ liệu trên Database' : 'Delete Database Data Only'}
                        </h5>
                        <p className="text-sm text-gray-600 mt-1">
                          {language === 'vi' 
                            ? 'Xóa thông tin tàu và tất cả chứng chỉ khỏi hệ thống. Giữ nguyên folder trên Google Drive.'
                            : 'Remove ship information and all certificates from the system. Keep Google Drive folder intact.'
                          }
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Option 2: Database + Google Drive */}
                  <div 
                    onClick={() => setDeleteShipOption('with_gdrive')}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      deleteShipOption === 'with_gdrive' 
                        ? 'border-red-500 bg-red-50' 
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start">
                      <input
                        type="radio"
                        name="deleteOption"
                        value="with_gdrive"
                        checked={deleteShipOption === 'with_gdrive'}
                        onChange={(e) => setDeleteShipOption(e.target.value)}
                        className="mt-1 mr-3"
                      />
                      <div>
                        <h5 className="font-medium text-gray-900">
                          {language === 'vi' ? 'Xóa cả Folder trên Google Drive' : 'Delete Including Google Drive Folder'}
                        </h5>
                        <p className="text-sm text-gray-600 mt-1">
                          {language === 'vi' 
                            ? 'Xóa hoàn toàn thông tin tàu và toàn bộ folder structure trên Google Drive. KHÔNG THỂ KHÔI PHỤC!'
                            : 'Completely remove ship information and entire Google Drive folder structure. CANNOT BE RECOVERED!'
                          }
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowDeleteShipModal(false);
                    setDeleteShipData(null);
                    setDeleteShipOption('database_only');
                  }}
                  disabled={isDeletingShip}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all disabled:opacity-50"
                >
                  {language === 'vi' ? 'Hủy' : 'Cancel'}
                </button>
                <button
                  onClick={() => handleDeleteShip(deleteShipData.id, deleteShipOption)}
                  disabled={isDeletingShip}
                  className={`px-6 py-2 text-white rounded-lg transition-all font-medium flex items-center disabled:opacity-50 ${
                    deleteShipOption === 'with_gdrive' 
                      ? 'bg-red-600 hover:bg-red-700' 
                      : 'bg-orange-600 hover:bg-orange-700'
                  }`}
                >
                  {isDeletingShip ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      {language === 'vi' ? 'Đang xóa...' : 'Deleting...'}
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      {language === 'vi' ? 'Xóa tàu' : 'Delete Ship'}
                    </>
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
  // Duplicate modal state for AccountControlPage
  const [duplicateModal, setDuplicateModal] = useState({
    show: false,
    duplicates: [],
    currentFile: null,
    analysisResult: null,
    uploadResult: null,
    status: 'all'
  });
  
  // Duplicate resolution modal for multi-cert upload - removed duplicate state
  
  // Ship mismatch modal state for AccountControlPage
  const [mismatchModal, setMismatchModal] = useState({
    show: false,
    mismatchInfo: null,
    analysisResult: null,
    uploadResult: null
  });
  const [availableCompanies, setAvailableCompanies] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [systemGdriveConfig, setSystemGdriveConfig] = useState({
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
    model: 'gpt-4o',
    api_key: ''
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

  // Helper function to format dates
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      return new Date(dateString).toLocaleDateString('vi-VN');
    } catch (error) {
      return '-';
    }
  };

  // Multi-file upload duplicate resolution functions (AccountControlPage)
  const handleDuplicateResolution = (action) => {
    toast.info(language === 'vi' ? 'Chức năng đang được xây dựng lại' : 'Feature is being rebuilt');
  };

  // These functions are not needed in AddRecordModal
  // Duplicate resolution is handled at the main component level

  const handleMismatchResolution = (action) => {
    toast.info(language === 'vi' ? 'Chức năng đang được xây dựng lại' : 'Feature is being rebuilt');
  };

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
    if (!systemGdriveConfig.service_account_json || !systemGdriveConfig.folder_id) {
      toast.error(language === 'vi' ? 'Vui lòng điền đầy đủ thông tin!' : 'Please fill in all required information!');
      return;
    }

    // Clean and validate folder ID
    const cleanFolderId = systemGdriveConfig.folder_id.trim();
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
        ...systemGdriveConfig,
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
      setAiConfig({
        provider: response.data.provider || 'openai',
        model: response.data.model || 'gpt-4o', 
        api_key: response.data.api_key || ''
      });
    } catch (error) {
      console.error('Failed to fetch AI config:', error);
      setAiConfig({ provider: 'openai', model: 'gpt-4o', api_key: '' });
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
    const authMethod = systemGdriveConfig.auth_method || 'apps_script';
    
    let missingFields = false;
    if (authMethod === 'apps_script') {
      if (!systemGdriveConfig.web_app_url || !systemGdriveConfig.folder_id) {
        missingFields = true;
      }
    } else if (authMethod === 'oauth') {
      if (!systemGdriveConfig.client_id || !systemGdriveConfig.client_secret || !systemGdriveConfig.folder_id) {
        missingFields = true;
      }
    } else if (authMethod === 'service_account') {
      if (!systemGdriveConfig.service_account_json || !systemGdriveConfig.folder_id) {
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
          web_app_url: systemGdriveConfig.web_app_url,
          folder_id: systemGdriveConfig.folder_id
        };
      } else if (authMethod === 'oauth') {
        endpoint = '/gdrive/oauth/authorize';
        payload = {
          client_id: systemGdriveConfig.client_id,
          client_secret: systemGdriveConfig.client_secret,
          redirect_uri: 'https://fleetops-7.preview.emergentagent.com/oauth2callback',
          folder_id: systemGdriveConfig.folder_id
        };
      } else {
        endpoint = '/gdrive/configure';
        payload = {
          service_account_json: systemGdriveConfig.service_account_json,
          folder_id: systemGdriveConfig.folder_id
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
          setSystemGdriveConfig(prev => ({ ...prev, web_app_url: '', folder_id: '' }));
        } else if (authMethod === 'oauth') {
          setSystemGdriveConfig(prev => ({ ...prev, client_id: '', client_secret: '', folder_id: '' }));
        } else {
          setSystemGdriveConfig(prev => ({ ...prev, service_account_json: '', folder_id: '' }));
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

  const toggleSystemGoogleDriveModal = () => {
    setShowGoogleDrive(!showGoogleDrive);
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
          redirect_uri: 'https://fleetops-7.preview.emergentagent.com/oauth2callback',
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
      await axios.delete(`${API}/companies/${company.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      toast.success(language === 'vi' ? 'Công ty đã được xóa thành công!' : 'Company deleted successfully!');
      fetchCompanies();
    } catch (error) {
      console.error('Delete company error:', error);
      const errorMessage = error.response?.data?.detail || 
        (language === 'vi' ? 'Không thể xóa công ty!' : 'Failed to delete company!');
      toast.error(errorMessage);
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
        <div className="w-full px-4 py-4">
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

      <div className="w-full px-4 py-8">
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
                      (gdriveStatus?.status === 'connected' || gdriveCurrentConfig?.configured) ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {(gdriveStatus?.status === 'connected' || gdriveCurrentConfig?.configured) ? 
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
                {(gdriveStatus?.status === 'connected' || gdriveCurrentConfig?.configured) && (
                  <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
                    <h4 className="font-medium text-blue-800 mb-2">
                      {language === 'vi' ? 'Trạng thái đồng bộ' : 'Sync Status'}
                    </h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">{gdriveStatus?.local_files || 0}</div>
                        <div className="text-gray-600">{language === 'vi' ? 'Files local' : 'Local files'}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">{gdriveStatus?.drive_files || 0}</div>
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
                
                {(gdriveStatus?.status === 'connected' || gdriveCurrentConfig?.configured) && (
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
            config={systemGdriveConfig}
            setConfig={setSystemGdriveConfig}
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

      {/* Duplicate Certificate Modal */}
      {duplicateModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="mb-6">
              <h3 className="text-xl font-bold text-red-600 mb-2">
                ⚠️ {language === 'vi' ? 'Phát hiện giấy chứng nhận trùng lặp' : 'Duplicate Certificate Detected'}
              </h3>
              <p className="text-gray-600">
                {language === 'vi' 
                  ? `File "${duplicateModal.currentFile}" có dữ liệu hoàn toàn trùng lặp với giấy chứng nhận đã có:`
                  : `File "${duplicateModal.currentFile}" has identical data with existing certificate:`}
              </p>
            </div>

            {/* Show duplicate certificates */}
            <div className="mb-6 max-h-60 overflow-y-auto">
              {duplicateModal.duplicates.map((duplicate, index) => (
                <div key={index} className="border rounded-lg p-4 mb-3 bg-yellow-50">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-semibold text-gray-800">
                      {duplicate.certificate.cert_name}
                    </h4>
                    <span className="text-sm font-medium text-red-600">
                      {duplicate.similarity.toFixed(1)}% {language === 'vi' ? 'trùng lặp' : 'similar'}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                    <div><strong>{language === 'vi' ? 'Số' : 'No'}:</strong> {duplicate.certificate.cert_no}</div>
                    <div><strong>{language === 'vi' ? 'Loại' : 'Type'}:</strong> {duplicate.certificate.cert_type}</div>
                    <div><strong>{language === 'vi' ? 'Ngày cấp' : 'Issue'}:</strong> {formatDate(duplicate.certificate.issue_date)}</div>
                    <div><strong>{language === 'vi' ? 'Hết hạn' : 'Valid'}:</strong> {formatDate(duplicate.certificate.valid_date)}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-4">
              <button
                onClick={() => handleLocalDuplicateResolution('overwrite')}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-3 rounded-lg transition-colors font-medium"
              >
                {language === 'vi' 
                  ? '🔄 Ghi đè lên dữ liệu đang có' 
                  : '🔄 Overwrite existing data'}
              </button>
              
              <button
                onClick={() => handleLocalDuplicateResolution('cancel')}
                className="flex-1 bg-gray-500 hover:bg-gray-600 text-white px-4 py-3 rounded-lg transition-colors font-medium"
              >
                {language === 'vi' 
                  ? '❌ Hủy bỏ việc thêm giấy chứng nhận' 
                  : '❌ Cancel certificate upload'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Ship Name Mismatch Modal */}
      {mismatchModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full mx-4">
            <div className="mb-6">
              <h3 className="text-xl font-bold text-orange-600 mb-2">
                ⚠️ {language === 'vi' ? 'Tên tàu không khớp' : 'Ship Name Mismatch'}
              </h3>
              <p className="text-gray-600">
                {language === 'vi' 
                  ? 'AI phát hiện tên tàu trong giấy chứng nhận khác với tàu đang được chọn:'
                  : 'AI detected ship name in the certificate differs from currently selected ship:'}
              </p>
            </div>

            <div className="bg-blue-50 rounded-lg p-4 mb-6">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <strong className="text-blue-700">{language === 'vi' ? 'Tàu đang chọn:' : 'Current Ship:'}</strong>
                  <p className="text-gray-700 font-medium mt-1">{mismatchModal.mismatchInfo?.current_ship_name}</p>
                </div>
                <div>
                  <strong className="text-orange-700">{language === 'vi' ? 'Tàu từ AI:' : 'AI Detected Ship:'}</strong>
                  <p className="text-gray-700 font-medium mt-1">{mismatchModal.mismatchInfo?.ai_ship_name}</p>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <button
                onClick={() => handleMismatchResolution('use_ai_ship')}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-lg transition-colors font-medium text-left"
                disabled={!mismatchModal.mismatchInfo?.ai_ship_exists}
              >
                <div className="flex items-center justify-between">
                  <span>
                    {language === 'vi' 
                      ? `🚢 Lưu vào database của tàu "${mismatchModal.mismatchInfo?.ai_ship_name}"` 
                      : `🚢 Save to "${mismatchModal.mismatchInfo?.ai_ship_name}" database`}
                  </span>
                  {!mismatchModal.mismatchInfo?.ai_ship_exists && (
                    <span className="text-xs bg-red-500 px-2 py-1 rounded">
                      {language === 'vi' ? 'Tàu không tồn tại' : 'Ship not found'}
                    </span>
                  )}
                </div>
              </button>
              
              <button
                onClick={() => handleMismatchResolution('use_current_ship')}
                className="w-full bg-orange-600 hover:bg-orange-700 text-white px-4 py-3 rounded-lg transition-colors font-medium text-left"
              >
                {language === 'vi' 
                  ? `📋 Lưu vào tàu "${mismatchModal.mismatchInfo?.current_ship_name}" kèm ghi chú tham khảo` 
                  : `📋 Save to "${mismatchModal.mismatchInfo?.current_ship_name}" with reference note`}
              </button>
            </div>
            
            <div className="mt-4 text-center">
              <p className="text-xs text-gray-500">
                {language === 'vi' 
                  ? 'Chọn tùy chọn thứ 2 sẽ thêm ghi chú: "Giấy chứng nhận này để tham khảo, không phải của tàu này"'
                  : 'Option 2 will add note: "This certificate is for reference, not belonging to this ship"'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Duplicate resolution is handled at main component level */}
      </div>
    </div>
  );
};

// Google Drive Configuration Modal Component
const GoogleDriveModal = ({ config, setConfig, currentConfig, onClose, onSave, onTest, testLoading, language }) => {
  const [authMethod, setAuthMethod] = useState('apps_script'); // Force apps_script as default
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
        redirect_uri: 'https://fleetops-7.preview.emergentagent.com/oauth2callback',
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
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[99999]" 
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
                  <li>3. {language === 'vi' ? 'Thêm Authorized redirect URI:' : 'Add Authorized redirect URI:'} <code>https://fleetops-7.preview.emergentagent.com/oauth2callback</code></li>
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
  const [authMethod, setAuthMethod] = useState('apps_script'); // Force apps_script as default
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
        redirect_uri: 'https://fleetops-7.preview.emergentagent.com/oauth2callback',
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
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[99999]" 
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
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]" 
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
    { value: 'google', label: 'Google', models: ['gemini-pro', 'gemini-pro-vision'] },
    { value: 'emergent', label: 'Emergent LLM', models: ['gemini-2.0-flash', 'gpt-4o', 'claude-3-sonnet'] }
  ];

  const selectedProvider = providers.find(p => p.value === config.provider);

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]" 
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

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'vi' ? 'Cấu hình API Key' : 'API Key Configuration'}
            </label>
            
            <div className="space-y-3">
              {/* Option 1: Use Emergent LLM Key */}
              <div className="flex items-center p-3 border border-green-200 rounded-lg bg-green-50">
                <input
                  type="radio"
                  id="use-emergent-key"
                  name="api-key-option"
                  checked={config.use_emergent_key !== false}
                  onChange={() => setConfig(prev => ({ 
                    ...prev, 
                    use_emergent_key: true, 
                    api_key: 'EMERGENT_LLM_KEY' 
                  }))}
                  className="mr-3"
                />
                <div className="flex-1">
                  <label htmlFor="use-emergent-key" className="text-sm font-medium text-green-800 cursor-pointer">
                    ✨ {language === 'vi' ? 'Sử dụng Emergent LLM Key (Khuyến nghị)' : 'Use Emergent LLM Key (Recommended)'}
                  </label>
                  <p className="text-xs text-green-600 mt-1">
                    {language === 'vi' 
                      ? 'Miễn phí sử dụng với tất cả models. Không cần nhập API key riêng.'
                      : 'Free to use with all models. No need to enter your own API key.'
                    }
                  </p>
                </div>
              </div>

              {/* Option 2: Use Custom API Key */}
              <div className="flex items-start p-3 border border-gray-200 rounded-lg">
                <input
                  type="radio"
                  id="use-custom-key"
                  name="api-key-option"
                  checked={config.use_emergent_key === false}
                  onChange={() => setConfig(prev => ({ 
                    ...prev, 
                    use_emergent_key: false, 
                    api_key: '' 
                  }))}
                  className="mr-3 mt-1"
                />
                <div className="flex-1">
                  <label htmlFor="use-custom-key" className="text-sm font-medium text-gray-700 cursor-pointer">
                    🔑 {language === 'vi' ? 'Sử dụng API Key riêng' : 'Use Custom API Key'}
                  </label>
                  <p className="text-xs text-gray-500 mb-2">
                    {language === 'vi' 
                      ? 'Nhập API key từ OpenAI, Anthropic, hoặc Google'
                      : 'Enter your API key from OpenAI, Anthropic, or Google'
                    }
                  </p>
                  
                  {config.use_emergent_key === false && (
                    <input
                      type="password"
                      value={config.api_key || ''}
                      onChange={(e) => setConfig(prev => ({ ...prev, api_key: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      placeholder={language === 'vi' ? 'Nhập API key của bạn' : 'Enter your API key'}
                      required
                    />
                  )}
                </div>
              </div>
            </div>
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
            onClick={() => {
              // Validate based on selected option
              if (config.use_emergent_key === false && (!config.api_key || config.api_key.trim() === '')) {
                alert(language === 'vi' ? 'Vui lòng nhập API key' : 'Please enter API key');
                return;
              }
              onSave();
            }}
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
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]" 
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-6xl w-full max-h-[95vh] overflow-y-auto mx-4">
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
            {companyGdriveCurrentConfig && companyGdriveCurrentConfig.config && 
             companyGdriveCurrentConfig.config.web_app_url && companyGdriveCurrentConfig.config.folder_id && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <h4 className="font-medium text-green-800 mb-2">
                  {language === 'vi' ? 'Cấu hình hiện tại:' : 'Current Configuration:'}
                </h4>
                <div className="text-sm text-green-700 space-y-1">
                  <div><strong>{language === 'vi' ? 'Phương thức:' : 'Auth Method:'}</strong> {
                    companyGdriveCurrentConfig.config.auth_method === 'apps_script' 
                      ? 'Apps Script' 
                      : companyGdriveCurrentConfig.config.auth_method === 'oauth' 
                        ? 'OAuth 2.0' 
                        : 'Service Account'
                  }</div>
                  <div><strong>{language === 'vi' ? 'Folder ID:' : 'Folder ID:'}</strong> {companyGdriveCurrentConfig.config.folder_id}</div>
                  <div><strong>{language === 'vi' ? 'Web App URL:' : 'Web App URL:'}</strong> {companyGdriveCurrentConfig.config.web_app_url}</div>
                  {companyGdriveCurrentConfig.config.service_account_email && (
                    <div><strong>{language === 'vi' ? 'Account Email:' : 'Account Email:'}</strong> {companyGdriveCurrentConfig.config.service_account_email}</div>
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
                (companyGdriveCurrentConfig?.config?.web_app_url && companyGdriveCurrentConfig?.config?.folder_id)
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {(companyGdriveCurrentConfig?.config?.web_app_url && companyGdriveCurrentConfig?.config?.folder_id)
                  ? (language === 'vi' ? 'Đã cấu hình' : 'Configured')
                  : (language === 'vi' ? 'Chưa cấu hình' : 'Not configured')
                }
              </div>
              
              {(companyGdriveCurrentConfig?.config?.web_app_url && companyGdriveCurrentConfig?.config?.folder_id) && (
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
    inspection_records: language === 'vi' ? 'Hồ sơ Đăng kiểm' : 'Class Survey Report',
    survey_reports: language === 'vi' ? 'Báo cáo kiểm tra' : 'Test Report',
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
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]" 
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-6xl w-full max-h-[95vh] overflow-y-auto mx-4">
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
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]" 
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-6xl w-full max-h-[95vh] overflow-y-auto mx-4">
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
const AddRecordModal = ({ 
  onClose, 
  onSuccess, 
  language, 
  selectedShip, 
  availableCompanies, 
  ships, 
  parentAiConfig,
  isMultiCertProcessing,
  multiCertUploads,
  handleMultiCertUpload,
  uploadSummary,
  setMultiCertUploads,
  setUploadSummary,
  handleUploadToFolder,
  handleSkipFile,
  defaultTab,
  // File Viewer Modal props
  showFileViewer,
  setShowFileViewer,
  fileViewerData,
  setFileViewerData,
  pendingManualReviews,
  handleManualReviewAction,
  duplicateResolutionModal,
  handleDuplicateResolution,
  setIsMultiCertProcessing
}) => {
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
  const { user, token } = useAuth();
  
  
  const [recordType, setRecordType] = useState(() => {
    // Use defaultTab if provided, otherwise use role-based logic
    if (defaultTab) {
      return defaultTab;
    }
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
  
  // Certificate file upload states for AddRecordModal  
  const [certificateFile, setCertificateFile] = useState(null);
  const [isCertificateAnalyzing, setIsCertificateAnalyzing] = useState(false);

  // Handle certificate file upload and auto-fill
  const handleCertificateFileUpload = async (file) => {
    try {
      if (!file) return;
      
      setCertificateFile(file);
      setIsCertificateAnalyzing(true);
      
      // Prepare form data for analysis
      const formData = new FormData();
      formData.append('files', file);
      
      if (!selectedShip?.id) {
        toast.error(language === 'vi' 
          ? '❌ Vui lòng chọn tàu trước khi upload certificate'
          : '❌ Please select a ship before uploading certificate'
        );
        setIsCertificateAnalyzing(false);
        return;
      }
      
      // Use multi-upload endpoint for certificate analysis
      const response = await axios.post(`${API}/certificates/multi-upload?ship_id=${selectedShip.id}`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data && response.data.results && response.data.results.length > 0) {
        const result = response.data.results[0];
        
        if (result.status === 'success' && result.analysis) {
          // Auto-fill certificate form with analysis data
          console.log('🎯 Certificate analysis successful:', result.analysis);
          
          // Map analysis data to certificate form fields
          const analysisData = result.analysis;
          const autoFillData = {
            cert_name: analysisData.cert_name || analysisData.certificate_name || '',
            cert_no: analysisData.cert_no || analysisData.certificate_number || '',
            issue_date: analysisData.issue_date || '',
            valid_date: analysisData.valid_date || analysisData.expiry_date || '',
            issued_by: analysisData.issued_by || '',
            ship_id: selectedShip.id,
            category: 'certificates',
            sensitivity_level: 'internal'
          };
          
          // Filter out empty values
          const filledFields = Object.keys(autoFillData).filter(key => 
            autoFillData[key] && String(autoFillData[key]).trim()
          ).length;
          
          console.log('📋 Auto-filling certificate form with', filledFields, 'fields');
          
          // Update certificate form data - CRITICAL FIX
          setCertificateData(prev => ({
            ...prev,
            ...autoFillData
          }));
          
          // Show success message
          toast.success(language === 'vi' 
            ? `✅ Phân tích certificate thành công! Đã điền ${filledFields} trường thông tin.`
            : `✅ Certificate analysis successful! Auto-filled ${filledFields} fields.`
          );
          
        } else if (result.status === 'error') {
          toast.error(language === 'vi' 
            ? `❌ Lỗi phân tích certificate: ${result.message}`
            : `❌ Certificate analysis error: ${result.message}`
          );
        } else {
          toast.warning(language === 'vi' 
            ? '⚠️ Không thể trích xuất đầy đủ thông tin từ certificate'
            : '⚠️ Could not extract complete information from certificate'
          );
        }
      } else {
        toast.error(language === 'vi' 
          ? '❌ Không nhận được phản hồi từ server'
          : '❌ No response received from server'
        );
      }
      
    } catch (error) {
      console.error('Certificate analysis error:', error);
      toast.error(language === 'vi' 
        ? `❌ Lỗi phân tích certificate: ${error.response?.data?.detail || error.message}`
        : `❌ Certificate analysis error: ${error.response?.data?.detail || error.message}`
      );
    } finally {
      setIsCertificateAnalyzing(false);
    }
  };
  const [aiConfig, setAiConfig] = useState(null);
  const [showShipConfirmModal, setShowShipConfirmModal] = useState(false);
  const [pendingShipData, setPendingShipData] = useState(null);
  const [documentData, setDocumentData] = useState({
    title: '',
    category: 'other_documents',
    description: '',
    file: null
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  // Duplicate and mismatch modal states for AddRecordModal
  const [duplicateModal, setDuplicateModal] = useState({
    show: false,
    duplicates: [],
    currentFile: null,
    analysisResult: null,
    uploadResult: null,
    status: 'all'
  });
  const [mismatchModal, setMismatchModal] = useState({
    show: false,
    mismatchInfo: null,
    analysisResult: null,
    uploadResult: null
  });

  // Check if user can create ships (Company Officer role and above)
  const canCreateShip = () => {
    const allowedRoles = ['manager', 'admin', 'super_admin'];
    return allowedRoles.includes(user?.role);
  };
  // Multi-file upload functions will be rebuilt from scratch
  const handleLocalDuplicateResolution = (action) => {
    toast.info(language === 'vi' ? 'Chức năng đang được xây dựng lại' : 'Feature is being rebuilt');
  };

  const handleMismatchResolution = (action) => {
    toast.info(language === 'vi' ? 'Chức năng đang được xây dựng lại' : 'Feature is being rebuilt');
  };

  // Helper function to format date from DD/MM/YYYY to YYYY-MM-DD for HTML date inputs
  const convertLastDockingToDateTime = (mmYyyyString) => {
    if (!mmYyyyString || typeof mmYyyyString !== 'string') return null;
    
    try {
      // Handle MM/YYYY format (convert to first day of the month)
      const mmYyyyPattern = /^\d{1,2}\/\d{4}$/;
      if (mmYyyyPattern.test(mmYyyyString.trim())) {
        const [month, year] = mmYyyyString.trim().split('/');
        const paddedMonth = month.padStart(2, '0');
        // Convert to ISO datetime (first day of the month)
        return `${year}-${paddedMonth}-01T00:00:00Z`;
      }
      
      // If it's already a full date format, return as is
      if (mmYyyyString.includes('-') || mmYyyyString.includes('T')) {
        return mmYyyyString;
      }
      
      // If it's DD/MM/YYYY format, convert to ISO
      const ddMmYyyyPattern = /^\d{1,2}\/\d{1,2}\/\d{4}$/;
      if (ddMmYyyyPattern.test(mmYyyyString.trim())) {
        const [day, month, year] = mmYyyyString.trim().split('/');
        const paddedDay = day.padStart(2, '0');
        const paddedMonth = month.padStart(2, '0');
        return `${year}-${paddedMonth}-${paddedDay}T00:00:00Z`;
      }
      
      return null;
    } catch (error) {
      console.error('Error converting last docking date:', error);
      return null;
    }
  };

  const formatLastDockingForDisplay = (dateString) => {
    if (!dateString || typeof dateString !== 'string') return '';
    
    try {
      // Check if it's month/year only format (like "NOV 2020", "DEC. 2022")
      const monthYearPattern = /^[A-Z]{3,4}\.?\s+\d{4}$/i;
      if (monthYearPattern.test(dateString.trim())) {
        // Convert month name to number
        const parts = dateString.trim().split(/\s+/);
        const monthName = parts[0].replace('.', '').toUpperCase();
        const year = parts[1];
        
        const monthMap = {
          'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
          'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        };
        
        if (monthMap[monthName]) {
          return `${monthMap[monthName]}/${year}`;
        }
      }
      
      // Check if it's MM/YYYY format - return as is
      const mmYyyyPattern = /^\d{1,2}\/\d{4}$/;
      if (mmYyyyPattern.test(dateString.trim())) {
        const [month, year] = dateString.split('/');
        const paddedMonth = month.padStart(2, '0');
        return `${paddedMonth}/${year}`;
      }
      
      // If it's a full date (DD/MM/YYYY or ISO format), convert to MM/YYYY
      if (dateString.includes('/')) {
        const parts = dateString.split('/');
        if (parts.length === 3) {
          const [day, month, year] = parts;
          if (year && year.length === 4) {
            const paddedMonth = month.padStart(2, '0');
            return `${paddedMonth}/${year}`;
          }
        }
      }
      
      // Handle ISO date format
      const date = new Date(dateString);
      if (!isNaN(date.getTime())) {
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const year = date.getFullYear();
        return `${month}/${year}`;
      }
      
      return dateString; // Return as is if cannot parse
    } catch (error) {
      console.error('Error formatting last docking date:', error);
      return dateString;
    }
  };

  const formatDateForInput = (dateString) => {
    if (!dateString || typeof dateString !== 'string') return '';
    
    try {
      // Handle DD/MM/YYYY format (from AI extraction)
      if (dateString.includes('/')) {
        const parts = dateString.split('/');
        if (parts.length === 3) {
          const [day, month, year] = parts;
          // Validate parts
          if (day && month && year && year.length === 4) {
            const paddedDay = day.padStart(2, '0');
            const paddedMonth = month.padStart(2, '0');
            return `${year}-${paddedMonth}-${paddedDay}`;
          }
        }
      }
      
      // Handle other date formats or ISO dates
      const date = new Date(dateString);
      if (!isNaN(date.getTime())) {
        return date.toISOString().split('T')[0];
      }
      
      return '';
    } catch (error) {
      console.warn('Date formatting error:', error, 'for date:', dateString);
      return '';
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

      const response = await axios.post(`${API}/analyze-ship-certificate`, formData, {
        headers: {
          // Content-Type is automatically set by axios for FormData with proper boundary
        }
      });

      if (response.data.success) {
        // Debug: Log the complete response structure
        console.log('=== PDF ANALYSIS RESPONSE ===');
        console.log('Full response:', response);
        console.log('Response data:', response.data);
        console.log('Analysis data:', response.data.analysis);
        console.log('============================');
        
        // Check if analysis contains error information
        const analysisData = response.data.analysis || {};
        if (analysisData?.error) {
          toast.error(language === 'vi' 
            ? `❌ Phân tích thất bại: ${analysisData.error}`
            : `❌ Analysis failed: ${analysisData.error}`
          );
          return;
        }
        
        // Check if we have meaningful extracted data - RELAXED VALIDATION
        const validFields = Object.keys(analysisData).filter(key => {
          const value = analysisData[key];
          return value && 
                 String(value).trim() && 
                 String(value).toLowerCase() !== 'null' &&
                 String(value).toLowerCase() !== 'undefined' &&
                 !['confidence', 'processing_notes', 'error', 'processing_method', 'engine_used'].includes(key);
        });
        
        console.log('📊 Valid extracted fields:', validFields);
        console.log('📊 Analysis data:', analysisData);
        
        if (validFields.length === 0) {
          toast.warning(language === 'vi' 
            ? '⚠️ Không thể trích xuất thông tin từ PDF. Vui lòng nhập thủ công.'
            : '⚠️ Could not extract information from PDF. Please enter manually.'
          );
          return;
        }
        
        // Auto-fill ship data with extracted information - FORCE UPDATE
        console.log('📋 Processing extracted data for auto-fill');
        
        // Convert extracted data to match frontend form field names
        // Enhanced to support ALL Ship Creation Form fields
        const processedData = {
          // Basic Information Section (original fields)
          name: analysisData.ship_name || '', 
          imo_number: analysisData.imo_number || '',
          class_society: analysisData.class_society || '', 
          flag: analysisData.flag || '',
          gross_tonnage: analysisData.gross_tonnage ? String(analysisData.gross_tonnage) : '',
          deadweight: analysisData.deadweight ? String(analysisData.deadweight) : '',
          built_year: analysisData.built_year ? String(analysisData.built_year) : '',
          delivery_date: formatDateForInput(analysisData.delivery_date) || '',
          keel_laid: formatDateForInput(analysisData.keel_laid) || '',
          ship_owner: analysisData.ship_owner || '',
          
          // Survey & Maintenance Information Section (NEW fields from enhanced extraction)
          last_docking: formatLastDockingForDisplay(analysisData.last_docking) || '',
          last_docking_2: formatLastDockingForDisplay(analysisData.last_docking_2) || '', 
          next_docking: formatDateForInput(analysisData.next_docking) || '',
          last_special_survey: formatDateForInput(analysisData.last_special_survey) || '',
          last_intermediate_survey: formatDateForInput(analysisData.last_intermediate_survey) || '',
          
          // Anniversary Date & Special Survey Cycle (NEW fields)
          anniversary_date_day: analysisData.anniversary_date_day ? String(analysisData.anniversary_date_day) : '',
          anniversary_date_month: analysisData.anniversary_date_month ? String(analysisData.anniversary_date_month) : '',
          special_survey_from_date: formatDateForInput(analysisData.special_survey_from_date) || '',
          special_survey_to_date: formatDateForInput(analysisData.special_survey_to_date) || ''
        };
        
        console.log('📝 Processed data for form:', processedData);
        
        // Count how many fields we're actually filling
        const filledFields = Object.keys(processedData).filter(key => 
          processedData[key] && processedData[key].trim()
        ).length;
        
        console.log('🔢 Number of fields to fill:', filledFields);
        
        if (filledFields === 0) {
          toast.warning(language === 'vi' 
            ? '⚠️ PDF được phân tích nhưng không tìm thấy thông tin tàu phù hợp'
            : '⚠️ PDF analyzed but no suitable ship information found'
          );
          return;
        }
        
        // FORCE UPDATE: Use functional update and force re-render
        console.log('🔄 FORCING form data update...');
        setShipData(prev => {
          const updatedData = {
            ...prev,
            ...processedData
          };
          console.log('📤 Previous data:', prev);
          console.log('📥 Updated data:', updatedData);
          
          // Force a timeout to ensure state update
          setTimeout(() => {
            console.log('⏰ Checking if form updated after timeout...');
          }, 100);
          
          return updatedData;
        });
        
        // Show success message IMMEDIATELY
        toast.success(language === 'vi' 
          ? `✅ Phân tích PDF thành công! Đã điền ${filledFields} trường thông tin tàu.`
          : `✅ PDF analysis completed! Auto-filled ${filledFields} ship information fields.`
        );
        
        // Show processing notes if available
        if (analysisData.processing_notes && analysisData.processing_notes.length > 0) {
          console.log('📋 Processing notes:', analysisData.processing_notes);
        }
        
        // Close modal after longer delay to show auto-filled data
        setTimeout(() => {
          console.log('🚪 Closing PDF analysis modal...');
          setShowPdfAnalysis(false);
        }, 2000);
        
      } else {
        // Handle API failure
        const errorMessage = response.data.message || response.data.error || 'Unknown error';
        console.error('❌ PDF analysis failed:', errorMessage);
        
        toast.error(language === 'vi' 
          ? `❌ Phân tích PDF thất bại: ${errorMessage}`
          : `❌ PDF analysis failed: ${errorMessage}`
        );
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
        deadweight: shipData.deadweight ? parseFloat(shipData.deadweight) : null,
        year_built: shipData.built_year ? parseInt(shipData.built_year) : null,
        delivery_date: shipData.delivery_date || null,
        keel_laid: shipData.keel_laid || null,
        // Convert Last Docking MM/YYYY format to datetime for backend
        last_docking: convertLastDockingToDateTime(shipData.last_docking),
        last_docking_2: convertLastDockingToDateTime(shipData.last_docking_2),
        next_docking: shipData.next_docking || null,
        last_special_survey: shipData.last_special_survey || null,
        last_intermediate_survey: shipData.last_intermediate_survey || null,
        ship_owner: shipData.ship_owner?.trim() || '',
        company: shipData.company?.trim() || user?.company || ''
      };

      // Add Anniversary Date if provided
      if (shipData.anniversary_date_day && shipData.anniversary_date_month) {
        shipPayload.anniversary_date = {
          day: parseInt(shipData.anniversary_date_day),
          month: parseInt(shipData.anniversary_date_month),
          manual_override: true,
          auto_calculated: false,
          source_certificate_type: "Manual Entry"
        };
      }

      // Add Special Survey Cycle if provided
      if (shipData.special_survey_from_date && shipData.special_survey_to_date) {
        shipPayload.special_survey_cycle = {
          from_date: shipData.special_survey_from_date,
          to_date: shipData.special_survey_to_date,
          cycle_type: "IMO 5-year Standard",
          manual_override: true,
          auto_calculated: false
        };
      }
      
      // Remove null values to avoid database constraint issues
      Object.keys(shipPayload).forEach(key => {
        if (shipPayload[key] === null || shipPayload[key] === '') {
          if (key === 'imo') {
            delete shipPayload[key]; // Remove IMO entirely if empty
          } else if (['gross_tonnage', 'deadweight', 'year_built', 'delivery_date', 'keel_laid', 'last_docking', 'last_docking_2', 'next_docking', 'last_special_survey', 'last_intermediate_survey'].includes(key)) {
            delete shipPayload[key]; // Remove optional numeric/date fields if empty
          }
        }
      });
      
      console.log('Ship payload:', shipPayload); // Debug log
      
      const response = await axios.post(`${API}/ships`, shipPayload);
      const createdShip = response.data;
      
      // Show initial success message and close modal immediately
      toast.success(language === 'vi' ? '🚢 Tàu đã được thêm thành công vào database!' : '🚢 Ship added to database successfully!');
      
      // Close modal immediately after ship creation
      onSuccess('ship');
      
      // Start polling for Google Drive folder creation status
      if (createdShip.id) {
        toast.info(language === 'vi' ? '📁 Đang tạo folder structure trên Google Drive...' : '📁 Creating folder structure on Google Drive...');
        startGoogleDriveFolderPolling(createdShip.id, createdShip.name);
      }
    } catch (error) {
      console.error('Ship creation error:', error);
      
      // Enhanced error message handling
      let errorMessage = 'Unknown error occurred';
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        // Handle FastAPI validation errors (array of error objects)
        if (Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map(err => {
            if (typeof err === 'object' && err.msg) {
              const field = Array.isArray(err.loc) ? err.loc.join('.') : 'field';
              return `${field}: ${err.msg}`;
            }
            return String(err);
          });
          errorMessage = errorMessages.join(', ');
        } 
        // Handle single error message
        else if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        }
        // Handle error objects
        else if (typeof errorData.detail === 'object') {
          errorMessage = JSON.stringify(errorData.detail);
        }
        // Handle other error formats
        else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(language === 'vi' ? `Không thể thêm tàu: ${errorMessage}` : `Failed to add ship: ${errorMessage}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitCertificate = async () => {
    try {
      setIsSubmitting(true);
      
      // Submit certificate metadata only
      const certPayload = {
        ...certificateData,
        ship_id: selectedShip?.id || '',
        issue_date: new Date(certificateData.issue_date).toISOString(),
        valid_date: new Date(certificateData.valid_date).toISOString(),
        last_endorse: certificateData.last_endorse ? new Date(certificateData.last_endorse).toISOString() : null,
        next_survey: certificateData.next_survey ? new Date(certificateData.next_survey).toISOString() : null
      };
      
      const response = await axios.post(`${API}/certificates`, certPayload);
      toast.success(language === 'vi' ? 'Chứng chỉ đã được thêm thành công!' : 'Certificate added successfully!');
      
      onSuccess('certificate');
    } catch (error) {
      console.error('Certificate creation error:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      
      toast.error(language === 'vi' 
        ? `Không thể tạo chứng chỉ: ${errorMessage}` 
        : `Failed to create certificate: ${errorMessage}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const checkShipExistence = (shipName) => {
    if (!shipName || shipName === 'Unknown_Ship') return false;
    
    // Check if ship exists in current ships list
    return ships.some(ship => 
      ship.name.toLowerCase().includes(shipName.toLowerCase()) ||
      shipName.toLowerCase().includes(ship.name.toLowerCase())
    );
  };

  const handleShipNotFound = (extractedShipName, fileData) => {
    setPendingShipData({
      shipName: extractedShipName,
      fileData: fileData,
      extractedInfo: fileData.extracted_info
    });
    setShowShipConfirmModal(true);
  };

  const handleShipConfirmation = async (createNewShip) => {
    if (createNewShip && pendingShipData) {
      // Close modal first
      setShowShipConfirmModal(false);
      
      // Switch to Ship tab and use Add Ship from Certificate
      setRecordType('ship');
      setShowPdfAnalysis(true);
      
      // Auto-fill ship data from extracted info
      const extractedInfo = pendingShipData.extractedInfo;
      setShipData({
        name: pendingShipData.shipName,
        imo: extractedInfo?.imo_number || '',
        ship_type: extractedInfo?.class_society || '',
        flag: extractedInfo?.flag || '',
        gross_tonnage: extractedInfo?.gross_tonnage || '',
        deadweight: extractedInfo?.deadweight || '',
        year_built: extractedInfo?.built_year || '',
        ship_owner: extractedInfo?.ship_owner || '',
        company: user?.company || ''
      });
      
      toast.success(
        language === 'vi' 
          ? `Chuyển sang tạo tàu mới: ${pendingShipData.shipName}` 
          : `Switching to create new ship: ${pendingShipData.shipName}`
      );
    } else {
      // Cancel - just close modal
      setShowShipConfirmModal(false);
      toast.info(
        language === 'vi' 
          ? 'Đã hủy thêm certificate' 
          : 'Certificate addition cancelled'
      );
    }
    
    // Clear pending data
    setPendingShipData(null);
  };

  // Complete Ship Folder Structure Extraction from Homepage Sidebar
  const getCompleteShipFolderStructure = () => {
    try {
      // Extract complete structure from homepage sidebar (line 990-1032)
      const currentCategories = [
        { key: 'documents', name: 'Document Portfolio', icon: '📁' },
        { key: 'crew', name: 'Crew Records', icon: '👥' },
        { key: 'ism', name: 'ISM Records', icon: '📋' },
        { key: 'isps', name: 'ISPS Records', icon: '🛡️' },
        { key: 'mlc', name: 'MLC Records', icon: '⚖️' },
        { key: 'supplies', name: 'Supplies', icon: '📦' },
      ];
      
      const currentSubMenuItems = {
        documents: [
          { key: 'certificates', name: 'Certificates' },
          { key: 'inspection_records', name: 'Class Survey Report' },
          { key: 'survey_reports', name: 'Test Report' },
          { key: 'drawings_manuals', name: 'Drawings & Manuals' },
          { key: 'other_documents', name: 'Other Documents' },
        ],
        crew: [
          { key: 'crew_list', name: 'Crew List' },
          { key: 'crew_certificates', name: 'Crew Certificates' },
          { key: 'medical_records', name: 'Medical Records' },
        ],
        ism: [
          { key: 'ism_certificate', name: 'ISM Certificate' },
          { key: 'safety_procedures', name: 'Safety Procedures' },
          { key: 'audit_reports', name: 'Audit Reports' },
        ],
        isps: [
          { key: 'isps_certificate', name: 'ISPS Certificate' },
          { key: 'security_plan', name: 'Security Plan' },
          { key: 'security_assessments', name: 'Security Assessments' },
        ],
        mlc: [
          { key: 'mlc_certificate', name: 'MLC Certificate' },
          { key: 'labor_conditions', name: 'Labor Conditions' },
          { key: 'accommodation_reports', name: 'Accommodation Reports' },
        ],
        supplies: [
          { key: 'inventory', name: 'Inventory' },
          { key: 'purchase_orders', name: 'Purchase Orders' },
          { key: 'spare_parts', name: 'Spare Parts' },
        ],
      };
      
      // Build complete folder structure
      const folderStructure = {};
      
      currentCategories.forEach(category => {
        const categoryName = category.name; // Use English names for consistency
        const subfolders = currentSubMenuItems[category.key]?.map(item => item.name) || [];
        
        folderStructure[categoryName] = subfolders;
      });
      
      console.log('📁 Complete ship folder structure extracted from homepage sidebar:');
      console.log(`   Categories: ${Object.keys(folderStructure).length}`);
      console.log(`   Total subfolders: ${Object.values(folderStructure).flat().length}`);
      Object.entries(folderStructure).forEach(([category, subfolders]) => {
        console.log(`   ${category}: [${subfolders.join(', ')}]`);
      });
      
      return folderStructure;
      
    } catch (error) {
      console.error('Error extracting complete folder structure from homepage sidebar:', error);
      
      // Fallback to minimal structure if extraction fails
      const fallbackStructure = {
        'Document Portfolio': ['Certificates', 'Class Survey Report', 'Test Report', 'Drawings & Manuals', 'Other Documents'],
        'Crew Records': ['Crew List', 'Crew Certificates', 'Medical Records'],
        'ISM Records': ['ISM Certificate', 'Safety Procedures', 'Audit Reports'],
        'ISPS Records': ['ISPS Certificate', 'Security Plan', 'Security Assessments'],
        'MLC Records': ['MLC Certificate', 'Labor Conditions', 'Accommodation Reports'],
        'Supplies': ['Inventory', 'Purchase Orders', 'Spare Parts']
      };
      
      console.warn('⚠️ Using fallback complete folder structure:', fallbackStructure);
      return fallbackStructure;
    }
  };

  // Poll Google Drive folder creation status
  const startGoogleDriveFolderPolling = async (shipId, shipName) => {
    const maxPollingTime = 185000; // 185 seconds (slightly more than backend timeout)
    const pollingInterval = 3000; // 3 seconds
    const startTime = Date.now();
    
    const pollStatus = async () => {
      try {
        const response = await axios.get(`${API}/ships/${shipId}/gdrive-folder-status`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const status = response.data.gdrive_folder_status;
        
        if (status === 'completed') {
          toast.success(language === 'vi' 
            ? `✅ Folder structure cho tàu "${shipName}" đã được tạo thành công trên Google Drive!`
            : `✅ Folder structure for ship "${shipName}" created successfully on Google Drive!`
          );
          return; // Stop polling
        } else if (status === 'failed' || status === 'error') {
          const errorMsg = response.data.gdrive_folder_error || 'Unknown error';
          toast.error(language === 'vi'
            ? `❌ Không thể tạo folder cho tàu "${shipName}": ${errorMsg}`
            : `❌ Failed to create folder for ship "${shipName}": ${errorMsg}`
          );
          return; // Stop polling
        } else if (status === 'timeout') {
          toast.warning(language === 'vi'
            ? `⏰ Tạo folder cho tàu "${shipName}" bị timeout sau 180 giây`
            : `⏰ Folder creation for ship "${shipName}" timed out after 180 seconds`
          );
          return; // Stop polling
        } else if (status === 'pending') {
          // Check if total polling time exceeded
          if (Date.now() - startTime > maxPollingTime) {
            toast.warning(language === 'vi'
              ? `⏰ Hết thời gian chờ tạo folder cho tàu "${shipName}"`
              : `⏰ Polling timeout for folder creation of ship "${shipName}"`
            );
            return; // Stop polling
          }
          // Continue polling
          setTimeout(pollStatus, pollingInterval);
        }
      } catch (error) {
        console.error('Error polling folder status:', error);
        toast.error(language === 'vi'
          ? `❌ Lỗi khi kiểm tra trạng thái folder cho tàu "${shipName}"`
          : `❌ Error checking folder status for ship "${shipName}"`
        );
      }
    };
    
    // Start polling after a short delay
    setTimeout(pollStatus, pollingInterval);
  };

  // Google Drive Ship Folder Creation with Complete Hierarchy Structure
  const createShipGoogleDriveFolder = async (shipName, companyId) => {
    try {
      console.log(`Creating complete Google Drive folder structure for ship: ${shipName}`);
      
      // Get complete folder structure from homepage sidebar
      const folderStructure = getCompleteShipFolderStructure();
      
      // Validate extracted structure
      if (!folderStructure || Object.keys(folderStructure).length === 0) {
        throw new Error('No folder structure found in homepage sidebar');
      }
      
      const totalCategories = Object.keys(folderStructure).length;
      const totalSubfolders = Object.values(folderStructure).flat().length;
      
      console.log(`📋 Using complete structure from homepage sidebar:`);
      console.log(`   Categories: ${totalCategories}`);
      console.log(`   Total subfolders: ${totalSubfolders}`);
      console.log(`🔄 Structure sync: Homepage Sidebar → Google Drive Complete Hierarchy`);
      
      // Call backend to create complete ship folder structure on Company Google Drive
      const response = await axios.post(`${API}/companies/${companyId}/gdrive/create-ship-folder`, {
        ship_name: shipName,
        folder_structure: folderStructure, // Send complete hierarchy
        source: 'homepage_sidebar_complete', // Indicate complete structure source
        total_categories: totalCategories,
        total_subfolders: totalSubfolders
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data.success) {
        console.log(`✅ Complete ship folder structure created successfully:`, response.data);
        toast.success(
          language === 'vi' 
            ? `📁 Đã tạo cấu trúc thư mục hoàn chỉnh "${shipName}" với ${totalCategories} danh mục và ${totalSubfolders} thư mục con`
            : `📁 Created complete "${shipName}" folder structure with ${totalCategories} categories and ${totalSubfolders} subfolders`
        );
        return response.data;
      } else {
        throw new Error(response.data.message || 'Failed to create ship folder structure');
      }
      
    } catch (error) {
      console.error('Error creating ship Google Drive folder structure:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      
      // Show warning but don't fail ship creation
      toast.warning(
        language === 'vi'
          ? `⚠️ Ship đã tạo thành công nhưng không thể tạo cấu trúc thư mục Google Drive: ${errorMessage}`
          : `⚠️ Ship created successfully but failed to create Google Drive folder structure: ${errorMessage}`
      );
      
      return null;
    }
  };

  // handleMultiFileUpload function will be rebuilt from scratch

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
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]" 
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-6xl w-full max-h-[95vh] overflow-y-auto mx-4">
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
          <div className="grid grid-cols-12 gap-4">
            
            {/* Basic Ship Information Section */}
            <div className="col-span-12">
              <h4 className="text-lg font-semibold text-gray-700 mb-3 pb-2 border-b">
                {language === 'vi' ? 'Thông tin cơ bản' : 'Basic Information'}
              </h4>
            </div>
            
            {/* Ship Name - Full width */}
            <div className="col-span-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tên tàu' : 'Ship Name'} *
              </label>
              <input
                type="text"
                required
                value={shipData.name}
                onChange={(e) => setShipData(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder={language === 'vi' ? 'Nhập tên tàu' : 'Enter ship name'}
              />
            </div>

            {/* IMO - Short width */}
            <div className="col-span-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Số IMO' : 'IMO Number'} *
              </label>
              <input
                type="text"
                required
                value={shipData.imo_number}
                onChange={(e) => setShipData(prev => ({ ...prev, imo_number: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="1234567"
              />
            </div>

            {/* Flag - Medium width */}
            <div className="col-span-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Cờ' : 'Flag'} *
              </label>
              <input
                type="text"
                required
                value={shipData.flag}
                onChange={(e) => setShipData(prev => ({ ...prev, flag: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder={language === 'vi' ? 'Việt Nam, Singapore...' : 'Vietnam, Singapore...'}
              />
            </div>

            {/* Class Society - Medium width */}
            <div className="col-span-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Tổ chức Phân cấp' : 'Class Society'} *
              </label>
              <input
                type="text"
                required
                value={shipData.class_society}
                onChange={(e) => setShipData(prev => ({ ...prev, class_society: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="DNV GL, ABS, LR..."
              />
            </div>

            {/* Ship Owner - Medium width */}
            <div className="col-span-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Chủ tàu' : 'Ship Owner'} *
              </label>
              <select
                required
                value={shipData.ship_owner}
                onChange={(e) => setShipData(prev => ({ ...prev, ship_owner: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              >
                <option value="">{language === 'vi' ? 'Chọn chủ tàu' : 'Select ship owner'}</option>
                {availableCompanies.map(company => (
                  <option key={company.id} value={language === 'vi' ? company.name_vn : company.name_en}>
                    {language === 'vi' ? company.name_vn : company.name_en}
                  </option>
                ))}
              </select>
            </div>

            {/* Gross Tonnage - Short width */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'GT' : 'GT'}
              </label>
              <input
                type="number"
                value={shipData.gross_tonnage}
                onChange={(e) => setShipData(prev => ({ ...prev, gross_tonnage: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="0"
              />
            </div>

            {/* Deadweight - Short width */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'DWT' : 'DWT'}
              </label>
              <input
                type="number"
                value={shipData.deadweight}
                onChange={(e) => setShipData(prev => ({ ...prev, deadweight: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="0"
              />
            </div>

            {/* Delivery Date - Short width */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Ngày giao' : 'Delivery Date'}
              </label>
              <input
                type="date"
                value={shipData.delivery_date || ''}
                onChange={(e) => setShipData(prev => ({ ...prev, delivery_date: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>

            {/* Keel Laid - Short width */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Keel Laid' : 'Keel Laid'}
              </label>
              <input
                type="date"
                value={shipData.keel_laid || ''}
                onChange={(e) => setShipData(prev => ({ ...prev, keel_laid: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>

            {/* Company - Short width (locked) */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Công ty' : 'Company'} *
              </label>
              <div className="relative">
                <select
                  required
                  disabled
                  value={shipData.company}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed text-sm"
                >
                  <option value={shipData.company}>
                    {shipData.company || (language === 'vi' ? 'Công ty của bạn' : 'Your company')}
                  </option>
                </select>
                <div className="absolute right-2 top-2 text-gray-400 text-sm">
                  🔒
                </div>
              </div>
            </div>

            {/* Survey & Maintenance Section */}
            <div className="col-span-12 mt-4">
              <h4 className="text-lg font-semibold text-gray-700 mb-3 pb-2 border-b">
                {language === 'vi' ? 'Thông tin Khảo sát & Bảo dưỡng (Tùy chọn)' : 'Survey & Maintenance Information (Optional)'}
              </h4>
            </div>

            {/* Docking Dates Row */}
            <div className="col-span-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Last Docking 1' : 'Last Docking 1'}
              </label>
              <input
                type="text"
                value={shipData.last_docking || ''}
                onChange={(e) => setShipData(prev => ({ ...prev, last_docking: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="11/2020"
              />
            </div>

            <div className="col-span-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Last Docking 2' : 'Last Docking 2'}
              </label>
              <input
                type="text"
                value={shipData.last_docking_2 || ''}
                onChange={(e) => setShipData(prev => ({ ...prev, last_docking_2: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="08/2021"
              />
            </div>

            <div className="col-span-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Next Docking' : 'Next Docking'}
              </label>
              <input
                type="date"
                value={shipData.next_docking || ''}
                onChange={(e) => setShipData(prev => ({ ...prev, next_docking: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>

            <div className="col-span-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Last Special Survey' : 'Last Special Survey'}
              </label>
              <input
                type="date"
                value={shipData.last_special_survey || ''}
                onChange={(e) => setShipData(prev => ({ ...prev, last_special_survey: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>

            <div className="col-span-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <span className="flex items-center">
                  {language === 'vi' ? 'Last Intermediate Survey' : 'Last Intermediate Survey'}
                  <div className="group relative ml-1">
                    <svg className="w-3 h-3 text-gray-400 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div className="absolute bottom-full left-0 mb-2 w-64 p-2 text-xs text-white bg-gray-800 rounded opacity-0 group-hover:opacity-100 transition-opacity z-10">
                      {language === 'vi' 
                        ? 'Kiểm tra trung gian thực hiện giữa 2 Special Survey (thường 2.5-3 năm). Bắt buộc theo quy định IMO và Class Society.'
                        : 'Intermediate inspection conducted between Special Surveys (typically 2.5-3 years). Required by IMO and Class Society regulations.'}
                    </div>
                  </div>
                </span>
              </label>
              <input
                type="date"
                value={shipData.last_intermediate_survey || ''}
                onChange={(e) => setShipData(prev => ({ ...prev, last_intermediate_survey: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>

            {/* Anniversary Date Section */}
            <div className="col-span-6 mt-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Anniversary Date' : 'Anniversary Date'}
              </label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <input
                    type="number"
                    min="1"
                    max="31"
                    value={shipData.anniversary_date_day || ''}
                    onChange={(e) => setShipData(prev => ({ ...prev, anniversary_date_day: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    placeholder="Day"
                  />
                </div>
                <div>
                  <select
                    value={shipData.anniversary_date_month || ''}
                    onChange={(e) => setShipData(prev => ({ ...prev, anniversary_date_month: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  >
                    <option value="">Month</option>
                    <option value="1">Jan</option>
                    <option value="2">Feb</option>
                    <option value="3">Mar</option>
                    <option value="4">Apr</option>
                    <option value="5">May</option>
                    <option value="6">Jun</option>
                    <option value="7">Jul</option>
                    <option value="8">Aug</option>
                    <option value="9">Sep</option>
                    <option value="10">Oct</option>
                    <option value="11">Nov</option>
                    <option value="12">Dec</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Special Survey Cycle Section */}
            <div className="col-span-6 mt-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {language === 'vi' ? 'Special Survey Cycle (IMO 5-year)' : 'Special Survey Cycle (IMO 5-year)'}
              </label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <input
                    type="date"
                    value={shipData.special_survey_from_date || ''}
                    onChange={(e) => setShipData(prev => ({ ...prev, special_survey_from_date: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    placeholder="From Date"
                  />
                </div>
                <div>
                  <input
                    type="date"
                    value={shipData.special_survey_to_date || ''}
                    onChange={(e) => setShipData(prev => ({ ...prev, special_survey_to_date: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    placeholder="To Date"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Certificate Form */}
        {recordType === 'certificate' && (
          <div className="space-y-4">
            {!selectedShip && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-yellow-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="text-yellow-800 text-sm font-medium">
                      {language === 'vi' ? '⚠️ Chưa chọn tàu' : '⚠️ No Ship Selected'}
                    </p>
                    <p className="text-yellow-700 text-xs mt-1">
                      {language === 'vi' 
                        ? 'Bạn cần chọn một tàu từ danh sách bên trái trước khi có thể upload chứng chỉ. Certificate sẽ được gán vào tàu đã chọn.'
                        : 'You need to select a ship from the left sidebar before uploading certificates. Certificates will be assigned to the selected ship.'
                      }
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Multi Cert Upload */}
            <div className="border-2 border-dashed border-blue-300 rounded-lg p-6 bg-blue-50">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-blue-900 mb-2">
                  📋 {language === 'vi' ? 'Multi Cert Upload' : 'Multi Cert Upload'}
                </h3>
                
                {/* AI Model Display */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center">
                    <span className="text-sm text-blue-700 mr-2">
                      {language === 'vi' ? 'Model AI đang sử dụng:' : 'AI Model in use:'}
                    </span>
                    <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z" />
                      </svg>
                      {aiConfig 
                        ? `${aiConfig.provider === 'emergent' ? 'Emergent LLM' : aiConfig.provider.charAt(0).toUpperCase() + aiConfig.provider.slice(1)} - ${aiConfig.model}`
                        : (language === 'vi' ? 'AI Model: Đang tải...' : 'AI Model: Loading...')
                      }
                    </div>
                  </div>
                </div>

                {/* Upload Instructions */}
                <div className="bg-blue-100 rounded-lg p-3 mb-4">
                  <h4 className="text-sm font-medium text-blue-800 mb-2">
                    📝 {language === 'vi' ? 'Hướng dẫn Upload:' : 'Upload Guidelines:'}
                  </h4>
                  <ul className="text-xs text-blue-700 space-y-1">
                    <li>• {language === 'vi' ? 'Format: PDF, JPG, PNG' : 'Format: PDF, JPG, PNG files'}</li>
                    <li>• {language === 'vi' ? 'Kích thước: Tối đa 50MB mỗi file' : 'Size: Maximum 50MB per file'}</li>
                    <li>• {language === 'vi' ? 'AI sẽ tự động phân tích và xác định Marine Certificate' : 'AI will automatically analyze and identify Marine Certificates'}</li>
                  </ul>
                </div>

                {/* Upload Button */}
                <div className="text-center">
                  <label
                    htmlFor="multi-cert-upload"
                    className={`inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md transition-colors cursor-pointer ${
                      selectedShip && !isMultiCertProcessing
                        ? 'text-white bg-blue-600 hover:bg-blue-700'
                        : 'text-gray-400 bg-gray-300 cursor-not-allowed'
                    }`}
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    {isMultiCertProcessing 
                      ? (language === 'vi' ? '⏳ Đang xử lý...' : '⏳ Processing...')
                      : (language === 'vi' ? '📋 Cert Upload' : '📋 Cert Upload')
                    }
                    <input
                      id="multi-cert-upload"
                      name="multi-cert-upload"
                      type="file"
                      multiple
                      className="sr-only"
                      onChange={(e) => {
                        if (selectedShip && !isMultiCertProcessing) {
                          // Create auto-fill callback for AddRecordModal context
                          const autoFillCallback = (data, fieldCount) => {
                            console.log('🔄 Auto-filling certificate form with data:', data);
                            setCertificateData(prev => ({
                              ...prev,
                              ...data
                            }));
                            
                            // Show auto-fill success message
                            toast.success(
                              language === 'vi' 
                                ? `✅ Đã auto-fill ${fieldCount} trường thông tin certificate!`
                                : `✅ Auto-filled ${fieldCount} certificate fields!`
                            );
                          };
                          
                          // Call handleMultiCertUpload with auto-fill callback
                          handleMultiCertUpload(e.target.files, autoFillCallback);
                        }
                      }}
                      accept=".pdf,.jpg,.jpeg,.png"
                      disabled={!selectedShip || isMultiCertProcessing}
                    />
                  </label>
                  
                  {!selectedShip && (
                    <p className="text-sm text-orange-600 mt-2">
                      ⚠️ {language === 'vi' 
                        ? 'Vui lòng chọn tàu trước khi upload certificates'
                        : 'Please select a ship before uploading certificates'
                      }
                    </p>
                  )}
                </div>
              </div>

              {/* Upload Progress */}
              {multiCertUploads && multiCertUploads.length > 0 && (
                <div className="mt-6 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-gray-900 flex items-center">
                      {language === 'vi' ? '📊 Tiến trình xử lý' : '📊 Processing Progress'}
                      {isMultiCertProcessing && (
                        <div className="ml-2 animate-spin">
                          <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        </div>
                      )}
                    </h4>
                    
                    {!isMultiCertProcessing && (
                      <button
                        onClick={() => {
                          setMultiCertUploads([]);
                          setUploadSummary(null);
                        }}
                        className="text-xs px-3 py-1 bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 transition-colors"
                      >
                        🗑️ {language === 'vi' ? 'Xóa kết quả' : 'Clear Results'}
                      </button>
                    )}
                  </div>

                  {/* File Progress List */}
                  {multiCertUploads.map((fileUpload, index) => (
                    <div key={index} className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center">
                          <div className={`w-3 h-3 rounded-full mr-3 ${
                            fileUpload.status === 'completed' ? 'bg-green-500' :
                            fileUpload.status === 'failed' ? 'bg-red-500' :
                            fileUpload.status === 'skipped' ? 'bg-yellow-500' :
                            fileUpload.status === 'pending_duplicate' ? 'bg-orange-500' :
                            'bg-blue-500'
                          }`}></div>
                          <span className="font-medium text-gray-900">{fileUpload.name}</span>
                          {fileUpload.size && (
                            <span className="text-sm text-gray-500 ml-2">
                              ({(fileUpload.size / 1024 / 1024).toFixed(2)} MB)
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-600">{fileUpload.progress}%</div>
                      </div>
                      
                      {/* Progress Bar */}
                      <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                        <div 
                          className={`h-2 rounded-full transition-all duration-300 ${
                            fileUpload.status === 'completed' ? 'bg-green-500' :
                            fileUpload.status === 'failed' ? 'bg-red-500' :
                            fileUpload.status === 'skipped' ? 'bg-yellow-500' :
                            fileUpload.status === 'pending_duplicate' ? 'bg-orange-500' :
                            'bg-blue-500'
                          }`}
                          style={{ width: `${fileUpload.progress}%` }}
                        />
                      </div>
                      
                      {/* Current Processing Status */}
                      <div className="text-sm font-medium mb-2 px-2 py-1 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
                        {fileUpload.stage}
                      </div>
                      
                      {/* Marine Certificate Analysis Results */}
                      {fileUpload.status === 'completed' && fileUpload.is_marine_certificate && (
                        <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
                          <h5 className="text-sm font-semibold text-green-700 mb-2">
                            ✅ {language === 'vi' ? 'Marine Certificate - Thông tin trích xuất' : 'Marine Certificate - Extracted Information'}
                          </h5>
                          <div className="text-sm space-y-1">
                            {fileUpload.cert_name && (
                              <div className="flex justify-between">
                                <span className="font-medium text-blue-600">{language === 'vi' ? 'Tên chứng chỉ:' : 'Certificate Name:'}</span>
                                <span className="text-blue-800 text-xs max-w-xs truncate">{fileUpload.cert_name}</span>
                              </div>
                            )}
                            {fileUpload.cert_no && (
                              <div className="flex justify-between">
                                <span className="font-medium text-purple-600">{language === 'vi' ? 'Số chứng chỉ:' : 'Certificate No:'}</span>
                                <span className="text-purple-800">{fileUpload.cert_no}</span>
                              </div>
                            )}
                            {fileUpload.valid_date && (
                              <div className="flex justify-between">
                                <span className="font-medium text-red-600">{language === 'vi' ? 'Hết hạn:' : 'Valid Until:'}</span>
                                <span className="text-red-800">{fileUpload.valid_date}</span>
                              </div>
                            )}
                            {fileUpload.issued_by && (
                              <div className="flex justify-between">
                                <span className="font-medium text-green-600">{language === 'vi' ? 'Cấp bởi:' : 'Issued By:'}</span>
                                <span className="text-green-800 text-xs max-w-xs truncate">{fileUpload.issued_by}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {/* Manual Review Required */}
                      {fileUpload.status === 'requires_manual_review' && (
                        <div className="mt-3 p-3 bg-orange-50 rounded-lg border border-orange-200">
                          <h5 className="text-sm font-semibold text-orange-700 mb-2">
                            🔍 {language === 'vi' ? 'Cần xem xét thủ công' : 'Manual Review Required'}
                          </h5>
                          <div className="text-sm space-y-2">
                            <div className="flex justify-between">
                              <span className="font-medium text-orange-600">
                                {language === 'vi' ? 'Hệ thống phân loại:' : 'System classified as:'}
                              </span>
                              <span className="text-orange-800 capitalize">{fileUpload.detected_category || 'unknown'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="font-medium text-orange-600">
                                {language === 'vi' ? 'Độ tin cậy:' : 'Confidence:'}
                              </span>
                              <span className="text-orange-800 capitalize">{fileUpload.confidence || 'unknown'}</span>
                            </div>
                            <p className="text-xs text-orange-600 mt-2">
                              {language === 'vi' 
                                ? 'Hệ thống không tự động nhận diện đây là Marine Certificate. Vui lòng xem lại và xác nhận.' 
                                : 'System did not automatically identify this as a Marine Certificate. Please review and confirm.'}
                            </p>
                          </div>
                          
                          {/* Action Buttons */}
                          <div className="flex justify-end space-x-2 mt-3 pt-2 border-t border-orange-200">
                            <button
                              onClick={() => {
                                const reviewData = pendingManualReviews.find(r => r.filename === fileUpload.name);
                                if (reviewData) handleManualReviewAction('view', reviewData);
                              }}
                              className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors flex items-center"
                            >
                              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                              {language === 'vi' ? 'Xem' : 'View'}
                            </button>
                            
                            <button
                              onClick={() => {
                                const reviewData = pendingManualReviews.find(r => r.filename === fileUpload.name);
                                if (reviewData) handleManualReviewAction('skip', reviewData);
                              }}
                              className="px-3 py-1 text-xs bg-gray-500 hover:bg-gray-600 text-white rounded-md transition-colors flex items-center"
                            >
                              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              {language === 'vi' ? 'Bỏ qua' : 'Skip'}
                            </button>
                            
                            <button
                              onClick={() => {
                                const reviewData = pendingManualReviews.find(r => r.filename === fileUpload.name);
                                if (reviewData) handleManualReviewAction('confirm_marine', reviewData);
                              }}
                              className="px-3 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors flex items-center"
                            >
                              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              {language === 'vi' ? 'Xác nhận Marine Cert' : 'Confirm Marine Cert'}
                            </button>
                          </div>
                        </div>
                      )}
                      
                      {/* Non-Marine Certificate */}
                      {fileUpload.status === 'skipped' && (
                        <div className="mt-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                          <h5 className="text-sm font-semibold text-yellow-700 mb-1">
                            ⚠️ {language === 'vi' ? 'Không phải Marine Certificate' : 'Not a Marine Certificate'}
                          </h5>
                          <p className="text-xs text-yellow-600">
                            {language === 'vi' ? 'File này đã được bỏ qua. Vui lòng kiểm tra lại.' : 'This file was skipped. Please review manually.'}
                          </p>
                        </div>
                      )}
                      
                      {/* Requires User Choice */}
                      {fileUpload.status === 'requires_user_choice' && (
                        <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                          <h5 className="text-sm font-semibold text-blue-700 mb-2">
                            📁 {language === 'vi' ? 'Chọn folder để lưu file' : 'Choose folder to save file'}
                          </h5>
                          <p className="text-xs text-blue-600 mb-3">
                            {fileUpload.message}
                          </p>
                          
                          {fileUpload.shipFolderExists ? (
                            <div className="space-y-2">
                              <p className="text-xs font-medium text-gray-700">
                                {language === 'vi' ? 'Folder có sẵn:' : 'Available folders:'}
                              </p>
                              <div className="flex flex-wrap gap-2">
                                {fileUpload.availableFolders?.map((folder, idx) => (
                                  <button
                                    key={idx}
                                    onClick={() => handleUploadToFolder(fileUpload.filename, folder)}
                                    className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 transition-colors"
                                  >
                                    📂 {folder}
                                  </button>
                                ))}
                                <button
                                  onClick={() => handleSkipFile(fileUpload.filename)}
                                  className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                                >
                                  ⏭️ {language === 'vi' ? 'Bỏ qua' : 'Skip'}
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="text-center">
                              <p className="text-xs text-red-600 mb-2">
                                {language === 'vi' ? 'Cần tạo ship folder trước' : 'Ship folder needs to be created first'}
                              </p>
                              <button
                                onClick={() => handleSkipFile(fileUpload.filename)}
                                className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                              >
                                ⏭️ {language === 'vi' ? 'Bỏ qua' : 'Skip'}
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* Error Display */}
                      {fileUpload.status === 'failed' && fileUpload.error && (
                        <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-200">
                          <h5 className="text-sm font-semibold text-red-700 mb-1">❌ {language === 'vi' ? 'Lỗi' : 'Error'}</h5>
                          <p className="text-xs text-red-600">{fileUpload.error}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Upload Summary */}
              {uploadSummary && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg border">
                  <h4 className="font-medium text-gray-900 mb-3">
                    📊 {language === 'vi' ? 'Báo cáo tổng hợp' : 'Summary Report'}
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{uploadSummary.total_files}</div>
                      <div className="text-gray-600">{language === 'vi' ? 'File upload' : 'Files Uploaded'}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{uploadSummary.marine_certificates}</div>
                      <div className="text-gray-600">{language === 'vi' ? 'Marine Cert' : 'Marine Certificates'}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">{uploadSummary.records_created}</div>
                      <div className="text-gray-600">{language === 'vi' ? 'Record tạo' : 'Records Created'}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-yellow-600">{uploadSummary.non_marine_files}</div>
                      <div className="text-gray-600">{language === 'vi' ? 'File khác' : 'Non-Marine'}</div>
                    </div>
                  </div>
                  
                  {uploadSummary.non_marine_files > 0 && (
                    <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                      <h5 className="text-sm font-medium text-yellow-800 mb-2">
                        ⚠️ {language === 'vi' ? 'File cần kiểm tra lại:' : 'Files to Review:'}
                      </h5>
                      <ul className="text-xs text-yellow-700 space-y-1">
                        {uploadSummary.non_marine_list?.map((fileName, index) => (
                          <li key={index}>• {fileName}</li>
                        ))}
                      </ul>
                    </div>
                  )}
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
                  placeholder={language === 'vi' ? 'VD: Safety Management Certificate' : 'e.g. Safety Management Certificate'}
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
              {/* Last Endorse - Only show for Full Term certificates */}
              {certificateData.cert_type === 'Full Term' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'vi' ? 'Xác nhận cuối' : 'Last Endorse'}
                    <span className="text-xs text-gray-500 ml-1">
                      ({language === 'vi' ? 'Chỉ cho chứng chỉ Full Term' : 'Full Term certificates only'})
                    </span>
                  </label>
                  <input
                    type="date"
                    value={certificateData.last_endorse}
                    onChange={(e) => setCertificateData(prev => ({ ...prev, last_endorse: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              )}
              
              {/* Placeholder div for grid alignment when Last Endorse is hidden */}
              {certificateData.cert_type !== 'Full Term' && (
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">
                    {language === 'vi' ? 'Xác nhận cuối' : 'Last Endorse'}
                    <span className="text-xs text-gray-400 ml-1">
                      ({language === 'vi' ? 'Không áp dụng cho loại chứng chỉ này' : 'Not applicable for this certificate type'})
                    </span>
                  </label>
                  <input
                    type="date"
                    disabled
                    className="w-full px-3 py-2 border border-gray-200 bg-gray-50 rounded-lg text-gray-400 cursor-not-allowed"
                    placeholder={language === 'vi' ? 'Chỉ Full Term mới có endorsement' : 'Full Term certificates only'}
                  />
                </div>
              )}
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
              
              {/* Next Survey Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'vi' ? 'Loại khảo sát tiếp theo' : 'Next Survey Type'}
                </label>
                <select
                  value={certificateData.next_survey_type || ''}
                  onChange={(e) => setCertificateData(prev => ({ ...prev, next_survey_type: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">{language === 'vi' ? 'Chọn loại khảo sát tiếp theo' : 'Select next survey type'}</option>
                  <option value="Annual">{language === 'vi' ? 'Khảo sát hàng năm' : 'Annual Survey'}</option>
                  <option value="Intermediate">{language === 'vi' ? 'Khảo sát trung gian' : 'Intermediate Survey'}</option>
                  <option value="Special">{language === 'vi' ? 'Khảo sát đặc biệt' : 'Special Survey'}</option>
                  <option value="Renewal">{language === 'vi' ? 'Khảo sát gia hạn' : 'Renewal Survey'}</option>
                  <option value="Docking">{language === 'vi' ? 'Khảo sát neo đậu' : 'Docking Survey'}</option>
                  <option value="Class">{language === 'vi' ? 'Khảo sát phân cấp' : 'Class Survey'}</option>
                  <option value="Other">{language === 'vi' ? 'Khác' : 'Other'}</option>
                </select>
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
                  <option value="inspection_records">{language === 'vi' ? 'Hồ sơ Đăng kiểm' : 'Class Survey Report'}</option>
                  <option value="survey_reports">{language === 'vi' ? 'Báo cáo kiểm tra' : 'Test Report'}</option>
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
                <option value="inspection_records">{language === 'vi' ? 'Hồ sơ Đăng kiểm' : 'Class Survey Report'}</option>
                <option value="survey_reports">{language === 'vi' ? 'Báo cáo kiểm tra' : 'Test Report'}</option>
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
            {recordType === 'ship' 
              ? (language === 'vi' ? '🚢 Thêm tàu mới' : '🚢 Add New Ship')
              : (language === 'vi' ? 'Thêm hồ sơ' : 'Add Record')
            }
          </button>
        </div>
      </div>
      
      {/* PDF Analysis Modal */}
      {showPdfAnalysis && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[99999] p-4">
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

      {/* Duplicate Certificate Modal */}
      {duplicateModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[70]">
          <div className="bg-white rounded-xl shadow-2xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="mb-6">
              <h3 className="text-xl font-bold text-red-600 mb-2">
                ⚠️ {language === 'vi' ? 'Phát hiện giấy chứng nhận trùng lặp' : 'Duplicate Certificate Detected'}
              </h3>
              <p className="text-gray-600">
                {language === 'vi' 
                  ? `File "${duplicateModal.currentFile}" có Certificate No và Cert Name trùng với giấy chứng nhận đã có:`
                  : `File "${duplicateModal.currentFile}" has matching Certificate No and Cert Name with existing certificate:`}
              </p>
            </div>

            {/* Show duplicate certificates */}
            <div className="mb-6 max-h-60 overflow-y-auto">
              {duplicateModal.duplicates && duplicateModal.duplicates.map((duplicate, index) => (
                <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-4 mb-3">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Tên chứng chỉ:' : 'Cert Name:'}</span>
                      <p className="text-gray-900">{duplicate.existing_cert?.cert_name || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Số chứng chỉ:' : 'Cert No:'}</span>
                      <p className="text-gray-900">{duplicate.existing_cert?.cert_no || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Ngày cấp:' : 'Issue Date:'}</span>
                      <p className="text-gray-900">{duplicate.existing_cert?.issue_date || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Ngày hết hạn:' : 'Valid Date:'}</span>
                      <p className="text-gray-900">{duplicate.existing_cert?.valid_date || 'N/A'}</p>
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-red-600">
                    {language === 'vi' ? 'Độ trùng lặp:' : 'Similarity:'} {duplicate.similarity?.toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>

            {/* Action buttons */}
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => handleLocalDuplicateResolution('cancel')}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
              >
                {language === 'vi' ? 'Hủy' : 'Cancel'}
              </button>
              <button
                onClick={() => handleLocalDuplicateResolution('overwrite')}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all"
              >
                {language === 'vi' ? 'Ghi đè' : 'Overwrite'}
              </button>
              <button
                onClick={() => handleLocalDuplicateResolution('keep_both')}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all"
              >
                {language === 'vi' ? 'Giữ cả hai' : 'Keep Both'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Duplicate Resolution Modal */}
      {duplicateResolutionModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[80]">
          <div className="bg-white rounded-xl shadow-2xl p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="mb-6 relative">
              <h3 className="text-xl font-bold text-orange-600 mb-2">
                ⚠️ {language === 'vi' ? 'Phát hiện chứng chỉ trùng lặp' : 'Duplicate Certificate Detected'}
              </h3>
              
              {/* Close button */}
              <button
                onClick={() => {
                  setDuplicateResolutionModal({
                    show: false,
                    fileData: null,
                    analysisResult: null,
                    duplicateInfo: null,
                    shipId: null,
                    fileIndex: -1,
                    fileName: ''
                  });
                  // Reset multi cert processing state when modal is closed
                  if (setIsMultiCertProcessing) {
                    setIsMultiCertProcessing(false);
                  }
                }}
                className="absolute top-0 right-0 text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
              <p className="text-gray-600">
                {language === 'vi' 
                  ? 'Hệ thống phát hiện chứng chỉ có thể trùng lặp. Vui lòng xem xét thông tin bên dưới và quyết định:'
                  : 'System detected a potential duplicate certificate. Please review the information below and decide:'
                }
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* Existing Certificate */}
              <div className="border border-red-200 rounded-lg p-4 bg-red-50">
                <h4 className="font-bold text-red-800 mb-3">
                  📋 {language === 'vi' ? 'Chứng chỉ đã tồn tại' : 'Existing Certificate'}
                </h4>
                {duplicateResolutionModal.duplicateInfo?.existing_certificate && (
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Tên:' : 'Name:'}</span>
                      <p className="text-gray-900">{duplicateResolutionModal.duplicateInfo.existing_certificate.cert_name}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Số chứng chỉ:' : 'Certificate No:'}</span>
                      <p className="text-gray-900">{duplicateResolutionModal.duplicateInfo.existing_certificate.cert_no}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Loại:' : 'Type:'}</span>
                      <p className="text-gray-900">{duplicateResolutionModal.duplicateInfo.existing_certificate.cert_type}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Ngày cấp:' : 'Issue Date:'}</span>
                      <p className="text-gray-900">{duplicateResolutionModal.duplicateInfo.existing_certificate.issue_date ? new Date(duplicateResolutionModal.duplicateInfo.existing_certificate.issue_date).toLocaleDateString('vi-VN') : '-'}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Ngày hết hạn:' : 'Valid Date:'}</span>
                      <p className="text-gray-900">{duplicateResolutionModal.duplicateInfo.existing_certificate.valid_date ? new Date(duplicateResolutionModal.duplicateInfo.existing_certificate.valid_date).toLocaleDateString('vi-VN') : '-'}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Cấp bởi:' : 'Issued By:'}</span>
                      <p className="text-gray-900">{duplicateResolutionModal.duplicateInfo.existing_certificate.issued_by || 'N/A'}</p>
                    </div>
                  </div>
                )}
              </div>

              {/* New Certificate */}
              <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                <h4 className="font-bold text-blue-800 mb-3">
                  📄 {language === 'vi' ? 'Chứng chỉ mới (đang upload)' : 'New Certificate (uploading)'}
                </h4>
                {duplicateResolutionModal.duplicateInfo?.new_certificate && (
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Tên:' : 'Name:'}</span>
                      <p className="text-gray-900">{duplicateResolutionModal.duplicateInfo.new_certificate.cert_name}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Số chứng chỉ:' : 'Certificate No:'}</span>
                      <p className="text-gray-900">{duplicateResolutionModal.duplicateInfo.new_certificate.cert_no}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Loại:' : 'Type:'}</span>
                      <p className="text-gray-900">{duplicateResolutionModal.duplicateInfo.new_certificate.cert_type}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Ngày cấp:' : 'Issue Date:'}</span>
                      <p className="text-gray-900">{duplicateResolutionModal.duplicateInfo.new_certificate.issue_date ? new Date(duplicateResolutionModal.duplicateInfo.new_certificate.issue_date).toLocaleDateString('vi-VN') : '-'}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Ngày hết hạn:' : 'Valid Date:'}</span>
                      <p className="text-gray-900">{duplicateResolutionModal.duplicateInfo.new_certificate.valid_date ? new Date(duplicateResolutionModal.duplicateInfo.new_certificate.valid_date).toLocaleDateString('vi-VN') : '-'}</p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{language === 'vi' ? 'Cấp bởi:' : 'Issued By:'}</span>
                      <p className="text-gray-900">{duplicateResolutionModal.duplicateInfo.new_certificate.issued_by || 'N/A'}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Similarity Info */}
            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h4 className="font-bold text-yellow-800 mb-2">
                📊 {language === 'vi' ? 'Thông tin trùng lặp' : 'Duplicate Information'}
              </h4>
              <p className="text-sm text-yellow-700">
                {language === 'vi' ? 'Độ tương đồng:' : 'Similarity:'} 
                <span className="font-bold ml-1">{duplicateResolutionModal.duplicateInfo?.similarity || 0}%</span>
              </p>
              <p className="text-xs text-yellow-600 mt-1">
                {language === 'vi' 
                  ? 'Số chứng chỉ khớp chính xác, tên chứng chỉ có độ tương đồng >75%'
                  : 'Certificate number matches exactly, certificate name similarity >75%'
                }
              </p>
            </div>

            {/* File Info */}
            <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <h4 className="font-bold text-gray-800 mb-2">
                📁 {language === 'vi' ? 'Thông tin file' : 'File Information'}
              </h4>
              <p className="text-sm text-gray-700">
                <span className="font-medium">{language === 'vi' ? 'Tên file:' : 'Filename:'}</span> {duplicateResolutionModal.fileName}
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-end">
              <button
                onClick={() => handleDuplicateResolution('skip', setIsCertificateAnalyzing)}
                className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition duration-200 font-medium"
              >
                ⏩ {language === 'vi' ? 'Skip (Bỏ qua)' : 'Skip'}
                <div className="text-xs opacity-75 mt-1">
                  {language === 'vi' ? 'Không upload, không tạo record' : 'Don\'t upload, don\'t create record'}
                </div>
              </button>
              <button
                onClick={() => handleDuplicateResolution('continue', setIsCertificateAnalyzing)}
                className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition duration-200 font-medium"
              >
                ✅ {language === 'vi' ? 'Continue (Tiếp tục)' : 'Continue'}
                <div className="text-xs opacity-75 mt-1">
                  {language === 'vi' ? 'Tiếp tục tạo record' : 'Continue creating record'}
                </div>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Ship Confirmation Modal */}
      {showShipConfirmModal && pendingShipData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mr-4">
                  <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900">
                    {language === 'vi' ? 'Tàu chưa có trong danh sách' : 'Ship not found in list'}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {language === 'vi' ? 'Tàu này chưa được thêm vào hệ thống' : 'This ship is not yet added to the system'}
                  </p>
                </div>
              </div>
              
              <div className="mb-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-800">
                    <span className="font-medium">{language === 'vi' ? 'Tên tàu từ giấy chứng nhận' : 'Ship name from certificate'}:</span>
                  </p>
                  <p className="text-lg font-bold text-blue-900 mt-1">
                    {pendingShipData.shipName}
                  </p>
                </div>
              </div>
              
              <div className="space-y-3">
                <button
                  onClick={() => handleShipConfirmation(true)}
                  className="w-full bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  {language === 'vi' 
                    ? '🚢 Tự động thêm tàu mới và tiếp tục' 
                    : '🚢 Auto-add new ship and continue'}
                </button>
                
                <button
                  onClick={() => handleShipConfirmation(false)}
                  className="w-full bg-gray-100 text-gray-700 px-4 py-3 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                >
                  {language === 'vi' 
                    ? '❌ Hủy bỏ việc thêm certificate' 
                    : '❌ Cancel certificate addition'}
                </button>
              </div>
              
              <div className="mt-4 text-center">
                <p className="text-xs text-gray-500">
                  {language === 'vi' 
                    ? 'Chọn "Tự động thêm tàu mới" sẽ chuyển sang mục tạo tàu với thông tin từ giấy chứng nhận'
                    : 'Selecting "Auto-add new ship" will switch to ship creation with certificate information'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* File Viewer Modal for Manual Review */}
      {showFileViewer && fileViewerData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-[95vh] flex flex-col">
            <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200">
              <h3 className="text-xl font-bold text-blue-600 flex items-center">
                <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                {language === 'vi' ? 'Xem xét file & Phân tích AI' : 'File Review & AI Analysis'}
              </h3>
              <button
                onClick={() => {
                  setShowFileViewer(false);
                  setFileViewerData(null);
                }}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
              >
                ×
              </button>
            </div>
            
            <div className="p-6 flex-grow overflow-auto">
              <div className="mb-4">
                <h4 className="text-lg font-semibold text-gray-900 mb-2">{fileViewerData.filename}</h4>
                <div className="flex space-x-4 text-sm text-gray-600">
                  <span>
                    <strong>{language === 'vi' ? 'Phân loại hệ thống:' : 'System Classification:'}</strong> 
                    <span className={`ml-1 px-2 py-1 rounded text-xs font-medium ${
                      fileViewerData.detected_category === 'certificates' 
                        ? 'bg-green-100 text-green-800'
                        : 'bg-orange-100 text-orange-800'
                    }`}>
                      {fileViewerData.detected_category}
                    </span>
                  </span>
                  <span>
                    <strong>{language === 'vi' ? 'Độ tin cậy:' : 'Confidence:'}</strong> 
                    <span className="ml-1 capitalize text-orange-600">{fileViewerData.confidence}</span>
                  </span>
                </div>
              </div>
              
              {/* Two-column layout for file content and AI analysis */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* Left Column: File Content */}
                <div className="space-y-4">
                  <h5 className="text-lg font-semibold text-gray-800 flex items-center">
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    {language === 'vi' ? '📄 Nội dung file' : '📄 File Content'}
                  </h5>
                  
                  {/* File Content Display */}
                  <div className="bg-gray-50 rounded-lg p-4 min-h-80 max-h-96 overflow-auto">
                {fileViewerData.content_type && fileViewerData.content_type.includes('pdf') ? (
                  <div className="space-y-4">
                    {/* PDF Viewer */}
                    <div className="bg-white rounded-lg border border-gray-300 min-h-80">
                      <div className="flex justify-between items-center p-3 bg-gray-100 rounded-t-lg border-b">
                        <h6 className="font-medium text-gray-800">PDF Preview</h6>
                        <button
                          onClick={() => {
                            // Download the file
                            const link = document.createElement('a');
                            link.href = `data:application/pdf;base64,${fileViewerData.content_b64}`;
                            link.download = fileViewerData.filename;
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                          }}
                          className="text-sm px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                        >
                          {language === 'vi' ? 'Tải PDF' : 'Download PDF'}
                        </button>
                      </div>
                      <div className="p-2" style={{ height: '300px' }}>
                        <iframe
                          src={`data:application/pdf;base64,${fileViewerData.content_b64}`}
                          width="100%"
                          height="100%"
                          style={{ border: 'none', borderRadius: '4px' }}
                          title={fileViewerData.filename}
                        />
                      </div>
                    </div>
                  </div>
                ) : fileViewerData.content_type && fileViewerData.content_type.includes('image') ? (
                  <div className="space-y-4">
                    {/* Image Viewer */}
                    <div className="text-center bg-white rounded-lg border border-gray-300 p-4">
                      <img 
                        src={`data:${fileViewerData.content_type};base64,${fileViewerData.content_b64}`}
                        alt={fileViewerData.filename}
                        className="max-w-full max-h-80 mx-auto rounded-lg shadow-lg"
                        style={{ maxHeight: '320px', objectFit: 'contain' }}
                      />
                      <div className="mt-3 flex justify-center space-x-2">
                        <button
                          onClick={() => {
                            const link = document.createElement('a');
                            link.href = `data:${fileViewerData.content_type};base64,${fileViewerData.content_b64}`;
                            link.download = fileViewerData.filename;
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                          }}
                          className="text-sm px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
                        >
                          {language === 'vi' ? 'Tải ảnh' : 'Download Image'}
                        </button>
                        <button
                          onClick={() => {
                            const newWindow = window.open();
                            newWindow.document.write(`<img src="data:${fileViewerData.content_type};base64,${fileViewerData.content_b64}" style="max-width:100%; height:auto;" alt="${fileViewerData.filename}" />`);
                          }}
                          className="text-sm px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                        >
                          {language === 'vi' ? 'Mở cửa sổ mới' : 'Open in New Window'}
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 bg-white rounded-lg border border-gray-300">
                    <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                    </svg>
                    <p className="text-gray-600">
                      {language === 'vi' 
                        ? 'Preview không khả dụng cho loại file này'
                        : 'Preview not available for this file type'}
                    </p>
                  </div>
                )}
              </div>
                
                {/* Right Column: AI Analysis Summary */}
                <div className="space-y-4">
                  <h5 className="text-lg font-semibold text-gray-800 flex items-center">
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    {language === 'vi' ? '🤖 Phân tích AI' : '🤖 AI Analysis'}
                  </h5>
                  
                  {/* AI Analysis Summary - Enhanced */}
                  <div className="bg-blue-50 rounded-lg border border-blue-200 p-4 max-h-96 overflow-auto">
                    {(() => {
                      const reviewData = pendingManualReviews.find(r => r.filename === fileViewerData.filename);
                      const analysis = fileViewerData.analysis || reviewData?.analysis || {};
                      
                      return (
                        <div className="space-y-4">
                          {/* Classification Summary */}
                          <div className="bg-white rounded-lg p-3 border border-blue-100">
                            <h6 className="text-sm font-semibold text-blue-700 mb-2 flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                              </svg>
                              {language === 'vi' ? 'Kết quả phân loại' : 'Classification Result'}
                            </h6>
                            <div className="grid grid-cols-1 gap-2">
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-600">
                                  {language === 'vi' ? 'Phân loại:' : 'Category:'}
                                </span>
                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                  fileViewerData.detected_category === 'certificates' 
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-orange-100 text-orange-800'
                                }`}>
                                  {fileViewerData.detected_category || 'Unknown'}
                                </span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-600">
                                  {language === 'vi' ? 'Độ tin cậy:' : 'Confidence:'}
                                </span>
                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                  fileViewerData.confidence === 'high' ? 'bg-green-100 text-green-800' :
                                  fileViewerData.confidence === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-red-100 text-red-800'
                                }`}>
                                  {fileViewerData.confidence || 'Unknown'}
                                </span>
                              </div>
                            </div>
                          </div>
                          
                          {/* Certificate Information */}
                          {analysis && Object.keys(analysis).length > 0 && (
                            <div className="bg-white rounded-lg p-3 border border-blue-100">
                              <h6 className="text-sm font-semibold text-blue-700 mb-3 flex items-center">
                                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                {language === 'vi' ? 'Thông tin được trích xuất' : 'Extracted Information'}
                              </h6>
                              
                              <div className="space-y-2">
                                {/* Certificate Details */}
                                {(analysis.cert_name || analysis.cert_no) && (
                                  <div className="bg-blue-50 rounded p-2 border-l-4 border-blue-400">
                                    <div className="text-xs font-medium text-blue-700 mb-1">Certificate Details</div>
                                    {analysis.cert_name && (
                                      <div className="flex justify-between items-start mb-1">
                                        <span className="text-xs text-blue-600 font-medium">Name:</span>
                                        <span className="text-xs text-blue-800 max-w-40 text-right">{analysis.cert_name}</span>
                                      </div>
                                    )}
                                    {analysis.cert_no && (
                                      <div className="flex justify-between items-center">
                                        <span className="text-xs text-blue-600 font-medium">Number:</span>
                                        <span className="text-xs text-blue-800">{analysis.cert_no}</span>
                                      </div>
                                    )}
                                  </div>
                                )}
                                
                                {/* Ship Information */}
                                {(analysis.ship_name || analysis.imo_number) && (
                                  <div className="bg-green-50 rounded p-2 border-l-4 border-green-400">
                                    <div className="text-xs font-medium text-green-700 mb-1">Ship Information</div>
                                    {analysis.ship_name && (
                                      <div className="flex justify-between items-center mb-1">
                                        <span className="text-xs text-green-600 font-medium">Ship Name:</span>
                                        <span className="text-xs text-green-800">{analysis.ship_name}</span>
                                      </div>
                                    )}
                                    {analysis.imo_number && (
                                      <div className="flex justify-between items-center">
                                        <span className="text-xs text-green-600 font-medium">IMO:</span>
                                        <span className="text-xs text-green-800">{analysis.imo_number}</span>
                                      </div>
                                    )}
                                  </div>
                                )}
                                
                                {/* Dates */}
                                {(analysis.issue_date || analysis.valid_date) && (
                                  <div className="bg-yellow-50 rounded p-2 border-l-4 border-yellow-400">
                                    <div className="text-xs font-medium text-yellow-700 mb-1">Important Dates</div>
                                    {analysis.issue_date && (
                                      <div className="flex justify-between items-center mb-1">
                                        <span className="text-xs text-yellow-600 font-medium">Issue Date:</span>
                                        <span className="text-xs text-yellow-800">{analysis.issue_date}</span>
                                      </div>
                                    )}
                                    {analysis.valid_date && (
                                      <div className="flex justify-between items-center">
                                        <span className="text-xs text-red-600 font-medium">Valid Until:</span>
                                        <span className="text-xs text-red-800 font-medium">{analysis.valid_date}</span>
                                      </div>
                                    )}
                                  </div>
                                )}
                                
                                {/* Authority */}
                                {analysis.issued_by && (
                                  <div className="bg-purple-50 rounded p-2 border-l-4 border-purple-400">
                                    <div className="text-xs font-medium text-purple-700 mb-1">Issuing Authority</div>
                                    <span className="text-xs text-purple-800">{analysis.issued_by}</span>
                                  </div>
                                )}
                                
                                {/* Survey Information */}
                                {(analysis.last_endorse || analysis.next_survey || analysis.next_survey_type) && (
                                  <div className="bg-orange-50 rounded p-2 border-l-4 border-orange-400">
                                    <div className="text-xs font-medium text-orange-700 mb-1">Survey Information</div>
                                    {analysis.last_endorse && (
                                      <div className="flex justify-between items-center mb-1">
                                        <span className="text-xs text-orange-600 font-medium">Last Endorse:</span>
                                        <span className="text-xs text-orange-800">{analysis.last_endorse}</span>
                                      </div>
                                    )}
                                    {analysis.next_survey && (
                                      <div className="flex justify-between items-center mb-1">
                                        <span className="text-xs text-orange-600 font-medium">Next Survey:</span>
                                        <span className="text-xs text-orange-800">{analysis.next_survey}</span>
                                      </div>
                                    )}
                                    {analysis.next_survey_type && (
                                      <div className="flex justify-between items-center">
                                        <span className="text-xs text-orange-600 font-medium">Survey Type:</span>
                                        <span className="text-xs text-orange-800 capitalize">{analysis.next_survey_type}</span>
                                      </div>
                                    )}
                                  </div>
                                )}
                                
                                {/* Additional Notes */}
                                {analysis.notes && (
                                  <div className="bg-gray-50 rounded p-2 border-l-4 border-gray-400">
                                    <div className="text-xs font-medium text-gray-700 mb-1">Additional Notes</div>
                                    <p className="text-xs text-gray-600">{analysis.notes}</p>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                          
                          {/* Action Recommendation */}
                          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                            <h6 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              {language === 'vi' ? 'Đề xuất hành động' : 'Recommended Action'}
                            </h6>
                            {fileViewerData.detected_category === 'certificates' ? (
                              <div className="text-xs text-green-700 bg-green-100 p-2 rounded">
                                <div className="font-medium">✅ {language === 'vi' ? 'Xác nhận Marine Certificate' : 'Confirm as Marine Certificate'}</div>
                                <div className="mt-1">{language === 'vi' ? 'Hệ thống đã phân loại đúng.' : 'System classification appears correct.'}</div>
                              </div>
                            ) : (
                              <div className="text-xs text-orange-700 bg-orange-100 p-2 rounded">
                                <div className="font-medium">⚠️ {language === 'vi' ? 'Cần xem xét' : 'Review Required'}</div>
                                <div className="mt-1">
                                  {language === 'vi' 
                                    ? 'Hệ thống không tự động nhận diện là Marine Certificate. Vui lòng kiểm tra nội dung file và xác nhận.'
                                    : 'System did not automatically classify as Marine Certificate. Please review file content and confirm.'}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })()}
                  </div>
            </div>
            </div>
            
            {/* Close grid container */}
            </div>
              
            {/* Action Instructions */}
            <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
                <h6 className="font-medium text-green-800 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {language === 'vi' ? 'Hướng dẫn quyết định:' : 'Decision Guidelines:'}
                </h6>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div className="space-y-2">
                    <div className="flex items-start">
                      <span className="inline-block w-2 h-2 bg-red-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                      <div>
                        <strong className="text-green-700">{language === 'vi' ? 'Bỏ qua nếu:' : 'Skip if:'}</strong>
                        <ul className="text-green-600 ml-2 mt-1">
                          <li>• {language === 'vi' ? 'Không phải tài liệu hàng hải' : 'Not a maritime document'}</li>
                          <li>• {language === 'vi' ? 'Báo cáo test/bảo trì thiết bị' : 'Equipment test/maintenance report'}</li>
                          <li>• {language === 'vi' ? 'Tài liệu thương mại/hành chính' : 'Commercial/administrative document'}</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-start">
                      <span className="inline-block w-2 h-2 bg-green-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                      <div>
                        <strong className="text-green-700">{language === 'vi' ? 'Xác nhận Marine Cert nếu:' : 'Confirm Marine Cert if:'}</strong>
                        <ul className="text-green-600 ml-2 mt-1">
                          <li>• {language === 'vi' ? 'Chứng chỉ an toàn/kỹ thuật tàu' : 'Ship safety/technical certificate'}</li>
                          <li>• {language === 'vi' ? 'Có từ khóa: SOLAS, MARPOL, ISM, ISPS' : 'Contains: SOLAS, MARPOL, ISM, ISPS'}</li>
                          <li>• {language === 'vi' ? 'Cấp bởi Cơ quan Hàng hải' : 'Issued by Maritime Authority'}</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Modal Action Buttons */}
            <div className="flex justify-end space-x-3 px-6 py-4 border-t border-gray-200">
              <button
                onClick={() => {
                  const reviewData = pendingManualReviews.find(r => r.filename === fileViewerData.filename);
                  if (reviewData) {
                    handleManualReviewAction('skip', reviewData);
                    setShowFileViewer(false);
                    setFileViewerData(null);
                  }
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all"
              >
                {language === 'vi' ? 'Bỏ qua' : 'Skip'}
              </button>
              <button
                onClick={() => {
                  const reviewData = pendingManualReviews.find(r => r.filename === fileViewerData.filename);
                  if (reviewData) {
                    handleManualReviewAction('confirm_marine', reviewData);
                    setShowFileViewer(false);
                    setFileViewerData(null);
                  }
                }}
                className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all font-medium"
              >
                {language === 'vi' ? 'Xác nhận Marine Certificate' : 'Confirm Marine Certificate'}
              </button>
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