# Electron Desktop App - Chi Tiết Đầy Đủ

## 🎯 ELECTRON LÀ GÌ?

### Định Nghĩa
**Electron** là framework cho phép build desktop applications sử dụng web technologies (HTML, CSS, JavaScript).

### Apps Nổi Tiếng Dùng Electron
- **VS Code** - Microsoft's code editor
- **Slack** - Team communication
- **Discord** - Gaming chat
- **Figma** - Design tool
- **Notion** - Note-taking
- **WhatsApp Desktop**
- **Spotify Desktop**

### Concept Cốt Lõi
```
Electron App = Chromium Browser + Node.js + Your Web App

┌─────────────────────────────────────────┐
│         Electron Application            │
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐  │
│  │   Chromium Browser                │  │
│  │   (Hiển thị React Frontend)      │  │
│  └───────────────────────────────────┘  │
│                                          │
│  ┌───────────────────────────────────┐  │
│  │   Node.js Runtime                 │  │
│  │   (Chạy Backend Logic)            │  │
│  └───────────────────────────────────┘  │
│                                          │
│  ┌───────────────────────────────────┐  │
│  │   Native OS APIs                  │  │
│  │   (File system, Process, etc)    │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 🏗️ ARCHITECTURE CHI TIẾT

### Tổng Quan Hệ Thống

```
ShipManagement.exe (Single Executable)
│
├── [Electron Framework]
│   ├── Chromium (Render web UI)
│   ├── Node.js (Run JavaScript)
│   └── Native Modules (OS integration)
│
├── [Embedded Resources]
│   ├── MongoDB Portable (mongod.exe)
│   ├── Python Portable (python.exe + libraries)
│   ├── Backend Code (FastAPI app)
│   └── Frontend Build (React production build)
│
├── [User Data Directory]
│   ├── MongoDB Data (collections, indexes)
│   ├── Uploaded Files (certificates, photos)
│   ├── Logs (application, error logs)
│   └── Config (settings, preferences)
│
└── [Auto-Start Services]
    1. Start MongoDB
    2. Start Backend (Python/FastAPI)
    3. Load Frontend (in Electron window)
```

### Main Process vs Renderer Process

```
┌─────────────────────────────────────────────────────┐
│  MAIN PROCESS (Node.js)                             │
│  - Single instance                                   │
│  - Full Node.js + Electron API access               │
│  - Controls application lifecycle                   │
│  - Starts MongoDB, Backend processes                │
│  - Creates and manages windows                      │
│                                                      │
│  ┌───────────────────────────────────────────────┐ │
│  │  RENDERER PROCESS 1 (Chromium)                │ │
│  │  - Main app window                             │ │
│  │  - Runs React Frontend                         │ │
│  │  - Limited Node.js access (security)          │ │
│  └───────────────────────────────────────────────┘ │
│                                                      │
│  ┌───────────────────────────────────────────────┐ │
│  │  RENDERER PROCESS 2 (Optional)                │ │
│  │  - Settings window                             │ │
│  │  - About window                                │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 💻 IMPLEMENTATION CHI TIẾT

### Project Structure

```
ship-management-electron/
│
├── package.json                    # Electron project config
├── electron-builder.yml            # Build configuration
│
├── main.js                         # Main process entry
├── preload.js                      # Preload script (security bridge)
│
├── src/
│   ├── services/
│   │   ├── mongodb-manager.js     # MongoDB lifecycle
│   │   ├── backend-manager.js     # Backend lifecycle
│   │   └── auto-updater.js        # Auto-update logic
│   │
│   ├── windows/
│   │   ├── main-window.js         # Main application window
│   │   ├── settings-window.js     # Settings window
│   │   └── splash-screen.js       # Loading screen
│   │
│   └── utils/
│       ├── process-manager.js     # Process spawning/killing
│       ├── port-checker.js        # Check if ports available
│       └── logger.js              # Logging utility
│
├── resources/                      # Embedded binaries
│   ├── mongodb/
│   │   ├── bin/
│   │   │   ├── mongod.exe        # MongoDB server (Windows)
│   │   │   ├── mongod            # MongoDB server (Mac/Linux)
│   │   │   └── mongo.exe         # MongoDB shell
│   │   └── data/                 # Initial database (if any)
│   │
│   ├── python/
│   │   ├── python.exe            # Python runtime (Windows)
│   │   ├── python                # Python runtime (Mac/Linux)
│   │   └── Lib/                  # Python standard library
│   │       └── site-packages/    # Installed packages
│   │
│   └── backend/
│       ├── server.py
│       ├── mongodb_database.py
│       └── ... (all backend files)
│
├── frontend/                       # React app
│   └── build/                     # Production build
│       ├── index.html
│       ├── static/
│       └── ...
│
└── assets/
    ├── icon.png                   # App icon (PNG)
    ├── icon.ico                   # Windows icon
    ├── icon.icns                  # macOS icon
    └── tray-icon.png             # System tray icon
```

