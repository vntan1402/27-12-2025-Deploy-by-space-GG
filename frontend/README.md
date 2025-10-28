# Ship Management System - Frontend V2

**Version:** 2.0.0  
**Architecture:** Modern React with feature-based structure

---

## 🎯 About This Version

Frontend V2 is a complete rewrite of the Ship Management System frontend with:

- ✅ Clean architecture (feature-based structure)
- ✅ Separation of concerns
- ✅ Reusable components and hooks
- ✅ Centralized API layer
- ✅ Type-safe ready (for future TypeScript migration)
- ✅ Performance optimized
- ✅ Easy to test and maintain

---

## 🏗️ Tech Stack

- **React 18** - UI framework
- **React Router v6** - Routing
- **TailwindCSS** - Styling
- **Axios** - HTTP client
- **Sonner** - Toast notifications
- **Lucide React** - Icons
- **date-fns** - Date utilities

---

## 📂 Project Structure

```
src/
├── components/          # UI Components
│   ├── common/         # Shared components (Button, Input, etc)
│   ├── layout/         # Layout components (Header, Sidebar, etc)
│   └── ui/             # shadcn/ui components (future)
│
├── features/           # Feature modules (one per domain)
│   ├── ship/          # Ship management
│   ├── crew/          # Crew management
│   ├── certificates/  # Certificate management
│   └── ...            # Other features
│
├── hooks/             # Custom React hooks
│   ├── useModal.js    # Modal management
│   ├── useSort.js     # Sorting logic
│   ├── useFetch.js    # Data fetching
│   └── useCRUD.js     # CRUD operations
│
├── services/          # API services
│   ├── api.js         # Axios instance & interceptors
│   ├── authService.js # Auth API calls
│   ├── shipService.js # Ship API calls
│   └── ...            # Other services
│
├── utils/             # Utility functions
│   ├── dateHelpers.js # Date formatting & parsing
│   ├── textHelpers.js # Text manipulation
│   └── validators.js  # Form validation
│
├── contexts/          # React contexts
│   ├── AuthContext.jsx # Auth state management
│   └── ...             # Other contexts
│
├── pages/             # Page components
│   ├── LoginPage.jsx  # Login page
│   ├── HomePage.jsx   # Home page
│   └── ...            # Other pages
│
├── routes/            # Routing configuration
│   └── AppRoutes.jsx  # Main router
│
└── constants/         # Constants & configurations
    ├── options.js     # Dropdown options
    └── api.js         # API endpoints
```

---

## 🚀 Getting Started

### Prerequisites

- Node.js 16+
- Yarn package manager

### Installation

```bash
cd /app/frontend
yarn install
```

### Development

```bash
yarn start
```

Runs on `http://localhost:3000`

### Build

```bash
yarn build
```

Builds for production to `build/` folder

---

## 🔑 Environment Variables

Create `.env` file:

```env
REACT_APP_BACKEND_URL=https://your-backend-url.com
REACT_APP_VERSION=2.0.0
```

---

## 📝 Development Guidelines

### 1. Feature-based Structure

Each feature should be self-contained:

```
features/ship/
├── components/       # Feature-specific components
├── hooks/           # Feature-specific hooks
├── services/        # Feature API calls
└── index.js         # Public exports
```

### 2. Component Guidelines

- Keep components small (< 200 lines)
- One component per file
- Use functional components + hooks
- PropTypes or TypeScript for type checking (future)

### 3. Naming Conventions

- Components: `PascalCase` (e.g., `ShipList.jsx`)
- Hooks: `camelCase` with `use` prefix (e.g., `useShips.js`)
- Services: `camelCase` with `Service` suffix (e.g., `shipService.js`)
- Utils: `camelCase` (e.g., `dateHelpers.js`)

### 4. Import Order

```javascript
// 1. External imports
import React from 'react';
import { useNavigate } from 'react-router-dom';

// 2. Internal imports - absolute
import { useAuth } from 'contexts/AuthContext';
import { shipService } from 'services/shipService';

// 3. Internal imports - relative
import ShipCard from './ShipCard';
import './styles.css';
```

---

## 🧪 Testing (Future)

```bash
yarn test
```

Testing setup will be added in future phases.

---

## 📚 Migration Status

### ✅ Completed (Phase 0)

- [x] Project setup
- [x] Base structure
- [x] Auth system
- [x] Routing
- [x] Basic styling (TailwindCSS)

### 🚧 In Progress

- [ ] Phase 1: Extract utilities from V1
- [ ] Phase 2: Create API service layer
- [ ] Phase 3: Create custom hooks
- [ ] Phase 4: Migrate Ship Management
- [ ] Phase 5: Migrate Crew Management
- [ ] Phase 6: Migrate Certificate Management
- [ ] Phase 7: Migrate Reports & Documents

---

## 🔄 Migrating from V1

V1 code is available at `/app/frontend-v1/` for reference.

When migrating a feature:

1. Create feature structure in `features/`
2. Extract API calls to `services/`
3. Create reusable hooks in `hooks/`
4. Build UI components in `components/`
5. Wire everything together in page components

---

## 🐛 Known Issues

None yet! 🎉

---

## 📖 Learn More

- [React Documentation](https://react.dev)
- [React Router](https://reactrouter.com)
- [TailwindCSS](https://tailwindcss.com)
- [Axios](https://axios-http.com)

---

## 👥 Team

Frontend V2 - Modern Architecture Initiative

---

## 📄 License

Proprietary - Ship Management System
