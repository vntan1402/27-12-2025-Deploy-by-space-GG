# 🚀 Hướng Dẫn Deploy Ship Management System lên Google Cloud

## Tổng Quan Kiến Trúc

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Cloud Run     │     │   Cloud Run     │     │  MongoDB Atlas  │
│   (Frontend)    │────▶│   (Backend)     │────▶│   (Database)    │
│   Port 80       │     │   Port 8001     │     │   Free Tier     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Chi Phí Ước Tính (USD/tháng)

| Dịch vụ | Free Tier | Ước tính sử dụng nhẹ |
|---------|-----------|---------------------|
| Cloud Run | 2 triệu requests/tháng | ~$0-5 |
| MongoDB Atlas | 512MB miễn phí | $0 |
| Container Registry | 0.5GB miễn phí | ~$0-1 |
| **Tổng** | | **~$0-6/tháng** |

---

## 📋 BƯỚC 1: Chuẩn Bị MongoDB Atlas (15 phút)

### 1.1. Tạo tài khoản MongoDB Atlas

1. Truy cập: https://www.mongodb.com/cloud/atlas/register
2. Đăng ký tài khoản miễn phí (có thể dùng Google account)

### 1.2. Tạo Cluster miễn phí

1. Click **"Build a Database"**
2. Chọn **"M0 FREE"** (Shared Cluster)
3. Chọn Cloud Provider: **Google Cloud**
4. Chọn Region: **asia-southeast1 (Singapore)** - gần Việt Nam nhất
5. Cluster Name: `ship-management`
6. Click **"Create Cluster"**

### 1.3. Cấu hình Security

**Tạo Database User:**
1. Vào **Database Access** (menu trái)
2. Click **"Add New Database User"**
3. Authentication: Password
   - Username: `shipmanagement`
   - Password: Tạo password mạnh (lưu lại!)
4. Database User Privileges: **Read and write to any database**
5. Click **"Add User"**

**Cấu hình Network Access:**
1. Vào **Network Access** (menu trái)
2. Click **"Add IP Address"**
3. Chọn **"Allow Access from Anywhere"** (0.0.0.0/0)
   - ⚠️ Cho production, nên giới hạn IP cụ thể
4. Click **"Confirm"**

### 1.4. Lấy Connection String

1. Vào **Database** → Click **"Connect"**
2. Chọn **"Connect your application"**
3. Driver: Python, Version: 3.12 or later
4. Copy connection string, ví dụ:
```
mongodb+srv://shipmanagement:<password>@ship-management.xxxxx.mongodb.net/?retryWrites=true&w=majority
```
5. Thay `<password>` bằng password đã tạo
6. Thêm tên database vào cuối:
```
mongodb+srv://shipmanagement:YOUR_PASSWORD@ship-management.xxxxx.mongodb.net/ship_management?retryWrites=true&w=majority
```

**⚠️ LƯU LẠI CONNECTION STRING NÀY - SẼ DÙNG Ở BƯỚC 3!**

---

## 📋 BƯỚC 2: Chuẩn Bị Google Cloud (10 phút)

### 2.1. Cài đặt Google Cloud SDK

**macOS:**
```bash
brew install google-cloud-sdk
```

**Windows:**
Download từ: https://cloud.google.com/sdk/docs/install

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 2.2. Đăng nhập và cấu hình

```bash
# Đăng nhập Google Cloud
gcloud auth login

# Xem danh sách projects
gcloud projects list

# Set project (thay YOUR_PROJECT_ID bằng project ID của bạn)
gcloud config set project YOUR_PROJECT_ID

# Kích hoạt các APIs cần thiết
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 2.3. Cấu hình Docker authentication

```bash
gcloud auth configure-docker
```

---

## 📋 BƯỚC 3: Deploy Backend (20 phút)

### 3.1. Clone code từ GitHub (nếu chưa có)

Đầu tiên, sử dụng tính năng **"Save to GitHub"** trên Emergent để push code lên GitHub.

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### 3.2. Tạo file .env.production cho Backend

Tạo file `backend/.env.production`:
```bash
cat > backend/.env.production << 'EOF'
# MongoDB Atlas Connection
MONGO_URL=mongodb+srv://shipmanagement:YOUR_PASSWORD@ship-management.xxxxx.mongodb.net/ship_management?retryWrites=true&w=majority
DB_NAME=ship_management

