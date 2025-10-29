# 📋 KẾ HOẠCH HOÀN THIỆN HOME PAGE CHI TIẾT

**Ngày tạo:** 2025-10-29  
**Trạng thái:** 📝 Kế hoạch  
**Thời gian dự kiến:** 1-2 ngày  
**Độ ưu tiên:** Cao (Foundation page)

---

## 🎯 MỤC TIÊU

Hoàn thiện Home Page thành một **Dashboard chuyên nghiệp** với:
- ✅ Navigation menu đầy đủ
- ✅ Statistics cards (tổng quan số liệu)
- ✅ Quick actions panel
- ✅ Recent activities list
- ✅ User profile dropdown
- ✅ Responsive design (mobile/tablet/desktop)

---

## 📊 PHÂN TÍCH TRANG HIỆN TẠI

### Home Page V2 hiện tại (Placeholder)

**File:** `/app/frontend/src/pages/HomePage.jsx`

**Cấu trúc hiện tại:**
```jsx
- Header
  - Logo/Title
  - Language toggle
  - Username + Logout button
- Main Content
  - Welcome message
  - Phase completion info boxes
  - Folder structure display
```

**Vấn đề:**
- ❌ Không có navigation menu
- ❌ Không có dashboard statistics
- ❌ Không có quick actions
- ❌ Chỉ hiển thị thông tin migration
- ❌ Không có sidebar navigation
- ❌ User profile không có dropdown

---

## 🏗️ KIẾN TRÚC MỚI

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│ Header (Top Navigation)                              │
│ - Logo | Breadcrumb | Search | Notifications | User │
├──────────┬──────────────────────────────────────────┤
│          │                                           │
│ Sidebar  │ Main Content Area                        │
│ Menu     │                                           │
│          │ - Page Title + Actions                   │
│ - Home   │ - Statistics Cards (4 cards)             │
│ - Ships  │ - Quick Actions Panel                    │
│ - Crew   │ - Recent Activities                      │
│ - Certs  │ - Charts/Graphs (future)                 │
│ - Docs   │                                           │
│          │                                           │
│          │                                           │
└──────────┴──────────────────────────────────────────┘
```

### Component Structure

```
HomePage
├── Layout (Wrapper)
│   ├── Header
│   │   ├── Logo
│   │   ├── Breadcrumb
│   │   ├── SearchBar (future)
│   │   ├── NotificationBell (future)
│   │   └── UserProfileDropdown
│   │       ├── Profile Info
│   │       ├── Language Toggle
│   │       └── Logout
│   │
│   ├── Sidebar
│   │   ├── Navigation Menu
│   │   │   ├── Dashboard (Home)
│   │   │   ├── Ship Management
│   │   │   ├── Crew Management
│   │   │   ├── Certificates
│   │   │   ├── Reports
│   │   │   ├── Documents
│   │   │   └── Settings
│   │   └── Collapse Toggle
│   │
│   └── MainContent
│       ├── PageHeader
│       │   ├── Title
│       │   └── Action Buttons
│       │
│       ├── StatisticsCards (4 cards)
│       │   ├── Total Ships
│       │   ├── Total Crew
│       │   ├── Expiring Certificates
│       │   └── Pending Reports
│       │
│       ├── QuickActionsPanel
│       │   ├── Add Ship
│       │   ├── Add Crew
│       │   ├── Upload Certificate
│       │   └── View Reports
│       │
│       └── RecentActivitiesPanel
│           └── Activity List (recent actions)
```

---

## 📝 KẾ HOẠCH THỰC HIỆN

### **BƯỚC 1: Tạo Layout Components** (3 giờ)

#### 1.1 Component: `Layout.jsx`

**Mục đích:** Wrapper component cho toàn bộ authenticated pages

**Location:** `/app/frontend/src/components/Layout.jsx`

**Structure:**
```jsx
import Header from './Header';
import Sidebar from './Sidebar';

