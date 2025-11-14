# Offline Deployment Architecture - Hướng Dẫn Chi Tiết

## TỔNG QUAN: HỆ THỐNG CHẠY NHƯ THẾ NÀO OFFLINE?

### Online Mode (Hiện tại) 🟢
```
┌─────────────────────────────────────────────────────────┐
│  User's Computer/Browser                                │
│  ├── Chrome/Firefox                                     │
│  └── Access: https://your-domain.com                    │
└────────────────┬────────────────────────────────────────┘
                 │ Internet
                 ↓
┌─────────────────────────────────────────────────────────┐
│  Cloud Server (Kubernetes/Docker)                       │
│  ├── Frontend (React) - Port 3000                       │
│  ├── Backend (FastAPI) - Port 8001                      │
│  └── Nginx (Reverse Proxy)                              │
└────────────────┬────────────────────────────────────────┘
                 │ Internet
                 ↓
┌─────────────────────────────────────────────────────────┐
│  MongoDB Atlas (Cloud Database)                         │
│  └── ship_management (All companies)                    │
└─────────────────────────────────────────────────────────┘
```

### Offline Mode (Đề xuất) 🔴
```
┌─────────────────────────────────────────────────────────┐
│  User's LOCAL Computer (Laptop/Desktop)                 │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Docker Desktop / Native Installation           │  │
│  │                                                  │  │
│  │  ├── MongoDB (Local)        Port: 27017        │  │
│  │  │   └── company_amcsc (Database)              │  │
│  │  │                                               │  │
│  │  ├── Backend (FastAPI)      Port: 8001         │  │
│  │  │   └── Connects to Local MongoDB             │  │
│  │  │                                               │  │
│  │  ├── Frontend (React)       Port: 3000         │  │
│  │  │   └── Connects to Local Backend             │  │
│  │  │                                               │  │
│  │  └── Browser                                    │  │
│  │      └── http://localhost:3000                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  NO INTERNET REQUIRED ✅                                │
└─────────────────────────────────────────────────────────┘
```

---

## PHƯƠNG ÁN 1: DOCKER DESKTOP (Recommended) ⭐

### Ưu điểm
- ✅ Dễ cài đặt (1 click install)
- ✅ Cross-platform (Windows, Mac, Linux)
- ✅ Isolated environment
- ✅ Easy backup/restore
- ✅ Portable (copy folder sang máy khác)

### Cấu trúc File

```
ship-management-offline/
├── docker-compose.yml           # Định nghĩa services
├── .env                          # Environment variables
├── data/
│   └── mongodb/                  # MongoDB data (persistent)
│       ├── company_amcsc.bson    # Exported database
│       └── ...
├── backend/
│   ├── Dockerfile
│   ├── server.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   └── ...
└── README.md                     # Hướng dẫn sử dụng
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  # MongoDB Local
  mongodb:
    image: mongo:7.0
    container_name: ship_management_mongodb
    restart: always
    ports:
      - "27017:27017"
    volumes:
      - ./data/mongodb:/data/db                    # ← Data lưu ở đây
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: SecurePass123
    command: mongod --quiet
    networks:
      - ship_network

  # Backend FastAPI
  backend:
    build: ./backend
    container_name: ship_management_backend
    restart: always
    ports:
      - "8001:8001"
    environment:
      # Offline mode configuration
      OFFLINE_MODE: "true"
      OFFLINE_DB_NAME: "company_amcsc"
      
      # Local MongoDB connection
      MONGO_URL: "mongodb://admin:SecurePass123@mongodb:27017"
      
      # JWT Secret
      SECRET_KEY: "your-secret-key-change-this"
      
      # Google Drive (optional - won't work offline)
      GOOGLE_DRIVE_ENABLED: "false"
    depends_on:
      - mongodb
    volumes:
      - ./backend:/app                             # ← Code lưu ở đây
      - ./data/uploads:/app/uploads                # ← Uploaded files
    networks:
      - ship_network
    command: uvicorn server:app --host 0.0.0.0 --port 8001 --reload

  # Frontend React
  frontend:
    build: ./frontend
    container_name: ship_management_frontend
    restart: always
    ports:
      - "3000:3000"
    environment:
      REACT_APP_BACKEND_URL: "http://localhost:8001"
      REACT_APP_OFFLINE_MODE: "true"
    volumes:
      - ./frontend:/app                            # ← Code lưu ở đây
      - /app/node_modules                          # ← Node modules
    networks:
      - ship_network
    command: npm start

networks:
  ship_network:
    driver: bridge
```