# Security
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production-make-it-long

# Emergent LLM Key (nếu dùng AI features)
EMERGENT_LLM_KEY=your-emergent-llm-key

# Admin Initialization
INIT_ADMIN_USERNAME=admin
INIT_ADMIN_EMAIL=admin@yourcompany.com
INIT_ADMIN_PASSWORD=YourSecurePassword123!
INIT_ADMIN_FULL_NAME=System Administrator

# Admin API Security
ADMIN_CREATION_SECRET=your-admin-creation-secret-key
EOF
```

**⚠️ QUAN TRỌNG:** 
- Thay `YOUR_PASSWORD` và connection string bằng MongoDB Atlas connection string
- Tạo JWT_SECRET mạnh (ít nhất 32 ký tự)
- Thay đổi tất cả passwords

### 3.3. Build và Push Docker Image

```bash
# Di chuyển vào thư mục backend
cd backend

# Build Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/ship-management-backend:latest .

# Push lên Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/ship-management-backend:latest
```

### 3.4. Deploy lên Cloud Run

```bash
# Deploy với environment variables
gcloud run deploy ship-management-backend \
  --image gcr.io/YOUR_PROJECT_ID/ship-management-backend:latest \
  --region asia-southeast1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8001 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "MONGO_URL=mongodb+srv://shipmanagement:YOUR_PASSWORD@ship-management.xxxxx.mongodb.net/ship_management?retryWrites=true&w=majority" \
  --set-env-vars "DB_NAME=ship_management" \
  --set-env-vars "JWT_SECRET=your-super-secret-jwt-key" \
  --set-env-vars "EMERGENT_LLM_KEY=your-emergent-llm-key"
```

### 3.5. Lấy Backend URL

Sau khi deploy thành công, bạn sẽ nhận được URL như:
```
Service URL: https://ship-management-backend-xxxxx-as.a.run.app
```

**📝 LƯU LẠI URL NÀY - SẼ DÙNG CHO FRONTEND!**

### 3.6. Test Backend

```bash
# Test health endpoint
curl https://ship-management-backend-xxxxx-as.a.run.app/health

# Kết quả mong đợi:
# {"status":"healthy","version":"2.0.0","database":"connected"}
```

---

## 📋 BƯỚC 4: Deploy Frontend (15 phút)

### 4.1. Build Frontend với Backend URL

```bash
# Di chuyển vào thư mục frontend
cd ../frontend

# Build Docker image với Backend URL
docker build \
  --build-arg REACT_APP_BACKEND_URL=https://ship-management-backend-xxxxx-as.a.run.app \
  -t gcr.io/YOUR_PROJECT_ID/ship-management-frontend:latest .

# Push lên Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/ship-management-frontend:latest
```

### 4.2. Deploy lên Cloud Run

```bash
gcloud run deploy ship-management-frontend \
  --image gcr.io/YOUR_PROJECT_ID/ship-management-frontend:latest \
  --region asia-southeast1 \
  --platform managed \
  --allow-unauthenticated \
  --port 80 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10
```

### 4.3. Lấy Frontend URL

Sau khi deploy thành công:
```
Service URL: https://ship-management-frontend-xxxxx-as.a.run.app
```

**🎉 ĐÂY LÀ URL ỨNG DỤNG CỦA BẠN!**

---

## 📋 BƯỚC 5: Cấu hình CORS cho Backend (5 phút)

Cập nhật CORS trong backend để cho phép Frontend URL:

### 5.1. Sửa file `backend/app/main.py`

Tìm phần CORS middleware và thêm Frontend URL:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # Hoặc liệt kê cụ thể:
        "https://ship-management-frontend-xxxxx-as.a.run.app",
        "https://your-custom-domain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)
```