const Layout = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="flex">
        <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
        
        <main className={`flex-1 transition-all ${sidebarCollapsed ? 'ml-16' : 'ml-64'}`}>
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
```

**Features:**
- ✅ Responsive layout
- ✅ Sidebar collapse/expand
- ✅ Smooth transitions
- ✅ Content area padding

---

#### 1.2 Component: `Header.jsx`

**Mục đích:** Top navigation bar với user profile, notifications, search

**Location:** `/app/frontend/src/components/Header.jsx`

**Props:**
```javascript
{
  // No props needed - uses AuthContext
}
```

**Structure:**
```jsx
<header className="bg-white border-b border-gray-200 sticky top-0 z-50">
  <div className="px-6 py-4 flex items-center justify-between">
    {/* Left: Logo + Title */}
    <div className="flex items-center gap-4">
      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
        <ShipIcon />
      </div>
      <div>
        <h1 className="text-xl font-bold text-gray-800">
          Ship Management System
        </h1>
        <p className="text-xs text-gray-500">Frontend V2.0.0</p>
      </div>
    </div>

    {/* Right: Actions */}
    <div className="flex items-center gap-4">
      {/* Language Toggle */}
      <LanguageToggle />
      
      {/* Notifications (future) */}
      <NotificationBell />
      
      {/* User Profile Dropdown */}
      <UserProfileDropdown />
    </div>
  </div>
</header>
```

**Sub-components:**
- `LanguageToggle` - Đổi ngôn ngữ
- `NotificationBell` - Thông báo (placeholder)
- `UserProfileDropdown` - Profile menu

---

#### 1.3 Component: `UserProfileDropdown.jsx`

**Mục đích:** Dropdown menu cho user profile

**Location:** `/app/frontend/src/components/UserProfileDropdown.jsx`

**UI Structure:**
```jsx
<div className="relative">
  {/* Trigger Button */}
  <button onClick={toggleDropdown}>
    <div className="flex items-center gap-2">
      <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
        {getInitials(user.username)}
      </div>
      <div className="text-left">
        <p className="text-sm font-medium">{user.username}</p>
        <p className="text-xs text-gray-500">{user.role}</p>
      </div>
      <ChevronDownIcon />
    </div>
  </button>

  {/* Dropdown Menu */}
  {isOpen && (
    <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-xl border">
      {/* User Info */}
      <div className="p-4 border-b">
        <p className="font-semibold">{user.full_name}</p>
        <p className="text-sm text-gray-500">{user.email}</p>
        <p className="text-xs text-gray-400 mt-1">{user.role}</p>
      </div>

      {/* Menu Items */}
      <div className="py-2">
        <MenuItem icon={<UserIcon />} onClick={handleProfile}>
          Profile Settings
        </MenuItem>
        <MenuItem icon={<LanguageIcon />} onClick={toggleLanguage}>
          {language === 'vi' ? '🇬🇧 English' : '🇻🇳 Tiếng Việt'}
        </MenuItem>
        <MenuItem icon={<SettingsIcon />} onClick={handleSettings}>
          System Settings
        </MenuItem>
      </div>

      {/* Logout */}
      <div className="border-t">
        <button onClick={logout} className="w-full p-3 text-left text-red-600 hover:bg-red-50">
          <LogoutIcon /> Logout
        </button>
      </div>
    </div>
  )}