### .env File

```bash
# Offline Mode Configuration
OFFLINE_MODE=true
OFFLINE_DB_NAME=company_amcsc

# MongoDB Local
MONGO_URL=mongodb://admin:SecurePass123@mongodb:27017

# Security
SECRET_KEY=your-secret-key-change-this

# Features
GOOGLE_DRIVE_ENABLED=false
AI_ENABLED=false  # Có thể disable AI nếu không cần

# Ports
BACKEND_PORT=8001
FRONTEND_PORT=3000
MONGODB_PORT=27017
```

### Cách Chạy

```bash
# 1. Cài Docker Desktop
# Download từ: https://www.docker.com/products/docker-desktop

# 2. Extract offline package
unzip ship-management-offline.zip
cd ship-management-offline

# 3. Import database
docker-compose up -d mongodb
mongorestore --uri="mongodb://admin:SecurePass123@localhost:27017" \
  --db=company_amcsc \
  --archive=data/company_amcsc.archive

# 4. Start all services
docker-compose up -d

# 5. Check status
docker-compose ps

# 6. Access application
# Mở browser: http://localhost:3000

# 7. View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# 8. Stop application
docker-compose down

# 9. Backup data
docker-compose exec mongodb mongodump \
  --uri="mongodb://admin:SecurePass123@localhost:27017" \
  --db=company_amcsc \
  --archive=/data/db/backup_$(date +%Y%m%d).archive
```

### Dockerfile - Backend

```dockerfile
# backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Run application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Dockerfile - Frontend

```dockerfile
# frontend/Dockerfile

FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Run application
CMD ["npm", "start"]
```

---

## PHƯƠNG ÁN 2: NATIVE INSTALLATION (Advanced)

### Ưu điểm
- ✅ Performance tốt hơn (no Docker overhead)
- ✅ Dễ debug
- ✅ Có thể customize nhiều hơn

### Nhược điểm
- ❌ Phức tạp hơn để setup
- ❌ Phải cài nhiều dependencies
- ❌ Có thể conflict với existing software

### Setup Steps

#### 1. Cài MongoDB Local

**Windows:**
```powershell
# Download MongoDB Community Server
# https://www.mongodb.com/try/download/community

# Install và start service
net start MongoDB

# Hoặc chạy manual
mongod --dbpath C:\data\db
```

**macOS:**
```bash
# Install via Homebrew
brew tap mongodb/brew
brew install mongodb-community@7.0

# Start MongoDB
brew services start mongodb-community@7.0

# Hoặc chạy manual
mongod --config /usr/local/etc/mongod.conf
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install -y mongodb-org

# Start service
sudo systemctl start mongod
sudo systemctl enable mongod

# Hoặc chạy manual
mongod --dbpath /var/lib/mongodb
```

#### 2. Import Database

```bash
# Extract database dump
unzip company_amcsc.zip

# Import to local MongoDB
mongorestore --uri="mongodb://localhost:27017" \
  --db=company_amcsc \
  database.bson
```

#### 3. Setup Backend

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OFFLINE_MODE=true
export OFFLINE_DB_NAME=company_amcsc
export MONGO_URL=mongodb://localhost:27017

# Run backend
uvicorn server:app --host 0.0.0.0 --port 8001
```

#### 4. Setup Frontend

```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Set environment variables
export REACT_APP_BACKEND_URL=http://localhost:8001
export REACT_APP_OFFLINE_MODE=true

# Run frontend
npm start

# Frontend will open at http://localhost:3000
```

---

## PHƯƠNG ÁN 3: DESKTOP APPLICATION (Electron) 🎯

### Concept: "Double-click to Run"

Package toàn bộ ứng dụng thành 1 file .exe (Windows) hoặc .app (Mac):

```
ship-management-offline.exe
├── Embedded MongoDB
├── Embedded Backend (Python)
├── Embedded Frontend (React)
└── Auto-start tất cả khi click
```

### Ưu điểm
- ✅ **Cực kỳ đơn giản**: Double-click là chạy
- ✅ Không cần cài Docker, Python, Node.js
- ✅ Tự động start/stop các services
- ✅ Icon trên Desktop
- ✅ Tray icon với menu

### Architecture