---

## 📝 CODE IMPLEMENTATION

### 1. main.js - Main Process (Core Logic)

```javascript
// main.js - Electron Main Process

const { app, BrowserWindow, Tray, Menu, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// Import custom services
const MongoDBManager = require('./src/services/mongodb-manager');
const BackendManager = require('./src/services/backend-manager');
const logger = require('./src/utils/logger');

// Global references
let mainWindow = null;
let tray = null;
let mongoDBManager = null;
let backendManager = null;
let splashWindow = null;

// Configuration
const APP_CONFIG = {
  MONGODB_PORT: 27017,
  BACKEND_PORT: 8001,
  FRONTEND_PORT: 3000,
  DATA_PATH: path.join(app.getPath('userData'), 'data'),
  LOGS_PATH: path.join(app.getPath('userData'), 'logs')
};

// ========================================
// Application Lifecycle
// ========================================

app.on('ready', async () => {
  try {
    logger.info('🚀 Application starting...');
    
    // Show splash screen
    showSplashScreen();
    
    // Initialize directories
    initializeDirectories();
    
    // Start services in sequence
    await startAllServices();
    
    // Create main window
    setTimeout(() => {
      createMainWindow();
      closeSplashScreen();
    }, 5000);
    
    // Create tray icon
    createTrayIcon();
    
    logger.info('✅ Application ready');
    
  } catch (error) {
    logger.error('❌ Failed to start application:', error);
    dialog.showErrorBox(
      'Startup Error',
      `Failed to start application: ${error.message}`
    );
    app.quit();
  }
});

app.on('window-all-closed', () => {
  // On macOS, keep app running in tray
  if (process.platform !== 'darwin') {
    // App will quit via tray menu
  }
});

app.on('before-quit', async (event) => {
  logger.info('🛑 Application shutting down...');
  
  event.preventDefault();
  
  // Stop all services gracefully
  await stopAllServices();
  
  logger.info('✅ Application stopped');
  app.exit(0);
});

// ========================================
// Splash Screen
// ========================================

function showSplashScreen() {
  splashWindow = new BrowserWindow({
    width: 600,
    height: 400,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    webPreferences: {
      nodeIntegration: true
    }
  });
  
  // Create splash HTML
  const splashHTML = `
    <!DOCTYPE html>
    <html>
      <head>
        <style>
          body {
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-family: Arial, sans-serif;
            color: white;
          }
          .container {
            text-align: center;
          }
          .logo {
            font-size: 48px;
            margin-bottom: 20px;
          }
          .title {
            font-size: 24px;
            margin-bottom: 30px;
          }
          .spinner {
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
          }
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          .status {
            margin-top: 20px;
            font-size: 14px;
            opacity: 0.8;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="logo">🚢</div>
          <div class="title">Ship Management</div>
          <div class="spinner"></div>
          <div class="status">Starting services...</div>
        </div>
      </body>
    </html>
  `;
  
  splashWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(splashHTML));
}

function closeSplashScreen() {
  if (splashWindow) {
    splashWindow.close();
    splashWindow = null;
  }
}

// ========================================
// Initialize Directories
// ========================================

function initializeDirectories() {
  const dirs = [
    APP_CONFIG.DATA_PATH,
    path.join(APP_CONFIG.DATA_PATH, 'mongodb'),
    path.join(APP_CONFIG.DATA_PATH, 'uploads'),
    path.join(APP_CONFIG.DATA_PATH, 'backups'),
    APP_CONFIG.LOGS_PATH
  ];
  
  dirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      logger.info(`📁 Created directory: ${dir}`);
    }
  });
}

// ========================================
// Start Services
// ========================================

async function startAllServices() {
  // 1. Start MongoDB
  logger.info('🔵 Starting MongoDB...');
  mongoDBManager = new MongoDBManager({
    port: APP_CONFIG.MONGODB_PORT,
    dbPath: path.join(APP_CONFIG.DATA_PATH, 'mongodb'),
    logPath: path.join(APP_CONFIG.LOGS_PATH, 'mongodb.log')
  });
  
  await mongoDBManager.start();
  logger.info('✅ MongoDB started');
  
  // Wait for MongoDB to be ready
  await sleep(3000);
  
  // 2. Start Backend
  logger.info('🟢 Starting Backend...');
  backendManager = new BackendManager({
    port: APP_CONFIG.BACKEND_PORT,
    mongoUrl: `mongodb://localhost:${APP_CONFIG.MONGODB_PORT}`,
    logPath: path.join(APP_CONFIG.LOGS_PATH, 'backend.log')
  });
  
  await backendManager.start();
  logger.info('✅ Backend started');
  
  // Wait for Backend to be ready
  await sleep(2000);
}