</div>
```

**Features:**
- ✅ Click outside to close
- ✅ User avatar với initials
- ✅ User info display
- ✅ Language toggle trong dropdown
- ✅ Profile settings link (placeholder)
- ✅ Logout function

---

#### 1.4 Component: `Sidebar.jsx`

**Mục đích:** Navigation sidebar với menu items

**Location:** `/app/frontend/src/components/Sidebar.jsx`

**Props:**
```javascript
{
  collapsed: boolean,
  onToggle: function
}
```

**Navigation Menu Items:**
```javascript
const menuItems = [
  {
    id: 'dashboard',
    label: { vi: 'Trang chủ', en: 'Dashboard' },
    icon: <HomeIcon />,
    path: '/',
    badge: null
  },
  {
    id: 'ships',
    label: { vi: 'Quản lý tàu', en: 'Ship Management' },
    icon: <ShipIcon />,
    path: '/ships',
    badge: null
  },
  {
    id: 'crew',
    label: { vi: 'Quản lý thuyền viên', en: 'Crew Management' },
    icon: <UsersIcon />,
    path: '/crew',
    badge: null
  },
  {
    id: 'certificates',
    label: { vi: 'Chứng chỉ', en: 'Certificates' },
    icon: <CertificateIcon />,
    path: '/certificates',
    badge: { count: 5, color: 'red' } // Expiring soon
  },
  {
    id: 'reports',
    label: { vi: 'Báo cáo', en: 'Reports' },
    icon: <DocumentIcon />,
    path: '/reports',
    badge: null,
    submenu: [
      { label: 'Survey Reports', path: '/reports/survey' },
      { label: 'Test Reports', path: '/reports/test' }
    ]
  },
  {
    id: 'documents',
    label: { vi: 'Tài liệu', en: 'Documents' },
    icon: <FolderIcon />,
    path: '/documents',
    badge: null,
    submenu: [
      { label: 'Drawings', path: '/documents/drawings' },
      { label: 'Manuals', path: '/documents/manuals' },
      { label: 'Others', path: '/documents/others' }
    ]
  },
  {
    id: 'settings',
    label: { vi: 'Cài đặt', en: 'Settings' },
    icon: <SettingsIcon />,
    path: '/settings',
    badge: null
  }
];
```

**UI Structure:**
```jsx
<aside className={`fixed left-0 top-16 h-full bg-white border-r border-gray-200 transition-all ${
  collapsed ? 'w-16' : 'w-64'
}`}>
  {/* Collapse Toggle Button */}
  <button onClick={onToggle} className="absolute -right-3 top-6 w-6 h-6 bg-white border rounded-full">
    {collapsed ? <ChevronRightIcon /> : <ChevronLeftIcon />}
  </button>

  {/* Navigation Menu */}
  <nav className="p-4 space-y-2">
    {menuItems.map(item => (
      <NavItem 
        key={item.id}
        item={item}
        collapsed={collapsed}
        active={location.pathname === item.path}
      />
    ))}
  </nav>

  {/* Footer Info */}
  {!collapsed && (
    <div className="absolute bottom-4 left-4 right-4 p-3 bg-blue-50 rounded-lg">
      <p className="text-xs text-blue-800">Frontend V2.0.0</p>
      <p className="text-xs text-blue-600">Phase 0-3 Complete</p>
    </div>
  )}
</aside>
```

**Features:**
- ✅ Collapsible sidebar
- ✅ Active route highlighting
- ✅ Badge notifications (expiring certs)
- ✅ Submenu support (future)
- ✅ Icons cho mỗi menu item
- ✅ Smooth transitions
- ✅ Tooltips khi collapsed

**Checklist Bước 1:**
- [ ] Tạo `Layout.jsx`
- [ ] Tạo `Header.jsx`
- [ ] Tạo `UserProfileDropdown.jsx`
- [ ] Tạo `Sidebar.jsx`
- [ ] Tạo `NavItem.jsx` (sub-component)
- [ ] Test responsive behavior
- [ ] Test collapse/expand
- [ ] Lint và fix errors

---

### **BƯỚC 2: Tạo Dashboard Statistics Cards** (2 giờ)

#### 2.1 Component: `StatisticsCard.jsx`

**Mục đích:** Reusable card component cho statistics

**Location:** `/app/frontend/src/components/StatisticsCard.jsx`

**Props:**
```javascript
{
  title: string,              // Card title
  value: number,              // Main value
  icon: ReactElement,         // Icon component
  trend: {                    // Trend info (optional)
    value: number,            // % change
    direction: 'up' | 'down', // Trend direction
    label: string             // Time period
  },
  color: string,              // Color theme
  loading: boolean,           // Loading state
  onClick: function           // Click handler (optional)
}
```

**UI Structure:**
```jsx
<div className={`bg-white rounded-lg shadow-md p-6 border-l-4 cursor-pointer hover:shadow-lg transition-all ${borderColor}`} onClick={onClick}>
  <div className="flex items-center justify-between mb-4">
    <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${bgColor}`}>
      {icon}
    </div>
    
    {trend && (
      <div className={`flex items-center gap-1 text-sm ${trend.direction === 'up' ? 'text-green-600' : 'text-red-600'}`}>
        {trend.direction === 'up' ? <ArrowUpIcon /> : <ArrowDownIcon />}
        <span className="font-semibold">{trend.value}%</span>
      </div>
    )}
  </div>

  <div>
    <p className="text-gray-600 text-sm mb-1">{title}</p>
    {loading ? (
      <div className="h-8 w-24 bg-gray-200 animate-pulse rounded"></div>
    ) : (
      <p className="text-3xl font-bold text-gray-800">{value.toLocaleString()}</p>
    )}
    {trend && <p className="text-xs text-gray-500 mt-2">{trend.label}</p>}
  </div>
</div>
```