### 5.2. Re-deploy Backend

```bash
cd backend
docker build -t gcr.io/YOUR_PROJECT_ID/ship-management-backend:latest .
docker push gcr.io/YOUR_PROJECT_ID/ship-management-backend:latest

gcloud run deploy ship-management-backend \
  --image gcr.io/YOUR_PROJECT_ID/ship-management-backend:latest \
  --region asia-southeast1
```

---

## 📋 BƯỚC 6: Migrate Data (Tùy chọn)

Nếu bạn muốn migrate data từ Emergent sang MongoDB Atlas:

### 6.1. Export data từ Emergent

Trên môi trường Emergent, chạy:
```bash
cd /app/backend
mongodump --uri="mongodb://localhost:27017/ship_management" --out=/tmp/backup
```

### 6.2. Import vào MongoDB Atlas

```bash
mongorestore --uri="mongodb+srv://shipmanagement:YOUR_PASSWORD@ship-management.xxxxx.mongodb.net" /tmp/backup
```

---

## 📋 BƯỚC 7: Cấu hình Custom Domain (Tùy chọn)

### 7.1. Thêm Custom Domain cho Frontend

1. Vào Google Cloud Console → Cloud Run
2. Chọn service `ship-management-frontend`
3. Tab **"Domain Mappings"** → **"Add Mapping"**
4. Chọn **"Verify a new domain"**
5. Thêm domain (ví dụ: `app.yourcompany.com`)
6. Làm theo hướng dẫn để verify DNS

### 7.2. Cập nhật DNS

Thêm CNAME record:
```
app.yourcompany.com  →  ghs.googlehosted.com
```

---

## 🔧 Troubleshooting

### Lỗi: "Connection refused" khi kết nối MongoDB

**Nguyên nhân:** IP chưa được whitelist
**Giải pháp:** 
1. Vào MongoDB Atlas → Network Access
2. Thêm IP: `0.0.0.0/0` (Allow all)

### Lỗi: "CORS policy" trên Frontend

**Nguyên nhân:** Backend chưa cho phép Frontend URL
**Giải pháp:** Cập nhật CORS origins trong `main.py`

### Lỗi: Container crash sau deploy

**Kiểm tra logs:**
```bash
gcloud run logs read ship-management-backend --region asia-southeast1 --limit 50
```

### Lỗi: "Permission denied" khi push image

**Giải pháp:**
```bash
gcloud auth configure-docker
```

---

## 📊 Monitoring & Logs

### Xem logs realtime

```bash
# Backend logs
gcloud run logs tail ship-management-backend --region asia-southeast1

# Frontend logs
gcloud run logs tail ship-management-frontend --region asia-southeast1
```

### Xem metrics

1. Vào Google Cloud Console
2. Cloud Run → Chọn service
3. Tab **"Metrics"**

---

## 💰 Tối ưu chi phí

### Cấu hình auto-scaling

```bash
# Giảm min-instances về 0 để tiết kiệm khi không có traffic
gcloud run services update ship-management-backend \
  --region asia-southeast1 \
  --min-instances 0 \
  --max-instances 5
```

### Set CPU allocation

```bash
# Chỉ charge CPU khi có request
gcloud run services update ship-management-backend \
  --region asia-southeast1 \
  --cpu-throttling
```

---

## ✅ Checklist Hoàn Thành

- [ ] MongoDB Atlas cluster đã tạo
- [ ] Database user đã tạo
- [ ] Network access đã cấu hình
- [ ] Google Cloud SDK đã cài đặt
- [ ] APIs đã kích hoạt
- [ ] Backend đã deploy và test
- [ ] Frontend đã deploy
- [ ] CORS đã cấu hình
- [ ] (Tùy chọn) Custom domain
- [ ] (Tùy chọn) Data migration

---

## 🆘 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra logs: `gcloud run logs read SERVICE_NAME`
2. Kiểm tra MongoDB Atlas connection
3. Verify environment variables đã set đúng

---

**Chúc bạn deploy thành công! 🎉**
