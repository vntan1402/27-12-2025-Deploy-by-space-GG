# MongoDB Atlas Setup Guide

## Bước 1: Tạo MongoDB Atlas Account
1. Truy cập [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Đăng ký tài khoản miễn phí
3. Verify email

## Bước 2: Tạo Cluster
1. Click **"Build a Database"**
2. Chọn **"M0 Sandbox"** (FREE tier)
3. Chọn **Cloud Provider**: AWS
4. Chọn **Region**: Singapore (gần Việt Nam nhất)
5. **Cluster Name**: `ship-management-cluster`
6. Click **"Create"**

## Bước 3: Tạo Database User
1. Trong **Database Access** tab
2. Click **"Add New Database User"**
3. **Authentication Method**: Password
4. **Username**: `ship_admin`
5. **Password**: Tạo password mạnh (lưu lại)
6. **Database User Privileges**: Read and write to any database
7. Click **"Add User"**

## Bước 4: Setup Network Access
1. Trong **Network Access** tab
2. Click **"Add IP Address"**
3. Chọn **"Add Current IP Address"** 
4. Hoặc chọn **"Allow Access from Anywhere"** (0.0.0.0/0) - để test
5. Click **"Confirm"**

## Bước 5: Get Connection String
1. Trong **Database** tab
2. Click **"Connect"** trên cluster
3. Chọn **"Connect your application"**
4. **Driver**: Python
5. **Version**: 3.6 or later
6. Copy **Connection String**:
   ```
   mongodb+srv://ship_admin:<password>@ship-management-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
7. Thay `<password>` bằng password thực của user

## Bước 6: Tạo Database
Connection string đầy đủ sẽ là:
```
mongodb+srv://ship_admin:YOUR_PASSWORD@ship-management-cluster.xxxxx.mongodb.net/ship_management?retryWrites=true&w=majority
```

**Lưu ý**: 
- Thay `YOUR_PASSWORD` bằng password thực
- Database name: `ship_management`
- Lưu connection string an toàn, sẽ cần để cấu hình hệ thống

## Security Best Practices
- Sử dụng strong password cho database user
- Giới hạn IP access khi deploy production
- Enable MongoDB Atlas backup (mặc định đã có)
- Monitor usage qua Atlas dashboard

## Next Steps
Sau khi có connection string, cung cấp cho developer để tiếp tục migration process.