**Color Themes:**
```javascript
const colorThemes = {
  blue: {
    border: 'border-blue-500',
    bg: 'bg-blue-100',
    text: 'text-blue-600'
  },
  green: {
    border: 'border-green-500',
    bg: 'bg-green-100',
    text: 'text-green-600'
  },
  yellow: {
    border: 'border-yellow-500',
    bg: 'bg-yellow-100',
    text: 'text-yellow-600'
  },
  red: {
    border: 'border-red-500',
    bg: 'bg-red-100',
    text: 'text-red-600'
  }
};
```

---

#### 2.2 Dashboard Statistics Data

**4 Statistics Cards:**

```javascript
const statisticsData = [
  {
    id: 'total_ships',
    title: { vi: 'Tổng số tàu', en: 'Total Ships' },
    value: 12, // Fetch from backend
    icon: <ShipIcon />,
    color: 'blue',
    trend: { value: 8, direction: 'up', label: 'vs last month' },
    onClick: () => navigate('/ships')
  },
  {
    id: 'total_crew',
    title: { vi: 'Tổng thuyền viên', en: 'Total Crew' },
    value: 245, // Fetch from backend
    icon: <UsersIcon />,
    color: 'green',
    trend: { value: 12, direction: 'up', label: 'vs last month' },
    onClick: () => navigate('/crew')
  },
  {
    id: 'expiring_certificates',
    title: { vi: 'Chứng chỉ sắp hết hạn', en: 'Expiring Certificates' },
    value: 18, // Fetch from backend
    icon: <AlertIcon />,
    color: 'yellow',
    trend: null,
    onClick: () => navigate('/certificates?filter=expiring')
  },
  {
    id: 'pending_reports',
    title: { vi: 'Báo cáo chờ duyệt', en: 'Pending Reports' },
    value: 5, // Fetch from backend
    icon: <DocumentIcon />,
    color: 'red',
    trend: { value: 20, direction: 'down', label: 'vs last week' },
    onClick: () => navigate('/reports?status=pending')
  }
];
```

---

#### 2.3 Fetch Statistics từ Backend

**Option 1: Mock Data (hiện tại)**
```javascript
const [statistics, setStatistics] = useState({
  total_ships: 12,
  total_crew: 245,
  expiring_certificates: 18,
  pending_reports: 5
});
```

**Option 2: Real Backend API (future)**
```javascript
// Add to backend: GET /api/dashboard/statistics
useEffect(() => {
  const fetchStatistics = async () => {
    try {
      const response = await api.get('/api/dashboard/statistics');
      setStatistics(response.data);
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
    }
  };
  
  fetchStatistics();
}, []);
```

**Checklist Bước 2:**
- [ ] Tạo `StatisticsCard.jsx`
- [ ] Tạo statistics data structure
- [ ] Implement mock data
- [ ] Add loading states
- [ ] Test click handlers
- [ ] Test responsive grid
- [ ] Lint và fix errors

---

### **BƯỚC 3: Tạo Quick Actions Panel** (1.5 giờ)

#### 3.1 Component: `QuickActionsPanel.jsx`

**Mục đích:** Panel với quick action buttons

**Location:** `/app/frontend/src/components/QuickActionsPanel.jsx`

**UI Structure:**
```jsx
<div className="bg-white rounded-lg shadow-md p-6">
  <h3 className="text-lg font-semibold text-gray-800 mb-4">
    {language === 'vi' ? 'Thao tác nhanh' : 'Quick Actions'}
  </h3>

  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
    {quickActions.map(action => (
      <QuickActionButton
        key={action.id}
        icon={action.icon}
        label={action.label[language]}
        onClick={action.onClick}
        color={action.color}
      />
    ))}
  </div>
</div>
```

