#!/bin/bash
# ============================================
# Ship Management System - Google Cloud Deploy Script
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Ship Management System - Deploy Script${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud SDK chưa được cài đặt!${NC}"
    echo "Vui lòng cài đặt tại: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker chưa được cài đặt!${NC}"
    echo "Vui lòng cài đặt Docker Desktop"
    exit 1
fi

# Get project ID
echo -e "${YELLOW}📋 Nhập thông tin deploy:${NC}"
echo ""

# Get Project ID
read -p "Google Cloud Project ID: " PROJECT_ID
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Project ID không được để trống!${NC}"
    exit 1
fi

# Get Region
read -p "Region (mặc định: asia-southeast1): " REGION
REGION=${REGION:-asia-southeast1}

# Get MongoDB URL
echo ""
echo -e "${YELLOW}📦 MongoDB Atlas Connection String:${NC}"
echo "Ví dụ: mongodb+srv://user:pass@cluster.xxxxx.mongodb.net/ship_management"
read -p "MONGO_URL: " MONGO_URL
if [ -z "$MONGO_URL" ]; then
    echo -e "${RED}❌ MongoDB URL không được để trống!${NC}"
    exit 1
fi

# Get JWT Secret
read -p "JWT_SECRET (nhấn Enter để tự generate): " JWT_SECRET
if [ -z "$JWT_SECRET" ]; then
    JWT_SECRET=$(openssl rand -hex 32)
    echo -e "${GREEN}✅ JWT_SECRET đã được generate: ${JWT_SECRET:0:20}...${NC}"
fi

# Get Emergent LLM Key
read -p "EMERGENT_LLM_KEY (có thể để trống nếu không dùng AI): " EMERGENT_LLM_KEY

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Bắt đầu Deploy Backend...${NC}"
echo -e "${BLUE}============================================${NC}"

# Set project
gcloud config set project $PROJECT_ID

# Configure docker
gcloud auth configure-docker --quiet

# Build backend
echo -e "${YELLOW}🔨 Building backend image...${NC}"
cd backend
docker build -t gcr.io/$PROJECT_ID/ship-management-backend:latest .

# Push backend
echo -e "${YELLOW}📤 Pushing backend image...${NC}"
docker push gcr.io/$PROJECT_ID/ship-management-backend:latest

# Deploy backend
echo -e "${YELLOW}🚀 Deploying backend to Cloud Run...${NC}"
gcloud run deploy ship-management-backend \
  --image gcr.io/$PROJECT_ID/ship-management-backend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8001 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "MONGO_URL=$MONGO_URL" \
  --set-env-vars "DB_NAME=ship_management" \
  --set-env-vars "JWT_SECRET=$JWT_SECRET" \
  --set-env-vars "EMERGENT_LLM_KEY=$EMERGENT_LLM_KEY" \
  --quiet

# Get backend URL
BACKEND_URL=$(gcloud run services describe ship-management-backend --region $REGION --format 'value(status.url)')
echo -e "${GREEN}✅ Backend deployed: $BACKEND_URL${NC}"

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Bắt đầu Deploy Frontend...${NC}"
echo -e "${BLUE}============================================${NC}"

# Build frontend
echo -e "${YELLOW}🔨 Building frontend image...${NC}"
cd ../frontend
docker build \
  --build-arg REACT_APP_BACKEND_URL=$BACKEND_URL \
  -t gcr.io/$PROJECT_ID/ship-management-frontend:latest .

# Push frontend
echo -e "${YELLOW}📤 Pushing frontend image...${NC}"
docker push gcr.io/$PROJECT_ID/ship-management-frontend:latest

# Deploy frontend
echo -e "${YELLOW}🚀 Deploying frontend to Cloud Run...${NC}"
gcloud run deploy ship-management-frontend \
  --image gcr.io/$PROJECT_ID/ship-management-frontend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 80 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --quiet

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe ship-management-frontend --region $REGION --format 'value(status.url)')
echo -e "${GREEN}✅ Frontend deployed: $FRONTEND_URL${NC}"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  🎉 DEPLOY THÀNH CÔNG!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "📌 ${YELLOW}Frontend URL:${NC} $FRONTEND_URL"
echo -e "📌 ${YELLOW}Backend URL:${NC} $BACKEND_URL"
echo -e "📌 ${YELLOW}Backend Health:${NC} $BACKEND_URL/health"
echo -e "📌 ${YELLOW}API Docs:${NC} $BACKEND_URL/docs"
echo ""
echo -e "${BLUE}Tài khoản mặc định:${NC}"
echo "  Username: system_admin"
echo "  Password: YourSecure@Pass2024"
echo ""
echo -e "${YELLOW}⚠️  Lưu ý: Hãy đổi password sau khi đăng nhập!${NC}"
