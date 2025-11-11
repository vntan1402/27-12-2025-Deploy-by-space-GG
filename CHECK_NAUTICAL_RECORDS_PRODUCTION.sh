#!/bin/bash

# Script kiểm tra Admin trên Production
# Domain: https://nautical-records.emergent.cloud/

echo "=========================================="
echo "  KIỂM TRA ADMIN - NAUTICAL RECORDS"
echo "  Production: nautical-records.emergent.cloud"
echo "=========================================="
echo ""

# 1. Kiểm tra Admin Status
echo "📊 Bước 1: Kiểm tra Admin Status..."
echo "URL: https://nautical-records.emergent.cloud/api/admin/status"
echo ""

curl -s -X GET "https://nautical-records.emergent.cloud/api/admin/status" | python3 -m json.tool 2>/dev/null || curl -s -X GET "https://nautical-records.emergent.cloud/api/admin/status"

echo ""
echo "=========================================="
echo ""

# 2. Test Login
echo "🔐 Bước 2: Test Login với system_admin..."
echo ""
echo "⚠️  Nhập password từ Environment Variables trong Deployments panel"
echo ""
read -p "Nhập password cho system_admin: " -s PASSWORD
echo ""
echo ""

curl -s -X POST "https://nautical-records.emergent.cloud/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"system_admin\",\"password\":\"$PASSWORD\",\"remember_me\":false}" | python3 -m json.tool 2>/dev/null || curl -s -X POST "https://nautical-records.emergent.cloud/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"system_admin\",\"password\":\"$PASSWORD\",\"remember_me\":false}"

echo ""
echo "=========================================="
echo ""
echo "✅ Hoàn tất kiểm tra!"
echo ""
echo "Nếu cần tạo admin thủ công:"
echo "https://nautical-records.emergent.cloud/api/admin/create-simple?secret=YOUR_SECRET"
echo ""