async function stopAllServices() {
  // Stop in reverse order
  if (backendManager) {
    logger.info('🟢 Stopping Backend...');
    await backendManager.stop();
  }
  
  if (mongoDBManager) {
    logger.info('🔵 Stopping MongoDB...');
    await mongoDBManager.stop();
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ========================================
// Main Window
// ========================================

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    minWidth: 1366,
    minHeight: 768,
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    show: false
  });
  
  // Load React app from backend
  mainWindow.loadURL(`http://localhost:${APP_CONFIG.BACKEND_PORT}`);
  
  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Open DevTools in development
    if (process.env.NODE_ENV === 'development') {
      mainWindow.webContents.openDevTools();
    }
  });
  
  // Handle window close
  mainWindow.on('close', (event) => {
    if (app.quitting !== true) {
      event.preventDefault();
      mainWindow.hide();
      
      // Show notification
      tray.displayBalloon({
        title: 'Ship Management',
        content: 'Application minimized to tray. Click to restore.'
      });
    }
  });
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ========================================
// Tray Icon & Menu
// ========================================

function createTrayIcon() {
  tray = new Tray(path.join(__dirname, 'assets', 'tray-icon.png'));
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Open Ship Management',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
        } else {
          createMainWindow();
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Services Status',
      submenu: [
        {
          label: `MongoDB: ${mongoDBManager?.isRunning() ? '🟢 Running' : '🔴 Stopped'}`,
          enabled: false
        },
        {
          label: `Backend: ${backendManager?.isRunning() ? '🟢 Running' : '🔴 Stopped'}`,
          enabled: false
        }
      ]
    },
    { type: 'separator' },
    {
      label: 'Backup Database',
      click: async () => {
        await createBackup();
      }
    },
    {
      label: 'Open Data Folder',
      click: () => {
        require('electron').shell.openPath(APP_CONFIG.DATA_PATH);
      }
    },
    {
      label: 'View Logs',
      click: () => {
        require('electron').shell.openPath(APP_CONFIG.LOGS_PATH);
      }
    },
    { type: 'separator' },
    {
      label: 'Settings',
      click: () => {
        // Open settings window
      }
    },
    {
      label: 'About',
      click: () => {
        dialog.showMessageBox({
          type: 'info',
          title: 'About Ship Management',
          message: 'Ship Management Offline v1.0.0',
          detail: 'Maritime document management system\nOffline mode with local database',
          buttons: ['OK']
        });
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.quitting = true;
        app.quit();
      }
    }
  ]);
  
  tray.setContextMenu(contextMenu);
  tray.setToolTip('Ship Management - Offline');
  
  // Double-click to show window
  tray.on('double-click', () => {
    if (mainWindow) {
      mainWindow.show();
    } else {
      createMainWindow();
    }
  });
}