```
Electron App
├── Main Process (Node.js)
│   ├── Start MongoDB (Embedded)
│   ├── Start Backend (Python subprocess)
│   ├── Start Frontend (React dev server)
│   └── Open Browser Window
│
└── Renderer Process
    └── Display React App in Electron window
```

### Implementation Overview

```javascript
// main.js (Electron)

const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let mongoProcess;
let backendProcess;
let mainWindow;

app.whenReady().then(() => {
  // 1. Start MongoDB
  startMongoDB();
  
  // 2. Start Backend
  setTimeout(() => startBackend(), 3000);
  
  // 3. Start Frontend (Electron window)
  setTimeout(() => createWindow(), 6000);
});

function startMongoDB() {
  const mongoPath = path.join(__dirname, 'resources', 'mongodb', 'mongod.exe');
  const dbPath = path.join(app.getPath('userData'), 'mongodb_data');
  
  mongoProcess = spawn(mongoPath, [
    '--dbpath', dbPath,
    '--quiet'
  ]);
  
  console.log('✅ MongoDB started');
}

function startBackend() {
  const pythonPath = path.join(__dirname, 'resources', 'python', 'python.exe');
  const serverPath = path.join(__dirname, 'backend', 'server.py');
  
  backendProcess = spawn(pythonPath, [
    '-m', 'uvicorn',
    'server:app',
    '--host', '0.0.0.0',
    '--port', '8001'
  ], {
    cwd: path.join(__dirname, 'backend'),
    env: {
      ...process.env,
      OFFLINE_MODE: 'true',
      MONGO_URL: 'mongodb://localhost:27017'
    }
  });
  
  console.log('✅ Backend started');
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      nodeIntegration: false
    }
  });
  
  // Load React app
  mainWindow.loadURL('http://localhost:8001');
  
  console.log('✅ Application ready');
}

// Cleanup on exit
app.on('quit', () => {
  if (mongoProcess) mongoProcess.kill();
  if (backendProcess) backendProcess.kill();
});
```

### Package Structure

```
ShipManagement-Offline.exe (Windows)
├── resources/
│   ├── mongodb/
│   │   ├── mongod.exe              # MongoDB binary
│   │   └── mongo.exe
│   ├── python/
│   │   ├── python.exe              # Python runtime
│   │   └── Lib/                    # Python libraries
│   └── data/
│       └── company_amcsc.archive   # Pre-imported database
├── backend/
│   ├── server.py
│   └── ...
├── frontend/
│   └── build/                      # React production build
└── main.js                         # Electron entry point
```

### Build Commands

```bash
# Install dependencies
npm install electron electron-builder

# Package for Windows
npm run build:windows

# Package for macOS
npm run build:mac

# Package for Linux
npm run build:linux
```

### package.json

```json
{
  "name": "ship-management-offline",
  "version": "1.0.0",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build:windows": "electron-builder --win",
    "build:mac": "electron-builder --mac",
    "build:linux": "electron-builder --linux"
  },
  "build": {
    "appId": "com.shipmanagement.offline",
    "productName": "Ship Management Offline",
    "files": [
      "main.js",
      "backend/**/*",
      "frontend/build/**/*",
      "resources/**/*"
    ],
    "extraResources": [
      {
        "from": "resources/mongodb",
        "to": "mongodb"
      },
      {
        "from": "resources/python",
        "to": "python"
      }
    ],
    "win": {
      "target": "nsis",
      "icon": "icon.ico"
    },
    "mac": {
      "target": "dmg",
      "icon": "icon.icns"
    }
  }
}
```

---

## SO SÁNH CÁC PHƯƠNG ÁN

| Tiêu chí | Docker | Native | Electron App |
|----------|--------|--------|--------------|
| **Dễ cài đặt** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Dễ sử dụng** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Performance** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Portable** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Maintenance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **File size** | ~500MB | ~200MB | ~800MB |
| **Platform** | All | All | All |
| **Updates** | Easy | Manual | Auto-update |

---

## DATA STORAGE & PERSISTENCE

### 1. Database Files (MongoDB)

**Docker:**
```
./data/mongodb/           # Host machine
  ├── collection-0-*.wt
  ├── collection-2-*.wt
  ├── index-1-*.wt
  └── WiredTiger
```

**Native:**
```
# Windows
C:\data\db\

# macOS
/usr/local/var/mongodb/

# Linux
/var/lib/mongodb/
```

**Electron:**
```
%APPDATA%\ship-management-offline\mongodb_data\
```

### 2. Uploaded Files