**Quick Actions Data:**
```javascript
const quickActions = [
  {
    id: 'add_ship',
    label: { vi: 'Thêm tàu', en: 'Add Ship' },
    icon: <PlusIcon />,
    color: 'blue',
    onClick: () => navigate('/ships?action=add')
  },
  {
    id: 'add_crew',
    label: { vi: 'Thêm thuyền viên', en: 'Add Crew' },
    icon: <UserPlusIcon />,
    color: 'green',
    onClick: () => navigate('/crew?action=add')
  },
  {
    id: 'upload_certificate',
    label: { vi: 'Upload chứng chỉ', en: 'Upload Certificate' },
    icon: <UploadIcon />,
    color: 'yellow',
    onClick: () => navigate('/certificates?action=upload')
  },
  {
    id: 'view_reports',
    label: { vi: 'Xem báo cáo', en: 'View Reports' },
    icon: <ChartIcon />,
    color: 'purple',
    onClick: () => navigate('/reports')
  }
];
```

---

#### 3.2 Component: `QuickActionButton.jsx`

**Props:**
```javascript
{
  icon: ReactElement,
  label: string,
  onClick: function,
  color: string
}
```

**UI:**
```jsx
<button
  onClick={onClick}
  className={`flex flex-col items-center justify-center p-6 rounded-lg border-2 border-dashed transition-all hover:scale-105 hover:shadow-md ${colorClass}`}
>
  <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-3 ${bgClass}`}>
    {icon}
  </div>
  <p className="text-sm font-medium text-gray-700">{label}</p>
</button>
```

**Checklist Bước 3:**
- [ ] Tạo `QuickActionsPanel.jsx`
- [ ] Tạo `QuickActionButton.jsx`
- [ ] Define actions data
- [ ] Test click handlers
- [ ] Test responsive grid
- [ ] Lint và fix errors

---

### **BƯỚC 4: Tạo Recent Activities Panel** (2 giờ)

#### 4.1 Component: `RecentActivitiesPanel.jsx`

**Mục đích:** Hiển thị recent activities/logs

**Location:** `/app/frontend/src/components/RecentActivitiesPanel.jsx`

**UI Structure:**
```jsx
<div className="bg-white rounded-lg shadow-md p-6">
  <div className="flex items-center justify-between mb-4">
    <h3 className="text-lg font-semibold text-gray-800">
      {language === 'vi' ? 'Hoạt động gần đây' : 'Recent Activities'}
    </h3>
    <button className="text-sm text-blue-600 hover:text-blue-800">
      {language === 'vi' ? 'Xem tất cả' : 'View all'}
    </button>
  </div>

  <div className="space-y-4">
    {activities.length === 0 ? (
      <EmptyState message="No recent activities" />
    ) : (
      activities.map(activity => (
        <ActivityItem key={activity.id} activity={activity} />
      ))
    )}
  </div>
</div>
```

---

#### 4.2 Component: `ActivityItem.jsx`

**Props:**
```javascript
{
  activity: {
    id: string,
    type: 'create' | 'update' | 'delete' | 'upload',
    entity: 'ship' | 'crew' | 'certificate' | 'report',
    description: string,
    user: string,
    timestamp: string,
    icon: ReactElement
  }
}
```

**UI:**
```jsx
<div className="flex items-start gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors">
  <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${iconBg}`}>
    {getActivityIcon(activity.type)}
  </div>

  <div className="flex-1 min-w-0">
    <p className="text-sm font-medium text-gray-800">
      {activity.description}
    </p>
    <div className="flex items-center gap-2 mt-1">
      <p className="text-xs text-gray-500">{activity.user}</p>
      <span className="text-xs text-gray-400">•</span>
      <p className="text-xs text-gray-500">{formatTimeAgo(activity.timestamp)}</p>
    </div>
  </div>

  <button className="text-gray-400 hover:text-gray-600">
    <ChevronRightIcon className="w-5 h-5" />
  </button>
</div>
```

---

#### 4.3 Mock Activities Data