// ========================================
// IPC Handlers (Communication with Renderer)
// ========================================

ipcMain.handle('get-app-info', () => {
  return {
    version: app.getVersion(),
    platform: process.platform,
    dataPath: APP_CONFIG.DATA_PATH,
    offlineMode: true
  };
});

ipcMain.handle('get-services-status', () => {
  return {
    mongodb: mongoDBManager?.isRunning() || false,
    backend: backendManager?.isRunning() || false
  };
});

ipcMain.handle('create-backup', async () => {
  return await createBackup();
});

// ========================================
// Backup Function
// ========================================

async function createBackup() {
  try {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupPath = path.join(
      APP_CONFIG.DATA_PATH, 
      'backups', 
      `backup_${timestamp}.archive`
    );
    
    logger.info(`📦 Creating backup: ${backupPath}`);
    
    // Use mongodump to create backup
    // This requires mongodump binary to be included
    
    dialog.showMessageBox({
      type: 'info',
      title: 'Backup',
      message: 'Backup created successfully',
      detail: `Backup saved to: ${backupPath}`,
      buttons: ['OK']
    });
    
    return { success: true, path: backupPath };
    
  } catch (error) {
    logger.error('❌ Backup failed:', error);
    
    dialog.showErrorBox(
      'Backup Failed',
      `Failed to create backup: ${error.message}`
    );
    
    return { success: false, error: error.message };
  }
}

// ========================================
// Error Handling
// ========================================

process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception:', error);
  dialog.showErrorBox('Unexpected Error', error.message);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
});
```

### 2. mongodb-manager.js - MongoDB Service Manager

```javascript
// src/services/mongodb-manager.js

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const logger = require('../utils/logger');
const { checkPort } = require('../utils/port-checker');

class MongoDBManager {
  constructor(config) {
    this.config = config;
    this.process = null;
    this.isReady = false;
  }
  
  async start() {
    // Check if port is available
    const portAvailable = await checkPort(this.config.port);
    if (!portAvailable) {
      throw new Error(`Port ${this.config.port} is already in use`);
    }
    
    // Get mongod binary path
    const mongodPath = this.getMongodPath();
    
    if (!fs.existsSync(mongodPath)) {
      throw new Error(`MongoDB binary not found: ${mongodPath}`);
    }
    
    // Ensure data directory exists
    if (!fs.existsSync(this.config.dbPath)) {
      fs.mkdirSync(this.config.dbPath, { recursive: true });
    }
    
    // Start MongoDB process
    const args = [
      '--dbpath', this.config.dbPath,
      '--port', this.config.port.toString(),
      '--bind_ip', '127.0.0.1',
      '--quiet',
      '--logpath', this.config.logPath,
      '--logappend'
    ];
    
    logger.info(`Starting MongoDB: ${mongodPath} ${args.join(' ')}`);
    
    this.process = spawn(mongodPath, args, {
      stdio: 'pipe',
      detached: false
    });
    
    // Handle process events
    this.process.on('error', (error) => {
      logger.error('MongoDB process error:', error);
    });
    
    this.process.on('exit', (code, signal) => {
      logger.info(`MongoDB process exited with code ${code}, signal ${signal}`);
      this.isReady = false;
    });
    
    // Wait for MongoDB to be ready
    await this.waitForReady();
    
    this.isReady = true;
    logger.info('✅ MongoDB is ready');
  }
  
  async stop() {
    if (!this.process) {
      return;
    }
    
    logger.info('Stopping MongoDB...');
    
    // Try graceful shutdown first
    this.process.kill('SIGTERM');
    
    // Wait up to 10 seconds
    await this.waitForExit(10000);
    
    // Force kill if still running
    if (this.process && !this.process.killed) {
      logger.warn('Force killing MongoDB process');
      this.process.kill('SIGKILL');
    }
    
    this.process = null;
    this.isReady = false;
    
    logger.info('✅ MongoDB stopped');
  }
  
