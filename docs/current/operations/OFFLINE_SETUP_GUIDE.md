# Ship Management Offline - Hướng Dẫn Cài Đặt

## 📦 PACKAGE CONTENTS

File bạn nhận được:
```
ship-management-offline.zip (hoặc USB drive)
├── docker-compose.offline.yml    # Docker configuration
├── .env                           # Environment settings
├── backend/                       # Backend code
├── frontend/                      # Frontend code
├── data/
│   └── company_amcsc.archive     # Database dump
├── scripts/
│   └── backup.sh                 # Backup script
├── config/
│   └── mongod.conf               # MongoDB config
└── README.md                      # This file
```

---

## 🖥️ YÊU CẦU HỆ THỐNG

### Tối Thiểu
- **OS:** Windows 10, macOS 10.15, Ubuntu 20.04
- **CPU:** Intel Core i3
- **RAM:** 4 GB
- **Ổ cứng:** 10 GB trống
- **Màn hình:** 1366x768

### Khuyến Nghị
- **OS:** Windows 11, macOS 12+, Ubuntu 22.04
- **CPU:** Intel Core i5+
- **RAM:** 8 GB
- **Ổ cứng:** 20 GB SSD
- **Màn hình:** 1920x1080

---

## 📥 CÁCH CÀI ĐẶT

### PHƯƠNG ÁN 1: DOCKER DESKTOP (Recommended) ⭐

#### Bước 1: Cài Docker Desktop

**Windows:**
1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
2. Double-click file `Docker Desktop Installer.exe`
3. Follow installation wizard
4. Restart computer nếu được yêu cầu
5. Start Docker Desktop from Start Menu

**macOS:**
1. Download Docker Desktop for Mac
2. Open `Docker.dmg` file
3. Drag Docker icon to Applications folder
4. Open Docker from Applications
5. Allow permissions when prompted

**Linux (Ubuntu/Debian):**
```bash
# Update package index
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and log back in
```

#### Bước 2: Giải Nén Package

**Windows:**
```powershell
# Right-click file ZIP → Extract All
# Hoặc dùng 7-Zip/WinRAR
```

**macOS/Linux:**
```bash
# Extract ZIP file
unzip ship-management-offline.zip
cd ship-management-offline
```

#### Bước 3: Import Database

```bash
# Start MongoDB container first
docker-compose -f docker-compose.offline.yml up -d mongodb

# Wait for MongoDB to be ready (30 seconds)
sleep 30

# Import database
docker-compose -f docker-compose.offline.yml exec -T mongodb \
  mongorestore \
  --uri="mongodb://admin:SecurePass123!@#@localhost:27017" \
  --db=company_offline \
  --archive=/data/db/company_amcsc.archive \
  --gzip
```

**Hoặc sử dụng script tự động:**
```bash
# Windows (PowerShell)
.\scripts\import-database.ps1

# Mac/Linux
./scripts/import-database.sh
```

#### Bước 4: Start Application

```bash
# Start all services
docker-compose -f docker-compose.offline.yml up -d

# Check status
docker-compose -f docker-compose.offline.yml ps

# Expected output:
# NAME                                    STATUS
# ship_management_backend_offline         Up (healthy)
# ship_management_frontend_offline        Up
# ship_management_mongodb_offline         Up (healthy)
```

#### Bước 5: Access Application

1. Mở trình duyệt (Chrome/Firefox/Edge)
2. Truy cập: **http://localhost:3000**
3. Login với credentials:
   - Username: `admin1`
   - Password: `123456`
4. Bạn sẽ thấy banner **🔴 OFFLINE MODE** ở top

---

### PHƯƠNG ÁN 2: NATIVE INSTALLATION

#### Bước 1: Cài MongoDB

**Windows:**
1. Download: https://www.mongodb.com/try/download/community
2. Install với default settings
3. Start MongoDB service:
   ```
   net start MongoDB
   ```

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

**Linux:**
```bash
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Bước 2: Import Database

```bash
mongorestore \
  --uri="mongodb://localhost:27017" \
  --db=company_offline \
  --archive=./data/company_amcsc.archive \
  --gzip
