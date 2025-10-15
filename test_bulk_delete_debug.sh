#!/bin/bash

echo "🔍 Testing Crew Certificates Bulk Delete"
echo "=========================================="

# Get backend URL from frontend .env
BACKEND_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
API="${BACKEND_URL}/api"

echo "📍 API URL: $API"
echo ""

# Login
echo "🔐 Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"123456"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  echo "$LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Login successful"
echo "🎫 Token: ${TOKEN:0:20}..."
echo ""

# Get ship ID
echo "🚢 Getting ships..."
SHIPS_RESPONSE=$(curl -s -X GET "$API/ships" \
  -H "Authorization: Bearer $TOKEN")

SHIP_ID=$(echo $SHIPS_RESPONSE | jq -r '.[0].id')
echo "✅ Ship ID: $SHIP_ID"
echo ""

# Get crew certificates
echo "📜 Getting crew certificates..."
CERTS_RESPONSE=$(curl -s -X GET "$API/crew-certificates/$SHIP_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "$CERTS_RESPONSE" | jq '.[0:2]'

# Extract first 2 certificate IDs
CERT_ID_1=$(echo $CERTS_RESPONSE | jq -r '.[0].id')
CERT_ID_2=$(echo $CERTS_RESPONSE | jq -r '.[1].id')

echo ""
echo "🎯 Testing bulk delete with 2 certificates:"
echo "   - Cert 1: $CERT_ID_1"
echo "   - Cert 2: $CERT_ID_2"
echo ""

# Bulk delete
echo "🗑️ Attempting bulk delete..."
BULK_DELETE_RESPONSE=$(curl -s -X DELETE "$API/crew-certificates/bulk-delete" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"certificate_ids\": [\"$CERT_ID_1\", \"$CERT_ID_2\"]}")

echo "📦 Response:"
echo "$BULK_DELETE_RESPONSE" | jq '.'

# Check backend logs
echo ""
echo "📋 Recent backend logs:"
tail -30 /var/log/supervisor/backend.err.log | grep -E "Bulk delete|Certificate|🗑️|🔍|⚠️|✅"