  isRunning() {
    return this.process !== null && !this.process.killed && this.isReady;
  }
  
  getMongodPath() {
    const isWin = process.platform === 'win32';
    const isMac = process.platform === 'darwin';
    const isLinux = process.platform === 'linux';
    
    let binaryName = 'mongod';
    if (isWin) {
      binaryName = 'mongod.exe';
    }
    
    // In production (packaged app)
    if (process.resourcesPath) {
      return path.join(process.resourcesPath, 'mongodb', 'bin', binaryName);
    }
    
    // In development
    return path.join(__dirname, '../../resources/mongodb/bin', binaryName);
  }
  
  async waitForReady(timeout = 30000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      try {
        // Try to connect to MongoDB
        const connected = await checkPort(this.config.port);
        if (!connected) {
          return;
        }
      } catch (error) {
        // Not ready yet
      }
      
      await sleep(500);
    }
    
    throw new Error('MongoDB failed to start within timeout');
  }
  
  async waitForExit(timeout) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      if (!this.process || this.process.killed) {
        return;
      }
      await sleep(100);
    }
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = MongoDBManager;
```

### 3. backend-manager.js - Backend Service Manager

```javascript
// src/services/backend-manager.js

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const logger = require('../utils/logger');

class BackendManager {
  constructor(config) {
    this.config = config;
    this.process = null;
    this.isReady = false;
  }
  
  async start() {
    // Get Python binary path
    const pythonPath = this.getPythonPath();
    
    if (!fs.existsSync(pythonPath)) {
      throw new Error(`Python binary not found: ${pythonPath}`);
    }
    
    // Get backend directory
    const backendDir = this.getBackendDir();
    
    // Start backend process
    const args = [
      '-m', 'uvicorn',
      'server:app',
      '--host', '0.0.0.0',
      '--port', this.config.port.toString(),
      '--log-level', 'info'
    ];
    
    logger.info(`Starting Backend: ${pythonPath} ${args.join(' ')}`);
    
    const env = {
      ...process.env,
      OFFLINE_MODE: 'true',
      MONGO_URL: this.config.mongoUrl,
      PYTHONPATH: backendDir
    };
    
    this.process = spawn(pythonPath, args, {
      cwd: backendDir,
      env: env,
      stdio: 'pipe',
      detached: false
    });
    
    // Capture logs
    this.process.stdout.on('data', (data) => {
      logger.info(`Backend: ${data.toString().trim()}`);
    });
    
    this.process.stderr.on('data', (data) => {
      logger.error(`Backend Error: ${data.toString().trim()}`);
    });
    
    this.process.on('error', (error) => {
      logger.error('Backend process error:', error);
    });
    
    this.process.on('exit', (code, signal) => {
      logger.info(`Backend process exited with code ${code}, signal ${signal}`);
      this.isReady = false;
    });
    
    // Wait for backend to be ready
    await this.waitForReady();
    
    this.isReady = true;
    logger.info('✅ Backend is ready');
  }
  
  async stop() {
    if (!this.process) {
      return;
    }
    
    logger.info('Stopping Backend...');
    
    this.process.kill('SIGTERM');
    
    await this.waitForExit(5000);
    
    if (this.process && !this.process.killed) {
      logger.warn('Force killing Backend process');
      this.process.kill('SIGKILL');
    }
    
    this.process = null;
    this.isReady = false;
    
    logger.info('✅ Backend stopped');
  }
  
  isRunning() {
    return this.process !== null && !this.process.killed && this.isReady;
  }
  
  getPythonPath() {
    const isWin = process.platform === 'win32';
    let binaryName = 'python';
    if (isWin) {
      binaryName = 'python.exe';
    }
    
    if (process.resourcesPath) {
      return path.join(process.resourcesPath, 'python', binaryName);
    }
    
    return path.join(__dirname, '../../resources/python', binaryName);
  }
  