```

#### Bước 3: Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment
export OFFLINE_MODE=true
export MONGO_URL=mongodb://localhost:27017

# Run
uvicorn server:app --host 0.0.0.0 --port 8001
```

#### Bước 4: Setup Frontend

```bash
# New terminal
cd frontend

# Install dependencies
npm install

# Set environment
export REACT_APP_BACKEND_URL=http://localhost:8001
export REACT_APP_OFFLINE_MODE=true

# Run
npm start
```

Browser sẽ tự động mở: http://localhost:3000

---

## 🔧 QUẢN LÝ HỆ THỐNG

### Xem Logs

```bash
# All services
docker-compose -f docker-compose.offline.yml logs -f

# Backend only
docker-compose -f docker-compose.offline.yml logs -f backend

# Frontend only
docker-compose -f docker-compose.offline.yml logs -f frontend

# MongoDB only
docker-compose -f docker-compose.offline.yml logs -f mongodb
```

### Stop Application

```bash
# Stop all services
docker-compose -f docker-compose.offline.yml down

# Stop and remove volumes (⚠️ WILL DELETE DATA)
docker-compose -f docker-compose.offline.yml down -v
```

### Restart Application

```bash
# Restart all
docker-compose -f docker-compose.offline.yml restart

# Restart specific service
docker-compose -f docker-compose.offline.yml restart backend
```

---

## 💾 BACKUP & RESTORE

### Automatic Backup

Hệ thống tự động backup mỗi ngày lúc 2:00 AM:
```bash
# Check backups
ls -lh ./backups/

# Example output:
# backup_company_offline_20250116_020000.archive
# backup_company_offline_20250117_020000.archive
# backup_company_offline_20250118_020000.archive
```

### Manual Backup

```bash
# Create backup now
docker-compose -f docker-compose.offline.yml exec mongodb \
  mongodump \
  --uri="mongodb://admin:SecurePass123!@#@localhost:27017" \
  --db=company_offline \
  --archive=/data/db/manual_backup_$(date +%Y%m%d).archive \
  --gzip

# Copy to external drive
cp ./data/mongodb/manual_backup_*.archive /mnt/usb/
```

### Restore from Backup

```bash
# Stop services
docker-compose -f docker-compose.offline.yml down

# Restore database
docker-compose -f docker-compose.offline.yml up -d mongodb
sleep 30

docker-compose -f docker-compose.offline.yml exec -T mongodb \
  mongorestore \
  --uri="mongodb://admin:SecurePass123!@#@localhost:27017" \
  --db=company_offline \
  --archive=/data/db/backup_company_offline_20250116.archive \
  --gzip \
  --drop

# Start all services
docker-compose -f docker-compose.offline.yml up -d
```

---

## 🔄 SYNC VỚI ONLINE

### Khi Có Internet Trở Lại

1. **Export Changes:**
   ```bash
   # Export local changes
   docker-compose -f docker-compose.offline.yml exec mongodb \
     mongodump \
     --uri="mongodb://admin:SecurePass123!@#@localhost:27017" \
     --db=company_offline \
     --archive=./sync/local_changes_$(date +%Y%m%d).archive \
     --gzip
   ```

2. **Connect to Online System:**
   - Login to online system
   - Go to: System Settings → Sync from Offline
   - Upload `local_changes_*.archive` file

3. **Resolve Conflicts:**
   - System sẽ detect conflicts (nếu có)
   - Review và chọn version to keep
   - Complete sync

4. **Download Updated Data:**
   - Export fresh database from online
   - Import vào offline system
   - Ready for next offline period

---

## ❓ TROUBLESHOOTING

### Problem: Docker Desktop không start

**Solution:**
```
1. Check if Hyper-V is enabled (Windows)
   - Control Panel → Programs → Turn Windows features on/off
   - Enable Hyper-V
   - Restart computer

2. Check if Docker service is running
   - Windows: Services → Docker Desktop Service → Start
   - Mac: Activity Monitor → Search "Docker" → Force Quit and restart
   - Linux: sudo systemctl start docker
```