```javascript
const mockActivities = [
  {
    id: '1',
    type: 'create',
    entity: 'ship',
    description: 'Added new ship "PACIFIC OCEAN"',
    user: 'admin1',
    timestamp: '2025-10-29T10:30:00Z'
  },
  {
    id: '2',
    type: 'upload',
    entity: 'certificate',
    description: 'Uploaded certificate for crew "Nguyen Van A"',
    user: 'admin1',
    timestamp: '2025-10-29T09:15:00Z'
  },
  {
    id: '3',
    type: 'update',
    entity: 'crew',
    description: 'Updated crew information for "Tran Van B"',
    user: 'admin1',
    timestamp: '2025-10-28T16:45:00Z'
  },
  {
    id: '4',
    type: 'delete',
    entity: 'report',
    description: 'Deleted test report #TR-2024-001',
    user: 'admin1',
    timestamp: '2025-10-28T14:20:00Z'
  }
];
```

**Checklist Bước 4:**
- [ ] Tạo `RecentActivitiesPanel.jsx`
- [ ] Tạo `ActivityItem.jsx`
- [ ] Create mock activities data
- [ ] Implement time ago formatter
- [ ] Add empty state
- [ ] Test activity types
- [ ] Lint và fix errors

---

### **BƯỚC 5: Update HomePage & Integration** (2 giờ)

#### 5.1 Update HomePage.jsx

**New Structure:**
```jsx
import React from 'react';
import Layout from '../components/Layout';
import StatisticsCard from '../components/StatisticsCard';
import QuickActionsPanel from '../components/QuickActionsPanel';
import RecentActivitiesPanel from '../components/RecentActivitiesPanel';
import { useAuth } from '../contexts/AuthContext';

const HomePage = () => {
  const { user, language } = useAuth();
  const [statistics, setStatistics] = useState({
    total_ships: 12,
    total_crew: 245,
    expiring_certificates: 18,
    pending_reports: 5
  });
  const [loading, setLoading] = useState(false);

  return (
    <Layout>
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800">
          {language === 'vi' 
            ? `Chào mừng trở lại, ${user?.username}!` 
            : `Welcome back, ${user?.username}!`}
        </h1>
        <p className="text-gray-600 mt-1">
          {language === 'vi' 
            ? 'Tổng quan hệ thống quản lý tàu' 
            : 'Ship management system overview'}
        </p>
      </div>

      {/* Statistics Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatisticsCard
          title={language === 'vi' ? 'Tổng số tàu' : 'Total Ships'}
          value={statistics.total_ships}
          icon={<ShipIcon />}
          color="blue"
          loading={loading}
          onClick={() => navigate('/ships')}
        />
        <StatisticsCard
          title={language === 'vi' ? 'Tổng thuyền viên' : 'Total Crew'}
          value={statistics.total_crew}
          icon={<UsersIcon />}
          color="green"
          loading={loading}
          onClick={() => navigate('/crew')}
        />
        <StatisticsCard
          title={language === 'vi' ? 'Chứng chỉ sắp hết hạn' : 'Expiring Certificates'}
          value={statistics.expiring_certificates}
          icon={<AlertIcon />}
          color="yellow"
          loading={loading}
          onClick={() => navigate('/certificates')}
        />
        <StatisticsCard
          title={language === 'vi' ? 'Báo cáo chờ duyệt' : 'Pending Reports'}
          value={statistics.pending_reports}
          icon={<DocumentIcon />}
          color="red"
          loading={loading}
          onClick={() => navigate('/reports')}
        />
      </div>

      {/* Quick Actions */}
      <div className="mb-6">
        <QuickActionsPanel />
      </div>

      {/* Recent Activities */}
      <div className="mb-6">
        <RecentActivitiesPanel />
      </div>

      {/* Migration Progress Info (Optional) */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">
          📊 {language === 'vi' ? 'Tiến độ phát triển' : 'Development Progress'}
        </h3>
        <div className="flex gap-2">
          <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-semibold">
            Phase 0-3 Complete
          </span>
          <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs font-semibold">
            Phase 4 In Progress
          </span>
        </div>
      </div>
    </Layout>
  );
};

export default HomePage;
```

---

#### 5.2 Update AppRoutes.jsx

**Wrap routes with Layout:**
```jsx
import Layout from '../components/Layout';

<Routes>
  {/* Public Routes */}
  <Route path="/login" element={<LoginPage />} />
  
  {/* Protected Routes with Layout */}
  <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
    <Route path="/" element={<HomePage />} />
    <Route path="/ships" element={<ShipManagementPage />} />
    <Route path="/crew" element={<CrewManagementPage />} />
    {/* More routes... */}
  </Route>
</Routes>
```