```
./data/uploads/
  ├── certificates/
  ├── passports/
  ├── crew_photos/
  └── documents/
```

### 3. Configuration Files

```
.env                       # Environment variables
config.json                # Application settings
offline_cache.json         # Offline mode metadata
```

### 4. Logs

```
./logs/
  ├── backend.log          # Backend logs
  ├── frontend.log         # Frontend logs
  ├── mongodb.log          # Database logs
  └── sync.log             # Sync operations
```

---

## BACKUP & RESTORE

### Automatic Backup

```python
# backend/backup_service.py

import schedule
import time
from datetime import datetime

def backup_database():
    """
    Automatic daily backup
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"./backups/backup_{timestamp}.archive"
    
    # MongoDB dump
    os.system(f"""
        mongodump 
        --uri="mongodb://localhost:27017" 
        --db=company_amcsc 
        --archive={backup_path}
        --gzip
    """)
    
    print(f"✅ Backup created: {backup_path}")
    
    # Keep only last 7 backups
    cleanup_old_backups(days=7)

# Schedule daily at 2 AM
schedule.every().day.at("02:00").do(backup_database)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Manual Backup

```bash
# Backup everything
docker-compose exec mongodb mongodump \
  --uri="mongodb://admin:SecurePass123@localhost:27017" \
  --db=company_amcsc \
  --archive=/data/db/manual_backup.archive \
  --gzip

# Copy backup to external drive
cp ./data/mongodb/manual_backup.archive /mnt/usb_drive/
```

### Restore

```bash
# Stop services
docker-compose down

# Restore database
mongorestore \
  --uri="mongodb://admin:SecurePass123@localhost:27017" \
  --db=company_amcsc \
  --archive=./backups/backup_20250116.archive \
  --gzip \
  --drop  # Drop existing data first

# Start services
docker-compose up -d
```

---

## SYSTEM REQUIREMENTS

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10+, macOS 10.15+, Ubuntu 20.04+ |
| **CPU** | Intel Core i3 or equivalent |
| **RAM** | 4 GB |
| **Storage** | 10 GB free space |
| **Display** | 1366x768 |

### Recommended Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 11, macOS 12+, Ubuntu 22.04+ |
| **CPU** | Intel Core i5 or equivalent |
| **RAM** | 8 GB |
| **Storage** | 20 GB SSD |
| **Display** | 1920x1080 |

---

## KHUYẾN NGHỊ

### Cho Văn Phòng (Office Use)
✅ **Docker Desktop**
- Dễ quản lý
- Dễ backup/restore
- Có thể chạy nhiều instances

### Cho Tàu (Ship Use)
✅ **Electron Desktop App**
- Cực kỳ đơn giản
- Double-click to run
- Không cần technical knowledge
- Tự động backup

### Cho Developer/IT
✅ **Native Installation**
- Full control
- Best performance
- Easy debugging

---

## DEPLOYMENT CHECKLIST

### Phase 1: Preparation
- [ ] Export company database with users
- [ ] Create offline package
- [ ] Write user documentation
- [ ] Prepare installation guide

### Phase 2: Package Creation
- [ ] Build Docker images
- [ ] Test on clean machine
- [ ] Create Electron app (if needed)
- [ ] Sign applications (Windows/Mac)

### Phase 3: Distribution
- [ ] Create USB installer
- [ ] Upload to download portal
- [ ] Create video tutorial
- [ ] Prepare support documentation

### Phase 4: Installation Support
- [ ] Remote assistance setup
- [ ] Troubleshooting guide
- [ ] Common issues FAQ
- [ ] Contact support info

---

## CÂU HỎI CHO BẠN

1. **Deployment Method:**
   - ⚪ Docker (recommended for flexibility)
   - ⚪ Electron App (recommended for simplicity)
   - ⚪ Native (recommended for performance)
   - ⚪ All three (provide options)

2. **Target Devices:**
   - ⚪ Laptop trên tàu
   - ⚪ Desktop văn phòng
   - ⚪ Tablet (iPad/Android)

3. **Distribution:**
   - ⚪ USB drive
   - ⚪ Download link
   - ⚪ Pre-installed on devices

4. **Support Level:**
   - ⚪ Self-service (documentation only)
   - ⚪ Remote assistance
   - ⚪ On-site training

Bạn muốn triển khai theo phương án nào? Tôi có thể tạo complete package cho bất kỳ phương án nào bạn chọn.