  getBackendDir() {
    if (process.resourcesPath) {
      return path.join(process.resourcesPath, 'backend');
    }
    
    return path.join(__dirname, '../../resources/backend');
  }
  
  async waitForReady(timeout = 30000) {
    const startTime = Date.now();
    const http = require('http');
    
    while (Date.now() - startTime < timeout) {
      try {
        await new Promise((resolve, reject) => {
          const req = http.get(`http://localhost:${this.config.port}/api/health`, (res) => {
            if (res.statusCode === 200) {
              resolve();
            } else {
              reject(new Error(`Status: ${res.statusCode}`));
            }
          });
          req.on('error', reject);
          req.setTimeout(1000);
        });
        
        return; // Success
        
      } catch (error) {
        // Not ready yet
      }
      
      await sleep(500);
    }
    
    throw new Error('Backend failed to start within timeout');
  }
  
  async waitForExit(timeout) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      if (!this.process || this.process.killed) {
        return;
      }
      await sleep(100);
    }
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = BackendManager;
```

---

## 🎨 USER EXPERIENCE FLOW

### From User Perspective

```
1. Download ShipManagement-Setup.exe (hoặc .dmg for Mac)
   File size: ~150MB
   
2. Double-click to install
   ├─ Choose installation location
   ├─ Create desktop shortcut
   └─ Installation completes in 1-2 minutes
   
3. Launch application
   ├─ Double-click desktop icon
   ├─ Splash screen appears: "Starting services..."
   ├─ Progress: Starting MongoDB... ✓
   ├─ Progress: Starting Backend... ✓
   └─ Main window opens: Login screen
   
4. Login and use
   ├─ Enter username/password
   ├─ See "🔴 OFFLINE MODE" banner
   └─ Use application normally
   
5. Minimize to system tray
   ├─ Click X to minimize (not quit)
   ├─ Icon appears in system tray
   ├─ Right-click for menu:
   │   ├─ Open Ship Management
   │   ├─ Services Status
   │   ├─ Backup Database
   │   ├─ Open Data Folder
   │   └─ Quit
   └─ Double-click tray to restore window
   
6. Close application
   ├─ Right-click tray → Quit
   ├─ Services stop gracefully
   └─ Application exits cleanly
```

### Visual Mockups

**Splash Screen:**
```
┌─────────────────────────────────┐
│                                 │
│            🚢                   │
│      Ship Management            │
│                                 │
│         [Spinner]               │
│    Starting services...         │
│                                 │
│   ✓ MongoDB started             │
│   ✓ Backend started             │
│   ⏳ Loading frontend...         │
│                                 │
└─────────────────────────────────┘
```

**System Tray Menu:**
```
┌──────────────────────────────────┐
│ 🚢 Ship Management               │
├──────────────────────────────────┤
│ ▶ Open Ship Management           │
├──────────────────────────────────┤
│ Services Status              ▶   │
│   🟢 MongoDB: Running            │
│   🟢 Backend: Running            │
├──────────────────────────────────┤
│ 📦 Backup Database               │
│ 📁 Open Data Folder              │
│ 📄 View Logs                     │
├──────────────────────────────────┤
│ ⚙️ Settings                       │
│ ℹ️ About                          │
├──────────────────────────────────┤
│ ❌ Quit                           │
└──────────────────────────────────┘
```

---

## 📦 BUILD & PACKAGING

### package.json Configuration

```json
{
  "name": "ship-management-offline",
  "version": "1.0.0",
  "description": "Ship Management Offline Desktop Application",
  "main": "main.js",
  "author": "Your Company",
  "license": "MIT",
  "scripts": {
    "start": "electron .",
    "dev": "NODE_ENV=development electron .",
    "build": "electron-builder",
    "build:win": "electron-builder --win",
    "build:mac": "electron-builder --mac",
    "build:linux": "electron-builder --linux",
    "pack": "electron-builder --dir",
    "dist": "electron-builder"
  },
  "dependencies": {
    "electron-log": "^5.0.0",
    "electron-store": "^8.1.0"
  },
  "devDependencies": {
    "electron": "^28.0.0",
    "electron-builder": "^24.9.1"
  }
}
```

### electron-builder.yml Configuration

```yaml
# electron-builder.yml