**Checklist Bước 5:**
- [ ] Update HomePage.jsx với new structure
- [ ] Import all components
- [ ] Add statistics state
- [ ] Test page layout
- [ ] Update AppRoutes if needed
- [ ] Test navigation
- [ ] Lint và fix errors

---

### **BƯỚC 6: Icons & Styling** (1.5 giờ)

#### 6.1 Icons cần thiết

**Install Heroicons (nếu chưa có):**
```bash
cd /app/frontend
yarn add @heroicons/react
```

**Icons List:**
```javascript
import {
  HomeIcon,
  ShipIcon, // Custom or use TruckIcon
  UsersIcon,
  DocumentIcon,
  FolderIcon,
  CogIcon,
  BellIcon,
  SearchIcon,
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PlusIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ChartBarIcon,
  ExclamationIcon
} from '@heroicons/react/outline';
```

---

#### 6.2 TailwindCSS Custom Classes

**Add to `tailwind.config.js`:**
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      },
      spacing: {
        '128': '32rem',
      }
    }
  }
}
```

**Checklist Bước 6:**
- [ ] Install @heroicons/react
- [ ] Import needed icons
- [ ] Test icon display
- [ ] Update Tailwind config
- [ ] Test responsive classes
- [ ] Lint và fix errors

---

### **BƯỚC 7: Responsive Design Testing** (1 giờ)

#### 7.1 Breakpoints Testing

**Test trên các màn hình:**
- Mobile: 375px, 414px
- Tablet: 768px, 1024px
- Desktop: 1280px, 1920px

**Responsive Behaviors:**
```javascript
// Statistics Cards Grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

// Quick Actions Grid
<div className="grid grid-cols-2 md:grid-cols-4 gap-4">

// Sidebar
<aside className="hidden md:block ...">

