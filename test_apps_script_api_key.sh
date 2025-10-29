#!/bin/bash

# ========================================
# Quick Test: Apps Script API Key
# ========================================

echo "🧪 Quick Test for Apps Script API Key Authentication"
echo "======================================================"
echo ""

# Configuration
WEB_APP_URL="PASTE_YOUR_WEB_APP_URL_HERE"
API_KEY="Vntan1402sms"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if Web App URL is configured
if [ "$WEB_APP_URL" = "PASTE_YOUR_WEB_APP_URL_HERE" ]; then
  echo -e "${RED}❌ ERROR: Please update WEB_APP_URL in this script${NC}"
  echo "   Edit this file and replace 'PASTE_YOUR_WEB_APP_URL_HERE' with your actual Web App URL"
  exit 1
fi

echo "Configuration:"
echo "  Web App URL: $WEB_APP_URL"
echo "  API Key: $API_KEY"
echo ""

# Test 1: No API Key (Should fail)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: No API Key (Should FAIL)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
RESPONSE=$(curl -s -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{"action": "test_connection"}' 2>&1)

echo "Response: $RESPONSE"
if echo "$RESPONSE" | grep -q '"success":false'; then
  echo -e "${GREEN}✅ PASS - Correctly rejected${NC}"
else
  echo -e "${RED}❌ FAIL - Should have been rejected${NC}"
fi
echo ""

# Test 2: Correct API Key (Should succeed)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Correct API Key (Should SUCCEED)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
RESPONSE=$(curl -s -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d "{\"action\": \"test_connection\", \"api_key\": \"$API_KEY\"}" 2>&1)

echo "Response: $RESPONSE"
if echo "$RESPONSE" | grep -q '"success":true'; then
  echo -e "${GREEN}✅ PASS - Connection successful!${NC}"
else
  echo -e "${RED}❌ FAIL - Should have succeeded${NC}"
fi
echo ""

echo "======================================================"
echo "Test completed!"
echo "======================================================"