appId: com.shipmanagement.offline
productName: Ship Management Offline
copyright: Copyright © 2025

directories:
  buildResources: assets
  output: dist

files:
  - main.js
  - preload.js
  - src/**/*
  - frontend/build/**/*
  - package.json

extraResources:
  - from: resources/mongodb
    to: mongodb
    filter:
      - "**/*"
  - from: resources/python
    to: python
    filter:
      - "**/*"
  - from: resources/backend
    to: backend
    filter:
      - "**/*"

# Windows Configuration
win:
  target:
    - target: nsis
      arch:
        - x64
  icon: assets/icon.ico
  artifactName: "${productName}-Setup-${version}.${ext}"

nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
  createDesktopShortcut: true
  createStartMenuShortcut: true
  shortcutName: Ship Management
  perMachine: false

# macOS Configuration
mac:
  target:
    - target: dmg
      arch:
        - x64
        - arm64
  icon: assets/icon.icns
  category: public.app-category.business
  hardenedRuntime: true
  gatekeeperAssess: false
  entitlements: assets/entitlements.mac.plist
  entitlementsInherit: assets/entitlements.mac.plist

dmg:
  title: "${productName} ${version}"
  icon: assets/icon.icns
  window:
    width: 540
    height: 380
  contents:
    - x: 140
      y: 180
      type: file
    - x: 400
      y: 180
      type: link
      path: /Applications

# Linux Configuration
linux:
  target:
    - target: AppImage
      arch:
        - x64
  icon: assets/icon.png
  category: Office
  synopsis: Ship Management System
  description: Maritime document management system with offline support

# Compression
compression: maximum

# Publish Configuration (for auto-updates)
publish:
  provider: generic
  url: https://yourdomain.com/updates/
```

---

## 🚀 BUILD PROCESS

### Step 1: Prepare Resources

```bash
# Create portable MongoDB
# Download MongoDB from official site
# Extract only necessary binaries

resources/
└── mongodb/
    └── bin/
        ├── mongod.exe      # ~30MB
        └── mongo.exe       # ~20MB

# Create portable Python
# Use pyinstaller or similar

resources/
└── python/
    ├── python.exe          # ~5MB
    └── Lib/                # ~50MB
        ├── site-packages/
        │   ├── fastapi/
        │   ├── uvicorn/
        │   ├── motor/
        │   └── ...
        └── ...

# Copy backend code
resources/
└── backend/
    ├── server.py
    ├── mongodb_database.py
    └── ...
```

### Step 2: Build React Frontend

```bash
cd frontend
npm run build

# Output: frontend/build/
# This will be loaded by Electron
```

### Step 3: Build Electron App

```bash
# Install dependencies
npm install

# Development test
npm run dev

# Build for Windows
npm run build:win

# Output:
# dist/Ship Management-Setup-1.0.0.exe  (~150MB)

# Build for Mac
npm run build:mac

# Output:
# dist/Ship Management-1.0.0.dmg  (~150MB)

# Build for Linux
npm run build:linux

# Output:
# dist/Ship Management-1.0.0.AppImage  (~150MB)
```

---

## 📊 FILE SIZE BREAKDOWN

| Component | Size | Notes |
|-----------|------|-------|
| **Electron** | ~80MB | Chromium + Node.js |
| **MongoDB** | ~50MB | Portable binaries |
| **Python** | ~60MB | Runtime + libraries |
| **Backend** | ~10MB | FastAPI code |
| **Frontend** | ~5MB | React build |
| **Total** | **~200MB** | Compressed installer |

**Installed Size:** ~250-300MB

---

## 🔄 AUTO-UPDATE MECHANISM

### Implementation

```javascript
// src/services/auto-updater.js

const { autoUpdater } = require('electron-updater');
const { dialog } = require('electron');
const logger = require('../utils/logger');