// Mobile Menu Button
<button className="md:hidden ...">
```

---

#### 7.2 Mobile Optimization

**Features:**
- ✅ Hamburger menu for mobile
- ✅ Collapsible sidebar on mobile
- ✅ Touch-friendly buttons (min 44px)
- ✅ Responsive typography
- ✅ Stack cards vertically on mobile

**Checklist Bước 7:**
- [ ] Test on mobile (375px)
- [ ] Test on tablet (768px)
- [ ] Test on desktop (1920px)
- [ ] Verify touch targets
- [ ] Test navigation on mobile
- [ ] Fix any layout issues

---

### **BƯỚC 8: Final Testing & Polish** (1 giờ)

#### 8.1 Functionality Testing

**Test Cases:**
1. ✅ Navigate between pages via sidebar
2. ✅ Click statistics cards to navigate
3. ✅ Click quick action buttons
4. ✅ View recent activities
5. ✅ User profile dropdown opens/closes
6. ✅ Language toggle works
7. ✅ Logout functionality
8. ✅ Sidebar collapse/expand
9. ✅ Responsive menu on mobile

---

#### 8.2 UI/UX Polish

**Improvements:**
- ✅ Smooth transitions (300ms)
- ✅ Hover effects on interactive elements
- ✅ Loading states for async data
- ✅ Empty states cho activities
- ✅ Tooltips for collapsed sidebar
- ✅ Focus states for accessibility
- ✅ Proper z-index layering

**Checklist Bước 8:**
- [ ] Test all functionality
- [ ] Check for console errors
- [ ] Verify smooth animations
- [ ] Test accessibility (tab navigation)
- [ ] Take final screenshots
- [ ] Lint entire project
- [ ] Fix all warnings

---

## 📊 TIMELINE

### Ngày 1 (8 giờ)
- **Morning (4h):** Bước 1 - Layout Components
- **Afternoon (4h):** Bước 2 - Statistics Cards + Bước 3 - Quick Actions

### Ngày 2 (5 giờ)
- **Morning (3h):** Bước 4 - Recent Activities + Bước 5 - Integration
- **Afternoon (2h):** Bước 6 - Icons + Bước 7 - Responsive Testing

### Bonus Time (1-2 giờ)
- Bước 8 - Final Testing & Polish

**Tổng thời gian:** 13-15 giờ (1.5-2 ngày)

---

## ✅ CHECKLIST TỔNG THỂ

### Components (10 files)
- [ ] `Layout.jsx` - Main layout wrapper
- [ ] `Header.jsx` - Top navigation bar
- [ ] `UserProfileDropdown.jsx` - User menu
- [ ] `Sidebar.jsx` - Navigation sidebar
- [ ] `NavItem.jsx` - Sidebar menu item
- [ ] `StatisticsCard.jsx` - Statistics display
- [ ] `QuickActionsPanel.jsx` - Quick actions
- [ ] `QuickActionButton.jsx` - Action button
- [ ] `RecentActivitiesPanel.jsx` - Activities list
- [ ] `ActivityItem.jsx` - Activity item

### Pages
- [ ] Update `HomePage.jsx` - New dashboard

### Integration
- [ ] Update AppRoutes (if needed)
- [ ] Test navigation flow
- [ ] Test authentication flow

### Styling
- [ ] Install @heroicons/react
- [ ] Update Tailwind config
- [ ] Add custom CSS if needed

### Testing
- [ ] Desktop testing
- [ ] Tablet testing
- [ ] Mobile testing
- [ ] Cross-browser testing
- [ ] Accessibility testing

---

## 🎯 TIÊU CHÍ THÀNH CÔNG

### Functional Requirements ✅

1. **Navigation**
   - ✅ Sidebar menu hoạt động
   - ✅ Active route highlighting
   - ✅ Click menu items để navigate
   - ✅ Collapse/expand sidebar

2. **Dashboard**
   - ✅ Statistics cards hiển thị data
   - ✅ Click cards để navigate
   - ✅ Loading states
   - ✅ Empty states

3. **User Profile**
   - ✅ Dropdown menu hoạt động
   - ✅ Language toggle
   - ✅ Logout function
   - ✅ User info display

4. **Quick Actions**
   - ✅ Action buttons hoạt động
   - ✅ Navigate to correct pages
   - ✅ Hover effects

5. **Recent Activities**
   - ✅ Activities list display
   - ✅ Time ago formatting
   - ✅ Empty state

### Technical Requirements ✅

1. **Code Quality**
   - ✅ All components modular
   - ✅ Reusable components
   - ✅ Clean code
   - ✅ ESLint pass

2. **Performance**
   - ✅ Fast page load
   - ✅ Smooth animations
   - ✅ No unnecessary re-renders

3. **Responsive**
   - ✅ Works on mobile
   - ✅ Works on tablet
   - ✅ Works on desktop

---

## 📝 GHI CHÚ

### Data Source

**Current:** Mock data (placeholder)
```javascript
const mockStatistics = {
  total_ships: 12,
  total_crew: 245,
  expiring_certificates: 18,
  pending_reports: 5
};
```

**Future:** Real backend API
```javascript
GET /api/dashboard/statistics
Response: {
  total_ships: 12,
  total_crew: 245,
  expiring_certificates: 18,
  pending_reports: 5,
  activities: [...]
}
```

### Design System

**Colors:**
- Primary: Blue (#3B82F6)
- Success: Green (#10B981)
- Warning: Yellow (#F59E0B)
- Danger: Red (#EF4444)
- Gray: (#6B7280)

**Spacing:**
- Card padding: 6 (1.5rem / 24px)
- Section gap: 6 (1.5rem / 24px)
- Grid gap: 4-6 (1-1.5rem)

**Typography:**
- Page title: text-3xl (30px)
- Section title: text-lg (18px)
- Body: text-sm (14px)
- Small: text-xs (12px)

---

## 🚀 SAU KHI HOÀN THÀNH

Home Page hoàn thiện sẽ:
- ✅ Có navigation sidebar đầy đủ
- ✅ Hiển thị dashboard statistics
- ✅ Có quick actions panel
- ✅ Hiển thị recent activities
- ✅ Professional UI/UX
- ✅ Fully responsive
- ✅ Ready cho Phase 4 (Ship Management)

**Next Steps:**
- Implement backend API cho statistics
- Add real activities tracking
- Implement notifications system
- Build Ship Management feature (Phase 4)

---

**Người tạo kế hoạch:** AI Engineer  
**Ngày tạo:** 2025-10-29  
**Status:** Ready for Implementation  
**Ước tính:** 1.5-2 ngày

🎨 **Let's build a professional Home Page!**