### Problem: MongoDB container không start

**Solution:**
```bash
# Check logs
docker-compose -f docker-compose.offline.yml logs mongodb

# Common issues:
# 1. Port 27017 đã được sử dụng
sudo lsof -i :27017  # Check what's using port
sudo kill -9 <PID>   # Kill process

# 2. Permission issues
sudo chown -R 999:999 ./data/mongodb

# 3. Corrupted data
rm -rf ./data/mongodb/*
# Re-import database
```

### Problem: Backend không connect MongoDB

**Solution:**
```bash
# Check if MongoDB is accessible
docker-compose -f docker-compose.offline.yml exec backend \
  curl mongodb:27017

# Check environment variables
docker-compose -f docker-compose.offline.yml exec backend env | grep MONGO

# Restart backend
docker-compose -f docker-compose.offline.yml restart backend
```

### Problem: Frontend không load

**Solution:**
```bash
# Check if backend is accessible
curl http://localhost:8001/api/health

# Check frontend logs
docker-compose -f docker-compose.offline.yml logs frontend

# Rebuild frontend
docker-compose -f docker-compose.offline.yml down frontend
docker-compose -f docker-compose.offline.yml up -d --build frontend
```

### Problem: Quên password admin

**Solution:**
```bash
# Reset admin password
docker-compose -f docker-compose.offline.yml exec mongodb mongosh

# In MongoDB shell:
use company_offline
db.users.updateOne(
  { username: "admin1" },
  { $set: { 
    hashed_password: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ztpNtj3KhQ8u"
    // This is bcrypt hash for "123456"
  }}
)
```

---

## 📞 SUPPORT

### Common Questions

**Q: Có thể chạy trên nhiều máy cùng lúc không?**
A: Có. Mỗi máy có thể chạy một instance độc lập. Sau đó sync changes về online system.

**Q: Data được lưu ở đâu?**
A: 
- Database: `./data/mongodb/`
- Uploaded files: `./data/uploads/`
- Backups: `./backups/`

**Q: Có thể copy sang máy khác không?**
A: Có. Stop services, copy toàn bộ folder `ship-management-offline` sang máy mới, start lại.

**Q: Cần bao nhiêu dung lượng?**
A:
- Fresh install: ~1 GB
- Sau 1 tháng sử dụng: ~3-5 GB
- Backups (7 days): ~2-3 GB
- Total: ~8-10 GB

**Q: Có thể update code không?**
A: Có. Copy file code mới vào `./backend/` hoặc `./frontend/`, restart services.

### Contact Support

- **Email:** support@shipmanagement.com
- **Phone:** +84 xxx xxx xxxx
- **Remote Support:** TeamViewer ID provided separately

---

## 📋 CHECKLIST

### Initial Setup
- [ ] Docker Desktop installed and running
- [ ] Package extracted to local folder
- [ ] Database imported successfully
- [ ] All services running (green status)
- [ ] Can access http://localhost:3000
- [ ] Can login with admin credentials
- [ ] See "🔴 OFFLINE MODE" indicator

### Daily Operation
- [ ] Check services status every morning
- [ ] Monitor backup logs
- [ ] Check available disk space
- [ ] Review system logs for errors

### Before Going Offline
- [ ] Export latest database from online
- [ ] Import to offline system
- [ ] Verify all data is present
- [ ] Test login and basic operations
- [ ] Create manual backup

### After Coming Online
- [ ] Export offline changes
- [ ] Upload to online system
- [ ] Resolve any conflicts
- [ ] Download updated data
- [ ] Verify sync completed

---

## 📝 CHANGELOG

### Version 1.0.0 (2025-01-16)
- Initial offline release
- Docker-based deployment
- Automatic backup system
- Complete offline authentication
- Data sync capability

---

**🎉 Chúc bạn sử dụng hệ thống thành công!**

Nếu gặp vấn đề, vui lòng liên hệ support team.