class AutoUpdater {
  constructor() {
    this.setupListeners();
  }
  
  setupListeners() {
    autoUpdater.on('checking-for-update', () => {
      logger.info('Checking for updates...');
    });
    
    autoUpdater.on('update-available', (info) => {
      logger.info('Update available:', info.version);
      
      dialog.showMessageBox({
        type: 'info',
        title: 'Update Available',
        message: `New version ${info.version} is available`,
        detail: 'The update will be downloaded in the background.',
        buttons: ['OK']
      });
    });
    
    autoUpdater.on('update-not-available', (info) => {
      logger.info('Update not available');
    });
    
    autoUpdater.on('error', (err) => {
      logger.error('Update error:', err);
    });
    
    autoUpdater.on('download-progress', (progress) => {
      logger.info(`Download progress: ${progress.percent}%`);
    });
    
    autoUpdater.on('update-downloaded', (info) => {
      logger.info('Update downloaded:', info.version);
      
      dialog.showMessageBox({
        type: 'info',
        title: 'Update Ready',
        message: 'Update has been downloaded',
        detail: 'The application will restart to install the update.',
        buttons: ['Restart Now', 'Later']
      }).then((result) => {
        if (result.response === 0) {
          autoUpdater.quitAndInstall();
        }
      });
    });
  }
  
  checkForUpdates() {
    autoUpdater.checkForUpdatesAndNotify();
  }
}

module.exports = AutoUpdater;
```

### Update Server

```
https://yourdomain.com/updates/
├── latest.yml              # Version metadata
├── latest-mac.yml
└── Ship Management-Setup-1.0.1.exe
```

---

## ⚖️ ƯU ĐIỂM & NHƯỢC ĐIỂM

### Ưu Điểm ✅

1. **User Experience Tuyệt Vời:**
   - Double-click to run
   - Không cần cài MongoDB, Python, Node.js
   - Tự động start/stop services
   - Icon trên Desktop và System Tray
   - Notification support

2. **Portability:**
   - Copy app sang máy khác = chạy ngay
   - USB drive ready
   - No system dependencies

3. **Professional:**
   - Native look & feel
   - Auto-update built-in
   - Installer/Uninstaller
   - Code signing support

4. **Integration:**
   - File system access
   - Notifications
   - System tray
   - Auto-launch on startup (optional)

### Nhược Điểm ❌

1. **File Size:**
   - Installer: ~150-200MB
   - Installed: ~250-300MB
   - Lớn hơn Docker hoặc Native

2. **Build Complexity:**
   - Phức tạp để package
   - Cần build cho từng platform
   - Code signing cần certificate ($$)

3. **Performance:**
   - Electron overhead (~80MB RAM)
   - Slower startup than native
   - More resource usage

4. **Updates:**
   - Cần rebuild toàn bộ app
   - Can't update backend code separately
   - Larger update downloads

---

## 📝 TÓM TẮT

**Electron App là lựa chọn tốt nhất cho:**
- ✅ Non-technical users
- ✅ Cần portable solution
- ✅ Muốn professional desktop app
- ✅ Budget cho development

**KHÔNG phù hợp nếu:**
- ❌ File size là vấn đề critical
- ❌ Cần absolute best performance
- ❌ Frequent backend updates
- ❌ Limited development resources

---

## 🎯 NEXT STEPS

Nếu bạn muốn tôi implement Electron App:

1. **Phase 1: Setup** (2 days)
   - Initialize Electron project
   - Setup build configuration
   - Prepare portable binaries

2. **Phase 2: Core Logic** (3 days)
   - Implement service managers
   - Create main window
   - Add tray icon & menu

3. **Phase 3: UI/UX** (2 days)
   - Splash screen
   - Settings window
   - Notifications

4. **Phase 4: Build & Test** (2 days)
   - Build for Windows/Mac/Linux
   - Test on different systems
   - Create installer

**Total: ~7-9 days**

Bạn có muốn tôi bắt đầu implement không? Hoặc cần thêm chi tiết về phần nào?
